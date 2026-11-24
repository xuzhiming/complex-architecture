"""Render cost budget: few global point lights, Render pixel-ratio cap 1, Clay cap stays 2.
Daylight paving uses shared stone, metal, wood and plaza maps. Glass and the crescent do not glow.
usage: python3 walk/perf_budget.py --url http://127.0.0.1:8771/index.html
"""
import asyncio, sys
from playwright.async_api import async_playwright

URL = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else "http://127.0.0.1:8771/index.html"

async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path="/usr/bin/google-chrome",
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await br.new_page(viewport={"width": 1280, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.goto(URL + ("&" if "?" in URL else "?") + "test=1")
        await pg.wait_for_function("window.__walk && window.__walk.ready", timeout=240000)
        info = await pg.evaluate("window.__perf && __perf.snapshot ? __perf.snapshot() : null")
        await pg.evaluate("__walk.render()")
        fails = []
        if not info:
            fails.append("missing __perf")
        else:
            if info.get("renderCap") != 1: fails.append(f"renderCap {info.get('renderCap')}")
            if info.get("clayCap") != 2: fails.append(f"clayCap {info.get('clayCap')}")
            if info.get("pointLights", 99) > 4: fails.append(f"pointLights {info.get('pointLights')}")
            if info.get("bollards", 0) < 5: fails.append(f"bollards {info.get('bollards')}")
            if not info.get("env"): fails.append("env off")
            if info.get("style") != "render": fails.append(f"style {info.get('style')}")
            if info.get("bloom", 1) > 0.08: fails.append(f"bloom {info.get('bloom')}")
            fin = info.get("finish") or {}
            if fin.get("stoneMetal", 1) > 0.12: fails.append(f"stoneMetal {fin.get('stoneMetal')}")
            if fin.get("saucerMetal", 0) < 0.7: fails.append(f"saucerMetal {fin.get('saucerMetal')}")
            if not (fin.get("bridgeR", 0) > fin.get("saucerR", 1)): fails.append("bridge not warmer than saucer")
            if fin.get("windowEstr", 1) > 0.05: fails.append(f"windowEstr {fin.get('windowEstr')}")
            if fin.get("crescentEstr", 1) > 0.02: fails.append(f"crescentEstr {fin.get('crescentEstr')}")
            g = info.get("glass") or {}
            if not g.get("transparent"): fails.append("glass opaque")
            if not (0.08 <= g.get("opacity", 1) <= 0.4): fails.append(f"glass opacity {g.get('opacity')}")
            if g.get("depthWrite", True): fails.append("glass writes depth")
            if g.get("transmission", 0): fails.append("transmission")
            if g.get("panes", 0) < 20: fails.append(f"glass panes {g.get('panes')}")
            tex = info.get("tex") or {}
            if tex.get("stone", 0) < 256: fails.append(f"stone map {tex.get('stone')}")
            if tex.get("metal", 0) < 256: fails.append(f"metal map {tex.get('metal')}")
            if tex.get("wood", 0) < 128: fails.append(f"wood map {tex.get('wood')}")
            if tex.get("plaza", 0) < 256: fails.append(f"plaza map {tex.get('plaza')}")
            if tex.get("proj") != "axis": fails.append(f"proj {tex.get('proj')}")
            if tex.get("ringEmit", 1) > 0.02: fails.append(f"ringEmit {tex.get('ringEmit')}")
        mp = await pg.evaluate("window.__map ? __map.read() : null")
        gln = await pg.evaluate("""() => {
          let n = 0;
          for (const c of document.querySelectorAll('canvas')) {
            if (c.id === 'minimap') continue;
            if (c.getContext('webgl2')) n++;
          }
          return n;
        }""")
        if gln != 1: fails.append(f"webgl contexts {gln}")
        if not mp: fails.append("missing map")
        else:
            if mp["dpr"] > 2: fails.append(f"map dpr {mp['dpr']}")
            if mp["kind"] != "orbit" or mp["marker"]: fails.append(f"orbit marker {mp['kind']}")
            if "环绕" not in (mp.get("caption") or ""): fails.append(mp.get("caption"))
        if errs: fails.append("errors " + " | ".join(errs[:4]))
        await br.close()
    print("PERF BUDGET", "PASS" if not fails else "FAIL", info, fails)
    if fails:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
