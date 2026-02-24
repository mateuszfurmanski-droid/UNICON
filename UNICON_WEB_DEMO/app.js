const video = document.getElementById("video");
const canvas = document.getElementById("overlay");
const ctx = canvas.getContext("2d");

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener("resize", resize);
resize();

navigator.mediaDevices.getUserMedia({
  video: { facingMode: "environment" },
  audio: false
}).then(stream => {
  video.srcObject = stream;
}).catch(err => {
  alert("Camera error: " + err);
});

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "#00ff66";
  ctx.lineWidth = 1;

  // crosshair
  ctx.beginPath();
  ctx.moveTo(canvas.width / 2 - 30, canvas.height / 2);
  ctx.lineTo(canvas.width / 2 + 30, canvas.height / 2);
  ctx.moveTo(canvas.width / 2, canvas.height / 2 - 30);
  ctx.lineTo(canvas.width / 2, canvas.height / 2 + 30);
  ctx.stroke();

  requestAnimationFrame(draw);
}
draw();
