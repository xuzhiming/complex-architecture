# Web preview / 网页预览

Static three.js site (no build step). Serve this folder and open `index.html`:

```bash
python3 -m http.server 8765 --directory web   # http://localhost:8765/
```

- `index.html` + `main.js`: orbit view and walk mode (WASD, mouse look, Shift run, R/F lift up/down), capsule collision on a
  three-mesh-bvh BVH, automatic sliding doors.
- `building_opt.glb`: Meshopt-compressed, window surrounds as GPU instances (EXT_mesh_gpu_instancing).
- `spaces.json`: rooms, doors, stairs and lifts exported by the Blender build (used by the walk test hooks).
- `vendor/`: three.js r187 + three-mesh-bvh, imported through an import map with relative paths.

所有路径均为相对路径，可直接作为静态站点部署（Cloudflare Pages 等）。
