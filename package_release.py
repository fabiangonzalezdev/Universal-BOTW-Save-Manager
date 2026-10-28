"""Build a versioned, allowlisted distribution folder and ZIP for any native OS."""
import argparse
import hashlib
from pathlib import Path
import platform
import tempfile
import zipfile
from botw_manager import __version__


def native_platform():
    system=platform.system()
    if system=='Windows':return 'windows-x64'
    if system=='Darwin':return 'macos-arm64'
    return 'linux-x64'


def package(root, target, version=__version__):
    root=Path(root).resolve()
    if target not in ('windows-x64','linux-x64','macos-arm64'):
        raise ValueError('Unsupported release platform')
    # Always package from dist, never from personal backups or working directories.
    stem='Universal-BOTW-Save-Manager'
    if target=='windows-x64':binary=root/'dist'/f'{stem}.exe'
    elif target=='macos-arm64':binary=root/'dist'/f'{stem}.app'
    else:binary=root/'dist'/stem
    versioned=root/'dist'/('v'+version)/binary.name
    if versioned.exists():binary=versioned
    if not binary.exists():raise FileNotFoundError(f'Build the native app first: {binary}')
    bundle_name=f'{stem}-v{version}-{target}'
    release=root/'releases'/f'v{version}'
    release.mkdir(parents=True,exist_ok=True)
    archive=release/f'{bundle_name}.zip'
    members=[]
    if binary.is_dir():
        members.extend((p,p.relative_to(binary.parent)) for p in sorted(binary.rglob('*')) if p.is_file())
    else:
        members.append((binary,Path(binary.name)))
    for name in ('README.md','README.es.md','LICENSE','THIRD_PARTY_NOTICES.md','RELEASE_NOTES.md'):
        members.append((root/name,Path(name)))
    for p in sorted((root/'docs').rglob('*')):
        if p.is_file() and p.suffix in ('.md','.svg','.png'):
            members.append((p,p.relative_to(root)))
    for p in sorted((root/'botw_manager/data').glob('LICENSE.*')):
        members.append((p,Path('third-party-licenses')/p.name))
    for name in ('sword.svg','sword.png'):
        p=root/'assets'/name
        if p.exists():members.append((p,Path('assets')/name))
    for p,rel in members:
        if p.is_symlink() or not p.is_file():raise ValueError(f'Unexpected release entry: {p}')
        if p.suffix in ('.sav','.keys') or rel.name in ('otp.bin','seeprom.bin'):
            raise ValueError('A private save or key cannot be packaged')
    with tempfile.NamedTemporaryFile(dir=release,suffix='.zip',delete=False) as f:
        tmp=Path(f.name)
    try:
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
            for p,rel in members:z.write(p,(Path(bundle_name)/rel).as_posix())
            z.writestr(f'{bundle_name}/VERSION.txt',f'{stem}\nVersion: {version}\nPlatform: {target}\n')
        tmp.replace(archive)
    finally:
        if tmp.exists():tmp.unlink()
    checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.sha256').write_text(checksum+'  '+archive.name+'\n',encoding='utf-8')
    tag=f'v{version}'
    url=f'https://github.com/fabiangonzalezdev/{stem}/releases/tag/{tag}'
    readme=f'''# {stem} {tag}

[GitHub release / Release en GitHub]({url})

## Upload / Subir

Attach each platform ZIP and its matching `.sha256` file to this GitHub release. Source code, build scripts and this README belong in Git; binaries are excluded by `.gitignore`.

Adjuntá el ZIP de cada plataforma y su archivo `.sha256` al release de GitHub. El código, los scripts y este README van en Git; los binarios quedan excluidos.

| Platform / Plataforma | Archive / Archivo |
|---|---|
| Windows x64 | `{stem}-{tag}-windows-x64.zip` |
| Linux x64 | `{stem}-{tag}-linux-x64.zip` |
| macOS ARM64 | `{stem}-{tag}-macos-arm64.zip` |

Only packages that have actually been built are present locally. GitHub Actions creates the other native builds.
Solo están disponibles localmente los paquetes ya compilados. GitHub Actions genera los demás builds nativos.

Extract the ZIP and open the application inside its versioned folder. Windows uses `{stem}.exe`; macOS uses the `.app` bundle. No Python installation is required for packaged builds. Binaries are unsigned; validate converted saves in-game.

Extraé el ZIP y abrí la aplicación dentro de la carpeta de esa versión. Windows usa `{stem}.exe`; macOS usa el paquete `.app`. No hace falta instalar Python. Los binarios no tienen firma digital; validá los saves dentro del juego.

## Verify / Verificar

Windows PowerShell: `Get-FileHash .\\{stem}-{tag}-windows-x64.zip -Algorithm SHA256`

Compare the result with the accompanying `.sha256` file. / Compará el resultado con el archivo `.sha256` correspondiente.
'''
    (release/'README.md').write_text(readme,encoding='utf-8')
    print(archive)
    print('SHA256',checksum)
    return archive


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--platform',choices=['windows-x64','linux-x64','macos-arm64'],default=native_platform())
    args=parser.parse_args()
    package(Path(__file__).parent,args.platform)
