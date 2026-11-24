import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createMap, project, screenHeading, yFront, FRAME } from '../web/minimap.js';

const params = JSON.parse(readFileSync(new URL('../params.json', import.meta.url)));
const map = createMap(params);
const round = (v) => {
  const n = (a) => { const r = Math.round(a * 1e6) / 1e6; return r === 0 ? 0 : r; };
  return { x: n(v.x), y: n(v.y) };
};

assert.equal(map.levels[0], 0);
assert.equal(map.levels.at(-1), 58.5);
assert.equal(map.levels.length, 14);
assert.ok(map.levels.every((z, i) => i === 0 || Math.abs(z - map.levels[i - 1] - params.global.floor_h) < 1e-6));
assert.equal(map.notice, '示意');

const pod = map.shapes.find((s) => s.id === 'podium');
assert.ok(Math.abs(yFront(pod, 0) - (params.podium.wall_cy - params.podium.wall_half_d)) < 1e-9);
assert.equal(pod.hw, params.podium.wall_half_w);
assert.equal(pod.n, params.podium.wall_n);

const deck = map.shapes.find((s) => s.id === 'deck');
assert.equal(deck.hw, params.podium.deck_half_w);
assert.equal(deck.hd, params.podium.deck_half_d);
assert.equal(deck.n, params.podium.deck_n);
assert.equal(deck.cy, params.podium.deck_cy);

const court = map.shapes.find((s) => s.id === 'court');
assert.ok(Math.abs(court.rx - params.courtyard.r * params.courtyard.kx) < 1e-9);
assert.equal(court.ry, params.courtyard.r);
assert.equal(court.cx, params.courtyard.cx);
assert.equal(court.cy, params.courtyard.cy);
assert.equal(court.void, true);

const tower = map.shapes.find((s) => s.id === 'tower');
assert.equal(tower.cx, params.tower.cx);
assert.equal(tower.cy, params.tower.cy);
assert.equal(tower.r, params.tower.drums[0][0]);

const west = map.shapes.find((s) => s.id === 'wing-west-hall');
assert.deepEqual([west.x0, west.y0, west.x1, west.y1], params.wings.west.hall);
const east = map.shapes.find((s) => s.id === 'wing-east-core');
assert.deepEqual([east.x0, east.y0, east.x1, east.y1], params.wings.east.core);

const arch = map.shapes.find((s) => s.id === 'arch');
assert.equal(arch.void, true);
assert.ok(Math.abs((arch.x1 - arch.x0) / 2 - params.arch.hw) < 1e-9);
assert.ok(Math.abs(arch.y0 - yFront(pod, params.arch.cx)) < 1e-9);
assert.ok(Math.abs((arch.y1 - arch.y0) - params.arch.portal_depth) < 1e-9);

const tunnel = map.shapes.find((s) => s.id === 'tunnel');
assert.equal(tunnel.void, true);
assert.ok(Math.abs((tunnel.x1 - tunnel.x0) / 2 - params.tunnel.hw) < 1e-9);
assert.ok(Math.abs(tunnel.y1 - (params.courtyard.cy - params.courtyard.r)) < 1e-9);

assert.equal(map.shapes.filter((s) => s.id.startsWith('drum-')).length, params.canopies.length);
assert.equal(JSON.stringify(map.shapes).includes('probe'), false);
assert.equal(JSON.stringify(map.shapes).includes('W_hall'), false);

assert.deepEqual(round(screenHeading(0)), { x: 0, y: -1 });
assert.deepEqual(round(screenHeading(Math.PI / 2)), { x: -1, y: 0 });

const layout = { mapX: 0, mapY: 0, mapW: 192, mapH: 172 };
const north = project(FRAME, layout, 0, 2);
const south = project(FRAME, layout, 0, -62);
assert.equal(north.inside, true);
assert.ok(north.y < south.y);

const orbit = map.describe({ mode: 'orbit', x: 0, y: 0, z: 0, yaw: 0 });
assert.equal(orbit.kind, 'orbit');
assert.equal(orbit.marker, null);
assert.match(orbit.caption, /环绕/);
assert.match(orbit.caption, /非玩家/);
assert.doesNotMatch(orbit.caption, /L\d|courtyard|W_hall|T_L/);

const walk = map.describe({ mode: 'walk', x: 0, y: 2, z: 0, yaw: 0 });
assert.equal(walk.kind, 'player');
assert.equal(walk.edge, false);
assert.match(walk.caption, /漫游/);
assert.match(walk.caption, /L0/);
assert.deepEqual(round(walk.dir), { x: 0, y: -1 });

const stair = map.describe({ mode: 'walk', x: -43, y: -8, z: 2.2, yaw: 0 });
assert.doesNotMatch(stair.caption, /L\d/);
assert.match(stair.caption, /2\.2 m/);

const near = map.describe({ mode: 'walk', x: 13.5, y: 40, z: 4.9, yaw: Math.PI / 2 });
assert.match(near.caption, /L1/);
assert.deepEqual(round(near.dir), { x: -1, y: 0 });
const offLevel = map.describe({ mode: 'walk', x: 13.5, y: 40, z: 4.91, yaw: 0 });
assert.doesNotMatch(offLevel.caption, /L\d/);

const fly = map.describe({ mode: 'fly', x: 0, y: 2, z: 80, yaw: 0 });
assert.equal(fly.kind, 'fly');
assert.match(fly.caption, /飞行/);
assert.match(fly.caption, /80\.0 m/);
assert.doesNotMatch(fly.caption, /L\d/);

const flyLevel = map.describe({ mode: 'fly', x: 0, y: 2, z: 4.5, yaw: 0 });
assert.match(flyLevel.caption, /飞行/);
assert.match(flyLevel.caption, /L1/);

const outside = map.describe({ mode: 'walk', x: 0, y: -170, z: 0, yaw: 0 });
assert.equal(outside.edge, true);
assert.match(outside.caption, /图外/);
assert.ok(Math.abs(outside.worldEdge.y - FRAME.minY) < 1e-6);
assert.ok(Math.abs(outside.worldEdge.x) < 1e-6);
assert.ok(Math.abs(outside.worldEdge.y - (-14)) > 10);

const shapes = map.shapes;
map.describe({ mode: 'walk', x: 1, y: 1, z: 9, yaw: 1 });
assert.equal(map.shapes, shapes);

console.log('MINIMAP LOGIC PASS');
