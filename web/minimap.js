// North-up schematic locator. Masses come from params.json. The plan bitmap is cached.
export const FRAME = { minX: -96, maxX: 96, minY: -100, maxY: 72 };

export function yFront(shape, x) {
  const v = 1 - Math.abs(x / shape.hw) ** shape.n;
  return shape.cy - shape.hd * Math.max(v, 0) ** (1 / shape.n);
}

export function screenHeading(yaw) {
  const x = -Math.sin(yaw), y = -Math.cos(yaw);
  return { x: x === 0 ? 0 : x, y: y === 0 ? 0 : y };
}

export function project(frame, layout, x, y) {
  const sx = (x - frame.minX) / (frame.maxX - frame.minX);
  const sy = (frame.maxY - y) / (frame.maxY - frame.minY);
  return {
    x: layout.mapX + sx * layout.mapW,
    y: layout.mapY + sy * layout.mapH,
    inside: sx >= 0 && sx <= 1 && sy >= 0 && sy <= 1,
  };
}

export function layoutFor(width, height) {
  const pad = Math.max(4, Math.round(Math.min(width, height) * 0.05));
  const caption = Math.max(13, Math.round(height * 0.12));
  return {
    mapX: pad, mapY: pad,
    mapW: Math.max(1, width - pad * 2),
    mapH: Math.max(1, height - pad * 2 - caption),
    captionY: height - caption,
  };
}

function sampleSuper(shape, nSeg = 72) {
  const pts = [];
  for (let i = 0; i < nSeg; i++) {
    const th = (2 * Math.PI * i) / nSeg;
    const c = Math.cos(th), sn = Math.sin(th);
    const r = (Math.abs(c / shape.hw) ** shape.n + Math.abs(sn / shape.hd) ** shape.n) ** (-1 / shape.n);
    pts.push({ x: r * c, y: shape.cy + r * sn });
  }
  return pts;
}

function levelsFrom(params) {
  const h = params.global.floor_h;
  const n = Math.round(params.tower.floors_top / h);
  const levels = [];
  for (let i = 0; i <= n; i++) levels.push(Math.round(i * h * 1000) / 1000);
  return levels;
}

function captionFor(mode, z, edge, levels, floorH) {
  if (mode === 'orbit') return '环绕 · 非玩家位置';
  let level = null;
  for (const lv of levels) if (Math.abs(lv - z) <= 0.4 + 1e-9) level = lv;
  const bits = [mode === 'fly' ? '飞行' : '漫游'];
  if (edge) bits.push('图外');
  if (level !== null) bits.push('L' + Math.round(level / floorH));
  bits.push(z.toFixed(1) + ' m');
  return bits.join(' · ');
}

function edgePoint(x, y) {
  const cx = (FRAME.minX + FRAME.maxX) / 2;
  const cy = (FRAME.minY + FRAME.maxY) / 2;
  const dx = x - cx, dy = y - cy;
  const hx = (FRAME.maxX - FRAME.minX) / 2;
  const hy = (FRAME.maxY - FRAME.minY) / 2;
  const t = Math.max(Math.abs(dx) / hx, Math.abs(dy) / hy);
  if (t <= 1) return { x, y, edge: false };
  return { x: cx + dx / t, y: cy + dy / t, edge: true };
}

export function createMap(params) {
  const pod = params.podium;
  const deck = { id: 'deck', kind: 'super', hw: pod.deck_half_w, hd: pod.deck_half_d, cy: pod.deck_cy, n: pod.deck_n };
  const podium = { id: 'podium', kind: 'super', hw: pod.wall_half_w, hd: pod.wall_half_d, cy: pod.wall_cy, n: pod.wall_n };
  deck.pts = sampleSuper(deck);
  podium.pts = sampleSuper(podium);
  const shapes = [deck, podium];
  for (const side of ['west', 'east']) {
    for (const [name, box] of Object.entries(params.wings[side])) {
      if (!Array.isArray(box)) continue;
      shapes.push({ id: `wing-${side}-${name}`, kind: 'rect', x0: box[0], y0: box[1], x1: box[2], y1: box[3] });
    }
  }
  const front = yFront(podium, params.arch.cx);
  shapes.push({
    id: 'arch', kind: 'rect', void: true,
    x0: params.arch.cx - params.arch.hw, x1: params.arch.cx + params.arch.hw,
    y0: front, y1: front + params.arch.portal_depth,
  });
  shapes.push({
    id: 'tunnel', kind: 'rect', void: true,
    x0: params.arch.cx - params.tunnel.hw, x1: params.arch.cx + params.tunnel.hw,
    y0: front, y1: params.courtyard.cy - params.courtyard.r,
  });
  shapes.push({
    id: 'court', kind: 'ellipse', void: true,
    cx: params.courtyard.cx, cy: params.courtyard.cy,
    rx: params.courtyard.r * params.courtyard.kx, ry: params.courtyard.r,
  });
  shapes.push({
    id: 'tower', kind: 'circle',
    cx: params.tower.cx, cy: params.tower.cy, r: params.tower.drums[0][0],
  });
  for (const c of params.canopies) {
    shapes.push({ id: 'drum-' + c.name, kind: 'circle', cx: c.cx, cy: c.cy, r: c.drum_r });
  }
  const levels = levelsFrom(params);
  const floorH = params.global.floor_h;
  return {
    notice: '示意',
    levels,
    shapes,
    describe(state) {
      const mode = state && state.mode ? state.mode : 'orbit';
      if (mode === 'orbit') {
        return {
          mode, kind: 'orbit', marker: null, edge: false, dir: null, worldEdge: null,
          caption: captionFor('orbit', 0, false, levels, floorH),
        };
      }
      const hit = edgePoint(state.x, state.y);
      return {
        mode, kind: mode === 'fly' ? 'fly' : 'player', edge: hit.edge,
        x: state.x, y: state.y, z: state.z, yaw: state.yaw,
        dir: screenHeading(state.yaw || 0),
        worldEdge: { x: hit.x, y: hit.y },
        marker: { x: hit.x, y: hit.y },
        caption: captionFor(mode, state.z, hit.edge, levels, floorH),
      };
    },
  };
}

const FILL = { deck: '#e6ded2', podium: '#d2c6b6', wing: '#c2b09a', void: '#8fa4ac', tower: '#8a847c', drum: '#667584' };

function paintPlan(ctx, shapes, layout, w, h) {
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = 'rgba(18, 24, 32, 0.88)';
  ctx.fillRect(0, 0, w, h);
  for (const s of shapes) {
    if (s.kind === 'super') {
      ctx.beginPath();
      s.pts.forEach((p, i) => {
        const q = project(FRAME, layout, p.x, p.y);
        if (i === 0) ctx.moveTo(q.x, q.y); else ctx.lineTo(q.x, q.y);
      });
      ctx.closePath();
      ctx.fillStyle = s.id === 'deck' ? FILL.deck : FILL.podium;
      ctx.fill();
    } else if (s.kind === 'rect') {
      const a = project(FRAME, layout, s.x0, s.y0);
      const b = project(FRAME, layout, s.x1, s.y1);
      ctx.fillStyle = s.void ? FILL.void : FILL.wing;
      ctx.fillRect(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.abs(b.x - a.x), Math.abs(b.y - a.y));
    } else {
      const c = project(FRAME, layout, s.cx, s.cy);
      const rx = Math.abs((s.rx || s.r) / (FRAME.maxX - FRAME.minX) * layout.mapW);
      const ry = Math.abs((s.ry || s.r) / (FRAME.maxY - FRAME.minY) * layout.mapH);
      ctx.beginPath();
      ctx.ellipse(c.x, c.y, Math.max(rx, 0.5), Math.max(ry, 0.5), 0, 0, Math.PI * 2);
      ctx.fillStyle = s.void ? FILL.void : (s.id === 'tower' ? FILL.tower : FILL.drum);
      ctx.fill();
    }
  }
  ctx.fillStyle = '#f7fbff';
  ctx.font = `${Math.max(11, Math.round(layout.mapH * 0.09))}px sans-serif`;
  ctx.textBaseline = 'top';
  ctx.fillText('N', layout.mapX + 3, layout.mapY + 2);
  ctx.fillText('示意', layout.mapX + layout.mapW - ctx.measureText('示意').width - 3, layout.mapY + 2);
}

function paintMarker(ctx, layout, desc, unit) {
  if (!desc || !desc.marker || !desc.dir) return;
  const p = project(FRAME, layout, desc.marker.x, desc.marker.y);
  ctx.save();
  ctx.translate(p.x, p.y);
  ctx.rotate(Math.atan2(desc.dir.x, -desc.dir.y));
  ctx.beginPath();
  ctx.moveTo(0, -8 * unit);
  ctx.lineTo(4.5 * unit, 6.5 * unit);
  ctx.lineTo(0, 3 * unit);
  ctx.lineTo(-4.5 * unit, 6.5 * unit);
  ctx.closePath();
  ctx.fillStyle = desc.edge ? '#ffb020' : '#e23b32';
  ctx.fill();
  ctx.restore();
}

export function attachMinimap(canvas, params) {
  if (!canvas) {
    canvas = document.createElement('canvas');
    canvas.id = 'minimap';
    canvas.setAttribute('aria-label', '位置示意');
    document.body.appendChild(canvas);
  }
  const map = createMap(params);
  let cache = null;
  let key = '';
  let last = null;
  let lastCost = 0;
  let builds = 0;
  function fit() {
    const css = canvas.getBoundingClientRect();
    const dpr = Math.min((typeof window !== 'undefined' && window.devicePixelRatio) || 1, 2);
    const w = Math.max(1, Math.round((css.width || canvas.clientWidth || 172) * dpr));
    const h = Math.max(1, Math.round((css.height || canvas.clientHeight || 148) * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
      key = '';
    }
    return { dpr, cssWidth: css.width, cssHeight: css.height };
  }
  function sync(state) {
    const t0 = performance.now();
    const box = fit();
    const next = canvas.width + 'x' + canvas.height;
    if (key !== next) {
      cache = document.createElement('canvas');
      cache.width = canvas.width;
      cache.height = canvas.height;
      paintPlan(cache.getContext('2d'), map.shapes, layoutFor(cache.width, cache.height), cache.width, cache.height);
      key = next;
      builds += 1;
    }
    const desc = map.describe(state || { mode: 'orbit' });
    const ctx = canvas.getContext('2d');
    const layout = layoutFor(canvas.width, canvas.height);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(cache, 0, 0);
    const unit = Math.max(1, canvas.width / 172);
    paintMarker(ctx, layout, desc, unit);
    ctx.fillStyle = '#f7f4ef';
    ctx.font = `${Math.max(10, Math.round(canvas.height * 0.078))}px sans-serif`;
    ctx.textBaseline = 'middle';
    ctx.fillText(desc.caption, layout.mapX, layout.captionY + (canvas.height - layout.captionY) / 2);
    let px = null, py = null;
    if (desc.marker) {
      const q = project(FRAME, layout, desc.marker.x, desc.marker.y);
      px = q.x; py = q.y;
    }
    last = { ...desc, px, py, dpr: box.dpr, cssWidth: box.cssWidth, cssHeight: box.cssHeight, builds };
    lastCost = performance.now() - t0;
  }
  return { sync, read: () => last, cost: () => lastCost, map, canvas };
}
