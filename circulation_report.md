# Circulation check report

Model: `building.blend` - spaces: 55, doors: 106, stairs (flights per storey): 32, lifts: 5

Method: BVH of all solid meshes (door leaves excluded because they slide open), ray tests through each door at 1.0 m and 2.0 m (plus jamb-side rays for wide openings), a sideways-offset ray that must hit wall material (proves the opening is a real gap in a real wall), down-rays on every stair tread, up-rays for headroom, floor probes for every space, hollow-shaft rays for lifts, then BFS over the passing doors/stairs from the entrance `forecourt`.

## as-built  ->  **PASS**

- doors ok: 106/106  (all pierce their wall: True)
- stair flights ok: 32/32
- spaces with floor + >=2.1 m headroom: 55/55
- lift shafts hollow: 5/5
- reachable from entrance: 55/55; unreachable: none

Example routes found by BFS:

- courtyard: D00_forecourt__portal_tunnel -> D01_portal_tunnel__courtyard
- T_L0: D00_forecourt__portal_tunnel -> D02_portal_tunnel__gallery -> D16_gallery__T_link -> D63_T_link__T_L0
- T_L1: D00_forecourt__portal_tunnel -> D02_portal_tunnel__gallery -> D16_gallery__T_link -> D63_T_link__T_L0 -> T_stairA_0
- T_L13: D00_forecourt__portal_tunnel -> D02_portal_tunnel__gallery -> D16_gallery__T_link -> D63_T_link__T_L0 -> D64_T_L0__T_lift0 -> D77_T_L13__T_lift0

| stair | riser (design) | measured riser range | tread | min headroom | ok |
|---|---|---|---|---|---|
| W_stair_0 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| W_stair_1 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| W_stair_2 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.173 m | yes |
| E_stair_0 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| E_stair_1 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| E_stair_2 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.173 m | yes |
| T_stairA_0 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_1 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_2 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_3 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_4 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_5 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_6 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_7 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_8 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_9 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_10 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_11 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairA_12 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.173 m | yes |
| T_stairB_0 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_1 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_2 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_3 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_4 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_5 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_6 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_7 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_8 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_9 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_10 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_11 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.123 m | yes |
| T_stairB_12 | 173.1 mm | [173.1, 173.1] | 280 mm | 2.173 m | yes |

| door | type | clear | pierces wall | ok |
|---|---|---|---|---|
| D00_forecourt__portal_tunnel | open | True | None | yes |
| D01_portal_tunnel__courtyard | open | True | None | yes |
| D02_portal_tunnel__gallery | opening | True | True | yes |
| D03_portal_tunnel__gallery | opening | True | True | yes |
| D04_courtyard__gallery | opening | True | True | yes |
| D05_courtyard__gallery | opening | True | True | yes |
| D06_courtyard__gallery | opening | True | True | yes |
| D07_courtyard__gallery | opening | True | True | yes |
| D08_courtyard__gallery | opening | True | True | yes |
| D09_courtyard__gallery | opening | True | True | yes |
| D10_courtyard__gallery | opening | True | True | yes |
| D11_courtyard__gallery | opening | True | True | yes |
| D12_courtyard__gallery | opening | True | True | yes |
| D13_courtyard__gallery | opening | True | True | yes |
| D14_gallery__W_link | door | True | True | yes |
| D15_gallery__E_link | door | True | True | yes |
| D16_gallery__T_link | door | True | True | yes |
| D17_W_link__W_hall | door | True | True | yes |
| D18_W_hall__W_room_s | door | True | True | yes |
| D19_W_hall__W_room_n | door | True | True | yes |
| D20_W_vest__W_room_s | door | True | True | yes |
| D21_W_room_s__W_room_n | door | True | True | yes |
| D22_W_hall__W_core | door | True | True | yes |
| D23_W_hall_L1__W_room_s_L1 | door | True | True | yes |
| D24_W_hall_L1__W_room_n_L1 | door | True | True | yes |
| D25_W_room_s_L1__W_room_n_L1 | door | True | True | yes |
| D26_W_hall_L1__W_core_L1 | door | True | True | yes |
| D27_W_hall_L2__W_room_s_L2 | door | True | True | yes |
| D28_W_hall_L2__W_room_n_L2 | door | True | True | yes |
| D29_W_room_s_L2__W_room_n_L2 | door | True | True | yes |
| D30_W_hall_L2__W_core_L2 | door | True | True | yes |
| D31_W_hall_L3__W_room_s_L3 | door | True | True | yes |
| D32_W_hall_L3__W_room_n_L3 | door | True | True | yes |
| D33_W_room_s_L3__W_room_n_L3 | door | True | True | yes |
| D34_W_hall_L3__W_core_L3 | door | True | True | yes |
| D35_forecourt__W_vest | ext_door | True | True | yes |
| D36_W_core__W_lift | lift_door | True | True | yes |
| D37_W_core_L1__W_lift | lift_door | True | True | yes |
| D38_W_core_L2__W_lift | lift_door | True | True | yes |
| D39_W_core_L3__W_lift | lift_door | True | True | yes |
| D40_E_link__E_hall | door | True | True | yes |
| D41_E_hall__E_room_s | door | True | True | yes |
| D42_E_hall__E_room_n | door | True | True | yes |
| D43_E_vest__E_room_s | door | True | True | yes |
| D44_E_room_s__E_room_n | door | True | True | yes |
| D45_E_room_n__E_core | door | True | True | yes |
| D46_E_hall_L1__E_room_s_L1 | door | True | True | yes |
| D47_E_hall_L1__E_room_n_L1 | door | True | True | yes |
| D48_E_room_s_L1__E_room_n_L1 | door | True | True | yes |
| D49_E_room_n_L1__E_core_L1 | door | True | True | yes |
| D50_E_hall_L2__E_room_s_L2 | door | True | True | yes |
| D51_E_hall_L2__E_room_n_L2 | door | True | True | yes |
| D52_E_room_s_L2__E_room_n_L2 | door | True | True | yes |
| D53_E_room_n_L2__E_core_L2 | door | True | True | yes |
| D54_E_hall_L3__E_room_s_L3 | door | True | True | yes |
| D55_E_hall_L3__E_room_n_L3 | door | True | True | yes |
| D56_E_room_s_L3__E_room_n_L3 | door | True | True | yes |
| D57_E_room_n_L3__E_core_L3 | door | True | True | yes |
| D58_forecourt__E_vest | ext_door | True | True | yes |
| D59_E_core__E_lift | lift_door | True | True | yes |
| D60_E_core_L1__E_lift | lift_door | True | True | yes |
| D61_E_core_L2__E_lift | lift_door | True | True | yes |
| D62_E_core_L3__E_lift | lift_door | True | True | yes |
| D63_T_link__T_L0 | door | True | True | yes |
| D64_T_L0__T_lift0 | lift_door | True | True | yes |
| D65_T_L1__T_lift0 | lift_door | True | True | yes |
| D66_T_L2__T_lift0 | lift_door | True | True | yes |
| D67_T_L3__T_lift0 | lift_door | True | True | yes |
| D68_T_L4__T_lift0 | lift_door | True | True | yes |
| D69_T_L5__T_lift0 | lift_door | True | True | yes |
| D70_T_L6__T_lift0 | lift_door | True | True | yes |
| D71_T_L7__T_lift0 | lift_door | True | True | yes |
| D72_T_L8__T_lift0 | lift_door | True | True | yes |
| D73_T_L9__T_lift0 | lift_door | True | True | yes |
| D74_T_L10__T_lift0 | lift_door | True | True | yes |
| D75_T_L11__T_lift0 | lift_door | True | True | yes |
| D76_T_L12__T_lift0 | lift_door | True | True | yes |
| D77_T_L13__T_lift0 | lift_door | True | True | yes |
| D78_T_L0__T_lift1 | lift_door | True | True | yes |
| D79_T_L1__T_lift1 | lift_door | True | True | yes |
| D80_T_L2__T_lift1 | lift_door | True | True | yes |
| D81_T_L3__T_lift1 | lift_door | True | True | yes |
| D82_T_L4__T_lift1 | lift_door | True | True | yes |
| D83_T_L5__T_lift1 | lift_door | True | True | yes |
| D84_T_L6__T_lift1 | lift_door | True | True | yes |
| D85_T_L7__T_lift1 | lift_door | True | True | yes |
| D86_T_L8__T_lift1 | lift_door | True | True | yes |
| D87_T_L9__T_lift1 | lift_door | True | True | yes |
| D88_T_L10__T_lift1 | lift_door | True | True | yes |
| D89_T_L11__T_lift1 | lift_door | True | True | yes |
| D90_T_L12__T_lift1 | lift_door | True | True | yes |
| D91_T_L13__T_lift1 | lift_door | True | True | yes |
| D92_T_L0__T_lift2 | lift_door | True | True | yes |
| D93_T_L1__T_lift2 | lift_door | True | True | yes |
| D94_T_L2__T_lift2 | lift_door | True | True | yes |
| D95_T_L3__T_lift2 | lift_door | True | True | yes |
| D96_T_L4__T_lift2 | lift_door | True | True | yes |
| D97_T_L5__T_lift2 | lift_door | True | True | yes |
| D98_T_L6__T_lift2 | lift_door | True | True | yes |
| D99_T_L7__T_lift2 | lift_door | True | True | yes |
| D100_T_L8__T_lift2 | lift_door | True | True | yes |
| D101_T_L9__T_lift2 | lift_door | True | True | yes |
| D102_T_L10__T_lift2 | lift_door | True | True | yes |
| D103_T_L11__T_lift2 | lift_door | True | True | yes |
| D104_T_L12__T_lift2 | lift_door | True | True | yes |
| D105_T_L13__T_lift2 | lift_door | True | True | yes |

## negative test: D63_T_link__T_L0 blocked  ->  **FAIL**

Expected result: FAIL. Negative test **PASSED** (the check correctly failed).

- doors ok: 104/106  (all pierce their wall: True)
- stair flights ok: 32/32
- spaces with floor + >=2.1 m headroom: 55/55
- lift shafts hollow: 5/5
- reachable from entrance: 40/55; unreachable: ['T_link', 'T_L0', 'T_L1', 'T_L2', 'T_L3', 'T_L4', 'T_L5', 'T_L6', 'T_L7', 'T_L8', 'T_L9', 'T_L10', 'T_L11', 'T_L12', 'T_L13']

Failures:

- door D16_gallery__T_link: clear=False wall=True blocked_at(h,lat,dist)=[2.0, 0.0, -0.35]
- door D63_T_link__T_L0: clear=False wall=True blocked_at(h,lat,dist)=[2.0, 0.0, -0.64]
- unreachable spaces from 'forecourt': ['T_link', 'T_L0', 'T_L1', 'T_L2', 'T_L3', 'T_L4', 'T_L5', 'T_L6', 'T_L7', 'T_L8', 'T_L9', 'T_L10', 'T_L11', 'T_L12', 'T_L13']
