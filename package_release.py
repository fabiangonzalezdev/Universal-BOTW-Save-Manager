"""Package local Windows build without saves, keys or development files."""
from pathlib import Path
import hashlib
import zipfile

root=Path(__file__).parent
out=root/'dist'/'Universal-BOTW-Save-Manager-windows-x64.zip'
files=['dist/Universal-BOTW-Save-Manager.exe','README.md','README.es.md','LICENSE','THIRD_PARTY_NOTICES.md',
       'docs/FORMAT.md','botw_manager/data/LICENSE.hashes']
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:
        p=root/f
        z.write(p,p.name if f.startswith('dist/') else f)
checksum=hashlib.sha256(out.read_bytes()).hexdigest()
out.with_suffix('.sha256').write_text(checksum+'  '+out.name+'\n',encoding='utf-8')
print(out)
print('SHA256',checksum)
