(() => {
  const stage = document.getElementById('stage');
  const cam = document.getElementById('cam');
  const canvas = document.getElementById('overlay');
  const hud = document.getElementById("hudline"); if (hud) hud.style.display = "none";
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
  let previewB = null;

  const SNAP_PX = 14;

  // ---- autosave ----
  let saveTimer = null;
  let saving = false;
  let pendingSave = false;

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

    if (curA && dist2(p, curA) <= bestD2) best = curA;

    for (const m of measures) {
      if (m.A && dist2(p, m.A) <= bestD2) best = m.A;
      if (m.B && dist2(p, m.B) <= bestD2) best = m.B;
    }

    return best ? { x: best.x, y: best.y, snapped: true } : { x: p.x, y: p.y, snapped: false };
  }

  function pxDist(p1, p2) {
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function drawCrosshair() {
    const w = canvas.width, h = canvas.height;
    const cx = w / 2, cy = h / 2;
    ctx.strokeStyle = 'rgba(124,255,124,0.95)';
    ctx.lineWidth = 1;
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
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
  }

  function drawSnapHint(p) {
    ctx.strokeStyle = 'rgba(124,255,124,0.35)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(p.x, p.y, SNAP_PX, 0, Math.PI * 2);
    ctx.stroke();
  }

  function drawLabel(p1, p2, text, alphaBg = 0.55, alphaFg = 0.95) {
    const mx = (p1.x + p2.x) / 2;
    const my = (p1.y + p2.y) / 2;

    ctx.fillStyle = `rgba(0,0,0,${alphaBg})`;
    ctx.fillRect(mx - 56, my - 18, 132, 20);

    ctx.fillStyle = `rgba(124,255,124,${alphaFg})`;
    ctx.font = "12px Arial";
    ctx.fillText(text, mx - 52, my - 4);
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

    for (const m of measures) drawMeasure(m, false);

    if (curA && previewB) {
      const sp = snapPoint(previewB);
      if (sp.snapped) drawSnapHint(sp);
      drawLine(curA, sp, 0.55, 2);
      drawDot(curA, 4, 0.95);
      drawDot(sp, 3, 0.75);
      const d = pxDist(curA, sp);
      drawLabel(curA, sp, `NEW  ${d.toFixed(0)} px`, 0.45, 0.75);
    }
  }

  function getMousePos(e) {
    const rect = stage.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  function deleteNearestMeasurement(p) {
    let bestIdx = -1;
    let best = 1e18;

    for (let i = 0; i < measures.length; i++) {
      const m = measures[i];
      const d = Math.min(dist2(p, m.A), dist2(p, m.B));
      if (d < best) { best = d; bestIdx = i; }
    }

    if (bestIdx >= 0 && best <= (26 * 26)) {
      measures.splice(bestIdx, 1);
      draw();
      scheduleSave();
      return true;
    }
    return false;
  }

  // ---- API (live_job) ----
  async function loadLiveJob() {
    try {
      const r = await fetch('/api/live_job', { cache: 'no-store' });
      if (!r.ok) return;
      const j = await r.json();

      measures.length = 0;
      if (Array.isArray(j.measurements)) {
        for (const m of j.measurements) {
          if (!m || !m.A || !m.B) continue;
          measures.push({
            id: Number(m.id) || 0,
            ts: Number(m.ts) || Date.now(),
            A: { x: Number(m.A.x) || 0, y: Number(m.A.y) || 0 },
            B: { x: Number(m.B.x) || 0, y: Number(m.B.y) || 0 },
          });
        }
      }

      nextId = Number(j.next_id) || (measures.reduce((mx, mm) => Math.max(mx, mm.id), 0) + 1);
      draw();
    } catch (e) {}
  }

  async function saveLiveJobNow() {
    if (saving) { pendingSave = true; return; }
    saving = true;

    const payload = {
      version: 1,
      updated_ts: Date.now() / 1000,
      next_id: nextId,
      measurements: measures.map(m => ({
        id: m.id,
        ts: m.ts,
        A: { x: m.A.x, y: m.A.y },
        B: { x: m.B.x, y: m.B.y },
      })),
    };

    try {
      await fetch('/api/live_job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (e) {
    } finally {
      saving = false;
      if (pendingSave) { pendingSave = false; scheduleSave(true); }
    }
  }

  function scheduleSave(immediate = false) {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => { saveLiveJobNow(); }, immediate ? 0 : 250);
  }

  // ---- interactions ----
  stage.addEventListener('contextmenu', (e) => e.preventDefault());

  stage.addEventListener('mousedown', (e) => {
    // ALT+LMB: delete nearest
    if (e.altKey && e.button === 0) {
      const p = getMousePos(e);
      if (deleteNearestMeasurement(p)) return;
    }

    // RMB: cancel current or clear all
    if (e.button === 2) {
      if (curA || previewB) {
        curA = null; previewB = null;
      } else {
        measures.length = 0;
        nextId = 1;
        scheduleSave(true);
      }
      draw();
      return;
    }

    // SHIFT+LMB: pan start
    if (e.shiftKey && e.button === 0) {
      dragging = true;
      lastX = e.clientX; lastY = e.clientY;
      return;
    }

    // LMB: A then B then save
    if (e.button === 0) {
      const p0 = getMousePos(e);

      if (!curA) {
        const sp = snapPoint(p0);
        curA = { x: sp.x, y: sp.y };
        previewB = null;
        draw();
        return;
      }

      const sp = snapPoint(p0);
      const curB = { x: sp.x, y: sp.y };

      measures.push({ A: curA, B: curB, id: nextId++, ts: Date.now() });

      curA = null;
      previewB = null;

      draw();
      scheduleSave();
    }
  });

  stage.addEventListener('mousemove', (e) => {
    if (dragging) {
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      lastX = e.clientX; lastY = e.clientY;
      panX += dx;
      panY += dy;
      applyTransform();
      return;
    }

    if (curA) {
      previewB = getMousePos(e);
      draw();
    }
  });

  window.addEventListener('mouseup', () => { dragging = false; });

  stage.addEventListener('wheel', (e) => {
    e.preventDefault();
    const dir = Math.sign(e.deltaY);
    const factor = dir > 0 ? 0.92 : 1.08;
    zoom = Math.max(0.25, Math.min(3.0, zoom * factor));
    applyTransform();
  }, { passive: false });

  // ---- HUD health ----
  async function pollHealth() { return; }
  }

  // ---- init ----
  window.addEventListener('resize', resize);
  applyTransform();
  resize();

  loadLiveJob();
  setInterval(loadLiveJob, 3000);
  pollHealth();
  setInterval(pollHealth, 500);
})();
