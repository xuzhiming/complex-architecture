# v12 — clean junction between the arch tunnel and the courtyard; clear sight line through the arch

User: "庭院和拱门相交处的位置需要清理一下，不要有东西挡住拱门的视角"

**Diagnosis**
- I ran a BVH scan of the tunnel's clear arch profile (±9 m wide, 11 m high) from the portal back wall into the courtyard
  centre (y −41 … +2), and rendered eight cameras (`tools/arch_views.py`). The before images are in `renders/arch_view/before/`.
- The scan found two objects crossing the opening: the courtyard balcony rails `CourtRail_4.5` and `CourtRail_9.0`. Both are
  full ellipse rings and ran straight across the tunnel mouth at z 4.5–5.6 and 9.0–10.1 m.
- The tunnel vault ran 0.3 m past the arcade wall at the jambs and about 1.1 m past it on the axis, so it stuck out as a
  hood into the courtyard.
- The arcade wall cut (x = ±9 m) was coplanar with the vault's inner face. In renders this showed as a black flickering strip
  up both jambs of the courtyard mouth.
- The tunnel→gallery side openings reached into the arcade wall's thickness, notching the jamb.
- The same coplanar problem existed on the outer great portal. The podium shell cut, the portal lining and the first
  archivolt all had reveal faces at x = ±25 m, which showed as black lines up both jambs seen from the forecourt.
- The tunnel's forecourt end had the same coplanar problem. The portal back wall was cut at x = ±9 m, exactly on the vault's
  inner face, which showed as black lines up both tunnel jambs. These were the dark lines framing the view through the arch
  from the forecourt.
- There were no leftover blocks, bridges, steps or doors in the opening. The tunnel→courtyard link is an open passage with
  no door leaf.

**Changes (build.py)**
- **Courtyard rails:** the tier 4.5 and 9.0 rails are cut back where they pass the portal and now stop against the new frame.
  The tier 13.5 rail runs above the frame (frame top 12 m) and is unchanged.
- **Tunnel vault:** it is built 1.5 m long, then trimmed by the courtyard ellipse, so it ends exactly flush with the
  arcade wall's inner face.
- **Arcade wall opening:** it is cut to the vault's outer profile (hw + 0.6, rise + 0.6). The vault alone forms the jambs, so
  the wall and vault no longer overlap.
- **New `CourtPortalFrame`:** a 1.0 m arch band around the opening.
  - Its opening is exactly the tunnel's clear profile, it follows the curved arcade face, and it stands 0.35 m proud of it.
  - It meets the vault edge to edge, with no coplanar faces.
  - The nearest arcade bays (x ±12.3 m) end about 1.1 m from it, which is a normal pier width. No half bays or slivers.
- **Tunnel→gallery side openings:** kept for circulation, but narrowed to stay 0.7 m clear of the arcade wall.
- **Outer portal:** the shell is cut to the lining's outer profile, and the lining now starts where the first archivolt ends
  (FRONT_Y + 0.2). All three reveals meet edge to edge, and the black jamb lines are gone.
- **Tunnel entrance:** the portal back wall is cut to the vault's outer profile, and the vault now starts flush with the back
  wall's front face. The vault alone forms the tunnel-mouth reveal, and the black jamb lines are gone.
- **Circulation:** spaces and doors are unchanged in topology. portal_tunnel ↔ courtyard is still an open 18 m passage, and the
  portal_tunnel ↔ gallery doors are rebuilt from the narrower openings.
- **Result:** the BVH scan of the clear profile now finds 0 objects. The forecourt sight line runs through the tunnel and
  courtyard to the far arcade and the tower.
- Before/after comparison (same cameras): `renders/arch_view_before_after.png`.
