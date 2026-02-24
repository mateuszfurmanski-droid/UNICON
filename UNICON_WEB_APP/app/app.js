const video = document.getElementById("cam");
const canvas = document.getElementById("hud");
const ctx = canvas.getContext("2d");
const btnPin = document.getElementById("btnPin");

let pinned = false;
let pin = { x: 0.5, y: 0.55 };

function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(canvas.clientWidth * dpr);
  canvas.height = Math.floor(canvas.clientHeight * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
window.addEventListener("resize", resizeCanvas);

async function startCamera() {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "environment" },
    audio: false
  });
  video.srcObject = stream;
  await video.play();
}

function drawLine(x1,y1,x2,y2,color,lw=1){
  ctx.strokeStyle = color;
  ctx.lineWidth = lw;
  ctx.beginPath();
  ctx.moveTo(x1,y1);
  ctx.lineTo(x2,y2);
  ctx.stroke();
}

function loop(now){
  const t = now / 1000;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;

  ctx.clearRect(0,0,w,h);

  const cx = w * (pinned ? pin.x : 0.5);
  const cy = h * (pinned ? pin.y : 0.55);

  const s = 18 + 4*Math.sin(t*1.6);
  drawLine(cx - s, cy, cx + s, cy, "rgba(85,255,85,0.35)", 1);
  drawLine(cx, cy - s, cx, cy + s, "rgba(85,255,85,0.35)", 1);

  requestAnimationFrame(loop);
}

btnPin.onclick = () => { pinned = !pinned; };

canvas.addEventListener("pointerdown", (e) => {
  const rect = canvas.getBoundingClientRect();
  pin.x = (e.clientX - rect.left) / rect.width;
  pin.y = (e.clientY - rect.top) / rect.height;
  pinned = true;
});

(async function main(){
  await startCamera();
  resizeCanvas();
  requestAnimationFrame(loop);
})();
