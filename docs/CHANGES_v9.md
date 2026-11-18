# v9 — crown: true circular-arc crescent moons

The user chose round crescent moons, closer to the roof-plan crown reference, and accepted that the side views fit less closely.

- **Each crescent is one flat plate built from two circles.** Outer circle R 24.6 m, minus an inner circle through both tips;
  the band is widest (6 m) at mid-arc. The section is a constant 1.3 m with rounded edges, and the tips are sharp. There is no
  stretch, twist or sweep. `crescent_plate()` in build.py; params `crescent.plate` (`R`, `w_mid`, `theta`, `alpha`, `zc`, `dy`, `ph_tip`, `ph_base`).
- **Mirror pair framing the tower like ( ).**
  - Each plate is turned 18.5° about the vertical (bulge outboard-front) and tilted 4° about its horizontal axis.
  - Circle centres are at z 53, with the planes 6 m behind the tower axis.
  - The tips curve inward over the tower crown to z 74.9 with a 5 m gap.
  - The lower ends run into the tower drums at z ~33 (trimmed at the shell).
- **No intersections with canopies, masses or bridges.**
  - A geometric clash check (`crescent clearance`: canopy discs ±1 m, drums, masses, bridge decks, the tower crown disc) was a
    hard constraint during tuning.
  - The final build was verified with a BVH mesh-overlap test. The crescents touch only the tower's own bands and ribs, where they
    enter the tower. No canopy, drum or bridge is touched, so no canopy or bridge had to move.
- **Tuning:** a random search, then coordinate descent, using only circle parameters (radius, band width, rotation, tilt,
  position, arc ends). The objective weighted the strict side views; the scores are in `compare_log.md` (v9).
