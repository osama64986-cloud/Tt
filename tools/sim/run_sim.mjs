// محاكي خفيف: يشغّل سكربتات المود على عالم وهمي حتى نكشف الأخطاء المبلوعة بـ try/catch
// (الأخطاء المنطقية، متغيرات ناقصة، دوال مو معرّفة...). ما يغني عن تجربة اللعبة الحقيقية.
// التشغيل:  node tools/sim/run_sim.mjs   (من جذر المشروع)
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "shsim-"));
fs.mkdirSync(path.join(tmp, "scripts"));
for (const f of fs.readdirSync(path.join(root, "AnimePowers/BP/scripts"))) {
  let s = fs.readFileSync(path.join(root, "AnimePowers/BP/scripts", f), "utf8");
  // كل catch يسجل الخطأ بدل ما يبلعه
  s = s.replace(/catch \((\w+)\) \{/g, "catch ($1) { globalThis.__swallow && globalThis.__swallow($1);");
  fs.writeFileSync(path.join(tmp, "scripts", f), s);
}
fs.writeFileSync(path.join(tmp, "package.json"), '{"type":"module"}');
const nm = (n) => { fs.mkdirSync(path.join(tmp, "node_modules", ...n.split("/")), { recursive: true }); return path.join(tmp, "node_modules", ...n.split("/")); };
fs.writeFileSync(nm("@minecraft/server") + "/package.json", '{"name":"@minecraft/server","type":"module","main":"index.js"}');
fs.writeFileSync(nm("@minecraft/server") + "/index.js", fs.readFileSync(path.join(root, "tools/sim/mc_server_stub.js"), "utf8"));
fs.writeFileSync(nm("@minecraft/server-ui") + "/package.json", '{"name":"@minecraft/server-ui","type":"module","main":"index.js"}');
fs.writeFileSync(nm("@minecraft/server-ui") + "/index.js", fs.readFileSync(path.join(root, "tools/sim/mc_ui_stub.js"), "utf8"));

const errors = new Map();
globalThis.__swallow = (e) => {
  const key = String(e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : e);
  errors.set(key, (errors.get(key) || 0) + 1);
};

const server = await import(pathToFileURL(path.join(tmp, "node_modules/@minecraft/server/index.js")).href);
const W = server.__sim;
await import(pathToFileURL(path.join(tmp, "scripts/main.js")).href);

const sc = JSON.parse(fs.readFileSync(path.join(root, "tools/sim/scenario.json"), "utf8"));
await W.runScenario(sc, root);

console.log("\n== نتيجة المحاكي ==");
console.log("جزيئات:", W.stats.particles, "| أصوات:", W.stats.sounds, "| كيانات fx:", W.stats.spawned);
{
  // كل جزيء بالمود لازم يكون من جزيئات ماينكرافت الأصلية (القائمة من Mojang/bedrock-samples)
  const vanilla = new Set(fs.readFileSync(path.join(root, "tools/sim/vanilla_particle_ids.txt"), "utf8").split("\n").filter(Boolean));
  const used = Object.entries(W.stats.pById || {});
  const bad = used.filter(([id]) => !vanilla.has(id));
  console.log("جزيئات مستعملة:", used.map(([id, n]) => `${id.replace("minecraft:", "")}×${n}`).join(" "));
  if (bad.length) W.failures.push("جزيئات مو من ماينكرافت: " + bad.map(([id]) => id).join(", "));
  if (W.stats.badTint) W.failures.push("colored_flame_particle بتلوين دافئ (يطلع أخضر لأن سبرايته سماوي): " + Object.entries(W.stats.badTint).map(([k, n]) => `${k}×${n}`).join(" "));
}
console.log("أصوات مستعملة:", [...W.stats.soundIds].sort().join(" "));
if (errors.size) {
  console.log(`\nأخطاء مبلوعة (${errors.size}):`);
  for (const [k, n] of errors) console.log(` x${n}  ${k}`);
  process.exitCode = 1;
} else console.log("بدون أخطاء مبلوعة.");
if (W.failures.length) { console.log("\nفشل التحقق:"); W.failures.forEach((f) => console.log(" -", f)); process.exitCode = 1; }
fs.rmSync(tmp, { recursive: true, force: true });
