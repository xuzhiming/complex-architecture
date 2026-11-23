# v14 — stylised render (目前是白模，参考这个抽象的效果图进行渲染) + no people

## Tower lobby `T_L0`

`T_L0` is the only space tagged `kind: "lobby"`. It is the ground floor of the tower (centre about 13.5, 40), reached from the gallery through the short passage `T_link` and door `D63`. The courtyard and the arch glow are outside that room; a warm streak through the door gap is that outside light, not hall lighting.

Four short-range point lights sit inside the room, just above the floor, on the render-only group: a warm body, a warmer one toward the entrance, one on the lift wall, and a small cool accent to the east. Range is 7–11 m, so they do not reach the forecourt. Exposure and bloom are unchanged. `style.cycles` `hall_*_w` and the matching points in `src/render_style.py` follow the same placement. Those Cycles frames were not re-rendered.

## Roof tops

The saucer and bridge tops stayed black after the colour pass. They are a near-black metal in the glb, and with no environment they reflect nothing, so the big upper surfaces read as holes. Render exposure and bloom were left alone. Those meshes now use a flat blue-slate (bridges a warmer slate), metal about 0.34 and roughness about 0.46, plus a faint cool emissive (strength 0.05, not a light panel). Two soft directional fills, one cool from above and one warm, give the curved tops a gradient. The crescent is not retinted. `style.web.saucer` matches that slate, and `src/render_style.py` uses the same base so the next Cycles run does not return to a black disc. That run was not done.

## Richer Render light (after the dimming pass)

The dimmed preview read as one blue-violet wash, and the courtyard plus the podium fell into black. This pass does not raise the global exposure (it stays 0.9) and does not grade a screenshot. `web/main.js` paints each loaded part once — crescent, crown, windows, glass, rim, saucer, floor band, deck, podium, arch, tower, shell — to an absolute emissive colour and strength that matches `params.json` `style.web`. That replaces the previous strength remap (3 → 0.70 and so on). It does not multiply those factors again.

The split is warm against cool, not a rainbow: warm-gold windows and the arch, cyan edges on the saucers and floor bands, rose and violet on the crescent and crown. Extra point lights sit in the arch, on the podium face, low and high in the courtyard, and on the east and west sides. Bloom stays a short halo (0.22 / 0.26 / 0.94). Clay lights, the two white materials, and exposure 1 are untouched.

`src/render_style.py` gained the same courtyard warm fill, courtyard cool fill, and podium warm light, and the window and deck-strip colours move toward gold. Those Cycles frames were not re-rendered.

## Render brightness (web preview)

The first web preview clipped. The crescent, the deck edge and the arch core went white, and bloom plus fog hid the floor plates. Clay was not the problem. The bright look came from several Render-only sources stacked together:

- glTF emissive strengths of 3 (rim / plaza / deck strip), 2.5 (windows), 2.2 (crescent) and 1.2 (crown);
- an arch point light at intensity 260 and a crown point light at 500;
- plaza rings drawn with `toneMapped: false` at high lightness;
- UnrealBloomPass strength 0.55 / radius 0.45 / threshold 0.8;
- FogExp2 density 0.0032 and Render exposure 0.95.

`web/main.js` now uses a tighter bloom (0.18 / 0.22 / 0.98), exposure 0.88, fog density 0.0017, and much weaker arch and crown lights (52 and 58). Fill and the pink/cyan rims are lower but still on, so the facade is not a black cutout. On load, only the old baked strengths above are rewritten to 0.70 / 0.85 / 0.65 / 0.40. Strengths that are already in that range are left alone, so a later export does not get darkened twice. Clay still uses the two white materials, the daylight rig and exposure 1. The style button, the V key and `?style=clay` are unchanged.

`params.json` `style.web` emissive strengths match those targets. `style.cycles` (exposure, haze, glare, rim, windows, arch, plaza, crescent, deck strip) and the matching energies in `src/render_style.py` were lowered in the same direction. Those Cycles frames were not re-rendered.

The user supplied an abstract concept image as the target look. It stays local in `ref/` and is not in the repo. The user
also asked that the renders and the web preview contain **no people** and no background city or megastructure.

## Settings live in params.json (`style`)
- **`style.palette`:** navy, indigo, violet, pink, cyan, white, amber, teal, lavender, yellow.
- **`style.rules`:** an ordered list of `[name|role, pattern, material]`. The first match wins.
  - Name patterns:
    - `^CrescentCrown` → crescent;
    - `^CanopyRim` → saucer_rim;
    - `_canopy$` → saucer;
    - `^Tower(Crown|Dome|Lantern…)` → crown;
    - tower slabs, bands, belts and steps, plus wing `_band/_floor` → ring;
    - `^PodiumDeck` → deck, with a strip on the fascia faces;
    - podium shell, slabs and tree columns → podium;
    - `^WindowLights$` → sparse podium windows.
  - Roles: rim, plaza_glow, window_light, glass, door_leaf, ground, facade, slab, wall and stair, with shell as the fallback.
- **`style.cycles`:** samples, resolution, haze densities, crown halo, rim and window strengths, glare, grain and chroma.
- **`style.web`:** plain glTF PBR values (base colour, metallic, roughness, emissive colour and strength) for each material.
- `people.count` is now 0. Previously it was 40 tiny figures in the mood render. `src/final_render.py` no longer adds any people.
- `params_table.md` leaves out the `style.*` render settings, which are not geometry.

## Cycles: `src/render_style.py` + `src/style_post.py`
**Materials, all assigned by rule:**
- dark iridescent shell and facade, with a grazing-angle pink/white/cyan sheen and thin-film coat;
- saucer discs: dark glossy metal with a bright iridescent lip and a faint sheen on top;
- stacked glossy tower rings: chrome-lavender with a pale grazing glow;
- pearly crown with an emissive glow;
- pale glowing crescent ribbon (pink → white → lavender);
- dark glass with a fine grid of tiny warm, amber, teal and pink lit cells;
- window instances in random warm, teal and pink colours at random brightness (Object Info Random; still shared meshes);
- sparse podium window band;
- dark podium, with an emissive light strip on the deck edge.

**Dressing:**
- iridescent emissive strips under every canopy lip;
- three pastel plaza rings (cyan → pink → yellow) plus a soft plaza wash, and a court ring;
- an emissive starburst disc deep in the tunnel, with a spot and 7 narrow god-ray spots fanning out of the arch;
- warm courtyard light;
- crown halo: two emissive volume spheres with radial falloff, plus a point light;
- pink and cyan rim lights and a cool fill;
- a global haze volume domain plus denser haze in front of the arch;
- five faint light swooshes behind the building, in the front view only;
- a dark blue-violet gradient world.
There is no city and there are no people.

**Compositor and post-process:**
- Compositor: Bloom glare, then Streaks glare (8 streaks, high threshold) for the starburst. AgX Medium High Contrast.
- `style_post.py` adds radial chromatic offset, a soft "screen" glow, a vignette and film grain. It also builds
  `renders/style_vs_ref.png`, which is local only and never synced to the repo.

**Views:**
| view | camera | output |
|---|---|---|
| front | forecourt, just below the deck, arch centred, 17 mm, 2:1 | `renders/style_front.png` (2400×1200) |
| aerial | 3/4 aerial from the south-west | `renders/style_aerial.png` (1800×1012) |
| courtyard | inside the courtyard, looking up at the tower and crescent | `renders/style_courtyard.png` (1800×1012) |

## Web preview
- **Styled glb:** `tools/export_style_glb.py` bakes the `style.web` materials, by the same rules, into `building_style.glb`.
  The deck uses two material slots: deck plus edge strip. Door leaves keep two slots: the `door_frame` material plus glass.
  gltf-transform then writes it to `web/building_opt.glb`. Windows are still GPU instances: shared mesh, one material.
- **`main.js`:**
  - A **风格 Style** toggle (button or V): **渲染 Render** is the default; **白模 Clay** is the v13 look; `?style=clay` opens in Clay.
  - Render look:
    - the glb materials;
    - a gradient background canvas (navy → indigo → violet haze), FogExp2 and blue-violet hemisphere light;
    - pink and cyan rim directional lights;
    - four emissive pastel plaza rings, with vertex colours cycling cyan → pink → yellow;
    - additive glow sprites: a warm arch starburst and a pastel crown halo;
    - point lights in the arch and at the crown;
    - EffectComposer (RenderPass → UnrealBloomPass at half resolution → OutputPass);
    - the walk/fly headlamp dimmed to 18%.
  - Clay look: two shared white materials and the old daylight lights and background.
  - Automatic doors clone the frame material for both looks, so the door glow works in either.
  - The test hooks gained `__walk.style()`.
- **Vendor files:** added the three r187 postprocessing modules: EffectComposer, RenderPass, UnrealBloomPass, OutputPass,
  ShaderPass, Pass and MaskPass, plus the Copy, LuminosityHighPass and Output shaders.

## Pipeline and tests
`run_all.sh` now has 9 steps:
- **Step 6:** exports the styled glb, then runs gltf-transform.
- **Step 7:** walk test (coverage, 13-door pass, fly-door check), fly test, a check that the glb is under 8 MB, and
  `walk/style_shots.py`. That script takes Render and Clay screenshots and a walk view, measures frame time and fails on
  any console error.
- **Step 8:** mood render, with no people.
- **Step 9:** style renders plus post-processing.
- The walk test's fly-door check now waits for the door next to D40 to finish closing before it measures the "far" state.
  The walk suite can leave that door closing.
