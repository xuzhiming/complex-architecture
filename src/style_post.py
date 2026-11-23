# v14 post-process for the stylised renders (system python: numpy + Pillow):
# chromatic softness (radial R/B offset), gentle bloom-softening, film grain, vignette; then the style_vs_ref sheet.
#   python3 src/style_post.py [renders_dir]      reads style_<view>_raw.png -> style_<view>.png ; ref/style_abstract_v14.png (local only)
import os, sys, json
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(H, "renders")
CY = json.load(open(os.path.join(H, "params.json")))["style"]["cycles"]
rng = np.random.default_rng(14)
def post(src, dst):
    im = Image.open(src).convert("RGB"); w, h = im.size; a = np.asarray(im).astype(np.float32) / 255
    k = CY["chroma_px"] * w / 2400                       # radial chromatic offset (px at the frame edge)
    def scaled(ch, s):
        c = Image.fromarray((ch*255).astype(np.uint8)); sw, sh = int(round(w*s)), int(round(h*s))
        c = c.resize((sw, sh), Image.BICUBIC); l, t = (sw - w)//2, (sh - h)//2
        return np.asarray(c.crop((l, t, l + w, t + h))).astype(np.float32)/255
    s = 1 + 2*k/w
    a = np.stack([scaled(a[..., 0], s), a[..., 1], scaled(a[..., 2], 1/s if s > 1 else 1)], -1)
    soft = np.asarray(Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(w/320))).astype(np.float32)/255
    a = 1 - (1 - a)*(1 - 0.18*soft)                      # screen a soft copy: painterly glow, lifts the haze slightly
    yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w/2)/(w/2), (yy - h/2)/(h/2))
    a *= (1 - 0.32*np.clip(r - 0.45, 0, 1)**1.6)[..., None]
    g = rng.normal(0, CY["grain"], (h, w, 1)).astype(np.float32); a = a + g*(0.35 + 0.65*(1 - a.mean(-1, keepdims=True)))
    Image.fromarray((np.clip(a, 0, 1)*255).astype(np.uint8)).save(dst); print("POST", dst, w, h)
out = []
for v in ("front", "aerial", "courtyard"):
    src = os.path.join(D, f"style_{v}_raw.png")
    if os.path.exists(src): post(src, os.path.join(D, f"style_{v}.png")); out.append(v)
ref = os.path.join(H, "ref", "style_abstract_v14.png")           # the user's reference: local comparison sheet only (never in the repo)
if os.path.exists(ref) and "front" in out:
    a = Image.open(ref).convert("RGB"); b = Image.open(os.path.join(D, "style_front.png")).convert("RGB")
    W = 1200; a = a.resize((W, int(a.size[1]*W/a.size[0]))); b = b.resize((W, int(b.size[1]*W/b.size[0])))
    sh = Image.new("RGB", (2*W + 30, max(a.size[1], b.size[1]) + 60), (12, 12, 24)); sh.paste(a, (10, 50)); sh.paste(b, (W + 20, 50))
    d = ImageDraw.Draw(sh)
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except Exception: f = None
    d.text((14, 14), "reference (abstract concept image)", fill=(230, 230, 240), font=f)
    d.text((W + 24, 14), "v14 Cycles style render (render_style.py, front)", fill=(230, 230, 240), font=f)
    sh.save(os.path.join(D, "style_vs_ref.png")); print("POST sheet", os.path.join(D, "style_vs_ref.png"))
