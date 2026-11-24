"""Seamless daylight maps for the web preview. Not a photograph and not the concept image.
Run from the repo root: python3 tools/make_daylight_textures.py
"""
import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "..", "web", "tex")
os.makedirs(OUT, exist_ok=True)


def noise(n, seed, cells=32):
    rng = np.random.default_rng(seed)
    g = rng.random((cells, cells), dtype=np.float32)
    # bilinear sample with wrap, so the tile repeats
    ys = np.linspace(0, cells, n, endpoint=False)
    xs = np.linspace(0, cells, n, endpoint=False)
    y0 = np.floor(ys).astype(np.int32) % cells
    x0 = np.floor(xs).astype(np.int32) % cells
    fy = (ys - np.floor(ys))[:, None]
    fx = (xs - np.floor(xs))[None, :]
    y1 = (y0 + 1) % cells
    x1 = (x0 + 1) % cells
    n00 = g[np.ix_(y0, x0)]
    n10 = g[np.ix_(y0, x1)]
    n01 = g[np.ix_(y1, x0)]
    n11 = g[np.ix_(y1, x1)]
    a = n00 * (1 - fx) + n10 * fx
    b = n01 * (1 - fx) + n11 * fx
    return (a * (1 - fy) + b * fy).astype(np.float32)


def save_rgb(name, rgb):
    img = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img, "RGB").save(os.path.join(OUT, name), optimize=True)


def save_r(name, r):
    img = (np.clip(r, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img, "L").save(os.path.join(OUT, name), optimize=True)


def stone(n=512, meters=4.8):
    y, x = np.mgrid[0:n, 0:n]
    xm = x / n * meters
    ym = y / n * meters
    course = np.floor(ym / 1.2)
    lx = (xm + (course % 2) * 1.2) % 2.4
    ly = ym - course * 1.2
    joint = (lx < 0.02) | (lx > 2.38) | (ly < 0.016) | (ly > 1.184)
    pore = noise(n, 3, cells=64)
    pit = (pore > 0.9).astype(np.float32) * 0.045
    fine = noise(n, 9, cells=48)
    base = np.array([0.88, 0.84, 0.76], dtype=np.float32)
    col = base * (0.96 + 0.05 * fine)[..., None]
    col -= pit[..., None]
    joint_col = np.array([0.74, 0.7, 0.64], dtype=np.float32)
    col = np.where(joint[..., None], joint_col, col)
    rough = np.where(joint, 0.92, 0.8 + 0.05 * fine)
    return col, rough.astype(np.float32)


def metal(n=512):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    brush = 0.5 + 0.5 * np.sin((y / n) * np.pi * 2.0 * 96.0)
    grain = noise(n, 4)
    streak = np.clip(0.65 * brush + 0.35 * grain, 0, 1)
    base = np.array([0.74, 0.76, 0.78], dtype=np.float32)
    col = base * (0.9 + 0.14 * streak)[..., None]
    rough = (0.34 + 0.22 * (1.0 - streak)).astype(np.float32)
    return col, rough


def wood(n=512, across=1.6, along=1.6):
    y, x = np.mgrid[0:n, 0:n]
    xm = x / n * along
    ym = y / n * across
    board = np.floor(ym / 0.16)
    ly = ym - board * 0.16
    seam = (ly < 0.008) | (ly > 0.152)
    grain = 0.5 + 0.5 * np.sin((xm / along) * np.pi * 2.0 * 18.0 + board * 1.7)
    fine = noise(n, 6)
    base = np.array([0.62, 0.46, 0.30], dtype=np.float32)
    shade = 0.9 + 0.12 * ((board % 3) / 2.0) + 0.06 * grain + 0.04 * fine
    col = base * shade[..., None]
    col = np.where(seam[..., None], col * 0.72, col)
    rough = np.where(seam, 0.9, 0.62 + 0.08 * fine).astype(np.float32)
    return col, rough


def plaza(n=512, meters=6.4):
    y, x = np.mgrid[0:n, 0:n]
    xm = x / n * meters
    ym = y / n * meters
    sx = np.floor(xm / 3.2)
    sy = np.floor(ym / 3.2)
    lx = xm - sx * 3.2
    ly = ym - sy * 3.2
    joint = (lx < 0.035) | (lx > 3.165) | (ly < 0.035) | (ly > 3.165)
    fine = noise(n, 2)
    slab_id = (sx + sy * 3) % 4
    tint = 0.94 + 0.05 * (slab_id / 3.0)
    base = np.array([0.78, 0.76, 0.72], dtype=np.float32)
    col = base * tint[..., None] * (0.97 + 0.05 * fine)[..., None]
    col = np.where(joint[..., None], np.array([0.55, 0.54, 0.52], dtype=np.float32), col)
    rough = np.where(joint, 0.95, 0.84 + 0.04 * fine).astype(np.float32)
    return col, rough


def main():
    pairs = {
        "stone": stone(),
        "metal": metal(),
        "wood": wood(),
        "plaza": plaza(),
    }
    total = 0
    for name, (col, rough) in pairs.items():
        save_rgb(f"{name}_albedo.png", col)
        save_r(f"{name}_rough.png", rough)
    for fn in sorted(os.listdir(OUT)):
        sz = os.path.getsize(os.path.join(OUT, fn))
        total += sz
        print(f"{fn} {sz}")
    print("total", total)


if __name__ == "__main__":
    main()
