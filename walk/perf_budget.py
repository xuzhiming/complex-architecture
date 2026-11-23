"""Render cost budget: few global point lights, Render pixel-ratio cap 1, Clay cap stays 2.
The path lamps and the lobby lights are not global PointLights; they are shaded only on the
surfaces they light. Bollards and the reflection stay.
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
            fin = info.get("finish") or {}
            if fin.get("stoneMetal", 1) > 0.16: fails.append(f"stoneMetal {fin.get('stoneMetal')}")
            if fin.get("saucerMetal", 0) < 0.75: fails.append(f"saucerMetal {fin.get('saucerMetal')}")
            if not (fin.get("bridgeR", 0) > fin.get("saucerR", 1)): fails.append("bridge not warmer than saucer")
            if fin.get("windowEstr", 1) > 0.42: fails.append(f"windowEstr {fin.get('windowEstr')}")
            if not fin.get("contact"): fails.append("contact darkening off")
        if errs: fails.append("errors " + " | ".join(errs[:4]))
        await br.close()
    print("PERF BUDGET", "PASS" if not fails else "FAIL", info, fails)
    if fails:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
