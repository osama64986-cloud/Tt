import { Entity, step, stats, fire, allEntities } from "./mock.mjs";
console.warn = () => {};
await import("./main.mjs");
const [A0, B0] = process.argv.slice(2);
const HP = { "ab:goku": 1000, "ab:vegeta": 950, "ab:gojo": 600, "ab:yuji": 300, "ab:yuji_final": 650, "ab:sukuna": 650, "ab:luffy": 950 };
const p = new Entity("minecraft:player", { x: 0, y: 0, z: -10 }, {});
const A = new Entity(A0, { x: -12, y: 0, z: 0 }, { families: ["anime_fighter", "mob"], hp: HP[A0] });
const B = new Entity(B0, { x: 12, y: 0, z: 0 }, { families: ["anime_fighter", "mob"], hp: HP[B0] });
p.held = "ab:team_stick"; fire("hit", { damagingEntity: p, hitEntity: A }); fire("hit", { damagingEntity: p, hitEntity: B });
const dmgBy = {};
const origLen = stats.damage.length;
for (let t = 0; t < 6000 && A.isValid && B.isValid; t++) {
  step();
  for (const [me, o] of [[A, B], [B, A]]) { const dx = o.location.x - me.location.x; if (Math.abs(dx) > 2) me.location.x += Math.sign(dx) * 0.15; }
  if (t % 100 === 0) console.log(t / 20 + "s", A.typeId, "hp", Math.round(A.hp), "form", A.props["ab:form"], "|", B.typeId, "hp", Math.round(B.hp), "form", B.props["ab:form"], "dist", Math.abs(A.location.x - B.location.x).toFixed(1), "tags", [...B.tags].join(","));
}
for (const d of stats.damage) { const k = d.from + "->" + d.to; dmgBy[k] = (dmgBy[k] ?? 0) + d.amount; }
console.log("winner", A.isValid ? A.typeId : B.typeId, dmgBy);
