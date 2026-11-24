# Daylight texture paving Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put real shared PBR textures on the Render materials so the building reads as daylight limestone, brushed metal, a wood soffit, clear glass and large plaza slabs.

**Architecture:** Procedural tileable maps live in `web/tex/` and are sampled in world metres inside the existing `onBeforeCompile` chain. One texture object is shared by every mesh of that family. Clay materials are not touched. The glTF file and the collision mesh stay as they are.

**Tech Stack:** three.js r187 MeshStandardMaterial, canvas/PNG textures, Playwright SwiftShader checks.

## Global Constraints

- Branch from `main` `5b19a8a`. Do not merge or deploy. Do not merge the night PR.
- Do not change building geometry, window count, the crescent, or `building_opt.glb`.
- Do not copy the approved concept image into the repo or project it onto the mesh.
- Keep Render pixel-ratio cap 1, Clay cap 2, at most 4 global point lights, localized path/hall pools, and the headlamp only in walk/fly.
- No strong bloom, no glowing coloured rings, no orange window emission.
- Blender is not installed. Do not claim a Cycles render or a glTF rewrite.

---

### Task 1: Budget test for the daylight maps

**Files:** `walk/perf_budget.py`

- [ ] Add assertions that stone, metal, wood and plaza maps exist at a real pixel size, glass emission is near zero, the crescent is not a light, ring emission is near zero, and bloom stays under 0.08.
- [ ] Keep the cap, point-light count, bollard count and environment checks.
- [ ] Run the test against current main and confirm it fails on the missing maps.

### Task 2: Tileable maps

**Files:** `tools/make_daylight_textures.py`, `web/tex/*.png`

- [ ] Generate seamless stone (3.2 m, pores and joints), brushed metal (0.5 m), wood boards (1.6 m) and plaza slabs (6.4 m), each with a linear roughness map.
- [ ] Record byte size. Do not generate one copy per mesh.

### Task 3: Bind the maps in Render only

**Files:** `web/main.js`, `docs/CHANGES_v14.md`, `README.md`, `web/README.md`

- [ ] Load the maps once, wrap and mip them, and sample them in world space from the stone, metal, deck and plaza shaders.
- [ ] Deck tops stay stone; downward and edge faces mix the wood boards.
- [ ] Windows and glass lose the orange emission. The crescent emission goes to zero. Plaza rings become dull metal.
- [ ] Swap the dusk sky and coloured lights for a neutral daylight rig. Leave the four global point lights out so the facade is not spot-lit. Keep the pool functions.
- [ ] Re-run `perf_budget` until it passes, then shoot the same cameras as main.
