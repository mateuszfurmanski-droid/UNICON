/* UNICON_ERRHOOK_V1: surface JS errors in HUD */
(function(){
  function put(msg){
    try{
      const el = document.getElementById('hudline') || document.getElementById('hud') || document.body;
      if(!el) return;
      const t = (new Date()).toISOString().slice(11,19);
      const line = `[${t}] ${msg}`;
      if (el.id === 'hudline') el.textContent = line;
      else el.textContent = line;
      console.log(line);
    }catch(e){}
  }
  window.addEventListener('error', function(e){
    put('JS ERROR: ' + (e && e.message ? e.message : 'unknown') + (e && e.filename ? (' @ ' + e.filename + ':' + e.lineno) : ''));
  });
  window.addEventListener('unhandledrejection', function(e){
    const r = e && e.reason ? (e.reason.stack || e.reason.message || String(e.reason)) : 'unknown';
    put('PROMISE REJECT: ' + r);
  });
  window.UNICON_put = put;
})();
(() => {
  const stage = document.getElementById('stage');
  const cam = document.getElementById('cam');
  const canvas = document.getElementById('overlay');
  const hud = document.getElementById('hudline');
  const ctx = canvas.getContext('2d');

  

  // --- UNICON_ARTIFACT_V1 (keep camera 'reference' dot-matrix in center) ---
  function drawArtifact() {
    const w = canvas.width, h = canvas.height;
    const cx = Math.floor(w * 0.5), cy = Math.floor(h * 0.5);
    const dot = 3;      // dot size
    const gap = 2;      // spacing
    const pts = [
      [0,0],[1,0],[2,0],[3,0],
      [0,1],[1,1],[2,1],
      [0,2],[1,2],
      [0,3],[1,3],[2,3],[3,3],[4,3],
      [0,4],[1,4],[2,4],[3,4],[4,4],[5,4],
      [1,5],[2,5],[3,5],[4,5]
    ];
    ctx.save();
    ctx.globalAlpha = 0.85;
    ctx.fillStyle = "#fff";
    for (const [x,y] of pts) {
      ctx.fillRect(cx + x*(dot+gap), cy + y*(dot+gap), dot, dot);
    }
    ctx.restore();
  }

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

    
    drawArtifact();
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


// UNICON MENU OVERLAY (V1)
(() => {
  if (window.__UNICON_MENU_V1__) return;
  window.__UNICON_MENU_V1__ = true;

  const btn = document.getElementById("uniconMenuBtn");
  const panel = document.getElementById("uniconMenuPanel");
  const shade = document.getElementById("uniconMenuShade");
  const closeBtn = document.getElementById("uniconMenuClose");
  const out = document.getElementById("uniconMenuOut");

  if (!btn || !panel || !shade || !out) {
    console.warn("UNICON MENU: elements missing");
    return;
  }

  function show(){
    panel.hidden = false;
    shade.hidden = false;
  }
  function hide(){
    panel.hidden = true;
    shade.hidden = true;
  }

  btn.addEventListener("click", () => show());
  closeBtn && closeBtn.addEventListener("click", () => hide());
  shade.addEventListener("click", () => hide());

  // click outside panel closes too
  document.addEventListener("click", (e) => {
    if (panel.hidden) return;
    const t = e.target;
    if (!panel.contains(t) && t !== btn) hide();
  }, true);

  function print(s){
    out.textContent = String(s);
  }

  async function getJson(path){
    const r = await fetch(path, { cache: "no-store" });
    const txt = await r.text();
    return { ok: r.ok, status: r.status, text: txt };
  }

  async function testPort(){
    // browser cannot do ss - just do /health fetch
    const r = await getJson("/health");
    if (r.ok) print("[OK] /health\n\n" + r.text);
    else print("[FAIL] /health (" + r.status + ")\n\n" + r.text);
  }

  async function health(){
    const r = await getJson("/health");
    if (r.ok) print("[OK] /health\n\n" + r.text);
    else print("[FAIL] /health (" + r.status + ")\n\n" + r.text);
  }

  async function liveJob(){
    const r = await getJson("/api/live_job");
    if (r.ok) print("[OK] /api/live_job\n\n" + r.text);
    else print("[FAIL] /api/live_job (" + r.status + ")\n\n" + r.text);
  }

  function openDebugImu(){ window.location.href = "/debug_imu"; }
  function openCam(){ window.open("/cam.mjpg", "_blank"); }
  function openRoot(){ window.location.href = "/"; }

  function toggleOverlay(){
    // best-effort: if existing HUD has overlay canvas, toggle its visibility
    const ov = document.getElementById("overlay");
    if (!ov) { print("[WARN] #overlay not found"); return; }
    const cur = getComputedStyle(ov).display;
    ov.style.display = (cur === "none") ? "block" : "none";
    print("[OK] overlay display -> " + ov.style.display);
  }

  panel.addEventListener("click", async (e) => {
    const b = e.target.closest("button[data-action]");
    if (!b) return;
    const a = b.getAttribute("data-action");
    try{
      if (a === "test_port") await testPort();
      else if (a === "health") await health();
      else if (a === "live_job") await liveJob();
      else if (a === "debug_imu") openDebugImu();
      else if (a === "cam_mjpg") openCam();
      else if (a === "open_root") openRoot();
      else if (a === "toggle_overlay") toggleOverlay();
    }catch(err){
      print("[ERR] " + (err && err.message ? err.message : String(err)));
    }
  });

})();


// UNICON_ARTIFACT_V1


/* UNICON_BOOT2LIVE_BRIDGE */
(function() {
  function setLive() {
    try {
      document.body.setAttribute('data-unicon', 'live');
      window.UNICON_BOOT_STATE = 'live';
      window.dispatchEvent(new CustomEvent('unicon:live'));
    } catch (e) {}
  }

  async function poll() {
    // If page already has stuff running, don't fight it.
    if (window.UNICON_BOOT_STATE === 'live') return;

    try {
      const r = await fetch('/health', { cache: 'no-store' });
      const j = await r.json();
      // Minimal condition: backend says ok:true
      if (j && j.ok === true) {
        setLive();
        return;
      }
    } catch (e) {
      // ignore
    }
    setTimeout(poll, 300);
  }

  function start() {
    // default is boot unless your app sets otherwise
    if (!document.body.hasAttribute('data-unicon')) {
      document.body.setAttribute('data-unicon', 'boot');
    }
    window.UNICON_BOOT_STATE = window.UNICON_BOOT_STATE || 'boot';
    poll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();


// === UNICON POZIOMICA OVERLAY BEGIN ===
(() => {
  if (window.__UNICON_POZIOMICA_INSTALLED) return;
  window.__UNICON_POZIOMICA_INSTALLED = true;

  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  const wrap = document.createElement('div');
  wrap.id = 'unicon-poziomica';
  wrap.style.position = 'fixed';
  wrap.style.left = '50%';
  wrap.style.bottom = '14px';
  wrap.style.transform = 'translateX(-50%)';
  wrap.style.zIndex = '999999';
  wrap.style.pointerEvents = 'none';
  wrap.style.fontFamily = 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace';
  wrap.style.color = 'rgba(120,255,160,0.95)';
  wrap.style.textShadow = '0 0 10px rgba(120,255,160,0.35)';

  const bar = document.createElement('div');
  bar.style.width = '340px';
  bar.style.height = '42px';
  bar.style.border = '1px solid rgba(120,255,160,0.45)';
  bar.style.borderRadius = '14px';
  bar.style.background = 'rgba(0,0,0,0.35)';
  bar.style.backdropFilter = 'blur(2px)';
  bar.style.position = 'relative';
  bar.style.boxShadow = '0 0 18px rgba(120,255,160,0.12) inset';

  const mid = document.createElement('div');
  mid.style.position = 'absolute';
  mid.style.left = '50%';
  mid.style.top = '8px';
  mid.style.width = '2px';
  mid.style.height = '26px';
  mid.style.transform = 'translateX(-50%)';
  mid.style.background = 'rgba(120,255,160,0.35)';
  bar.appendChild(mid);

  const ticks = document.createElement('div');
  ticks.style.position = 'absolute';
  ticks.style.left = '10px';
  ticks.style.right = '10px';
  ticks.style.top = '20px';
  ticks.style.height = '2px';
  ticks.style.background = 'rgba(120,255,160,0.12)';
  bar.appendChild(ticks);

  const bubble = document.createElement('div');
  bubble.style.position = 'absolute';
  bubble.style.top = '9px';
  bubble.style.left = '50%';
  bubble.style.width = '24px';
  bubble.style.height = '24px';
  bubble.style.borderRadius = '999px';
  bubble.style.transform = 'translateX(-50%)';
  bubble.style.border = '1px solid rgba(120,255,160,0.65)';
  bubble.style.background = 'rgba(120,255,160,0.10)';
  bubble.style.boxShadow = '0 0 14px rgba(120,255,160,0.25)';
  bar.appendChild(bubble);

  const dot = document.createElement('div');
  dot.style.position = 'absolute';
  dot.style.left = '50%';
  dot.style.top = '50%';
  dot.style.width = '6px';
  dot.style.height = '6px';
  dot.style.borderRadius = '999px';
  dot.style.transform = 'translate(-50%,-50%)';
  dot.style.background = 'rgba(120,255,160,0.90)';
  dot.style.boxShadow = '0 0 10px rgba(120,255,160,0.55)';
  bubble.appendChild(dot);

  const txt = document.createElement('div');
  txt.style.marginTop = '6px';
  txt.style.textAlign = 'center';
  txt.style.fontSize = '12px';
  txt.textContent = 'LEVEL: boot...';
  wrap.appendChild(bar);
  wrap.appendChild(txt);
  document.body.appendChild(wrap);

  let last = { pitch: 0, roll: 0, ok: false };

  async function poll() {
    try {
      const r = await fetch('/health', { cache: 'no-store' });
      const j = await r.json();
      last.pitch = Number(j?.latest?.pitch ?? 0);
      last.roll  = Number(j?.latest?.roll  ?? 0);
      last.ok    = !!j?.ok;
    } catch (e) {
      last.ok = false;
    }
  }

  setInterval(poll, 150);
  poll();

  function draw() {
    const maxPx = 120;              // travel range
    const x = clamp((last.roll / 30) * maxPx, -maxPx, maxPx);
    bubble.style.left = `calc(50% + ${x}px)`;
    txt.textContent = `LEVEL ${last.ok ? 'OK' : 'NO'} | R:${last.roll.toFixed(2)}  P:${last.pitch.toFixed(2)}`;
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();
// === UNICON POZIOMICA OVERLAY END ===

