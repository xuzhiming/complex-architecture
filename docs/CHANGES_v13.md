# v13 — 所有的门设置为自动门 (every door is an automatic door)

## Audit (v12, before)
| | count |
|---|---|
| doors in `spaces.json` | 106 = 40 door + 2 ext_door + 50 lift_door + 12 opening + 2 open |
| `DoorLeaf_*` in `building.glb` | 42 (door + ext_door only; lift doors were built with `leaf=False`) |
| `DoorLeaf_*` surviving in `web/building_opt.glb` | **4** (D16, D35, D58, D63) |

gltf-transform `optimize --instance --instance-min 5` de-duplicated the 38 identical 1.8 m leaves into 29 anonymous
`EXT_mesh_gpu_instancing` nodes. That stripped their names and extras, so they were static decoration: not animated,
not in the door list, not collidable. That left **4 effective auto doors** in the preview, and the walk route only ever
passed 2 of them (D16, D63).

## Build (`build.py`)
- Every real door now gets leaves: `door`, `ext_door` and `lift_door` (`lift_module` no longer passes `leaf=False`).
  That is **92 doors and 184 leaves**.
- Each leaf is a split double sliding leaf `DoorLeaf_<door id>_A` / `_B`: a glazed panel (Clay_Recess) in a 6 cm clay frame,
  8 cm thick, on the wall centre line. Each half slides `(w-0.06)/2` along the wall tangent into the wall pocket.
- Each leaf carries glTF extras: `door_id, door_type, leaf, mode=slide, slide (open offset), slide_axis, width, height,
  center, normal`, plus `lift_id, level` on lift doors.
- Leaf meshes are baked in world space (object origin = world origin), so every mesh is unique. gltf-transform can no longer
  merge them into instances: all 184 leaves survive in `web/building_opt.glb` (0 instanced). The window instancing is unchanged.
- The open archways are left as they are, with no leaves (14):
  - `D00_forecourt__portal_tunnel` (arch portal) and `D01_portal_tunnel__courtyard` (tunnel mouth), both type `open`;
  - `D02/D03_portal_tunnel__gallery` (tunnel side openings) and `D04–D13_courtyard__gallery` (arcade bays), type `opening`.
- The wall openings are unchanged. Door leaves are skipped by the circulation check, as before.

## Web preview (`web/main.js`)
- **Door table:** leaves are grouped by `door_id` into 92 door objects and stored in an 8 m spatial hash. Each frame only
  doors in the 3×3 cells around the probe, plus currently animating doors, are updated (no raycasts).
- **Trigger:**
  - Walk mode: the player within 2.8 m horizontally, with feet in [floor−1.0, floor+1.6].
  - Fly mode: the camera within 3.0 m of the door centre.
  - Orbit mode: doors close.
- **Motion:** open at 2.2/s, close at 1.4/s, eased with smoothstep. The door holds open 0.7 s after the trigger is lost.
  The frame has a faint cool emissive rim while active.
- **Collision follows the leaves:** each leaf's current oriented box is solid for the walk capsule (circle vs OBB in plan,
  with vertical overlap). A closed door blocks; a sliding door lets you through once the gap clears the capsule.
- **Lifts:** every lift has a persistent car (`car`, `target`).
  - A lift door opens only when the car stands at that floor with no pending departure.
  - Walking up to a lift door calls the nearest car (only the nearest lift door in range calls, so a bank of three does
    not all come).
  - A car leaves only after its doors have shut (R/F inside the car, as before).
- **HUD** shows `自动门 auto doors 92 (active n)`.
- **Test hooks:** `__walk.doorList()`, `door(id)`, `activeDoors()`, `leafBlocks()`, `lift(id)`.

## Tests (`walk/walk_test.py`)
- **Coverage:** every `spaces.json` door of type door/ext_door/lift_door must map to exactly 2 animated (non-instanced) leaves
  A+B with slide > 0.3 m. Missing, bad and extra doors are listed, and so are the archways without leaves.
- **Scripted door pass (13 doors, all types):**
  - Doors covered: 2 exterior side-wing doors; gallery→W/E link; W link→hall; hall→core; E room s→n; an L1 room door;
    the tower link→lobby door; and lift doors at L0 (W lift), L1 (E lift, car called from L0) and L2 (tower lift 0,
    car called from L3).
  - Each pass: start closed → walk through → walk back out → the door closes after leaving.
  - Logged per door: trigger distance, open duration, crossings, gap at crossing, leaf blocks while closed, and close delay.
- **Fly check:** the camera 8 m away leaves the door shut, 2.2 m away opens it, and moving 9 m away closes it again.
- The passed-door check now uses real plane crossings, and requires the leaf gap at crossing ≥ 0.7 m (capsule 0.6 m + 0.1).
  It replaces the old "open ≥ 0.9 when within 0.9 m" check, which would wrongly flag a player waiting at a closed lift door.
