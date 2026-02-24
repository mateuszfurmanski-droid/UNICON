(() => {
  const HUD_POLL_MS = 120;

  function el(tag, attrs={}, parent=document.body) {
    const e = document.createElement(tag);
    for (const [k,v] of Object.entries(attrs)) {
      if (k === "style") Object.assign(e.style, v);
      else if (k === "class") e.className = v;
      else e.setAttribute(k, v);
    }
    parent.appendChild(e);
    return e;
  }

  // Root overlay
  const root = el("div", {
    id: "uniconHudOverlay",
    style: {
      position: "fixed",
      inset: "0",
      pointerEvents: "none",
      zIndex: "9999",
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
      color: "#6bff6b",
      textShadow: "0 0 6px rgba(0,255,0,0.35)"
    }
  });

  // Top debug strip (minimal)
  const top = el("div", {
    style: {
      position: "absolute",
      left: "8px",
      right: "8px",
      top: "6px",
      padding: "6px 8px",
      border: "1px solid rgba(0,255,0,0.25)",
      borderRadius: "8px",
      background: "rgba(0,0,0,0.25)",
      fontSize: "12px",
      display: "flex",
      gap: "10px",
      alignItems: "center",
      justifyContent: "space-between"
    }
  }, root);

  const statusL = el("div", { id: "hudStatusL" }, top);
  const statusR = el("div", { id: "hudStatusR" }, top);

  // Center crosshair is already in your HTML, we only add numbers near center
  const center = el("div", {
    style: {
      position: "absolute",
      left: "50%",
      top: "50%",
      transform: "translate(-50%, -30%)",
      padding: "6px 10px",
      borderRadius: "10px",
      background: "rgba(0,0,0,0.22)",
      border: "1px solid rgba(0,255,0,0.22)",
      fontSize: "18px",
      whiteSpace: "nowrap"
    }
  }, root);

  const txt = el("div", { id: "hudMainTxt" }, center);

  // Bottom ruler / level canvas
  const cv = el("canvas", {
    id: "hudCanvas",
    style: {
      position: "absolute",
      left: "0",
      top: "0",
      width: "100%",
      height: "100%"
    }
  }, root);

  const ctx = cv.getContext("2d");

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    cv.width = Math.floor(window.innerWidth * dpr);
    cv.height = Math.floor(window.innerHeight * dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  window.addEventListener("resize", resize);
  resize();

  function clear() {
    ctx.clearRect(0,0,window.innerWidth, window.innerHeight);
  }

  function drawLevel(pitch, roll) {
    // simple level indicator around center: a horizontal line tilting with roll
    const W = window.innerWidth;
    const H = window.innerHeight;
    const cx = W/2;
    const cy = H/2 + 140;

    const len = Math.min(420, W*0.65);
    const ang = (roll || 0) * Math.PI / 180; // roll degrees -> rad
    const dx = Math.cos(ang) * (len/2);
    const dy = Math.sin(ang) * (len/2);

    ctx.globalAlpha = 0.9;
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(240,240,120,0.95)";

    ctx.beginPath();
    ctx.moveTo(cx - dx, cy - dy);
    ctx.lineTo(cx + dx, cy + dy);
    ctx.stroke();

    // center marker
    ctx.beginPath();
    ctx.arc(cx, cy, 10, 0, Math.PI*2);
    ctx.stroke();

    // small tick
    ctx.beginPath();
    ctx.moveTo(cx, cy - 18);
    ctx.lineTo(cx, cy + 18);
    ctx.stroke();

    // pitch text (small)
    ctx.font = "16px ui-monospace, Menlo, Consolas, monospace";
    ctx.fillStyle = "rgba(240,240,120,0.95)";
    const p = (pitch ?? 0).toFixed(2);
    const r = (roll ?? 0).toFixed(2);
    ctx.fillText(`pitch ${p}°  roll ${r}°`, cx - 120, cy + 42);
  }

  function drawRuler(distCm) {
    // minimal ruler centered bottom
    const W = window.innerWidth;
    const H = window.innerHeight;
    const y = H - 160;
    const cx = W/2;

    const span = Math.min(520, W*0.78);
    const x1 = cx - span/2;
    const x2 = cx + span/2;

    ctx.globalAlpha = 0.9;
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(240,240,120,0.95)";

    // main line
    ctx.beginPath();
    ctx.moveTo(x1, y);
    ctx.lineTo(x2, y);
    ctx.stroke();

    // end ticks
    ctx.beginPath();
    ctx.moveTo(x1, y-18); ctx.lineTo(x1, y+18);
    ctx.moveTo(x2, y-18); ctx.lineTo(x2, y+18);
    ctx.stroke();

    // center tick
    ctx.beginPath();
    ctx.moveTo(cx, y-26); ctx.lineTo(cx, y+26);
    ctx.stroke();

    // distance label
    ctx.font = "18px ui-monospace, Menlo, Consolas, monospace";
    ctx.fillStyle = "rgba(240,240,120,0.95)";
    const d = (distCm ?? 0).toFixed(1);
    ctx.fillText(`${d} cm`, cx - 35, y - 34);
  }

  async function poll() {
    try {
      const r = await fetch(`/health?ts=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) throw new Error(`health ${r.status}`);
      const j = await r.json();

      const latest = j.latest || {};
      const dist = latest.dist_cm;
      const pitch = latest.pitch;
      const roll = latest.roll;
      const fps = latest.fps;
      const ok = j.ok;
      const st = j.status || {};
      const imu = st.imu_ok;
      const lidar = st.lidar_ok;
      const video = st.video_ok;

      statusL.textContent = `OK:${ok}  IMU:${imu}  LiDAR:${lidar}  VIDEO:${video}`;
      statusR.textContent = `fps:${(fps ?? 0).toFixed(1)}  ts:${Math.floor((latest.ts ?? 0) % 100000)}`;

      txt.textContent = `L:${(dist ?? 0).toFixed(1)} cm   P:${(pitch ?? 0).toFixed(2)}°   R:${(roll ?? 0).toFixed(2)}°`;

      clear();
      drawLevel(pitch, roll);
      drawRuler(dist);
    } catch (e) {
      statusL.textContent = `HUD ERROR: ${String(e).slice(0,80)}`;
    } finally {
      setTimeout(poll, HUD_POLL_MS);
    }
  }

  poll();
})();
