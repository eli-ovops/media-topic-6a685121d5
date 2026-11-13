"""Bounded read-only video-output audit; creates only its own evidence files."""
import os,json,hashlib,subprocess,csv,datetime,stat,collections
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=Path('/Volumes/EXTERNAL/自媒体')
GROUPS={
 'AI唱反调':ROOT/'ai-contrarian-20261019/02_制作/fred-v5',
 'WorkBuddy已取消':ROOT/'workbuddy-test-20261015/flow/04',
 'AI漏斗已发布':ROOT/'ai-funnel-vibe-20261020/04-制作',
 '豆包155旧制作':ROOT/'doubao-app-rejection-20261016/03_制作过程/remotion',
 '独立动效对比':ROOT/'motion-model-comparison-20261013/astra-max/evidence',
}
SKIP={'node_modules','.git','.venv','gate-runtime','toolchain','runtime-cache'}
def now():return datetime.datetime.now().astimezone().isoformat()
def save(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
HC={}
def sha(p):
 s=p.stat();k=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
 if k not in HC:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for z in iter(lambda:f.read(4*1024*1024),b''):h.update(z)
  HC[k]=h.hexdigest()
 return HC[k]
def files(p):
 for dr,ds,fs in os.walk(p,followlinks=False):
  ds[:]=[d for d in ds if not Path(dr,d).is_symlink()]
  for f in fs:yield Path(dr,f)
def du(p):
 r=subprocess.run(['du','-sk',str(p)],capture_output=True,text=True)
 return int(r.stdout.split()[0]) if r.returncode==0 else None
def safe_same(p,body):
 try:return p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(body.encode()).hexdigest()
 except OSError:return False
def source_options(group,bundle,src):
 rel=src.removeprefix('./') if hasattr(src,'removeprefix') else src[2:] if src.startswith('./') else src
 # These are bounded possible roots from the actual render scripts; no source execution.
 roots=[ROOT,bundle.parent,bundle.parent.parent,GROUPS[group],GROUPS[group]/'project',GROUPS[group]/'fred-v5/project']
 return [p/rel for p in roots if '..' not in Path(rel).parts]
rows=[];allfiles=[]
for group,base in GROUPS.items():
 for dr,ds,fs in os.walk(base,followlinks=False):
  p=Path(dr);ds[:]=[d for d in ds if d not in SKIP and not Path(dr,d).is_symlink()]
  if len(p.relative_to(base).parts)>11:ds[:]=[];continue
  kind='webpack-bundle' if p.name=='bundle' or p.name.startswith('bundle-') else 'webpack-cache' if p.name=='webpack' and p.parent.name=='.cache' else None
  if not kind:continue
  ds[:]=[]
  rr={'group':group,'path':str(p),'kind':kind,'allocated_kib':du(p),'logical_bytes':0,'file_count':0,'symlinks':[],'extension_bytes':{},'source_records':[],'public_files':[]}
  ex=collections.Counter()
  for q in files(p):
   s=q.lstat()
   if q.is_symlink():rr['symlinks'].append(str(q));continue
   if not stat.S_ISREG(s.st_mode):continue
   rr['logical_bytes']+=s.st_size;rr['file_count']+=1;ex[q.suffix]+=s.st_size
   allfiles.append({'directory':str(p),'path':str(q),'bytes':s.st_size,'allocated_bytes':s.st_blocks*512,'mtime_ns':s.st_mtime_ns,'device':s.st_dev,'inode':s.st_ino})
  rr['extension_bytes']=dict(ex)
  if kind=='webpack-bundle':
   seen=set()
   for mp in p.glob('*.map'):
    try:m=json.loads(mp.read_text())
    except Exception:continue
    for src,body in zip(m.get('sources',[]),m.get('sourcesContent',[])):
     if 'node_modules' in src or not src.startswith('./') or not isinstance(body,str):continue
     h=hashlib.sha256(body.encode()).hexdigest()
     if (src,h) in seen:continue
     seen.add((src,h));opts=source_options(group,p,src)
     matches=[str(z) for z in opts if safe_same(z,body)]
     rr['source_records'].append({'source':src,'sha256':h,'bytes':len(body.encode()),'exact_preserved_source_paths':matches,'status':'EXACT_SOURCE_PRESENT' if matches else 'PRESERVE_OR_LOCATE_HISTORY_FIRST'})
   pub=p/'public'
   if pub.is_dir() and not pub.is_symlink():
    poss=[p.parent/'public',p.parent.parent/'public',GROUPS[group]/'public',GROUPS[group]/'render-public',GROUPS[group]/'project/public',GROUPS[group]/'fred-v5/project/public']
    for q in files(pub):
     if q.is_symlink() or not q.is_file():continue
     rel=q.relative_to(pub);opts=[a/rel for a in poss if a!=pub]
     h=sha(q);matches=[str(z) for z in opts if z.is_file() and z.stat().st_size==q.stat().st_size and sha(z)==h]
     rr['public_files'].append({'path':str(q),'relative':str(rel),'bytes':q.stat().st_size,'sha256':h,'exact_original_paths':matches,'status':'EXACT_COPY' if matches else 'HOLD_NO_EXACT_ORIGINAL_YET'})
  rows.append(rr)
save('候选目录逐项.json',rows)
with (OUT/'候选目录精确文件清单.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(allfiles[0]) if allfiles else ['path']);w.writeheader();w.writerows(allfiles)
summary=[]
for group in GROUPS:
 for kind in ['webpack-cache','webpack-bundle']:
  a=[r for r in rows if r['group']==group and r['kind']==kind]
  if not a:continue
  summary.append({'group':group,'kind':kind,'directories':len(a),'allocated_kib':sum(r['allocated_kib'] or 0 for r in a),'logical_bytes':sum(r['logical_bytes'] for r in a),'public_exact':sum(sum(z['status']=='EXACT_COPY' for z in r['public_files']) for r in a),'public_held':sum(sum(z['status']!='EXACT_COPY' for z in r['public_files']) for r in a),'source_exact':sum(sum(z['status']=='EXACT_SOURCE_PRESENT' for z in r['source_records']) for r in a),'source_history_unlocated':sum(sum(z['status']!='EXACT_SOURCE_PRESENT' for z in r['source_records']) for r in a)})
save('汇总.json',{'at':now(),'groups':summary,'scope_roots':[str(p) for p in GROUPS.values()],'asset_mutations':0,'scope_excludes_original_libraries':True,'allocation_not_reclaimable_bytes':True})
print(json.dumps(summary,ensure_ascii=False,indent=2))
