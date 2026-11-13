"""Archive gate and exact-list deletion for the user-approved remaining 40 bundles."""
from pathlib import Path
import argparse, csv, datetime, hashlib, json, os, runpy, stat, subprocess

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[1]
TEMP = Path('/var/folders/1q/6mf7kw2j1z19q1f9dydq60wh0000gn/T')
H = runpy.run_path(str(ROOT / 'delete_approved56.py'))
stamp, digest, tree = H['stamp'], H['digest'], H['tree']
runtime_check, df, anchored_parent = H['runtime_check'], H['df'], H['anchored_parent']
now, write_json = H['now'], H['write_json']
PLAN_PATH = ROOT / 'held40-preservation-plan.json'
EVIDENCE_PATH = ROOT / 'held40-review-evidence.json'
PREFLIGHT = ROOT / 'held40-cleanup-preflight.json'
VERIFIED = ROOT / 'held40-archive-verification.json'
RECEIPT = ROOT / 'held40-deletion-receipt.json'
PLAN = json.loads(PLAN_PATH.read_text())
EVIDENCE = json.loads(EVIDENCE_PATH.read_text())
ARCHIVE = Path(PLAN['proposed_archive_directory'])
PATHS = [r['absolute_path'] for r in PLAN['reviewed_bundle_paths']]
assert len(PATHS) == len(set(PATHS)) == 40
assert set(PATHS) == {r['absolute_path'] for r in csv.DictReader((ROOT / '\u6682\u755940\u5305.csv').open())}
assert set(PATHS) == {b['path'] for b in EVIDENCE['bundles']}

def filesystem_inventory(root):
    """Metadata-only protected tree; symlinks are recorded but never followed."""
    result = {'.': {'stat': stamp(root)}}
    for base, ds, fs in os.walk(root, followlinks=False):
        for name in sorted(ds + fs):
            p = Path(base) / name
            e = {'stat': stamp(p)}
            if p.is_symlink(): e['symlink_target'] = os.readlink(p)
            result[str(p.relative_to(root))] = e
    return result

def protected_snapshot():
    projects = sorted({b['project'] for b in EVIDENCE['bundles']})
    protected = {str(Path(proj) / name): filesystem_inventory(Path(proj) / name)
                 for proj in projects for name in ('src', 'public')}
    library = WORK / '\u8d44\u4ea7\u5e93/FredTalk'
    protected[str(library)] = filesystem_inventory(library)
    indexes = {}
    for p in [library / 'manifest.json', library / 'README.md',
              WORK / 'Fred\u4ed8\u8d39\u8d44\u6599\u5168\u7ad9\u5b66\u4e60-20261016/README.md']:
        indexes[str(p)] = {'stat': stamp(p), 'sha256': digest(p)}
    for c in PLAN['current_build_reference']:
        p = Path(c['source'])
        assert digest(p) == c['sha256']
        indexes[str(p)] = {'stat': stamp(p), 'sha256': c['sha256']}
    return {'trees': protected, 'indexes': indexes}

def check_protected(pre):
    return (all(filesystem_inventory(Path(p)) == t for p, t in pre['protected']['trees'].items())
            and all(stamp(Path(p)) == e['stat'] and digest(Path(p)) == e['sha256']
                    for p, e in pre['protected']['indexes'].items()))

def prepare():
    assert not PREFLIGHT.exists(), 'PREFLIGHT_EXISTS_REVIEW_BEFORE_REPEAT'
    assert not ARCHIVE.exists(), 'ARCHIVE_ALREADY_EXISTS'
    assert ARCHIVE.parent.resolve() == ARCHIVE.parent, 'ARCHIVE_PARENT_ALIAS'
    projects = sorted({b['project'] for b in EVIDENCE['bundles']})
    out = {'started_at': now(), 'authorization': {
        'user_instruction': '\u90a3\u5c31\u6309\u8fd9\u4e2a\u65b9\u6848\uff0c\u5148\u628a\u5386\u53f2\u6e90\u7801\u3001\u914d\u7f6e\u548c\u9700\u8981\u4fdd\u7559\u7684\u7d20\u6750\u5355\u72ec\u5f52\u6863\uff0c\u6838\u9a8c\u901a\u8fc7\u540e\u518d\u5220\u9664\u8fd940\u4e2a\u4e34\u65f6\u5305\u3002\u539f\u5de5\u7a0b\u548c\u7ec4\u4ef6\u5e93\u522b\u52a8\uff0c\u6700\u540e\u544a\u8bc9\u6211\u5b9e\u9645\u91ca\u653e\u4e86\u591a\u5c11\u7a7a\u95f4\u3002',
        'exact_paths_csv': str(ROOT / '\u6682\u755940\u5305.csv'),
        'paths_csv_sha256': digest(ROOT / '\u6682\u755940\u5305.csv'),
        'condition': 'Archive and verify first; delete only the exact approved 40 paths after PASS'},
        'plan_sha256': digest(PLAN_PATH), 'review_evidence_sha256': digest(EVIDENCE_PATH),
        'archive_directory': str(ARCHIVE), 'archive_absent_before': True, 'targets': [],
        'protected': protected_snapshot(), 'preserved_originals': {}}
    for n, b in enumerate(EVIDENCE['bundles']):
        p = Path(b['path'])
        assert p.parent == TEMP and not p.is_symlink() and p.resolve() == TEMP.resolve() / p.name
        t = tree(p)
        assert {rel: e['stat'] for rel, e in t.items()} == b['before_inventory'], ('TARGET_METADATA_CHANGED', str(p))
        expected_files = {e['path']: e['sha256'] for e in b['artifact_files'] + b['public_files']}
        actual_files = {str(p / rel) for rel, e in t.items() if stat.S_ISREG(e['stat'][2])}
        assert set(expected_files) == actual_files, ('FILE_SET_CHANGED', str(p))
        for rel, e in t.items():
            if stat.S_ISREG(e['stat'][2]):
                e['sha256'] = digest(p / rel)
                assert e['sha256'] == expected_files[str(p / rel)], ('FILE_HASH_CHANGED', str(p / rel))
        for e in b['public_files']:
            original = Path(e['original'])
            assert original.resolve() == original and not original.is_symlink()
            assert digest(original) == e['original_sha256'], ('PRESERVED_ORIGINAL_CHANGED', str(original))
            out['preserved_originals'][str(original)] = {'stat': stamp(original), 'sha256': e['original_sha256']}
        out['targets'].append({'path': str(p), 'tree': t, 'project': b['project']})
        if (n+1) % 8 == 0: print('preflight verified', n+1, '/ 40', flush=True)
    out['other_temp_trees'] = {str(p): tree(p) for p in TEMP.glob('remotion-webpack-bundle-*') if str(p) not in PATHS}
    out['runtime_check'] = runtime_check(PATHS, projects)
    out['completed_at'] = now()
    write_json(PREFLIGHT, out)
    print(json.dumps({'preflight':'PASS','targets':40,'protected_originals':len(out['preserved_originals']),
                      'other_temp_roots':len(out['other_temp_trees']),'file':str(PREFLIGHT)}),flush=True)

def verify_archive():
    pre = json.loads(PREFLIGHT.read_text())
    assert pre['plan_sha256'] == digest(PLAN_PATH)
    manifest_path = ARCHIVE / 'archive-manifest.json'
    m = json.loads(manifest_path.read_text())
    assert m['status'] == 'ARCHIVED_STATIC_DEPENDENCY_CHECK_PASSED'
    assert m['plan_sha256'] == pre['plan_sha256']
    assert m['logical_counts'] == {'source_versions':53,'json_versions':30,'snapshot_mappings':40,'incomplete_media_unique_files':6,'current_build_reference_files':6,'current_source_supplemental_files':2}
    assert not m['unresolved_static_dependencies']
    expected = {str(manifest_path)}
    for e in m['files']:
        p = ARCHIVE / e['relative_path']
        assert p.is_relative_to(ARCHIVE) and p.resolve() == p and not p.is_symlink()
        assert p.stat().st_size == e['bytes'] and digest(p) == e['sha256'], ('ARCHIVE_FILE_MISMATCH', str(p))
        expected.add(str(p))
    actual = {str(ARCHIVE / rel) for rel, e in tree(ARCHIVE).items() if stat.S_ISREG(e['stat'][2])}
    assert actual == expected, 'UNLISTED_ARCHIVE_FILES'
    for e in PLAN['source_objects'] + PLAN['incomplete_media_evidence']:
        assert digest(Path(e['proposed_path'])) == e['sha256']
    for e in PLAN['current_build_reference']:
        assert digest(Path(e['proposed_path'])) == e['sha256']
    for e in m['supplemental_source_files']:
        assert digest(Path(e['archive_path'])) == e['sha256'] == digest(Path(e['source']))
    assert len(m['supplemental_dependency_resolutions']) == 1
    assert all(Path(e['archive_path']).is_file() for e in m['supplemental_dependency_resolutions'])
    for e in PLAN['json_objects']:
        assert digest(Path(e['proposed_path'])) == e['structured_sha256']
        assert digest(Path(e['proposed_raw_expression_path'])) == e['raw_expression_sha256']
    for snap in PLAN['snapshots']:
        archived = json.loads(Path(snap['proposed_snapshot_path']).read_text())
        assert archived['original_snapshot'] == snap
        assert len(archived['source_archive_paths']) == len(snap['source_mapping'])
        assert len(archived['json_archive_paths']) == len(snap['json_mapping'])
    assert check_protected(pre), 'PROTECTED_TREES_CHANGED'
    assert all(stamp(Path(p)) == e['stat'] and digest(Path(p)) == e['sha256'] for p,e in pre['preserved_originals'].items())
    assert all(tree(Path(t['path'])) == {k:{'stat':v['stat']} for k,v in t['tree'].items()} for t in pre['targets'])
    du = subprocess.run(['du','-sk',str(ARCHIVE)],capture_output=True,text=True,check=True)
    result = {'status':'PASS','verified_at':now(),'archive_directory':str(ARCHIVE),
              'archive_manifest':str(manifest_path),'archive_manifest_sha256':digest(manifest_path),
              'listed_file_count':len(m['files']),'archive_total_file_count':len(actual),
              'logical_counts':m['logical_counts'],'archive_logical_bytes':sum(Path(p).stat().st_size for p in actual),
              'archive_allocated_kib':int(du.stdout.split()[0]),'protected_inputs_unchanged':True,
              'static_dependency_check':'PASS','build_or_render_performed':False,'all_40_targets_unchanged':True,
              'plan_sha256':pre['plan_sha256'],'deleted_count':0}
    write_json(VERIFIED,result)
    print(json.dumps(result,ensure_ascii=False),flush=True)

def remove_targets():
    assert not RECEIPT.exists(), 'RECEIPT_EXISTS_DO_NOT_REPEAT'
    pre = json.loads(PREFLIGHT.read_text())
    verify_archive()
    verified = json.loads(VERIFIED.read_text())
    assert verified['status'] == 'PASS' and pre['plan_sha256'] == digest(PLAN_PATH)
    assert digest(ROOT / '\u6682\u755940\u5305.csv') == pre['authorization']['paths_csv_sha256']
    assert check_protected(pre)
    assert all(tree(Path(p)) == inv for p, inv in pre['other_temp_trees'].items())
    for target in pre['targets']:
        assert tree(Path(target['path']), hashes=True) == target['tree'], ('LAST_CONTENT_CHECK_CHANGED',target['path'])
    live = runtime_check(PATHS, sorted({t['project'] for t in pre['targets']}))
    result = {'started_at':now(),'authorization':pre['authorization'],'archive_verification_file':str(VERIFIED),
              'archive_verification_sha256':digest(VERIFIED),'archive_manifest_sha256':verified['archive_manifest_sha256'],
              'preflight_sha256':digest(PREFLIGHT),'runtime_check':live,'deleted_bundles':[],
              'removed_files':[],'removed_directories':[],'errors':[],'df_before':df()}
    write_json(RECEIPT,result)
    try:
        for target in pre['targets']:
            p, inv = Path(target['path']), target['tree']
            assert str(p) in PATHS and p.parent == TEMP and p.resolve() == TEMP.resolve() / p.name
            assert tree(p) == {k:{'stat':v['stat']} for k,v in inv.items()}
            rootfd = os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:
                s = os.fstat(rootfd)
                assert [s.st_dev,s.st_ino] == inv['.']['stat'][:2]
                for rel in sorted(r for r,e in inv.items() if r!='.' and stat.S_ISREG(e['stat'][2])):
                    fd = anchored_parent(rootfd,rel,inv)
                    try:
                        s = os.stat(Path(rel).name,dir_fd=fd,follow_symlinks=False)
                        assert [s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns] == inv[rel]['stat']
                        os.unlink(Path(rel).name,dir_fd=fd)
                        result['removed_files'].append({'path':str(p/rel),'bytes':s.st_size,'sha256':inv[rel]['sha256']})
                    finally: os.close(fd)
                for rel in sorted((r for r,e in inv.items() if r!='.' and stat.S_ISDIR(e['stat'][2])),key=lambda r:len(Path(r).parts),reverse=True):
                    fd = anchored_parent(rootfd,rel,inv)
                    try:
                        s = os.stat(Path(rel).name,dir_fd=fd,follow_symlinks=False)
                        assert [s.st_dev,s.st_ino] == inv[rel]['stat'][:2]
                        os.rmdir(Path(rel).name,dir_fd=fd)
                        result['removed_directories'].append(str(p/rel))
                    finally: os.close(fd)
            finally: os.close(rootfd)
            assert stamp(p)[:2] == inv['.']['stat'][:2]
            os.rmdir(p)
            result['removed_directories'].append(str(p))
            result['deleted_bundles'].append(str(p))
            write_json(RECEIPT,result)
    except BaseException as e:
        result['errors'].append(repr(e))
    finally:
        result['df_after'] = df()
        result['completed_at'] = now()
        result['all_40_paths_absent'] = all(not os.path.lexists(p) for p in PATHS)
        result['protected_trees_and_indexes_unchanged'] = check_protected(pre)
        result['other_temp_trees_unchanged'] = all(tree(Path(p))==inv for p,inv in pre['other_temp_trees'].items())
        result['preserved_originals_unchanged'] = all(stamp(Path(p))==e['stat'] and digest(Path(p))==e['sha256'] for p,e in pre['preserved_originals'].items())
        result['archive_unchanged'] = digest(ARCHIVE/'archive-manifest.json') == verified['archive_manifest_sha256']
        assert result['df_before']['filesystem']==result['df_after']['filesystem']
        result['actual_available_delta_kib'] = result['df_after']['available_kib']-result['df_before']['available_kib']
        result['status'] = 'COMPLETED' if (len(result['deleted_bundles'])==40 and not result['errors'] and
             all(result[k] for k in ('all_40_paths_absent','protected_trees_and_indexes_unchanged','other_temp_trees_unchanged','preserved_originals_unchanged','archive_unchanged'))) else 'PARTIAL_REQUIRES_REVIEW'
        write_json(RECEIPT,result)
        print(json.dumps({k:result[k] for k in ('status','df_before','df_after','actual_available_delta_kib','errors',
           'all_40_paths_absent','protected_trees_and_indexes_unchanged','other_temp_trees_unchanged','preserved_originals_unchanged','archive_unchanged')}|
           {'deleted_count':len(result['deleted_bundles']),'removed_file_count':len(result['removed_files']),'receipt':str(RECEIPT)},ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['prepare','verify','delete'])
    args=parser.parse_args()
    {'prepare':prepare,'verify':verify_archive,'delete':remove_targets}[args.phase]()
