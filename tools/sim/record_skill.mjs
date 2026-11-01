// يسجل مهارة وحش من السكربت الحقيقي (نفس main.js) ويكتب كل الجزيئات المطلوبة وحركة الكيانات بملف JSON.
// بعدها tools/fit/skill_capture.py يرسمها بجزيئات ماينكرافت الأصلية (حجم، مدة، حركة، ألوان من ملفات Mojang).
// الاستعمال: node tools/sim/record_skill.mjs <نوع_الوحش> <رقم_الحالة> <مسافة_اللاعب> <مخرج.json> [أقصى_تكات] [نسبة_صحة_الوحش]
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [type, stateArg, distArg, outFile, maxArg, hpArg] = process.argv.slice(2);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "shrec-"));
fs.mkdirSync(path.join(tmp, "scripts"));
for (const f of fs.readdirSync(path.join(root, "AnimePowers/BP/scripts"))) {
  let txt = fs.readFileSync(path.join(root, "AnimePowers/BP/scripts", f), "utf8");
  if (process.env.SH_DBG && f === "main.js") txt = txt.replace("if (blocked) { crash(); return; }", "if (blocked) { console.log('BLOCKED', JSON.stringify({ nx, nz, d, L, a: airAt(dim, nx + d.x * 1.6, L.y + 0.6, nz + d.z * 1.6), b: airAt(dim, nx + d.x * 1.6, L.y + 1.8, nz + d.z * 1.6), c: airAt(dim, nx + d.x * 1.6, L.y + 3.0, nz + d.z * 1.6) })); crash(); return; }");
  fs.writeFileSync(path.join(tmp, "scripts", f), txt);
}
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

const want = Number(stateArg), dist = Number(distArg), maxTicks = Number(maxArg || 1400);
const { entities, mkEntity, dims, player, rec } = W;
entities.length = 0;
player.location = { x: 0, y: 64, z: 0 }; player._hp = 5000; player._max = 5000; player._valid = true; player._yaw = 180;
const hp = { "sh:veilfox": [90, 90], "sh:magmamoth": [260, 260], "sh:gloomhorn": [90, 90], "sh:hollow_seer": [90, 90] }[type] || [60, 60];
const m = mkEntity(type, { x: 0, y: 64, z: dist }, dims.overworld, hp[0]); m._max = hp[1]; if (hpArg) m._hp = hp[1] * Number(hpArg); m._yaw = 180; entities.push(m);
// نبقي اللاعب بمكانه، ونترك الوحش يختار مهاراته لحد ما تجي الحالة المطلوبة؛ بعدها نسجل من أول ما تبدأ لحد ما ترجع للخمول
let started = -1, tEnd = -1, prev = null;
const t0 = W.tick;
for (let i = 0; i < maxTicks; i++) {
  const st = m.getProperty("sh:state");
  if (started < 0 && st === want && prev !== want) { started = W.tick; rec.on = true; rec.particles.length = 0; rec.frames.length = 0; }
  prev = st;
  if (rec.on) { W.snapFrame(); if (process.env.SH_DBG && (process.env.SH_DBG === "2" || (W.tick - started) % 2 === 0)) console.log("t+" + (W.tick - started), "state", m.getProperty("sh:state"), "z", m.location.z.toFixed(2)); }
  W.advance(1);
  player.location = { x: 0, y: 64, z: 0 };
  if (started < 0 && Math.hypot(m.location.x, m.location.z - dist) > 0.01 && i % 40 === 0) m.location = { x: 0, y: 64, z: dist };
  if (rec.on && (m.getProperty("sh:state") === 0 || m.getProperty("sh:state") === undefined) && W.tick - started > 12) { tEnd = W.tick; break; }
  if (rec.on && W.tick - started > 260) { tEnd = W.tick; break; }
}
if (started < 0) { console.error("الحالة ما ظهرت: " + want); process.exit(2); }
for (let i = 0; i < 90; i++) { W.snapFrame(); W.advance(1); player.location = { x: 0, y: 64, z: 0 }; }   // نكمل شوي حتى تخلص الجزيئات
fs.writeFileSync(outFile, JSON.stringify({ type, state: want, dist, start: started, particles: rec.particles, frames: rec.frames }));
const by = {}; for (const p of rec.particles) by[p.id] = (by[p.id] || 0) + 1;
console.log(`سجّلت ${rec.particles.length} جزيء و${rec.frames.length} إطار من التك ${started} (المهارة انتهت ~${tEnd - started} تك):`, Object.entries(by).map(([k, v]) => k.replace("minecraft:", "") + "×" + v).join(" "));
fs.rmSync(tmp, { recursive: true, force: true });
process.exit(0);
