"""v14: screenshots of the web preview in 渲染 Render and 白模 Clay style + a frame-time sample (headless Chrome, swiftshader).
usage: python3 walk/style_shots.py --url http://localhost:8765/index.html"""
import asyncio, json, os, sys, time
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
URL = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else "http://localhost:8765/index.html"
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await br.new_page(viewport={"width": 1280, "height": 640}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.goto(URL + "?test=1"); await pg.wait_for_function("window.__walk && window.__walk.ready", timeout=240000)
        res = {"default_style": await pg.evaluate("__walk.style()"), "shots": {}}
        poses = {"front": (0, -175, 18, 0, 10, 30), "aerial": (-150, -175, 120, 2, 4, 22)}
        for st in ("render", "clay"):
            await pg.evaluate(f"__walk.style('{st}')")
            for nm, (px, py, pz, tx, ty, tz) in poses.items():
                await pg.evaluate(f"__fly.orbitPose({px},{py},{pz},{tx},{ty},{tz})"); await pg.evaluate("__walk.render()")
                f = os.path.join(HERE, f"web_style_{st}_{nm}.png"); await pg.screenshot(path=f); res["shots"][f"{st}_{nm}"] = f
        await pg.evaluate("__walk.style('render')")
        # walk view at a door in render style
        await pg.evaluate("__walk.teleport(-38.4 + 3.4, 2.0, 0.05, Math.atan2(1, 0))"); await pg.wait_for_timeout(500)
        await pg.evaluate("__walk.render()"); f = os.path.join(HERE, "web_style_render_walk.png"); await pg.screenshot(path=f); res["shots"]["render_walk"] = f
        # frame time of draw() (render + bloom) in this software-GL container: indicative only
        t = await pg.evaluate("(() => { const gl = document.querySelector('canvas').getContext('webgl2'); const px = new Uint8Array(4); const t0 = performance.now(); for (let i = 0; i < 5; i++) { __walk.render(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); } return (performance.now() - t0) / 5; })()")
        await pg.evaluate("__walk.style('clay')")
        tc = await pg.evaluate("(() => { const gl = document.querySelector('canvas').getContext('webgl2'); const px = new Uint8Array(4); const t0 = performance.now(); for (let i = 0; i < 5; i++) { __walk.render(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); } return (performance.now() - t0) / 5; })()")
        res["frame_ms_swiftshader"] = {"render_bloom": round(t, 1), "clay": round(tc, 1)}; res["errors"] = errs
        await br.close()
    json.dump(res, open(os.path.join(HERE, "style_shots.json"), "w"), indent=1)
    print("STYLE SHOTS", "PASS" if not errs and res["default_style"] == "render" else "FAIL", json.dumps(res))
asyncio.run(main())
