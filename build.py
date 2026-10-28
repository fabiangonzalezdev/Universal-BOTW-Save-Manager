"""Build on the target OS. PyInstaller does not cross-compile."""
from pathlib import Path
import subprocess
import sys
import uuid

root=Path(__file__).parent
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--workpath',str(root/'build'/uuid.uuid4().hex),'--onefile','--windowed',
                '--name','Universal-BOTW-Save-Manager','--add-data','botw_manager/data:botw_manager/data',
                'main.py'],cwd=root,check=True)
