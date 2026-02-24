(() => {
  // === UNICON Level Bubble Overlay (WORKTOP V1: thin, 1D bubble, smooth, color feedback) ===
  const STAGE = document.getElementById('stage') || document.body;

  // separate overlay canvas (no conflicts)
  const c = document.createElement('canvas');
  c.id = 'levelBubble';
  c.style.position = 'absolute';
  c.style.inset = '0';
  c.style.pointerEvents = 'none';
  c.style.zIndex = '9';
  STAGE.appendChild(c);

  const ctx = c.getContext('2d');

  let W=0,H=0, dpr=1;
  function resize(){
    dpr = Math.max(1, window.devicePixelRatio || 1);
    W = Math.floor(window.innerWidth);
    H = Math.floor(window.innerHeight);
    c.width  = Math.floor(W * dpr);
    c.height = Math.floor(H * dpr);
    c.style.width = W+'px';
    c.style.height = H+'px';
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  window.addEventListener('resize', resize);
  resize();

  // latest IMU values (deg)
  let roll=0, pitch=0;

  // "fluid" smoothing
  let rollS=0, pitchS=0;

  async function poll(){
    try{
      const r = await fetch('/health', {cache:'no-store'});
      const j = await r.json();
      const L = (j && j.latest) ? j.latest : {};
      roll  = Number(L.roll  || 0);
      pitch = Number(L.pitch || 0);
    }catch(e){}
    setTimeout(poll, 120);
  }
  poll();

  function colorFor(errDeg){
    if (errDeg <= 0.6)  return 'rgba(140,255,180,0.95)'; // green
    if (errDeg <= 1.5)  return 'rgba(255,235,120,0.95)'; // yellow
    return 'rgba(255,120,120,0.95)';                     // red
  }

  function clamp(v, lo, hi){ return Math.max(lo, Math.min(hi, v)); }

  function draw(){
    ctx.clearRect(0,0,W,H);

    // bottom-center position (tune if needed)
    const cx  = Math.round(W * 0.50);
    const cy  = Math.round(H * 0.78);

    // geometry (more "tool-like", smaller + tighter)
    const len   = Math.round(Math.min(W,H) * 0.20); // half-length
    const tickX = Math.round(len * 0.22);

    // smoothing (bubble in liquid feel)
    rollS  = rollS  * 0.86 + roll  * 0.14;
    pitchS = pitchS * 0.86 + pitch * 0.14;

    // 1D bubble movement: roll -> X ONLY (worktop level)
    const pxPerDeg = Math.max(5, Math.round(len / 14));
    const maxOff   = Math.round(len * 0.78);
    const ox = clamp(rollS * pxPerDeg, -maxOff, maxOff);

    // color by worst-axis error (so it goes red even if pitch is off)
    const err = Math.max(Math.abs(rollS), Math.abs(pitchS));
    const col = colorFor(err);

    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // ultra-thin
    const lwMain = 1.15;
    const lwTick = 0.95;

    // main horizontal "tube" axis
    ctx.strokeStyle = col;
    ctx.globalAlpha = 0.95;
    ctx.lineWidth = lwMain;

    ctx.beginPath();
    ctx.moveTo(cx-len, cy);
    ctx.lineTo(cx+len, cy);
    ctx.stroke();

    // end caps (subtle)
    ctx.globalAlpha = 0.55;
    ctx.lineWidth = 1.0;
    ctx.beginPath();
    ctx.moveTo(cx-len, cy-8); ctx.lineTo(cx-len, cy+8);
    ctx.moveTo(cx+len, cy-8); ctx.lineTo(cx+len, cy+8);
    ctx.stroke();

    // ticks (like scale marks)
    ctx.globalAlpha = 0.95;
    ctx.lineWidth = lwTick;

    const tH = 12;
    ctx.beginPath();
    ctx.moveTo(cx - tickX, cy - tH); ctx.lineTo(cx - tickX, cy + tH);
    ctx.moveTo(cx + tickX, cy - tH); ctx.lineTo(cx + tickX, cy + tH);
    ctx.stroke();

    // center ring (small)
    ctx.beginPath();
    ctx.lineWidth = 1.0;
    ctx.arc(cx, cy, 7, 0, Math.PI*2);
    ctx.stroke();

    // bubble ring (small, tool-like)
    const br = 6.2;
    ctx.beginPath();
    ctx.lineWidth = 1.25;
    ctx.arc(cx + ox, cy, br, 0, Math.PI*2);
    ctx.stroke();

    // dot inside bubble
    ctx.beginPath();
    ctx.fillStyle = col;
    ctx.globalAlpha = 0.55;
    ctx.arc(cx + ox, cy, 2.0, 0, Math.PI*2);
    ctx.fill();

    // faint guide line from center to bubble (very subtle)
    ctx.globalAlpha = 0.18;
    ctx.lineWidth = 1.0;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + ox, cy);
    ctx.stroke();

    ctx.restore();

    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();
