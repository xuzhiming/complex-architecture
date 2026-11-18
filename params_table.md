# Parameter table

Every dimension used by `build.py` comes from `params.json` (metres; +Z up, front = -Y). Scale: the sheets have no dimension lines, so the reference-pixel scale (0.1733 m/px) was fixed from the tower storey pitch (~26 px per 4.5 m storey) and sanity-checked against a 1.75 m person; the compare loop aligns silhouettes by scaling each reference bbox to `global.H_total`.

**measured from sheet** = read off the elevation / plan crops at that scale. **inferred** = design assumption (interior layout, code-typical sizes, faces not visible on the sheets). **tuned** = changed by the auto-compare loop (start value in brackets; start file `params_initial.json`).

| parameter | value | source | tuned |
|---|---|---|---|
| `global.H_total` | `77.8` | measured from sheet |  |
| `global.W_total` | `126.6` | measured from sheet |  |
| `global.D_total` | `118.9` | measured from sheet |  |
| `global.floor_h` | `4.5` | inferred |  |
| `global.ground_z` | `0.0` | inferred |  |
| `podium.wall_half_w` | `49.5` | measured from sheet |  |
| `podium.wall_half_d` | `45.0` | measured from sheet |  |
| `podium.wall_cy` | `-0.5` | inferred |  |
| `podium.wall_n` | `3.5` | inferred |  |
| `podium.wall_t` | `0.6` | inferred |  |
| `podium.deck_half_w` | `61.4` | measured from sheet |  |
| `podium.deck_half_d` | `54.0` | measured from sheet |  |
| `podium.deck_cy` | `-4.0` | inferred |  |
| `podium.deck_n` | `3.2` | inferred |  |
| `podium.deck_bot` | `20.5` | measured from sheet |  |
| `podium.deck_top` | `24.0` | measured from sheet |  |
| `podium.fascia_out` | `1.6` | inferred |  |
| `podium.levels` | `[0.0, 4.5, 9.0, 13.5]` | inferred |  |
| `podium.slab_t` | `0.25` | inferred |  |
| `podium.window_pitch` | `5.0` | inferred |  |
| `podium.window_hw` | `1.1` | inferred |  |
| `podium.window_spring` | `2.2` | inferred |  |
| `podium.window_rise` | `1.1` | inferred |  |
| `podium.window_recess` | `0.3` | inferred |  |
| `podium.deck_edge_z` | `23.0` | measured from sheet |  |
| `podium.loggia.sill` | `0.6` | inferred |  |
| `podium.loggia.hw` | `1.7` | measured from sheet |  |
| `podium.loggia.spring` | `3.0` | measured from sheet |  |
| `podium.loggia.rise` | `1.7` | measured from sheet |  |
| `podium.loggia.depth` | `3.5` | inferred |  |
| `podium.loggia.pitch` | `4.6` | inferred |  |
| `arch.cx` | `0.0` | inferred |  |
| `arch.hw` | `20.0` | measured from sheet |  |
| `arch.spring` | `3.3` | measured from sheet |  |
| `arch.rise` | `13.5` | measured from sheet |  |
| `arch.portal_depth` | `4.0` | inferred |  |
| `tunnel.hw` | `9.0` | inferred |  |
| `tunnel.spring` | `4.0` | inferred |  |
| `tunnel.rise` | `7.0` | inferred |  |
| `courtyard.cx` | `0.0` | inferred |  |
| `courtyard.cy` | `3.0` | inferred |  |
| `courtyard.r` | `16.5` | measured from sheet |  |
| `courtyard.wall_t` | `0.6` | inferred |  |
| `courtyard.gallery_w` | `4.0` | inferred |  |
| `courtyard.outer_wall_t` | `0.5` | inferred |  |
| `courtyard.tiers` | `[0.0, 4.5, 9.0, 13.5]` | measured from sheet |  |
| `courtyard.arch_hw` | `1.3` | inferred |  |
| `courtyard.arch_spring` | `2.4` | inferred |  |
| `courtyard.arch_rise` | `1.3` | inferred |  |
| `courtyard.n_arches` | `28` | inferred |  |
| `courtyard.rim_h` | `1.2` | inferred |  |
| `tower.cx` | `13.5` | measured from sheet |  |
| `tower.cy` | `39.0` | measured from sheet | yes (from 40.0) |
| `tower.drums` | `[[17.5, 0.0, 23.2], [17.0, 23.2, 36.7], [16.0, 36.7, 50.2], [15.0, 50.2, 59.2], [13.5, 59.2, 64.0]]` | measured from sheet |  |
| `tower.shell_t` | `0.3` | inferred |  |
| `tower.floors_top` | `58.5` | inferred |  |
| `tower.belts` | `[[27.0, 1.5, -1.0, 19.5], [36.5, -1.5, 1.0, 19.0], [45.0, 1.0, 1.5, 18.5], [52.0, -1.0, -1.0, 17.5], [60.0, 1.5, 0.5, 16.5]]` | inferred |  |
| `tower.crown_z` | `65.6` | measured from sheet |  |
| `tower.crown_R` | `19.0` | measured from sheet |  |
| `tower.dome_r` | `6.0` | inferred |  |
| `tower.dome_h` | `1.2` | inferred |  |
| `tower.ribs_per_drum` | `10` | inferred |  |
| `tower.core.lifts` | `3` | inferred |  |
| `tower.core.lift_w` | `2.6` | inferred |  |
| `tower.core.stairs` | `2` | inferred |  |
| `wings.west.hall` | `[-27.0, -34.0, -23.0, 18.0]` | inferred |  |
| `wings.west.room_s` | `[-42.0, -34.0, -27.0, -2.0]` | inferred |  |
| `wings.west.room_n` | `[-42.0, -2.0, -27.0, 18.0]` | inferred |  |
| `wings.west.core` | `[-33.0, 18.0, -23.0, 28.0]` | inferred |  |
| `wings.west.ext_door_x` | `-36.0` | measured from sheet |  |
| `wings.east.hall` | `[23.0, -34.0, 27.0, 14.0]` | inferred |  |
| `wings.east.room_s` | `[27.0, -34.0, 42.0, -2.0]` | inferred |  |
| `wings.east.room_n` | `[27.0, -2.0, 42.0, 14.0]` | inferred |  |
| `wings.east.core` | `[27.0, 14.0, 37.0, 24.0]` | inferred |  |
| `wings.east.ext_door_x` | `39.0` | measured from sheet |  |
| `stairs.riser_n` | `26` | inferred |  |
| `stairs.tread` | `0.28` | inferred |  |
| `stairs.flight_w` | `1.5` | inferred |  |
| `stairs.shaft_w` | `3.4` | inferred |  |
| `stairs.shaft_l` | `7.6` | inferred |  |
| `stairs.entry_l` | `1.8` | inferred |  |
| `stairs.landing_l` | `1.6` | inferred |  |
| `stairs.headroom_min` | `2.1` | inferred |  |
| `stairs.riser_min` | `0.15` | inferred |  |
| `stairs.riser_max` | `0.18` | inferred |  |
| `stairs.tread_min` | `0.26` | inferred |  |
| `lifts.door_w` | `1.2` | inferred |  |
| `lifts.door_h` | `2.2` | inferred |  |
| `lifts.shaft` | `2.6` | inferred |  |
| `doors.int_w` | `1.8` | inferred |  |
| `doors.int_h` | `2.4` | inferred |  |
| `doors.ext_w` | `2.6` | measured from sheet |  |
| `doors.ext_h` | `5.0` | measured from sheet |  |
| `doors.leaf_t` | `0.08` | inferred |  |
| `doors.wall_t` | `0.3` | inferred |  |
| `doors.wall_h` | `4.2` | inferred |  |
| `doors.link_w` | `3.0` | inferred |  |
| `doors.open_dist` | `3.5` | inferred |  |
| `canopies.W_big` | `{"cx": -38.0, "cy": -16.0, "z": 43.3, "rx": 21.0, "ry": 20.0, "drum_r": 7.0, "lip": 0.35}` | measured from sheet |  |
| `canopies.W_low1` | `{"cx": -42.0, "cy": -27.0, "z": 31.8, "rx": 16.0, "ry": 17.0, "drum_r": 6.0, "lip": 0.3}` | measured from sheet |  |
| `canopies.W_low0` | `{"cx": -40.0, "cy": -28.0, "z": 27.8, "rx": 15.0, "ry": 16.0, "drum_r": 7.5, "lip": 0.4}` | measured from sheet |  |
| `canopies.W_mid` | `{"cx": -24.0, "cy": -13.0, "z": 35.8, "rx": 10.0, "ry": 11.0, "drum_r": 4.5, "lip": 0.3, "dome": true}` | inferred |  |
| `canopies.W_tall` | `{"cx": -27.0, "cy": -5.5, "z": 52.8, "rx": 9.5, "ry": 9.5, "drum_r": 5.5, "lip": 0.25}` | measured from sheet |  |
| `canopies.E_high` | `{"cx": 35.0, "cy": -5.0, "z": 55.3, "rx": 22.5, "ry": 9.0, "drum_r": 5.0, "lip": 0.45}` | measured from sheet |  |
| `canopies.E_mid` | `{"cx": 46.0, "cy": -20.0, "z": 30.8, "rx": 15.0, "ry": 13.0, "drum_r": 6.0, "lip": 0.35}` | measured from sheet |  |
| `canopies.E_low` | `{"cx": 44.0, "cy": -30.0, "z": 25.8, "rx": 14.0, "ry": 12.0, "drum_r": 6.5, "lip": 0.3, "dome": true}` | measured from sheet |  |
| `canopies.C_dome` | `{"cx": 3.5, "cy": 21.5, "z": 27.8, "rx": 7.8, "ry": 7.8, "drum_r": 3.5, "lip": 0.2, "dome": true}` | measured from sheet |  |
| `canopies.T_side` | `{"cx": -2.0, "cy": 24.0, "z": 39.8, "rx": 10.0, "ry": 11.0, "drum_r": 4.0, "lip": 0.3}` | inferred |  |
| `canopies.E_rear` | `{"cx": 47.0, "cy": 22.0, "z": 29.8, "rx": 12.0, "ry": 11.0, "drum_r": 5.0, "lip": 0.3}` | inferred |  |
| `canopies.W_rear` | `{"cx": -36.0, "cy": 26.0, "z": 27.8, "rx": 18.0, "ry": 13.0, "drum_r": 6.0, "lip": 0.35}` | inferred |  |
| `canopy_scale` | `1.0` | inferred |  |
| `columns.positions` | `[[-47.0, -38.0], [47.0, -38.0], [-48.0, 34.0], [48.0, 34.0], [-48.3, -2.0], [48.3, -2.0]]` | measured from sheet |  |
| `columns.base_r` | `2.4` | measured from sheet |  |
| `columns.shaft_r` | `1.6` | measured from sheet |  |
| `columns.flare_r` | `11.5` | measured from sheet |  |
| `columns.ribs` | `10` | inferred |  |
| `columns.flare_z0` | `14.0` | measured from sheet |  |
| `columns.flare_p` | `1.1` | inferred |  |
| `crescent.pts` | `[[-15.5, 10.0, 56.0], [-16.1, 9.599999999999998, 61.0], [-15.5, 10.2, 65.5], [-12.5, 13.399999999999999, 70.0], [-9.0, 17.4, 72.6], [-5.5, 20.9, 74.2], [0.0,...` | measured from sheet | yes (from [[-15.5, 10.0, 56.0], [-16.1, 10.399999999999999, 61.0], [-15.5, 11.0, 65.5], [-12.5, 14.2, 70.0], [-9.0, 18.2, 72.6], [-5.5, 21.7, 74.2], [0.0, 27.2, 75.8], [6.5, 31.5, 76.6], [14.0, 38.0, 76.6], [21.0, 43.5, 76.0], [26.5, 47.5, 75.0]]) |
| `crescent.d` | `[6.0, 7.2, 7.0, 6.0, 4.6, 3.4, 2.6, 1.9, 1.4, 0.9, 0.3]` | measured from sheet |  |
| `crescent.d_scale` | `1.0` | inferred |  |
| `crescent.flat` | `0.85` | inferred |  |
| `crescent.spread` | `1.025` | inferred | yes (from 1.0) |
| `crescent.rise` | `1.0` | inferred |  |
| `crescent.dz` | `0.0` | inferred |  |
| `crescent.bank` | `0.0` | inferred |  |
| `crescent.post_r` | `3.2` | inferred |  |
| `crescent.horn2` | `0.0` | inferred |  |
| `bridges` | `[[[-31.0, -5.5, 40.0], [-20.0, 4.0, 40.5], [-6.0, 14.0, 41.0], [-0.5, 24.0, 41.0]], [[40.0, -1.0, 34.0], [34.0, 10.0, 34.5], [30.0, 22.0, 35.0], [28.5, 30.0,...` | inferred |  |
| `people.height` | `1.75` | inferred |  |
| `people.count` | `40` | inferred |  |
| `masses.M_W` | `{"cx": -14.0, "cy": 4.0, "r": 9.0, "z1": 47.0}` | inferred |  |
| `masses.M_WT` | `{"cx": -19.0, "cy": 12.0, "r": 5.0, "z1": 56.0}` | inferred |  |
| `masses.M_E` | `{"cx": 29.0, "cy": 10.0, "r": 8.0, "z1": 57.5}` | measured from sheet | yes (from {"cx": 29.0, "cy": 10.0, "r": 8.0, "z1": 58.5}) |
| `masses.M_C` | `{"cx": -7.0, "cy": 19.5, "r": 5.0, "z1": 59.5}` | measured from sheet |  |

135 parameters: 44 measured from sheet, 91 inferred, 4 tuned by the compare loop.
