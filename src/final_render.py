# Mood render matching ref/mood_render.png: dark blue-violet haze, glossy dark + glass, iridescent rims,
# warm light pouring out of the front arch onto a luminous plaza ring, coloured window lights (v14: no people).
#   blender -b building.blend -P src/final_render.py     env: SAMPLES (128) RES (1536) OUT
import bpy, math, os, random, json
from mathutils import Vector
scene = bpy.context.scene
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(HERE, "params.json")))
OUT = os.environ.get("OUT", os.path.join(HERE, "final_render.png"))
SAMPLES = int(os.environ.get("SAMPLES", "128")); RES = int(os.environ.get("RES", "2048"))
random.seed(7)

def nodes(m): m.use_nodes = True; return m.node_tree.nodes, m.node_tree.links
def principled(name, base, metal=0.0, rough=0.3, coat=0.0, film=0.0, emis=None, estr=0.0):
    m = bpy.data.materials.new(name); N, L = nodes(m); b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Metallic"].default_value = metal; b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    if film and "Thin Film Thickness" in b.inputs: b.inputs["Thin Film Thickness"].default_value = film; b.inputs["Thin Film IOR"].default_value = 1.45
    if emis: b.inputs["Emission Color"].default_value = (*emis, 1); b.inputs["Emission Strength"].default_value = estr
    return m

# --- dark glossy shell with thin-film iridescence
def shell_mat():
    m = principled("MoodShell", (0.035, 0.04, 0.07), metal=0.75, rough=0.2, coat=0.8, film=420); N, L = nodes(m); b = N["Principled BSDF"]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 3.0; L.new(lw.outputs["Facing"], pw.inputs[0])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 0.7; L.new(pw.outputs[0], sc.inputs[0])
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (1.0, 0.3, 0.75, 1); el[1].position = 1.0; el[1].color = (0.25, 0.85, 1.0, 1)
    e = el.new(0.5); e.color = (0.95, 0.9, 1.0, 1)
    L.new(sp.outputs["X"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Emission Color"]); L.new(sc.outputs[0], b.inputs["Emission Strength"])
    return m
SHELL = shell_mat()
SLAB = principled("MoodSlab", (0.022, 0.024, 0.040), metal=0.3, rough=0.4)
GROUND = principled("MoodGround", (0.012, 0.013, 0.025), metal=0.0, rough=0.12, coat=1.0)

# --- glass with procedural coloured window lights (brick grid -> random emissive cells)
def glass_mat():
    m = bpy.data.materials.new("MoodGlass"); N, L = nodes(m); b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.04, 0.06, 0.11, 1); b.inputs["Metallic"].default_value = 0.4
    b.inputs["Roughness"].default_value = 0.06; b.inputs["Coat Weight"].default_value = 1.0
    if "Thin Film Thickness" in b.inputs: b.inputs["Thin Film Thickness"].default_value = 300
    tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 0.8
    br.inputs["Mortar Size"].default_value = 0.08; br.inputs["Brick Width"].default_value = 1.6; br.inputs["Row Height"].default_value = 1.1
    br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0, 0, 0, 1)
    br.offset = 0.5
    L.new(tc.outputs["Object"], br.inputs["Vector"])
    # per-cell random: use brick "Fac" (random per brick) through a ramp of window colours, gated by a threshold
    ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (0, 0, 0, 1); el[1].position = 1.0; el[1].color = (0.3, 0.8, 1.0, 1)
    for pos, col in [(0.30, (0, 0, 0, 1)), (0.32, (1.0, 0.55, 0.18, 1)), (0.55, (1.0, 0.82, 0.5, 1)), (0.72, (1.0, 0.65, 0.3, 1)), (0.82, (1.0, 0.3, 0.45, 1)), (0.9, (0.3, 0.85, 1.0, 1))]:
        e = el.new(pos); e.color = col
    ramp.color_ramp.interpolation = 'CONSTANT'
    bw = N.new("ShaderNodeRGBToBW"); L.new(br.outputs["Color"], bw.inputs[0]); L.new(bw.outputs[0], ramp.inputs["Fac"])
    br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0, 0, 0, 1); br.inputs["Mortar"].default_value = (0, 0, 0, 1)
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(br.outputs["Fac"], inv.inputs[1])
    mask = N.new("ShaderNodeMath"); mask.operation = 'MULTIPLY'; L.new(inv.outputs[0], mask.inputs[0]); mask.inputs[1].default_value = 10.0
    L.new(ramp.outputs["Color"], b.inputs["Emission Color"]); L.new(mask.outputs[0], b.inputs["Emission Strength"])
    return m
GLASS = glass_mat()

# --- iridescent rim: emission colour cycles pink/cyan/white with azimuth around the object's origin
def rim_mat():
    m = bpy.data.materials.new("MoodRim"); N, L = nodes(m); b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.9, 0.9, 1, 1); b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.1
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    at = N.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; L.new(sp.outputs["Y"], at.inputs[0]); L.new(sp.outputs["X"], at.inputs[1])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY_ADD'; sc.inputs[1].default_value = 1/(2*math.pi); sc.inputs[2].default_value = 0.5
    L.new(at.outputs[0], sc.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (1.0, 0.35, 0.75, 1); el[1].position = 1.0; el[1].color = (1.0, 0.35, 0.75, 1)
    for pos, col in [(0.22, (0.3, 0.9, 1.0, 1)), (0.40, (0.95, 0.75, 1, 1)), (0.48, (0.3, 0.9, 1.0, 1)), (0.7, (0.75, 0.45, 1.0, 1))]:
        e = el.new(pos); e.color = col
    L.new(sc.outputs[0], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 9.0
    return m
RIM = rim_mat()
def emit(name, col, s):
    m = bpy.data.materials.new(name); N, L = nodes(m); N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = s
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"]); return m
PLAZA = emit("MoodPlaza", (1.0, 0.85, 0.55), 14.0)
def win_mat():
    m = bpy.data.materials.new("MoodWindows"); N, L = nodes(m); N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 0.35
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements; ramp.color_ramp.interpolation = 'CONSTANT'
    el[0].color = (1.0, 0.62, 0.28, 1); el[1].position = 0.92; el[1].color = (0.35, 0.85, 1.0, 1)
    for pos, col in [(0.45, (1.0, 0.82, 0.55, 1)), (0.7, (1.0, 0.5, 0.22, 1)), (0.84, (1.0, 0.35, 0.55, 1))]:
        x = el.new(pos); x.color = col
    bw = N.new("ShaderNodeRGBToBW"); L.new(vo.outputs["Color"], bw.inputs[0]); L.new(bw.outputs[0], ramp.inputs["Fac"])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 13.0; L.new(sep.outputs["Z"], gt.inputs[0])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY_ADD'; st.inputs[1].default_value = 8.0; st.inputs[2].default_value = 6.0; L.new(gt.outputs[0], st.inputs[0])
    L.new(ramp.outputs["Color"], e.inputs["Color"]); L.new(st.outputs[0], e.inputs["Strength"])
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"]); return m
WIN = [win_mat()]

def crescent_mat():
    m = bpy.data.materials.new("MoodCrescent"); N, L = nodes(m); b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.9, 0.85, 1, 1); b.inputs["Metallic"].default_value = 0.6; b.inputs["Roughness"].default_value = 0.15
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].color = (1.0, 0.3, 0.7, 1); el[1].color = (1.0, 0.97, 1.0, 1); e = el.new(0.5); e.color = (1.0, 0.6, 0.9, 1)
    L.new(sp.outputs["X"], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 6.0
    return m
CRESC = crescent_mat()
for o in list(scene.objects):
    if o.type != 'MESH': continue
    if o.name.startswith("CrescentCrown"):
        o.data.materials.clear(); o.data.materials.append(CRESC); [setattr(p, "material_index", 0) for p in o.data.polygons]; continue
    r = o.get("role")
    m = {"glass": GLASS, "ground": GROUND, "rim": RIM, "plaza_glow": PLAZA, "slab": SLAB, "wall": SLAB, "stair": SLAB}.get(r, SHELL)
    if r == "window_light": m = random.choice(WIN)
    if r == "cut": o.hide_render = True; continue
    o.data.materials.clear(); o.data.materials.append(m)
    for p in o.data.polygons: p.material_index = 0

# --- extra plaza rings (render dressing) in front of the arch
FRONT_Y = -P["podium"]["wall_half_d"] + P["podium"]["wall_cy"]
def ringmesh(name, r0, r1, c, z=0.03, n=192):
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new(); vs = []
    for i in range(n):
        a = 2*math.pi*i/n
        vs.append((bm.verts.new((c[0] + r0*math.cos(a), c[1] + r0*math.sin(a), z)), bm.verts.new((c[0] + r1*math.cos(a), c[1] + r1*math.sin(a), z))))
    for i in range(n):
        a, b = vs[i], vs[(i + 1) % n]; bm.faces.new((a[0], b[0], b[1], a[1]))
    bm.to_mesh(me); ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); ob.data.materials.append(PLAZA); return ob
pc = (0, FRONT_Y - 16*P["global"].get("plaza_scale", 1.0))
PLAZA_SX = P["global"].get("ref_stretch_x", 1.0)   # v6: forecourt widened with the building
PS = P["global"].get("plaza_scale", 1.0)            # v7: larger forecourt plaza overall
for r0, r1 in [(13.5, 14.3), (19.0, 19.5), (24.0, 24.35), (6.0, 6.3)]: ringmesh(f"PlazaDress_{r0}", r0*PS, r1*PS, pc).scale.x = PLAZA_SX


# filled elliptical plaza glow: warm-white centre -> gold ring -> magenta edge
def plaza_disc():
    m = bpy.data.materials.new("MoodPlazaDisc"); N, L = nodes(m); N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord"); vl = N.new("ShaderNodeVectorMath"); vl.operation = 'LENGTH'
    L.new(tc.outputs["Object"], vl.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (1.0, 0.9, 0.7, 1); el[1].position = 1.0; el[1].color = (0.9, 0.15, 0.6, 1)
    for pos, col in [(0.55, (1.0, 0.75, 0.35, 1)), (0.8, (1.0, 0.4, 0.55, 1))]: x = el.new(pos); x.color = col
    L.new(vl.outputs["Value"], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], e.inputs["Color"]); e.inputs["Strength"].default_value = 2.2
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"]); return m
bpy.ops.mesh.primitive_circle_add(radius=1.0, vertices=128, fill_type='NGON', location=(pc[0], pc[1], 0.02))
pd = bpy.context.active_object; pd.name = "PlazaDisc"; pd.scale = (24.0*PS*PLAZA_SX, 24.0*PS, 1); pd.data.materials.append(plaza_disc())
# --- tiny people (1.75 m) on the forecourt
pm = [principled("MoodPerson", (0.02, 0.02, 0.03), rough=0.5)] + [emit(f"MoodPersonC{i}", c, 1.5) for i, c in enumerate([(1, 0.3, 0.4), (0.3, 0.7, 1), (1, 0.8, 0.5)])]
H = P["people"]["height"]
for i in range(0):          # v14: no people (user request) - P["people"]["count"] is 0 as well
    a = random.uniform(0, 2*math.pi); rr = random.uniform(4, 24*PS)
    x, y = pc[0] + rr*math.cos(a)*1.3, pc[1] + rr*math.sin(a)*0.8 + 4
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=H - 0.3, location=(x, y, (H - 0.3)/2), vertices=8)
    body = bpy.context.active_object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(x, y, H - 0.13), segments=8, ring_count=6)
    head = bpy.context.active_object
    m = pm[0] if random.random() < 0.7 else random.choice(pm[1:])
    for ob in (body, head): ob.data.materials.append(m)

# --- world: blue-violet sky gradient + volumetric haze
world = bpy.data.worlds.new("MoodWorld"); scene.world = world; world.use_nodes = True
N, L = world.node_tree.nodes, world.node_tree.links
bg = N["Background"]; tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
el[0].position = 0.45; el[0].color = (0.16, 0.19, 0.36, 1); el[1].position = 0.75; el[1].color = (0.03, 0.03, 0.09, 1)
L.new(sp.outputs["Z"], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.35
vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.5, 0.5, 0.95, 1); vol.inputs["Density"].default_value = 0.0006
vol.inputs["Anisotropy"].default_value = 0.55
# v6: no world volume / background haze / far city -> plain dark sky gradient

# --- lights
def light(name, kind, loc, energy, col, size=1.0, rot=None, spot=None):
    L_ = bpy.data.lights.new(name, kind); L_.energy = energy; L_.color = col
    if kind in ('POINT', 'SPOT'): L_.shadow_soft_size = size
    if kind == 'AREA': L_.size = size
    if spot: L_.spot_size = spot; L_.spot_blend = 0.6
    o = bpy.data.objects.new(name, L_); scene.collection.objects.link(o); o.location = loc
    if rot: o.rotation_euler = rot
    return o
tz = P["tower"]["crown_z"]; tx, ty = P["tower"]["cx"], P["tower"]["cy"]
light("ArchCore", 'POINT', (0, FRONT_Y + 8, 3.0), 1.0e4, (1.0, 0.88, 0.7), 2.5)              # light source inside the portal
light("ArchSpill", 'SPOT', (0, FRONT_Y + 3, 6.0), 4e3, (1.0, 0.9, 0.75), 3.0, (math.radians(105), 0, math.radians(180)), math.radians(95))
light("CourtGlow", 'POINT', (0, 3, 6), 3e4, (1.0, 0.85, 0.7), 5)
light("CrownHalo", 'POINT', (tx, ty, tz + 14), 1.2e5, (0.95, 0.85, 1.0), 10)                   # bright sky opening above the crown
light("Moon", 'SUN', (0, 0, 100), 0.6, (0.6, 0.65, 1.0), rot=(math.radians(40), 0, math.radians(200)))
light("RimPink", 'AREA', (-80, 30, 70), 6e3, (1.0, 0.4, 0.8), 40, (math.radians(60), 0, math.radians(-120)))
light("RimCyan", 'AREA', (90, 20, 60), 6e3, (0.3, 0.8, 1.0), 40, (math.radians(60), 0, math.radians(120)))
light("UnderFill", 'AREA', (0, FRONT_Y - 35, 12), 3e3, (0.55, 0.5, 1.0), 60, (math.radians(-80), 0, 0))
# denser haze box in front of the arch so the outpouring light shows rays
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, FRONT_Y - 17, 18)); hz = bpy.context.active_object; hz.scale = (110, 32, 36)
hm = bpy.data.materials.new("MoodHazeBox"); N2, L2 = nodes(hm); N2.remove(N2["Principled BSDF"])
pv = N2.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = 0.006; pv.inputs["Color"].default_value = (0.8, 0.8, 1.0, 1); pv.inputs["Anisotropy"].default_value = 0.7
L2.new(pv.outputs[0], N2["Material Output"].inputs["Volume"]); hz.data.materials.append(hm)
# brilliant source inside the tunnel mouth: emissive disc + strong spot aimed out toward the camera
bpy.ops.mesh.primitive_circle_add(radius=6.5, fill_type='NGON', location=(0, FRONT_Y + 14, 6.5), rotation=(math.radians(90), 0, 0))
burst = bpy.context.active_object; burst.data.materials.append(emit("MoodBurst", (1.0, 0.85, 0.62), 2.4))
light("BurstSpot", 'SPOT', (0, FRONT_Y + 12, 7), 4e3, (1.0, 0.9, 0.75), 1.5, (math.radians(95), 0, math.radians(180)), math.radians(120))
# --- visible light shafts: narrow warm spots fanning out of the arch + cool beams from the sky opening, scattered by the haze box
for k, (ax, az_) in enumerate([(-40, 22), (-26, 34), (-12, 44), (0, 50), (12, 44), (26, 34), (40, 22)]):
    light(f"ArchBeam{k}", 'SPOT', (0, FRONT_Y - 3.0, 1.5), 7e5, (1.0, 0.86, 0.66), 0.3,
          (math.radians(90 + az_), 0, math.radians(180 + ax)), math.radians(6)).data.spot_blend = 0.1
# --- iridescent rim strips: an emissive tube just under every canopy lip, alternating pink / cyan
import bmesh
def rim_strip(o, k):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = (min(v.x for v in bb) + max(v.x for v in bb))/2; cy = (min(v.y for v in bb) + max(v.y for v in bb))/2
    rx = (max(v.x for v in bb) - min(v.x for v in bb))/2; ry = (max(v.y for v in bb) - min(v.y for v in bb))/2
    z = min(v.z for v in bb) - 0.12
    cu = bpy.data.curves.new(f"RimStrip{k}", 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('POLY'); n = 96; sp.points.add(n - 1)
    for i in range(n):
        a = 2*math.pi*i/n; sp.points[i].co = (cx + rx*math.cos(a), cy + ry*math.sin(a), z, 1)
    sp.use_cyclic_u = True; cu.bevel_depth = 0.16 if rx > 6 else 0.11; cu.bevel_resolution = 2
    ob = bpy.data.objects.new(f"RimStrip{k}", cu); scene.collection.objects.link(ob)
    col = [(1.0, 0.12, 0.6), (0.08, 0.75, 1.0), (0.7, 0.3, 1.0)][k % 3]
    ob.data.materials.append(emit(f"MoodStrip{k}", col, 14.0))
for k, o in enumerate([o for o in scene.objects if o.name.startswith("CanopyRim")]):
    rim_strip(o, k)
# --- camera: low, front, looking up through the plaza ring into the arch
cam = bpy.data.objects.new("MoodCam", bpy.data.cameras.new("MoodCam")); scene.collection.objects.link(cam); scene.camera = cam
cam.location = Vector((0, FRONT_Y - 112, 3.5)); cam.data.lens = 24; cam.data.sensor_width = 36   # v7: pulled back for the wider frame
tgt = Vector((0, 10, 35)); cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.shift_y = 0.0; cam.data.clip_end = 2000

scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.cycles.volume_step_rate = 4.0; scene.cycles.volume_max_steps = 256; scene.cycles.max_bounces = 6; scene.cycles.volume_bounces = 1
scene.render.film_transparent = False
scene.render.resolution_x = RES; scene.render.resolution_y = RES//2
scene.cycles.use_light_tree = True; scene.render.use_persistent_data = False
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'; scene.view_settings.exposure = 0.0
# soft bloom around the brightest sources (arch glow, rims) - compositor fog glow
try:
    ng = bpy.data.node_groups.new("MoodComp", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new("CompositorNodeRLayers"); gl = ng.nodes.new("CompositorNodeGlare"); go = ng.nodes.new("NodeGroupOutput")
    for v in ("Fog Glow", "FOG_GLOW"):
        try: gl.inputs["Type"].default_value = v; break
        except Exception: pass
    gl.inputs["Threshold"].default_value = 1.2; gl.inputs["Strength"].default_value = 0.45
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"]); ng.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = ng; scene.render.use_compositing = True
    print("glare on", gl.inputs["Type"].default_value)
except Exception as e:
    print("glare skipped:", e)
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("FINAL RENDER", OUT)
