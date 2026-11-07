import json,subprocess,sys,tempfile,time,xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
from workbench.bridge import course_sync_task as task
ns={"t":task.NAMESPACE}
report={"kind":"isolated real native task lifecycle; no real course configuration"}
# Remove only the exact unintended test task whose creation was observed this run.
query=subprocess.run(["schtasks","/Query","/TN","LessonKit Course Sync","/XML"],capture_output=True)
if query.returncode==0:
 xml=ET.fromstring(query.stdout.decode("utf-8-sig",errors="replace"))
 date=xml.find("t:RegistrationInfo/t:Date",ns).text
 command=xml.find("t:Actions/t:Exec/t:Command",ns).text
 args=xml.find("t:Actions/t:Exec/t:Arguments",ns).text
 if date=="2026-11-07T14:43:25" and args==task.ARGUMENTS:
  removed=subprocess.run(["schtasks","/Delete","/TN","LessonKit Course Sync","/F"],capture_output=True)
  report["unintended_test_task"]={"created":date,"command":command,"arguments":args,"removed":removed.returncode==0}
 else: report["unintended_test_task"]={"removed":False,"reason":"identity changed; not touched"}
name="LessonKit Sync Acceptance "+str(uuid4())
original=task.definition
with tempfile.TemporaryDirectory(prefix="lessonkit-native-probe-") as folder:
 folder=Path(folder); marker=folder/"result.json"; runner=folder/"invoke.py"
 runner.write_text("import os,sys,json,pathlib\nos.environ['LESSONKIT_WB_HOME']="+repr(str(folder/"registry"))+"\nsys.path.insert(0,"+repr(str(root))+")\nfrom workbench.cli.main import main\ncode=main(['course-sync','--all-configured','sync'])\npathlib.Path("+repr(str(marker))+").write_text(json.dumps({'exit':code,'cwd':os.getcwd(),'source':__import__('workbench').__file__}))\n",encoding="utf-8")
 def definition(source):
  xml=ET.fromstring(original(source));xml.find("t:Actions/t:Exec/t:Arguments",ns).text=subprocess.list2cmdline([str(runner)])
  return ET.tostring(xml,encoding="unicode")
 task.definition=definition
 try:
  report["runtime"]=task.preflight(root)
  for action in ["install","install","disable","enable"]:
   result=task.manage(action,name,root);report.setdefault("actions",[]).append({"action":action,"exit":result.returncode,"output":(result.stdout+result.stderr).decode(errors="replace")[:400]})
   if result.returncode:raise RuntimeError("native lifecycle failure")
  started=subprocess.run(["schtasks","/Run","/TN",name],capture_output=True);report["run_exit"]=started.returncode
  deadline=time.monotonic()+35
  while not marker.exists() and time.monotonic()<deadline:time.sleep(1)
  report["execution"]=json.loads(marker.read_text()) if marker.exists() else {"status":"timeout"}
 finally:
  removed=task.manage("remove",name,root);report["cleanup_exit"]=removed.returncode
  task.definition=original
(root/'tmp/agent-runs/native-task-probe.json').write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
