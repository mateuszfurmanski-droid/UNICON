(() => {
  const cam = document.getElementById('cam');
  if (!cam) return;

  const cams = ['/cam.mjpg', '/cam2.mjpg'];
  let idx = 0;

  function setCam(i){
    idx = (i + cams.length) % cams.length;
    cam.src = cams[idx] + '?t=' + Date.now(); // cache-bust
    console.log('CAM =', cams[idx]);
  }

  window.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 'c') setCam(idx + 1);
  });

  setCam(0);
})();
