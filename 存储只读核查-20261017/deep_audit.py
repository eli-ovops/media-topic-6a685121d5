"""Read-only exact-list audit. Does not remove, move, patch or execute inputs."""
from pathlib import Path
import os, json, hashlib, csv, datetime, subprocess, collections

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[1]
FRED = WORK / 'Fred复刻测试-20261016/7694088597179239690/source-snapshot/FredTalk-1.5-3D/camera'
QWEN = WORK / 'qianwen-go-case-20261013/flow/04/project'
OLD = json.loads((ROOT / 'bundle-details.json').read_text())
ITEMS = [r for r in OLD if r['project_source_names']]
assert len(ITEMS) == 96
CACHE = {}
def digest(p):
    st = p.lstat()
    if p.is_symlink():
        raise ValueError('SYMLINK_NOT_FOLLOWED')
    key = (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)
    if key not in CACHE:
        h = hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
                h.update(b)
        after = p.lstat()
        if key != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError('FILE_CHANGED_DURING_READ')
        CACHE[key] = h.hexdigest()
    return CACHE[key]

def files_under(p):
    for directory, dirs, files in os.walk(p, followlinks=False):
        for d in list(dirs):
            x = Path(directory) / d
            if x.is_symlink():
                dirs.remove(d)
                yield x
        for name in files:
            yield Path(directory) / name

# Only the two preserved source trees; no whole-home/project scan.
source_hash_index = {}
for project in (FRED, QWEN):
    idx = collections.defaultdict(list)
    for p in files_under(project / 'src'):
        if not p.is_symlink() and p.is_file():
            idx[digest(p)].append(str(p))
    source_hash_index[str(project)] = idx

results = []
for n, old in enumerate(ITEMS):
    bundle = Path(old['path'])
    assert bundle.parent == Path('/var/folders/1q/6mf7kw2j1z19q1f9dydq60wh0000gn/T')
    if bundle.is_symlink():
        raise ValueError('BUNDLE_REPLACED_BY_SYMLINK')
    project = FRED if any('Replica' in s for s in old['project_source_names']) else QWEN
    rec = {'path': str(bundle), 'project': str(project), 'allocated_kib_previous': old['allocated_kib'],
           'public_files': [], 'project_sources': [], 'special_or_unclassified': [], 'errors': []}
    public_root = bundle / 'public'
    if public_root.exists():
        for p in files_under(public_root):
            rel = p.relative_to(public_root)
            original = project / 'public' / rel
            entry = {'path': str(p), 'original': str(original)}
            try:
                st = p.lstat()
                entry.update(bytes=st.st_size, inode=st.st_ino, mtime_ns=st.st_mtime_ns)
                if p.is_symlink() or original.is_symlink():
                    entry['status'] = 'HOLD_SYMLINK'
                elif not original.is_file():
                    entry['sha256'] = digest(p)
                    entry['status'] = 'HOLD_ORIGINAL_MISSING'
                else:
                    entry['sha256'] = digest(p)
                    entry['original_sha256'] = digest(original)
                    entry['status'] = 'EXACT_DUPLICATE' if entry['sha256'] == entry['original_sha256'] else 'HOLD_CONTENT_DIFFERS'
            except Exception as e:
                entry['status'] = 'HOLD_ERROR'
                entry['error'] = str(e)
            rec['public_files'].append(entry)
    seen = set()
    for p in bundle.iterdir():
        if p.name == 'public':
            continue
        if p.is_symlink() or not p.is_file():
            rec['special_or_unclassified'].append(str(p))
            continue
        if p.suffix not in {'.js', '.map', '.wasm', '.html', '.ico', '.css'}:
            rec['special_or_unclassified'].append(str(p))
        if p.suffix != '.map':
            continue
        try:
            m = json.loads(p.read_text())
            content = m.get('sourcesContent', [])
            for i, src in enumerate(m.get('sources', [])):
                if not src.startswith('./src/'):
                    if not any(x in src for x in ('node_modules', 'webpack/', 'webpack ', 'external ', 'ignored|')):
                        rec['special_or_unclassified'].append({'map': str(p), 'source': src})
                    continue
                body = content[i] if i < len(content) else None
                identity = (src, hashlib.sha256(body.encode()).hexdigest() if body is not None else None)
                if identity in seen:
                    continue
                seen.add(identity)
                disk = project / src[2:]
                e = {'source': src, 'map': str(p), 'preserved_source': str(disk), 'embedded_sha256': identity[1]}
                if body is None:
                    e['status'] = 'HOLD_NO_EMBEDDED_CONTENT'
                elif disk.is_symlink():
                    e['status'] = 'HOLD_SOURCE_SYMLINK'
                elif disk.is_file() and digest(disk) == identity[1]:
                    e['status'] = 'EXACT_SOURCE_PRESENT'
                else:
                    alternatives = source_hash_index[str(project)].get(identity[1], [])
                    e['same_content_elsewhere_in_source_tree'] = alternatives
                    e['status'] = 'EXACT_SOURCE_ELSEWHERE' if alternatives else 'HOLD_HISTORICAL_SOURCE_VERSION'
                rec['project_sources'].append(e)
        except Exception as e:
            rec['errors'].append({'map': str(p), 'error': str(e)})
    public_ok = all(e['status'] == 'EXACT_DUPLICATE' for e in rec['public_files'])
    source_ok = all(e['status'] in {'EXACT_SOURCE_PRESENT', 'EXACT_SOURCE_ELSEWHERE'} for e in rec['project_sources'])
    rec['content_copy_check_passed'] = public_ok and source_ok and not rec['errors'] and not rec['special_or_unclassified']
    rec['classification'] = 'CONTENT_CHECK_PASSED_RUNTIME_REVIEW_PENDING' if rec['content_copy_check_passed'] else 'HOLD_REQUIRES_REVIEW'
    results.append(rec)
    if (n + 1) % 8 == 0:
        print('audited', n + 1, '/', len(ITEMS), flush=True)

stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
summary = {'checked_at': stamp, 'read_only': True, 'bundle_count': len(results),
           'public_files_compared': sum(len(r['public_files']) for r in results),
           'public_status_counts': dict(collections.Counter(e['status'] for r in results for e in r['public_files'])),
           'source_status_counts': dict(collections.Counter(e['status'] for r in results for e in r['project_sources'])),
           'content_passed_bundle_count': sum(r['content_copy_check_passed'] for r in results),
           'content_passed_allocated_gib': sum(r['allocated_kib_previous'] for r in results if r['content_copy_check_passed']) / 1024**2,
           'held_bundle_count': sum(not r['content_copy_check_passed'] for r in results),
           'held_allocated_gib': sum(r['allocated_kib_previous'] for r in results if not r['content_copy_check_passed']) / 1024**2,
           'deleted_count': 0, 'delete_authorized': False}
(ROOT / '逐项深核-96包.json').write_text(json.dumps({'summary': summary, 'bundles': results}, ensure_ascii=False, indent=2))
with (ROOT / '逐项深核-96包.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['path', 'classification', 'allocated_MiB', 'public_files', 'public_mismatch_or_missing', 'historical_source_versions', 'other_or_errors'])
    for r in results:
        w.writerow([r['path'], r['classification'], round(r['allocated_kib_previous']/1024, 3), len(r['public_files']),
                    sum(e['status'] != 'EXACT_DUPLICATE' for e in r['public_files']),
                    sum(e['status'].startswith('HOLD_') for e in r['project_sources']),
                    len(r['special_or_unclassified']) + len(r['errors'])])
print(json.dumps(summary, ensure_ascii=False), flush=True)
