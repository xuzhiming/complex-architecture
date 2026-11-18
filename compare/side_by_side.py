# compare/final/side_by_side.png : reference sheet crop | model clay ortho | silhouette overlay, per elevation, with scores
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(R)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
sc = json.load(open('compare/final/scores.json')); H = 360; rows = []
def crop_nonwhite(im):
    a = np.asarray(im.convert('L')); ys, xs = np.where(a < 245); return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
def fit(im, h): return im.resize((int(im.width*h/im.height), h), Image.LANCZOS)
for v in ['front', 'rear', 'left', 'right']:
    rows.append((v, *(fit(crop_nonwhite(Image.open(p).convert('RGB')), H) for p in
                      (f'compare/ref_{v}_crop.png', f'renders/{v}.png', f'compare/final/overlay_{v}.png'))))
c1 = max(r[1].width for r in rows); c2 = max(r[2].width for r in rows); c3 = max(r[3].width for r in rows)
S = Image.new('RGB', (c1 + c2 + c3 + 80, len(rows)*(H + 50) + 50), 'white'); d = ImageDraw.Draw(S)
d.text((20, 10), "REFERENCE (sheet crop)", fill='black', font=f); d.text((c1 + 40, 10), "MODEL (clay ortho)", fill='black', font=f)
d.text((c1 + c2 + 60, 10), "OVERLAY  red=ref only  blue=model only", fill='black', font=f)
for i, (v, ref, mod, ov) in enumerate(rows):
    y = 50 + i*(H + 50); s = sc['views'][v] if 'views' in sc else sc[v]
    d.text((20, y), f"{v.upper()}  IoU {s['iou']:.3f}  skyline err {s['skyline_err_m']:.2f} m", fill=(30, 30, 120), font=f)
    S.paste(ref, (20, y + 30)); S.paste(mod, (c1 + 40, y + 30)); S.paste(ov, (c1 + c2 + 60, y + 30))
S.save('compare/final/side_by_side.png'); print('side_by_side.png', S.size)
