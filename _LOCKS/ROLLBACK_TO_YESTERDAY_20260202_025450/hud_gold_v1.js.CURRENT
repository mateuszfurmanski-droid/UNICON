(function () {
  const hud = document.createElement('div');
  hud.id = 'hud-gold-v1';
  hud.style.cssText = `
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    color: #eab308;
    font-family: monospace;
    font-size: 14px;
    background: rgba(0,0,0,0.45);
    padding: 6px 10px;
    border: 1px solid #eab308;
    border-radius: 6px;
    z-index: 9999;
  `;
  hud.textContent = 'HUD INIT';
  document.body.appendChild(hud);

  async function tick() {
    try {
      const r = await fetch('/health');
      const j = await r.json();
      const L = j.latest || {};
      hud.textContent =
        `L:${(L.dist_cm||0).toFixed(1)}cm ` +
        `P:${(L.pitch||0).toFixed(2)}° ` +
        `R:${(L.roll||0).toFixed(2)}°`;
    } catch (e) {
      hud.textContent = 'HUD ERR';
    }
  }

  setInterval(tick, 200);
})();

// === UNICON FORCE LIVE (DEV MODE) ===
setInterval(async () => {
  try {
    const r = await fetch('/health', { cache: 'no-store' });
    const j = await r.json();
    if (j && j.ok === true) {
      if (window.HUD_STATE === 'boot') {
        console.log('[HUD] force LIVE');
        window.HUD_STATE = 'live';
      }
    }
  } catch (e) {}
}, 500);
