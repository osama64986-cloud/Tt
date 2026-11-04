// Renders every character form (geometry + texture) to one preview sheet with three.js + Playwright.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const RP = process.argv[2];
const OUT = process.argv[3];
const only = process.argv[4] ? process.argv[4].split(",") : null;
let forms = [
  ["goku", "base", "base"], ["goku", "ssj", "ssj"], ["goku", "ssj3", "ssj3"], ["goku", "ssb", "ssb"], ["goku", "ui", "ui"],
  ["vegeta", "base", "base"], ["vegeta", "ssj", "ssj"], ["vegeta", "ssb", "ssb"], ["vegeta", "ue", "ue"],
  ["gojo", "blindfold", "blindfold"], ["gojo", "eyes", "eyes"],
  ["yuji", "base", "base"], ["yuji_final", "base", "base"], ["sukuna", "yuji", "yuji"], ["sukuna", "megumi", "megumi"], ["sukuna", "heian", "heian"],
  ["luffy", "base", "base"], ["luffy", "g2", "g2"], ["luffy", "g3", "g3"], ["luffy", "g4b", "g4b"], ["luffy", "g4s", "g4s"], ["luffy", "g4t", "g4t"], ["luffy", "g5", "g5"],
];
if (only) forms = forms.filter((f) => only.includes(f[0]) || only.includes(f[0] + ":" + f[2]));
const models = forms.map(([ch, geo, tex]) => ({
  label: `${ch} ${tex}`,
  geo: JSON.parse(fs.readFileSync(path.join(RP, "models/entity", `${ch}_${geo}.geo.json`)))["minecraft:geometry"][0],
  tex: "data:image/png;base64," + fs.readFileSync(path.join(RP, "textures/entity", ch, `${tex}.png`)).toString("base64"),
}));
const three = fs.readFileSync(path.join(__dirname, "node_modules/three/build/three.module.js"), "utf8");

const html = `<!doctype html><html><body style="margin:0;background:#9cc3e6">
<script type="module">
${three.replace(/export \{[\s\S]*?\};\s*$/m, "")}
const models = ${JSON.stringify(models)}; const CLOSE = ${process.env.CLOSE ? 1 : 0};
const W = 300, H = 420, cols = models.length;
const renderer = new WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W * cols, H * 3);
renderer.setScissorTest(true);
document.body.appendChild(renderer.domElement);
const loader = new TextureLoader();
const faceRects = (u, v, s) => { const [w, h, d] = s; return {
  px: [u, v + d, d, h], nx: [u + d + w, v + d, d, h], py: [u + d, v, w, d], ny: [u + d + w, v, w, d],
  pz: [u + 2 * d + w, v + d, w, h], nz: [u + d, v + d, w, h] }; };
const order = ["px", "nx", "py", "ny", "pz", "nz"];
let pending = models.length;
models.forEach((m, i) => loader.load(m.tex, (tex) => {
  tex.magFilter = NearestFilter; tex.minFilter = NearestFilter; tex.colorSpace = SRGBColorSpace;
  const T = m.geo.description.texture_width;
  const mat = new MeshLambertMaterial({ map: tex, transparent: false, alphaTest: 0.5, side: DoubleSide });
  const group = new Group();
  for (const b of m.geo.bones) for (const c of b.cubes || []) {
    const inf = c.inflate || 0;
    const g = new BoxGeometry(c.size[0] + 2 * inf, c.size[1] + 2 * inf, c.size[2] + 2 * inf);
    const uv = g.attributes.uv;
    const r = faceRects(c.uv[0], c.uv[1], c.size);
    order.forEach((f, fi) => {
      const [x, y, w, h] = r[f];
      const u0 = x / T, u1 = (x + w) / T, vt = 1 - y / T, vb = 1 - (y + h) / T;
      const q = [[u0, vt], [u1, vt], [u0, vb], [u1, vb]];
      for (let k = 0; k < 4; k++) uv.setXY(fi * 4 + k, q[k][0], q[k][1]);
    });
    const mesh = new Mesh(g, mat);
    // Bedrock -> Blockbench space (what you see in game): mirror X, negate X/Y rotation, Euler ZYX.
    const from = [-(c.origin[0] + c.size[0]), c.origin[1], c.origin[2]];
    const center = [from[0] + c.size[0] / 2, from[1] + c.size[1] / 2, from[2] + c.size[2] / 2];
    if (c.rotation) {
      const pv = [-c.pivot[0], c.pivot[1], c.pivot[2]];
      const pg = new Group();
      pg.position.set(pv[0], pv[1], pv[2]);
      pg.rotation.order = "ZYX";
      pg.rotation.set(-c.rotation[0] * Math.PI / 180, -c.rotation[1] * Math.PI / 180, c.rotation[2] * Math.PI / 180);
      mesh.position.set(center[0] - pv[0], center[1] - pv[1], center[2] - pv[2]);
      pg.add(mesh);
      group.add(pg);
    } else {
      mesh.position.set(center[0], center[1], center[2]);
      group.add(mesh);
    }
  }
  for (const [row, angle] of [[0, -0.35], [1, Math.PI / 2 + 0.2], [2, Math.PI * 0.85]]) {
    const scene = new Scene();
    scene.background = new Color([0x9cc3e6, 0x8fb7da, 0x7fa8cc][row]);
    scene.add(new AmbientLight(0xffffff, 1.6));
    const sun = new DirectionalLight(0xffffff, 1.4); sun.position.set(20, 40, -30); scene.add(sun);
    const gg = group.clone(); gg.rotation.y = angle; scene.add(gg);
    const cam = new PerspectiveCamera(35, W / H, 1, 500);
    if (CLOSE) { cam.position.set(0, 29, -30); cam.lookAt(0, 28, 0); } else { cam.position.set(0, 26, -70); cam.lookAt(0, 21, 0); }
    const y = (2 - row) * H;
    renderer.setViewport(i * W, y, W, H); renderer.setScissor(i * W, y, W, H);
    renderer.render(scene, cam);
  }
  if (--pending === 0) document.title = "done";
}));
</script></body></html>`;
const file = path.join(__dirname, "preview.html");
fs.writeFileSync(file, html);
(async () => {
  const browser = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage({ viewport: { width: 300 * models.length, height: 1260 } });
  page.on("console", (m) => console.log("page:", m.text()));
  page.on("pageerror", (e) => console.log("pageerror:", e.message));
  await page.goto("file://" + file);
  await page.waitForFunction(() => document.title === "done", null, { timeout: 60000 });
  await page.screenshot({ path: OUT });
  await browser.close();
  console.log("saved", OUT, models.map((m) => m.label).join(" | "));
})();
