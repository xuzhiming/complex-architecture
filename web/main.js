// Building preview: orbit view + first-person walk (WASD + pointer-lock mouse look) + free fly (6-DoF, no collision, tour),
// capsule collision against a three-mesh-bvh BVH, automatic sliding doors, virtual lift cars.
// Blender (x,y,z) -> glTF/three (x, z, -y).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { MeshBVH } from 'three-mesh-bvh';

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
scene.background = new THREE.Color(0xc9ced8);
scene.fog = new THREE.Fog(0xc9ced8, 250, 700);
scene.add(new THREE.HemisphereLight(0xffffff, 0x80786c, 1.6));
const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(-120, 200, 160); scene.add(sun);
const amb = new THREE.AmbientLight(0xffffff, 0.35); scene.add(amb);

const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.05, 3000);
const headlamp = new THREE.PointLight(0xfff4e0, 0, 30, 1.5); camera.add(headlamp); scene.add(camera);
camera.position.copy(b2t(-120, -170, 80));
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
const SPEED = 4.0, GRAV = -20, OPEN_DIST = 3.5;

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

// door leaves
gltf.scene.traverse(o => {
  if (!/^DoorLeaf_/.test(o.name) || leafRoot(o.parent)) return;
  const s = o.userData.slide || [1, 0, 0];
  const box = new THREE.Box3().setFromObject(o); const c = box.getCenter(new THREE.Vector3());
  doors.push({ obj: o, id: o.userData.door_id || o.name.slice(9), closed: o.position.clone(), centre: c,
               slideW: new THREE.Vector3(s[0], s[2], -s[1]), t: 0 });
});
// slide vector is in world space; convert to the leaf's parent space
for (const d of doors) {
  const m = new THREE.Matrix4().copy(d.obj.parent.matrixWorld).invert();
  d.slideL = d.slideW.clone().applyMatrix3(new THREE.Matrix3().setFromMatrix4(m));
}
if (SPACES) for (const L of SPACES.lifts) {
  const [x0, y0, x1, y1] = L.shaft;
  lifts.push({ id: L.id, x0, x1, z0: -y1, z1: -y0, levels: L.levels });   // three x/z bounds
}
document.getElementById('load').remove();

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
      liftState = { lift: L, carY: lv, target: lv };
    }
    const d = liftState.target - liftState.carY;
    liftState.carY += Math.sign(d) * Math.min(Math.abs(d), 3.0 * dt);
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
  // doors
  for (const d of doors) {
    const dx = player.pos.x - d.centre.x, dz = player.pos.z - d.centre.z, dy = feetY() - (d.centre.y - 1.2);
    const near = Math.hypot(dx, dz) < OPEN_DIST && Math.abs(dy) < 2.5;
    d.t = THREE.MathUtils.clamp(d.t + (near ? 1 : -1) * dt * 2.2, 0, 1);
    d.obj.position.copy(d.closed).addScaledVector(d.slideL, THREE.MathUtils.smoothstep(d.t, 0, 1));
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
  orbit.enabled = m === 'orbit'; headlamp.intensity = m === 'walk' ? 25 : (m === 'fly' ? 12 : 0); cross.style.display = m !== 'orbit' ? 'block' : 'none';
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
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });

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
    ? `WALK  ·  WASD move · mouse look (click) · Shift run · Tab orbit · F fly 飞行<br>${liftState ? `in lift ${liftState.lift.id} · R up / F down · level ${liftState.target}` : ''}<br>x ${b.x}  y ${b.y}  floor z ${b.z} m`
    : `ORBIT  ·  drag rotate · wheel zoom · right-drag pan · Tab / button = walk mode · F fly 飞行<br>collider triangles: ${window.__colliderTris}`;
}

let last = performance.now(), renderEvery = TEST ? 0 : 1;
function loop(now) {
  const dt = Math.min((now - last) / 1000, 0.1); last = now;
  if (mode === 'walk') { const n = Math.ceil(dt / 0.01); for (let i = 0; i < n; i++) step(dt / n); syncCamera(); }
  else if (mode === 'fly') { if (tour.on) tourStep(dt); else flyStep(dt); flyCamera(); document.getElementById('bTour').classList.toggle('on', tour.on); }
  else orbit.update();
  hud.innerHTML = hudText();
  if (renderEvery) renderer.render(scene, camera);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

// ---------------- test hooks (used by walk_test.py) ----------------
window.__walk = {
  ready: true,
  setMode, render() { if (mode === 'walk') syncCamera(); else if (mode === 'fly') flyCamera(); renderer.render(scene, camera); },
  mode() { return mode; },
  teleport(x, y, z, yaw = 0) { setMode('walk'); setFeet(b2t(x, y, z)); player.yaw = yaw; player.onGround = false; },
  setYaw(y) { player.yaw = y; }, setPitch(p) { player.pitch = p; },
  state() { return { x: player.pos.x, y: -player.pos.z, z: feetY(), yaw: player.yaw, onGround: player.onGround,
                     lift: liftState ? { id: liftState.lift.id, car: liftState.carY, target: liftState.target } : null }; },
  doorsNear(r = 4) { return doors.filter(d => Math.hypot(player.pos.x - d.centre.x, player.pos.z - d.centre.z) < r && Math.abs(feetY() - (d.centre.y - 1.2)) < 2.5).map(d => ({ id: d.id, open: d.t })); },
  doorCount() { return doors.length; },
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
