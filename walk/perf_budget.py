"""Render cost budget: few global point lights, Render pixel-ratio cap 1, Clay cap stays 2.
The path lamps and the lobby lights are not global PointLights. The night look is the original
dark blue scene: no dusk reflection, a bright arch core, and the lobby ceiling drawn from both sides.
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
            if info.get("env"): fails.append("dusk env on")
            if info.get("style") != "render": fails.append(f"style {info.get('style')}")
            look = info.get("look") or {}
            if look.get("fog") != 0x1b1840: fails.append(f"fog {look.get('fog')}")
            if look.get("exposure", 0) < 0.94: fails.append(f"exposure {look.get('exposure')}")
            if look.get("bloom", 0) < 0.5: fails.append(f"bloom {look.get('bloom')}")
            if look.get("arch", 0) < 200: fails.append(f"arch {look.get('arch')}")
            if look.get("pools", 0) < 7: fails.append(f"pools {look.get('pools')}")
            if not look.get("hallDouble"): fails.append("hall ceiling single sided")
        if errs: fails.append("errors " + " | ".join(errs[:4]))
        await br.close()
    print("PERF BUDGET", "PASS" if not fails else "FAIL", info, fails)
    if fails:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
