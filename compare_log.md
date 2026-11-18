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
