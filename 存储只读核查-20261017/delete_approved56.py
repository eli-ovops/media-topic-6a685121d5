"""Exact approved-list cleanup with content, identity and live-use checks."""
from pathlib import Path
import argparse, collections, csv, datetime, hashlib, json, os, stat, subprocess, sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[1]
TEMP = Path('/var/folders/1q/6mf7kw2j1z19q1f9dydq60wh0000gn/T')
APPROVAL = ROOT / '\u5185\u5bb9\u6838\u9a8c\u901a\u8fc756\u5305.csv'
HELD = ROOT / '\u6682\u755940\u5305.csv'
AUDIT = ROOT / '\u9010\u9879\u6df1\u6838-96\u5305.json'
PREFLIGHT = ROOT / 'approved56-preflight.json'
RECEIPT = ROOT / 'approved56-deletion-receipt.json'
CACHE = {}

def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()

def stamp(p):
    s = p.lstat()
    return [s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns]

def digest(p):
    before = stamp(p)
    assert stat.S_ISREG(before[2]), ('NOT_REGULAR', str(p))
    key = tuple(before)
    if key not in CACHE:
        h = hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
                h.update(block)
        assert stamp(p) == before, ('CHANGED_DURING_HASH', str(p))
        CACHE[key] = h.hexdigest()
    return CACHE[key]

def tree(p, hashes=False):
    items = {'.': {'stat': stamp(p)}}
    assert stat.S_ISDIR(items['.']['stat'][2]), ('NOT_DIRECTORY', str(p))
    for base, dirs, files in os.walk(p, followlinks=False):
        for name in sorted(dirs + files):
            q = Path(base) / name
            st = stamp(q)
            assert stat.S_ISDIR(st[2]) or stat.S_ISREG(st[2]), ('SPECIAL_ENTRY', str(q))
            e = {'stat': st}
            if hashes and stat.S_ISREG(st[2]):
                e['sha256'] = digest(q)
            items[str(q.relative_to(p))] = e
    return items

def write_json(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def runtime_check(paths, projects):
    # macOS /var is the system alias of /private/var; inspect both names.
    path_aliases = sorted(set(paths + [str(Path(p).resolve()) for p in paths]))
    opened = subprocess.run(['lsof', '-nP', '-Fpcn'], capture_output=True, text=True, timeout=45)
    assert opened.returncode in (0, 1), 'LSOF_FAILED'
    matches, pid, command = [], None, None
    for line in opened.stdout.splitlines():
        if line.startswith('p'): pid = line[1:]
        elif line.startswith('c'): command = line[1:]
        elif line.startswith('n'):
            name = line[1:]
            for p in path_aliases:
                if name == p or name.startswith(p + '/'):
                    matches.append({'pid': pid, 'command': command, 'path': name})
    ps = subprocess.run(['ps', '-axo', 'pid=,command='], capture_output=True, text=True, timeout=15)
    assert ps.returncode == 0, 'PS_FAILED'
    args = []
    for line in ps.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2 or int(parts[0]) == os.getpid(): continue
        hits = [p for p in path_aliases + projects if p in parts[1]]
        if hits: args.append({'pid': parts[0], 'executable': parts[1].split()[0], 'matched_paths': hits})
    result = {'checked_at': now(), 'lsof_returncode': opened.returncode,
              'ps_returncode': ps.returncode, 'open_bundle_references': matches,
              'process_argument_references': args}
    assert not matches and not args, ('LIVE_REFERENCE_FOUND', result)
    return result

def df():
    r = subprocess.run(['df', '-k', '/Users/USER'], capture_output=True, text=True, check=True)
    a = r.stdout.splitlines()[-1].split()
    return {'checked_at': now(), 'filesystem': a[0], 'total_kib': int(a[1]),
            'used_kib': int(a[2]), 'available_kib': int(a[3]), 'mount': a[-1]}

def prepare():
    rows = list(csv.DictReader(APPROVAL.open()))
    held_rows = list(csv.DictReader(HELD.open()))
    baseline = {b['path']: b for b in json.loads(AUDIT.read_text())['bundles']}
    paths = [r['absolute_path'] for r in rows]
    held_paths = [r['absolute_path'] for r in held_rows]
    assert len(paths) == len(set(paths)) == 56
    assert len(held_paths) == len(set(held_paths)) == 40
    assert not set(paths) & set(held_paths)
    for s in paths + held_paths:
        p = Path(s)
        assert p.parent == TEMP and p.name.startswith('remotion-webpack-bundle-')
        assert p.resolve() == TEMP.resolve() / p.name and not p.is_symlink()
    projects = sorted(set(r['source_project'] for r in rows))
    assert len(projects) == 2
    result = {'started_at': now(), 'authorization': {
        'user_instruction': '\u5185\u5bb9\u6838\u9a8c\u901a\u8fc7\uff0c\u53ef\u5217\u5165\u5220\u9664\u6e05\u5355  \u5220\u9664\u5427',
        'exact_scope': str(APPROVAL), 'approval_sha256': digest(APPROVAL),
        'approved_count': 56, 'excluded_held_count': 40},
        'bundles': [], 'held_trees': {p: tree(Path(p)) for p in held_paths},
        'original_files': {}, 'protected_indexes': {}}
    originals = result['original_files']
    def check_original(p, expected):
        p = Path(p)
        assert any(p.is_relative_to(Path(proj)) for proj in projects), ('OUTSIDE_PROJECT', str(p))
        assert not p.is_symlink() and p.resolve() == p, ('ORIGINAL_SYMLINK', str(p))
        actual = digest(p)
        assert actual == expected, ('ORIGINAL_CHANGED', str(p))
        originals[str(p)] = {'stat': stamp(p), 'sha256': actual}
    for n, row in enumerate(rows):
        p = Path(row['absolute_path'])
        old = baseline[str(p)]
        assert old['content_copy_check_passed'] and not old['errors'] and not old['special_or_unclassified']
        s = p.lstat()
        assert (s.st_dev, s.st_ino, s.st_mtime_ns) == tuple(int(row[k]) for k in ('device', 'directory_inode', 'mtime_ns')), ('DIRECTORY_CHANGED', str(p))
        files = tree(p, hashes=True)
        actual_public = {str(p / rel) for rel, e in files.items()
                         if rel.startswith('public/') and stat.S_ISREG(e['stat'][2])}
        expected_public = {e['path'] for e in old['public_files']}
        assert actual_public == expected_public, ('PUBLIC_FILE_SET_CHANGED', str(p))
        for e in old['public_files']:
            current = files[str(Path(e['path']).relative_to(p))]
            assert e['status'] == 'EXACT_DUPLICATE'
            assert current['stat'][1] == e['inode'] and current['stat'][3:] == [e['bytes'], e['mtime_ns']]
            assert current['sha256'] == e['sha256'] == e['original_sha256']
            check_original(e['original'], e['sha256'])
        expected_sources = {(e['source'], e['embedded_sha256']) for e in old['project_sources']}
        actual_sources = set()
        for q in p.iterdir():
            if q.name == 'public':
                assert q.is_dir() and not q.is_symlink()
                continue
            assert q.is_file() and q.suffix in {'.js', '.map', '.wasm', '.html', '.ico', '.css'}, ('UNCLASSIFIED', str(q))
            if q.suffix != '.map': continue
            m = json.loads(q.read_text())
            bodies = m.get('sourcesContent', [])
            for i, source in enumerate(m.get('sources', [])):
                if source.startswith('./src/'):
                    assert i < len(bodies) and bodies[i] is not None
                    actual_sources.add((source, hashlib.sha256(bodies[i].encode()).hexdigest()))
                else:
                    assert any(t in source for t in ('node_modules', 'webpack/', 'webpack ', 'external ', 'ignored|')), ('UNKNOWN_EMBEDDED_SOURCE', str(q), source)
        assert actual_sources == expected_sources, ('EMBEDDED_SOURCE_SET_CHANGED', str(p))
        for e in old['project_sources']:
            assert e['status'] == 'EXACT_SOURCE_PRESENT', ('SOURCE_REQUIRES_REVIEW', e['source'])
            check_original(e['preserved_source'], e['embedded_sha256'])
        result['bundles'].append({'path': str(p), 'project': old['project'],
                                  'allocated_kib_at_audit': old['allocated_kib_previous'], 'tree': files})
        if (n + 1) % 8 == 0: print('revalidated', n + 1, '/ 56', flush=True)
    # Fingerprint long-lived library indexes, outside the cleanup scope.
    for relative in ('\u8d44\u4ea7\u5e93/FredTalk/manifest.json', '\u8d44\u4ea7\u5e93/FredTalk/README.md',
                     'Fred\u4ed8\u8d39\u8d44\u6599\u5168\u7ad9\u5b66\u4e60-20261016/README.md'):
        p = WORK / relative
        assert p.is_file()
        result['protected_indexes'][str(p)] = {'stat': stamp(p), 'sha256': digest(p)}
    result['runtime_check'] = runtime_check(paths, projects)
    result['completed_at'] = now()
    write_json(PREFLIGHT, result)
    print(json.dumps({'preflight': 'PASSED', 'bundles': 56, 'public_files': sum(len(baseline[p]['public_files']) for p in paths),
                      'original_files': len(originals), 'file': str(PREFLIGHT)}, ensure_ascii=False), flush=True)

def anchored_parent(rootfd, rel, inventory):
    fd = os.dup(rootfd)
    current = Path('.')
    try:
        for part in Path(rel).parent.parts:
            if part == '.': continue
            current /= part
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            s = os.fstat(fd)
            expected = inventory[str(current)]['stat']
            assert [s.st_dev, s.st_ino] == expected[:2], 'PARENT_IDENTITY_CHANGED'
        return fd
    except BaseException:
        os.close(fd)
        raise

def execute():
    assert not RECEIPT.exists(), 'RECEIPT_ALREADY_EXISTS_DO_NOT_REPEAT'
    pre = json.loads(PREFLIGHT.read_text())
    assert digest(APPROVAL) == pre['authorization']['approval_sha256']
    paths = [b['path'] for b in pre['bundles']]
    assert len(paths) == len(set(paths)) == 56
    # Check all preserved inputs and complete target inventories before first unlink.
    for p, e in {**pre['original_files'], **pre['protected_indexes']}.items():
        assert stamp(Path(p)) == e['stat'] and digest(Path(p)) == e['sha256'], ('PRESERVED_INPUT_CHANGED', p)
    for p, inv in pre['held_trees'].items():
        assert tree(Path(p)) == inv, ('HELD_TREE_CHANGED', p)
    for b in pre['bundles']:
        assert tree(Path(b['path']), hashes=True) == b['tree'], ('TARGET_CHANGED', b['path'])
    live = runtime_check(paths, sorted({b['project'] for b in pre['bundles']}))
    other_temp_trees = {str(p): tree(p) for p in TEMP.glob('remotion-webpack-bundle-*')
                        if str(p) not in paths and str(p) not in pre['held_trees']}
    receipt = {'started_at': now(), 'authorization': pre['authorization'],
               'preflight_file': str(PREFLIGHT), 'preflight_sha256': digest(PREFLIGHT),
               'runtime_check': live, 'removed_files': [], 'removed_directories': [],
               'deleted_bundles': [], 'errors': [], 'other_temp_trees_before': other_temp_trees,
               'df_before': df()}
    write_json(RECEIPT, receipt)
    try:
        for b in pre['bundles']:
            p, inv = Path(b['path']), b['tree']
            assert p.parent == TEMP and p.resolve() == TEMP.resolve() / p.name
            assert tree(p) == {k: {'stat': v['stat']} for k, v in inv.items()}, ('LAST_INVENTORY_CHANGED', str(p))
            fd = os.open(p, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                s = os.fstat(fd)
                assert [s.st_dev, s.st_ino] == inv['.']['stat'][:2]
                files = [r for r, e in inv.items() if r != '.' and stat.S_ISREG(e['stat'][2])]
                for rel in sorted(files):
                    parentfd = anchored_parent(fd, rel, inv)
                    try:
                        s = os.stat(Path(rel).name, dir_fd=parentfd, follow_symlinks=False)
                        assert [s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns] == inv[rel]['stat'], ('FILE_IDENTITY_CHANGED', rel)
                        os.unlink(Path(rel).name, dir_fd=parentfd)
                        receipt['removed_files'].append({'path': str(p / rel), 'bytes': s.st_size, 'sha256': inv[rel]['sha256']})
                    finally: os.close(parentfd)
                dirs = [r for r, e in inv.items() if r != '.' and stat.S_ISDIR(e['stat'][2])]
                for rel in sorted(dirs, key=lambda r: len(Path(r).parts), reverse=True):
                    parentfd = anchored_parent(fd, rel, inv)
                    try:
                        s = os.stat(Path(rel).name, dir_fd=parentfd, follow_symlinks=False)
                        assert [s.st_dev, s.st_ino] == inv[rel]['stat'][:2]
                        os.rmdir(Path(rel).name, dir_fd=parentfd)
                        receipt['removed_directories'].append(str(p / rel))
                    finally: os.close(parentfd)
            finally: os.close(fd)
            assert stamp(p)[:2] == inv['.']['stat'][:2]
            os.rmdir(p)
            receipt['removed_directories'].append(str(p))
            receipt['deleted_bundles'].append(str(p))
            write_json(RECEIPT, receipt)
    except BaseException as e:
        receipt['errors'].append(repr(e))
    finally:
        receipt['df_after'] = df()
        receipt['completed_at'] = now()
        receipt['all_approved_paths_absent'] = all(not os.path.lexists(p) for p in paths)
        receipt['held_40_unchanged'] = all(tree(Path(p)) == inv for p, inv in pre['held_trees'].items())
        receipt['other_temp_trees_unchanged'] = all(tree(Path(p)) == inv for p, inv in other_temp_trees.items())
        receipt['preserved_inputs_unchanged'] = all(stamp(Path(p)) == e['stat'] and digest(Path(p)) == e['sha256']
            for p, e in {**pre['original_files'], **pre['protected_indexes']}.items())
        assert receipt['df_before']['filesystem'] == receipt['df_after']['filesystem']
        receipt['actual_available_delta_kib'] = receipt['df_after']['available_kib'] - receipt['df_before']['available_kib']
        receipt['status'] = 'COMPLETED' if len(receipt['deleted_bundles']) == 56 and not receipt['errors'] and receipt['all_approved_paths_absent'] and receipt['held_40_unchanged'] and receipt['other_temp_trees_unchanged'] and receipt['preserved_inputs_unchanged'] else 'PARTIAL_REQUIRES_REVIEW'
        write_json(RECEIPT, receipt)
        print(json.dumps({k: receipt[k] for k in ('status', 'df_before', 'df_after', 'actual_available_delta_kib', 'all_approved_paths_absent', 'held_40_unchanged', 'other_temp_trees_unchanged', 'preserved_inputs_unchanged', 'errors')} | {'deleted_count': len(receipt['deleted_bundles']), 'removed_file_count': len(receipt['removed_files']), 'receipt': str(RECEIPT)}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--execute', action='store_true')
    opts = a.parse_args()
    if opts.execute: execute()
    else: prepare()
