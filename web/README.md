# Web preview / 网页预览

Static three.js site (no build step). Serve this folder and open `index.html`:

```bash
python3 -m http.server 8765 --directory web   # http://localhost:8765/
```

- `index.html` + `main.js`: three modes, switched with the top-right buttons 环绕 Orbit / 漫游 Walk / 飞行 Fly.
  - **Orbit:** drag rotate, wheel zoom, right-drag pan.
  - **Walk (Tab):** WASD, click for mouse look (Esc releases), Shift run, R/F lift up/down inside a lift car; capsule collision on a
    three-mesh-bvh BVH plus the door leaves in their current position.
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
- **Automatic doors 自动门 (all modes):** all 92 real doors are automatic: 40 interior/gallery/tower doors, 2 exterior side-wing
  doors and 50 lift doors. Each one is a split double sliding leaf (glazed panel in a clay frame) that slides into the wall
  pockets. It opens when you come within 2.8 m (walk: the player, on that floor) or 3.0 m (fly: the camera). Opening and
  closing are eased (≈0.45 s open, ≈0.7 s close), with a 0.7 s hold after you leave, and the frame shows a faint cool rim glow
  while the door is active. Closed leaves are solid and block you; the gap opens up as they slide. **Lift doors** open only
  while the car stands at that floor. Walking up to one calls the nearest car (3 m/s), and a car leaves only after its doors
  have shut. The 14 open archways have no leaves: the arch portal, the tunnel→courtyard mouth, 2 tunnel side openings and
  10 courtyard→gallery arcade openings.
- **Style 风格 (V or the 风格 Style button):** two looks, **渲染 Render** (the default) and **白模 Clay**, the v13 white model.
  Render uses the model's own colours, metal/roughness and glow (exported in the glb) on a dark blue-violet gradient
  background with fog and a tight bloom. Emissive strengths, the arch and crown lights and the fog are kept low enough
  that the crescent, floors and facade stay readable. It adds pastel rings on the forecourt plaza, a warm glow in the arch
  and a pastel halo around the crown. Clay swaps in two plain white materials and the old daylight, and is not dimmed with
  Render. Walk, fly and the automatic doors work the same in both looks. Use `?style=clay` to open in Clay.
- `building_opt.glb`: Meshopt-compressed, window surrounds as GPU instances (EXT_mesh_gpu_instancing). Door leaves are
  `DoorLeaf_<door id>_A|B` nodes whose extras are `door_id, door_type, leaf, slide, slide_axis, width, height, center, normal, lift_id, level`.
  Their meshes are baked in world space so they are never merged into instances.
- `spaces.json`: rooms, doors, stairs and lifts exported by the Blender build (used by the walk test hooks).
- `vendor/`: three.js r187 (+ EffectComposer / RenderPass / UnrealBloomPass / OutputPass) + three-mesh-bvh, imported through an import map with relative paths.

所有路径均为相对路径，可直接作为静态站点部署（Cloudflare Pages 等）。
