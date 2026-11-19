# v10 — crown rebuilt as ONE asymmetric crescent (user's four-view crown sheet)

User: "参考这个四视图，把顶部的月牙型建筑删除重建。注意这个月牙构件不是左右对称的，它是个单体构件"
(rebuild the crown from the four-view sheet; it is one single component, not left-right symmetric).

- **Removed:** the v9 mirror pair of crescents.
- **New crown: one flat crescent plate.** Its outline is an outer circle (R 19.2 m) minus an inner circle through both tips,
  so the band is widest (8.8 m) at mid-arc and runs to sharp tips. Section: constant 1.3 m, rounded edges. No twist or sweep.
  Code: `crescent.single` in params, `crescent_plate()` in build.py.
- **Orientation, as read from the four panels:**
  - Front: the back of the C is west of the tower top; the lower tip enters the tower's upper west side (z 44.7); the arc
    sweeps over to the upper tip above the tower crown (z 72.0).
  - Rear and side views show the matching mirror and side images.
  - The plate's plane is turned 48.8° in plan (bulge to the south-west, tip toward the north-east over the tower) and
    leans 10.7°.
- **No clashes with canopies, drums, infill masses or bridges**, and it stays clear of the crown disc and lantern. This was a
  hard constraint in the search. A BVH mesh-overlap test on the final build shows only the tower belt it enters.
- **Compare:**
  - New reference silhouettes come from `ref/elevations_crown_v10.png` (`compare/ref_v10/`; `ref_extract.py` gained
    `SHEET`/`REF_OUT`/`TRIM` options and drops the thicker ground line).
  - The crown zone (above z 46 m, within 36 m of the tower axis) is scored against the STRICT panel, re-anchored on the tower
    axis. The rest of the front/rear keeps the ×1.313 widened target (`global.crown_zone`, `global.ref_dir`).
- **Tuning:** only the crescent parameters were tuned (radius, band width, rotation, lean, centre position, arc ends). Method:
  a constrained random search (1 M samples, 270 valid), then 24 quick evaluations, then coordinate descent on the mean of the
  4 views (IoU − 0.02 × skyline error).
- **Limitation:** the sheet's crescent is a long, low C (wider than tall). With true circular arcs and the tip kept clear of
  the crown lantern, the fitted moon is more compact than the drawing.
- New render: `renders/crown_detail.png`.
