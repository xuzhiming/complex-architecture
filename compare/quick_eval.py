# quick single evaluation of params.json (or PARAMS) -> scores + zoom overlays in compare/work/<tag>
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_loop as L
tag = sys.argv[1] if len(sys.argv) > 1 else "quick"
P = json.load(open(os.environ.get("PARAMS", os.path.join(L.ROOT, "params.json"))))
res, d = L.evaluate(P, tag)
if res.get("score", -1) < 0: print(res.get("error")); sys.exit(1)
print(f"{tag}: IoU {res['mean_iou']:.4f} sky {res['mean_skyline_err_m']:.2f} score {res['score']:.4f} | {L.fmt(res)}")
print("regions", {k: round(v, 3) for k, v in sorted(L.region_totals(res).items(), key=lambda x: -x[1])[:5]})
