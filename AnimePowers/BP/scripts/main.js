import { world, system, ItemStack, MolangVariableMap, EntityDamageCause } from "@minecraft/server";
import * as MC from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import {
  RANKS, LEVELS_PER_RANK, HARD_RANK_FROM, RARITIES, unlockLevel, powerXpNeeded, addPowerXp, xpNeeded, defaultState, addXp, monsterReward, isSkillUnlocked, addSkillXp, skillXpNeeded, skillLevel, SKILL_UNLOCK_LEVEL, SKILL_MAX_LV, rankProgress, rankHealthBonus,
} from "./logic.js";
import { setupStructures, buildTemple, findTemple } from "./structures.js";
import { SHAPE } from "./shapes.js";

// ───────────────────────── البيانات ─────────────────────────
const TRAIN_NEED = 3;

const POWERS = {
  accountant: {
    name: "The Accountant", color: "§6",
    desc: "Every enemy carries a number above its head and you manipulate the numbers. At zero it collapses.",
  },
  law: {
    name: "Law Scribe", color: "§5",
    desc: "Write a law over the area around you; everyone who enters it obeys.",
  },
  distance: {
    name: "Distance Warper", color: "§b",
    desc: "Bend the distance between you and anything: pull, push, swap and fold space.",
  },
  echo: {
    name: "Echo Weaver", color: "§3",
    desc: "Every action leaves an echo that returns a moment later and strikes again.",
  },
  iron: {
    name: "Iron Body", color: "§7",
    desc: "Harden your body like iron and strike with a heavy fist.",
  },
  crystal: {
    name: "Crystal Lord", color: "§d",
    desc: "Grow sharp crystals: throw them, armor up with them, imprison enemies, and detonate them.",
  },
  borrower: {
    name: "Trait Borrower", color: "§e",
    desc: "Borrow a trait from nature (rock, fangs, wings, hunter's eye) and fuse two traits together.",
  },
  wind: {
    name: "Wind Strider", color: "§a",
    desc: "Speed, leaps and gales; move faster than any enemy.",
  },
  star: {
    name: "Star Sovereign", color: "§9",
    desc: "Summon the stars: meteors, gravity, orbits, constellations and black holes, up to the Supernova that turns any battle.",
  },
};
// ندرة كل قدرة: تحدد عدد مهاراتها وأعلى ليفل لها
const POWER_RARITY = { iron: "common", wind: "uncommon", star: "mythic", echo: "rare", crystal: "rare", accountant: "epic", borrower: "epic", distance: "legendary", law: "legendary" };
const rarityOf = (key) => RARITIES.find((r) => r.key === POWER_RARITY[key]) || RARITIES[0];

// مستويات فتح المهارات الخمس لكل قدرة
const LV = [1, 3, 8, 14, 20];
function mk(id, power, name, item, idx, cooldown, desc) {
  return { id, power, name, item, first: idx === 0, prev: null, cooldown, desc };
}
const SKILLS = {};
const AIMED = new Set(["seal", "subtract", "transfer", "divide", "zero", "pull", "push", "swap", "fold", "echoseal", "prison", "meteor", "gravwell", "blackhole"]);
for (const s of [
  mk("seal", "accountant", "Number Seal", "sh:skill_seal", 0, 10, "Mark an enemy with the number 10. It drops by itself every 2 seconds and every hit lowers it; at zero it collapses and takes damage."),
  mk("subtract", "accountant", "Subtract", "sh:skill_subtract", 1, 60, "Lower an enemy's number by 3 (if unmarked, marks it with 7)."),
  mk("transfer", "accountant", "Transfer", "sh:skill_transfer", 2, 200, "Move an enemy's number to the nearest other enemy."),
  mk("ironskin", "iron", "Iron Skin", "sh:skill_ironskin", 0, 300, "Your body hardens: high resistance for 6 seconds."),
  mk("ironfist", "iron", "Iron Fist", "sh:skill_ironfist", 1, 100, "A heavy punch to the enemy in front of you: high damage and knockback."),
  mk("windrun", "wind", "Wind Run", "sh:skill_windrun", 0, 200, "High speed for 5 seconds with a wind trail."),
  mk("windleap", "wind", "Wind Leap", "sh:skill_windleap", 1, 140, "Leap forward with force and land softly."),
  mk("gale", "wind", "Gale", "sh:skill_gale", 2, 360, "A gale that pushes and hurts every nearby enemy."),
  mk("divide", "accountant", "Divide", "sh:skill_divide", 3, 240, "Split an enemy's number in two: half stays, half goes to the nearest other enemy (if unmarked, starts from 10)."),
  mk("zero", "accountant", "Zero", "sh:skill_zero", 3, 900, "If the enemy's number is 5 or less it collapses instantly, otherwise lowers it by 5."),

  mk("weight", "law", "Law of Weight", "sh:skill_weight", 0, 16, "A circle that greatly slows enemies, stops them from jumping and hurts them every second."),
  mk("silence", "law", "Law of Silence", "sh:skill_silence", 1, 120, "Archers inside the circle cannot shoot and every enemy hits weaker."),
  mk("reflect", "law", "Law of Reflection", "sh:skill_reflect", 2, 300, "Any hit you take inside the circle is thrown back at the attacker."),
  mk("boundary", "law", "Law of Boundary", "sh:skill_boundary", 3, 600, "Enemies inside the circle cannot leave it."),
  mk("time", "law", "Law of Time", "sh:skill_time", 4, 700, "Enemies around you freeze for 3 seconds."),
  mk("absolute", "law", "Absolute Law", "sh:skill_absolute", 5, 1500, "Choose a law that lasts 5 seconds."),

  mk("pull", "distance", "Pull", "sh:skill_pull", 0, 12, "The enemy is yanked to you without walking."),
  mk("push", "distance", "Push", "sh:skill_push", 1, 60, "Throw the enemy far away without touching it."),
  mk("swap", "distance", "Swap", "sh:skill_swap", 2, 160, "Swap places with the enemy."),
  mk("fold", "distance", "Fold", "sh:skill_fold", 3, 420, "Fold the distance and strike the enemy as if they were beside you."),
  mk("spacecollapse", "distance", "Collapse", "sh:skill_spacecollapse", 4, 1200, "All nearby enemies are gathered into a single point."),

  mk("echostrike", "echo", "Echo Strike", "sh:skill_echostrike", 0, 14, "Your next hit repeats after one second."),
  mk("echoseal", "echo", "Echo Seal", "sh:skill_echoseal", 1, 100, "Mark an enemy: all damage it takes is echoed back and explodes."),
  mk("echowave", "echo", "Echo Wave", "sh:skill_echowave", 2, 480, "A wave in front of you, followed by a second echo that strikes again."),
  mk("chorus", "echo", "Echo Chorus", "sh:skill_chorus", 3, 1000, "Three echo waves expand around you, each stronger than the last."),
  mk("spacerewind", "distance", "Spatial Rewind", "sh:skill_spacerewind", 5, 20, "First use: saves your position for 15 seconds. Second use: return to that spot and recover some health."),

  mk("shards", "crystal", "Crystal Shards", "sh:skill_shards", 0, 30, "Three shards where you look. While sneaking: one powerful crystal spear that pierces everything. Shards leave crystals on enemies."),
  mk("crystalshield", "crystal", "Crystal Shield", "sh:skill_crystalshield", 1, 400, "Crystals orbit you and give you an absorption shield for 10 seconds."),
  mk("prison", "crystal", "Crystal Prison", "sh:skill_prison", 2, 700, "Trap an enemy in crystals: frozen in place and weakened (bosses for a shorter time)."),
  mk("burst", "crystal", "Crystal Burst", "sh:skill_burst", 3, 500, "Detonate every crystal stuck on enemies. Each crystal deals damage and a small blast hits those around it."),

  mk("rockskin", "borrower", "Rock Trait", "sh:skill_rockskin", 0, 260, "Borrow rock skin: high resistance and slight slowness."),
  mk("fangs", "borrower", "Fang Trait", "sh:skill_fangs", 1, 300, "For 8 seconds your hits poison the enemy and heal you a little."),
  mk("windwings", "borrower", "Wing Trait", "sh:skill_windwings", 2, 360, "High jump, slow fall and speed for 10 seconds."),
  mk("huntereye", "borrower", "Hunter's Eye Trait", "sh:skill_huntereye", 3, 480, "Night vision and mark every nearby enemy; your hits on them are stronger."),
  mk("adapt", "borrower", "Adapt", "sh:skill_adapt", 4, 900, "Fuse the last two traits you used (within 40 seconds) so they work together for a shorter time."),
  mk("meteor", "star", "Meteor", "sh:skill_meteor", 0, 80, "Call a meteor onto the spot you aim at after one second: area damage and burning."),
  mk("gravwell", "star", "Gravity Well", "sh:skill_gravwell", 1, 300, "A well that pulls enemies into one point for 4 seconds, slowing and hurting them."),
  mk("orbit", "star", "Star Orbit", "sh:skill_orbit", 2, 500, "3 stars orbit you for 10 seconds, hit everything they touch, and reduce the damage you take."),
  mk("constellation", "star", "Constellation", "sh:skill_constellation", 3, 700, "Link nearby enemies with star lines and shock them all two seconds later."),
  mk("stardash", "star", "Star Dash", "sh:skill_stardash", 4, 160, "A star dash forward that hits and slows everything in the way."),
  mk("blackhole", "star", "Black Hole", "sh:skill_blackhole", 5, 1100, "A black hole that pulls everything in for 6 seconds, then collapses and explodes."),
  mk("supernova", "star", "Supernova", "sh:skill_supernova", 6, 1800, "Charge for two seconds, then a huge stellar explosion hits and blinds every enemy within 14 blocks. You are weakened afterwards."),
]) SKILLS[s.id] = s;
{
  const last = {}, count = {};
  for (const s of Object.values(SKILLS)) { s.prev = last[s.power] || null; last[s.power] = s.id; s.idx = count[s.power] = (count[s.power] ?? -1) + 1; }
  for (const s of Object.values(SKILLS)) {
    const r = rarityOf(s.power);
    s.first = s.idx === 0;
    s.unlock = unlockLevel(s.idx, count[s.power] + 1, r.maxLv);
  }
}
const ITEM_TO_SKILL = {};
for (const s of Object.values(SKILLS)) ITEM_TO_SKILL[s.item] = s;

// طريقة استعمال كل مهارة (تظهر بالـHUD وبنافذة الحالة)
const SKILL_USAGE = {
  seal: "Aim at an enemy and use: marks it with 10; it drops by itself and every hit lowers it",
  subtract: "Aim at an enemy and use: lowers its number by 3",
  transfer: "Aim at a marked enemy: its number moves to the nearest enemy",
  divide: "Aim at a marked enemy: its number splits between it and the nearest enemy",
  zero: "Aim at an enemy: if its number is 5 or less it collapses instantly",
  shards: "Use: 3 shards. Sneak + use: one powerful piercing crystal spear",
  crystalshield: "Use: crystals orbit you and absorb damage",
  prison: "Aim at an enemy: imprison it in crystals (frozen in place)",
  burst: "Use Crystal Shards on enemies first, then use: detonates every crystal",
  spacerewind: "First use: saves your position. Second use: return to the same spot",
  spacecollapse: "Use: all nearby enemies are gathered into one point",
  absolute: "Use: opens a menu, choose the law that lasts 5 seconds",
  adapt: "Use two different traits in a row, then use Adapt to fuse them",
  weight: "Use: a circle around you slows and hurts enemies",
  silence: "Use: a circle that stops archers from shooting and weakens enemy hits",
  reflect: "Use: a circle that reflects any hit back at the attacker",
  boundary: "Use: a circle nobody can leave",
  time: "Use: every enemy around you freezes for 3 seconds",
  meteor: "Aim at a spot and use: a warning circle, then a meteor lands one second later",
  gravwell: "Aim at a spot: a well pulls enemies in for 4 seconds and slows them",
  orbit: "Use: 3 stars orbit you for 10 seconds and hit everything they touch",
  constellation: "Use near 2 or more enemies: link them with star lines, then shock them all two seconds later",
  stardash: "Use: dash forward hitting everything in the way",
  blackhole: "Aim at a spot: a black hole pulls everything in for 6 seconds, then explodes",
  supernova: "Use: stand still for two seconds, then a huge stellar explosion (you are weakened for 6 seconds)",
};
function usageOf(s) {
  if (SKILL_USAGE[s.id]) return SKILL_USAGE[s.id];
  return AIMED.has(s.id) ? "Aim at an enemy and use" : "Use (works around you)";
}


// رتب الوحوش (سلم خاص بيهم، مطابق لألوان الصدوع): كل رتبة وحش تقابل رتبة لاعب بنفس الرقم
const MON_RANKS = [
  { name: "Lowly", col: "§9", desc: "the weakest spawn of the Abyss (blue rifts)" },
  { name: "Grim", col: "§a", desc: "dark-hearted hunters that stalk travellers at dusk" },
  { name: "Vile", col: "§5", desc: "the Abyss has tainted them (violet rifts)" },
  { name: "Cursed", col: "§d", desc: "they hit harder and carry the Abyss's strength" },
  { name: "Dread", col: "§c", desc: "veterans of a hundred hunts (crimson rifts)" },
  { name: "Calamity", col: "§6", desc: "one of them can empty a village" },
  { name: "Cataclysm", col: "§4", desc: "the Abyss's own wardens (black-gold rifts)" },
];
const monRankName = (rk) => (rk < 0 ? "Training" : MON_RANKS[Math.min(MON_RANKS.length - 1, rk)].name);
// وحوش: rank -1 = وحش تدريب (بلا رتبة)
const MONSTERS = {
  "sh:training_archer": { rank: -1, xp: [20, 50], training: true },
  // وحوش الرتبة الأولى (index 0 = مبتدئ)
  "sh:ember_imp": { rank: 0, xp: 18 },
  "sh:rust_guard": { rank: 0, xp: 30 },
  "sh:shadow_hound": { rank: 0, xp: 24 },
  "sh:sand_scorpion": { rank: 0, xp: 36 },
};
const MONSTER_CAP = 3; // أقصى عدد وحوش الرتبة الأولى قرب لاعب واحد
const MONSTER_SPAWN_TICKS = 1200; // محاولة ظهور كل دقيقة (غيّرها إذا تريد أبطأ أو أسرع)
// ─── تدرج الصعوبة: الوحش يظهر بقوة تناسب رتبة اللاعب اللي قربه (حياة + ضرر + خبرة) ───
const TIER_HP = 0.30, TIER_DMG = 0.15, TIER_XP = 0.30;
function tierOf(e) { try { const v = e.getDynamicProperty("sh_tier"); return typeof v === "number" ? v : 0; } catch (err) { return 0; } }
function scaleMonster(e, rank) {
  try {
    if (!e || !rank) return;
    e.setDynamicProperty("sh_tier", rank);
    const hp = e.getComponent("minecraft:health");
    const extra = Math.round(hp.effectiveMax * TIER_HP * rank);
    e.addEffect("health_boost", 1000000, { amplifier: Math.max(0, Math.min(250, Math.round(extra / 4) - 1)), showParticles: false });
    if (rank >= 3) e.addEffect("strength", 1000000, { amplifier: 0, showParticles: false });
    later(2, () => { try { e.getComponent("minecraft:health").resetToMaxValue(); } catch (err) { /* */ } });
  } catch (err) { /* */ }
}
const effRank = (info, tier) => Math.min(RANKS.length - 1, info.rank + Math.floor(tier / 2));
const RANK0_TYPES = ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion"];

// أسلحة الدفاع: ضرر إضافي فوق ضرر اليد، تشتغل حتى بدون قدرة
const WEAPONS = {
  // خفيف: ضرر واطي، بس بيده تقييد وضربة الفجر
  "sh:dawn_dagger": { extra: 3, sound: "sh.dagger_hit", color: "gold", knock: 0.0, name: "Dawn Dagger", special: "combo",
    desc: "Every third consecutive hit is a Dawn Strike (double damage). Use: Sun Bind. Sneak + use: Radiant Flurry. Weakness: low damage." },
  // ثقيل: يضرب أكثر من عدو بكل ضربة وضرره عالي، بس يبطئك
  "sh:ember_cleaver": { extra: 9, sound: "sh.cleaver_hit", color: "orange", knock: 1.2, name: "Ember Cleaver", cleave: 4, heavy: 1,
    desc: "Every hit cleaves several enemies. Use: Ember Arc. Sneak + use: Inferno Spin. Weakness: slows you while held." },
  // قاتل الظل: ينتقل خلف العدو ويضربه
  // سيف النور (Oath of Light): عكس كاتانا الهاوية، بضريح سيف النور. كل رابع ضربة "بريق" يعمي ويضرب أكثر
  "sh:silver_oath": { extra: 5, sound: "sh.dagger_hit", color: "white", knock: 0.3, name: "Oath of Light", special: "glint",
    desc: "The sword of light, the Abyss Katana's opposite. Every fourth hit in a row is a Glint (bonus damage and a flash that blinds). Use: Oath Cleave. Sneak + use: Silver Step." },
  "sh:shadow_blade": { extra: 2, sound: "sh.dagger_hit", color: "purple", knock: 0.0, name: "Shadow Blade", fast: true,
    desc: "Every hit repeats quickly. Use: Shadow Ambush (appear behind the enemy and stab it). Sneak + use: Phantom Strike (shadows hit every enemy around)." },
  // كاتانا الهاوية: أقوى سلاح، مهارتين تكبر مع ليفلها
  "sh:dark_katana": { extra: 4, sound: "sh.dagger_hit", color: "purple", knock: 0.0, name: "Abyss Katana",
    desc: "The strongest weapon. Use: Abyss Crescent. Sneak + use: Void Execution. Both grow with the katana level (kill enemies while holding it)." },
  // مخالب: انقضاض وتمزيق ونزيف وتشفي منه
  "sh:shadow_claws": { extra: 3, sound: "sh.dagger_hit", color: "purple", knock: 0.0, name: "Shadow Claws", special: "rend",
    desc: "Every hit makes the enemy bleed. Use: Rending Pounce (leap on the enemy, three rakes that heal you). Sneak + use: Claw Storm." },
  // ثقيل جدا: يكسر الأرض فعلاً والبلوكات تسقط لك
  "sh:stone_maul": { extra: 11, sound: "sh.cleaver_hit", color: "green", knock: 2.0, name: "Stone Maul", shock: true, heavy: 2,
    desc: "Every hit shakes the ground. Use: Earthbreaker (smash a crater, the blocks drop for you). Sneak + use: Seismic Fissure. Weakness: slows you a lot." },
  // رمح: ترميه ويرجع، أو مطر رماح
  "sh:sunset_spear": { extra: 5, sound: "sh.dagger_hit", color: "red", knock: 0.4, name: "Sunset Spear",
    desc: "Use: Sunset Throw (it returns to you). Sneak + use: Spear Rain on the spot you aim at." },
};

// الوحوش اللي ينفع عليها قانون الصمت (عندها حدث sh:silence)
const RANGED_TYPES = new Set(["sh:training_archer"]);

// ───────────────────────── أدوات عامة ─────────────────────────
const wait = (t) => new Promise((r) => system.runTimeout(r, t));

function getState(p) {
  try {
    const raw = p.getDynamicProperty("sh");
    if (typeof raw === "string") return { ...defaultState(), ...JSON.parse(raw) };
  } catch (e) { /* نرجع للافتراضي */ }
  return defaultState();
}
function saveState(p, st) {
  try { p.setDynamicProperty("sh", JSON.stringify(st)); } catch (e) { /* ما نوقف اللعبة */ }
}

const tempMsg = new Map();
function notify(p, text, ticks = 60) {
  tempMsg.set(p.id, { text, until: system.currentTick + ticks });
}
function say(p, text) {
  try { p.sendMessage(text); } catch (e) { /* */ }
}

// ───────────────────────── واجهة اللاعب (HUD) ─────────────────────────
// تنعرض عبر شريط الأكشن وتتنقل لأعلى الشاشة بملف ui بالـRP. الأسطر:
//   1) الرتبة │ القدرة │ نجوم الندرة │ ليفل القدرة
//   2) الصحة │ ليفل اللاعب + شريط الخبرة
//   3) شريط المهارات: جاهزة ✔ / كولداون ثواني / مقفولة ✖ (المسكوكة بيدك بين أقواس)
//   4) معلومات الأيتم اللي بيدك (مستوى المهارة وحالتها)
//   5) تلميح طريقة الاستعمال (يظهر 6 ثواني بعد ما تمسك الأيتم)
// أوسمة: sh_hud_off يطفي الواجهة | sh_hud_plain شريط بسيط إذا الرموز ما تنعرض عندك.
function bar(frac, len, on, off = "§8", plain = false) {
  const n = Math.max(0, Math.min(len, Math.round(frac * len)));
  const ch = plain ? "|" : "█";
  return on + ch.repeat(n) + off + ch.repeat(len - n);
}
const fmtSec = (ticks) => (ticks / 20).toFixed(ticks >= 200 ? 0 : 1);
function rarityStars(key) {
  const idx = RARITIES.findIndex((r) => r.key === POWER_RARITY[key]);
  return rarityOf(key).color + "★".repeat(idx + 1) + "§8" + "★".repeat(RARITIES.length - idx - 1);
}
// ───── رموز الـHUD المرسومة (RP/font/glyph_E5.png من tools/gen_hud_art.py): الرمز i = U+E500+i ─────
const GI = { heart: 0, heart_half: 1, heart_empty: 2, rift: 3, wave_on: 4, wave_off: 5, gold_full: 6, gold_empty: 7, xp_full: 8, xp_empty: 9,
  pw_full: 10, pw_empty: 11, boss: 12, rank0: 16, power0: 32, ready: 48, cool: 49, lock: 50, held: 51, sword: 52, lens: 53, rift_ring: 54, sep: 55 };
const GLYPH_POWERS = ["iron", "wind", "echo", "crystal", "accountant", "borrower", "distance", "law", "star"];
const GL = (i) => String.fromCharCode(0xE500 + i);
function gbar(frac, n, full, empty) {
  const k = Math.max(0, Math.min(n, Math.round(frac * n)));
  return "§f" + GL(full).repeat(k) + GL(empty).repeat(n - k);
}
function gHearts(cur, max) {
  const h = Math.max(0, Math.min(10, (cur / Math.max(1, max)) * 10));
  const full = Math.floor(h), half = h - full >= 0.5 ? 1 : 0;
  return "§f" + GL(GI.heart).repeat(full) + GL(GI.heart_half).repeat(half) + GL(GI.heart_empty).repeat(10 - full - half);
}
function hudArt(p, st) {
  const pw = POWERS[st.power];
  const rp = rankProgress(st);
  let hpTxt = "";
  try {
    const h = p.getComponent("minecraft:health");
    hpTxt = `${gHearts(h.currentValue, h.effectiveMax)} §c${Math.ceil(h.currentValue)}§7/${Math.ceil(h.effectiveMax)}`;
  } catch (e) { /* */ }
  const l1 = `§f${GL(GI.rank0 + Math.min(6, st.rank))} §6§l${RANKS[st.rank]}§r ${gbar(rp.frac, 6, GI.gold_full, GI.gold_empty)} §7${rp.max ? "MAX" : `${rp.cur}/${rp.need}`}  ${hpTxt}`;
  const need = xpNeeded(st.level);
  let l2 = `§bLv §l${st.level}§r ${gbar(st.xp / need, 5, GI.xp_full, GI.xp_empty)} §7${Math.floor((st.xp / need) * 100)}%`;
  if (pw) {
    const r = rarityOf(st.power), pl = st.plevel || 1;
    const pfrac = pl >= r.maxLv ? 1 : (st.pxp || 0) / powerXpNeeded(pl);
    l2 += `  §f${GL(GI.power0 + Math.max(0, GLYPH_POWERS.indexOf(st.power)))} ${pw.color}${pw.name} §dLv${pl}/${r.maxLv} ${gbar(pfrac, 5, GI.pw_full, GI.pw_empty)}`;
  } else l2 += st.powerless ? "  §8§lUnbound §r§c+STR §b+SPD" : "  §7No power: find the Star Temple";
  const l3 = riftHudLine(p, false);
  return l3 ? `${l1}\n${l2}\n${l3}` : `${l1}\n${l2}`;
}
function hudText(p, st, plain) {
  if (!plain) return hudArt(p, st);
  const rl = riftHudLine(p, true);
  if (rl) return hudPlain(p, st) + "\n" + rl;
  return hudPlain(p, st);
}
function hudPlain(p, st) {
  const pw = POWERS[st.power];
  const rp = rankProgress(st);
  let hp = "§c♥ --";
  try {
    const h = p.getComponent("minecraft:health");
    hp = `§c♥ ${bar(h.currentValue / h.effectiveMax, 6, "§c", "§8", plain)} §f${Math.ceil(h.currentValue)}§7/${Math.ceil(h.effectiveMax)}`;
  } catch (e) { /* */ }
  // سطر 1: الرتبة + تقدمها │ الصحة
  const l1 = `§6◆ ${RANKS[st.rank]} ${bar(rp.frac, 6, "§6", "§8", plain)} §7${rp.max ? "MAX" : `${rp.cur}/${rp.need}`} §8│ ${hp}`;
  // سطر 2: ليفل اللاعب + خبرته │ القدرة وتطورها
  const need = xpNeeded(st.level);
  let l2 = `§bLv ${st.level} ${bar(st.xp / need, 6, "§b", "§8", plain)} §7${Math.floor((st.xp / need) * 100)}%`;
  if (pw) {
    const r = rarityOf(st.power), pl = st.plevel || 1;
    const pfrac = pl >= r.maxLv ? 1 : (st.pxp || 0) / powerXpNeeded(pl);
    l2 += ` §8│ ${pw.color}${pw.name} §dLv${pl}/${r.maxLv} ${bar(pfrac, 5, "§d", "§8", plain)}`;
  } else l2 += " §8│ §7No power";
  return `${l1}\n${l2}`;
}

// شريط المهارات + نغمة خفيفة لما تخلص مهارة طويلة الكولداون
const wasCooling = new Map();
function skillStrip(p, st, heldId, plain) {
  if (!st.power) return "";
  const now = system.currentTick;
  const mine = Object.values(SKILLS).filter((s) => s.power === st.power);
  const parts = mine.map((s, i) => {
    const n = i + 1;
    let txt;
    if (!isSkillUnlocked(st, s)) txt = plain ? `§8${n}✖` : `§f${GL(GI.lock)}§8${n}`;
    else {
      const key = `${p.id}:${s.id}`;
      const left = (cooldowns.get(key) ?? 0) - now;
      const cooling = left > 0;
      if (wasCooling.get(key) && !cooling && s.cooldown >= 100) {
        sfxPlayer(p, "sh.ready", 0.5);
        const m = tempMsg.get(p.id);
        if (!m || m.until <= now) notify(p, `§a✔ ${s.name} ready`, 25);
      }
      wasCooling.set(key, cooling);
      txt = plain ? (cooling ? `§c${n}·${fmtSec(left)}` : `§a${n}✔`) : (cooling ? `§f${GL(GI.cool)}§c${n} ${fmtSec(left)}` : `§f${GL(GI.ready)}§a${n}`);
    }
    return heldId === s.id ? (plain ? `§e[${txt}§e]` : `§f${GL(GI.held)}${txt}`) : txt;
  });
  return `§7Skills ${parts.join(plain ? " " : "  ")}`;
}

// معلومات الأيتم اللي بإيدك + تلميح طريقة الاستعمال
const heldSeen = new Map();
function heldLine(p, st, plain) {
  const now = system.currentTick;
  const held = inv(p).getItem(p.selectedSlotIndex);
  const id = held ? held.typeId : "";
  const seen = heldSeen.get(p.id);
  if (!seen || seen.id !== id) heldSeen.set(p.id, { id, tick: now });
  const showTip = now - heldSeen.get(p.id).tick < 120;
  const none = { line: "", tip: "" };
  if (!id) return none;
  const stateOf = (left) => (left > 0 ? `§c⏳ ${fmtSec(left)}s` : "§a✔ Ready");
  const mini = (left) => (left > 0 ? `§c${fmtSec(left)}s` : "§a✔");

  const sk = ITEM_TO_SKILL[id];
  if (sk) {
    if (st.power !== sk.power) return { line: `§c${sk.name}: not part of your power`, tip: "" };
    const lv = skillLevel(st, sk.id);
    const x = (st.skills && st.skills[sk.id] && st.skills[sk.id].xp) || 0;
    const left = (cooldowns.get(`${p.id}:${sk.id}`) ?? 0) - now;
    return {
      skillId: sk.id,
      line: `${POWERS[sk.power].color}${sk.name} §8│ §bLevel ${lv}${lv >= SKILL_MAX_LV ? " §6MAX" : ""} ${bar(lv >= SKILL_MAX_LV ? 1 : x / skillXpNeeded(lv), 5, "§b", "§8", plain)} §8│ ${stateOf(left)}`,
      tip: showTip ? `§7${usageOf(sk)}` : "",
    };
  }
  if (id === KATANA) {
    const kat = getKat(p);
    const prog = kat.lv >= KAT_MAX ? "§6MAX" : bar(kat.xp / KAT_NEED[kat.lv], 4, "§5", "§8", plain);
    const l0 = (weaponCd.get(`${p.id}:${KATANA}:0`) ?? 0) - now, l1 = (weaponCd.get(`${p.id}:${KATANA}:1`) ?? 0) - now;
    return {
      line: `§5⚔ Katana §8Lv${kat.lv} ${prog} §8│ §d${KATANA_SKILLS[0].name} ${mini(l0)} §8│ §7S: §d${KATANA_SKILLS[1].name} ${mini(l1)}`,
      tip: showTip ? `§7Use: ${KATANA_SKILLS[0].name} §8│ §7Sneak + use: ${KATANA_SKILLS[1].name}` : "",
    };
  }
  if (id === "sh:explorer_compass") {
    const key = compassKey(p), tg = compassFind(p, key);
    const nm = (COMPASS_TARGETS.find((t) => t.key === key) || COMPASS_TARGETS[5]).name;
    const line = tg
      ? `§6◎ ${tg.name} §8│ §f${Math.round(Math.hypot(tg.x - p.location.x, tg.z - p.location.z))}m §e${compassArrow(p, tg)}`
      : `§6◎ ${nm} §8│ §7Not discovered yet, explore more`;
    return { line, tip: showTip ? "§7Use: choose destination §8│ §7Sneak + use: guide line" : "" };
  }
  if (id === "sh:star_shard") return { line: "§b✦ Star Shard", tip: showTip ? (st.power ? "§7You already carry a power" : "§7Use: points you to the Star Temple") : "" };
  if (id === "sh:skill_scroll") return { line: "§b✦ Skill Upgrade Scroll", tip: showTip ? "§7Use: pick a skill and raise it a full level" : "" };
  if (id === "sh:evolution_book") return { line: "§eEvolution Book", tip: showTip ? "§7Use: skills, status window, ranks, story" : "" };
  if (id === "sh:monster_book") return { line: "§5Monster Book", tip: showTip ? "§7Use: info on the monsters you have killed" : "" };
  const ws = WEAPON_SKILLS[id];
  if (ws) {
    const l0 = (weaponCd.get(`${p.id}:${id}:0`) ?? 0) - now, l1 = (weaponCd.get(`${p.id}:${id}:1`) ?? 0) - now;
    const wk = getWlv(p, id), lk = wk.lv < 2;
    return { line: `§f⚔ §6Lv${wk.lv}${wk.lv >= WLV_MAX ? "★" : ""} §e${ws[0].name} ${mini(l0)} §8│ §7S: ${lk ? `§8${ws[1].name} (Lv2)` : `§e${ws[1].name} ${mini(l1)}`}`,
      tip: showTip ? `§7Use: ${ws[0].name} §8│ §7Sneak + use: ${ws[1].name}${wk.lv < WLV_MAX ? ` §8│ §7XP ${wk.xp}/${WLV_NEED[wk.lv]}` : ""}` : "" };
  }
  return none;
}

function renderHud(p) {
    try {
      if (p.hasTag("sh_hud_off")) return;
      const plain = p.hasTag("sh_hud_plain");
      const st = getState(p);
      const h = heldLine(p, st, plain);
      let text = hudText(p, st, plain);
      const strip = skillStrip(p, st, h.skillId, plain);
      if (strip) text += "\n" + strip;
      const m = tempMsg.get(p.id);
      if (m && m.until > system.currentTick) text += "\n" + m.text;
      else {
        if (h.line) text += "\n" + h.line;
        if (h.tip) text += "\n" + h.tip;
      }
      p.onScreenDisplay.setActionBar(text);
    } catch (e) { /* */ }
}
system.runInterval(() => { for (const p of world.getAllPlayers()) renderHud(p); }, 5);

async function showForm(player, form) {
  for (let i = 0; i < 30; i++) {
    const r = await form.show(player);
    if (r.canceled && r.cancelationReason === "UserBusy") { await wait(20); continue; }
    return r;
  }
  return { canceled: true };
}

// ───────────────────────── جزيئات وأصوات ─────────────────────────
const POWER_COLOR = {};
const COLORS = {
  gold: [1.0, 0.78, 0.2], orange: [1.0, 0.5, 0.15], red: [1.0, 0.2, 0.2],
  teal: [0.43, 1.0, 0.8], purple: [0.65, 0.3, 1.0], blue: [0.3, 0.7, 1.0], white: [0.95, 0.95, 1.0], green: [0.4, 1.0, 0.5],
};

POWER_COLOR.accountant = COLORS.gold;
POWER_COLOR.law = COLORS.purple;
POWER_COLOR.distance = COLORS.blue;
POWER_COLOR.echo = [0.3, 0.95, 0.9];
POWER_COLOR.crystal = [1.0, 0.6, 0.85];
POWER_COLOR.borrower = [1.0, 0.7, 0.2];
POWER_COLOR.iron = [0.75, 0.78, 0.85];
POWER_COLOR.wind = COLORS.green;
POWER_COLOR.star = [0.5, 0.72, 1.0];

// أماكن عيون اللاعبين (تتحدث كل تكين): الجزيئات القريبة من الكاميرا ما تنرسم حتى ما تغطي الشاشة
const eyeCache = [];
system.runInterval(() => {
  eyeCache.length = 0;
  for (const p of world.getAllPlayers()) { try { const h = p.getHeadLocation(); eyeCache.push({ d: p.dimension.id, x: h.x, y: h.y, z: h.z }); } catch (e) { /* */ } }
}, 2);
function nearEye(dim, loc, r) {
  for (const c of eyeCache) {
    if (c.d !== dim.id) continue;
    const dx = c.x - loc.x, dy = c.y - loc.y, dz = c.z - loc.z;
    if (dx * dx + dy * dy + dz * dz < r * r) return true;
  }
  return false;
}
function glow(dim, loc, o = {}) {
  try {
    const sz = Math.min(1.1, o.size ?? 0.18);
    if (nearEye(dim, loc, 1.4 + sz * 1.5)) return;
    const c = o.color || COLORS.gold;
    const m = new MolangVariableMap();
    m.setFloat("variable.r", c[0]);
    m.setFloat("variable.g", c[1]);
    m.setFloat("variable.b", c[2]);
    m.setFloat("variable.size", sz);
    m.setFloat("variable.life", o.life ?? 0.7);
    m.setFloat("variable.speed", o.speed ?? 0.0);
    m.setFloat("variable.rise", o.rise ?? 0.0);
    dim.spawnParticle("sh:glow", loc, m);
  } catch (e) { /* مكان غير محمل */ }
}

function burst(dim, loc, n, color, speed = 2.5, size = 0.2) {
  for (let i = 0; i < n; i++) glow(dim, loc, { color, speed, size, life: 0.6, rise: 0.5 });
}

// مربع بكسل صغير يتوهج (جزيء sh:pixel) — يعطي شكل شظايا مثل صورة السيف
let pixBudget = 0;
system.runInterval(() => { pixBudget = 0; }, 1);
function pix(dim, loc, o = {}) {
  try {
    if (++pixBudget > 70) return; // حد أعلى بالتك الواحد
    const sz = Math.min(0.16, (o.size ?? 0.14) * 0.6);
    if (nearEye(dim, loc, o.eye ?? 1.6)) return;
    const c = o.color || COLORS.gold;
    const m = new MolangVariableMap();
    m.setFloat("variable.r", c[0]);
    m.setFloat("variable.g", c[1]);
    m.setFloat("variable.b", c[2]);
    m.setFloat("variable.size", sz);
    m.setFloat("variable.life", o.life ?? 0.7);
    m.setFloat("variable.speed", o.speed ?? 0.0);
    m.setFloat("variable.rise", o.rise ?? 0.0);
    dim.spawnParticle("sh:pixel", loc, m);
  } catch (e) { /* مكان غير محمل */ }
}
const later = (t, fn) => system.runTimeout(() => { try { fn(); } catch (e) { /* */ } }, Math.max(1, t));

function ring(dim, c, r, n, phase, color, size = 0.2) {
  for (let i = 0; i < n; i++) {
    const a = phase + (i / n) * Math.PI * 2;
    glow(dim, { x: c.x + Math.cos(a) * r, y: c.y + 0.15, z: c.z + Math.sin(a) * r }, { color, size, life: 0.8, rise: 0.4 });
  }
}

function line(dim, from, to, color) {
  const steps = 14;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    glow(dim, { x: from.x + (to.x - from.x) * t, y: from.y + (to.y - from.y) * t, z: from.z + (to.z - from.z) * t },
      { color, size: 0.12, life: 0.35 });
  }
}

function sfx(dim, id, loc, volume = 1, pitch = 1) {
  try { dim.playSound(id, loc, { volume, pitch }); } catch (e) { /* */ }
}
function sfxPlayer(p, id, volume = 1, pitch = 1) {
  try { p.playSound(id, { volume, pitch }); } catch (e) { /* */ }
}
function shake(p, amount = 0.1, secs = 0.12) {
  try { p.runCommand(`camerashake add @s ${amount} ${secs}`); } catch (e) { /* */ }
}

function headPos(e) {
  const l = e.location;
  let h = 1.6;
  try { h = e.getHeadLocation().y - l.y + 0.5; } catch (err) { /* */ }
  return { x: l.x, y: l.y + h, z: l.z };
}

// ───────────────────────── الإنفنتوري ─────────────────────────
function inv(p) {
  return p.getComponent("minecraft:inventory").container;
}
function hasItem(p, typeId) {
  const c = inv(p);
  for (let i = 0; i < c.size; i++) {
    const it = c.getItem(i);
    if (it && it.typeId === typeId) return true;
  }
  return false;
}
function giveItem(p, typeId, amount = 1) {
  const left = inv(p).addItem(new ItemStack(typeId, amount));
  if (left) p.dimension.spawnItem(left, p.location);
}
function removeSkillItems(p) {
  const c = inv(p);
  for (let i = 0; i < c.size; i++) {
    const it = c.getItem(i);
    if (it && ITEM_TO_SKILL[it.typeId]) c.setItem(i, undefined);
  }
}

// ───────────────────────── القوائم ─────────────────────────
const POWER_KEYS = ["iron", "wind", "echo", "crystal", "accountant", "borrower", "distance", "law", "star"];

// القدرة تجي عشوائيا، ويمكن ما تطلع لك أي قدرة (للتجربة: /tag @s add sh_menu يرجع قائمة الاختيار)
const RANDOM_POWERS = true;
// احتمال "بلا قدرة" (Unbound) وقت السحب بالمعبد: 0.5% (أقل من أندر قدرة). بدالها الجسم يقوى ويسرع مع الرتبة.
const NO_POWER_CHANCE = 0.005;

function grantPower(player, key) {
  const pw = POWERS[key];
  const st = getState(player);
  st.power = key;
  st.powerless = false;
  saveState(player, st);
  sfxPlayer(player, "sh.select");
  burst(player.dimension, headPos(player), 24, POWER_COLOR[key], 3);
  notify(player, `${pw.color}Your power: ${pw.name}`, 80);
  const rar = rarityOf(key);
  say(player, `§e[Power] §fYou drew ${pw.color}${pw.name}§f, rarity ${rar.color}${rar.name}§f (${rar.skills} skills, max level ${rar.maxLv}). ${pw.desc}`);
  say(player, "§e[Power] §fFind the Trainer so they can teach you the basics.");
  const t = ensureTrainerNear(player, true);
  if (t) say(player, `§e[Trainer] §f${describeDir(player, t)}`);
}

// القرعة موزونة بالندرة (تنستعمل بالمعبد)
const drawing = new Set();
function pickPowerKey() {
  let total = 0;
  for (const k of POWER_KEYS) total += rarityOf(k).weight;
  let roll = Math.random() * total, pick = POWER_KEYS[0];
  for (const k of POWER_KEYS) { roll -= rarityOf(k).weight; if (roll <= 0) { pick = k; break; } }
  return pick;
}
function removeOne(p, typeId) {
  const c = inv(p);
  for (let i = 0; i < c.size; i++) {
    const it = c.getItem(i);
    if (it && it.typeId === typeId) { if (it.amount > 1) { it.amount -= 1; c.setItem(i, it); } else c.setItem(i, undefined); return true; }
  }
  return false;
}
// ───────────────────────── معبد النجمة: السحب بالدوس على البلورة ─────────────────────────
// أول ما تدخل بدون قدرة يطلع معبد قريب منك (أو يدلك على الموجود). بنصه لوحة ذهبية فوقها بلورة كبيرة:
// تدوس على اللوحة يبدي السحب، ولون البلورة يتقلب بين الندرات (أبيض شائع ← أخضر ← أزرق ← بنفسجي ← ذهبي ← أحمر خرافي)
// ويوقف على لون قدرتك. نادراً جداً (0.5%) البلورة تنطفي: "بلا قدرة" (Unbound) بجسم أقوى وأسرع.
const DRAW_VARIANTS = ["draw_common", "draw_uncommon", "draw_rare", "draw_epic", "draw_legendary", "draw_mythic"];
const RAR_RGB = [[0.85, 0.87, 0.92], [0.4, 0.95, 0.5], [0.45, 0.65, 1], [0.7, 0.45, 1], [1, 0.8, 0.3], [1, 0.3, 0.35]];
const templeFx = new Map(); // "x,y,z" -> { e, mode, v, until }
let templeBusy = false;
function templeCenter(t) { return { x: t.x + 0.5, y: t.y + 1, z: t.z + 0.5 }; }
function templeKey(t) { return `${t.x},${t.y},${t.z}`; }
function rarityIndexOf(key) { return Math.max(0, RARITIES.findIndex((r) => r.key === rarityOf(key).key)); }
function needsDraw(st) { return !st.power && !st.powerless; }
function guideTemple(p, t) {
  try {
    const c = templeCenter(t), dx = c.x - p.location.x, dz = c.z - p.location.z, dist = Math.round(Math.hypot(dx, dz));
    const dirs = ["east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"];
    const dir = dirs[((Math.round((Math.atan2(dz, dx) * 180) / Math.PI / 45) % 8) + 8) % 8];
    say(p, `§b[Star Temple] §f${dist} blocks to the ${dir}. Walk inside and §estep on the golden plate§f under the crystal to awaken your power.`);
    notify(p, "§bFollow the light to the Star Temple", 100);
    p.setDynamicProperty("sh_ctarget", "temple");
  } catch (e) { /* */ }
}
function ensureTemple(p) {
  try {
    if (!needsDraw(getState(p)) || p.dimension.id !== "minecraft:overworld") return;
    // المعبد ينبني مرة وحدة بالعالم: إذا موجود (بأي مسافة) ندلك عليه
    const t = findTemple(p.location);
    if (t) { guideTemple(p, t); return; }
    if (templeBusy) return;
    templeBusy = true;
    say(p, "§b[Fallen Star] §fThe ground trembles... a great §bStar Temple§f rises right in front of you. It appears only once in this world. The heart of the fallen star waits inside.");
    sfxPlayer(p, "sh.supernova_charge", 0.8, 0.6);
    shake(p, 0.15, 1.2);
    buildTemple(p, (rec) => { templeBusy = false; if (valid(p)) guideTemple(p, rec); });
  } catch (e) { templeBusy = false; }
}
// البلورة: تتبنى وقت يكون لاعب قريب، وبالراحة تتقلب ألوانها ببطء
system.runInterval(() => {
  const now = system.currentTick;
  let temples = [];
  try { temples = getStructs().filter((s) => s.type === "temple"); } catch (e) { /* */ }
  for (const t of temples) {
    try {
      const dim = world.getDimension("minecraft:overworld"), c = templeCenter(t);
      const near = world.getAllPlayers().filter((q) => q.dimension.id === dim.id && Math.hypot(q.location.x - c.x, q.location.z - c.z) < 56);
      const k = templeKey(t);
      let f = templeFx.get(k);
      if (!near.length) { if (f) { removeFx(f.e); templeFx.delete(k); } continue; }
      if (!f) { f = { e: undefined, mode: "idle", v: 0, until: 0 }; templeFx.set(k, f); }
      if (f.mode === "show" && now > f.until) f.mode = "idle";
      if (f.mode === "idle" && now % 40 === 0) f.v = (f.v + 1) % DRAW_VARIANTS.length;
      const name = f.v === -1 ? "draw_void" : DRAW_VARIANTS[f.v];
      const at = { x: c.x, y: c.y + 1.3 + Math.sin(now * 0.05) * 0.12, z: c.z };
      if (!f.e || !valid(f.e)) f.e = shapeFx(dim, name, at, { r: 1.15, s: f.mode === "draw" ? 240 : 25, life: 1100 });
      else { moveShape(f.e, at); setShape(f.e, "sh:v", SHAPE[name]); setShape(f.e, "sh:s", f.mode === "draw" ? 240 : 25); }
      if (now % 10 === 0) {
        const col = f.v === -1 ? [0.4, 0.3, 0.6] : RAR_RGB[f.v];
        glow(dim, { x: c.x + (Math.random() - 0.5) * 2, y: c.y + 0.3, z: c.z + (Math.random() - 0.5) * 2 }, { color: col, size: 0.22, life: 1.4, rise: 1.2 });
      }
      // عمود ضوء يدل اللاعبين اللي بعدهم بدون قدرة
      if (now % 20 === 0 && near.some((q) => needsDraw(getState(q)))) {
        for (let y = 6; y < 22; y += 2) glow(dim, { x: c.x, y: c.y + y, z: c.z }, { color: [0.6, 0.85, 1], size: 0.35, life: 1.1, rise: 1 });
      }
    } catch (e) { /* */ }
  }
}, 2);
// الدوس على اللوحة الذهبية يبدي السحب
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      if (drawing.has(p.id) || p.dimension.id !== "minecraft:overworld") continue;
      const st = getState(p);
      if (!needsDraw(st)) continue;
      const t = findTemple(p.location, 12);
      if (!t) continue;
      const c = templeCenter(t);
      if (Math.hypot(p.location.x - c.x, p.location.z - c.z) < 0.85 && Math.abs(p.location.y - c.y) < 1.3) startDraw(p, t);
    } catch (e) { /* */ }
  }
}, 4);
// السحب: العناوين تتقلب، والبلورة تتلون حسب ندرة كل قدرة، وتوقف على لون قدرتك
function startDraw(p, t) {
  const k = templeKey(t);
  const f = templeFx.get(k) || { e: undefined, mode: "idle", v: 0, until: 0 };
  templeFx.set(k, f);
  f.mode = "draw";
  drawing.add(p.id);
  const unbound = Math.random() < NO_POWER_CHANCE;
  const key = unbound ? null : pickPowerKey();
  const frames = 22, offset = Math.floor(Math.random() * POWER_KEYS.length);
  const dim = p.dimension, c = templeCenter(t);
  let last = 8;
  sfxPlayer(p, "sh.supernova_charge", 0.9, 1.1);
  try { p.camera.fade({ fadeColor: { red: 0.7, green: 0.85, blue: 1 }, fadeTime: { fadeInTime: 0.1, holdTime: 0.1, fadeOutTime: 0.6 } }); } catch (e) { /* */ }
  for (let i = 0; i < frames; i++) {
    const at = Math.floor(8 + i * 1.5 + i * i * 0.2);
    last = at;
    later(at, () => {
      if (!valid(p)) return;
      const kk = POWER_KEYS[(i + offset) % POWER_KEYS.length];
      const pw = POWERS[kk], rar = rarityOf(kk);
      f.v = rarityIndexOf(kk);
      try { p.onScreenDisplay.setTitle(`${pw.color}${pw.name}`, { subtitle: `${rar.color}${rar.name}`, fadeInDuration: 0, stayDuration: 6, fadeOutDuration: 0 }); } catch (e) { /* */ }
      sfxPlayer(p, "sh.tick", 0.7, 0.8 + i * 0.04);
      glow(dim, { x: c.x, y: c.y + 2.2, z: c.z }, { color: RAR_RGB[f.v], size: 0.6, life: 0.4 });
    });
  }
  later(last + 16, () => {
    drawing.delete(p.id);
    f.mode = "show"; f.until = system.currentTick + 240;
    if (!valid(p)) return;
    const s2 = getState(p);
    if (!needsDraw(s2)) return;
    if (unbound) {
      f.v = -1;
      s2.powerless = true;
      saveState(p, s2);
      applyVitality(p, true);
      try { p.onScreenDisplay.setTitle("§8§lUNBOUND", { subtitle: "§7The crystal stays dark... your body answers instead", fadeInDuration: 8, stayDuration: 90, fadeOutDuration: 24 }); } catch (e) { /* */ }
      sfxPlayer(p, "sh.blackhole_end", 1, 0.7);
      popShape(dim, "nova", { x: c.x, y: c.y + 2, z: c.z }, 0.3, 2.2, 10, { s: 300 });
      say(p, "§8[Unbound] §fThe star gave you no power: one in two hundred. Instead your body refuses to break: §cstronger §fand §bfaster§f, and it grows with every rank. The Trainer has nothing to teach you; fight with weapons and your own fists.");
      return;
    }
    grantPower(p, key);
    const pw = POWERS[key], rar = rarityOf(key), idx = rarityIndexOf(key);
    f.v = idx;
    try { p.onScreenDisplay.setTitle(`§l${pw.color}${pw.name}`, { subtitle: `${rar.color}${rar.name}  ${rarityStars(key)}`, fadeInDuration: 6, stayDuration: 80, fadeOutDuration: 24 }); } catch (e) { /* */ }
    const col = RAR_RGB[idx];
    popShape(dim, "nova", { x: c.x, y: c.y + 2.2, z: c.z }, 0.3, 1.6 + idx * 0.4, 10, { s: 300, ease: "out" });
    waveFx(dim, c, 6 + idx, 0, 14);
    burst(dim, { x: c.x, y: c.y + 2.2, z: c.z }, 20 + idx * 10, col, 4 + idx * 0.6, 0.28);
    sfxPlayer(p, idx >= 4 ? "sh.supernova_boom" : idx >= 2 ? "sh.rank_up" : "sh.level_up", idx >= 4 ? 0.9 : 1, 1);
    if (idx >= 2) shake(p, 0.1 + idx * 0.05, 0.4);
  });
}
// توافق قديم: الشظية صارت تدلك على المعبد
function ensureShard(p) { ensureTemple(p); }
function useStarShard(p) {
  const st = getState(p);
  if (!needsDraw(st)) { notify(p, "§7The shard is silent. Your fate is already drawn.", 60); return; }
  ensureTemple(p);
}

async function openPowerMenu(player) {
  const st0 = getState(player);
  if (st0.power) return openBook(player);
  if (st0.powerless) {
    await showForm(player, new ActionFormData().title("Unbound").body("§8The crystal stayed dark for you.§r\n\nYou carry no power, but your body grows with your rank:\n§c+ Strength§7 (more at Warrior and Legend)\n§b+ Speed§7 (more at Elite)\n§7+ Resistance at Commander\n\nFight with the mod's weapons and the Rhythm Strike (from Elite, 30% stronger for the Unbound).").button("§aOK"));
    return;
  }
  if (!player.hasTag("sh_menu")) {
    // السحب يصير بمعبد النجمة: ندلك عليه (أو نبنيه إذا ماكو)
    ensureTemple(player);
    return;
  }

  const form = new ActionFormData()
    .title("Choose your power")
    .body(
      POWER_KEYS.map((k) => `${POWERS[k].color}${POWERS[k].name}§r\n${POWERS[k].desc}`).join("\n\n") +
      "\n\n§7This choice is final: the other powers vanish."
    );
  for (const k of POWER_KEYS) form.button(`${POWERS[k].color}${POWERS[k].name}`);
  const r = await showForm(player, form);
  if (r.canceled) { notify(player, "§7Open the Evolution Book to choose your power", 100); return; }
  const key = POWER_KEYS[r.selection];
  const pw = POWERS[key];

  const conf = new ActionFormData()
    .title("Confirm")
    .body(`Lock in ${pw.color}${pw.name}§r?\n\n${pw.desc}`)
    .button("§aConfirm")
    .button("§cBack");
  const c = await showForm(player, conf);
  if (c.canceled || c.selection !== 0) return openPowerMenu(player);

  const st = getState(player);
  if (st.power) return;
  st.power = key;
  saveState(player, st);
  sfxPlayer(player, "sh.select");
  burst(player.dimension, headPos(player), 24, POWER_COLOR[key], 3);
  notify(player, `${pw.color}Your power: ${pw.name}`, 80);
  say(player, `§e[Power] §fYou chose ${pw.color}${pw.name}§f. Find the Trainer so they can teach you the basics.`);
  const t = ensureTrainerNear(player, true);
  if (t) say(player, `§e[Trainer] §f${describeDir(player, t)}`);
}

function nextRankLine(st) {
  if (st.rank >= RANKS.length - 1) return "§6You reached the highest rank";
  const need = (st.rank + 1) * LEVELS_PER_RANK;
  return `§7Next rank: §e${RANKS[st.rank + 1]}§7 at level §b${need}§7 (${Math.max(0, need - st.level)} to go)`;
}

async function showRanks(player) {
  const st = getState(player);
  let body = "§eRanks and how to rise§r\n\n";
  RANKS.forEach((n, i) => {
    const mark = i === st.rank ? "§a◀ You are here" : "";
    body += `${i === st.rank ? "§a" : "§f"}${i + 1}. ${n}§7 (from level ${i * LEVELS_PER_RANK}) ${mark}\n`;
  });
  body += `\n§bNormal promotion:§f every ${LEVELS_PER_RANK} levels you gain a rank.\n`;
  body += `§bJump:§f if you kill a monster two or more ranks above you, you rank up instantly (for the first ranks, up to ${RANKS[HARD_RANK_FROM]}).\n`;
  body += `§bAfterwards:§f killing a stronger monster gives triple experience but does not rank you up.\n`;
  body += "§bWeak:§f a monster three ranks below you gives half the experience.\n\n";
  body += "§7Experience comes from: killing monsters, XP scrolls, and some structure chests.";
  await showForm(player, new ActionFormData().title("Ranks").body(body).button("§aOK"));
}

// ───────────────────────── حكاية العالم: «النجمة الساقطة» ─────────────────────────
// 7 فصول، فصل لكل رتبة. الفصل ينفتح لما توصل رتبته (حتى تكون الرتب لها معنى بالحكاية).
const LORE_TITLE = "The Tale of the Fallen Star";
const LORE = [
  ["The Night the Star Fell",
    "A thousand years ago, on the longest night the world remembers, a great star named \"Siraj al-Fajr\" fell from the sky. Its heart did not burn out: it froze into a crystal and sank into the earth, and wherever its light reached, temples grew around it.\n\nWhoever steps into that light draws a power, and the crystal shows its worth in color: white for common, then green, blue, violet, gold, and the red of the rarest. Once in two hundred souls the crystal stays dark. Those are the Unbound: no power answers them, so their own bodies grow stronger instead."],
  ["The Order of Dawn",
    "The first who carried powers founded the \"Order of Dawn\" to keep them from the wrong hands. They set seven ranks, one for each night the star burned: Novice, Trainee, Warrior, Elite, Commander, Legend, and Master.\n\nNo rank was ever given by birth or gold, only by what you defeat and what you learn. The Trainer is the last of the Order who still teaches. They built Sakura Village as their first home and planted pink trees so they would remember that beauty deserves protection."],
  ["The Abyss",
    "But the star did not fall alone. A black void followed it as a shadow follows its owner: \"the Abyss\". Whatever it touches loses its color, then its name.\n\nFrom it came the creatures you fight: the Ember Imp was born from the ashes of burned villages, the Rust Guard watched a temple until it forgot what it guarded, the Shadow Hound hunts on the star's old trail, and the Sand Scorpion carries the Abyss's own venom in its tail."],
  ["The Rifts",
    "The Abyss still breathes through wounds in the world: the Rifts. They open without warning, spread rot around them, and spill out waves of its creatures. At the end of each wave stands a Warden, and the color of the Rift tells its rank: blue for the Lowly, violet for the Vile, crimson for the Dread, and black-gold for the Cataclysm.\n\nSeal a Rift by defeating its Warden. Leave it open, and the Warden walks free."],
  ["Sunset Palace",
    "When the Abyss came for the Order, its last commanders made their stand in a palace on the edge of the horizon, \"Sunset Palace\", where the final light of their days fell. They fought with a spear of sunlight and a maul of living stone.\n\nThe palace fell, but the Abyss paid for it and sank back into the deep. Its towers still hide the weapons the guards could not carry away. Weapons remember: the more you fight with one, the more it gives back."],
  ["The Abyss Katana",
    "Light alone could not close the Abyss, so the last smith of the Order forged a blade from its own darkness: \"the Abyss Katana\". Every victory makes it sharper, and every strike takes a little of you.\n\nHe buried it in the \"Dark Sword Shrine\" beneath guards who never sleep and said: \"Only one who can carry it without being carried by it may lift it.\" The Explorer's Compass knows the way.\n\nThe smith's apprentice could not sleep while only darkness guarded the world. From the last light of the fallen star she forged its opposite: \"the Oath of Light\", a silver sword that never dulls. It rests in the \"Light Sword Shrine\", beneath a beam that rises to the sky. Whoever holds both blades holds the balance of the world."],
  ["The Heart of the Abyss",
    "You are the \"Master\" now, and here is what the Trainer never said: the Abyss is not an enemy from outside. It is the rest of the fallen star, still searching for its heart, the crystal in the temples. Every Rift is it reaching out; every creature is its call.\n\nYou can close it forever, or return the heart and let the star rise again. Your choice will write the final chapter.\n\n§7(The final chapter arrives in a future update)"],
];
async function openLore(player) {
  const st = getState(player);
  const form = new ActionFormData().title(LORE_TITLE).body(`§7One chapter per rank. Your rank: §e${RANKS[st.rank]}§7 (${Math.min(LORE.length, st.rank + 1)}/${LORE.length} chapters unlocked)`);
  LORE.forEach((c, i) => form.button(i <= st.rank ? `§d${i + 1}. ${c[0]}` : `§8${i + 1}. §c[Locked] rank ${RANKS[i]}`));
  const r = await showForm(player, form);
  if (r.canceled) return;
  const i = r.selection;
  if (i > st.rank) { notify(player, `§7This chapter unlocks at rank ${RANKS[i]}`, 60); return; }
  await showForm(player, new ActionFormData().title(`${i + 1}. ${LORE[i][0]}`).body(LORE[i][1]).button("§aBack"));
  return openLore(player);
}
function introStory(player) {
  try {
    player.onScreenDisplay.setTitle("§l§9Anime Powers", { subtitle: `§7${LORE_TITLE}`, fadeInDuration: 20, stayDuration: 100, fadeOutDuration: 30 });
  } catch (e) { /* */ }
  sfxPlayer(player, "sh.orbit", 0.8, 0.8);
  say(player, `§9[Story] §f${LORE[0][1].split("\n")[0]}`);
  say(player, "§7Open the Evolution Book > [World Story] to read the other chapters; every new rank unlocks one.");
}

// ───────────────────────── كتاب الوحوش ─────────────────────────
const MONSTER_INFO = [
  ["sh:training_archer", "Training Archer", "Unranked", "It draws when you come close and recoils as it shoots a violet-trailed arrow. It weakens up close, and the Law of Silence stops it from shooting."],
  ["sh:ember_imp", "Ember Imp", "Lowly to Cataclysm", "Close: a red circle marks where it will pounce, then it rakes you with fiery claws. Far (7-13 blocks): it charges a fireball and lobs it; a red circle shows where it lands, so move!"],
  ["sh:rust_guard", "Rust Guard", "Lowly to Cataclysm", "A red circle grows around it before its ground slam, so step out. Up close it sweeps with crystal fists. Far (6-14 blocks): it tears out a boulder and throws it; dodge the red circle."],
  ["sh:shadow_hound", "Shadow Hound", "Lowly to Cataclysm", "It howls to slow you, bites twice up close, and from 4-10 blocks it melts into violet smoke and appears behind you to bite. Keep turning."],
  ["sh:sand_scorpion", "Sand Scorpion", "Lowly to Cataclysm", "Its tail spits a venom glob up close. From 5-12 blocks it burrows underground; a red circle locks under you before it erupts, poisoning and launching you."],
];
async function openMonsterBook(player) {
  const st = getState(player);
  const kills = st.kills || {};
  let body = "§5Monster Book§r\n\n§fMonster ranks§7 (the tag above their heads; its color shows how dangerous they are for you: green easy, yellow fair, orange hard, red deadly):\n";
  MON_RANKS.forEach((r, i) => { body += `${r.col}${i + 1}. ${r.name}§7: ${r.desc}\n`; });
  body += "\n";
  for (const [id, name, rank, tip] of MONSTER_INFO) {
    const k = kills[id] || 0;
    body += `§e${name} §7(${rank}) §fKilled: §b${k}\n§7${k > 0 || id === "sh:training_archer" ? tip : "Kill one to reveal its info."}\n\n`;
  }
  await showForm(player, new ActionFormData().title("Monster Book").body(body).button("§aOK"));
}

// ───────────────────────── نافذة الحالة ─────────────────────────
// ملخص كامل: الرتبة والليفل والقدرة وكل مهارة (مستواها، حالتها، طريقة استعمالها) وتطور الكاتانا.
async function showStatus(player) {
  const st = getState(player);
  const pw = POWERS[st.power];
  let b = `§6◆ ${RANKS[st.rank]}§r  §bLv ${st.level}§r  §7(${st.xp}/${xpNeeded(st.level)} XP)\n${nextRankLine(st)}\n`;
  if (pw) {
    const r = rarityOf(st.power);
    b += `\n${pw.color}${pw.name}§r ${rarityStars(st.power)}§r ${r.color}${r.name}§r\n§dPower level ${st.plevel || 1}/${r.maxLv}§r ${(st.plevel || 1) >= r.maxLv ? "§6(MAX)" : `§7(${st.pxp || 0}/${powerXpNeeded(st.plevel || 1)})`}\n`;
    const tr = st.training && st.training[st.power];
    if (!tr || tr.status !== "done") b += "§e⚠ Finish the Trainer's training to unlock the other skills\n";
    b += "\n§eSkills:§r\n";
    Object.values(SKILLS).filter((s) => s.power === st.power).forEach((s, i) => {
      if (isSkillUnlocked(st, s)) {
        const lv = skillLevel(st, s.id), x = (st.skills[s.id] && st.skills[s.id].xp) || 0;
        b += `§a${i + 1}. ${s.name}§r §bLevel ${lv}§7 ${skillProg(lv, x)}\n§7   ${usageOf(s)}\n`;
      } else {
        b += `§8${i + 1}. ${s.name} §c(unlocks at power level ${s.unlock}${tr && tr.status === "done" ? "" : " + training"})\n`;
      }
    });
  } else b += st.powerless ? "\n§8Unbound§7: no power. Your body grows stronger and faster with each rank.\n" : "\n§7You have no power yet. Step on the crystal in the Star Temple.\n";
  b += `\n§fPerfect Guard§7: ${st.rank >= GUARD_RANK ? `press sneak right as a monster's hit lands: no damage, the monster is stunned, and your next hit is a Counter. Guards so far: ${st.guards || 0}` : `§cunlocks at rank ${RANKS[GUARD_RANK]}`}\n`;
  b += `\n${riftStatusText(player)}\n§fRhythm Strike§7: ${st.rank >= RHY_RANK ? `hit enemies in a steady beat, like a drum. Your first two hits set the beat; keep hitting on it and each hit plays a rising note. 4th hit in rhythm = Rhythm, 7th = Crescendo, 10th = Finale. Best: ${st.rhyBest || 0}` : `§cunlocks at rank ${RANKS[RHY_RANK]}`}\n`;
  {
    const all = wlvAll(player), ids = Object.keys(WEAPON_SKILLS).filter((id) => all[id] || hasItem(player, id));
    if (ids.length) {
      b += "\n§e⚔ Weapon levels§r §7(grow by hitting and killing with each weapon)\n";
      for (const id of ids) {
        const k = getWlv(player, id);
        b += `§f${WEAPONS[id] ? WEAPONS[id].name : id}§r §6Lv ${k.lv}/${WLV_MAX}${k.lv >= WLV_MAX ? " §6(AWAKENED)" : ` §7(${k.xp}/${WLV_NEED[k.lv]} XP) next: ${WLV_PERKS[k.lv + 1]}`}\n`;
      }
    }
  }
  if (hasItem(player, KATANA) || player.getDynamicProperty("sh_kat")) {
    const k = getKat(player);
    b += `\n§5⚔ Abyss Katana§r §dLv ${k.lv}/${KAT_MAX}§r ${k.lv >= KAT_MAX ? "§6(MAX)" : `§7(${k.xp}/${KAT_NEED[k.lv]} XP, grows by killing enemies while holding it)`}\n`;
    b += `§d1. ${KATANA_SKILLS[0].name}§r §7(use): ${KATANA_SKILLS[0].desc}\n§d2. ${KATANA_SKILLS[1].name}§r §7(sneak + use): ${KATANA_SKILLS[1].desc}\n`;
    for (let i = 2; i <= KAT_MAX; i++) b += `${i <= k.lv ? "§a✔" : "§8✖"} Lv${i}: ${KAT_PERKS[i]}\n`;
  }
  await showForm(player, new ActionFormData().title("Status Window").body(b).button("§aOK"));
}

function skillProg(lv, xp) { return lv >= SKILL_MAX_LV ? "§6(MAX)" : `(${xp || 0}/${skillXpNeeded(lv)})`; }
async function openBook(player) {
  const st = getState(player);
  if (!st.power) return openPowerMenu(player);
  const pw = POWERS[st.power];
  const mine = Object.values(SKILLS).filter((s) => s.power === st.power);

  const form = new ActionFormData()
    .title("Evolution Book")
    .body(
      `${pw.color}${pw.name} ${rarityOf(st.power).color}[${rarityOf(st.power).name}]§r\nPower level: §d${st.plevel || 1}/${rarityOf(st.power).maxLv}§r ${(st.plevel || 1) >= rarityOf(st.power).maxLv ? "§6(MAX)" : `§7(XP ${st.pxp || 0}/${powerXpNeeded(st.plevel || 1)})`}§r\nRank: §e${RANKS[st.rank]}§r\nLevel: §b${st.level}§r\nXP: §a${st.xp}/${xpNeeded(st.level)}§r\n${nextRankLine(st)}\n\n§7Pick a skill to receive it. Your power grows with every kill, every skill hit and with your level.`
    );
  for (const s of mine) {
    if (isSkillUnlocked(st, s)) {
      const lv = skillLevel(st, s.id);
      const sk = st.skills[s.id] || { xp: 0 };
      form.button(`§a${s.name} §bLevel ${lv} §7${skillProg(lv, sk.xp)} §e${AIMED.has(s.id) ? "[Aimed]" : "[Around you]"}\n§7${usageOf(s)}`);
    }
    else {
      const tr = st.training[st.power];
      const need = !tr || tr.status !== "done" ? "Finish the Trainer's training" : `Unlocks at power level ${s.unlock}`;
      form.button(`§8${s.name}\n§c${need}`);
    }
  }
  form.button("§e[Ranks and how to rise]");
  form.button("§b[Status window and how to use skills]");
  form.button("§d[World Story]");
  const r = await showForm(player, form);
  if (r.canceled) return;
  if (r.selection === mine.length) { showRanks(player); return; }
  if (r.selection === mine.length + 1) { showStatus(player); return; }
  if (r.selection === mine.length + 2) { openLore(player); return; }
  const s = mine[r.selection];
  if (!s) return;
  if (!isSkillUnlocked(st, s)) { notify(player, `§c${s.name}: still locked`, 60); return; }
  const c = inv(player);
  let has = false;
  for (let i = 0; i < c.size; i++) { const it = c.getItem(i); if (it && it.typeId === s.item) { has = true; break; } }
  if (has) { notify(player, `§e${s.name} is already in your inventory`, 50); return; }
  giveItem(player, s.item);
  sfxPlayer(player, "sh.select", 0.7, 1.3);
  notify(player, `§aYou received: ${s.name}`, 60);
  say(player, `§e[${s.name}] §f${s.desc}\n§7How to use: ${usageOf(s)}. You can take several skills and spread them across the hotbar.`);
}

// ───────────────────────── المدرب ─────────────────────────
const talkCd = new Map();

function describeDir(player, trainer) {
  const dx = trainer.location.x - player.location.x;
  const dz = trainer.location.z - player.location.z;
  const dist = Math.round(Math.hypot(dx, dz));
  let dir;
  if (Math.abs(dx) > Math.abs(dz) * 2) dir = dx > 0 ? "east" : "west";
  else if (Math.abs(dz) > Math.abs(dx) * 2) dir = dz > 0 ? "south" : "north";
  else dir = (dz > 0 ? "south" : "north") + (dx > 0 ? "-east" : "-west");
  return `The Trainer appeared ${dist} blocks away, to the ${dir}.`;
}

function spawnOnSurface(dim, id, cx, cz, tries = 12, minD = 24, maxD = 40) {
  for (let i = 0; i < tries; i++) {
    const a = Math.random() * Math.PI * 2;
    const d = minD + Math.random() * (maxD - minD);
    const x = Math.floor(cx + Math.cos(a) * d);
    const z = Math.floor(cz + Math.sin(a) * d);
    try {
      const top = dim.getTopmostBlock({ x, z });
      if (!top) continue;
      if (/water|lava|leaves|log|ice|cactus|fire|powder_snow|vine/.test(top.typeId)) continue;
      const above = top.above(1);
      if (!above || !above.isAir) continue;
      return dim.spawnEntity(id, { x: top.x + 0.5, y: top.y + 1, z: top.z + 0.5 });
    } catch (e) { /* جرب مكان ثاني */ }
  }
  return undefined;
}

function ensureTrainerNear(player, force) {
  if (player.dimension.id !== "minecraft:overworld") return undefined;
  const dim = player.dimension;
  const found = dim.getEntities({ type: "sh:trainer", location: player.location, maxDistance: 160 });
  if (found.length > 0) return force ? found[0] : undefined;
  if (!force && Math.random() > 0.5) return undefined;
  const t = spawnOnSurface(dim, "sh:trainer", player.location.x, player.location.z);
  if (t) t.nameTag = "§6Trainer";
  return t;
}

system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      const st = getState(p);
      if (st.power) ensureTrainerNear(p, false);
    } catch (e) { /* */ }
  }
}, 600);

function spawnTrainingMonsters(player, n) {
  const dim = player.dimension;
  let made = 0;
  for (let i = 0; i < n; i++) {
    const e = spawnOnSurface(dim, "sh:training_archer", player.location.x, player.location.z, 10, 8, 14);
    if (e) made++;
  }
  return made;
}

async function trainerTalk(player) {
  const st = getState(player);
  sfxPlayer(player, "sh.talk");
  if (!st.power) {
    notify(player, st.powerless ? "§7You are Unbound: I have no power to train. Fight on." : "§7Go to the Star Temple and step on its crystal first", 80);
    if (st.powerless) return;
    return openPowerMenu(player);
  }
  const pw = POWERS[st.power];
  const tr = st.training[st.power] || { status: "none", kills: 0 };

  if (tr.status === "none") {
    const f = new ActionFormData()
      .title("Trainer")
      .body(`§eWelcome, ${pw.color}${pw.name}§e.\n\n§fYour training is to defeat §e${TRAIN_NEED}§f basic unranked monsters. Each gives 20 to 50 experience.\n\n§7Do you accept the mission?`)
      .button("§aAccept")
      .button("§7Later");
    const r = await showForm(player, f);
    if (r.canceled || r.selection !== 0) return;
    const s2 = getState(player);
    s2.training[s2.power] = { status: "active", kills: 0 };
    const giveMB = !s2.gotMonsterBook;
    s2.gotMonsterBook = true;
    saveState(player, s2);
    if (giveMB) { giveItem(player, "sh:monster_book"); say(player, "§5[Trainer] §fTake the Monster Book. It teaches you their weaknesses, and every kind you kill reveals more info."); }
    const made = spawnTrainingMonsters(player, TRAIN_NEED);
    say(player, `§6[Mission] §fDefeat ${TRAIN_NEED} training monsters (0/${TRAIN_NEED})`);
    notify(player, `§eMission started: defeat ${TRAIN_NEED} monsters (${made} appeared)`, 100);
    return;
  }

  if (tr.status === "active") {
    if (tr.kills < TRAIN_NEED) {
      const f = new ActionFormData()
        .title("Trainer")
        .body(`Your progress: §e${tr.kills}/${TRAIN_NEED}§r\nKeep defeating training monsters.`)
        .button("§bSummon monsters again")
        .button("§7Back");
      const r = await showForm(player, f);
      if (r.canceled || r.selection !== 0) return;
      const made = spawnTrainingMonsters(player, TRAIN_NEED - tr.kills);
      notify(player, `§e${made} monsters appeared near you`, 80);
      return;
    }
    // خلص التدريب
    const s2 = getState(player);
    s2.training[s2.power] = { status: "done", kills: tr.kills };
    const ups = addXp(s2, 15);
    // أول تدريب لكل قدرة: 3 لفائف تطور مهارة هدية من المدرب
    if (!s2.scrollGiven) s2.scrollGiven = {};
    const reward = s2.scrollGiven[s2.power] ? 0 : 3;
    s2.scrollGiven[s2.power] = true;
    saveState(player, s2);
    if (reward) { giveItem(player, "sh:skill_scroll", reward); say(player, `§b[Trainer] §fTake ${reward} Skill Upgrade Scrolls. Use one while holding it and pick the skill to level up.`); }
    if (!hasItem(player, "sh:evolution_book")) giveItem(player, "sh:evolution_book");
    sfxPlayer(player, "sh.mission");
    say(player, `§e[Trainer] §fWell done! You learned the basics of ${pw.color}${pw.name}§f. Open the Evolution Book and choose your skill.`);
    announceUps(player, ups);
    return;
  }

  // done
  const nextSkill = Object.values(SKILLS).find((s) => s.power === st.power && !isSkillUnlocked(st, s));
  const f = new ActionFormData()
    .title("Trainer")
    .body(
      nextSkill
        ? `Your basics are done.\nNext skill: §e${nextSkill.name}§r. It unlocks when your power reaches level §b${nextSkill.unlock}§r (now ${st.plevel || 1}). Grow it by killing enemies while using your skills.`
        : "Your basics are done. Discover the other skills as you grow."
    )
    .button("§bSummon training monsters")
    .button("§7Back");
  const r = await showForm(player, f);
  if (r.canceled || r.selection !== 0) return;
  const made = spawnTrainingMonsters(player, 3);
  notify(player, `§e${made} monsters appeared near you`, 80);
}

world.afterEvents.playerInteractWithEntity.subscribe((ev) => {
  try {
    if (ev.target.typeId !== "sh:trainer") return;
    const p = ev.player;
    const last = talkCd.get(p.id) ?? -100;
    if (system.currentTick - last < 10) return;
    talkCd.set(p.id, system.currentTick);
    trainerTalk(p);
  } catch (e) { /* */ }
});

// ───────────────────────── الضرر والقتل والترقي ─────────────────────────
function announceUps(player, ups) {
  for (const u of ups) {
    if (u.type === "level") {
      sfxPlayer(player, "sh.level_up");
      say(player, `§b[Level] §fYou reached level §b${u.level}`);
    } else if (u.type === "plevel") {
      sfxPlayer(player, "sh.level_up", 1, 0.8);
      burst(player.dimension, headPos(player), 24, COLORS.purple, 3, 0.22);
      const stx = getState(player);
      say(player, `§d[Power] §fYour power reached level §d${u.level}`);
      for (const sk of Object.values(SKILLS)) {
        if (sk.power === stx.power && !sk.first && sk.unlock === u.level) say(player, `§a[New skill] §f${sk.name} unlocked${(stx.training[stx.power] || {}).status === "done" ? " - open the Evolution Book." : " (needs the Trainer's training)."}`);
      }
    } else if (u.type === "skill") {
      sfxPlayer(player, "sh.level_up", 0.8, 1.3);
      const sk = SKILLS[u.id];
      say(player, `§d[Skill] §f${sk.name} reached level §d${u.level}`);

    } else if (u.type === "rank") {
      sfxPlayer(player, "sh.rank_up");
      burst(player.dimension, headPos(player), 30, COLORS.gold, 3.5, 0.25);
      notify(player, `§6You reached rank ${RANKS[u.rank]}! §c+4 health`, 100);
      applyVitality(player, true);
      if (LORE[u.rank]) say(player, `§d[Story] A new chapter unlocked: "${LORE[u.rank][0]}". Open the Evolution Book > [World Story]`);
      waveFx(player.dimension, player.location, 6, 0, 14);
      say(player, `§6[Rank] §fYour rank is now §e${RANKS[u.rank]}`);
      try { if (needsDraw(getState(player))) later(60, () => ensureTemple(player)); } catch (e) { /* */ }
      if (u.rank === GUARD_RANK) later(120, () => { say(player, "§f§l[Perfect Guard unlocked]§r §7Press §fsneak§7 at the very moment a monster's hit reaches you (watch its wind-up and the red circles). The hit is cancelled, the monster is stunned, and your next hit is a strong §6Counter§7. Pressing sneak over and over does not work: time it."); sfxPlayer(player, "sh.reflect", 0.8, 1.3); });
      if (u.rank === RHY_RANK) later(100, () => { say(player, "§b§l[Rhythm Strike unlocked]§r §7No item needed. Hit enemies in a steady beat, like playing a drum: your first two hits set the beat. Keep hitting on that beat and every hit plays a higher note; a soft tick tells you when the next hit is due. §fthe 4th hit in rhythm = Rhythm§7 (area hit), §dthe 7th = Crescendo§7, §6the 10th = Finale§7 (huge blast). Hitting off beat or stopping resets it. Practice: /scriptevent sh:rhythm"); sfxPlayer(player, "note.pling", 0.8, 1); later(5, () => sfxPlayer(player, "note.pling", 0.8, 1.26)); later(10, () => sfxPlayer(player, "note.pling", 0.8, 1.5)); });
    }
  }
}

// صحة اللاعب تزيد مع الرتبة (+4 لكل رتبة) عبر health_boost يتجدد كل 5 ثواني
function applyVitality(p, fill) {
  try {
    const st = getState(p);
    if (st.powerless) {
      p.addEffect("strength", 140, { amplifier: st.rank >= 5 ? 2 : st.rank >= 2 ? 1 : 0, showParticles: false });
      p.addEffect("speed", 140, { amplifier: st.rank >= 3 ? 1 : 0, showParticles: false });
      if (st.rank >= 4) p.addEffect("resistance", 140, { amplifier: 0, showParticles: false });
    }
    const bonus = rankHealthBonus(st.rank);
    if (bonus <= 0) { try { p.removeEffect("health_boost"); } catch (e) { /* */ } return; }
    p.addEffect("health_boost", 600, { amplifier: Math.max(0, bonus / 4 - 1), showParticles: false });
    if (fill) later(4, () => { try { const h = p.getComponent("minecraft:health"); h.resetToMaxValue(); } catch (e) { /* */ } });
  } catch (e) { /* */ }
}
system.runInterval(() => { for (const p of world.getAllPlayers()) applyVitality(p, false); }, 100);

const lastSkillUse = new Map();
const SKILL_XP_WINDOW = 200; // 10 ثواني بعد استعمال المهارة
function grantSkillXp(player, amount) {
  const u = lastSkillUse.get(player.id);
  if (!u || system.currentTick - u.tick > SKILL_XP_WINDOW) return;
  const st = getState(player);
  if (!st.power || !SKILLS[u.id] || !isSkillUnlocked(st, SKILLS[u.id])) return;
  const ups = addSkillXp(st, u.id, amount);
  ups.push(...addPowerXp(st, amount, rarityOf(st.power).maxLv));
  saveState(player, st);
  announceUps(player, ups);
}

function handleKill(player, info) {
  const st = getState(player);
  if (info.training && st.power) {
    const tr = st.training[st.power];
    if (tr && tr.status === "active") {
      tr.kills++;
      notify(player, tr.kills >= TRAIN_NEED ? "§aDone! Return to the Trainer" : `§eTraining ${tr.kills}/${TRAIN_NEED}`, 70);
    }
  }
  const res = monsterReward(st, info);
  if (st.power) res.ups.push(...addPowerXp(st, res.xp, rarityOf(st.power).maxLv));
  saveState(player, st);
  announceUps(player, res.ups);
  grantSkillXp(player, res.xp);
}

world.afterEvents.entityDie.subscribe((ev) => {
  try {
    const info = MONSTERS[ev.deadEntity.typeId];
    const killer = ev.damageSource && ev.damageSource.damagingEntity;
    if (!killer || killer.typeId !== "minecraft:player") return;
    try {
      const held = inv(killer).getItem(killer.selectedSlotIndex);
      const kx = info ? (Array.isArray(info.xp) ? info.xp[0] : info.xp) : 2;
      if (held && held.typeId === KATANA) addKatXp(killer, kx);
      else if (held && WEAPON_SKILLS[held.typeId]) addWeaponXp(killer, held.typeId, kx);
    } catch (e0) { /* */ }
    if (!info) {
      // الوحوش العادية: 1 XP لكل قتلة
      if (ev.deadEntity.typeId === "minecraft:player" || ev.deadEntity.typeId.startsWith("sh:")) return;
      const fam = ev.deadEntity.getComponent("minecraft:type_family");
      if (!fam) return;
      // الغولم الحديدي 12، الوحوش 5، باقي الموبز 2
      const amount = fam.hasTypeFamily("irongolem") ? 12 : fam.hasTypeFamily("monster") ? 5 : fam.hasTypeFamily("mob") ? 2 : 0;
      if (!amount) return;
      const st = getState(killer);
      const ups = addXp(st, amount);
      saveState(killer, st);
      announceUps(killer, ups);
      grantSkillXp(killer, amount);
      return;
    }
    let kinfo = info;
    try {
      const tier = tierOf(ev.deadEntity);
      if (tier > 0 && info.rank >= 0 && !Array.isArray(info.xp)) kinfo = { ...info, rank: effRank(info, tier), xp: Math.round(info.xp * (1 + TIER_XP * tier)) };
    } catch (e4) { /* */ }
    handleKill(killer, kinfo);
    try {
      const sk = getState(killer);
      sk.kills = sk.kills || {};
      sk.kills[ev.deadEntity.typeId] = (sk.kills[ev.deadEntity.typeId] || 0) + 1;
      saveState(killer, sk);
    } catch (e3) { /* */ }
    // الوحوش تسقط لفائف خبرة أحيانا
    try {
      const t = ev.deadEntity.typeId;
      const roll = Math.random();
      const drop = t === "sh:rust_guard" ? (roll < 0.4 ? "sh:xp_scroll_small" : roll < 0.5 ? "sh:xp_scroll_big" : null)
        : t === "sh:ember_imp" ? (roll < 0.3 ? "sh:xp_scroll_small" : null)
        : t === "sh:shadow_hound" ? (roll < 0.3 ? "sh:xp_scroll_small" : null)
        : t === "sh:sand_scorpion" ? (roll < 0.35 ? "sh:xp_scroll_small" : roll < 0.42 ? "sh:xp_scroll_big" : null)
        : t === "sh:training_archer" ? (roll < 0.25 ? "sh:xp_scroll_small" : null) : null;
      if (drop) ev.deadEntity.dimension.spawnItem(new ItemStack(drop, 1), ev.deadEntity.location);
    } catch (e2) { /* */ }
  } catch (e) { /* */ }
});

// ───────────────────────── المحاسب: الأرقام ─────────────────────────
function numColor(n) { return n > 5 ? "§6" : n > 2 ? "§c" : "§4"; }

// الرقم يطلع فوق راس العدو كأرقام ذهبية 3D تواجه أقرب لاعب (إذا ما قدرنا نطلعها، يطلع كاسم)
const numShapes = new Map(); // id -> { e, ents, n }
function setNum(e, n) {
  e.setDynamicProperty("sh_num", n);
  const old = numShapes.get(e.id);
  if (old) old.ents.forEach(removeFx);
  const ents = [];
  for (const ch of String(Math.max(0, Math.min(99, n)))) {
    const x = shapeFx(e.dimension, `digit_${ch}`, { ...headPos(e), y: headPos(e).y + 0.9 }, { r: 0.85, life: 1200 });
    if (x) ents.push(x);
  }
  numShapes.set(e.id, { e, ents, n });
  try { e.nameTag = ents.length ? "" : `${numColor(n)}⟦${n}⟧`; } catch (err) { /* */ }
}
function clearNum(e) {
  try { e.setDynamicProperty("sh_num", undefined); e.nameTag = ""; } catch (err) { /* */ }
  const o = numShapes.get(e.id);
  if (o) { o.ents.forEach(removeFx); numShapes.delete(e.id); }
}
system.runInterval(() => {
  for (const [id, o] of [...numShapes]) {
    try {
      if (!valid(o.e) || typeof o.e.getDynamicProperty("sh_num") !== "number") { o.ents.forEach(removeFx); numShapes.delete(id); continue; }
      const h = headPos(o.e), c = { x: h.x, y: h.y + 0.9, z: h.z };
      let pl, bd = 1e9;
      for (const q of world.getAllPlayers()) { if (q.dimension.id !== o.e.dimension.id) continue; const d = dist2d(q.location, c); if (d < bd) { bd = d; pl = q; } }
      let f = { x: 0, y: 0, z: 1 };
      if (pl) { const dx = pl.location.x - c.x, dz = pl.location.z - c.z, l = Math.hypot(dx, dz) || 1; f = { x: dx / l, y: 0, z: dz / l }; }
      const yaw = dirYaw(f), right = { x: f.z, z: -f.x };
      const n = o.ents.length;
      o.ents.forEach((x, i) => { const off = (i - (n - 1) / 2) * 0.78; moveShape(x, { x: c.x + right.x * off, y: c.y + Math.sin(system.currentTick * 0.15) * 0.06, z: c.z + right.z * off }, yaw); });
    } catch (err) { numShapes.delete(id); }
  }
}, 2);
// شكل رمز (ناقص، قسمة، سهم) يطير من اللاعب للهدف
function symbolShot(p, t, name, onHit, speed = 1.1) {
  const from = { x: p.location.x, y: p.location.y + 1.3, z: p.location.z }, to = headPos(t);
  const dx = to.x - from.x, dy = to.y - from.y, dz = to.z - from.z, l = Math.hypot(dx, dy, dz) || 1;
  const d = { x: dx / l, y: dy / l, z: dz / l };
  flyShape(p.dimension, name, { x: from.x + d.x, y: from.y + d.y, z: from.z + d.z }, d, speed, Math.max(1.5, l - 1), { r: 1.0, w: name.startsWith("arrow") ? 0 : 360 },
    undefined, () => { try { onHit && onHit(); } catch (err) { /* */ } });
}

function collapse(e, p) {
  const dim = e.dimension;
  const loc = headPos(e);
  clearNum(e);
  sfx(dim, "sh.collapse", loc, 1.2);
  fling(dim, ["digit_0", "digit_1", "digit_7", "digit_9", "digit_3"], loc, 6, 1.2, 0.35, 0.6);
  popShape(dim, "digit_0", { x: loc.x, y: loc.y + 0.3, z: loc.z }, 0.6, 2.2, 8, { s: 500 });
  burst(dim, loc, 16, COLORS.red, 4, 0.25);
  ring(dim, { x: e.location.x, y: e.location.y, z: e.location.z }, 1.4, 20, 0, COLORS.orange, 0.22);
  try { e.applyDamage(10, { cause: EntityDamageCause.entityAttack, damagingEntity: p }); } catch (err) { /* */ }
}

// عداد حقيقي: كل ثانيتين ينقص الرقم 1 لحاله، وإذا وصل صفر ينهار العدو
const numOwners = new Map();
system.runInterval(() => {
  for (const [id, o] of [...numOwners.entries()]) {
    try {
      const e = o.e;
      if (!valid(e)) { numOwners.delete(id); continue; }
      const n = e.getDynamicProperty("sh_num");
      if (typeof n !== "number") { numOwners.delete(id); continue; }
      const pl = world.getAllPlayers().find((x) => x.id === o.pid);
      if (!pl) { numOwners.delete(id); continue; }
      sfx(e.dimension, "sh.tick", e.location, 0.5, 1 + (10 - n) * 0.05);
      decNum(e, 1, pl);
    } catch (err) { numOwners.delete(id); }
  }
}, 40);

function decNum(e, amount, p) {
  const n = e.getDynamicProperty("sh_num");
  if (typeof n !== "number") return;
  const left = Math.max(0, n - amount);
  if (left === 0) { collapse(e, p); return; }
  setNum(e, left);
  glow(e.dimension, headPos(e), { color: COLORS.orange, size: 0.3, life: 0.5, rise: 1 });
}

world.afterEvents.entityHurt.subscribe((ev) => {
  try {
    const e = ev.hurtEntity;
    if (e.typeId === "sh:trainer") {
      const h = e.getComponent("minecraft:health");
      if (h) h.resetToMaxValue();
      return;
    }
    const n = e.getDynamicProperty("sh_num");
    if (typeof n !== "number" || n <= 0) return;
    const attacker = ev.damageSource && ev.damageSource.damagingEntity;
    if (!attacker || attacker.typeId !== "minecraft:player") return;
    sfx(e.dimension, "sh.tick", e.location, 0.8, 1 + (10 - n) * 0.05);
    decNum(e, 1, attacker);
  } catch (err) { /* */ }
});

function raycastTarget(p, dist = 24) {
  let hits = [];
  try { hits = p.getEntitiesFromViewDirection({ maxDistance: dist }); } catch (e) { return undefined; }
  hits.sort((a, b) => a.distance - b.distance);
  for (const h of hits) {
    const e = h.entity;
    if (e.id === p.id || e.typeId === "sh:trainer" || isFriendly(e)) continue;
    let hp;
    try { hp = e.getComponent("minecraft:health"); } catch (err) { continue; }
    if (!hp) continue;
    return e;
  }
  return undefined;
}

// ───────────────────────── أدوات الأعداء ─────────────────────────
// الأصدقاء اللي ما نأذيهم: قرويين، غولم، تاجر متجول، حيوانات أليفة (مروضة)، أو أي كيان بوسم sh_ignore
function isFriendly(e) {
  try {
    if (e.hasTag("sh_ignore")) return true;
    if (e.getComponent("minecraft:is_tamed")) return true;
    const fam = e.getComponent("minecraft:type_family");
    if (fam && (fam.hasTypeFamily("villager") || fam.hasTypeFamily("irongolem") || fam.hasTypeFamily("wandering_trader") || fam.hasTypeFamily("npc"))) return true;
  } catch (err) { /* */ }
  return false;
}
function enemiesNear(dim, center, r, excludeId) {
  let list = [];
  try {
    list = dim.getEntities({
      location: center, maxDistance: r,
      excludeTypes: ["minecraft:player", "sh:trainer", "minecraft:villager_v2", "minecraft:villager", "minecraft:iron_golem", "minecraft:wandering_trader", "minecraft:npc", "minecraft:armor_stand"],
      excludeFamilies: ["inanimate"],
    });
  } catch (e) { return []; }
  return list.filter((e) => {
    if (e.id === excludeId) return false;
    try { return !!e.getComponent("minecraft:health") && !isFriendly(e); } catch (err) { return false; }
  });
}
function nearestEnemy(e, r) {
  let best, bd = 1e9;
  for (const o of enemiesNear(e.dimension, e.location, r, e.id)) {
    const d = Math.hypot(o.location.x - e.location.x, o.location.z - e.location.z);
    if (d < bd) { bd = d; best = o; }
  }
  return best;
}
function dist2d(a, b) { return Math.hypot(a.x - b.x, a.z - b.z); }
// ضرر المهارة يكبر مع: مستوى المهارة (+4% لكل مستوى)، ليفل القدرة (+3%)، الرتبة (+1%)، أقصى 1.8x
const dmgMulCache = new Map();
function skillDmgMul(by) {
  if (!by || by.typeId !== "minecraft:player") return 1;
  const now = system.currentTick;
  const u = lastSkillUse.get(by.id);
  if (!u || now - u.tick > 200) return 1;
  const c = dmgMulCache.get(by.id);
  if (c && c.tick === now) return c.mul;
  let mul = 1;
  try {
    const s = getState(by);
    mul = Math.min(1.8, 1 + 0.04 * (skillLevel(s, u.id) - 1) + 0.03 * ((s.plevel || 1) - 1) + 0.01 * s.rank);
  } catch (err) { /* */ }
  dmgMulCache.set(by.id, { tick: now, mul });
  return mul;
}
// كل ضربة مهارة تصيب عدو تعطي خبرة صغيرة للمهارة وللقدرة (مرة كل نص ثانية) حتى التطور يمشي وانت تقاتل
const hitXpAt = new Map();
function skillHitXp(by, target) {
  try {
    if (!by || by.typeId !== "minecraft:player" || !target || target.typeId === "minecraft:player" || isFriendly(target)) return;
    const u = lastSkillUse.get(by.id), now = system.currentTick;
    if (!u || now - u.tick > 120 || now - (hitXpAt.get(by.id) ?? -99) < 10) return;
    hitXpAt.set(by.id, now);
    const st = getState(by);
    if (!st.power || !SKILLS[u.id] || SKILLS[u.id].power !== st.power) return;
    const ups = addSkillXp(st, u.id, 2);
    ups.push(...addPowerXp(st, 2, rarityOf(st.power).maxLv));
    saveState(by, st);
    if (ups.length) announceUps(by, ups);
  } catch (err) { /* */ }
}
function hurt(e, amount, by) {
  try { e.applyDamage(amount * skillDmgMul(by) * weaponSkillMul(by), { cause: EntityDamageCause.entityAttack, damagingEntity: by }); skillHitXp(by, e); } catch (err) { /* */ }
}
function viewDir(p) {
  try { return p.getViewDirection(); } catch (e) { return { x: 0, y: 0, z: 1 }; }
}
function flatDir(p) {
  const v = viewDir(p);
  const l = Math.hypot(v.x, v.z) || 1;
  return { x: v.x / l, z: v.z / l };
}
function pushAway(from, e, force, up) {
  const dx = e.location.x - from.x, dz = e.location.z - from.z;
  const l = Math.hypot(dx, dz) || 1;
  try { e.applyKnockback({ x: (dx / l) * force, z: (dz / l) * force }, up); } catch (err) { /* */ }
}
function safeTeleport(e, loc, facing) {
  try {
    const dim = e.dimension;
    const b1 = dim.getBlock({ x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) });
    const b2 = dim.getBlock({ x: Math.floor(loc.x), y: Math.floor(loc.y) + 1, z: Math.floor(loc.z) });
    if (!b1 || !b2 || !b1.isAir || !b2.isAir) return false;
    e.teleport(loc, facing ? { facingLocation: facing } : undefined);
    return true;
  } catch (err) { return false; }
}

// ───────────────────────── مؤثرات بصرية حقيقية (كيانات) ─────────────────────────
// ألوان: 0 ذهبي، 1 بنفسجي، 2 أزرق، 3 تركواز، 4 أبيض، 5 أحمر
function spawnFx(dim, kind, loc, c, r, life, yaw) {
  try {
    const e = dim.spawnEntity(`sh:fx_${kind}`, { x: loc.x, y: loc.y + 0.05, z: loc.z });
    e.setProperty("sh:c", c);
    e.setProperty("sh:r", r);
    if (yaw !== undefined) { try { e.setRotation({ x: 0, y: yaw }); } catch (err) { /* */ } }
    if (life) system.runTimeout(() => { try { if (valid(e)) e.remove(); } catch (err) { /* */ } }, life);
    return e;
  } catch (err) { return undefined; }
}
function removeFx(e) { try { if (e && valid(e)) e.remove(); } catch (err) { /* */ } }
function yawOf(from, to) { return (Math.atan2(-(to.x - from.x), to.z - from.z) * 180) / Math.PI; }
// دائرة تتوسع (موجة صدى)
function waveFx(dim, c, rmax, color, dur = 14) {
  const e = spawnFx(dim, "circle", c, color, 1, dur + 4);
  if (!e) return;
  let t = 0;
  const h = system.runInterval(() => {
    try {
      t += 2;
      if (!valid(e) || t >= dur) { system.clearRun(h); removeFx(e); return; }
      e.setProperty("sh:r", 1 + (rmax - 1) * (t / dur));
    } catch (err) { system.clearRun(h); }
  }, 2);
}
// قشرة الجسم المتحولة: كيان sh:fx_body يلبس اللاعب (حديد variant=0، حجر variant=1) ويتبعه بحركة أطراف وميل راس.
// تظهر بنبضة تكبير، وتطلع شرارات كل ما اللاعب ينضرب. تنتهي بعد ticks.
const bodyShells = new Map();
function hpNow(e) { try { return e.getComponent("minecraft:health").currentValue; } catch (err) { return 0; } }
function bodyShell(p, variant, ticks) {
  try {
    const old = bodyShells.get(p.id);
    if (old) { removeFx(old.e); system.clearRun(old.h); bodyShells.delete(p.id); }
    const dim = p.dimension;
    const e = dim.spawnEntity("sh:fx_body", p.location);
    e.setProperty("sh:v", variant);
    e.setProperty("sh:r", 0.55);
    const spark = variant === 0 ? [0.85, 0.9, 1.0] : [0.6, 0.62, 0.55];
    // لحظة التحول: موجة + شرارات صاعدة بطول الجسم + وميض شاشة خفيف
    ring(dim, p.location, 1.0, 22, 0, spark, 0.22);
    waveFx(dim, p.location, 3, 4, 8);
    for (let i = 0; i < 40; i++) pix(dim, { x: p.location.x + (Math.random() - 0.5) * 1.2, y: p.location.y + Math.random() * 2, z: p.location.z + (Math.random() - 0.5) * 1.2 }, { color: spark, size: 0.14, life: 0.9, speed: 0.8, rise: 1.8 });
    try { p.camera.fade({ fadeColor: { red: spark[0], green: spark[1], blue: spark[2] }, fadeTime: { fadeInTime: 0.04, holdTime: 0.04, fadeOutTime: 0.25 } }); } catch (err) { /* */ }
    let t = 0, lastHp = hpNow(p);
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p) || !valid(e) || t > ticks) {
          system.clearRun(h); removeFx(e); bodyShells.delete(p.id);
          if (valid(p)) { burst(p.dimension, headPos(p), 18, spark, 2.5, 0.2); sfx(p.dimension, "sh.cleaver_hit", p.location, 0.6, 1.6); }
          return;
        }
        const rot = p.getRotation();
        e.teleport(p.location, { rotation: { x: 0, y: rot.y } });
        e.setProperty("sh:p", Math.max(-90, Math.min(90, rot.x)));
        const v = p.getVelocity();
        e.setProperty("sh:mv", Math.hypot(v.x, v.z) > 0.04 ? 1 : 0);
        e.setProperty("sh:r", Math.min(1, 0.55 + t * 0.045));
        const hp = hpNow(p);
        if (hp < lastHp - 0.4) { burst(p.dimension, { x: p.location.x, y: p.location.y + 1.1, z: p.location.z }, 14, spark, 3, 0.16); sfx(p.dimension, "sh.dagger_hit", p.location, 0.7, 1.9); }
        lastHp = hp;
      } catch (err) { system.clearRun(h); removeFx(e); bodyShells.delete(p.id); }
    }, 2);
    bodyShells.set(p.id, { e, h });
    return e;
  } catch (err) { return undefined; }
}
// علامة تتبع الهدف فوق راسه
function followFx(target, color, ticks, scale = 1) {
  const e = spawnFx(target.dimension, "plate", headPos(target), color, scale, ticks + 5);
  if (!e) return;
  let t = 0;
  const h = system.runInterval(() => {
    try {
      t += 4;
      if (!valid(e) || !valid(target) || t > ticks) { system.clearRun(h); removeFx(e); return; }
      const hp = headPos(target);
      e.teleport({ x: hp.x, y: hp.y + 0.7, z: hp.z });
    } catch (err) { system.clearRun(h); removeFx(e); }
  }, 4);
}
function portalFx(dim, loc, color, r, from, to, life = 24) {
  return spawnFx(dim, "portal", { x: loc.x, y: loc.y, z: loc.z }, color, r, life, from && to ? yawOf(from, to) : 0);
}

// ───────────────────────── أشكال المهارات 3D (كيان sh:fx_shape) ─────────────────────────
// كل شكل موديل مصنوع بـ tools/gen_fx_shapes.py (بلورات، قبضة، أجنحة، أرقام، ساعة، نيزك...).
// o: { r حجم، yaw، p ميل (سالب = الراس للأعلى)، a لفة، s دوران Y بالثانية، w لفة بالثانية، life مدة بالتكات }
// الحد يحسب الأشكال الحية فعلاً (الشكل اللي انشال قبل وقته يفرغ مكانه فوراً)
const SHAPE_CAP = 90;
const liveShapes = new Set();
function shapeFx(dim, name, loc, o = {}) {
  if (SHAPE[name] === undefined) return undefined;
  if (liveShapes.size >= SHAPE_CAP) { for (const x of liveShapes) if (!valid(x)) liveShapes.delete(x); }
  if (liveShapes.size >= SHAPE_CAP) return undefined;
  try {
    const e = dim.spawnEntity("sh:fx_shape", { x: loc.x, y: loc.y, z: loc.z });
    liveShapes.add(e);
    e.setProperty("sh:v", SHAPE[name]);
    if (o.r !== undefined) e.setProperty("sh:r", Math.max(0, Math.min(40, o.r)));
    if (o.p) e.setProperty("sh:p", Math.max(-180, Math.min(180, o.p)));
    if (o.a) e.setProperty("sh:a", o.a);
    if (o.s) e.setProperty("sh:s", o.s);
    if (o.w) e.setProperty("sh:w", o.w);
    if (o.yaw !== undefined) { try { e.setRotation({ x: 0, y: o.yaw }); } catch (err) { /* */ } }
    const life = o.life ?? 40;
    system.runTimeout(() => { liveShapes.delete(e); removeFx(e); }, Math.max(1, life));
    return e;
  } catch (err) { return undefined; }
}
function setShape(e, prop, v) { try { if (e && valid(e)) e.setProperty(prop, v); } catch (err) { /* */ } }
function moveShape(e, loc, yaw) {
  try { if (e && valid(e)) e.teleport(loc, yaw !== undefined ? { rotation: { x: 0, y: yaw } } : undefined); } catch (err) { /* */ }
}
// ميل واتجاه من متجه
function dirYaw(d) { return (Math.atan2(-d.x, d.z) * 180) / Math.PI; }
function dirPitch(d) { return (-Math.asin(Math.max(-1, Math.min(1, d.y))) * 180) / Math.PI; }
// حركة على مراحل: fn(k من 0 إلى 1، t) كل step تك، وبالنهاية done()
function tween(ticks, step, fn, done) {
  let t = 0;
  const h = system.runInterval(() => {
    try {
      t += step;
      fn(Math.min(1, t / ticks), t);
      if (t >= ticks) { system.clearRun(h); if (done) done(); }
    } catch (err) { system.clearRun(h); }
  }, step);
  return h;
}
// شكل يكبر ثم يختفي (انفجار/موجة)
function popShape(dim, name, loc, r0, r1, ticks, o = {}) {
  const e = shapeFx(dim, name, loc, { ...o, r: r0, life: ticks + 2 });
  if (!e) return undefined;
  tween(ticks, 1, (k) => setShape(e, "sh:r", r0 + (r1 - r0) * (o.ease === "out" ? 1 - (1 - k) * (1 - k) : k)));
  return e;
}
// شكل يطير بخط مستقيم (قذيفة): onStep(pos) يرجع true حتى يوقف
function flyShape(dim, name, from, d, speed, maxDist, o = {}, onStep, onEnd) {
  const yaw = dirYaw(d), pitch = dirPitch(d);
  const e = shapeFx(dim, name, from, { ...o, yaw, p: (o.p ?? 0) + pitch, life: Math.ceil(maxDist / speed) + 6 });
  let dist = 0;
  const pos = { ...from };
  const h = system.runInterval(() => {
    try {
      dist += speed;
      pos.x = from.x + d.x * dist; pos.y = from.y + d.y * dist; pos.z = from.z + d.z * dist;
      let blocked = false;
      try { const b = dim.getBlock({ x: Math.floor(pos.x), y: Math.floor(pos.y), z: Math.floor(pos.z) }); blocked = !!(b && !b.isAir && !b.isLiquid); } catch (err) { /* */ }
      const stop = blocked || dist >= maxDist || (onStep && onStep(pos, dist));
      moveShape(e, pos, yaw);
      if (stop) { system.clearRun(h); removeFx(e); if (onEnd) onEnd({ ...pos }, blocked); }
    } catch (err) { system.clearRun(h); removeFx(e); }
  }, 1);
  return e;
}
// شكل يلحق كيان (فوق راسه أو عند رجليه) لمدة معينة
function followShape(target, name, ticks, o = {}) {
  const off = o.dy ?? 0.8;
  const at = () => (o.feet ? { x: target.location.x, y: target.location.y + off, z: target.location.z } : { ...headPos(target), y: headPos(target).y + off });
  const e = shapeFx(target.dimension, name, at(), { ...o, life: ticks + 4 });
  if (!e) return undefined;
  let t = 0;
  const h = system.runInterval(() => {
    try {
      t += 2;
      if (!valid(e) || !valid(target) || t > ticks) { system.clearRun(h); removeFx(e); return; }
      moveShape(e, at(), o.faceYaw ? o.faceYaw() : undefined);
    } catch (err) { system.clearRun(h); removeFx(e); }
  }, 2);
  return e;
}
// أشكال تنرمي وتنزل بالجاذبية (صخور، أرقام متكسرة، شظايا)
function fling(dim, names, c, n, power = 1, rmin = 0.6, rmax = 1.3) {
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2, sp = (0.12 + Math.random() * 0.18) * power, up = 0.35 + Math.random() * 0.35 * power;
    const pos = { x: c.x + Math.cos(a) * 0.6, y: c.y + 0.3, z: c.z + Math.sin(a) * 0.6 };
    const nm = Array.isArray(names) ? names[Math.floor(Math.random() * names.length)] : names;
    const e = shapeFx(dim, nm, pos, { r: rmin + Math.random() * (rmax - rmin), s: 300 + Math.random() * 300, a: Math.random() * 90, life: 26 });
    if (!e) return;
    let vy = up;
    tween(24, 1, () => {
      pos.x += Math.cos(a) * sp; pos.z += Math.sin(a) * sp; pos.y += vy; vy -= 0.06;
      moveShape(e, pos);
    });
  }
}
// صخور صغيرة تطير وتنزل (إحساس تكسير الأرض بدون ما نغير البلوكات)
function rockBurst(dim, c, n, power = 1) { fling(dim, "rock_chunk", c, n, power); }

// ───────────────────────── تكسير بلوكات حقيقي (المطرقة): البلوكات تسقط وتقدر تجمعها ─────────────────────────
const UNBREAKABLE = new Set(["minecraft:bedrock", "minecraft:barrier", "minecraft:command_block", "minecraft:repeating_command_block", "minecraft:chain_command_block",
  "minecraft:structure_block", "minecraft:structure_void", "minecraft:jigsaw", "minecraft:end_portal_frame", "minecraft:end_portal", "minecraft:portal", "minecraft:end_gateway",
  "minecraft:obsidian", "minecraft:crying_obsidian", "minecraft:reinforced_deepslate", "minecraft:mob_spawner", "minecraft:trial_spawner", "minecraft:vault", "minecraft:light_block",
  "minecraft:border_block", "minecraft:allow", "minecraft:deny", "minecraft:respawn_anchor", "minecraft:beacon", "minecraft:enchanting_table", "minecraft:ender_chest"]);
const CONTAINER_HINT = ["chest", "barrel", "shulker", "furnace", "smoker", "hopper", "dispenser", "dropper", "brewing", "crafter", "lectern", "campfire", "bed", "sign", "banner", "skull", "head", "frame", "pot", "bookshelf", "jukebox"];
function canBreak(b) {
  if (!b || b.isAir || b.isLiquid) return false;
  const id = b.typeId;
  if (UNBREAKABLE.has(id) || id.startsWith("sh:")) return false;
  return !CONTAINER_HINT.some((k) => id.includes(k));
}
// يكسر البلوكات كأن اللاعب حفرها (تسقط كأيتمات). max حد أعلى للأمان.
function breakBlocks(dim, positions, max = 40) {
  let n = 0;
  for (const q of positions) {
    if (n >= max) break;
    try {
      const b = dim.getBlock(q);
      if (!canBreak(b)) continue;
      dim.runCommand(`setblock ${q.x} ${q.y} ${q.z} air destroy`);
      n++;
    } catch (err) { /* */ }
  }
  return n;
}

// ═════════════════════════ الصدع (Rift) ═════════════════════════
// يتفتح نادراً (محاولة كل دقيقتين باحتمال 8%) على بعد 40-70 بلوكة من لاعب، وحد أقصى صدع واحد بالعالم.
// لونه يحدد رتبة زعيمه: أزرق = دنيئة (Lowly)، بنفسجي = خبيثة (Vile)، قرمزي = مرعبة (Dread)، ذهبي أسود = كارثية (Cataclysm).
// يكبر كل 30 ثانية ويفسد الأرض حواليه (ترجع طبيعية لما يتسد). من يقرب لاعب 14 بلوكة تبدي 3 موجات، والثالثة زعيم.
// قتل الزعيم = الصدع ينسد ومكافآت حسب لونه. إذا ما أحد سده خلال 20 دقيقة ينفجر ويطلق زعيمه بالعالم.
const RIFT_TIERS = [
  { key: "blue", name: "Blue Rift", rank: "Lowly", col: "§9", rgb: [0.3, 0.65, 1], weight: 60, minRank: 0, ground: "minecraft:warped_nylium", circle: 2, mob: 0, boss: 12, waves: [4, 6], skill: 0.25, weapon: 0.1 },
  { key: "violet", name: "Violet Rift", rank: "Vile", col: "§5", rgb: [0.65, 0.32, 1], weight: 25, minRank: 1, ground: "minecraft:purple_terracotta", circle: 1, mob: 2, boss: 20, waves: [5, 7], skill: 0.6, weapon: 0.25 },
  { key: "crimson", name: "Crimson Rift", rank: "Dread", col: "§c", rgb: [1, 0.2, 0.25], weight: 12, minRank: 2, ground: "minecraft:crimson_nylium", circle: 5, mob: 4, boss: 32, waves: [6, 8], skill: 1, weapon: 0.45 },
  { key: "abyss", name: "Abyssal Rift", rank: "Cataclysm", col: "§6", rgb: [1, 0.8, 0.3], weight: 3, minRank: 3, ground: "minecraft:blackstone", circle: 0, mob: 6, boss: 48, waves: [7, 9], skill: 2, weapon: 1 },
];
const RIFT_LIFE = 24000, RIFT_ENGAGE = 14, RIFT_MAX_R = 12;
const RIFT_GROUND = new Set(["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol", "minecraft:sand", "minecraft:red_sand", "minecraft:gravel", "minecraft:stone", "minecraft:andesite", "minecraft:diorite", "minecraft:granite", "minecraft:snow", "minecraft:mycelium", "minecraft:moss_block", "minecraft:mud", "minecraft:terracotta", "minecraft:sandstone"]);
let rift = null;
function riftState() { return rift; }
function riftTier() { return rift ? RIFT_TIERS[rift.tier] : undefined; }
function riftSave() {
  try { world.setDynamicProperty("sh_rift", rift ? JSON.stringify({ ...rift, ent: undefined, scars: rift.scars.slice(0, 700) }) : undefined); } catch (e) { /* */ }
}
system.runTimeout(() => {
  try { const raw = world.getDynamicProperty("sh_rift"); if (typeof raw === "string") rift = JSON.parse(raw); } catch (e) { rift = null; }
}, 40);
function nearStructure(x, z, d) { try { return getStructs().some((s) => Math.hypot(s.x - x, s.z - z) < d); } catch (e) { return false; } }
function openRift(p, tierIdx, force) {
  if (rift || p.dimension.id !== "minecraft:overworld") return false;
  const dim = p.dimension;
  for (let i = 0; i < 14; i++) {
    const a = Math.random() * Math.PI * 2, d = force ? 14 + Math.random() * 6 : 40 + Math.random() * 30;
    const x = Math.floor(p.location.x + Math.cos(a) * d), z = Math.floor(p.location.z + Math.sin(a) * d);
    if (!force && nearStructure(x, z, 40)) continue;
    let top;
    try { top = dim.getTopmostBlock({ x, z }); } catch (e) { continue; }
    if (!top || /water|lava|leaves|log|ice/.test(top.typeId)) continue;
    rift = { id: `r${Date.now() % 100000}`, tier: tierIdx, dim: dim.id, x: x + 0.5, y: top.y + 1, z: z + 0.5, age: 0, r: 0, phase: "growing", wave: 0, pause: 0, bossId: "", scars: [], pulse: 0 };
    riftGrow();
    const t = RIFT_TIERS[tierIdx];
    for (const q of world.getAllPlayers()) {
      if (q.dimension.id !== dim.id) continue;
      const dist = Math.round(dist2d(q.location, rift)), dirs = ["east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"];
      const dir = dirs[((Math.round((Math.atan2(rift.z - q.location.z, rift.x - q.location.x) * 180) / Math.PI / 45) % 8) + 8) % 8];
      say(q, `${t.col}§l[${t.name}]§r §fA rift tore open ${dist} blocks to the ${dir}. Its warden is of the §l${t.col}${t.rank}§r§f rank. Close it before it spreads.`);
      sfxPlayer(q, "sh.blackhole", 0.8, 0.6);
      try { q.onScreenDisplay.setTitle(`${t.col}§l${t.name.toUpperCase()}`, { subtitle: `§7${dist}m ${dir} · Warden: ${t.col}${t.rank}`, fadeInDuration: 5, stayDuration: 50, fadeOutDuration: 15 }); } catch (e) { /* */ }
    }
    riftSave();
    return true;
  }
  return false;
}
// الفساد يتوسع حلقة حلقة (وتسجل البلوكات الأصلية حتى ترجع)
function riftGrow() {
  if (!rift || rift.r >= RIFT_MAX_R) return;
  const t = riftTier(), dim = world.getDimension(rift.dim);
  const r0 = rift.r, r1 = rift.r === 0 ? 3 : rift.r + 1;
  rift.r = r1;
  const cx = Math.floor(rift.x), cz = Math.floor(rift.z), id = rift.id;
  system.runJob((function* () {
    let n = 0;
    for (let dx = -r1; dx <= r1; dx++) for (let dz = -r1; dz <= r1; dz++) {
      const d = Math.hypot(dx, dz);
      if (d > r1 || d <= r0 || (d > r1 - 1.2 && Math.random() < 0.45)) continue;
      if (++n % 10 === 0) yield;
      try {
        if (!rift || rift.id !== id || rift.scars.length >= 700) return;
        const top = dim.getTopmostBlock({ x: cx + dx, z: cz + dz });
        if (!top || !RIFT_GROUND.has(top.typeId) || Math.abs(top.y - rift.y) > 6) continue;
        rift.scars.push([top.x, top.y, top.z, top.typeId]);
        top.setType(t.ground);
        if (Math.random() < 0.25) glow(dim, { x: top.x + 0.5, y: top.y + 1.1, z: top.z + 0.5 }, { color: t.rgb, size: 0.25, life: 0.9, rise: 0.6 });
      } catch (e) { /* */ }
    }
  })());
}
function riftRestore(scars, ground) {
  const dim = world.getDimension(rift ? rift.dim : "minecraft:overworld");
  system.runJob((function* () {
    let n = 0;
    for (const [x, y, z, type] of scars) {
      if (++n % 12 === 0) yield;
      try { const b = dim.getBlock({ x, y, z }); if (b && b.typeId === ground) b.setType(type); } catch (e) { /* */ }
    }
  })());
}
function riftPlayersNear(r) {
  if (!rift) return [];
  return world.getAllPlayers().filter((q) => q.dimension.id === rift.dim && Math.hypot(q.location.x - rift.x, q.location.z - rift.z) <= r);
}
function riftMobs() {
  try { return world.getDimension(rift.dim).getEntities({ tags: ["sh_rift"], location: rift, maxDistance: 60 }); } catch (e) { return []; }
}
function riftSpawnMob(type, boss) {
  const t = riftTier(), dim = world.getDimension(rift.dim);
  const a = Math.random() * Math.PI * 2, d = 1.5 + Math.random() * 2;
  const x = rift.x + Math.cos(a) * d, z = rift.z + Math.sin(a) * d;
  let y = rift.y;
  try { const top = dim.getTopmostBlock({ x: Math.floor(x), z: Math.floor(z) }); if (top && Math.abs(top.y + 1 - rift.y) < 5) y = top.y + 1; } catch (e) { /* */ }
  let e;
  try { e = dim.spawnEntity(type, { x, y, z }); } catch (err) { return undefined; }
  const pr = Math.max(0, ...riftPlayersNear(60).map((q) => getState(q).rank));
  scaleMonster(e, Math.min(RANKS.length - 1 + 2, Math.max(pr, t.mob) + (boss ? 2 : 0)));
  try { e.addTag("sh_rift"); } catch (err) { /* */ }
  burst(dim, { x, y: y + 1, z }, 10, t.rgb, 3, 0.25);
  try { e.applyKnockback({ x: Math.cos(a) * 0.6, z: Math.sin(a) * 0.6 }, 0.4); } catch (err) { /* */ }
  if (boss) {
    try { e.triggerEvent("sh:rift_boss"); } catch (err) { /* */ }
    try { e.addTag("sh_rift_boss"); } catch (err) { /* */ }
    const amp = Math.min(250, t.boss + pr * 2);
    later(3, () => {
      try {
        e.addEffect("health_boost", 1000000, { amplifier: amp, showParticles: false });
        e.addEffect("strength", 1000000, { amplifier: rift && rift.tier >= 2 ? 1 : 0, showParticles: false });
        e.addEffect("resistance", 1000000, { amplifier: rift && rift.tier >= 3 ? 1 : 0, showParticles: false });
        later(2, () => { try { e.getComponent("minecraft:health").resetToMaxValue(); } catch (err) { /* */ } });
      } catch (err) { /* */ }
    });
    try { e.nameTag = `${t.col}§l[${t.rank}] Rift Warden§r §7(${MON_NAMES[type] || "?"})`; } catch (err) { /* */ }
    rift.bossId = e.id;
  }
  return e;
}
function riftStartWave(n) {
  const t = riftTier();
  rift.wave = n;
  rift.pause = 0;
  for (const q of riftPlayersNear(48)) {
    try { q.onScreenDisplay.setTitle(n === 3 ? `${t.col}§lTHE WARDEN` : `${t.col}§lWAVE ${n}/3`, { subtitle: n === 3 ? `§7Rank: ${t.col}${t.rank}` : `§7${t.name}`, fadeInDuration: 3, stayDuration: 30, fadeOutDuration: 10 }); } catch (e) { /* */ }
    sfxPlayer(q, n === 3 ? "sh.supernova_charge" : "sh.boundary", 1, n === 3 ? 0.6 : 0.8);
  }
  const dim = world.getDimension(rift.dim);
  popShape(dim, "nova", { x: rift.x, y: rift.y + 2.2, z: rift.z }, 0.3, 1.6, 8, { s: 300 });
  if (n === 3) {
    later(20, () => { if (rift) { riftSpawnMob(RANK0_TYPES[Math.floor(Math.random() * RANK0_TYPES.length)], true); for (let i = 0; i < 2; i++) riftSpawnMob(RANK0_TYPES[Math.floor(Math.random() * RANK0_TYPES.length)], false); } });
  } else {
    const count = t.waves[n - 1];
    for (let i = 0; i < count; i++) later(i * 6, () => { if (rift) riftSpawnMob(RANK0_TYPES[Math.floor(Math.random() * RANK0_TYPES.length)], false); });
  }
  riftSave();
}
// زعيم الصدع: نبضة كل 8 ثواني تضرب اللاعبين القريبين (وبالقرمزي والكارثي تطلع وحش مساعد)
function riftBossPulse(boss) {
  const t = riftTier(), dim = boss.dimension;
  spawnFx(dim, "circle", boss.location, t.circle, 6, 16);
  waveFx(dim, boss.location, 6, t.circle, 10);
  sfx(dim, "sh.guard_slam", boss.location, 1.2, 0.6);
  for (const q of world.getAllPlayers()) {
    if (q.dimension.id !== dim.id || dist2d(q.location, boss.location) > 6) continue;
    try { q.applyDamage(3 + rift.tier * 2, { cause: EntityDamageCause.entityAttack, damagingEntity: boss }); } catch (e) { /* */ }
    pushAway(boss.location, q, 1.4, 0.45);
  }
  if (rift.tier >= 2 && riftMobs().length < 6) riftSpawnMob(RANK0_TYPES[Math.floor(Math.random() * RANK0_TYPES.length)], false);
}
function closeRift(victory, killer) {
  if (!rift) return;
  const r = rift, t = RIFT_TIERS[r.tier], dim = world.getDimension(r.dim);
  rift = null;
  riftSave();
  removeFx(r.ent);
  const c = { x: r.x, y: r.y + 2.2, z: r.z };
  const imp = shapeFx(dim, `rift_${t.key}`, c, { r: 1.2 + r.r * 0.08, s: 600, life: 16 });
  tween(12, 1, (k) => setShape(imp, "sh:r", (1.2 + r.r * 0.08) * (1 - k)), () => { popShape(dim, "nova", c, 0.3, 2.4, 8, { s: 400, ease: "out" }); sfx(dim, "sh.blackhole_end", c, 1.5, 1); });
  riftRestore(r.scars, t.ground);
  if (!victory) return;
  // المكافآت تنزل عند الصدع
  const drops = ["sh:xp_scroll_big", "sh:xp_scroll_small", "sh:xp_scroll_small"];
  for (let i = 0; i < Math.floor(t.skill); i++) drops.push("sh:skill_scroll");
  if (Math.random() < t.skill % 1) drops.push("sh:skill_scroll");
  if (Math.random() < t.weapon) drops.push(["sh:dawn_dagger", "sh:shadow_blade", "sh:shadow_claws", "sh:ember_cleaver", "sh:stone_maul", "sh:sunset_spear"][Math.floor(Math.random() * 6)]);
  drops.push(...Array(1 + r.tier).fill(r.tier >= 2 ? "minecraft:diamond" : "minecraft:emerald"));
  later(14, () => { for (const id of drops) { try { dim.spawnItem(new ItemStack(id, 1), { x: r.x + (Math.random() - 0.5), y: r.y + 1, z: r.z + (Math.random() - 0.5) }); } catch (e) { /* */ } } });
  for (const q of world.getAllPlayers()) {
    if (q.dimension.id !== r.dim || Math.hypot(q.location.x - r.x, q.location.z - r.z) > 60) continue;
    try { q.onScreenDisplay.setTitle("§f§lRIFT SEALED", { subtitle: `${t.col}${t.name} §7· rewards dropped at the rift`, fadeInDuration: 4, stayDuration: 50, fadeOutDuration: 15 }); } catch (e) { /* */ }
    const st = getState(q), amt = 80 * (r.tier + 1);
    const ups = addXp(st, amt);
    if (st.power) ups.push(...addPowerXp(st, amt, rarityOf(st.power).maxLv));
    st.rifts = (st.rifts || 0) + 1;
    saveState(q, st);
    announceUps(q, ups);
    sfxPlayer(q, "sh.rank_up", 1, 1.2);
  }
}
world.afterEvents.entityDie.subscribe((ev) => {
  try { if (rift && rift.bossId && ev.deadEntity.id === rift.bossId) closeRift(true, ev.damageSource && ev.damageSource.damagingEntity); } catch (e) { /* */ }
});
// القلب: كل ثانية
system.runInterval(() => {
  try {
    const now = system.currentTick;
    if (!rift) {
      if (now % 2400 === 0 && Math.random() < 0.08) {
        const ps = world.getAllPlayers().filter((q) => q.dimension.id === "minecraft:overworld");
        if (ps.length) {
          const p = ps[Math.floor(Math.random() * ps.length)], rank = getState(p).rank;
          const ok = RIFT_TIERS.map((t, i) => ({ t, i })).filter((x) => x.t.minRank <= rank);
          let roll = Math.random() * ok.reduce((a, x) => a + x.t.weight, 0), pick = 0;
          for (const x of ok) { roll -= x.t.weight; if (roll <= 0) { pick = x.i; break; } }
          openRift(p, pick, false);
        }
      }
      return;
    }
    const t = riftTier(), dim = world.getDimension(rift.dim);
    rift.age += 20;
    const near = riftPlayersNear(64);
    if (!near.length) { if (rift.age > RIFT_LIFE && rift.phase !== "battle") closeRift(false); return; }
    // الشكل: شق كبير يكبر ويه الفساد
    const c = { x: rift.x, y: rift.y + 2.2, z: rift.z };
    if (!rift.ent || !valid(rift.ent)) rift.ent = shapeFx(dim, `rift_${t.key}`, c, { r: 1.2 + rift.r * 0.08, s: 10, life: 1100 });
    else setShape(rift.ent, "sh:r", 1.2 + rift.r * 0.08);
    for (let i = 0; i < 4; i++) {
      const a = Math.random() * Math.PI * 2, rr = 1 + Math.random() * rift.r;
      glow(dim, { x: rift.x + Math.cos(a) * rr, y: rift.y + 0.3, z: rift.z + Math.sin(a) * rr }, { color: t.rgb, size: 0.25, life: 1.2, rise: 1.2 });
    }
    if (rift.age % 600 === 0) riftGrow();
    if (rift.age % 200 === 0) sfx(dim, "sh.blackhole", c, 0.5, 0.5);
    if (rift.phase === "growing") {
      if (riftPlayersNear(RIFT_ENGAGE).length) { rift.phase = "battle"; riftStartWave(1); }
      else if (rift.age > RIFT_LIFE) {
        // ما أحد سده: ينفجر ويطلق زعيمه بالعالم
        const b = riftSpawnMob(RANK0_TYPES[Math.floor(Math.random() * RANK0_TYPES.length)], true);
        for (const q of world.getAllPlayers()) say(q, `${t.col}§l[${t.name}]§r §cThe rift erupted. Its warden now roams the land.`);
        if (b) { try { b.removeTag("sh_rift"); } catch (e) { /* */ } }
        closeRift(false);
      }
      return;
    }
    // المعركة: الموجة تخلص لما ما يبقى وحش من الصدع
    const mobs = riftMobs();
    if (rift.wave < 3 && mobs.length === 0) {
      rift.pause += 20;
      if (rift.pause === 20) for (const q of riftPlayersNear(48)) notify(q, `${t.col}Wave ${rift.wave} cleared. The rift stirs...`, 60);
      if (rift.pause >= 100) riftStartWave(rift.wave + 1);
    }
    if (rift.wave === 3) {
      const boss = mobs.find((m) => m.id === rift.bossId);
      if (boss) { rift.pulse += 20; if (rift.pulse >= 160) { rift.pulse = 0; riftBossPulse(boss); } }
      else if (rift.bossId && rift.pause++ > 4 && !mobs.some((m) => m.id === rift.bossId)) {
        // الزعيم اختفى (مو قتل): نطلع زعيم جديد
        rift.bossId = ""; riftStartWave(3);
      }
    }
    if (rift.age % 100 === 0) riftSave();
  } catch (e) { /* */ }
}, 20);
function riftHudLine(p, plain) {
  if (!rift || p.dimension.id !== rift.dim) return "";
  const t = riftTier(), dist = Math.round(Math.hypot(rift.x - p.location.x, rift.z - p.location.z));
  const arrow = compassArrow(p, rift);
  let line = `${plain ? "§d⟁" : "§f" + GL(GI.rift)} ${t.col}§l${t.name}§r §7(${t.rank}) ${dist}m ${arrow}`;
  if (rift.phase === "battle") {
    const waves = plain ? `§c${rift.wave}/3` : "§f" + GL(GI.wave_on).repeat(rift.wave) + GL(GI.wave_off).repeat(3 - rift.wave);
    line += `  ${waves} §6Wave ${rift.wave}/3`;
    if (rift.wave === 3 && !plain) line += ` §f${GL(GI.boss)}`;
  } else line += `  §7spreading ${rift.r}/${RIFT_MAX_R}`;
  return line;
}
function riftStatusText(p) {
  const st = getState(p);
  if (!rift) return `§5Rifts§7: none open right now. They tear open rarely; the warden's rank follows the rift's color. Sealed: ${st.rifts || 0}`;
  const t = riftTier();
  return `${t.col}${t.name}§7 open (warden rank ${t.col}${t.rank}§7), ${Math.round(Math.hypot(rift.x - p.location.x, rift.z - p.location.z))} blocks away, ${rift.phase === "battle" ? `wave ${rift.wave}/3` : "spreading"}. Sealed: ${st.rifts || 0}`;
}

// ═════════════════════════ ضربة الإيقاع (Rhythm Strike) ═════════════════════════
// بدون أيتم وبدون عداد. تنفتح من رتبة Elite (الرابعة).
//  * أول ضربتين على أي عدو تحدد "الإيقاع" (الفرق بينهم لازم يكون بين 0.3 و1.5 ثانية).
//  * بعدها كل ضربة لازم تجي بنفس الإيقاع (هامش 15% أو تكتين، الأكبر). كل ضربة صح = نوتة موسيقية ترتفع.
//  * صوت خفيف (تك) بوقت الضربة الجاية حتى تمشي ويا الإيقاع مثل الموسيقى، بدون ما تباوع على شي.
//  * الضربة الرابعة بالإيقاع = ضربة الإيقاع، السابعة = التصاعد (Crescendo)، العاشرة = الختام (Finale) وتنعاد.
//  * ضربة برا الإيقاع أو توقف = نوتة واطية والإيقاع يبدي من جديد.
//  * الـUnbound (بلا قدرة) ضربتهم أقوى 30%.
const RHY_RANK = 3, RHY_MIN = 6, RHY_MAX = 30;
const RHY_NOTES = [0.5, 0.56, 0.63, 0.75, 0.84, 1, 1.12, 1.26, 1.5, 1.68, 2];
const rhythm = new Map(); // pid -> { last, iv, combo, tid, ticked }
const rhyDebug = new Set();
function vanillaFx(dim, id, loc) { try { dim.spawnParticle(id, loc); } catch (e) { /* */ } }
function rhyTol(iv) { return Math.max(2, Math.round(iv * 0.15)); }
function rhyNote(p, i, vol = 0.9) { sfxPlayer(p, "note.pling", vol, RHY_NOTES[Math.max(0, Math.min(RHY_NOTES.length - 1, i))]); }
function rhyLost(p, why) {
  rhythm.delete(p.id);
  sfxPlayer(p, "note.bass", 0.8, 0.6);
  later(3, () => { if (valid(p)) sfxPlayer(p, "note.bass", 0.7, 0.5); });
  if (why) notify(p, why, 25);
}
// المترونوم: تك خفيف بوقت الضربة الجاية، وإذا فاتك الوقت ينقطع الإيقاع
system.runInterval(() => {
  const now = system.currentTick;
  if (!rhythm.size) return;
  for (const p of world.getAllPlayers()) {
    try {
      const r = rhythm.get(p.id);
      if (!r) continue;
      if (!r.iv) { if (now - r.last > RHY_MAX + 4) rhythm.delete(p.id); continue; }
      const due = r.last + r.iv;
      if (now === due && r.ticked !== due) { r.ticked = due; sfxPlayer(p, "note.hat", 0.35, 1.2); }
      if (now > due + rhyTol(r.iv) + 1) rhyLost(p, r.combo >= 2 ? "§8♪ rhythm lost" : "");
    } catch (e) { /* */ }
  }
}, 1);
function rhythmStrike(p, t, tier) {
  const dim = t.dimension, c = center3(t), st = getState(p);
  const mult = st.powerless ? 1.3 : 1;
  const base = tier === 1 ? 8 + 2 * st.rank : tier === 2 ? 14 + 3 * st.rank : 24 + 4 * st.rank;
  const dmg = Math.round(base * mult), r = tier === 1 ? 3 : tier === 2 ? 4.5 : 6;
  try { t.applyDamage(dmg, { cause: EntityDamageCause.entityAttack, damagingEntity: p }); } catch (e) { /* */ }
  for (const e of enemiesNear(dim, t.location, r, t.id)) {
    try { e.applyDamage(Math.round(dmg * (tier === 1 ? 0.6 : 0.8)), { cause: EntityDamageCause.entityAttack, damagingEntity: p }); } catch (err) { /* */ }
    pushAway(t.location, e, 0.8 + tier * 0.4, 0.3 + tier * 0.1);
  }
  pushAway(p.location, t, 1 + tier * 0.5, tier === 2 ? 0.8 : 0.35);
  effect(t, "slowness", 30 + tier * 20, Math.min(4, tier + 1));
  if (tier >= 2) effect(t, "weakness", 80, tier - 1);
  // المؤثرات: نوتات وحلقة صوت وموجة
  for (let i = 0; i < 8 + tier * 4; i++) {
    const a = (i / (8 + tier * 4)) * Math.PI * 2;
    vanillaFx(dim, "minecraft:note_particle", { x: c.x + Math.cos(a) * r * 0.6, y: c.y + 0.4 + Math.random() * 0.6, z: c.z + Math.sin(a) * r * 0.6 });
  }
  vanillaFx(dim, "minecraft:critical_hit_emitter", c);
  waveFx(dim, { x: t.location.x, y: t.location.y + 0.1, z: t.location.z }, r, 0, 10);
  vanillaFx(dim, "minecraft:knockback_roar_particle", { x: t.location.x, y: t.location.y + 0.3, z: t.location.z });
  if (tier >= 2) { popShape(dim, "nova", c, 0.3, r * 0.45, 8, { s: 300, ease: "out" }); vanillaFx(dim, "minecraft:sonic_explosion", c); }
  if (tier >= 3) { vanillaFx(dim, "minecraft:huge_explosion_emitter", c); rockBurst(dim, t.location, 8); }
  const names = ["", "§b§lRHYTHM", "§d§lCRESCENDO", "§6§lFINALE"];
  notify(p, `${names[tier]} §r§7${dmg} dmg`, 35);
  try { dim.playSound(tier === 3 ? "sh.supernova_boom" : tier === 2 ? "sh.guard_slam" : "sh.echostrike", t.location, { volume: 0.9, pitch: 1 + tier * 0.05 }); } catch (e) { /* */ }
  // كورد: 3 نوتات سوه
  for (const k of [0, 2, 4]) rhyNote(p, 3 + tier + k, 0.8);
  shake(p, 0.08 + tier * 0.06, 0.15 + tier * 0.05);
  const best = tier * 3 + 1;
  if (best > (st.rhyBest || 0)) { st.rhyBest = best; saveState(p, st); }
}
world.afterEvents.entityHitEntity.subscribe((ev) => {
  try {
    const p = ev.damagingEntity, t = ev.hitEntity;
    if (!p || p.typeId !== "minecraft:player" || !t || t.typeId === "sh:trainer" || isFriendly(t) || !t.getComponent("minecraft:health")) return;
    if (getState(p).rank < RHY_RANK) return;
    const now = system.currentTick;
    let r = rhythm.get(p.id);
    if (!r || now - r.last > RHY_MAX + 4) {
      rhythm.set(p.id, { last: now, iv: 0, combo: 0, tid: t.id, ticked: 0 });
      return;
    }
    const dt = now - r.last;
    if (dt < 3) return; // نفس الضربة مرتين
    if (!r.iv) {
      if (dt < RHY_MIN) { r.last = now; return; }
      // الضربة الثانية تحدد الإيقاع
      r.iv = dt; r.last = now; r.combo = 1; r.tid = t.id;
      rhyNote(p, 2);
      vanillaFx(t.dimension, "minecraft:note_particle", headPos(t));
      return;
    }
    const err = dt - r.iv, tol = rhyTol(r.iv);
    if (rhyDebug.has(p.id)) notify(p, Math.abs(err) <= tol ? "§a§lON BEAT" : err < 0 ? `§eToo early §7by ${(-err / 20).toFixed(2)}s` : `§cToo late §7by ${(err / 20).toFixed(2)}s`, 30);
    if (Math.abs(err) > tol) {
      rhyLost(p, r.combo >= 2 ? "§8♪ off beat" : "");
      rhythm.set(p.id, { last: now, iv: 0, combo: 0, tid: t.id, ticked: 0 }); // هالضربة تصير أول نبضة جديدة
      return;
    }
    r.combo++; r.last = now; r.tid = t.id;
    r.iv = Math.round((r.iv * 3 + dt) / 4); // يتبعك شوية إذا تبطئ أو تسرع بالتدريج
    vanillaFx(t.dimension, "minecraft:note_particle", { x: t.location.x, y: t.location.y + 2.3, z: t.location.z });
    if (r.combo % 3 === 0) {
      const tier = r.combo / 3;
      rhythmStrike(p, t, tier);
      if (tier >= 3) rhythm.delete(p.id);
    } else {
      rhyNote(p, r.combo + 1);
      if (r.combo >= 2) notify(p, `§b♪ ${r.combo}`, 15);
    }
  } catch (e) { /* */ }
});

// ═════════════════════════ الصد المثالي (Perfect Guard) ═════════════════════════
// من رتبة Trainee: اضغط سنيك بنفس لحظة ما توصلك ضربة وحش (خلال 0.35 ثانية من الضغطة) = الضرر يرجع،
// الوحش يندفع ويتشل ثانيتين ونص، وضربتك الجاية خلال ثانيتين ونص = ضربة مضادة قوية.
// الضغط المتكرر ما ينفع: بعد كل ضغطة لازم تنتظر ثانية حتى تنحسب ضغطة صد جديدة.
const GUARD_RANK = 1, GUARD_WIN = 7, GUARD_GAP = 20;
const sneakPrev = new Map(), guardAt = new Map(), riposte = new Map();
system.runInterval(() => {
  const now = system.currentTick;
  for (const p of world.getAllPlayers()) {
    try {
      const sn = !!p.isSneaking, was = sneakPrev.get(p.id);
      sneakPrev.set(p.id, sn);
      if (sn && !was) { const g = guardAt.get(p.id); if (!g || now - g.at > GUARD_GAP) guardAt.set(p.id, { at: now, used: false }); }
    } catch (e) { /* */ }
  }
}, 1);
world.afterEvents.entityHurt.subscribe((ev) => {
  try {
    const p = ev.hurtEntity;
    if (!p || p.typeId !== "minecraft:player") return;
    const src = ev.damageSource && ev.damageSource.damagingEntity;
    if (!src || src.typeId === "minecraft:player" || !valid(src)) return;
    const g = guardAt.get(p.id), now = system.currentTick;
    if (!g || g.used || now - g.at > GUARD_WIN) return;
    if (getState(p).rank < GUARD_RANK) return;
    g.used = true;
    const hp = p.getComponent("minecraft:health");
    if (!hp || hp.currentValue <= 0) return;
    hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + ev.damage));
    effect(src, "slowness", 50, 4);
    effect(src, "weakness", 50, 1);
    setMState(src, 0);
    pushAway(p.location, src, 1.1, 0.3);
    const dim = p.dimension, c = { x: (p.location.x + src.location.x) / 2, y: p.location.y + 1.2, z: (p.location.z + src.location.z) / 2 };
    popShape(dim, "nova", c, 0.2, 0.9, 6, { s: 400, ease: "out" });
    for (let i = 0; i < 10; i++) pix(dim, { x: c.x + (Math.random() - 0.5) * 0.6, y: c.y + (Math.random() - 0.5) * 0.6, z: c.z + (Math.random() - 0.5) * 0.6 }, { color: i % 2 ? COLORS.gold : COLORS.white, size: 0.18, life: 0.4, speed: 2.4 });
    try { dim.playSound("random.anvil_land", p.location, { volume: 0.6, pitch: 1.7 }); } catch (e) { /* */ }
    sfxPlayer(p, "sh.reflect", 1, 1.3);
    shake(p, 0.08, 0.12);
    riposte.set(p.id, { until: now + 50, tid: src.id });
    notify(p, "§f§lPERFECT GUARD §r§7strike back now!", 30);
    const st = getState(p); st.guards = (st.guards || 0) + 1; saveState(p, st);
  } catch (e) { /* */ }
});
// الضربة المضادة: أول ضربة بعد الصد
world.afterEvents.entityHitEntity.subscribe((ev) => {
  try {
    const p = ev.damagingEntity, t = ev.hitEntity;
    if (!p || p.typeId !== "minecraft:player" || !t || isFriendly(t) || t.typeId === "sh:trainer") return;
    const r = riposte.get(p.id);
    if (!r || system.currentTick > r.until) return;
    riposte.delete(p.id);
    const st = getState(p), dmg = 6 + 2 * st.rank + (t.id === r.tid ? 4 : 0);
    try { t.applyDamage(dmg, { cause: EntityDamageCause.entityAttack, damagingEntity: p }); } catch (e) { /* */ }
    pushAway(p.location, t, 1.3, 0.4);
    const c = center3(t);
    popShape(t.dimension, "slash_gold", c, 0.6, 1.4, 5, { yaw: yawOf(c, p.location), a: 30 });
    vanillaFx(t.dimension, "minecraft:critical_hit_emitter", c);
    sfx(t.dimension, "sh.kat_exec", t.location, 0.9, 1.3);
    notify(p, `§6§lCOUNTER §r§7${dmg} dmg`, 25);
  } catch (e) { /* */ }
});

// إخفاء قلوب ماينكرافت تحت (القلوب صارت فوق بالـHUD) ومجسمها الأصلي اللي كان يطلع فوق مجسمنا
function hideVanillaHud(p) {
  try {
    const H = MC.HudElement, V = MC.HudVisibility;
    if (!H || !V || !p.onScreenDisplay.setHudVisibility) return;
    const els = [H.Health, H.PaperDoll].filter((x) => x !== undefined);
    if (p.hasTag("sh_hud_off") || p.hasTag("sh_vanilla_hearts")) p.onScreenDisplay.setHudVisibility(V.Reset, els);
    else p.onScreenDisplay.setHudVisibility(V.Hide, els);
  } catch (e) { /* */ }
}
system.runInterval(() => { for (const p of world.getAllPlayers()) hideVanillaHud(p); }, 100);

// ───────────────────────── كاتب القوانين: المناطق ─────────────────────────
const zones = [];

function startZone(p, kind, r, durTicks) {
  for (let i = zones.length - 1; i >= 0; i--) {
    if (zones[i].owner === p.id && zones[i].kind === kind) endZone(i);
  }
  const z = {
    owner: p.id, kind, dim: p.dimension, r,
    c: { x: p.location.x, y: p.location.y, z: p.location.z },
    until: system.currentTick + durTicks, silenced: new Map(), captured: new Map(),
  };
  if (kind === "boundary") {
    for (const e of enemiesNear(p.dimension, z.c, r, p.id)) z.captured.set(e.id, e);
  }
  const colorIdx = { weight: 5, silence: 2, reflect: 4, boundary: 1 }[kind] ?? 0;
  z.fx = spawnFx(p.dimension, "circle", z.c, colorIdx, r, durTicks + 6);
  z.shapes = [];
  zones.push(z);
  return z;
}

function unsilenceAll(z) {
  for (const e of z.silenced.values()) { try { e.triggerEvent("sh:unsilence"); } catch (err) { /* */ } }
  z.silenced.clear();
}

const ZONE_COLORS = { weight: COLORS.red, silence: COLORS.blue, reflect: COLORS.white, boundary: COLORS.purple };

function endZone(i) {
  const z = zones[i];
  removeFx(z.fx);
  for (const e of z.shapes || []) removeFx(e);
  if (z.orbit) system.clearRun(z.orbit);
  unsilenceAll(z);
  ring(z.dim, z.c, z.r, 36, 0, ZONE_COLORS[z.kind] || COLORS.gold, 0.25);
  zones.splice(i, 1);
}

function zoneOf(kind, ownerId) {
  return zones.find((z) => z.kind === kind && z.owner === ownerId);
}

system.runInterval(() => {
  const now = system.currentTick;
  for (let i = zones.length - 1; i >= 0; i--) {
    const z = zones[i];
    if (now >= z.until) { endZone(i); continue; }
    let inside = [];
    try { inside = z.dim.getEntities({ location: z.c, maxDistance: z.r }); } catch (e) { /* */ }
    const seen = new Set();
    z.pulse = false;
    for (const e of inside) {
      try {
        if (e.id === z.owner || e.typeId === "sh:trainer") continue;
        if (!e.getComponent("minecraft:health")) continue;
        if (z.kind === "weight") {
          e.addEffect("slowness", 20, { amplifier: 3, showParticles: false });
          e.addEffect("jump_boost", 20, { amplifier: 200, showParticles: false });
          if (now - (z.lastDmg || 0) >= 20) { z.pulse = true; try { e.applyDamage(1, { cause: EntityDamageCause.magic }); } catch (err2) { /* */ } }
        } else if (z.kind === "silence") {
          e.addEffect("weakness", 20, { amplifier: 1, showParticles: false });
          if (RANGED_TYPES.has(e.typeId)) {
            seen.add(e.id);
            if (!z.silenced.has(e.id)) { e.triggerEvent("sh:silence"); z.silenced.set(e.id, e); followShape(e, "padlock", Math.max(10, z.until - now), { r: 0.55, s: 120, dy: 0.7 }); }
          }
        }
      } catch (err) { /* */ }
    }
    if (z.pulse) z.lastDmg = now;
    if (z.kind === "silence") {
      for (const [id, e] of [...z.silenced.entries()]) {
        if (!seen.has(id)) { try { e.triggerEvent("sh:unsilence"); } catch (err) { /* */ } z.silenced.delete(id); }
      }
    }
    if (z.kind === "boundary") {
      for (const [id, e] of [...z.captured.entries()]) {
        try {
          const d = dist2d(e.location, z.c);
          if (d > z.r - 1) {
            const k = (z.r - 2) / d;
            safeTeleport(e, { x: z.c.x + (e.location.x - z.c.x) * k, y: e.location.y, z: z.c.z + (e.location.z - z.c.z) * k });
            glow(z.dim, headPos(e), { color: COLORS.purple, size: 0.3, life: 0.4 });
          }
        } catch (err) { z.captured.delete(id); }
      }
    }
    if (now % 20 === 0) {
      const col = ZONE_COLORS[z.kind] || COLORS.gold;
      ring(z.dim, z.c, z.r, 18, now * 0.03, z.kind === "weight" ? COLORS.gold : col, 0.2);
    }
  }
}, 5);

// انعكاس: الضرر اللي ياخذه صاحب المنطقة يرجع على اللي ضربه
let reflecting = false;
world.afterEvents.entityHurt.subscribe((ev) => {
  try {
    if (reflecting) return;
    const victim = ev.hurtEntity;
    if (victim.typeId !== "minecraft:player") return;
    const z = zoneOf("reflect", victim.id);
    if (!z) return;
    const attacker = ev.damageSource && ev.damageSource.damagingEntity;
    if (!attacker || attacker.id === victim.id) return;
    if (dist2d(victim.location, z.c) > z.r) return;
    reflecting = true;
    try {
      hurt(attacker, ev.damage, victim);
      const hp = victim.getComponent("minecraft:health");
      if (hp) hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + ev.damage * 0.5));
      sfx(victim.dimension, "sh.reflect", victim.location, 1);
      popShape(attacker.dimension, "mirror", headPos(attacker), 0.5, 1.5, 6, { yaw: yawOf(attacker.location, victim.location) });
      burst(attacker.dimension, headPos(attacker), 10, COLORS.white, 3);
    } finally { reflecting = false; }
  } catch (e) { reflecting = false; }
});

// ───────────────────────── المهارات ─────────────────────────
const SKILL_FN = {
  seal(p) {
    const t = raycastTarget(p);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    sfx(p.dimension, "sh.seal", p.location);
    shake(p, 0.05, 0.1);
    symbolShot(p, t, "arrow_gold", () => {
      if (!valid(t)) return;
      setNum(t, 10);
      numOwners.set(t.id, { e: t, pid: p.id });
      try { t.addEffect("slowness", 60, { amplifier: 0, showParticles: false }); } catch (e) { /* */ }
      popShape(t.dimension, "echo_glyph", headPos(t), 0.4, 1.4, 8, { s: 400 });
      burst(t.dimension, headPos(t), 10, COLORS.gold, 2);
    });
    notify(p, "§6The number drops every two seconds and every hit lowers it. At zero it collapses", 70);
    return true;
  },
  subtract(p) {
    const t = raycastTarget(p);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    sfx(p.dimension, "sh.subtract", p.location);
    shake(p, 0.08, 0.12);
    symbolShot(p, t, "sym_minus", () => {
      if (!valid(t)) return;
      popShape(t.dimension, "sym_minus", { ...headPos(t), y: headPos(t).y + 0.3 }, 1.0, 1.8, 6, { s: 300 });
      const n = t.getDynamicProperty("sh_num");
      if (typeof n !== "number") { setNum(t, 7); numOwners.set(t.id, { e: t, pid: p.id }); }
      else decNum(t, 3, p);
      hurt(t, 2, p);
    }, 1.3);
    return true;
  },
  weight(p) {
    const z = startZone(p, "weight", 6, 120);
    sfx(p.dimension, "sh.weight", p.location, 1.2);
    // ثقل حديدي عملاق ينزل من السما بمركز الدائرة
    const c = { ...z.c }, dim = p.dimension;
    const w = shapeFx(dim, "weight", { x: c.x, y: c.y + 9, z: c.z }, { r: 1.6, yaw: Math.random() * 90, life: 124 });
    if (w) z.shapes.push(w);
    tween(6, 1, (k) => moveShape(w, { x: c.x, y: c.y + 9 * (1 - k * k), z: c.z }), () => {
      shake(p, 0.22, 0.3);
      sfx(dim, "sh.guard_slam", c, 1.2, 0.7);
      waveFx(dim, c, 6, 5, 10);
      rockBurst(dim, c, 5, 1.2);
      for (const e of enemiesNear(dim, c, 6, p.id)) { hurt(e, 3, p); try { e.applyKnockback({ x: 0, z: 0 }, -0.6); } catch (err) { /* */ } }
    });
    return true;
  },
  silence(p) {
    const z = startZone(p, "silence", 8, 100);
    sfx(p.dimension, "sh.silence", p.location, 1.1);
    const lock = shapeFx(p.dimension, "padlock", { x: z.c.x, y: z.c.y + 3.2, z: z.c.z }, { r: 1.6, s: 70, life: 104 });
    if (lock) z.shapes.push(lock);
    ring(p.dimension, p.location, 8, 24, 0, COLORS.blue, 0.22);
    return true;
  },
};


// ───────────────────────── مهارات إضافية ─────────────────────────
function valid(e) {
  try { return typeof e.isValid === "function" ? e.isValid() : !!e.isValid; } catch (err) { return false; }
}
const echoReady = new Map();
const echoMarks = new Map();

function numberOf(e) { const n = e.getDynamicProperty("sh_num"); return typeof n === "number" ? n : undefined; }

function arc(dim, c, dir, r, halfAngle, color, n = 14) {
  const base = Math.atan2(dir.z, dir.x);
  for (let i = 0; i < n; i++) {
    const a = base - halfAngle + (i / (n - 1)) * halfAngle * 2;
    glow(dim, { x: c.x + Math.cos(a) * r, y: c.y + 0.3, z: c.z + Math.sin(a) * r }, { color, size: 0.22, life: 0.5, rise: 0.3 });
  }
}

Object.assign(SKILL_FN, {
  // ── المحاسب ──
  transfer(p) {
    const t = raycastTarget(p);
    const n = t && numberOf(t);
    if (!t || n === undefined) { notify(p, "§cTarget an enemy with a number", 40); return false; }
    const o = nearestEnemy(t, 12);
    if (!o) { notify(p, "§cNo other enemy nearby", 40); return false; }
    clearNum(t);
    const a = headPos(t), b = headPos(o);
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z, l = Math.hypot(dx, dy, dz) || 1;
    flyShape(t.dimension, `digit_${String(n)[0]}`, a, { x: dx / l, y: dy / l, z: dz / l }, 0.9, l, { r: 0.85, s: 500 }, undefined, () => {
      if (!valid(o)) return;
      setNum(o, n);
      numOwners.set(o.id, { e: o, pid: p.id });
      burst(o.dimension, headPos(o), 12, COLORS.gold, 2.5);
    });
    sfx(p.dimension, "sh.transfer", p.location);
    return true;
  },
  divide(p) {
    const t = raycastTarget(p);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    let n = numberOf(t);
    if (n === undefined) n = 10;
    if (n < 2) { notify(p, "§cThe number 1 cannot be divided", 40); return false; }
    const o = nearestEnemy(t, 12);
    if (!o) { notify(p, "§cNo other enemy nearby", 40); return false; }
    const a = Math.ceil(n / 2), b = Math.floor(n / 2);
    popShape(t.dimension, "sym_divide", { ...headPos(t), y: headPos(t).y + 0.4 }, 0.6, 1.8, 10, { s: 360 });
    later(8, () => {
      if (valid(t)) { setNum(t, a); numOwners.set(t.id, { e: t, pid: p.id }); }
      if (valid(o) && valid(t)) {
        const A = headPos(t), B = headPos(o), dx = B.x - A.x, dy = B.y - A.y, dz = B.z - A.z, l = Math.hypot(dx, dy, dz) || 1;
        flyShape(t.dimension, `digit_${String(b)[0]}`, A, { x: dx / l, y: dy / l, z: dz / l }, 0.9, l, { r: 0.7, s: 500 }, undefined, () => {
          if (valid(o)) { setNum(o, b); numOwners.set(o.id, { e: o, pid: p.id }); }
        });
      }
    });
    sfx(p.dimension, "sh.divide", p.location);
    shake(p, 0.08, 0.1);
    return true;
  },
  zero(p) {
    const t = raycastTarget(p);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    sfx(p.dimension, "sh.zero", p.location, 1.2);
    // صفر ذهبي عملاق ينزل من فوق ويسحق الهدف
    const top = { x: t.location.x, y: t.location.y + 6, z: t.location.z };
    const z0 = shapeFx(t.dimension, "digit_0", top, { r: 2.4, yaw: yawOf(t.location, p.location), life: 16 });
    tween(8, 1, (k) => moveShape(z0, { x: t.location.x, y: top.y - 5.0 * k * k, z: t.location.z }), () => {
      if (!valid(t)) return;
      shake(p, 0.18, 0.25);
      rockBurst(t.dimension, t.location, 4, 1);
      waveFx(t.dimension, t.location, 3, 0, 8);
      const n = numberOf(t);
      if (n === undefined || n <= 5) collapse(t, p);
      else { decNum(t, 5, p); hurt(t, 4, p); }
    });
    return true;
  },

  // ── كاتب القوانين ──
  reflect(p) {
    const z = startZone(p, "reflect", 5, 140);
    sfx(p.dimension, "sh.reflect", p.location, 1.1);
    // 3 مرايا تدور حولك طول مدة القانون
    const mirrors = [0, 1, 2].map(() => shapeFx(p.dimension, "mirror", p.location, { r: 1.1, life: 144 })).filter(Boolean);
    z.shapes.push(...mirrors);
    let t = 0;
    z.orbit = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p)) return;
        mirrors.forEach((m, i) => {
          const a = t * 0.09 + (i * Math.PI * 2) / 3;
          const pos = { x: p.location.x + Math.cos(a) * 1.7, y: p.location.y + 1.1, z: p.location.z + Math.sin(a) * 1.7 };
          moveShape(m, pos, dirYaw({ x: Math.cos(a), y: 0, z: Math.sin(a) }));
        });
      } catch (err) { /* */ }
    }, 2);
    return true;
  },
  boundary(p) {
    const z = startZone(p, "boundary", 7, 160);
    sfx(p.dimension, "sh.boundary", p.location, 1.2);
    shake(p, 0.12, 0.2);
    // 8 أعمدة رونية تطلع من الأرض حول الدائرة
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      const pos = { x: z.c.x + Math.cos(a) * 6.6, y: z.c.y, z: z.c.z + Math.sin(a) * 6.6 };
      const e = shapeFx(p.dimension, "rune_pillar", { ...pos, y: pos.y - 2.6 }, { r: 1.0, yaw: i * 45, life: 162 });
      if (e) { z.shapes.push(e); tween(10, 1, (k) => moveShape(e, { ...pos, y: pos.y - 2.6 * (1 - k) })); }
    }
    rockBurst(p.dimension, p.location, 3, 0.8);
    return true;
  },
  async absolute(p) {
    const laws = [
      ["§aNobody is hurt but me", "Full immunity"],
      ["§cEveryone is heavy", "All enemies around you slow down and weaken"],
      ["§6Royal Strike", "Your damage is doubled"],
    ];
    const f = new ActionFormData().title("Absolute Law").body("§7Write your law. It lasts 5 seconds.");
    for (const l of laws) f.button(`${l[0]}\n§7${l[1]}`);
    const r = await showForm(p, f);
    if (r.canceled) return false;
    const dim = p.dimension, d = flatDir(p);
    spawnFx(dim, "circle", p.location, 0, 4, 106);
    // مطرقة القاضي العملاقة تنزل قدامك وتختم القانون
    const at = { x: p.location.x + d.x * 2.6, y: p.location.y, z: p.location.z + d.z * 2.6 };
    const back = { x: p.location.x - d.x * 0.8, y: p.location.y, z: p.location.z - d.z * 0.8 };
    const g = shapeFx(dim, "gavel", back, { r: 2.0, yaw: dirYaw({ x: d.x, y: 0, z: d.z }), p: -35, life: 40 });
    sfx(dim, "sh.absolute", p.location, 1.3);
    tween(7, 1, (k) => setShape(g, "sh:p", -35 + 120 * k * k), () => {
      sfx(dim, "sh.guard_slam", at, 1.3, 0.8);
      shake(p, 0.25, 0.4);
      waveFx(dim, at, 7, 0, 12);
      rockBurst(dim, at, 5, 1.1);
      popShape(dim, "echo_glyph", { x: at.x, y: at.y + 0.2, z: at.z }, 1, 3, 10, { p: 90, s: 200 });
    });
    try {
      if (r.selection === 0) {
        p.addEffect("resistance", 100, { amplifier: 4, showParticles: false });
      } else if (r.selection === 1) {
        for (const e of enemiesNear(dim, p.location, 14, p.id)) {
          e.addEffect("slowness", 100, { amplifier: 4, showParticles: false });
          e.addEffect("weakness", 100, { amplifier: 2, showParticles: false });
          followShape(e, "weight", 100, { r: 0.35, dy: 0.5 });
        }
      } else {
        p.addEffect("strength", 100, { amplifier: 2, showParticles: false });
      }
    } catch (e) { /* */ }
    notify(p, `${laws[r.selection][0]}§r: 5 seconds`, 100);
    return true;
  },

  // ── محرف المسافة ──
  pull(p) {
    const t = raycastTarget(p, 32);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    const d = flatDir(p), dim = p.dimension;
    const from = { ...t.location };
    // سهم أزرق يطلع من الهدف باتجاهك، والهدف ينسحب من بوابة لبوابة
    popShape(dim, "arrow_blue", { x: from.x, y: from.y + 1.2, z: from.z }, 0.6, 1.4, 6, { yaw: yawOf(from, p.location) });
    portalFx(dim, from, 2, 1.4, from, p.location);
    const dest = { x: p.location.x + d.x * 2.2, y: p.location.y, z: p.location.z + d.z * 2.2 };
    later(4, () => {
      if (!valid(t)) return;
      if (!safeTeleport(t, dest)) {
        const dx = p.location.x - t.location.x, dz = p.location.z - t.location.z, l = Math.hypot(dx, dz) || 1;
        try { t.applyKnockback({ x: (dx / l) * 3, z: (dz / l) * 3 }, 0.3); } catch (e) { /* */ }
      }
      portalFx(dim, dest, 2, 1.2, from, p.location);
      popShape(dim, "space_cube", { x: t.location.x, y: t.location.y + 1, z: t.location.z }, 1.0, 0.1, 8, { s: 600 });
      try { t.addEffect("slowness", 30, { amplifier: 2, showParticles: false }); } catch (e) { /* */ }
    });
    sfx(dim, "sh.pull", p.location);
    shake(p, 0.06, 0.1);
    return true;
  },
  push(p) {
    const t = raycastTarget(p, 24);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    sfx(p.dimension, "sh.push", p.location);
    shake(p, 0.08, 0.12);
    portalFx(p.dimension, { x: p.location.x, y: p.location.y, z: p.location.z }, 2, 1.2, p.location, t.location);
    symbolShot(p, t, "arrow_blue", () => {
      if (!valid(t)) return;
      pushAway(p.location, t, 6, 0.6);
      hurt(t, 3, p);
      popShape(t.dimension, "sound_ring", headPos(t), 0.4, 1.8, 6, { yaw: yawOf(p.location, t.location) });
      burst(t.dimension, headPos(t), 10, COLORS.white, 3);
    }, 1.6);
    return true;
  },
  swap(p) {
    const t = raycastTarget(p, 30);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    const a = { ...p.location }, b = { ...t.location };
    try { p.teleport(b, { facingLocation: a }); t.teleport(a); } catch (e) { return false; }
    portalFx(p.dimension, a, 2, 1.4, a, b); portalFx(p.dimension, b, 2, 1.4, a, b);
    for (const q of [a, b]) popShape(p.dimension, "space_cube", { x: q.x, y: q.y + 1, z: q.z }, 1.4, 0.2, 10, { s: -500 });
    shapeFx(p.dimension, "arrow_blue", { x: a.x, y: a.y + 2.2, z: a.z }, { r: 1, yaw: yawOf(a, b), life: 10 });
    shapeFx(p.dimension, "arrow_blue", { x: b.x, y: b.y + 2.2, z: b.z }, { r: 1, yaw: yawOf(b, a), life: 10 });
    try { t.addEffect("nausea", 60, { amplifier: 0, showParticles: false }); t.addEffect("slowness", 30, { amplifier: 1, showParticles: false }); } catch (e) { /* */ }
    sfx(p.dimension, "sh.swap", p.location);
    return true;
  },
  fold(p) {
    const t = raycastTarget(p, 40);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    const dx = t.location.x - p.location.x, dz = t.location.z - p.location.z, l = Math.hypot(dx, dz) || 1;
    const start = { ...p.location };
    const dest = { x: t.location.x - (dx / l) * 1.8, y: t.location.y, z: t.location.z - (dz / l) * 1.8 };
    // المكان ينطوي: مكعب يتقلص مكانك ويتوسع جنب الهدف
    popShape(p.dimension, "space_cube", { x: start.x, y: start.y + 1, z: start.z }, 1.6, 0.1, 6, { s: 900 });
    portalFx(p.dimension, start, 2, 1.5, start, t.location, 20);
    safeTeleport(p, dest, t.location);
    portalFx(p.dimension, dest, 2, 1.5, start, t.location, 20);
    popShape(p.dimension, "space_cube", headPos(t), 0.2, 1.8, 6, { s: -900 });
    hurt(t, 9, p);
    pushAway(p.location, t, 1.2, 0.3);
    burst(t.dimension, headPos(t), 14, COLORS.blue, 3.5, 0.24);
    sfx(p.dimension, "sh.fold", t.location, 1.1);
    shake(p, 0.15, 0.15);
    return true;
  },
  spacecollapse(p) {
    const list = enemiesNear(p.dimension, p.location, 12, p.id);
    if (list.length === 0) { notify(p, "§cNo enemies nearby", 40); return false; }
    const d = flatDir(p), dim = p.dimension;
    const c = { x: p.location.x + d.x * 5, y: p.location.y, z: p.location.z + d.z * 5 };
    portalFx(dim, c, 2, 3.2, p.location, c, 50);
    sfx(dim, "sh.spacecollapse", p.location, 1.3);
    shake(p, 0.25, 0.5);
    // مكعب فضاء ضخم ينطوي على نفسه ويسحب الأعداء لنقطة وحدة
    popShape(dim, "space_cube", { x: c.x, y: c.y + 1.5, z: c.z }, 4.5, 0.3, 16, { s: 500, ease: "out" });
    for (const e of list) {
      const dest = { x: c.x + (Math.random() - 0.5) * 2.4, y: c.y, z: c.z + (Math.random() - 0.5) * 2.4 };
      safeTeleport(e, dest);
      hurt(e, 5, p);
    }
    later(16, () => {
      popShape(dim, "nova", { x: c.x, y: c.y + 1.2, z: c.z }, 0.3, 2.2, 8, { s: 300 });
      burst(dim, c, 20, COLORS.white, 4, 0.3);
      for (const e of enemiesNear(dim, c, 4, p.id)) hurt(e, 6, p);
      rockBurst(dim, c, 5, 1.2);
    });
    return true;
  },

  // ── ناسج الصدى ──
  echostrike(p) {
    echoReady.set(p.id, { until: system.currentTick + 160 });
    sfx(p.dimension, "sh.echostrike", p.location);
    popShape(p.dimension, "sound_ring", { x: p.location.x, y: p.location.y + 0.2, z: p.location.z }, 0.6, 2.4, 10, { p: 90 });
    followShape(p, "echo_glyph", 160, { r: 0.45, s: 220, feet: true, dy: 2.4 });
    notify(p, "§3Your next hit will echo", 50);
    return true;
  },
  echoseal(p) {
    const t = raycastTarget(p, 24);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    echoMarks.set(t.id, { sum: 0 });
    followShape(t, "echo_glyph", 100, { r: 0.9, s: 160, dy: 0.9 });
    symbolShot(p, t, "sound_ring", undefined, 1.4);
    sfx(p.dimension, "sh.echoseal", p.location);
    system.runTimeout(() => {
      const m = echoMarks.get(t.id);
      echoMarks.delete(t.id);
      if (!m || !valid(t)) return;
      hurt(t, Math.max(4, m.sum), p);
      for (const [pp, yy] of [[0, 0], [0, 90], [90, 0]]) popShape(t.dimension, "sound_ring", center3(t), 0.5, 3.0, 9, { p: pp, yaw: yy });
      burst(t.dimension, headPos(t), 16, POWER_COLOR.echo, 4, 0.26);
      sfx(t.dimension, "sh.echoseal", t.location, 1.2, 0.7);
    }, 100);
    return true;
  },
  sonar(p) {
    sfx(p.dimension, "sh.sonar", p.location, 1.2);
    for (let k = 0; k < 3; k++) system.runTimeout(() => { if (valid(p)) waveFx(p.dimension, p.location, 22, 3, 24); }, k * 12);
    for (let k = 0; k < 6; k++) {
      system.runTimeout(() => {
        if (!valid(p)) return;
        ring(p.dimension, p.location, 3.3 * (k + 1), 36, k, POWER_COLOR.echo, 0.2);
        for (const e of enemiesNear(p.dimension, p.location, 22, p.id)) {
          for (let h = 0; h < 5; h++) glow(e.dimension, { x: e.location.x, y: e.location.y + 0.4 + h * 0.5, z: e.location.z }, { color: POWER_COLOR.echo, size: 0.28, life: 0.7, rise: 0.4 });
        }
      }, k * 10);
    }
    return true;
  },
  echowave(p) {
    const d = flatDir(p), c = { ...p.location }, dim = p.dimension;
    const wave = (dmg, rmax, pitch) => {
      sfx(dim, "sh.echowave", c, 1, pitch);
      shake(p, 0.12, 0.15);
      // حلقة صوت عملاقة تطير قدامك وتكبر
      const from = { x: c.x + d.x * 1.2, y: c.y + 1.1, z: c.z + d.z * 1.2 };
      const e = flyShape(dim, "sound_ring", from, { x: d.x, y: 0, z: d.z }, 0.9, rmax, { r: 0.8 });
      tween(Math.ceil(rmax / 0.9), 1, (k) => setShape(e, "sh:r", 0.8 + k * 3.2));
      for (const e2 of enemiesNear(dim, c, rmax, p.id)) {
        const vx = e2.location.x - c.x, vz = e2.location.z - c.z, l = Math.hypot(vx, vz) || 1;
        if ((vx / l) * d.x + (vz / l) * d.z < 0.64) continue;
        later(Math.ceil(l / 0.9), () => {
          if (!valid(e2)) return;
          hurt(e2, dmg, p);
          pushAway(c, e2, 1.6, 0.35);
          burst(dim, headPos(e2), 8, POWER_COLOR.echo, 2.5);
        });
      }
    };
    wave(7, 12, 1);
    later(10, () => { if (valid(p)) wave(4, 14, 0.8); });
    return true;
  },
  chorus(p) {
    const radii = [6, 9, 12], dmgs = [8, 10, 12];
    sfx(p.dimension, "sh.chorus", p.location, 1.4);
    radii.forEach((r, i) => {
      system.runTimeout(() => {
        if (!valid(p)) return;
        shake(p, 0.2, 0.3);
        sfx(p.dimension, "sh.chorus", p.location, 1.1, 1 + i * 0.15);
        // حلقة صوت أرضية تتوسع لحد نصف القطر
        popShape(p.dimension, "sound_ring", { x: p.location.x, y: p.location.y + 0.4 + i * 0.4, z: p.location.z }, 1, r / 0.9, 12, { p: 90, ease: "out" });
        for (const e of enemiesNear(p.dimension, p.location, r, p.id)) {
          hurt(e, dmgs[i], p);
          pushAway(p.location, e, 1.4, 0.3);
          burst(e.dimension, headPos(e), 6, POWER_COLOR.echo, 3);
        }
      }, i * 20);
    });
    return true;
  },
});

Object.assign(SKILL_FN, {
  // ── جسد الحديد ──
  ironskin(p) {
    try { p.addEffect("resistance", 120, { amplifier: 2, showParticles: false }); p.addEffect("slowness", 120, { amplifier: 0, showParticles: false }); } catch (e) { return false; }
    sfx(p.dimension, "sh.guard_slam", p.location, 0.8, 1.4);
    bodyShell(p, 0, 120);
    rockBurst(p.dimension, p.location, 3, 0.7);
    notify(p, "§7Your body turned to iron: high resistance for 6 seconds", 60);
    return true;
  },
  ironfist(p) {
    const t = raycastTarget(p, 10);
    if (!t) { notify(p, "§cNo enemy in front of you (10 blocks)", 30); return false; }
    // قبضة حديد عملاقة تنطلق من صدرك وتسحق الهدف
    const from = { x: p.location.x, y: p.location.y + 1.2, z: p.location.z }, to = center3(t);
    const dx = to.x - from.x, dy = to.y - from.y, dz = to.z - from.z, l = Math.hypot(dx, dy, dz) || 1;
    const d = { x: dx / l, y: dy / l, z: dz / l };
    sfx(p.dimension, "sh.push", p.location, 1, 0.6);
    flyShape(p.dimension, "iron_fist", { x: from.x + d.x * 0.8, y: from.y + d.y * 0.8, z: from.z + d.z * 0.8 }, d, 1.3, Math.max(1, l - 0.9), { r: 1.5 }, undefined, () => {
      if (!valid(t)) return;
      hurt(t, 10, p);
      pushAway(p.location, t, 2.8, 0.5);
      waveFx(t.dimension, t.location, 3, 4, 8);
      groundBreak(t.dimension, t.location, 3, { cracks: 6, ttl: 160 });
      popShape(t.dimension, "iron_fist", center3(t), 1.5, 2.2, 4, { yaw: dirYaw(d) });
      sfx(p.dimension, "sh.cleaver_hit", t.location, 1.1, 0.7);
      shake(p, 0.2, 0.2);
    });
    return true;
  },
  // ── متتبع الريح ──
  windrun(p) {
    try { p.addEffect("speed", 100, { amplifier: 2, showParticles: false }); } catch (e) { return false; }
    sfx(p.dimension, "sh.push", p.location, 0.8, 1.5);
    // إعصار صغير يلف حول رجليك، وشفرات ريح تتخلف وراك وانت تركض
    followShape(p, "tornado", 100, { r: 0.45, s: 900, feet: true, dy: 0 });
    popShape(p.dimension, "wind_crescent", { x: p.location.x, y: p.location.y + 0.3, z: p.location.z }, 0.6, 2.2, 8, { p: 0, s: 600 });
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 6;
        if (!valid(p) || t > 100) { system.clearRun(h); return; }
        const d = flatDir(p), v = p.getVelocity();
        if (Math.hypot(v.x, v.z) < 0.05) return;
        popShape(p.dimension, "wind_crescent", { x: p.location.x - d.x * 1.2, y: p.location.y + 0.8, z: p.location.z - d.z * 1.2 }, 1.0, 0.3, 10, { yaw: dirYaw({ ...d, y: 0 }) });
      } catch (e) { system.clearRun(h); }
    }, 6);
    return true;
  },
  windleap(p) {
    const d = flatDir(p);
    try {
      p.applyKnockback({ x: d.x * 2.6, z: d.z * 2.6 }, 0.9);
      p.addEffect("slow_falling", 80, { amplifier: 0, showParticles: false });
    } catch (e) { return false; }
    popShape(p.dimension, "wind_crescent", { x: p.location.x, y: p.location.y + 0.2, z: p.location.z }, 0.8, 2.4, 8, { yaw: dirYaw({ x: d.x, y: 0, z: d.z }) + 180 });
    wingsOn(p, 40);
    sfx(p.dimension, "sh.push", p.location, 1, 1.3);
    return true;
  },
  gale(p) {
    const dim = p.dimension;
    const list = enemiesNear(dim, p.location, 7, p.id);
    popShape(dim, "tornado", p.location, 0.8, 1.9, 14, { s: 1100 });
    // 8 شفرات ريح تطير للخارج من حولك
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2, d = { x: Math.cos(a), y: 0, z: Math.sin(a) };
      flyShape(dim, "wind_crescent", { x: p.location.x + d.x, y: p.location.y + 1, z: p.location.z + d.z }, d, 0.7, 7, { r: 1.1 });
    }
    for (const e of list) {
      hurt(e, 3, p);
      pushAway(p.location, e, 2.6, 0.55);
    }
    sfx(dim, "sh.push", p.location, 1.3, 0.8);
    shake(p, 0.18, 0.3);
    return true;
  },
  // ── قانون الزمن ──
  time(p) {
    const list = enemiesNear(p.dimension, p.location, 9, p.id);
    if (list.length === 0) { notify(p, "§cNo enemies nearby", 40); return false; }
    const dim = p.dimension;
    spawnFx(dim, "circle", p.location, 0, 9, 66);
    // ساعة كبيرة فوقك عقاربها تدور، وساعة صغيرة فوق كل عدو متجمد
    shapeFx(dim, "clock", { x: p.location.x, y: p.location.y + 3.4, z: p.location.z }, { r: 2.2, s: 40, life: 62 });
    for (const e of list) {
      try {
        e.addEffect("slowness", 60, { amplifier: 9, showParticles: false });
        e.addEffect("weakness", 60, { amplifier: 3, showParticles: false });
      } catch (err) { /* */ }
      followShape(e, "clock", 60, { r: 0.6, s: 90, dy: 0.8 });
    }
    sfx(dim, "sh.weight", p.location, 1.2, 0.6);
    shake(p, 0.15, 0.3);
    return true;
  },
});

// أجنحة 3D على ظهر اللاعب ترفرف وتتبعه
function wingsOn(p, ticks) {
  const at = () => { const d = flatDir(p); return { x: p.location.x - d.x * 0.32, y: p.location.y + 1.25, z: p.location.z - d.z * 0.32 }; };
  const e = shapeFx(p.dimension, "wings", at(), { r: 1.25, life: ticks + 4 });
  if (!e) return;
  let t = 0;
  const h = system.runInterval(() => {
    try {
      t += 1;
      if (!valid(e) || !valid(p) || t > ticks) { system.clearRun(h); removeFx(e); return; }
      moveShape(e, at(), dirYaw({ ...flatDir(p), y: 0 }));
    } catch (err) { system.clearRun(h); removeFx(e); }
  }, 1);
}
// صدى الضربة: الضربة اللي بعد التفعيل تنعاد بعد ثانية
// ضعف الأسلحة الثقيلة: تبطئ حاملها
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      const held = inv(p).getItem(p.selectedSlotIndex);
      const w = held && WEAPONS[held.typeId];
      if (w && w.heavy) p.addEffect("slowness", 40, { amplifier: w.heavy - 1, showParticles: false });
    } catch (e) { /* */ }
  }
}, 20);

const comboMap = new Map();
const wHitXpAt = new Map();
const weaponCd = new Map();

// كل سلاح له مهارتين: الاستعمال = الأولى، السنيك + الاستعمال = الثانية
function frontOf(p, k) { const d = flatDir(p); return { x: p.location.x + d.x * k, y: p.location.y, z: p.location.z + d.z * k }; }
function inFront(p, e, minDot = 0.35) {
  const d = flatDir(p), vx = e.location.x - p.location.x, vz = e.location.z - p.location.z, l = Math.hypot(vx, vz) || 1;
  return (vx / l) * d.x + (vz / l) * d.z >= minDot;
}
// مكان آمن خلف الهدف (عكس جهة اللاعب)
function behindSpot(t, from) {
  const dx = t.location.x - from.x, dz = t.location.z - from.z, l = Math.hypot(dx, dz) || 1;
  const ux = dx / l, uz = dz / l;
  for (const k of [1.5, 1.1, 2.0]) {
    const dest = { x: t.location.x + ux * k, y: t.location.y, z: t.location.z + uz * k };
    try {
      const b1 = t.dimension.getBlock({ x: Math.floor(dest.x), y: Math.floor(dest.y), z: Math.floor(dest.z) });
      const b2 = t.dimension.getBlock({ x: Math.floor(dest.x), y: Math.floor(dest.y) + 1, z: Math.floor(dest.z) });
      if (b1 && b2 && b1.isAir && b2.isAir) return dest;
    } catch (e) { /* */ }
  }
  return undefined;
}
// شطرة 3D على الهدف (a = زاوية الشطرة)
function slashOn(dim, name, c, faceFrom, a, r = 1.2) {
  return popShape(dim, name, c, r * 0.6, r, 5, { yaw: yawOf(c, faceFrom), a });
}
// أرض اللاعب: أول بلوك صلب تحت (x,z) قرب الارتفاع y
function groundY(dim, x, z, y) {
  for (let k = 1; k >= -3; k--) {
    try {
      const b = dim.getBlock({ x: Math.floor(x), y: Math.floor(y) + k - 1, z: Math.floor(z) });
      const above = dim.getBlock({ x: Math.floor(x), y: Math.floor(y) + k, z: Math.floor(z) });
      if (b && !b.isAir && !b.isLiquid && above && (above.isAir || above.isLiquid || !canBreak(above) || above.typeId.includes("grass") || above.typeId.includes("flower"))) return Math.floor(y) + k - 1;
    } catch (e) { return undefined; }
  }
  return undefined;
}

// ═════════════════════════ تلفيل الأسلحة (كل الأسلحة ما عدا الكاتانا اللي إلها نظامها) ═════════════════════════
// كل سلاح يكبر لحاله: خبرة من الضرب (1 كل نص ثانية) ومن القتل وانت ماسكه. 5 ليفلات:
//  Lv1 المهارة الأولى | Lv2 تنفتح المهارة الثانية (سنيك) +10% ضرر | Lv3 +20% وتصحى الهالة
//  Lv4 +30% وتبريد المهارات أقل 20% | Lv5 (مستيقظ) +45% ضرر، المهارات أقوى 25%، هالة كاملة
const WLV_MAX = 5, WLV_NEED = [0, 30, 70, 130, 210];
const WLV_DMG = [1, 1, 1.1, 1.2, 1.3, 1.45], WLV_SKILL = [1, 1, 1.05, 1.1, 1.15, 1.4];
const WLV_PERKS = ["", "Skill 1 (use)", "Skill 2 (sneak + use) unlocks, +10% damage", "+20% damage, the weapon's aura awakens", "+30% damage, skill cooldowns 20% shorter", "AWAKENED: +45% damage, skills hit 25% harder, full aura"];
// هالة كل سلاح (مثل الصور): ذهب يلتف، لهب، ريح زرقاء، هالة خضراء، رونات حمراء، ظل بنفسجي
const WEAPON_AURA = {
  "sh:dawn_dagger": { style: "swirl", cols: [[1, 0.85, 0.35], [1, 0.95, 0.65], [1, 1, 0.9]] },
  "sh:ember_cleaver": { style: "flame", cols: [[1, 0.35, 0.08], [1, 0.62, 0.15], [1, 0.88, 0.45]] },
  "sh:silver_oath": { style: "sparkle", cols: [[1, 1, 1], [0.86, 0.9, 1], [0.95, 0.9, 0.7]] },
  "sh:shadow_blade": { style: "wind", cols: [[0.45, 0.8, 1], [0.75, 0.93, 1], [1, 1, 1]] },
  "sh:stone_maul": { style: "motes", cols: [[0.25, 0.85, 0.45], [0.55, 1, 0.65], [0.85, 1, 0.9]] },
  "sh:sunset_spear": { style: "runes", cols: [[0.95, 0.15, 0.15], [1, 0.45, 0.35], [1, 0.85, 0.8]] },
  "sh:shadow_claws": { style: "motes", cols: [[0.6, 0.4, 1], [0.8, 0.65, 1], [0.95, 0.9, 1]] },
};
function wlvAll(p) { try { const raw = p.getDynamicProperty("sh_wlv"); return typeof raw === "string" ? JSON.parse(raw) : {}; } catch (e) { return {}; } }
function getWlv(p, id) { const k = wlvAll(p)[id] || {}; return { lv: Math.min(WLV_MAX, Math.max(1, k.lv || 1)), xp: k.xp || 0 }; }
function setWlv(p, id, k) { try { const all = wlvAll(p); all[id] = k; p.setDynamicProperty("sh_wlv", JSON.stringify(all)); } catch (e) { /* */ } }
function wlvOf(p, id) { return getWlv(p, id).lv; }
function addWeaponXp(p, id, amount) {
  if (!WEAPON_SKILLS[id]) return;
  const k = getWlv(p, id);
  if (k.lv >= WLV_MAX) return;
  k.xp += amount;
  const name = (WEAPONS[id] && WEAPONS[id].name) || id;
  while (k.lv < WLV_MAX && k.xp >= WLV_NEED[k.lv]) {
    k.xp -= WLV_NEED[k.lv];
    k.lv++;
    sfxPlayer(p, k.lv >= WLV_MAX ? "sh.kat_levelup" : "sh.level_up", 1, k.lv >= WLV_MAX ? 0.9 : 1.2);
    say(p, `§e[${name}] §fLevel §e${k.lv}§f: ${WLV_PERKS[k.lv]}.`);
    notify(p, k.lv >= WLV_MAX ? `§6§l${name} AWAKENED` : `§e${name} Lv ${k.lv}`, 70);
    weaponAuraBurst(p, id, 30);
  }
  if (k.lv >= WLV_MAX) k.xp = 0;
  setWlv(p, id, k);
}
const wBoost = new Map(); // pid -> { until, mul }  مضاعف ضرر مهارة السلاح لفترة قصيرة بعد التفعيل
function weaponSkillMul(by) {
  if (!by || by.typeId !== "minecraft:player") return 1;
  const b = wBoost.get(by.id);
  return b && system.currentTick <= b.until ? b.mul : 1;
}
// نقطة الهالة: على النصل/الرأس حسب طول السلاح
function weaponAuraPoint(p, id, u) {
  if (id === "sh:shadow_claws") {
    // المخالب لابسها على الإيد: الهالة حول الكف والشفرات (جنب الجسم يمين وتحت شوية)
    const d = flatDir(p), r = katanaRight(d);
    return { x: p.location.x + r.x * 0.4 + d.x * 0.15, y: p.location.y + 0.45 + u * 0.55, z: p.location.z + r.z * 0.4 + d.z * 0.15 };
  }
  const tip = id === "sh:sunset_spear" ? 1.6 : id === "sh:stone_maul" ? 1.3 : 1.15;
  return bladePoint(p, 0.25 + u * (tip - 0.25));
}
function weaponAuraTick(p, id, lv, t, strong) {
  const a = WEAPON_AURA[id];
  if (!a) return;
  const dim = p.dimension, n = strong ? 3 : lv >= 5 ? 3 : lv >= 3 ? 2 : 1;
  for (let i = 0; i < n; i++) {
    const u = Math.random(), b = weaponAuraPoint(p, id, id === "sh:stone_maul" ? 0.85 + u * 0.15 : u);
    const col = a.cols[Math.floor(Math.random() * a.cols.length)];
    if (a.style === "swirl" || a.style === "wind") {
      const ang = t * (a.style === "wind" ? 0.9 : 0.5) + i * 2.1, r = a.style === "wind" ? 0.32 : 0.22;
      pix(dim, { x: b.x + Math.cos(ang) * r, y: b.y + (a.style === "wind" ? 0.05 : 0.1), z: b.z + Math.sin(ang) * r }, { color: col, size: 0.14, life: 0.5, speed: a.style === "wind" ? 0.9 : 0.2, rise: 0.2, eye: 0.7 });
    } else if (a.style === "flame") {
      pix(dim, { x: b.x + (Math.random() - 0.5) * 0.15, y: b.y + 0.05, z: b.z + (Math.random() - 0.5) * 0.15 }, { color: col, size: 0.17, life: 0.55, speed: 0.15, rise: 1.4, eye: 0.7 });
    } else if (a.style === "sparkle") {
      // نجيمات بيضاء: تلمع وتختفي بسرعة بأماكن عشوائية على النصل
      pix(dim, { x: b.x + (Math.random() - 0.5) * 0.3, y: b.y, z: b.z + (Math.random() - 0.5) * 0.3 }, { color: col, size: 0.12 + Math.random() * 0.06, life: 0.35, speed: 0.05, rise: 0.1, eye: 0.7 });
    } else if (a.style === "runes") {
      pix(dim, b, { color: col, size: 0.13, life: 0.7, speed: 0.1, rise: 0.3, eye: 0.7 });
    } else {
      pix(dim, { x: b.x + (Math.random() - 0.5) * 0.5, y: b.y + (Math.random() - 0.5) * 0.4, z: b.z + (Math.random() - 0.5) * 0.5 }, { color: col, size: 0.15, life: 0.8, speed: 0.15, rise: 0.5, eye: 0.7 });
    }
  }
}
function weaponAuraBurst(p, id, ticks) {
  let t = 0;
  const h = system.runInterval(() => {
    try { t += 2; if (!valid(p) || t > ticks) { system.clearRun(h); return; } weaponAuraTick(p, id, WLV_MAX, t, true); } catch (e) { system.clearRun(h); }
  }, 2);
}
// الهالة وانت ماسك السلاح: خفيفة بالبداية، تصحى بـLv3، وكاملة بـLv5
system.runInterval(() => {
  const now = system.currentTick;
  for (const p of world.getAllPlayers()) {
    try {
      const held = inv(p).getItem(p.selectedSlotIndex);
      if (!held || !WEAPON_AURA[held.typeId]) continue;
      const lv = wlvOf(p, held.typeId);
      if (lv < 3 && now % 12 !== 0) continue;
      weaponAuraTick(p, held.typeId, lv, now / 4, false);
    } catch (e) { /* */ }
  }
}, 4);

const WEAPON_SKILLS = {
  "sh:ember_cleaver": [
    { name: "Ember Arc", cd: 160, desc: "An arc of fire in front of you", fn(p) {
      const dim = p.dimension, o = p.location, d = flatDir(p);
      for (const e of enemiesNear(dim, o, 4.8, p.id)) {
        if (!inFront(p, e)) continue;
        hurt(e, 7, p);
        try { e.setOnFire(4, true); } catch (err) { /* */ }
        pushAway(o, e, 1.0, 0.3);
      }
      popShape(dim, "slash_fire", { x: o.x + d.x * 1.4, y: o.y + 1.0, z: o.z + d.z * 1.4 }, 1.0, 2.6, 6, { yaw: dirYaw({ ...d, y: 0 }), p: 90, ease: "out" });
      later(2, () => popShape(dim, "slash_fire", { x: o.x + d.x * 1.8, y: o.y + 0.6, z: o.z + d.z * 1.8 }, 0.8, 2.2, 6, { yaw: dirYaw({ ...d, y: 0 }), p: 90, a: 12, ease: "out" }));
      for (let i = 0; i < 12; i++) {
        const a = Math.atan2(d.z, d.x) - 1.0 + Math.random() * 2.0, r = 1.6 + Math.random() * 2.6;
        pix(dim, { x: o.x + Math.cos(a) * r, y: o.y + 0.8 + Math.random(), z: o.z + Math.sin(a) * r }, { color: i % 3 ? COLORS.orange : COLORS.gold, size: 0.2, life: 0.8, speed: 1.6, rise: 1.6 });
      }
      sfx(dim, "sh.cleaver_hit", o, 1.2, 0.7);
      shake(p, 0.15, 0.2);
      return true;
    } },
    { name: "Inferno Spin", cd: 240, desc: "Spin: a ring of fire hits everything around you", fn(p) {
      const dim = p.dimension;
      effect(p, "resistance", 20, 1);
      const r1 = shapeFx(dim, "slash_fire", { x: p.location.x, y: p.location.y + 1.0, z: p.location.z }, { r: 2.6, p: 90, s: 1500, life: 14 });
      const r2 = shapeFx(dim, "slash_fire", { x: p.location.x, y: p.location.y + 0.5, z: p.location.z }, { r: 2.2, p: 90, s: -1300, yaw: 180, life: 14 });
      tween(12, 1, () => { moveShape(r1, { x: p.location.x, y: p.location.y + 1.0, z: p.location.z }); moveShape(r2, { x: p.location.x, y: p.location.y + 0.5, z: p.location.z }); });
      for (const k of [0, 6]) later(k, () => {
        if (!valid(p)) return;
        sfx(dim, "sh.cleaver_hit", p.location, 1.1, 0.8 + k * 0.05);
        for (const e of enemiesNear(dim, p.location, 5.2, p.id)) {
          hurt(e, 6, p);
          try { e.setOnFire(5, true); } catch (err) { /* */ }
          pushAway(p.location, e, 1.3, 0.35);
        }
      });
      shake(p, 0.18, 0.3);
      return true;
    } },
  ],
  "sh:dawn_dagger": [
    { name: "Sun Bind", cd: 140, desc: "Binds the enemy you look at with chains of light", fn(p) {
      const t = katanaTarget(p, 10);
      if (!t) { notify(p, "§7No enemy where you look", 20); return false; }
      hurt(t, 3, p);
      effect(t, "slowness", 100, 2);
      effect(t, "weakness", 100, 0);
      symbolShot(p, t, "arrow_gold", undefined, 1.6);
      // 3 سلاسل ضوء تلف حول العدو بعكس بعض
      [[0.3, 260], [1.0, -320], [1.7, 240]].forEach(([dy, sp]) => followShape(t, "sun_chain", 100, { r: 0.9, s: sp, feet: true, dy }));
      sfx(p.dimension, "sh.dagger_hit", p.location, 1, 1.5);
      return true;
    } },
    { name: "Radiant Flurry", cd: 200, desc: "Six rapid stabs on the enemy in front, the last is a Dawn Strike", fn(p) {
      const t = katanaTarget(p, 6);
      if (!t) { notify(p, "§7No enemy in front of you", 20); return false; }
      if (dist2d(p.location, t.location) > 2.6) {
        const dx = t.location.x - p.location.x, dz = t.location.z - p.location.z, l = Math.hypot(dx, dz) || 1;
        safeTeleport(p, { x: t.location.x - (dx / l) * 1.5, y: t.location.y, z: t.location.z - (dz / l) * 1.5 }, t.location);
      }
      for (let i = 0; i < 6; i++) later(i * 3, () => {
        if (!valid(t) || !valid(p)) return;
        const last = i === 5;
        hurt(t, last ? 9 : 3, p);
        slashOn(t.dimension, "slash_gold", center3(t), p.location, Math.random() * 360, last ? 1.6 : 0.8);
        sfx(t.dimension, "sh.dagger_hit", t.location, 1, 1.2 + i * 0.08);
        if (last) { popShape(t.dimension, "star5", center3(t), 0.4, 1.6, 7, { yaw: yawOf(t.location, p.location), w: 400 }); shake(p, 0.15, 0.15); }
      });
      return true;
    } },
  ],
  "sh:silver_oath": [
    { name: "Oath Cleave", cd: 140, desc: "A wide silver crescent in front of you that pushes enemies back", fn(p) {
      const dim = p.dimension, o = p.location, d = flatDir(p);
      const c = { x: o.x + d.x * 1.6, y: o.y + 1.0, z: o.z + d.z * 1.6 };
      popShape(dim, "slash_silver", c, 1.0, 2.8, 6, { yaw: dirYaw({ ...d, y: 0 }), p: 90, ease: "out" });
      later(2, () => popShape(dim, "slash_silver", { x: c.x + d.x * 0.6, y: c.y - 0.2, z: c.z + d.z * 0.6 }, 0.8, 2.4, 6, { yaw: dirYaw({ ...d, y: 0 }), p: 90, a: 14, ease: "out" }));
      let n = 0;
      for (const e of enemiesNear(dim, o, 5, p.id)) {
        if (!inFront(p, e, 0.2)) continue;
        hurt(e, 9, p); n++;
        pushAway(o, e, 1.3, 0.35);
        effect(e, "weakness", 60, 0);
        for (let i = 0; i < 4; i++) pix(dim, { x: e.location.x + (Math.random() - 0.5), y: e.location.y + 0.6 + Math.random(), z: e.location.z + (Math.random() - 0.5) }, { color: COLORS.white, size: 0.18, life: 0.5, speed: 1.2 });
      }
      for (let i = 0; i < 14; i++) {
        const a = Math.atan2(d.z, d.x) - 1.1 + (i / 13) * 2.2, r = 2.2 + Math.random() * 2;
        pix(dim, { x: o.x + Math.cos(a) * r, y: o.y + 1 + Math.random() * 0.6, z: o.z + Math.sin(a) * r }, { color: i % 3 ? COLORS.white : [0.95, 0.9, 0.7], size: 0.16, life: 0.6, speed: 0.6, rise: 0.4 });
      }
      sfx(dim, "sh.kat_wave", o, 1.0, 1.4);
      shake(p, 0.08, 0.15);
      return true;
    } },
    { name: "Silver Step", cd: 200, desc: "Dash 6 blocks forward through enemies, cutting each one you pass", fn(p) {
      const dim = p.dimension, d = flatDir(p), from = { ...p.location };
      let to = { ...from };
      for (let k = 1; k <= 6; k++) {
        const q = { x: from.x + d.x * k, y: from.y, z: from.z + d.z * k };
        try {
          const b1 = dim.getBlock({ x: Math.floor(q.x), y: Math.floor(q.y), z: Math.floor(q.z) });
          const b2 = dim.getBlock({ x: Math.floor(q.x), y: Math.floor(q.y) + 1, z: Math.floor(q.z) });
          if (!b1 || !b2 || !b1.isAir || !b2.isAir) break;
        } catch (e) { break; }
        to = q;
      }
      if (Math.hypot(to.x - from.x, to.z - from.z) < 1) { notify(p, "§7No room to dash", 20); return false; }
      shapeFx(dim, "afterimage", from, { r: 1.0, yaw: dirYaw({ ...d, y: 0 }), life: 14 });
      safeTeleport(p, to, { x: to.x + d.x, y: to.y, z: to.z + d.z });
      const len = Math.hypot(to.x - from.x, to.z - from.z), hit = new Set();
      for (let i = 0; i <= 10; i++) {
        const t = i / 10, pt = { x: from.x + (to.x - from.x) * t, y: from.y + 1, z: from.z + (to.z - from.z) * t };
        pix(dim, pt, { color: i % 2 ? COLORS.white : [0.86, 0.9, 1], size: 0.18, life: 0.7, speed: 0.3, rise: 0.3 });
        for (const e of enemiesNear(dim, pt, 1.6, p.id)) {
          if (hit.has(e.id)) continue;
          hit.add(e.id);
          later(2 + hit.size * 2, () => {
            if (!valid(e)) return;
            hurt(e, 8, p);
            slashOn(dim, "slash_silver", center3(e), from, hit.size % 2 ? 35 : -35, 1.1);
            effect(e, "slowness", 40, 1);
            sfx(dim, "sh.dagger_hit", e.location, 1, 1.4);
          });
        }
      }
      sfx(dim, "sh.kat_step", to, 1.1, 1.3);
      effect(p, "resistance", 20, 1);
      if (!hit.size) notify(p, `§7Silver Step: ${len.toFixed(0)} blocks`, 15);
      return true;
    } },
  ],
  "sh:shadow_blade": [
    { name: "Shadow Ambush", cd: 120, desc: "Appear behind the enemy you look at and stab it twice", fn(p) {
      const t = katanaTarget(p, 16);
      if (!t) { notify(p, "§7No enemy where you look", 20); return false; }
      const dest = behindSpot(t, p.location);
      if (!dest) { notify(p, "§7No room behind the enemy", 20); return false; }
      const dim = p.dimension, from = { ...p.location };
      shapeFx(dim, "afterimage", from, { r: 1.0, yaw: dirYaw({ ...flatDir(p), y: 0 }), life: 16 });
      safeTeleport(p, dest, t.location);
      sfx(dim, "sh.kat_step", dest, 1.1, 1.1);
      later(1, () => {
        if (!valid(t)) return;
        hurt(t, 8, p);
        slashOn(dim, "slash_violet", center3(t), p.location, 45, 1.1);
        effect(t, "blindness", 40, 0);
        effect(t, "slowness", 40, 1);
      });
      later(5, () => {
        if (!valid(t)) return;
        hurt(t, 6, p);
        slashOn(dim, "slash_violet", center3(t), p.location, -45, 1.1);
        sfx(dim, "sh.dagger_hit", t.location, 1, 1.3);
      });
      effect(p, "resistance", 20, 2);
      return true;
    } },
    { name: "Phantom Strike", cd: 240, desc: "Shadows of you appear behind up to 4 nearby enemies and slash them", fn(p) {
      const dim = p.dimension;
      const list = enemiesNear(dim, p.location, 9, p.id).slice(0, 4);
      if (!list.length) { notify(p, "§7No enemies nearby", 20); return false; }
      sfx(dim, "sh.kat_step", p.location, 1.2, 0.8);
      list.forEach((e, i) => later(i * 4, () => {
        if (!valid(e)) return;
        const spot = behindSpot(e, p.location) || e.location;
        shapeFx(dim, "afterimage", spot, { r: 1.0, yaw: yawOf(spot, e.location), life: 12 });
        hurt(e, 7, p);
        effect(e, "weakness", 60, 0);
        slashOn(dim, "slash_violet", center3(e), spot, i % 2 ? 40 : -40, 1.1);
        sfx(dim, "sh.dagger_hit", e.location, 1, 1.0 + i * 0.1);
      }));
      return true;
    } },
  ],
  "sh:shadow_claws": [
    { name: "Rending Pounce", cd: 120, desc: "Leap onto the enemy: three rakes that make it bleed and heal you", fn(p) {
      const t = katanaTarget(p, 12);
      if (!t) { notify(p, "§7No enemy where you look", 20); return false; }
      const dim = p.dimension;
      const dx = t.location.x - p.location.x, dz = t.location.z - p.location.z, l = Math.hypot(dx, dz) || 1;
      if (l > 2.2) safeTeleport(p, { x: t.location.x - (dx / l) * 1.3, y: t.location.y, z: t.location.z - (dz / l) * 1.3 }, t.location);
      sfx(dim, "sh.trait_fangs", p.location, 1, 1.2);
      [[1, 4, -25], [4, 4, 25], [8, 7, 0]].forEach(([tk, dmg, a]) => later(tk, () => {
        if (!valid(t) || !valid(p)) return;
        hurt(t, dmg, p);
        popShape(dim, "claw_marks", center3(t), 0.7, 1.3, 5, { yaw: yawOf(t.location, p.location), a });
        effect(t, "poison", 60, 1);
        try { const hp = p.getComponent("minecraft:health"); hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + 1)); } catch (err) { /* */ }
        sfx(dim, "sh.dagger_hit", t.location, 1, 0.8 + tk * 0.04);
      }));
      return true;
    } },
    { name: "Claw Storm", cd: 220, desc: "Three waves of claws rip every enemy around you", fn(p) {
      const dim = p.dimension;
      for (let w = 0; w < 3; w++) later(w * 6, () => {
        if (!valid(p)) return;
        for (let i = 0; i < 4; i++) {
          const a = (i * 90 + w * 30) * Math.PI / 180;
          const c = { x: p.location.x + Math.cos(a) * 1.7, y: p.location.y + 1.0, z: p.location.z + Math.sin(a) * 1.7 };
          popShape(dim, "claw_marks", c, 0.6, 1.2, 5, { yaw: dirYaw({ x: Math.cos(a), y: 0, z: Math.sin(a) }), a: w * 20 - 20 });
        }
        for (const e of enemiesNear(dim, p.location, 4.5, p.id)) { hurt(e, 5, p); effect(e, "poison", 40, 0); pullTo(p.location, e, 0.25, 0.05); }
        sfx(dim, "sh.dagger_hit", p.location, 1, 0.9 + w * 0.15);
      });
      return true;
    } },
  ],
  "sh:stone_maul": [
    { name: "Earthbreaker", cd: 120, desc: "Smash a real crater in front of you; the broken blocks drop for you", fn(p) {
      const dim = p.dimension, c = frontOf(p, 2.4);
      const gy = groundY(dim, c.x, c.z, p.location.y);
      if (gy === undefined) { notify(p, "§7No ground to smash", 20); return false; }
      const list = [];
      for (let dx = -3; dx <= 3; dx++) for (let dz = -3; dz <= 3; dz++) {
        const x = Math.floor(c.x) + dx, z = Math.floor(c.z) + dz, dd = Math.hypot(dx, dz);
        if (dd > 2.4 || Math.hypot(x + 0.5 - p.location.x, z + 0.5 - p.location.z) < 1.1) continue;
        list.push({ x, y: gy + 1, z, d: dd }, { x, y: gy, z, d: dd });
        if (dd < 1.5) list.push({ x, y: gy - 1, z, d: dd });
      }
      list.sort((a, b) => a.d - b.d);
      const n = breakBlocks(dim, list, 32);
      const cc = { x: c.x, y: gy + 1, z: c.z };
      rockBurst(dim, cc, 6, 1.4);
      waveFx(dim, cc, 4, 5, 10);
      for (const e of enemiesNear(dim, cc, 3.4, p.id)) {
        hurt(e, 10, p);
        try { e.applyKnockback({ x: 0, z: 0 }, 0.85); } catch (err) { /* */ }
        effect(e, "slowness", 40, 2);
      }
      sfx(dim, "sh.guard_slam", cc, 1.4, 0.8);
      shake(p, 0.35, 0.35);
      if (n) notify(p, `§2${n} blocks broken`, 25);
      return true;
    } },
    { name: "Seismic Fissure", cd: 200, desc: "A fissure tears the ground forward for 10 blocks", fn(p) {
      const dim = p.dimension, d = flatDir(p), o = { ...p.location };
      const hit = new Set();
      let budget = 26;
      sfx(dim, "sh.guard_slam", o, 1.2, 0.6);
      shake(p, 0.25, 0.5);
      for (let t = 2; t <= 11; t++) later((t - 2) * 2, () => {
        const x = o.x + d.x * t, z = o.z + d.z * t;
        const gy = groundY(dim, x, z, o.y);
        if (gy === undefined) return;
        const side = { x: -d.z, z: d.x };
        const cells = [{ x: Math.floor(x), y: gy + 1, z: Math.floor(z) }, { x: Math.floor(x), y: gy, z: Math.floor(z) }];
        if (t % 2 === 0) cells.push({ x: Math.floor(x + side.x), y: gy, z: Math.floor(z + side.z) });
        const n = breakBlocks(dim, cells, Math.max(0, budget));
        budget -= n;
        const c = { x, y: gy + 1, z };
        fling(dim, "rock_chunk", c, 2, 1.1);
        for (const e of enemiesNear(dim, c, 1.8, p.id)) {
          if (hit.has(e.id)) continue;
          hit.add(e.id);
          hurt(e, 8, p);
          try { e.applyKnockback({ x: 0, z: 0 }, 0.9); } catch (err) { /* */ }
        }
        sfx(dim, "sh.cleaver_hit", c, 0.7, 0.6);
      });
      return true;
    } },
  ],
  "sh:sunset_spear": [
    { name: "Sunset Throw", cd: 100, desc: "Throw the spear; it hits on the way out and back and returns to you", fn(p) {
      const dim = p.dimension, v = viewDir(p);
      const pos = { x: p.location.x, y: p.location.y + 1.4, z: p.location.z };
      let dist = 0, out = true;
      const hit = new Set();
      const spear = shapeFx(dim, "spear_proj", pos, { r: 1.3, yaw: dirYaw(v), p: dirPitch(v), w: 700, life: 80 });
      const h = system.runInterval(() => {
        try {
          const step = 1.5;
          let dir = v;
          if (out) {
            pos.x += v.x * step; pos.y += v.y * step; pos.z += v.z * step; dist += step;
            const b = dim.getBlock({ x: Math.floor(pos.x), y: Math.floor(pos.y), z: Math.floor(pos.z) });
            if (dist >= 16 || !b || !b.isAir) { out = false; hit.clear(); }
          } else {
            const tx = p.location.x, ty = p.location.y + 1.2, tz = p.location.z;
            const dx = tx - pos.x, dy = ty - pos.y, dz = tz - pos.z, l = Math.hypot(dx, dy, dz) || 1;
            if (l < 1.6 || !valid(p)) { sfxPlayer(p, "sh.select", 0.6, 1.6); system.clearRun(h); removeFx(spear); return; }
            dir = { x: dx / l, y: dy / l, z: dz / l };
            const k = Math.min(step * 1.3, l);
            pos.x += dir.x * k; pos.y += dir.y * k; pos.z += dir.z * k;
          }
          moveShape(spear, pos, dirYaw(dir));
          setShape(spear, "sh:p", dirPitch(dir));
          glow(dim, pos, { color: COLORS.orange, size: 0.25, life: 0.3 });
          for (const e of enemiesNear(dim, pos, 1.5, p.id)) {
            if (hit.has(e.id)) continue;
            hit.add(e.id);
            hurt(e, out ? 8 : 5, p);
            sfx(dim, "sh.dagger_hit", e.location, 1, 0.8);
          }
        } catch (err) { system.clearRun(h); removeFx(spear); }
      }, 1);
      sfx(dim, "sh.dagger_hit", p.location, 1, 0.5);
      return true;
    } },
    { name: "Spear Rain", cd: 260, desc: "Seven burning spears rain on the spot you aim at", fn(p) {
      const dim = p.dimension, c = aimPoint(p, 24);
      spawnFx(dim, "circle", c, 5, 3.2, 30);
      flyShape(dim, "spear_proj", { x: p.location.x, y: p.location.y + 1.6, z: p.location.z }, { x: 0, y: 1, z: 0 }, 1.6, 10, { r: 1.2 });
      sfx(dim, "sh.dagger_hit", p.location, 1, 0.5);
      for (let i = 0; i < 7; i++) later(14 + i * 2, () => {
        const a = Math.random() * Math.PI * 2, r = i === 0 ? 0 : 0.8 + Math.random() * 2.2;
        const top = { x: c.x + Math.cos(a) * r, y: c.y + 12, z: c.z + Math.sin(a) * r };
        flyShape(dim, "spear_proj", top, { x: 0, y: -1, z: 0 }, 1.4, 12.5, { r: 1.2 }, undefined, (end) => {
          for (const e of enemiesNear(dim, end, 1.8, p.id)) { hurt(e, 6, p); try { e.setOnFire(3, true); } catch (err) { /* */ } }
          fling(dim, "rock_chunk", end, 1, 0.7);
          glow(dim, end, { color: COLORS.orange, size: 0.6, life: 0.4 });
          sfx(dim, "sh.dagger_hit", end, 0.9, 0.7 + Math.random() * 0.2);
        });
      });
      return true;
    } },
  ],
};
function weaponActive(p, id) {
  const list = id === KATANA ? KATANA_SKILLS : WEAPON_SKILLS[id];
  if (!list) return;
  const idx = p.isSneaking ? 1 : 0;
  const sk = list[idx];
  const key = `${p.id}:${id}:${idx}`;
  const now = system.currentTick;
  const wl = id === KATANA ? 0 : wlvOf(p, id);
  if (id !== KATANA && idx === 1 && wl < 2) { notify(p, `§7${sk.name} §cunlocks at weapon Lv 2 §8(${getWlv(p, id).xp}/${WLV_NEED[1]} XP)`, 40); return; }
  if (id !== KATANA) wBoost.set(p.id, { until: now + 80, mul: WLV_SKILL[wl] });
  const ready = weaponCd.get(key) ?? 0;
  if (now < ready) { notify(p, `§7${sk.name}: wait ${((ready - now) / 20).toFixed(1)}s`, 15); return; }
  let ok = false;
  try { ok = sk.fn(p); } catch (e) { ok = false; }
  if (ok) { const cd = typeof sk.cd === "function" ? sk.cd(p) : sk.cd; weaponCd.set(key, now + Math.round(cd * (wl >= 4 ? 0.8 : 1))); notify(p, `§f⚔ ${sk.name}`, 20); }
  else weaponCd.set(key, now + 6);
}

world.afterEvents.entityHitEntity.subscribe((ev) => {
  try {
    const p = ev.damagingEntity;
    if (!p || p.typeId !== "minecraft:player") return;
    const er = echoReady.get(p.id);
    if (!er || system.currentTick > er.until) return;
    const t = ev.hitEntity;
    if (t.typeId === "sh:trainer") return;
    echoReady.delete(p.id);
    system.runTimeout(() => {
      if (!valid(t)) return;
      hurt(t, 6, p);
      popShape(t.dimension, "sound_ring", center3(t), 0.4, 2.0, 7, { yaw: yawOf(p.location, t.location) });
      burst(t.dimension, headPos(t), 8, POWER_COLOR.echo, 3);
      sfx(t.dimension, "sh.echostrike", t.location, 1, 0.75);
    }, 20);
  } catch (e) { /* */ }
});

// ختم الصدى: يخزن الضرر
world.afterEvents.entityHurt.subscribe((ev) => {
  try {
    const m = echoMarks.get(ev.hurtEntity.id);
    if (m) m.sum += ev.damage;
  } catch (e) { /* */ }
});


// ───────────────────────── سيد البلورات + مستعير الصفات + الارتداد ─────────────────────────
const BOSS_TYPES = new Set(["minecraft:ender_dragon", "minecraft:wither", "minecraft:warden", "minecraft:elder_guardian"]);
const CRYSTAL_PINK = [1.0, 0.6, 0.85];
const crystals = new Map(); // id هدف -> { e, pid, n, until }
const MAX_CRYSTALS = 8;

function center3(e) { return { x: e.location.x, y: e.location.y + 1.0, z: e.location.z }; }
function eyePos(p) {
  try { return p.getHeadLocation(); } catch (e) { return { x: p.location.x, y: p.location.y + 1.62, z: p.location.z }; }
}
function rotY(d, deg) {
  const a = (deg * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a);
  return { x: d.x * c - d.z * s, y: d.y, z: d.x * s + d.z * c };
}
// أعداء على خط (من راس اللاعب): ترجع مرتبة بالمسافة
function rayHits(p, d, range, width) {
  const o = eyePos(p);
  const out = [];
  for (const e of enemiesNear(p.dimension, p.location, range + 3, p.id)) {
    const c = center3(e);
    const vx = c.x - o.x, vy = c.y - o.y, vz = c.z - o.z;
    const t = vx * d.x + vy * d.y + vz * d.z;
    if (t < 0.4 || t > range) continue;
    const px = vx - d.x * t, py = vy - d.y * t, pz = vz - d.z * t;
    if (Math.hypot(px, py, pz) <= width) out.push({ e, t });
  }
  out.sort((a, b) => a.t - b.t);
  return out;
}
// شظية حقيقية تطير بخط مستقيم ثم تختفي
function flyShard(p, d, len, r = 0.8, name = "crystal_spike", onEnd) {
  const o = eyePos(p);
  const from = { x: o.x + d.x * 1.2, y: o.y - 0.35 + d.y * 1.2, z: o.z + d.z * 1.2 };
  return flyShape(p.dimension, name, from, d, 2.4, Math.max(1, len - 1.2), { r, w: 540 }, undefined, onEnd);
}
function rayTrail(p, d, len, color, size = 0.24) {
  const o = eyePos(p);
  for (let t = 2.2; t <= len; t += 1.4) {
    glow(p.dimension, { x: o.x + d.x * t, y: o.y - 0.25 + d.y * t, z: o.z + d.z * t }, { color, size, life: 0.5 });
  }
}
function crystalCount(pid) {
  let n = 0;
  for (const c of crystals.values()) if (c.pid === pid) n += c.n;
  return n;
}
// بلورة حقيقية (كيان مجسم): الرأس باتجاه d
function crystalEnt(dim, loc, d, r, life, c = 0) {
  const e = spawnFx(dim, "crystal", loc, c, r, life, yawOf({ x: 0, z: 0 }, { x: d.x, z: d.z }));
  if (!e) return undefined;
  try { e.setProperty("sh:p", Math.max(-90, Math.min(90, (-Math.asin(Math.max(-1, Math.min(1, d.y))) * 180) / Math.PI))); } catch (err) { /* */ }
  return e;
}
function dropCrystal(id) {
  const c = crystals.get(id);
  if (!c) return;
  for (const f of c.fx || []) removeFx(f);
  crystals.delete(id);
}
function addCrystal(e, p, n = 1) {
  if (!valid(e)) return;
  const room = MAX_CRYSTALS - crystalCount(p.id);
  if (room <= 0) return;
  n = Math.min(n, room);
  const cur = crystals.get(e.id);
  if (cur) { cur.n = Math.min(4, cur.n + n); cur.until = system.currentTick + 300; }
  else crystals.set(e.id, { e, pid: p.id, n: Math.min(4, n), until: system.currentTick + 300, fx: [] });
  glow(e.dimension, headPos(e), { color: CRYSTAL_PINK, size: 0.3, life: 0.5 });
}
// بلورات عالقة بالهدف: تدور حول راسه وتتبعه
system.runInterval(() => {
  const now = system.currentTick;
  for (const [id, c] of [...crystals.entries()]) {
    if (!valid(c.e) || now > c.until) { dropCrystal(id); continue; }
    c.fx = c.fx.filter((f) => valid(f));
    while (c.fx.length < c.n) {
      const f = shapeFx(c.e.dimension, "crystal_gem", headPos(c.e), { r: 0.9, s: 360, life: 320 });
      if (!f) break;
      c.fx.push(f);
    }
    const h = headPos(c.e);
    c.fx.forEach((f, i) => {
      const a = now * 0.12 + (i / Math.max(1, c.fx.length)) * Math.PI * 2;
      try { f.teleport({ x: h.x + Math.cos(a) * 0.75, y: h.y - 0.5 + (i % 2) * 0.3, z: h.z + Math.sin(a) * 0.75 }); } catch (err) { /* */ }
    });
  }
}, 4);

// صفات مستعير الصفات
const fangsUntil = new Map();
const huntMarks = new Map(); // id عدو -> { pid, until }
const lastTraits = new Map(); // pid -> [{ id, tick }]
const TRAIT_NAMES = { rock: "Rock", fangs: "Fangs", wings: "Wings", eye: "Hunter's Eye" };

function effect(p, id, ticks, amp) {
  try { p.addEffect(id, Math.max(20, Math.round(ticks)), { amplifier: amp, showParticles: false }); } catch (e) { /* */ }
}
function applyTrait(p, id, m) {
  const now = system.currentTick;
  const col = { rock: [0.7, 0.62, 0.5], fangs: COLORS.red, wings: COLORS.green, eye: COLORS.gold }[id];
  if (id === "rock") {
    effect(p, "resistance", 200 * m, 1);
    effect(p, "slowness", 200 * m, 0);
    bodyShell(p, 1, Math.round(200 * m));
    rockBurst(p.dimension, p.location, 4, 0.8);
  } else if (id === "fangs") {
    fangsUntil.set(p.id, now + 160 * m);
    effect(p, "strength", 160 * m, 0);
    const d0 = flatDir(p);
    popShape(p.dimension, "fang_jaw", { x: p.location.x + d0.x * 1.3, y: p.location.y + 1.3, z: p.location.z + d0.z * 1.3 }, 1.4, 1.8, 10, { yaw: dirYaw({ ...d0, y: 0 }) + 180 });
  } else if (id === "wings") {
    const d = flatDir(p);
    try { p.applyKnockback({ x: d.x * 0.9, z: d.z * 0.9 }, 1.1); } catch (e) { /* */ }
    effect(p, "slow_falling", 240 * m, 0);
    effect(p, "jump_boost", 200 * m, 1);
    effect(p, "speed", 200 * m, 1);
    wingsOn(p, Math.round(200 * m));
    popShape(p.dimension, "tornado", p.location, 0.4, 1.3, 10, { s: 1000 });
  } else if (id === "eye") {
    effect(p, "night_vision", 300 * m, 0);
    popShape(p.dimension, "hunter_eye", { x: p.location.x, y: p.location.y + 3, z: p.location.z }, 0.4, 2.2, 12, { yaw: dirYaw({ ...flatDir(p), y: 0 }) + 180 });
    const list = enemiesNear(p.dimension, p.location, 24, p.id).slice(0, 10);
    for (const e of list) {
      huntMarks.set(e.id, { pid: p.id, until: now + 200 * m });
      followShape(e, "hunter_eye", Math.round(200 * m), { r: 0.7, dy: 0.9, faceYaw: () => valid(p) && valid(e) ? yawOf(e.location, p.location) : undefined });
    }
    notify(p, list.length ? `§eMarked ${list.length} enemies` : "§7No enemies nearby, but your vision improved", 50);
  }
  burst(p.dimension, headPos(p), 10, col, 2.5);
  sfx(p.dimension, "sh.trait_" + id, p.location, 1.1, 1);
  shake(p, 0.06, 0.1);
}
function recordTrait(p, id) {
  const arr = (lastTraits.get(p.id) || []).filter((x) => x.id !== id);
  arr.push({ id, tick: system.currentTick });
  lastTraits.set(p.id, arr.slice(-4));
}

let huntBusy = false;
world.afterEvents.entityHurt.subscribe((ev) => {
  try {
    if (huntBusy) return;
    const mk2 = huntMarks.get(ev.hurtEntity.id);
    if (!mk2) return;
    if (system.currentTick > mk2.until) { huntMarks.delete(ev.hurtEntity.id); return; }
    const a = ev.damageSource && ev.damageSource.damagingEntity;
    if (!a || a.id !== mk2.pid) return;
    huntBusy = true;
    try { hurt(ev.hurtEntity, 2, a); glow(ev.hurtEntity.dimension, headPos(ev.hurtEntity), { color: COLORS.gold, size: 0.3, life: 0.4 }); } finally { huntBusy = false; }
  } catch (e) { huntBusy = false; }
});
const fangsHeal = new Map();
world.afterEvents.entityHitEntity.subscribe((ev) => {
  try {
    const p = ev.damagingEntity;
    if (!p || p.typeId !== "minecraft:player") return;
    const until = fangsUntil.get(p.id);
    if (!until) return;
    const now = system.currentTick;
    if (now > until) { fangsUntil.delete(p.id); return; }
    const t = ev.hitEntity;
    if (t.typeId === "sh:trainer") return;
    try { t.addEffect("poison", 80, { amplifier: 0, showParticles: true }); } catch (e) { /* */ }
    if (now - (fangsHeal.get(p.id) || -99) >= 10) {
      popShape(t.dimension, "fang_jaw", center3(t), 0.9, 1.3, 9, { yaw: yawOf(t.location, p.location) });
      fangsHeal.set(p.id, now);
      const hp = p.getComponent("minecraft:health");
      if (hp) hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + 1.5));
    }
  } catch (e) { /* */ }
});
system.runInterval(() => {
  const now = system.currentTick;
  for (const [id, m2] of [...huntMarks.entries()]) if (now > m2.until) huntMarks.delete(id);
}, 100);

const rewindAnchors = new Map();

Object.assign(SKILL_FN, {
  // ── سيد البلورات ──
  shards(p) {
    const base = viewDir(p);
    const sneak = !!p.isSneaking;
    if (sneak) {
      // رمح بلوري عملاق يخترق كل شي بالخط
      const hits = rayHits(p, base, 20, 1.3);
      const len = 20;
      flyShard(p, base, len, 1.5, "crystal_lance");
      hits.forEach((h) => later(Math.ceil(h.t / 2.4), () => {
        if (!valid(h.e)) return;
        hurt(h.e, 10, p); pushAway(p.location, h.e, 0.6, 0.15); addCrystal(h.e, p, 1);
        popShape(h.e.dimension, "crystal_nova", center3(h.e), 0.3, 1.0, 5, { s: 400 });
      }));
      sfx(p.dimension, "sh.push", p.location, 1.1, 1.6);
      shake(p, 0.1, 0.12);
      return true;
    }
    // 3 شوكات بلورية حقيقية تطير وتلزق بالأعداء
    for (const ang of [-12, 0, 12]) {
      const d = rotY(base, ang);
      const hits = rayHits(p, d, 16, 1.1);
      const len = hits.length ? hits[0].t : 16;
      const e = hits.length ? hits[0].e : undefined;
      flyShard(p, d, len, 1.0, "crystal_spike", () => {
        if (!e || !valid(e)) return;
        hurt(e, 4, p);
        addCrystal(e, p, 1);
        burst(e.dimension, headPos(e), 6, CRYSTAL_PINK, 2.5);
      });
    }
    sfx(p.dimension, "sh.push", p.location, 0.9, 1.9);
    return true;
  },
  crystalshield(p) {
    effect(p, "absorption", 200, 2);
    sfx(p.dimension, "sh.reflect", p.location, 1, 1.5);
    popShape(p.dimension, "crystal_cluster", p.location, 0.2, 1.2, 6);
    // 4 دروع بلورية سداسية تدور حولك وتواجه الخارج
    let t = 0;
    const plates = [0, 1, 2, 3].map(() => shapeFx(p.dimension, "crystal_plate", p.location, { r: 1.3, life: 206 }));
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p) || t > 200) { system.clearRun(h); plates.forEach(removeFx); if (valid(p)) fling(p.dimension, "crystal_gem", center3(p), 5, 1, 0.6, 1); return; }
        plates.forEach((f, i) => {
          if (!f) return;
          const a = t * 0.12 + (i / 4) * Math.PI * 2;
          moveShape(f, { x: p.location.x + Math.cos(a) * 1.25, y: p.location.y + 1.0 + Math.sin(t * 0.1 + i) * 0.15, z: p.location.z + Math.sin(a) * 1.25 }, dirYaw({ x: Math.cos(a), y: 0, z: Math.sin(a) }));
        });
      } catch (e) { system.clearRun(h); plates.forEach(removeFx); }
    }, 2);
    return true;
  },
  prison(p) {
    const t = raycastTarget(p, 20);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    const dur = BOSS_TYPES.has(t.typeId) ? 40 : 100;
    effect(t, "slowness", dur, 8);
    effect(t, "jump_boost", dur, 200);
    effect(t, "weakness", dur, 1);
    addCrystal(t, p, 2);
    // قفص بلوري يطلع من الأرض ويحبس الهدف
    let size = 1.1;
    try { const bb = t.getComponent("minecraft:collision_box"); if (bb && bb.width) size = Math.max(1, Math.min(2.6, bb.width * 1.5)); } catch (e) { /* */ }
    const cage = shapeFx(t.dimension, "crystal_cage", t.location, { r: 0.1, s: 20, life: dur + 4 });
    tween(6, 1, (k) => setShape(cage, "sh:r", size * k));
    sfx(p.dimension, "sh.boundary", t.location, 1, 1.4);
    symbolShot(p, t, "crystal_spike", undefined, 2.2);
    let k2 = 0;
    const h = system.runInterval(() => {
      try {
        k2 += 4;
        if (!valid(t) || k2 > dur) {
          system.clearRun(h); removeFx(cage);
          if (valid(t)) { popShape(t.dimension, "crystal_nova", center3(t), 0.4, 1.5, 6, { s: 300 }); fling(t.dimension, "crystal_gem", center3(t), 5, 1, 0.6, 1); sfx(t.dimension, "sh.collapse", t.location, 0.8, 1.6); }
          return;
        }
        moveShape(cage, t.location);
      } catch (e) { system.clearRun(h); removeFx(cage); }
    }, 4);
    notify(p, BOSS_TYPES.has(t.typeId) ? "§dThe boss resists: short imprisonment" : "§dImprisoned", 40);
    return true;
  },
  burst(p) {
    const mine = [...crystals.entries()].filter(([, c]) => c.pid === p.id && valid(c.e));
    if (!mine.length) { notify(p, "§cNo crystals on enemies. Use Shards or Prison first", 50); return false; }
    let total = 0;
    mine.forEach(([id, c], i) => {
      dropCrystal(id);
      total += c.n;
      const e = c.e;
      later(i * 2, () => {
        if (!valid(e)) return;
        hurt(e, 5 * c.n, p);
        // تفجير: عنقود بلوري يطلع من تحت العدو + انفجار نجمي بلوري
        popShape(e.dimension, "crystal_cluster", e.location, 0.3, 1.2 + c.n * 0.15, 5);
        popShape(e.dimension, "crystal_nova", center3(e), 0.4, 1.2 + c.n * 0.2, 7, { s: 500, ease: "out" });
        fling(e.dimension, "crystal_gem", center3(e), 2 + c.n, 1.1, 0.5, 0.9);
        sfx(e.dimension, "sh.collapse", e.location, 0.9, 1.5 + Math.random() * 0.2);
        for (const o of enemiesNear(e.dimension, e.location, 3, p.id)) {
          if (o.id === e.id) continue;
          hurt(o, 3, p);
          pushAway(e.location, o, 0.8, 0.2);
        }
      });
    });
    sfx(p.dimension, "sh.collapse", p.location, 1.1, 1.5);
    shake(p, 0.15, 0.2);
    notify(p, `§dDetonated ${total} crystals`, 40);
    return true;
  },

  // ── مستعير الصفات ──
  rockskin(p) { applyTrait(p, "rock", 1); recordTrait(p, "rock"); return true; },
  fangs(p) { applyTrait(p, "fangs", 1); recordTrait(p, "fangs"); return true; },
  windwings(p) { applyTrait(p, "wings", 1); recordTrait(p, "wings"); return true; },
  huntereye(p) { applyTrait(p, "eye", 1); recordTrait(p, "eye"); return true; },
  adapt(p) {
    const now = system.currentTick;
    const arr = (lastTraits.get(p.id) || []).filter((x) => now - x.tick <= 800);
    if (arr.length < 2) { notify(p, "§cUse two different traits within 40 seconds first", 60); return false; }
    const two = arr.slice(-2);
    for (const x of two) applyTrait(p, x.id, 0.7);
    popShape(p.dimension, "nova", center3(p), 0.3, 1.4, 8, { s: 400 });
    notify(p, `§eFused: ${TRAIT_NAMES[two[0].id]} + ${TRAIT_NAMES[two[1].id]}`, 60);
    return true;
  },

  // ── محرف المسافة: الارتداد ──
  spacerewind(p) {
    const now = system.currentTick;
    const a = rewindAnchors.get(p.id);
    if (a && now <= a.until) {
      removeFx(a.fx); removeFx(a.glass);
      rewindAnchors.delete(p.id);
      if (a.dim.id !== p.dimension.id) { notify(p, "§cYou are in another dimension, the rewind is lost", 50); return 20; }
      const from = { ...p.location };
      if (!safeTeleport(p, a.loc)) { notify(p, "§cThe rewind spot is blocked", 50); return 20; }
      const hp = p.getComponent("minecraft:health");
      if (hp && a.hp > hp.currentValue) hp.setCurrentValue(Math.min(hp.effectiveMax, a.hp, hp.currentValue + 8));
      effect(p, "slow_falling", 40, 0);
      portalFx(p.dimension, from, 1, 1.6, undefined, undefined, 20);
      portalFx(p.dimension, a.loc, 1, 1.6, undefined, undefined, 20);
      popShape(p.dimension, "hourglass", { x: from.x, y: from.y + 1.2, z: from.z }, 1.4, 0.1, 8, { a: 180, s: 600 });
      popShape(p.dimension, "hourglass", { x: a.loc.x, y: a.loc.y + 2.6, z: a.loc.z }, 0.3, 1.6, 10, { a: 180, s: -300 });
      sfx(p.dimension, "sh.swap", p.location, 1, 0.8);
      shake(p, 0.1, 0.15);
      return 1200;
    }
    const hp = p.getComponent("minecraft:health");
    const fx = spawnFx(p.dimension, "circle", p.location, 2, 1.3, 305);
    const glass = shapeFx(p.dimension, "hourglass", { x: p.location.x, y: p.location.y + 1.4, z: p.location.z }, { r: 1.3, s: 60, life: 305 });
    rewindAnchors.set(p.id, { loc: { ...p.location }, dim: p.dimension, hp: hp ? hp.currentValue : 20, until: now + 300, fx, glass });
    sfx(p.dimension, "sh.select", p.location, 1, 0.7);
    notify(p, "§bYour position is saved for 15 seconds. Use it again to return", 80);
    return 20;
  },
});


// ───────────────────────── تكسير الأرض: حفر وشقوق مؤقتة + حطام متطاير ─────────────────────────
// المهارات الثقيلة (نيزك، ثقب أسود، المستعر، لكمة الحديد، المطرقة...) تكسر سطح الأرض فعلاً:
// حفرة بالمنتصف، شقوق شعاعية، وحلقة حطام. كل شي مؤقت: البلوكات ترجع لأصلها بعد بضع ثواني.
// الأمان: بس بلوكات طبيعية (عشب، تراب، رمل، حجر...)، ما يلمس البنايات (30 بلوكة) ولا يحفر تحت لاعب.
// لإيقاف تعديل البلوكات (بقاء الجزيئات بس): /scriptevent sh:scars off
const SCAR_INFO = {
  "minecraft:grass_block": { to: ["minecraft:coarse_dirt", "minecraft:gravel"], col: [0.42, 0.33, 0.2] },
  "minecraft:dirt": { to: ["minecraft:coarse_dirt", "minecraft:gravel"], col: [0.45, 0.33, 0.2] },
  "minecraft:coarse_dirt": { to: ["minecraft:gravel"], col: [0.45, 0.35, 0.25] },
  "minecraft:podzol": { to: ["minecraft:coarse_dirt"], col: [0.4, 0.3, 0.18] },
  "minecraft:mycelium": { to: ["minecraft:coarse_dirt"], col: [0.45, 0.35, 0.4] },
  "minecraft:moss_block": { to: ["minecraft:coarse_dirt"], col: [0.3, 0.45, 0.2] },
  "minecraft:mud": { to: ["minecraft:coarse_dirt"], col: [0.3, 0.25, 0.2] },
  "minecraft:sand": { to: ["minecraft:gravel"], col: [0.85, 0.78, 0.5] },
  "minecraft:red_sand": { to: ["minecraft:gravel"], col: [0.75, 0.4, 0.2] },
  "minecraft:gravel": { to: ["minecraft:cobblestone"], col: [0.5, 0.5, 0.5] },
  "minecraft:stone": { to: ["minecraft:cobblestone", "minecraft:gravel"], col: [0.55, 0.55, 0.55] },
  "minecraft:andesite": { to: ["minecraft:gravel"], col: [0.55, 0.55, 0.55] },
  "minecraft:diorite": { to: ["minecraft:gravel"], col: [0.7, 0.7, 0.7] },
  "minecraft:granite": { to: ["minecraft:gravel"], col: [0.6, 0.4, 0.35] },
  "minecraft:tuff": { to: ["minecraft:gravel"], col: [0.4, 0.42, 0.38] },
  "minecraft:cobblestone": { to: ["minecraft:gravel"], col: [0.5, 0.5, 0.5] },
  "minecraft:sandstone": { to: ["minecraft:gravel"], col: [0.85, 0.78, 0.5] },
  "minecraft:red_sandstone": { to: ["minecraft:gravel"], col: [0.75, 0.4, 0.2] },
  "minecraft:deepslate": { to: ["minecraft:cobbled_deepslate"], col: [0.25, 0.25, 0.28] },
  "minecraft:netherrack": { to: ["minecraft:gravel"], col: [0.5, 0.2, 0.2] },
};
const SCAR_RESULT = new Set(["minecraft:air", "minecraft:coarse_dirt", "minecraft:gravel", "minecraft:cobblestone", "minecraft:cobbled_deepslate"]);
const DIM_IDS = ["minecraft:overworld", "minecraft:nether", "minecraft:the_end"];
const SCAR_MAX = 700;
const scars = new Map(); // "d|x|y|z" -> { d, x, y, z, type, at }
let scarsDirty = false;
// تلوين الأرض المؤقت صار مطفي افتراضياً (ما عجب اللاعب). يتفعل بـ /scriptevent sh:scars on
const scarsEnabled = () => world.getDynamicProperty("sh_scars_on") === true;

function scarSet(block, to, ttl) {
  if (scars.size >= SCAR_MAX) return false;
  const d = DIM_IDS.indexOf(block.dimension.id);
  if (d < 0) return false;
  const k = `${d}|${block.x}|${block.y}|${block.z}`;
  const had = scars.get(k);
  try { block.setType(to); } catch (e) { return false; }
  if (had) had.at = system.currentTick + ttl;
  else scars.set(k, { d, x: block.x, y: block.y, z: block.z, type: had ? had.type : block._orig || "minecraft:dirt", at: system.currentTick + ttl });
  scarsDirty = true;
  return true;
}
function restoreScars(all) {
  const now = system.currentTick;
  for (const [k, s] of [...scars]) {
    if (!all && s.at > now) continue;
    try {
      const b = world.getDimension(DIM_IDS[s.d]).getBlock({ x: s.x, y: s.y, z: s.z });
      if (!b) { s.at = now + 200; continue; } // الشنك مو محمل: نجرب بعدين
      if (SCAR_RESULT.has(b.typeId)) b.setType(s.type); // إذا اللاعب غيّر البلوك نتركه
      scars.delete(k);
      scarsDirty = true;
    } catch (e) { scars.delete(k); }
  }
}
function saveScars() {
  if (!scarsDirty) return;
  scarsDirty = false;
  try {
    const now = system.currentTick;
    const arr = [...scars.values()].slice(0, 450).map((s) => [s.d, s.x, s.y, s.z, s.type]);
    world.setDynamicProperty("sh_scars", JSON.stringify(arr));
  } catch (e) { /* */ }
}
system.runInterval(() => { restoreScars(false); }, 20);
system.runInterval(saveScars, 100);
// إذا انسدّت اللعبة والبلوكات مكسورة: نرجعها بعد التحميل
system.runTimeout(() => {
  try {
    const raw = world.getDynamicProperty("sh_scars");
    if (typeof raw !== "string") return;
    for (const [d, x, y, z, type] of JSON.parse(raw)) scars.set(`${d}|${x}|${y}|${z}`, { d, x, y, z, type, at: system.currentTick + 40 });
  } catch (e) { /* */ }
}, 60);

// أعلى بلوك سطح قرب مركز الانفجار + تسجيل أصله قبل التغيير
function surfaceAt(dim, x, z, cy) {
  try {
    const top = dim.getTopmostBlock({ x, z });
    if (!top || Math.abs(top.y - cy) > 3) return undefined;
    const info = SCAR_INFO[top.typeId];
    if (!info) return undefined;
    const above = top.above(1);
    if (!above || !above.isAir) return undefined;
    return { top, info };
  } catch (e) { return undefined; }
}

// c: المركز، r: نصف القطر. o: { crater: نسبة الحفرة (0 بدون)، cracks: عدد الشقوق، ttl: مدة بالتكات، height }
function groundBreak(dim, c, r, o = {}) {
  const ttl = o.ttl ?? 260, crater = o.crater ?? 0, nCrack = o.cracks ?? 7;
  let visualOnly = !scarsEnabled();
  try { if (getStructs().some((s) => Math.hypot(s.x - c.x, s.z - c.z) < 30)) visualOnly = true; } catch (e) { /* */ }
  const players = world.getAllPlayers().filter((p) => p.dimension.id === dim.id);
  const cols = [];
  const R = Math.ceil(r);
  for (let dx = -R; dx <= R; dx++) for (let dz = -R; dz <= R; dz++) {
    const dist = Math.hypot(dx, dz);
    if (dist <= r) cols.push({ dx, dz, dist });
  }
  cols.sort((a, b) => a.dist - b.dist); // من المركز للخارج: موجة تتوسع
  const jitter = Math.random() * Math.PI * 2, sector = (Math.PI * 2) / Math.max(1, nCrack);
  const cx = Math.floor(c.x), cz = Math.floor(c.z);
  rockBurst(dim, c, Math.min(6, Math.round(r * 0.9)), Math.min(1.6, 0.6 + r * 0.12));
  system.runJob((function* () {
    let n = 0;
    for (const col of cols) {
      if (++n % 12 === 0) yield;
      try {
        const sf = surfaceAt(dim, cx + col.dx, cz + col.dz, c.y);
        if (!sf) continue;
        const { top, info } = sf;
        const ang = Math.atan2(col.dz, col.dx) + jitter;
        const k = ((ang / sector) % 1 + 1) % 1;
        const arc = Math.min(k, 1 - k) * sector * col.dist;
        const inCrater = crater > 0 && col.dist < r * crater;
        const inRing = col.dist > r * 0.62 && Math.abs(col.dist - r * 0.72) < 0.55;
        const inCrack = col.dist > 0.8 && arc < 0.5 + 0.12 * Math.sin(col.dist * 2.3);
        const scatter = col.dist < r * 0.85 && Math.random() < 0.12;
        if (!(inCrater || inRing || inCrack || scatter)) continue;
        const loc = { x: top.x + 0.5, y: top.y + 1.05, z: top.z + 0.5 };
        // حطام: قطع صغيرة ترتفع وتنزل
        if (Math.random() < 0.5) pix(dim, loc, { color: info.col, size: 0.2, life: 0.9 + Math.random() * 0.5, speed: 1.2 + Math.random() * 3.5, rise: -7 });
        if (visualOnly) continue;
        let to;
        if (inCrater) {
          const nearPlayer = players.some((p) => Math.hypot(p.location.x - loc.x, p.location.z - loc.z) < 2.2 && Math.abs(p.location.y - loc.y) < 3);
          const below = top.below(1);
          if (!nearPlayer && below && !below.isAir && !below.isLiquid) to = "minecraft:air";
        }
        if (!to) to = info.to[Math.floor(Math.random() * info.to.length)];
        top._orig = top.typeId;
        scarSet(top, to, ttl + Math.floor(col.dist * 3) + Math.floor(Math.random() * 40));
      } catch (e) { /* */ }
    }
  })());
}
// خط شق مستقيم على الأرض (للشطرات الطويلة)
function groundLine(dim, from, d, len, o = {}) {
  const ttl = o.ttl ?? 160;
  const visualOnly = !scarsEnabled();
  for (let t = 0.5; t <= len; t += 0.8) {
    const x = from.x + d.x * t, z = from.z + d.z * t;
    const sf = surfaceAt(dim, Math.floor(x), Math.floor(z), from.y);
    if (!sf) continue;
    const loc = { x: sf.top.x + 0.5, y: sf.top.y + 1.05, z: sf.top.z + 0.5 };
    for (let i = 0; i < 2; i++) pix(dim, loc, { color: sf.info.col, size: 0.14, life: 0.8, speed: 2, rise: -6 });
    if (!visualOnly) { sf.top._orig = sf.top.typeId; scarSet(sf.top, sf.info.to[0], ttl + Math.floor(t * 4)); }
  }
}

// ───────────────────────── سيد النجوم (قدرة خرافية) ─────────────────────────
// 7 مهارات: نيزك، بئر الجاذبية، مدار النجوم، كوكبة، ومضة نجمية، ثقب أسود، المستعر الأعظم.
// كل مهارة لها مؤثرات (جزيئات + كيانات الدوائر) وأصوات خاصة. الضرر ينقص للنص على البوسات.
const STAR_BLUE = [0.5, 0.72, 1.0], STAR_GOLD = [1.0, 0.85, 0.4], STAR_WHITE = [1, 1, 1], VOID_PURPLE = [0.5, 0.25, 0.95];
function hurtS(e, n, by) { hurt(e, Math.max(1, Math.round(n * (BOSS_TYPES.has(e.typeId) ? 0.5 : 1))), by); }
// نقطة التصويب: عدو بنظرك، أو بلوك، أو نقطة بالهواء
function aimPoint(p, max = 28) {
  const t = raycastTarget(p, max);
  if (t) return { x: t.location.x, y: t.location.y, z: t.location.z };
  try {
    const hit = p.getBlockFromViewDirection({ maxDistance: max });
    if (hit && hit.block) {
      const b = hit.block.location, f = hit.faceLocation;
      return { x: b.x + f.x, y: b.y + f.y, z: b.z + f.z };
    }
  } catch (e) { /* */ }
  const o = eyePos(p), d = viewDir(p);
  return { x: o.x + d.x * max * 0.7, y: o.y + d.y * max * 0.7 - 0.5, z: o.z + d.z * max * 0.7 };
}
function pixRing(dim, c, r, n, phase, color, size = 0.18, life = 0.7) {
  for (let i = 0; i < n; i++) {
    const a = phase + (i / n) * Math.PI * 2;
    pix(dim, { x: c.x + Math.cos(a) * r, y: c.y, z: c.z + Math.sin(a) * r }, { color, size, life, rise: 0.3 });
  }
}
function pixLine(dim, a, b, color, steps = 16, size = 0.14, life = 0.5) {
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    pix(dim, { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, z: a.z + (b.z - a.z) * t }, { color, size, life });
  }
}
function pullTo(c, e, force, up = 0.05) {
  const dx = c.x - e.location.x, dz = c.z - e.location.z, l = Math.hypot(dx, dz) || 1;
  try { e.applyKnockback({ x: (dx / l) * force, z: (dz / l) * force }, up); } catch (err) { /* */ }
}

Object.assign(SKILL_FN, {
  // 1) نيزك: دائرة تحذير ثم نيزك ينزل من السماء
  meteor(p) {
    const dim = p.dimension, c = aimPoint(p, 32);
    const top = { x: c.x + 6, y: c.y + 22, z: c.z - 6 };
    spawnFx(dim, "circle", c, 0, 3.8, 30);
    sfx(dim, "sh.meteor_fall", c, 1.3, 1);
    // نيزك صخري مشتعل ينزل بالمايل
    const dx = c.x - top.x, dy = c.y - top.y, dz = c.z - top.z, l = Math.hypot(dx, dy, dz);
    const d = { x: dx / l, y: dy / l, z: dz / l };
    const m = shapeFx(dim, "meteor", top, { r: 2.4, yaw: dirYaw(d), p: dirPitch(d), w: 200, life: 24 });
    tween(18, 1, (k) => {
      const loc = { x: top.x + dx * k, y: top.y + dy * k, z: top.z + dz * k };
      moveShape(m, loc, dirYaw(d));
      if (Math.random() < 0.6) glow(dim, loc, { color: [1, 0.55, 0.2], size: 0.9, life: 0.5 });
    }, () => {
      removeFx(m);
      sfx(dim, "sh.meteor_hit", c, 1.5, 1);
      waveFx(dim, c, 7, 0, 12);
      popShape(dim, "nova", { x: c.x, y: c.y + 0.8, z: c.z }, 0.4, 2.6, 7, { s: 300, ease: "out" });
      burst(dim, { x: c.x, y: c.y + 0.6, z: c.z }, 18, STAR_GOLD, 5, 0.3);
      for (const e of enemiesNear(dim, c, 4, p.id)) { hurtS(e, 14, p); pushAway(c, e, 1.1, 0.5); try { e.setOnFire(4, false); } catch (err) { /* */ } }
      groundBreak(dim, c, 5, { crater: 0.5, cracks: 8, ttl: 400 });
      shake(p, 0.2, 0.2);
    });
    return true;
  },
  // 2) بئر الجاذبية: يسحب الأعداء لنقطة 4 ثواني
  gravwell(p) {
    const dim = p.dimension, c = aimPoint(p, 24), life = 80;
    spawnFx(dim, "circle", c, 2, 6, life + 6);
    // دوامة جاذبية تدور بالأرض ونجمة بنصها
    const vx = shapeFx(dim, "vortex", { x: c.x, y: c.y + 0.1, z: c.z }, { r: 2.6, s: 540, life: life + 2 });
    shapeFx(dim, "star5", { x: c.x, y: c.y + 1.2, z: c.z }, { r: 0.8, s: 360, life: life + 2 });
    groundBreak(dim, c, 5, { cracks: 7, ttl: 160 });
    sfx(dim, "sh.gravwell", c, 1.2, 1);
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (t % 6 === 0) for (let i = 0; i < 4; i++) {
          const a = t * 0.3 + i * 1.57, r = 7.5 * (1 - ((i / 4 + t * 0.04) % 1));
          pix(dim, { x: c.x + Math.cos(a) * r, y: c.y + 0.3 + r * 0.12, z: c.z + Math.sin(a) * r }, { color: i % 2 ? STAR_BLUE : STAR_WHITE, size: 0.2, life: 0.5 });
        }
        for (const e of enemiesNear(dim, c, 7.5, p.id)) {
          const d = Math.hypot(e.location.x - c.x, e.location.z - c.z);
          pullTo(c, e, Math.min(0.5, 0.1 + 0.05 * (7.5 - d)));
          try { e.addEffect("slowness", 20, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
          if (t % 10 === 0) hurtS(e, 2, p);
        }
        if (t >= life) {
          system.clearRun(h);
          burst(dim, { x: c.x, y: c.y + 0.6, z: c.z }, 24, STAR_BLUE, 4, 0.24);
          waveFx(dim, c, 8, 2, 10);
          sfx(dim, "sh.pull", c, 1, 0.7);
        }
      } catch (err) { system.clearRun(h); }
    }, 2);
    return true;
  },
  // 3) مدار النجوم: 3 نجوم تدور حولك وتضرب كل من يلمسها
  orbit(p) {
    const dim = p.dimension, life = 200, orbs = [], hitCd = new Map();
    for (let i = 0; i < 3; i++) { const o = shapeFx(dim, "star5", p.location, { r: 0.8, w: 300, life: life + 10 }); if (o) orbs.push(o); }
    effect(p, "resistance", life, 0);
    sfx(dim, "sh.orbit", p.location, 1.1, 1);
    pixRing(dim, p.location, 2.3, 24, 0, STAR_GOLD, 0.22);
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p) || t > life) {
          system.clearRun(h);
          for (const o of orbs) removeFx(o);
          return;
        }
        for (let i = 0; i < 3; i++) {
          const a = t * 0.18 + (i * Math.PI * 2) / 3;
          const loc = { x: p.location.x + Math.cos(a) * 2.3, y: p.location.y + 1.0 + Math.sin(t * 0.1 + i) * 0.25, z: p.location.z + Math.sin(a) * 2.3 };
          if (orbs[i]) moveShape(orbs[i], loc, dirYaw({ x: Math.cos(a), y: 0, z: Math.sin(a) }));
          for (const e of enemiesNear(dim, loc, 1.5, p.id)) {
            if ((hitCd.get(e.id) ?? 0) > t) continue;
            hitCd.set(e.id, t + 10);
            hurtS(e, 4, p);
            pushAway(p.location, e, 0.5, 0.2);
            burst(dim, headPos(e), 6, STAR_GOLD, 2.5, 0.16);
          }
        }

      } catch (err) { system.clearRun(h); for (const o of orbs) removeFx(o); }
    }, 2);
    return true;
  },
  // 4) كوكبة: توصل الأعداء بخطوط نجمية وبعد ثانيتين تصعقهم كلهم
  constellation(p) {
    const dim = p.dimension;
    let list = enemiesNear(dim, p.location, 18, p.id).filter((e) => valid(e));
    if (list.length < 2) { notify(p, "§cYou need at least two enemies nearby", 40); return false; }
    list.sort((a, b) => Math.hypot(a.location.x - p.location.x, a.location.z - p.location.z) - Math.hypot(b.location.x - p.location.x, b.location.z - p.location.z));
    list = list.slice(0, 6);
    list.sort((a, b) => Math.atan2(a.location.z - p.location.z, a.location.x - p.location.x) - Math.atan2(b.location.z - p.location.z, b.location.x - p.location.x));
    sfx(dim, "sh.const_mark", p.location, 1.2, 1);
    for (const e of list) followShape(e, "star5", 48, { r: 0.7, s: 240, dy: 0.9 });
    const draw = (bright) => {
      for (let i = 0; i < list.length - 1; i++) {
        const a = list[i], b = list[i + 1];
        if (!valid(a) || !valid(b)) continue;
        pixLine(dim, center3(a), center3(b), bright ? STAR_WHITE : STAR_BLUE, bright ? 14 : 8, 0.2, bright ? 0.6 : 0.45);
      }
    };
    for (let k = 4; k <= 40; k += 12) later(k, () => draw(false));
    later(44, () => {
      draw(true);
      const bonus = list.length >= 4 ? 4 : 0;
      for (const e of list) {
        if (!valid(e)) continue;
        hurtS(e, 8 + bonus, p);
        popShape(dim, "nova", center3(e), 0.3, 1.2, 6, { s: 500 });
        sfx(dim, "sh.const_zap", e.location, 1, 1 + Math.random() * 0.2);
      }
      shake(p, 0.12, 0.15);
    });
    notify(p, `§9Constellation of ${list.length} stars... the shock comes in two seconds`, 50);
    return true;
  },
  // 5) ومضة نجمية: اندفاع للأمام يترك أثر نجوم ويضرب كل من بالطريق
  stardash(p) {
    const d = flatDir(p), from = { ...p.location };
    let to;
    for (const dist of [12, 10, 8, 6, 4, 2.5]) {
      const dest = { x: from.x + d.x * dist, y: from.y, z: from.z + d.z * dist };
      if (safeTeleport(p, dest, { x: dest.x + d.x * 3, y: dest.y, z: dest.z + d.z * 3 })) { to = dest; break; }
    }
    if (!to) { notify(p, "§cNo room to dash", 30); return false; }
    const dim = p.dimension;
    for (let i = 0; i <= 5; i++) {
      const k = i / 5, loc = { x: from.x + (to.x - from.x) * k, y: from.y + 1.0, z: from.z + (to.z - from.z) * k };
      later(i, () => popShape(dim, "star5", loc, 0.9, 0.1, 10, { yaw: yawOf(from, to), w: 600 }));
    }
    const seg = { x: to.x - from.x, z: to.z - from.z }, sl = Math.hypot(seg.x, seg.z) || 1;
    for (const e of enemiesNear(dim, from, sl + 4, p.id)) {
      const vx = e.location.x - from.x, vz = e.location.z - from.z;
      const proj = (vx * seg.x + vz * seg.z) / sl;
      if (proj < -0.5 || proj > sl + 0.5) continue;
      if (Math.abs(vx * seg.z - vz * seg.x) / sl > 1.8) continue;
      hurtS(e, 9, p);
      try { e.addEffect("slowness", 40, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
      burst(dim, headPos(e), 12, STAR_GOLD, 3, 0.22);
    }
    effect(p, "resistance", 20, 4);
    spawnFx(dim, "circle", from, 4, 1.4, 14);
    burst(dim, { x: to.x, y: to.y + 1, z: to.z }, 16, STAR_WHITE, 3, 0.22);
    sfx(dim, "sh.stardash", to, 1.2, 1);
    shake(p, 0.14, 0.15);
    return true;
  },
  // 6) ثقب أسود: يسحب كل شي 6 ثواني ثم ينهار وينفجر
  blackhole(p) {
    const dim = p.dimension, g = aimPoint(p, 26), life = 120;
    const c = { x: g.x, y: g.y + 2.4, z: g.z };
    spawnFx(dim, "circle", g, 1, 4, life + 6);
    // ثقب أسود حقيقي: كرة سودة بقرص تراكم يدور
    const bh = shapeFx(dim, "black_hole", c, { r: 0.3, s: 260, life: life + 12 });
    tween(20, 1, (k) => setShape(bh, "sh:r", 0.3 + 1.9 * k));
    groundBreak(dim, g, 6, { cracks: 9, ttl: 240 });
    sfx(dim, "sh.blackhole", g, 1.5, 1);
    shake(p, 0.1, 0.4);
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        for (let i = 0; i < 2; i++) {
          const a = Math.random() * Math.PI * 2, r = 9 * Math.random() + 3;
          pix(dim, { x: c.x + Math.cos(a) * r, y: c.y + (Math.random() - 0.5) * 4, z: c.z + Math.sin(a) * r }, { color: VOID_PURPLE, size: 0.15, life: 0.4, speed: -2 });
        }
        for (const e of enemiesNear(dim, c, 12, p.id)) {
          const d = Math.hypot(e.location.x - c.x, e.location.z - c.z);
          pullTo(c, e, Math.min(0.65, 0.12 + 0.07 * (12 - d)), 0.08);
          try { e.addEffect("slowness", 20, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
          if (d < 3 && t % 10 === 0) hurtS(e, 3, p);
        }
        if (t >= life) {
          system.clearRun(h);
          sfx(dim, "sh.blackhole_end", g, 1.6, 1);
          tween(8, 1, (k) => setShape(bh, "sh:r", 2.2 * (1 - k)), () => removeFx(bh));
          for (let i = 0; i < 30; i++) {
            const a = Math.random() * Math.PI * 2, r = 5 + Math.random() * 3;
            pix(dim, { x: c.x + Math.cos(a) * r, y: c.y + (Math.random() - 0.5) * 3, z: c.z + Math.sin(a) * r }, { color: VOID_PURPLE, size: 0.2, life: 0.4, speed: -9 });
          }
          later(8, () => {
            popShape(dim, "nova", c, 0.3, 4, 9, { s: 400, ease: "out" });
            burst(dim, c, 24, VOID_PURPLE, 7, 0.3);
            waveFx(dim, g, 10, 1, 14);
            waveFx(dim, g, 6, 4, 10);
            groundBreak(dim, g, 9, { crater: 0.45, cracks: 10, ttl: 500 });
            for (const e of enemiesNear(dim, c, 9, p.id)) { hurtS(e, 16, p); pushAway(c, e, 1.6, 0.6); }
            shake(p, 0.3, 0.3);
          });
        }
      } catch (err) { system.clearRun(h); }
    }, 2);
    return true;
  },
  // 7) المستعر الأعظم: شحن ثانيتين ثم انفجار نجمي هائل (تضعف بعده)
  supernova(p) {
    const dim = p.dimension, charge = 40;
    sfx(dim, "sh.supernova_charge", p.location, 1.5, 1);
    effect(p, "slowness", charge + 10, 3);
    effect(p, "resistance", charge + 10, 3);
    notify(p, "§9§lSUPERNOVA... hold still", 50);
    const core = shapeFx(dim, "nova", { x: p.location.x, y: p.location.y + 3.2, z: p.location.z }, { r: 0.2, s: 240, life: charge + 4 });
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p)) { system.clearRun(h); return; }
        const c = { x: p.location.x, y: p.location.y + 1.0, z: p.location.z };
        const k = t / charge;
        moveShape(core, { x: c.x, y: c.y + 2.2, z: c.z });
        setShape(core, "sh:r", 0.2 + 1.4 * k);
        for (let i = 0; i < 4; i++) {
          const a = Math.random() * Math.PI * 2, r = 10 * (1 - k) + 1.2, up = (Math.random() - 0.3) * 3;
          pix(dim, { x: c.x + Math.cos(a) * r, y: c.y + up, z: c.z + Math.sin(a) * r }, { color: i % 2 ? STAR_GOLD : STAR_WHITE, size: 0.18, life: 0.35, speed: -6 * (1 - k) - 1 });
        }
        if (t % 6 === 0) pixRing(dim, { x: c.x, y: p.location.y + 0.2, z: c.z }, 1 + 3 * k, 14, t * 0.4, STAR_BLUE, 0.2, 0.3);
        if (t % 10 === 0) shake(p, 0.05 + 0.12 * k, 0.12);
        if (t >= charge) {
          system.clearRun(h);
          sfx(dim, "sh.supernova_boom", p.location, 2, 1);
          shake(p, 0.5, 0.5);
          removeFx(core);
          // النجمة تنفجر: كرة نجمية تكبر لحد 14 بلوكة، ونجوم تنرمي حولك
          popShape(dim, "nova", { x: c.x, y: c.y + 2.2, z: c.z }, 1.6, 12, 12, { s: 200, ease: "out" });
          fling(dim, "star5", c, 8, 2, 0.6, 1.1);
          burst(dim, c, 30, STAR_GOLD, 9, 0.34);
          waveFx(dim, p.location, 16, 0, 16);
          later(3, () => waveFx(dim, p.location, 13, 4, 14));
          later(6, () => waveFx(dim, p.location, 10, 2, 12));
          groundBreak(dim, p.location, 13, { crater: 0.16, cracks: 12, ttl: 500 });
          for (const e of enemiesNear(dim, p.location, 14, p.id)) {
            hurtS(e, 28, p);
            pushAway(p.location, e, 2.2, 0.8);
            try { e.addEffect("blindness", 60, { amplifier: 0, showParticles: false }); } catch (err) { /* */ }
          }
          effect(p, "weakness", 120, 1);
          notify(p, "§9The star burst. You are exhausted for six seconds", 80);
        }
      } catch (err) { system.clearRun(h); }
    }, 2);
    return true;
  },
});
// لون الشحن يتحول من الأزرق للذهبي للأبيض
function i2c(k) { return k < 0.5 ? [0.4 + k, 0.6 + k * 0.4, 1.0] : [1.0, 0.85 + (k - 0.5) * 0.3, 0.4 + (k - 0.5) * 1.2]; }

// ───────────────────────── كاتانا الهاوية: سلاح يتطور ومهاراته تتبدل بالسنيك ─────────────────────────
// تلاقيها بضريح السيف المظلم. كل قتلة وانت ماسكها تعطيها خبرة (ليفل 1 → 5)، وكل ليفل يفتح مهارة جديدة.
// السنيك (الجلوس) يبدل المهارة، والاستعمال ينفذها. المؤثرات: شظايا بكسل بنفسجية تحيط بالنصل.
const KATANA = "sh:dark_katana";
const KAT_MAX = 5;
const KAT_NEED = [0, 40, 90, 160, 260]; // خبرة الانتقال من الليفل i إلى i+1
const KATANA_PURPLE = [0.7, 0.35, 1.0];
const KAT_PALETTE = [[0.7, 0.35, 1.0], [0.45, 0.35, 1.0], [0.95, 0.45, 1.0], [0.3, 0.5, 1.0], [1, 1, 1]];
// شنو يضيف كل ليفل للكاتانا
const KAT_PERKS = ["", "Base skills", "+12% damage", "Crescent fires twice, Execution finishes enemies under 30% health", "Execution jumps to a second enemy", "Triple crescent, Execution chains to two more enemies"];

function getKat(p) {
  try {
    const raw = p.getDynamicProperty("sh_kat");
    if (typeof raw === "string") { const k = JSON.parse(raw); return { lv: Math.min(KAT_MAX, Math.max(1, k.lv || 1)), xp: k.xp || 0 }; }
  } catch (e) { /* */ }
  return { lv: 1, xp: 0 };
}
function saveKat(p, k) { try { p.setDynamicProperty("sh_kat", JSON.stringify(k)); } catch (e) { /* */ } }
function katLv(p) { return getKat(p).lv; }
const kd = (p, base) => Math.round(base * (1 + 0.12 * (katLv(p) - 1)));
function addKatXp(p, amount) {
  const k = getKat(p);
  if (k.lv >= KAT_MAX) return;
  k.xp += amount;
  while (k.lv < KAT_MAX && k.xp >= KAT_NEED[k.lv]) {
    k.xp -= KAT_NEED[k.lv];
    k.lv++;
    sfxPlayer(p, "sh.kat_levelup", 1, 1);
    katanaAura(p, 40, true);
    say(p, `§5[Katana] §fIt evolved to level §d${k.lv}§f: ${KAT_PERKS[k.lv]}.`);
    notify(p, `§5Katana level ${k.lv}!`, 80);
  }
  if (k.lv >= KAT_MAX) k.xp = 0;
  saveKat(p, k);
}

// موقع النصل التقريبي بيد اللاعب (للهالة)
function bladePoint(p, u) {
  const d = flatDir(p), r = katanaRight(d);
  return { x: p.location.x + d.x * (0.5 + u * 0.55) + r.x * 0.38, y: p.location.y + 0.9 + u * 1.35, z: p.location.z + d.z * (0.5 + u * 0.55) + r.z * 0.38 };
}
// هالة خفيفة حول النصل (ما تنرسم قرب عينك حتى ما تغطي الشاشة)
function katanaAura(p, ticks, strong) {
  let t = 0;
  const h = system.runInterval(() => {
    try {
      t += 4;
      if (!valid(p) || t > ticks) { system.clearRun(h); return; }
      for (let i = 0; i < (strong ? 3 : 1); i++) {
        const b = bladePoint(p, Math.random());
        pix(p.dimension, b, { color: KAT_PALETTE[Math.floor(Math.random() * KAT_PALETTE.length)], size: 0.2, life: 0.6, speed: 0.5, rise: 0.6 });
      }
    } catch (e) { system.clearRun(h); }
  }, 4);
}
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      const held = inv(p).getItem(p.selectedSlotIndex);
      if (!held || held.typeId !== KATANA || katLv(p) < 3) continue;
      pix(p.dimension, bladePoint(p, 0.3 + Math.random() * 0.7), { color: KAT_PALETTE[Math.floor(Math.random() * 3)], size: 0.2, life: 0.9, speed: 0.2, rise: 0.4 });
    } catch (e) { /* */ }
  }
}, 10);

// أقرب عدو بنظر اللاعب (مسافة max) أو أمامه
function katanaTarget(p, max) {
  const t = raycastTarget(p, max);
  if (t) return t;
  const d = flatDir(p);
  let best, bd = 1e9;
  for (const e of enemiesNear(p.dimension, p.location, max, p.id)) {
    const vx = e.location.x - p.location.x, vz = e.location.z - p.location.z, l = Math.hypot(vx, vz) || 1;
    if ((vx / l) * d.x + (vz / l) * d.z < 0.7) continue;
    if (l < bd) { bd = l; best = e; }
  }
  return best;
}
function katanaRight(d) { return { x: -d.z, z: d.x }; }
// هلال الهاوية: هلال بنفسجي 3D يطير ويقطع كل شي (مرتين بليفل 3، ثلاث بليفل 5)
function katCrescent(p, roll, delay) {
  later(delay, () => {
    if (!valid(p)) return;
    const lv = katLv(p), dim = p.dimension, d = flatDir(p);
    const dir = { x: d.x, y: 0, z: d.z };
    const from = { x: p.location.x + d.x * 1.4, y: p.location.y + 1.1, z: p.location.z + d.z * 1.4 };
    const hit = new Set(), rad = 1.8 + 0.15 * lv;
    sfx(dim, "sh.kat_wave", p.location, 1.1, 1 + delay * 0.03);
    flyShape(dim, "slash_violet", from, dir, 1.4, 18 + 2 * lv, { r: 1.6 + 0.2 * lv, p: 90, a: roll }, (pos) => {
      for (const e of enemiesNear(dim, pos, rad, p.id)) {
        if (hit.has(e.id)) continue;
        hit.add(e.id);
        hurt(e, kd(p, 10), p);
        pushAway(p.location, e, 0.6, 0.2);
        burst(dim, headPos(e), 8, KATANA_PURPLE, 3, 0.22);
      }
      return false;
    });
  });
}
// إعدام الفراغ: تختفي وتطلع خلف العدو، شطرة X، وتنهي الضعيف، وتقفز للعدو اللي بعده
function katExecute(p, t, chainsLeft) {
  if (!valid(p) || !valid(t)) return;
  const dim = p.dimension, lv = katLv(p);
  const dest = behindSpot(t, p.location);
  shapeFx(dim, "afterimage", p.location, { r: 1.0, yaw: dirYaw({ ...flatDir(p), y: 0 }), life: 14 });
  if (dest) safeTeleport(p, dest, t.location);
  sfx(dim, "sh.kat_step", p.location, 1.1, 1);
  later(1, () => {
    if (!valid(t)) return;
    const c = center3(t);
    slashOn(dim, "slash_violet", c, p.location, 45, 1.5);
    hurt(t, kd(p, 8), p);
    sfx(dim, "sh.dagger_hit", t.location, 1.1, 0.8);
  });
  later(5, () => {
    if (!valid(t)) return;
    const c = center3(t);
    slashOn(dim, "slash_violet", c, p.location, -45, 1.5);
    let low = false;
    try { const hp = t.getComponent("minecraft:health"); low = hp.currentValue <= hp.effectiveMax * 0.3; } catch (err) { /* */ }
    if (lv >= 3 && low && !BOSS_TYPES.has(t.typeId)) {
      hurt(t, 9999, p);
      popShape(dim, "slash_violet", c, 1.0, 3.0, 7, { yaw: yawOf(c, p.location), a: 90 });
      notify(p, "§5EXECUTED!", 25);
    } else hurt(t, kd(p, 8), p);
    sfx(dim, "sh.kat_exec", t.location, 1.1, 1.2);
    shake(p, 0.18, 0.15);
    if (chainsLeft > 0) {
      later(5, () => {
        const next = enemiesNear(dim, p.location, 9, p.id).filter((e) => e.id !== t.id)[0];
        if (next) katExecute(p, next, chainsLeft - 1);
      });
    }
  });
  effect(p, "resistance", 20, 3);
}
const KATANA_SKILLS = [
  { name: "Abyss Crescent", cd: 50, desc: "A violet crescent flies forward and cuts everything in its way", fn(p) {
    const lv = katLv(p);
    katCrescent(p, 0, 0);
    if (lv >= 3) katCrescent(p, 35, 4);
    if (lv >= 5) katCrescent(p, -35, 8);
    katanaAura(p, 16, true);
    shake(p, 0.1, 0.12);
    return true;
  } },
  { name: "Void Execution", cd: 140, desc: "Vanish behind the enemy and cut it in an X; finishes weakened enemies", fn(p) {
    const lv = katLv(p);
    const t = katanaTarget(p, 12 + lv);
    if (!t) { notify(p, "§cNo enemy in front of you", 30); return false; }
    katExecute(p, t, lv >= 5 ? 2 : lv >= 4 ? 1 : 0);
    return true;
  } },
];

const cooldowns = new Map();

function useSkill(p, skill) {
  const st = getState(p);
  if (st.power !== skill.power || !isSkillUnlocked(st, skill)) {
    notify(p, "§cYou cannot use this skill", 40);
    return;
  }
  const key = `${p.id}:${skill.id}`;
  const ready = cooldowns.get(key) ?? 0;
  const now = system.currentTick;
  if (now < ready) {
    notify(p, `§7${skill.name}: wait ${((ready - now) / 20).toFixed(1)}s`, 15);
    return;
  }
  lastSkillUse.set(p.id, { id: skill.id, tick: now });
  let res = false;
  try { res = SKILL_FN[skill.id](p); } catch (e) { res = false; }
  if (res && typeof res.then === "function") {
    cooldowns.set(key, now + 40); // يمنع الضغط المتكرر أثناء القائمة
    res.then((ok) => cooldowns.set(key, system.currentTick + (ok ? skill.cooldown : 6))).catch(() => cooldowns.set(key, system.currentTick + 6));
    return;
  }
  cooldowns.set(key, now + (typeof res === "number" && res > 0 ? res : res ? skill.cooldown : 6));
}

world.afterEvents.itemUse.subscribe((ev) => {
  try {
    const p = ev.source;
    const id = ev.itemStack && ev.itemStack.typeId;
    if (!id) return;
    if (id === "sh:evolution_book") { openBook(p); return; }
    if (id === KATANA || WEAPON_SKILLS[id]) { weaponActive(p, id); return; }
    if (SCROLLS[id]) { useScroll(p, id); return; }
    if (id === "sh:skill_scroll") { useSkillScroll(p); return; }
    if (id === "sh:star_shard") { useStarShard(p); return; }
    if (id === "sh:explorer_compass") { useCompass(p); return; }
    if (id === "sh:monster_book") { openMonsterBook(p); return; }
    const skill = ITEM_TO_SKILL[id];
    if (skill) useSkill(p, skill);
  } catch (e) { /* */ }
});

// ───────────────────────── الدخول للعالم ─────────────────────────
world.afterEvents.playerSpawn.subscribe((ev) => {
  if (!ev.initialSpawn) return;
  const p = ev.player;
  system.runTimeout(() => {
    try {
      const st = getState(p);
      if (!st.gotBook) {
        giveItem(p, "sh:evolution_book");
        st.gotBook = true;
        saveState(p, st);
      }
      if (!st.gotCompass) {
        const s3 = getState(p);
        s3.gotCompass = true;
        saveState(p, s3);
        if (!hasItem(p, "sh:explorer_compass")) giveItem(p, "sh:explorer_compass");
      }
      if (!st.sawIntro) {
        const s2 = getState(p);
        s2.sawIntro = true;
        saveState(p, s2);
        introStory(p);
        starterMonsters(p);
      }
      if (st.power) {
        // تصحيح للاعبين القدامى: ليفل القدرة يلحق بليفل اللاعب، والخبرة الزايدة تتحول لليفلات
        const s5 = getState(p);
        const ups = addPowerXp(s5, 0, rarityOf(s5.power).maxLv);
        saveState(p, s5);
        if (ups.length) announceUps(p, ups);
      }
      if (!st.power) {
        const s4 = getState(p);
        if (needsDraw(s4)) later(100, () => ensureTemple(p));
      }
    } catch (e) { /* */ }
  }, 60);
});

// ───────────────────────── الأسلحة ─────────────────────────

world.afterEvents.entityHitEntity.subscribe((ev) => {
  try {
    const p = ev.damagingEntity;
    if (!p || p.typeId !== "minecraft:player") return;
    const target = ev.hitEntity;
    if (target.typeId === "sh:trainer") return;
    const held = inv(p).getItem(p.selectedSlotIndex);
    const w = held && WEAPONS[held.typeId];
    if (!w) return;
    const hp = target.getComponent("minecraft:health");
    if (!hp) return;
    let extra = w.extra;
    if (WEAPON_SKILLS[held.typeId]) {
      extra = Math.round(extra * WLV_DMG[wlvOf(p, held.typeId)]);
      const now = system.currentTick;
      if (now - (wHitXpAt.get(p.id) ?? -99) >= 10 && !isFriendly(target)) { wHitXpAt.set(p.id, now); addWeaponXp(p, held.typeId, 1); }
    }
    if (w.special === "combo") {
      const c = comboMap.get(p.id) || { n: 0, t: -999 };
      c.n = system.currentTick - c.t < 60 ? c.n + 1 : 1;
      c.t = system.currentTick;
      if (c.n >= 3) {
        extra += 6; c.n = 0;
        ring(target.dimension, { x: target.location.x, y: target.location.y + 0.8, z: target.location.z }, 1.2, 20, 0, COLORS.gold, 0.22);
        burst(target.dimension, headPos(target), 18, COLORS.gold, 3.5, 0.2);
        sfx(target.dimension, "sh.dagger_hit", target.location, 1.1, 1.5);
        notify(p, "§6Dawn Strike!", 20);
      }
      comboMap.set(p.id, c);
    }
    if (w.special === "glint") {
      const c = comboMap.get(p.id) || { n: 0, t: -999 };
      c.n = system.currentTick - c.t < 60 ? c.n + 1 : 1;
      c.t = system.currentTick;
      if (c.n >= 4) {
        extra += 7; c.n = 0;
        try { target.addEffect("blindness", 25, { amplifier: 0, showParticles: false }); } catch (e) { /* */ }
        const hc = headPos(target);
        for (let i = 0; i < 12; i++) pix(target.dimension, { x: hc.x + (Math.random() - 0.5) * 0.8, y: hc.y + (Math.random() - 0.5) * 0.8, z: hc.z + (Math.random() - 0.5) * 0.8 }, { color: i % 3 ? COLORS.white : [0.95, 0.9, 0.7], size: 0.2, life: 0.4, speed: 1.8 });
        sfx(target.dimension, "sh.dagger_hit", target.location, 1.1, 1.8);
        notify(p, "§f§lGlint!", 20);
      }
      comboMap.set(p.id, c);
    }
    if (w.special === "rend") {
      try { target.addEffect("poison", 60, { amplifier: 0, showParticles: true }); } catch (e) { /* */ }
      for (let i = 0; i < 3; i++) line(target.dimension, { x: target.location.x - 0.5, y: target.location.y + 0.6 + i * 0.4, z: target.location.z - 0.4 }, { x: target.location.x + 0.5, y: target.location.y + 1.3 + i * 0.4, z: target.location.z + 0.4 }, COLORS.white);
    }
    if (w.cleave) {
      let n = 0;
      for (const o2 of enemiesNear(target.dimension, target.location, 2.8, target.id)) {
        if (o2.id === p.id || n >= w.cleave) continue;
        hurt(o2, Math.round(w.extra * 0.6), p); n++;
        burst(target.dimension, headPos(o2), 6, COLORS.orange, 2, 0.18);
      }
    }
    if (w.shock) {
      for (const o2 of enemiesNear(target.dimension, target.location, 2.6, target.id)) {
        if (o2.id === p.id) continue;
        hurt(o2, Math.round(w.extra * 0.4), p);
        pushAway(target.location, o2, 0.9, 0.3);
      }
      ring(target.dimension, { x: target.location.x, y: target.location.y + 0.1, z: target.location.z }, 1.4, 16, 0, [0.6, 0.62, 0.58], 0.24);
      if (Math.random() < 0.2) { try { target.addEffect("slowness", 30, { amplifier: 3, showParticles: false }); } catch (e) { /* */ } }
    }
    if (w.fast) {
      const tg = target;
      system.runTimeout(() => {
        try {
          if (!valid(tg)) return;
          hurt(tg, 2, p);
          burst(tg.dimension, headPos(tg), 6, COLORS.blue, 2.5, 0.15);
          sfx(tg.dimension, w.sound, tg.location, 0.8, 1.4);
        } catch (e) { /* */ }
      }, 3);
    }
    try { target.applyDamage(extra, { cause: EntityDamageCause.entityAttack, damagingEntity: p }); } catch (e) { /* */ }
    sfx(p.dimension, w.sound, target.location, 1, 0.95 + Math.random() * 0.1);
    burst(target.dimension, headPos(target), w.knock ? 14 : 8, COLORS[w.color], w.knock ? 3 : 2, 0.18);
    if (w.knock) {
      const dx = target.location.x - p.location.x, dz = target.location.z - p.location.z;
      const len = Math.hypot(dx, dz) || 1;
      try { target.applyKnockback({ x: (dx / len) * w.knock, z: (dz / len) * w.knock }, 0.35); } catch (e) { /* */ }
      shake(p, 0.12, 0.15);
    }
  } catch (e) { /* */ }
});

// ───────────────────────── ظهور وحوش الرتبة الأولى ─────────────────────────
// يظهرون قرب اللاعب بقوة تناسب رتبته. force = يتخطى الاحتمال (للبداية والاختبار).
function trySpawnMonster(p, force) {
  try {
    if (p.dimension.id !== "minecraft:overworld") return undefined;
    const st = getState(p);
    const near = p.dimension.getEntities({ location: p.location, maxDistance: 64, families: ["sh_rank0"] });
    if (near.length >= MONSTER_CAP + (force ? 2 : 0)) return undefined;
    if (!force && Math.random() < 0.4) return undefined;
    const id = RANK0_TYPES[Math.floor(Math.random() * RANK0_TYPES.length)];
    const m = spawnOnSurface(p.dimension, id, p.location.x, p.location.z, 10, force ? 16 : 26, force ? 30 : 44);
    if (m) scaleMonster(m, st.rank);
    return m;
  } catch (e) { return undefined; }
}
system.runInterval(() => { for (const p of world.getAllPlayers()) trySpawnMonster(p, false); }, MONSTER_SPAWN_TICKS);
// وحوش البداية: بعد ما يدخل اللاعب بدقيقة (وبعد القدرة) يطلع له وحشين قريبين حتى ما يحس العالم فاضي
function starterMonsters(p) {
  for (let i = 0; i < 2; i++) later(40 + i * 30, () => trySpawnMonster(p, true));
}




// ───────────────────────── لفافة تطور المهارة ─────────────────────────
// ترفع مهارة تختارها مستوى كامل (غير القتل). تنحصل من المدرب بأول تدريب (3 لفائف)، أو من قائمة الكرييتف. ما تنحط بالصناديق.
async function useSkillScroll(p) {
  const st = getState(p);
  if (!st.power) { notify(p, "§cYou have no power", 40); return; }
  const mine = Object.values(SKILLS).filter((s) => s.power === st.power && isSkillUnlocked(st, s));
  if (!mine.length) { notify(p, "§cYou have no unlocked skill", 40); return; }
  const form = new ActionFormData().title("Skill Upgrade Scroll").body("§7Choose the skill you want to raise one full level. One scroll is consumed.");
  for (const s of mine) {
    const lv = skillLevel(st, s.id);
    form.button(lv >= SKILL_MAX_LV ? `§8${s.name} §7(max level ${SKILL_MAX_LV})` : `§a${s.name}\n§7Level ${lv} → §b${lv + 1}`);
  }
  const r = await showForm(p, form);
  if (r.canceled) return;
  const sk = mine[r.selection];
  if (!sk) return;
  const st2 = getState(p);
  const lv = skillLevel(st2, sk.id);
  if (lv >= SKILL_MAX_LV) { notify(p, `§7${sk.name} has reached the maximum`, 40); return; }
  const c = inv(p);
  let slot = -1;
  for (let i = 0; i < c.size; i++) { const it = c.getItem(i); if (it && it.typeId === "sh:skill_scroll") { slot = i; break; } }
  if (slot < 0) return;
  const it = c.getItem(slot);
  if (it.amount > 1) { it.amount -= 1; c.setItem(slot, it); } else c.setItem(slot, undefined);
  const cur = (st2.skills[sk.id] && st2.skills[sk.id].xp) || 0;
  const ups = addSkillXp(st2, sk.id, Math.max(1, skillXpNeeded(lv) - cur));
  saveState(p, st2);
  announceUps(p, ups);
  const col = POWER_COLOR[st2.power] || COLORS.gold;
  ring(p.dimension, p.location, 1.2, 24, 0, col, 0.22);
  for (let i = 0; i < 36; i++) pix(p.dimension, { x: p.location.x + (Math.random() - 0.5) * 1.4, y: p.location.y + Math.random() * 2, z: p.location.z + (Math.random() - 0.5) * 1.4 }, { color: i % 2 ? col : [1, 1, 1], size: 0.14, life: 0.9, speed: 0.7, rise: 1.8 });
  sfxPlayer(p, "sh.kat_levelup", 0.9, 1.1);
  notify(p, `§b${sk.name} reached level ${lv + 1}`, 70);
}

// ───────────────────────── لفائف الخبرة ─────────────────────────
const SCROLLS = { "sh:xp_scroll_small": 60, "sh:xp_scroll_big": 250 };

function useScroll(p, id) {
  const c = inv(p);
  const slot = p.selectedSlotIndex;
  const it = c.getItem(slot);
  if (!it || it.typeId !== id) return;
  if (it.amount > 1) { it.amount -= 1; c.setItem(slot, it); } else c.setItem(slot, undefined);
  const st = getState(p);
  const ups = addXp(st, SCROLLS[id]);
  if (st.power) ups.push(...addPowerXp(st, SCROLLS[id], rarityOf(st.power).maxLv));
  saveState(p, st);
  burst(p.dimension, headPos(p), 26, COLORS.green, 3, 0.22);
  sfxPlayer(p, "sh.level_up", 0.8, 1.2);
  notify(p, `§a+${SCROLLS[id]} XP`, 50);
  announceUps(p, ups);
}

// ───────────────────────── مهارات الوحوش (حركة + جزيئات) ─────────────────────────
const mstate = new Map();
const MONSTER_SKILLS = {
  "sh:ember_imp": { windup: 16, hold: 12, range: [3.5, 12] },
  "sh:rust_guard": { windup: 28, hold: 12, range: [0, 5] },
};

const CLOSE = {
  "sh:ember_imp": { trig: 2.6, chance: 0.7, dur: 28, hits: [8, 16], dmg: 3 },
  "sh:rust_guard": { trig: 3.0, chance: 0.6, dur: 32, hits: [12], dmg: 5 },
};

function slashFx(dim, origin, fx, fz, mirror) {
  const lx = -fz, lz = fx, sg = mirror ? -1 : 1;
  for (let k = -1; k <= 1; k++) {
    const off = k * 0.36;
    for (let i = 0; i <= 16; i++) {
      const t = i / 16;
      const lat = sg * (-0.7 + 1.4 * t) + off;
      const h = 0.7 - 1.1 * t + 0.12 * Math.sin(Math.PI * t);
      glow(dim, { x: origin.x + lx * lat + fx * 0.15 * Math.sin(Math.PI * t), y: origin.y + h, z: origin.z + lz * lat + fz * 0.15 * Math.sin(Math.PI * t) },
        { color: [1, 1, 1], size: 0.13, life: 0.45 });
    }
  }
}

function closeHit(dim, e, tp, type, idx) {
  const cfg = CLOSE[type];
  let fx = 0, fz = 1;
  if (tp) { fx = tp.location.x - e.location.x; fz = tp.location.z - e.location.z; const l = Math.hypot(fx, fz) || 1; fx /= l; fz /= l; }
  if (type === "sh:ember_imp") {
    const o = tp ? { x: tp.location.x, y: tp.location.y + 1.1, z: tp.location.z } : { x: e.location.x + fx * 1.3, y: e.location.y + 1, z: e.location.z + fz * 1.3 };
    popShape(dim, "slash_fire", o, 0.4, 0.8, 5, { yaw: dirYaw({ x: -fx, y: 0, z: -fz }), a: idx % 2 ? 40 : -40 });
    sfx(dim, "sh.imp_pounce", e.location, 0.8, 1.2 + idx * 0.15);
  } else {
    popShape(dim, "slash_teal", { x: e.location.x + fx * 1.4, y: e.location.y + 1.3, z: e.location.z + fz * 1.4 }, 0.8, 1.8, 6, { yaw: dirYaw({ x: fx, y: 0, z: fz }), p: 90, ease: "out" });
    rockBurst(dim, { x: e.location.x + fx * 1.8, y: e.location.y, z: e.location.z + fz * 1.8 }, 2, 0.7);
    sfx(dim, "sh.guard_slam", e.location, 0.9, 1.3);
  }
  for (const pl of dim.getPlayers({ location: e.location, maxDistance: cfg.trig + 0.6 })) {
    hurtPlayer(pl, cfg.dmg, e);
    pushAway(e.location, pl, type === "sh:rust_guard" ? 1.8 : 0.8, 0.25);
  }
}

function nearestPlayer(e, maxD) {
  let best, bd = maxD;
  try {
    for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: maxD })) {
      const d = Math.hypot(p.location.x - e.location.x, p.location.z - e.location.z);
      if (d < bd) { bd = d; best = p; }
    }
  } catch (err) { /* */ }
  return best ? { p: best, d: bd } : undefined;
}

function hurtPlayer(pl, amount, by) {
  try { pl.applyDamage(amount * (1 + TIER_DMG * tierOf(by)), { cause: EntityDamageCause.entityAttack, damagingEntity: by }); } catch (err) { /* */ }
}

function setMState(e, v) { try { e.setProperty("sh:state", v); } catch (err) { /* */ } }
// دائرة تحذير حمراء على الأرض قبل الضربات الكبيرة (اللاعب الشاطر يلحق يهرب)
function dangerZone(dim, loc, r, ticks) {
  const f = spawnFx(dim, "circle", { x: loc.x, y: loc.y, z: loc.z }, 5, r, ticks);
  if (f) tween(ticks, 2, (k) => setShape(f, "sh:r", r * (0.35 + 0.65 * k)));
  return f;
}
function groundAt(dim, x, z, nearY) {
  try { const t = dim.getTopmostBlock({ x: Math.floor(x), z: Math.floor(z) }); if (t && Math.abs(t.y + 1 - nearY) < 6) return t.y + 1; } catch (e) { /* */ }
  return nearY;
}
function playersNear(dim, loc, r) { try { return dim.getPlayers({ location: loc, maxDistance: r }); } catch (e) { return []; } }
// مسار مقوس (قذيفة ترتفع وتنزل) من a إلى b خلال ticks
function arcShape(dim, name, a, b, ticks, h, o, onLand) {
  const e = shapeFx(dim, name, a, { ...o, life: ticks + 4 });
  tween(ticks, 1, (k) => {
    const pos = { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k + Math.sin(Math.PI * k) * h, z: a.z + (b.z - a.z) * k };
    const d = { x: b.x - a.x, y: (b.y - a.y) + Math.cos(Math.PI * k) * h * Math.PI, z: b.z - a.z }, l = Math.hypot(d.x, d.y, d.z) || 1;
    moveShape(e, pos, dirYaw(d)); setShape(e, "sh:p", dirPitch({ x: d.x / l, y: d.y / l, z: d.z / l }));
  }, () => { removeFx(e); onLand && onLand(); });
}
function endSpecial(st, e, cd) { st.phase = 0; st.cd = cd + Math.random() * 40; st.target = undefined; if (valid(e)) setMState(e, 0); }
// عفريت الرماد: كرة نار تطير بقوس وتنفجر (من 7 لـ 13 بلوكة)
function impEmberBolt(e, tp, st) {
  const dim = e.dimension;
  st.phase = 4; setMState(e, 1);
  sfx(dim, "sh.imp_windup", e.location, 1, 0.8);
  const hold = followShape(e, "fireball", 16, { r: 0.35, s: 500, dy: 0.5 });
  tween(16, 2, (k) => setShape(hold, "sh:r", 0.35 + 0.45 * k));
  later(16, () => {
    if (!valid(e) || !valid(tp)) { endSpecial(st, e, 60); return; }
    setMState(e, 2);
    const a = { ...headPos(e), y: headPos(e).y + 0.4 }, b = { x: tp.location.x, y: groundAt(dim, tp.location.x, tp.location.z, tp.location.y), z: tp.location.z };
    dangerZone(dim, b, 2.2, 18);
    sfx(dim, "sh.imp_pounce", e.location, 1, 0.7);
    arcShape(dim, "fireball", a, b, 18, 2.5, { r: 0.8, w: 600 }, () => {
      popShape(dim, "nova", { ...b, y: b.y + 0.4 }, 0.3, 1.4, 6);
      for (let i = 0; i < 10; i++) glow(dim, b, { color: i % 2 ? COLORS.orange : COLORS.gold, size: 0.3, life: 0.8, speed: 3, rise: 1 });
      sfx(dim, "sh.meteor_hit", b, 0.8, 1.4);
      for (const pl of playersNear(dim, b, 2.4)) { hurtPlayer(pl, 4, e); try { pl.setOnFire(3, true); } catch (err) { /* */ } pushAway(b, pl, 0.6, 0.3); }
    });
    later(8, () => endSpecial(st, e, 80));
  });
}
// حارس الصدأ: يقلع صخرة ويرميها بقوس (من 6 لـ 14 بلوكة)
function guardRockThrow(e, tp, st) {
  const dim = e.dimension;
  st.phase = 4; setMState(e, 1);
  sfx(dim, "sh.guard_windup", e.location, 1, 0.8);
  rockBurst(dim, e.location, 3, 0.7);
  const rock = followShape(e, "rock_chunk", 24, { r: 1.0, s: 200, dy: 1.6 });
  tween(24, 2, (k) => setShape(rock, "sh:r", 1.0 + 1.0 * k));
  later(24, () => {
    if (!valid(e) || !valid(tp)) { endSpecial(st, e, 60); return; }
    setMState(e, 2);
    const a = { ...headPos(e), y: headPos(e).y + 1.6 }, b = { x: tp.location.x, y: groundAt(dim, tp.location.x, tp.location.z, tp.location.y), z: tp.location.z };
    dangerZone(dim, b, 2.6, 20);
    sfx(dim, "sh.guard_slam", e.location, 0.9, 1.4);
    arcShape(dim, "rock_chunk", a, b, 20, 4, { r: 2.0, w: 300, a: 30 }, () => {
      rockBurst(dim, b, 6, 1.2);
      waveFx(dim, b, 3, 3, 8);
      sfx(dim, "sh.guard_slam", b, 1.2, 0.8);
      for (const pl of playersNear(dim, b, 2.6)) { hurtPlayer(pl, 6, e); pushAway(b, pl, 1.6, 0.5); shake(pl, 0.25, 0.3); }
    });
    later(10, () => endSpecial(st, e, 100));
  });
}
// ذئب الظل: يختفي بدخان بنفسجي ويطلع خلفك ويعض (من 4 لـ 10 بلوكات)
function houndShadowLeap(e, tp, st) {
  const dim = e.dimension;
  st.phase = 4; setMState(e, 1);
  try { dim.playSound("mob.wolf.growl", e.location, { volume: 1.2, pitch: 0.6 }); } catch (err) { /* */ }
  for (let i = 0; i < 12; i++) glow(dim, { x: e.location.x + (Math.random() - 0.5), y: e.location.y + Math.random(), z: e.location.z + (Math.random() - 0.5) }, { color: VIOLET, size: 0.3, life: 0.8, rise: 1 });
  later(10, () => {
    if (!valid(e) || !valid(tp)) { endSpecial(st, e, 60); return; }
    const from = { ...e.location }, dest = behindSpot(tp, e.location);
    if (!dest) { endSpecial(st, e, 40); return; }
    for (let i = 0; i < 16; i++) glow(dim, { x: from.x + (Math.random() - 0.5), y: from.y + Math.random() * 1.2, z: from.z + (Math.random() - 0.5) }, { color: [0.1, 0.05, 0.2], size: 0.35, life: 1, rise: 0.4 });
    safeTeleport(e, dest, tp.location);
    setMState(e, 3);
    sfx(dim, "sh.kat_step", dest, 0.9, 0.7);
    later(4, () => {
      if (!valid(e) || !valid(tp)) return;
      popShape(dim, "fang_jaw", center3(tp), 0.9, 1.3, 9, { yaw: yawOf(tp.location, e.location) });
      if (dist2d(e.location, tp.location) < 3) { hurtPlayer(tp, 4, e); try { tp.addEffect("slowness", 40, { amplifier: 1 }); } catch (err) { /* */ } }
      sfx(dim, "sh.dagger_hit", tp.location, 1, 0.7);
    });
    later(14, () => endSpecial(st, e, 90));
  });
}
// عقرب الرمل: يغوص بالأرض ويطلع تحتك (من 5 لـ 12 بلوكة)
function scorpionBurrow(e, tp, st) {
  const dim = e.dimension;
  st.phase = 4; setMState(e, 1);
  sfx(dim, "sh.guard_windup", e.location, 0.8, 1.6);
  rockBurst(dim, e.location, 4, 0.7);
  try { e.addEffect("invisibility", 34, { amplifier: 0, showParticles: false }); e.addEffect("slowness", 34, { amplifier: 4, showParticles: false }); } catch (err) { /* */ }
  let lock;
  const tick = system.runInterval(() => {
    try {
      if (!valid(e) || !valid(tp)) return;
      const L = lock || tp.location;
      glow(dim, { x: L.x + (Math.random() - 0.5) * 1.5, y: L.y + 0.1, z: L.z + (Math.random() - 0.5) * 1.5 }, { color: [0.75, 0.6, 0.35], size: 0.25, life: 0.6, rise: 0.8 });
    } catch (err) { /* */ }
  }, 3);
  later(14, () => { if (valid(tp)) { lock = { ...tp.location }; dangerZone(dim, lock, 1.8, 16); sfx(dim, "sh.guard_windup", lock, 0.7, 1.9); } });
  later(30, () => {
    system.clearRun(tick);
    if (!valid(e) || !lock) { endSpecial(st, e, 60); return; }
    safeTeleport(e, lock);
    try { e.removeEffect("invisibility"); } catch (err) { /* */ }
    setMState(e, 2);
    rockBurst(dim, lock, 6, 1.3);
    popShape(dim, "slash_venom", { ...lock, y: lock.y + 1 }, 0.6, 1.8, 6, { p: 90, s: 600 });
    sfx(dim, "sh.guard_slam", lock, 1, 1.3);
    for (const pl of playersNear(dim, lock, 2.0)) { hurtPlayer(pl, 6, e); try { pl.addEffect("poison", 100, { amplifier: 0 }); pl.applyKnockback({ x: 0, z: 0 }, 0.9); } catch (err) { /* */ } }
    later(12, () => endSpecial(st, e, 110));
  });
}


function ambientFx(dim, e, type) {
  const L = e.location;
  if (type === "sh:ember_imp") {
    if (Math.random() < 0.7) glow(dim, { x: L.x + (Math.random() - 0.5) * 0.6, y: L.y + 0.4 + Math.random() * 1.1, z: L.z + (Math.random() - 0.5) * 0.6 }, { color: COLORS.orange, size: 0.14, life: 0.9, rise: 1.2 });
    if (Math.random() < 0.3) glow(dim, { x: L.x, y: L.y + 1.5, z: L.z }, { color: COLORS.gold, size: 0.1, life: 0.6, rise: 0.8 });
  } else {
    if (Math.random() < 0.6) glow(dim, { x: L.x + (Math.random() - 0.5) * 0.5, y: L.y + 3.0, z: L.z + (Math.random() - 0.5) * 0.5 }, { color: [0.55, 0.6, 0.5], size: 0.2, life: 1.4, rise: 0.5 });
    if (Math.random() < 0.25) glow(dim, { x: L.x + (Math.random() - 0.5) * 0.9, y: L.y + 0.2 + Math.random() * 1.8, z: L.z + (Math.random() - 0.5) * 0.9 }, { color: COLORS.teal, size: 0.1, life: 0.7, rise: 0.6 });
  }
}
function runMonsterSkills() {
  for (const dimId of ["overworld", "nether", "the_end"]) {
    let dim;
    try { dim = world.getDimension(dimId); } catch (e) { continue; }
    for (const type of Object.keys(MONSTER_SKILLS)) {
      let list = [];
      try { list = dim.getEntities({ type }); } catch (e) { continue; }
      for (const e of list) {
        try {
          const cfg = MONSTER_SKILLS[type];
          ambientFx(dim, e, type);
          let st = mstate.get(e.id);
          if (!st) { st = { phase: 0, t: 0, cd: 40 + Math.random() * 60 }; mstate.set(e.id, st); }
          if (st.phase === 0) {
            st.cd -= 4;
            if (st.cd > 0) continue;
            const np = nearestPlayer(e, Math.max(cfg.range[1], 14));
            const cl = CLOSE[type];
            if (cl && np && np.d < cl.trig && Math.random() < cl.chance) {
              st.phase = 3; st.t = 0; st.hit = 0; st.target = np.p;
              setMState(e, 3);
              sfx(dim, type === "sh:ember_imp" ? "sh.imp_windup" : "sh.guard_windup", e.location, 0.8, 1.2);
              continue;
            }
            if (np && type === "sh:ember_imp" && np.d >= 7 && np.d <= 13 && Math.random() < 0.45) { st.target = np.p; impEmberBolt(e, np.p, st); continue; }
            if (np && type === "sh:rust_guard" && np.d >= 6 && np.d <= 14 && Math.random() < 0.6) { st.target = np.p; guardRockThrow(e, np.p, st); continue; }
            if (!np || np.d < cfg.range[0] || np.d > cfg.range[1]) { st.cd = 10; continue; }
            st.phase = 1; st.t = 0; st.target = np.p;
            // تحذير: العفريت يأشر على مكان انقضاضه، والحارس يرسم دائرة الضربة
            if (type === "sh:ember_imp") dangerZone(dim, np.p.location, 1.6, cfg.windup + cfg.hold);
            else dangerZone(dim, e.location, 4, cfg.windup);
            setMState(e, 1);
            sfx(dim, type === "sh:ember_imp" ? "sh.imp_windup" : "sh.guard_windup", e.location, 1);
            continue;
          }
          if (st.phase === 4) continue; // مهارة خاصة شغالة
          if (st.phase === 1) {
            st.t += 4;
            if (type === "sh:ember_imp") {
              for (let i = 0; i < 3; i++) glow(dim, { x: e.location.x + (Math.random() - 0.5) * 0.8, y: e.location.y + 0.1, z: e.location.z + (Math.random() - 0.5) * 0.8 }, { color: COLORS.orange, size: 0.2, life: 0.5, rise: 1.5 });
              if (valid(st.target)) {
                // خط تحذير باتجاه الهدف
                const tx = st.target.location.x - e.location.x, tz = st.target.location.z - e.location.z, tl = Math.hypot(tx, tz) || 1;
                for (let k = 1; k <= 6; k++) glow(dim, { x: e.location.x + (tx / tl) * k * 0.7, y: e.location.y + 0.15, z: e.location.z + (tz / tl) * k * 0.7 }, { color: COLORS.red, size: 0.12, life: 0.3 });
              }
            } else if (st.t % 8 === 0) {
              rockBurst(dim, e.location, 1, 0.5);
            }
            if (st.t >= cfg.windup) {
              st.phase = 2; st.t = 0;
              setMState(e, 2);
              if (type === "sh:ember_imp") {
                const tp = valid(st.target) ? st.target : undefined;
                const dx = tp ? tp.location.x - e.location.x : 0, dz = tp ? tp.location.z - e.location.z : 1;
                const l = Math.hypot(dx, dz) || 1;
                try { e.applyImpulse({ x: (dx / l) * 1.1, y: 0.45, z: (dz / l) * 1.1 }); } catch (err) { /* */ }
                sfx(dim, "sh.imp_pounce", e.location, 1);
                burst(dim, e.location, 16, COLORS.orange, 3.5, 0.22);
                ring(dim, e.location, 1.0, 14, 0, COLORS.gold, 0.2);
              } else {
                sfx(dim, "sh.guard_slam", e.location, 1.3);
                for (const pl of dim.getPlayers({ location: e.location, maxDistance: 4 })) {
                  hurtPlayer(pl, 6, e);
                  pushAway(e.location, pl, 2.2, 0.5);
                  shake(pl, 0.25, 0.3);
                }
                waveFx(dim, e.location, 4.5, 3, 10);
                rockBurst(dim, e.location, 6, 1.3);
                for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2; popShape(dim, "crystal_gem", { x: e.location.x + Math.cos(a) * 2.2, y: e.location.y + 0.4, z: e.location.z + Math.sin(a) * 2.2 }, 0.4, 1.4, 8, { s: 400 }); }
              }
            }
            continue;
          }
          if (st.phase === 3) {
            st.t += 4;
            const cl3 = CLOSE[type];
            const tp3 = valid(st.target) ? st.target : undefined;
            while (st.hit < cl3.hits.length && st.t >= cl3.hits[st.hit]) { closeHit(dim, e, tp3, type, st.hit); st.hit++; }
            if (st.t >= cl3.dur) { st.phase = 0; st.cd = 40 + Math.random() * 40; setMState(e, 0); }
            continue;
          }
          if (st.phase === 2) {
            st.t += 4;
            if (type === "sh:ember_imp") {
              glow(dim, { x: e.location.x, y: e.location.y + 0.6, z: e.location.z }, { color: COLORS.orange, size: 0.3, life: 0.6, rise: 0.5 });
              glow(dim, { x: e.location.x, y: e.location.y + 0.9, z: e.location.z }, { color: COLORS.gold, size: 0.2, life: 0.5, rise: 0.8 });
            }
            if (st.t >= cfg.hold) {
              if (type === "sh:ember_imp") {
                for (const pl of dim.getPlayers({ location: e.location, maxDistance: 2.2 })) {
                  hurtPlayer(pl, 4, e);
                  pushAway(e.location, pl, 1.2, 0.3);
                  burst(dim, headPos(pl), 12, COLORS.orange, 3);
                }
              }
              st.phase = 0; st.cd = 80 + Math.random() * 60; st.target = undefined;
              setMState(e, 0);
            }
          }
        } catch (err) { mstate.delete(e.id); }
      }
    }
  }
}
system.runInterval(runMonsterSkills, 4);

// الرامي: الرمي صار بالسكربت حتى الحركة والسهم يكونون متزامنين 100%:
// تصويب (يرفع القوس) ← سحب الوتر 1.3 ثانية وهو يلف عليك ← إطلاق السهم بنفس لحظة حركة الإطلاق ← يجهز السهم الجاي.
const archerAI = new Map();
function archerSilenced(e) { return zones.some((z) => z.kind === "silence" && z.silenced.has(e.id)); }
function archerShoot(e, tp) {
  const dim = e.dimension;
  const from = { x: e.location.x, y: e.location.y + 1.5, z: e.location.z };
  const to = { x: tp.location.x, y: tp.location.y + 1.1, z: tp.location.z };
  const dx = to.x - from.x, dz = to.z - from.z, flat = Math.hypot(dx, dz) || 1;
  const dy = to.y - from.y + flat * 0.06;
  const l = Math.hypot(dx, dy, dz) || 1, speed = 1.7;
  const start = { x: from.x + (dx / flat) * 0.8, y: from.y, z: from.z + (dz / flat) * 0.8 };
  let ar;
  try { ar = dim.spawnEntity("minecraft:arrow", start); } catch (err) { return; }
  try { const pr = ar.getComponent("minecraft:projectile"); if (pr) { pr.owner = e; pr.shoot({ x: (dx / l) * speed, y: (dy / l) * speed, z: (dz / l) * speed }); } else ar.applyImpulse({ x: (dx / l) * speed, y: (dy / l) * speed, z: (dz / l) * speed }); }
  catch (err) { try { ar.applyImpulse({ x: (dx / l) * speed, y: (dy / l) * speed, z: (dz / l) * speed }); } catch (err2) { /* */ } }
  try { dim.playSound("random.bow", from, { volume: 1, pitch: 0.9 + Math.random() * 0.2 }); } catch (err) { /* */ }
  burst(dim, start, 8, [0.62, 0.35, 1], 2.5, 0.16);
  // أثر بنفسجي يلحق السهم وهو طاير (مثل سهم الرامي البنفسجي اللي بإيده)
  let n = 0;
  const h = system.runInterval(() => {
    try {
      if (++n > 30 || !ar || !valid(ar)) { system.clearRun(h); return; }
      const v = ar.getVelocity ? ar.getVelocity() : { x: 0, y: 0, z: 0 };
      if (n > 3 && Math.hypot(v.x, v.y, v.z) < 0.05) { system.clearRun(h); return; }   // السهم وقف (انغرس)
      glow(dim, ar.location, { color: n % 2 ? [0.62, 0.35, 1] : [0.85, 0.7, 1], size: 0.14, life: 0.35 });
    } catch (err) { system.clearRun(h); }
  }, 1);
}
system.runInterval(() => {
  for (const dimId of ["overworld", "nether", "the_end"]) {
    let dim;
    try { dim = world.getDimension(dimId); } catch (e) { continue; }
    let list = [];
    try { list = dim.getEntities({ type: "sh:training_archer" }); } catch (e) { continue; }
    for (const e of list) {
      try {
        let st = archerAI.get(e.id);
        if (!st) { st = { phase: "rest", t: 0, cd: 20 }; archerAI.set(e.id, st); }
        const np = nearestPlayer(e, 16);
        if (!np || archerSilenced(e)) { if (st.phase !== "rest") { st.phase = "rest"; setMState(e, 0); } continue; }
        const tp = np.p;
        if (st.phase !== "rest" && st.phase !== "aim") { try { e.setRotation({ x: 0, y: yawOf(e.location, tp.location) }); } catch (err) { /* */ } }
        st.t += 2;
        if (st.phase === "rest" || st.phase === "aim") {
          if (st.phase === "rest") { st.phase = "aim"; setMState(e, 3); }
          st.cd -= 2;
          if (st.cd <= 0 && np.d > 1.5) { st.phase = "draw"; st.t = 0; setMState(e, 1); try { dim.playSound("random.click", e.location, { volume: 0.4, pitch: 1.6 }); } catch (err) { /* */ } }
        } else if (st.phase === "draw") {
          // شحنة بنفسجية تكبر عند القوس (تحذير: السهم جاي)
          if (st.t % 4 === 0) {
            const f = flatDir(e), k = Math.max(0, (st.t - 15) / 17);
            glow(dim, { x: e.location.x + f.x * 0.9, y: e.location.y + 1.45, z: e.location.z + f.z * 0.9 }, { color: [0.62 + 0.3 * k, 0.35 + 0.4 * k, 1], size: 0.12 + 0.22 * k, life: 0.3 });
          }
          if (st.t >= 32) { archerShoot(e, tp); st.phase = "release"; st.t = 0; setMState(e, 2); }
        } else if (st.phase === "release") {
          if (st.t >= 10) { st.phase = "aim"; st.cd = 24 + Math.random() * 30; setMState(e, 3); }
        }
      } catch (err) { archerAI.delete(e.id); }
    }
  }
}, 2);
world.afterEvents.entityDie.subscribe((ev) => { try { archerAI.delete(ev.deadEntity.id); } catch (e) { /* */ } });


// ───────────────────────── الرامي: سهمه يظهر ويترك أثر ─────────────────────────
const seenArrows = new Set();
system.runInterval(() => {
  for (const dimId of ["overworld", "nether", "the_end"]) {
    let dim;
    try { dim = world.getDimension(dimId); } catch (e) { continue; }
    let archers = [];
    try { archers = dim.getEntities({ type: "sh:training_archer" }); } catch (e) { continue; }
    for (const a of archers) {
      try {
        let arrows = [];
        try { arrows = dim.getEntities({ type: "minecraft:arrow", location: a.location, maxDistance: 28 }); } catch (e) { /* */ }
        for (const ar of arrows) {
          const L = ar.location;
          if (!seenArrows.has(ar.id)) {
            seenArrows.add(ar.id);
            if (Math.hypot(L.x - a.location.x, L.z - a.location.z) > 3) continue;
            ring(dim, L, 0.6, 10, 0, [0.62, 0.35, 1], 0.15);
            if (seenArrows.size > 200) seenArrows.clear();
          }
          const sp = ar.getVelocity();
          if (Math.hypot(sp.x, sp.y, sp.z) < 0.2) continue;
          glow(dim, L, { color: [0.72, 0.45, 1], size: 0.2, life: 0.45 });
          glow(dim, { x: L.x - sp.x * 0.5, y: L.y - sp.y * 0.5, z: L.z - sp.z * 0.5 }, { color: [0.45, 0.8, 1], size: 0.14, life: 0.4 });
        }
      } catch (err) { /* */ }
    }
  }
}, 2);

try { setupStructures((e, pl) => scaleMonster(e, getState(pl).rank)); } catch (e) { /* */ }




// ───────────────────────── ذئب الظل وعقرب الرمل ─────────────────────────
const VIOLET = [0.62, 0.35, 1];
const VENOM = [0.6, 1, 0.35];
const mst2 = new Map();

function spitVenom(dim, from, target, shooter) {
  const pos = { x: from.x, y: from.y, z: from.z };
  let n = 0;
  const h = system.runInterval(() => {
    try {
      if (!valid(target) || n++ > 30) { system.clearRun(h); return; }
      const tx = target.location.x, ty = target.location.y + 1.0, tz = target.location.z;
      const dx = tx - pos.x, dy = ty - pos.y, dz = tz - pos.z, l = Math.hypot(dx, dy, dz) || 1;
      const k = Math.min(1.2, l);
      pos.x += (dx / l) * k; pos.y += (dy / l) * k; pos.z += (dz / l) * k;
      glow(dim, pos, { color: VENOM, size: 0.28, life: 0.4 });
      glow(dim, { x: pos.x - (dx / l) * 0.5, y: pos.y - (dy / l) * 0.5, z: pos.z - (dz / l) * 0.5 }, { color: [0.3, 0.7, 0.2], size: 0.18, life: 0.4 });
      if (l < 1.1) {
        hurtPlayer(target, 4, shooter);
        try { target.addEffect("poison", 100, { amplifier: 0 }); } catch (e) { /* */ }
        burst(dim, headPos(target), 16, VENOM, 3, 0.2);
        sfx(dim, "sh.imp_pounce", target.location, 0.7, 0.7);
        system.clearRun(h);
      }
    } catch (e) { system.clearRun(h); }
  }, 1);
}

system.runInterval(() => {
  for (const dimId of ["overworld", "nether", "the_end"]) {
    let dim;
    try { dim = world.getDimension(dimId); } catch (e) { continue; }
    for (const type of ["sh:shadow_hound", "sh:sand_scorpion"]) {
      let list = [];
      try { list = dim.getEntities({ type }); } catch (e) { continue; }
      for (const e of list) {
        try {
          const hound = type === "sh:shadow_hound";
          const L = e.location;
          // جزيئات دائمة
          if (hound) {
            if (Math.random() < 0.5) glow(dim, { x: L.x + (Math.random() - 0.5) * 0.8, y: L.y + 0.5 + Math.random() * 0.6, z: L.z + (Math.random() - 0.5) * 0.8 }, { color: VIOLET, size: 0.12, life: 0.8, rise: 0.8 });
          } else if (Math.random() < 0.3) glow(dim, { x: L.x, y: L.y + 1.2, z: L.z }, { color: VENOM, size: 0.12, life: 0.7, rise: 0.6 });
          let st = mst2.get(e.id);
          if (!st) { st = { phase: 0, t: 0, cd: 30 + Math.random() * 50 }; mst2.set(e.id, st); }
          if (st.phase === 0) {
            st.cd -= 4;
            if (st.cd > 0) continue;
            const np = nearestPlayer(e, hound ? 14 : 12);
            if (!np) { st.cd = 10; continue; }
            if (hound && np.d >= 4 && np.d <= 10 && Math.random() < 0.4) { st.target = np.p; houndShadowLeap(e, np.p, st); continue; }
            if (!hound && np.d >= 5 && np.d <= 12 && Math.random() < 0.5) { st.target = np.p; scorpionBurrow(e, np.p, st); continue; }
            if (!hound && np.d > 5) { st.cd = 8; continue; }
            if (np.d < 2.4) {
              st.phase = 3; st.t = 0; st.hit = 0; st.target = np.p; setMState(e, 3);
              sfx(dim, "sh.imp_windup", L, 0.7, hound ? 0.7 : 1.4);
            } else if (hound ? np.d > 4 : np.d < 3.8) {
              st.phase = 1; st.t = 0; st.target = np.p; setMState(e, 1);
              sfx(dim, "sh.imp_windup", L, 0.9, hound ? 0.6 : 1.0);
            } else st.cd = 8;
            continue;
          }
          if (st.phase === 4) continue; // مهارة خاصة شغالة
          const tp = valid(st.target) ? st.target : undefined;
          if (st.phase === 1) {
            st.t += 4;
            const need = hound ? 12 : 20;
            if (hound) {
              for (let i = 0; i < 3; i++) glow(dim, { x: L.x + (Math.random() - 0.5), y: L.y + 0.1, z: L.z + (Math.random() - 0.5) }, { color: VIOLET, size: 0.18, life: 0.5, rise: 1.2 });
            } else {
              glow(dim, { x: L.x, y: L.y + 1.6 + st.t * 0.02, z: L.z }, { color: VENOM, size: 0.3, life: 0.4 });
              ring(dim, { x: L.x, y: L.y + 0.1, z: L.z }, 1.2, 12, st.t * 0.2, VENOM, 0.14);
            }
            if (st.t >= need) {
              st.phase = 2; st.t = 0; setMState(e, 2);
              if (hound) {
                // عواء: يبطئ كل اللاعبين القريبين
                sfx(dim, "sh.imp_windup", L, 1.6, 0.45);
                try { dim.playSound("mob.wolf.growl", L, { volume: 1.5, pitch: 0.5 }); } catch (err) { /* */ }
                waveFx(dim, L, 14, 1, 20);
                for (const k of [0, 6, 12]) system.runTimeout(() => { try { ring(dim, L, 2 + k * 0.9, 30, k, VIOLET, 0.26); } catch (err) { /* */ } }, k);
                burst(dim, { x: L.x, y: L.y + 1.8, z: L.z }, 30, VIOLET, 5, 0.25);
                for (const pl of dim.getPlayers({ location: L, maxDistance: 14 })) {
                  try { pl.addEffect("slowness", 100, { amplifier: 1 }); } catch (err) { /* */ }
                  notify(pl, "§5The howl slows you!", 40);
                  shake(pl, 0.12, 0.4);
                }
              } else if (tp && dist2d(tp.location, L) <= 5) {
                // ضربة الذيل: خط أخضر من الإبرة للهدف + تسمم
                try { e.applyImpulse({ x: (tp.location.x - L.x) * 0.12, y: 0.2, z: (tp.location.z - L.z) * 0.12 }); } catch (err) { /* */ }
                const from = { x: L.x, y: L.y + 1.9, z: L.z }, to = center3(tp);
                const dx = to.x - from.x, dy = to.y - from.y, dz = to.z - from.z, l = Math.hypot(dx, dy, dz) || 1;
                flyShape(dim, "venom_glob", from, { x: dx / l, y: dy / l, z: dz / l }, 1.4, l, { r: 0.6, w: 500 });
                popShape(dim, "slash_venom", to, 0.5, 1.2, 6, { yaw: yawOf(tp.location, L), a: 60 });
                sfx(dim, "sh.imp_pounce", L, 0.9, 1.5);
                for (const pl of dim.getPlayers({ location: L, maxDistance: 4 })) {
                  hurtPlayer(pl, 5, e);
                  try { pl.addEffect("poison", 120, { amplifier: 0 }); } catch (err) { /* */ }
                  pushAway(L, pl, 0.6, 0.2);
                }
              }
            }
            continue;
          }
          if (st.phase === 2) {
            st.t += 4;
            if (hound) {
              glow(dim, { x: L.x, y: L.y + 2.0, z: L.z + 0.6 }, { color: VIOLET, size: 0.3, life: 0.6, rise: 0.8 });
              glow(dim, { x: L.x, y: L.y + 2.2, z: L.z }, { color: [0.85, 0.7, 1], size: 0.18, life: 0.5, rise: 1 });
            }
            if (st.t >= (hound ? 36 : 12)) { st.phase = 0; st.cd = 50 + Math.random() * 50; st.hitP = false; setMState(e, 0); }
            continue;
          }
          if (st.phase === 3) {
            st.t += 4;
            const hits = hound ? [6, 14] : [10];
            while (st.hit < hits.length && st.t >= hits[st.hit]) {
              st.hit++;
              let fx = 0, fz = 1;
              if (tp) { fx = tp.location.x - L.x; fz = tp.location.z - L.z; const l = Math.hypot(fx, fz) || 1; fx /= l; fz /= l; }
              const o = { x: L.x + fx * 1.4, y: L.y + 0.8, z: L.z + fz * 1.4 };
              if (hound) popShape(dim, st.hit % 2 ? "claw_marks" : "fang_jaw", o, 0.7, 1.1, 7, { yaw: dirYaw({ x: -fx, y: 0, z: -fz }), a: st.hit % 2 ? 25 : 0 });
              else popShape(dim, "slash_venom", o, 0.4, 0.9, 5, { yaw: dirYaw({ x: -fx, y: 0, z: -fz }), a: -30 });
              sfx(dim, "sh.guard_slam", L, 0.6, hound ? 1.6 : 1.0);
              for (const pl of dim.getPlayers({ location: L, maxDistance: 2.8 })) {
                hurtPlayer(pl, hound ? 3 : 5, e); pushAway(L, pl, hound ? 0.5 : 1.2, 0.2);
              }
            }
            if (st.t >= (hound ? 24 : 20)) { st.phase = 0; st.cd = 40 + Math.random() * 40; setMState(e, 0); }
          }
        } catch (err) { mst2.delete(e.id); }
      }
    }
  }
}, 4);


// ───────────────────────── بوصلة المستكشف: تختار وين تدلك ─────────────────────────
// استعمال = قائمة اختيار الوجهة. وانت ماسكها الـHUD يعرض اتجاهها ومسافتها لحظياً.
// سنيك + استعمال = خط إرشاد بالجزيئات نحو الوجهة المختارة.
const COMPASS_TARGETS = [
  { key: "shrine", name: "Dark Sword Shrine" },
  { key: "lightshrine", name: "Light Sword Shrine" },
  { key: "palace", name: "Sunset Palace" },
  { key: "ruins", name: "Temple Ruins" },
  { key: "village", name: "Sakura Village" },
  { key: "temple", name: "Star Temple" },
  { key: "trainer", name: "Trainer" },
  { key: "rift", name: "Open Rift" },
  { key: "nearest", name: "Nearest (any destination)" },
];
const COMPASS_NAMES = { village: "Sakura Village", palace: "Sunset Palace", ruins: "Temple Ruins", shrine: "Dark Sword Shrine", temple: "Star Temple", lightshrine: "Light Sword Shrine" };
const structCache = { tick: -9999, list: [] };
function getStructs() {
  if (system.currentTick - structCache.tick > 100) {
    structCache.tick = system.currentTick;
    try { const raw = world.getDynamicProperty("sh_structs"); structCache.list = typeof raw === "string" ? JSON.parse(raw) : []; } catch (e) { structCache.list = []; }
  }
  return structCache.list;
}
const trainerCache = new Map();
function trainerPos(p) {
  const c = trainerCache.get(p.id), now = system.currentTick;
  if (c && now - c.tick < 40) return c.pos;
  let pos;
  try {
    const t = p.dimension.getEntities({ type: "sh:trainer", location: p.location, maxDistance: 400 })[0];
    if (t) pos = { x: t.location.x, z: t.location.z };
  } catch (e) { /* */ }
  trainerCache.set(p.id, { tick: now, pos });
  return pos;
}
function compassKey(p) {
  const v = p.getDynamicProperty("sh_ctarget");
  return typeof v === "string" && COMPASS_TARGETS.some((t) => t.key === v) ? v : "nearest";
}
function compassFind(p, key) {
  const dist = (o) => Math.hypot(o.x - p.location.x, o.z - p.location.z);
  let best, bd = 1e9;
  if (key !== "trainer") {
    for (const s of getStructs()) {
      if (key !== "nearest" && s.type !== key) continue;
      const d = dist(s);
      if (d < bd) { bd = d; best = { x: s.x, z: s.z, name: COMPASS_NAMES[s.type] || "Structure" }; }
    }
  }
  if (key === "trainer" || key === "nearest") {
    const t = trainerPos(p);
    if (t && dist(t) < bd) { bd = dist(t); best = { x: t.x, z: t.z, name: "Trainer" }; }
  }
  if ((key === "rift" || key === "nearest") && rift && rift.dim === p.dimension.id && (key === "rift" || dist(rift) < bd)) best = { x: rift.x, z: rift.z, name: riftTier().name };
  return best;
}
const ARROWS = { 0: "↑", 1: "↗", 2: "→", 3: "↘", 4: "↓", [-1]: "↖", [-2]: "←", [-3]: "↙", [-4]: "↓" };
function compassArrow(p, tg) {
  let rel = yawOf(p.location, tg) - p.getRotation().y;
  rel = ((((rel + 180) % 360) + 360) % 360) - 180;
  return ARROWS[Math.round(rel / 45)] || "↑";
}
function compassPulse(p) {
  const key = compassKey(p), tg = compassFind(p, key);
  if (!tg) { notify(p, "§7That destination has not been discovered yet. Explore and try again", 60); return; }
  const dx = tg.x - p.location.x, dz = tg.z - p.location.z, dist = Math.round(Math.hypot(dx, dz));
  const dirs = ["east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"];
  const dir = dirs[((Math.round((Math.atan2(dz, dx) * 180) / Math.PI / 45) % 8) + 8) % 8];
  notify(p, `§6${tg.name}§r: ${dist} blocks to the ${dir}`, 100);
  const l = Math.hypot(dx, dz) || 1;
  for (let i = 1; i <= 10; i++) glow(p.dimension, { x: p.location.x + (dx / l) * i * 1.2, y: p.location.y + 1.2, z: p.location.z + (dz / l) * i * 1.2 }, { color: COLORS.gold, size: 0.2, life: 1.2, rise: 0.2 });
  sfxPlayer(p, "sh.compass", 0.8, 1);
}
async function openCompassMenu(p) {
  const cur = compassKey(p);
  const form = new ActionFormData().title("Explorer's Compass").body("§7Choose the destination you want the compass to guide you to. It shows at the top of the screen while you hold it.");
  for (const t of COMPASS_TARGETS) {
    const f = compassFind(p, t.key);
    const d = f ? `§a${Math.round(Math.hypot(f.x - p.location.x, f.z - p.location.z))} blocks` : "§8Not discovered yet";
    form.button(`${t.key === cur ? "§6✔ " : "§f"}${t.name}\n${d}`);
  }
  const r = await showForm(p, form);
  if (r.canceled) return;
  const pick = COMPASS_TARGETS[r.selection];
  if (!pick) return;
  p.setDynamicProperty("sh_ctarget", pick.key);
  sfxPlayer(p, "sh.compass", 0.8, 1.2);
  if (compassFind(p, pick.key)) compassPulse(p);
  else notify(p, `§7${pick.name}: not discovered yet. Structures appear as you travel the world`, 80);
}
function useCompass(p) {
  if (p.isSneaking) compassPulse(p);
  else openCompassMenu(p);
}


// ───────────────────────── رؤية الرتب: رتبة الوحش فوق راسه بلون حسب خطره عليك ─────────────────────────
const MON_NAMES = { "sh:training_archer": "Training Archer", "sh:ember_imp": "Ember Imp", "sh:rust_guard": "Rust Guard", "sh:shadow_hound": "Shadow Hound", "sh:sand_scorpion": "Sand Scorpion" };
system.runInterval(() => {
  const players = world.getAllPlayers();
  if (!players.length) return;
  for (const [type, info] of Object.entries(MONSTERS)) {
    for (const dimId of ["overworld", "nether", "the_end"]) {
      let list = [];
      try { list = world.getDimension(dimId).getEntities({ type }); } catch (e) { continue; }
      for (const e of list) {
        try {
          if (typeof e.getDynamicProperty("sh_num") === "number") continue; // رقم المحاسب له الأولوية
          if (e.hasTag("sh_rift_boss")) continue; // اسم زعيم الصدع ثابت
          let near, nd = 48;
          for (const p of players) {
            if (p.dimension.id !== e.dimension.id) continue;
            const d = Math.hypot(p.location.x - e.location.x, p.location.z - e.location.z);
            if (d < nd) { nd = d; near = p; }
          }
          if (!near) continue;
          const st = getState(near);
          let col = "§f", tag = "";
          const rk = info.rank >= 0 ? effRank(info, tierOf(e)) : info.rank;
          if (rk < 0) { col = "§7"; tag = "Training"; }
          else {
            const diff = rk - st.rank;
            tag = monRankName(rk);
            col = diff <= -2 ? "§a" : diff <= 0 ? "§e" : diff === 1 ? "§6" : "§c";
            if (diff >= 2 && st.rank < HARD_RANK_FROM) tag += " ⚡";
          }
          const h = e.getComponent("minecraft:health");
          e.nameTag = `${col}[${tag}] ${MON_NAMES[type] || ""} §7♥${Math.ceil(h.currentValue)}`;
        } catch (err) { /* */ }
      }
    }
  }
}, 20);

// ───────────────────────── أوامر التجربة (تحتاج صلاحية الأوامر) ─────────────────────────
//   /scriptevent sh:power star     يعطيك القدرة (مفاتيحها: iron wind echo crystal accountant borrower distance law star)
//   /scriptevent sh:unlock         يفتح كل مهارات قدرتك ويخلص التدريب
//   /scriptevent sh:katlv 5        يضبط ليفل الكاتانا (1 إلى 5)
//   /scriptevent sh:cdreset        يصفّر كل الكولداون
//   /scriptevent sh:spawn 3        يطلّع 3 وحوش قربك
//   /scriptevent sh:weapons        يعطيك كل الأسلحة السبعة + 3 لفائف تطور مهارة
//   /scriptevent sh:shard          يعطيك شظية نجمة (للسحب)
//   /scriptevent sh:rhythm         وضع تدريب ضربة الإيقاع (يكلك مبكر/متأخر/على الإيقاع)
//   /scriptevent sh:rift blue      يفتح صدع قربك (blue violet crimson abyss) | sh:rift close يسده
//   /scriptevent sh:rank 3         يضبط الرتبة (0-6) وصحتها | sh:xp 500 يعطيك خبرة | sh:scars on يشغل تلوين الأرض المؤقت (مطفي افتراضياً)
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  try {
    const p = ev.sourceEntity;
    if (!p || p.typeId !== "minecraft:player") return;
    const msg = (ev.message || "").trim();
    if (ev.id === "sh:power") {
      if (msg === "unbound") { const st = getState(p); st.power = null; st.powerless = true; saveState(p, st); applyVitality(p, true); say(p, "§8You are Unbound"); return; }
      if (!POWERS[msg]) { say(p, `§cUse: ${POWER_KEYS.join(" ")} unbound`); return; }
      grantPower(p, msg);
    } else if (ev.id === "sh:unlock") {
      const st = getState(p);
      if (!st.power) { say(p, "§cYou have no power"); return; }
      st.training[st.power] = { status: "done", kills: TRAIN_NEED };
      st.plevel = rarityOf(st.power).maxLv;
      saveState(p, st);
      say(p, "§aAll skills unlocked. Open the Evolution Book.");
    } else if (ev.id === "sh:wlv") {
      const held = inv(p).getItem(p.selectedSlotIndex);
      if (!held || !WEAPON_SKILLS[held.typeId]) { say(p, "§cHold one of the mod's weapons (not the katana: use sh:katlv)"); return; }
      const n = Math.min(WLV_MAX, Math.max(1, parseInt(msg, 10) || 1));
      setWlv(p, held.typeId, { lv: n, xp: 0 });
      say(p, `§aWeapon level: ${n}`);
    } else if (ev.id === "sh:katlv") {
      const n = Math.min(KAT_MAX, Math.max(1, parseInt(msg, 10) || 1));
      saveKat(p, { lv: n, xp: 0 });
      say(p, `§aKatana level: ${n}`);
    } else if (ev.id === "sh:rhythm" || ev.id === "sh:pendulum") {
      if (rhyDebug.has(p.id)) { rhyDebug.delete(p.id); say(p, "§7Rhythm practice: off"); } else { rhyDebug.add(p.id); say(p, "§eRhythm practice: on (tells you if each hit was early, late or on beat)"); }
    } else if (ev.id === "sh:rift") {
      if (msg === "close") { if (riftState()) { closeRift(false); say(p, "§aRift closed"); } else say(p, "§7No rift is open"); }
      else { const t = RIFT_TIERS.findIndex((x) => x.key === msg); const ok = openRift(p, t >= 0 ? t : 0, true); say(p, ok ? "§aA rift opened near you" : "§cCould not open a rift here (one is already open, or no ground)"); }

    } else if (ev.id === "sh:shard" || ev.id === "sh:temple") {
      if (msg === "here" || ev.id === "sh:temple") { buildTemple(p, (rec) => guideTemple(p, rec)); say(p, "§bA Star Temple is rising near you"); }
      else ensureTemple(p);
    } else if (ev.id === "sh:redraw") {
      const st = getState(p); st.power = null; st.powerless = false; saveState(p, st); removeSkillItems(p); say(p, "§bYour power was released. Step on a temple crystal to draw again.");
    } else if (ev.id === "sh:weapons") {
      for (const wid of [KATANA, ...Object.keys(WEAPONS).filter((k) => k !== KATANA)]) if (!hasItem(p, wid)) giveItem(p, wid);
      giveItem(p, "sh:skill_scroll", 3);
      say(p, "§aYou received all weapons (7) + 3 Skill Upgrade Scrolls");
    } else if (ev.id === "sh:spawn") {
      let n = Math.min(6, Math.max(1, parseInt(msg, 10) || 2)), ok = 0;
      for (let i = 0; i < n; i++) if (trySpawnMonster(p, true)) ok++;
      say(p, `§a${ok} monsters appeared near you`);
    } else if (ev.id === "sh:scars") {
      world.setDynamicProperty("sh_scars_on", msg === "on" ? true : undefined);
      if (msg !== "on") restoreScars(true);
      say(p, msg === "on" ? "§aGround scars: on (temporary)" : "§eGround scars: off (blocks unchanged)");
    } else if (ev.id === "sh:rank") {
      const r = Math.min(RANKS.length - 1, Math.max(0, parseInt(msg, 10) || 0));
      const st = getState(p);
      st.rank = r; st.level = Math.max(st.level, r * LEVELS_PER_RANK); st.xp = 0;
      saveState(p, st); applyVitality(p, true);
      say(p, `§aRank: ${RANKS[r]} (health +${rankHealthBonus(r)})`);
    } else if (ev.id === "sh:xp") {
      const st = getState(p);
      const amt = Math.max(1, parseInt(msg, 10) || 100);
      const ups = addXp(st, amt);
      if (st.power) ups.push(...addPowerXp(st, amt, rarityOf(st.power).maxLv));
      saveState(p, st); announceUps(p, ups);
    } else if (ev.id === "sh:cdreset") {
      cooldowns.clear(); weaponCd.clear();
      say(p, "§aCooldowns reset");
    }
  } catch (e) { /* */ }
});
