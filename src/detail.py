# v6 architectural detail helpers (exec'd by build.py after geom.py)
#  - instanced window surrounds/panes: one shared mesh per window type, placed as linked duplicates
#    (exported as shared glTF meshes -> gltf-transform turns them into EXT_mesh_gpu_instancing)
#  - sector slabs (balconies), solid rib plates, arch-soffit bridges
import random
DT_ = P.get("detail", {})
RNG = random.Random(DT_.get("seed", 7))
INST = {}
N_INST = [0]

def _arch_pts(hw, sp, rise, seg=10, z0=0.0):
    pts = [(-hw, z0), (hw, z0), (hw, sp)]
    for k in range(1, seg):
        a = math.pi*k/seg; pts.append((hw*math.cos(a), sp + rise*math.sin(a)))
    pts.append((-hw, sp)); return pts

def _shared(name, V, F, m, smooth_=False):
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.materials.append(m)
    for p in me.polygons: p.use_smooth = smooth_
    return me

def window_type(key, hw, sp, rise, frame=0.2, depth=0.26):
    """(frame_mesh, dark_pane_mesh, lit_pane_mesh). Local axes: x tangent, +y outward, z up; origin = sill centre on wall face."""
    if key in INST: return INST[key]
    inner = _arch_pts(hw, sp, rise); outer = _arch_pts(hw + frame, sp, rise + frame, z0=-frame)
    n = len(inner); V, F = [], []
    for y in (0.0, depth):
        V += [(u, y, v) for (u, v) in outer] + [(u, y, v) for (u, v) in inner]
    o = lambda L, i: L*2*n + i % n
    q = lambda L, i: L*2*n + n + i % n
    for i in range(n):
        F.append([o(1, i), o(1, i + 1), q(1, i + 1), q(1, i)])      # front
        F.append([o(0, i), q(0, i), q(0, i + 1), o(0, i + 1)])      # back (against the wall)
        F.append([o(0, i), o(0, i + 1), o(1, i + 1), o(1, i)])      # outer side
        F.append([q(0, i), q(1, i), q(1, i + 1), q(0, i + 1)])      # reveal
    b = len(V); sw = hw + frame + 0.12; z0, z1 = -frame - 0.16, -frame
    V += [(-sw, 0, z0), (sw, 0, z0), (sw, depth + 0.14, z0), (-sw, depth + 0.14, z0), (-sw, 0, z1), (sw, 0, z1), (sw, depth + 0.14, z1), (-sw, depth + 0.14, z1)]
    F += [[b, b + 3, b + 2, b + 1], [b + 4, b + 5, b + 6, b + 7], [b, b + 1, b + 5, b + 4], [b + 1, b + 2, b + 6, b + 5], [b + 2, b + 3, b + 7, b + 6], [b + 3, b, b + 4, b + 7]]
    fr = _shared(key + "_frame", V, F, CLAY)
    pv = [(u, 0.04, v) for (u, v) in inner]
    dark = _shared(key + "_pane", pv, [list(range(n))], GLAZE)
    lit = _shared(key + "_lit", pv, [list(range(n))], GLAZE)
    INST[key] = (fr, dark, lit); return INST[key]

def _place(me, name, loc, rz, role):
    ob = bpy.data.objects.new(name, me); COL.objects.link(ob)
    ob.location = loc; ob.rotation_euler = (0.0, 0.0, rz); ob["role"] = role; ob["inst"] = 1
    N_INST[0] += 1; return ob

def window_at(wt, x, y, z, ang, lit_p=0.4, tag="W"):
    fr, dark, lit = wt
    rz = ang - math.pi/2
    _place(fr, f"{tag}_f", (x, y, z), rz, "facade")
    if RNG.random() < lit_p: _place(lit, f"{tag}_l", (x, y, z), rz, "window_light")
    else: _place(dark, f"{tag}_g", (x, y, z), rz, "glass")

def ring_windows(tag, c, r, z, wt, n, phase=0.0, skip=(), lit_p=0.4, keep=None):
    for j in range(n):
        a = phase + 2*math.pi*(j + 0.5)/n
        if any(abs(((a - s + math.pi) % (2*math.pi)) - math.pi) < hw for s, hw in skip): continue
        if keep and not keep(c[0] + r*math.cos(a), c[1] + r*math.sin(a), z): continue
        window_at(wt, c[0] + r*math.cos(a), c[1] + r*math.sin(a), z, a, lit_p, tag)

def sector_bm(bm, c, r0, r1, a0, a1, z0, z1, seg=10):
    rows = []
    for i in range(seg + 1):
        a = a0 + (a1 - a0)*i/seg; ca, sa = math.cos(a), math.sin(a)
        rows.append([bm.verts.new((c[0] + r*ca, c[1] + r*sa, z)) for (r, z) in ((r0, z0), (r1, z0), (r1, z1), (r0, z1))])
    for i in range(seg):
        A, B = rows[i], rows[i + 1]
        for k in range(4):
            k2 = (k + 1) % 4; bm.faces.new((A[k], B[k], B[k2], A[k2]))
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])

def bm_object(name, bm, m=None):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return link(ob, m or CLAY)

def balconies(name, c, r_wall, floors, depth, span, per_floor, rail_h=1.05):
    """cantilevered sector balconies with solid parapets, rotating around the drum floor by floor"""
    bm = bmesh.new()
    for k, z in enumerate(floors):
        for j in range(per_floor):
            a0 = 2*math.pi*j/per_floor + k*0.9 + RNG.uniform(-0.15, 0.15)
            sector_bm(bm, c, r_wall - 0.3, r_wall + depth, a0, a0 + span, z - 0.35, z, 10)
            sector_bm(bm, c, r_wall + depth - 0.18, r_wall + depth, a0, a0 + span, z, z + rail_h, 10)
    return bm_object(name, bm)

def rib_plates(name, c, rz_pts, n, t=0.32, phase=0.0, sx=1.0, sy=1.0):
    """n solid radial plates; rz_pts = closed polygon [(r, z)] in the radial plane"""
    bm = bmesh.new(); m = len(rz_pts)
    for k in range(n):
        a = phase + 2*math.pi*k/n; ca, sa = math.cos(a), math.sin(a)
        vs = []
        for side in (-t/2, t/2):
            for (r, z) in rz_pts:
                vs.append(bm.verts.new((c[0] + (r*ca)*sx - side*sa, c[1] + (r*sa)*sy + side*ca, z)))
        bm.faces.new(vs[:m]); bm.faces.new(vs[m:][::-1])
        for i in range(m):
            i2 = (i + 1) % m; bm.faces.new((vs[i], vs[i2], vs[m + i2], vs[m + i]))
    return bm_object(name, bm)

def _cr_path(pts, samples):
    Pp = [Vector(p) for p in pts]
    def cr(t):
        n = len(Pp) - 1; f = t*n; i = min(int(f), n - 1); u = f - i
        p0 = Pp[max(i - 1, 0)]; p1 = Pp[i]; p2 = Pp[i + 1]; p3 = Pp[min(i + 2, n)]
        return 0.5*((2*p1) + (-p0 + p2)*u + (2*p0 - 5*p1 + 4*p2 - p3)*u*u + (-p0 + 3*p1 - 3*p2 + p3)*u**3)
    C = [cr(k/samples) for k in range(samples + 1)]
    fr = []
    for k, p in enumerate(C):
        T = (C[min(k + 1, samples)] - C[max(k - 1, 0)]); T.z = 0; T.normalize(); fr.append((p, Vector((T.y, -T.x, 0.0))))
    return fr

def _loft(name, frames, sec_fun):
    verts, faces = [], []; NS = None
    for k, (p, S) in enumerate(frames):
        sec = sec_fun(k/(len(frames) - 1)); NS = len(sec)
        for (s_, z) in sec: verts.append(tuple(p + S*s_ + Vector((0, 0, z))))
    n = len(frames)
    for k in range(n - 1):
        for j in range(NS):
            a = k*NS + j; b = k*NS + (j + 1) % NS; faces.append([a, b, b + NS, a + NS])
    faces.append(list(range(NS))[::-1]); faces.append([(n - 1)*NS + j for j in range(NS)])
    return mesh_from(name, verts, faces)

def arch_bridge(name, pts, w=3.0, deck_t=0.7, rail_h=1.1, post_pitch=1.6, rib=0.38, rib_drop=2.6, samples=64):
    """v6 slender bridge: thin deck slab, open railing (posts + handrail + mid-rail), and a thin
    under-slung arch rib with slender hangers that springs from the supporting drums at both ends."""
    fr = _cr_path(pts, samples)
    _loft(name, fr, lambda t: [(-w/2, -deck_t), (w/2, -deck_t), (w/2, 0.0), (-w/2, 0.0)])
    rz = lambda t: -deck_t - rib_drop*(1 - math.sin(math.pi*t))**1.6 - 0.05
    _loft(name + "_rib", fr, lambda t: [(-rib/2, rz(t) - rib), (rib/2, rz(t) - rib), (rib/2, rz(t)), (-rib/2, rz(t))])
    for sd in (-1, 1):
        for zr, hh in ((rail_h - 0.06, 0.07), (rail_h*0.5, 0.04)):
            _loft(f"{name}_rail{sd}_{int(zr*10)}", fr, lambda t, sd=sd, zr=zr, hh=hh: [(sd*(w/2 - 0.08) - hh, zr - hh), (sd*(w/2 - 0.08) + hh, zr - hh), (sd*(w/2 - 0.08) + hh, zr + hh), (sd*(w/2 - 0.08) - hh, zr + hh)])
    L = sum((fr[k + 1][0] - fr[k][0]).length for k in range(len(fr) - 1))
    npost = max(2, int(L/post_pitch)); bm = bmesh.new()
    for q in range(npost + 1):
        k = round(q*samples/npost); p, S = fr[k]; t = k/samples
        for sd in (-1, 1):
            c = p + S*(sd*(w/2 - 0.08))
            m = Matrix.Translation((c.x, c.y, c.z + rail_h/2)) @ Matrix.Diagonal((0.07, 0.07, rail_h, 1))
            bmesh.ops.create_cube(bm, size=1.0, matrix=m)
        if q % 2 == 0 and 0 < q < npost:   # hanger from the deck to the rib
            h = -rz(t) - deck_t
            if h > 0.15:
                m = Matrix.Translation((p.x, p.y, p.z - deck_t - h/2)) @ Matrix.Diagonal((0.12, 0.12, h + 0.05, 1))
                bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    return bm_object(name + "_posts", bm)
