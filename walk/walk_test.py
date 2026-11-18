"""Headless-Chrome walk test.
Drives the web preview with real WASD key events (plus yaw steering through the test hook, standing in for mouse-look),
along: forecourt -> arch/tunnel -> courtyard -> gallery -> west wing (link, hall, core) -> back -> gallery ring ->
tower link -> tower lobby -> stair A up to L1 -> lift 0 up to L3 -> exit on L3.
Records the trajectory, checks every movement segment for wall penetration (BVH ray between consecutive samples at
knee and chest height), detects getting stuck, checks auto-doors were open when passed, takes checkpoint screenshots.
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
            for d in await pg.evaluate(f"{W}.doorsNear(0.9)"):
                doorpass.append({"door": d["id"], "open": round(d["open"], 2), "t": s["t"]})
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
        await br.close()
    # doors passed: minimum open fraction while within 0.9 m of the leaf
    dmin = {}
    for d in doorpass: dmin[d["door"]] = min(dmin.get(d["door"], 1.0), d["open"])
    reached_upper = final["z"] > 13.0
    res = {"route_completed": ok_route, "final_state": final, "reached_upper_floor": reached_upper,
           "samples": len(traj), "duration_s": round(time.time() - t0, 1),
           "path_length_m": round(sum(math.dist((a['x'], a['y'], a['z']), (b['x'], b['y'], b['z'])) for a, b in zip(traj, traj[1:])), 1),
           "penetrations": pen, "stuck": stuck, "doors_passed_min_open": dmin, "events": events, "page_errors": errs, "sanity_ray_hits_wall": sanity is not None,
           "PASS": ok_route and not pen and not stuck and reached_upper and all(v >= 0.9 for v in dmin.values()) and not errs and sanity is not None}
    json.dump(res, open(os.path.join(OUT, "walk_result.json"), "w"), indent=1)
    json.dump(traj, open(os.path.join(OUT, "trajectory.json"), "w"))
    with open(os.path.join(OUT, "trajectory.csv"), "w") as f:
        f.write("t,x,y,z,yaw,onGround,lift\n")
        for s in traj: f.write(f"{s['t']},{s['x']:.3f},{s['y']:.3f},{s['z']:.3f},{s['yaw']:.3f},{int(s['onGround'])},{(s['lift'] or {}).get('id','')}\n")
    plot(traj, events)
    print("WALK", "PASS" if res["PASS"] else "FAIL", {k: res[k] for k in ("route_completed", "reached_upper_floor", "samples", "path_length_m", "duration_s")},
          "penetrations", len(pen), "stuck", len(stuck), "doors", dmin, "errs", errs[:3], "sanity_wall_ray", sanity)

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
