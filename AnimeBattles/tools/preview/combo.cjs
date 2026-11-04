// Ability showcase: poses the real models (bone rotations from the animation file) and draws the
// ability particles the way BP/scripts/main.js spawns them (beams, orbs, auras, domain).
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
const RP = process.argv[2], OUT = process.argv[3];
const load = (ch, form) => ({
  geo: JSON.parse(fs.readFileSync(path.join(RP, "models/entity", `${ch}_${form}.geo.json`)))["minecraft:geometry"][0],
  tex: "data:image/png;base64," + fs.readFileSync(path.join(RP, "textures/entity", ch, `${form}.png`)).toString("base64"),
});
const anims = JSON.parse(fs.readFileSync(path.join(RP, "animations/ab.animation.json"))).animations;
const pose = (name) => {
  if (!name) return {};
  const out = {};
  for (const [b, v] of Object.entries(anims[`animation.ab.${name}`].bones)) out[b] = v.rotation.map((x) => (typeof x === "number" ? x : 0));
  return out;
};
const need = {};
const scenes = [
  { title: "Goku — Right jab", caster: ["goku", "base", "jab_r"], target: ["vegeta", "base"], fx: "hit", near: 1 },
  { title: "Goku — Knee", caster: ["goku", "base", "knee"], target: ["vegeta", "base"], fx: "hit", near: 1 },
  { title: "Goku — Rush barrage", caster: ["goku", "ssj", "rush"], target: ["vegeta", "ssj"], fx: "rush", near: 1 },
  { title: "Goku — Uppercut", caster: ["goku", "ssb", "upper"], target: ["vegeta", "ssb"], fx: "upper", near: 1 },
  { title: "Goku — Roundhouse finisher", caster: ["goku", "ui", "round"], target: ["vegeta", "ue"], fx: "big", near: 1 },
  { title: "Vegeta — Left jab", caster: ["vegeta", "base", "jab_l"], target: ["goku", "base"], fx: "hit", near: 1 },
  { title: "Vegeta — Elbow", caster: ["vegeta", "ssj", "elbow"], target: ["goku", "ssj"], fx: "hit", near: 1 },
  { title: "Vegeta — Front kick", caster: ["vegeta", "ssb", "kick"], target: ["goku", "ssb"], fx: "hit", near: 1 },
  { title: "Vegeta — Point-blank ki", caster: ["vegeta", "ue", "pose_point"], target: ["goku", "ui"], fx: "kiburst", near: 1 },
  { title: "Gojo — Jab", caster: ["gojo", "blindfold", "jab_r"], target: ["vegeta", "base"], fx: "chit", near: 1 },
  { title: "Gojo — Blinks behind…", caster: ["gojo", "eyes", null], target: ["goku", "base"], fx: "blink", behind: 1 },
  { title: "…and roundhouse kicks", caster: ["gojo", "eyes", "round"], target: ["goku", "base"], fx: "cbig", near: 1 },
  { title: "Gojo — Knee", caster: ["gojo", "blindfold", "knee"], target: ["goku", "ssj"], fx: "chit", near: 1 },
  { title: "Gojo — Uppercut", caster: ["gojo", "eyes", "upper"], target: ["vegeta", "ssj"], fx: "cupper", near: 1 },
  { title: "Gojo — Black Flash finisher", caster: ["gojo", "eyes", "kick"], target: ["vegeta", "base"], fx: "blackflash2", near: 1 },
];
for (const s of scenes) { need[s.caster[0] + ":" + s.caster[1]] = 1; if (s.target) need[s.target[0] + ":" + s.target[1]] = 1; }
const models = {};
for (const k of Object.keys(need)) { const [c, f] = k.split(":"); models[k] = load(c, f); }
for (const s of scenes) s.pose = s.caster[2] === "rush" ? { rightArm: [-120, 10, 0], leftArm: [-65, -10, 0], body: [8, 10, 0], rightLeg: [-15, 0, 0], leftLeg: [15, 0, 0] } : pose(s.caster[2]);
const orb = "data:image/png;base64," + fs.readFileSync(path.join(RP, "textures/particle/ab_orb.png")).toString("base64");
const three = fs.readFileSync(path.join(__dirname, "node_modules/three/build/three.module.js"), "utf8");
const COLS = 5, W = 420, H = 330;
const rows = Math.ceil(scenes.length / COLS);

const html = `<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:#111;font-family:sans-serif">
<div id="labels"></div>
<script type="module">
${three.replace(/export \{[\s\S]*?\};\s*$/m, "")}
const scenes = ${JSON.stringify(scenes)}, models = ${JSON.stringify(models)}, ORB = "${orb}";
const COLS = ${COLS}, W = ${W}, H = ${H}, ROWS = ${rows};
const renderer = new WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W * COLS, H * ROWS); renderer.setScissorTest(true); renderer.autoClear = false;
document.body.appendChild(renderer.domElement);
const L = new TextureLoader(); const ld = (s) => new Promise((r) => L.load(s, r));
const order = ["px", "nx", "py", "ny", "pz", "nz"];
const boxRects = (u, v, s) => { const [w, h, d] = s; return { px: [u, v + d, d, h], nx: [u + d + w, v + d, d, h], py: [u + d, v, w, d], ny: [u + d + w, v, w, d], pz: [u + 2 * d + w, v + d, w, h], nz: [u + d, v + d, w, h] }; };
const D = Math.PI / 180;
async function build(key, poseRot) {
  const m = models[key];
  const tex = await ld(m.tex); tex.magFilter = NearestFilter; tex.minFilter = NearestFilter; tex.colorSpace = SRGBColorSpace;
  const T = m.geo.description.texture_width;
  const mat = new MeshLambertMaterial({ map: tex, alphaTest: 0.5, side: DoubleSide });
  const groups = {}, root = new Group();
  for (const b of m.geo.bones) {
    const g = new Group(); const pv = [-(b.pivot[0]), b.pivot[1], b.pivot[2]];
    g.userData.pv = pv; groups[b.name] = g;
    const r = poseRot[b.name]; if (r) { g.rotation.order = "ZYX"; g.rotation.set(-r[0] * D, -r[1] * D, r[2] * D); }
  }
  for (const b of m.geo.bones) {
    const g = groups[b.name], par = b.parent ? groups[b.parent] : root;
    const ppv = b.parent ? groups[b.parent].userData.pv : [0, 0, 0];
    g.position.set(g.userData.pv[0] - ppv[0], g.userData.pv[1] - ppv[1], g.userData.pv[2] - ppv[2]);
    par.add(g);
    for (const c of b.cubes || []) {
      const inf = c.inflate || 0;
      const geo = new BoxGeometry(c.size[0] + 2 * inf, c.size[1] + 2 * inf, c.size[2] + 2 * inf);
      const uv = geo.attributes.uv, rr = boxRects(c.uv[0], c.uv[1], c.size);
      order.forEach((f, fi) => { const [x, y, w, h] = rr[f]; const u0 = x / T, u1 = (x + w) / T, vt = 1 - y / T, vb = 1 - (y + h) / T;
        [[u0, vt], [u1, vt], [u0, vb], [u1, vb]].forEach((q, k) => uv.setXY(fi * 4 + k, q[0], q[1])); });
      const mesh = new Mesh(geo, mat);
      const from = [-(c.origin[0] + c.size[0]), c.origin[1], c.origin[2]];
      const ctr = [from[0] + c.size[0] / 2, from[1] + c.size[1] / 2, from[2] + c.size[2] / 2];
      const pv = g.userData.pv;
      if (c.rotation) {
        const cp = [-c.pivot[0], c.pivot[1], c.pivot[2]];
        const pg = new Group(); pg.position.set(cp[0] - pv[0], cp[1] - pv[1], cp[2] - pv[2]); pg.rotation.order = "ZYX";
        pg.rotation.set(-c.rotation[0] * D, -c.rotation[1] * D, c.rotation[2] * D);
        mesh.position.set(ctr[0] - cp[0], ctr[1] - cp[1], ctr[2] - cp[2]); pg.add(mesh); g.add(pg);
      } else { mesh.position.set(ctr[0] - pv[0], ctr[1] - pv[1], ctr[2] - pv[2]); g.add(mesh); }
    }
  }
  return root;
}
// ---- particles (units: 16 = one block)
let orbTex;
function P(scene, p, c, s, solid = false, stretch = 1) {
  const m = new SpriteMaterial({ map: orbTex, color: new Color(c[0], c[1], c[2]), blending: solid ? NormalBlending : AdditiveBlending, depthWrite: false, transparent: true, opacity: solid ? (scene.userData.dim || 0.85) : 0.42 });
  const sp = new Sprite(m); sp.position.set(p[0], p[1], p[2]); sp.scale.set(s, s * stretch, 1); scene.add(sp);
}
const rnd = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
const sph = () => { const u = rnd() * 2 - 1, t = rnd() * 6.283, q = Math.sqrt(1 - u * u); return [q * Math.cos(t), u, q * Math.sin(t)]; };
const add = (a, b, k = 1) => [a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k];
const C = { white: [1, 1, 1], kame: [0.35, 0.75, 1], gold: [1, 0.85, 0.2], ssb: [0.2, 0.7, 1], silver: [0.85, 0.88, 1], flash: [1, 0.95, 0.4],
  galick: [0.75, 0.3, 1], bigbang: [0.6, 0.85, 1], ego: [0.75, 0.2, 0.95], hakai: [0.45, 0.05, 0.6], blue: [0.15, 0.45, 1], red: [1, 0.12, 0.12],
  purple: [0.7, 0.2, 1], void: [0.04, 0.04, 0.1], black: [0.02, 0.02, 0.02] };
const HAND = [0, 19, -12], TGT = [0, 16, -100];
function beam(sc, color, width, from = HAND, to = TGT) {
  const d = [to[0] - from[0], to[1] - from[1], to[2] - from[2]], n = Math.hypot(...d);
  for (let s = 0; s <= n; s += 4) { const p = add(from, d, s / n); P(sc, p, color, width * 2.2); P(sc, p, color, width * 1.4); if (s % 8 === 0) P(sc, p, C.white, width * 0.5); }
  burst(sc, to, color, width * 2.2, 70);
}
function burst(sc, c, color, r, n) { for (let i = 0; i < n; i++) { const v = sph(), k = rnd(); P(sc, add(c, v, r * k), i % 4 ? color : C.white, 5 + 7 * (1 - k)); } P(sc, c, color, r * 1.2); }
function sphere(sc, c, r, color, n, size, solid = false) { for (let i = 0; i < n; i++) P(sc, add(c, sph(), r), color, size, solid); }
function aura(sc, color, n = 90) { for (let i = 0; i < n; i++) { const a = rnd() * 6.283, rr = 7 + rnd() * 6; P(sc, [Math.cos(a) * rr, 2 + rnd() * 36, Math.sin(a) * rr], color, 4 + rnd() * 3, false, 3.2); } }
const HIT = [0, 22, -20];
const FX = {
  hit(sc) { burst(sc, HIT, C.gold, 10, 30); P(sc, HIT, C.white, 16); },
  chit(sc) { burst(sc, HIT, C.blue, 10, 30); P(sc, HIT, C.white, 14); },
  rush(sc) { for (let i = 0; i < 8; i++) { const p = [rnd() * 10 - 5, 18 + rnd() * 10, -18 - rnd() * 4]; P(sc, p, C.gold, 10); P(sc, p, C.white, 5); }
    for (let k = 0; k < 4; k++) P(sc, [k % 2 ? 5 : -5, 22 - k, -12 - k], C.white, 7, false, 0.4); aura(sc, C.gold, 60); },
  upper(sc) { burst(sc, [0, 30, -20], C.ssb, 14, 40); P(sc, [0, 30, -20], C.white, 18); aura(sc, C.ssb, 60); },
  big(sc) { burst(sc, HIT, C.silver, 18, 70); for (let i = 0; i < 24; i++) { const a = i / 24 * 6.283; P(sc, [Math.cos(a) * 16, 22 + Math.sin(a) * 16, -22], C.white, 4); } aura(sc, C.silver, 60); },
  kiburst(sc) { burst(sc, [0, 20, -24], C.bigbang, 22, 110); P(sc, [0, 20, -14], C.bigbang, 14); aura(sc, C.ego, 60); },
  blink(sc) { for (let i = 0; i < 40; i++) P(sc, [rnd() * 8 - 4, rnd() * 32, rnd() * 4 - 2], C.white, 5, false, 2.5); P(sc, [0, 18, -50], C.blue, 10); },
  cbig(sc) { burst(sc, HIT, C.blue, 16, 70); for (let i = 0; i < 24; i++) { const a = i / 24 * 6.283; P(sc, [Math.cos(a) * 15, 22 + Math.sin(a) * 15, -22], C.blue, 4); } },
  cupper(sc) { burst(sc, [0, 30, -20], C.blue, 14, 40); P(sc, [0, 30, -20], C.white, 16); },
  blackflash2(sc) { const c = [0, 16, -20]; sphere(sc, c, 7, C.black, 60, 8, true); burst(sc, c, C.red, 15, 80);
    for (let i = 0; i < 14; i++) { const v = sph(); P(sc, add(c, v, 13), C.black, 9, true, 0.3); } },
  kame(sc) { beam(sc, C.kame, 11); },
  galick(sc) { beam(sc, C.galick, 10); },
  flash(sc) { beam(sc, C.flash, 19); aura(sc, C.gold, 60); },
  spirit(sc) { const c = [0, 100, 0]; sphere(sc, c, 34, C.kame, 420, 9); P(sc, c, C.kame, 80); P(sc, c, C.kame, 60);
    for (let i = 0; i < 70; i++) { const v = sph(); P(sc, add(c, v, 60 + rnd() * 40), C.kame, 3, false, 1); } },
  aura_blue(sc) { aura(sc, C.ssb, 160); for (let i = 0; i < 40; i++) { const a = i / 40 * 6.283; P(sc, [Math.cos(a) * 26, 1, Math.sin(a) * 26], C.ssb, 9); } },
  ui(sc) { aura(sc, C.silver, 110); for (let k = 1; k <= 2; k++) for (let i = 0; i < 25; i++) P(sc, [k * 9 + rnd() * 4, 4 + rnd() * 28, rnd() * 4], C.silver, 5, false, 2);
    beam(sc, C.ego, 5, [0, 19, -86], [6, 20, 10]); },
  dragon(sc) { const from = [0, 20, -14], to = [0, 18, -92];
    for (let s = 0; s < 1; s += 0.012) { const p = add(from, [to[0] - from[0], to[1] - from[1], to[2] - from[2]], s); const a = s * 30;
      P(sc, [p[0] + Math.cos(a) * 12, p[1] + Math.sin(a) * 12, p[2]], C.gold, 11); }
    burst(sc, to, C.gold, 30, 90); aura(sc, C.gold, 60); },
  bigbang(sc) { P(sc, [0, 19, -50], C.bigbang, 30); P(sc, [0, 19, -50], C.white, 16); for (let s = -14; s > -50; s -= 3) P(sc, [0, 19, s], C.bigbang, 10);
    burst(sc, TGT, C.bigbang, 40, 120); aura(sc, C.ssb, 70); },
  hakai(sc) { const c = [0, 18, -90]; for (let k = 0; k < 3; k++) sphere(sc, c, 10 + k * 7, k % 2 ? C.ego : C.hakai, 70, 8, true); P(sc, [0, 19, -14], C.hakai, 14, true); aura(sc, C.ego, 90); },
  infinity(sc) { for (let r of [14, 17]) for (let i = 0; i < 26; i++) { const a = i / 26 * 6.283; P(sc, [Math.cos(a) * r, 18 + Math.sin(a * 3) * 2, Math.sin(a) * r - 4], C.blue, 4); }
    for (let i = 0; i < 6; i++) P(sc, [rnd() * 6 - 3, 16 + rnd() * 6, -22 - rnd() * 4], C.white, 6); },
  blue(sc) { const c = [0, 20, -88]; P(sc, c, C.blue, 40); P(sc, c, C.white, 16);
    for (let i = 0; i < 160; i++) { const a = rnd() * 6.283, rr = 8 + rnd() * 34; P(sc, [c[0] + Math.cos(a) * rr, c[1] + (rnd() - 0.5) * 16, c[2] + Math.sin(a) * rr], C.blue, 3 + rnd() * 3); }
    for (let i = 0; i < 30; i++) { const a = i / 30 * 6.283; P(sc, [c[0] + Math.cos(a) * 30, c[1] + Math.sin(a * 2) * 6, c[2] + Math.sin(a) * 30], C.blue, 6); } },
  red(sc) { for (let s = -14; s > -88; s -= 5) P(sc, [0, 20, s], C.red, 7); burst(sc, [0, 18, -98], C.red, 46, 160); },
  purple(sc) { const c = [0, 22, -56]; sphere(sc, c, 22, C.purple, 260, 10); P(sc, c, C.purple, 50); P(sc, c, C.purple, 30); P(sc, c, C.white, 10);
    for (let s = -14; s > -34; s -= 3) P(sc, [0, 22, s], C.purple, 18); P(sc, [-12, 22, -10], C.blue, 12); P(sc, [12, 22, -10], C.red, 12); },
  domain(sc) { sc.userData.dim = 0.3; for (let i = 0; i < 900; i++) { const v = sph(); if (v[0] > 0.2) continue; P(sc, add([0, 18, -48], v, 96), C.void, 22, true); } sphere(sc, [0, 18, -48], 80, C.white, 220, 3);
    for (let i = 0; i < 40; i++) { const v = sph(); P(sc, add([0, 18, -48], v, rnd() * 70), [0.6, 0.9, 1], 2.5); }
    for (let i = 0; i < 10; i++) { const a = i / 10 * 6.283; P(sc, [Math.cos(a) * 6, 38, -96 + Math.sin(a) * 6], C.white, 3); } },
  blackflash(sc) { const c = [0, 20, -22]; sphere(sc, c, 8, C.black, 60, 8, true); burst(sc, c, C.red, 16, 70);
    for (let i = 0; i < 14; i++) { const v = sph(); P(sc, add(c, v, 14), C.black, 9, true, 0.3); } },
};
(async () => {
  orbTex = await ld(ORB);
  for (let i = 0; i < scenes.length; i++) {
    const s = scenes[i];
    const sc = new Scene(); sc.background = new Color(s.fx === "domain" ? 0x10142a : 0x7fa8d8);
    sc.add(new AmbientLight(0xffffff, s.fx === "domain" ? 2.2 : 1.5)); const sun = new DirectionalLight(0xffffff, 1.3); sun.position.set(40, 60, 20); sc.add(sun);
    const ground = new Mesh(new PlaneGeometry(600, 600), new MeshLambertMaterial({ color: s.fx === "domain" ? 0x0b0d1c : 0x5c9a3c }));
    ground.rotation.x = -Math.PI / 2; sc.add(ground);
    const caster = await build(s.caster[0] + ":" + s.caster[1], s.pose); sc.add(caster);
    if (s.target) { const t = await build(s.target[0] + ":" + s.target[1], {}); t.position.set(0, 0, s.near ? -30 : -104); t.rotation.y = Math.PI; if (s.behind) { t.position.set(0, 0, -30); t.rotation.y = 0; caster.position.set(0, 0, -58); caster.rotation.y = Math.PI; } if (s.fx === "red") { t.rotation.x = -0.35; t.position.z = -118; } sc.add(t); }
    FX[s.fx](sc);
    const cam = new PerspectiveCamera(42, W / H, 1, 2000);
    if (s.fx === "spirit") { cam.position.set(95, 70, 70); cam.lookAt(0, 55, -10); }
    else if (s.fx === "aura_blue" || s.fx === "infinity") { cam.position.set(55, 34, -70); cam.lookAt(0, 22, -20); }
    else if (s.near || s.behind) { cam.position.set(70, 34, -4); cam.lookAt(0, 20, -22); } else { cam.position.set(120, 55, 10); cam.lookAt(0, 20, -52); }
    const col = i % COLS, row = Math.floor(i / COLS), y = (ROWS - 1 - row) * H;
    renderer.setViewport(col * W, y, W, H); renderer.setScissor(col * W, y, W, H); renderer.clear(); renderer.render(sc, cam);
    const d = document.createElement("div");
    d.textContent = s.title;
    d.style.cssText = "position:absolute;left:" + (col * W + 8) + "px;top:" + (row * H + 8) + "px;color:#fff;font:bold 17px sans-serif;text-shadow:0 0 4px #000,0 0 2px #000;padding:3px 8px;background:rgba(0,0,0,.45);border-radius:6px";
    document.getElementById("labels").appendChild(d);
  }
  document.title = "done";
})();
</script></body></html>`;
const file = path.join(__dirname, "showcase.html");
fs.writeFileSync(file, html);
(async () => {
  const browser = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage({ viewport: { width: W * COLS, height: H * rows } });
  page.on("pageerror", (e) => console.log("pageerror:", e.stack));
  await page.goto("file://" + file);
  await page.waitForFunction(() => document.title === "done", null, { timeout: 60000 });
  await page.screenshot({ path: OUT });
  await browser.close();
  console.log("saved", OUT);
})();
