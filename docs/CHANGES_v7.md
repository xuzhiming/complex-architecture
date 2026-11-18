# v7 — larger plaza, symmetric crown pair, side elevations back on the reference

## Plaza / courtyard (广场再大一些)
- Courtyard is now an **ellipse**: semi-axes 30.2 m (x) x 18 m (y) (`courtyard.r` 18, `courtyard.kx` 1.68). With the arcade
  wall and gallery it spans **~77.6 m E-W** (v6 circle r 24: ~58 m, v5 r 16.5: ~43 m), while its N-S depth stays at the v5 value
  so the side elevations keep their reference proportions.
- All courtyard geometry is ellipse-aware (`EP/EN/EPAR/ecut` in build.py): deck cut, arcade wall + rim + rails (`sx`),
  44 arches spaced by equal arc length, gallery outer wall openings, courtyard/gallery/tunnel/wing/tower link doors,
  slab cuts, plaza ring; the walk test follows elliptical gallery arcs.
- Frame widened in x: podium wall 116.8 -> 130 m, deck 144.9 -> **161 m** wide (depth 90/108 m unchanged); wings moved out
  (W hall x -45..-41, E hall x 41..45, rooms to +/-57), canopies and masses x1.113, tower kept rear-centre at (13.5, 40).
- Forecourt plaza in the mood render x1.3 (`global.plaza_scale`), camera pulled back.

## Crown
- The single asymmetric C is replaced by **two mirror-symmetric thin crescent blades** (roof-plan crown reference): each
  springs from its own post + drum beside the tower (x = 13.5 -/+ 24 m, behind the courtyard rim), bulges outward 6 m, then
  curls up and inward; tips stop 2.5 m off the axis, leaving a 5 m gap above the tower. Blade section: thin (0.32 x width),
  sharp edges, tapering to the tip. Params: `crescent.pair`.
- Both horns share the v5 side-fitted (y, z) profile, so in the side elevations they coincide with the reference crescent.

## Bridges
- Re-seated between the moved drums and the tower (W_tall->T_side, E_high->tower, W_tall->tower), still 0.7 m decks with
  open railings and hangers; under-rib drop 3.2 m.

## Compare
- Front/rear design target `ref_stretch_x` 1.18 -> **1.313** (deck width ratio); **sides strict** (`ref_stretch_y` = 1.0).
- Frame for silhouettes widened to 200 m. Scores: see `compare_log.md` (v7 section).
