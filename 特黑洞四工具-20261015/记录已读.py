from pathlib import Path
import json
D=Path(__file__).parent
P=D/'完整阅读覆盖.json'
def record(notes,batch):
 d=json.loads(P.read_text()); covered={}
 for r in d['files']:
  rel=r['path'].split('/.agents/skills/',1)[1]
  if rel in notes:
   r.update(status='full_text_read',read_ranges=[[1,len(Path(r['path']).read_text().splitlines())]],method='model read full tool output; not keyword scan',summary=notes[rel],batch=batch)
   covered[r['sha256']]=r['path']
 for r in d['files']:
  if r['status']=='unread' and r['sha256'] in covered:r.update(status='exact_hash_duplicate',read_via=covered[r['sha256']],batch=batch)
 d['counts']={x:sum(r['status']==x for r in d['files']) for x in sorted(set(r['status'] for r in d['files']))};d['status']='进行中，未全读';P.write_text(json.dumps(d,ensure_ascii=False,indent=2));print(d['counts'])
if __name__=='__main__':record(json.loads((D/'批次笔记.json').read_text()),'B01')
