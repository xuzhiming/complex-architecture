# per-column skyline difference (model - ref, metres) for a view, binned every 4 m along the horizontal axis
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare as C
sil, view = sys.argv[1], sys.argv[2]
H = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "params.json")))["global"]["H_total"]
meta = json.load(open(os.path.join(sil, "sil_meta.json"))); mpp = meta["mpp"]
mm = C.load_model(sil, view); g = mm.shape[0] - int(round(meta["ground_from_bottom_m"]/mpp)); mm[g:, :] = False
ys, xs = np.where(mm); cx = (xs.min() + xs.max())/2
rm = C.ref_mask(view, H, mpp, mm.shape, g, cx)
sm = np.clip(C.skyline(mm)*mpp - (mm.shape[0] - g)*mpp, 0, None); sr = np.clip(C.skyline(rm)*mpp - (mm.shape[0] - g)*mpp, 0, None)
cols = np.where((sm > 0) | (sr > 0))[0]
W = mm.shape[1]
for b0 in range(cols.min(), cols.max() + 1, int(4/mpp)):
    c = np.arange(b0, min(b0 + int(4/mpp), cols.max() + 1))
    h = (c.mean() - W/2)*mpp
    d = (sm[c] - sr[c]); print(f"h {h:7.1f}  model {sm[c].mean():6.1f}  ref {sr[c].mean():6.1f}  diff {d.mean():6.2f}  |d| {np.abs(d).mean():5.2f}")
