# Mood render matching ref/mood_render.png: dark blue-violet haze, glossy dark + glass, iridescent rims,
# warm light pouring out of the front arch onto a luminous plaza ring, coloured window lights, tiny people.
#   blender -b building.blend -P src/final_render.py     env: SAMPLES (128) RES (1536) OUT
import bpy, math, os, random, json
from mathutils import Vector
scene = bpy.context.scene
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(HERE, "params.json")))
OUT = os.environ.get("OUT", os.path.join(HERE, "final_render.png"))
SAMPLES = int(os.environ.get("SAMPLES", "128")); RES = int(os.environ.get("RES", "1536"))
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
SHELL = principled("MoodShell", (0.06, 0.065, 0.11), metal=0.7, rough=0.18, coat=0.6, film=420)
SLAB = principled("MoodSlab", (0.022, 0.024, 0.040), metal=0.3, rough=0.4)
GROUND = principled("MoodGround", (0.012, 0.013, 0.025), metal=0.0, rough=0.12, coat=1.0)

# --- glass with procedural coloured window lights (brick grid -> random emissive cells)
def glass_mat():
    m = bpy.data.materials.new("MoodGlass"); N, L = nodes(m); b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.04, 0.06, 0.11, 1); b.inputs["Metallic"].default_value = 0.4
    b.inputs["Roughness"].default_value = 0.06; b.inputs["Coat Weight"].default_value = 1.0
    if "Thin Film Thickness" in b.inputs: b.inputs["Thin Film Thickness"].default_value = 300
    tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 0.42
    br.inputs["Mortar Size"].default_value = 0.08; br.inputs["Brick Width"].default_value = 1.6; br.inputs["Row Height"].default_value = 1.1
    br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0, 0, 0, 1)
    br.offset = 0.5
    L.new(tc.outputs["Object"], br.inputs["Vector"])
    # per-cell random: use brick "Fac" (random per brick) through a ramp of window colours, gated by a threshold
    ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (0, 0, 0, 1); el[1].position = 1.0; el[1].color = (0.3, 0.8, 1.0, 1)
    for pos, col in [(0.62, (0, 0, 0, 1)), (0.64, (1.0, 0.55, 0.18, 1)), (0.74, (1.0, 0.85, 0.55, 1)), (0.82, (1.0, 0.25, 0.35, 1)), (0.9, (0.25, 0.85, 1.0, 1))]:
        e = el.new(pos); e.color = col
    ramp.color_ramp.interpolation = 'CONSTANT'
    bw = N.new("ShaderNodeRGBToBW"); L.new(br.outputs["Color"], bw.inputs[0]); L.new(bw.outputs[0], ramp.inputs["Fac"])
    br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0, 0, 0, 1); br.inputs["Mortar"].default_value = (0, 0, 0, 1)
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(br.outputs["Fac"], inv.inputs[1])
    mask = N.new("ShaderNodeMath"); mask.operation = 'MULTIPLY'; L.new(inv.outputs[0], mask.inputs[0]); mask.inputs[1].default_value = 7.0
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
    for pos, col in [(0.22, (0.3, 0.9, 1.0, 1)), (0.40, (0.85, 0.95, 1, 1)), (0.48, (0.3, 0.9, 1.0, 1)), (0.7, (0.75, 0.45, 1.0, 1))]:
        e = el.new(pos); e.color = col
    L.new(sc.outputs[0], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 9.0
    return m
RIM = rim_mat()
def emit(name, col, s):
    m = bpy.data.materials.new(name); N, L = nodes(m); N.remove(N["Principled BSDF"])
    e = N.new("ShaderNodeEmission"); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = s
    L.new(e.outputs[0], N["Material Output"].inputs["Surface"]); return m
PLAZA = emit("MoodPlaza", (1.0, 0.86, 0.6), 22.0)
WIN = [emit(f"MoodWin{i}", c, 9.0) for i, c in enumerate([(1.0, 0.55, 0.2), (1.0, 0.8, 0.5), (0.25, 0.8, 1.0), (1.0, 0.3, 0.45), (0.65, 0.4, 1.0)])]

for o in list(scene.objects):
    if o.type != 'MESH': continue
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
pc = (0, FRONT_Y - 16)
for r0, r1 in [(13.5, 14.2), (19.0, 19.35), (6.0, 6.25)]: ringmesh(f"PlazaDress_{r0}", r0, r1, pc)

# --- tiny people (1.75 m) on the forecourt
pm = [principled("MoodPerson", (0.02, 0.02, 0.03), rough=0.5)] + [emit(f"MoodPersonC{i}", c, 1.5) for i, c in enumerate([(1, 0.3, 0.4), (0.3, 0.7, 1), (1, 0.8, 0.5)])]
H = P["people"]["height"]
for i in range(P["people"]["count"]):
    a = random.uniform(0, 2*math.pi); rr = random.uniform(4, 24)
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
el[0].position = 0.45; el[0].color = (0.035, 0.04, 0.09, 1); el[1].position = 0.75; el[1].color = (0.06, 0.05, 0.14, 1)
L.new(sp.outputs["Z"], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 3.5
vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.5, 0.5, 0.95, 1); vol.inputs["Density"].default_value = 0.0012
vol.inputs["Anisotropy"].default_value = 0.55
L.new(vol.outputs[0], N["World Output"].inputs["Volume"])

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
light("ArchCore", 'POINT', (0, FRONT_Y + 8, 3.0), 6e4, (1.0, 0.88, 0.7), 2.5)              # light source inside the portal
light("ArchSpill", 'SPOT', (0, FRONT_Y + 3, 6.0), 1.2e5, (1.0, 0.9, 0.75), 3.0, (math.radians(105), 0, math.radians(180)), math.radians(95))
light("CourtGlow", 'POINT', (0, 3, 6), 3e4, (1.0, 0.85, 0.7), 5)
light("CrownHalo", 'POINT', (tx, ty, tz + 14), 1.2e5, (0.95, 0.85, 1.0), 10)                   # bright sky opening above the crown
light("Moon", 'SUN', (0, 0, 100), 0.6, (0.6, 0.65, 1.0), rot=(math.radians(40), 0, math.radians(200)))
light("RimPink", 'AREA', (-80, 30, 70), 6e3, (1.0, 0.4, 0.8), 40, (math.radians(60), 0, math.radians(-120)))
light("RimCyan", 'AREA', (90, 20, 60), 6e3, (0.3, 0.8, 1.0), 40, (math.radians(60), 0, math.radians(120)))
light("UnderFill", 'AREA', (0, FRONT_Y - 35, 12), 2.5e4, (0.55, 0.5, 1.0), 60, (math.radians(-80), 0, 0))
# glowing disc behind the crown (sky opening in the reference)
bpy.ops.mesh.primitive_circle_add(radius=30, fill_type='NGON', location=(tx, ty + 60, tz + 10), rotation=(math.radians(90), 0, 0))
disc = bpy.context.active_object; disc.data.materials.append(emit("MoodSkyDisc", (0.85, 0.85, 1.0), 6.0))

# --- camera: low, front, looking up through the plaza ring into the arch
cam = bpy.data.objects.new("MoodCam", bpy.data.cameras.new("MoodCam")); scene.collection.objects.link(cam); scene.camera = cam
cam.location = Vector((0, FRONT_Y - 95, 8.0)); cam.data.lens = 23; cam.data.sensor_width = 36
tgt = Vector((0, 10, 37)); cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.shift_y = 0.0; cam.data.clip_end = 2000

scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.cycles.volume_step_rate = 4.0; scene.cycles.volume_max_steps = 256; scene.cycles.max_bounces = 6; scene.cycles.volume_bounces = 1
scene.render.film_transparent = False
scene.render.resolution_x = RES; scene.render.resolution_y = RES//2
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Punchy'; scene.view_settings.exposure = 0.0
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("FINAL RENDER", OUT)
