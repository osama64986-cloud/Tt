// يطبع مدينة إثيريا (نفس city_plan.js و city_raster.js اللي باللعبة) لملفين: الشبكة (Uint16) والبيانات (لوحة البلوكات، الحراس، الصناديق...)
// node tools/sim/dump_city.mjs <outdir> [seed]
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const out = process.argv[2] || ".";
const seed = Number(process.argv[3] || 20260601);
const plan = await import(pathToFileURL(path.join(root, "AnimePowers/BP/scripts/city_plan.js")).href);
const ras = await import(pathToFileURL(path.join(root, "AnimePowers/BP/scripts/city_raster.js")).href);
const t0 = Date.now();
const P = plan.planCity(seed);
const o = {};
const gen = ras.rasterize(P, o, 1e9);
let steps = 0; while (!gen.next().done) steps++;
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, "city_grid.bin"), Buffer.from(o.grid.buffer));
fs.writeFileSync(path.join(out, "city_meta.json"), JSON.stringify({ dims: [ras.RX, ras.RY, ras.RZ], ymin: plan.CITY_YMIN, pal: P.pal, posts: P.posts, chests: P.chests, beds: P.beds, marks: P.marks, homes: P.homes, lights: P.lights, ops: P.ops.length }));
console.log(`city: ops ${P.ops.length}, pal ${P.pal.length}, ${Date.now() - t0} ms`);
