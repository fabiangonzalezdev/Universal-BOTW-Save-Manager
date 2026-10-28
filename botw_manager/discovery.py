"""Read-only BOTW discovery; every user profile remains a separate candidate."""
from dataclasses import dataclass
from pathlib import Path
import os
import struct
import sys
from .core import VERSIONS, inspect

EXAMPLES = (
    ('Cemu · Wii U', 'mlc01/usr/save/00050000/101c9400|101c9500|101c9300/user/<user>/'),
    ('Ryujinx · Switch', '%APPDATA%/Ryujinx/bis/user/save/<profile>/0/'),
    ('Eden · Switch', '%APPDATA%/eden/nand/user/save/0000000000000000/<user>/01007EF00011E000/'),
    ('yuzu / suyu / Sudachi · Switch', '<emulator-user-folder>/nand/user/save/0000000000000000/<user>/01007EF00011E000/'),
    ('Savage Wind · PC port · Switch format', '<game>/save/save_0/ · save_1/ · …'),
    ('Cemu · Linux / macOS', '~/.local/share/Cemu/mlc01/ · ~/Library/Application Support/Cemu/'),
    ('Switch emulators · Linux / macOS', '~/.local/share/<emulator>/ · ~/.config/Ryujinx/ · ~/Library/Application Support/Ryujinx/'),
    ('Custom / other PC ports', '<selected save folder>/option.sav + 0/game_data.sav; format must be verified before conversion'),
)

@dataclass(frozen=True)
class Candidate:
    path: Path
    kind: str
    platform: str
    format_id: str = 'botw'

def common_roots():
    home=Path.home()
    bases=[Path(os.environ.get('APPDATA',home/'AppData/Roaming'))] if sys.platform=='win32' else [home/'.local/share',home/'.config',home/'Library/Application Support']
    bases += [home/'.var/app/info.cemu.Cemu/data', home/'.var/app/org.ryujinx.Ryujinx/config']
    return [base/name for base in bases for name in ('Cemu','cemu','Ryujinx','ryujinx','eden','Eden','yuzu','suyu','sudachi') if (base/name).is_dir()]

def kind_for(path, platform):
    parts={p.casefold() for p in path.parts}
    if platform=='Wii U' and ('mlc01' in parts or 'cemu' in parts): return 'Cemu'
    if path.name.startswith('save_') and path.parent.name=='save': return 'Savage Wind'
    for kind in ('Ryujinx','Eden','yuzu','suyu','Sudachi'):
        if kind.casefold() in parts: return kind
    return 'Custom'

def scan(roots, max_dirs=50000, max_depth=12):
    """Bounded scan; skip game assets, keys, links and generated backup trees.

    Header prefilter avoids loading unrelated files. Full core validation is
    required before displaying a profile. Never write or choose a profile.
    """
    excluded={'keys','prod.keys','romfs','exefs','extracted','cache','shadercache','games','node_modules','.git','system','registered','contents'}
    stack=[(Path(p).expanduser(),0) for p in roots]
    visited=set();found=[]
    while stack:
        path,depth=stack.pop()
        if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()): continue
        try:
            path=path.resolve()
            if path in visited: continue
            if len(visited)>=max_dirs: raise ValueError('Search limit reached. Select a smaller folder (50,000 directory limit).')
            visited.add(path)
            if (path/'option.sav').is_file() and not (path/'option.sav').is_symlink():
                with (path/'option.sav').open('rb') as f: header=f.read(12)
                if len(header)==12 and any(struct.unpack(e+'III',header)[0] in VERSIONS and struct.unpack(e+'III',header)[1:]==(0xffffffff,1) for e in ('<','>')):
                    try:
                        # Reject links before reading the validated payload.
                        if any(p.is_symlink() for p in path.rglob('*')): continue
                        info=inspect(path)
                        if info['root'].resolve()==path:
                            found.append(Candidate(path,kind_for(path,info['platform']),info['platform']))
                            continue
                    except (ValueError,OSError): pass
            if depth<max_depth:
                for child in path.iterdir():
                    if child.name.casefold() not in excluded and '.ubsm-backup-' not in child.name and child.is_dir():
                        stack.append((child,depth+1))
        except (OSError,PermissionError): continue
    return sorted(found,key=lambda item:str(item.path).casefold())
