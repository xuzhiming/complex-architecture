# White-clay Cycles renders of building.blend: true-ortho FRONT/REAR/LEFT/RIGHT/TOP + perspective hero.
#   blender -b building.blend -P src/render_clay.py      env: SAMPLES (64)  RES (1600)  ONLY (comma list)  OUTDIR
import bpy, math, os
from mathutils import Vector
scene = bpy.context.scene
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("OUTDIR", os.path.join(HERE, "renders")); os.makedirs(OUT, exist_ok=True)
SAMPLES = int(os.environ.get("SAMPLES", "64")); RES = int(os.environ.get("RES", "1600")); ONLY = os.environ.get("ONLY", "")
H = max((o.matrix_world @ Vector(c)).z for o in scene.objects if o.type == 'MESH' for c in o.bound_box)

clay = bpy.data.materials.new("ClayWhite"); clay.use_nodes = True
b = clay.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.86, 0.86, 0.85, 1); b.inputs["Roughness"].default_value = 0.6
glz = bpy.data.materials.new("ClayGlaze"); glz.use_nodes = True
b = glz.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.74, 0.75, 0.76, 1); b.inputs["Roughness"].default_value = 0.35
for o in scene.objects:
    if o.type != 'MESH': continue
    r = o.get("role")
    if r in ("plaza_glow", "window_light", "cut"): o.hide_render = True; continue
    m = glz if r == "glass" else clay
    o.data.materials.clear(); o.data.materials.append(m)
    for p in o.data.polygons: p.material_index = 0

scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'; scene.view_settings.exposure = -0.2
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.5
gs = bpy.data.objects.get("GroundSlab")
if gs: gs.hide_render = True
bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, -0.02)); gnd = bpy.context.active_object; gnd.is_shadow_catcher = True
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 2.6; sun.data.angle = math.radians(10)
for nm, loc, pw, rad in [("CourtFill", (0, 0, 8.0), 9000, 6.0), ("TunnelFill", (0, -36, 5.0), 3000, 4.0)]:
    L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT')); scene.collection.objects.link(L)
    L.location = loc; L.data.energy = pw; L.data.shadow_soft_size = rad
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.clip_end = 3000
def look(target): cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
def render(name, loc, target, ortho=None, lens=40, sun_rot=(0, 0, 0), rx=RES, ry=None):
    if ONLY and not any(k in name for k in ONLY.split(",")): return
    scene.render.resolution_x = rx; scene.render.resolution_y = ry or int(rx*0.625)
    cam.location = Vector(loc)
    if ortho: cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else: cam.data.type = 'PERSP'; cam.data.lens = lens
    look(target); sun.rotation_euler = sun_rot
    scene.render.filepath = os.path.join(OUT, name); bpy.ops.render.render(write_still=True); print("rendered", name)
D, zc, OS = 500, H/2, 175
r = math.radians
render("front.png", (0, -D, zc), (0, 0, zc), OS, sun_rot=(r(55), 0, r(-30)))
render("rear.png", (0, D, zc), (0, 0, zc), OS, sun_rot=(r(55), 0, r(150)))
render("left.png", (D, 0, zc), (0, 0, zc), OS, sun_rot=(r(55), 0, r(60)))      # camera at +X: front on image left, tower right
render("right.png", (-D, 0, zc), (0, 0, zc), OS, sun_rot=(r(55), 0, r(-120)))
if not ONLY or "top" in ONLY:
    gnd.hide_render = True
    scene.render.resolution_x = scene.render.resolution_y = RES
    cam.location = Vector((0, 0, 600)); cam.data.type = 'ORTHO'; cam.data.ortho_scale = 180; cam.rotation_euler = (0, 0, 0)
    sun.rotation_euler = (r(30), 0, r(-30)); scene.render.filepath = os.path.join(OUT, "top.png"); bpy.ops.render.render(write_still=True)
    gnd.hide_render = False
# hero: front-left, azimuth 35 deg, elevation 25 deg, looking into the arch
az, el, dist, tgt = r(35), r(float(os.environ.get("HERO_EL", "25"))), 300, (0, -10, 26)
render(os.environ.get("HERO_NAME", "perspective_hero.png"), (tgt[0] - dist*math.cos(el)*math.sin(az), tgt[1] - dist*math.cos(el)*math.cos(az), tgt[2] + dist*math.sin(el)),
       tgt, None, lens=42, sun_rot=(r(50), 0, r(-60)), ry=int(RES*0.66))
