// Runs a few simulated battles and reports winners, damage and any script errors.
import { Entity, step, stats, fire, allEntities } from "./mock.mjs";

const origWarn = console.warn;
console.warn = (...a) => { stats.errors.push(a.join(" ")); origWarn(...a); };
await import("./main.mjs");

const HP = { "ab:goku": 1000, "ab:vegeta": 950, "ab:gojo": 600, "ab:yuji": 300, "ab:yuji_final": 550, "ab:yuji_sukuna": 600, "ab:luffy": 950 };
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
        const dmg = { "ab:goku": [14, 20, 27, 40, 55], "ab:vegeta": [13, 19, 37, 50], "ab:gojo": [10, 13], "ab:yuji": [8], "ab:yuji_final": [16], "ab:yuji_sukuna": [18], "ab:luffy": [10, 16, 22, 42, 40, 36, 58] }[me.typeId][me.props["ab:form"]];
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

const results = {};
for (const [a, b] of [["ab:goku", "ab:gojo"], ["ab:vegeta", "ab:gojo"], ["ab:goku", "ab:vegeta"], ["ab:gojo", "ab:yuji_sukuna"], ["ab:yuji_sukuna", "ab:yuji_final"], ["ab:yuji_final", "ab:yuji"], ["ab:luffy", "ab:gojo"], ["ab:goku", "ab:luffy"], ["ab:luffy", "ab:yuji_sukuna"]]) {
  const wins = {};
  for (let i = 0; i < (process.env.ONLY && !(a + b).includes(process.env.ONLY) ? 0 : 10); i++) { const r = battle(a, b); wins[r.winner] = (wins[r.winner] ?? 0) + 1; if (i === 0) console.log(`${a} vs ${b}:`, r); }
  results[`${a} vs ${b}`] = wins;
}
console.log("wins over 10 fights each:", results);

// Kill stick on a warden + reset
for (const e of allEntities) if (e !== player) e.isValid = false;
const warden = new Entity("minecraft:warden", { x: 2, y: 0, z: 0 }, { hp: 500 });
const gojo = fighter("ab:gojo", 4);
gojo.addTag("ab_infinity");
player.held = "ab:kill_stick";
fire("hit", { damagingEntity: player, hitEntity: warden });
fire("hit", { damagingEntity: player, hitEntity: gojo });
for (let i = 0; i < 5; i++) step();
console.log("kill stick: warden dead =", !warden.isValid, " gojo (Infinity) dead =", !gojo.isValid);
player.held = "ab:team_stick"; player.isSneaking = true;
fire("use", { source: player, itemStack: { typeId: "ab:team_stick" } });
console.log("reset message:", player.actionbar);
fire("use", { source: player, itemStack: { typeId: "ab:kill_stick" } });
console.log("kill stick use:", player.actionbar);
console.log("particles:", stats.particles, "sounds:", stats.sounds, "blocks carved:", stats.carved);
console.log("transform events:", [...new Set(stats.events.filter((e) => e.includes("form_") && !e.endsWith("form_0")))]);
console.log("vfx spawned:", stats.vfx, " camera shakes:", stats.cmds, " vfx left alive:", allEntities.filter((e) => e.typeId === "ab:vfx" && e.isValid).length);
console.log("SCRIPT ERRORS:", stats.errors.length ? stats.errors : "none");
