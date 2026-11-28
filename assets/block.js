/*
 * Hero grass block: a 16x16-texel isometric Minecraft-style block drawn on a canvas.
 * First visit: the block "paints itself" pixel by pixel, then floats.
 * Later visits: drawn instantly. Respects prefers-reduced-motion.
 */
(() => {
  const canvas = document.getElementById("heroBlock");
  if (!canvas || !canvas.getContext) return;
  const wrap = canvas.parentElement;
  const ctx = canvas.getContext("2d");
  const N = 16;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- textures (seeded so the block looks the same every time) ---------- */
  let seed = 20261112;
  const rnd = () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const pick = (arr) => arr[Math.floor(rnd() * arr.length)];
  const GRASS = ["#5e9b33", "#6aab3b", "#78bb45", "#539029", "#86c94f", "#649f37"];
  const GRASS_DARK = ["#4c8326", "#558f2c", "#5e9b33"];
  const DIRT = ["#7a553a", "#8a6244", "#6b4a31", "#5d3f29", "#946d4c", "#82593d"];
  const STONE = ["#8d8d8d", "#757575"];

  // Top: grass with soft clusters.
  const top = [];
  for (let v = 0; v < N; v++) for (let u = 0; u < N; u++) {
    const cluster = Math.sin(u * 0.9 + v * 0.4) + Math.cos(v * 0.8 - u * 0.3);
    top.push(cluster > 1.1 ? pick(["#86c94f", "#78bb45"]) : cluster < -1.1 ? pick(["#539029", "#4c8326"]) : pick(GRASS));
  }
  // Sides: dirt, with a ragged grass lip at the top and a few pebbles.
  const side = () => {
    const drip = Array.from({ length: N }, () => 2 + Math.floor(rnd() * 3) - (rnd() < 0.25 ? 1 : 0));
    const out = [];
    for (let v = 0; v < N; v++) for (let u = 0; u < N; u++) {
      if (v < drip[u]) out.push(v === drip[u] - 1 ? pick(GRASS_DARK) : pick(GRASS));
      else if (rnd() < 0.05) out.push(pick(STONE));
      else out.push(pick(DIRT));
    }
    return out;
  };
  const left = side();
  const right = side();

  const shade = (hex, f) => {
    const n = parseInt(hex.slice(1), 16);
    const c = (s) => Math.max(0, Math.min(255, Math.round(((n >> s) & 255) * f)));
    return `rgb(${c(16)},${c(8)},${c(0)})`;
  };

  /* ---------- geometry ---------- */
  let s, cx, y0;
  function layout() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth || 280;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(w * dpr);
    s = canvas.width / (N * 2 + 2);            // texel size
    cx = canvas.width / 2;
    y0 = (canvas.height - N * 2 * s) / 2;      // block is 32 texels tall in screen space
  }
  // Each face: origin + u axis + v axis (in texel units).
  const faces = () => [
    { tex: top, f: 1.0, m: [s, s / 2, -s, s / 2, cx, y0] },
    { tex: left, f: 0.8, m: [s, s / 2, 0, s, cx - N * s, y0 + (N / 2) * s] },
    { tex: right, f: 0.62, m: [s, -s / 2, 0, s, cx, y0 + N * s] },
  ];

  const texels = [];
  for (let face = 0; face < 3; face++) for (let v = 0; v < N; v++) for (let u = 0; u < N; u++) texels.push({ face, u, v });

  function drawTexel(F, t) {
    ctx.setTransform(...F[t.face].m);
    ctx.fillStyle = shade(F[t.face].tex[t.v * N + t.u], F[t.face].f);
    ctx.fillRect(t.u - 0.03, t.v - 0.03, 1.06, 1.06); // tiny overlap hides seams
  }
  function drawEdges() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.strokeStyle = "rgba(255,255,255,.18)";
    ctx.lineWidth = Math.max(1, s * 0.18);
    ctx.beginPath();
    ctx.moveTo(cx - N * s, y0 + (N / 2) * s); ctx.lineTo(cx, y0 + N * s); ctx.lineTo(cx + N * s, y0 + (N / 2) * s);
    ctx.moveTo(cx, y0 + N * s); ctx.lineTo(cx, y0 + 2 * N * s);
    ctx.stroke();
  }
  function drawAll() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const F = faces();
    texels.forEach((t) => drawTexel(F, t));
    drawEdges();
  }

  function paintIn(done) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const F = faces();
    // Paint from the bottom of the block upward, with a little randomness, like a brush.
    const order = texels
      .map((t) => ({ t, k: (t.face === 0 ? 40 - (t.u + t.v) : 40 + (N - t.v) * 1.6 + (t.face === 1 ? N - t.u : t.u) * 0.4) + rnd() * 6 }))
      .sort((a, b) => b.k - a.k);
    const total = 1700;
    const start = performance.now();
    let i = 0;
    const step = (now) => {
      const target = Math.min(order.length, Math.ceil(((now - start) / total) * order.length));
      for (; i < target; i++) drawTexel(F, order[i].t);
      if (i < order.length) requestAnimationFrame(step);
      else { drawEdges(); done(); }
    };
    requestAnimationFrame(step);
  }

  let seen = false;
  try { seen = localStorage.getItem("nabd.drawn") === "1"; } catch { /* storage blocked */ }

  layout();
  const finish = () => {
    wrap.classList.add("ready");
    if (!reduce) wrap.classList.add("floating");
    try { localStorage.setItem("nabd.drawn", "1"); } catch { /* ignore */ }
  };
  if (seen || reduce) { drawAll(); finish(); }
  else { wrap.classList.add("painting"); paintIn(finish); }

  let rt;
  addEventListener("resize", () => {
    clearTimeout(rt);
    rt = setTimeout(() => { if (wrap.classList.contains("ready")) { layout(); drawAll(); } }, 150);
  });
})();
