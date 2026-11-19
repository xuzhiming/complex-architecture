# Complex Architecture / 复杂建筑

Procedural Blender building (white-clay massing → detailed structure) + three.js orbit / walk / fly preview.
程序化 Blender 建筑（参数驱动）+ three.js 环绕/漫游预览。

Live preview / 在线预览: https://complex-architecture.pages.dev (Cloudflare Pages, deployed from `web/` on push to `main`).

![final](docs/final_render.png)
![views](docs/four_views.png)
![hero](docs/perspective_hero.png)
![crown](docs/crown_detail.png)
![detail](docs/detail_tower.png)

## Run locally / 本地预览

```bash
cd web && python3 -m http.server 8765    # open http://localhost:8765/
```
Controls / 操作 (buttons 环绕 Orbit / 漫游 Walk / 飞行 Fly, top right):
- **Orbit 环绕:** drag rotate · wheel zoom · right-drag pan.
- **Walk 漫游 (Tab):** WASD · click for mouse look (Esc releases) · Shift run · R/F lift up/down inside a lift car.
- **Fly 飞行 (F toggles):** free 6-DoF camera, no gravity, no collision (passes through walls). Click for mouse look, Esc releases ·
  WASD along the view direction · Space/E up · Q/C down · Shift ×3 boost · wheel or +/− base speed · 1–5 preset viewpoints
  (forecourt, arch, courtyard, crown, aerial) · T auto tour (arch → courtyard → over the crown → around). Entering fly keeps the
  current camera pose; switching to Walk drops you onto the floor below. Touch: one-finger drag looks, two-finger drag moves,
  ▲/▼ buttons rise/sink.

## Pipeline / 流程

Every dimension lives in `params.json` (tagged measured / inferred in `params_table.md`); all geometry is generated from it.
所有尺寸都在 `params.json`（`params_table.md` 标注“图纸量取 / 推断”），几何体全部由参数生成。

```bash
COMPARE_ROUNDS=4 ./run_all.sh
```
1. `compare/ref_extract.py` – reference elevation silhouettes (needs `ref/sheet_elevations.png`, not included in this repo).
2. `compare/compare_loop.py` – silhouette IoU + skyline error vs the reference (design target: front/rear stretched by
   `global.ref_stretch_x` for the widened plaza, side elevations strict via `ref_stretch_y` = 1), coordinate-descent tuning of the knobs, log in `compare_log.md`.
3. `build.py` (+ `src/geom.py`, `src/detail.py`) – Blender 5 headless build: exterior, interior (rooms/doors/stairs/lifts),
   `building.blend`, `building.glb`, `spaces.json`.
4. `src/render_clay.py` – true-ortho clay elevations, hero views, tower close-up.
5. `check/circulation_check.py` – circulation graph BFS + door/wall raycasts + stair riser/tread/headroom + lift shafts,
   with a negative test (blocked door must make the check fail) → `circulation_report.md`.
6. gltf-transform – Meshopt + GPU instancing → `web/building_opt.glb` (< 25 MiB).
7. `walk/walk_test.py` – headless Chrome walk through the web preview (WASD keys, penetration rays, stuck detection, doors).
   `walk/fly_test.py` – headless fly-mode test (pose hand-over, no gravity/collision, over the crown, through the courtyard, speed, presets, tour, drop to walk).
8. `src/final_render.py` – Cycles mood render (AgX, volumetric arch beams, pink/cyan rims, glowing plaza).

管线：参考立面剪影 → 剪影对比与参数自动调优 → Blender 无头建模（外观+室内）→ 白模渲染 → 流线检查（含反向测试）→
glTF 压缩导出 → 无头 Chrome 漫游测试 → 氛围渲染。每次修改脚本后整条管线重跑，保证不回退。

Requirements / 依赖: Blender 5.x, Python 3 (numpy, scipy, Pillow, matplotlib, playwright), Node + `@gltf-transform/cli`, Chrome.

## Layout / 目录
- `web/` – static site (deployed) / 静态站点（部署目录）
- `build.py`, `src/` – Blender generation / Blender 生成脚本
- `check/` – circulation checks / 流线检查
- `compare/` – silhouette compare + tuning loop / 剪影对比与调参
- `walk/` – headless walk + fly tests / 漫游、飞行测试
- `docs/` – renders, change notes, walk + fly results (`docs/fly/` screenshots) / 渲染图、变更说明、漫游与飞行结果

Deploy mirrors [cyber-louvre](https://github.com/xuzhiming/cyber-louvre): push `main` → GitHub Actions → Cloudflare Pages.
