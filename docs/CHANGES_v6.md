# v6 changes - refined main structure + user-widened design

## Scores
- Strict reference: v5 IoU 0.9311 / skyline 1.67 m -> S1 side fix 0.9366 / 1.03 m -> with v6 detail (not widened) 0.9233 / 1.43 m.
- The user then widened the design (bigger courtyard/plaza). Compare target = reference front/rear stretched x1.18:
  v6 final IoU **0.9048** / skyline **2.44 m** (front 0.928, rear 0.922, left 0.882, right 0.888). Strict reference: 0.8526 / 6.09 m.

## Design changes (user)
- Building widened in x: podium/deck x1.18, wings 8 m outward, canopies/masses/columns x1.18, arch half-width 20 -> 23 m.
- Courtyard r 16.5 -> 24 m (about 58 m across incl. the gallery), tower moved back 3.5 m (still rear centre), crescent re-seated.
- Rooftop bridges much thinner: 0.7 m deck, open railing (posts + handrail + mid-rail), thin under-slung arch rib + hangers.
- No background: final render has no far city, no sky disc, no world haze; plain dark gradient sky.

## Geometry code (build.py, src/geom.py, new src/detail.py)
- Windows: one shared mesh per window type (arched / tall-rect surround + sill, dark or lit pane) placed as linked duplicates on the
  tower and every drum (about 1,100 windows); exported as shared meshes and turned into EXT_mesh_gpu_instancing by gltf-transform.
- Tower: solid clay shell (no fins over a dark drum), thick rounded floor belts, buttress pilasters with stepped feet/corbelled heads,
  offset cantilever belts with brackets, rotating sector balconies with parapets, crown under-disc with rib soffit, dome lantern.
- Canopies: lens profile with rounded fascia nose, underside radial rib soffits; drums are solid with pilasters, thick bands and
  arched window rings per storey.
- Side towers (W_tall, E_high): slim windowed core + ring of slender columns, stacked rounded floors, trumpet flare under the cap.
- Podium: rounded deck nose, ribbed flaring tree-column heads (solid rib plates), 4-layer archivolts + keystone + imposts;
  open loggia band and courtyard arcade kept.
- Crescent: blade cross-section (full width, thin crisp edges, cambered top); post is constrained to clear the courtyard void.

## Pipeline
- compare: `global.ref_stretch_x` design-target stretch (REF_STRETCH_X=1 = strict), `KNOB_EXCLUDE`, `compare/skyline_diff.py`.
- export: gltf-transform `--instance true` (building.glb 10.2 MB -> building_opt.glb 2.2 MB).
- web/main.js: instanced facade meshes are excluded from the collision BVH.
- walk test: wing waypoints are read from spaces.json (plan moved); renders: perspective_hero_low.png, detail_tower.png.
