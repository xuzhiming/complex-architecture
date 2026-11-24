# Locator map

Approved implementation of the lower-left plan. North is up. The map stays visible in Orbit, Walk and Fly. It is a schematic, not a surveyed floor plan.

## Coordinates

Blender `(x, y, z)` becomes three.js `(x, z, -y)`. `params.json` `meta.front_axis` is `-Y` (south) and `up` is `+Z`, so `+Y` is north. Walk and fly yaw `0` looks along three.js `-Z`, which is north. Positive yaw turns toward west. The map uses the same conversion the HUD already prints: east `x`, north `y = -three.z`, height `z = three.y`.

## What is drawn

`shapesFromParams` reads only `params.json`:

- Deck and podium are the superellipses `build.py` already uses (`half_w`, `half_d`, `cy`, `n`).
- Wing halls, rooms and cores are the axis-aligned boxes under `wings`.
- The court is the ellipse `courtyard.r` by `courtyard.r * courtyard.kx`.
- The arch mouth is `arch.hw` deep by `arch.portal_depth`, starting at the podium south edge `yFront(arch.cx)`.
- The tunnel is `tunnel.hw` wide from that south edge to `courtyard.cy - courtyard.r`.
- The tower is the base drum circle. Each canopy contributes its `drum_r` circle only.
- Saucer roof ellipses, the crescent and the plaza rings are omitted. The rings are not dimensions in `params.json`.

`spaces.json` probes are not polygons and are not drawn. The caption never names a room. The cached plan is marked `示意`.

The frame is Blender x `-96..96`, y `-100..72`, which contains the deck, the tower and the forecourt spawn. It does not follow the camera.

## Marker

- Walk: feet `(player.x, -player.z)` and `feetY()`, arrow from `player.yaw`. Caption starts with `漫游`.
- Fly: camera `(fly.x, -fly.z)` and camera height `fly.y`, arrow from `fly.yaw`. Caption starts with `飞行`.
- Orbit: caption `环绕 · 非玩家位置`. No arrow, including when the walk body is still the unset origin.
- A height within `0.4 m` of `i * global.floor_h` (through `tower.floors_top`) adds `L{i}`. Stairs and open air do not.
- Outside the frame, a tick sits on the frame edge toward the subject. The arrow is not moved to the building centre.

## Presentation

One 2D canvas, `#minimap`, created after the WebGL canvas so `querySelector('canvas')` stays the renderer. CSS: `172×148` px, `12` px from the left and bottom; `132×114` below `720` px wide; `112×96` below `480` px tall. `pointer-events: none`. Backing-store ratio is `min(devicePixelRatio, 2)`.

The plan is rasterised once per canvas size. Later frames blit that image and stroke the arrow. No model traversal, no polygon rebuild, no `innerHTML`, no second WebGL context, no click teleport.

## Packaging

`dist/minimap.js` and `dist/params.json` are part of the Pages bundle. `tools/check_pages_dist.py` checks they exist and match the repo bytes. A missing file must fail the pack test, not merely return HTTP 200.

## Out of scope

Arch-edge smoothing, window openings, geometry, doors, collision, textures, lighting, and `sync_gh_repo.py`.
