# Web preview / 网页预览

Static three.js site (no build step). Serve this folder and open `index.html`:

```bash
python3 -m http.server 8765 --directory web   # http://localhost:8765/
```

- `index.html` + `main.js`: three modes, switched with the top-right buttons 环绕 Orbit / 漫游 Walk / 飞行 Fly.
  - **Orbit:** drag rotate, wheel zoom, right-drag pan.
  - **Walk (Tab):** WASD, click for mouse look (Esc releases), Shift run, R/F lift up/down inside a lift car; capsule collision on a
    three-mesh-bvh BVH, automatic sliding doors.
  - **Fly (F toggles; in a lift car F stays "lift down"):** free 6-DoF camera, no gravity, no collision.

    | input | action |
    |---|---|
    | click / Esc | capture / release mouse look |
    | W A S D | move along the view direction / strafe |
    | Space or E / Q or C | up / down |
    | Shift | ×3 speed boost |
    | wheel, + / − | base speed (1–200 m/s, shown in the HUD) |
    | 1–5 | presets: forecourt, arch, courtyard, crown, aerial |
    | T | auto tour (arch → tunnel → courtyard → over the crown → around); any move key stops it |
    | touch | one-finger drag = look, two-finger drag = forward/back + strafe, ▲/▼ = up/down |

    Movement eases in and out (0.18 s). Entering fly keeps the current orbit/walk camera pose; Walk from fly drops onto the
    first floor with head room below the camera (else the forecourt spawn); Orbit from fly keeps the view.
- `building_opt.glb`: Meshopt-compressed, window surrounds as GPU instances (EXT_mesh_gpu_instancing).
- `spaces.json`: rooms, doors, stairs and lifts exported by the Blender build (used by the walk test hooks).
- `vendor/`: three.js r187 + three-mesh-bvh, imported through an import map with relative paths.

所有路径均为相对路径，可直接作为静态站点部署（Cloudflare Pages 等）。
