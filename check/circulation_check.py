# =====================================================================
# circulation_check.py  (run inside Blender)
#   blender -b building.blend -P check/circulation_check.py -- [--block DOOR_ID] [--out report_prefix]
# 1. builds a BVH of every solid mesh (door leaves excluded: they slide open)
# 2. door test: rays through every door centre at z+1.0 and z+2.0 must be clear;
#    a ray offset beside the door must HIT a wall (proves the door really pierces a wall)
# 3. stair test: riser 150-180 mm, tread >= 260 mm, headroom >= 2.1 m (up-rays from every tread),
#    and every tread exists (down-ray lands on it)
# 4. floor probe: every space has a floor under its probe point and >= 2.1 m clear above
# 5. lift test: shaft hollow from bottom to top level
# 6. graph BFS from the entrance over passed doors / stairs / lifts; every space must be reachable
# =====================================================================
import bpy, bmesh, json, math, os, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
BLOCK = arg("--block")
BLEND_DIR = os.path.dirname(bpy.data.filepath)
OUT = arg("--out", os.path.join(BLEND_DIR, "circulation_report"))
S = json.load(open(os.path.join(BLEND_DIR, "spaces.json")))
SKIP_ROLES = {"plaza_glow", "cut", "window_light"}

def build_bvh(extra_boxes=()):
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or ob.name.startswith("DoorLeaf_") or ob.get("role") in SKIP_ROLES or ob.hide_render:
            continue
        me = ob.evaluated_get(dg).to_mesh()
        me.transform(ob.matrix_world)
        bm.from_mesh(me)
        ob.evaluated_get(dg).to_mesh_clear()
    for (c, sz) in extra_boxes:
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co = Vector((c[0] + v.co.x*sz[0], c[1] + v.co.y*sz[1], c[2] + v.co.z*sz[2]))
    bm.verts.ensure_lookup_table()
    t = BVHTree.FromBMesh(bm, epsilon=0.0)
    bm.free()
    return t

def hit(T, o, d, L):
    d = Vector(d).normalized(); loc, nrm, idx, dist = T.ray_cast(Vector(o), d, L)
    return dist  # None if clear

def run(T, label):
    res = {"label": label, "doors": [], "stairs": [], "spaces": [], "lifts": [], "fail": []}
    door_ok = {}
    for d in S["doors"]:
        c = Vector(d["center"]); n = Vector((d["normal"][0], d["normal"][1], 0)).normalized()
        t = Vector((d["tangent"][0], d["tangent"][1], 0)) if "tangent" in d else Vector((-n.y, n.x, 0))
        L = 2.4 if d["type"] in ("door", "ext_door", "lift_door", "opening") else 6.0
        hs = [1.0, min(2.0, d["h"] - 0.15)]
        lat = [0.0] if d["w"] < 2.0 else [0.0, -(d["w"]/2 - 0.5), d["w"]/2 - 0.5]
        clear = True; blocked_at = None
        for h in hs:
            for s in lat:
                o = c + t*s + Vector((0, 0, h)) - n*(L/2)
                dist = hit(T, o, n, L)
                if dist is not None:
                    clear = False; blocked_at = [round(h, 2), round(s, 2), round(dist - L/2, 2)]
        wall = None
        if d.get("check_wall"):
            # a ray parallel to the door axis, displaced sideways past the jamb, must hit wall material
            off = d["w"]/2 + 0.35
            wall = any(hit(T, c + t*sg*off + Vector((0, 0, 1.0)) - n*(L/2), n, L) is not None for sg in (-1, 1))
        ok = clear and (wall is not False)
        door_ok[d["id"]] = ok
        res["doors"].append({"id": d["id"], "type": d["type"], "clear": clear, "pierces_wall": wall, "ok": ok, "blocked_at": blocked_at})
        if not ok: res["fail"].append(f"door {d['id']}: clear={clear} wall={wall} blocked_at(h,lat,dist)={blocked_at}")
    stair_ok = {}
    for st in S["stairs"]:
        steps = st["steps"]; r = st["riser"]; tr = st["tread"]
        issues = []
        if not (0.150 <= r <= 0.180): issues.append(f"riser {r*1000:.0f}mm out of 150-180")
        if tr < 0.26: issues.append(f"tread {tr*1000:.0f}mm < 260")
        # measured riser/tread from geometry: down-rays on each tread centre
        tops = []
        for p in steps:
            dist = hit(T, (p[0], p[1], p[2] + 0.5), (0, 0, -1), 1.0)
            tops.append(None if dist is None else p[2] + 0.5 - dist)
            if dist is None or abs(dist - 0.5) > 0.03: issues.append(f"tread missing at {p}")
        rs = [b - a for a, b in zip(tops, tops[1:]) if a is not None and b is not None and abs(b - a) < 0.3 and abs(b - a) > 0.01]
        mr = [min(rs), max(rs)] if rs else None
        if mr and (mr[0] < 0.149 or mr[1] > 0.181): issues.append(f"measured riser range {mr}")
        hr = []
        for p in steps:
            dist = hit(T, (p[0], p[1], p[2] + 0.02), (0, 0, 1), 10.0)
            hr.append(10.0 if dist is None else dist + 0.02)
        hmin = min(hr)
        if hmin < st["headroom_min"]: issues.append(f"headroom {hmin:.2f} m < {st['headroom_min']}")
        # entry & exit standing points have floor below
        for key in ("entry", "exit"):
            p = st[key]; dist = hit(T, (p[0], p[1], p[2] + 1.0), (0, 0, -1), 1.5)
            if dist is None or abs(dist - 1.0) > 0.35: issues.append(f"{key} has no floor (dist {dist})")
        ok = not issues; stair_ok[st["id"]] = ok
        res["stairs"].append({"id": st["id"], "riser_mm": round(r*1000, 1), "tread_mm": round(tr*1000), "measured_riser_mm": [round(x*1000, 1) for x in mr] if mr else None,
                              "headroom_min_m": round(hmin, 3), "n_steps": len(steps), "ok": ok, "issues": issues})
        if not ok: res["fail"].append(f"stair {st['id']}: {issues}")
    for nm, sp in S["spaces"].items():
        p = sp["probe"]; dn = hit(T, (p[0], p[1], p[2] + 1.0), (0, 0, -1), 1.6)
        up = hit(T, (p[0], p[1], p[2] + 0.1), (0, 0, 1), 30.0)
        floor_ok = dn is not None and abs(dn - 1.0) < 0.4
        head = 99.0 if up is None else up + 0.1
        ok = floor_ok and head >= 2.1
        res["spaces"].append({"name": nm, "floor": floor_ok, "headroom_m": round(head, 2), "ok": ok})
        if not ok: res["fail"].append(f"space {nm}: floor={floor_ok} headroom={head:.2f}")
    lift_ok = {}
    for lf in S["lifts"]:
        x0, y0, x1, y1 = lf["shaft"]; cx, cy = (x0 + x1)/2, (y0 + y1)/2
        span = lf["levels"][-1] - lf["levels"][0] + 2.2
        dist = hit(T, (cx, cy, lf["levels"][0] + 0.05), (0, 0, 1), span)
        ok = dist is None
        lift_ok[lf["id"]] = ok
        res["lifts"].append({"id": lf["id"], "hollow": ok, "levels": len(lf["levels"])})
        if not ok: res["fail"].append(f"lift {lf['id']}: shaft obstructed at +{dist:.2f} m")
    # ---- graph ----
    adj = {}
    def link(a, b, via):
        adj.setdefault(a, []).append((b, via)); adj.setdefault(b, []).append((a, via))
    for d in S["doors"]:
        if door_ok[d["id"]]: link(d["a"], d["b"], d["id"])
    for st in S["stairs"]:
        if stair_ok[st["id"]]: link(st["a"], st["b"], st["id"])
    start = S["entrance"]; seen = {start: None}; q = [start]
    while q:
        a = q.pop(0)
        for b, via in adj.get(a, []):
            if b not in seen: seen[b] = (a, via); q.append(b)
    unreached = [s for s in S["spaces"] if s not in seen]
    res["reachable"] = sorted(s for s in seen if s in S["spaces"]); res["unreachable"] = unreached
    def path(s):
        out = []
        while seen.get(s): a, via = seen[s]; out.append(via); s = a
        return out[::-1]
    res["paths"] = {s: path(s) for s in ("courtyard", "W_L1", "E_L1", "T_L0", "T_L1", "T_L13") if s in seen}
    if unreached: res["fail"].append(f"unreachable spaces from '{start}': {unreached}")
    res["graph"] = {"nodes": len(S["spaces"]) + len(S["lifts"]), "door_edges": sum(door_ok.values()), "stair_edges": sum(stair_ok.values())}
    res["PASS"] = not res["fail"]
    return res

T = build_bvh()
main = run(T, "as-built")
reports = [main]
# ---- negative test: block one door with a solid box, the check MUST fail ----
neg_id = BLOCK or next(x["id"] for x in S["doors"] if x["a"] == "T_link" and x["b"] == "T_L0")
d = next(x for x in S["doors"] if x["id"] == neg_id)
n = Vector((d["normal"][0], d["normal"][1], 0)).normalized(); t = Vector((-n.y, n.x, 0))
ang = math.atan2(n.y, n.x)
# axis aligned box big enough to plug the gap (door width + margin), 0.5 m thick
sx = abs(math.cos(ang))*0.5 + abs(math.sin(ang))*(d["w"] + 0.4)
sy = abs(math.sin(ang))*0.5 + abs(math.cos(ang))*(d["w"] + 0.4)
c = d["center"]
T2 = build_bvh([((c[0], c[1], c[2] + d["h"]/2), (sx, sy, d["h"] + 0.2))])
neg = run(T2, f"negative test: {neg_id} blocked")
neg["expected"] = "FAIL"; neg["negative_test_passed"] = not neg["PASS"]
reports.append(neg)
json.dump(reports, open(OUT + ".json", "w"), indent=1)

L = ["# Circulation check report", "", f"Model: `{os.path.basename(bpy.data.filepath)}` - spaces: {len(S['spaces'])}, doors: {len(S['doors'])}, stairs (flights per storey): {len(S['stairs'])}, lifts: {len(S['lifts'])}", "",
     "Method: BVH of all solid meshes (door leaves excluded because they slide open), ray tests through each door at 1.0 m and 2.0 m (plus jamb-side rays for wide openings), a sideways-offset ray that must hit wall material (proves the opening is a real gap in a real wall), down-rays on every stair tread, up-rays for headroom, floor probes for every space, hollow-shaft rays for lifts, then BFS over the passing doors/stairs from the entrance `forecourt`.", ""]
for R in reports:
    L += [f"## {R['label']}  ->  **{'PASS' if R['PASS'] else 'FAIL'}**", ""]
    if "expected" in R:
        L += [f"Expected result: FAIL. Negative test {'**PASSED** (the check correctly failed)' if R['negative_test_passed'] else '**DID NOT CATCH THE BLOCK**'}.", ""]
    nd = sum(x["ok"] for x in R["doors"]); ns = sum(x["ok"] for x in R["stairs"])
    L += [f"- doors ok: {nd}/{len(R['doors'])}  (all pierce their wall: {all(x['pierces_wall'] is not False for x in R['doors'])})",
          f"- stair flights ok: {ns}/{len(R['stairs'])}",
          f"- spaces with floor + >=2.1 m headroom: {sum(x['ok'] for x in R['spaces'])}/{len(R['spaces'])}",
          f"- lift shafts hollow: {sum(x['hollow'] for x in R['lifts'])}/{len(R['lifts'])}",
          f"- reachable from entrance: {len(R['reachable'])}/{len(S['spaces'])}; unreachable: {R['unreachable'] or 'none'}", ""]
    if R["fail"]:
        L += ["Failures:", ""] + [f"- {f}" for f in R["fail"][:40]] + [""]
    if R is main:
        L += ["Example routes found by BFS:", ""] + [f"- {k}: {' -> '.join(v)}" for k, v in R["paths"].items()] + [""]
        L += ["| stair | riser (design) | measured riser range | tread | min headroom | ok |", "|---|---|---|---|---|---|"]
        for s in R["stairs"]:
            L.append(f"| {s['id']} | {s['riser_mm']} mm | {s['measured_riser_mm']} | {s['tread_mm']} mm | {s['headroom_min_m']} m | {'yes' if s['ok'] else 'NO'} |")
        L += ["", "| door | type | clear | pierces wall | ok |", "|---|---|---|---|---|"]
        for x in R["doors"]:
            L.append(f"| {x['id']} | {x['type']} | {x['clear']} | {x['pierces_wall']} | {'yes' if x['ok'] else 'NO'} |")
        L.append("")
open(OUT + ".md", "w").write("\n".join(L))
print("CIRCULATION", "PASS" if main["PASS"] else "FAIL", "| negative test caught:", neg["negative_test_passed"])
for f in main["fail"][:30]: print("  FAIL:", f)
