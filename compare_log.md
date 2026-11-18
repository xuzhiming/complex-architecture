# Silhouette compare log

Reference: `ref/sheet_elevations.png` (4 elevation panels). No dimension lines on the sheets, so each reference panel is scaled uniformly until
its silhouette bbox height equals `global.H_total` (ground lines anchored, bbox centres aligned). Model silhouettes: true orthographic renders
at 0.2 m/px. Score = mean IoU - 0.01 x mean skyline error (m). Overlays: red = reference only, blue = model only.

## v4 result (previous delivery, params-only tuning)
- mean IoU **0.8646**, skyline **2.57 m**, score 0.8389 (front 0.861/1.51 m, rear 0.853/1.94 m, left 0.870/3.55 m, right 0.874/3.28 m)
- full v4 log kept in `compare_log_v4.md`

# v5 - geometry-code rounds (manual, guided by the red/blue regions)
Each round = edit `build.py` / params, rebuild silhouettes, score (`compare/quick_eval.py`).

## G1 - crescent rebuilt, tree columns, deck (build.py)
- crescent: new centreline (11 points measured from the front + left elevation runs, z 56->77 m), measured diameter profile 6-7 m at the
  base tapering to 0.3 m at the tip, rounder section, no bank; the two tie-stays to the crown removed (model-only blue lines);
  new knobs `crescent.spread/rise/d_scale/flat/dz`, optional mirrored 2nd horn `crescent.horn2`
- tree columns: new profile = narrow foot (base_r 2.4) + straight 1.6 m shaft to z 14, trumpet flare only over the top 8 m (flare_r 11.5, power 1.1);
  side columns pulled in from x +/-53 to +/-48.3
- deck: knife-edge fascia at `deck_edge_z` 23.0 m, deck_half_w 61.4
- score **0.8814** (IoU 0.8997, sky 1.84 m) | front 0.905/1.07 | rear 0.895/1.37 | left 0.898/2.54 | right 0.900/2.38

## G2 - top-centre massing + crown
- new infill mass `M_C` (x -7, y 19.5, r 5, top 59.5 m) fills the reference-only block under the crescent; `M_E` raised to 58.5 m
- crescent shifted +1.2 m in y / +0.5 m in x on its rising limb; tower crown at 66.0 m with a low 1.2 m dome (was 3 m)
- `E_high` canopy drum moved inboard (x 40 -> 34), `W_tall` canopy lowered to 55 m
- score **0.9050** (IoU 0.9234, sky 1.84 m) | front 0.934/1.09 | rear 0.921/1.30 | left 0.917/2.57 | right 0.921/2.39

## G3 - small fixes
- `M_WT` r 6 -> 5 and moved to y 12; `E_high` drum r 5 at x 35; `W_tall` 54 m; crown 65.6 m
- score **0.9054** (IoU 0.9241, sky 1.87 m)

## G4 - deck profile
- concave soffit rising from deck_bot 20.5 m to a 0.35 m lip at 23.0 m; thin plate back to the wall line, deck_top 24 m only inboard;
  drums/masses now start inside the deck (no gaps)
- score **0.9065** (IoU 0.9252, sky 1.87 m) | front 0.937/1.14 | rear 0.924/1.44 | left 0.916/2.68 | right 0.924/2.24

## G5 - podium open arcades + stacked wing floors (no silhouette change expected)
- top podium storey (13.5 m -> deck) is now an open arcaded loggia: arches cut through the shell every 5 m (3.4 m wide, 5.3 m high),
  3.5 m deep gallery, back wall with lit panels; the saw-tooth recesses in the (now thin) deck fascia removed
- wings get floors on every podium level (0 / 4.5 / 9 / 13.5 m): hall + 2 rooms + core per level, stair + lift serving all levels;
  top-storey rooms pulled 4.5 m in behind the loggia
# v5 run 1 - auto-tuning loop on the new geometry knobs (run_all.sh, 5 rounds)

# Silhouette compare log

Reference: `ref/sheet_elevations.png` (4 elevation panels). The sheets carry **no dimension lines**, so each reference panel
is scaled uniformly until its silhouette bbox height equals `global.H_total` (ground lines anchored, bbox centres aligned).
Model silhouettes are true orthographic renders at 0.2 m/px. Score = mean IoU - 0.01 x mean skyline error (m).
Each round: the 3x3 XOR-error regions (summed over the 4 views) are ranked; knobs that drive the worst regions are tried at +/- step
(parallel builds); the best improving candidate is accepted, otherwise those knob steps are halved.

## Round 0 (initial params)
- mean IoU **0.9281**, mean skyline err **1.74 m**, score 0.9108
- per view (IoU/skyline): front 0.939/1.09m | rear 0.932/1.16m | left 0.916/2.60m | right 0.926/2.09m

## Round 1
- worst regions: highC (0.054), midR (0.047), midL (0.041)
- candidates (12 builds, 78 s):
  - `tower.cy` +1.000: score 0.9075 (IoU 0.9254, sky 1.79 m)
  - `tower.cy` -1.000: score 0.9118 (IoU 0.9293, sky 1.74 m)
  - `canopy_scale` +0.040: score 0.9107 (IoU 0.9279, sky 1.71 m)
  - `canopy_scale` -0.040: score 0.9085 (IoU 0.9282, sky 1.97 m)
  - `canopies.z_shift` +0.800: score 0.9092 (IoU 0.9271, sky 1.79 m)
  - `canopies.z_shift` -0.800: score 0.9073 (IoU 0.9256, sky 1.83 m)
  - `mass_scale` +0.060: score 0.8792 (IoU 0.8969, sky 1.77 m)
  - `mass_scale` -0.060: score 0.8838 (IoU 0.9016, sky 1.77 m)
  - `masses.top_E` +1.000: score 0.9097 (IoU 0.9274, sky 1.76 m)
  - `masses.top_E` -1.000: score 0.9119 (IoU 0.9290, sky 1.71 m)
  - `canopies.west_dx` +1.000: score 0.9097 (IoU 0.9274, sky 1.77 m)
  - `canopies.west_dx` -1.000: score 0.9105 (IoU 0.9286, sky 1.81 m)
- **accepted** `tower.cy` -1.000 -> mean IoU **0.9293**, skyline **1.74 m**, score 0.9118
- per view: front 0.939/1.09m | rear 0.932/1.16m | left 0.920/2.45m | right 0.926/2.27m

## Round 2
- worst regions: highC (0.056), midR (0.046), midL (0.042)
- candidates (12 builds, 86 s):
  - `canopies.east_dx` +1.000: score 0.9103 (IoU 0.9284, sky 1.81 m)
  - `canopies.east_dx` -1.000: score 0.9106 (IoU 0.9293, sky 1.87 m)
  - `tower.cx` +1.000: score 0.9120 (IoU 0.9292, sky 1.71 m)
  - `tower.cx` -1.000: score 0.9111 (IoU 0.9288, sky 1.77 m)
  - `tower.r_scale` +0.030: score 0.9103 (IoU 0.9279, sky 1.76 m)
  - `tower.r_scale` -0.030: score 0.9121 (IoU 0.9294, sky 1.74 m)
  - `tower.crown_z` +0.600: score 0.9114 (IoU 0.9287, sky 1.73 m)
  - `tower.crown_z` -0.600: score 0.9097 (IoU 0.9273, sky 1.77 m)
  - `crescent.dz` +0.800: score 0.9068 (IoU 0.9258, sky 1.90 m)
  - `crescent.dz` -0.800: score 0.9036 (IoU 0.9231, sky 1.94 m)
  - `crescent.spread` +0.050: score 0.9110 (IoU 0.9286, sky 1.76 m)
  - `crescent.spread` -0.050: score 0.9102 (IoU 0.9293, sky 1.91 m)
- no improvement -> halved steps of tried knobs

## Round 3
- worst regions: highC (0.056), midR (0.046), midL (0.042)
- candidates (12 builds, 58 s):
  - `crescent.rise` +0.060: score 0.9026 (IoU 0.9227, sky 2.00 m)
  - `crescent.rise` -0.060: score 0.9000 (IoU 0.9205, sky 2.05 m)
  - `crescent.d_scale` +0.100: score 0.9112 (IoU 0.9287, sky 1.75 m)
  - `crescent.d_scale` -0.100: score 0.9113 (IoU 0.9290, sky 1.77 m)
  - `crescent.dx` +0.800: score 0.9121 (IoU 0.9294, sky 1.73 m)
  - `crescent.dx` -0.800: score 0.9091 (IoU 0.9273, sky 1.82 m)
  - `crescent.dy` +0.800: score 0.9096 (IoU 0.9273, sky 1.77 m)
  - `crescent.dy` -0.800: score 0.9127 (IoU 0.9303, sky 1.76 m)
  - `masses.top_C` +1.000: score 0.9106 (IoU 0.9281, sky 1.74 m)
  - `masses.top_C` -1.000: score 0.9131 (IoU 0.9306, sky 1.74 m)
  - `masses.r_WT` +0.600: score 0.9120 (IoU 0.9294, sky 1.74 m)
  - `masses.r_WT` -0.600: score 0.9116 (IoU 0.9291, sky 1.75 m)
- **accepted** `crescent.dy` -0.800 -> mean IoU **0.9303**, skyline **1.76 m**, score 0.9127
- per view: front 0.939/1.09m | rear 0.932/1.16m | left 0.923/2.49m | right 0.928/2.31m

## Round 4
- worst regions: highC (0.053), midR (0.046), midL (0.042)
- candidates (12 builds, 44 s):
  - `tower.cy` +1.000: score 0.9104 (IoU 0.9281, sky 1.77 m)
  - `tower.cy` -1.000: score 0.9118 (IoU 0.9302, sky 1.84 m)
  - `canopy_scale` +0.040: score 0.9127 (IoU 0.9301, sky 1.74 m)
  - `canopy_scale` -0.040: score 0.9104 (IoU 0.9304, sky 2.00 m)
  - `canopies.z_shift` +0.800: score 0.9110 (IoU 0.9291, sky 1.81 m)
  - `canopies.z_shift` -0.800: score 0.9092 (IoU 0.9279, sky 1.86 m)
  - `mass_scale` +0.060: score 0.8821 (IoU 0.9000, sky 1.79 m)
  - `mass_scale` -0.060: score 0.8867 (IoU 0.9047, sky 1.80 m)
  - `masses.top_E` +1.000: score 0.9117 (IoU 0.9296, sky 1.79 m)
  - `masses.top_E` -1.000: score 0.9138 (IoU 0.9311, sky 1.73 m)
  - `canopies.west_dx` +1.000: score 0.9116 (IoU 0.9296, sky 1.80 m)
  - `canopies.west_dx` -1.000: score 0.9124 (IoU 0.9308, sky 1.84 m)
- **accepted** `masses.top_E` -1.000 -> mean IoU **0.9311**, skyline **1.73 m**, score 0.9138
- per view: front 0.940/1.06m | rear 0.933/1.14m | left 0.924/2.46m | right 0.928/2.28m

## Round 5
- worst regions: highC (0.052), midR (0.046), midL (0.042)
- candidates (12 builds, 41 s):
  - `canopies.east_dx` +0.500: score 0.9134 (IoU 0.9307, sky 1.73 m)
  - `canopies.east_dx` -0.500: score 0.9132 (IoU 0.9313, sky 1.80 m)
  - `tower.cx` +0.500: score 0.9141 (IoU 0.9313, sky 1.72 m)
  - `tower.cx` -0.500: score 0.9134 (IoU 0.9309, sky 1.75 m)
  - `tower.r_scale` +0.015: score 0.9130 (IoU 0.9305, sky 1.75 m)
  - `tower.r_scale` -0.015: score 0.9140 (IoU 0.9314, sky 1.74 m)
  - `tower.crown_z` +0.300: score 0.9137 (IoU 0.9311, sky 1.73 m)
  - `tower.crown_z` -0.300: score 0.9125 (IoU 0.9301, sky 1.75 m)
  - `crescent.dz` +0.400: score 0.9118 (IoU 0.9297, sky 1.79 m)
  - `crescent.dz` -0.400: score 0.9116 (IoU 0.9294, sky 1.78 m)
  - `crescent.spread` +0.025: score 0.9143 (IoU 0.9311, sky 1.67 m)
  - `crescent.spread` -0.025: score 0.9129 (IoU 0.9310, sky 1.82 m)
- **accepted** `crescent.spread` +0.025 -> mean IoU **0.9311**, skyline **1.67 m**, score 0.9143
- per view: front 0.940/1.03m | rear 0.933/1.10m | left 0.923/2.38m | right 0.928/2.19m

## Final
- mean IoU **0.9311**, mean skyline error **1.67 m**, score 0.9143
- per view: front 0.940/1.03m | rear 0.933/1.10m | left 0.923/2.38m | right 0.928/2.19m
- roof plan loose check (oblique sheet, bbox-fitted, indicative only): IoU 0.563
- overlays: `compare/final/overlay_sheet.png` (red = reference only, blue = model only, grey = overlap)
- tuned params written back to `params.json` (start values kept in `params_initial.json`)
# v5 run 2 - re-run after canopy-into-tower trim fix (run_all.sh, 2 rounds)

# Silhouette compare log

Reference: `ref/sheet_elevations.png` (4 elevation panels). The sheets carry **no dimension lines**, so each reference panel
is scaled uniformly until its silhouette bbox height equals `global.H_total` (ground lines anchored, bbox centres aligned).
Model silhouettes are true orthographic renders at 0.2 m/px. Score = mean IoU - 0.01 x mean skyline error (m).
Each round: the 3x3 XOR-error regions (summed over the 4 views) are ranked; knobs that drive the worst regions are tried at +/- step
(parallel builds); the best improving candidate is accepted, otherwise those knob steps are halved.

## Round 0 (initial params)
- mean IoU **0.9311**, mean skyline err **1.67 m**, score 0.9143
- per view (IoU/skyline): front 0.940/1.03m | rear 0.933/1.10m | left 0.923/2.38m | right 0.928/2.19m

## Round 1
- worst regions: highC (0.051), midR (0.046), midL (0.042)
- candidates (12 builds, 53 s):
  - `tower.cy` +1.000: score 0.9121 (IoU 0.9289, sky 1.68 m)
  - `tower.cy` -1.000: score 0.9131 (IoU 0.9307, sky 1.77 m)
  - `canopy_scale` +0.040: score 0.9143 (IoU 0.9308, sky 1.65 m)
  - `canopy_scale` -0.040: score 0.9120 (IoU 0.9311, sky 1.91 m)
  - `canopies.z_shift` +0.800: score 0.9127 (IoU 0.9299, sky 1.72 m)
  - `canopies.z_shift` -0.800: score 0.9108 (IoU 0.9286, sky 1.78 m)
  - `mass_scale` +0.060: score 0.8827 (IoU 0.9000, sky 1.73 m)
  - `mass_scale` -0.060: score 0.8872 (IoU 0.9046, sky 1.74 m)
  - `masses.top_E` +1.000: score 0.9133 (IoU 0.9303, sky 1.70 m)
  - `masses.top_E` -1.000: score 0.9148 (IoU 0.9314, sky 1.66 m)
  - `canopies.west_dx` +1.000: score 0.9132 (IoU 0.9303, sky 1.71 m)
  - `canopies.west_dx` -1.000: score 0.9140 (IoU 0.9315, sky 1.75 m)
- no improvement -> halved steps of tried knobs

## Round 2
- worst regions: highC (0.051), midR (0.046), midL (0.042)
- candidates (12 builds, 50 s):
  - `canopies.east_dx` +1.000: score 0.9127 (IoU 0.9302, sky 1.74 m)
  - `canopies.east_dx` -1.000: score 0.9130 (IoU 0.9311, sky 1.80 m)
  - `tower.cx` +1.000: score 0.9146 (IoU 0.9310, sky 1.64 m)
  - `tower.cx` -1.000: score 0.9134 (IoU 0.9305, sky 1.71 m)
  - `tower.r_scale` +0.030: score 0.9128 (IoU 0.9297, sky 1.69 m)
  - `tower.r_scale` -0.030: score 0.9145 (IoU 0.9312, sky 1.67 m)
  - `tower.crown_z` +0.600: score 0.9138 (IoU 0.9305, sky 1.67 m)
  - `tower.crown_z` -0.600: score 0.9122 (IoU 0.9291, sky 1.70 m)
  - `crescent.dz` +0.800: score 0.9081 (IoU 0.9265, sky 1.85 m)
  - `crescent.dz` -0.800: score 0.9072 (IoU 0.9256, sky 1.84 m)
  - `crescent.spread` +0.050: score 0.9132 (IoU 0.9306, sky 1.74 m)
  - `crescent.spread` -0.050: score 0.9129 (IoU 0.9310, sky 1.82 m)
- no improvement -> halved steps of tried knobs

## Final
- mean IoU **0.9311**, mean skyline error **1.67 m**, score 0.9143
- per view: front 0.940/1.03m | rear 0.933/1.10m | left 0.923/2.38m | right 0.928/2.19m
- roof plan loose check (oblique sheet, bbox-fitted, indicative only): IoU 0.563
- overlays: `compare/final/overlay_sheet.png` (red = reference only, blue = model only, grey = overlap)
- tuned params written back to `params.json` (start values kept in `params_initial.json`)

### Note on the v5 runs (circulation gate)
- Run 1 (5 rounds, accepted tower.cy -1, crescent.dy -0.8, masses.top_E -1, crescent.spread +0.025) produced **CIRCULATION FAIL**:
  space T_L6 headroom 1.44 m - the C_dome canopy reached into the tower interior at z 28.4 m once the tower moved 1 m south.
- Fix in geometry code (build.py): canopies that reach into the tower are boolean-trimmed to the tower's inner face.
- Run 2 (2 more rounds, no further improving step): silhouette unchanged (IoU 0.9311 / skyline 1.67 m), CIRCULATION PASS
  (55/55 spaces, 102/102 doors, 32/32 flights, negative test caught), WALK PASS (0 penetrations, 0 stuck).

# v6 - structure refinement + user-widened design

## S1 - side-view skyline fix (params, before the detail work), scored against the strict reference
Per-4-m skyline tables of the LEFT/RIGHT views (`compare/skyline_diff.py`) showed (a) the front canopies stopped short in y
(ref has a z~34 lip out to y -48 and a z~43 lip out to y -40) and (b) a 2 m-too-high plateau at y -10..+1 from E_high / W_tall,
while the front elevation needs those caps at 57-58 m. Resolution: the two tall capped towers sit BEHIND the courtyard (y +14,
hidden behind the tower in the side views, as in the roof plan), and a broad mass (M_W) carries the 55 m side plateau.
- W_big ry 20->23, W_low1 z +1 / ry 17->21, E_high + W_tall cy -> +14, W_tall z 52.8->56, M_W -> (-14,-4) r 11 z1 54.4, M_E z1 57.5->54.5
- result (strict reference): IoU 0.9311 -> **0.9366**, skyline 1.67 -> **1.03 m**; LEFT 2.38 -> 1.33 m, RIGHT 2.19 -> 1.12 m

## S2 - geometry-code detail (build.py, src/geom.py, src/detail.py) - mostly sub-silhouette
Instanced arched / tall-rect windows on tower and every drum (linked duplicates -> GPU instancing in the glb), solid clay drums,
thick rounded floor belts, buttress pilasters, cantilever belts with brackets, rotating sector balconies, crown under-disc + lantern,
lens canopies with rounded fascia nose + underside rib soffits, column-cluster side towers with trumpet flares, ribbed tree-column
heads, rounded deck nose, 4-layer archivolts + keystone + imposts, blade-section crescent, slender bridges.

## S3 - USER DESIGN CHANGE: widened building (reference no longer the strict target for width)
The user asked for a clearly larger central courtyard/plaza and a wider building. Changes: podium/deck half-width x1.18,
wings shifted 8 m outward, canopies/masses/columns x1.18 (canopy rx x1.18), courtyard r 16.5 -> 24 m (about 58 m across incl.
gallery) and centre y 3 -> -2, tower moved back 3.5 m (rear centre kept), crescent re-seated (its post must clear the courtyard void;
enforced in build.py), M_C/M_E2 masses fill the tower shoulders, arch half-width 20 -> 23 m, bridges much thinner.
- strict reference after widening: IoU **0.8368**, skyline **5.63 m** (expected: the reference is narrower)
- the compare now uses the DESIGN TARGET = reference FRONT/REAR elevations stretched x1.18 (`global.ref_stretch_x`; side views
  unchanged; `REF_STRETCH_X=1` gives the strict reference). Against the target before tuning: IoU 0.9016, skyline 2.59 m.
# Silhouette compare log

Reference: `ref/sheet_elevations.png` (4 elevation panels). The sheets carry **no dimension lines**, so each reference panel
is scaled uniformly until its silhouette bbox height equals `global.H_total` (ground lines anchored, bbox centres aligned).
Model silhouettes are true orthographic renders at 0.2 m/px. Score = mean IoU - 0.01 x mean skyline error (m).
Each round: the 3x3 XOR-error regions (summed over the 4 views) are ranked; knobs that drive the worst regions are tried at +/- step
(parallel builds); the best improving candidate is accepted, otherwise those knob steps are halved.

## Round 0 (initial params)
- mean IoU **0.8994**, mean skyline err **2.69 m**, score 0.8725
- per view (IoU/skyline): front 0.926/1.75m | rear 0.921/1.60m | left 0.872/3.90m | right 0.877/3.52m

## Round 1
- worst regions: highC (0.106), highR (0.051), midR (0.051)
- candidates (12 builds, 78 s):
  - `tower.crown_z` +0.600: score 0.8719 (IoU 0.8988, sky 2.69 m)
  - `tower.crown_z` -0.600: score 0.8720 (IoU 0.8988, sky 2.68 m)
  - `crescent.dz` +0.800: score 0.8711 (IoU 0.8986, sky 2.75 m)
  - `crescent.dz` -0.800: score 0.8691 (IoU 0.8968, sky 2.77 m)
  - `crescent.spread` +0.050: score 0.8724 (IoU 0.8995, sky 2.70 m)
  - `crescent.spread` -0.050: score 0.8725 (IoU 0.8994, sky 2.70 m)
  - `crescent.rise` +0.060: score 0.8686 (IoU 0.8969, sky 2.83 m)
  - `crescent.rise` -0.060: score 0.8672 (IoU 0.8956, sky 2.84 m)
  - `crescent.d_scale` +0.100: score 0.8734 (IoU 0.9000, sky 2.66 m)
  - `crescent.d_scale` -0.100: score 0.8714 (IoU 0.8987, sky 2.73 m)
  - `crescent.dy` +0.800: score 0.8706 (IoU 0.8985, sky 2.80 m)
  - `crescent.dy` -0.800: score 0.8749 (IoU 0.9008, sky 2.59 m)
- **accepted** `crescent.dy` -0.800 -> mean IoU **0.9008**, skyline **2.59 m**, score 0.8749
- per view: front 0.926/1.75m | rear 0.921/1.60m | left 0.875/3.69m | right 0.881/3.32m

## Round 2
- worst regions: highC (0.104), midR (0.051), highR (0.049)
- candidates (12 builds, 79 s):
  - `masses.top_E` +1.000: score 0.8744 (IoU 0.9005, sky 2.60 m)
  - `masses.top_E` -1.000: score 0.8749 (IoU 0.9008, sky 2.59 m)
  - `tower.r_scale` +0.030: score 0.8726 (IoU 0.8990, sky 2.64 m)
  - `tower.r_scale` -0.030: score 0.8771 (IoU 0.9025, sky 2.54 m)
  - `canopy_scale` +0.040: score 0.8733 (IoU 0.9003, sky 2.70 m)
  - `canopy_scale` -0.040: score 0.8746 (IoU 0.9013, sky 2.67 m)
  - `canopies.z_shift` +0.800: score 0.8711 (IoU 0.8982, sky 2.72 m)
  - `canopies.z_shift` -0.800: score 0.8683 (IoU 0.8956, sky 2.73 m)
  - `crescent.dx` +0.800: score 0.8760 (IoU 0.9017, sky 2.57 m)
  - `crescent.dx` -0.800: score 0.8731 (IoU 0.8995, sky 2.64 m)
  - `mass_scale` +0.060: score 0.8123 (IoU 0.8444, sky 3.22 m)
  - `mass_scale` -0.060: score 0.8198 (IoU 0.8523, sky 3.25 m)
- **accepted** `tower.r_scale` -0.030 -> mean IoU **0.9025**, skyline **2.54 m**, score 0.8771
- per view: front 0.926/1.75m | rear 0.921/1.60m | left 0.878/3.59m | right 0.884/3.22m

## Round 3
- worst regions: highC (0.105), midR (0.049), highR (0.049)
- candidates (12 builds, 66 s):
  - `masses.top_C` +1.000: score 0.8766 (IoU 0.9020, sky 2.54 m)
  - `masses.top_C` -1.000: score 0.8777 (IoU 0.9031, sky 2.54 m)
  - `masses.r_WT` +0.600: score 0.8771 (IoU 0.9025, sky 2.54 m)
  - `masses.r_WT` -0.600: score 0.8770 (IoU 0.9024, sky 2.54 m)
  - `canopies.west_dx` +1.000: score 0.8771 (IoU 0.9023, sky 2.52 m)
  - `canopies.west_dx` -1.000: score 0.8760 (IoU 0.9021, sky 2.60 m)
  - `canopies.east_dx` +1.000: score 0.8764 (IoU 0.9025, sky 2.61 m)
  - `canopies.east_dx` -1.000: score 0.8748 (IoU 0.9011, sky 2.63 m)
  - `tower.crown_z` +0.600: score 0.8765 (IoU 0.9019, sky 2.54 m)
  - `tower.crown_z` -0.600: score 0.8766 (IoU 0.9019, sky 2.53 m)
  - `crescent.dz` +0.800: score 0.8757 (IoU 0.9017, sky 2.60 m)
  - `crescent.dz` -0.800: score 0.8731 (IoU 0.8994, sky 2.63 m)
- **accepted** `masses.top_C` -1.000 -> mean IoU **0.9031**, skyline **2.54 m**, score 0.8777
- per view: front 0.928/1.75m | rear 0.922/1.60m | left 0.878/3.59m | right 0.884/3.22m

## Round 4
- worst regions: highC (0.101), midR (0.050), highR (0.049)
- candidates (12 builds, 66 s):
  - `crescent.spread` +0.050: score 0.8780 (IoU 0.9033, sky 2.53 m)
  - `crescent.spread` -0.050: score 0.8775 (IoU 0.9031, sky 2.56 m)
  - `crescent.rise` +0.060: score 0.8737 (IoU 0.9005, sky 2.68 m)
  - `crescent.rise` -0.060: score 0.8718 (IoU 0.8989, sky 2.70 m)
  - `crescent.d_scale` +0.100: score 0.8788 (IoU 0.9039, sky 2.51 m)
  - `crescent.d_scale` -0.100: score 0.8765 (IoU 0.9023, sky 2.58 m)
  - `crescent.dy` +0.800: score 0.8753 (IoU 0.9017, sky 2.64 m)
  - `crescent.dy` -0.800: score 0.8804 (IoU 0.9048, sky 2.44 m)
  - `masses.top_E` +1.000: score 0.8772 (IoU 0.9028, sky 2.55 m)
  - `masses.top_E` -1.000: score 0.8777 (IoU 0.9031, sky 2.54 m)
  - `tower.r_scale` +0.030: score 0.8757 (IoU 0.9016, sky 2.59 m)
  - `tower.r_scale` -0.030: score 0.8796 (IoU 0.9046, sky 2.50 m)
- **accepted** `crescent.dy` -0.800 -> mean IoU **0.9048**, skyline **2.44 m**, score 0.8804
- per view: front 0.928/1.75m | rear 0.922/1.60m | left 0.882/3.40m | right 0.888/3.01m

## Final
- mean IoU **0.9048**, mean skyline error **2.44 m**, score 0.8804
- per view: front 0.928/1.75m | rear 0.922/1.60m | left 0.882/3.40m | right 0.888/3.01m
- roof plan loose check (oblique sheet, bbox-fitted, indicative only): IoU 0.510
- overlays: `compare/final/overlay_sheet.png` (red = reference only, blue = model only, grey = overlap)
- tuned params written back to `params.json` (start values kept in `params_initial.json`)

## v6 summary (scores)
| stage | target | mean IoU | mean skyline | front / rear / left / right IoU |
|---|---|---|---|---|
| v5 final | strict ref | 0.9311 | 1.67 m | 0.940 / 0.933 / 0.923 / 0.928 |
| S1 side-skyline params | strict ref | 0.9366 | 1.03 m | 0.943 / 0.937 / 0.932 / 0.935 |
| S1+S2 detail code, not widened | strict ref | 0.9233 | 1.43 m | 0.920 / 0.916 / 0.926 / 0.931 |
| S3 widened, before tuning | design target (front/rear ref x1.18) | 0.9016 | 2.59 m | 0.928 / 0.924 / 0.874 / 0.880 |
| **v6 final (after 4 loop rounds)** | design target | **0.9048** | **2.44 m** | 0.928 / 0.922 / 0.882 / 0.888 |
| v6 final | strict ref (for the record) | 0.8526 | 6.09 m | 0.824 / 0.818 / 0.882 / 0.888 |
The S2 detail drop (0.9366 -> 0.9233 strict) comes mainly from the column-cluster side towers + trumpet flares and the blade-section
crescent in the front/rear elevations. The side views got worse after widening (tower moved back 3.5 m, crescent re-seated behind
the larger courtyard) and are the main remaining gap.

## v7 — larger plaza / courtyard, crown pair, side elevations back to the strict reference
- **Courtyard -> ellipse**: y semi-axis 18 m (a first try with a circle r 32 pushed the tower far back and broke the side views), x semi-axis
  18 x kx 1.68 = 30.2 m; arcade + gallery outer ~ 38.8 m -> **~77.6 m across including the gallery** (v6 circle r 24: ~58 m;
  the N-S depth stays near the v5 side-fitted value). Arches re-spaced by equal arc length on the ellipse (44 bays).
- **Frame widened mainly in x**: podium wall_half_w 58.4 -> 65, deck_half_w 72.45 -> 80.6 (161 m wide deck), depth unchanged
  (wall 45 / deck 54); wings moved out (W hall x -45..-41, E hall x 41..45), canopies/masses x x1.113, tower kept rear-centre at
  (13.5, 40) (v5 39, v6 43.5). Forecourt plaza in the mood render x1.3.
- **Compare targets**: `global.ref_stretch_x` 1.18 -> **1.313** (front/rear reference stretched by the new deck width ratio
  161/122.6 = 1.313); **`ref_stretch_y` = 1.0 -> side views are scored against the STRICT reference**.
- **Crown**: the single asymmetric C is replaced by two mirror-symmetric thin blades (per the roof-plan crown reference): each
  horn springs from a post beside the tower (x = 13.5 -/+ 24), bulges outward 6 m, curls inward with tips 2.5 m off the axis
  (gap 5 m above the tower); blade section thickness 0.32 x width, sharp edges (sec_p). Both horns share the v5 side-fitted (y, z)
  profile, so in the side elevations they overlap into the reference C.
- Bridges recomputed for the new drum positions (0.7 m deck, open rails, hangers, rib_drop 3.2).

| stage | front / rear (target x1.313) | left / right (STRICT) | mean IoU / skyline |
|---|---|---|---|
| v6 final | (x1.18) 0.928/1.75 m, 0.922/1.60 m | 0.882/3.40 m, 0.888/3.01 m | — |
| v7a ellipse + pair (base_dx 19, bulge 3.5) | 0.875/3.53 m, 0.873/3.33 m | **0.924/1.33 m, 0.927/1.14 m** | 0.8998 / 2.33 m |
| v7b pair base_dx 24, bulge 6 | 0.875/2.96 m, 0.873/2.80 m | **0.924/1.37 m, 0.927/1.18 m** | 0.8998 / 2.08 m |
Front/rear are lower than v6 by design: the reference elevation shows the old single C, the new crown is a symmetric pair.
# Silhouette compare log

Reference: `ref/sheet_elevations.png` (4 elevation panels). The sheets carry **no dimension lines**, so each reference panel
is scaled uniformly until its silhouette bbox height equals `global.H_total` (ground lines anchored, bbox centres aligned).
Model silhouettes are true orthographic renders at 0.2 m/px. Score = mean IoU - 0.01 x mean skyline error (m).
Each round: the 3x3 XOR-error regions (summed over the 4 views) are ranked; knobs that drive the worst regions are tried at +/- step
(parallel builds); the best improving candidate is accepted, otherwise those knob steps are halved.

## Round 0 (initial params)
- mean IoU **0.8998**, mean skyline err **2.08 m**, score 0.8790
- per view (IoU/skyline): front 0.875/2.96m | rear 0.873/2.80m | left 0.924/1.37m | right 0.927/1.18m

## Round 1
- worst regions: highC (0.109), midR (0.046), midL (0.044)
- candidates (12 builds, 62 s):
  - `canopy_scale` +0.040: score 0.8779 (IoU 0.8996, sky 2.16 m)
  - `canopy_scale` -0.040: score 0.8768 (IoU 0.8999, sky 2.31 m)
  - `canopies.z_shift` +0.800: score 0.8744 (IoU 0.8965, sky 2.21 m)
  - `canopies.z_shift` -0.800: score 0.8723 (IoU 0.8945, sky 2.22 m)
  - `mass_scale` +0.060: score 0.8215 (IoU 0.8478, sky 2.63 m)
  - `mass_scale` -0.060: score 0.8268 (IoU 0.8534, sky 2.66 m)
  - `masses.top_E` +1.000: score 0.8785 (IoU 0.8995, sky 2.09 m)
  - `masses.top_E` -1.000: score 0.8790 (IoU 0.8998, sky 2.08 m)
  - `canopies.west_dx` +1.000: score 0.8796 (IoU 0.9006, sky 2.09 m)
  - `canopies.west_dx` -1.000: score 0.8777 (IoU 0.8989, sky 2.11 m)
  - `canopies.east_dx` +1.000: score 0.8792 (IoU 0.9004, sky 2.12 m)
  - `canopies.east_dx` -1.000: score 0.8766 (IoU 0.8984, sky 2.18 m)
- **accepted** `canopies.west_dx` +1.000 -> mean IoU **0.9006**, skyline **2.09 m**, score 0.8796
- per view: front 0.877/2.90m | rear 0.874/2.92m | left 0.924/1.37m | right 0.927/1.18m

## Round 2
- worst regions: highC (0.109), midR (0.047), highR (0.044)
- candidates (12 builds, 61 s):
  - `tower.crown_z` +0.600: score 0.8795 (IoU 0.9003, sky 2.07 m)
  - `tower.crown_z` -0.600: score 0.8788 (IoU 0.8999, sky 2.11 m)
  - `crescent.d_scale` +0.100: score 0.8792 (IoU 0.9001, sky 2.09 m)
  - `crescent.d_scale` -0.100: score 0.8800 (IoU 0.9009, sky 2.09 m)
  - `tower.r_scale` +0.030: score 0.8782 (IoU 0.8994, sky 2.12 m)
  - `tower.r_scale` -0.030: score 0.8798 (IoU 0.9005, sky 2.07 m)
  - `crescent.dx` +0.800: score 0.8796 (IoU 0.9006, sky 2.09 m)
  - `crescent.dx` -0.800: score 0.8796 (IoU 0.9006, sky 2.09 m)
  - `masses.top_C` +1.000: score 0.8792 (IoU 0.9001, sky 2.09 m)
  - `masses.top_C` -1.000: score 0.8796 (IoU 0.9005, sky 2.09 m)
  - `masses.r_WT` +0.600: score 0.8805 (IoU 0.9014, sky 2.08 m)
  - `masses.r_WT` -0.600: score 0.8788 (IoU 0.8998, sky 2.10 m)
- **accepted** `masses.r_WT` +0.600 -> mean IoU **0.9014**, skyline **2.08 m**, score 0.8805
- per view: front 0.879/2.87m | rear 0.876/2.90m | left 0.924/1.37m | right 0.927/1.18m

## Round 3
- worst regions: highC (0.108), midR (0.047), highR (0.044)
- candidates (12 builds, 57 s):
  - `tower.crown_z` +0.600: score 0.8805 (IoU 0.9011, sky 2.06 m)
  - `tower.crown_z` -0.600: score 0.8797 (IoU 0.9007, sky 2.10 m)
  - `crescent.d_scale` +0.100: score 0.8801 (IoU 0.9009, sky 2.08 m)
  - `crescent.d_scale` -0.100: score 0.8809 (IoU 0.9017, sky 2.08 m)
  - `masses.top_E` +1.000: score 0.8800 (IoU 0.9010, sky 2.10 m)
  - `masses.top_E` -1.000: score 0.8805 (IoU 0.9013, sky 2.08 m)
  - `tower.r_scale` +0.030: score 0.8791 (IoU 0.9002, sky 2.11 m)
  - `tower.r_scale` -0.030: score 0.8807 (IoU 0.9013, sky 2.06 m)
  - `canopy_scale` +0.040: score 0.8785 (IoU 0.9010, sky 2.25 m)
  - `canopy_scale` -0.040: score 0.8790 (IoU 0.9016, sky 2.25 m)
  - `canopies.z_shift` +0.800: score 0.8760 (IoU 0.8982, sky 2.22 m)
  - `canopies.z_shift` -0.800: score 0.8739 (IoU 0.8960, sky 2.21 m)
- no improvement -> halved steps of tried knobs

## Final
- mean IoU **0.9014**, mean skyline error **2.08 m**, score 0.8805
- per view: front 0.879/2.87m | rear 0.876/2.90m | left 0.924/1.37m | right 0.927/1.18m
- roof plan loose check (oblique sheet, bbox-fitted, indicative only): IoU 0.523
- overlays: `compare/final/overlay_sheet.png` (red = reference only, blue = model only, grey = overlap)
- tuned params written back to `params.json` (start values kept in `params_initial.json`)

## v7 summary (scores)
| stage | front / rear | left / right (STRICT reference) | mean IoU / skyline |
|---|---|---|---|
| v6 final (sides strict, front/rear x1.18) | 0.928/1.75 m, 0.922/1.60 m | 0.882/3.40 m, 0.888/3.01 m | 0.9048 / 2.44 m |
| **v7 final (3 loop rounds; sides strict, front/rear x1.313)** | 0.879/2.87 m, 0.876/2.90 m | **0.924/1.37 m, 0.927/1.18 m** | **0.9013 / 2.08 m** |
| v7 final, everything strict (for the record) | 0.713/15.25 m, 0.708/15.41 m | 0.924/1.37 m, 0.927/1.18 m | 0.8181 / 8.30 m |
Loop accepted `canopies.west_dx` +1.0 and `masses.r_WT` +0.6 (side-defining knobs tower.cx/cy and crescent dy/dz/rise/spread were
excluded so the strict side fit is not traded away); bridges re-seated afterwards. Front/rear loss vs v6 = the reference shows the
old single C crown, the model now has the symmetric pair; strict front/rear is low because the design is ~31 % wider than the sheet.

## v8 — crown = two clean planar crescent moons (user: follow the reference strictly, no twist, natural)
- The v7 horns are removed: the outward bulge, the curl, the banked sweep, and their posts and drums. Each crescent is now one flat plate
  (`crescent_plate()`, params `crescent.plate`). Its outline is two conic arcs: an outer ellipse and an inner ellipse through both tips,
  offset so the band is widest (3.5 m) at mid-arc and runs to sharp tips. The section is a constant 1.3 m with rounded edges.
  There is no twist and no sweep.
- Both the front and the side panels of the elevation sheet show the same long, low C, so each plate stands upright in a
  plane turned 52.4° from E-W:
  - Ax (C semi-axis in the front view) 29.3 m and Ay (in the side view) 38 m give an in-plane semi-axis of 48 m; the vertical semi-axis B is 14.4 m.
  - The plane is 12 m behind the tower axis.
  - The bulges sit outboard-front, and the tips curve in above the tower crown to z 77.7 with a 5 m gap.
  - The lower ends run into the tower drums (trimmed at the shell at z ~49).
- Variants tried (quick evals, sides vs the STRICT ref, front/rear vs ×1.313):
  | crown variant | front / rear | left / right | 3/4 crown view |
  |---|---|---|---|
  | v7 horns (twisted sweep) | 0.879/2.87, 0.876/2.90 | 0.924/1.37, 0.927/1.18 | rejected by the user (twisted) |
  | planar circle, upright, R 30, turned 20° | 0.888/2.17, 0.886/2.23 | 0.901/4.17, 0.903/3.97 | round ( ), but side views lose ~3 m |
  | planar circle, leaning back 54° (silhouette-optimised) | 0.886/2.10, 0.883/2.22 | 0.906/3.70, 0.908/3.50 | lies almost flat, wrong |
  | **planar ellipse crescent, upright, turned 52.4° (chosen, coordinate-descent tuned)** | **0.889/2.03, 0.886/2.11** | **0.925/1.33, 0.928/1.11** | crescent pair framing the tower |
- A circular crescent cannot show the sheet's side C, because a round upright plate seen from the side is narrow. The elliptical
  plate keeps the side views better than v7, and it is still a single flat crescent with no twist.

## v8 summary (final run_all, no tuning rounds)
| stage | front / rear (target x1.313) | left / right (STRICT) | mean IoU / skyline |
|---|---|---|---|
| v7 final | 0.879/2.87 m, 0.876/2.90 m | 0.924/1.37 m, 0.927/1.18 m | 0.9013 / 2.08 m |
| **v8 final (planar crescent pair)** | **0.889/2.03 m, 0.886/2.11 m** | **0.925/1.33 m, 0.928/1.11 m** | **0.9067 / 1.65 m** |
