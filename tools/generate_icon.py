"""Generate original sword artwork as SVG, PNG, multi-size ICO and macOS ICNS."""
from pathlib import Path
from PIL import Image, ImageDraw


def generate(root):
    root = Path(root)
    assets, data = root / 'assets', root / 'botw_manager/data'
    assets.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    shapes = [
        ('rounded', (28, 28, 996, 996), '#101920'),
        ('ellipse', (110, 110, 914, 914), '#1c333d'),
        ('polygon', [(510, 76), (594, 212), (568, 655), (512, 697), (456, 655), (430, 212)], '#83b5c6'),
        ('polygon', [(510, 76), (514, 624), (462, 651), (447, 218)], '#e4f1f5'),
        ('polygon', [(510, 76), (579, 218), (562, 651), (514, 624)], '#b5d4dd'),
        ('polygon', [(510, 110), (520, 218), (515, 601), (505, 601), (501, 218)], '#f5fbfc'),
        ('polygon', [(486, 671), (538, 671), (543, 888), (512, 934), (481, 888)], '#453a75'),
        ('polygon', [(486, 703), (508, 703), (508, 884), (488, 895)], '#8c7bc1'),
        ('polygon', [(462, 639), (360, 574), (284, 605), (418, 711), (512, 685), (606, 711), (740, 605), (664, 574), (562, 639)], '#7161ab'),
        ('polygon', [(360, 574), (284, 605), (418, 666), (462, 639)], '#a295d3'),
        ('polygon', [(664, 574), (740, 605), (606, 666), (562, 639)], '#9284c8'),
        ('polygon', [(512, 604), (561, 657), (512, 716), (463, 657)], '#d8b86c'),
        ('polygon', [(512, 623), (542, 657), (512, 695), (482, 657)], '#6de0cf'),
        ('polygon', [(512, 636), (529, 657), (512, 679), (495, 657)], '#c5fff0'),
        ('polygon', [(483, 884), (541, 884), (557, 914), (512, 951), (467, 914)], '#a295d3'),
        ('polygon', [(512, 905), (538, 916), (512, 939), (486, 916)], '#d8b86c'),
    ]
    image = Image.new('RGBA', (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">']
    for kind, geometry, color in shapes:
        if kind == 'polygon':
            draw.polygon([(x*2, y*2) for x,y in geometry], fill=color)
            points = ' '.join(f'{x},{y}' for x,y in geometry)
            svg.append(f'<polygon points="{points}" fill="{color}"/>')
        elif kind == 'rounded':
            draw.rounded_rectangle(tuple(v*2 for v in geometry), radius=400, fill=color)
            x,y,right,bottom=geometry
            svg.append(f'<rect x="{x}" y="{y}" width="{right-x}" height="{bottom-y}" rx="200" fill="{color}"/>')
        else:
            draw.ellipse(tuple(v*2 for v in geometry), fill=color)
            x,y,right,bottom=geometry
            svg.append(f'<ellipse cx="{(x+right)/2}" cy="{(y+bottom)/2}" rx="{(right-x)/2}" ry="{(bottom-y)/2}" fill="{color}"/>')
    # Original grip detail, rendered from the same geometry in both formats.
    for y in range(743, 877, 28):
        draw.line([(488*2,y*2),(536*2,(y-12)*2)], fill='#a295d3', width=8)
        svg.append(f'<path d="M488 {y}L536 {y-12}" stroke="#a295d3" stroke-width="4"/>')
    svg.append('</svg>')
    (assets/'sword.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8')
    image = image.resize((1024,1024),Image.Resampling.LANCZOS)
    image.save(assets/'sword.png')
    image.resize((256,256),Image.Resampling.LANCZOS).save(data/'app-icon.png')
    image.save(data/'app-icon.ico',sizes=[(s,s) for s in (16,20,24,32,40,48,64,96,128,256)])
    image.save(data/'app-icon.icns')
    print('Generated assets/sword.svg, sword.png and bundled PNG/ICO/ICNS icons.')


if __name__=='__main__':
    generate(Path(__file__).resolve().parents[1])
