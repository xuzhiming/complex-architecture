// Building preview: orbit view + first-person walk (WASD + pointer-lock mouse look),
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
    if (!o.isMesh) return;
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
  mode = m; document.getElementById('bOrbit').classList.toggle('on', m === 'orbit'); document.getElementById('bWalk').classList.toggle('on', m === 'walk');
  orbit.enabled = m === 'orbit'; headlamp.intensity = m === 'walk' ? 25 : 0; cross.style.display = m === 'walk' ? 'block' : 'none';
  if (m === 'walk' && player.pos.lengthSq() === 0) { setFeet(b2t(0, -62, 0)); player.yaw = 0; }
}
document.getElementById('bOrbit').onclick = () => { document.exitPointerLock?.(); setMode('orbit'); };
document.getElementById('bWalk').onclick = () => setMode('walk');
renderer.domElement.addEventListener('click', () => { if (mode === 'walk' && !TEST) renderer.domElement.requestPointerLock?.(); });
document.addEventListener('mousemove', e => {
  if (mode !== 'walk' || document.pointerLockElement !== renderer.domElement) return;
  player.yaw -= e.movementX * 0.0022; player.pitch = THREE.MathUtils.clamp(player.pitch - e.movementY * 0.0022, -1.4, 1.4);
});
addEventListener('keydown', e => {
  keys[e.code] = true;
  if (e.code === 'Tab') { e.preventDefault(); setMode(mode === 'walk' ? 'orbit' : 'walk'); }
  if (liftState && (e.code === 'KeyR' || e.code === 'KeyF')) {
    const lv = liftState.lift.levels; let i = lv.indexOf(liftState.target);
    i = THREE.MathUtils.clamp(i + (e.code === 'KeyR' ? 1 : -1), 0, lv.length - 1); liftState.target = lv[i];
  }
});
addEventListener('keyup', e => { keys[e.code] = false; });
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });

function syncCamera() {
  camera.position.set(player.pos.x, player.pos.y + EYE, player.pos.z);
  camera.rotation.set(player.pitch, player.yaw, 0, 'YXZ');
}
function hudText() {
  const f = feetY();
  const b = { x: player.pos.x.toFixed(1), y: (-player.pos.z).toFixed(1), z: f.toFixed(2) };
  return mode === 'walk'
    ? `WALK  ·  WASD move · mouse look (click) · Shift run · Tab orbit<br>${liftState ? `in lift ${liftState.lift.id} · R up / F down · level ${liftState.target}` : ''}<br>x ${b.x}  y ${b.y}  floor z ${b.z} m`
    : `ORBIT  ·  drag rotate · wheel zoom · right-drag pan · Tab / button = walk mode<br>collider triangles: ${window.__colliderTris}`;
}

let last = performance.now(), renderEvery = TEST ? 0 : 1;
function loop(now) {
  const dt = Math.min((now - last) / 1000, 0.1); last = now;
  if (mode === 'walk') { const n = Math.ceil(dt / 0.01); for (let i = 0; i < n; i++) step(dt / n); syncCamera(); }
  else orbit.update();
  hud.innerHTML = hudText();
  if (renderEvery) renderer.render(scene, camera);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

// ---------------- test hooks (used by walk_test.py) ----------------
window.__walk = {
  ready: true,
  setMode, render() { syncCamera(); renderer.render(scene, camera); },
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
