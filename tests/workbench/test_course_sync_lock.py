"""OS-owned exchange locks release on process death, without PID guessing."""
import subprocess
import sys
from pathlib import Path

import pytest
from workbench.data.course_sync_lock import exclusive


def test_busy_lock_rejects_another_owner_and_then_releases(tmp_path):
    path=tmp_path/"write.lock"
    with exclusive(path):
        with pytest.raises(ValueError,match="locked"):
            with exclusive(path):
                pytest.fail("second owner entered")
    with exclusive(path):
        pass


def test_process_death_releases_lock_without_deleting_the_file(tmp_path):
    path=tmp_path/"write.lock"
    code="import os,sys;from pathlib import Path;from workbench.data.course_sync_lock import exclusive\nwith exclusive(Path(sys.argv[1])): os._exit(3)"
    result=subprocess.run([sys.executable,"-c",code,str(path)],cwd=Path(__file__).resolve().parents[2],capture_output=True,timeout=10)
    assert result.returncode==3,result.stderr
    assert path.exists()
    with exclusive(path):
        assert path.exists()


def test_exception_releases_ownership(tmp_path):
    path=tmp_path/"write.lock"
    with pytest.raises(RuntimeError):
        with exclusive(path):
            raise RuntimeError("operation failed")
    with exclusive(path):
        pass


def test_public_course_lock_releases_after_process_death(tmp_path):
    from workbench.data.course_sync import course_lock
    code="import os,sys;from workbench.data.course_sync import course_lock\nwith course_lock(sys.argv[1]): os._exit(3)"
    result=subprocess.run([sys.executable,"-c",code,str(tmp_path)],cwd=Path(__file__).resolve().parents[2],capture_output=True,timeout=10)
    assert result.returncode==3,result.stderr
    with course_lock(tmp_path):
        pass
