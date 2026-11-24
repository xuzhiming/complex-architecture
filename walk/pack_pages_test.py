"""The Pages bundle must contain the eight real texture PNGs, not an HTML fallback.
Replays the Build site script from .github/workflows/deploy.yml.
usage: python3 walk/pack_pages_test.py
"""
import hashlib, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG = b"\x89PNG\r\n\x1a\n"
TEX = [
    "metal_albedo.png", "metal_rough.png",
    "plaza_albedo.png", "plaza_rough.png",
    "stone_albedo.png", "stone_rough.png",
    "wood_albedo.png", "wood_rough.png",
]
REQUIRED = [
    "index.html", "main.js", "spaces.json", "building_opt.glb",
    "vendor/three/build/three.module.js",
]

def build_script():
    lines = open(os.path.join(ROOT, ".github/workflows/deploy.yml"), encoding="utf-8").read().splitlines()
    start = next(i for i, line in enumerate(lines) if "Build site" in line)
    body = []
    for line in lines[start + 1:]:
        if line.startswith("        run: |"):
            continue
        if line.startswith("          "):
            body.append(line[10:])
            continue
        if body:
            break
    if not body:
        raise SystemExit("deploy.yml has no Build site script")
    return "\n".join(body) + "\n"

def pack(dist):
    script = re.sub(r"\bdist\b", dist, build_script())
    proc = subprocess.run(["bash", "-lc", script], cwd=ROOT, capture_output=True, text=True)
    return proc

def check(dist):
    bad = []
    for rel in REQUIRED:
        path = os.path.join(dist, rel)
        if not os.path.isfile(path) or os.path.getsize(path) < 32:
            bad.append("missing " + rel)
    for name in TEX:
        path = os.path.join(dist, "tex", name)
        src = os.path.join(ROOT, "web", "tex", name)
        if not os.path.isfile(path):
            bad.append("missing tex/" + name)
            continue
        data = open(path, "rb").read()
        if not data.startswith(PNG) or len(data) < 8000:
            bad.append("not a png tex/" + name)
            continue
        if hashlib.sha256(data).hexdigest() != hashlib.sha256(open(src, "rb").read()).hexdigest():
            bad.append("hash tex/" + name)
    return bad

def main():
    dist = tempfile.mkdtemp(prefix="pages-dist-")
    try:
        proc = pack(dist)
        bad = check(dist)
        if proc.returncode != 0:
            bad.append("build exit " + str(proc.returncode))
            if proc.stderr:
                bad.append(proc.stderr.strip().splitlines()[-1])
        if not bad:
            bad.extend(load_preview(dist))
        print("PACK", "PASS" if not bad else "FAIL", bad)
        if bad:
            sys.exit(1)
    finally:
        shutil.rmtree(dist, ignore_errors=True)

def load_preview(dist):
    import asyncio
    from playwright.async_api import async_playwright
    async def run():
        proc = subprocess.Popen(["python3", "-m", "http.server", "8819", "--directory", dist], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            async with async_playwright() as p:
                br = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
                pg = await br.new_page(viewport={"width": 960, "height": 540})
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:180]))
                pg.on("console", lambda m: errs.append(m.text[:180]) if m.type == "error" else None)
                await pg.goto("http://127.0.0.1:8819/index.html?test=1")
                await pg.wait_for_function("window.__walk && window.__walk.ready", timeout=180000)
                render = await pg.evaluate("__walk.style()")
                clay = await pg.evaluate("__walk.style('clay')")
                tex = await pg.evaluate("__perf.snapshot().tex")
                await br.close()
            if errs:
                return ["page " + errs[0]]
            if render != "render" or clay != "clay":
                return [f"style {render} {clay}"]
            if tex.get("stone") != 512 or tex.get("proj") != "axis":
                return ["textures did not decode " + str(tex)]
            return []
        finally:
            proc.terminate()
    return asyncio.run(run())

if __name__ == "__main__":
    main()
