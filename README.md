# Complex Architecture / 复杂建筑

Procedural Blender building + three.js orbit/walk preview.

## Live preview

After Cloudflare Pages deploy: https://complex-architecture.pages.dev

Local:
```bash
cd web && python3 -m http.server 8765
# open http://localhost:8765/
```

Controls: Orbit / Walk · WASD · mouse look · Shift run · R/F lift

## Pipeline

```bash
COMPARE_ROUNDS=6 ./run_all.sh   # rebuild, silhouette compare, circulation, export, walk test, mood render
```

Requires Blender 4+/5+, Node (`gltf-transform`), Playwright/Chrome for walk test.

## Layout

- `web/` — static three.js site (deployed)
- `build.py`, `src/` — Blender bpy generation
- `check/` — circulation graph + ray tests
- `compare/` — silhouette IoU loop
- `walk/` — headless Chrome walk test
- `docs/` — clay elevations + mood render

Deploy mirrors [cyber-louvre](https://github.com/xuzhiming/cyber-louvre): push `main` → GitHub Actions → Cloudflare Pages.
