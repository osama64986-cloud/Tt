// يسجل مهارات اللاعب (القدرات والأسلحة) من السكربت الحقيقي (main.js) بالمحاكي: كل جزيء انطلب (الاسم والمكان والمتغيرات) وحركة كل الكيانات.
// بعدها tools/fit/skill_capture.py يرسم كل تسجيل بجزيئات ماينكرافت الأصلية (نفس الأحجام والأعمار والحركة والألوان من ملفات Mojang).
// الاستعمال: node tools/sim/record_player.mjs <مجلد_الإخراج> [فلتر: اسم مهارة أو سلاح، أو عدة أسماء بفواصل]
//   مثال: node tools/sim/record_player.mjs /tmp/caps meteor,ironfist,sh:dawn_dagger
// اللاعب واقف بـ (0,64,0) ويباوع +z، وقدامه 4 زومبيات (أهداف ثابتة). الأسلحة بليفل 5 والكاتانا بليفل 5 حتى تنفتح كل المهارات.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [outDir, filterArg] = process.argv.slice(2);
if (!outDir) { console.error("usage: record_player.mjs <outdir> [filter]"); process.exit(1); }
fs.mkdirSync(outDir, { recursive: true });
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "shrecp-"));
fs.mkdirSync(path.join(tmp, "scripts"));
for (const f of fs.readdirSync(path.join(root, "AnimePowers/BP/scripts"))) fs.copyFileSync(path.join(root, "AnimePowers/BP/scripts", f), path.join(tmp, "scripts", f));
fs.writeFileSync(path.join(tmp, "package.json"), '{"type":"module"}');
const nm = (n) => { fs.mkdirSync(path.join(tmp, "node_modules", ...n.split("/")), { recursive: true }); return path.join(tmp, "node_modules", ...n.split("/")); };
fs.writeFileSync(nm("@minecraft/server") + "/package.json", '{"name":"@minecraft/server","type":"module","main":"index.js"}');
fs.writeFileSync(nm("@minecraft/server") + "/index.js", fs.readFileSync(path.join(root, "tools/sim/mc_server_stub.js"), "utf8"));
fs.writeFileSync(nm("@minecraft/server-ui") + "/package.json", '{"name":"@minecraft/server-ui","type":"module","main":"index.js"}');
fs.writeFileSync(nm("@minecraft/server-ui") + "/index.js", fs.readFileSync(path.join(root, "tools/sim/mc_ui_stub.js"), "utf8"));
const server = await import(pathToFileURL(path.join(tmp, "node_modules/@minecraft/server/index.js")).href);
const W = server.__sim;
await import(pathToFileURL(path.join(tmp, "scripts/main.js")).href);
W.advance(80);
W.fire("playerSpawn", { player: W.player, initialSpawn: true });
W.advance(100);

const main = fs.readFileSync(path.join(root, "AnimePowers/BP/scripts/main.js"), "utf8");
const skills = [...main.matchAll(/mk\("([a-z]+)", "([a-z]+)", "[^"]+", "(sh:skill_[a-z]+)"/g)].map((m) => ({ id: m[1], power: m[2], item: m[3] }));
const WEAPONS = ["sh:dawn_dagger", "sh:ember_cleaver", "sh:shadow_blade", "sh:shadow_claws", "sh:stone_maul", "sh:sunset_spear", "sh:silver_oath", "sh:dark_katana"];
const filt = filterArg ? new Set(filterArg.split(",")) : null;

const { player, entities, rec } = W;
const zombieHit = (i = 0) => { const z = entities.filter((e) => e._valid && e.typeId === "minecraft:zombie")[i]; if (z) W.fire("entityHitEntity", { damagingEntity: player, hitEntity: z }); };
// إعدادات خاصة: مدة التسجيل، خطوات قبل التسجيل، وأحداث أثناءه (ضربات، استعمال ثاني...)
const SPEC = {
  burst: { pre: [["sh:skill_shards", 40]] },
  subtract: { pre: [["sh:skill_seal", 10]] },
  transfer: { pre: [["sh:skill_seal", 10]] },
  divide: { pre: [["sh:skill_seal", 10]] },
  zero: { pre: [["sh:skill_seal", 10], ["sh:skill_subtract", 10]] },
  adapt: { pre: [["sh:skill_rockskin", 6], ["sh:skill_fangs", 6]] },
  spacerewind: { ticks: 90, during: [[46, () => { player.location = { x: 3, y: 64, z: 2 }; }], [50, () => W.useItem("sh:skill_spacerewind")]] },
  echostrike: { ticks: 70, during: [[8, () => zombieHit(0)]] },
  echoseal: { ticks: 120, during: [[14, () => zombieHit(0)], [30, () => zombieHit(0)]] },
  fangs: { ticks: 60, during: [[10, () => zombieHit(0)], [24, () => zombieHit(1)]] },
  huntereye: { ticks: 60, during: [[16, () => zombieHit(0)]] },
  supernova: { ticks: 140 }, blackhole: { ticks: 170 }, chorus: { ticks: 110 }, gravwell: { ticks: 110 }, orbit: { ticks: 80 },
  constellation: { ticks: 80 }, time: { ticks: 90 }, weight: { ticks: 70 }, silence: { ticks: 70 }, reflect: { ticks: 70 }, boundary: { ticks: 70 },
  crystalshield: { ticks: 80 }, windrun: { ticks: 70 }, windwings: { ticks: 70 }, rockskin: { ticks: 60 }, ironskin: { ticks: 70 },
};
// كل تسجيل معزول: نلغي كل الكيانات القديمة (زومبيات علمتها مهارة سابقة، أشكال، وحوش طبيعية) ونخلي المؤقتات تخلص قبل ما نبدأ
const purge = () => { for (const e of entities) e._valid = false; entities.length = 0; };
const strays = () => { for (const e of entities) if (e._valid && e.typeId !== "minecraft:zombie" && !e.typeId.startsWith("sh:fx_")) e._valid = false; };
function record(name, setup, use, ticks = 100, during = []) {
  rec.on = false; purge(); W.advance(320); purge();
  W.cdReset();
  setup();
  strays();
  rec.on = true; rec.particles.length = 0; rec.frames.length = 0;
  const start = W.tick;
  use();
  for (let i = 0; i < ticks; i++) {
    strays();
    W.snapFrame();
    for (const [t, fn] of during) if (t === i) { try { fn(); } catch (e) { console.error(name, e); } }
    W.advance(1);
  }
  rec.on = false;
  const out = path.join(outDir, name.replace(/[^a-z0-9_]+/gi, "_") + ".json");
  fs.writeFileSync(out, JSON.stringify({ type: "player", name, dist: 6, start, particles: rec.particles, frames: rec.frames }));
  const by = {}; for (const p of rec.particles) by[p.id] = (by[p.id] || 0) + 1;
  const ents = new Set(); for (const f of rec.frames) for (const e of f.ents) if (e.type !== "player" && e.type !== "minecraft:zombie") ents.add(e.type + (e.props && e.props["sh:v"] !== undefined ? "#" + e.props["sh:v"] : ""));
  console.log(`${name.padEnd(26)} ${String(rec.particles.length).padStart(5)} جزيء | ${Object.entries(by).sort((a, b) => b[1] - a[1]).map(([k, v]) => k.replace("minecraft:", "") + "×" + v).join(" ")} | كيانات: ${[...ents].join(" ")}`);
}

for (const s of skills) {
  if (filt && !filt.has(s.id) && !filt.has(s.power)) continue;
  const sp = SPEC[s.id] || {};
  record(s.id, () => {
    W.setState(W.baseState(s.power)); W.spawnZombies(4, false); player.isSneaking = false; player.location = { x: 0, y: 64, z: 0 };
    for (const [it, adv] of sp.pre || []) { W.useItem(it); W.advance(adv); W.cdReset(); }
  }, () => W.useItem(s.item), sp.ticks || 100, sp.during || []);
  if (s.id === "shards") record("shards_sneak", () => { W.setState(W.baseState(s.power)); W.spawnZombies(4, false); player.isSneaking = true; }, () => W.useItem(s.item), 60);
  player.isSneaking = false;
}
const all = {}; for (const id of WEAPONS) all[id] = { lv: 5, xp: 0 };
for (const wid of WEAPONS) {
  if (filt && !filt.has(wid)) continue;
  for (const sneak of [false, true]) {
    record(`${wid.split(":")[1]}_${sneak ? 2 : 1}`, () => {
      W.setState(W.baseState("star")); player.setDynamicProperty("sh_wlv", JSON.stringify(all)); player.setDynamicProperty("sh_kat", JSON.stringify({ lv: 5, xp: 0 }));
      W.spawnZombies(4, true); player.isSneaking = sneak; player.location = { x: 0, y: 64, z: 0 };
    }, () => W.useItem(wid), 100);
    player.isSneaking = false;
  }
}
fs.rmSync(tmp, { recursive: true, force: true });
process.exit(0);
