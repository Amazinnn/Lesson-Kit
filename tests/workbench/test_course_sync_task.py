"""Native task construction without touching the host task registry."""
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from workbench.bridge import course_sync_task

NS={"t":"http://schemas.microsoft.com/windows/2004/02/mit/task"}

def test_native_definition_binds_command_and_directory(tmp_path):
    root=tmp_path / "课程 & source";root.mkdir()
    executable=tmp_path / "Python folder/python.exe"
    xml=course_sync_task.definition(root, executable, "DOMAIN\\user")
    task=ET.fromstring(xml)
    assert task.find("t:Actions/t:Exec/t:Command",NS).text == str(executable)
    assert task.find("t:Actions/t:Exec/t:Arguments",NS).text == "-m workbench.cli.main course-sync --all-configured sync"
    assert task.find("t:Actions/t:Exec/t:WorkingDirectory",NS).text == str(root.resolve())
    assert task.find("t:Triggers/t:TimeTrigger/t:Repetition/t:Interval",NS).text == "PT1H"
    assert task.find("t:Principals/t:Principal/t:LogonType",NS).text == "InteractiveToken"

def test_task_creation_uses_xml_hidden_timeout_and_removes_temporary_file(tmp_path, monkeypatch):
    calls=[]
    def run(args,**kwargs):
        path=Path(args[args.index("/XML")+1]);assert path.exists()
        calls.append((args,kwargs,path))
        return subprocess.CompletedProcess(args,0,b"OK",b"")
    monkeypatch.setattr(course_sync_task.subprocess,"run",run)
    monkeypatch.setattr(course_sync_task.sys,"platform","win32")
    result=course_sync_task.manage("install","test",tmp_path)
    assert result.returncode==0
    assert calls[0][1]["timeout"]==30
    assert not calls[0][2].exists()
    assert "/TR" not in calls[0][0]

@pytest.mark.parametrize("action,flag",[("enable","/ENABLE"),("disable","/DISABLE"),("remove","/Delete")])
def test_lifecycle(action,flag,tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(course_sync_task.sys,"platform","win32")
    monkeypatch.setattr(course_sync_task.subprocess,"run",lambda args,**kw: calls.append(args) or subprocess.CompletedProcess(args,0,b"",b""))
    course_sync_task.manage(action,"test",tmp_path)
    assert flag in calls[0]


def test_preflight_uses_the_selected_checkout():
    root=Path(__file__).resolve().parents[2]
    assert course_sync_task.preflight(root)["working_directory"]==str(root)
