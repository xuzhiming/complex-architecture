"""Headless-Chrome FLY-mode test for the web preview.
Checks: entering fly from orbit keeps the camera pose; real key input (W/Space/Shift) moves along the view direction with no
gravity; flying up over the crown; flying straight through the arch, the courtyard and on through a wall (no collision);
wheel / +/- speed; preset buttons and the auto tour; F back to orbit; fly -> walk drops onto a real floor; no page/console
errors. Screenshots: walk/fly_*.png ; result: walk/fly_result.json
usage: python3 walk/fly_test.py [--url http://localhost:8765/index.html]"""
import asyncio, json, math, os, sys, time
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
URL = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else "http://localhost:8765/index.html"
S = json.load(open(os.path.join(HERE, "..", "web", "spaces.json")))
P = json.load(open(os.path.join(HERE, "..", "params.json")))
CC = S["spaces"]["courtyard"]["probe"]
FY = next(d["center"][1] for d in S["doors"] if {d["a"], d["b"]} == {"forecourt", "portal_tunnel"})
TC = (P["tower"]["cx"], P["tower"]["cy"]); CROWN = P["tower"]["crown_z"]

async def main():
    checks, shots = {}, []
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path="/usr/bin/google-chrome",
                                     args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await br.new_page(viewport={"width": 1280, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL + "?test=1")
        await pg.wait_for_function("window.__walk && window.__walk.ready && window.__fly", timeout=240000)
        F = "window.__fly"
        async def st(): return await pg.evaluate(f"{F}.state()")
        async def shot(name):
            await pg.wait_for_timeout(150); await pg.evaluate("window.__walk.render()")
            path = os.path.join(HERE, f"fly_{name}.png"); await pg.screenshot(path=path); shots.append(path)
        async def hold(keys, ms):
            for k in keys: await pg.keyboard.down(k)
            await pg.wait_for_timeout(ms)
            for k in keys: await pg.keyboard.up(k)
            await pg.wait_for_timeout(700)          # let the damping settle

        # 1 orbit -> fly keeps the camera pose (F key)
        await pg.evaluate(f"{F}.orbitPose(-120, -170, 80, 0, 0, 25)")
        await pg.wait_for_timeout(300)
        before = await pg.evaluate(f"{F}.camPose()")
        await pg.keyboard.press("f"); await pg.wait_for_timeout(300)
        s = await st(); after = await pg.evaluate(f"{F}.camPose()")
        checks["enter_from_orbit_keeps_pose"] = s["mode"] == "fly" and all(abs(before[k] - after[k]) < 1e-3 for k in ("x", "y", "z", "yaw", "pitch"))
        await shot("01_enter_from_orbit")

        # 2 no gravity: idle 1.5 s, height unchanged
        z0 = (await st())["z"]; await pg.wait_for_timeout(1500); checks["no_gravity"] = abs((await st())["z"] - z0) < 1e-3

        # 3 W moves along the view direction (pitched down 20 deg, yaw 30 deg)
        await pg.evaluate(f"{F}.setPose(-60, -120, 60, 0.5236, -0.349)")
        a = await st(); await hold(["w"], 1500); b = await st()
        d = [b["x"] - a["x"], b["y"] - a["y"], b["z"] - a["z"]]; L = math.sqrt(sum(c*c for c in d)) or 1
        view = [-math.sin(0.5236)*math.cos(-0.349), math.cos(0.5236)*math.cos(-0.349), math.sin(-0.349)]   # Blender coords
        checks["W_along_view_dir_cos"] = round(sum(x*y/L for x, y in zip(d, view)), 4); checks["W_dist_m"] = round(L, 2)
        # Shift boost
        await pg.evaluate(f"{F}.setPose(-60, -120, 60, 0.5236, -0.349)")
        a = await st(); await hold(["Shift", "w"], 1500); b = await st()
        L2 = math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"])); checks["shift_boost_ratio"] = round(L2/L, 2)

        # 4 fly up over the crown: start south-west of the tower at z 60 facing it, hold Space + W
        yaw = math.atan2(-(TC[0] - (TC[0] - 30)), TC[1] - (TC[1] - 30))
        await pg.evaluate(f"{F}.setPose({TC[0] - 30}, {TC[1] - 30}, 60, {yaw}, 0)")
        await hold(["Space", "w"], 2600); s = await st()
        checks["climbed_over_crown"] = {"z": round(s["z"], 1), "crown_z": CROWN, "dist_to_tower_axis": round(math.hypot(s["x"] - TC[0], s["y"] - TC[1]), 1)}
        checks["climb_ok"] = s["z"] > CROWN + 15
        await shot("02_climbing_to_crown")
        await pg.evaluate(f"{F}.preset(3)"); await shot("03_over_crown")
        # Q descends
        a = await st(); await hold(["q"], 1000); b = await st(); checks["Q_descends"] = b["z"] < a["z"] - 5

        # 5 straight through the arch, the tunnel, the courtyard and on through the north buildings (no collision)
        await pg.evaluate(f"{F}.setPose(0, {FY - 25}, 5, 0, 0)"); await pg.evaluate(f"{F}.speed(14)")
        a = await st(); await shot("04_approach_arch")
        await pg.keyboard.down("w"); t0 = time.time(); seen = []
        while True:
            s = await st(); seen.append(s["y"])
            if s["y"] > CC[1] - 6 and "05_in_courtyard" not in "".join(shots): await pg.keyboard.up("w"); await pg.wait_for_timeout(700); await shot("05_in_courtyard"); await pg.keyboard.down("w")
            if s["y"] > 75 or time.time() - t0 > 25: break
            await pg.wait_for_timeout(100)
        await pg.keyboard.up("w"); await pg.wait_for_timeout(500); b = await st()
        wall = await pg.evaluate(f"window.__walk.raySegment([0, {CC[1] + 10}, 5], [0, 75, 5])")
        checks["through_courtyard"] = {"from_y": round(a["y"], 1), "to_y": round(b["y"], 1), "z_drift": round(b["z"] - a["z"], 3),
                                        "x_drift": round(b["x"] - a["x"], 3), "solid_crossed_after_courtyard": wall is not None}
        checks["through_ok"] = b["y"] > 75 and abs(b["z"] - a["z"]) < 0.05 and wall is not None
        await pg.evaluate(f"{F}.setPose({CC[0] - 14}, {CC[1] - 10}, 6, -0.3, 0.35)"); await shot("06_courtyard_look_up")

        # 6 speed: wheel and +/- keys
        s0 = (await st())["speed"]; await pg.mouse.move(640, 360); await pg.mouse.wheel(0, -300); await pg.wait_for_timeout(200)
        s1 = (await st())["speed"]; await pg.keyboard.press("Minus"); await pg.keyboard.press("Minus"); s2 = (await st())["speed"]
        checks["speed_wheel_up"] = s1 > s0; checks["speed_minus"] = s2 < s1; checks["speeds"] = [round(s0, 2), round(s1, 2), round(s2, 2)]
        hud = await pg.evaluate(f"{F}.hud()"); checks["hud_shows_speed"] = "speed" in hud and "飞行" in hud

        # 7 preset buttons (real DOM clicks) + auto tour
        btns = await pg.locator("#flyBar button").all_inner_texts(); checks["fly_bar_buttons"] = btns
        await pg.click("#flyBar button >> nth=3"); s = await st(); checks["preset_crown_z"] = round(s["z"], 1)
        await pg.click("#bTour"); a = await st(); await pg.wait_for_timeout(1500); b = await st()
        checks["tour_moves"] = b["tour"] and math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"])) > 1
        for u, nm in ((0.25, "07_tour_tunnel"), (0.5, "08_tour_over_crown")):
            await pg.evaluate(f"{F}.tourAt({u})"); await shot(nm)
        await pg.keyboard.press("w"); checks["key_stops_tour"] = not (await st())["tour"]

        # 8 F -> back to orbit
        await pg.keyboard.press("f"); await pg.wait_for_timeout(300); checks["F_back_to_orbit"] = (await st())["mode"] == "orbit"
        # 9 fly -> walk drops onto a floor (over the courtyard, z 30)
        await pg.click("#bFly"); await pg.evaluate(f"{F}.setPose({CC[0] + 4}, {CC[1] + 3}, 30, 0, -0.2)")
        await pg.click("#bWalk"); await pg.wait_for_timeout(1500)
        w = await pg.evaluate("window.__walk.state()")
        checks["walk_drop"] = {"mode": await pg.evaluate("window.__walk.mode()"), "x": round(w["x"], 2), "y": round(w["y"], 2), "z": round(w["z"], 2), "onGround": w["onGround"]}
        checks["walk_drop_ok"] = w["onGround"] and abs(w["z"] - CC[2]) < 0.5 and abs(w["x"] - (CC[0] + 4)) < 0.6
        await shot("09_dropped_to_walk")
        await br.close()
    ok_keys = ["enter_from_orbit_keeps_pose", "no_gravity", "climb_ok", "Q_descends", "through_ok", "speed_wheel_up", "speed_minus",
               "hud_shows_speed", "tour_moves", "key_stops_tour", "F_back_to_orbit", "walk_drop_ok"]
    PASS = all(checks[k] for k in ok_keys) and checks["W_along_view_dir_cos"] > 0.99 and 2.5 < checks["shift_boost_ratio"] < 3.5 and not errs
    res = {"PASS": PASS, "checks": checks, "errors": errs, "screenshots": shots}
    json.dump(res, open(os.path.join(HERE, "fly_result.json"), "w"), indent=1, ensure_ascii=False)
    print("FLY", "PASS" if PASS else "FAIL", json.dumps(checks, ensure_ascii=False), "errors", errs[:5])
asyncio.run(main())
