"""Browser checks for the north-up locator: layout, pose, packaging of the live page, and WebGL cost.
usage: python3 walk/minimap_preview.py [--url http://127.0.0.1:8773/index.html]
"""
import asyncio, base64, hashlib, json, os, statistics, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
URL = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else "http://127.0.0.1:8773/index.html"
OUT = os.environ.get("MINIMAP_OUT", "/opt/cursor/artifacts")
S = json.load(open(os.path.join(HERE, "..", "web", "spaces.json")))
BASE = json.load(open("/tmp/minimap_baseline.json"))
os.makedirs(OUT, exist_ok=True)

def probe(name):
    p = S["spaces"][name]["probe"]
    return p[0], p[1], p[2]

async def save_map(pg, name):
    data = await pg.evaluate("document.getElementById('minimap').toDataURL('image/png')")
    raw = base64.b64decode(data.split(",", 1)[1])
    path = os.path.join(OUT, name)
    open(path, "wb").write(raw)
    return path

async def save_page(pg, name):
    path = os.path.join(OUT, name)
    await pg.screenshot(path=path)
    return path

def med(xs):
    return statistics.median(xs)

def p95(xs):
    ys = sorted(xs)
    return ys[min(len(ys) - 1, max(0, int(round(0.95 * (len(ys) - 1)))))]

async def main():
    fails, shots = [], []
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path="/usr/bin/google-chrome",
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await br.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        errs = []
        pg.on("pageerror", lambda e: errs.append("page " + str(e)[:180]))
        pg.on("console", lambda m: errs.append("console " + m.text[:180]) if m.type == "error" else None)
        pg.on("requestfailed", lambda r: errs.append("request " + r.url))
        await pg.goto(URL + ("&" if "?" in URL else "?") + "test=1")
        await pg.wait_for_function("window.__walk && window.__walk.ready && window.__map && __map.read()", timeout=180000)
        await pg.evaluate("__walk.render()")
        render_url = await pg.evaluate("document.querySelector('canvas').toDataURL('image/png')")
        render_hash = hashlib.sha256(base64.b64decode(render_url.split(",", 1)[1])).hexdigest()
        calls = await pg.evaluate("__perf.frame()")
        await pg.evaluate("__walk.style('clay')")
        await pg.evaluate("__walk.render()")
        clay_url = await pg.evaluate("document.querySelector('canvas').toDataURL('image/png')")
        clay_hash = hashlib.sha256(base64.b64decode(clay_url.split(",", 1)[1])).hexdigest()
        await pg.evaluate("__walk.style('render')")
        if render_hash != BASE["render_sha256"]:
            fails.append("render canvas hash changed")
        if clay_hash != BASE["clay_sha256"]:
            fails.append("clay canvas hash changed")
        if calls.get("calls") != BASE["calls"]["calls"]:
            fails.append(f"draw calls {calls.get('calls')} baseline {BASE['calls']['calls']}")
        box = await pg.evaluate("""() => {
          const r = document.getElementById('minimap').getBoundingClientRect();
          const s = getComputedStyle(document.getElementById('minimap'));
          return { x: r.x, y: r.y, w: r.width, h: r.height, pe: s.pointerEvents, bottom: innerHeight - r.bottom, left: r.left };
        }""")
        if abs(box["w"] - 172) > 1 or abs(box["h"] - 148) > 1 or abs(box["left"] - 12) > 1 or abs(box["bottom"] - 12) > 1:
            fails.append("desktop layout " + json.dumps(box))
        if box["pe"] != "none":
            fails.append("pointer events " + box["pe"])
        orbit = await pg.evaluate("__map.read()")
        if orbit["kind"] != "orbit" or orbit["marker"] or "环绕" not in orbit["caption"] or "非玩家" not in orbit["caption"]:
            fails.append("orbit " + json.dumps(orbit))
        hit = await pg.evaluate("""() => {
          const r = document.getElementById('minimap').getBoundingClientRect();
          const el = document.elementFromPoint(r.x + 20, r.y + 20);
          return { id: el && el.id, tag: el && el.tagName };
        }""")
        if hit["id"] == "minimap" or hit["tag"] != "CANVAS":
            fails.append("hit target " + json.dumps(hit))
        shots.append(await save_page(pg, "minimap-orbit-page.png"))
        shots.append(await save_map(pg, "minimap-orbit-map.png"))

        async def place(x, y, z, yaw=0):
            await pg.evaluate("([x,y,z,yaw]) => __walk.teleport(x, y, z, yaw)", [x, y, z, yaw])
            await pg.wait_for_timeout(50)
            return await pg.evaluate("__map.read()")

        court = await place(*probe("courtyard"), 0)
        tower = await place(*probe("T_L0"), 0)
        west = await place(*probe("W_hall"), 0)
        if not (west["px"] < court["px"] < tower["px"] and tower["py"] < court["py"]):
            fails.append(f"plan positions court {court['px']:.1f},{court['py']:.1f} tower {tower['px']:.1f},{tower['py']:.1f} west {west['px']:.1f},{west['py']:.1f}")
        if court["edge"] or west["edge"] or tower["edge"]:
            fails.append("known points fell outside the frame")
        if "L0" not in court["caption"] or "漫游" not in court["caption"]:
            fails.append("court caption " + court["caption"])
        for label, rec in (("court", court), ("tower", tower), ("west", west)):
            if any(w in rec["caption"] for w in ("courtyard", "W_hall", "T_L", "lobby")):
                fails.append("room name in " + label + " " + rec["caption"])
        await place(*probe("courtyard"), yaw=3.141592653589793 / 2)
        faced = await pg.evaluate("__map.read()")
        if faced["dir"]["x"] > -0.99 or abs(faced["dir"]["y"]) > 0.05:
            fails.append("yaw pi/2 " + json.dumps(faced["dir"]))
        shots.append(await save_page(pg, "minimap-walk-court-page.png"))
        shots.append(await save_map(pg, "minimap-walk-court-map.png"))
        await place(*probe("T_L0"))
        shots.append(await save_map(pg, "minimap-walk-tower-map.png"))
        await place(*probe("W_hall"))
        shots.append(await save_map(pg, "minimap-walk-west-map.png"))

        stair = await place(0, 2, 2.2, 0)
        if "L" in stair["caption"]:
            fails.append("stair labelled " + stair["caption"])
        await pg.evaluate("__fly.setPose(0, 2, 80, 0, 0)")
        await pg.wait_for_timeout(50)
        air = await pg.evaluate("__map.read()")
        if air["kind"] != "fly" or "飞行" not in air["caption"] or "80.0" not in air["caption"] or "L" in air["caption"]:
            fails.append("fly air " + air["caption"])
        shots.append(await save_map(pg, "minimap-fly-map.png"))
        shots.append(await save_page(pg, "minimap-fly-page.png"))
        outside = await place(0, -170, 0, 0)
        if not outside["edge"] or "图外" not in outside["caption"] or abs(outside["worldEdge"]["y"] + 100) > 1e-3:
            fails.append("off map " + json.dumps({"edge": outside["edge"], "caption": outside["caption"], "worldEdge": outside["worldEdge"]}))
        if abs(outside["worldEdge"]["y"] + 14) < 5:
            fails.append("off map snapped to frame centre")
        shots.append(await save_map(pg, "minimap-off-map.png"))

        before = await pg.evaluate("__map.read().builds")
        await pg.evaluate("__map.bench(20)")
        after = await pg.evaluate("__map.read().builds")
        if after != before:
            fails.append(f"plan rebuilt during sync {before} -> {after}")

        await pg.set_viewport_size({"width": 390, "height": 844})
        await pg.wait_for_timeout(80)
        narrow = await pg.evaluate("""() => { const r = document.getElementById('minimap').getBoundingClientRect(); return { w: r.width, h: r.height, left: r.left }; }""")
        if abs(narrow["w"] - 132) > 2 or abs(narrow["h"] - 114) > 2:
            fails.append("narrow " + json.dumps(narrow))
        shots.append(await save_page(pg, "minimap-narrow-page.png"))
        await pg.set_viewport_size({"width": 800, "height": 420})
        await pg.wait_for_timeout(80)
        short = await pg.evaluate("""() => { const r = document.getElementById('minimap').getBoundingClientRect(); return { w: r.width, h: r.height }; }""")
        if abs(short["w"] - 112) > 2 or abs(short["h"] - 96) > 2:
            fails.append("short " + json.dumps(short))
        shots.append(await save_page(pg, "minimap-short-page.png"))

        await pg.set_viewport_size({"width": 1280, "height": 720})
        await pg.evaluate("__fly.orbitPose(-120, -170, 80, 0, 0, 25)")
        a = await pg.evaluate("__fly.camPose()")
        rect = await pg.evaluate("() => { const r = document.getElementById('minimap').getBoundingClientRect(); return { x: r.x, y: r.y }; }")
        await pg.mouse.move(rect["x"] + 30, rect["y"] + 40)
        await pg.mouse.down()
        await pg.mouse.move(rect["x"] + 120, rect["y"] + 90)
        await pg.mouse.up()
        await pg.wait_for_timeout(60)
        b = await pg.evaluate("__fly.camPose()")
        if abs(a["x"] - b["x"]) + abs(a["y"] - b["y"]) + abs(a["z"] - b["z"]) < 0.05:
            fails.append("drag on the map did not orbit")

        dpr_page = await br.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=3)
        await dpr_page.goto(URL + ("&" if "?" in URL else "?") + "test=1")
        await dpr_page.wait_for_function("window.__map && __map.read()", timeout=180000)
        dpr = await dpr_page.evaluate("""() => {
          const m = __map.read();
          const snap = __perf.snapshot();
          return { map: m.dpr, render: snap.pixelRatio, cap: snap.renderCap, clay: snap.clayCap };
        }""")
        if dpr["map"] > 2 or dpr["render"] != 1 or dpr["cap"] != 1 or dpr["clay"] != 2:
            fails.append("pixel caps " + json.dumps(dpr))
        await dpr_page.close()

        lock_page = await br.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        lock_errs = []
        lock_page.on("pageerror", lambda e: lock_errs.append(str(e)[:180]))
        await lock_page.goto(URL.split("?")[0])
        await lock_page.wait_for_function("window.__walk && window.__walk.ready", timeout=180000)
        await lock_page.evaluate("""() => {
          window.__lock = 0;
          const c = document.querySelector('canvas');
          c.requestPointerLock = () => { window.__lock++; };
        }""")
        await lock_page.evaluate("__walk.setMode('walk')")
        lb = await lock_page.evaluate("() => { const r = document.getElementById('minimap').getBoundingClientRect(); return { x: r.x + 16, y: r.y + 16 }; }")
        await lock_page.mouse.click(lb["x"], lb["y"])
        locks = await lock_page.evaluate("window.__lock")
        if locks < 1:
            fails.append("click through the map did not request pointer lock")
        if lock_errs:
            fails.append("lock page " + lock_errs[0])
        await lock_page.close()

        await pg.evaluate("__walk.style('render')")
        await pg.evaluate("__fly.orbitPose(-120, -170, 80, 0, 0, 25)")
        rounds = []
        for _ in range(3):
            rounds.append(await pg.evaluate("""async () => {
              const gl = document.querySelector('canvas').getContext('webgl2');
              const px = new Uint8Array(4);
              const out = [];
              for (let i = 0; i < 12; i++) {
                const t0 = performance.now();
                __walk.render();
                gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
                out.push(performance.now() - t0);
              }
              return out;
            }"""))
        flat = [v for group in rounds for v in group]
        costs = await pg.evaluate("__map.bench(30)")
        if errs:
            fails.append(errs[0])
        report = {
            "PASS": not fails,
            "fails": fails,
            "render_sha256": render_hash,
            "clay_sha256": clay_hash,
            "calls": calls,
            "frame_med": med(flat),
            "frame_p95": p95(flat),
            "baseline_med": BASE["med"],
            "baseline_p95": BASE["p95"],
            "map_sync_med": med(costs),
            "map_sync_p95": p95(costs),
            "shots": shots,
        }
        json.dump(report, open(os.path.join(OUT, "minimap-preview.json"), "w"), indent=2)
        print("MINIMAP PREVIEW", "PASS" if not fails else "FAIL")
        print(json.dumps({k: report[k] for k in ("fails", "calls", "frame_med", "frame_p95", "baseline_med", "baseline_p95", "map_sync_med", "map_sync_p95")}, indent=2))
        await br.close()
    if fails:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
