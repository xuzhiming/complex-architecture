"""Fail unless dist/ is a real Pages bundle: site files plus eight texture PNGs.
A 200 HTML fallback is not a texture. usage: python3 tools/check_pages_dist.py dist
"""
import hashlib, os, sys

PNG = b"\x89PNG\r\n\x1a\n"
TEX = [
    "metal_albedo.png", "metal_rough.png",
    "plaza_albedo.png", "plaza_rough.png",
    "stone_albedo.png", "stone_rough.png",
    "wood_albedo.png", "wood_rough.png",
]
REQUIRED = [
    "index.html", "main.js", "minimap.js", "params.json", "spaces.json", "building_opt.glb",
    "vendor/three/build/three.module.js",
]
HASHED = {
    "minimap.js": "web/minimap.js",
    "params.json": "params.json",
}

def main():
    dist = sys.argv[1] if len(sys.argv) > 1 else "dist"
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for rel in REQUIRED:
        path = os.path.join(dist, rel)
        if not os.path.isfile(path) or os.path.getsize(path) < 32:
            bad.append("missing " + rel)
    for rel, src_rel in HASHED.items():
        path = os.path.join(dist, rel)
        src = os.path.join(root, src_rel)
        if not os.path.isfile(path) or not os.path.isfile(src):
            bad.append("missing " + rel)
            continue
        if hashlib.sha256(open(path, "rb").read()).hexdigest() != hashlib.sha256(open(src, "rb").read()).hexdigest():
            bad.append("hash " + rel)
    for name in TEX:
        path = os.path.join(dist, "tex", name)
        src = os.path.join(root, "web", "tex", name)
        if not os.path.isfile(path):
            bad.append("missing tex/" + name)
            continue
        data = open(path, "rb").read()
        if not data.startswith(PNG) or len(data) < 8000:
            bad.append("not a png tex/" + name)
            continue
        if hashlib.sha256(data).hexdigest() != hashlib.sha256(open(src, "rb").read()).hexdigest():
            bad.append("hash tex/" + name)
    print("PAGES DIST", "PASS" if not bad else "FAIL", bad)
    if bad:
        sys.exit(1)

if __name__ == "__main__":
    main()
