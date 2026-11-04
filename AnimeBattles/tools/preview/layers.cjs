// Layered model renderer (box + per-face UV, tint per layer). Usage: node layers.cjs out.png spec.json
// spec: [{label, layers:[{geo, id?, tex, tint?:[r,g,b]}]}]
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
const [OUT, SPEC] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(SPEC));
const models = spec.map((m) => ({
  label: m.label,
  layers: m.layers.map((l) => {
    const all = JSON.parse(fs.readFileSync(l.geo, "utf8").replace(/\/\/.*$/gm, ""))["minecraft:geometry"];
    const geo = l.id ? all.find((g) => g.description.identifier === l.id) : all[0];
    return { geo, tint: l.tint || [1, 1, 1], tex: "data:image/png;base64," + fs.readFileSync(l.tex).toString("base64") };
  }),
}));
const three = fs.readFileSync(path.join(__dirname, "node_modules/three/build/three.module.js"), "utf8");
const html = `<!doctype html><html><body style="margin:0"><script type="module">
${three.replace(/export \{[\s\S]*?\};\s*$/m, "")}
const models = ${JSON.stringify(models)}; const CLOSE = ${process.env.CLOSE ? 1 : 0};
const W = 300, H = 420;
const renderer = new WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W * models.length, H * 2); renderer.setScissorTest(true);
document.body.appendChild(renderer.domElement);
const loader = new TextureLoader();
const load = (src) => new Promise((r) => loader.load(src, r));
const boxRects = (u, v, s) => { const [w, h, d] = s; return { px: [u, v + d, d, h], nx: [u + d + w, v + d, d, h], py: [u + d, v, w, d], ny: [u + d + w, v, w, d], pz: [u + 2 * d + w, v + d, w, h], nz: [u + d, v + d, w, h] }; };
// Bedrock per-face keys in Blockbench space: east=+X ... but Bedrock "east" is model -X; after the X mirror it lands on +X.
const faceKey = { px: "west", nx: "east", py: "up", ny: "down", pz: "south", nz: "north" };
const order = ["px", "nx", "py", "ny", "pz", "nz"];
(async () => {
  for (let i = 0; i < models.length; i++) {
    const group = new Group();
    for (const L of models[i].layers) {
      const tex = await load(L.tex); tex.magFilter = NearestFilter; tex.minFilter = NearestFilter; tex.colorSpace = SRGBColorSpace;
      const TW = L.geo.description.texture_width, TH = L.geo.description.texture_height;
      const mat = new MeshLambertMaterial({ map: tex, transparent: true, alphaTest: 0.1, color: new Color(...L.tint) });
      for (const b of L.geo.bones) for (const c of b.cubes || []) {
        const inf = c.inflate || 0;
        const g = new BoxGeometry(c.size[0] + 2 * inf + 0.001, c.size[1] + 2 * inf + 0.001, c.size[2] + 2 * inf + 0.001);
        const uv = g.attributes.uv;
        const per = c.uv && !Array.isArray(c.uv);
        const r = per ? null : boxRects(c.uv[0], c.uv[1], c.size);
        order.forEach((f, fi) => {
          let x, y, w, h;
          if (per) { const fd = c.uv[faceKey[f]]; if (!fd) { for (let k = 0; k < 4; k++) uv.setXY(fi * 4 + k, 0, 0); return; } [x, y] = fd.uv; [w, h] = fd.uv_size; }
          else [x, y, w, h] = r[f];
          const u0 = x / TW, u1 = (x + w) / TW, vt = 1 - y / TH, vb = 1 - (y + h) / TH;
          const q = [[u0, vt], [u1, vt], [u0, vb], [u1, vb]];
          for (let k = 0; k < 4; k++) uv.setXY(fi * 4 + k, q[k][0], q[k][1]);
        });
        const mesh = new Mesh(g, mat);
        const from = [-(c.origin[0] + c.size[0]), c.origin[1], c.origin[2]];
        const center = [from[0] + c.size[0] / 2, from[1] + c.size[1] / 2, from[2] + c.size[2] / 2];
        if (c.rotation) {
          const pv = [-c.pivot[0], c.pivot[1], c.pivot[2]];
          const pg = new Group(); pg.position.set(...pv); pg.rotation.order = "ZYX";
          pg.rotation.set(-c.rotation[0] * Math.PI / 180, -c.rotation[1] * Math.PI / 180, c.rotation[2] * Math.PI / 180);
          mesh.position.set(center[0] - pv[0], center[1] - pv[1], center[2] - pv[2]); pg.add(mesh); group.add(pg);
        } else { mesh.position.set(...center); group.add(mesh); }
      }
    }
    for (const [row, angle] of [[0, -0.35], [1, Math.PI * 0.85]]) {
      const scene = new Scene(); scene.background = new Color(row ? 0x8fb7da : 0x9cc3e6);
      scene.add(new AmbientLight(0xffffff, 1.6)); const sun = new DirectionalLight(0xffffff, 1.4); sun.position.set(20, 40, -30); scene.add(sun);
      const gg = group.clone(); gg.rotation.y = angle; scene.add(gg);
      const cam = new PerspectiveCamera(35, W / H, 1, 500);
      if (CLOSE) { cam.position.set(0, 29, -30); cam.lookAt(0, 28, 0); } else { cam.position.set(0, 26, -70); cam.lookAt(0, 21, 0); }
      const yy = (1 - row) * H; renderer.setViewport(i * W, yy, W, H); renderer.setScissor(i * W, yy, W, H); renderer.render(scene, cam);
    }
  }
  document.title = "done";
})();
</script></body></html>`;
const file = path.join(__dirname, "layers.html");
fs.writeFileSync(file, html);
(async () => {
  const browser = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage({ viewport: { width: 300 * models.length, height: 840 } });
  page.on("pageerror", (e) => console.log("pageerror:", e.message));
  await page.goto("file://" + file);
  await page.waitForFunction(() => document.title === "done", null, { timeout: 90000 });
  await page.screenshot({ path: OUT });
  await browser.close();
  console.log("saved", OUT);
})();
