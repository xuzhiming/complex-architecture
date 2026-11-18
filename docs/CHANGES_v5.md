# v5 changes (geometry code + params + pipeline)

Scores (mean of 4 elevations): v4 IoU 0.8646 / skyline 2.57 m  ->  v5 IoU **0.9311** / skyline **1.67 m** (score 0.8389 -> 0.9143)
(per view IoU/skyline: front 0.940/1.03 m, rear 0.933/1.10 m, left 0.923/2.38 m, right 0.928/2.19 m)
Auto-loop accepted: tower.cy -1, crescent.dy -0.8, masses.top_E -1, crescent.spread +0.025.

Geometry (build.py, v4 kept as build_v4.py)
- Crescent rewritten: Catmull-Rom centreline fitted from per-height runs of the reference front + left silhouettes,
  tapering diameter list (6.0 -> 0.3 m), flattened 24-sided section, post + drum; stays removed. Knobs: d_scale, spread, rise.
  Optional mirrored second horn (`crescent.horn2`) implemented but OFF: the roof plan shows two horns, the elevations show one.
- Top-centre massing: new central mass M_C, M_E/M_WT reshaped, canopy heights/radii refit; knobs masses.top_z, tower.cy, tower.crown_dz.
- Tree columns: narrow foot (base_r 2.4) -> shaft 1.6 -> late power flare to 11.5 m under a knife-edge deck lip (deck_edge_z 23.0).
- Podium top storey = open arched loggia band all round (pitch 4.6 m, 3.5 m deep) with a recessed back wall and lit panels.
- Interior: wing halls/rooms/cores stacked on every podium level (L0..L3) served by stair + lift; slabs cut for both cores.

Pipeline
- compare loop: 23 knobs, log prefix support (v4 log + v5 geometry rounds G1-G5 + loop rounds in compare_log.md).
- circulation check + walk test look doors up by space pair (ids renumber with the plan).
- web/main.js doorsNear() test hook now filters by storey (it falsely reported closed doors stacked above the route).
- final_render.py r3: AgX Medium High Contrast, dimmer arch, 7 volumetric beams fanning out of the arch + haze box,
  saturated pink/cyan/violet rim strips, warm window cells (loggia brighter), filled elliptical plaza glow.

Circulation gate caught a regression
- After the tuning loop moved the tower 1 m south, the C_dome canopy intruded into tower floor T_L6 (headroom 1.44 m) -> CIRCULATION FAIL.
- Fixed in build.py: canopies that reach into the tower are boolean-trimmed to the tower's inner face. Re-run: PASS
  (55/55 spaces, 102/102 doors, 32/32 flights, 5/5 lift shafts, negative test caught), WALK PASS (0 penetrations, 0 stuck).
- final_render.py: + compositor Fog Glow bloom (threshold 1.2), arch burst emission 3.5 -> 2.4, sky 0.9 -> 1.8, exposure 0.
