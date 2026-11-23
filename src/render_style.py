# v14 stylised "abstract" Cycles render of building.blend (style of the abstract concept image): deep blue-violet / indigo
# palette, dark glossy saucers with iridescent pink/cyan/white rims, stacked glossy tower rings with tiny warm/teal window
# lights, pale glowing crescent ribbon, dark podium with a deck-edge light strip, warm-white starburst through the arch,
# pastel plaza rings, volumetric haze + god rays, compositor bloom/streaks. Abstract backdrop only (no city, no people).
# Every material is assigned by rules in params.json -> style.rules ([by "name" regex | "role", pattern, material]).
#   blender -b building.blend -P src/render_style.py      env: VIEWS (front,aerial,courtyard) SAMPLES RES OUTDIR
# Writes <OUTDIR>/style_<view>_raw.png ; src/style_post.py adds grain / chromatic softness / vignette -> style_<view>.png
import bpy, bmesh, math, os, re, random, json
from mathutils import Vector
scene = bpy.context.scene
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(HERE, "params.json"))); ST = P["style"]; CY = ST["cycles"]; PAL = {k: tuple(v) for k, v in ST["palette"].items()}
OUT = os.environ.get("OUTDIR", os.path.join(HERE, "renders")); os.makedirs(OUT, exist_ok=True)
VIEWS = os.environ.get("VIEWS", "front,aerial,courtyard").split(",")
SAMPLES = int(os.environ.get("SAMPLES", CY["samples"])); RES = os.environ.get("RES")
random.seed(14)
FRONT_Y = -P["podium"]["wall_half_d"] + P["podium"]["wall_cy"]
TX, TY, TZ = P["tower"]["cx"], P["tower"]["cy"], P["tower"]["crown_z"]
CC = (P["courtyard"]["cx"], P["courtyard"]["cy"])

def nodes(m): m.use_nodes = True; return m.node_tree.nodes, m.node_tree.links
def principled(name, base, metal=0.0, rough=0.3, coat=0.0, film=0.0, emis=None, estr=0.0):
    m = bpy.data.materials.new(name); N, L = nodes(m); b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Metallic"].default_value = metal; b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    if film and "Thin Film Thickness" in b.inputs: b.inputs["Thin Film Thickness"].default_value = film; b.inputs["Thin Film IOR"].default_value = 1.45
    if emis: b.inputs["Emission Color"].default_value = (*emis, 1); b.inputs["Emission Strength"].default_value = estr
    return m
def ramp_node(N, stops, interp='LINEAR'):
    r = N.new("ShaderNodeValToRGB"); el = r.color_ramp.elements; r.color_ramp.interpolation = interp
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1); el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
    for p, c in stops[1:-1]: e = el.new(p); e.color = (*c, 1)
    return r
def emit(name, col, s):
    m = bpy.data.materials.new(name); N, L = nodes(m); N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = s
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"]); return m
def fresnel_iri(m, k=0.7, blend=0.25, coord="Generated", axis="X", stops=None):
    """add a grazing-angle iridescent emission (pink -> white -> cyan along an axis) to a Principled material"""
    N, L = nodes(m); b = N["Principled BSDF"]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = blend
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 3.0; L.new(lw.outputs["Facing"], pw.inputs[0])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = k; L.new(pw.outputs[0], sc.inputs[0])
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs[coord], sp.inputs[0])
    r = ramp_node(N, stops or [(0.0, PAL["pink"]), (0.5, PAL["white"]), (1.0, PAL["cyan"])])
    L.new(sp.outputs[axis], r.inputs["Fac"]); L.new(r.outputs["Color"], b.inputs["Emission Color"]); L.new(sc.outputs[0], b.inputs["Emission Strength"])
    return m

# ---------------- material library ----------------
MAT = {}
MAT["shell"] = fresnel_iri(principled("St_Shell", PAL["indigo"], 0.8, 0.22, 0.8, 380), 0.55)
MAT["facade"] = fresnel_iri(principled("St_Facade", (0.05, 0.05, 0.12), 0.7, 0.3, 0.5, 300), 0.3)
MAT["podium"] = principled("St_Podium", PAL["navy"], 0.5, 0.35, 0.4)
MAT["ground"] = principled("St_Ground", (0.008, 0.009, 0.02), 0.2, 0.1, 1.0)
def saucer_mat():
    """dark glossy/metallic underside; top surface catches bright iridescent pink/cyan/white light"""
    m = principled("St_Saucer", (0.03, 0.03, 0.07), 0.9, 0.15, 1.0, 420); N, L = nodes(m); b = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], sp.inputs[0])
    top = N.new("ShaderNodeMapRange"); top.inputs["From Min"].default_value = 0.2; top.inputs["From Max"].default_value = 0.9
    top.inputs["To Max"].default_value = CY["saucer_top_glow"]; L.new(sp.outputs["Z"], top.inputs["Value"])
    tc = N.new("ShaderNodeTexCoord"); s2 = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], s2.inputs[0])
    r = ramp_node(N, [(0.0, PAL["pink"]), (0.35, PAL["white"]), (0.6, PAL["lavender"]), (1.0, PAL["cyan"])])
    L.new(s2.outputs["X"], r.inputs["Fac"]); L.new(r.outputs["Color"], b.inputs["Emission Color"]); L.new(top.outputs["Result"], b.inputs["Emission Strength"])
    return m
MAT["saucer"] = saucer_mat()
def saucer_rim_mat():
    """canopy discs: dark glossy metallic body; bright iridescent pink/cyan/white light only on the outer lip, faint sheen on top"""
    m = principled("St_SaucerRim", (0.025, 0.025, 0.06), 0.95, 0.12, 1.0, 420); N, L = nodes(m); b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
    cx = N.new("ShaderNodeMath"); cx.operation = 'MULTIPLY_ADD'; cx.inputs[1].default_value = 2.0; cx.inputs[2].default_value = -1.0; L.new(sp.outputs["X"], cx.inputs[0])
    cy = N.new("ShaderNodeMath"); cy.operation = 'MULTIPLY_ADD'; cy.inputs[1].default_value = 2.0; cy.inputs[2].default_value = -1.0; L.new(sp.outputs["Y"], cy.inputs[0])
    cb = N.new("ShaderNodeCombineXYZ"); L.new(cx.outputs[0], cb.inputs["X"]); L.new(cy.outputs[0], cb.inputs["Y"])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(cb.outputs[0], ln.inputs[0])
    edge = N.new("ShaderNodeMapRange"); edge.inputs["From Min"].default_value = 0.86; edge.inputs["From Max"].default_value = 0.99
    edge.inputs["To Min"].default_value = CY["saucer_top_glow"]*0.25; edge.inputs["To Max"].default_value = CY["rim_strength"]; L.new(ln.outputs["Value"], edge.inputs["Value"])
    at = N.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; L.new(cy.outputs[0], at.inputs[0]); L.new(cx.outputs[0], at.inputs[1])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY_ADD'; sc.inputs[1].default_value = 1/(2*math.pi); sc.inputs[2].default_value = 0.5; L.new(at.outputs[0], sc.inputs[0])
    r = ramp_node(N, [(0.0, PAL["pink"]), (0.22, PAL["cyan"]), (0.4, PAL["white"]), (0.55, PAL["lavender"]), (0.75, PAL["cyan"]), (1.0, PAL["pink"])])
    L.new(sc.outputs[0], r.inputs["Fac"]); L.new(r.outputs["Color"], b.inputs["Emission Color"]); L.new(edge.outputs["Result"], b.inputs["Emission Strength"])
    return m
MAT["saucer_rim"] = saucer_rim_mat()
MAT["ring"] = fresnel_iri(principled("St_Ring", (0.32, 0.32, 0.5), 1.0, 0.08, 1.0, 450), 1.6, 0.35,
                          stops=[(0.0, PAL["lavender"]), (0.5, PAL["white"]), (1.0, PAL["pink"])])
MAT["crown"] = fresnel_iri(principled("St_Crown", (0.75, 0.7, 0.95), 0.4, 0.15, 1.0, 350, PAL["lavender"], 2.0), 3.0, 0.4)
def crescent_mat():
    m = principled("St_Crescent", (0.92, 0.88, 1.0), 0.3, 0.15, 1.0); N, L = nodes(m); b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
    r = ramp_node(N, [(0.0, PAL["pink"]), (0.45, PAL["white"]), (1.0, PAL["lavender"])])
    L.new(sp.outputs["X"], r.inputs["Fac"]); L.new(r.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 7.0
    return m
MAT["crescent"] = crescent_mat()
def rim_mat():
    m = principled("St_Rim", (0.9, 0.9, 1.0), 1.0, 0.1); N, L = nodes(m); b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    at = N.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; L.new(sp.outputs["Y"], at.inputs[0]); L.new(sp.outputs["X"], at.inputs[1])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY_ADD'; sc.inputs[1].default_value = 1/(2*math.pi); sc.inputs[2].default_value = 0.5
    L.new(at.outputs[0], sc.inputs[0])
    r = ramp_node(N, [(0.0, PAL["pink"]), (0.22, PAL["cyan"]), (0.4, PAL["white"]), (0.5, PAL["cyan"]), (0.7, PAL["lavender"]), (1.0, PAL["pink"])])
    L.new(sc.outputs[0], r.inputs["Fac"]); L.new(r.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = CY["rim_strength"]
    return m
MAT["rim"] = rim_mat()
def plaza_mat():
    m = bpy.data.materials.new("St_Plaza"); N, L = nodes(m); N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    at = N.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; L.new(sp.outputs["Y"], at.inputs[0]); L.new(sp.outputs["X"], at.inputs[1])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY_ADD'; sc.inputs[1].default_value = 1/(2*math.pi); sc.inputs[2].default_value = 0.5
    L.new(at.outputs[0], sc.inputs[0])
    r = ramp_node(N, [(0.0, PAL["cyan"]), (0.25, PAL["pink"]), (0.5, PAL["yellow"]), (0.75, PAL["pink"]), (1.0, PAL["cyan"])])
    L.new(sc.outputs[0], r.inputs["Fac"]); L.new(r.outputs["Color"], e.inputs["Color"]); e.inputs["Strength"].default_value = CY["plaza_ring"]
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"]); return m
MAT["plaza"] = plaza_mat()
def windows_mat():
    """window-light instances: per-instance random colour (warm white / amber / teal / pink / cyan) and brightness"""
    m = bpy.data.materials.new("St_Windows"); N, L = nodes(m); N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); oi = N.new("ShaderNodeObjectInfo")
    r = ramp_node(N, [(0.0, PAL["amber"]), (0.35, (1.0, 0.82, 0.55)), (0.62, (1.0, 0.5, 0.2)), (0.78, PAL["teal"]), (0.9, PAL["pink"]), (1.0, PAL["cyan"])], 'CONSTANT')
    L.new(oi.outputs["Random"], r.inputs["Fac"])
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexWhiteNoise"); L.new(tc.outputs["Object"], vo.inputs["Vector"])
    st = N.new("ShaderNodeMapRange"); st.inputs["To Min"].default_value = CY["window_strength"]*0.3; st.inputs["To Max"].default_value = CY["window_strength"]
    L.new(oi.outputs["Random"], st.inputs["Value"])
    L.new(r.outputs["Color"], e.inputs["Color"]); L.new(st.outputs["Result"], e.inputs["Strength"])
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"]); return m
MAT["windows"] = windows_mat()
def windows_sparse_mat():
    """podium window band: mostly dark, a sparse scatter of warm / teal / pink lit cells (ref: dark podium, few lights)"""
    m = bpy.data.materials.new("St_WindowsSparse"); N, L = nodes(m); N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 0.22
    L.new(tc.outputs["Object"], vo.inputs["Vector"]); bw = N.new("ShaderNodeRGBToBW"); L.new(vo.outputs["Color"], bw.inputs[0])
    r = ramp_node(N, [(0.0, PAL["amber"]), (0.4, (1.0, 0.8, 0.5)), (0.7, PAL["teal"]), (0.85, PAL["pink"]), (1.0, PAL["cyan"])], 'CONSTANT')
    L.new(bw.outputs[0], r.inputs["Fac"])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 1.0 - ST["cycles"]["podium_lit_frac"]
    wn = N.new("ShaderNodeTexWhiteNoise"); L.new(vo.outputs["Position"], wn.inputs["Vector"]); L.new(wn.outputs["Value"], gt.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY_ADD'; mul.inputs[1].default_value = CY["window_strength"]*0.6; mul.inputs[2].default_value = 0.04
    L.new(gt.outputs[0], mul.inputs[0])
    L.new(r.outputs["Color"], e.inputs["Color"]); L.new(mul.outputs[0], e.inputs["Strength"])
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"]); return m
MAT["windows_sparse"] = windows_sparse_mat()
def glass_mat():
    """dark reflective glass with a fine grid of tiny warm/amber/teal lit cells (procedural, per-cell random)"""
    m = principled("St_Glass", (0.03, 0.05, 0.10), 0.5, 0.05, 1.0, 300); N, L = nodes(m); b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.6
    br.inputs["Mortar Size"].default_value = 0.1; br.inputs["Brick Width"].default_value = 0.9; br.inputs["Row Height"].default_value = 0.55
    br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0, 0, 0, 1); br.inputs["Mortar"].default_value = (0, 0, 0, 1); br.offset = 0.5
    L.new(tc.outputs["Object"], br.inputs["Vector"])
    bw = N.new("ShaderNodeRGBToBW"); L.new(br.outputs["Color"], bw.inputs[0])
    r = ramp_node(N, [(0.0, (0, 0, 0)), (0.42, (0, 0, 0)), (0.45, PAL["amber"]), (0.62, (1.0, 0.85, 0.6)), (0.75, (1.0, 0.55, 0.25)),
                      (0.84, PAL["teal"]), (0.92, PAL["pink"]), (1.0, PAL["cyan"])], 'CONSTANT')
    L.new(bw.outputs[0], r.inputs["Fac"])
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(br.outputs["Fac"], inv.inputs[1])
    mk = N.new("ShaderNodeMath"); mk.operation = 'MULTIPLY'; mk.inputs[1].default_value = 6.0; L.new(inv.outputs[0], mk.inputs[0])
    L.new(r.outputs["Color"], b.inputs["Emission Color"]); L.new(mk.outputs[0], b.inputs["Emission Strength"])
    return m
MAT["glass"] = glass_mat()
STRIP = emit("St_DeckStrip", (0.85, 0.88, 1.0), 6.0)
MAT["deck"] = MAT["podium"]

# ---------------- assignment by rules (params.json style.rules) ----------------
def pick(o):
    for kind, pat, mat in ST["rules"]:
        if kind == "name" and re.search(pat, o.name): return mat
        if kind == "role" and (pat == "*" or o.get("role") == pat): return mat
    return "shell"
count = {}
done_mesh = set()
for o in list(scene.objects):
    if o.type != 'MESH': continue
    if o.get("role") == "cut": o.hide_render = True; continue
    k = pick(o); count[k] = count.get(k, 0) + 1
    if o.data.name in done_mesh: continue          # shared (instanced) window meshes: assign once
    done_mesh.add(o.data.name)
    o.data.materials.clear(); o.data.materials.append(MAT[k])
    if k == "deck":                                 # light strip along the deck edge = the deck's vertical fascia faces
        o.data.materials.append(STRIP)
        for p in o.data.polygons: p.material_index = 1 if abs(p.normal.z) < 0.35 else 0
    else:
        for p in o.data.polygons: p.material_index = 0
print("STYLE assignment", count)

# ---------------- dressing (render only; no people, no city) ----------------
def light(name, kind, loc, energy, col, size=1.0, rot=None, spot=None, blend=0.6):
    L_ = bpy.data.lights.new(name, kind); L_.energy = energy; L_.color = col
    if kind in ('POINT', 'SPOT'): L_.shadow_soft_size = size
    if kind == 'AREA': L_.size = size
    if spot: L_.spot_size = spot; L_.spot_blend = blend
    o = bpy.data.objects.new(name, L_); scene.collection.objects.link(o); o.location = loc
    if rot: o.rotation_euler = rot
    return o
def ringmesh(name, r0, r1, c, z=0.03, n=192, sx=1.0, mat=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); vs = []
    for i in range(n):
        a = 2*math.pi*i/n
        vs.append((bm.verts.new((r0*math.cos(a)*sx, r0*math.sin(a), 0)), bm.verts.new((r1*math.cos(a)*sx, r1*math.sin(a), 0))))
    for i in range(n):
        a, b = vs[i], vs[(i + 1) % n]; bm.faces.new((a[0], b[0], b[1], a[1]))
    bm.to_mesh(me); ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); ob.location = (c[0], c[1], z)
    ob.data.materials.append(mat or MAT["plaza"]); return ob
PS = P["global"].get("plaza_scale", 1.0); PSX = P["global"].get("ref_stretch_x", 1.0)
pc = (0, FRONT_Y - 16*PS)
for r0, r1 in [(6.0, 6.3), (13.5, 14.1), (19.0, 19.35)]: ringmesh(f"StPlaza_{r0}", r0*PS, r1*PS, pc, sx=PSX)
# soft pastel plaza wash (warm centre -> pink -> violet edge)
def plaza_disc():
    m = bpy.data.materials.new("St_PlazaDisc"); N, L = nodes(m); N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord"); vl = N.new("ShaderNodeVectorMath"); vl.operation = 'LENGTH'
    L.new(tc.outputs["Object"], vl.inputs[0])
    r = ramp_node(N, [(0.0, (1.0, 0.85, 0.55)), (0.35, (1.0, 0.45, 0.7)), (0.7, (0.3, 0.6, 1.0)), (1.0, (0.05, 0.05, 0.2))])
    L.new(vl.outputs["Value"], r.inputs["Fac"]); L.new(r.outputs["Color"], e.inputs["Color"]); e.inputs["Strength"].default_value = CY["plaza_wash"]
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"]); return m
bpy.ops.mesh.primitive_circle_add(radius=1.0, vertices=128, fill_type='NGON', location=(pc[0], pc[1], 0.015))
pd = bpy.context.active_object; pd.name = "StPlazaDisc"; pd.scale = (25*PS*PSX, 25*PS, 1); pd.data.materials.append(plaza_disc())
SWOOSH = []
ringmesh("StCourtRing", P["courtyard"]["r"]*0.62, P["courtyard"]["r"]*0.66, CC, sx=P["courtyard"]["kx"])
# iridescent rim strips just under each canopy lip
def rim_strip(o, k):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = (min(v.x for v in bb) + max(v.x for v in bb))/2; cy = (min(v.y for v in bb) + max(v.y for v in bb))/2
    rx = (max(v.x for v in bb) - min(v.x for v in bb))/2; ry = (max(v.y for v in bb) - min(v.y for v in bb))/2
    cu = bpy.data.curves.new(f"StRimStrip{k}", 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('POLY'); n = 128; sp.points.add(n - 1)
    for i in range(n):
        a = 2*math.pi*i/n; sp.points[i].co = (cx + rx*math.cos(a), cy + ry*math.sin(a), min(v.z for v in bb) - 0.12, 1)
    sp.use_cyclic_u = True; cu.bevel_depth = 0.16 if rx > 6 else 0.11; cu.bevel_resolution = 2
    ob = bpy.data.objects.new(f"StRimStrip{k}", cu); scene.collection.objects.link(ob)
    ob.data.materials.append(emit(f"St_Strip{k}", [PAL["pink"], PAL["cyan"], PAL["white"], PAL["lavender"]][k % 4], CY["rim_strength"] * 1.1))
for k, o in enumerate([o for o in scene.objects if o.name.startswith("CanopyRim")]): rim_strip(o, k)
# warm-white starburst source deep in the tunnel + god rays fanning out of the arch
bpy.ops.mesh.primitive_circle_add(radius=6.0, fill_type='NGON', location=(0, FRONT_Y + 16, 6.0), rotation=(math.radians(90), 0, 0))
bpy.context.active_object.data.materials.append(emit("St_Burst", (1.0, 0.9, 0.72), 6.0))
light("StArchCore", 'POINT', (0, FRONT_Y + 8, 3.0), CY["arch_core_w"], (1.0, 0.88, 0.7), 2.0)
light("StBurstSpot", 'SPOT', (0, FRONT_Y + 12, 6), 6e3, (1.0, 0.9, 0.78), 1.0, (math.radians(95), 0, math.radians(180)), math.radians(120))
for k, (ax, az_) in enumerate([(-44, 20), (-30, 32), (-15, 42), (0, 48), (15, 42), (30, 32), (44, 20)]):
    light(f"StArchBeam{k}", 'SPOT', (0, FRONT_Y - 2.0, 1.5), 6e5, (1.0, 0.88, 0.7), 0.3,
          (math.radians(90 + az_), 0, math.radians(180 + ax)), math.radians(5), 0.1)
light("StCourtGlow", 'POINT', (CC[0], CC[1], 7), 2.5e4, (1.0, 0.82, 0.7), 5)
light("StCrownHalo", 'POINT', (TX, TY, TZ + 12), 1.5e5, (0.95, 0.85, 1.0), 12)
light("StMoon", 'SUN', (0, 0, 100), 0.25, (0.55, 0.6, 1.0), rot=(math.radians(40), 0, math.radians(200)))
light("StRimPink", 'AREA', (-90, 30, 80), 8e3, (1.0, 0.35, 0.8), 50, (math.radians(60), 0, math.radians(-120)))
light("StRimCyan", 'AREA', (100, 20, 70), 8e3, (0.25, 0.8, 1.0), 50, (math.radians(60), 0, math.radians(120)))
light("StUnderFill", 'AREA', (0, FRONT_Y - 40, 10), 2.5e3, (0.5, 0.45, 1.0), 70, (math.radians(-80), 0, 0))
# luminous pastel halo around the upper tower / crown: emissive volume sphere with a soft radial falloff
def halo(name, loc, R, strength, col):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R, location=loc, segments=48, ring_count=24); s = bpy.context.active_object; s.name = name
    m = bpy.data.materials.new(name); N, L = nodes(m); N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); vl = N.new("ShaderNodeVectorMath"); vl.operation = 'LENGTH'; L.new(tc.outputs["Object"], vl.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = R
    mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0; L.new(vl.outputs["Value"], mr.inputs["Value"])
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 3.0; L.new(mr.outputs["Result"], pw.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = strength; L.new(pw.outputs[0], mul.inputs[0])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs["Density"].default_value = 0.0; v.inputs["Emission Color"].default_value = (*col, 1)
    L.new(mul.outputs[0], v.inputs["Emission Strength"]); L.new(v.outputs[0], N["Material Output"].inputs["Volume"]); s.data.materials.append(m)
    return s
halo("StCrownHalo", (TX, TY, TZ + 4), 42.0, CY["crown_halo_strength"], (0.92, 0.82, 1.0))
halo("StCrownHaloPink", (TX - 8, TY, TZ + 12), 26.0, CY["crown_halo_strength"]*0.7, (1.0, 0.7, 0.9))
# global haze domain (scatter) + denser haze in front of the arch for the god rays
def haze_box(name, loc, scale, dens, col=(0.75, 0.75, 1.0), aniso=0.6):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); h = bpy.context.active_object; h.name = name; h.scale = scale
    m = bpy.data.materials.new(name); N, L = nodes(m); N.remove(N["Principled BSDF"])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs["Density"].default_value = dens; v.inputs["Color"].default_value = (*col, 1)
    v.inputs["Anisotropy"].default_value = aniso; L.new(v.outputs[0], N["Material Output"].inputs["Volume"]); h.data.materials.append(m)
    return h
haze_box("StHaze", (0, 0, 60), (420, 360, 120), CY["haze_density"], (0.62, 0.62, 1.0), 0.5)
haze_box("StHazeFront", (0, FRONT_Y - 18, 16), (120, 34, 32), CY["front_haze_density"], (0.85, 0.82, 1.0), 0.7)
# abstract backdrop: a few faint light swooshes (thin emissive arcs) far behind - no buildings
for k in range(5):
    cu = bpy.data.curves.new(f"StSwoosh{k}", 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('POLY'); n = 64; sp.points.add(n - 1)
    R = random.uniform(150, 230); z0 = random.uniform(25, 95); tilt = random.uniform(-0.25, 0.25); a0 = random.uniform(0.15, 0.4)*math.pi
    for i in range(n):
        a = a0 + (math.pi - 2*a0)*i/(n - 1); sp.points[i].co = (R*math.cos(a)*1.4, 120 + R*math.sin(a)*0.6, z0 + tilt*R*math.cos(a) + 18*math.sin(a), 1)
    cu.bevel_depth = random.uniform(0.25, 0.6)
    ob = bpy.data.objects.new(f"StSwoosh{k}", cu); scene.collection.objects.link(ob); SWOOSH.append(ob)
    ob.data.materials.append(emit(f"St_Swoosh{k}", random.choice([PAL["pink"], PAL["cyan"], PAL["lavender"]]), random.uniform(0.8, 2.0)))
# world: deep blue-violet gradient (dark navy at the top)
world = bpy.data.worlds.new("StWorld"); scene.world = world; world.use_nodes = True
N, L = world.node_tree.nodes, world.node_tree.links
bg = N["Background"]; tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
r = ramp_node(N, [(0.45, (0.10, 0.10, 0.30)), (0.56, (0.05, 0.045, 0.16)), (0.75, (0.008, 0.008, 0.03))])
L.new(sp.outputs["Z"], r.inputs["Fac"]); L.new(r.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = CY["world_strength"]

# ---------------- render settings + compositor (bloom + soft streaks) ----------------
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.cycles.volume_step_rate = 5.0; scene.cycles.volume_max_steps = 192; scene.cycles.max_bounces = 6; scene.cycles.volume_bounces = 1
scene.cycles.use_light_tree = True; scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'; scene.view_settings.exposure = CY["exposure"]
try:
    ng = bpy.data.node_groups.new("StComp", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new("CompositorNodeRLayers"); g1 = ng.nodes.new("CompositorNodeGlare"); g2 = ng.nodes.new("CompositorNodeGlare"); go = ng.nodes.new("NodeGroupOutput")
    def gtype(g, names):
        for v in names:
            try: g.inputs["Type"].default_value = v; return v
            except Exception: pass
    gtype(g1, ("Bloom", "BLOOM", "Fog Glow", "FOG_GLOW")); gtype(g2, ("Streaks", "STREAKS"))
    g1.inputs["Threshold"].default_value = CY["glare_threshold"]; g1.inputs["Strength"].default_value = CY["glare_strength"]
    g2.inputs["Threshold"].default_value = 6.0; g2.inputs["Strength"].default_value = 0.25
    try: g2.inputs["Streaks"].default_value = 8
    except Exception: pass
    ng.links.new(rl.outputs["Image"], g1.inputs["Image"]); ng.links.new(g1.outputs["Image"], g2.inputs["Image"]); ng.links.new(g2.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = ng; scene.render.use_compositing = True
    print("STYLE glare", g1.inputs["Type"].default_value, g2.inputs["Type"].default_value)
except Exception as e:
    print("STYLE glare skipped:", e)

# ---------------- cameras ----------------
cam = bpy.data.objects.new("StCam", bpy.data.cameras.new("StCam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.clip_end = 3000; cam.data.sensor_width = 36
dz = P["podium"]["deck_top"]
VIEW = {   # loc, target, lens, (w, h)
    "front": ((0, FRONT_Y - 80, dz - 5.0), (0, 10, dz + 7.0), 17, (CY["front_res"], CY["front_res"]//2)),
    "aerial": ((-150, -175, 120), (2, 4, 22), 30, (CY["view_res"], int(CY["view_res"]*0.5625))),
    "courtyard": ((CC[0], CC[1] - 15.5, 1.7), (TX*0.5, TY, 42), 15, (CY["view_res"], int(CY["view_res"]*0.5625))),
}
for v in VIEWS:
    loc, tgt, lens, (w, h) = VIEW[v]
    for o in SWOOSH: o.hide_render = v != "front"          # backdrop swooshes only behind the front view
    if RES: s = int(RES)/w; w, h = int(RES), int(h*s)
    cam.location = Vector(loc); cam.data.lens = lens; cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.filepath = os.path.join(OUT, f"style_{v}_raw.png")
    bpy.ops.render.render(write_still=True)
    print("STYLE RENDER", v, scene.render.filepath, w, h)
