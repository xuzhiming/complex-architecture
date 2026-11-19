"""Auto-compare loop: build silhouettes from params -> score vs reference -> adjust the params that drive the
regions with the largest XOR error -> rebuild ... Logs every round to compare_log.md."""
import json, os, sys, copy, subprocess, time, shutil
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare
ROOT = "/workspace/gothic_model"
WORK = os.path.join(ROOT, "compare", "work"); os.makedirs(WORK, exist_ok=True)
LOG = os.environ.get("COMPARE_LOG", os.path.join(ROOT, "compare_log.md"))
ROUNDS = int(os.environ.get("ROUNDS", "6"))

def sh_canopies(p, side, d):
    for c in p["canopies"]:
        if (side == "W" and c["cx"] < -5) or (side == "E" and c["cx"] > 5): c["cx"] += d if side == "E" else -d
def _mass(p, name, key, d, lo=None):
    for m in p["masses"]:
        if m["name"] == name: m[key] = m[key] + d if lo is None else max(lo, m[key] + d)
def _cres_shift(p, ax, d):
    for q in p["crescent"]["pts"][1:]: q[ax] += d
def _set(p, path, d, lo=None, hi=None):
    *a, k = path.split("."); o = p
    for x in a: o = o[x]
    v = o.get(k, 1.0 if k in ("spread", "rise", "d_scale") else 0.0) + d
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    o[k] = v
KNOBS = {
 "tower.cx":          (1.0,  ["highC", "highR", "highL", "midC"], lambda p, d: _set(p, "tower.cx", d)),
 "tower.cy":          (1.0,  ["highC", "highR", "highL", "midR"], lambda p, d: _set(p, "tower.cy", d)),
 "tower.r_scale":     (0.03, ["highC", "midC"], lambda p, d: [dr.__setitem__(0, dr[0]*(1 + d)) for dr in p["tower"]["drums"]] and p["tower"].__setitem__("crown_R", p["tower"]["crown_R"]*(1 + d))),
 "tower.crown_z":     (0.6,  ["highC", "highL", "highR"], lambda p, d: _set(p, "tower.crown_z", d)),
 "podium.deck_z":     (0.5,  ["lowL", "lowC", "lowR"], lambda p, d: (_set(p, "podium.deck_top", d), _set(p, "podium.deck_bot", d), _set(p, "podium.deck_edge_z", d))),
 "podium.deck_half_w":(1.0,  ["lowL", "lowR"], lambda p, d: _set(p, "podium.deck_half_w", d)),
 "podium.deck_half_d":(1.0,  ["lowL", "lowR"], lambda p, d: _set(p, "podium.deck_half_d", d)),
 "canopy_scale":      (0.04, ["midL", "midR", "lowL", "lowR"], lambda p, d: _set(p, "canopy_scale", d)),
 "canopies.z_shift":  (0.8,  ["midL", "midR"], lambda p, d: [c.__setitem__("z", c["z"] + d) for c in p["canopies"]]),
 "crescent.dz":       (0.8,  ["highC", "highL", "highR"], lambda p, d: _set(p, "crescent.dz", d)),
 "crescent.spread":   (0.05, ["highC", "highL", "highR"], lambda p, d: _set(p, "crescent.spread", d, 0.6, 1.4)),
 "crescent.rise":     (0.06, ["highC", "highL", "highR"], lambda p, d: _set(p, "crescent.rise", d, 0.6, 1.4)),
 "crescent.d_scale":  (0.10, ["highC", "highL", "highR"], lambda p, d: _set(p, "crescent.d_scale", d, 0.5, 1.6)),
 "crescent.dx":       (0.8,  ["highC", "highL"], lambda p, d: _cres_shift(p, 0, d)),
 "crescent.dy":       (0.8,  ["highC", "highR"], lambda p, d: _cres_shift(p, 1, d)),
 "mass_scale":        (0.06, ["midC", "midL", "midR"], lambda p, d: _set(p, "mass_scale", d)),
 "masses.top_C":      (1.0,  ["highC", "midC"], lambda p, d: _mass(p, "M_C", "z1", d)),
 "masses.top_E":      (1.0,  ["midR", "highR", "midL"], lambda p, d: _mass(p, "M_E", "z1", d)),
 "masses.r_WT":       (0.6,  ["highL", "midL", "highR"], lambda p, d: _mass(p, "M_WT", "r", d, 2.0)),
 "columns.flare_r":   (0.6,  ["lowL", "lowR"], lambda p, d: _set(p, "columns.flare_r", d, 4.0)),
 "columns.base_r":    (0.3,  ["lowL", "lowR"], lambda p, d: _set(p, "columns.base_r", d, 1.0)),
 "columns.flare_z0":  (0.8,  ["lowL", "lowR"], lambda p, d: _set(p, "columns.flare_z0", d, 6.0, 19.0)),
 "canopies.west_dx":  (1.0,  ["midL", "lowL", "midR"], lambda p, d: sh_canopies(p, "W", d)),
 "canopies.east_dx":  (1.0,  ["midR", "lowR", "midL"], lambda p, d: sh_canopies(p, "E", d)),
}

def evaluate(params, tag):
    d = os.path.join(WORK, tag); os.makedirs(d, exist_ok=True)
    pp = os.path.join(d, "params.json"); json.dump(params, open(pp, "w"), indent=1)
    env = dict(os.environ, MODE="sil", PARAMS=pp, SIL_DIR=os.path.join(d, "sil"), OUTDIR=d)
    r = subprocess.run(["blender", "-b", "-P", os.path.join(ROOT, "build.py")], env=env, capture_output=True, text=True, timeout=900)
    if "SIL OK" not in r.stdout:
        return {"score": -1, "error": r.stdout[-2000:] + r.stderr[-2000:]}, d
    res = compare.run(os.path.join(d, "sil"), params["global"]["H_total"], os.path.join(d, "cmp"))
    return res, d

def region_totals(res):
    tot = {}
    for v in compare.VIEWS:
        for k, x in res[v]["regions"].items():
            # mirror horizontal labels for rear/right so that L/R refer to the same building side as front/left
            tot[k] = tot.get(k, 0) + x
    return tot

def fmt(res):
    return " | ".join(f"{v} {res[v]['iou']:.3f}/{res[v]['skyline_err_m']:.2f}m" for v in compare.VIEWS) + " || crown " + \
        " | ".join(f"{v} {res[v].get('crown_iou', 0):.3f}/{res[v].get('crown_sky_m', 0):.2f}m" for v in compare.VIEWS)

def main():
    base = json.load(open(os.path.join(ROOT, "params.json")))
    if not os.path.exists(os.path.join(ROOT, "params_initial.json")):
        json.dump(base, open(os.path.join(ROOT, "params_initial.json"), "w"), indent=1)
    steps = {k: v[0] for k, v in KNOBS.items()}; tries = {}
    best, bd = evaluate(base, "r00_base")
    pre = open(os.environ["COMPARE_PREFIX"]).read() + "\n\n" if os.environ.get("COMPARE_PREFIX") else ""
    log = [pre + "# Silhouette compare log" + (" (v5 tuning loop)" if pre else ""), "",
           "Reference: `ref/sheet_elevations.png` (4 elevation panels). The sheets carry **no dimension lines**, so each reference panel",
           "is scaled uniformly until its silhouette bbox height equals `global.H_total` (ground lines anchored, bbox centres aligned).",
           "Model silhouettes are true orthographic renders at 0.2 m/px. Score = mean IoU - 0.01 x mean skyline error (m).",
           "Each round: the 3x3 XOR-error regions (summed over the 4 views) are ranked; knobs that drive the worst regions are tried at +/- step",
           "(parallel builds); the best improving candidate is accepted, otherwise those knob steps are halved.", "",
           f"## Round 0 (initial params)", f"- mean IoU **{best['mean_iou']:.4f}**, mean skyline err **{best['mean_skyline_err_m']:.2f} m**, score {best['score']:.4f}",
           f"- per view (IoU/skyline): {fmt(best)}", ""]
    open(LOG, "a" if os.environ.get("APPEND_LOG") else "w").write("\n".join(log))
    cur = copy.deepcopy(base)
    for rnd in range(1, ROUNDS + 1):
        tot = region_totals(best)
        worst = sorted(tot, key=tot.get, reverse=True)[:3]
        EXC = set(filter(None, os.environ.get("KNOB_EXCLUDE", "").split(",")))
        cands = sorted([k for k, v in KNOBS.items() if set(v[1]) & set(worst) and k not in EXC], key=lambda k: (tries.get(k, 0), -len(set(KNOBS[k][1]) & set(worst))))[:int(os.environ.get("CANDS", "6"))]
        for k in cands: tries[k] = tries.get(k, 0) + 1
        jobs = []
        for k in cands:
            for sgn in (1, -1):
                p = copy.deepcopy(cur); KNOBS[k][2](p, sgn*steps[k]); jobs.append((k, sgn*steps[k], p))
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=4) as ex:
            outs = list(ex.map(lambda j: evaluate(j[2], f"r{rnd:02d}_{j[0].replace('.', '_')}_{'p' if j[1] > 0 else 'm'}"), jobs))
        tried = []
        bi, bs = None, best["score"]
        for (k, d, p), (res, dd) in zip(jobs, outs):
            tried.append(f"  - `{k}` {d:+.3f}: score {res['score']:.4f}" + (f" (IoU {res['mean_iou']:.4f}, sky {res['mean_skyline_err_m']:.2f} m)" if res['score'] > 0 else " (build failed)"))
            if res["score"] > bs + 5e-4: bi, bs = (k, d, p, res, dd), res["score"]
        lines = [f"## Round {rnd}", f"- worst regions: {', '.join(f'{w} ({tot[w]:.3f})' for w in worst)}", f"- candidates ({len(jobs)} builds, {time.time() - t0:.0f} s):"] + tried
        if bi:
            k, d, p, res, dd = bi; cur, best, bd = p, res, dd
            lines += [f"- **accepted** `{k}` {d:+.3f} -> mean IoU **{res['mean_iou']:.4f}**, skyline **{res['mean_skyline_err_m']:.2f} m**, score {res['score']:.4f}",
                      f"- per view: {fmt(res)}"]
        else:
            for k in cands: steps[k] *= 0.5
            lines += ["- no improvement -> halved steps of tried knobs"]
        open(LOG, "a").write("\n" + "\n".join(lines) + "\n")
        print("\n".join(lines), flush=True)
    json.dump(cur, open(os.path.join(ROOT, "params.json"), "w"), indent=1)
    fin = os.path.join(ROOT, "compare", "final"); shutil.rmtree(fin, ignore_errors=True); shutil.copytree(os.path.join(bd, "cmp"), fin)
    roof = compare.roof_check(os.path.join(bd, "sil"), cur["global"]["W_total"], fin)
    open(LOG, "a").write(f"\n## Final\n- mean IoU **{best['mean_iou']:.4f}**, mean skyline error **{best['mean_skyline_err_m']:.2f} m**, score {best['score']:.4f}\n"
                         f"- per view: {fmt(best)}\n- roof plan loose check (oblique sheet, bbox-fitted, indicative only): IoU {roof['roof_iou_loose_bbox_fitted']:.3f}\n"
                         f"- overlays: `compare/final/overlay_sheet.png` (red = reference only, blue = model only, grey = overlap)\n- tuned params written back to `params.json` (start values kept in `params_initial.json`)\n")
if __name__ == "__main__": main()
