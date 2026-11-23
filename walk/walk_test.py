"""Headless-Chrome walk test.
Drives the web preview with real WASD key events (plus yaw steering through the test hook, standing in for mouse-look),
along: forecourt -> arch/tunnel -> courtyard -> gallery -> west wing (link, hall, core) -> back -> gallery ring ->
tower link -> tower lobby -> stair A up to L1 -> lift 0 up to L3 -> exit on L3.
Records the trajectory, checks every movement segment for wall penetration (BVH ray between consecutive samples at
knee and chest height), detects getting stuck, checks auto-doors were open when passed, takes checkpoint screenshots.
v13: + auto-door coverage (every door in spaces.json except open archways -> 2 animated leaves in the page) and a scripted
pass through >= 10 doors of every type (exterior, gallery, interior, upper floor, tower, lift) logging open-on-approach,
crossing open fraction, and close-after-leaving; + a fly-mode door check (camera proximity).
usage: python3 walk/walk_test.py [--url http://localhost:8765/index.html]"""
import asyncio, json, math, os, sys, time
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
URL = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else "http://localhost:8765/index.html"
OUT = HERE
S = json.load(open(os.path.join(HERE, "..", "web", "spaces.json")))
D = {d["id"]: d for d in S["doors"]}
def did(a, b):   # door id by the pair of spaces it joins (ids are renumbered when the plan changes)
    return next(d["id"] for d in S["doors"] if {d["a"], d["b"]} == {a, b})
_cg = [d for d in S["doors"] if {d["a"], d["b"]} == {"courtyard", "gallery"} and d["center"][1] > 0]
D_CG = min(_cg, key=lambda d: d["center"][0])["id"]
ST = {s["id"]: s for s in S["stairs"]}
GAP_MIN = 0.7                                           # v13: min physical leaf gap when crossed (capsule 2R = 0.6 m + 0.1)
LEAF_TYPES = ("door", "ext_door", "lift_door")          # door types that must be auto doors; "opening"/"open" are archways
LEAFED = [d for d in S["doors"] if d["type"] in LEAF_TYPES]
def crossings(a, b):
    """doors whose plane the move a->b crossed inside the door width (Blender coords)"""
    out = []
    for d in LEAFED:
        c, n, tg = d["center"], d["normal"], d["tangent"]
        if abs(a[2] - c[2]) > 1.2 or math.hypot(b[0] - c[0], b[1] - c[1]) > 3: continue
        sa = (a[0] - c[0])*n[0] + (a[1] - c[1])*n[1]; sb = (b[0] - c[0])*n[0] + (b[1] - c[1])*n[1]
        if sa*sb < 0:
            f = sa/(sa - sb); px, py = a[0] + (b[0] - a[0])*f, a[1] + (b[1] - a[1])*f
            if abs((px - c[0])*tg[0] + (py - c[1])*tg[1]) < d["w"]/2 + 0.2: out.append(d["id"])
    return out
# v13 scripted door pass: >= 10 doors across all types (by space pair, so renumbering does not break it)
PASS_DOORS = [did("forecourt", "W_vest"), did("forecourt", "E_vest"), did("gallery", "W_link"), did("gallery", "E_link"),
              did("W_link", "W_hall"), did("W_hall", "W_core"), did("E_room_s", "E_room_n"), did("W_hall_L1", "W_room_n_L1"),
              did("T_link", "T_L0"), did("W_core", "W_lift"), did("E_core_L1", "E_lift"), did("T_L2", "T_lift0"), did("E_link", "E_hall")]
LF = {l["id"]: l for l in S["lifts"]}

def through(did, k=1.6, rev=False):
    d = D[did]; c, n = d["center"], d["normal"]; s = -1 if rev else 1
    pa, pb = S["spaces"][d["a"]]["probe"], S["spaces"][d["b"]]["probe"]     # orient a -> b
    if (pb[0] - pa[0])*n[0] + (pb[1] - pa[1])*n[1] < 0: s = -s
    return [(c[0] - s*n[0]*k, c[1] - s*n[1]*k, c[2]), (c[0] + s*n[0]*k, c[1] + s*n[1]*k, c[2])]

KX = json.load(open(os.path.join(HERE, "..", "params.json")))["courtyard"].get("kx", 1.0)   # v7: elliptical courtyard
def arc(cx, cy, r, a0, a1, n, z=0.0):   # r = x semi-axis (gallery probe offset); y semi-axis = r / KX
    return [(cx + r*math.cos(math.radians(a0 + (a1 - a0)*i/n)), cy + r/KX*math.sin(math.radians(a0 + (a1 - a0)*i/n)), z) for i in range(n + 1)]

# ---- route (Blender coords, z = floor level) ; ("shot", name) = checkpoint screenshot ; ("lift", level) ----
cc = S["spaces"]["courtyard"]["probe"]; gal_r = abs(S["spaces"]["gallery"]["probe"][0] - cc[0])
sa = ST["T_stairA_0"]; steps = sa["steps"]
lift0 = LF["T_lift0"]; lx0, ly0, lx1, ly1 = lift0["shaft"]
a_d07 = math.degrees(math.atan2(D[D_CG]["center"][1] - cc[1], (D[D_CG]["center"][0] - cc[0])/KX))
a_d12 = math.degrees(math.atan2(D[did("gallery", "T_link")]["center"][1] - cc[1], (D[did("gallery", "T_link")]["center"][0] - cc[0])/KX))
hx = S["spaces"]["W_hall"]["probe"][0]; wcx = S["spaces"]["W_core"]["probe"][0]   # wing positions come from the plan
fy = D[did("forecourt", "portal_tunnel")]["center"][1]   # portal face y (moves with the podium depth)
ROUTE = [("start", (0, fy - 12, 0), 0.0), ("shot", "01_forecourt"),
         (0, fy + 0.5, 0), ("shot", "02_arch"), (0, fy + 9, 0), ("shot", "03_tunnel"), (0, cc[1] - 10, 0), (0, cc[1] - 2, 0), ("shot", "04_courtyard"),
         (cc[0] - 8, cc[1] + 4, 0), *through(D_CG), ("shot", "05_gallery"),
         *arc(cc[0], cc[1], gal_r, a_d07, 180, 3)[1:], *through(did("gallery", "W_link"), 1.0), ("shot", "06_W_link_door"),
         *through(did("W_link", "W_hall"), 1.0), (hx, 10, 0), (hx, 15.5, 0), ("shot", "07_W_hall"),
         *through(did("W_hall", "W_core"), 1.3), (wcx, 20.5, 0), ("shot", "08_W_core"),
         *through(did("W_hall", "W_core"), 1.3, rev=True), (hx, 10, 0), (hx, cc[1], 0),
         *through(did("W_link", "W_hall"), 1.0, rev=True), *through(did("gallery", "W_link"), 1.0, rev=True),
         *arc(cc[0], cc[1], gal_r, 180, a_d12 + 6, 8)[1:], ("shot", "09_gallery_ring"),
         *through(did("gallery", "T_link"), 1.0), *through(did("T_link", "T_L0"), 1.6), ("shot", "10_tower_lobby"),
         (sa["entry"][0], sa["entry"][1] - 1.5, 0), (steps[0][0], sa["entry"][1], 0),
         *[tuple(p) for p in steps[:12:3]], tuple(steps[11]), tuple(steps[12]), ("shot", "11_stair_landing"),
         *[tuple(p) for p in steps[13::3]], tuple(steps[-1]), (sa["exit"][0], sa["exit"][1], sa["z1"]), (sa["exit"][0], sa["exit"][1] - 1.8, sa["z1"]), ("shot", "12_tower_L1"),
         ((lx0 + lx1)/2, ly0 - 1.2, 4.5), ((lx0 + lx1)/2, (ly0 + ly1)/2, 4.5), ("lift", 13.5), ("shot", "13_in_lift_L3"),
         ((lx0 + lx1)/2, ly0 - 2.0, 13.5), ((lx0 + lx1)/2 - 2.5, ly0 - 3.5, 13.5), ("shot", "14_tower_L3")]

async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path="/usr/bin/google-chrome",
                                     args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await br.new_page(viewport={"width": 960, "height": 540})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(URL + "?test=1")
        await pg.wait_for_function("window.__walk && window.__walk.ready", timeout=240000)
        W = "window.__walk"
        # sanity: the penetration detector must see a wall between the forecourt and the closed west room
        sanity = await pg.evaluate(f"{W}.raySegment([0,{fy - 10},1.0],[{S['spaces']['W_room_s']['probe'][0]},{S['spaces']['W_room_s']['probe'][1]},1.0])")
        traj, events, pen, stuck, doorpass = [], [], [], [], []
        t0 = time.time()
        async def st(): return await pg.evaluate(f"{W}.state()")
        async def shot(name):
            await pg.evaluate(f"{W}.render()"); path = os.path.join(OUT, f"cp_{name}.png")
            await pg.screenshot(path=path); s = await st(); events.append({"shot": name, "at": [round(s['x'], 2), round(s['y'], 2), round(s['z'], 2)]})
        prev = None
        async def sample(tag=""):
            nonlocal prev
            s = await st(); s["t"] = round(time.time() - t0, 2); traj.append(s)
            if prev is not None:
                for h in (0.5, 1.3):
                    a = [prev["x"], prev["y"], prev["z"] + h]; b = [s["x"], s["y"], s["z"] + h]
                    hit = await pg.evaluate(f"{W}.raySegment({json.dumps(a)},{json.dumps(b)})")
                    if hit is not None:
                        pen.append({"t": s["t"], "from": a, "to": b, "hit_at": hit})
                for dd in crossings((prev["x"], prev["y"], prev["z"]), (s["x"], s["y"], s["z"])):
                    info = await pg.evaluate(f"{W}.door({json.dumps(dd)})")
                    doorpass.append({"door": dd, "open": round(info["t"], 2) if info else -1, "gap_m": round(info["gap"], 2) if info else -1, "t": s["t"]})
            prev = s; return s
        ok_route = True
        for item in ROUTE:
            if item[0] == "start":
                await pg.evaluate(f"{W}.teleport({item[1][0]},{item[1][1]},{item[1][2]},{item[2]})")
                await pg.wait_for_timeout(600); await sample(); continue
            if item[0] == "shot": await shot(item[1]); continue
            if item[0] == "lift":
                okl = await pg.evaluate(f"{W}.liftTo({item[1]})"); events.append({"lift_to": item[1], "accepted": okl})
                for _ in range(80):
                    await pg.wait_for_timeout(100); s = await sample()
                    if s["lift"] and abs(s["lift"]["car"] - item[1]) < 1e-3: break
                await pg.wait_for_timeout(300); continue
            tx, ty, tz = item
            await pg.keyboard.down("w")
            best, best_t, arrived = 1e9, time.time(), False
            while True:
                s = await sample()
                dx, dy = tx - s["x"], ty - s["y"]; dist = math.hypot(dx, dy)
                if dist < 0.45: arrived = True; break
                await pg.evaluate(f"{W}.setYaw({math.atan2(-dx, dy)})")
                if dist < best - 0.1: best, best_t = dist, time.time()
                if time.time() - best_t > 4.0:
                    stuck.append({"target": item, "at": [s["x"], s["y"], s["z"]], "dist": dist}); break
                await pg.wait_for_timeout(40 if dist < 1.2 else 80)
            await pg.keyboard.up("w"); await pg.wait_for_timeout(120)
            s = await sample()
            if not arrived:
                ok_route = False; events.append({"stuck_before": item}); break
            if abs(s["z"] - tz) > 0.6:
                events.append({"warn_level": item, "z": s["z"]})
        await shot("99_end")
        final = await st()
        # ---------------- v13: auto-door coverage ----------------
        page_doors = {d["id"]: d for d in await pg.evaluate(f"{W}.doorList()")}
        cov = {"spaces_doors": len(S["doors"]), "by_type": {}, "auto_doors_in_page": len(page_doors),
               "missing": [], "bad": [], "archways_no_leaf": [d["id"] for d in S["doors"] if d["type"] not in LEAF_TYPES],
               "extra_in_page": sorted(set(page_doors) - {d["id"] for d in LEAFED})}
        for d in S["doors"]:
            t = cov["by_type"].setdefault(d["type"], {"n": 0, "auto": 0})
            t["n"] += 1
            pd = page_doors.get(d["id"])
            if pd and len(pd["leaves"]) == 2 and pd["animated"] and sorted(pd["sides"]) == ["A", "B"] and min(pd["slide"]) > 0.3: t["auto"] += 1
            elif d["type"] in LEAF_TYPES: (cov["bad"] if pd else cov["missing"]).append(d["id"])
        cov["PASS"] = not cov["missing"] and not cov["bad"] and not cov["extra_in_page"] and len(page_doors) == len(LEAFED)
        # ---------------- v13: scripted pass through >= 10 doors ----------------
        async def walk_to(tx, ty, on_sample=None, timeout=4.0):
            await pg.keyboard.down("w"); best, best_t, ok = 1e9, time.time(), False
            while True:
                s = await sample()
                if on_sample: await on_sample(s)
                dx, dy = tx - s["x"], ty - s["y"]; dist = math.hypot(dx, dy)
                if dist < 0.4: ok = True; break
                await pg.evaluate(f"{W}.setYaw({math.atan2(-dx, dy)})")
                if dist < best - 0.1: best, best_t = dist, time.time()
                if time.time() - best_t > timeout: break
                await pg.wait_for_timeout(40)
            await pg.keyboard.up("w"); return ok
        async def door_state(i): return await pg.evaluate(f"{W}.door({json.dumps(i)})")
        door_log, shots = [], {}
        for i in PASS_DOORS:
            d = D[i]; c, n = d["center"], d["normal"]; lift = d["type"] == "lift_door"
            if lift: sx, sy = -n[0], -n[1]                               # lift door normal points out of the shaft
            else:
                (a0, a1) = through(i, 1.0); sx, sy = (a1[0] - a0[0])/2, (a1[1] - a0[1])/2   # unit vector a -> b
            k_in = 1.3 if lift else 1.8
            start, end = None, None
            for k_out in (3.6, 3.3):
                st_ = (c[0] - sx*k_out, c[1] - sy*k_out); en_ = (c[0] + sx*k_in, c[1] + sy*k_in)
                if await pg.evaluate(f"{W}.raySegment([{st_[0]},{st_[1]},{c[2] + 1.0}],[{en_[0]},{en_[1]},{c[2] + 1.0}])") is None:
                    start, end = st_, en_; break
            rec = {"door": i, "type": d["type"], "level": c[2]}
            if start is None: rec["skipped"] = "no clear approach line"; door_log.append(rec); continue
            await pg.evaluate(f"{W}.teleport({start[0]},{start[1]},{c[2] + 0.05},{math.atan2(-sx, sy)})")
            prev = None                                                  # teleport: not a walked segment
            for _ in range(40):                                          # wait for the door to be closed before approaching
                ds = await door_state(i)
                if ds["t"] == 0 and not ds["active"]: break
                await pg.wait_for_timeout(100)
            await pg.wait_for_timeout(300)
            rec["closed_at_start"] = (await door_state(i))["t"] == 0
            if lift: rec["car_before"] = (await door_state(i))["car"]
            b0 = await pg.evaluate(f"{W}.leafBlocks()")
            mx = {"t": 0.0, "first_dist": None, "t_open_s": None, "call_dist": None, "t0": time.time()}
            async def watch(s, i=i, c=c, mx=mx):
                ds = await door_state(i); dist = math.hypot(s["x"] - c[0], s["y"] - c[1])
                if lift and mx["call_dist"] is None and ds["target"] is not None and abs(ds["target"] - c[2]) < 1e-3: mx["call_dist"] = round(dist, 2)
                if ds["t"] > 0 and mx["first_dist"] is None: mx["first_dist"] = round(dist, 2); mx["t_first"] = time.time()
                if ds["t"] >= 0.999 and mx["t_open_s"] is None: mx["t_open_s"] = round(ds["openDur"], 2) if ds["openDur"] is not None else None
                mx["t"] = max(mx["t"], ds["t"])
                if 0.35 < ds["t"] < 0.8 and d["type"] not in shots:
                    await pg.evaluate(f"{W}.render()"); pth = os.path.join(OUT, f"door_opening_{d['type']}.png")
                    await pg.screenshot(path=pth); shots[d["type"]] = pth
            n_before = len(doorpass)
            rec["reached_inside"] = await walk_to(*end, on_sample=watch, timeout=6.0 if lift else 4.0)
            rec["trigger_dist_m"] = mx["first_dist"]
            if lift: rec["call_dist_m"] = mx["call_dist"]; rec["car_waited"] = rec["car_before"] != c[2]
            rec["open_time_s"] = mx["t_open_s"]; rec["max_open"] = round(mx["t"], 3)
            rec["leaf_blocks_while_closed"] = await pg.evaluate(f"{W}.leafBlocks()") - b0
            await pg.wait_for_timeout(300)
            rec["back_out"] = await walk_to(*start, on_sample=watch)
            cr = [p for p in doorpass[n_before:] if p["door"] == i]
            rec["crossings"] = len(cr); rec["crossing_min_open"] = min((p["open"] for p in cr), default=None)
            rec["crossing_min_gap_m"] = min((p["gap_m"] for p in cr), default=None)
            tl = time.time(); closed = None
            while time.time() - tl < 4.0:
                ds = await door_state(i)
                if ds["t"] == 0: closed = round(time.time() - tl, 2); break
                await pg.wait_for_timeout(80)
            rec["closed_after_leaving_s"] = closed
            rec["PASS"] = bool(rec["closed_at_start"] and rec["reached_inside"] and rec["back_out"] and rec["max_open"] >= 0.999
                               and ((rec.get("call_dist_m") or 9) <= 3.05 if lift and rec["car_waited"] else
                                    (rec["trigger_dist_m"] is not None and 2.0 <= rec["trigger_dist_m"] <= 3.05))
                               and rec["crossings"] >= 2 and rec["crossing_min_gap_m"] >= GAP_MIN and closed is not None)
            door_log.append(rec)
        # ---------------- v13: fly-mode proximity (camera) ----------------
        fd = D[did("gallery", "E_link")]; c, n = fd["center"], fd["normal"]
        fly = {"door": fd["id"]}
        await pg.evaluate(f"window.__fly.setPose({c[0] - n[0]*8},{c[1] - n[1]*8},{c[2] + 1.6},{math.atan2(-n[0], n[1])},0)")
        await pg.wait_for_timeout(1500)
        for _ in range(40):                   # the walk suite may have left this door (next to D40) open: let it settle first
            if (await door_state(fd["id"]))["t"] == 0: break
            await pg.wait_for_timeout(100)
        await pg.wait_for_timeout(800); fly["far_t"] = (await door_state(fd["id"]))["t"]
        await pg.evaluate(f"window.__fly.setPose({c[0] - n[0]*2.2},{c[1] - n[1]*2.2},{c[2] + 1.6},{math.atan2(-n[0], n[1])},0)")
        await pg.wait_for_timeout(900); fly["near_t"] = (await door_state(fd["id"]))["t"]
        await pg.evaluate(f"window.__walk.render()"); fly["shot"] = os.path.join(OUT, "door_open_fly.png"); await pg.screenshot(path=fly["shot"])
        await pg.evaluate(f"window.__fly.setPose({c[0] - n[0]*9},{c[1] - n[1]*9},{c[2] + 1.6},{math.atan2(-n[0], n[1])},0)")
        await pg.wait_for_timeout(2500); fly["after_leave_t"] = (await door_state(fd["id"]))["t"]
        fly["PASS"] = fly["far_t"] == 0 and fly["near_t"] >= 0.999 and fly["after_leave_t"] == 0
        await pg.evaluate("window.__walk.setMode('walk')")
        await br.close()
    # doors passed: minimum open fraction while within 0.9 m of the leaf
    # v13: leaves are solid, so a crossing is legal once the physical gap clears the capsule (2R = 0.6 m) + 0.1 m;
    # plain doors are always fully open when crossed at walking speed, lift doors may be crossed while still sliding.
    dmin, gmin = {}, {}
    for d in doorpass:
        dmin[d["door"]] = min(dmin.get(d["door"], 1.0), d["open"]); gmin[d["door"]] = min(gmin.get(d["door"], 9.0), d["gap_m"])
    passed = [r for r in door_log if r.get("PASS")]
    door_suite = {"doors": door_log, "n_pass": len(passed), "types_passed": sorted({r["type"] for r in passed}),
                  "screenshots": shots, "fly": fly}
    door_suite["PASS"] = len(passed) >= 10 and len(passed) == len(door_log) and set(door_suite["types_passed"]) == set(LEAF_TYPES) and fly["PASS"]
    reached_upper = final["z"] > 13.0
    res = {"route_completed": ok_route, "final_state": final, "reached_upper_floor": reached_upper,
           "samples": len(traj), "duration_s": round(time.time() - t0, 1),
           "path_length_m": round(sum(math.dist((a['x'], a['y'], a['z']), (b['x'], b['y'], b['z'])) for a, b in zip(traj, traj[1:])), 1),
           "penetrations": pen, "stuck": stuck, "doors_passed_min_open": dmin, "doors_passed_min_gap_m": gmin, "events": events, "page_errors": errs, "sanity_ray_hits_wall": sanity is not None,
           "door_coverage": cov, "door_suite": door_suite,
           "PASS": cov["PASS"] and door_suite["PASS"] and ok_route and not pen and not stuck and reached_upper and all(v >= GAP_MIN for v in gmin.values()) and not errs and sanity is not None}
    json.dump(res, open(os.path.join(OUT, "walk_result.json"), "w"), indent=1)
    json.dump(traj, open(os.path.join(OUT, "trajectory.json"), "w"))
    with open(os.path.join(OUT, "trajectory.csv"), "w") as f:
        f.write("t,x,y,z,yaw,onGround,lift\n")
        for s in traj: f.write(f"{s['t']},{s['x']:.3f},{s['y']:.3f},{s['z']:.3f},{s['yaw']:.3f},{int(s['onGround'])},{(s['lift'] or {}).get('id','')}\n")
    plot(traj, events)
    print("WALK", "PASS" if res["PASS"] else "FAIL", {k: res[k] for k in ("route_completed", "reached_upper_floor", "samples", "path_length_m", "duration_s")},
          "penetrations", len(pen), "stuck", len(stuck), "doors(min open)", dmin, "gap_m", gmin, "errs", errs[:3], "sanity_wall_ray", sanity)
    print("DOOR COVERAGE", "PASS" if cov["PASS"] else "FAIL", cov["auto_doors_in_page"], "auto /", cov["spaces_doors"], "doors", cov["by_type"],
          "archways(no leaf):", cov["archways_no_leaf"], "missing", cov["missing"], "bad", cov["bad"])
    for r in door_log: print("  DOOR", "ok " if r.get("PASS") else "BAD", r)
    print("DOOR SUITE", "PASS" if door_suite["PASS"] else "FAIL", f"{door_suite['n_pass']}/{len(door_log)} doors, types {door_suite['types_passed']}", "fly", fly, "shots", shots)

def plot(traj, events):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 7.5), gridspec_kw={"width_ratios": [1.25, 1]})
    sil = os.path.join(HERE, "..", "renders", "sil_top_plan.png")
    import numpy as np
    for d in S["doors"]:
        if d["center"][2] == 0: a1.plot(d["center"][0], d["center"][1], "s", ms=3, color="#999")
    for nm, sp in S["spaces"].items():
        if sp["z"] == 0 and not nm.startswith("T_L") or nm == "T_L0": a1.text(sp["probe"][0], sp["probe"][1], nm, fontsize=7, color="#555", ha="center")
    xs = [s["x"] for s in traj]; ys = [s["y"] for s in traj]; zs = [s["z"] for s in traj]
    sc = a1.scatter(xs, ys, c=zs, s=4, cmap="viridis"); plt.colorbar(sc, ax=a1, label="floor z (m)")
    for e in events:
        if "shot" in e: a1.annotate(e["shot"][:2], e["at"][:2], fontsize=8, color="crimson")
    a1.set_aspect("equal"); a1.set_title("walk trajectory (plan, Blender XY, m)"); a1.grid(alpha=.3)
    a2.plot([s["t"] for s in traj], zs); a2.set_xlabel("time (s)"); a2.set_ylabel("floor z (m)"); a2.set_title("height over time (stair 0->4.5 m, lift 4.5->13.5 m)"); a2.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "trajectory.png"), dpi=110)

asyncio.run(main())
