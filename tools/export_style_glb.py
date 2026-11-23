# v14: export building_style.glb = building.blend with the "Render" look baked into plain glTF PBR materials
# (base colour, metallic/roughness, emissive) chosen by the same rules as src/render_style.py (params.json style.rules ->
# style.web). Shared window meshes keep one material, so they stay GPU instances after gltf-transform.
#   blender -b building.blend -P tools/export_style_glb.py
import bpy, os, re, json
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(HERE, "params.json"))); ST = P["style"]; WEB = ST["web"]
MATS = {}
def mat(key):
    if key in MATS: return MATS[key]
    d = WEB.get(key) or WEB["shell"]
    m = bpy.data.materials.new(f"Style_{key}"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*d["color"], 1); b.inputs["Metallic"].default_value = d.get("metal", 0.0)
    b.inputs["Roughness"].default_value = d.get("rough", 0.5)
    if d.get("estr", 0) > 0:
        b.inputs["Emission Color"].default_value = (*d["emit"], 1); b.inputs["Emission Strength"].default_value = d["estr"]
    MATS[key] = m; return m
def pick(o):
    for kind, pat, key in ST["rules"]:
        if kind == "name" and re.search(pat, o.name): return key
        if kind == "role" and (pat == "*" or o.get("role") == pat): return key
    return "shell"
seen, cnt = set(), {}
for o in bpy.data.objects:
    if o.type != 'MESH' or o.data.name in seen: continue
    seen.add(o.data.name); k = pick(o)
    if k == "windows_sparse": k = "windows_sparse" if "windows_sparse" in WEB else "windows"
    cnt[k] = cnt.get(k, 0) + 1
    if o.get("role") == "door_leaf":       # frame + recessed glazing (two slots, kept: main.js finds the frame by name)
        o.data.materials.clear(); o.data.materials.append(mat("door_frame")); o.data.materials.append(mat("glass")); continue
    n = len(o.data.materials) or 1
    o.data.materials.clear()
    if k == "deck":                        # deck fascia faces = light strip
        o.data.materials.append(mat("deck")); o.data.materials.append(mat("deck_strip"))
        for p in o.data.polygons: p.material_index = 1 if abs(p.normal.z) < 0.35 else 0
        continue
    o.data.materials.append(mat(k))
    for p in o.data.polygons: p.material_index = 0
print("STYLE GLB materials", cnt)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, "building_style.glb"), export_format='GLB', export_extras=True, export_apply=True)
print("STYLE GLB OK", os.path.getsize(os.path.join(HERE, "building_style.glb")))
