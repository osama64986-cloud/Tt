// Runs a few simulated battles and reports winners, damage and any script errors.
import { Entity, step, stats, fire, allEntities } from "./mock.mjs";

const origWarn = console.warn;
console.warn = (...a) => { stats.errors.push(a.join(" ")); origWarn(...a); };
await import("./main.mjs");

const HP = { "ab:goku": 1000, "ab:vegeta": 950, "ab:gojo": 600, "ab:yuji": 300, "ab:yuji_final": 650, "ab:sukuna": 650, "ab:luffy": 950 };
const fighter = (id, x) => new Entity(id, { x, y: 0, z: 0 }, { families: ["anime_fighter", "mob"], hp: HP[id] });

const player = new Entity("minecraft:player", { x: 0, y: 0, z: -10 }, { name: "Osama" });
fire("spawn", { player, initialSpawn: true });
console.log("starter kit:", player.inv);

function battle(a, b, ticks = 6000) {
  for (const e of allEntities) if (e !== player) e.isValid = false;
  const A = fighter(a, -12), B = fighter(b, 12);
  player.held = "ab:team_stick";
  fire("hit", { damagingEntity: player, hitEntity: A });
  fire("hit", { damagingEntity: player, hitEntity: B });
  let t = 0;
  for (; t < ticks && A.isValid && B.isValid; t++) {
    step();
    // crude movement: close in until 2 blocks apart; melee like the game AI does
    for (const [me, other] of [[A, B], [B, A]]) {
      if (!me.isValid || !other.isValid) continue;
      const dx = other.location.x - me.location.x;
      if (Math.abs(dx) > 2) me.location.x += Math.sign(dx) * 0.15;
      else if (t % 20 === 0) {
        const dmg = { "ab:goku": [14, 20, 27, 40, 55], "ab:vegeta": [13, 19, 37, 50], "ab:gojo": [10, 13], "ab:yuji": [8], "ab:yuji_final": [20], "ab:sukuna": [18, 24, 30], "ab:luffy": [10, 16, 22, 42, 40, 36, 58] }[me.typeId][me.props["ab:form"]];
        const ev = { hurtEntity: other, damage: dmg, cancel: false, damageSource: { cause: "entityAttack", damagingEntity: me } };
        fire("beforeHurt", ev);
        if (!ev.cancel) { other.hp -= ev.damage; if (other.hp <= 0) other.die(); }
        fire("hit", { damagingEntity: me, hitEntity: other });
      }
    }
  }
  const winner = A.isValid ? A : B.isValid ? B : null;
  return { winner: winner?.typeId ?? "none", seconds: (t / 20).toFixed(0), hpLeft: winner ? Math.round(winner.hp) : 0,
    formA: A.props["ab:form"], formB: B.props["ab:form"], tagA: A.nameTag.split("\n")[0] };
}


const ORDER = ["ab:goku", "ab:vegeta", "ab:luffy", "ab:yuji_final", "ab:sukuna", "ab:gojo", "ab:yuji"];
const N = Number(process.env.N ?? 6);
let wrong = 0, total = 0;
const PAIRS = process.env.PAIRS ? process.env.PAIRS.split(",").map((p) => p.split(":").map((x) => "ab:" + x)) : null;
const list = PAIRS ?? ORDER.flatMap((a, i) => ORDER.slice(i + 1).map((b) => [a, b]));
for (const [a, b] of list) {
  const wins = {};
  for (let k = 0; k < N; k++) { const r = k % 2 ? battle(b, a) : battle(a, b); wins[r.winner] = (wins[r.winner] ?? 0) + 1; }
  const upset = N - (wins[a] ?? 0);
  wrong += upset; total += N;
  console.log(`${a.padEnd(15)} vs ${b.padEnd(15)} -> ${JSON.stringify(wins)}${upset ? "   <-- UPSET" : ""}`);
}
console.log(`stronger side won ${total - wrong}/${total}`);
console.log("SCRIPT ERRORS:", stats.errors.length ? stats.errors.slice(0, 3) : "none");
