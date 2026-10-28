"""Build on the target OS. PyInstaller does not cross-compile."""
from pathlib import Path
import subprocess
import sys
import uuid

root=Path(__file__).resolve().parent
args=[sys.executable,'-m','PyInstaller','--noconfirm','--workpath',str(root/'build'/uuid.uuid4().hex),
      '--onefile','--windowed','--collect-all','tkinterdnd2','--name','Universal-BOTW-Save-Manager',
      '--add-data','botw_manager/data:botw_manager/data']
if sys.platform=='win32':args += ['--icon',str(root/'botw_manager/data/app-icon.ico')]
elif sys.platform=='darwin':args += ['--icon',str(root/'botw_manager/data/app-icon.icns')]
args += ['main.py']
subprocess.run(args,cwd=root,check=True)
