# zoomed overlay with a metre grid (horizontal = image-right world axis: front +x, rear -x, left +y, right -y)
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import compare as C
sil = sys.argv[1]; H = float(sys.argv[2]); z0 = float(sys.argv[3]) if len(sys.argv) > 3 else 35; out = sys.argv[4] if len(sys.argv) > 4 else "/tmp/zoom"
for v in C.VIEWS:
    r, mm, rm = C.score_view(sil, v, H)
    img = np.full(mm.shape + (3,), 255, np.uint8); img[rm & ~mm] = (230, 60, 60); img[mm & ~rm] = (40, 150, 230); img[mm & rm] = (150, 150, 150)
    gr = 490; top = int(gr - 82/0.2); bot = int(gr - z0/0.2)
    im = Image.fromarray(img[top:bot, 75:775]).resize((1400, (bot - top)*2), Image.NEAREST); d = ImageDraw.Draw(im)
    for hm in range(-70, 71, 5):
        x = ((hm/0.2 + 425) - 75)*2; d.line([(x, 0), (x, im.height)], fill=(0, 0, 0) if hm % 10 == 0 else (200, 200, 200), width=1)
        if hm % 10 == 0: d.text((x + 2, 2), str(hm), fill=(0, 0, 0))
    for zm in range(int(z0), 83, 5):
        y = ((gr - zm/0.2) - top)*2; d.line([(0, y), (im.width, y)], fill=(0, 0, 0) if zm % 10 == 0 else (200, 200, 200))
        d.text((2, y + 1), f"z{zm}", fill=(0, 0, 0))
    d.text((700, 2), f"{v} IoU {r['iou']:.3f}", fill=(0, 0, 0)); im.save(f"{out}_{v}.png")
