# =====================================================================
# v4 PARAMETRIC BUILD  -  all geometry generated from params.json
#   blender -b -P build.py                 (full: exterior + interior, saves .blend/.glb + spaces.json)
#   MODE=sil blender -b -P build.py        (fast exterior-only build used by the compare loop; renders silhouettes)
# env: PARAMS=path/to/params.json  OUTDIR=dir  SIL_DIR=dir
# =====================================================================
import bpy, bmesh, math, os, json, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.environ.get("PARAMS", os.path.join(HERE, "params.json"))))
MODE = os.environ.get("MODE", "full")
FULL = MODE == "full"
OUT = os.environ.get("OUTDIR", HERE)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
COL = bpy.data.collections.new("Building"); scene.collection.children.link(COL)
exec(open(os.path.join(HERE, "src", "geom.py")).read())
exec(open(os.path.join(HERE, "src", "detail.py")).read())   # v6: instanced windows, balconies, rib plates, arch bridges

G, POD, ARC, TUN, CY, TW, ST = P["global"], P["podium"], P["arch"], P["tunnel"], P["courtyard"], P["tower"], P["stairs"]
DR = P["doors"]
FH = G["floor_h"]

# ---------------------------------------------------------------------
# plan outlines (superellipse, sampled)
# ---------------------------------------------------------------------
class Outline:
    def __init__(s, hw, hd, cy, n, N=256):
        s.N = N; s.pts = []
        for i in range(N):
            th = 2*math.pi*i/N; c, sn = math.cos(th), math.sin(th)
            r = (abs(c/hw)**n + abs(sn/hd)**n) ** (-1.0/n)
            s.pts.append((r*c, cy + r*sn))
        s.nrm = []
        for i in range(N):
            p0, p1 = s.pts[i - 1], s.pts[(i + 1) % N]
            tx, ty = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(tx, ty); s.nrm.append((ty/L, -tx/L))
        s.cy = cy; s.hw = hw; s.hd = hd; s.n = n
    def off(s, i, d):
        p, q = s.pts[i % s.N], s.nrm[i % s.N]; return (p[0] + q[0]*d, p[1] + q[1]*d)
    def y_front(s, x):   # front (south) boundary y at given x
        n = s.n; v = 1 - abs(x/s.hw)**n
        return s.cy - s.hd*max(v, 0)**(1.0/n)
    def inside(s, x, y, margin=0.0):
        return (abs(x/(s.hw - margin))**s.n + abs((y - s.cy)/(s.hd - margin))**s.n) < 1.0
    def loft(s, name, prof, m=None):
        m = m or CLAY; N = s.N; verts, faces = [], []
        for (d, z) in prof:
            for i in range(N):
                x, y = s.off(i, d); verts.append((x, y, z))
        R = len(prof)
        for j in range(R - 1):
            for i in range(N):
                a, b = j*N + i, j*N + (i + 1) % N; faces.append([a, b, b + N, a + N])
        cb = len(verts); verts.append((0, s.cy, prof[0][1])); ct = len(verts); verts.append((0, s.cy, prof[-1][1]))
        for i in range(N):
            faces.append([cb, (i + 1) % N, i]); faces.append([ct, (R - 1)*N + i, (R - 1)*N + (i + 1) % N])
        return mesh_from(name, verts, faces, m)
    def loft_ring(s, name, d_out, d_in, z0, z1, m=None):
        m = m or CLAY; N = s.N; verts, faces = [], []
        for (d, z) in ((d_out, z0), (d_out, z1), (d_in, z1), (d_in, z0)):
            for i in range(N):
                x, y = s.off(i, d); verts.append((x, y, z))
        for j in range(4):
            j2 = (j + 1) % 4
            for i in range(N):
                a, b = j*N + i, j*N + (i + 1) % N; c2, d2 = j2*N + (i + 1) % N, j2*N + i
                faces.append([a, b, c2, d2])
        return mesh_from(name, verts, faces, m)

WALL = Outline(POD["wall_half_w"], POD["wall_half_d"], POD["wall_cy"], POD["wall_n"])
DECK = Outline(POD["deck_half_w"], POD["deck_half_d"], POD["deck_cy"], POD["deck_n"])
DB, DT = POD["deck_bot"], POD["deck_top"]
CC = (CY["cx"], CY["cy"]); CR = CY["r"]
KX = CY.get("kx", 1.0)          # v7: elliptical courtyard, x semi-axes = KX * (y semi-axes); KX = 1 -> circle
def EP(R, a): return (CC[0] + R*KX*math.cos(a), CC[1] + R*math.sin(a))          # point on the ellipse "radius" R at parameter a
def EN(a): return math.atan2(KX*math.sin(a), math.cos(a))                        # outward normal angle there
def EPAR(px, py): return math.atan2(py - CC[1], (px - CC[0])/KX)                 # parameter of the ray towards (px, py)
def ecut(R, z0, z1, seg=128): return cyl("cut", R, z0, z1, (CC[0], CC[1], 0), seg, sx=KX)
R_ARC_OUT = CR + CY["wall_t"]                      # outer face of arcade wall
R_GAL_OUT = R_ARC_OUT + CY["gallery_w"]            # inner face of gallery outer wall
TC = (TW["cx"], TW["cy"])
FRONT_Y = WALL.y_front(ARC["cx"])

def tower_r_at(z):
    for (r, z0, z1) in TW["drums"]:
        if z0 - 1e-6 <= z < z1: return r
    return TW["drums"][-1][0]

def cyl_cut(r, c, z0=-2, z1=200, seg=96): return cyl("cut", r, z0, z1, (c[0], c[1], 0), seg)

# =====================================================================
# EXTERIOR
# =====================================================================
ROLE = "ground"
DECK.loft("GroundSlab", [(14.0, -0.35), (14.0, 0.0)])
ROLE = "shell"
shell = WALL.loft_ring("PodiumShell", 0.0, -POD["wall_t"], 0.0, DB + 0.2)
DE, FO = POD.get("deck_edge_z", DB + 2.4), POD["fascia_out"]
# knife-edge deck: concave soffit rising from deck_bot to a thin lip at deck_edge_z, thin plate back to the wall line, deck_top inboard
deck = DECK.loft("PodiumDeck", [(-16, DB), (-7.0, DB), (-3.0, DB + (DE - DB)*0.35), (FO - 1.6, DE - 0.75), (FO - 0.6, DE - 0.4)] +
                               [(FO - 0.42 + 0.42*math.cos(math.radians(a)), DE + 0.05 + 0.42*math.sin(math.radians(a))) for a in (-90, -55, -25, 0, 25, 55, 90)] +   # v6 rounded nose
                               [(FO - 1.2, DE + 0.55), (-8.0, DE + 0.7), (-13.0, DT), (-16, DT)])
smooth(deck)

# doors / portal positions on the shell
EXT_DOORS = []
for side, wd in (("W", P["wings"]["west"]), ("E", P["wings"]["east"])):
    x = wd["ext_door_x"]; EXT_DOORS.append((side, x, WALL.y_front(x)))

shell_cuts, deck_cuts = [], []
win_items, win_lights = [], []
loggia_items, loggia_lights = [], []
if FULL:
    # arcade windows: recessed arches around the shell on each podium level (not through)
    acc, last = 0.0, None
    for i in range(WALL.N):
        p = WALL.off(i, 0.0)
        if last is not None: acc += math.hypot(p[0] - last[0], p[1] - last[1])
        last = p
        if acc < POD["window_pitch"]: continue
        acc = 0.0
        if p[1] < WALL.cy and abs(p[0] - ARC["cx"]) < ARC["hw"] + 3: continue
        if any(abs(p[0] - x) < 4 and abs(p[1] - y) < 4 for (_, x, y) in EXT_DOORS): continue
        if math.hypot(p[0] - TC[0], p[1] - TC[1]) < TW["drums"][0][0] + 2: continue
        nx, ny = WALL.nrm[i]; ang = math.atan2(ny, nx)
        LG = POD.get("loggia")
        for lv in (POD["levels"][:-1] if LG else POD["levels"]):
            win_items.append((p[0], p[1], lv + 0.9, ang, POD["window_hw"], POD["window_spring"], POD["window_rise"], 2*POD["window_recess"]))
            win_lights.append((p[0] - nx*(POD["window_recess"] - 0.02), p[1] - ny*(POD["window_recess"] - 0.02), lv + 0.9, ang))
    LG = POD.get("loggia")
    if LG:   # top storey = continuous open arcaded loggia: arches cut right through the shell at their own pitch
        acc, last = 0.0, None
        for i in range(WALL.N*4):
            th = 2*math.pi*i/(WALL.N*4); c_, sn_ = math.cos(th), math.sin(th)
            rr = (abs(c_/WALL.hw)**WALL.n + abs(sn_/WALL.hd)**WALL.n) ** (-1.0/WALL.n)
            p = (rr*c_, WALL.cy + rr*sn_)
            if last is not None: acc += math.hypot(p[0] - last[0], p[1] - last[1])
            last = p
            if acc < LG["pitch"]: continue
            acc = 0.0
            if p[1] < WALL.cy and abs(p[0] - ARC["cx"]) < ARC["hw"] + 3.2: continue
            if math.hypot(p[0] - TC[0], p[1] - TC[1]) < TW["drums"][0][0] + 2.5: continue
            nx, ny = WALL.nrm[(i//4) % WALL.N]; ang = math.atan2(ny, nx)
            loggia_items.append((p[0], p[1], POD["levels"][-1] + LG["sill"], ang, LG["hw"], LG["spring"], LG["rise"], 3.0))
            loggia_lights.append((p[0] - nx*(LG["depth"] - 0.05), p[1] - ny*(LG["depth"] - 0.05), POD["levels"][-1] + LG["sill"], ang))
    shell_cuts.append(arch_prisms("cut_win", win_items))
    if loggia_items: shell_cuts.append(arch_prisms("cut_loggia_arcade", loggia_items))
    # great portal through the shell
    shell_cuts.append(arch_prisms("cut_portal", [(ARC["cx"], FRONT_Y, 0.0, -math.pi/2, ARC["hw"], ARC["spring"], ARC["rise"], 3.0)]))
    # exterior pedestrian doors (arched, through)
    for (_, x, y) in EXT_DOORS:
        shell_cuts.append(arch_prisms("cut_extdoor", [(x, y + 0.2, 0.0, -math.pi/2, DR["ext_w"]/2, DR["ext_h"] - DR["ext_w"]/2, DR["ext_w"]/2, 3.0)]))
    shell_cuts.append(cyl_cut(TW["drums"][0][0] - 0.2, TC, -1, DB + 1))
    boolean(shell, shell_cuts)
    # loggia recesses in the deck fascia
    fitems, acc, last = [], 0.0, None
    for i in range(DECK.N):
        p = DECK.off(i, POD["fascia_out"])
        if last is not None: acc += math.hypot(p[0] - last[0], p[1] - last[1])
        last = p
        if acc < 4.0: continue
        acc = 0.0
        if math.hypot(p[0] - TC[0], p[1] - TC[1]) < TW["drums"][0][0] + 3: continue
        nx, ny = DECK.nrm[i]; fitems.append((p[0], p[1], DB + 1.0, math.atan2(ny, nx), 1.0, 1.3, 1.0, 2.6))
    if POD.get("fascia_loggia", False): deck_cuts.append(arch_prisms("cut_loggia", fitems))   # off: the deck edge is now a thin knife-edge
deck_cuts += [ecut(CR + 0.05, DB - 1, DT + 3), cyl_cut(TW["drums"][0][0] - 0.2, TC, DB - 1, DT + 3)]
boolean(deck, deck_cuts)

# loggia back wall (open arcade gallery behind the top-storey arches)
if FULL and loggia_items:
    LG = POD["loggia"]; zl = POD["levels"][-1]
    lbw = WALL.loft_ring("LoggiaBackWall", -LG["depth"], -LG["depth"] - 0.35, zl, DB + 0.3)
    lbw_cuts = [cyl_cut(TW["drums"][0][0] + 0.5, TC, zl - 1, DB + 1),
                arch_prisms("c", [(ARC["cx"], FRONT_Y + 2, -0.5, -math.pi/2, ARC["hw"] + 0.6, ARC["spring"] + 0.5, ARC["rise"] + 0.6, 14.0)])]
    boolean(lbw, lbw_cuts)
    win_lights += [("loggia",) + l for l in loggia_lights]
# window glow planes (role window_light) inside recesses
if FULL and win_lights:
    ROLE = "window_light"
    bm = bmesh.new()
    for wl in win_lights:
        lg = wl[0] == "loggia"; (x, y, z0, ang) = wl[1:] if lg else wl
        nx, ny = math.cos(ang), math.sin(ang); tx, ty = -ny, nx
        if lg: hw = POD["loggia"]["hw"]*0.85; h = POD["loggia"]["spring"] + POD["loggia"]["rise"]*0.7
        else: hw = POD["window_hw"]*0.9; h = POD["window_spring"] + POD["window_rise"]*0.6
        vs = [bm.verts.new((x + tx*u, y + ty*u, z0 + v)) for (u, v) in ((-hw, 0.1), (hw, 0.1), (hw, h), (-hw, h))]
        bm.faces.new(vs)
    me = bpy.data.meshes.new("WindowLights"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("WindowLights", me); scene.collection.objects.link(o); link(o)
    ROLE = "shell"

# ---------------- portal recess + tunnel vault ----------------
def arch_tube(name, x, y_mid, length, hw, sp, rise, t):
    outer = arch_prisms(name, [(x, y_mid, 0.0, -math.pi/2, hw + t, sp, rise + t, length)])
    if FULL or True:
        boolean(outer, [arch_prisms("c", [(x, y_mid, -0.5, -math.pi/2, hw, sp + 0.5, rise, length + 2)])])
    return outer
PORTAL_BACK = FRONT_Y + ARC["portal_depth"]
arch_tube("PortalLining", ARC["cx"], (FRONT_Y + PORTAL_BACK)/2, ARC["portal_depth"] + 0.2, ARC["hw"], ARC["spring"], ARC["rise"], 0.6)
pb = arch_prisms("PortalBackWall", [(ARC["cx"], PORTAL_BACK, 0.0, -math.pi/2, ARC["hw"] + 0.3, ARC["spring"], ARC["rise"] + 0.3, 0.6)])
boolean(pb, [arch_prisms("c", [(ARC["cx"], PORTAL_BACK, -0.5, -math.pi/2, TUN["hw"], TUN["spring"] + 0.5, TUN["rise"], 2.0)])])
# archivolts on the shell face
for k, (grow, dep) in enumerate(P.get("detail", {}).get("archivolts", [[1.4, 1.6], [2.8, 1.0]])):   # v6: layered, stepped archivolts
    av = arch_prisms(f"Archivolt{k}", [(ARC["cx"], FRONT_Y - dep/2 + 0.2, 0.0, -math.pi/2, ARC["hw"] + grow, ARC["spring"], ARC["rise"] + grow*0.8, dep)])
    boolean(av, [arch_prisms("c", [(ARC["cx"], FRONT_Y - dep/2 + 0.2, -0.5, -math.pi/2, ARC["hw"] + grow - 1.4, ARC["spring"] + 0.5, ARC["rise"] + grow*0.8 - 1.4, dep + 2)])])
AVL = P.get("detail", {}).get("archivolts", [[1.4, 1.6], [2.8, 1.0]]); gmax = max(g for g, _ in AVL)
box("ArchKeystone", (2.4, AVL[0][1] + 0.6, 3.2), (ARC["cx"], FRONT_Y - (AVL[0][1] + 0.6)/2 + 0.2, ARC["spring"] + ARC["rise"] + gmax*0.8 - 1.0))
for sx_ in (-1, 1):   # impost blocks where the archivolts spring
    box(f"ArchImpost{sx_}", (gmax + 1.2, AVL[0][1] + 0.4, 0.9), (ARC["cx"] + sx_*(ARC["hw"] + gmax/2), FRONT_Y - (AVL[0][1] + 0.4)/2 + 0.2, ARC["spring"] - 0.45))
# tunnel from portal back wall to the arcade wall of the courtyard
Y_TUN_END = CC[1] - CR*math.sqrt(max(1 - (TUN["hw"]/(CR*KX))**2, 0)) + 0.3
tun = arch_tube("TunnelVault", ARC["cx"], (PORTAL_BACK + Y_TUN_END)/2, Y_TUN_END - PORTAL_BACK, TUN["hw"], TUN["spring"], TUN["rise"], 0.6)
# side openings where the gallery ring crosses the tunnel
def ring_y(R, x): return CC[1] - R*math.sqrt(max(1 - (x/(R*KX))**2, 0))
GX = TUN["hw"] + 0.3
gy0, gy1 = ring_y(R_GAL_OUT, GX), ring_y(R_ARC_OUT, GX)
TUN_SIDE_OPEN = (gy0 + 0.3, gy1 - 0.3)
if FULL:
    boolean(tun, [box("c", (2.0, TUN_SIDE_OPEN[1] - TUN_SIDE_OPEN[0], 3.0), (sx*GX, (TUN_SIDE_OPEN[0] + TUN_SIDE_OPEN[1])/2, 1.5)) for sx in (-1, 1)])

# ---------------- courtyard arcade wall (4 tiers) + rim ----------------
cwall = ring("CourtArcadeWall", CR, R_ARC_OUT, 0.0, DT + CY["rim_h"], (CC[0], CC[1], 0), 160, sx=KX)
ARCADE_OPEN = []   # L0 arcade openings (courtyard <-> gallery)
citems = []
n = CY["n_arches"]
def eq_angles(n, R=(CR + R_ARC_OUT)/2, m=2048):
    # v7: on the ellipse, space arches by equal arc length (uniform angle would cram them at the x-ends)
    acc = [0.0]
    for i in range(m):
        a0, a1 = 2*math.pi*i/m, 2*math.pi*(i + 1)/m
        acc.append(acc[-1] + math.dist(EP(R, a0), EP(R, a1)))
    out, j = [], 0
    for k in range(n):
        tgt = acc[-1]*(k + 0.5)/n
        while acc[j + 1] < tgt: j += 1
        out.append(2*math.pi*(j + (tgt - acc[j])/(acc[j + 1] - acc[j]))/m)
    return out
ARCH_ANGS = eq_angles(n)
for lv in CY["tiers"]:
    for a in ARCH_ANGS:
        if abs(((a - 1.5*math.pi + math.pi) % (2*math.pi)) - math.pi) < math.asin(min(1, (TUN["hw"] + 1.5)/(CR*KX))): continue
        r = (CR + R_ARC_OUT)/2; pe = EP(r, a)
        citems.append((pe[0], pe[1], lv + (0.0 if lv == 0 else 1.0), EN(a), CY["arch_hw"], CY["arch_spring"], CY["arch_rise"], CY["wall_t"]*KX + 1.0))
        if lv == 0: ARCADE_OPEN.append(a)
citems.append((ARC["cx"], CC[1] - CR, -0.5, -math.pi/2, TUN["hw"], TUN["spring"] + 0.5, TUN["rise"], 6.0))
if FULL: boolean(cwall, [arch_prisms("cut_courtarch", citems)])
rounded_band("CourtRim", (CC[0], CC[1], 0), R_ARC_OUT, DT + CY["rim_h"], 0.9, 0.7, 160, sx=KX)
for lv in CY["tiers"][1:]:   # balcony rails on upper tiers (inside face)
    ring(f"CourtRail_{lv}", CR - 0.35, CR - 0.15, lv, lv + 1.1, (CC[0], CC[1], 0), 160, sx=KX)

# ---------------- flared tree columns ----------------
COLS = P["columns"]
def column_profile():
    br, sr, fr = COLS["base_r"], COLS["shaft_r"], COLS["flare_r"]
    fz0, fp = COLS.get("flare_z0", 14.0), COLS.get("flare_p", 1.1)
    ztop = DE - 0.6
    prof = [(0, 0), (br, 0), (br*0.7 + sr*0.3, 0.5), (sr, 1.6), (sr, fz0)]
    for k in range(1, 9):
        z = fz0 + (ztop - fz0)*k/8; prof.append((sr + (fr - sr)*(k/8)**fp, z))
    prof += [(fr, ztop + 0.6), (0, ztop + 0.6)]
    return prof
for k, (x, y) in enumerate(COLS["positions"]):
    prof = column_profile()
    lathe(f"TreeColumn{k}", prof, 64, (x, y, 0))
    # v6: solid rib plates following the flare (ribbed flaring head), thin on the shaft, deep under the deck
    fl = [(r, z) for (r, z) in prof[3:-2] if z >= COLS.get("flare_z0", 14.0) - 4.0]
    outer = [(r + 0.15 + 0.55*(i/(len(fl) - 1))**1.5, z) for i, (r, z) in enumerate(fl)]
    inner = [(max(r - 0.4, 0.3), z) for (r, z) in fl][::-1]
    rib_plates(f"TreeRibs{k}", (x, y), outer + inner, COLS["ribs"], 0.38)

# ---------------- tower exterior ----------------
DOOR_ANG_T = math.atan2(CC[1] - TC[1], CC[0] - TC[0])   # tower faces the courtyard here
tower_shells = []
TD = P.get("detail", {}).get("tower", {})
for k, (r, z0, z1) in enumerate(TW["drums"]):
    # v6: solid clay shell (no dark drum behind fins) carrying instanced arched / tall-rect windows
    sh = ring(f"TowerShell{k}", r - 0.5 - TW["shell_t"], r - 0.5, z0, z1, (TC[0], TC[1], 0), 128, CLAY)
    tower_shells.append(sh)
    zz = [z for z in [FH*j for j in range(0, 30)] if z0 < z < z1 + 0.01]
    for z in zz:   # thick rounded floor-edge belts
        rounded_band(f"TowerBand{k}_{int(z*10)}", (TC[0], TC[1], 0), r - 0.3, z, TD.get("band_h", 1.05), TD.get("band_out", 1.15), 128)
    rib_angles = []
    for j in range(TW["ribs_per_drum"]):   # buttress pilasters: stepped foot, slender shaft, corbelled head
        a = 2*math.pi*(j + 0.5*(k % 2))/TW["ribs_per_drum"] + 0.15
        if z0 < 1 and abs(((a - DOOR_ANG_T + math.pi) % (2*math.pi)) - math.pi) < 0.25: continue
        rib_angles.append(a)
        p = (TC[0] + (r + 0.2)*math.cos(a), TC[1] + (r + 0.2)*math.sin(a))
        lathe(f"TowerRib{k}_{j}", [(0, z0), (1.25, z0), (1.25, z0 + 1.6), (0.85, z0 + 2.4), (0.72, z1 - 2.0), (1.05, z1 - 0.9), (1.05, z1), (0, z1)], 12, (p[0], p[1], 0))
    if FULL:
        rw = r - 0.5; pitch = TD.get("win_pitch", 2.7)
        n = max(8, int(2*math.pi*rw/pitch))
        skip = [(a, 1.6/rw) for a in rib_angles] + ([(DOOR_ANG_T, 0.2)] if z0 < 1 else [])
        wfl = [FH*j for j in range(0, 30) if z0 - 0.01 <= FH*j and FH*j + FH <= z1 + 0.3]
        for f_i, zf in enumerate(wfl):
            arched = (f_i + k) % 2 == 0
            wt = window_type("tw_arch", 0.62, 2.0, 0.62) if arched else window_type("tw_rect", 0.55, 2.55, 0.12)
            ring_windows(f"TW{k}", TC, rw, zf + 0.85, wt, n, phase=0.11*f_i, skip=skip, lit_p=0.35,
                         keep=lambda x, y, z: z > DT + 0.5 or not DECK.inside(x, y, -1.5))   # nothing inside the podium or under the deck
    rounded_band(f"TowerStep{k}", (TC[0], TC[1], 0), r, z1, 1.6, 1.6, 128)
for k, (z, dx, dy, ro) in enumerate(TW["belts"]):   # offset cantilever belts (thick rounded)
    ri = tower_r_at(z) - 1.0; hb = TD.get("belt_h", 1.0)
    lathe(f"TowerBelt{k}", [(ri, z - hb), (ro - 1.2, z - hb), (ro - 0.25, z - hb*0.6), (ro + 0.1, z), (ro - 0.25, z + hb*0.6), (ro - 1.2, z + hb), (ri, z + hb), (ri, z - hb)],
          128, (TC[0] + dx, TC[1] + dy, 0))
    rib_plates(f"TowerBeltBrackets{k}", (TC[0] + dx, TC[1] + dy), [(ri + 0.5, z - hb), (ro - 1.4, z - hb), (ri + 0.5, z - hb - 2.2)], 14, 0.35, 0.2*k)
# balconies: sector slabs with parapets on alternate floors, rotating around the tower
BT = TD.get("balconies", {"every": 2, "depth": 2.2, "span_deg": 40, "per_floor": 3})
bfl = [FH*j for j in range(2, 40) if FH*j < TW["floors_top"] - 1 and j % BT["every"] == 0]
bm_ = bmesh.new()
for kk, zf in enumerate(bfl):
    rwall = tower_r_at(zf) - 0.5
    for jb in range(BT["per_floor"]):
        a0 = 2*math.pi*jb/BT["per_floor"] + kk*0.9 + 0.35
        sector_bm(bm_, TC, rwall - 0.2, rwall + BT["depth"], a0, a0 + math.radians(BT["span_deg"]), zf - 0.35, zf, 10)
        sector_bm(bm_, TC, rwall + BT["depth"] - 0.2, rwall + BT["depth"], a0, a0 + math.radians(BT["span_deg"]), zf, zf + 1.05, 10)
bm_object("TowerBalconies", bm_)
canopy("TowerCrown", TW["crown_R"], TW["crown_z"], TC, t=1.8, fins=12, r_drum=TW["drums"][-1][0] - 0.5, lip_k=0.45)
lathe("TowerDome", [(TW["dome_r"], 0), (TW["dome_r"]*0.92, TW["dome_h"]*0.45), (TW["dome_r"]*0.6, TW["dome_h"]*0.85), (0, TW["dome_h"])], 96, (TC[0], TC[1], TW["crown_z"] + 0.6))
ring("TowerParapet", TW["drums"][-1][0] - 1.2, TW["drums"][-1][0] - 0.4, TW["drums"][-1][2], TW["crown_z"], (TC[0], TC[1], 0), 96)
# v6 crown detail: secondary under-disc, ribbed soffit, dome lantern with ring of mini-arches
canopy("TowerCrownUnder", TW["crown_R"]*0.72, TW["crown_z"] - 2.2, TC, t=0.9, r_drum=TW["drums"][-1][0] - 0.5, lip_k=0.3, ribs=True)
DZ = TW["crown_z"] + 0.6 + TW["dome_h"]
cyl("TowerLantern", TW["dome_r"]*0.32, DZ - 0.3, DZ + 1.6, (TC[0], TC[1], 0), 32)
lathe("TowerLanternCap", [(TW["dome_r"]*0.42, 0), (TW["dome_r"]*0.4, 0.25), (TW["dome_r"]*0.22, 0.75), (0, 1.0)], 32, (TC[0], TC[1], DZ + 1.6))
fins_around("TowerLanternFins", TC, TW["dome_r"]*0.32, DZ - 0.3, DZ + 1.6, 12, w=0.18, d=0.25)

# ---------------- canopies with drums ----------------
CS = P.get("canopy_scale", 1.0)
RIMS = []
for cp in P["canopies"]:
    c = (cp["cx"], cp["cy"]); r = cp["drum_r"]
    rx, ry = cp["rx"]*CS, cp["ry"]*CS
    R = max(rx, ry)
    if cp.get("style") == "column_tower":
        # v6 side tower: slim windowed core + ring of slender columns with stacked rounded floors, trumpet flare under the cap
        nc, rc = cp.get("n_cols", 8), cp.get("col_r", 0.55)
        drum(cp["name"], c, r*0.62, DE - 0.3, cp["z"] - 3.0, band=FH)
        for j in range(nc):
            a = 2*math.pi*(j + 0.5)/nc
            lathe(f'{cp["name"]}_col{j}', [(0, DE - 0.3), (rc*1.5, DE - 0.3), (rc*1.5, DE + 0.6), (rc, DE + 1.4), (rc, cp["z"] - 3.4), (rc*1.6, cp["z"] - 2.6), (0, cp["z"] - 2.6)],
                  16, (c[0] + (r - 0.7)*math.cos(a), c[1] + (r - 0.7)*math.sin(a), 0))
        for zb in [DE - 0.3 + FH*(q + 1) for q in range(int((cp["z"] - DE - 3.0)/FH))]:
            ring(f'{cp["name"]}_floor{int(zb)}', r*0.62 - 0.5, r + 0.15, zb - 0.3, zb + 0.25, (c[0], c[1], 0), 64)
        lathe(cp["name"] + "_trumpet", [(0, cp["z"] - 8.0), (r*0.62, cp["z"] - 8.0), (r*0.7, cp["z"] - 5.0), (r*0.95, cp["z"] - 2.6), (r*1.35, cp["z"] - 0.6),
                                        (r*1.5, cp["z"] + 0.2), (0, cp["z"] + 0.2)], 64, (c[0], c[1], 0))
    else:
        drum(cp["name"], c, r, DE - 0.3, cp["z"], band=FH)
    canopy(cp["name"] + "_canopy", R, cp["z"] + 0.6, c, sx=rx/R, sy=ry/R, lip_k=cp.get("lip", 0.3), r_drum=r, ribs=True)
    canopy(cp["name"] + "_fins", r + 0.6, cp["z"] + 0.3, c, t=0.7, fins=8, r_drum=r - 0.3, fin_c=min(min(rx, ry)*0.6, r + 6.0))
    if cp.get("dome"):
        lathe(cp["name"] + "_dome", [(r*0.8, 0), (r*0.72, r*0.3), (r*0.5, r*0.55), (r*0.22, r*0.7), (0, r*0.74)], 48, (c[0], c[1], cp["z"] + 1.0))
    RIMS.append((c, R, rx/R, ry/R, cp["z"] + 0.6, cp.get("lip", 0.3)))
    # v5: a canopy that reaches into the tower is trimmed to the tower's inner face, so it never
    # intrudes into the tower floors (found by the circulation headroom probe on T_L6)
    ri = tower_r_at(cp["z"]) - 0.5 - TW["shell_t"]
    if math.hypot(c[0] - TC[0], c[1] - TC[1]) - R < ri:
        for nm in (cp["name"] + "_canopy", cp["name"] + "_fins", cp["name"] + "_canopy_ribs"):
            ob = bpy.data.objects.get(nm)
            if ob: boolean(ob, [cyl("cut", ri, cp["z"] - 3.0, cp["z"] + 4.0, (TC[0], TC[1], 0), 128)])
RIMS.append((TC, TW["crown_R"], 1, 1, TW["crown_z"], 0.45))
if FULL:
    ROLE = "rim"
    for k, (c, R, sx, sy, z, lip) in enumerate(RIMS):
        t = min(1.9, 0.055*R + 0.55); zl = z + lip*t
        lathe(f"CanopyRim{k}", [(R - 0.05, zl - 0.12), (R + 0.12, zl - 0.04), (R + 0.12, zl + 0.06), (R - 0.05, zl + 0.1), (R - 0.05, zl - 0.12)], 128, (c[0], c[1], 0), sx, sy)
    ROLE = "shell"

# ---------------- infill masses (dense cluster between wings and tower) ----------------
for ms in P.get("masses", []):
    if ms["r"] <= 0.5 or ms["z1"] <= DT + 1: continue
    drum(ms["name"], (ms["cx"], ms["cy"]), ms["r"]*P.get("mass_scale", 1.0), DE - 0.3, ms["z1"], band=FH)
    rounded_band(ms["name"] + "_cap", (ms["cx"], ms["cy"], 0), ms["r"]*P.get("mass_scale", 1.0), ms["z1"], 1.2, 1.2, 96)
    cyl(ms["name"] + "_roof", ms["r"]*P.get("mass_scale", 1.0) - 0.3, ms["z1"] - 0.5, ms["z1"] + 0.6, (ms["cx"], ms["cy"], 0), 96)

# ---------------- crescent crown ----------------
CRS = P["crescent"]
def sweep_bank(name, pts, wfun, tfun, samples=220, bank=0.0):
    Pp = [Vector(p) for p in pts]
    def cr(t):
        n = len(Pp) - 1; f = t*n; i = min(int(f), n - 1); u = f - i
        p0 = Pp[max(i - 1, 0)]; p1 = Pp[i]; p2 = Pp[i + 1]; p3 = Pp[min(i + 2, n)]
        return 0.5*((2*p1) + (-p0 + p2)*u + (2*p0 - 5*p1 + 4*p2 - p3)*u*u + (-p0 + 3*p1 - 3*p2 + p3)*u**3)
    C = [cr(k/samples) for k in range(samples + 1)]
    NS = 24
    NS = 32; px, pz = CRS.get("sec_p", [0.7, 0.7])   # v6 blade section: full width, thin crisp edges (pz > 1), cambered top
    sec = [(math.copysign(abs(math.cos(a))**px, math.cos(a)), math.copysign(abs(math.sin(a))**pz, math.sin(a)) + CRS.get("camber", 0.0)*(1 - math.cos(a)**2))
           for a in [2*math.pi*k/NS for k in range(NS)]]
    verts, faces = [], []
    for k, p in enumerate(C):
        T = (C[min(k + 1, samples)] - C[max(k - 1, 0)]).normalized()
        S = T.cross(Vector((0, 0, 1)))
        if S.length < 1e-3: S = Vector((1, 0, 0))
        S.normalize(); U = S.cross(T).normalized()
        S, U = S*math.cos(bank) + U*math.sin(bank), U*math.cos(bank) - S*math.sin(bank)
        t = k/samples; w, h = wfun(t), tfun(t)
        for (a, b) in sec: verts.append(tuple(p + S*(a*w) + U*(b*h)))
    for k in range(samples):
        for j in range(NS):
            a = k*NS + j; b = k*NS + (j + 1) % NS; faces.append([a, b, b + NS, a + NS])
    faces.append(list(range(NS))[::-1]); faces.append([samples*NS + j for j in range(NS)])
    ob = mesh_from(name, verts, faces); smooth(ob); return ob
def crescent_pts(mirror=False, scale=1.0):
    base = Vector(CRS["pts"][0]); out = []
    # v6 constraint: the crescent post stands on the deck, so its foot must clear the (larger) courtyard void
    dvec = Vector((base.x - CC[0], base.y - CC[1], 0.0)); need = CR + CRS["post_r"] + 1.0
    push = dvec.normalized()*(need - dvec.length) if dvec.length < need else Vector((0, 0, 0))
    if CRS.get("pair"): push = Vector((0, 0, 0))   # pair mode places the post foot itself
    for p in CRS["pts"]:
        v = Vector(p) - base
        q = base + Vector((v.x*CRS.get("spread", 1.0), v.y*CRS.get("spread", 1.0), v.z*CRS.get("rise", 1.0)))
        q.z += CRS.get("dz", 0.0); q += push
        if mirror:
            q.x = 2*TC[0] - q.x
            q = Vector((TC[0], TC[1], q.z)) + (q - Vector((TC[0], TC[1], q.z)))*scale
            q.z = base.z + CRS.get("dz", 0.0) + (q.z - base.z - CRS.get("dz", 0.0))*scale
        out.append(tuple(q))
    return out
def crescent_d(t):
    D = CRS["d"]; f = t*(len(D) - 1); i = min(int(f), len(D) - 2); u = f - i
    return max(0.25, (D[i]*(1 - u) + D[i + 1]*u)*CRS.get("d_scale", 1.0))
def crescent_plate(name, ctr, e, R, ph_t, ph_b, w_mid, thick, vax=(0, 0, 1), sx=1.0, N=160, M=28):
    """v8: a clean PLANAR crescent moon in the vertical plane spanned by plan direction e and +Z.
    Outer boundary = arc of circle (0,0,R) from the tip angle ph_t round the far side to the base angle ph_b;
    inner boundary = circle through both ends and the outer mid-point moved inward by w_mid (thickest at mid-arc).
    Constant flat section (thick), corners rounded by a superellipse. No twist, no sweep."""
    a0, a1 = math.radians(ph_t), math.radians(ph_b) + 2*math.pi
    O = lambda a: (R*math.cos(a), R*math.sin(a))
    Pt, Pb = O(a0), O(a1); am = (a0 + a1)/2; Mi = ((R - w_mid)*math.cos(am), (R - w_mid)*math.sin(am))
    (x1, y1), (x2, y2), (x3, y3) = Pt, Mi, Pb
    dd = 2*(x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))
    ux = ((x1*x1 + y1*y1)*(y2 - y3) + (x2*x2 + y2*y2)*(y3 - y1) + (x3*x3 + y3*y3)*(y1 - y2))/dd
    uy = ((x1*x1 + y1*y1)*(x3 - x2) + (x2*x2 + y2*y2)*(x1 - x3) + (x3*x3 + y3*y3)*(x2 - x1))/dd
    ri = math.hypot(x1 - ux, y1 - uy)
    b0, bm_, b1 = [math.atan2(q[1] - uy, q[0] - ux) for q in (Pt, Mi, Pb)]
    # unwrap so the inner arc runs Pt -> Mi -> Pb
    def unwrap(x, ref):
        while x - ref > math.pi: x -= 2*math.pi
        while x - ref < -math.pi: x += 2*math.pi
        return x
    bm_ = unwrap(bm_, b0); b1 = unwrap(b1, bm_)
    e = Vector((e[0], e[1], 0)).normalized(); Z = Vector(vax).normalized(); nrm = e.cross(Z).normalized(); C0 = Vector(ctr)
    W = lambda s, z: C0 + e*(s*sx) + Z*z     # sx > 1: elliptical crescent (affine, still planar); plane spanned by e (horizontal) and vax (vertical, optionally leaning back)
    sec = [(math.copysign(abs(math.cos(t))**0.25, math.cos(t)), math.copysign(abs(math.sin(t))**0.25, math.sin(t)))
           for t in [2*math.pi*k/M for k in range(M)]]
    verts, faces = [], []
    for k in range(N + 1):
        f = k/N
        o = O(a0 + (a1 - a0)*f); bb = b0 + (b1 - b0)*f; i_ = (ux + ri*math.cos(bb), uy + ri*math.sin(bb))
        mid = W((o[0] + i_[0])/2, (o[1] + i_[1])/2); acr = W(o[0], o[1]) - W(i_[0], i_[1])
        hw = max(acr.length/2, 0.04); acr = acr.normalized() if acr.length > 1e-6 else Vector((0, 0, 1))
        ht = thick/2*min(1.0, 0.35 + hw/1.2)     # flat plate; only the last metre of each tip thins to a sharp edge
        for (u, v) in sec: verts.append(tuple(mid + acr*(u*hw) + nrm*(v*ht)))
    for k in range(N):
        for j in range(M):
            p_ = k*M + j; q_ = k*M + (j + 1) % M; faces.append([p_, q_, q_ + M, p_ + M])
    faces.append(list(range(M))[::-1]); faces.append([N*M + j for j in range(M)])
    ob = mesh_from(name, verts, faces); smooth(ob)
    return ob, W(*Pt), W(*Pb)

PR = CRS.get("pair")
PL = CRS.get("plate")
if PL:
    # v8 crown (user: follow the reference strictly, no twist, natural): two mirror-image planar crescents framing the tower
    # like ( ). Each lies in a vertical plane yawed by theta (bulge front-outboard, tips rear-inboard), so the front
    # elevation shows the pair and each side elevation shows the crescent C of the reference sheet.
    ax = PL.get("axis_x") if PL.get("axis_x") is not None else TC[0]
    # Each crescent: circle radius R in a plane yawed by theta about Z (horizontal axis e runs from the outboard bulge
    # towards the axis) and leaning back by alpha about e. Measured from the elevations, both the front and the side panels
    # show a ~45 m x 29 m C: a circular crescent at yaw ~45 deg, lean ~54 deg gives exactly that, and seen from the
    # front-high roof-plan view the two read as round ( ) moons.
    if PL.get("Ax"):
        # elliptical crescent in an upright plane: Ax / Ay = its semi-axis as seen in the front / side elevation (both sheets
        # show the same long low C), B = vertical semi-axis; the plane yaw follows from Ax/Ay. Still one flat plate, no twist.
        th = math.atan2(PL["Ay"], PL["Ax"]); A_ = math.hypot(PL["Ax"], PL["Ay"]); B_ = PL["B"]; uc = PL["uc"]*A_
        print("CRESCENT ellipse plane yaw", round(math.degrees(th), 1), "A", round(A_, 1), "B", B_)
        for sd, nm in ((-1, "CrescentCrownL"), (1, "CrescentCrownR")):
            e = (-sd*math.cos(th), math.sin(th))
            u_tip = -(PL["tip_gap"]/2)/math.cos(th)
            ph_t = math.degrees(math.acos(max(-1, min(1, (u_tip - uc)/A_))))
            ctr = (ax + e[0]*uc, TC[1] + e[1]*uc + PL.get("dy", 0.0), PL["zc"])
            ob, ptip, pbase = crescent_plate(nm, ctr, e, B_, ph_t, PL["ph_base"], PL["w_mid"], PL["thick"], sx=A_/B_)
            cut = cyl("cut", tower_r_at(max(DT, pbase.z)) - 0.45, DT, TW["crown_z"] - 1.5, (TC[0], TC[1], 0), 96)
            boolean(ob, [cut])
            print("CRESCENT", nm, "tip", tuple(round(c, 1) for c in ptip), "base", tuple(round(c, 1) for c in pbase))
        pts = [tuple(pbase)]
if PL and not PL.get("Ax"):
    th, al, R_ = math.radians(PL["theta"]), math.radians(PL["alpha"]), PL["R"]
    print("CRESCENT plane yaw", PL["theta"], "lean", PL["alpha"], "R", R_)
    for sd, nm in ((-1, "CrescentCrownL"), (1, "CrescentCrownR")):
        e = Vector((-sd*math.cos(th), math.sin(th), 0))
        w = Vector((-e.y, e.x, 0)) if sd < 0 else Vector((e.y, -e.x, 0))      # horizontal normal pointing to the rear
        v = Vector((0, 0, 1))*math.cos(al) + w*math.sin(al)
        pt = math.radians(PL["ph_tip"])
        off = e*(R_*math.cos(pt)) + v*(R_*math.sin(pt))                       # tip relative to the circle centre
        ctr = (ax + sd*PL["tip_gap"]/2 - off.x, TC[1] + PL["dy"], PL["zc"])
        ob, ptip, pbase = crescent_plate(nm, ctr, e, R_, PL["ph_tip"], PL["ph_base"], PL["w_mid"], PL["thick"], vax=tuple(v))
        cut = cyl("cut", tower_r_at(max(DT, pbase.z)) - 0.45, DT, TW["crown_z"] - 1.5, (TC[0], TC[1], 0), 96)
        boolean(ob, [cut])
        print("CRESCENT", nm, "tip", tuple(round(c, 1) for c in ptip), "base", tuple(round(c, 1) for c in pbase))
    pts = [tuple(pbase)]
elif PR and not PL:
    # v7 crown: TWO mirror-symmetric horn blades framing the tower (user's roof-plan reference). Each horn keeps the
    # side-elevation (y, z) profile fitted to the LEFT/RIGHT reference panels (both horns coincide in the side views);
    # in plan/front it springs beside the tower, bulges outward, then curls inward with the tips leaving a gap above the tower.
    yz = crescent_pts(); n_ = len(yz)
    ax = PR.get("axis_x") if PR.get("axis_x") is not None else TC[0]
    bdx, bul, tdx = PR["base_dx"], PR["bulge"], PR["tip_dx"]
    def xoff(t): return bdx + (tdx - bdx)*t**PR.get("curl_p", 1.6) + bul*math.sin(math.pi*min(1.0, t*1.4))
    m_ = CRS["post_r"] + 1.0; A_, B_ = CR*KX + m_, CR + m_
    def ymin(x):
        v = 1 - ((x - CC[0])/A_)**2
        return CC[1] + B_*math.sqrt(v) if v > 0 else -1e9
    yb = max(yz[0][1], ymin(ax - bdx), ymin(ax + bdx)) + 0.3     # post foot must clear the courtyard void
    zb = yz[0][2] - PR.get("base_drop", 4.0)
    for sd, nm in ((-1, "CrescentCrownL"), (1, "CrescentCrownR")):
        hp = [(ax + sd*xoff(i/(n_ - 1)), yb if i == 0 else p[1], zb if i == 0 else p[2]) for i, p in enumerate(yz)]
        sweep_bank(nm, hp, lambda t: crescent_d(t)/2*PR.get("thick", 0.32), lambda t: crescent_d(t)/2*CRS.get("flat", 0.85),
                   bank=math.radians(CRS.get("bank", 0.0)))
        cyl(nm + "_Post", CRS["post_r"], DT, zb + 0.6, (hp[0][0], hp[0][1], 0), 48)
        drum(nm + "_PostDrum", (hp[0][0], hp[0][1]), CRS["post_r"] + 0.8, DT, max(DT + 6, zb - 3.0), band=FH)
    pts = [(ax - bdx, yb, zb)]
elif not PL:
    pts = crescent_pts()
    sweep_bank("CrescentCrown", pts, lambda t: crescent_d(t)/2, lambda t: crescent_d(t)/2*CRS.get("flat", 0.8), bank=math.radians(CRS.get("bank", 0.0)))
    cyl("CrescentPost", CRS["post_r"], DT, pts[0][2] + 0.5, (pts[0][0], pts[0][1], 0), 48)
    drum("CrescentPostDrum", (pts[0][0], pts[0][1]), CRS["post_r"] + 0.8, DT, pts[0][2] - 3.0, band=FH)

# ---------------- bridges ----------------
BRD = P.get("detail", {}).get("bridge", {})
for k, pl in enumerate(P["bridges"]):   # v6: slender curved bridges: thin deck, open railing, under-slung arch rib
    arch_bridge(f"Bridge{k}", [tuple(p) for p in pl], **BRD)
for ob in [o for o in bpy.data.objects if o.type == 'CURVE']: bpy.data.objects.remove(ob, do_unlink=True)

# =====================================================================
# INTERIOR (full mode): spaces, walls with real door gaps, stairs, lifts, slabs
# =====================================================================
SPACES, DOORS, STAIRS, LIFTS = {}, [], [], []
class Boxes:
    def __init__(s): s.bm = bmesh.new()
    def add(s, c, size, rotz=0.0):
        m = Matrix.Translation(c) @ Matrix.Rotation(rotz, 4, 'Z') @ Matrix.Diagonal((size[0], size[1], size[2], 1))
        bmesh.ops.create_cube(s.bm, size=1.0, matrix=m)
    def flush(s, name, role, m=None):
        global ROLE
        me = bpy.data.meshes.new(name); s.bm.to_mesh(me); s.bm.free(); s.bm = bmesh.new()
        o = bpy.data.objects.new(name, me); scene.collection.objects.link(o)
        old = ROLE; ROLE = role; link(o, m or CLAY); ROLE = old; return o
WALLB, STAIRB, SLABB = Boxes(), Boxes(), Boxes()
DOOR_LEAVES = []

def space(name, probe, z, kind="room"):
    SPACES[name] = {"name": name, "probe": [probe[0], probe[1], z], "z": z, "kind": kind}

def add_door(a, b, c, nrm, w, h, z, kind="door", check_wall=True, leaf=True):
    did = f"D{len(DOORS):02d}_{a}__{b}"
    tng = (-nrm[1], nrm[0])
    DOORS.append({"id": did, "a": a, "b": b, "type": kind, "center": [c[0], c[1], z], "normal": list(nrm), "tangent": list(tng),
                  "w": w, "h": h, "check_wall": check_wall})
    if leaf and kind in ("door", "ext_door"):
        DOOR_LEAVES.append((did, c, nrm, w, h, z))
    return did

def wall_line(p0, p1, z0, z1, t, openings=(), batch=None):
    """openings: list of (s_center, width, zb, h). Emits boxes around real gaps."""
    batch = batch or WALLB
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy); ux, uy = dx/L, dy/L; rot = math.atan2(uy, ux)
    br = {0.0, L}
    for (s, w, zb, h) in openings: br.add(max(0, min(L, s - w/2))); br.add(max(0, min(L, s + w/2)))
    br = sorted(br)
    for sa, sb in zip(br[:-1], br[1:]):
        if sb - sa < 1e-4: continue
        mid = (sa + sb)/2
        holes = sorted([(zb, zb + h) for (s, w, zb, h) in openings if s - w/2 - 1e-6 <= mid <= s + w/2 + 1e-6])
        zc = z0; segs = []
        for (ha, hb) in holes:
            if ha > zc: segs.append((zc, min(ha, z1)))
            zc = max(zc, hb)
        if zc < z1: segs.append((zc, z1))
        for (za, zb_) in segs:
            if zb_ - za < 1e-3: continue
            sa2 = sa - (t/2 if sa == 0.0 else 0.0); sb2 = sb + (t/2 if sb == L else 0.0); m2 = (sa2 + sb2)/2
            cx = p0[0] + ux*m2; cy = p0[1] + uy*m2
            batch.add(Vector((cx, cy, (za + zb_)/2)), (sb2 - sa2, t, zb_ - za), rot)

def arc_wall(c, r, t, z0, z1, a0, a1, openings=(), seg_len=0.8):
    """openings: list of (angle, width, zb, h); v7: elliptical (x scaled by KX) about the courtyard centre"""
    n = max(4, int(abs(a1 - a0)*r*KX/seg_len))
    for i in range(n):
        aa = a0 + (a1 - a0)*i/n; ab = a0 + (a1 - a0)*(i + 1)/n; am = (aa + ab)/2
        pa_, pb_ = EP(r, aa), EP(r, ab); seg_l = math.hypot(pb_[0] - pa_[0], pb_[1] - pa_[1]); pm = EP(r, am)
        holes = sorted([(zb, zb + h) for (ang, w, zb, h) in openings if math.hypot(pm[0] - EP(r, ang)[0], pm[1] - EP(r, ang)[1]) <= w/2])
        zc = z0; segs = []
        for (ha, hb) in holes:
            if ha > zc: segs.append((zc, ha))
            zc = max(zc, hb)
        if zc < z1: segs.append((zc, z1))
        for (za, zb_) in segs:
            WALLB.add(Vector((pm[0], pm[1], (za + zb_)/2)), (seg_l*1.04, t, zb_ - za), EN(am) + math.pi/2)

def stair_module(sid, x0, y0, levels, lower_name, upper_names, flip=False):
    """Dog-leg stair in a shaft whose SW corner is (x0,y0), entry on the south side. Returns slab-hole rects per upper level."""
    W, Ls, EL, LL, FW = ST["shaft_w"], ST["shaft_l"], ST["entry_l"], ST["landing_l"], ST["flight_w"]
    n = ST["riser_n"]; r = None; tread = ST["tread"]; n1 = n//2; n2 = n - n1
    t_in = 0.2
    holes = []
    for li in range(len(levels) - 1):
        za, zb = levels[li], levels[li + 1]; r = (zb - za)/n
        xa = x0 + t_in; xb = x0 + W - t_in       # inner shaft x
        x1a, x1b = (xa, xa + FW) if not flip else (xb - FW, xb)       # flight 1 lane
        x2a, x2b = (xb - FW, xb) if not flip else (xa, xa + FW)       # flight 2 lane
        ys = y0 + EL                                                   # flight start
        steps = []
        for k in range(n1 - 1):                                        # flight 1 treads (going +y)
            top = za + (k + 1)*r; yc = ys + (k + 0.5)*tread
            STAIRB.add(Vector(((x1a + x1b)/2, yc, (za + top)/2)), (x1b - x1a, tread, top - za))
            steps.append([(x1a + x1b)/2, yc, top])
        yl = ys + (n1 - 1)*tread; zl = za + n1*r                        # mid landing
        STAIRB.add(Vector(((xa + xb)/2, yl + LL/2, zl - 0.15)), (xb - xa, LL, 0.3))
        steps.append([(xa + xb)/2, yl + LL/2, zl])
        for k in range(n2 - 1):                                        # flight 2 treads (going -y)
            top = zl + (k + 1)*r; yc = yl - (k + 0.5)*tread
            STAIRB.add(Vector(((x2a + x2b)/2, yc, (zl - 0.3 + top)/2)), (x2b - x2a, tread, top - zl + 0.3))
            steps.append([(x2a + x2b)/2, yc, top])
        # the last riser of flight 2 reaches the upper floor slab at y = ys
        holes.append((min(x2a, x2b) - 0.05, ys - 0.05 + 0.0, max(x2a, x2b) + 0.05, yl + LL + 0.05))
        holes.append((xa, yl - 0.05, xb, yl + LL + 0.05))
        STAIRS.append({"id": f"{sid}_{li}", "a": lower_name if li == 0 else upper_names[li - 1], "b": upper_names[li],
                       "z0": za, "z1": zb, "riser": r, "tread": tread, "steps": steps, "headroom_min": ST["headroom_min"],
                       "entry": [(xa + xb)/2, y0 + 0.6, za], "exit": [(x2a + x2b)/2, y0 + 0.6, zb]})
    # shaft walls (W, E, N) full height; south wall with an opening per floor
    zt = levels[-1] + FH*0.95
    wall_line((x0, y0), (x0, y0 + Ls), levels[0], zt, 0.3)
    wall_line((x0 + W, y0), (x0 + W, y0 + Ls), levels[0], zt, 0.3)
    wall_line((x0, y0 + Ls), (x0 + W, y0 + Ls), levels[0], zt, 0.3)
    wall_line((x0, y0), (x0 + W, y0), levels[0], zt, 0.3, [(W/2, W - 0.4, z, 2.4) for z in levels])
    return holes

def lift_module(lid, x0, y0, levels, names):
    S = P["lifts"]["shaft"]; dw, dh = P["lifts"]["door_w"], P["lifts"]["door_h"]
    zt = levels[-1] + FH*0.95
    wall_line((x0, y0), (x0, y0 + S), levels[0], zt, 0.25)
    wall_line((x0 + S, y0), (x0 + S, y0 + S), levels[0], zt, 0.25)
    wall_line((x0, y0 + S), (x0 + S, y0 + S), levels[0], zt, 0.25)
    wall_line((x0, y0), (x0 + S, y0), levels[0], zt, 0.25, [(S/2, dw, z, dh) for z in levels])
    dids = []
    for z, nm in zip(levels, names):
        dids.append(add_door(nm, lid, (x0 + S/2, y0), (0.0, -1.0), dw, dh, z, kind="lift_door", leaf=False))
    LIFTS.append({"id": lid, "floors": names, "levels": levels, "doors": dids, "shaft": [x0, y0, x0 + S, y0 + S]})
    return (x0, y0, x0 + S, y0 + S)

if FULL:
    WT, WH = DR["wall_t"], FH - POD["slab_t"]
    # ---- outside / entrance sequence ----
    space("forecourt", (ARC["cx"], FRONT_Y - 12.0), 0.0, "outside")
    space("portal_tunnel", (ARC["cx"], (PORTAL_BACK + Y_TUN_END)/2), 0.0, "passage")
    space("courtyard", (CC[0], CC[1]), 0.0, "open")
    space("gallery", (CC[0] - (R_ARC_OUT + R_GAL_OUT)/2*KX, CC[1]), 0.0, "passage")
    add_door("forecourt", "portal_tunnel", (ARC["cx"], FRONT_Y), (0, 1), 2*TUN["hw"], TUN["spring"] + TUN["rise"], 0.0, "open", check_wall=False)
    add_door("portal_tunnel", "courtyard", (ARC["cx"], CC[1] - CR), (0, 1), 2*TUN["hw"], TUN["spring"] + TUN["rise"], 0.0, "open", check_wall=False)
    for sx in (-1, 1):
        add_door("portal_tunnel", "gallery", (sx*(TUN["hw"] + 0.3), sum(TUN_SIDE_OPEN)/2), (sx, 0), TUN_SIDE_OPEN[1] - TUN_SIDE_OPEN[0], 3.0, 0.0, "opening")
    for a in ARCADE_OPEN:
        if abs(math.cos(a)) > 0.97 or abs(math.sin(a)) > 0.97 or True:
            pass
    for a in ARCADE_OPEN[::4]:
        add_door("courtyard", "gallery", EP((CR + R_ARC_OUT)/2, a), (math.cos(EN(a)), math.sin(EN(a))),
                 2*CY["arch_hw"], CY["arch_spring"], 0.0, "opening")
    # ---- gallery outer wall (L0) with doors ----
    ang_W, ang_E = math.pi, 0.0
    ang_T = EPAR(TC[0], TC[1])
    RG = R_GAL_OUT + CY["outer_wall_t"]/2
    lw = DR["link_w"]
    a_tun = math.asin(min(1, (TUN["hw"] + 0.6)/(RG*KX)))
    arc_wall(CC, RG, CY["outer_wall_t"], 0.0, WH, -math.pi/2 + a_tun, 3*math.pi/2 - a_tun,
             [(ang_W, DR["int_w"], 0.0, DR["int_h"]), (ang_E, DR["int_w"], 0.0, DR["int_h"]), (ang_T, DR["int_w"], 0.0, DR["int_h"])])
    for nm, ang in (("W", ang_W), ("E", ang_E), ("T", ang_T)):
        c = EP(RG, ang)
        add_door("gallery", f"{nm}_link", c, (math.cos(EN(ang)), math.sin(EN(ang))), DR["int_w"], DR["int_h"], 0.0)
    # ---- wings ----
    def wing(tag, wd, sgn):
        """Wing with stacked floors on every podium level (section A-A): hall + 2 rooms + core per level,
        stair + lift in the core connect all levels; ground floor adds the gallery link and the street vestibule."""
        hall, rs0, rn0, core = wd["hall"], wd["room_s"], wd["room_n"], wd["core"]
        hx_in = hall[2] if sgn < 0 else hall[0]      # hall wall facing the courtyard
        hx_out = hall[0] if sgn < 0 else hall[2]
        levels = POD["levels"]; LGc = POD.get("loggia")
        sfx = lambda k: "" if k == 0 else f"_L{k}"
        space(f"{tag}_link", ((hx_in + CC[0] + sgn*RG*KX)/2, CC[1]), 0.0, "passage")
        space(f"{tag}_vest", (wd["ext_door_x"], (WALL.y_front(wd["ext_door_x"]) + rs0[1])/2), 0.0, "passage")
        # link corridor gallery -> hall (ground floor)
        xg = CC[0] + sgn*(RG*KX + CY["outer_wall_t"]/2)
        for dy in (-lw/2, lw/2):
            wall_line((xg, CC[1] + dy), (hx_in, CC[1] + dy), 0.0, WH, WT)
        add_door(f"{tag}_link", f"{tag}_hall", (hx_in, CC[1]), (-sgn, 0.0), DR["int_w"], DR["int_h"], 0.0)
        c0, c1 = core[0], core[2]
        dx = (c0 + c1)/2 + (1.5 if sgn < 0 else -1.5)
        for k, lv in enumerate(levels):
            rs, rn = list(rs0), list(rn0)
            if LGc and k == len(levels) - 1:          # top storey sits behind the open loggia: pull the outer rooms in
                sh = LGc["depth"] + 1.0
                if sgn < 0: rs[0] += sh; rn[0] += sh
                else: rs[2] -= sh; rn[2] -= sh
                rs[1] += sh
            z0, z1 = lv, lv + WH
            H_, RS, RN, CO = f"{tag}_hall{sfx(k)}", f"{tag}_room_s{sfx(k)}", f"{tag}_room_n{sfx(k)}", f"{tag}_core{sfx(k)}"
            space(H_, ((hall[0] + hall[2])/2, (hall[1] + hall[3])/2), lv, "corridor")
            space(RS, ((rs[0] + rs[2])/2, (rs[1] + rs[3])/2), lv)
            space(RN, ((rn[0] + rn[2])/2, (rn[1] + rn[3])/2), lv)
            space(CO, ((c0 + c1)/2, core[1] + 0.6), lv, "core")
            hs = max(hall[1], rs[1])
            wall_line((hx_in, hs), (hx_in, hall[3]), z0, z1, WT, [(CC[1] - hs, DR["int_w"], z0, DR["int_h"])] if k == 0 else [])
            ys_door, yn_door = (rs[1] + rs[3])/2, (rn[1] + rn[3])/2
            wall_line((hx_out, hs), (hx_out, hall[3]), z0, z1, WT,
                      [(ys_door - hs, DR["int_w"], z0, DR["int_h"]), (yn_door - hs, DR["int_w"], z0, DR["int_h"])])
            add_door(H_, RS, (hx_out, ys_door), (sgn, 0.0), DR["int_w"], DR["int_h"], lv)
            add_door(H_, RN, (hx_out, yn_door), (sgn, 0.0), DR["int_w"], DR["int_h"], lv)
            xo = rs[0] if sgn < 0 else rs[2]
            wall_line((xo, rs[1]), (xo, rn[3]), z0, z1, WT)
            xs0, xs1 = min(xo, hx_in), max(xo, hx_in)
            ex = wd["ext_door_x"]
            if k == 0:
                wall_line((xs0, rs[1]), (xs1, rs[1]), z0, z1, WT, [(ex - xs0, DR["int_w"], z0, DR["int_h"])])
                add_door(f"{tag}_vest", RS, (ex, rs[1]), (0.0, 1.0), DR["int_w"], DR["int_h"], 0.0)
            else:
                wall_line((xs0, rs[1]), (xs1, rs[1]), z0, z1, WT)
            rx0, rx1 = min(rs[0], rs[2]), max(rs[0], rs[2]); xm = (rx0 + rx1)/2
            wall_line((rx0, rs[3]), (rx1, rs[3]), z0, z1, WT, [(xm - rx0, DR["int_w"], z0, DR["int_h"])])
            add_door(RS, RN, (xm, rs[3]), (0.0, 1.0), DR["int_w"], DR["int_h"], lv)
            wall_line((xs0, rn[3]), (xs1, rn[3]), z0, z1, WT, [(dx - xs0, DR["int_w"], z0, DR["int_h"])])
            nb_space = H_ if (hall[0] <= dx <= hall[2]) else RN
            add_door(nb_space, CO, (dx, rn[3]), (0.0, 1.0), DR["int_w"], DR["int_h"], lv)
            wall_line((c0, core[1]), (c0, core[3]), z0, z1, WT)
            wall_line((c1, core[1]), (c1, core[3]), z0, z1, WT)
            wall_line((c0, core[3]), (c1, core[3]), z0, z1, WT)
        # vestibule from the exterior door
        ex = wd["ext_door_x"]; ysh = WALL.y_front(ex) + POD["wall_t"]
        for dxv in (-lw/2, lw/2):
            wall_line((ex + dxv, ysh - 0.3), (ex + dxv, rs0[1]), 0.0, WH, WT)
        add_door("forecourt", f"{tag}_vest", (ex, WALL.y_front(ex) + POD["wall_t"]/2), (0.0, 1.0), DR["ext_w"], DR["ext_h"] - DR["ext_w"]/2, 0.0, "ext_door")
        # stair + lift in the core, serving every level
        names = [f"{tag}_core{sfx(k)}" for k in range(len(levels))]
        sx0 = c0 + 0.4 if sgn < 0 else c1 - 0.4 - ST["shaft_w"]
        holes = stair_module(f"{tag}_stair", sx0, core[1] + 1.2, levels, names[0], names[1:])
        lx0 = c1 - 0.4 - P["lifts"]["shaft"] if sgn < 0 else c0 + 0.4
        lift = lift_module(f"{tag}_lift", lx0, core[3] - 0.4 - P["lifts"]["shaft"], levels, names)
        return holes + [lift]
    holesW = wing("W", P["wings"]["west"], -1)
    holesE = wing("E", P["wings"]["east"], +1)
    # ---- tower link + lobby + core ----
    p_g = EP(RG + 0.25, ang_T)
    tdir = (TC[0] - p_g[0], TC[1] - p_g[1]); _l = math.hypot(*tdir); tdir = (tdir[0]/_l, tdir[1]/_l); tn = (-tdir[1], tdir[0])
    R_T0 = TW["drums"][0][0] - 0.5 - TW["shell_t"]
    dct = math.hypot(TC[0] - p_g[0], TC[1] - p_g[1])
    p_t = (TC[0] - tdir[0]*(TW["drums"][0][0] - 0.5 - TW["shell_t"]/2), TC[1] - tdir[1]*(TW["drums"][0][0] - 0.5 - TW["shell_t"]/2))
    p_t = (TC[0] + (p_g[0] - TC[0])/dct*(TW["drums"][0][0] - 0.5 - TW["shell_t"]/2), TC[1] + (p_g[1] - TC[1])/dct*(TW["drums"][0][0] - 0.5 - TW["shell_t"]/2))
    space("T_link", ((p_g[0] + p_t[0])/2, (p_g[1] + p_t[1])/2), 0.0, "passage")
    for s_ in (-lw/2, lw/2):
        wall_line((p_g[0] + tn[0]*s_, p_g[1] + tn[1]*s_), (p_t[0] + tn[0]*s_ + tdir[0]*0.6, p_t[1] + tn[1]*s_ + tdir[1]*0.6), 0.0, WH, WT)
    td = (TC[0] - p_t[0], TC[1] - p_t[1]); L_ = math.hypot(*td); td = (td[0]/L_, td[1]/L_)
    did_tower = add_door("T_link", "T_L0", p_t, td, DR["int_w"], DR["int_h"], 0.0)
    ang_door_t = math.atan2(p_t[1] - TC[1], p_t[0] - TC[0])
    boolean(tower_shells[0], [box("c", (2.0, DR["int_w"], DR["int_h"]), (p_t[0], p_t[1], DR["int_h"]/2), rot=ang_door_t)])
    # tower floors
    t_levels = [FH*k for k in range(0, int(TW["floors_top"]/FH) + 1)]
    t_names = [f"T_L{k}" for k in range(len(t_levels))]
    for k, z in enumerate(t_levels):
        space(t_names[k], (TC[0] + (tower_r_at(z) - 4.0)*math.cos(ang_door_t), TC[1] + (tower_r_at(z) - 4.0)*math.sin(ang_door_t)), z, "floor" if k else "lobby")
    # core: lift bank (centre) + 2 stairs (west/east)
    LS = P["lifts"]["shaft"]; nl = TW["core"]["lifts"]
    bank_w = nl*LS + (nl - 1)*0.3
    by = TC[1] - LS/2 + 0.5
    core_holes = []
    for i in range(nl):
        lx = TC[0] - bank_w/2 + i*(LS + 0.3)
        core_holes.append(lift_module(f"T_lift{i}", lx, by, t_levels, t_names))
    sy0 = TC[1] - ST["shaft_l"]/2 + 1.0
    core_holes += stair_module("T_stairA", TC[0] - bank_w/2 - 0.6 - ST["shaft_w"], sy0, t_levels, "T_L0", t_names[1:])
    core_holes += stair_module("T_stairB", TC[0] + bank_w/2 + 0.6, sy0, t_levels, "T_L0", t_names[1:], flip=True)
    # ---- slabs ----
    ROLE = "slab"
    st = POD["slab_t"]
    def rect_cut(h, z): return box("c", (h[2] - h[0], h[3] - h[1], 1.0), ((h[0] + h[2])/2, (h[1] + h[3])/2, z))
    def rects_cutter(rects, z):
        bx = Boxes()
        for h in rects: bx.add(Vector(((h[0] + h[2])/2, (h[1] + h[3])/2, z)), (h[2] - h[0], h[3] - h[1], 1.0))
        return bx.flush("cut_rects", "cut")
    for k, z in enumerate(t_levels[1:], start=1):
        sl = cyl(f"TowerSlab{k}", tower_r_at(z) - 0.5 - TW["shell_t"] + 0.05, z - st, z, (TC[0], TC[1], 0), 96)
        boolean(sl, [rects_cutter(core_holes, z - st/2)])
    for k, z in enumerate(POD["levels"][1:], start=1):
        sl = WALL.loft(f"PodiumSlab{k}", [(-POD["wall_t"] + 0.02, z - st), (-POD["wall_t"] + 0.02, z)])
        cuts = [ecut(CR + 0.02, z - 2, z + 2, 128), cyl_cut(TW["drums"][0][0] - 0.2, TC, z - 2, z + 2)]
        if z < TUN["spring"] + TUN["rise"] + 0.6:
            cuts.append(box("c", (2*TUN["hw"] + 1.2, Y_TUN_END - FRONT_Y + 4, 3.0), (ARC["cx"], (FRONT_Y + Y_TUN_END)/2, z)))
        if z < ARC["spring"] + ARC["rise"] + 1.0:
            cuts.append(box("c", (2*ARC["hw"] + 1.2, ARC["portal_depth"] + 4.0, 3.0), (ARC["cx"], FRONT_Y + ARC["portal_depth"]/2 - 1.0, z)))
        cuts.append(rects_cutter(holesW + holesE, z - st/2))
        boolean(sl, cuts)
    ROLE = "shell"
    WALLB.flush("InteriorWalls", "wall")
    STAIRB.flush("Stairs", "stair")
    # door leaves (auto doors)
    ROLE = "door_leaf"
    for (did, c, nrm, w, h, z) in DOOR_LEAVES:
        o = box(f"DoorLeaf_{did}", (DR["leaf_t"], w - 0.06, h - 0.05), (c[0], c[1], z + (h - 0.05)/2 + 0.02), rot=math.atan2(nrm[1], nrm[0]))
        o["door_id"] = did; o["slide"] = [-nrm[1]*w, nrm[0]*w, 0.0]
    ROLE = "shell"
    # ---- glowing plaza rings (forecourt + courtyard) ----
    ROLE = "plaza_glow"
    ring("PlazaRingCourt", CR*0.45, CR*0.52, 0.0, 0.04, (CC[0], CC[1], 0), 128, sx=KX)
    ring("PlazaRingFore", 9.0, 10.0, 0.0, 0.04, (ARC["cx"], FRONT_Y - 14.0, 0), 128)
    ROLE = "shell"
    # spaces / graph export
    json.dump({"spaces": SPACES, "doors": DOORS, "stairs": STAIRS, "lifts": LIFTS,
               "entrance": "forecourt", "params": os.environ.get("PARAMS", "params.json")},
              open(os.path.join(OUT, "spaces.json"), "w"), indent=1)

# ---------------- clean meshes ----------------
for o in list(COL.objects):
    if o.type != 'MESH' or o.get("inst"): continue
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bm.to_mesh(o.data); bm.free()

print("BUILD OK", MODE, "objects:", len(COL.objects), "instances:", N_INST[0], "doors:", len(DOORS), "stairs:", len(STAIRS))

# =====================================================================
# SAVE / EXPORT (full)  |  SILHOUETTES (sil)
# =====================================================================
if FULL:
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "building.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "building.glb"), export_format='GLB', export_extras=True, export_apply=True)
if MODE == "sil" or os.environ.get("SIL", "0") == "1":
    exec(open(os.path.join(HERE, "src", "render_sil.py")).read())
