# geometry helper library (exec'd inside Blender by build.py; expects bpy, bmesh, math, Vector, Matrix, scene, COL)
def mat(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m
CLAY = mat("Clay_White", (0.76, 0.76, 0.75))
GLAZE = mat("Clay_Recess", (0.6, 0.61, 0.63), 0.6)   # darker clay for recessed glazing/voids
DARK = mat("Clay_Shadow", (0.40, 0.40, 0.42), 0.9)

ROLE = "shell"
def link(ob, m=CLAY):
    for c in ob.users_collection: c.objects.unlink(ob)
    COL.objects.link(ob)
    ob["role"] = "glass" if m is GLAZE else ROLE
    ob.data.materials.clear(); ob.data.materials.append(m)
    return ob

def smooth(ob, angle=35):
    for p in ob.data.polygons: p.use_smooth = True
    try:
        ob.modifiers.new("ss", "SMOOTH_BY_ANGLE")
    except Exception:
        pass
    return ob

def mesh_from(name, verts, faces, m=CLAY):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    return link(ob, m)

# ---------------- primitives ----------------
def lathe(name, prof, seg=96, c=(0, 0, 0), sx=1.0, sy=1.0, m=CLAY, a0=0.0, a1=2*math.pi, closed=True, sm=True):
    """Revolve profile [(r,z)] about Z. r==0 points become poles."""
    c = tuple(c) + (0,)*(3-len(c))
    verts, faces = [], []
    full = closed and abs(a1 - a0 - 2*math.pi) < 1e-6
    n = seg if full else seg + 1
    idx = []
    for (r, z) in prof:
        row = []
        if r < 1e-6:
            verts.append((c[0], c[1], c[2] + z)); row = [len(verts) - 1] * n
        else:
            for i in range(n):
                a = a0 + (a1 - a0) * i / seg
                verts.append((c[0] + r*math.cos(a)*sx, c[1] + r*math.sin(a)*sy, c[2] + z)); row.append(len(verts) - 1)
        idx.append(row)
    for j in range(len(prof) - 1):
        A, B = idx[j], idx[j+1]
        rng = n if full else n - 1
        for i in range(rng):
            i2 = (i + 1) % n
            f = [A[i], A[i2], B[i2], B[i]]
            f2 = []
            for v in f:
                if v not in f2: f2.append(v)
            if len(f2) >= 3: faces.append(f2)
    ob = mesh_from(name, verts, faces, m)
    if sm: smooth(ob)
    return ob

def cyl(name, r, z0, z1, c=(0, 0, 0), seg=96, m=CLAY, sx=1, sy=1):
    return lathe(name, [(0, z0), (r, z0), (r, z1), (0, z1)], seg, c, sx, sy, m)

def ring(name, r_in, r_out, z0, z1, c=(0, 0, 0), seg=96, m=CLAY, sx=1, sy=1):
    return lathe(name, [(r_in, z0), (r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)], seg, c, sx, sy, m)

def box(name, size, loc, rot=0.0, m=CLAY):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object; ob.name = name
    ob.scale = size; ob.rotation_euler[2] = rot
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return link(ob, m)

def saucer(name, R, z, c=(0, 0), t=1.6, sx=1.0, sy=1.0, under=0.9, seg=128):
    """Thin lens-shaped canopy with crisp rim. Center (c) at height z."""
    prof = [(0, t*0.55), (R*0.35, t*0.5), (R*0.75, t*0.25), (R*0.98, 0.08), (R, 0.0),
            (R*0.98, -0.12), (R*0.7, -t*under*0.45), (R*0.3, -t*under*0.8), (0, -t*under)]
    return lathe(name, prof, seg, (c[0], c[1], z), sx, sy)


def rrect_prism(name, w, d, z0, z1, rad, seg=12, m=CLAY):
    """Rounded-rectangle prism (crisp top/bottom edges, rounded vertical corners)."""
    pts = []
    for cx, cy, a0 in ((w/2-rad, d/2-rad, 0), (-w/2+rad, d/2-rad, 90), (-w/2+rad, -d/2+rad, 180), (w/2-rad, -d/2+rad, 270)):
        for k in range(seg+1):
            a = math.radians(a0 + 90*k/seg); pts.append((cx + rad*math.cos(a), cy + rad*math.sin(a)))
    n = len(pts)
    verts = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
    faces = [list(range(n))[::-1], list(range(n, 2*n))] + [[i, (i+1) % n, n + (i+1) % n, n + i] for i in range(n)]
    return mesh_from(name, verts, faces, m)

def apply_mods(ob):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    for md in list(ob.modifiers):
        if md.type == 'SMOOTH_BY_ANGLE':
            continue
        bpy.ops.object.modifier_apply(modifier=md.name)

def boolean(target, cutters, op='DIFFERENCE', keep=False):
    for ct in cutters:
        md = target.modifiers.new("b", 'BOOLEAN'); md.operation = op; md.object = ct; md.solver = 'EXACT'; md.use_self = True; md.use_hole_tolerant = True
        apply_mods(target)
        if not keep: bpy.data.objects.remove(ct, do_unlink=True)

def curve_obj(name, pts, bevel_obj=None, depth=0.0, radii=None, res=24, m=CLAY):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.resolution_u = res
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
        if radii: sp.points[i].radius = radii[i]
    sp.use_endpoint_u = True; sp.order_u = min(4, len(pts))
    if bevel_obj:
        cu.bevel_mode = 'OBJECT'; cu.bevel_object = bevel_obj
    else:
        cu.bevel_depth = depth; cu.bevel_resolution = 6
    cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu); scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.active_object
    return link(ob, m)

def profile_rect(name, w, h):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'
    sp = cu.splines.new('POLY'); sp.points.add(7)
    # deck with small upstand parapets (U-section)
    P = [(-w/2, 0), (w/2, 0), (w/2, h+0.9), (w/2-0.25, h+0.9), (w/2-0.25, h), (-w/2+0.25, h), (-w/2+0.25, h+0.9), (-w/2, h+0.9)]
    for i, p in enumerate(P): sp.points[i].co = (p[0], p[1] - h/2, 0, 1)
    sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu); scene.collection.objects.link(ob)
    return ob

def fins_around(name, c, r, z0, z1, n, w=0.45, d=1.2, a_skip=None, m=CLAY):
    """Vertical mullion fins around a drum -> reads as dense recessed window bays."""
    bm = bmesh.new()
    for i in range(n):
        a = 2*math.pi*i/n
        if a_skip and any(abs(((a - s + math.pi) % (2*math.pi)) - math.pi) < hw for s, hw in a_skip):
            continue
        mtx = Matrix.Translation((c[0] + (r + d/2)*math.cos(a), c[1] + (r + d/2)*math.sin(a), (z0 + z1)/2)) @ Matrix.Rotation(a, 4, 'Z')
        bmesh.ops.create_cube(bm, size=1.0, matrix=mtx @ Matrix.Diagonal((d, w, z1 - z0, 1)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    return link(ob, m)

def floor_bands(name, c, r_in, r_out, zs, t=0.45, sx=1, sy=1):
    obs = [ring(f"{name}_{i}", r_in, r_out, z - t/2, z + t/2, c, 96, CLAY, sx, sy) for i, z in enumerate(zs)]
    return obs

def stem(name, c, z0, z1, r0, r1):
    return lathe(name, [(0, z0), (r0, z0), (r0*0.8 + r1*0.2, z0 + (z1 - z0)*0.5), (r1, z1), (0, z1)], 48, (c[0], c[1], 0))


def arch_poly(hw, spring, rise, seg=16):
    P = [(-hw, 0.0), (hw, 0.0), (hw, spring)]
    for k in range(1, seg):
        a = math.pi*k/seg; P.append((hw*math.cos(a), spring + rise*math.sin(a)))
    P.append((-hw, spring)); return P
def arch_prisms(name, items, m=CLAY):
    """items: (x, y, z0, angle_of_outward_normal, hw, spring, rise, depth)"""
    verts, faces = [], []
    for (x, y, z0, ang, hw, sp, rise, depth) in items:
        P = arch_poly(hw, sp, rise); n = len(P); b = len(verts)
        nx, ny = math.cos(ang), math.sin(ang); tx, ty = -ny, nx
        for dd in (-depth/2, depth/2):
            for (u, v) in P:
                verts.append((x + tx*u + nx*dd, y + ty*u + ny*dd, z0 + v))
        faces.append([b + k for k in range(n)]); faces.append([b + n + k for k in range(n)][::-1])
        for k in range(n):
            k2 = (k + 1) % n; faces.append([b + k, b + n + k, b + n + k2, b + k2])
    return mesh_from(name, verts, faces, m)

def rounded_band(name, c, r, z, h=0.9, out=0.9, seg=96):
    p = [(r - 1.2, z - h/2), (r + out*0.4, z - h/2), (r + out*0.85, z - h*0.3), (r + out, z), (r + out*0.85, z + h*0.3), (r + out*0.4, z + h/2), (r - 1.2, z + h/2), (r - 1.2, z - h/2)]
    return lathe(name, p, seg, c)

def canopy(name, R, z, c, t=None, sx=1.0, sy=1.0, fins=0, r_drum=3.0, upturn=True, lip_k=0.32, fin_c=None, ribs=False):
    """Thin tapered canopy: thick centre, thin up-turned edge; optional down-curving support fins."""
    if t is None: t = min(1.9, 0.055*R + 0.55)
    lip = lip_k*t if upturn else 0.05
    # v6 lens: tapered top, rounded fascia nose of thickness e at the rim, shallow concave underside
    e = max(0.32, 0.2*t); zc = lip - e/2 + 0.04
    nose = [(R - e/2 + e/2*math.cos(math.radians(a)), zc + e/2*math.sin(math.radians(a))) for a in (90, 50, 20, 0, -20, -50, -90)]
    prof = [(0, 0.55*t), (0.3*R, 0.45*t), (0.65*R, 0.22*t), (0.86*R, max(0.12*t, zc + e/2 + 0.02))] + nose + \
           [(0.93*R, min(-0.04*t, zc - e/2 - 0.02)), (0.7*R, -0.18*t), (0.4*R, -0.42*t), (0, -0.65*t)]
    ob = lathe(name, prof, 128, (c[0], c[1], z), sx, sy)
    if ribs and R > 5.5 and 0.9*R > r_drum + 1.7:   # underside radial ribs (soffit), from the drum to near the fascia
        under = [(0.93*R, min(-0.04*t, zc - e/2 - 0.02)), (0.7*R, -0.18*t), (0.4*R, -0.42*t), (0, -0.65*t)][::-1]
        def uz(r):
            for (r0, z0), (r1, z1) in zip(under, under[1:]):
                if r0 <= r <= r1: return z0 + (z1 - z0)*(r - r0)/(r1 - r0)
            return under[-1][1]
        ra, rb = r_drum + 0.2, 0.9*R; K = 6
        top = [(ra + (rb - ra)*i/K, z + uz(ra + (rb - ra)*i/K) + 0.15) for i in range(K + 1)]
        bot = [(r_, zz - 0.15 - 0.75*max(0.0, 1 - (r_ - ra)/(rb - ra))**1.5 - 0.12) for (r_, zz) in top]
        rib_plates(name + "_ribs", c, top + bot[::-1], max(8, int(2*math.pi*R/4.5)), 0.28, 0.13, sx, sy)
    if fins:
        bm = bmesh.new()
        for k in range(fins):
            a = 2*math.pi*k/fins + 0.3
            r1 = (0.62*R*min(sx, sy)) if fin_c is None else fin_c; zt = z - 0.18*t
            pts2 = []
            N = 8
            for q in range(N + 1):   # curved lower edge
                u = q/N; rr = r_drum + (r1 - r_drum)*u
                pts2.append((rr, z - 0.3*t - (1 - u)**1.6*0.32*(r1 - r_drum)))
            poly = pts2 + [(r1, zt), (r_drum, zt)]
            vs = []
            for side in (-0.22, 0.22):
                for (rr, zz) in poly:
                    vs.append(bm.verts.new((c[0] + rr*math.cos(a) - side*math.sin(a), c[1] + rr*math.sin(a) + side*math.cos(a), zz)))
            n = len(poly)
            bm.faces.new(vs[:n]); bm.faces.new(vs[n:][::-1])
            for q in range(n):
                q2 = (q + 1) % n; bm.faces.new([vs[q], vs[q2], vs[n + q2], vs[n + q]])
        me = bpy.data.meshes.new(name + "_fins"); bm.normal_update(); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name + "_fins", me); scene.collection.objects.link(o); link(o)
    return ob

def drum(name, c, r, z0, z1, band=4.2, arched=True, nfin=None):
    """v6 drum: solid clay core, thick rounded floor bands, pilasters, and per storey a ring of
    instanced arched windows between the pilasters (full build only; silhouettes ignore them)."""
    cyl(name + "_core", r - 0.7, z0 - 0.3, z1, (c[0], c[1], 0), 96, CLAY)
    nb = max(1, int(round((z1 - z0)/band)))
    zs = [z0 + (z1 - z0)*k/nb for k in range(nb + 1)]
    for k, z in enumerate(zs):
        rounded_band(f"{name}_band{k}", (c[0], c[1], 0), r, z, 1.0 if 0 < k < nb else 1.25, 0.8)
    DW = P.get("detail", {}).get("drum_windows", {})
    npil = nfin or max(6, int(2*math.pi*r/DW.get("bay", 5.2)))
    fins_around(name + "_pil", c, r - 0.75, z0, z1, npil, w=0.75, d=0.6, a_skip=None)
    if FULL and arched:
        rc = r - 0.7; per = max(1, int(round(2*math.pi*rc/npil/DW.get("pitch", 2.7))))
        for k in range(nb):
            h = zs[k + 1] - zs[k]; sill = 0.75; rise = min(DW.get("hw", 0.7), 0.9)
            sp = max(0.8, h - sill - rise - 0.75)
            wt = window_type(f"dw_{int(sp*10)}", DW.get("hw", 0.7), sp, rise)
            for j in range(npil):
                for q in range(per):
                    a = 2*math.pi*(j + (q + 0.5)/per)/npil
                    window_at(wt, c[0] + rc*math.cos(a), c[1] + rc*math.sin(a), zs[k] + sill, a, DW.get("lit", 0.45), name)
    return zs

def turret(name, c, r, z0, z1, cap_R=None, dome=True, fins=0):
    drum(name, c, r, z0, z1, band=3.6)
    cR = cap_R or r*1.9
    canopy(name + "_cap", cR, z1 + 0.5, c, fins=fins, r_drum=r)
    if dome:
        lathe(name + "_dome", [(r*0.75, 0), (r*0.7, r*0.25), (r*0.5, r*0.5), (r*0.25, r*0.65), (0, r*0.7)], 48, (c[0], c[1], z1 + 0.9))

def sweep(name, pts, wfun, hfun, samples=160, m=CLAY, prof_n=16):
    """Sweep a rounded-rectangle section (half-width wfun(t) sideways, half-height hfun(t) up) along Catmull-Rom path."""
    P = [Vector(p) for p in pts]
    def cr(t):
        n = len(P) - 1; f = t*n; i = min(int(f), n - 1); u = f - i
        p0 = P[max(i - 1, 0)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(i + 2, n)]
        return 0.5*((2*p1) + (-p0 + p2)*u + (2*p0 - 5*p1 + 4*p2 - p3)*u*u + (-p0 + 3*p1 - 3*p2 + p3)*u**3)
    C = [cr(k/samples) for k in range(samples + 1)]
    sec = []
    for k in range(prof_n):  # superellipse section
        a = 2*math.pi*k/prof_n; ca, sa = math.cos(a), math.sin(a)
        sec.append((math.copysign(abs(ca)**0.45, ca), math.copysign(abs(sa)**0.45, sa)))
    verts, faces = [], []
    for k, p in enumerate(C):
        T = (C[min(k + 1, samples)] - C[max(k - 1, 0)]).normalized()
        S = T.cross(Vector((0, 0, 1)))
        if S.length < 1e-3: S = Vector((1, 0, 0))
        S.normalize(); U = S.cross(T).normalized()
        t = k/samples; w, h = wfun(t), hfun(t)
        for (a, b) in sec: verts.append(tuple(p + S*(a*w) + U*(b*h)))
    for k in range(samples):
        for j in range(prof_n):
            a = k*prof_n + j; b = k*prof_n + (j + 1) % prof_n
            faces.append([a, b, b + prof_n, a + prof_n])
    faces.append(list(range(prof_n))[::-1]); faces.append([samples*prof_n + j for j in range(prof_n)])
    ob = mesh_from(name, verts, faces, m); smooth(ob); return ob

