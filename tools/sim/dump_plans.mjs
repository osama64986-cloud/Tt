// يطبع مخططات البنايات (ops) كـJSON حتى نعاينها بـ tools/preview_structures.py
// node tools/sim/dump_plans.mjs <outdir>
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const out = process.argv[2] || os.tmpdir();
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "shplan-"));
fs.mkdirSync(path.join(tmp, "scripts"));
for (const f of fs.readdirSync(path.join(root, "AnimePowers/BP/scripts"))) fs.copyFileSync(path.join(root, "AnimePowers/BP/scripts", f), path.join(tmp, "scripts", f));
fs.writeFileSync(path.join(tmp, "package.json"), '{"type":"module"}');
for (const [n, f] of [["@minecraft/server", "mc_server_stub.js"], ["@minecraft/server-ui", "mc_ui_stub.js"]]) {
  const d = path.join(tmp, "node_modules", ...n.split("/")); fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(path.join(d, "package.json"), '{"type":"module","main":"index.js"}');
  fs.copyFileSync(path.join(root, "tools/sim", f), path.join(d, "index.js"));
}
const m = await import(pathToFileURL(path.join(tmp, "scripts/structures.js")).href);
for (const [k, fn] of [["village", m.planVillage], ["palace", m.planPalace], ["ruins", m.planRuins], ["shrine", m.planShrine], ["temple", m.planTemple], ["lightshrine", m.planLightShrine]]) {
  const p = fn(20260101);
  fs.writeFileSync(path.join(out, `plan_${k}.json`), JSON.stringify({ ops: p.ops, spawns: p.spawns }));
  console.log(k, "ops:", p.ops.length);
}
fs.rmSync(tmp, { recursive: true, force: true });
