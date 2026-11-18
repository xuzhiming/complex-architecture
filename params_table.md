# Parameter table

Every dimension used by `build.py` comes from `params.json` (metres; +Z up, front = -Y). Scale: the sheets have no dimension lines, so the reference-pixel scale (0.1733 m/px) was fixed from the tower storey pitch (~26 px per 4.5 m storey) and sanity-checked against a 1.75 m person; the compare loop aligns silhouettes by scaling each reference bbox to `global.H_total`.

**measured from sheet** = read off the elevation / plan crops at that scale. **inferred** = design assumption (interior layout, code-typical sizes, faces not visible on the sheets). **tuned** = changed by the auto-compare loop (start value in brackets; start file `params_initial.json`).

| parameter | value | source | tuned |
|---|---|---|---|
| `global.H_total` | `77.8` | measured from sheet |  |
| `global.W_total` | `166.3` | measured from sheet | yes (from 126.6) |
| `global.D_total` | `118.9` | measured from sheet |  |
| `global.floor_h` | `4.5` | inferred |  |
| `global.ground_z` | `0.0` | inferred |  |
| `global.ref_stretch_x` | `1.313` | inferred | yes (from null) |
| `global.ref_stretch_y` | `1.0` | inferred | yes (from null) |
| `global.plaza_scale` | `1.3` | inferred | yes (from null) |
| `podium.wall_half_w` | `65.0` | measured from sheet | yes (from 49.5) |
| `podium.wall_half_d` | `45.0` | measured from sheet |  |
| `podium.wall_cy` | `-0.5` | inferred |  |
| `podium.wall_n` | `3.5` | inferred |  |
| `podium.wall_t` | `0.6` | inferred |  |
| `podium.deck_half_w` | `80.62` | measured from sheet | yes (from 61.4) |
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
| `arch.hw` | `25.0` | measured from sheet | yes (from 20.0) |
| `arch.spring` | `3.3` | measured from sheet |  |
| `arch.rise` | `13.5` | measured from sheet |  |
| `arch.portal_depth` | `4.0` | inferred |  |
| `tunnel.hw` | `9.0` | inferred |  |
| `tunnel.spring` | `4.0` | inferred |  |
| `tunnel.rise` | `7.0` | inferred |  |
| `courtyard.cx` | `0.0` | inferred |  |
| `courtyard.cy` | `2.0` | inferred | yes (from 3.0) |
| `courtyard.r` | `18.0` | measured from sheet | yes (from 16.5) |
| `courtyard.wall_t` | `0.6` | inferred |  |
| `courtyard.gallery_w` | `4.0` | inferred |  |
| `courtyard.outer_wall_t` | `0.5` | inferred |  |
| `courtyard.tiers` | `[0.0, 4.5, 9.0, 13.5]` | measured from sheet |  |
| `courtyard.arch_hw` | `1.3` | inferred |  |
| `courtyard.arch_spring` | `2.4` | inferred |  |
| `courtyard.arch_rise` | `1.3` | inferred |  |
| `courtyard.n_arches` | `44` | inferred | yes (from 28) |
| `courtyard.rim_h` | `1.2` | inferred |  |
| `courtyard.kx` | `1.68` | inferred | yes (from null) |
| `tower.cx` | `13.5` | measured from sheet |  |
| `tower.cy` | `40.0` | measured from sheet |  |
| `tower.drums` | `[[16.974999999999998, 0.0, 23.2], [16.49, 23.2, 36.7], [15.52, 36.7, 50.2], [14.549999999999999, 50.2, 59.2], [13.094999999999999, 59.2, 64.0]]` | measured from sheet | yes (from [[17.5, 0.0, 23.2], [17.0, 23.2, 36.7], [16.0, 36.7, 50.2], [15.0, 50.2, 59.2], [13.5, 59.2, 64.0]]) |
| `tower.shell_t` | `0.3` | inferred |  |
| `tower.floors_top` | `58.5` | inferred |  |
| `tower.belts` | `[[27.0, 1.5, -1.0, 19.5], [36.5, -1.5, 1.0, 19.0], [45.0, 1.0, 1.5, 18.5], [52.0, -1.0, -1.0, 17.5], [60.0, 1.5, 0.5, 16.5]]` | inferred |  |
| `tower.crown_z` | `65.6` | measured from sheet |  |
| `tower.crown_R` | `18.43` | measured from sheet | yes (from 19.0) |
| `tower.dome_r` | `6.0` | inferred |  |
| `tower.dome_h` | `1.2` | inferred |  |
| `tower.ribs_per_drum` | `10` | inferred |  |
| `tower.core.lifts` | `3` | inferred |  |
| `tower.core.lift_w` | `2.6` | inferred |  |
| `tower.core.stairs` | `2` | inferred |  |
| `wings.west.hall` | `[-45.0, -34.0, -41.0, 18.0]` | inferred | yes (from [-27.0, -34.0, -23.0, 18.0]) |
| `wings.west.room_s` | `[-57.0, -34.0, -45.0, -2.0]` | inferred | yes (from [-42.0, -34.0, -27.0, -2.0]) |
| `wings.west.room_n` | `[-57.0, -2.0, -45.0, 18.0]` | inferred | yes (from [-42.0, -2.0, -27.0, 18.0]) |
| `wings.west.core` | `[-51.0, 18.0, -41.0, 28.0]` | inferred | yes (from [-33.0, 18.0, -23.0, 28.0]) |
| `wings.west.ext_door_x` | `-51.0` | measured from sheet | yes (from -36.0) |
| `wings.east.hall` | `[41.0, -34.0, 45.0, 14.0]` | inferred | yes (from [23.0, -34.0, 27.0, 14.0]) |
| `wings.east.room_s` | `[45.0, -34.0, 57.0, -2.0]` | inferred | yes (from [27.0, -34.0, 42.0, -2.0]) |
| `wings.east.room_n` | `[45.0, -2.0, 57.0, 14.0]` | inferred | yes (from [27.0, -2.0, 42.0, 14.0]) |
| `wings.east.core` | `[45.0, 14.0, 55.0, 24.0]` | inferred | yes (from [27.0, 14.0, 37.0, 24.0]) |
| `wings.east.ext_door_x` | `51.0` | measured from sheet | yes (from 39.0) |
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
| `canopies.W_big` | `{"cx": -50.9, "cy": -16.0, "z": 43.3, "rx": 27.6, "ry": 23, "drum_r": 7.0, "lip": 0.35}` | measured from sheet | yes (from {"cx": -38.0, "cy": -16.0, "z": 43.3, "rx": 21.0, "ry": 20.0, "drum_r": 7.0, "lip": 0.35}) |
| `canopies.W_low1` | `{"cx": -56.2, "cy": -27.0, "z": 32.8, "rx": 21.0, "ry": 21, "drum_r": 6.0, "lip": 0.3}` | measured from sheet | yes (from {"cx": -42.0, "cy": -27.0, "z": 31.8, "rx": 16.0, "ry": 17.0, "drum_r": 6.0, "lip": 0.3}) |
| `canopies.W_low0` | `{"cx": -53.5, "cy": -28.0, "z": 27.8, "rx": 19.7, "ry": 16.0, "drum_r": 7.5, "lip": 0.4}` | measured from sheet | yes (from {"cx": -40.0, "cy": -28.0, "z": 27.8, "rx": 15.0, "ry": 16.0, "drum_r": 7.5, "lip": 0.4}) |
| `canopies.W_mid` | `{"cx": -32.5, "cy": -13.0, "z": 35.8, "rx": 13.1, "ry": 11.0, "drum_r": 4.5, "lip": 0.3, "dome": true}` | inferred | yes (from {"cx": -24.0, "cy": -13.0, "z": 35.8, "rx": 10.0, "ry": 11.0, "drum_r": 4.5, "lip": 0.3, "dome": true}) |
| `canopies.W_tall` | `{"cx": -36.5, "cy": 14, "z": 56, "rx": 12.5, "ry": 9.5, "drum_r": 5.5, "lip": 0.25, "style": "column_tower", "n_cols": 8, "col_r": 0.55}` | measured from sheet | yes (from {"cx": -27.0, "cy": -5.5, "z": 52.8, "rx": 9.5, "ry": 9.5, "drum_r": 5.5, "lip": 0.25}) |
| `canopies.E_high` | `{"cx": 46.0, "cy": 14, "z": 55.3, "rx": 29.5, "ry": 9.0, "drum_r": 5.0, "lip": 0.45, "style": "column_tower", "n_cols": 7, "col_r": 0.55}` | measured from sheet | yes (from {"cx": 35.0, "cy": -5.0, "z": 55.3, "rx": 22.5, "ry": 9.0, "drum_r": 5.0, "lip": 0.45}) |
| `canopies.E_mid` | `{"cx": 60.4, "cy": -20.0, "z": 30.8, "rx": 19.7, "ry": 13.0, "drum_r": 6.0, "lip": 0.35}` | measured from sheet | yes (from {"cx": 46.0, "cy": -20.0, "z": 30.8, "rx": 15.0, "ry": 13.0, "drum_r": 6.0, "lip": 0.35}) |
| `canopies.E_low` | `{"cx": 57.8, "cy": -30.0, "z": 25.8, "rx": 18.4, "ry": 12.0, "drum_r": 6.5, "lip": 0.3, "dome": true}` | measured from sheet | yes (from {"cx": 44.0, "cy": -30.0, "z": 25.8, "rx": 14.0, "ry": 12.0, "drum_r": 6.5, "lip": 0.3, "dome": true}) |
| `canopies.C_dome` | `{"cx": -3.4, "cy": 25.0, "z": 27.8, "rx": 10.2, "ry": 7.8, "drum_r": 3.5, "lip": 0.2, "dome": true}` | measured from sheet | yes (from {"cx": 3.5, "cy": 21.5, "z": 27.8, "rx": 7.8, "ry": 7.8, "drum_r": 3.5, "lip": 0.2, "dome": true}) |
| `canopies.T_side` | `{"cx": -16.6, "cy": 25.5, "z": 39.8, "rx": 13.1, "ry": 11.0, "drum_r": 4.0, "lip": 0.3}` | inferred | yes (from {"cx": -2.0, "cy": 24.0, "z": 39.8, "rx": 10.0, "ry": 11.0, "drum_r": 4.0, "lip": 0.3}) |
| `canopies.E_rear` | `{"cx": 61.8, "cy": 19.5, "z": 29.8, "rx": 15.8, "ry": 11.0, "drum_r": 5.0, "lip": 0.3}` | inferred | yes (from {"cx": 47.0, "cy": 22.0, "z": 29.8, "rx": 12.0, "ry": 11.0, "drum_r": 5.0, "lip": 0.3}) |
| `canopies.W_rear` | `{"cx": -48.3, "cy": 23.5, "z": 27.8, "rx": 23.6, "ry": 13.0, "drum_r": 6.0, "lip": 0.35}` | inferred | yes (from {"cx": -36.0, "cy": 26.0, "z": 27.8, "rx": 18.0, "ry": 13.0, "drum_r": 6.0, "lip": 0.35}) |
| `canopy_scale` | `1.0` | inferred |  |
| `columns.positions` | `[[-61.8, -38.0], [61.8, -38.0], [-63.0, 34.0], [63.0, 34.0], [-63.4, -2.0], [63.4, -2.0]]` | measured from sheet | yes (from [[-47.0, -38.0], [47.0, -38.0], [-48.0, 34.0], [48.0, 34.0], [-48.3, -2.0], [48.3, -2.0]]) |
| `columns.base_r` | `2.4` | measured from sheet |  |
| `columns.shaft_r` | `1.6` | measured from sheet |  |
| `columns.flare_r` | `11.5` | measured from sheet |  |
| `columns.ribs` | `10` | inferred |  |
| `columns.flare_z0` | `14.0` | measured from sheet |  |
| `columns.flare_p` | `1.1` | inferred |  |
| `crescent.pts` | `[[-15.5, 11.0, 56.0], [-16.1, 10.599999999999998, 61.0], [-15.5, 11.2, 65.5], [-12.5, 14.399999999999999, 70.0], [-9.0, 18.4, 72.6], [-5.5, 21.9, 74.2], [0.0...` | measured from sheet | yes (from [[-15.5, 10.0, 56.0], [-16.1, 10.399999999999999, 61.0], [-15.5, 11.0, 65.5], [-12.5, 14.2, 70.0], [-9.0, 18.2, 72.6], [-5.5, 21.7, 74.2], [0.0, 27.2, 75.8], [6.5, 31.5, 76.6], [14.0, 38.0, 76.6], [21.0, 43.5, 76.0], [26.5, 47.5, 75.0]]) |
| `crescent.d` | `[6.0, 7.2, 7.0, 6.0, 4.6, 3.4, 2.6, 1.9, 1.4, 0.9, 0.3]` | measured from sheet |  |
| `crescent.d_scale` | `1.0` | inferred |  |
| `crescent.flat` | `0.85` | inferred |  |
| `crescent.spread` | `1.025` | inferred | yes (from 1.0) |
| `crescent.rise` | `1.0` | inferred |  |
| `crescent.dz` | `0.0` | inferred |  |
| `crescent.bank` | `0.0` | inferred |  |
| `crescent.post_r` | `2.4` | inferred | yes (from 3.2) |
| `crescent.horn2` | `0.0` | inferred |  |
| `crescent.sec_p` | `[0.6, 1.35]` | inferred | yes (from null) |
| `crescent.camber` | `0.25` | inferred | yes (from null) |
| `crescent.pair.axis_x` | `13.5` | inferred | yes (from null) |
| `crescent.pair.base_dx` | `24.0` | inferred | yes (from null) |
| `crescent.pair.bulge` | `6.0` | inferred | yes (from null) |
| `crescent.pair.tip_dx` | `2.5` | inferred | yes (from null) |
| `crescent.pair.thick` | `0.32` | inferred | yes (from null) |
| `crescent.pair.curl_p` | `1.6` | inferred | yes (from null) |
| `crescent.pair.base_drop` | `4.0` | inferred | yes (from null) |
| `crescent.plate.axis_x` | `13.5` | inferred | yes (from null) |
| `crescent.plate.zc` | `63.4` | inferred | yes (from null) |
| `crescent.plate.dy` | `12.0` | inferred | yes (from null) |
| `crescent.plate.ph_base` | `-85.0` | inferred | yes (from null) |
| `crescent.plate.w_mid` | `3.5` | inferred | yes (from null) |
| `crescent.plate.thick` | `1.3` | inferred | yes (from null) |
| `crescent.plate.tip_gap` | `5.0` | inferred | yes (from null) |
| `crescent.plate.theta` | `20.0` | inferred | yes (from null) |
| `crescent.plate.alpha` | `0.0` | inferred | yes (from null) |
| `crescent.plate.R` | `30.0` | inferred | yes (from null) |
| `crescent.plate.ph_tip` | `78.0` | inferred | yes (from null) |
| `crescent.plate.Ax` | `29.3` | inferred | yes (from null) |
| `crescent.plate.Ay` | `38.0` | inferred | yes (from null) |
| `crescent.plate.B` | `14.4` | inferred | yes (from null) |
| `crescent.plate.uc` | `-0.21` | inferred | yes (from null) |
| `bridges` | `[[[-32.6, 16.3, 38.0], [-28.1, 20.3, 38.2], [-23.7, 22.9, 38.4], [-19.2, 24.0, 38.6]], [[42.9, 16.5, 34.0], [37.1, 22.6, 34.3], [31.4, 27.2, 34.7], [25.6, 30...` | inferred | yes (from [[[-31.0, -5.5, 40.0], [-20.0, 4.0, 40.5], [-6.0, 14.0, 41.0], [-0.5, 24.0, 41.0]], [[40.0, -1.0, 34.0], [34.0, 10.0, 34.5], [30.0, 22.0, 35.0], [28.5, 30.0, 35.0]], [[-27.0, -5.5, 48.0], [-12.0, 6.0, 49.0], [0.0, 20.0, 49.5], [1.5, 31.0, 50.0]]]) |
| `people.height` | `1.75` | inferred |  |
| `people.count` | `40` | inferred |  |
| `masses.M_W` | `{"cx": -40.3, "cy": -4.2, "r": 9.0, "z1": 54.4}` | inferred | yes (from {"cx": -14.0, "cy": 4.0, "r": 9.0, "z1": 47.0}) |
| `masses.M_WT` | `{"cx": -30.0, "cy": 16.5, "r": 6.799999999999999, "z1": 56.0}` | inferred | yes (from {"cx": -19.0, "cy": 12.0, "r": 5.0, "z1": 56.0}) |
| `masses.M_E` | `{"cx": 38.5, "cy": 10.1, "r": 8.0, "z1": 54.5}` | measured from sheet | yes (from {"cx": 29.0, "cy": 10.0, "r": 8.0, "z1": 58.5}) |
| `masses.M_C` | `{"cx": -8.9, "cy": 27.5, "r": 5.0, "z1": 58.5}` | measured from sheet | yes (from {"cx": -7.0, "cy": 19.5, "r": 5.0, "z1": 59.5}) |
| `masses.M_E2` | `{"cx": 31.2, "cy": 24.5, "r": 6.0, "z1": 66.0}` | inferred | yes (from null) |
| `detail.seed` | `7` | inferred | yes (from null) |
| `detail.archivolts` | `[[1.4, 1.8], [2.5, 1.3], [3.6, 0.9], [4.7, 0.5]]` | inferred | yes (from null) |
| `detail.drum_windows.bay` | `5.2` | inferred | yes (from null) |
| `detail.drum_windows.pitch` | `2.7` | inferred | yes (from null) |
| `detail.drum_windows.hw` | `0.7` | inferred | yes (from null) |
| `detail.drum_windows.lit` | `0.45` | inferred | yes (from null) |
| `detail.tower.band_h` | `1.05` | inferred | yes (from null) |
| `detail.tower.band_out` | `1.15` | inferred | yes (from null) |
| `detail.tower.belt_h` | `1.0` | inferred | yes (from null) |
| `detail.tower.win_pitch` | `2.7` | inferred | yes (from null) |
| `detail.tower.balconies.every` | `2` | inferred | yes (from null) |
| `detail.tower.balconies.depth` | `2.2` | inferred | yes (from null) |
| `detail.tower.balconies.span_deg` | `40` | inferred | yes (from null) |
| `detail.tower.balconies.per_floor` | `3` | inferred | yes (from null) |
| `detail.bridge.w` | `3.0` | inferred | yes (from null) |
| `detail.bridge.deck_t` | `0.7` | inferred | yes (from null) |
| `detail.bridge.rail_h` | `1.1` | inferred | yes (from null) |
| `detail.bridge.post_pitch` | `1.6` | inferred | yes (from null) |
| `detail.bridge.rib` | `0.38` | inferred | yes (from null) |
| `detail.bridge.rib_drop` | `3.2` | inferred | yes (from null) |

186 parameters: 44 measured from sheet, 142 inferred, 89 tuned by the compare loop.
