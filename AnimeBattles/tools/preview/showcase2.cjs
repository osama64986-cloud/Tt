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
const num = (x, d) => (typeof x === "number" ? x : (parseFloat(String(x).replace(/^[^0-9.-]*/, "")) || d));
const pose = (name) => {
  if (!name) return {};
  const out = {};
  for (const [b, v] of Object.entries(anims[`animation.ab.${name}`].bones)) {
    out[b] = { r: (v.rotation || [0, 0, 0]).map((x) => (typeof x === "number" ? x : -90)), s: v.scale ? v.scale.map((x) => num(x, 1)) : null };
  }
  return out;
};
const need = {};
const scenes = [
  { title: "Itadori — Black Flash", caster: ["yuji", "base", "jab_r"], target: ["luffy", "base"], fx: "bflash", near: 1 },
  { title: "Itadori (final) — Dismantle", caster: ["yuji_final", "base", "slash"], target: ["sukuna", "megumi"], fx: "dismantle" },
  { title: "Itadori (final) — Piercing Blood", caster: ["yuji_final", "base", "pose_beam"], target: ["sukuna", "heian"], fx: "piercing" },
  { title: "Sukuna (Yuji's body) — Cleave", caster: ["sukuna", "yuji", "slash"], target: ["yuji_final", "base"], fx: "cleave", near: 1 },
  { title: "Sukuna (Megumi) — Mahoraga's wheel", caster: ["sukuna", "megumi", null], target: ["gojo", "eyes"], fx: "wheel", near: 1 },
  { title: "Sukuna (Megumi) — World-Cutting Slash", caster: ["sukuna", "megumi", "handsign"], target: ["gojo", "eyes"], fx: "world" },
  { title: "Sukuna (Heian) — Fuga", caster: ["sukuna", "heian", "fuga"], target: ["yuji_final", "base"], fx: "fuga" },
  { title: "Sukuna (Heian) — Malevolent Shrine", caster: ["sukuna", "heian", "handsign"], target: ["yuji_final", "base"], fx: "shrine" },
  { title: "Luffy — Gum-Gum Pistol", caster: ["luffy", "base", "pistol"], target: ["yuji", "base"], fx: "pistol" },
  { title: "Luffy Gear 2 — Jet Gatling", caster: ["luffy", "g2", "gatling"], target: ["yuji", "base"], fx: "gatling" },
  { title: "Luffy Gear 3 — Elephant Gun", caster: ["luffy", "g3", "giant_fist"], target: ["yuji_final", "base"], fx: "elephant" },
  { title: "Luffy Boundman — Kong Gun", caster: ["luffy", "g4b", "giant_fist"], target: ["sukuna", "yuji"], fx: "kong" },
  { title: "Luffy Snakeman — King Cobra", caster: ["luffy", "g4s", "pistol"], target: ["sukuna", "yuji"], fx: "cobra" },
  { title: "Luffy Tankman — Conqueror's Haki", caster: ["luffy", "g4t", "pose_raise"], target: ["yuji", "base"], fx: "conq" },
  { title: "Luffy Gear 5 — Bajrang Gun", caster: ["luffy", "g5", "giant_up"], target: ["gojo", "eyes"], fx: "bajrang" },
];
for (const s of scenes) { need[s.caster[0] + ":" + s.caster[1]] = 1; if (s.target) need[s.target[0] + ":" + s.target[1]] = 1; }
const models = {};
for (const k of Object.keys(need)) { const [c, f] = k.split(":"); models[k] = load(c, f); }
for (const s of scenes) s.pose = s.poseOverride || s.caster[2] === "attack" ? { rightArm: [-100, 0, 0], body: [0, 15, 0] } : pose(s.caster[2]);
const vfxTex = [...Array(15).keys()].map((i) => "data:image/png;base64," + fs.readFileSync(path.join(RP, "textures/entity/vfx", `vfx_${i}.png`)).toString("base64"));
const orb = "data:image/png;base64," + fs.readFileSync(path.join(RP, "textures/particle/ab_orb.png")).toString("base64");
const three = fs.readFileSync(path.join(__dirname, "node_modules/three/build/three.module.js"), "utf8");
const COLS = 5, W = 420, H = 330;
const rows = Math.ceil(scenes.length / COLS);

const html = `<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:#111;font-family:sans-serif">
<div id="labels"></div>
<script type="module">
${three.replace(/export \{[\s\S]*?\};\s*$/m, "")}
const scenes = ${JSON.stringify(scenes)}, models = ${JSON.stringify(models)}, ORB = "${orb}", VFXT = ${JSON.stringify(vfxTex)};
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
    const pr = poseRot[b.name]; if (pr) { const r = pr.r || pr; g.rotation.order = "ZYX"; g.rotation.set(-r[0] * D, -r[1] * D, r[2] * D); if (pr.s) g.scale.set(...pr.s); }
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
let orbTex; const VT = [];
const vmat = (slot, op, add) => new MeshBasicMaterial({ map: VT[slot], transparent: true, opacity: op, depthWrite: false, side: DoubleSide, blending: NormalBlending });
function vbox(g, w, h, d, z, rz, rx, ry, m) { const b = new Mesh(new BoxGeometry(w, h, d), m); b.position.z = z; const p = new Group(); p.rotation.set(rx || 0, ry || 0, rz || 0); p.add(b); g.add(p); }
function vBeam(sc, from, to, slot, size) {
  const g = new Group(); g.position.set(...from); g.lookAt(new Vector3(...to)); const L = Math.hypot(to[0] - from[0], to[1] - from[1], to[2] - from[2]);
  vbox(g, 4 * size, 4 * size, L, L / 2, 0, 0, 0, vmat(slot, 0.98, false));
  vbox(g, 10 * size, 10 * size, L, L / 2, 0, 0, 0, vmat(slot, 0.45, true)); vbox(g, 10 * size, 10 * size, L, L / 2, Math.PI / 4, 0, 0, vmat(slot, 0.45, true));
  for (const [x, y] of [[6.75, 0], [-6.75, 0], [0, 6.75], [0, -6.75]]) { const b = new Mesh(new BoxGeometry(1.5 * size, 1.5 * size, L), vmat(slot, 0.8, true)); b.position.set(x * size, y * size, L / 2); g.add(b); }
  vbox(g, 12 * size, 12 * size, 12 * size, 0, 0, 0, 0, vmat(slot, 0.7, true)); vbox(g, 12 * size, 12 * size, 12 * size, 0, 0, Math.PI / 4, Math.PI / 4, vmat(slot, 0.7, true));
  sc.add(g);
}
function vSlash(sc, c, slot, size, rz, ry) { const g = new Group(); g.position.set(...c); g.rotation.set(0, ry || 0, rz || 0);
  const m1 = new Mesh(new BoxGeometry(20 * size, 0.6 * size, 3 * size), vmat(slot, 0.98, false)); g.add(m1);
  const m2 = new Mesh(new BoxGeometry(26 * size, 1.4 * size, 5 * size), vmat(slot, 0.35, true)); g.add(m2); sc.add(g); }
function vOrb(sc, c, slot, size) {
  const g = new Group(); g.position.set(...c);
  vbox(g, 7.2 * size, 7.2 * size, 7.2 * size, 0, 0, 0, 0, vmat(slot, 0.98, false)); vbox(g, 7.2 * size, 7.2 * size, 7.2 * size, 0, 0, Math.PI / 4, Math.PI / 4, vmat(slot, 0.98, false));
  for (const r of [[0, 0, 0], [Math.PI / 4, 0, 0], [0, Math.PI / 4, 0], [0, 0, Math.PI / 4]]) vbox(g, 16 * size, 16 * size, 16 * size, 0, r[2], r[0], r[1], vmat(slot, 0.35, true));
  sc.add(g);
}
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
const FX = {
  wheel(sc) { const c = [0, 46, 0]; for (let k = 0; k < 8; k++) { const a = k / 8 * 6.283; for (let r = 3; r <= 12; r += 3) P(sc, [c[0] + Math.cos(a) * r, c[1], c[2] + Math.sin(a) * r], C.gold, 3.5); }
    for (let i = 0; i < 40; i++) { const a = i / 40 * 6.283; P(sc, [Math.cos(a) * 12, 46, Math.sin(a) * 12], C.gold, 3); } },
  world(sc) { for (let k = -3; k <= 3; k++) vSlash(sc, [0, 20, -100 + k * 10], 10, 3, 0.35, 1.57); P(sc, [0, 20, -100], C.white, 50); },
  divergent(sc) { P(sc, [0, 22, -20], C.white, 16); vOrb(sc, [0, 22, -24], 5, 0.7); for (let i = 0; i < 26; i++) { const a = i / 26 * 6.283; P(sc, [Math.cos(a) * 14, 22 + Math.sin(a) * 14, -24], C.blue, 3); } },
  bflash(sc) { const c = [0, 22, -20]; vOrb(sc, c, 13, 1.1); for (let i = 0; i < 18; i++) { const v = sph(); for (let k = 1; k < 6; k++) P(sc, add(c, v, k * 3.4), i % 2 ? C.red : C.black, 3, i % 2 === 0); } },
  dismantle(sc) { for (let k = 0; k < 3; k++) vSlash(sc, [0, 20 + k * 3, -30 - k * 22], 10, 1.1, 0.3 + k * 0.6, 0); },
  piercing(sc) { vBeam(sc, HAND, TGT, 12, 0.32); vOrb(sc, TGT, 12, 0.8); },
  supernova(sc) { for (let k = 0; k < 5; k++) { const a = k * 1.256; vOrb(sc, [Math.cos(a) * 22, 38, Math.sin(a) * 22], 12, 0.4); } },
  cleave(sc) { for (let k = 0; k < 5; k++) vSlash(sc, [rnd() * 6 - 3, 16 + k * 4, -30], 4, 0.6, rnd() * 3, 1.57); },
  fuga(sc) { vBeam(sc, HAND, TGT, 11, 0.9); vOrb(sc, TGT, 11, 4); for (let i = 0; i < 60; i++) { const v = sph(); P(sc, add(TGT, v, 30 + rnd() * 20), C.red, 4, false, 2); } },
  shrine(sc) { sphere(sc, [0, 18, -50], 90, [0.5, 0.02, 0.05], 700, 22, true); for (let k = 0; k < 14; k++) vSlash(sc, [rnd() * 80 - 40, 4 + rnd() * 40, -20 - rnd() * 70], 10, 1, rnd() * 3, rnd() * 3); },
  pistol(sc) { P(sc, [0, 20, -96], C.white, 18); for (let i = 0; i < 10; i++) { const v = sph(); P(sc, add([0, 20, -96], v, 8), C.white, 3, false, 2); } },
  gatling(sc) { for (let i = 0; i < 12; i++) { const p = [rnd() * 16 - 8, 14 + rnd() * 14, -60 - rnd() * 30]; P(sc, p, C.white, 9); } aura(sc, [1, 0.75, 0.78], 80); },
  elephant(sc) { vOrb(sc, [0, 22, -98], 13, 2); for (let i = 0; i < 36; i++) { const a = i / 36 * 6.283; P(sc, [Math.cos(a) * 30, 1, -100 + Math.sin(a) * 30], C.white, 5); } },
  kong(sc) { vOrb(sc, [0, 22, -100], 13, 3); aura(sc, [1, 0.8, 0.8], 70); for (let i = 0; i < 36; i++) { const a = i / 36 * 6.283; P(sc, [Math.cos(a) * 40, 1, -100 + Math.sin(a) * 40], C.white, 6); } },
  cobra(sc) { for (let s = 0; s < 1; s += 0.03) P(sc, [Math.sin(s * 14) * 10, 20, -14 - s * 82], [0.3, 0.05, 0.08], 7, true); aura(sc, [1, 0.8, 0.8], 60); },
  bajrang(sc) { vOrb(sc, [0, 4, -100], 14, 5); for (let i = 0; i < 48; i++) { const a = i / 48 * 6.283; P(sc, [Math.cos(a) * 60, 1, -100 + Math.sin(a) * 60], C.white, 7); } aura(sc, [1, 1, 0.9], 90); },
  conq(sc) { for (let i = 0; i < 40; i++) { const v = sph(); const d = [v[0], Math.abs(v[1]) * 0.3, v[2]]; for (let k = 2; k < 9; k++) P(sc, add([0, 18, 0], d, k * 6 + rnd() * 3), i % 2 ? [0.6, 0.05, 0.1] : C.black, 4, i % 2 === 0); }
    for (let i = 0; i < 40; i++) { const a = i / 40 * 6.283; P(sc, [Math.cos(a) * 50, 1, Math.sin(a) * 50], [0.6, 0.05, 0.1], 6); } },
  kame(sc) { vBeam(sc, HAND, TGT, 0, 0.95); vOrb(sc, TGT, 0, 1.6); for (let i = 0; i < 30; i++) { const v = sph(); P(sc, add(TGT, v, 14 + rnd() * 10), C.kame, 3, false, 3); } },
  galick(sc) { vBeam(sc, HAND, TGT, 1, 0.95); vOrb(sc, TGT, 1, 1.5); for (let i = 0; i < 30; i++) { const v = sph(); P(sc, add(TGT, v, 14 + rnd() * 10), C.galick, 3, false, 3); } },
  flash(sc) { vBeam(sc, HAND, TGT, 2, 1.95); vOrb(sc, TGT, 2, 2.4); aura(sc, C.gold, 60); },
  spirit(sc) { const c = [0, 100, 0]; vOrb(sc, c, 8, 4.4);
    for (let i = 0; i < 70; i++) { const v = sph(); P(sc, add(c, v, 60 + rnd() * 40), C.kame, 3, false, 1); } },
  aura_blue(sc) { aura(sc, C.ssb, 160); for (let i = 0; i < 40; i++) { const a = i / 40 * 6.283; P(sc, [Math.cos(a) * 26, 1, Math.sin(a) * 26], C.ssb, 9); } },
  ui(sc) { aura(sc, C.silver, 110); for (let k = 1; k <= 2; k++) for (let i = 0; i < 25; i++) P(sc, [k * 9 + rnd() * 4, 4 + rnd() * 28, rnd() * 4], C.silver, 5, false, 2);
    beam(sc, C.ego, 5, [0, 19, -86], [6, 20, 10]); },
  dragon(sc) { const from = [0, 20, -14], to = [0, 18, -92];
    for (let s = 0; s < 1; s += 0.012) { const p = add(from, [to[0] - from[0], to[1] - from[1], to[2] - from[2]], s); const a = s * 30;
      P(sc, [p[0] + Math.cos(a) * 12, p[1] + Math.sin(a) * 12, p[2]], C.gold, 11); }
    burst(sc, to, C.gold, 30, 90); aura(sc, C.gold, 60); },
  bigbang(sc) { vOrb(sc, [0, 19, -50], 3, 0.9); for (let s = -14; s > -44; s -= 3) P(sc, [0, 19, s], C.bigbang, 6); vOrb(sc, TGT, 3, 3.4); aura(sc, C.ssb, 70); },
  hakai(sc) { const c = [0, 18, -90]; vOrb(sc, [0, 19, -40], 7, 0.7); for (let k = 0; k < 3; k++) sphere(sc, c, 10 + k * 7, k % 2 ? C.ego : C.hakai, 70, 8, true); P(sc, [0, 19, -14], C.hakai, 14, true); aura(sc, C.ego, 90); },
  infinity(sc) { for (let r of [14, 17]) for (let i = 0; i < 26; i++) { const a = i / 26 * 6.283; P(sc, [Math.cos(a) * r, 18 + Math.sin(a * 3) * 2, Math.sin(a) * r - 4], C.blue, 4); }
    for (let i = 0; i < 6; i++) P(sc, [rnd() * 6 - 3, 16 + rnd() * 6, -22 - rnd() * 4], C.white, 6); },
  blue(sc) { const c = [0, 20, -88]; vOrb(sc, c, 5, 1.8);
    for (let i = 0; i < 160; i++) { const a = rnd() * 6.283, rr = 8 + rnd() * 34; P(sc, [c[0] + Math.cos(a) * rr, c[1] + (rnd() - 0.5) * 16, c[2] + Math.sin(a) * rr], C.blue, 3 + rnd() * 3); }
    for (let i = 0; i < 30; i++) { const a = i / 30 * 6.283; P(sc, [c[0] + Math.cos(a) * 30, c[1] + Math.sin(a * 2) * 6, c[2] + Math.sin(a) * 30], C.blue, 6); } },
  red(sc) { for (let s = -14; s > -80; s -= 5) P(sc, [0, 20, s], C.red, 5); vOrb(sc, [0, 20, -60], 4, 0.6); vOrb(sc, [0, 18, -100], 4, 2.6); for (let i = 0; i < 40; i++) { const v = sph(); P(sc, add([0, 18, -100], v, 24 + rnd() * 14), C.red, 3, false, 3); } },
  purple(sc) { const c = [0, 22, -56]; vOrb(sc, c, 6, 2.5);
    for (let s = -14; s > -34; s -= 3) P(sc, [0, 22, s], C.purple, 18); P(sc, [-12, 22, -10], C.blue, 12); P(sc, [12, 22, -10], C.red, 12); },
  domain(sc) { sc.userData.dim = 0.3; for (let i = 0; i < 900; i++) { const v = sph(); if (v[0] > 0.2) continue; P(sc, add([0, 18, -48], v, 96), C.void, 22, true); } sphere(sc, [0, 18, -48], 80, C.white, 220, 3);
    for (let i = 0; i < 40; i++) { const v = sph(); P(sc, add([0, 18, -48], v, rnd() * 70), [0.6, 0.9, 1], 2.5); }
    for (let i = 0; i < 10; i++) { const a = i / 10 * 6.283; P(sc, [Math.cos(a) * 6, 38, -96 + Math.sin(a) * 6], C.white, 3); } },
  blackflash(sc) { const c = [0, 20, -22]; sphere(sc, c, 8, C.black, 60, 8, true); burst(sc, c, C.red, 16, 70);
    for (let i = 0; i < 14; i++) { const v = sph(); P(sc, add(c, v, 14), C.black, 9, true, 0.3); } },
};
(async () => {
  orbTex = await ld(ORB); for (let i = 0; i < VFXT.length; i++) { VT[i] = await ld(VFXT[i]); VT[i].magFilter = NearestFilter; VT[i].colorSpace = SRGBColorSpace; }
  for (let i = 0; i < scenes.length; i++) {
    const s = scenes[i];
    const sc = new Scene(); sc.background = new Color(s.fx === "domain" ? 0x10142a : s.fx === "shrine" ? 0x2a0508 : 0x7fa8d8);
    sc.add(new AmbientLight(0xffffff, s.fx === "domain" ? 2.2 : 1.5)); const sun = new DirectionalLight(0xffffff, 1.3); sun.position.set(40, 60, 20); sc.add(sun);
    const ground = new Mesh(new PlaneGeometry(600, 600), new MeshLambertMaterial({ color: s.fx === "domain" ? 0x0b0d1c : 0x5c9a3c }));
    ground.rotation.x = -Math.PI / 2; sc.add(ground);
    const caster = await build(s.caster[0] + ":" + s.caster[1], s.pose); sc.add(caster);
    if (s.target) { const t = await build(s.target[0] + ":" + s.target[1], {}); t.position.set(0, 0, -104); t.rotation.y = Math.PI; if (s.fx === "red") { t.rotation.x = -0.35; t.position.z = -118; } sc.add(t); }
    FX[s.fx](sc);
    const cam = new PerspectiveCamera(42, W / H, 1, 2000);
    if (s.fx === "spirit") { cam.position.set(95, 70, 70); cam.lookAt(0, 55, -10); }
    else if (s.fx === "supernova" || s.fx === "conq") { cam.position.set(80, 60, -80); cam.lookAt(0, 20, -10); }
    else if (s.fx === "aura_blue" || s.fx === "infinity") { cam.position.set(55, 34, -70); cam.lookAt(0, 22, -20); }
    else { cam.position.set(120, 55, 10); cam.lookAt(0, 20, -52); }
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
  page.on("pageerror", (e) => console.log("pageerror:", e.message));
  await page.goto("file://" + file);
  await page.waitForFunction(() => document.title === "done", null, { timeout: 180000 });
  await page.screenshot({ path: OUT });
  await browser.close();
  console.log("saved", OUT);
})();
