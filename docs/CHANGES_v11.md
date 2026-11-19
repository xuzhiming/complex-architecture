# v11 — the crescent grows out of the central tower (larger, smoother)

User: "从中间的建筑延伸上去，幅度大一些，平滑一点。" (extend it up out of the central building, bigger sweep, smoother)

- **New construction:** one smooth sweep along an elliptical-arc centreline instead of the v10 outer-minus-inner circles.
  - A 42.1 m, B 13.5 m; plane turned 42.8° in plan (bulge to the south-west, tip toward the north-east over the tower), lean 1°.
  - Width tapers smoothly to a sharp tip. Constant 1.3 m plate with rounded edges. Planar, no twist, no kinks.
  - Code: `src/crescent_geom.py` (shared by build.py and the clearance search); `crescent.single` keys A/B/theta/alpha/cx_off/dy/zc/
    ph_root/ph_tip/w_max/t_peak, plus the root fillet fil_w/fil_th/fil_l. `crescent.single.off` builds without a crown.
- **Grows out of the tower:**
  - The root starts in the tower shell at z 50.3 and is trimmed at the shell's inner face, drum by drum, so nothing enters the interior.
  - It fans out like a fillet where it leaves the shell.
  - Bands, belts, steps, ribs and balconies are trimmed around the root, and 8 windows behind it are removed.
- **Much larger:** about 45 m wide in the front view (back about 27 m west of the tower axis, tip about 15 m east), tip at z 76.
- **Clearance:** no intersections with canopies, bridges, masses, drums, the crown disc or the lantern. The BVH check shows
  contact only with the tower shell.
- **Fit to the four-view crown sheet:**
  - Crown-zone skyline error: front 3.61 → 1.45 m, rear 3.44 → 1.30, left 3.77 → 1.41, right 3.71 → 1.35.
  - Whole-view skyline error: 3.15/3.13/2.81/2.63 → 1.51/1.49/1.34/1.17 m.
  - compare.py also reports crown-zone metrics now.
- `renders/crown_detail.png` is reframed (south-south-east, higher, wider) to show the whole C and its root.
