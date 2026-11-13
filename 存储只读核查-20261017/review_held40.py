"""Read-only review of the 40 explicitly held bundles; writes audit reports only."""
from pathlib import Path
import collections, csv, datetime, difflib, hashlib, json, os, re, shutil, stat, struct, subprocess

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[1]
TEMP = Path('/var/folders/1q/6mf7kw2j1z19q1f9dydq60wh0000gn/T')
OLD = json.loads((ROOT / '\u9010\u9879\u6df1\u6838-96\u5305.json').read_text())
ROWS = list(csv.DictReader((ROOT / '\u6682\u755940\u5305.csv').open()))
PATHS = [r['absolute_path'] for r in ROWS]
assert len(PATHS) == len(set(PATHS)) == 40
BASE = {b['path']: b for b in OLD['bundles']}
CACHE = {}
PROBE_CACHE = {}

def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()

def signature(p):
    s = p.lstat()
    return [s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns]

def sha(p):
    s = signature(p)
    assert stat.S_ISREG(s[2]), ('NOT_REGULAR', str(p))
    k = tuple(s)
    if k not in CACHE:
        h = hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda: f.read(4 * 1024 * 1024), b''): h.update(block)
        assert signature(p) == s, ('FILE_CHANGED', str(p))
        CACHE[k] = h.hexdigest()
    return CACHE[k]

def inventory(root):
    inv = {'.': signature(root)}
    assert stat.S_ISDIR(inv['.'][2])
    for base, ds, fs in os.walk(root, followlinks=False):
        for name in sorted(ds + fs):
            p = Path(base) / name
            s = signature(p)
            assert stat.S_ISDIR(s[2]) or stat.S_ISREG(s[2]), ('SPECIAL_FILE', str(p))
            inv[str(p.relative_to(root))] = s
    return inv

def probe(p):
    # Existing ffprobe is x86_64 and fails on this arm64 host (LOCAL_BLOCKERS).
    # Use the already installed arm64 ffmpeg, decoding only to the null muxer.
    key = sha(p)
    if key not in PROBE_CACHE:
        r = subprocess.run([shutil.which('ffmpeg'), '-hide_banner', '-nostdin', '-i', str(p),
                            '-map', '0:v?', '-map', '0:a?', '-f', 'null', '-'],
                           capture_output=True, text=True, timeout=45)
        frames = re.findall(r'frame=\s*(\d+)', r.stderr)
        durations = re.findall(r'Duration:\s*([^,\n]+)', r.stderr)
        PROBE_CACHE[key] = {'method':'existing arm64 ffmpeg full decode to null; no output media',
            'returncode':r.returncode,'decoded_frames':int(frames[-1]) if frames else None,
            'reported_duration':durations[0] if durations else None,'stderr':r.stderr.strip()}
    return PROBE_CACHE[key]

def boxes(p):
    size, offset, found = p.stat().st_size, 0, []
    with p.open('rb') as f:
        while offset + 8 <= size:
            f.seek(offset)
            raw = f.read(8)
            length, kind = struct.unpack('>I4s', raw)
            header = 8
            if length == 1:
                extra = f.read(8)
                if len(extra) != 8: break
                length = struct.unpack('>Q', extra)[0]
                header = 16
            declared = length
            if length == 0: length = size - offset
            if length < header: break
            found.append({'type': kind.decode('ascii', errors='replace'), 'offset': offset,
                          'header_bytes': header, 'declared_bytes': declared,
                          'available_payload_bytes': max(0, min(length, size - offset) - header),
                          'complete_box': offset + length <= size})
            if offset + length > size: break
            offset += length
    return found

def payload_prefix(a, a_boxes, b, b_boxes):
    x = next((q for q in a_boxes if q['type'] == 'mdat'), None)
    y = next((q for q in b_boxes if q['type'] == 'mdat'), None)
    if x is None or y is None: return {'status': 'NO_MDAT_PAIR'}
    n = x['available_payload_bytes']
    if n == 0: return {'status': 'EMPTY_MDAT', 'compared_bytes': 0}
    if n > y['available_payload_bytes']: return {'status': 'LONGER_THAN_ORIGINAL', 'compared_bytes': 0}
    ha, hb = hashlib.sha256(), hashlib.sha256()
    with a.open('rb') as fa, b.open('rb') as fb:
        fa.seek(x['offset'] + x['header_bytes'])
        fb.seek(y['offset'] + y['header_bytes'])
        left = n
        while left:
            length = min(left, 1024 * 1024)
            aa, bb = fa.read(length), fb.read(length)
            assert len(aa) == len(bb) == length
            ha.update(aa); hb.update(bb); left -= length
    return {'status': 'EXACT_MDAT_PREFIX' if ha.digest() == hb.digest() else 'DIFFERENT_MDAT_PAYLOAD',
            'compared_bytes': n, 'candidate_payload_sha256': ha.hexdigest(), 'original_prefix_sha256': hb.hexdigest()}

out = {'started_at': now(), 'scope': '40 exact held bundle directories; associated preserved originals and bounded source roots',
       'read_only': True, 'deleted_count': 0, 'moved_count': 0, 'archived_asset_count': 0,
       'bundles': [], 'source_versions': {}, 'source_graphs': {}, 'media_differences': [],
       'errors': [], 'source_search_roots': [],
       'tool_limit': 'ffprobe static binary is x86_64 despite arm64 pathname; Bad CPU type. LOCAL_BLOCKERS checked; existing arm64 ffmpeg used without installation or system changes.'}
all_sources, historical, media_originals = {}, {}, {}
preserved = {}
for n, row in enumerate(ROWS):
    root = Path(row['absolute_path'])
    assert root.parent == TEMP and not root.is_symlink() and root.resolve() == TEMP.resolve() / root.name
    old = BASE[str(root)]
    before = inventory(root)
    assert before['.'][0] == int(row['device']) and before['.'][1] == int(row['directory_inode']) and before['.'][4] == int(row['mtime_ns'])
    rec = {'path': str(root), 'project': old['project'], 'before_inventory': before,
           'allocated_kib_previous': old['allocated_kib_previous'], 'public_files': [],
           'project_source_records': [], 'artifact_files': [], 'source_graph': {}}
    expected_public = {x['path']: x for x in old['public_files']}
    actual_public = {str(root / r) for r, s in before.items() if r.startswith('public/') and stat.S_ISREG(s[2])}
    assert actual_public == set(expected_public), ('PUBLIC_SET_CHANGED', str(root))
    for path, e in expected_public.items():
        p, original = Path(path), Path(e['original'])
        current = sha(p)
        assert current == e['sha256'] and p.stat().st_size == e['bytes'], ('BUNDLE_PUBLIC_CHANGED', str(p))
        assert original.is_file() and not original.is_symlink()
        original_hash = sha(original)
        assert original_hash == e['original_sha256'], ('ORIGINAL_CHANGED', str(original))
        preserved[str(original)] = {'stat': signature(original), 'sha256': original_hash}
        x = {'path': path, 'original': str(original), 'bytes': p.stat().st_size, 'sha256': current,
             'original_bytes': original.stat().st_size, 'original_sha256': original_hash,
             'status': 'EXACT_DUPLICATE' if current == original_hash else 'DIFFERENT_BYTES'}
        rec['public_files'].append(x)
        if current != original_hash:
            xb, yb = boxes(p), boxes(original)
            x.update(container_boxes=xb, original_container_boxes=yb, probe=probe(p), original_probe=probe(original),
                     payload_comparison=payload_prefix(p, xb, original, yb), bundle=str(root))
            out['media_differences'].append(x)
    expected_sources = {(x['source'], x['embedded_sha256']) for x in old['project_sources']}
    seen = set()
    for p in sorted(root.iterdir()):
        if p.name == 'public': continue
        assert p.is_file() and not p.is_symlink() and p.suffix in {'.js', '.map', '.wasm', '.html', '.ico', '.css'}
        rec['artifact_files'].append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)})
        if p.suffix != '.map': continue
        m = json.loads(p.read_text())
        bodies = m.get('sourcesContent', [])
        for i, source in enumerate(m.get('sources', [])):
            if not source.startswith('./src/'):
                assert any(t in source for t in ('node_modules', 'webpack/', 'webpack ', 'external ', 'ignored|'))
                continue
            assert i < len(bodies) and bodies[i] is not None
            body = bodies[i]
            h = hashlib.sha256(body.encode()).hexdigest()
            if (source, h) in seen: continue
            seen.add((source, h))
            src = Path(old['project']) / source[2:]
            project_key = 'fred' if 'Fred\u590d\u523b\u6d4b\u8bd5' in old['project'] else 'qianwen'
            key = project_key + '/' + source[6:] + '@' + h
            current_hash = sha(src) if src.is_file() and not src.is_symlink() else None
            imports = re.findall(r'(?:from\s*|import\s*|require\s*\()\s*[\'\"]([^\'\"]+)[\'\"]', body)
            asset_calls = re.findall(r'staticFile\s*\(\s*[\'\"]([^\'\"]+)[\'\"]', body)
            e = {'key': key, 'source': source, 'map': str(p), 'bytes': len(body.encode()), 'sha256': h,
                 'original_project': old['project'], 'current_source': str(src), 'current_sha256': current_hash,
                 'imports': sorted(set(imports)), 'literal_asset_references': sorted(set(asset_calls)),
                 'historical_difference': current_hash != h}
            rec['project_source_records'].append(e)
            rec['source_graph'][source] = key
            if key not in all_sources:
                all_sources[key] = {'record': e, 'body': body, 'occurrences': []}
            all_sources[key]['occurrences'].append({'bundle': str(root), 'map': str(p), 'source': source})
            if current_hash != h:
                current_body = src.read_text() if src.is_file() else ''
                delta = list(difflib.unified_diff(body.splitlines(), current_body.splitlines(), fromfile='historical', tofile='current', lineterm=''))
                e['diff_added_lines'] = sum(z.startswith('+') and not z.startswith('+++') for z in delta)
                e['diff_removed_lines'] = sum(z.startswith('-') and not z.startswith('---') for z in delta)
                e['diff_to_current'] = delta
                historical[key] = all_sources[key]
            elif current_hash is not None:
                preserved[str(src)] = {'stat': signature(src), 'sha256': current_hash}
    assert seen == expected_sources, ('SOURCE_SET_CHANGED', str(root))
    for source, key in rec['source_graph'].items():
        for dependency in all_sources[key]['record']['imports']:
            if not dependency.startswith('.'): continue
            relative = os.path.normpath(str(Path(source).parent / dependency))
            candidates = ['./' + relative + ext for ext in ('', '.tsx', '.ts', '.js', '/index.tsx', '/index.ts')]
            matches = [c for c in candidates if c in rec['source_graph']]
            all_sources[key]['record'].setdefault('local_dependency_resolution', {})[dependency] = matches
    graph_hash = hashlib.sha256(json.dumps(rec['source_graph'], sort_keys=True).encode()).hexdigest()
    rec['source_graph_sha256'] = graph_hash
    out['source_graphs'].setdefault(graph_hash, {'source_mapping': rec['source_graph'], 'bundles': []})['bundles'].append(str(root))
    rec['unchanged_during_read'] = inventory(root) == before
    assert rec['unchanged_during_read']
    out['bundles'].append(rec)
    if (n + 1) % 8 == 0: print('reviewed', n + 1, '/ 40', flush=True)

# Search only source-like files under the two exact historical content roots.
fred_root = WORK / 'Fred\u590d\u523b\u6d4b\u8bd5-20261016/7694088597179239690'
qwen_root = WORK / 'qianwen-go-case-20261013'
for scope in (fred_root, qwen_root):
    out['source_search_roots'].append(str(scope))
    found = 0
    for base, ds, fs in os.walk(scope, followlinks=False):
        ds[:] = [d for d in ds if d not in {'node_modules', '.git', 'public', 'out', 'frames', 'stills', 'authorized-media', '.cache', 'dist'} and not (Path(base)/d).is_symlink()]
        for name in fs:
            p = Path(base) / name
            if p.suffix not in {'.tsx', '.ts', '.jsx', '.js'} or p.is_symlink() or p.stat().st_size > 4*1024*1024: continue
            h = sha(p)
            found += 1
            for key, value in historical.items():
                if h == value['record']['sha256']:
                    value['record'].setdefault('matching_preserved_source_files', []).append(str(p))
    out.setdefault('bounded_source_file_counts', {})[str(scope)] = found

for key, value in all_sources.items():
    e = value['record']
    e['occurrences'] = value['occurrences']
    if e['historical_difference']:
        e.setdefault('matching_preserved_source_files', [])
    out['source_versions'][key] = e
out['preserved_original_files'] = preserved

# Group byte-distinct partial files, without creating copies or changing media.
groups = collections.defaultdict(list)
for x in out['media_differences']: groups[x['sha256']].append(x['path'])
out['unique_difference_media'] = [{'sha256': h, 'paths': paths,
    'bytes': next(x['bytes'] for x in out['media_differences'] if x['sha256']==h)} for h, paths in groups.items()]

aliases = sorted(set(PATHS + [str(Path(p).resolve()) for p in PATHS]))
opened = subprocess.run(['lsof', '-nP', '-Fpcn'], capture_output=True, text=True, timeout=45)
assert opened.returncode in (0,1)
matches, pid, command = [], None, None
for line in opened.stdout.splitlines():
    if line.startswith('p'): pid = line[1:]
    elif line.startswith('c'): command = line[1:]
    elif line.startswith('n'):
        name = line[1:]
        if any(name==p or name.startswith(p+'/') for p in aliases): matches.append({'pid':pid,'command':command,'path':name})
ps = subprocess.run(['ps','-axo','pid=,command='],capture_output=True,text=True,check=True)
refs = []
for line in ps.stdout.splitlines():
    row = line.strip().split(None,1)
    if len(row)!=2 or int(row[0])==os.getpid(): continue
    hits = [p for p in aliases if p in row[1]]
    if hits: refs.append({'pid':row[0],'executable':row[1].split()[0],'bundle_references':hits})
out['runtime_snapshot'] = {'checked_at':now(),'lsof_returncode':opened.returncode,'open_bundle_references':matches,'process_argument_references':refs}
out['all_40_unchanged'] = all(inventory(Path(b['path'])) == b['before_inventory'] for b in out['bundles'])
assert out['all_40_unchanged']
out['summary'] = {'bundle_count':40, 'public_file_count':sum(len(b['public_files']) for b in out['bundles']),
 'public_exact_duplicates':sum(x['status']=='EXACT_DUPLICATE' for b in out['bundles'] for x in b['public_files']),
 'historical_source_records':sum(e['historical_difference'] for b in out['bundles'] for e in b['project_source_records']),
 'historical_source_unique_versions':len(historical), 'historical_source_unique_bytes':sum(len(v['body'].encode()) for v in historical.values()),
 'all_embedded_source_unique_versions':len(all_sources), 'all_embedded_source_unique_bytes':sum(len(v['body'].encode()) for v in all_sources.values()),
 'source_graph_count':len(out['source_graphs']),
 'media_difference_occurrences':len(out['media_differences']), 'media_difference_unique_files':len(groups),
 'media_difference_unique_bytes':sum(x['bytes'] for x in out['unique_difference_media']),
 'allocated_kib_previous':sum(b['allocated_kib_previous'] for b in out['bundles']),
 'historical_versions_found_elsewhere':sum(bool(v['record'].get('matching_preserved_source_files')) for v in historical.values()),
 'live_references_found':len(matches)+len(refs), 'deleted_count':0,'moved_count':0,'archived_asset_count':0}
out['completed_at']=now()
(ROOT/'held40-review-evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (ROOT/'held40-historical-sources.csv').open('w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['source_key','source','bytes','sha256','occurrences','existing_same_bytes','example_map','proposed_relative_path'])
    for key,v in historical.items():
        e=v['record']; project,rest=key.split('/',1); rel=rest.split('@')[0]
        target=str(Path('sources')/project/e['sha256']/rel)
        w.writerow([key,e['source'],e['bytes'],e['sha256'],len(v['occurrences']),';'.join(e.get('matching_preserved_source_files',[])),e['map'],target])
print(json.dumps(out['summary'],ensure_ascii=False),flush=True)
