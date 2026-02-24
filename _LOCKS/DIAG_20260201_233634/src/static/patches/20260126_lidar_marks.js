(() => {
  // UNICON PATCH: LiDAR heart/dot + labels on midpoints of saved measurements
  // Reads:
  //  - /health        -> dist_cm, strength
  //  - /api/live_job  -> measurements (A,B,id)
  //
  // NOTE: measurement cm is an approximation using camera HFOV + current LiDAR distance.

  const HFOV_DEG = 62; // tweak if needed (typical webcam ~60-70). Bigger HFOV -> smaller cm.
  const HEALTH_MS = 250;
  const JOB_MS = 350;

  const stage = document.getElementById('stage');
  const baseCanvas = document.getElementById('overlay');

  if (!stage || !baseCanvas) {
    console.warn('UNICON PATCH: stage/overlay not found');
    return;
  }

  // create extra overlay canvas (non-interactive)
  const c = document.createElement('canvas');
  c.id = 'patchOverlay';
  c.style.position = 'absolute';
  c.style.left = '0';
  c.style.top = '0';
  c.style.width = '100%';
  c.style.height = '100%';
  c.style.pointerEvents = 'none';
  c.style.zIndex = '50';
  stage.appendChild(c);

  const ctx = c.getContext('2d');

  function resize() {
    c.width = stage.clientWidth;
    c.height = stage.clientHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  // state
  let health = { dist_cm: null, strength: null, ts: 0 };
  let job = { measurements: [] };

  function pxDist(a, b) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function focalPx(widthPx) {
    const hfov = (HFOV_DEG * Math.PI) / 180;
    return (widthPx / 2) / Math.tan(hfov / 2);
  }

  // approximate cm for a screen-space segment using current LiDAR distance
  function cmFromPx(pxLen) {
    const d = Number(health.dist_cm);
    if (!Number.isFinite(d) || d <= 0) return null;
    const f = focalPx(c.width);
    return (pxLen / f) * d;
  }

  function drawHeartDots(cx, cy, scale = 1) {
    // simple dotted-heart cluster under crosshair
    const pts = [
      [-6, -2], [-2, -4], [ 2, -4], [ 6, -2],
      [-4,  2], [ 0,  6], [ 4,  2],
      [ 0,  0],
    ];
    ctx.fillStyle = 'rgba(124,255,124,0.95)';
    for (const [dx, dy] of pts) {
      ctx.beginPath();
      ctx.arc(cx + dx * scale, cy + dy * scale, 1.6 * scale, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawLidarMarker() {
    const cx = c.width / 2;
    const cy = c.height / 2;

    // put the “heart” slightly under crosshair
    const hx = cx;
    const hy = cy + 18;

    drawHeartDots(hx, hy, 1);

    const d = Number(health.dist_cm);
    const s = Number(health.strength);

    let text = 'L: --';
    if (Number.isFinite(d)) text = `L: ${d.toFixed(0)} cm`;
    if (Number.isFinite(s)) text += `  S:${s}`;

    // small background
    ctx.font = '12px Arial';
    const pad = 4;
    const w = ctx.measureText(text).width;
    ctx.fillStyle = 'rgba(0,0,0,0.45)';
    ctx.fillRect(hx - w / 2 - pad, hy + 10, w + pad * 2, 16);

    ctx.fillStyle = 'rgba(124,255,124,0.95)';
    ctx.fillText(text, hx - w / 2, hy + 22);
  }

  function drawMidLabels() {
    const arr = Array.isArray(job.measurements) ? job.measurements : [];
    ctx.font = '13px Arial';

    for (const m of arr) {
      if (!m || !m.A || !m.B) continue;
      const A = { x: Number(m.A.x), y: Number(m.A.y) };
      const B = { x: Number(m.B.x), y: Number(m.B.y) };
      if (![A.x, A.y, B.x, B.y].every(Number.isFinite)) continue;

      const mx = (A.x + B.x) / 2;
      const my = (A.y + B.y) / 2;

      const px = pxDist(A, B);
      const cm = cmFromPx(px);

      // one value at the middle of line:
      const text = (cm == null)
        ? `${px.toFixed(0)} px`
        : `${cm.toFixed(1)} cm`;

      const pad = 4;
      const tw = ctx.measureText(text).width;

      ctx.fillStyle = 'rgba(0,0,0,0.55)';
      ctx.fillRect(mx - tw / 2 - pad, my - 18, tw + pad * 2, 16);

      ctx.fillStyle = 'rgba(124,255,124,0.95)';
      ctx.fillText(text, mx - tw / 2, my - 6);
    }
  }

  function render() {
    ctx.clearRect(0, 0, c.width, c.height);
    drawLidarMarker();
    drawMidLabels();
  }

  async function pollHealth() {
    try {
      const r = await fetch('/health', { cache: 'no-store' });
      if (!r.ok) return;
      const j = await r.json();
      if (j && j.latest) {
        health.dist_cm = j.latest.dist_cm ?? null;
        health.strength = j.latest.strength ?? null;
        health.ts = Date.now();
      }
      render();
    } catch (_) {}
  }

  async function pollJob() {
    try {
      const r = await fetch('/api/live_job', { cache: 'no-store' });
      if (!r.ok) return;
      const j = await r.json();
      if (j) job = j;
      render();
    } catch (_) {}
  }

  // kick
  pollHealth();
  pollJob();
  setInterval(pollHealth, HEALTH_MS);
  setInterval(pollJob, JOB_MS);
})();
