import json,os,sys,time,tempfile
from pathlib import Path
sys.path.insert(0,str(next(parent for parent in Path(__file__).resolve().parents if (parent / 'pyproject.toml').is_file())))
from tests.workbench.test_course_sync_receive import make_course,workspace
from workbench.data import course_sync as sync
results=[]
for count in (100,300,1000):
 with tempfile.TemporaryDirectory(prefix='lessonkit-sync-pilot-') as name:
  root=Path(name);os.environ['LESSONKIT_WB_HOME']=str(root/'registry')
  left=make_course(root/'left');right=make_course(root/'right')
  left.connect().executemany('INSERT INTO knowledge_points(kp_id,body) VALUES(?,?)',[(f'math-kp-{i}','content '*125) for i in range(count)]);left.commit()
  began=time.perf_counter();sync.export_course(left,workspace(left),root/'bundle');export=time.perf_counter()-began
  inspection=sync.inspect_exchange(right,workspace(right),root/'bundle')
  began=time.perf_counter();result=sync.apply_exchange(right,workspace(right),inspection);receive=time.perf_counter()-began
  item={'rows':count,'export_seconds':round(export,3),'receive_seconds':round(receive,3),'status':result['status'],'state_bytes':(right.root/'.lessonkit/course-sync/state.json').stat().st_size}
  results.append(item);print(json.dumps(item),flush=True)
  Path('tmp/agent-runs/receive-scaling-pilot.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
  left.close();right.close()
