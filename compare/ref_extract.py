"""Extract binary silhouettes of the 4 elevations from the reference sheet.
Sheet has no dimension lines: each panel is cropped to the building, ground line removed;
alignment is done by bbox (width -> params overall width)."""
import numpy as np, json, sys
from PIL import Image
from scipy import ndimage as ndi
SHEET = "/workspace/gothic_model/ref/sheet_elevations.png"
im = np.asarray(Image.open(SHEET).convert("L")).astype(np.float32)
H, W = im.shape
out = {}
quads = {"front": (0, 0), "rear": (0, 1), "left": (1, 0), "right": (1, 1)}
for name, (qy, qx) in quads.items():
    sub = im[qy*H//2:(qy+1)*H//2, qx*W//2:(qx+1)*W//2]
    h, w = sub.shape
    # ground line: row with the longest run of dark pixels
    dark = sub < 120
    rows = dark.sum(1)
    gl = int(np.argmax(rows[: int(h*0.97)]))
    m = sub < 235                     # non-white = building
    m[gl - 1:, :] = False             # drop ground line + label
    m = ndi.binary_closing(m, iterations=2)
    m = ndi.binary_fill_holes(m)
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.where(sizes > 0.002*m.size)[0])
    ys, xs = np.where(keep)
    y0, y1, x0, x1 = ys.min(), gl, xs.min(), xs.max() + 1
    crop = keep[y0:y1, x0:x1]
    Image.fromarray((crop*255).astype(np.uint8)).save(f"ref_{name}_sil.png")
    Image.fromarray(sub[y0:y1, x0:x1].astype(np.uint8)).save(f"ref_{name}_crop.png")
    out[name] = {"ground_row": gl, "bbox_px": [int(x0), int(y0), int(x1), int(y1)], "w_px": int(x1 - x0), "h_px": int(y1 - y0),
                 "aspect_w_over_h": round((x1 - x0)/(y1 - y0), 3)}
    print(name, out[name])
json.dump(out, open("ref_measure.json", "w"), indent=1)
