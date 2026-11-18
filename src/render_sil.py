# Silhouette renders at a known metric scale (exec'd at the end of build.py in sil mode, or standalone on a .blend)
import bpy, math, os, json
from mathutils import Vector
SIL_DIR = os.environ.get("SIL_DIR", os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else ".", "sil"))
os.makedirs(SIL_DIR, exist_ok=True)
MPP = float(os.environ.get("SIL_MPP", "0.2"))           # metres per pixel
FW, FH_ = 200.0, 100.0; ZC = FH_/2 - 2.0                 # frame (m); ground 2 m above bottom edge
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type == 'LIGHT' or (o.type == 'MESH' and o.get("role") in ("cut",)): o.hide_render = True
    if o.name.startswith("GroundSlab") or o.name.startswith("Plaza"): o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (0, 0, 0)
sc.render.film_transparent = True
sc.render.resolution_x = int(FW/MPP); sc.render.resolution_y = int(FH_/MPP); sc.render.resolution_percentage = 100
cam = bpy.data.objects.get("SilCam") or bpy.data.objects.new("SilCam", bpy.data.cameras.new("SilCam"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = FW; cam.data.clip_end = 2000
D = 500
views = {"front": ((0, -D, ZC), (math.pi/2, 0, 0)), "rear": ((0, D, ZC), (math.pi/2, 0, math.pi)),
         "left": ((D, 0, ZC), (math.pi/2, 0, math.pi/2)), "right": ((-D, 0, ZC), (math.pi/2, 0, -math.pi/2))}
for n, (loc, rot) in views.items():
    cam.location = loc; cam.rotation_euler = rot
    sc.render.filepath = os.path.join(SIL_DIR, f"sil_{n}.png"); bpy.ops.render.render(write_still=True)
# top (roof plan): frame 170 x 170 centred
sc.render.resolution_y = int(FW/MPP)
cam.location = (0, 0, 400); cam.rotation_euler = (0, 0, 0)
sc.render.filepath = os.path.join(SIL_DIR, "sil_top.png"); bpy.ops.render.render(write_still=True)
json.dump({"mpp": MPP, "frame_w": FW, "frame_h": FH_, "ground_from_bottom_m": 2.0}, open(os.path.join(SIL_DIR, "sil_meta.json"), "w"))
print("SIL OK", SIL_DIR)
