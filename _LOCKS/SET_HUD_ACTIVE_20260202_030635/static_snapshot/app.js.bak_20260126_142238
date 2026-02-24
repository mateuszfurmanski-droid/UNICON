(() => {
  const stage = document.getElementById('stage');
  const cam = document.getElementById('cam');
  const canvas = document.getElementById('overlay');
  const hud = document.getElementById('hudline');
  const ctx = canvas.getContext('2d');

  // ---- view transform (pan/zoom) ----
  let zoom = 1.0;
  let panX = 0;
  let panY = 0;

  let dragging = false;
  let lastX = 0;
  let lastY = 0;

  // ---- measurements ----
  // each measurement = { A:{x,y}, B:{x,y}, id:int, ts:number }
  const measures = [];
  let nextId = 1;

  // current building segment
  let curA = null;
  let curB = null;       // fixed B after click
  let previewB = null;   // live mouse B before click

  const SNAP_PX = 14;

  function resize() {
    canvas.width = stage.clientWidth;
    canvas.height = stage.clientHeight;
    draw();
  }

  function applyTransform() {
    cam.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
  }

  function dist2(p, q) {
    const dx = p.x - q.x;
    const dy = p.y - q.y;
    return dx * dx + dy * dy;
  }

  function snapPoint(p) {
    let best = null;
    let bestD2 = SNAP_PX * SNAP_PX;

    // snap to current points
    if (curA && dist2(p, curA) <= bestD2) best = curA;
    if (curB && dist2(p, curB) <= bestD2) best = curB;

    // snap to saved measurements endpoints
    for (const m of measures) {
      if (m.A && dist2(p, m.A) <= bestD2) best = m.A;
      if (m.B && dist2(p, m.B) <= bestD2) best = m.B;
    }

    return best ? { x: best.x, y: best.y, snapped: true } : { x: p.x, y: p.y, snapped: false };
  }

  function drawCrosshair() {
    const w = canvas.width, h = canvas.height;
    const cx = w / 2, cy = h / 2;
    ctx.strokeStyle = 'rgba(124,255,124,0.95)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(cx - 14, cy); ctx.lineTo(cx + 14, cy);
    ctx.moveTo(cx, cy - 14); ctx.lineTo(cx, cy + 14);
    ctx.stroke();
  }

  function drawDot(p, r = 4, alpha = 0.95) {
    ctx.fillStyle = `rgba(124,255,124,${alpha})`;
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawLine(p1, p2, alpha = 0.95, width = 2) {
    ctx.strokeStyle = `rgba(124,255,124,${alpha})`;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
  }

  function drawSnapHint(p) {
    ctx.strokeStyle = 'rgba(124,255,124,0.35)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, SNAP_PX, 0, Math.PI * 2);
    ctx.stroke();
  }

  function pxDist(p1, p2) {
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function drawLabel(p1, p2, text, alphaBg = 0.55, alphaFg = 0.95) {
    const mx = (p1.x + p2.x) / 2;
    const my = (p1.y + p2.y) / 2;

    ctx.fillStyle = `rgba(0,0,0,${alphaBg})`;
    ctx.fillRect(mx - 42, my - 18, 96, 20);

    ctx.fillStyle = `rgba(124,255,124,${alphaFg})`;
    ctx.font = '14px Arial';
    ctx.fillText(text, mx - 38, my - 4);
  }

  function drawMeasure(m, faded = false) {
    const a = faded ? 0.55 : 0.95;
    drawLine(m.A, m.B, a, 2);
    drawDot(m.A, 4, a);
    drawDot(m.B, 4, a);

    const d = pxDist(m.A, m.B);
    drawLabel(m.A, m.B, `#${m.id}  ${d.toFixed(0)} px`, 0.45, a);
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    drawCrosshair();

    // saved measurements
    for (const m of measures) drawMeasure(m, false);

    // current preview
    if (curA && !curB && previewB) {
      const sp = snapPoint(previewB);
      if (sp.snapped) drawSnapHint(sp);
      drawLine(curA, sp, 0.55, 2);
      drawDot(curA, 4, 0.95);
      drawDot(sp, 3, 0.75);
      const d = pxDist(curA, sp);
      drawLabel(curA, sp, `NEW  ${d.toFixed(0)} px`, 0.45, 0.75);
    }

    // current fixed (if somehow set)
    if (curA && curB) {
      drawLine(curA, curB, 0.95, 2);
      drawDot(curA, 4, 0.95);
      drawDot(curB, 4, 0.95);
      const d = pxDist(curA, curB);
      drawLabel(curA, curB, `NEW  ${d.toFixed(0)} px`, 0.45, 0.95);
    }
  }

  function getMousePos(e) {
    const rect = stage.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  // ---- interactions ----
  stage.addEventListener('contextmenu', (e) => e.preventDefault());

  stage.addEventListener('mousedown', (e) => {
    // RMB:
    //  - if building: cancel current segment
    //  - else: clear all measurements
    if (e.button === 2) {
      if (curA || curB || previewB) {
        curA = null; curB = null; previewB = null;
      } else {
        measures.length = 0;
        nextId = 1;
      }
      draw();
      return;
    }

    // SHIFT+LMB: pan
    if (e.shiftKey && e.button === 0) {
      dragging = true;
      lastX = e.clientX; lastY = e.clientY;
      return;
    }

    // LMB: set A then set B, then SAVE to list and start new
    if (e.button === 0) {
      const p = getMousePos(e);

      if (!curA) {
        const sp = snapPoint(p);
        curA = { x: sp.x, y: sp.y };
        curB = null;
        previewB = null;
        draw();
        return;
      }

      // set B + save
      const sp = snapPoint(p);
      curB = { x: sp.x, y: sp.y };

      // save measurement
      measures.push({ A: curA, B: curB, id: nextId++, ts: Date.now() });

      // immediately start next measurement (A resets)
      curA = null;
      curB = null;
      previewB = null;

      draw();
    }
  });

  stage.addEventListener('mousemove', (e) => {
    // pan
    if (dragging) {
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      lastX = e.clientX; lastY = e.clientY;
      panX += dx;
      panY += dy;
      applyTransform();
      return;
    }

    // preview ruler
    if (curA && !curB) {
      previewB = getMousePos(e);
      draw();
    }
  });

  window.addEventListener('mouseup', () => dragging = false);

  stage.addEventListener('wheel', (e) => {
    e.preventDefault();
    const delta = Math.sign(e.deltaY);
    const factor = (delta > 0) ? 0.92 : 1.08;
    zoom = Math.max(0.5, Math.min(4.0, zoom * factor));
    applyTransform();
  }, { passive: false });

  // ---- HUD polling ----
  async function pollHealth() {
    try {
      const r = await fetch('/health', { cache: 'no-store' });
      const j = await r.json();
      const L = j.latest || {};
      const S = j.status || {};

      const dist = (L.dist_cm == null) ? '—' : `${Number(L.dist_cm).toFixed(0)}cm`;
      const strength = (L.strength == null) ? '—' : `${L.strength}`;
      const temp = (L.temp_c == null) ? '—' : `${Number(L.temp_c).toFixed(1)}C`;
      const roll = (L.roll == null) ? '—' : `${Number(L.roll).toFixed(2)}`;
      const pitch = (L.pitch == null) ? '—' : `${Number(L.pitch).toFixed(2)}`;
      const fps = (L.fps == null) ? '—' : `${Number(L.fps).toFixed(1)}`;

      const flags = `V:${S.video_ok ? 'OK' : 'NO'} I:${S.imu_ok ? 'OK' : 'NO'} L:${S.lidar_ok ? 'OK' : 'NO'}`;
      hud.textContent =
        `LiDAR:${dist} S:${strength} T:${temp} | R:${roll} P:${pitch} FPS:${fps} | ${flags} | ` +
        `MEAS:${measures.length} | RMB:cancel/clear | SHIFT+LMB:pan | wheel:zoom`;
    } catch (e) {
      hud.textContent = 'health: fetch failed';
    }
  }

  // init
  window.addEventListener('resize', resize);
  resize();
  applyTransform();
  pollHealth();
  setInterval(pollHealth, 200);
})();
