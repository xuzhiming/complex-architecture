# v8 — crown: two clean planar crescent moons

User feedback on v7: "冠顶的新月形状对称建筑严格按照参考图 不需要扭曲，自然一点就好" (follow the reference strictly, no twisting, natural).

- The v7 horns (swept blade with outward bulge, inward curl and banked section) are removed, along with their posts and drums.
- Each crescent is a **flat plate**. Its outline is two smooth conic arcs: an outer ellipse and an inner ellipse through both
  tips, offset so the band is widest (3.5 m) at mid-arc and tapers to sharp tips. The section is a constant 1.3 m with rounded
  (superellipse) edges. There is no sweep, twist or bank. Code: `crescent_plate()` in build.py; params: `crescent.plate`.
- The two are mirror images framing the tower.
  - Each stands upright in a plane turned 52.4° from E-W (bulge outboard-front, tips inboard-rear).
  - Size: 48 m in-plane semi-axis, 14.4 m vertical.
  - The tips curve inward above the tower crown to z 77.7, leaving a 5 m gap.
  - The lower ends run into the tower drums at z ~49 (trimmed at the shell).
- The proportions are measured from the elevation sheet, which shows the same long, low C in the front and the side panels.
  A plain circle could not match the side panels (about 4 m worse), so the outline is an ellipse; it is still one flat plate.
- New render: `renders/crown_detail.png` (front 3/4-high view, like the roof-plan crown reference).
- Everything else is unchanged from v7 (elliptical ~78 m courtyard, 161 m deck, bridges, details).
- Silhouettes: front/rear and the strict side views are all better than v7 (see `compare_log.md`, v8).
