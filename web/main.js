// Building preview: orbit view + first-person walk (WASD + pointer-lock mouse look) + free fly (6-DoF, no collision, tour),
// capsule collision against a three-mesh-bvh BVH, automatic sliding doors on every door (v13: proximity + hold + lift gating), virtual lift cars.
// Blender (x,y,z) -> glTF/three (x, z, -y).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { MeshBVH } from 'three-mesh-bvh';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const Q = new URLSearchParams(location.search);
const TEST = Q.has('test');
const MODEL = Q.get('model') || './building_opt.glb';
const b2t = (x, y, z) => new THREE.Vector3(x, z, -y);

const renderer = new THREE.WebGLRenderer({ antialias: !TEST, preserveDrawingBuffer: true });
renderer.setPixelRatio(TEST ? 1 : Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
// ---- v14 style: 渲染 Render (default; blue-violet night look + bloom) / 白模 Clay (v13 white model) ----
const clayLights = new THREE.Group(), renderLights = new THREE.Group(); scene.add(clayLights, renderLights);
clayLights.add(new THREE.HemisphereLight(0xffffff, 0x80786c, 1.6));
const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(-120, 200, 160); clayLights.add(sun);
clayLights.add(new THREE.AmbientLight(0xffffff, 0.35));
const CLAY_BG = new THREE.Color(0xc9ced8), CLAY_FOG = new THREE.Fog(0xc9ced8, 250, 700);
const RENDER_FOG = new THREE.FogExp2(0x141028, 0.00145);
const RENDER_BG = (() => {             // navy sky, violet near the horizon (abstract, no city)
  const c = document.createElement('canvas'); c.width = 4; c.height = 256; const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, '#07061a'); gr.addColorStop(0.42, '#12143a'); gr.addColorStop(0.62, '#2a2158'); gr.addColorStop(0.78, '#1a2048'); gr.addColorStop(1, '#0a0818');
  g.fillStyle = gr; g.fillRect(0, 0, 4, 256); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; })();
// Coloured rig, not a single violet wash: cool sky, warm ground bounce, cyan and rose from the sides, a low gold key on the podium.
renderLights.add(new THREE.HemisphereLight(0x8aa4ff, 0x3a1848, 0.92));
renderLights.add(new THREE.AmbientLight(0x241838, 0.16));
{ const d = new THREE.DirectionalLight(0xb7c6ff, 0.4); d.position.set(-80, 160, 90); renderLights.add(d);
  const pink = new THREE.DirectionalLight(0xff4ec8, 0.72); pink.position.set(-150, 80, -20); renderLights.add(pink);
  const cyan = new THREE.DirectionalLight(0x3ec8ff, 0.86); cyan.position.set(160, 64, 16); renderLights.add(cyan);
  const gold = new THREE.DirectionalLight(0xffb15a, 0.32); gold.position.set(10, 30, -150); renderLights.add(gold);
  // soft overhead fill so saucer and bridge tops are not black mirrors; kept dim so the crescent stays the highlight
  const roofSky = new THREE.DirectionalLight(0xd5e2ff, 0.42); roofSky.position.set(-36, 260, 24); renderLights.add(roofSky);
  const roofWarm = new THREE.DirectionalLight(0xffc9a2, 0.16); roofWarm.position.set(70, 200, -90); renderLights.add(roofWarm); }
let style = (Q.get('style') || 'render') === 'clay' ? 'clay' : 'render';

const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.05, 3000);
const headlamp = new THREE.PointLight(0xfff4e0, 0, 30, 1.5); camera.add(headlamp); scene.add(camera);
camera.position.copy(b2t(-120, -170, 80));
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth / 2, innerHeight / 2), 0.22, 0.26, 0.94);   // soft coloured halo; threshold stays high so peaks do not bloom into white fog
composer.addPass(bloom); composer.addPass(new OutputPass());
function draw() { if (style === 'render') composer.render(); else renderer.render(scene, camera); }
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.target.copy(b2t(0, 0, 25)); orbit.update();

// ---------------- player ----------------
const R = 0.3, SEG = 1.0, EYE = 0.3;          // capsule radius, segment length; eye = top sphere centre + 0.3 -> 1.6 m above feet
const FEET = R + SEG;                          // feet = position.y - 1.3
const player = { pos: new THREE.Vector3(), vel: new THREE.Vector3(), yaw: 0, pitch: 0, onGround: false };
const keys = {};
let mode = 'orbit', collider = null, bvh = null, SPACES = null;
const doors = [], lifts = [];
let liftState = null;          // {lift, carY, target}
const SPEED = 4.0, GRAV = -20;
// auto doors (v13): every DoorLeaf_<id>_A/_B pair in the glb is a split double sliding glass door
const DOOR = { trigger: 2.8, flyTrigger: 3.0, openRate: 2.2, closeRate: 1.4, hold: 0.7, cell: 8 };
const doorById = new Map(), doorGrid = new Map(), activeDoors = new Set();

function feetY() { return player.pos.y - FEET; }
function setFeet(v3) { player.pos.set(v3.x, v3.y + FEET, v3.z); player.vel.set(0, 0, 0); }

// ---------------- load ----------------
const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
const [gltf, spaces] = await Promise.all([
  loader.loadAsync(MODEL),
  fetch('./spaces.json').then(r => r.json()).catch(() => null)]);
SPACES = spaces;
scene.add(gltf.scene);
scene.updateMatrixWorld(true);

function roleOf(o) { while (o) { if (o.userData && o.userData.role) return o.userData.role; o = o.parent; } return null; }
function leafRoot(o) { while (o) { if (/^DoorLeaf_/.test(o.name)) return o; o = o.parent; } return null; }

// collider: merge every solid triangle in world space (door leaves, glows and window-light planes excluded)
{
  const parts = []; let nV = 0, nI = 0;
  gltf.scene.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh) return;   // instanced facade windows (EXT_mesh_gpu_instancing) are decoration, not collision
    if (leafRoot(o)) return;
    const role = roleOf(o);
    if (role === 'plaza_glow' || role === 'window_light' || role === 'cut') return;
    parts.push(o); const g = o.geometry; nV += g.attributes.position.count; nI += g.index ? g.index.count : g.attributes.position.count;
  });
  const pos = new Float32Array(nV * 3), idx = new Uint32Array(nI); let vo = 0, io = 0; const v = new THREE.Vector3();
  for (const o of parts) {
    const g = o.geometry, p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(o.matrixWorld); pos.set([v.x, v.y, v.z], (vo + i) * 3); }
    if (g.index) for (let i = 0; i < g.index.count; i++) idx[io++] = g.index.getX(i) + vo;
    else for (let i = 0; i < p.count; i++) idx[io++] = i + vo;
    vo += p.count;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setIndex(new THREE.BufferAttribute(idx, 1));
  bvh = new MeshBVH(geo, { targetLeafSize: 12 });
  geo.boundsTree = bvh;
  collider = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, wireframe: true, visible: false }));
  collider.name = 'collider'; scene.add(collider);
  window.__colliderTris = io / 3;
}

// ---------------- v14 style materials: glb carries the Render look; Clay swaps in two shared white materials ----------------
const CLAY_M = new THREE.MeshStandardMaterial({ color: 0xc2c2bf, roughness: 0.85 });
const CLAY_G = new THREE.MeshStandardMaterial({ color: 0x9a9ca1, roughness: 0.6 });
const isGlassMat = m => /glass|Recess/i.test(m.name);
gltf.scene.traverse(o => {
  if (!o.isMesh) return;
  o.userData.matRender = o.material;
  o.userData.matClay = (isGlassMat(o.material) || roleOf(o) === 'glass' || roleOf(o) === 'window_light') ? CLAY_G : CLAY_M;
});
// One absolute paint per part. The shipped glb is still an atlas with the old hot strengths, so this
// replaces those values instead of multiplying the previous 0.70/0.85/0.65/0.40 pass. Targets match
// params.json style.web. A later export that already has these strengths is cloned and set to the same
// numbers, not scaled again. Clay materials are a separate pair and are not painted.
const LOOK = {
  crescent: { emit: 0xffd4f3, estr: 0.95 },
  crown: { emit: 0xe4d4ff, estr: 0.55 },
  windows: { emit: 0xffb45c, estr: 1.1 },
  glass: { emit: 0xffc48a, estr: 0.22 },
  rim: { emit: 0xff86d6, estr: 0.72 },
  // Roofs: the baked saucer is a near-black metal, so the top reads as a hole. These are absolute
  // slate colours (maps cleared), not another multiply. Emissive stays a faint tint, not a light panel.
  saucer: { flat: [0.24, 0.28, 0.42], metal: 0.34, rough: 0.46, emit: 0xa9c4ea, estr: 0.05 },
  roof: { flat: [0.22, 0.2, 0.36], metal: 0.36, rough: 0.5, emit: 0xc2b0e4, estr: 0.04 },
  bridge: { flat: [0.32, 0.24, 0.28], metal: 0.32, rough: 0.48, emit: 0xe4c6a8, estr: 0.05 },
  roofrib: { flat: [0.13, 0.15, 0.24], metal: 0.48, rough: 0.4 },
  ring: { emit: 0x7ee7ff, estr: 0.48, color: [1.05, 1.15, 1.55] },
  deck: { emit: 0xffe0a4, estr: 0.82 },
  podium: { emit: 0xffb888, estr: 0.07, color: [1.75, 1.4, 1.6] },
  arch: { emit: 0xffc090, estr: 0.16, color: [1.55, 1.25, 1.4] },
  tower: { color: [1.12, 1.2, 1.72] },
  shell: { color: [1.18, 1.22, 1.58] },
};
function partRole(o) {
  const ns = [];
  for (let p = o; p; p = p.parent) if (p.name) ns.push(p.name);
  const n = ns.join(' ');
  if (/DoorLeaf/.test(n)) return 'door';
  if (/Crescent/i.test(n)) return 'crescent';
  if (/Crown|Dome|Lantern/i.test(n)) return 'crown';
  if (/Window/i.test(n)) return 'windows';
  if (/Deck/i.test(n)) return 'deck';
  const self = o.name || '';
  if (/CanopyRim/i.test(self)) return 'rim';
  if (/canopy_rib/i.test(self)) return 'roofrib';
  if (/canopy/i.test(self)) return 'saucer';
  if (/_roof$/i.test(self)) return 'roof';
  if (/^Bridge\d+$/.test(self)) return 'bridge';
  if (/^Bridge\d+_(rail|posts|rib)/.test(self)) return 'roofrib';
  if (/band|Belt|Slab|_floor|Floor/i.test(n)) return 'ring';
  if (/Arch/i.test(n)) return 'arch';
  if (/Podium/i.test(n)) return 'podium';
  if (/Tower/i.test(n)) return 'tower';
  if (/[Gg]lass|Recess/.test(n)) return 'glass';
  return 'shell';
}
const paintCache = new Map();
function paintMaterial(src, role) {
  if (!src || !src.isMaterial) return src;
  const key = src.uuid + '|' + role;
  if (paintCache.has(key)) return paintCache.get(key);
  const m = src.clone();
  const spec = LOOK[role];
  if (spec) {
    if (spec.flat) {
      m.map = null; m.color.setRGB(spec.flat[0], spec.flat[1], spec.flat[2]);
      if (spec.metal !== undefined) { m.metalnessMap = null; m.metalness = spec.metal; }
      if (spec.rough !== undefined) { m.roughnessMap = null; m.roughness = spec.rough; }
    } else if (spec.color) m.color.setRGB(spec.color[0], spec.color[1], spec.color[2]);
    if (spec.emit !== undefined) {
      if (spec.flat) m.emissiveMap = null;
      m.emissive.setHex(spec.emit); m.emissiveIntensity = spec.estr;
    } else if ((src.emissiveIntensity ?? 1) >= 1.05) m.emissiveIntensity = 0.4;
  }
  paintCache.set(key, m);
  return m;
}
gltf.scene.traverse(o => {
  if (!o.isMesh || !o.userData.matRender || partRole(o) === 'door') return;
  const role = partRole(o);
  const src = o.userData.matRender;
  o.userData.matRender = Array.isArray(src) ? src.map(m => paintMaterial(m, role)) : paintMaterial(src, role);
});
// emissive pastel plaza rings in front of the arch (render look only)
const plazaFx = new THREE.Group(); scene.add(plazaFx);
{
  const fy = (SPACES && SPACES.doors.find(d => d.type === 'open')) ? SPACES.doors.find(d => d.type === 'open').center[1] : -45.5;
  const c = b2t(0, fy - 20.8, 0.06);
  for (const [r0, r1, k] of [[7.8, 8.3, 0], [17.5, 18.6, 1], [24.7, 25.3, 2], [31.2, 31.7, 3]]) {
    const g = new THREE.RingGeometry(r0, r1, 160, 1); g.rotateX(-Math.PI / 2);
    const col = new Float32Array(g.attributes.position.count * 3), P3 = g.attributes.position, cc = new THREE.Color();
    for (let i = 0; i < P3.count; i++) {      // one hue per ring: gold, rose, violet, cyan
      const a = (Math.atan2(P3.getZ(i), P3.getX(i)) / (2 * Math.PI) + 1) % 1;
      cc.setHSL([0.1, 0.92, 0.78, 0.54][k] + (a - 0.5) * 0.03, 0.72, 0.46); col.set([cc.r, cc.g, cc.b], i * 3);
    }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, toneMapped: true, fog: false }));
    m.position.copy(c); m.scale.x = 1.31; plazaFx.add(m);
  }
  // soft additive glows: warm starburst in the arch, pastel halo around the crown
  const glowTex = (() => { const cv = document.createElement('canvas'); cv.width = cv.height = 128; const g = cv.getContext('2d');
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128); const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t; })();
  const sprite = (col, size, pos, op) => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: col, blending: THREE.AdditiveBlending,
    depthWrite: false, transparent: true, opacity: op, fog: false })); s.scale.set(size, size, 1); s.position.copy(pos); plazaFx.add(s); return s; };
  sprite(0xffc080, 12, b2t(0, fy + 8, 6), 0.3);
  sprite(0xe4d2ff, 34, b2t(13.5, 40, 76), 0.13); sprite(0xffb0e4, 16, b2t(4, 38, 72), 0.1);
  const glow = (hex, inten, dist, pos) => { const L = new THREE.PointLight(hex, inten, dist, 2); L.position.copy(pos); plazaFx.add(L); };
  glow(0xffb060, 64, 52, b2t(0, fy + 6, 6));          // warm arch
  glow(0xc9a6ff, 44, 68, b2t(13.5, 40, 78));          // violet crown
  glow(0xffc48a, 96, 36, b2t(0, 2, 5));               // low courtyard, so the arcade is not black
  glow(0xffd0a0, 70, 42, b2t(0, 2, 16));              // mid courtyard
  glow(0x6aa8ff, 58, 58, b2t(0, 12, 30));             // cool light higher in the court
  glow(0xffb070, 70, 68, b2t(0, -58, 9));             // podium front
  glow(0xff78c8, 32, 48, b2t(-58, 16, 26));           // west rose
  glow(0x49d0ff, 36, 52, b2t(62, 6, 24));             // east cyan
  glow(0xffd090, 26, 34, b2t(13.5, 40, 48));          // warm light between the saucers
}
function headlampFor(m) { return (m === 'walk' ? 25 : (m === 'fly' ? 12 : 0)) * (style === 'render' ? 0.18 : 1); }
function applyStyle(s) {
  style = s;
  const R = s === 'render';
  gltf.scene.traverse(o => { if (o.isMesh && o.userData.matRender) o.material = R ? o.userData.matRender : o.userData.matClay; });
  scene.background = R ? RENDER_BG : CLAY_BG; scene.fog = R ? RENDER_FOG : CLAY_FOG;
  clayLights.visible = !R; renderLights.visible = R; plazaFx.visible = R;
  renderer.toneMappingExposure = R ? 0.9 : 1.0;
  headlamp.intensity = headlampFor(mode);
  const b = document.getElementById('bStyle'); if (b) b.textContent = R ? '风格 Style: 渲染 Render' : '风格 Style: 白模 Clay';
}

// ---------------- auto doors (v13) ----------------
// Leaves are exported with extras: door_id, door_type, leaf (A|B), slide (open offset), slide_axis, width, height,
// center, normal, lift_id/level. Leaf meshes are baked in world space, so the closed position is the node position.
const gkey = (i, j) => i + ',' + j;
const easeIO = t => t * t * (3 - 2 * t);
gltf.scene.traverse(o => {
  if (!/^DoorLeaf_/.test(o.name) || leafRoot(o.parent)) return;
  const u = o.userData, id = u.door_id || o.name.replace(/^DoorLeaf_/, '').replace(/_[AB]$/, '');
  let d = doorById.get(id);
  if (!d) {
    const c = u.center || [0, 0, 0], n = u.normal || [0, 1, 0];
    d = { id, type: u.door_type || 'door', leaves: [], t: 0, s: 0, hold: 0, want: false, opened: 0, closedAfter: 0,
          w: u.width || 1.8, h: u.height || 2.4, floorY: c[2], centre: b2t(c[0], c[1], c[2] + 1.2), base: b2t(c[0], c[1], c[2]),
          n3: new THREE.Vector3(n[0], 0, -n[1]).normalize(), lift: u.lift_id || null, level: u.level ?? c[2], mats: [] };
    d.tg3 = new THREE.Vector3(-d.n3.z, 0, d.n3.x);
    doorById.set(id, d); doors.push(d);
  }
  const sl = u.slide || [1, 0, 0], slideW = new THREE.Vector3(sl[0], sl[2], -sl[1]);
  const inv = new THREE.Matrix4().copy(o.parent.matrixWorld).invert();
  const box = new THREE.Box3().setFromObject(o);
  // per-door material clones so the rim glow can follow the door state
  // (only the clay frame glows: a faint cool rim strip while the door is active; the recessed glazing stays dark)
  o.traverse(m => { if (m.isMesh && !isGlassMat(m.userData.matRender || m.material)) {
    for (const k of ['matRender', 'matClay']) { const c = m.userData[k].clone(); c.emissive = new THREE.Color(0x8ccaff); c.emissiveIntensity = 0; m.userData[k] = c; d.mats.push(c); }
    m.material = m.userData.matRender; } });
  d.leaves.push({ obj: o, side: u.leaf || 'A', closed: o.position.clone(), slideW, slideL: slideW.clone().applyMatrix3(new THREE.Matrix3().setFromMatrix4(inv)),
                  c0: box.getCenter(new THREE.Vector3()), hw: slideW.length() / 2, ht: 0.06 });
});
for (const d of doors) {        // spatial hash: door -> 8 m cell
  const k = gkey(Math.floor(d.base.x / DOOR.cell), Math.floor(d.base.z / DOOR.cell));
  if (!doorGrid.has(k)) doorGrid.set(k, []); doorGrid.get(k).push(d);
}
function doorsAround(p, out = []) {
  out.length = 0; const ci = Math.floor(p.x / DOOR.cell), cj = Math.floor(p.z / DOOR.cell);
  for (let i = ci - 1; i <= ci + 1; i++) for (let j = cj - 1; j <= cj + 1; j++) { const a = doorGrid.get(gkey(i, j)); if (a) for (const d of a) out.push(d); }
  return out;
}
if (SPACES) for (const L of SPACES.lifts) {
  const [x0, y0, x1, y1] = L.shaft;
  lifts.push({ id: L.id, x0, x1, z0: -y1, z1: -y0, levels: L.levels, car: L.levels[0], target: L.levels[0], doors: [] });   // three x/z bounds
}
const liftById = new Map(lifts.map(L => [L.id, L]));
for (const d of doors) if (d.lift && liftById.has(d.lift)) liftById.get(d.lift).doors.push(d);
document.getElementById('load').remove();
applyStyle(style);
document.getElementById('bStyle').onclick = () => applyStyle(style === 'render' ? 'clay' : 'render');

// ---------------- helpers ----------------
const ray = new THREE.Ray();
function castFirst(o, d, far) {
  ray.origin.copy(o); ray.direction.copy(d).normalize();
  const h = bvh.raycastFirst(ray, THREE.DoubleSide);
  return (h && h.distance <= far) ? h : null;
}
function inLift(p) {
  for (const L of lifts) if (p.x > L.x0 + 0.15 && p.x < L.x1 - 0.15 && p.z > L.z0 + 0.15 && p.z < L.z1 - 0.15) return L;
  return null;
}

// ---------------- character update (three-mesh-bvh capsule approach) ----------------
const seg = new THREE.Line3(), tBox = new THREE.Box3(), tv = new THREE.Vector3(), tv2 = new THREE.Vector3();
const fwd = new THREE.Vector3(), right = new THREE.Vector3(), mv = new THREE.Vector3();
function step(dt) {
  // input
  fwd.set(-Math.sin(player.yaw), 0, -Math.cos(player.yaw)); right.set(-fwd.z, 0, fwd.x);
  mv.set(0, 0, 0);
  if (keys.KeyW) mv.add(fwd); if (keys.KeyS) mv.sub(fwd); if (keys.KeyD) mv.add(right); if (keys.KeyA) mv.sub(right);
  if (mv.lengthSq() > 0) mv.normalize().multiplyScalar(SPEED * (keys.ShiftLeft ? 1.8 : 1));
  // gravity
  if (player.onGround) player.vel.y = GRAV * dt; else player.vel.y += GRAV * dt;
  player.pos.addScaledVector(player.vel, dt);
  player.pos.addScaledVector(mv, dt);
  // step-up assist for stair risers (<= 0.4 m)
  if (mv.lengthSq() > 0 && player.onGround) {
    const probe = tv.copy(player.pos).addScaledVector(mv.clone().normalize(), R + 0.12); probe.y = feetY() + 0.45;
    const h = castFirst(probe, tv2.set(0, -1, 0), 0.5);
    if (h) { const rise = h.point.y - feetY(); if (rise > 0.03 && rise < 0.4) player.pos.y += rise + 0.005; }
  }
  // lift car floor
  const L = inLift(player.pos);
  if (L) {
    if (!liftState || liftState.lift !== L) {
      let lv = L.levels[0]; for (const z of L.levels) if (z <= feetY() + 0.4) lv = z;
      L.car = L.target = lv; liftState = { lift: L, carY: lv, target: lv };
    }
    L.target = liftState.target;
    const d = liftState.target - liftState.carY;
    if (!liftDoorsBusy(L)) liftState.carY += Math.sign(d) * Math.min(Math.abs(d), 3.0 * dt);   // car leaves only once its doors are shut
    L.car = liftState.carY;
    if (feetY() < liftState.carY + 0.02 || Math.abs(d) > 1e-4) { player.pos.y = liftState.carY + FEET; player.vel.y = 0; player.onGround = true; }
  } else liftState = null;
  // collision
  seg.start.copy(player.pos); seg.end.copy(player.pos).y -= SEG;
  tBox.makeEmpty(); tBox.expandByPoint(seg.start); tBox.expandByPoint(seg.end); tBox.min.addScalar(-R); tBox.max.addScalar(R);
  bvh.shapecast({
    intersectsBounds: b => b.intersectsBox(tBox),
    intersectsTriangle: tri => {
      const d = tri.closestPointToSegment(seg, tv, tv2);
      if (d < R) { const depth = R - d; const dir = tv2.sub(tv).normalize(); seg.start.addScaledVector(dir, depth); seg.end.addScaledVector(dir, depth); }
    }
  });
  const delta = tv.subVectors(seg.start, player.pos);
  const grounded = delta.y > Math.abs(dt * player.vel.y * 0.25);
  if (!(L && liftState)) player.onGround = grounded; else player.onGround = true;
  const off = Math.max(0, delta.length() - 1e-5); delta.normalize().multiplyScalar(off); player.pos.add(delta);
  if (!player.onGround) { delta.normalize(); player.vel.addScaledVector(delta, -delta.dot(player.vel)); } else player.vel.set(0, 0, 0);
  if (player.pos.y < -20) setFeet(b2t(0, -60, 0));
  // door leaves are solid in their *current* position (closed = blocked, open = slid into the wall pockets)
  collideLeaves();
}

// ---------------- auto-door update (per frame, spatial-hash candidates only; no raycasts) ----------------
const _cand = [], _near = [];
function liftDoorsBusy(L) { for (const d of L.doors) if (d.t > 0.01 && Math.abs(d.level - L.car) < 0.05) return true; return false; }
function updateDoors(dt, probe, isFly) {
  const cand = probe ? doorsAround(probe, _cand) : _cand.splice(0);
  for (const d of activeDoors) if (!cand.includes(d)) cand.push(d);
  const now = performance.now() / 1000;
  // hall call: only the nearest lift door in range calls a car (a bank of three lifts does not all come at once)
  let callDoor = null, callD = 1e9;
  if (probe) for (const d of cand) if (d.lift) { const dd = probe.distanceTo(d.centre); if (dd < callD) { callD = dd; callDoor = d; } }
  for (const d of cand) {
    let near = false;
    if (probe) {
      const hz = Math.hypot(probe.x - d.base.x, probe.z - d.base.z);
      if (isFly) near = probe.distanceTo(d.centre) < DOOR.flyTrigger;
      else { const fy = probe.y - FEET; near = hz < DOOR.trigger && fy > d.floorY - 1.0 && fy < d.floorY + 1.6; }
    }
    let want = near;
    if (d.lift) {                                       // lift doors: open only while the car stands at this floor
      const L = liftById.get(d.lift);
      const here = L && Math.abs(L.car - d.level) < 0.02 && Math.abs(L.target - d.level) < 0.02;
      near = near && d === callDoor;
      if (near && L && !here && Math.abs(L.car - L.target) < 1e-3 && !(liftState && liftState.lift === L)) L.target = d.level;   // call the car
      want = near && here;
      if (!here) d.hold = 0;
    }
    if (want && !d.want) d.trigAt = now;
    if (want) d.hold = DOOR.hold; else d.hold = Math.max(0, d.hold - dt);
    const open = want || d.hold > 0;
    const t0 = d.t;
    d.t = THREE.MathUtils.clamp(d.t + (open ? DOOR.openRate : -DOOR.closeRate) * dt, 0, 1);
    if (d.t >= 0.999 && t0 < 0.999) { d.opened = now; d.openDur = now - (d.trigAt ?? now); }
    if (d.t <= 0 && t0 > 0) d.closedAfter = now;
    d.want = open; d.s = easeIO(d.t);
    for (const lf of d.leaves) lf.obj.position.copy(lf.closed).addScaledVector(lf.slideL, d.s);
    const glow = open ? 0.06 + 0.16 * d.s : 0.22 * d.s;
    for (const m of d.mats) m.emissiveIntensity = glow;
    if (d.t > 0 || d.hold > 0) activeDoors.add(d); else activeDoors.delete(d);
  }
  // idle lift cars travel to their call level (3 m/s) once their doors are shut
  for (const L of lifts) {
    if (liftState && liftState.lift === L) continue;
    const dd = L.target - L.car;
    if (Math.abs(dd) > 1e-4 && !liftDoorsBusy(L)) L.car += Math.sign(dd) * Math.min(Math.abs(dd), 3.0 * dt);
  }
}
const _lp = new THREE.Vector3();
function collideLeaves() {
  const fy = feetY(), top = fy + FEET + R;
  for (const d of doorsAround(player.pos, _near)) {
    if (d.s > 0.999) continue;
    if (fy > d.floorY + d.h - 0.05 || top < d.floorY + 0.02) continue;
    for (const lf of d.leaves) {
      _lp.copy(lf.c0).addScaledVector(lf.slideW, d.s);           // current leaf centre (world)
      const rx = player.pos.x - _lp.x, rz = player.pos.z - _lp.z;
      const u = rx * d.tg3.x + rz * d.tg3.z, v = rx * d.n3.x + rz * d.n3.z;
      const cu = THREE.MathUtils.clamp(u, -lf.hw, lf.hw), cv = THREE.MathUtils.clamp(v, -lf.ht, lf.ht);
      const du = u - cu, dv = v - cv, dist = Math.hypot(du, dv);
      if (dist >= R) continue;
      let pu, pv;
      if (dist > 1e-6) { pu = du / dist * (R - dist); pv = dv / dist * (R - dist); }
      else { pu = 0; pv = (v >= 0 ? 1 : -1) * (R + lf.ht - Math.abs(v)); }   // centre inside the leaf: push out through the face
      player.pos.x += d.tg3.x * pu + d.n3.x * pv; player.pos.z += d.tg3.z * pu + d.n3.z * pv;
      window.__leafBlocks = (window.__leafBlocks || 0) + 1;
    }
  }
}

// ---------------- modes / input ----------------
const hud = document.getElementById('hud'), cross = document.getElementById('cross');
function setMode(m) {
  const prev = mode;
  if (m === 'fly' && prev !== 'fly') enterFly();
  if (m === 'walk' && prev === 'fly') dropToFloor();
  if (m === 'orbit' && prev === 'fly') { const d = new THREE.Vector3(); camera.getWorldDirection(d); orbit.target.copy(camera.position).addScaledVector(d, 60); }
  if (m !== 'fly') tour.on = false;
  mode = m;
  for (const [id, mm] of [['bOrbit', 'orbit'], ['bWalk', 'walk'], ['bFly', 'fly']]) document.getElementById(id).classList.toggle('on', m === mm);
  document.getElementById('flyBar').style.display = m === 'fly' ? 'flex' : 'none';
  document.getElementById('touchFly').style.display = (m === 'fly' && TOUCH) ? 'block' : 'none';
  orbit.enabled = m === 'orbit'; headlamp.intensity = headlampFor(m); cross.style.display = m !== 'orbit' ? 'block' : 'none';
  if (m === 'walk' && player.pos.lengthSq() === 0) { setFeet(b2t(0, -62, 0)); player.yaw = 0; }
  if (m === 'orbit' && document.pointerLockElement) document.exitPointerLock?.();
}
document.getElementById('bOrbit').onclick = () => { document.exitPointerLock?.(); setMode('orbit'); };
document.getElementById('bWalk').onclick = () => setMode('walk');
document.getElementById('bFly').onclick = () => setMode('fly');
renderer.domElement.addEventListener('click', () => { if ((mode === 'walk' || mode === 'fly') && !TEST && !TOUCH) renderer.domElement.requestPointerLock?.(); });
document.addEventListener('mousemove', e => {
  if (document.pointerLockElement !== renderer.domElement) return;
  if (mode === 'walk') { player.yaw -= e.movementX * 0.0022; player.pitch = THREE.MathUtils.clamp(player.pitch - e.movementY * 0.0022, -1.4, 1.4); }
  else if (mode === 'fly') { fly.yaw -= e.movementX * 0.0022; fly.pitch = THREE.MathUtils.clamp(fly.pitch - e.movementY * 0.0022, -1.55, 1.55); tour.on = false; }
});
addEventListener('keydown', e => {
  keys[e.code] = true;
  if (e.code === 'Tab') { e.preventDefault(); setMode(mode === 'walk' ? 'orbit' : 'walk'); }
  if (e.code === 'KeyV' && !e.repeat) applyStyle(style === 'render' ? 'clay' : 'render');   // 风格 Style toggle
  // F toggles fly (inside a lift car F keeps its old meaning: lift down)
  if (e.code === 'KeyF' && !e.repeat && !(mode === 'walk' && liftState)) { setMode(mode === 'fly' ? (flyFrom === 'walk' ? 'walk' : 'orbit') : 'fly'); return; }
  if (mode === 'fly') {
    if (e.code === 'Space' || e.code.startsWith('Control')) e.preventDefault();
    if (e.code === 'Equal' || e.code === 'NumpadAdd') fly.base = Math.min(200, fly.base * 1.25);
    if (e.code === 'Minus' || e.code === 'NumpadSubtract') fly.base = Math.max(1, fly.base / 1.25);
    if (e.code === 'KeyT' && !e.repeat) toggleTour();
    if (/^Digit[1-5]$/.test(e.code)) goPreset(+e.code.slice(5) - 1);
    if (/^Key[WASDQEC]$/.test(e.code) || e.code === 'Space') tour.on = false;
  }
  if (liftState && (e.code === 'KeyR' || e.code === 'KeyF')) {
    const lv = liftState.lift.levels; let i = lv.indexOf(liftState.target);
    i = THREE.MathUtils.clamp(i + (e.code === 'KeyR' ? 1 : -1), 0, lv.length - 1); liftState.target = lv[i];
  }
});
addEventListener('keyup', e => { keys[e.code] = false; });
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight); bloom.resolution.set(innerWidth / 2, innerHeight / 2); });

// ---------------- fly mode: free 6-DoF camera, no gravity, no collision ----------------
const TOUCH = matchMedia('(pointer: coarse)').matches || Q.has('touch');
const fly = { pos: new THREE.Vector3(), vel: new THREE.Vector3(), yaw: 0, pitch: 0, base: 12 };
let flyFrom = 'orbit';
const fv = new THREE.Vector3(), fr = new THREE.Vector3(), fwish = new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0), fE = new THREE.Euler();
const touchMove = { f: 0, s: 0, u: 0 };
function enterFly() {
  flyFrom = mode;
  if (mode === 'walk') syncCamera(); else orbit.update();
  fly.pos.copy(camera.position); fly.vel.set(0, 0, 0);
  const e = new THREE.Euler().setFromQuaternion(camera.quaternion, 'YXZ'); fly.yaw = e.y; fly.pitch = e.x;
}
function flyStep(dt) {
  fv.set(0, 0, -1).applyEuler(fE.set(fly.pitch, fly.yaw, 0, 'YXZ'));     // view direction (incl. pitch)
  fr.set(Math.cos(fly.yaw), 0, -Math.sin(fly.yaw));                         // right (horizontal)
  fwish.set(0, 0, 0);
  if (keys.KeyW) fwish.add(fv); if (keys.KeyS) fwish.sub(fv); if (keys.KeyD) fwish.add(fr); if (keys.KeyA) fwish.sub(fr);
  if (keys.Space || keys.KeyE) fwish.add(UP); if (keys.KeyQ || keys.KeyC) fwish.sub(UP);
  fwish.addScaledVector(fv, touchMove.f).addScaledVector(fr, touchMove.s).addScaledVector(UP, touchMove.u);
  if (fwish.lengthSq() > 1) fwish.normalize();
  const sp = fly.base * ((keys.ShiftLeft || keys.ShiftRight) ? 3 : 1);
  // smooth acceleration / damping: the velocity eases toward the wished velocity (time constant 0.18 s)
  fly.vel.lerp(fwish.multiplyScalar(sp), 1 - Math.exp(-dt / 0.18));
  fly.pos.addScaledVector(fly.vel, dt);
}
function flyCamera() { camera.position.copy(fly.pos); camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ'); }
// fly -> walk: drop straight down onto the first walkable floor with head room (same BVH raycast as the walk code);
// if none is found (e.g. over open ground outside), fall back to the forecourt spawn.
function dropToFloor() {
  let h = castFirst(fly.pos.clone(), new THREE.Vector3(0, -1, 0), 500);
  for (let i = 0; i < 6 && h; i++) {
    const n = h.face ? h.face.normal : null;
    const up = castFirst(h.point.clone().add(new THREE.Vector3(0, 0.05, 0)), new THREE.Vector3(0, 1, 0), 2.0);
    if (!up && (!n || Math.abs(n.y) > 0.7)) { setFeet(h.point.clone().add(new THREE.Vector3(0, 0.05, 0))); player.yaw = fly.yaw; player.pitch = 0; player.onGround = false; return true; }
    h = castFirst(h.point.clone().add(new THREE.Vector3(0, -0.05, 0)), new THREE.Vector3(0, -1, 0), 500);
  }
  setFeet(b2t(0, -62, 0)); player.yaw = 0; player.pitch = 0; return false;
}
// presets & tour (Blender coordinates)
const T_C = SPACES ? SPACES.spaces.courtyard.probe : [0, 2, 0];
const _pd = SPACES && SPACES.doors.find(d => [d.a, d.b].includes('forecourt') && [d.a, d.b].includes('portal_tunnel'));
const PORTAL = _pd ? _pd.center : [0, -45.5, 0];
const TOWER = [13.5, 40, 65.6];
const PRESETS = [
  ['前广场 Forecourt', [0, PORTAL[1] - 65, 9], [0, PORTAL[1], 10]],
  ['拱门 Arch', [0, PORTAL[1] - 7, 5], [0, T_C[1], 6]],
  ['庭院 Courtyard', [T_C[0] - 14, T_C[1] - 10, 6], [TOWER[0], TOWER[1], 45]],
  ['冠顶 Crown', [TOWER[0] + 55, TOWER[1] - 62, 92], [TOWER[0] - 8, TOWER[1] - 2, 66]],
  ['鸟瞰 Aerial', [-150, -175, 115], [0, 0, 25]]];
function lookFrom(p, t) {
  const a = b2t(...p), b = b2t(...t); fly.pos.copy(a); fly.vel.set(0, 0, 0);
  const d = b.sub(a).normalize(); fly.yaw = Math.atan2(-d.x, -d.z); fly.pitch = Math.asin(THREE.MathUtils.clamp(d.y, -1, 1));
}
function goPreset(i) { if (mode !== 'fly') setMode('fly'); tour.on = false; lookFrom(...PRESETS[i].slice(1)); }
// auto tour: closed Catmull-Rom loop: aerial -> forecourt -> through the arch and tunnel -> courtyard -> up past the tower -> over the crown -> around
const TOUR_PTS = [[-150, -175, 70], [-40, PORTAL[1] - 70, 25], [0, PORTAL[1] - 25, 6], [0, PORTAL[1] - 2, 5], [0, PORTAL[1] + 20, 5],
  [T_C[0], T_C[1] - 12, 7], [T_C[0] + 6, T_C[1] + 6, 20], [TOWER[0] - 35, TOWER[1] - 28, 62], [TOWER[0] - 14, TOWER[1] - 12, 104],
  [TOWER[0] + 35, TOWER[1] + 4, 100], [TOWER[0] + 70, TOWER[1] - 20, 75], [130, -60, 70], [60, -170, 60]];
const tourCurve = new THREE.CatmullRomCurve3(TOUR_PTS.map(p => b2t(...p)), true, 'centripetal');
const tour = { on: false, u: 0, dur: 75 };
const TOUR_LOOK = b2t(TOWER[0], TOWER[1], 55);
function toggleTour() { if (mode !== 'fly') setMode('fly'); tour.on = !tour.on; }
function tourPose(u, k) {
  const p = tourCurve.getPointAt(u), q = tourCurve.getPointAt((u + 0.012) % 1);
  fly.pos.copy(p); fly.vel.set(0, 0, 0);
  // look ahead along the path; when high up, swing the view toward the crown so the tour frames the building
  const ahead = p.clone().addScaledVector(q.sub(p).normalize(), 30);
  const w = THREE.MathUtils.smoothstep(p.y, 25, 60) * 0.85, look = ahead.lerp(TOUR_LOOK, w);
  const d = look.sub(p).normalize(); const yaw = Math.atan2(-d.x, -d.z), pitch = Math.asin(THREE.MathUtils.clamp(d.y, -1, 1));
  let dy = yaw - fly.yaw; dy = Math.atan2(Math.sin(dy), Math.cos(dy));
  fly.yaw += dy * k; fly.pitch += (pitch - fly.pitch) * k;
}
function tourStep(dt) { tour.u = (tour.u + dt / tour.dur) % 1; tourPose(tour.u, 1 - Math.exp(-dt / 0.5)); }
// fly UI: preset buttons + tour
{
  const fb = document.getElementById('flyBar');
  PRESETS.forEach((p, i) => { const b = document.createElement('button'); b.textContent = `${i + 1} ${p[0]}`; b.onclick = () => goPreset(i); fb.appendChild(b); });
  const tb = document.createElement('button'); tb.id = 'bTour'; tb.textContent = 'T 巡航 Tour'; tb.onclick = toggleTour; fb.appendChild(tb);
}
renderer.domElement.addEventListener('wheel', e => {
  if (mode !== 'fly') return; e.preventDefault(); fly.base = THREE.MathUtils.clamp(fly.base * (e.deltaY < 0 ? 1.15 : 1 / 1.15), 1, 200);
}, { passive: false });
// touch: one finger drags to look, two fingers drag to move (up/down = forward/back, left/right = strafe); the round buttons rise/sink
{
  let last1 = null, last2 = null;
  const el = renderer.domElement;
  el.addEventListener('touchstart', e => { if (mode !== 'fly') return; e.preventDefault(); tour.on = false;
    if (e.touches.length === 1) { last1 = [e.touches[0].clientX, e.touches[0].clientY]; last2 = null; }
    else { last2 = [(e.touches[0].clientX + e.touches[1].clientX) / 2, (e.touches[0].clientY + e.touches[1].clientY) / 2]; last1 = null; } }, { passive: false });
  el.addEventListener('touchmove', e => { if (mode !== 'fly') return; e.preventDefault();
    if (e.touches.length === 1 && last1) { const x = e.touches[0].clientX, y = e.touches[0].clientY;
      fly.yaw += (x - last1[0]) * 0.005; fly.pitch = THREE.MathUtils.clamp(fly.pitch + (y - last1[1]) * 0.005, -1.55, 1.55); last1 = [x, y]; }
    else if (e.touches.length >= 2 && last2) { const x = (e.touches[0].clientX + e.touches[1].clientX) / 2, y = (e.touches[0].clientY + e.touches[1].clientY) / 2;
      touchMove.f = THREE.MathUtils.clamp(-(y - last2[1]) / 60, -1, 1); touchMove.s = THREE.MathUtils.clamp((x - last2[0]) / 60, -1, 1); } }, { passive: false });
  el.addEventListener('touchend', e => { if (e.touches.length < 2) { touchMove.f = touchMove.s = 0; last2 = null; }
    last1 = e.touches.length === 1 ? [e.touches[0].clientX, e.touches[0].clientY] : null; });
  const hold = (id, v) => { const b = document.getElementById(id);
    b.addEventListener('pointerdown', e => { e.preventDefault(); touchMove.u = v; });
    for (const ev of ['pointerup', 'pointerleave', 'pointercancel']) b.addEventListener(ev, () => { touchMove.u = 0; }); };
  hold('tUp', 1); hold('tDown', -1);
}

function syncCamera() {
  camera.position.set(player.pos.x, player.pos.y + EYE, player.pos.z);
  camera.rotation.set(player.pitch, player.yaw, 0, 'YXZ');
}
function hudText() {
  const f = feetY();
  const b = { x: player.pos.x.toFixed(1), y: (-player.pos.z).toFixed(1), z: f.toFixed(2) };
  if (mode === 'fly') {
    const p = camera.position;
    return `飞行 FLY  ·  ${TOUCH ? '单指拖动环视 · 双指拖动前进/平移 · ▲▼ 升降' : '点击锁定鼠标环视 (Esc 释放) · WASD 沿视线移动 · Space/E 上升 · Q/C 下降 · Shift 加速'}<br>` +
      `滚轮 / + − 调速 · 1–5 预设视点 · T 巡航${tour.on ? ' (进行中 on)' : ''} · F 退出 exit<br>` +
      `speed ${fly.base.toFixed(1)} m/s${(keys.ShiftLeft || keys.ShiftRight) ? ' ×3' : ''} · now ${fly.vel.length().toFixed(1)} m/s · x ${p.x.toFixed(1)}  y ${(-p.z).toFixed(1)}  z ${p.y.toFixed(1)} m · no collision 无碰撞`;
  }
  return mode === 'walk'
    ? `WALK  ·  WASD move · mouse look (click) · Shift run · Tab orbit · F fly 飞行<br>${liftState ? `in lift ${liftState.lift.id} · R up / F down · level ${liftState.target}` : ''}<br>x ${b.x}  y ${b.y}  floor z ${b.z} m · 自动门 auto doors ${doors.length} (active ${activeDoors.size})`
    : `ORBIT  ·  drag rotate · wheel zoom · right-drag pan · Tab / button = walk mode · F fly 飞行 · V 风格 Render/Clay<br>collider triangles: ${window.__colliderTris} · 自动门 auto doors: ${doors.length}`;
}

let last = performance.now(), renderEvery = TEST ? 0 : 1;
function loop(now) {
  const dt = Math.min((now - last) / 1000, 0.1); last = now;
  if (mode === 'walk') { const n = Math.ceil(dt / 0.01); for (let i = 0; i < n; i++) step(dt / n); syncCamera(); }
  else if (mode === 'fly') { if (tour.on) tourStep(dt); else flyStep(dt); flyCamera(); document.getElementById('bTour').classList.toggle('on', tour.on); }
  else orbit.update();
  updateDoors(dt, mode === 'walk' ? player.pos : (mode === 'fly' ? camera.position : null), mode === 'fly');
  hud.innerHTML = hudText();
  if (renderEvery) draw();
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

// ---------------- test hooks (used by walk_test.py) ----------------
window.__walk = {
  ready: true,
  setMode, render() { if (mode === 'walk') syncCamera(); else if (mode === 'fly') flyCamera(); draw(); },
  style(s) { if (s) applyStyle(s); return style; },
  mode() { return mode; },
  teleport(x, y, z, yaw = 0) { setMode('walk'); setFeet(b2t(x, y, z)); player.yaw = yaw; player.onGround = false; },
  setYaw(y) { player.yaw = y; }, setPitch(p) { player.pitch = p; },
  state() { return { x: player.pos.x, y: -player.pos.z, z: feetY(), yaw: player.yaw, onGround: player.onGround,
                     lift: liftState ? { id: liftState.lift.id, car: liftState.carY, target: liftState.target } : null }; },
  doorsNear(r = 4) { return doors.filter(d => Math.hypot(player.pos.x - d.base.x, player.pos.z - d.base.z) < r && Math.abs(feetY() - d.floorY) < 2.5).map(d => ({ id: d.id, open: d.t, type: d.type })); },
  doorCount() { return doors.length; },
  // v13 auto-door hooks
  doorList() { return doors.map(d => ({ id: d.id, type: d.type, leaves: d.leaves.map(l => l.obj.name), sides: d.leaves.map(l => l.side),
                                        slide: d.leaves.map(l => l.slideW.length()), lift: d.lift, level: d.level, w: d.w, h: d.h,
                                        animated: d.leaves.every(l => l.obj.isObject3D && !l.obj.isInstancedMesh && !!l.obj.parent) })); },
  door(id) { const d = doorById.get(id); if (!d) return null;
             return { id, t: d.t, s: d.s, hold: d.hold, want: d.want, opened: d.opened, closedAfter: d.closedAfter, active: activeDoors.has(d),
                      openDur: d.openDur ?? null, gap: d.s * (d.w - 0.06) + 0.01, target: d.lift ? liftById.get(d.lift).target : null,
                      leafOffset: d.leaves.map(l => l.obj.position.distanceTo(l.closed)), x: d.base.x, y: -d.base.z, z: d.floorY,
                      nx: d.n3.x, ny: -d.n3.z, lift: d.lift, car: d.lift ? liftById.get(d.lift).car : null }; },
  activeDoors() { return [...activeDoors].map(d => d.id); },
  leafBlocks() { return window.__leafBlocks || 0; },
  lift(id) { const L = liftById.get(id); return L ? { id, car: L.car, target: L.target, levels: L.levels } : null; },
  // segment test in Blender coords: returns hit distance or null
  raySegment(a, b) { const A = b2t(...a), B = b2t(...b); const d = B.clone().sub(A); const L = d.length(); if (L < 1e-6) return null;
                     const h = castFirst(A, d, L); return h ? h.distance : null; },
  liftTo(level) { if (liftState) { liftState.target = level; return true; } return false; },
};

// ---------------- fly test hooks (used by walk/fly_test.py); Blender coords ----------------
window.__fly = {
  enter() { setMode('fly'); return this.state(); },
  setPose(x, y, z, yaw = 0, pitch = 0) { setMode('fly'); tour.on = false; fly.pos.copy(b2t(x, y, z)); fly.vel.set(0, 0, 0); fly.yaw = yaw; fly.pitch = pitch; flyCamera(); },
  lookFrom(p, t) { setMode('fly'); tour.on = false; lookFrom(p, t); flyCamera(); },
  preset(i) { goPreset(i); flyCamera(); return PRESETS[i][0]; },
  tour(on = true, u = null) { setMode('fly'); if (u !== null) tour.u = u; tour.on = on; },
  tourAt(u) { setMode('fly'); tour.on = false; tour.u = u; tourPose(u, 1); flyCamera(); },
  speed(v) { if (v) fly.base = v; return fly.base; },
  camPose() { const e = new THREE.Euler().setFromQuaternion(camera.quaternion, 'YXZ'); return { x: camera.position.x, y: -camera.position.z, z: camera.position.y, yaw: e.y, pitch: e.x }; },
  state() { return { mode, x: fly.pos.x, y: -fly.pos.z, z: fly.pos.y, yaw: fly.yaw, pitch: fly.pitch, speed: fly.base, v: fly.vel.length(), tour: tour.on }; },
  orbitPose(px, py, pz, tx, ty, tz) { setMode('orbit'); camera.position.copy(b2t(px, py, pz)); orbit.target.copy(b2t(tx, ty, tz)); orbit.update(); },
  hud() { return document.getElementById('hud').innerText; },
};
