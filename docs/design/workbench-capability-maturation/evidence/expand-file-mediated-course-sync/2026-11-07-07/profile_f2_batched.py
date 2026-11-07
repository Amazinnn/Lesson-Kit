import base64
"""One F2-scale diagnostic run, not a twenty-run/p95 acceptance benchmark."""
import json,os,sqlite3,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=next(parent for parent in Path(__file__).resolve().parents if (parent/'pyproject.toml').is_file())
sys.path.insert(0,str(ROOT))
from workbench.data import course_sync,active_practice,practice_sets
from workbench.data.pool import Pool
OUT=ROOT/'tmp/agent-runs/f2-batched-profile.json'
report={'kind':'single F2 diagnostic; not p95 acceptance','phases':{},'fixture':{'chapters':20,'knowledge_points':1000,'problems':10000,'papers':100,'attempts':10000,'unfinished':30,'learning_files':500,'attachment_bytes':100*1024*1024}}
def save():OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def mark(name,start):
 report['phases'][name]=round(time.perf_counter()-start,3);save();print(name,report['phases'][name],flush=True)
def workspace(pool):return {'name':'bench','path':str(pool.root),'db':'course.db','active_course':'dmath'}
def counts(pool):
 names=[row[0] for row in pool.connect().execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'") if row[0] not in {'course_sync_checkpoint','course_sync_units'}]
 return {name:pool.connect().execute(f'SELECT count(*) FROM "{name}"').fetchone()[0] for name in names}
with tempfile.TemporaryDirectory(prefix='lessonkit-f2-batched-profile-') as folder:
 root=Path(folder);os.environ['LESSONKIT_WB_HOME']=str(root/'registry')
 pools=[]
 try:
  started=time.perf_counter()
  for name in ('a','b'):
   course=root/name;course.mkdir()
   built=subprocess.run([sys.executable,str(ROOT/'pipeline/scripts/create-tables.py'),'--db',str(course/'course.db')],cwd=ROOT,capture_output=True,text=True)
   if built.returncode:raise RuntimeError(built.stderr)
   pools.append(Pool(course,course/'course.db','dmath','ch01'))
  left,right=pools
  conn=left.connect()
  kps=[f'dmath-ch{i//50+1:02d}-kp-{i+1:04d}' for i in range(1000)]
  conn.executemany('INSERT INTO knowledge_points(kp_id,knowledge_item,knowledge_type,importance,body) VALUES(?,?,?,?,?)',[(key,f'知识点 {key} $P(A\\mid B)$','concept-property','core','定义 **原文**\n\n$$x^2+y^2=z^2$$\n\n|条件|结论|\n|---|---|\n|A|B|') for key in kps])
  problems=[f'dmath-ch{i//500+1:02d}-prob-{i+1:05d}' for i in range(10000)]
  conn.executemany('INSERT INTO problems(problem_id,kp_ids,problem_text,solution,problem_type,source_kind) VALUES(?,?,?,?,?,?)',[(key,json.dumps([kps[i//10]]),f'题目 {i+1}：证明 $x<y$。\n\n保留 **中文** 与 & < >。','$x=1$','calculation','textbook') for i,key in enumerate(problems)])
  conn.executemany('INSERT INTO problem_attempts(problem_id,status,answer_text,note) VALUES(?,?,?,?)',[(key,'wrong',f'原始作答 {i+1}：$x=2$','未被标准答案替换') for i,key in enumerate(problems)])
  left.commit()
  papers=[]
  for i in range(100):papers.append(practice_sets.create_saved(left,f'卷 {i+1} **复习** $P(A)$',problems[i*100:(i+1)*100]))
  for i,paper in enumerate(papers[:30]):
   current=active_practice.start_saved(left,paper['practice_set_id'],reveal_timing='on_submit')
   active_practice.save_draft(left,current['execution_id'],0,{'answer':f'未提交草稿 {i+1} $x$'})
  learning=left.root/'.lessonkit/learning';learning.mkdir(parents=True)
  for i in range(500):(learning/f'note-{i+1:04d}.md').write_text(f'# 总结 {i+1}\n\n误解与续接。$P(A\\mid B)$\n',encoding='utf-8')
  attachments=left.root/'attachments';attachments.mkdir()
  block=bytes(range(256))*4096
  for i in range(100):(attachments/f'original-{i+1:03d}.bin').write_bytes(block)
  config=left.root/'.lessonkit/course-sync/config.json';config.parent.mkdir(parents=True,exist_ok=True);config.write_text(json.dumps({'managed_paths':['attachments']}),encoding='utf-8')
  report['source_counts']=counts(left);mark('fixture',started)
  started=time.perf_counter();exported=course_sync.export_course(left,workspace(left),root/'bundle');report['export_status']=exported['status'];report['asset_count']=exported['assets'];mark('export',started)
  started=time.perf_counter();inspection=course_sync.inspect_exchange(right,workspace(right),root/'bundle');report['inspection_errors']=inspection['errors'];mark('initial_check',started)
  started=time.perf_counter();received=course_sync.apply_exchange(right,workspace(right),inspection);report['receive_status']=received['status'];report['receive_failures']=received['failed'];report['received_counts']=counts(right);report['table_counts_equal']=report['source_counts']==report['received_counts'];mark('receive',started)
  started=time.perf_counter();again=course_sync.inspect_exchange(right,workspace(right),root/'bundle');report['repeat_changes']=len(again['changes']);report['repeat_outgoing']=len(again['outgoing']);report['repeat_errors']=again['errors'];mark('repeat_check',started)
  files=course_sync.read_exchange(root/'bundle')['assets']; mismatches=[]; checked=0; total_bytes=0
  for asset in files.values():
   if asset['kind']=='file' and not asset.get('deleted'):
    expected=base64.b64decode(asset['content']['data']); target=right.root/asset['content']['path']; checked+=1;total_bytes+=len(expected)
    if not target.is_file() or target.read_bytes()!=expected:mismatches.append(asset['content']['path'])
  report['file_byte_check']={'checked':checked,'bytes':total_bytes,'mismatches':mismatches};report['repeat_unchanged']=again['unchanged'];save()
 except Exception as exc:
  report['error']={'type':type(exc).__name__,'message':str(exc)};save();raise
 finally:
  for pool in pools:pool.close()
