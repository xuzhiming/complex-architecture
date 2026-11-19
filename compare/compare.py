"""Silhouette comparison: model ortho silhouettes (known m/px) vs reference elevation sheet panels.
Reference has no dimension lines -> each ref panel is scaled uniformly so its bbox HEIGHT equals params H_total
(ground line anchored, bbox centres aligned horizontally). Width mismatch therefore shows up in the scores."""
import numpy as np, json, os, sys
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
VIEWS = ["front", "rear", "left", "right"]
# v6: the user widened the design in x. The design target is the reference stretched horizontally by
# global.ref_stretch_x in the FRONT/REAR elevations (side elevations unchanged). REF_STRETCH_X=1 -> strict reference.
try:
    _G = json.load(open(os.path.join(os.path.dirname(HERE), "params.json")))["global"]
except Exception:
    _G = {}
STRETCH_X = float(os.environ.get("REF_STRETCH_X", _G.get("ref_stretch_x", 1.0)))
STRETCH_Y = float(os.environ.get("REF_STRETCH_Y", _G.get("ref_stretch_y", 1.0)))   # v7: depth grew with the larger courtyard

# v10: reference panels come from global.ref_dir (the user's crown four-view sheet). The crown zone (global.crown_zone: rows above
# z0, within half_w of the tower axis) is scored against the STRICT (unstretched) panel, re-anchored on the tower axis, so the
# single crescent is fitted at its true proportions while the rest of the front/rear keeps the widened x-stretch target.
try:
    _P = json.load(open(os.path.join(os.path.dirname(HERE), "params.json")))
except Exception:
    _P = {}
REF_DIR = os.path.join(os.path.dirname(HERE), os.environ.get("REF_DIR", _G.get("ref_dir", "compare")))
CZ = _G.get("crown_zone")
TCX = _P.get("tower", {}).get("cx", 0.0)

def load_model(sil_dir, view):
    a = np.asarray(Image.open(os.path.join(sil_dir, f"sil_{view}.png")).convert("RGBA"))[..., 3] > 20
    return a

def ref_mask(view, H_m, mpp, shape, ground_row, cx_px, kx=None, shift_px=0):
    r = np.asarray(Image.open(os.path.join(REF_DIR, f"ref_{view}_sil.png"))) > 127
    h, w = r.shape
    s = (H_m/mpp)/h
    top = kx is None
    if kx is None: kx = STRETCH_X if view in ("front", "rear") else STRETCH_Y
    if top and CZ and view in ("front", "rear") and abs(kx - 1) > 1e-6:
        base = ref_mask(view, H_m, mpp, shape, ground_row, cx_px, kx)
        sg = 1 if view == "front" else -1
        tx = cx_px + sg*TCX/mpp                                   # tower axis column in this view
        strict = ref_mask(view, H_m, mpp, shape, ground_row, cx_px + sg*TCX*(1 - 1/kx)/mpp, 1.0)
        zone = np.zeros(shape, bool)
        r0 = int(round(ground_row - CZ["z0"]/mpp)); c0 = max(0, int(tx - CZ["half_w"]/mpp)); c1 = min(shape[1], int(tx + CZ["half_w"]/mpp))
        zone[:max(0, r0), c0:c1] = True
        return np.where(zone, strict, base)
    nw, nh = max(1, int(round(w*s*kx))), max(1, int(round(h*s)))
    rr = np.asarray(Image.fromarray((r*255).astype(np.uint8)).resize((nw, nh), Image.BILINEAR)) > 127
    out = np.zeros(shape, bool)
    y1 = ground_row; y0 = y1 - nh; x0 = int(round(cx_px - nw/2))
    ys0, xs0 = max(0, y0), max(0, x0); ys1, xs1 = min(shape[0], y1), min(shape[1], x0 + nw)
    out[ys0:ys1, xs0:xs1] = rr[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
    return out

def skyline(m):
    has = m.any(0); top = np.argmax(m, 0)
    return np.where(has, m.shape[0] - top, 0)

def score_view(sil_dir, view, H_m):
    meta = json.load(open(os.path.join(sil_dir, "sil_meta.json"))); mpp = meta["mpp"]
    mm = load_model(sil_dir, view)
    ground_row = mm.shape[0] - int(round(meta["ground_from_bottom_m"]/mpp))
    mm[ground_row:, :] = False
    ys, xs = np.where(mm)
    cx = (xs.min() + xs.max())/2 if len(xs) else mm.shape[1]/2
    rm = ref_mask(view, H_m, mpp, mm.shape, ground_row, cx)
    inter = (mm & rm).sum(); uni = (mm | rm).sum()
    iou = inter/max(uni, 1)
    sm, sr = skyline(mm)*mpp - (mm.shape[0] - ground_row)*mpp, skyline(rm)*mpp - (mm.shape[0] - ground_row)*mpp
    sm = np.clip(sm, 0, None); sr = np.clip(sr, 0, None)
    cols = (sm > 0) | (sr > 0)
    sky = float(np.abs(sm - sr)[cols].mean()) if cols.any() else 0.0
    # 3x3 region XOR fractions over the union bbox
    yy, xx = np.where(mm | rm); y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
    xor = (mm ^ rm)[y0:y1, x0:x1]; H, W = xor.shape
    reg = {}
    for i, vn in enumerate(["high", "mid", "low"]):
        for j, hn in enumerate(["L", "C", "R"]):
            cell = xor[i*H//3:(i + 1)*H//3, j*W//3:(j + 1)*W//3]
            reg[f"{vn}{hn}"] = float(cell.sum())/max(uni, 1)
    mw = (xs.max() - xs.min() + 1)*mpp if len(xs) else 0; mh = (ground_row - ys.min())*mpp if len(ys) else 0
    ry, rx = np.where(rm)
    rw = (rx.max() - rx.min() + 1)*mpp; rh = (ground_row - ry.min())*mpp
    # v11: crown-zone metrics (reported only, score unchanged): rows above crown_zone.z0; skyline error over columns where model or
    # ref rises above z0; IoU of the masks restricted to those rows.
    z0 = (CZ or {}).get("z0", 46.0); r0 = int(round(ground_row - z0/mpp))
    smc, src = np.clip(sm - z0, 0, None), np.clip(sr - z0, 0, None); cc = (smc > 0) | (src > 0)
    c_sky = float(np.abs(smc - src)[cc].mean()) if cc.any() else 0.0
    c_iou = float((mm[:r0] & rm[:r0]).sum()/max((mm[:r0] | rm[:r0]).sum(), 1))
    return {"iou": float(iou), "skyline_err_m": sky, "crown_iou": c_iou, "crown_sky_m": c_sky, "model_wh_m": [round(mw, 2), round(mh, 2)], "ref_wh_m": [round(rw, 2), round(rh, 2)],
            "regions": reg}, mm, rm

def overlay(mm, rm, path):
    img = np.full(mm.shape + (3,), 255, np.uint8)
    img[rm & ~mm] = (230, 60, 60)      # reference only  -> red
    img[mm & ~rm] = (40, 150, 230)     # model only      -> blue
    img[mm & rm] = (120, 120, 120)     # overlap         -> grey
    Image.fromarray(img).save(path)

def side_by_side(sil_dir, view, rm, mm, path, clay_dir=None):
    a = np.where(rm, 60, 255).astype(np.uint8); b = np.where(mm, 60, 255).astype(np.uint8)
    pad = np.full((mm.shape[0], 10), 200, np.uint8)
    Image.fromarray(np.hstack([a, pad, b])).save(path)

def run(sil_dir, H_m, out_dir, tag=""):
    os.makedirs(out_dir, exist_ok=True)
    res = {}
    for v in VIEWS:
        r, mm, rm = score_view(sil_dir, v, H_m)
        res[v] = r
        overlay(mm, rm, os.path.join(out_dir, f"overlay_{v}.png"))
        side_by_side(sil_dir, v, rm, mm, os.path.join(out_dir, f"sbs_{v}.png"))
    res["mean_iou"] = float(np.mean([res[v]["iou"] for v in VIEWS]))
    res["mean_skyline_err_m"] = float(np.mean([res[v]["skyline_err_m"] for v in VIEWS]))
    res["score"] = res["mean_iou"] - 0.01*res["mean_skyline_err_m"]
    # 2x2 overlay sheet
    ims = [Image.open(os.path.join(out_dir, f"overlay_{v}.png")) for v in VIEWS]
    w, h = ims[0].size; S = Image.new("RGB", (2*w, 2*h), "white"); d = ImageDraw.Draw(S)
    for i, (v, im) in enumerate(zip(VIEWS, ims)):
        S.paste(im, ((i % 2)*w, (i//2)*h)); d.text(((i % 2)*w + 10, (i//2)*h + 10), f"{v.upper()}  IoU {res[v]['iou']:.3f}  sky {res[v]['skyline_err_m']:.2f} m", fill=(0, 0, 0))
    S.save(os.path.join(out_dir, "overlay_sheet.png"))
    json.dump(res, open(os.path.join(out_dir, "scores.json"), "w"), indent=1)
    return res

def roof_check(sil_dir, W_m, out_dir):
    """Loose check vs the (oblique) roof plan: scale ref bbox width to params W_total."""
    sheet = np.asarray(Image.open("/workspace/gothic_model/ref/sheet_plans.png").convert("L")).astype(np.float32)
    H, W = sheet.shape; sub = sheet[:int(H*0.30), :W//2]
    m = ndi.binary_fill_holes(ndi.binary_closing(sub < 235, iterations=2))
    lab, n = ndi.label(m); sizes = ndi.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sizes)))
    ys, xs = np.where(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    meta = json.load(open(os.path.join(sil_dir, "sil_meta.json"))); mpp = meta["mpp"]
    mm = np.asarray(Image.open(os.path.join(sil_dir, "sil_top.png")).convert("RGBA"))[..., 3] > 20
    yy, xx = np.where(mm); mm = mm[yy.min():yy.max() + 1, xx.min():xx.max() + 1]
    rr = np.asarray(Image.fromarray((m*255).astype(np.uint8)).resize((mm.shape[1], mm.shape[0]))) > 127
    iou = float((mm & rr).sum()/max((mm | rr).sum(), 1))
    overlay(mm, rr, os.path.join(out_dir, "overlay_roof_loose.png"))
    return {"roof_iou_loose_bbox_fitted": iou}

if __name__ == "__main__":
    sil_dir, H_m, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    r = run(sil_dir, H_m, out); print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != "regions"}) for k, v in r.items()}, indent=1))
    print(roof_check(sil_dir, 0, out))
