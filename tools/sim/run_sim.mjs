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
{
  // v1.39: أنميشن اللاعب: خلال الاختبارات لازم انشغلت ضربات أسلحة وحركات مهارات وداش، وكلها توقف بالمنظور الأول
  const an = [...new Set((W.stats.anims || []).map((a) => a.replace("animation.sh.player.", "")))].sort();
  console.log("أنميشن اللاعب:", an.join(" "));
  const need = [/^slash|^stab|^cleave|^heavy|^thrust|^claw|^reap/, /^cast_/, /^dash_/];
  if (need.some((r) => !an.some((a) => r.test(a)))) W.failures.push("أنميشن اللاعب ما انشغل (ضربة سلاح، مهارة، داش)");
  const op = W.stats.animOpts || {};
  if (!/is_first_person/.test(op.stopExpression || "")) W.failures.push("أنميشن اللاعب ما يوقف بالمنظور الأول");
  // V1: حلقات الحركة (الوقوف/وقفة القتال/المشي/الركض) بالطبقة sh_move وتوقف بالعميل لما تتغير الحالة
  const mo = W.stats.moveOpts || {};
  if (!an.some((a) => a === "idle" || a === "idle_combat")) W.failures.push("أنميشن الوقوف ما اشتغل");
  if (mo.controller !== "sh_move" || !/query\.is_/.test(mo.stopExpression || "")) W.failures.push("حلقات حركة اللاعب لازم تكون بطبقة sh_move وتوقف لما تتغير الحالة");
}
{
  // V1: تغطية الترجمة: كل سطر إنكليزي طلع للاعب خلال المحاكي نمرره على القاموس العربي؛ السطور اللي بقت بيها كلمات إنكليزية تنكتب بملف
  const { trText } = await import(pathToFileURL(path.join(tmp, "scripts/i18n.js")).href);
  const KEEP = /^(Lv|XP|S|V1|V1\.5|MAX|HUD|OK|STR|SPD|X)$/;                                   // رموز تبقى إنكليزي حتى بالعربي
  // نصوص story.js بلغتين (العربي جاهز بيها) ونصوص الإعدادات بالإنكليزي ما تحتاج قاموس
  const ST = await import(pathToFileURL(path.join(tmp, "scripts/story.js")).href);
  const bil = new Set();
  const addEn = (o) => { if (o && typeof o.en === "string") for (const ln of o.en.split("\n")) if (ln.trim()) bil.add(ln.trim()); };
  ST.CHRONICLE.forEach(([t, b]) => { addEn(t); addEn(b); }); addEn(ST.CHRONICLE_TITLE); addEn(ST.STORY_TITLE); addEn(ST.STORY_END.t); addEn(ST.STORY_END.n);
  ST.STORY.forEach((c) => { addEn(c.t); c.steps.forEach((x) => { addEn(x.n); addEn(x.o); }); });
  const isBil = (l) => { const p = l.replace(/§./g, "").trim(); for (const b of bil) if (p.includes(b) || b.includes(p.replace(/^[^A-Za-z]+|[^A-Za-z.]+$/g, ""))) return true; return /HUD panel|Story mission on screen|now speaks English/.test(p); };
  const lines = [...(globalThis.__allText || [])].filter((l) => !/[\u0600-\u06FF\uFE70-\uFEFF]/.test(l) && /[A-Za-z]{3}/.test(l.replace(/§./g, "")) && !isBil(l));
  const I18 = await import(pathToFileURL(path.join(tmp, "scripts/i18n.js")).href);
  const left = lines.filter((l) => { const t = (/[│]/.test(l) ? I18.trSeg(l) : trText(l)).replace(/§./g, ""); return (t.match(/[A-Za-z]{2,}/g) || []).some((w) => !KEEP.test(w)); });
  const pct = lines.length ? (100 * (lines.length - left.length)) / lines.length : 100;
  console.log(`تغطية الترجمة العربية: ${pct.toFixed(1)}% من ${lines.length} سطر طلع للاعب (باقي ${left.length})`);
  fs.writeFileSync(path.join(root, "tools/i18n/untranslated_runtime.txt"), left.sort().join("\n") + "\n");
}
if (errors.size) {
  console.log(`\nأخطاء مبلوعة (${errors.size}):`);
  for (const [k, n] of errors) console.log(` x${n}  ${k}`);
  process.exitCode = 1;
} else console.log("بدون أخطاء مبلوعة.");
if (W.failures.length) { console.log("\nفشل التحقق:"); W.failures.forEach((f) => console.log(" -", f)); process.exitCode = 1; }
fs.rmSync(tmp, { recursive: true, force: true });
