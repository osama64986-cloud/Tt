import { world, system, ItemStack, MolangVariableMap, EntityDamageCause } from "@minecraft/server";
import * as MC from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import {
  RANKS, LEVELS_PER_RANK, HARD_RANK_FROM, RARITIES, unlockLevel, powerXpNeeded, addPowerXp, xpNeeded, defaultState, addXp, monsterReward, isSkillUnlocked, addSkillXp, skillXpNeeded, skillLevel, SKILL_UNLOCK_LEVEL, SKILL_MAX_LV, rankProgress, rankHealthBonus,
} from "./logic.js";
import { setupStructures, buildTemple, findTemple, onShrineBossDeath, onTowerMobDeath, towerHudLine } from "./structures.js";
import { setupDash, dashCooldown } from "./dash.js";
import { SHAPE } from "./shapes.js";
import { GEAR } from "./gear.js";
import { P as vP, nearEye as vNearEye, PT, dustRing as vDustRing } from "./vfx.js";
import { IRON, WIND, ECHO, CRYSTAL, ACCOUNT, SPACE, LAW, STAR, TRAIT, TRAIT_COLOR, WEAPON, MONSTER, SYS } from "./skillfx.js";

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
  // وحوش الرتبة الثانية (Grim): أقوى بكثير، ثلاث مهارات لكل وحش
  "sh:gloomhorn": { rank: 1, xp: 70 },
  "sh:hollow_seer": { rank: 1, xp: 80 },
  "sh:veilfox": { rank: 1, xp: 90 },
  // وحوش الرتبة الثالثة (Vile): زعماء بخمس مهارات
  "sh:magmamoth": { rank: 2, xp: 220 },
  "sh:grey_bear": { rank: 2, xp: 230 },
  "sh:bear_cub": { rank: 0, xp: 6 },
  // الرتبة الرابعة (Cursed): نادر جداً بالعالم
  "sh:prayer_mantis": { rank: 3, xp: 320 },
};
const MONSTER_CAP = 3; // أقصى عدد وحوش الرتبة الأولى قرب لاعب واحد
const MONSTER_SPAWN_TICKS = 1200; // محاولة ظهور كل دقيقة (غيّرها إذا تريد أبطأ أو أسرع)
// ─── تدرج الصعوبة: الوحش يظهر بقوة تناسب رتبة اللاعب اللي قربه (حياة + ضرر + خبرة) ───
const TIER_HP = 0.30, TIER_DMG = 0.15, TIER_XP = 0.30;
function tierOf(e) { if (!e) return 0; try { const v = e.getDynamicProperty("sh_tier"); return typeof v === "number" ? v : 0; } catch (err) { return 0; } }
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
const GRIM_TYPES = ["sh:gloomhorn", "sh:hollow_seer", "sh:veilfox"];
const VILE_TYPES = ["sh:magmamoth", "sh:grey_bear"];
const CURSED_TYPES = ["sh:prayer_mantis"];
// وحوش الصدع: من الصدع البنفسجي وفوق، 30% منهم من رتبة Grim
function riftMobType() {
  if (rift && rift.tier >= 2 && Math.random() < 0.12) return VILE_TYPES[Math.floor(Math.random() * VILE_TYPES.length)];
  if (rift && rift.tier >= 1 && Math.random() < 0.3) return GRIM_TYPES[Math.floor(Math.random() * GRIM_TYPES.length)];
  return RANK0_TYPES[Math.floor(Math.random() * RANK0_TYPES.length)];
}

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
  pw_full: 10, pw_empty: 11, boss: 12, rank0: 16, power0: 32, ready: 48, cool: 49, lock: 50, held: 51, sword: 52, lens: 53, rift_ring: 54, sep: 55,
  mana_full: 56, mana_empty: 57, mana: 58, buff_might: 59, buff_bulwark: 60, buff_focus: 61, buff_swift: 62 };
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
  const lm = manaHudLine(p, st, false);                                         // المانا والتقويات (v1.35)
  return [l1, l2, lm, riftHudLine(p, false), towerHudLine(p, false)].filter(Boolean).join("\n");
}
function hudText(p, st, plain) {
  if (!plain) return hudArt(p, st);
  return [hudPlain(p, st), manaHudLine(p, st, true), riftHudLine(p, true), towerHudLine(p, true)].filter(Boolean).join("\n");
}
function hudPlain(p, st, plain = true) {        // plain: أشرطة نصية بدل رموز الواجهة (كانت ناقصة = خطأ ReferenceError بالواجهة البسيطة)
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
      line: `${POWERS[sk.power].color}${sk.name} §8│ §bLevel ${lv}${lv >= SKILL_MAX_LV ? " §6MAX" : ""} ${bar(lv >= SKILL_MAX_LV ? 1 : x / skillXpNeeded(lv), 5, "§b", "§8", plain)} §8│ §9✦${manaCost(sk)} §8│ ${stateOf(left)}`,
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
  const gh = gearHeld(id, showTip);
  if (gh) return gh;
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
// (الكاش والميزانية صاروا بمكتبة vfx.js حتى كل المود يشترك بنفس الحد)
const nearEye = vNearEye;
// ═══════════════ بارتكلز ماينكرافت الأصلية بس: المود ما عنده ولا جزيء مخصص ═══════════════
// كل جزيء هنا هو "minecraft:..." بتعريف ماينكرافت نفسه (حجمه ومدته وحركته). اللي يقبل تلوين (variable.color) ننطيه لون المهارة.
// تصنيف اللون حتى نختار الجزيء المناسب لطابع المهارة (نار، جليد، أرواح، فراغ...)
function hueClass(c) {
  const mx = Math.max(c[0], c[1], c[2]), mn = Math.min(c[0], c[1], c[2]), d = mx - mn;
  if (mx < 0.28) return "dark";
  if (d / mx < 0.22) return "white";
  let h = mx === c[0] ? ((c[1] - c[2]) / d) % 6 : mx === c[1] ? (c[2] - c[0]) / d + 2 : (c[0] - c[1]) / d + 4;
  h *= 60; if (h < 0) h += 360;
  if (h < 22 || h >= 340) return "red";
  if (h < 45) return "orange";
  if (h < 70) return "gold";
  if (h < 165) return "green";
  if (h < 205) return "cyan";
  if (h < 255) return "blue";
  return "violet";
}
// يطلع جزيء ماينكرافت: id = معرفه الأصلي، color = لون التلوين (للي يدعمه)، dir = اتجاه الانبعاث، extra = متغيرات إضافية
function mcP(dim, loc, id, color, dir, extra) { vP(dim, loc, id, { c: color, d: dir, f: extra, eye: 0 }); }
const rndDir = (k) => { const a = Math.random() * 6.2832, b = Math.random() * 2 - 1, r = Math.sqrt(1 - b * b); return { x: Math.cos(a) * r * k, y: b * k, z: Math.sin(a) * r * k }; };
// ملاحظة مهمة عن سبرايتات ماينكرافت: colored_flame_particle وsmall_soul_fire_flame سبرايتهم سماوي أصلاً، والتلوين يضرب ألوان السبرايت بلون التلوين،
// فالتلوين الدافئ (أحمر/برتقالي/ذهبي) يطلعه أخضر زيتوني. لذلك للألوان الدافئة نستعمل لهب المشعل البرتقالي الطبيعي (small_flame_particle بدون تلوين)،
// وللبنفسجي/الأبيض/الداكن glow_particle (سبرايته أبيض فيقبل أي لون)، وللسماوي/الأزرق/الأخضر اللهب الملوّن (colored_flame_particle) لأن سبرايته سماوي.
const isWarm = (cls) => cls === "red" || cls === "orange" || cls === "gold";
// نار حقيقية: لهب المشعل الأصلي (small_flame_particle). dir = اتجاه الحركة، sp = السرعة الابتدائية (يتباطأ بالاحتكاك 0.96 ويصغر بعمره)
function flame(dim, loc, dir, sp) {
  mcP(dim, loc, "minecraft:small_flame_particle", undefined, dir || { x: 0, y: 1, z: 0 }, { particle_initial_speed: sp ?? 0.6 });
}
// لهب كبير: mobflame_single = نفس لهب الكيان المحترق (سبرايت لهب متحرك 0.5 بلوكة، يطلع لفوق ويعيش 1.25 ثانية). حسب توثيق Mojang لما ما يكون في كيان يطلع من نقطة المنبعث.
function bigFlame(dim, loc) { vanillaFx(dim, "minecraft:mobflame_single", loc); }
// جمرات: lava_particle (نقطة حمم تنط بقوس وتنزل بالجاذبية)
function embers(dim, loc, n = 1) { for (let i = 0; i < n; i++) mcP(dim, loc, "minecraft:lava_particle"); }
// حلقة لهب على الأرض (بدل الأشكال المصنوعة): لهب المشعل الأصلي + جمرات
function fireRing(dim, c, r, n, y = 0.15) {
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2, p = { x: c.x + Math.cos(a) * r, y: c.y + y, z: c.z + Math.sin(a) * r };
    flame(dim, p, { x: 0, y: 1, z: 0 }, 0.3 + Math.random() * 0.4);
    if (i % 3 === 0) bigFlame(dim, p);
    if (i % 5 === 0) mcP(dim, p, "minecraft:lava_particle");
  }
}
// ضربة/انفجار بجزيئات ماينكرافت بس: big = حلقة صدمة (sonic_explosion) + شرر، وإلا انفجار عادي (large_explosion) + شرر ملوّن
function impactFx(dim, c, color, big) {
  vanillaFx(dim, big ? "minecraft:sonic_explosion" : "minecraft:large_explosion", c);
  burst(dim, c, big ? 22 : 14, color, big ? 3.5 : 2.5);
}
function glow(dim, loc, o = {}) {
  try {
    if (nearEye(dim, loc, 1.4)) return;
    const c = o.color || COLORS.gold, cls = hueClass(c), r = Math.random();
    if (isWarm(cls)) {
      if (r < 0.55) flame(dim, loc, { x: 0, y: 1, z: 0 }, 0.3 + Math.random() * 0.5);
      else if (r < 0.65 && cls !== "gold") mcP(dim, loc, "minecraft:lava_particle");
      else mcP(dim, loc, "minecraft:glow_particle", c, rndDir(0.15));
      return;
    }
    if (cls === "cyan" && r < 0.6) { mcP(dim, loc, "minecraft:small_soul_fire_flame", undefined, undefined, { particle_initial_speed: 0 }); return; }
    if (cls === "white") { const q = r < 0.4 ? "electric" : r < 0.65 ? "snow" : "glow"; mcP(dim, loc, q === "electric" ? "minecraft:electric_spark_particle" : q === "snow" ? "minecraft:falling_dust_top_snow_particle" : "minecraft:glow_particle", c, q === "electric" ? rndDir(0.4) : rndDir(0.1)); return; }
    if (cls === "violet") { if (r < 0.35) mcP(dim, loc, "minecraft:basic_portal_particle", c); else mcP(dim, loc, "minecraft:glow_particle", c, rndDir(0.12)); return; }
    if (cls === "dark") { mcP(dim, loc, "minecraft:glow_particle", [0.25, 0.2, 0.32], rndDir(0.1)); return; }
    mcP(dim, loc, "minecraft:colored_flame_particle", c);
  } catch (e) { /* */ }
}
// شرارات: glow_particle (نقطة متوهجة) ملونة، تنطلق بالاتجاه العشوائي حسب speed
function pix(dim, loc, o = {}) {
  try {
    if (nearEye(dim, loc, o.eye ?? 1.6)) return;
    const c = o.color || COLORS.gold, sp = o.speed ?? 0;
    mcP(dim, loc, "minecraft:glow_particle", c, sp > 0 ? rndDir(Math.min(1.2, sp * 0.35)) : rndDir(0.15));
  } catch (e) { /* */ }
}
// انفجار شرارات: شرارة ماينكرافت الحرجة (critical_hit_emitter، وللسحري magic_critical_hit_emitter) + شرارات glow_particle ملونة
function burst(dim, loc, n, color, speed = 2.5, size = 0.2) {
  try {
    if (nearEye(dim, loc, 1.2)) return;
    const c = color || COLORS.gold, cls = hueClass(c);
    const magic = cls === "cyan" || cls === "blue" || cls === "violet";
    if (n >= 8) mcP(dim, loc, magic ? "minecraft:magic_critical_hit_emitter" : "minecraft:critical_hit_emitter", c, undefined, { particle_count: Math.min(32, n) });
    for (let i = 0; i < Math.min(n, 14); i++) mcP(dim, loc, "minecraft:glow_particle", c, rndDir(Math.min(1.5, speed * 0.4)));
  } catch (e) { /* */ }
}
// شعاع من جزيئات ماينكرافت من a إلى b: قلب (لهب المشعل للدافئ، لهب ملوّن للسماوي، glow_particle للباقي) وخيطين glow_particle ملتفين حوله، وشرارة كهرباء كل بلوكة
function particleBeam(dim, a, b, color, life = 0.6, coreColor = [1, 0.9, 0.6]) {
  try {
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z, len = Math.hypot(dx, dy, dz) || 1;
    const d = { x: dx / len, y: dy / len, z: dz / len };
    let p = Math.abs(d.y) < 0.9 ? { x: -d.z, y: 0, z: d.x } : { x: 1, y: 0, z: 0 };
    const pl = Math.hypot(p.x, p.y, p.z) || 1; p = { x: p.x / pl, y: p.y / pl, z: p.z / pl };
    const q = { x: d.y * p.z - d.z * p.y, y: d.z * p.x - d.x * p.z, z: d.x * p.y - d.y * p.x };
    for (let s = 0, k = 0; s <= len; s += 0.4, k++) {
      const c = { x: a.x + d.x * s, y: a.y + d.y * s, z: a.z + d.z * s };
      const cc = hueClass(coreColor);
      if (isWarm(cc)) flame(dim, c, { x: 0, y: 0, z: 0 }, 0); else if (cc === "cyan" || cc === "blue" || cc === "green") mcP(dim, c, "minecraft:colored_flame_particle", coreColor); else mcP(dim, c, "minecraft:glow_particle", coreColor);
      for (const ph of [0, Math.PI]) {
        const ang = s * 2.6 + ph, cs = Math.cos(ang) * 0.22, sn = Math.sin(ang) * 0.22;
        mcP(dim, { x: c.x + p.x * cs + q.x * sn, y: c.y + p.y * cs + q.y * sn, z: c.z + p.z * cs + q.z * sn }, "minecraft:glow_particle", color);
      }
      if (k % 3 === 0) mcP(dim, c, "minecraft:electric_spark_particle", [1, 0.85, 0.6], rndDir(0.3));
    }
  } catch (e) { /* */ }
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
      SYS.unbound(dim, c);                                                     // البلورة تنطفي: دخان أسود وحبر
      say(p, "§8[Unbound] §fThe star gave you no power: one in two hundred. Instead your body refuses to break: §cstronger §fand §bfaster§f, and it grows with every rank. The Trainer has nothing to teach you; fight with weapons and your own fists.");
      return;
    }
    grantPower(p, key);
    const pw = POWERS[key], rar = rarityOf(key), idx = rarityIndexOf(key);
    f.v = idx;
    try { p.onScreenDisplay.setTitle(`§l${pw.color}${pw.name}`, { subtitle: `${rar.color}${rar.name}  ${rarityStars(key)}`, fadeInDuration: 6, stayDuration: 80, fadeOutDuration: 24 }); } catch (e) { /* */ }
    const col = RAR_RGB[idx];
    waveFx(dim, c, 6 + idx, 0, 14);
    SYS.reveal(dim, c, col, idx);                                              // شرار بلون الندرة يكبر مع الندرة (+ توتم للأسطورية، وانفجار التنين للخرافية)
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
  body += "§bWeak:§f a monster three ranks below you gives half the experience.\n";
  body += `§bDash:§f unlocks the moment you earn your first rank (${RANKS[1]}) and stays with you forever: double-tap left, right or back to dash 3 blocks that way. Cooldown by rank: ${RANKS.slice(1).map((n, i) => `${n} ${(dashCooldown(i + 1) / 20).toFixed(1)}s`).join(", ")}.\n\n`;
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
  ["sh:gloomhorn", "Gloomhorn", "Grim to Cataclysm", "A spectral stag with an open ribcage and a floating heart. It scrapes the ground, then CHARGES and RAMS you with its antlers, so step aside. From afar its heart glows and a SPIRIT STAG bursts from its chest and gallops at you, followed by two more. Up close its heart BEATS three times: each beat sends a wave along the ground (JUMP over it), and the last one binds you with SOUL CHAINS that drain your life. Run more than 10 blocks to break them."],
  ["sh:hollow_seer", "Hollow Seer", "Grim to Cataclysm", "A floating seer with one round eye. When it raises its hand in front of the eye, an ORANGE BEAM gathers: the aim locks a moment before it fires, so sidestep. From 6-7 blocks away it lifts its arms and ROOTS erupt from the ground one after another toward you, then a CAGE OF ROOTS curls around you. Up close an ICE ORB forms before its face and it exhales a FROST BREATH: your screen freezes like powder snow and you slow down, but you can still fight."],
  ["sh:veilfox", "Veilfox", "Grim to Cataclysm", "A spirit fox with five flame-tipped tails and a white mask. FOXFIRE SERPENT: nine spirit flames weave toward you in a snaking train (stand between the waves). MIRROR CAROUSEL: it and three real shadow foxes circle you in a tightening ring, then all collapse on you at once (kill the shadows to thin it). SUN SHOWER: foxfire drops rain down over eight blocks around you. Below half health it casts MOON LIFT: it floats you into the air while three volleys of crescent waves fall on you."],
  ["sh:magmamoth", "Magmamoth", "Vile to Cataclysm", "A volcanic mammoth, about 4 blocks tall on long legs, of armoured basalt and glowing magma cracks. FISSURE STOMP: a shock ring, then eight magma cracks race outward and burst one spot at a time (stand between the cracks). INFERNO SWEEP: from 7+ blocks away it raises its trunk and sweeps a real jet of flames from the trunk tip across you, leaving fire patches. TUSK STAMPEDE: it scrapes, charges, re-aims and charges again; whoever it catches is tossed by the tusks, and it leaves a trail of fire. VOLCANIC BOMBARDMENT: it hurls burning boulders high that arc down onto you. MAGMA ARMOR: its cracks blaze white-hot and it takes much less damage for nine seconds."],
  ["sh:grey_bear", "Grey Bear", "Vile to Cataclysm", "A grey bear that fights standing on two legs, with a silver crescent on its chest and a clawed scar over one eye. BEAR HUG: it spreads its arms and grabs whoever is in front of it, squeezes three times and throws them; hit it 3 times or dash out to break free. RENDING CLAWS: four alternating claw swipes that scratch your body and make you bleed (stacks up to 3). CUB CALL: it roars and two cubs run at you and cling to your legs, slowing you; kill a cub and the bear goes into a rage. DEEP HIBERNATION: when hurt it falls asleep and heals; strike it and it wakes in a WRATH that blasts you away. Thick pelt: hits on its front do 30% less damage, hits on its back 20% more."],
  ["sh:prayer_mantis", "Prayer Mantis", "Cursed to Cataclysm", "A leaf-green mantis with a long raised neck, glowing violet eyes and two folded scythe arms. It is very rare in the wild. PRAYER STANCE: a cursed halo rises behind its head and it raises both scythes; any hit you land is turned back at you DOUBLED as an X of blades, so wait it out or keep your distance. LEAF CAMOUFLAGE: a whirl of leaves and it turns half transparent, creeps close and stabs with both scythes; hit it to reveal it early. SCISSOR LOCK: two huge blades close around your waist and pin you for 1.5 s before a final snip; DASH to break it. MOLT: at half health it sheds its old shell, which explodes a moment later (run!), and the fresh mantis is faster and attacks more often."],
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
    const dn = dropNames(id);
    body += `§e${name} §7(${rank}) §fKilled: §b${k}\n§7${k > 0 || id === "sh:training_archer" ? tip : "Kill one to reveal its info."}${dn && k > 0 ? `\n§6Drops: ${dn}` : ""}\n\n`;
  }
  await showForm(player, new ActionFormData().title("Monster Book").body(body).button("§aOK"));
}

// ───────────────────────── نافذة الحالة ─────────────────────────
// ملخص كامل: الرتبة والليفل والقدرة وكل مهارة (مستواها، حالتها، طريقة استعمالها) وتطور الكاتانا.
async function showStatus(player) {
  const st = getState(player);
  const pw = POWERS[st.power];
  let b = `§6◆ ${RANKS[st.rank]}§r  §bLv ${st.level}§r  §7(${st.xp}/${xpNeeded(st.level)} XP)\n${nextRankLine(st)}\n`;
  if (st.power) b += `§9✦ Mana: ${Math.floor(manaOf(player, st))}/${manaMax(st)} §7(+${(4 + 0.5 * (st.rank || 0)).toFixed(1)}/s; each ability costs mana, weapons don't)\n`;
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
    try { if (ev.deadEntity.getDynamicProperty("sh_clone") === 1) return; } catch (e00) { /* */ }
    try {
      let tagged = true;                                                  // وحش طبيعي من نفس النوع ما يحسب (لو قدرنا نقرا الوسوم)
      try { tagged = ev.deadEntity.hasTag("sh_boss"); } catch (e02) { tagged = true; }
      onShrineBossDeath(ev.deadEntity.typeId, ev.deadEntity.location, ev.deadEntity.dimension, tagged);
    } catch (e01) { /* */ }
    try { onTowerMobDeath(ev.deadEntity); } catch (e04) { /* */ }                      // قمة برج الهاوية: لما ينقتلون كلهم يطلع الصندوق
    if (ev.deadEntity.typeId === "sh:bear_cub") { try { onCubDeath(ev.deadEntity); } catch (e03) { /* */ } }   // الدب يغضب إذا قتلت جروه   // حراس الضريحين: لما يموت الاثنان يظهر صندوق السيف
    if (ev.deadEntity.typeId === "sh:magmamoth") {            // موت الماموث: انفجار حمم وصخور
      const dl = ev.deadEntity.location, dm = ev.deadEntity.dimension;
      vanillaFx(dm, "minecraft:huge_explosion_emitter", { x: dl.x, y: dl.y + 1.5, z: dl.z });
      rockBurst(dm, dl, 12, 1.3);
      for (let i = 0; i < 28; i++) { const a = Math.random() * 6.28, r = Math.random() * 2.4, q = { x: dl.x + Math.cos(a) * r, y: dl.y + 0.4 + Math.random() * 3, z: dl.z + Math.sin(a) * r }; if (i % 2) mcP(dm, q, "minecraft:lava_particle"); else flame(dm, q, UP, 1 + Math.random() * 2); }
      sfx(dm, "sh.supernova_boom", dl, 1.2, 0.7);
    }
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
        : t === "sh:training_archer" ? (roll < 0.25 ? "sh:xp_scroll_small" : null)
        : t === "sh:gloomhorn" ? (roll < 0.45 ? "sh:xp_scroll_small" : roll < 0.7 ? "sh:xp_scroll_big" : roll < 0.75 ? "sh:skill_scroll" : null)
        : t === "sh:grey_bear" ? (roll < 0.5 ? "sh:xp_scroll_big" : roll < 0.8 ? "sh:skill_scroll" : "sh:xp_scroll_small")
        : t === "sh:prayer_mantis" ? (roll < 0.55 ? "sh:skill_scroll" : "sh:xp_scroll_big")
        : t === "sh:magmamoth" ? (roll < 0.5 ? "sh:xp_scroll_big" : roll < 0.8 ? "sh:skill_scroll" : "sh:xp_scroll_small")
        : t === "sh:veilfox" ? (roll < 0.4 ? "sh:xp_scroll_small" : roll < 0.7 ? "sh:xp_scroll_big" : roll < 0.8 ? "sh:skill_scroll" : null)
        : t === "sh:hollow_seer" ? (roll < 0.4 ? "sh:xp_scroll_small" : roll < 0.7 ? "sh:xp_scroll_big" : roll < 0.78 ? "sh:skill_scroll" : null) : null;
      if (drop) ev.deadEntity.dimension.spawnItem(new ItemStack(drop, 1), ev.deadEntity.location);
    } catch (e2) { /* */ }
    try { dropMaterials(ev.deadEntity); } catch (e5) { /* */ }                     // مواد الوحوش (جلود، قشور، مخالب...)
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
function symbolShot(p, t, name, onHit, speed = 1.1, trail) {
  const from = { x: p.location.x, y: p.location.y + 1.3, z: p.location.z }, to = headPos(t);
  const dx = to.x - from.x, dy = to.y - from.y, dz = to.z - from.z, l = Math.hypot(dx, dy, dz) || 1;
  const d = { x: dx / l, y: dy / l, z: dz / l };
  let k = 0;
  flyShape(p.dimension, name, { x: from.x + d.x, y: from.y + d.y, z: from.z + d.z }, d, speed, Math.max(1.5, l - 1), { r: 1.0, w: name.startsWith("arrow") ? 0 : 360 },
    trail ? (pos) => { try { trail(pos, k++); } catch (err) { /* */ } } : undefined, () => { try { onHit && onHit(); } catch (err) { /* */ } });
}

function collapse(e, p) {
  const dim = e.dimension;
  const loc = headPos(e);
  clearNum(e);
  sfx(dim, "sh.collapse", loc, 1.2);
  fling(dim, ["digit_0", "digit_1", "digit_7", "digit_9", "digit_3"], loc, 6, 1.2, 0.35, 0.6);
  popShape(dim, "digit_0", { x: loc.x, y: loc.y + 0.3, z: loc.z }, 0.6, 2.2, 8, { s: 500 });
  // الانهيار: انفجار التوتم (عملات ذهب وخضر) + انفجار + شرر + حلقة ذهب، والحروف تنسحب للمكان
  ACCOUNT.collapse(dim, center3(e));
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
  try { e.applyDamage(amount * skillDmgMul(by) * weaponSkillMul(by) * mightMul(by), { cause: EntityDamageCause.entityAttack, damagingEntity: by }); skillHitXp(by, e); } catch (err) { /* */ }
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
    // لحظة التحول: الحديد = حلقة شرر تصعد من الرجل للراس ورنة شرر حرج؛ الصخر = غبار حصى وحلقة غبار أرضية (+ وميض شاشة خفيف)
    if (variant === 0) IRON.skinForm(dim, p.location); else TRAIT.rock(dim, p.location);
    try { p.camera.fade({ fadeColor: { red: spark[0], green: spark[1], blue: spark[2] }, fadeTime: { fadeInTime: 0.04, holdTime: 0.04, fadeOutTime: 0.25 } }); } catch (err) { /* */ }
    let t = 0, lastHp = hpNow(p);
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p) || !valid(e) || t > ticks) {
          system.clearRun(h); removeFx(e); bodyShells.delete(p.id);
          if (valid(p)) { IRON.skinEnd(p.dimension, p.location); sfx(p.dimension, "sh.cleaver_hit", p.location, 0.6, 1.6); }
          return;
        }
        const rot = p.getRotation();
        e.teleport(p.location, { rotation: { x: 0, y: rot.y } });
        e.setProperty("sh:p", Math.max(-90, Math.min(90, rot.x)));
        const v = p.getVelocity();
        e.setProperty("sh:mv", Math.hypot(v.x, v.z) > 0.04 ? 1 : 0);
        e.setProperty("sh:r", Math.min(1, 0.55 + t * 0.045));
        const hp = hpNow(p);
        if (hp < lastHp - 0.4) { IRON.skinHit(p.dimension, p.location); sfx(p.dimension, "sh.dagger_hit", p.location, 0.7, 1.9); }
        if (variant === 0 && t % 10 === 0) IRON.skinTick(p.dimension, p.location);
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
    if (o.l !== undefined) e.setProperty("sh:l", Math.max(0, Math.min(64, o.l)));
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
// شعاع بين نقطتين: star_beam طوله بلوكة × sh:r ويتمدد بالطول بـ sh:l (خطوط الكوكبة ومسار الومضة)
function beamShape(dim, a, b, life, r = 1) {
  const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z, L = Math.hypot(dx, dy, dz) || 0.01, d = { x: dx / L, y: dy / L, z: dz / L };
  return shapeFx(dim, "star_beam", a, { r, yaw: dirYaw(d), p: dirPitch(d), l: L / r, life });
}
function aimBeam(e, a, b, r = 1) {
  if (!e || !valid(e)) return;
  const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z, L = Math.hypot(dx, dy, dz) || 0.01, d = { x: dx / L, y: dy / L, z: dz / L };
  moveShape(e, a, dirYaw(d)); setShape(e, "sh:p", dirPitch(d)); setShape(e, "sh:l", Math.min(64, L / r));
}
// بوابة المسافة (warp_gate): تنفتح خلال 4 تكات، تبقى hold، وتنسد خلال 5
function warpGate(dim, loc, yaw, r = 1, hold = 6) {
  const g = shapeFx(dim, "warp_gate", loc, { r: 0.1, yaw, life: hold + 12 });
  if (!g) return undefined;
  tween(4, 1, (k) => setShape(g, "sh:r", 0.1 + (r - 0.1) * k), () => later(hold, () => tween(5, 1, (k) => setShape(g, "sh:r", Math.max(0.01, r * (1 - k))))));
  return g;
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
      blocked = !airAt(dim, pos.x, pos.y, pos.z);
      const stop = blocked || dist >= maxDist || (onStep && onStep(pos, dist));
      moveShape(e, pos, yaw);
      if (stop) { system.clearRun(h); removeFx(e); if (onEnd) onEnd({ ...pos }, blocked); }
    } catch (err) { system.clearRun(h); removeFx(e); }
  }, 1);
  return e;
}
// قذيفة من جزيئات بس (بدون شكل): نفس حركة flyShape وفحص الجدار؛ onStep(pos, dist) يرجع true حتى يوقف
function flyFx(dim, from, d, speed, maxDist, onStep, onEnd) {
  let dist = 0;
  const pos = { ...from };
  const h = system.runInterval(() => {
    try {
      dist += speed;
      pos.x = from.x + d.x * dist; pos.y = from.y + d.y * dist; pos.z = from.z + d.z * dist;
      const blocked = !airAt(dim, pos.x, pos.y, pos.z);
      const stop = blocked || dist >= maxDist || (onStep && onStep(pos, dist));
      if (stop) { system.clearRun(h); if (onEnd) onEnd({ ...pos }, blocked); }
    } catch (err) { system.clearRun(h); }
  }, 1);
  return h;
}
// شكل يركض على الأرض ويتبع ارتفاعها (يصعد/ينزل بلوكة)، يوقف عند الجدار: onStep(pos) يرجع true حتى يوقف
function runShape(dim, name, from, d, speed, maxDist, o = {}, onStep, onEnd) {
  const yaw = dirYaw(d);
  const e = shapeFx(dim, name, from, { ...o, yaw, life: Math.ceil(maxDist / speed) + 6 });
  let dist = 0;
  const pos = { ...from };
  const h = system.runInterval(() => {
    try {
      dist += speed;
      const x = from.x + d.x * dist, z = from.z + d.z * dist, gy = groundAt(dim, x, z, pos.y);
      const wall = gy - pos.y > 1.2 || !airAt(dim, x, gy + 0.5, z) || !airAt(dim, x, gy + 1.5, z);
      if (!wall) { pos.x = x; pos.z = z; pos.y = pos.y + (Math.max(pos.y - 3, gy) - pos.y) * 0.6; }
      const stop = wall || dist >= maxDist || (onStep && onStep(pos, dist));
      moveShape(e, pos, yaw);
      if (stop) { system.clearRun(h); removeFx(e); if (onEnd) onEnd({ ...pos }, wall); }
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
  if (UNBREAKABLE.has(id) || id.startsWith("sh:") || id.startsWith("minecraft:light_block")) return false;   // بلوكات الضوء: light_block_0..15
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
  { key: "blue", name: "Blue Rift", rank: "Lowly", col: "§9", rgb: [0.3, 0.65, 1], weight: 60, minRank: 0, ground: "minecraft:sculk", circle: 2, mob: 0, boss: 12, waves: [4, 6], skill: 0.25, weapon: 0.1 },
  { key: "violet", name: "Violet Rift", rank: "Vile", col: "§5", rgb: [0.65, 0.32, 1], weight: 25, minRank: 1, ground: "minecraft:crying_obsidian", circle: 1, mob: 2, boss: 20, waves: [5, 7], skill: 0.6, weapon: 0.25 },
  { key: "crimson", name: "Crimson Rift", rank: "Dread", col: "§c", rgb: [1, 0.2, 0.25], weight: 12, minRank: 2, ground: "minecraft:red_terracotta", circle: 5, mob: 4, boss: 32, waves: [6, 8], skill: 1, weapon: 0.45 },
  { key: "abyss", name: "Abyssal Rift", rank: "Cataclysm", col: "§6", rgb: [1, 0.8, 0.3], weight: 3, minRank: 3, ground: "minecraft:gilded_blackstone", circle: 0, mob: 6, boss: 48, waves: [7, 9], skill: 2, weapon: 1 },
];
const RIFT_LIFE = 24000, RIFT_ENGAGE = 14, RIFT_MAX_R = 12;
// كل أنواع أرضية الصدع (القديمة والجديدة) حتى الإرجاع يشتغل حتى لصدوع محفوظة من نسخ قبل
const RIFT_SCAR_TYPES = new Set(["minecraft:warped_nylium", "minecraft:purple_terracotta", "minecraft:crimson_nylium", "minecraft:blackstone", "minecraft:sculk", "minecraft:crying_obsidian", "minecraft:red_terracotta", "minecraft:gilded_blackstone"]);
const riftRadius = (r) => 2.4 + r.r * 0.15;                  // حجم شكل الصدع 3D (كان صغير ويضيع)
const riftShapeAt = (r) => ({ x: r.x, y: r.y + 1.6 + riftRadius(r) * 1.15, z: r.z });
const RIFT_GROUND = new Set(["minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol", "minecraft:sand", "minecraft:red_sand", "minecraft:gravel", "minecraft:stone", "minecraft:andesite", "minecraft:diorite", "minecraft:granite", "minecraft:snow", "minecraft:mycelium", "minecraft:moss_block", "minecraft:mud", "minecraft:hardened_clay", "minecraft:sandstone"]);   // التيراكوتا العادية اسمها hardened_clay ببيدروك
let rift = null;
function riftState() { return rift; }
function riftTier() { return rift ? RIFT_TIERS[rift.tier] : undefined; }
function riftSave() {
  try { world.setDynamicProperty("sh_rift", rift ? JSON.stringify({ ...rift, ent: undefined, circle: undefined, scars: rift.scars.slice(0, 700) }) : undefined); } catch (e) { /* */ }
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
    rift = { id: `r${Date.now() % 100000}`, tier: tierIdx, dim: dim.id, x: x + 0.5, y: top.y + 1, z: z + 0.5, age: 0, r: 0, phase: "growing", wave: 0, pause: 0, bossId: "", scars: [], pulse: 0,
      cracks: [...Array(7).keys()].map((k) => (k / 7) * Math.PI * 2 + Math.random() * 0.5), waveIds: [], dead: [], expect: 0, miss: 0 };
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
      if (d > r1 || d <= r0) continue;
      if (d > 2.2) {                                                          // شقوق شعاعية متعرجة تطلع من الصدع (مو قرص كامل)
        const cr = rift.cracks || (rift.cracks = [...Array(7).keys()].map((k) => (k / 7) * Math.PI * 2));
        const ang = Math.atan2(dz, dx);
        if (!cr.some((c0, k) => { let da = ang - (c0 + 0.32 * Math.sin(d * 0.55 + k)); da = Math.atan2(Math.sin(da), Math.cos(da)); return Math.abs(da) * d < 0.75; })) continue;
      }
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
      try { const b = dim.getBlock({ x, y, z }); if (b && (b.typeId === ground || RIFT_SCAR_TYPES.has(b.typeId)) && b.typeId !== type) b.setType(type); } catch (e) { /* */ }
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
  if (!boss) { (rift.waveIds = rift.waveIds || []).push(e.id); }
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
  SYS.riftWave(dim, { x: rift.x, y: rift.y, z: rift.z });
  rift.waveIds = []; rift.dead = []; rift.miss = 0; rift.expect = n === 3 ? 2 : t.waves[n - 1];
  if (n === 3) {
    later(20, () => { if (rift) { riftSpawnMob(riftMobType(), true); for (let i = 0; i < 2; i++) riftSpawnMob(riftMobType(), false); } });
  } else {
    const count = t.waves[n - 1];
    for (let i = 0; i < count; i++) later(i * 6, () => { if (rift) riftSpawnMob(riftMobType(), false); });
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
  if (rift.tier >= 2 && riftMobs().length < 6) riftSpawnMob(riftMobType(), false);
}
function closeRift(victory, killer) {
  if (!rift) return;
  const r = rift, t = RIFT_TIERS[r.tier], dim = world.getDimension(r.dim);
  rift = null;
  riftSave();
  removeFx(r.ent); removeFx(r.circle);
  const c = riftShapeAt(r);
  const imp = shapeFx(dim, `rift_${t.key}`, c, { r: riftRadius(r), s: 600, life: 16 });
  tween(12, 1, (k) => setShape(imp, "sh:r", riftRadius(r) * (1 - k)), () => { SYS.riftClose(dim, c); sfx(dim, "sh.blackhole_end", c, 1.5, 1); });
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
  try { if (rift && (rift.waveIds || []).includes(ev.deadEntity.id) && !(rift.dead || []).includes(ev.deadEntity.id)) (rift.dead = rift.dead || []).push(ev.deadEntity.id); } catch (e) { /* */ }
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
    const c = riftShapeAt(rift);
    if (!rift.ent || !valid(rift.ent)) rift.ent = shapeFx(dim, `rift_${t.key}`, c, { r: riftRadius(rift), s: 10, life: 1100 });
    else { setShape(rift.ent, "sh:r", riftRadius(rift)); moveShape(rift.ent, c); }
    if (!rift.circle || !valid(rift.circle)) rift.circle = spawnFx(dim, "circle", { x: rift.x, y: rift.y, z: rift.z }, t.circle, 3 + rift.r * 0.45, 1100);
    else setShape(rift.circle, "sh:r", 3 + rift.r * 0.45);
    if (rift.age % 40 === 0) for (let y = 2; y < 26; y += 2) vP(dim, { x: rift.x, y: rift.y + y, z: rift.z }, PT.endrod, { eye: 2 });   // عمود نور يبين من بعيد
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
        const b = riftSpawnMob(riftMobType(), true);
        for (const q of world.getAllPlayers()) say(q, `${t.col}§l[${t.name}]§r §cThe rift erupted. Its warden now roams the land.`);
        if (b) { try { b.removeTag("sh_rift"); } catch (e) { /* */ } }
        closeRift(false);
      }
      return;
    }
    // المعركة: الموجة تخلص لما ما يبقى وحش من الصدع
    const mobs = riftMobs();
    const engaged = riftPlayersNear(RIFT_ENGAGE + 6).length > 0;
    if (!rift.waveIds && engaged) { rift.waveIds = mobs.filter((m) => m.id !== rift.bossId).map((m) => m.id); rift.dead = []; rift.expect = rift.waveIds.length; }   // صدع محفوظ من نسخة قديمة
    const ids = rift.waveIds || [], dead = rift.dead || [];
    const alive = ids.filter((id) => !dead.includes(id));
    const spawnedAll = ids.length >= (rift.expect || 0);
    if (rift.wave < 3 && spawnedAll && alive.length && engaged) {
      const loaded = new Set(mobs.map((m) => m.id));
      const lost = alive.filter((id) => !loaded.has(id));
      if (lost.length) {
        rift.miss = (rift.miss || 0) + 20;
        if (rift.miss >= 100) {                                                 // 5 ثواني وانت جنب الصدع ووحوشه مو موجودة: يطلع بدالهم (ما تعبر الموجة)
          rift.waveIds = ids.filter((id) => !lost.includes(id)); rift.expect = rift.waveIds.length + lost.length; rift.miss = 0;
          lost.forEach((_, i) => later(i * 6, () => { if (rift) riftSpawnMob(riftMobType(), false); }));
        }
      } else rift.miss = 0;
    }
    if (rift.wave < 3 && spawnedAll && alive.length === 0 && engaged) {
      rift.pause += 20;
      if (rift.pause === 20) for (const q of riftPlayersNear(48)) notify(q, `${t.col}Wave ${rift.wave} cleared. The rift stirs...`, 60);
      if (rift.pause >= 100) riftStartWave(rift.wave + 1);
    }
    if (rift.wave === 3) {
      const boss = mobs.find((m) => m.id === rift.bossId);
      if (boss) { rift.pulse += 20; if (rift.pulse >= 160) { rift.pulse = 0; riftBossPulse(boss); } }
      else if (rift.bossId && engaged && rift.pause++ > 4 && !mobs.some((m) => m.id === rift.bossId)) {
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
  SYS.rhythm(dim, c, tier, r);
  if (tier >= 2) vanillaFx(dim, "minecraft:sonic_explosion", c);
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
    SYS.parry(dim, c);
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
    SYS.counter(t.dimension, c, p.location);
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
          if (now - (z.lastDmg || 0) >= 20) { z.pulse = true; try { e.applyDamage(1, { cause: EntityDamageCause.magic }); } catch (err2) { /* */ } LAW.weightPulse(z.dim, headPos(e)); }
        } else if (z.kind === "silence") {
          e.addEffect("weakness", 20, { amplifier: 1, showParticles: false });
          if (RANGED_TYPES.has(e.typeId)) {
            seen.add(e.id);
            if (now % 20 === 0) LAW.silenced(z.dim, headPos(e));
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
            LAW.bounce(z.dim, e.location);
          }
        } catch (err) { z.captured.delete(id); }
      }
    }
    // حدود كل قانون بجزيء يناسبه (الثقل: غبار حصى وحروف تنزل، الصمت: دخان وحبر، الانعكاس: لمعات، الحدود: سياج بوابة ولمعات)
    if (now % 10 === 0) LAW.border(z.dim, z.kind, z.c, z.r, now);
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
      LAW.reflectHit(attacker.dimension, { x: victim.location.x, y: victim.location.y + 1.1, z: victim.location.z }, headPos(attacker));
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
      ACCOUNT.stamp(t.dimension, headPos(t));
      popShape(t.dimension, "seal_stamp", { ...headPos(t), y: headPos(t).y + 0.55 }, 1.9, 0.75, 7, { yaw: yawOf(t.location, p.location), w: 420 });   // ختم ذهبي ينطبع على راسه
    }, 1.1, (pos, i) => ACCOUNT.shotTrail(p.dimension, pos, i));
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
      ACCOUNT.minus(t.dimension, headPos(t));
      const n = t.getDynamicProperty("sh_num");
      if (typeof n !== "number") { setNum(t, 7); numOwners.set(t.id, { e: t, pid: p.id }); }
      else decNum(t, 3, p);
      hurt(t, 2, p);
    }, 1.3, (pos, i) => ACCOUNT.shotTrail(p.dimension, pos, i));
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
      LAW.weightSlam(dim, c, 6);
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
    LAW.silenceCast(p.dimension, z.c, 8);
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
    let k = 0;
    flyShape(t.dimension, `digit_${String(n)[0]}`, a, { x: dx / l, y: dy / l, z: dz / l }, 0.9, l, { r: 0.85, s: 500 }, (pos) => { ACCOUNT.shotTrail(t.dimension, pos, k++); }, () => {
      if (!valid(o)) return;
      setNum(o, n);
      numOwners.set(o.id, { e: o, pid: p.id });
      ACCOUNT.arrive(o.dimension, headPos(o));
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
    ACCOUNT.split(t.dimension, t.location, headPos(t), { x: t.location.x - p.location.x, y: 0, z: t.location.z - p.location.z });
    later(8, () => {
      if (valid(t)) { setNum(t, a); numOwners.set(t.id, { e: t, pid: p.id }); }
      if (valid(o) && valid(t)) {
        const A = headPos(t), B = headPos(o), dx = B.x - A.x, dy = B.y - A.y, dz = B.z - A.z, l = Math.hypot(dx, dy, dz) || 1;
        let k = 0;
        flyShape(t.dimension, `digit_${String(b)[0]}`, A, { x: dx / l, y: dy / l, z: dz / l }, 0.9, l, { r: 0.7, s: 500 }, (pos) => { ACCOUNT.shotTrail(t.dimension, pos, k++); }, () => {
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
    tween(8, 1, (k) => { const zp = { x: t.location.x, y: top.y - 5.0 * k * k, z: t.location.z }; moveShape(z0, zp); ACCOUNT.zeroFall(t.dimension, { x: zp.x, y: zp.y + 1.2, z: zp.z }); }, () => {
      if (!valid(t)) return;
      shake(p, 0.18, 0.25);
      rockBurst(t.dimension, t.location, 4, 1);
      ACCOUNT.zeroSlam(t.dimension, t.location);
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
    LAW.reflectCast(p.dimension, p.location);
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
      later(i, () => LAW.pillarRise(p.dimension, pos));
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
      LAW.gavelSlam(dim, at);
      rockBurst(dim, at, 5, 1.1);
    });
    try {
      LAW.absoluteLaw(dim, r.selection, p.location);
      if (r.selection === 0) {
        p.addEffect("resistance", 100, { amplifier: 4, showParticles: false });
      } else if (r.selection === 1) {
        for (const e of enemiesNear(dim, p.location, 14, p.id)) {
          e.addEffect("slowness", 100, { amplifier: 4, showParticles: false });
          e.addEffect("weakness", 100, { amplifier: 2, showParticles: false });
          followShape(e, "weight", 100, { r: 0.35, dy: 0.5 });
          LAW.heavyOn(dim, headPos(e));
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
    // شق مكاني (بوابة + نَفَس تنين) عند الهدف، وحبل مكاني منه لك
    SPACE.rift(dim, from, { x: p.location.x - from.x, y: 0, z: p.location.z - from.z }, 1.1, 9);
    warpGate(dim, { x: from.x, y: from.y + 1.0, z: from.z }, yawOf(from, p.location), 1.1, 3);                 // بوابة عند الهدف تبلعه
    later(3, () => { if (valid(p)) warpGate(dim, { x: p.location.x + d.x * 2.2, y: p.location.y + 1.0, z: p.location.z + d.z * 2.2 }, yawOf(p.location, from), 1.1, 4); });   // وبوابة قدامك يطلع منها
    SPACE.tether(dim, { x: from.x, y: from.y + 1.1, z: from.z }, { x: p.location.x, y: p.location.y + 1.1, z: p.location.z });
    const dest = { x: p.location.x + d.x * 2.2, y: p.location.y, z: p.location.z + d.z * 2.2 };
    later(4, () => {
      if (!valid(t)) return;
      if (!safeTeleport(t, dest)) {
        const dx = p.location.x - t.location.x, dz = p.location.z - t.location.z, l = Math.hypot(dx, dz) || 1;
        try { t.applyKnockback({ x: (dx / l) * 3, z: (dz / l) * 3 }, 0.3); } catch (e) { /* */ }
      }
      SPACE.implode(dim, { x: from.x, y: from.y + 1, z: from.z }, 1.4, 10);
      SPACE.arriveBurst(dim, { x: t.location.x, y: t.location.y + 1, z: t.location.z });
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
    const pd = { x: t.location.x - p.location.x, y: 0, z: t.location.z - p.location.z }, pl = Math.hypot(pd.x, pd.z) || 1;
    const pdir = { x: pd.x / pl, y: 0, z: pd.z / pl };
    SPACE.rift(p.dimension, { x: p.location.x + pdir.x * 0.8, y: p.location.y, z: p.location.z + pdir.z * 0.8 }, pdir, 0.9, 6);
    warpGate(p.dimension, { x: p.location.x + pdir.x * 1.4, y: p.location.y + 1.1, z: p.location.z + pdir.z * 1.4 }, dirYaw(pdir), 0.9, 3);   // بوابة قدامك يطلع منها السهم
    symbolShot(p, t, "arrow_blue", () => {
      if (!valid(t)) return;
      pushAway(p.location, t, 6, 0.6);
      hurt(t, 3, p);
      // كبش مكاني: حلقات بوابة تكبر باتجاه الدفع + نفخة
      SPACE.ram(t.dimension, center3(t), pdir);
    }, 1.6, (pos, i) => { if (i % 2 === 0) vP(p.dimension, pos, PT.portal, {}); });
    return true;
  },
  swap(p) {
    const t = raycastTarget(p, 30);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    const a = { ...p.location }, b = { ...t.location };
    try { p.teleport(b, { facingLocation: a }); t.teleport(a); } catch (e) { return false; }
    // لولب مزدوج (بوابة + End Rod) بين المكانين، وشق مكاني بكل مكان
    SPACE.swap(p.dimension, a, b);
    warpGate(p.dimension, { x: a.x, y: a.y + 1.0, z: a.z }, yawOf(a, b), 1.2, 5); warpGate(p.dimension, { x: b.x, y: b.y + 1.0, z: b.z }, yawOf(b, a), 1.2, 5);
    SPACE.rift(p.dimension, a, { x: b.x - a.x, y: 0, z: b.z - a.z }, 1.1, 9); SPACE.rift(p.dimension, b, { x: a.x - b.x, y: 0, z: a.z - b.z }, 1.1, 9);
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
    safeTeleport(p, dest, t.location);
    // المكان ينطوي: انضمام بمكانك، خط تجعيدة أبيض ونَفَس تنين لحد الهدف، وانفلاق بوابة عنده
    SPACE.fold(p.dimension, start, dest, center3(t));
    warpGate(p.dimension, { x: start.x, y: start.y + 1.0, z: start.z }, yawOf(start, dest), 1.2, 1);
    warpGate(p.dimension, { x: dest.x, y: dest.y + 1.0, z: dest.z }, yawOf(dest, t.location), 1.2, 3);
    popShape(p.dimension, "space_cube", headPos(t), 0.2, 1.8, 6, { s: -900 });
    hurt(t, 9, p);
    pushAway(p.location, t, 1.2, 0.3);
    sfx(p.dimension, "sh.fold", t.location, 1.1);
    shake(p, 0.15, 0.15);
    return true;
  },
  spacecollapse(p) {
    const list = enemiesNear(p.dimension, p.location, 12, p.id);
    if (list.length === 0) { notify(p, "§cNo enemies nearby", 40); return false; }
    const d = flatDir(p), dim = p.dimension;
    const c = { x: p.location.x + d.x * 5, y: p.location.y, z: p.location.z + d.z * 5 };
    SPACE.collapseCharge(dim, c);
    warpGate(dim, { x: c.x, y: c.y + 1.6, z: c.z }, yawOf(c, p.location), 2.6, 10);                          // بوابة ضخمة تبلع الكل
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
      SPACE.collapseBoom(dim, c);
      for (const e of enemiesNear(dim, c, 4, p.id)) hurt(e, 6, p);
      rockBurst(dim, c, 5, 1.2);
    });
    return true;
  },

  // ── ناسج الصدى ──
  echostrike(p) {
    { const old = echoReady.get(p.id); if (old) removeFx(old.glyph); }
    echoReady.set(p.id, { until: system.currentTick + 160, glyph: followShape(p, "echo_glyph", 160, { r: 0.55, dy: 0.75, s: 140 }) });
    sfx(p.dimension, "sh.echostrike", p.location);
    // حلقات الـShrieker تصعد وراك (4 ثواني، وتنعاد مرة ثانية لو الصدى بعده جاهز) + نوتات وسكلك حولك
    const back = () => { const d0 = flatDir(p); return { x: p.location.x - d0.x * 0.7, y: p.location.y, z: p.location.z - d0.z * 0.7 }; };
    ECHO.strikeArm(p.dimension, back());
    later(80, () => { const er = echoReady.get(p.id); if (er && valid(p) && system.currentTick <= er.until) vP(p.dimension, { ...back(), y: p.location.y + 0.1 }, PT.shriek, { eye: 0 }); });
    notify(p, "§3Your next hit will echo", 50);
    return true;
  },
  echoseal(p) {
    const t = raycastTarget(p, 24);
    if (!t) { notify(p, "§cNo target in front of you", 30); return false; }
    echoMarks.set(t.id, { sum: 0 });
    const sealGlyph = followShape(t, "echo_glyph", 100, { r: 0.7, dy: 0.5, s: 220 });              // رمز الصدى يحوم فوق الهدف
    // نبضة سكلك تمشي من صدرك للهدف، وتختمه بحلقات Shrieker، وبعدها حلقة شحنات سكلك تدور على صدره لحد الانفجار
    const dimE = p.dimension;
    ECHO.pulseTo(dimE, { x: p.location.x, y: p.location.y + 1.3, z: p.location.z }, center3(t), () => { if (valid(t)) ECHO.sealMark(t.dimension, center3(t)); });
    let tk = 0;
    const hm = system.runInterval(() => { try { tk += 5; if (!valid(t) || tk >= 100 || !echoMarks.has(t.id)) { system.clearRun(hm); return; } ECHO.sealTick(t.dimension, center3(t), tk); } catch (e) { system.clearRun(hm); } }, 5);
    sfx(p.dimension, "sh.echoseal", p.location);
    system.runTimeout(() => {
      const m = echoMarks.get(t.id);
      echoMarks.delete(t.id);
      if (!m || !valid(t)) return;
      hurt(t, Math.max(4, m.sum), p);
      ECHO.sealBlast(t.dimension, center3(t));
      removeFx(sealGlyph);
      popShape(t.dimension, "echo_pulse", t.location, 0.3, 2.6, 10, { ease: "out" });
      popShape(t.dimension, "sound_ring", center3(t), 0.4, 1.8, 7, { yaw: yawOf(t.location, p.location) });
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
    const wave = (dmg, rmax, pitch, k0) => {
      sfx(dim, "sh.echowave", c, 1, pitch);
      shake(p, 0.12, 0.15);
      // جبهة موجة صوتية (قوس 80°) تتقدم قدامك: نوتات وسكلك، وحلقة Warden كل 3 تكات بنصها
      ECHO.wave(dim, c, { x: d.x, y: 0, z: d.z }, rmax, k0);
      { const T = Math.ceil(rmax / 0.9), yw = dirYaw({ x: d.x, y: 0, z: d.z });
        const sw = shapeFx(dim, "sound_wave", { x: c.x + d.x * 0.8, y: c.y + 0.9, z: c.z + d.z * 0.8 }, { r: 1.0, yaw: yw, life: T + 3 });
        tween(T, 1, (k) => { const q = 0.8 + k * (rmax - 3.0); moveShape(sw, { x: c.x + d.x * q, y: c.y + 0.9, z: c.z + d.z * q }, yw); setShape(sw, "sh:r", 1.0 + 2.2 * k); }, () => removeFx(sw)); }
      for (const e2 of enemiesNear(dim, c, rmax, p.id)) {
        const vx = e2.location.x - c.x, vz = e2.location.z - c.z, l = Math.hypot(vx, vz) || 1;
        if ((vx / l) * d.x + (vz / l) * d.z < 0.64) continue;
        later(Math.ceil(l / 0.9), () => {
          if (!valid(e2)) return;
          hurt(e2, dmg, p);
          pushAway(c, e2, 1.6, 0.35);
          ECHO.hit(dim, center3(e2), k0);
        });
      }
    };
    wave(7, 12, 1, 0);
    later(10, () => { if (valid(p)) wave(4, 14, 0.8, 2); });
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
        // حلقة Warden عليك + موجة أرضية من النوتات والسكلك تتوسع لحد نصف القطر (كل نبضة بلون نوتة)
        ECHO.chorusPulse(p.dimension, p.location, r, i);
        popShape(p.dimension, "echo_pulse", p.location, 0.6, r, 10, { ease: "out", s: 40 + i * 30 });
        for (const e of enemiesNear(p.dimension, p.location, r, p.id)) {
          hurt(e, dmgs[i], p);
          pushAway(p.location, e, 1.4, 0.3);
          ECHO.chorusHit(e.dimension, center3(e), i);
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
    const launch = { x: from.x + d.x * 0.8, y: from.y + d.y * 0.8, z: from.z + d.z * 0.8 };
    IRON.fistLaunch(p.dimension, launch, d);
    flyShape(p.dimension, "iron_fist", launch, d, 1.3, Math.max(1, l - 0.9), { r: 1.5 }, (pos) => { IRON.fistTrail(p.dimension, pos, d); }, () => {
      if (!valid(t)) return;
      hurt(t, 10, p);
      pushAway(p.location, t, 2.8, 0.5);
      IRON.fistImpact(t.dimension, center3(t), d, t.location);
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
    // انفجار شحنة ريح حقيقي عند رجليك، وبعدها دوامات ريح صغيرة ودخان أبيض يتخلف وراك وانت تركض (كل 3 تكات، وانفجار ريح كل 12)
    WIND.runStart(p.dimension, p.location);
    popShape(p.dimension, "wind_ring", p.location, 0.4, 1.8, 8, { s: 400 });                 // حلقة عصفة عند الانطلاق
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 3;
        if (!valid(p) || t > 100) { system.clearRun(h); return; }
        const d = flatDir(p), v = p.getVelocity();
        if (Math.hypot(v.x, v.z) < 0.05) return;
        WIND.runTrail(p.dimension, p.location, d, t % 12 === 0);
        if (t % 6 === 0) shapeFx(p.dimension, "wind_trail", { x: p.location.x - d.x * 0.7, y: p.location.y, z: p.location.z - d.z * 0.7 }, { r: 1.0, s: 720, yaw: dirYaw({ x: d.x, y: 0, z: d.z }), life: 9 });   // شرائط ريح تلف حول الرجلين
      } catch (e) { system.clearRun(h); }
    }, 3);
    return true;
  },
  windleap(p) {
    const d = flatDir(p);
    try {
      p.applyKnockback({ x: d.x * 2.6, z: d.z * 2.6 }, 0.9);
      p.addEffect("slow_falling", 80, { amplifier: 0, showParticles: false });
    } catch (e) { return false; }
    WIND.leapLaunch(p.dimension, p.location);
    popShape(p.dimension, "wind_ring", p.location, 0.5, 2.4, 8, { s: 500 });
    for (let i = 2; i <= 16; i += 2) later(i, () => { if (valid(p)) WIND.leapTrail(p.dimension, p.location); });
    wingsOn(p, 40);
    sfx(p.dimension, "sh.push", p.location, 1, 1.3);
    return true;
  },
  gale(p) {
    const dim = p.dimension;
    const list = enemiesNear(dim, p.location, 7, p.id);
    // انفجار ريح البريز الكبير بالمنتصف، و3 حلقات من انفجارات شحنة الريح تتوسع، وغبار أرضي ودخان
    WIND.gale(dim, p.location);
    { const cy = shapeFx(dim, "cyclone", p.location, { r: 0.4, s: 220, life: 32 });
      tween(28, 1, (k) => { if (valid(p)) moveShape(cy, p.location); setShape(cy, "sh:r", k < 0.25 ? 0.4 + 1.2 * (k / 0.25) : k < 0.7 ? 1.6 : 1.6 * (1 - (k - 0.7) / 0.3)); }, () => removeFx(cy)); }
    popShape(dim, "wind_ring", p.location, 0.8, 7.0, 10, { s: 300, ease: "out" });
    for (const e of list) {
      hurt(e, 3, p);
      pushAway(p.location, e, 2.6, 0.55);
      WIND.galeHit(dim, center3(e));
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
    spawnFx(dim, "circle", p.location, 6, 9, 66);            // دائرة الساعة (ميناء 60 علامة + عقربين)
    // ساعة كبيرة فوقك عقاربها تدور، وساعة صغيرة فوق كل عدو متجمد
    shapeFx(dim, "clock", { x: p.location.x, y: p.location.y + 3.4, z: p.location.z }, { r: 2.2, s: 40, life: 62 });
    // حروف السحر تنسحب للساعة، موجة لمعات وثلج، والمتجمدين يتساقط عليهم ثلج، ونبضة "تك" كل ثانية
    LAW.timeCast(dim, { x: p.location.x, y: p.location.y + 3.4, z: p.location.z }, p.location, 9);
    { let tt = 0; const at0 = { ...p.location };
      const th = system.runInterval(() => { try { tt += 10; if (tt > 60) { system.clearRun(th); return; } for (const e of list) if (valid(e)) LAW.frozen(dim, headPos(e)); if (tt % 20 === 0) LAW.tick(dim, at0, 9); } catch (err) { system.clearRun(th); } }, 10); }
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
  // كل سلاح بجزيء ماينكرافت يناسبه: ذهب يلف (خنجر)، لهب حقيقي (ساطور)، لمعات End Rod (سيف القسم)، ريح زرقاء (سيف الظل)،
  // نجوم خضر (مطرقة)، غبار أحمر (رمح)، نَفَس تنين (مخالب)
  for (let i = 0; i < n; i++) {
    const u = Math.random(), b = weaponAuraPoint(p, id, id === "sh:stone_maul" ? 0.85 + u * 0.15 : u);
    WEAPON.aura(dim, id, b, t, i);
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

// يوقع شكل (رمح نور، سيف شبح) من 7 بلوكات فوق للأرض بتسارع خلال fall تك، ويبقى life تك. يرجع الكيان
function dropShape(dim, name, x, y, z, r, fall, life, yaw) {
  const e = shapeFx(dim, name, { x, y: y + 7, z }, { r, yaw: yaw ?? Math.random() * 360, life: fall + life });
  if (e) tween(fall, 1, (q) => moveShape(e, { x, y: y + 7 * (1 - q * q), z }));
  return e;
}
// رمح نور ينزل على مكان: يضرب القريب منه عند الوصول
function lanceStrike(p, x, z, dmg, delay = 0) {
  const dim = p.dimension, y = groundAt(dim, x, z, p.location.y);
  later(delay, () => {
    if (!valid(p)) return;
    dropShape(dim, "light_lance", x, y, z, 1.25, 4, 10);
    later(4, () => {
      for (const e of enemiesNear(dim, { x, y, z }, 1.9, p.id)) { hurt(e, dmg, p); effect(e, "weakness", 50, 0); }
      WEAPON.lanceHit(dim, { x, y, z });
      sfx(dim, "sh.kat_wave", { x, y, z }, 0.7, 1.9);
    });
  });
}
// سيف شبح ينزل على مكان (زينة + ضربة اختيارية)
function ghostSword(p, x, z, dmg, delay = 0, r = 1.2) {
  const dim = p.dimension, y = groundAt(dim, x, z, p.location.y);
  later(delay, () => {
    if (!valid(p)) return;
    dropShape(dim, "ghost_sword", x, y, z, r, 3, 12);
    later(3, () => {
      if (dmg > 0) for (const e of enemiesNear(dim, { x, y, z }, 1.7, p.id)) hurt(e, dmg, p);
      WEAPON.ghostLand(dim, { x, y, z });
      sfx(dim, "sh.dagger_hit", { x, y, z }, 0.7, 0.7);
    });
  });
}
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
      // هلالين نار حقيقية (لهب المشعل يتحرك مع الشطرة) + ألسنة لهب كبيرة وجمرات ودخان نار
      WEAPON.emberArc(dim, o, d);
      popShape(dim, "slash_fire", { x: o.x, y: o.y + 0.95, z: o.z }, 1.7, 2.5, 6, { yaw: dirYaw({ x: d.x, y: 0, z: d.z }), p: 84, a: -30, w: 300 });   // هلال نار يكنس قدامك
      sfx(dim, "sh.cleaver_hit", o, 1.2, 0.7);
      shake(p, 0.15, 0.2);
      return true;
    } },
    { name: "Inferno Spin", cd: 240, desc: "Spin: a ring of fire hits everything around you", fn(p) {
      const dim = p.dimension;
      effect(p, "resistance", 20, 1);
      // حلقتين نار تلف حولك بعكس بعض (تترسم كل تك) وبكل ضربة حلقة لهب أرضية وجمرات
      tween(12, 1, (k, tt) => { if (valid(p)) WEAPON.infernoSpin(dim, p.location, tt); });
      { const yw = dirYaw({ ...flatDir(p), y: 0 });
        const s1 = shapeFx(dim, "slash_fire", { x: p.location.x, y: p.location.y + 1.1, z: p.location.z }, { r: 2.2, p: 90, yaw: yw, s: 1500, life: 13 });
        const s2 = shapeFx(dim, "slash_fire", { x: p.location.x, y: p.location.y + 0.5, z: p.location.z }, { r: 1.9, p: 90, yaw: yw + 180, s: -1300, life: 13 });
        const fr = popShape(dim, "fire_ring", p.location, 1.0, 3.2, 6, { s: 500 });
        tween(12, 1, () => { if (!valid(p)) return; moveShape(s1, { x: p.location.x, y: p.location.y + 1.1, z: p.location.z }); moveShape(s2, { x: p.location.x, y: p.location.y + 0.5, z: p.location.z }); moveShape(fr, p.location); }); }
      for (const k of [0, 6]) later(k, () => {
        if (!valid(p)) return;
        WEAPON.infernoBurst(dim, p.location);
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
      symbolShot(p, t, "arrow_gold", () => { if (valid(t)) WEAPON.sunBind(t.dimension, t.location); }, 1.6, (pos, i) => vP(p.dimension, pos, PT.wax, { c: [1, 0.85, 0.35] }));
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
        WEAPON.stab(t.dimension, center3(t), p.location, i, last);           // هلال ذهبي صغير بزاوية مختلفة كل طعنة، والأخيرة انفجار شرار ذهبي
        popShape(t.dimension, "slash_gold", center3(t), last ? 1.0 : 0.55, last ? 1.5 : 0.85, 3, { yaw: yawOf(t.location, p.location), a: (i * 67) % 180 - 90 });
        sfx(t.dimension, "sh.dagger_hit", t.location, 1, 1.2 + i * 0.08);
        if (last) shake(p, 0.15, 0.15);
      });
      return true;
    } },
  ],
  "sh:silver_oath": [
    { name: "Oath Cleave", cd: 140, desc: "A wide silver crescent in front of you that pushes enemies back", fn(p) {
      const dim = p.dimension, o = p.location, d = flatDir(p);
      const c = { x: o.x + d.x * 1.6, y: o.y + 1.0, z: o.z + d.z * 1.6 };
      WEAPON.oathCleave(dim, o, d);                                        // هلال نور: لمعات End Rod تبقى بالهوا + شرر أبيض
      popShape(dim, "slash_silver", { x: o.x, y: o.y + 1.0, z: o.z }, 1.9, 2.8, 6, { yaw: dirYaw({ x: d.x, y: 0, z: d.z }), p: 86, a: 25, w: -260 });
      let n = 0;
      for (const e of enemiesNear(dim, o, 5, p.id)) {
        if (!inFront(p, e, 0.2)) continue;
        hurt(e, 9, p); n++;
        pushAway(o, e, 1.3, 0.35);
        effect(e, "weakness", 60, 0);
        WEAPON.silverCut(dim, center3(e), o, n);
      }
      sfx(dim, "sh.kat_wave", o, 1.0, 1.4);
      shake(p, 0.08, 0.15);
      // رماح نور تنزل من السما قدامك بشكل مثلث، وحدة ورا وحدة
      const rr = katanaRight(d);
      [[3.6, 0, 3], [5.4, -1.7, 6], [5.4, 1.7, 9]].forEach(([dist, off, dl]) => lanceStrike(p, o.x + d.x * dist + rr.x * off, o.z + d.z * dist + rr.z * off, 4, dl));
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
      WEAPON.silverStep(dim, from, to);                                    // خط لمعات End Rod وشرر أبيض + حلقة بالبداية والنهاية
      const len = Math.hypot(to.x - from.x, to.z - from.z), hit = new Set();
      for (let i = 0; i <= 10; i++) {
        const t = i / 10, pt = { x: from.x + (to.x - from.x) * t, y: from.y + 1, z: from.z + (to.z - from.z) * t };
        for (const e of enemiesNear(dim, pt, 1.6, p.id)) {
          if (hit.has(e.id)) continue;
          hit.add(e.id);
          later(2 + hit.size * 2, () => {
            if (!valid(e)) return;
            hurt(e, 8, p);
            lanceStrike(p, e.location.x, e.location.z, 4, 1);
            WEAPON.silverCut(dim, center3(e), from, hit.size);
            popShape(dim, "slash_silver", center3(e), 0.6, 1.0, 4, { yaw: yawOf(e.location, from), a: hit.size % 2 ? 45 : -45 });
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
      WEAPON.shadowPuff(dim, from);
      safeTeleport(p, dest, t.location);
      WEAPON.shadowPuff(dim, dest);
      sfx(dim, "sh.kat_step", dest, 1.1, 1.1);
      for (let i = 0; i < 3; i++) { const a = i * 2.0944 + 0.5; ghostSword(p, t.location.x + Math.cos(a) * 1.8, t.location.z + Math.sin(a) * 1.8, 0, 2 + i, 1.1); }
      later(1, () => {
        if (!valid(t)) return;
        hurt(t, 8, p);
        WEAPON.shadowCut(dim, center3(t), p.location, 45);
        popShape(dim, "slash_teal", center3(t), 0.6, 1.05, 4, { yaw: yawOf(t.location, p.location), a: 45 });
        effect(t, "blindness", 40, 0);
        effect(t, "slowness", 40, 1);
      });
      later(5, () => {
        if (!valid(t)) return;
        hurt(t, 6, p);
        WEAPON.shadowCut(dim, center3(t), p.location, -45);
        popShape(dim, "slash_teal", center3(t), 0.6, 1.05, 4, { yaw: yawOf(t.location, p.location), a: -45 });
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
        WEAPON.shadowPuff(dim, spot);
        hurt(e, 7, p);
        effect(e, "weakness", 60, 0);
        WEAPON.shadowCut(dim, center3(e), spot, i % 2 ? 40 : -40);
        popShape(dim, "slash_teal", center3(e), 0.6, 1.1, 4, { yaw: yawOf(e.location, spot), a: i % 2 ? 40 : -40 });
        ghostSword(p, e.location.x, e.location.z, 3, 1, 1.4);
        sfx(dim, "sh.dagger_hit", e.location, 1, 1.0 + i * 0.1);
      }));
      // الخاتمة: ثمانية سيوف شبح تنزل بحلقة حواليك وموجة بنفسجية
      later(list.length * 4 + 6, () => {
        if (!valid(p)) return;
        for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; ghostSword(p, p.location.x + Math.cos(a) * 3.6, p.location.z + Math.sin(a) * 3.6, 0, i % 4, 1.1); }
        WEAPON.shadowWave(dim, p.location);
        for (const e of enemiesNear(dim, p.location, 4.8, p.id)) { hurt(e, 3, p); pushAway(p.location, e, 0.8, 0.25); }
        sfx(dim, "sh.kat_wave", p.location, 1, 0.8);
      });
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
        WEAPON.rake(dim, center3(t), { x: t.location.x - p.location.x, y: 0, z: t.location.z - p.location.z }, a);
        popShape(dim, "claw_violet", center3(t), 0.45, 0.8, 4, { yaw: yawOf(t.location, p.location), a: a + 20 });
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
          WEAPON.clawStorm(dim, c, { x: Math.cos(a), y: 0, z: Math.sin(a) }, w * 20 - 20);
          popShape(dim, "claw_violet", c, 0.5, 0.85, 4, { yaw: dirYaw({ x: Math.cos(a), y: 0, z: Math.sin(a) }) + 180, a: w * 20 - 20 });
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
      WEAPON.quake(dim, cc, 3.6);                                          // نفخات زئير + غبار + موجة حصى
      { const sr = shapeFx(dim, "stone_ring", { x: cc.x, y: gy + 1 - 1.4, z: cc.z }, { r: 1.8, yaw: Math.random() * 360, life: 26 });
        tween(5, 1, (k) => moveShape(sr, { x: cc.x, y: gy + 1 - 1.4 * (1 - k), z: cc.z }), () => later(14, () => tween(6, 1, (k) => moveShape(sr, { x: cc.x, y: gy + 1 - 1.6 * k, z: cc.z })))); }
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
        WEAPON.fissure(dim, c);
        { const sp = shapeFx(dim, "stone_ring", { x: c.x, y: c.y - 0.8, z: c.z }, { r: 0.55, yaw: t * 47, life: 16 });
          tween(3, 1, (k) => moveShape(sp, { x: c.x, y: c.y - 0.8 * (1 - k), z: c.z }), () => later(8, () => tween(5, 1, (k) => moveShape(sp, { x: c.x, y: c.y - k, z: c.z })))); }
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
          WEAPON.spearTrail(dim, pos, dir);
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
        flyShape(dim, "spear_proj", top, { x: 0, y: -1, z: 0 }, 1.4, 12.5, { r: 1.2 }, (pos) => { WEAPON.spearTrail(dim, pos, { x: 0, y: -1, z: 0 }); }, (end) => {
          for (const e of enemiesNear(dim, end, 1.8, p.id)) { hurt(e, 6, p); try { e.setOnFire(3, true); } catch (err) { /* */ } }
          fling(dim, "rock_chunk", end, 1, 0.7);
          WEAPON.spearLand(dim, end);
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
    removeFx(er.glyph);
    ECHO.strikeMark(t.dimension, center3(t));
    popShape(t.dimension, "sound_ring", center3(t), 0.3, 0.9, 6, { yaw: yawOf(t.location, p.location) });
    system.runTimeout(() => {
      if (!valid(t)) return;
      hurt(t, 6, p);
      ECHO.echo(t.dimension, center3(t));
      popShape(t.dimension, "echo_glyph", center3(t), 0.4, 1.3, 8, { s: 600 });                                         // الصدى: الرمز ينفجر على الهدف
      popShape(t.dimension, "sound_ring", center3(t), 0.6, 1.6, 7, { yaw: yawOf(t.location, p.location) });
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
function flyShard(p, d, len, r = 0.8, name = "crystal_spike", onEnd, onStep) {
  const o = eyePos(p);
  const from = { x: o.x + d.x * 1.2, y: o.y - 0.35 + d.y * 1.2, z: o.z + d.z * 1.2 };
  return flyShape(p.dimension, name, from, d, 2.4, Math.max(1, len - 1.2), { r, w: 540 }, onStep, onEnd);
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
    TRAIT.fangs(p.dimension, p.location, { x: p.location.x + d0.x * 1.3, y: p.location.y + 1.3, z: p.location.z + d0.z * 1.3 });
  } else if (id === "wings") {
    const d = flatDir(p);
    try { p.applyKnockback({ x: d.x * 0.9, z: d.z * 0.9 }, 1.1); } catch (e) { /* */ }
    effect(p, "slow_falling", 240 * m, 0);
    effect(p, "jump_boost", 200 * m, 1);
    effect(p, "speed", 200 * m, 1);
    wingsOn(p, Math.round(200 * m));
    TRAIT.wings(p.dimension, p.location);
  } else if (id === "eye") {
    effect(p, "night_vision", 300 * m, 0);
    popShape(p.dimension, "hunter_eye", { x: p.location.x, y: p.location.y + 3, z: p.location.z }, 0.4, 2.2, 12, { yaw: dirYaw({ ...flatDir(p), y: 0 }) + 180 });
    const list = enemiesNear(p.dimension, p.location, 24, p.id).slice(0, 10);
    TRAIT.eyeScan(p.dimension, p.location);                       // نبضة رادار ذهبية
    for (const e of list) {
      huntMarks.set(e.id, { pid: p.id, until: now + 200 * m });
      TRAIT.eyeMark(e.dimension, center3(e));
      followShape(e, "hunter_eye", Math.round(200 * m), { r: 0.7, dy: 0.9, faceYaw: () => valid(p) && valid(e) ? yawOf(e.location, p.location) : undefined });
    }
    notify(p, list.length ? `§eMarked ${list.length} enemies` : "§7No enemies nearby, but your vision improved", 50);
  }
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
    try { hurt(ev.hurtEntity, 2, a); TRAIT.eyeBonus(ev.hurtEntity.dimension, headPos(ev.hurtEntity)); } finally { huntBusy = false; }
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
      TRAIT.fangsBite(t.dimension, center3(t), p.location);
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
      const len = 20, o0 = eyePos(p);
      // الرمح يترك نَفَس تنين بنفسجي واكف ولولب لمعات End Rod على مساره
      let prev = { x: o0.x + base.x * 1.2, y: o0.y - 0.35 + base.y * 1.2, z: o0.z + base.z * 1.2 }, k = 0;
      CRYSTAL.muzzle(p.dimension, prev, base);
      flyShard(p, base, len, 1.5, "crystal_lance", undefined, (pos) => { CRYSTAL.lanceStep(p.dimension, prev, pos, base, k++); prev = { ...pos }; });
      hits.forEach((h) => later(Math.ceil(h.t / 2.4), () => {
        if (!valid(h.e)) return;
        hurt(h.e, 10, p); pushAway(p.location, h.e, 0.6, 0.15); addCrystal(h.e, p, 1);
        CRYSTAL.lanceHit(h.e.dimension, center3(h.e));
      }));
      sfx(p.dimension, "sh.push", p.location, 1.1, 1.6);
      shake(p, 0.1, 0.12);
      return true;
    }
    // 3 شوكات بلورية حقيقية تطير وتلزق بالأعداء: رشة نجوم وردية عند الإطلاق، وأثر نجوم ولمعات وراها
    { const o0 = eyePos(p); CRYSTAL.muzzle(p.dimension, { x: o0.x + base.x * 1.1, y: o0.y - 0.3 + base.y * 1.1, z: o0.z + base.z * 1.1 }, base); }
    for (const ang of [-12, 0, 12]) {
      const d = rotY(base, ang);
      const hits = rayHits(p, d, 16, 1.1);
      const len = hits.length ? hits[0].t : 16;
      const e = hits.length ? hits[0].e : undefined;
      let k = 0;
      flyShard(p, d, len, 1.0, "crystal_spike", () => {
        if (!e || !valid(e)) return;
        hurt(e, 4, p);
        addCrystal(e, p, 1);
        CRYSTAL.shardHit(e.dimension, center3(e));
      }, (pos) => { CRYSTAL.shardTrail(p.dimension, pos, k++, d); });
    }
    sfx(p.dimension, "sh.push", p.location, 0.9, 1.9);
    return true;
  },
  crystalshield(p) {
    effect(p, "absorption", 200, 2);
    sfx(p.dimension, "sh.reflect", p.location, 1, 1.5);
    popShape(p.dimension, "crystal_cluster", p.location, 0.2, 1.2, 6);
    CRYSTAL.shieldForm(p.dimension, p.location);
    // 4 دروع بلورية سداسية تدور حولك وتواجه الخارج (لمعة End Rod على درع كل 8 تكات، وتتكسر بالنهاية)
    let t = 0;
    const plates = [0, 1, 2, 3].map(() => shapeFx(p.dimension, "crystal_plate", p.location, { r: 1.3, life: 206 }));
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p) || t > 200) {
          system.clearRun(h);
          plates.forEach((f) => { try { if (f && valid(f)) CRYSTAL.shatter(f.dimension, { x: f.location.x, y: f.location.y + 0.4, z: f.location.z }); } catch (err) { /* */ } removeFx(f); });
          if (valid(p)) fling(p.dimension, "crystal_gem", center3(p), 5, 1, 0.6, 1);
          return;
        }
        plates.forEach((f, i) => {
          if (!f) return;
          const a = t * 0.12 + (i / 4) * Math.PI * 2;
          const pos = { x: p.location.x + Math.cos(a) * 1.25, y: p.location.y + 1.0 + Math.sin(t * 0.1 + i) * 0.15, z: p.location.z + Math.sin(a) * 1.25 };
          moveShape(f, pos, dirYaw({ x: Math.cos(a), y: 0, z: Math.sin(a) }));
          if (t % 8 === 0 && i === (t / 8) % 4) CRYSTAL.shieldGlint(p.dimension, { x: pos.x, y: pos.y + 0.4, z: pos.z });
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
    CRYSTAL.prisonGrow(t.dimension, t.location, size * 0.75);
    sfx(p.dimension, "sh.boundary", t.location, 1, 1.4);
    symbolShot(p, t, "crystal_spike", undefined, 2.2);
    let k2 = 0;
    const h = system.runInterval(() => {
      try {
        k2 += 4;
        if (!valid(t) || k2 > dur) {
          system.clearRun(h); removeFx(cage);
          if (valid(t)) { CRYSTAL.prisonBreak(t.dimension, center3(t)); fling(t.dimension, "crystal_gem", center3(t), 5, 1, 0.6, 1); sfx(t.dimension, "sh.collapse", t.location, 0.8, 1.6); }
          return;
        }
        moveShape(cage, t.location);
        if (k2 % 8 === 0) CRYSTAL.prisonTick(t.dimension, t.location, size * 0.6);
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
      CRYSTAL.detonateLink(p.dimension, { x: p.location.x, y: p.location.y + 1.2, z: p.location.z }, center3(e));
      later(i * 2, () => {
        if (!valid(e)) return;
        hurt(e, 5 * c.n, p);
        // تفجير: عنقود بلوري يطلع من تحت العدو + انفجار عين الإندر وموجة نجوم وردية حسب عدد البلورات
        popShape(e.dimension, "crystal_cluster", e.location, 0.3, 1.2 + c.n * 0.15, 5);
        CRYSTAL.detonate(e.dimension, center3(e), c.n);
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
    TRAIT.fuse(p.dimension, p.location, TRAIT_COLOR[two[0].id], TRAIT_COLOR[two[1].id]);   // لولبين بلوني الصفتين يلتفون ببعض
    followShape(p, "fusion_rings", 40, { r: 0.95, dy: -0.95 });                                                           // حلقتين صفات متداخلات تدور حول صدرك
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
      SPACE.rewind(p.dimension, from, a.loc);
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
    // علامة المكان المحفوظ: حلقة End Rod تنبض كل ثانية لحد ما ترجع أو تخلص المدة
    const anchor = rewindAnchors.get(p.id), dimA = p.dimension, at = { ...p.location };
    const ha = system.runInterval(() => { try { if (rewindAnchors.get(p.id) !== anchor || system.currentTick > anchor.until) { system.clearRun(ha); return; } SPACE.anchorPulse(dimA, at); } catch (e) { system.clearRun(ha); } }, 20);
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
    tween(18, 1, (k, tt) => {
      const loc = { x: top.x + dx * k, y: top.y + dy * k, z: top.z + dz * k };
      moveShape(m, loc, dirYaw(d));
      STAR.meteorTrail(dim, loc, d, tt);                       // ذيل نار حقيقي ودخان نار يبقى بالسما
    }, () => {
      removeFx(m);
      sfx(dim, "sh.meteor_hit", c, 1.5, 1);
      STAR.meteorImpact(dim, c);                               // انفجار TNT الكبير + حلقة لهب + حمم + غبار + أعمدة دخان
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
    // دوامة جاذبية من جزيئات: أذرع لولبية تدور وتنسحب للمركز، وبوابة تنضم لنجم صغير بالنص
    groundBreak(dim, c, 5, { cracks: 7, ttl: 160 });
    const well = shapeFx(dim, "grav_well", c, { r: 0.3, s: -140, life: life + 14 });                 // قمع جاذبية بأذرع لولبية ونواة سودة
    tween(10, 1, (k) => setShape(well, "sh:r", 0.3 + 4.9 * k));
    sfx(dim, "sh.gravwell", c, 1.2, 1);
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        STAR.wellTick(dim, c, t);
        for (const e of enemiesNear(dim, c, 7.5, p.id)) {
          const d = Math.hypot(e.location.x - c.x, e.location.z - c.z);
          pullTo(c, e, Math.min(0.5, 0.1 + 0.05 * (7.5 - d)));
          try { e.addEffect("slowness", 20, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
          if (t % 10 === 0) hurtS(e, 2, p);
        }
        if (t >= life) {
          system.clearRun(h);
          STAR.wellEnd(dim, c);
          tween(8, 1, (k) => setShape(well, "sh:r", 5.2 * (1 - k)), () => removeFx(well));
          sfx(dim, "sh.pull", c, 1, 0.7);
        }
      } catch (err) { system.clearRun(h); }
    }, 2);
    return true;
  },
  // 3) مدار النجوم: 3 نجوم تدور حولك وتضرب كل من يلمسها
  orbit(p) {
    const dim = p.dimension, life = 200, orbs = [], hitCd = new Map();
    // 3 نجوم من جزيئات (نواة لمعات + شرار ذهبي) تدور وتترك ذيل End Rod يرسم المدار
    effect(p, "resistance", life, 0);
    sfx(dim, "sh.orbit", p.location, 1.1, 1);
    STAR.orbCast(dim, p.location);
    for (let i = 0; i < 3; i++) { const o = shapeFx(dim, "star5", p.location, { r: 0.45, s: 420, life: life + 6 }); if (o) orbs.push(o); }
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
          STAR.orbTick(dim, loc, i);
          moveShape(orbs[i], loc);
          for (const e of enemiesNear(dim, loc, 1.5, p.id)) {
            if ((hitCd.get(e.id) ?? 0) > t) continue;
            hitCd.set(e.id, t + 10);
            hurtS(e, 4, p);
            pushAway(p.location, e, 0.5, 0.2);
            STAR.orbHit(dim, center3(e));
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
    // نجمة لمعات تومض فوق كل عدو، وخطوط End Rod منقطة بينهم (تبقى بالهوا)، وبالأخير خطوط شرر وصاعقة نجمية
    for (let k = 0; k <= 42; k += 6) later(k, () => { for (const e of list) if (valid(e)) STAR.starMark(dim, headPos(e)); });
    for (const e of list) followShape(e, "star5", 46, { r: 0.32, s: 300, dy: 0.55 });
    const beams = [];
    const linkBeams = () => { for (let i = 0; i < list.length - 1; i++) { const a = list[i], b = list[i + 1]; if (!valid(a) || !valid(b)) continue; if (beams[i] && valid(beams[i])) aimBeam(beams[i], center3(a), center3(b), 0.7); else beams[i] = beamShape(dim, center3(a), center3(b), 46, 0.7); } };
    for (const k of [4, 14, 26, 36, 44]) later(k, linkBeams);
    const draw = (bright) => {
      for (let i = 0; i < list.length - 1; i++) {
        const a = list[i], b = list[i + 1];
        if (!valid(a) || !valid(b)) continue;
        STAR.starLine(dim, center3(a), center3(b), bright);
      }
    };
    for (const k of [4, 26]) later(k, () => draw(false));
    later(44, () => {
      draw(true);
      const bonus = list.length >= 4 ? 4 : 0;
      for (const e of list) {
        if (!valid(e)) continue;
        hurtS(e, 8 + bonus, p);
        STAR.starfall(dim, center3(e));
        dropShape(dim, "star5", e.location.x, e.location.y + 1.0, e.location.z, 0.7, 4, 5);
        sfx(dim, "sh.const_zap", e.location, 1, 1 + Math.random() * 0.2);
      }
      shake(p, 0.12, 0.15);
      later(4, () => beams.forEach(removeFx));
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
    STAR.dash(dim, from, to);                                   // ذيل مذنب: End Rod واكف + شرار ذهبي + دخان
    beamShape(dim, { x: from.x, y: from.y + 1.0, z: from.z }, { x: to.x, y: to.y + 1.0, z: to.z }, 14, 1.4);
    popShape(dim, "comet", { x: to.x + d.x * 0.6, y: to.y + 1.0, z: to.z + d.z * 0.6 }, 1.5, 0.4, 10, { yaw: dirYaw({ x: d.x, y: 0, z: d.z }) });
    const seg = { x: to.x - from.x, z: to.z - from.z }, sl = Math.hypot(seg.x, seg.z) || 1;
    for (const e of enemiesNear(dim, from, sl + 4, p.id)) {
      const vx = e.location.x - from.x, vz = e.location.z - from.z;
      const proj = (vx * seg.x + vz * seg.z) / sl;
      if (proj < -0.5 || proj > sl + 0.5) continue;
      if (Math.abs(vx * seg.z - vz * seg.x) / sl > 1.8) continue;
      hurtS(e, 9, p);
      try { e.addEffect("slowness", 40, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
      STAR.dashHit(dim, center3(e));
    }
    effect(p, "resistance", 20, 4);
    STAR.dashEnd(dim, to);
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
        STAR.holeTick(dim, c, t);                                   // قرص تراكم من نَفَس التنين يلف للداخل + بوابة تنسحب
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
          STAR.holeCollapse(dim, c);
          later(8, () => {
            STAR.holeBoom(dim, c, g);
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
    const core = shapeFx(dim, "nova_core", { x: p.location.x, y: p.location.y + 3.0, z: p.location.z }, { r: 0.3, life: charge + 6 });
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p)) { system.clearRun(h); return; }
        const c = { x: p.location.x, y: p.location.y + 1.0, z: p.location.z };
        const k = t / charge;
        // شحن: بوابة تنسحب لنواة فوق راسك، لولب شرار ذهبي وأزرق، ولمعات تكبر بالنواة، وحلقة لمعات بالأرض تتوسع
        STAR.novaCharge(dim, p.location, k, t);
        moveShape(core, { x: p.location.x, y: p.location.y + 3.0, z: p.location.z }); setShape(core, "sh:r", 0.3 + 1.4 * k);
        if (t % 10 === 0) shake(p, 0.05 + 0.12 * k, 0.12);
        if (t >= charge) {
          system.clearRun(h);
          sfx(dim, "sh.supernova_boom", p.location, 2, 1);
          shake(p, 0.5, 0.5);
          // النجمة تنفجر: انفجار موت التنين + TNT الكبير، وثلاث موجات (غبار، لمعات، شرار ذهبي) لحد 14 بلوكة، ووميض أبيض
          STAR.novaBoom(dim, p.location);
          removeFx(core);
          popShape(dim, "nova", { x: p.location.x, y: p.location.y + 1.6, z: p.location.z }, 1.4, 4.6, 7, { ease: "out", s: 300 });
          popShape(dim, "nova_ring", p.location, 1.0, 14.0, 12, { ease: "out", s: 120 });
          for (const q of dim.getPlayers({ location: p.location, maxDistance: 26 })) { try { q.camera.fade({ fadeColor: { red: 1, green: 0.97, blue: 0.85 }, fadeTime: { fadeInTime: 0.05, holdTime: 0.05, fadeOutTime: 0.6 } }); } catch (err) { /* */ } }
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
        WEAPON.aura(p.dimension, KATANA, bladePoint(p, Math.random()), t, i);
      }
    } catch (e) { system.clearRun(h); }
  }, 4);
}
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      const held = inv(p).getItem(p.selectedSlotIndex);
      if (!held || held.typeId !== KATANA || katLv(p) < 3) continue;
      WEAPON.aura(p.dimension, KATANA, bladePoint(p, 0.3 + Math.random() * 0.7), 0, 0);
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
    // هلال الهاوية: هلال من نَفَس التنين وتوهج بنفسجي يطير لقدام (يترسم بكل تك بمكانه، ونَفَس التنين يبقى ثانية فيبين أثر الهلال)
    // الهلال نفسه 3D (slash_violet بقطر الضربة) يطير لقدام بزاوية الضربة، وجزيئات الهاوية تكمّله
    // (مركز الهلال بمستوى الصدر حتى فحص الجدار يبقى بالهوا؛ القوس نفسه يلف فوق الهدف بنصف قطر الضربة)
    flyShape(dim, "slash_violet", from, dir, 1.4, 18 + 2 * lv, { r: rad * 0.75, a: roll }, (pos) => {
      WEAPON.abyssStep(dim, { x: pos.x - dir.x * rad * 0.7, y: pos.y, z: pos.z - dir.z * rad * 0.7 }, dir, roll, rad);
      for (const e of enemiesNear(dim, pos, rad, p.id)) {
        if (hit.has(e.id)) continue;
        hit.add(e.id);
        hurt(e, kd(p, 10), p);
        pushAway(p.location, e, 0.6, 0.2);
        WEAPON.abyssHit(dim, center3(e));
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
  WEAPON.shadowPuff(dim, p.location);
  if (dest) { safeTeleport(p, dest, t.location); WEAPON.shadowPuff(dim, dest); }
  sfx(dim, "sh.kat_step", p.location, 1.1, 1);
  later(1, () => {
    if (!valid(t)) return;
    const c = center3(t);
    WEAPON.xCut(dim, c, p.location, 45, false);
    popShape(dim, "x_cut", c, 0.6, 1.1, 4, { yaw: yawOf(t.location, p.location) });
    hurt(t, kd(p, 8), p);
    sfx(dim, "sh.dagger_hit", t.location, 1.1, 0.8);
  });
  later(5, () => {
    if (!valid(t)) return;
    const c = center3(t);
    WEAPON.xCut(dim, c, p.location, -45, false);
    popShape(dim, "x_cut", c, 0.6, 1.1, 4, { yaw: yawOf(t.location, p.location), a: 45 });
    let low = false;
    try { const hp = t.getComponent("minecraft:health"); low = hp.currentValue <= hp.effectiveMax * 0.3; } catch (err) { /* */ }
    if (lv >= 3 && low && !BOSS_TYPES.has(t.typeId)) {
      hurt(t, 9999, p);
      WEAPON.xCut(dim, c, p.location, 90, true);
      popShape(dim, "x_cut", c, 1.0, 1.9, 6, { yaw: yawOf(t.location, p.location), w: 240 });
      vP(dim, c, PT.ender, {}); vP(dim, c, PT.dragonBoom, { eye: 0 });
      notify(p, "§5EXECUTED!", 25);
    } else hurt(t, kd(p, 8), p);
    ghostSword(p, t.location.x, t.location.z, 0, 0, 1.9);
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
  // المانا: كل مهارة قدرة تكلف مانا حسب طول كولداونها (الأسلحة ما تكلف)
  const cost = manaCost(skill), have = manaOf(p, st);
  if (have < cost) {
    notify(p, `§9Not enough mana §7(${Math.floor(have)}/${cost})`, 25);
    sfxPlayer(p, "note.bass", 0.5, 0.6);
    return;
  }
  lastSkillUse.set(p.id, { id: skill.id, tick: now });
  const fm = focusMul(p);                                                  // جرعة التركيز: كولداون أقصر 30%
  let res = false;
  try { res = SKILL_FN[skill.id](p); } catch (e) { res = false; }
  if (res && typeof res.then === "function") {
    cooldowns.set(key, now + 40); // يمنع الضغط المتكرر أثناء القائمة
    res.then((ok) => { cooldowns.set(key, system.currentTick + (ok ? Math.round(skill.cooldown * fm) : 6)); if (ok) spendMana(p, cost); }).catch(() => cooldowns.set(key, system.currentTick + 6));
    return;
  }
  if (res) spendMana(p, cost);
  cooldowns.set(key, now + (typeof res === "number" && res > 0 ? Math.round(res * fm) : res ? Math.round(skill.cooldown * fm) : 6));
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
        WEAPON.stab(target.dimension, center3(target), p.location, 5, true);        // ضربة الفجر: هلال ذهبي + انفجار شرار ذهبي
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
        WEAPON.glint(target.dimension, hc);
        sfx(target.dimension, "sh.dagger_hit", target.location, 1.1, 1.8);
        notify(p, "§f§lGlint!", 20);
      }
      comboMap.set(p.id, c);
    }
    if (w.special === "rend") {
      try { target.addEffect("poison", 60, { amplifier: 0, showParticles: true }); } catch (e) { /* */ }
      WEAPON.rake(target.dimension, center3(target), { x: target.location.x - p.location.x, y: 0, z: target.location.z - p.location.z }, Math.random() * 60 - 30);
    }
    if (w.cleave) {
      let n = 0;
      for (const o2 of enemiesNear(target.dimension, target.location, 2.8, target.id)) {
        if (o2.id === p.id || n >= w.cleave) continue;
        hurt(o2, Math.round(w.extra * 0.6), p); n++;
        WEAPON.cleaveHit(target.dimension, center3(o2));
      }
    }
    if (w.shock) {
      for (const o2 of enemiesNear(target.dimension, target.location, 2.6, target.id)) {
        if (o2.id === p.id) continue;
        hurt(o2, Math.round(w.extra * 0.4), p);
        pushAway(target.location, o2, 0.9, 0.3);
      }
      WEAPON.shockHit(target.dimension, target.location);
      if (Math.random() < 0.2) { try { target.addEffect("slowness", 30, { amplifier: 3, showParticles: false }); } catch (e) { /* */ } }
    }
    if (w.fast) {
      const tg = target;
      system.runTimeout(() => {
        try {
          if (!valid(tg)) return;
          hurt(tg, 2, p);
          WEAPON.doubleHit(tg.dimension, center3(tg));
          sfx(tg.dimension, w.sound, tg.location, 0.8, 1.4);
        } catch (e) { /* */ }
      }, 3);
    }
    try { target.applyDamage(extra * mightMul(p), { cause: EntityDamageCause.entityAttack, damagingEntity: p }); } catch (e) { /* */ }
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
    const near = p.dimension.getEntities({ location: p.location, maxDistance: 64, families: ["sh_monster"] });
    if (near.length >= MONSTER_CAP + (force ? 2 : 0)) return undefined;
    if (!force && Math.random() < 0.4) return undefined;
    // الوحوش القوية جداً نادرة بالعالم: Vile (الماغماموث، الدب) 3% وCursed (السرعوف) 1.5% من كل محاولة، وبس إذا ماكو وحش قوي ثاني قريب
    const strongNear = near.some((e) => (MONSTERS[e.typeId] || {}).rank >= 2) || p.dimension.getEntities({ location: p.location, maxDistance: 110, families: ["sh_monster"] }).some((e) => (MONSTERS[e.typeId] || {}).rank >= 2);
    const roll = Math.random();
    const cursed = !force && !strongNear && st.rank >= 3 && roll < 0.015;
    const vile = !force && !strongNear && !cursed && st.rank >= 2 && roll < 0.045;
    const grim = st.rank >= 1 && !force && !cursed && !vile && Math.random() < 0.15;
    const id = cursed ? CURSED_TYPES[Math.floor(Math.random() * CURSED_TYPES.length)] : vile ? VILE_TYPES[Math.floor(Math.random() * VILE_TYPES.length)] : grim ? GRIM_TYPES[Math.floor(Math.random() * GRIM_TYPES.length)] : RANK0_TYPES[Math.floor(Math.random() * RANK0_TYPES.length)];
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
    MONSTER.fireSwipe(dim, o, { x: fx, y: 0, z: fz }, idx);                // خرمشة نار حقيقية
    sfx(dim, "sh.imp_pounce", e.location, 0.8, 1.2 + idx * 0.15);
  } else {
    MONSTER.guardSwipe(dim, { x: e.location.x + fx * 0.6, y: e.location.y + 1.3, z: e.location.z + fz * 0.6 }, { x: fx, y: 0, z: fz });   // ضربة عمودية برون تركوازي وحصى
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
  try {
    const t = dim.getTopmostBlock({ x: Math.floor(x), z: Math.floor(z) });
    if (t) {
      let y = t.y;
      while (y > t.y - 4 && airAt(dim, x, y + 0.5, z)) y--;      // العشب والورد وطبقة الثلج مو أرض
      if (Math.abs(y + 1 - nearY) < 6) return y + 1;
    }
  } catch (e) { /* */ }
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
      MONSTER.emberBoom(dim, b);                                            // انفجار صغير + حلقة لهب + جمرات + دخان نار
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
      MONSTER.rockImpact(dim, b);
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
  MONSTER.houndCharge(dim, e.location); MONSTER.houndCharge(dim, e.location);
  later(10, () => {
    if (!valid(e) || !valid(tp)) { endSpecial(st, e, 60); return; }
    const from = { ...e.location }, dest = behindSpot(tp, e.location);
    if (!dest) { endSpecial(st, e, 40); return; }
    WEAPON.shadowPuff(dim, from);                                         // يذوب بدخان ظل (حبر + بوابة + نفخة)
    safeTeleport(e, dest, tp.location);
    WEAPON.shadowPuff(dim, dest);
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
  MONSTER.burrowDig(dim, e.location);
  try { e.addEffect("invisibility", 34, { amplifier: 0, showParticles: false }); e.addEffect("slowness", 34, { amplifier: 4, showParticles: false }); } catch (err) { /* */ }
  let lock;
  const tick = system.runInterval(() => {
    try {
      if (!valid(e) || !valid(tp)) return;
      const L = lock || tp.location;
      MONSTER.sandMark(dim, L);                                             // رمل يتحرك تحت الأرض وين بيطلع
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
    MONSTER.burrowErupt(dim, lock);                                       // انفجار رمل + رشة سم خضرا
    sfx(dim, "sh.guard_slam", lock, 1, 1.3);
    for (const pl of playersNear(dim, lock, 2.0)) { hurtPlayer(pl, 6, e); try { pl.addEffect("poison", 100, { amplifier: 0 }); pl.applyKnockback({ x: 0, z: 0 }, 0.9); } catch (err) { /* */ } }
    later(12, () => endSpecial(st, e, 110));
  });
}


function ambientFx(dim, e, type) {
  const L = e.location;
  if (type === "sh:ember_imp") MONSTER.impAmbient(dim, L);                // لهب حقيقي يطلع من جسمه وجمرات
  else MONSTER.guardAmbient(dim, L);                                       // غبار حصى ولمعات رون تركوازية
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
              MONSTER.impCharge(dim, e.location);
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
                MONSTER.impLeap(dim, e.location);
              } else {
                sfx(dim, "sh.guard_slam", e.location, 1.3);
                for (const pl of dim.getPlayers({ location: e.location, maxDistance: 4 })) {
                  hurtPlayer(pl, 6, e);
                  pushAway(e.location, pl, 2.2, 0.5);
                  shake(pl, 0.25, 0.3);
                }
                MONSTER.guardSlam(dim, e.location);
                rockBurst(dim, e.location, 6, 1.3);
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
              MONSTER.impTrail(dim, e.location);
            }
            if (st.t >= cfg.hold) {
              if (type === "sh:ember_imp") {
                for (const pl of dim.getPlayers({ location: e.location, maxDistance: 2.2 })) {
                  hurtPlayer(pl, 4, e);
                  pushAway(e.location, pl, 1.2, 0.3);
                  MONSTER.fireHit(dim, center3(pl));
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
      vP(dim, ar.location, n % 2 ? PT.breath : PT.glow, { c: [0.7, 0.45, 1], eye: 1.0 });       // أثر السهم: نَفَس تنين بنفسجي يبقى ثانية
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
          vP(dim, L, PT.breath, { eye: 1.0 });
          vP(dim, { x: L.x - sp.x * 0.5, y: L.y - sp.y * 0.5, z: L.z - sp.z * 0.5 }, PT.glow, { c: [0.6, 0.45, 1], eye: 1.0 });
        }
      } catch (err) { /* */ }
    }
  }
}, 2);

try { setupStructures((e, pl) => scaleMonster(e, getState(pl).rank)); } catch (e) { /* */ }
try { setupDash(); } catch (e) { /* */ }




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
      MONSTER.venomTrail(dim, pos);
      if (l < 1.1) {
        hurtPlayer(target, 4, shooter);
        try { target.addEffect("poison", 100, { amplifier: 0 }); } catch (e) { /* */ }
        MONSTER.venomSplash(dim, center3(target));
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
          if (hound) MONSTER.houndAmbient(dim, L); else MONSTER.scorpAmbient(dim, L);
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
            if (hound) MONSTER.houndCharge(dim, L); else MONSTER.scorpCharge(dim, L, st.t);
            if (st.t >= need) {
              st.phase = 2; st.t = 0; setMState(e, 2);
              if (hound) {
                // عواء: يبطئ كل اللاعبين القريبين
                sfx(dim, "sh.imp_windup", L, 1.6, 0.45);
                try { dim.playSound("mob.wolf.growl", L, { volume: 1.5, pitch: 0.5 }); } catch (err) { /* */ }
                MONSTER.howl(dim, L);                                         // زئير (نفخات الـRavager) + موجة ظل تتوسع + غيوم غضب
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
                flyShape(dim, "venom_glob", from, { x: dx / l, y: dy / l, z: dz / l }, 1.4, l, { r: 0.6, w: 500 }, (pos) => { MONSTER.venomTrail(dim, pos); });
                MONSTER.venomSplash(dim, to);                                  // رشة جرعة سم خضرا حقيقية
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
            if (hound && st.t % 8 === 0) MONSTER.houndCharge(dim, L);
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
              if (hound) { if (st.hit % 2) MONSTER.houndBite(dim, o, { x: fx, y: 0, z: fz }, st.hit); else popShape(dim, "fang_jaw", o, 0.7, 1.1, 7, { yaw: dirYaw({ x: -fx, y: 0, z: -fz }) }); }
              else MONSTER.venomSwipe(dim, o, { x: fx, y: 0, z: fz });
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
  { key: "tower", name: "Abyss Tower" },
  { key: "palace", name: "Sunset Palace" },
  { key: "ruins", name: "Temple Ruins" },
  { key: "village", name: "Sakura Village" },
  { key: "temple", name: "Star Temple" },
  { key: "trainer", name: "Trainer" },
  { key: "rift", name: "Open Rift" },
  { key: "nearest", name: "Nearest (any destination)" },
];
const COMPASS_NAMES = { tower: "Abyss Tower", village: "Sakura Village", palace: "Sunset Palace", ruins: "Temple Ruins", shrine: "Dark Sword Shrine", temple: "Star Temple", lightshrine: "Light Sword Shrine" };
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
// ═════════════════════════ وحوش رتبة Grim: القرن القاتم والرائي الأجوف ═════════════════════════
const SOUL = [0.4, 0.9, 1.0], AMBER = [1.0, 0.7, 0.2];
const gst = new Map();          // حالة كل وحش
function fwdTo(from, to) { const dx = to.x - from.x, dz = to.z - from.z, l = Math.hypot(dx, dz) || 1; return { x: dx / l, z: dz / l }; }
// بلوكات تنعبر (عشب، ورد، شتلات، طبقة ثلج، مشاعل...). Block.isSolid تجريبي بس (مو موجود بالنسخة المستقرة) فنعرفها بالاسم.
const PASSABLE_RE = /(^|:|_)(short_grass|tall_grass|grass$|fern|large_fern|flower|tulip|dandelion|poppy|orchid|allium|azure_bluet|oxeye_daisy|cornflower|lily_of_the_valley|wither_rose|rose_bush|peony|lilac|sunflower|pitcher_plant|torchflower|pink_petals|wildflowers|leaf_litter|bush|deadbush|sapling|propagule|vine|snow_layer|torch|lantern|carpet|button|lever|rail|sign|banner|brown_mushroom$|red_mushroom$|fungus|roots$|sprouts|sugar_cane|kelp|seagrass|sea_pickle|wheat|carrots|potatoes|beetroot|melon_stem|pumpkin_stem|sweet_berry_bush|cocoa|nether_wart|pressure_plate|redstone_wire|redstone_torch|tripwire|string$|glow_lichen|sculk_vein|hanging_roots|cave_vines|spore_blossom|frame|web|structure_void|light_block|firefly_bush|cactus_flower)/;
function airAt(dim, x, y, z) {
  try {
    const b = dim.getBlock({ x: Math.floor(x), y: Math.floor(y), z: Math.floor(z) });
    if (!b || b.isAir || b.isLiquid) return true;
    if (typeof b.isSolid === "boolean") return !b.isSolid;
    return PASSABLE_RE.test(b.typeId);
  } catch (e) { return false; }
}
function segDist(p, a, b) {
  const abx = b.x - a.x, aby = b.y - a.y, abz = b.z - a.z, l2 = abx * abx + aby * aby + abz * abz || 1;
  const t = Math.max(0, Math.min(1, ((p.x - a.x) * abx + (p.y - a.y) * aby + (p.z - a.z) * abz) / l2));
  return Math.hypot(p.x - (a.x + abx * t), p.y - (a.y + aby * t), p.z - (a.z + abz * t));
}
function grimEnd(e, st, cd) { st.phase = 0; st.skill = ""; st.t = 0; st.cd = cd + Math.random() * cd * 0.5; setMState(e, 0); }

// ── القرن القاتم: اندفاع القرون، فوانيس الروح، ضربة الجذور ──
// قلب الغزال (بالنموذج: 20 بكسل فوق، بالنص) ومكانه بالعالم
function gloomHeart(e) { const L = e.location; return { x: L.x, y: L.y + 1.3, z: L.z }; }
// سلسلة روح متدلية (منحنى) من نقطة لنقطة، حلقات بلونين
function soulChain(dim, a, b, n = 14) {
  for (let i = 0; i <= n; i++) {
    const s = i / n, sag = Math.sin(Math.PI * s) * 0.55;
    pix(dim, { x: a.x + (b.x - a.x) * s, y: a.y + (b.y - a.y) * s - sag, z: a.z + (b.z - a.z) * s }, { color: i % 2 ? SOUL : [0.72, 0.55, 1], size: i % 2 ? 0.13 : 0.17, life: 0.2, speed: 0 });
  }
}
function gloomTick(e, st) {
  const dim = e.dimension, L = e.location;
  if (Math.random() < 0.35) glow(dim, { x: L.x + (Math.random() - 0.5) * 1.2, y: L.y + 1.2 + Math.random() * 0.8, z: L.z + (Math.random() - 0.5) * 1.2 }, { color: Math.random() < 0.5 ? SOUL : VIOLET, size: 0.12, life: 0.9, rise: 0.6 });
  if (st.phase === 0) {
    st.cd -= 2;
    if (st.cd > 0) return;
    const np = nearestPlayer(e, 22);
    if (!np) { st.cd = 10; return; }
    st.target = np.p; st.t = 0;
    if (np.d < 5.5) { st.skill = "heart"; st.phase = 1; setMState(e, 3); sfx(dim, "sh.chorus", L, 1, 0.4); }
    else if (np.d <= 14 && Math.random() < 0.55) { st.skill = "charge"; st.phase = 1; setMState(e, 1); sfx(dim, "sh.imp_windup", L, 1.2, 0.5); }
    else if (np.d <= 22) { st.skill = "spirit"; st.phase = 1; setMState(e, 4); sfx(dim, "sh.chorus", L, 1, 0.7); }
    else st.cd = 10;
    return;
  }
  const tp = valid(st.target) ? st.target : undefined;
  st.t += 2;
  // ── 1) الاندفاع والنطح: يحك الأرض، خط أحمر يبين طريقه، يركض وينطح أول لاعب بقرونه ويطيره ──
  if (st.skill === "charge") {
    if (st.phase === 1) {
      if (tp && st.t <= 12) st.dir = fwdTo(L, tp.location);
      const d = st.dir || { x: 0, z: 1 };
      // (بدون خط أحمر قبل الاندفاع بطلب اللاعب) الحك بالحافر بس
      if (st.t % 4 === 2) rockBurst(dim, { x: L.x + d.x * 0.9, y: L.y, z: L.z + d.z * 0.9 }, 2, 0.4);
      if (st.t >= 18) { st.phase = 2; st.t = 0; setMState(e, 2); sfx(dim, "sh.stardash", L, 1.2, 0.6); }
      return;
    }
    const d = st.dir || { x: 0, z: 1 };
    const nx = L.x + d.x * 0.9, nz = L.z + d.z * 0.9;
    if (st.t > 22 || !airAt(dim, nx, L.y + 0.5, nz) || !airAt(dim, nx, L.y + 1.6, nz)) {
      waveFx(dim, L, 4, 1, 10); rockBurst(dim, L, 5, 0.8); sfx(dim, "sh.guard_slam", L, 1.1, 0.8);
      grimEnd(e, st, 70); return;
    }
    try { e.teleport({ x: nx, y: L.y, z: nz }, { facingLocation: { x: nx + d.x, y: L.y + 1, z: nz + d.z } }); } catch (err) { /* */ }
    glow(dim, { x: L.x, y: L.y + 1.4, z: L.z }, { color: SOUL, size: 0.3, life: 0.5, rise: 0.2 });
    for (const sx of [-1, 1]) pix(dim, { x: L.x - d.z * sx * 0.35, y: L.y + 0.05, z: L.z + d.x * sx * 0.35 }, { color: st.t % 4 ? SOUL : [0.85, 1, 1], size: 0.2, life: 2.0, speed: 0 });
    // النطحة: أول لاعب قدام قرونه
    const horn = { x: nx + d.x * 0.6, y: L.y + 1.2, z: nz + d.z * 0.6 };
    const hit = dim.getPlayers({ location: horn, maxDistance: 1.9 });
    if (hit.length) {
      for (const pl of hit) {
        hurtPlayer(pl, 10, e);
        try { pl.applyKnockback({ x: d.x * 2.4, z: d.z * 2.4 }, 0.85); } catch (err) { /* */ }
        shake(pl, 0.35, 0.4); notify(pl, "§bThe Gloomhorn rams you with its antlers!", 40);
        burst(dim, center3(pl), 16, SOUL, 3, 0.22);
      }
      impactFx(dim, horn, SOUL, false);
      for (let k = 0; k < 16; k++) pix(dim, horn, { color: k % 2 ? SOUL : [0.95, 1, 1], size: 0.2, life: 0.6, speed: 3 });
      sfx(dim, "sh.guard_slam", L, 1.4, 1.1); sfx(dim, "random.anvil_land", L, 0.6, 0.6);
      grimEnd(e, st, 70);
    }
    return;
  }
  // ── 2) روح الغزال: القلب يضوي وروح غزال تطلع من صدره وتكبر قدامه، تركض عليك، ووراها روحين بمروحة ──
  if (st.skill === "spirit") {
    if (tp && st.t <= 16) st.aim = { ...tp.location };
    const f = st.aim ? fwdTo(L, st.aim) : { x: 0, z: 1 }, yaw = dirYaw({ x: f.x, y: 0, z: f.z });
    const H = gloomHeart(e), front = { x: L.x + f.x * 1.6, y: L.y, z: L.z + f.z * 1.6 };
    if (st.t <= 16) {
      if (!st.sp) {
        st.sp = shapeFx(dim, "spirit_stag", front, { r: 0.1, yaw, life: 24 });
        tween(14, 1, (q) => setShape(st.sp, "sh:r", 0.1 + 1.4 * q));
      } else moveShape(st.sp, front, yaw);
    }
    const run = (from, dir, r, dmg) => {
      const hitS = new Set();
      runShape(dim, "spirit_stag", from, dir, 0.9, 18, { r }, (pos) => {
        pix(dim, { x: pos.x, y: pos.y + 0.05, z: pos.z }, { color: SOUL, size: 0.18, life: 1.8, speed: 0 });     // آثار حوافر مضيئة
        glow(dim, { x: pos.x, y: pos.y + 1, z: pos.z }, { color: SOUL, size: 0.25, life: 0.4, rise: 0.4 });
        for (const pl of dim.getPlayers({ location: { x: pos.x, y: pos.y + 1, z: pos.z }, maxDistance: 1.3 + r * 0.4 })) {
          if (hitS.has(pl.id)) continue;
          hitS.add(pl.id); hurtPlayer(pl, dmg, valid(e) ? e : undefined);
          try { pl.applyKnockback({ x: dir.x * 1.4, z: dir.z * 1.4 }, 0.5); } catch (err) { /* */ }
          notify(pl, "§bA spirit stag tramples you!", 30);
          impactFx(dim, center3(pl), SOUL, false);
          return true;                                          // الروح تتفجر لما تضرب
        }
        return false;
      }, (pos) => { burst(dim, { x: pos.x, y: pos.y + 1, z: pos.z }, 14, SOUL, 2.5, 0.2); sfx(dim, "sh.blackhole_end", pos, 0.7, 1.6); });
    };
    if (st.t === 18) {
      removeFx(st.sp); st.sp = undefined;
      run(front, { x: f.x, y: 0, z: f.z }, 1.5, 8);
      sfx(dim, "sh.stardash", L, 1.1, 1.3);
    }
    if (st.t === 26) {
      for (const sx of [-1, 1]) {
        const ang = Math.atan2(f.z, f.x) + sx * 0.42, dir = { x: Math.cos(ang), y: 0, z: Math.sin(ang) };
        run({ x: L.x + dir.x * 1.6, y: L.y, z: L.z + dir.z * 1.6 }, dir, 1.0, 5);
      }
      sfx(dim, "sh.stardash", L, 0.9, 1.6);
    }
    if (st.t >= 34) { removeFx(st.sp); st.sp = undefined; grimEnd(e, st, 70); }
    return;
  }
  // ── 3) نبض القلب الشبحي: 3 دقات، كل دقة موجة على الأرض (تنطها وتسلم)، وبالأخيرة سلاسل روح تمص صحتك ──
  if (st.skill === "heart") {
    const H = gloomHeart(e);
    if (st.t === 10 || st.t === 20 || st.t === 30) {
      const n = st.t / 10, hitB = new Set(), C = { ...L };
      sfx(dim, "note.bass", L, 1.6, 0.5); sfx(dim, "sh.guard_slam", L, 0.7 + n * 0.2, 0.5);
      impactFx(dim, H, [0.8, 0.6, 1], n >= 2);
      for (let k = 0; k < 10 + n * 2; k++) pix(dim, H, { color: k % 2 ? SOUL : [0.8, 0.6, 1], size: 0.18, life: 0.5, speed: 2.2 });
      const steps = 9;
      for (let k = 0; k <= steps; k++) {
        later(1 + k, () => {
          const r = 1 + k * 0.72;
          ring(dim, { x: C.x, y: C.y + 0.12, z: C.z }, r, 10 + k * 4, k * 0.2, n === 3 ? [0.75, 0.5, 1] : SOUL, 0.2);
          for (const pl of dim.getPlayers({ location: C, maxDistance: r + 0.7 })) {
            const dd = Math.hypot(pl.location.x - C.x, pl.location.z - C.z);
            if (hitB.has(pl.id) || Math.abs(dd - r) > 0.6 || pl.isOnGround === false) continue;   // اللي ينط يسلم
            hitB.add(pl.id); hurtPlayer(pl, 3 + n, valid(e) ? e : undefined);
            try { pl.applyKnockback({ x: (pl.location.x - C.x) / (dd || 1) * 0.6, z: (pl.location.z - C.z) / (dd || 1) * 0.6 }, 0.3); } catch (err) { /* */ }
            if (n === 1) notify(pl, "§bJump over the heartbeat waves!", 30);
          }
        });
      }
      if (n === 3) {
        st.chains = dim.getPlayers({ location: L, maxDistance: 8 }).map((pl) => ({ pl, t: 0 }));
        for (const c of st.chains) { notify(c.pl, "§5Soul chains drain your life! Run!", 40); sfx(dim, "sh.pull", c.pl.location, 0.8, 0.7); }
      }
    }
    if (st.chains && st.t > 30) {
      for (const c of st.chains) {
        if (c.gone) continue;
        if (!valid(c.pl) || Math.hypot(c.pl.location.x - L.x, c.pl.location.z - L.z) > 10) {
          c.gone = true;
          if (valid(c.pl)) { burst(dim, center3(c.pl), 12, VIOLET, 2.5, 0.18); sfx(dim, "random.anvil_land", c.pl.location, 0.4, 1.8); }
          continue;
        }
        soulChain(dim, H, center3(c.pl));
        if (st.t % 8 === 0) {
          hurtPlayer(c.pl, 1.5, e);
          try { const h = e.getComponent("minecraft:health"); h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + 2)); } catch (err) { /* */ }
          glow(dim, H, { color: [0.75, 0.5, 1], size: 0.6, life: 0.3 });
          pix(dim, center3(c.pl), { color: [0.75, 0.5, 1], size: 0.2, life: 0.5, speed: 1 });
        }
      }
    }
    if (st.t >= 68) { st.chains = undefined; grimEnd(e, st, 70); }
  }
}

// ── الرائي الأجوف: الشعاع البرتقالي، جذور الأرض، زفير التجميد (من كرة جليد) ──
const ORANGE = [1.0, 0.55, 0.12], ICE = [[0.92, 0.97, 1.0], [0.72, 0.88, 1.0], [0.52, 0.74, 1.0], [0.85, 0.95, 1.0]];
const frostBlocks = new Map();   // "dim|x,y,z" -> { dim, pos, until }  ثلج ناعم مؤقت حول اللاعب المتجمد
function freezePlayer(pl) {
  // الثلج الناعم الحقيقي يخلي شاشة اللاعب تتجمد (مثل لما يطب بيه) ويبطئه، وينشال قبل ما يوصل للضرر
  const dim = pl.dimension, now = system.currentTick;
  for (const dy of [0, 1]) {
    const pos = { x: Math.floor(pl.location.x), y: Math.floor(pl.location.y) + dy, z: Math.floor(pl.location.z) };
    const key = `${dim.id}|${pos.x},${pos.y},${pos.z}`;
    try {
      const b = dim.getBlock(pos);
      if (!b) continue;
      if (b.typeId === "minecraft:powder_snow") { const f = frostBlocks.get(key); if (f) f.until = now + 70; continue; }
      if (!b.isAir) continue;
      b.setType("minecraft:powder_snow");
      frostBlocks.set(key, { dim, pos, until: now + 70 });
    } catch (e) { /* */ }
  }
  try { pl.addEffect("slowness", 60, { amplifier: 2, showParticles: false }); } catch (e) { /* */ }
}
system.runInterval(() => {
  const now = system.currentTick;
  for (const [key, f] of frostBlocks) {
    if (now < f.until) continue;
    try { const b = f.dim.getBlock(f.pos); if (b && b.typeId === "minecraft:powder_snow") b.setType("minecraft:air"); } catch (e) { /* */ }
    frostBlocks.delete(key);
  }
}, 5);
function seerTick(e, st) {
  const dim = e.dimension, L = e.location;
  if (Math.random() < 0.3) glow(dim, { x: L.x + (Math.random() - 0.5) * 0.8, y: L.y + 0.3, z: L.z + (Math.random() - 0.5) * 0.8 }, { color: VIOLET, size: 0.14, life: 0.8, rise: 0.4 });
  if (st.phase === 0) {
    st.cd -= 2;
    if (st.cd > 0) return;
    const np = nearestPlayer(e, 24);
    if (!np) { st.cd = 10; return; }
    st.target = np.p; st.t = 0; st.phase = 1;
    const r = Math.random();
    if (np.d >= 2 && np.d <= 8 && (np.d < 5 ? r < 0.65 : r < 0.3)) { st.skill = "breath"; setMState(e, 3); sfx(dim, "sh.chorus", L, 1, 0.5); st.frozen = new Set(); }
    else if (np.d <= 9.5) { st.skill = "thorns"; setMState(e, 2); sfx(dim, "sh.guard_windup", L, 1, 1.3); }
    else if (np.d <= 22) { st.skill = "beam"; setMState(e, 1); sfx(dim, "sh.supernova_charge", L, 0.7, 1.4); }
    else { st.phase = 0; st.cd = 10; }
    return;
  }
  const tp = valid(st.target) ? st.target : undefined;
  st.t += 2;
  // ── 1) الشعاع البرتقالي: يرفع كفه قدام عينه ويطلق مباشرة (بدون تحذير). الشعاع من جزيئات ماينكرافت:
  //       قلب لمعات End Rod وخيطين غبار ملتفين حوله (مثل شعاع الحارس)، شرار ونار ودخان عند نقطة الضربة ──
  if (st.skill === "beam") {
    if (tp && st.t <= 14) st.aim = center3(tp);
    const f = st.aim ? fwdTo(L, st.aim) : { x: 0, z: 1 };
    const hand = { x: L.x + f.x * 0.95, y: L.y + 2.3, z: L.z + f.z * 0.95 };
    if (st.t < 20) {
      for (let i = 0; i < 3; i++) {
        const a = Math.random() * Math.PI * 2, rr = 0.9 - st.t * 0.04;
        pix(dim, { x: hand.x + Math.cos(a) * rr, y: hand.y + Math.sin(a) * rr, z: hand.z }, { color: i % 2 ? ORANGE : [1, 0.85, 0.5], size: 0.16, life: 0.25, speed: 0.1 });
      }
      if (st.t >= 14) glow(dim, hand, { color: ORANGE, size: 0.5, life: 0.2 });
    }
    if (st.t === 20 && st.aim) {
      const dx = st.aim.x - hand.x, dy = st.aim.y - hand.y, dz = st.aim.z - hand.z, l = Math.hypot(dx, dy, dz) || 1;
      const d = { x: dx / l, y: dy / l, z: dz / l };
      let len = 0;
      for (let k = 0.5; k <= 22; k += 0.5) { if (!airAt(dim, hand.x + d.x * k, hand.y + d.y * k, hand.z + d.z * k)) break; len = k; }
      len = Math.max(len, 1);
      st.beam = { a: hand, b: { x: hand.x + d.x * len, y: hand.y + d.y * len, z: hand.z + d.z * len } };
      sfx(dim, "sh.supernova_boom", L, 0.8, 1.7);
      for (const pl of dim.getPlayers({ location: L, maxDistance: 24 })) {
        if (segDist(center3(pl), hand, st.beam.b) > 0.95) continue;
        hurtPlayer(pl, 9, e);
        try { pl.setOnFire(4, true); } catch (err) { /* */ }
        shake(pl, 0.25, 0.3); notify(pl, "§6The Seer's beam burns you!", 40);
      }
    }
    if (st.beam && st.t >= 20 && st.t <= 28 && st.t % 4 === 0) {         // الشعاع يبقى 0.4 ثانية (يتجدد كل 4 تكات)
      const B = st.beam.b;
      particleBeam(dim, st.beam.a, B, ORANGE, 0.5);
      burst(dim, B, 6, ORANGE, 2.2);
      for (let i = 0; i < 3; i++) { try { dim.spawnParticle("minecraft:basic_flame_particle", { x: B.x + (Math.random() - 0.5) * 0.6, y: B.y + (Math.random() - 0.5) * 0.6, z: B.z + (Math.random() - 0.5) * 0.6 }); } catch (err) { /* */ } }
      try { dim.spawnParticle("minecraft:basic_smoke_particle", B); } catch (err) { /* */ }
    }
    if (st.t >= 34) { st.beam = undefined; grimEnd(e, st, 70); }
    return;
  }
  // ── 2) جذور الأرض: من بعد 5-9 بلوكات، جذور تطلع ورا بعض بخط لمكانك، وبالأخير قفص جذور يلتف حواليك ──
  if (st.skill === "thorns") {
    if (st.t === 10 && tp) { st.spot = { ...tp.location }; st.from = { ...L }; st.n = 0; }
    if (st.spot && st.t >= 12) {
      const f = fwdTo(st.from, st.spot), dist = Math.min(11, Math.hypot(st.spot.x - st.from.x, st.spot.z - st.from.z) + 1);
      const k = (st.t - 12) / 2;
      const thorn = (x, z, delay) => {
        const y = groundAt(dim, x, z, st.from.y);
        glow(dim, { x, y: y + 0.1, z }, { color: VIOLET, size: 0.35, life: 0.3, rise: 0.4 });
        later(delay, () => {
          const s2 = shapeFx(dim, "root_spike", { x, y: y - 1.2, z }, { r: 0.4, yaw: Math.random() * 360, p: (Math.random() - 0.5) * 16, life: 22 });
          if (s2) tween(5, 1, (q) => { setShape(s2, "sh:r", 0.4 + 1.4 * q); moveShape(s2, { x, y: y - 1.2 + 1.2 * q, z }); });
          for (let i = 0; i < 4; i++) pix(dim, { x: x + (Math.random() - 0.5), y: y + 0.2, z: z + (Math.random() - 0.5) }, { color: i % 2 ? [0.45, 0.32, 0.25] : [0.45, 0.92, 1], size: 0.16, life: 0.5, speed: 1.2, rise: 1.0 });
          sfx(dim, "sh.guard_slam", { x, y, z }, 0.5, 1.6);
          for (const pl of dim.getPlayers({ location: { x, y: y + 1, z }, maxDistance: 1.4 })) {
            const hc = st.hitT ? (st.hitT.get(pl.id) || 0) : 2;
            if (hc >= 2) continue;
            if (st.hitT) st.hitT.set(pl.id, hc + 1);
            hurtPlayer(pl, 6, valid(e) ? e : undefined);
            try { pl.applyKnockback({ x: 0, z: 0 }, 0.55); } catch (err) { /* */ }
            notify(pl, "§5Roots erupt beneath you!", 30);
          }
        });
      };
      if (!st.hitT) st.hitT = new Map();
      const along = 1.5 + k;
      if (along <= dist) thorn(st.from.x + f.x * along, st.from.z + f.z * along, 4);
      else if (!st.ring) {
        st.ring = true;
        // قفص الجذور: 6 جذور حوالين مكانك، رؤوسها تنحني لك (محسوبة: r=1.7 ونصف قطر 1.75 → الراس يوقف 0.72 بلوكة منك بارتفاع 1.7، يلفك وما يخترقك)
        const P = st.spot;
        for (let i = 0; i < 6; i++) {
          const a = (i / 6) * Math.PI * 2, x = P.x + Math.cos(a) * 1.75, z = P.z + Math.sin(a) * 1.75, y = groundAt(dim, x, z, P.y);
          glow(dim, { x, y: y + 0.1, z }, { color: [0.45, 0.92, 1], size: 0.35, life: 0.3, rise: 0.4 });
          later(6 + i, () => {
            const rs = shapeFx(dim, "root_spike", { x, y: y - 1.0, z }, { r: 0.3, yaw: dirYaw({ x: P.x - x, y: 0, z: P.z - z }), life: 50 });
            if (rs) tween(6, 1, (q) => { setShape(rs, "sh:r", 0.3 + 1.4 * q); moveShape(rs, { x, y: y - 1.0 + 1.0 * q, z }); });
          });
        }
        later(12, () => {
          sfx(dim, "sh.guard_slam", P, 0.8, 0.7);
          for (const pl of dim.getPlayers({ location: P, maxDistance: 2.1 })) {
            try { pl.addEffect("slowness", 50, { amplifier: 4 }); pl.addEffect("weakness", 50, { amplifier: 0 }); } catch (err) { /* */ }
            hurtPlayer(pl, 4, valid(e) ? e : undefined);
            notify(pl, "§5A cage of roots closes around you!", 40);
          }
        });
      }
    }
    if (st.t >= 44) { st.ring = false; st.spot = undefined; st.hitT = undefined; grimEnd(e, st, 70); }
    return;
  }
  // ── 3) زفير التجميد: مخروط بكسلات ثلجية مزرقة، والشاشة تتجمد مثل الثلج الناعم + بطء، بدون ضرر وبدون تجميد كامل ──
  if (st.skill === "breath") {
    if (tp && st.t <= 30) st.aim = center3(tp);
    {
      const f0 = st.aim ? fwdTo(L, st.aim) : { x: 0, z: 1 }, op = { x: L.x + f0.x * 1.4, y: L.y + 2.2, z: L.z + f0.z * 1.4 };
      if (st.t === 2) { st.orb = shapeFx(dim, "soul_orb", op, { r: 0.1, s: 360, life: 52 }); tween(8, 1, (q) => setShape(st.orb, "sh:r", 0.1 + 0.85 * q)); }
      else if (st.orb && st.t < 48) moveShape(st.orb, op);
      if (st.t < 8) for (let i = 0; i < 3; i++) { const a = Math.random() * 6.28; pix(dim, { x: op.x + Math.cos(a) * 0.9, y: op.y + Math.sin(a) * 0.9, z: op.z }, { color: ICE[i], size: 0.15, life: 0.3, speed: 0.1 }); }
      if (st.t === 48 && st.orb) {      // الكرة تتكسر شظايا
        removeFx(st.orb); st.orb = undefined;
        for (let k = 0; k < 18; k++) pix(dim, op, { color: ICE[k % 4], size: 0.18, life: 0.7, speed: 2.6 });
        impactFx(dim, op, ICE[0], false); sfx(dim, "random.glass", op, 0.8, 1.4);
      }
    }
    if (st.t >= 8 && st.t <= 46 && st.aim) {
      const mouth = { x: L.x, y: L.y + 2.2, z: L.z }, f = fwdTo(L, st.aim);
      mouth.x += f.x * 1.9; mouth.z += f.z * 1.9;                         // الزفير يطلع من كرة الجليد
      const dy = (st.aim.y - mouth.y) / Math.max(1, Math.hypot(st.aim.x - mouth.x, st.aim.z - mouth.z));
      for (let i = 0; i < 12; i++) {
        const dd = 0.4 + Math.random() * 8, spread = dd * 0.32, side = (Math.random() - 0.5) * 2 * spread, up = (Math.random() - 0.5) * spread;
        pix(dim, { x: mouth.x + f.x * dd - f.z * side, y: mouth.y + dy * dd + up, z: mouth.z + f.z * dd + f.x * side }, { color: ICE[i % 4], size: 0.15 + Math.random() * 0.06, life: 0.5, speed: 0.4, rise: -0.1 });
      }
      if (st.t % 6 === 0) { try { dim.spawnParticle("minecraft:snowflake_particle", { x: mouth.x + f.x * 2, y: mouth.y, z: mouth.z + f.z * 2 }); } catch (err) { /* */ } }
      if (st.t % 4 === 0) {
        for (const pl of dim.getPlayers({ location: L, maxDistance: 9 })) {
          const vx = pl.location.x - L.x, vz = pl.location.z - L.z, l = Math.hypot(vx, vz) || 1;
          if ((vx / l) * f.x + (vz / l) * f.z < 0.86) continue;          // داخل مخروط ~30°
          freezePlayer(pl);
          if (!st.frozen.has(pl.id)) {
            st.frozen.add(pl.id);
            try { pl.camera.fade({ fadeColor: { red: 0.75, green: 0.9, blue: 1 }, fadeTime: { fadeInTime: 0.1, holdTime: 0.15, fadeOutTime: 0.7 } }); } catch (err) { /* */ }
            notify(pl, "§bFrost Breath! You are freezing...", 50);
            sfx(dim, "sh.blackhole_end", pl.location, 0.6, 1.8);
          }
        }
      }
    }
    if (st.t >= 50) grimEnd(e, st, 90);
  }
}
// ═════════════════════════ شوكاني (Quillback، Lowly) وثعلب الحجاب (Veilfox، Grim) ═════════════════════════
const FOXV = [0.62, 0.45, 1.0], FOXC = [0.35, 0.8, 1.0];
const isClone = (e) => { try { return e.getDynamicProperty("sh_clone") === 1; } catch (err) { return false; } };
const hpFrac = (e) => { try { const h = e.getComponent("minecraft:health"); return h.currentValue / h.effectiveMax; } catch (err) { return 1; } };
const pickSkill = (opts, last) => { let p = opts[Math.floor(Math.random() * opts.length)]; if (p === last && opts.length > 1) p = opts.find((o) => o !== last); return p; };
// ظل الثعلب: ثعلب حجاب حقيقي بنفس الموديل، يحدد موقعه الثعلب الأصلي (دوران المرآة)، ويتبخر لما ينتهي عمره
function veilClone(e, st) {
  st.t += 2;
  if (st.t >= st.life) {
    const L = e.location;
    MONSTER.foxVanish(e.dimension, L); sfx(e.dimension, "sh.blackhole_end", L, 0.6, 1.8);
    try { e.remove(); } catch (err) { /* */ }
  }
}
// ═════════ ثعلب الحجاب: أربع مهارات خاصة به (ما تشبه أي وحش ثاني): ثعبان نار الثعلب، دوّامة المرايا، مطر الشمس، رفع القمر ═════════
function veilTick(e, st) {
  const dim = e.dimension, L = e.location;
  if (isClone(e)) { veilClone(e, st); return; }
  if (Math.random() < 0.4) glow(dim, { x: L.x + (Math.random() - 0.5) * 1.0, y: L.y + 1.4 + Math.random() * 0.8, z: L.z + 1.2 * (Math.random() - 0.5) }, { color: Math.random() < 0.5 ? FOXV : FOXC, size: 0.12, life: 0.8, rise: 0.6 });
  if (st.phase === 0) {
    st.cd -= 2; st.ult = (st.ult ?? 300) - 2;
    if (st.cd > 0) return;
    const np = nearestPlayer(e, 22);
    if (!np) { st.cd = 10; return; }
    st.target = np.p; st.t = 0;
    const opts = [];
    if (np.d >= 4 && np.d <= 20) opts.push("serpent");
    if (np.d >= 3 && np.d <= 13) opts.push("carousel");
    if (np.d <= 20) opts.push("shower");
    if (!opts.length) { st.cd = 10; return; }
    if (hpFrac(e) <= 0.5 && st.ult <= 0 && np.d <= 18) { st.skill = "moon"; st.ult = 900; setMState(e, 4); sfx(dim, "sh.chorus", L, 1.4, 0.5); }
    else { st.skill = pickSkill(opts, st.last); st.last = st.skill; setMState(e, { serpent: 1, carousel: 2, shower: 3 }[st.skill]); sfx(dim, "sh.chorus", L, 0.9, 1.3); }
    st.phase = 1;
    return;
  }
  const tp = valid(st.target) ? st.target : undefined;
  st.t += 2;
  const face = (loc) => { try { e.teleport(e.location, { facingLocation: { x: loc.x, y: e.location.y + 1, z: loc.z } }); } catch (err) { /* */ } };
  // ── 1) ثعبان نار الثعلب: قطار من 9 ألسنة نار روحية يزحف على الأرض بتعرّج جيبي (±2.4 بلوكة) باتجاهك، تتفاداه بالوقوف بين الموجات ──
  if (st.skill === "serpent") {
    if (tp && st.t <= 10) { st.dir = fwdTo(L, tp.location); face(tp.location); }
    if (st.t === 10) {
      st.sx = L.x; st.sz = L.z; st.sy = L.y; st.hitMap = new Map();
      st.wisps = [...Array(9).keys()].map(() => shapeFx(dim, "foxfire", { x: L.x, y: L.y + 0.7, z: L.z }, { r: 0.8, s: 240, life: 110 }));
      MONSTER.foxSummon(dim, L);
      sfx(dim, "sh.pull", L, 0.9, 1.5);
    }
    if (st.wisps && st.t > 10) {
      const step = (st.t - 10) / 2, d = st.dir || { x: 0, z: 1 }, perp = { x: -d.z, z: d.x };
      st.wisps.forEach((w, i) => {
        if (!w) return;
        const s = step * 1.1 - i * 1.4;
        if (s < 0) return;
        if (s > 28) { removeFx(w); st.wisps[i] = undefined; return; }
        const lat = 2.4 * Math.sin(s * 0.5), x = st.sx + d.x * s + perp.x * lat, z = st.sz + d.z * s + perp.z * lat;
        const y = groundAt(dim, x, z, st.sy) + 0.7;
        moveShape(w, { x, y, z });
        MONSTER.foxWisp(dim, { x, y, z }, i);
        for (const pl of dim.getPlayers({ location: { x, y, z }, maxDistance: 1.3 })) {
          const key = pl.id, n = st.hitMap.get(key) || 0, wk = key + ":" + i;
          if (n >= 3 || st.hitMap.has(wk)) continue;
          st.hitMap.set(wk, 1); st.hitMap.set(key, n + 1);
          hurtPlayer(pl, 4, e); try { pl.setOnFire(1, true); } catch (err) { /* */ }
          MONSTER.foxHit(dim, { x, y: y + 0.3, z }); notify(pl, "§dFoxfire Serpent!", 25);
        }
      });
    }
    if (st.t >= 84) { (st.wisps || []).forEach((w) => w && removeFx(w)); st.wisps = undefined; st.hitMap = undefined; grimEnd(e, st, 70); }
    return;
  }
  // ── 2) دوّامة المرايا: 4 ثعالب (هو + 3 ظلال حقيقية) تدور حولك بحلقة تضيق وتسرع، وبالنهاية كلها تنهار عليك مرة وحدة ──
  if (st.skill === "carousel") {
    if (st.t === 2 && tp) {
      st.cen = { x: tp.location.x, z: tp.location.z }; st.phi = Math.random() * 6.28; st.clones = []; st.touch = new Map();
      for (let i = 0; i < 3; i++) {
        try {
          const c = dim.spawnEntity("sh:veilfox", { x: L.x, y: L.y, z: L.z });
          c.setDynamicProperty("sh_clone", 1);
          try { c.nameTag = ""; c.addEffect("slowness", 90, { amplifier: 250, showParticles: false }); } catch (err) { /* */ }
          gst.set(c.id, { phase: 1, t: 0, cd: 0, skill: "clone", life: 74 });
          st.clones.push(c);
        } catch (err) { /* */ }
      }
      sfx(dim, "sh.kat_step", L, 1, 1.3); MONSTER.foxSplit(dim, L);
    }
    if (st.cen && st.t >= 4 && st.t <= 50) {
      if (tp) { st.cen.x += (tp.location.x - st.cen.x) * 0.25; st.cen.z += (tp.location.z - st.cen.z) * 0.25; }
      const k = (st.t - 4) / 46, rad = 5.2 - 2.9 * k * k;
      st.phi += 0.1 + 0.28 * k;
      const foxes = [e, ...(st.clones || [])];
      foxes.forEach((f, j) => {
        if (!valid(f)) return;
        const a = st.phi + j * Math.PI / 2, x = st.cen.x + Math.cos(a) * rad, z = st.cen.z + Math.sin(a) * rad, y = groundAt(dim, x, z, L.y);
        try { f.teleport({ x, y, z }, { facingLocation: { x: st.cen.x, y: y + 1, z: st.cen.z } }); } catch (err) { /* */ }
        MONSTER.foxAfter(dim, { x, y, z }, j);
        for (const pl of dim.getPlayers({ location: { x, y, z }, maxDistance: 1.5 })) {
          const key = pl.id + ":" + j;
          if ((st.touch.get(key) ?? -99) > st.t - 12) continue;
          st.touch.set(key, st.t); hurtPlayer(pl, j === 0 ? 3 : 2, e); pushAway({ x, z }, pl, 0.5, 0.2);
        }
      });
    }
    if (st.cen && st.t === 54) {                                              // الانهيار: الكل يقفز للمركز
      const C = { x: st.cen.x, y: groundAt(dim, st.cen.x, st.cen.z, L.y), z: st.cen.z };
      [e, ...(st.clones || [])].forEach((f, j) => {
        if (!valid(f)) return;
        const a = st.phi + j * Math.PI / 2;
        try { f.teleport({ x: C.x + Math.cos(a) * 1.3, y: C.y, z: C.z + Math.sin(a) * 1.3 }, { facingLocation: { x: C.x, y: C.y + 1, z: C.z } }); } catch (err) { /* */ }
      });
      MONSTER.foxCollapse(dim, C);
      sfx(dim, "sh.supernova_boom", C, 0.9, 1.6);
      for (const pl of dim.getPlayers({ location: C, maxDistance: 2.8 })) { hurtPlayer(pl, 9, e); pushAway(C, pl, 1.6, 0.5); try { pl.addEffect("weakness", 60, { amplifier: 0 }); } catch (err) { /* */ } shake(pl, 0.3, 0.3); }
    }
    if (st.t >= 62) { st.clones = undefined; st.cen = undefined; grimEnd(e, st, 80); }
    return;
  }
  // ── 3) مطر الشمس (زواج الثعلب): مطر قطرات نار ثعلب يهطل 3 ثواني على مساحة 8 بلوكات حواليك، كل قطرة تضرب لما تنزل ──
  if (st.skill === "shower") {
    if (tp && st.t <= 72) st.cen = { x: tp.location.x, z: tp.location.z };
    if (tp && st.t <= 10) face(tp.location);
    if (st.cen && st.t >= 10 && st.t <= 72) {
      for (let n = 0; n < 2; n++) {
        const aimed = n === 0 && tp && Math.random() < 0.55, a = Math.random() * 6.28, r = Math.random() * 8;
        const x = aimed ? tp.location.x + (Math.random() - 0.5) * 2 : st.cen.x + Math.cos(a) * r, z = aimed ? tp.location.z + (Math.random() - 0.5) * 2 : st.cen.z + Math.sin(a) * r;
        const y = groundAt(dim, x, z, L.y);
        dropShape(dim, "foxfire", x, y, z, 0.6, 6, 1); MONSTER.foxRain(dim, x, y, z);
        later(6, () => {
          MONSTER.foxDrop(dim, { x, y, z });
          for (const pl of dim.getPlayers({ location: { x, y: y + 1, z }, maxDistance: 1.5 })) { hurtPlayer(pl, 3, valid(e) ? e : undefined); try { pl.setOnFire(1, true); } catch (err) { /* */ } }
        });
      }
      if (st.t % 6 === 0) for (let i = 0; i < 6; i++) { const a = Math.random() * 6.28, r = Math.random() * 8; mcP(dim, { x: st.cen.x + Math.cos(a) * r, y: L.y + 6 + Math.random() * 3, z: st.cen.z + Math.sin(a) * r }, "minecraft:glow_particle", FOXC, { x: 0, y: -0.6, z: 0 }); }
      if (st.t % 12 === 10) MONSTER.foxCloud(dim, { x: st.cen.x, y: L.y + 6.8, z: st.cen.z }, 4.5);
    }
    if (st.t >= 84) { st.cen = undefined; grimEnd(e, st, 75); }
    return;
  }
  // ── 4) رفع القمر (مهارة نهائية عند نص الصحة): يرفعك بالهواء وتنزل عليك 3 موجات أهلّة قمر قبل ما تقدر تنزل ──
  if (st.skill === "moon") {
    if (st.t === 8) {
      st.victims = dim.getPlayers({ location: L, maxDistance: 16 });
      for (const pl of st.victims) { try { pl.addEffect("levitation", 38, { amplifier: 2, showParticles: false }); } catch (err) { /* */ } notify(pl, "§dThe Veilfox lifts you into the moonlight!", 50); MONSTER.foxLift(dim, pl.location); }
      sfx(dim, "sh.chorus", L, 1.4, 1.6); MONSTER.foxMoonRise(dim, L);
    }
    for (const w of [18, 30, 42]) {
      if (st.t !== w) continue;
      sfx(dim, "sh.kat_wave", L, 1, 1.5);
      for (const pl of st.victims || []) {
        if (!valid(pl)) continue;
        const from = { x: L.x, y: L.y + 2.2, z: L.z }, c = center3(pl), dx = c.x - from.x, dy = c.y - from.y, dz = c.z - from.z, l = Math.hypot(dx, dy, dz) || 1;
        for (let k = -1; k <= 1; k++) {
          const a0 = Math.atan2(dz, dx) + k * 0.3, hl = Math.hypot(dx, dz) || 1, dir = { x: Math.cos(a0) * hl / l, y: dy / l, z: Math.sin(a0) * hl / l };
          const hit = new Set();
          flyFx(dim, from, dir, 1.3, 26, (pos) => {
            MONSTER.moonStep(dim, pos, dir);                                  // هلال قمر من لمعات End Rod يطير لك
            for (const p2 of dim.getPlayers({ location: pos, maxDistance: 1.7 })) {
              if (hit.has(p2.id)) continue;
              hit.add(p2.id); hurtPlayer(p2, 7, valid(e) ? e : undefined); MONSTER.foxMoonHit(dim, center3(p2)); shake(p2, 0.2, 0.2);
            }
            return false;
          });
        }
      }
    }
    if (st.t === 50) for (const pl of st.victims || []) { try { if (valid(pl)) pl.addEffect("slow_falling", 120, { amplifier: 0, showParticles: false }); } catch (err) { /* */ } }
    if (st.t >= 60) { st.victims = undefined; grimEnd(e, st, 90); }
  }
}
// ═════════════════════════ ماغماموث (Magmamoth، Vile): ماموث بركاني بخمس مهارات خاصة ═════════════════════════
// كل نار هنا لهب ماينكرافت الأصلي (small_flame_particle = لهب المشعل البرتقالي الطبيعي) + جمرات lava_particle + glow_particle ملوّن، بدون أشكال مصنوعة
const MAGC = [1.0, 0.42, 0.08], MAGY = [1.0, 0.78, 0.25];
const MOUTH_F = 5.0, MOUTH_H = 3.0;                               // فوهة الخرطوم أثناء النفخ (مقيسة من أنيميشن النموذج): 5 بلوكات لقدام و3 ارتفاع
const setHot = (e, v) => { try { e.setProperty("sh:hot", v); } catch (err) { /* */ } };
const UP = { x: 0, y: 1, z: 0 };
// رقع نار على الأرض (آثار الاندفاع، نهاية تيار النفخ، سقوط القذائف): لهب طبيعي يطلع وجمرات، وتحرق اللي يوقف فيها
function addPatch(st, dim, x, y, z, life = 60) { (st.patches = st.patches || []).push({ dim, x, y, z, until: system.currentTick + life, n: 0 }); }
function patchTick(st) {
  if (!st.patches || !st.patches.length) return;
  const now = system.currentTick;
  st.patches = st.patches.filter((p) => now < p.until);
  for (const p of st.patches) {
    p.n++;
    for (let k = 0; k < 3; k++) flame(p.dim, { x: p.x + (Math.random() - 0.5) * 1.3, y: p.y + 0.1, z: p.z + (Math.random() - 0.5) * 1.3 }, UP, 0.5 + Math.random() * 0.8);
    if (p.n % 2 === 0) bigFlame(p.dim, { x: p.x + (Math.random() - 0.5) * 0.9, y: p.y, z: p.z + (Math.random() - 0.5) * 0.9 });
    if (p.n % 4 === 0) embers(p.dim, { x: p.x, y: p.y + 0.2, z: p.z });
    if (p.n % 3 === 0) vanillaFx(p.dim, "minecraft:basic_flame_particle", { x: p.x + (Math.random() - 0.5) * 0.8, y: p.y + 0.1, z: p.z + (Math.random() - 0.5) * 0.8 });
    if (p.n % 6 === 0) for (const pl of p.dim.getPlayers({ location: { x: p.x, y: p.y + 0.5, z: p.z }, maxDistance: 1.2 })) { hurtPlayer(pl, 2, undefined); try { pl.setOnFire(2, true); } catch (err) { /* */ } }
  }
}
function mammothTick(e, st) {
  const dim = e.dimension, L = e.location;
  const hot = st.hot > 0;
  patchTick(st);
  if (Math.random() < (hot ? 0.9 : 0.35)) {                      // جمر يتصاعد من تاج الصخر
    const a = Math.random() * 6.28, r = 0.5 + Math.random() * 1.6;
    flame(dim, { x: L.x + Math.cos(a) * r, y: L.y + 3.7, z: L.z + Math.sin(a) * r }, UP, 0.6 + Math.random() * 0.6);
    if (hot) embers(dim, { x: L.x + Math.cos(a) * 1.9, y: L.y + 1.4 + Math.random() * 2.2, z: L.z + Math.sin(a) * 1.9 });
  }
  if (hot) {                                                      // درع الماغما: لهب حواليه، وحرق للقريب
    st.hot -= 2;
    if (st.hot % 4 === 0) for (let i = 0; i < 8; i++) { const a = Math.random() * 6.28; flame(dim, { x: L.x + Math.cos(a) * 2.3, y: L.y + 0.3 + Math.random() * 3.4, z: L.z + Math.sin(a) * 2.3 }, UP, 0.8 + Math.random() * 0.8); if (i % 2 === 0) bigFlame(dim, { x: L.x + Math.cos(a) * 2.2, y: L.y + 0.2 + Math.random() * 1.5, z: L.z + Math.sin(a) * 2.2 }); }
    if (st.hot % 20 === 0) for (const pl of dim.getPlayers({ location: L, maxDistance: 3.8 })) { hurtPlayer(pl, 2, e); try { pl.setOnFire(2, true); } catch (err) { /* */ } }
    if (st.hot <= 0) { setHot(e, 0); st.hot = 0; }
  }
  const face = (loc) => { try { e.teleport(e.location, { facingLocation: { x: loc.x, y: e.location.y + 1, z: loc.z } }); } catch (err) { /* */ } };
  if (st.phase === 0) {
    st.cd -= 2;
    if (st.cd > 0) return;
    const np = nearestPlayer(e, 26);
    if (!np) { st.cd = 10; return; }
    st.target = np.p; st.t = 0;
    const opts = [];
    if (np.d < 8) opts.push("stomp");
    if (np.d >= 7 && np.d <= 16) opts.push("breath");              // الفوهة 5 بلوكات قدام الماموث، فلازم اللاعب أبعد منها
    if (np.d >= 6 && np.d <= 26) opts.push("stampede");
    if (np.d >= 5) opts.push("bombard");
    if (!hot && hpFrac(e) < 0.75) opts.push("armor");
    if (!opts.length) { st.cd = 10; return; }
    st.skill = pickSkill(opts, st.last); st.last = st.skill;
    setMState(e, { stomp: 1, breath: 2, stampede: 6, bombard: 4, armor: 5 }[st.skill]);
    st.phase = 1; st.stage = 0; st.aimDir = undefined; st.a0 = undefined;
    return;
  }
  const tp = valid(st.target) ? st.target : undefined;
  st.t += 2;
  // ── 1) دكّة الشقوق: يرفع رجله ويدق: حلقة صدمة قريبة (تدفع) ثم 8 شقوق ماغما تنطلق شعاعياً وتنفجر نقطة بعد نقطة (بين الشقوق آمن) ──
  if (st.skill === "stomp") {
    if (tp && st.t < 16) face(tp.location);
    if (st.t === 18) {
      const C = { x: L.x, y: L.y, z: L.z }, hitS = new Set(), a0 = Math.random() * 6.28;
      sfx(dim, "sh.guard_slam", C, 1.6, 0.5); sfx(dim, "sh.collapse", C, 1.0, 0.7);
      MONSTER.mamStomp(dim, C); rockBurst(dim, C, 8, 1.1);
      for (const q of dim.getPlayers({ location: C, maxDistance: 22 })) shake(q, 0.35, 0.35);
      for (let k = 0; k < 3; k++) later(k, () => fireRing(dim, C, 1.2 + k * 1.2, 22 + k * 8));
      for (const pl of dim.getPlayers({ location: C, maxDistance: 3.8 })) { hurtPlayer(pl, 7, e); pushAway(C, pl, 2.0, 0.6); notify(pl, "§6Magma Stomp!", 30); hitS.add(pl.id); }
      for (let j = 0; j < 8; j++) {
        const ang = a0 + (j / 8) * Math.PI * 2, dx = Math.cos(ang), dz = Math.sin(ang);
        for (let k = 1; k <= 9; k++) {
          const px = C.x + dx * (2.5 + k * 1.05), pz = C.z + dz * (2.5 + k * 1.05), py = groundAt(dim, px, pz, C.y);
          later(k, () => {
            MONSTER.mamCrack(dim, { x: px, y: py, z: pz });
            later(7, () => {
              MONSTER.mamErupt(dim, { x: px, y: py, z: pz }, k % 3 === 0);
              for (const pl of dim.getPlayers({ location: { x: px, y: py + 1, z: pz }, maxDistance: 1.3 })) {
                if (hitS.has(pl.id)) continue;
                hitS.add(pl.id); hurtPlayer(pl, 6, valid(e) ? e : undefined); try { pl.setOnFire(2, true); } catch (err) { /* */ }
                pushAway(C, pl, 0.7, 0.4); notify(pl, "§6Magma fissure!", 25);
              }
            });
          });
        }
      }
    }
    if (st.t >= 46) grimEnd(e, st, 75);
    return;
  }
  // ── 2) كنس الجحيم: يرفع خرطومه وينفث نار حقيقية (لهب المشعل الأصلي، مو حمم) من فوهة الخرطوم نحو صدرك، ويكنس جانبياً ±55° خلال 3 ثواني ──
  if (st.skill === "breath") {
    if (tp && st.t < 18) {                                         // يثبّت التصويب: الاتجاه الأفقي + زاوية نزول اللهب من الفوهة (3 بلوكات ارتفاع) لصدر اللاعب
      const dx = tp.location.x - L.x, dz = tp.location.z - L.z;
      st.a0 = Math.atan2(dz, dx);
      if (st.sgn === undefined) st.sgn = Math.random() < 0.5 ? 1 : -1;
      st.pitch = Math.max(0.12, Math.min(0.7, Math.atan2(MOUTH_H - 1.1, Math.max(2, Math.hypot(dx, dz) - MOUTH_F))));
      face(tp.location);
    }
    if (st.a0 === undefined) { st.a0 = 0; st.pitch = 0.3; }
    if (st.t >= 18 && st.t <= 82) {
      const k = (st.t - 18) / 64, ang = st.a0 + st.sgn * (-0.95 + 1.9 * k), ch = Math.cos(st.pitch);
      const u = { x: Math.cos(ang) * ch, y: -Math.sin(st.pitch), z: Math.sin(ang) * ch };
      try { e.teleport(L, { facingLocation: { x: L.x + Math.cos(ang) * 5, y: L.y + 1, z: L.z + Math.sin(ang) * 5 } }); } catch (err) { /* */ }
      const M = { x: L.x + Math.cos(ang) * MOUTH_F, y: L.y + MOUTH_H, z: L.z + Math.sin(ang) * MOUTH_F };
      const len = Math.min(13, (MOUTH_H + 0.2) / Math.sin(st.pitch) + 1.0);          // التيار ينتهي لما يلمس الأرض
      const at = (d, w) => ({ x: M.x + u.x * d + (Math.random() - 0.5) * 2 * w, y: M.y + u.y * d + (Math.random() - 0.5) * 2 * w, z: M.z + u.z * d + (Math.random() - 0.5) * 2 * w });
      for (let i = 0; i < 40; i++) {                              // نار دقيقة: لهب المشعل ينطلق مع التيار، أكثف قرب الفوهة ويتسع مخروطياً
        const d = 0.3 + Math.pow(Math.random(), 0.85) * len, j = 0.25;
        flame(dim, at(d, 0.1 + d * 0.085), { x: u.x + (Math.random() - 0.5) * j, y: u.y + (Math.random() - 0.5) * j, z: u.z + (Math.random() - 0.5) * j }, 3 + Math.random() * 5);
      }
      for (let i = 0; i < 12; i++) bigFlame(dim, at(0.6 + Math.pow(Math.random(), 0.9) * len, 0.06 + 0.04 * len * Math.random()));   // لهب الكيان المحترق الكبير: هو جسم التيار
      for (let i = 0; i < 8; i++) mcP(dim, at(Math.random() * 4.5, 0.12), "minecraft:glow_particle", i % 2 ? MAGY : MAGC, rndDir(0.2));   // قلب مضيء قرب الفوهة
      if (Math.random() < 0.8) embers(dim, at(1 + Math.random() * len, 0.3));
      if (st.t % 4 === 0) vanillaFx(dim, "minecraft:basic_smoke_particle", at(len * 0.9, 0.3));
      if (st.t % 6 === 0) MONSTER.mamSnort(dim, M);
      const E = at(len, 0);
      const gy = groundAt(dim, E.x, E.z, L.y);
      for (let i = 0; i < 6; i++) flame(dim, { x: E.x + (Math.random() - 0.5) * 1.6, y: gy + 0.1, z: E.z + (Math.random() - 0.5) * 1.6 }, UP, 1 + Math.random() * 1.5);   // لهب يتناثر عند الأرض
      if (st.t % 4 === 0) {
        sfx(dim, "sh.imp_pounce", M, 0.8, 0.6);
        for (const pl of dim.getPlayers({ location: M, maxDistance: 15 })) {
          const c = center3(pl), vx = c.x - M.x, vy = c.y - M.y, vz = c.z - M.z, along = vx * u.x + vy * u.y + vz * u.z;
          if (along < 0 || along > len + 0.8) continue;
          const perp = Math.hypot(vx - u.x * along, vy - u.y * along, vz - u.z * along);
          if (perp > 0.9 + along * 0.1) continue;
          hurtPlayer(pl, 3, e); try { pl.setOnFire(3, true); } catch (err) { /* */ }
        }
      }
      if (st.t % 6 === 0) addPatch(st, dim, E.x, gy, E.z, 50);
    }
    if (st.t >= 90) { st.a0 = undefined; grimEnd(e, st, 80); }
    return;
  }
  // ── 3) اندفاع الأنياب المزدوج: ينزل راسه ويحك الأرض ثم يندفع، ويعيد التصويب ويندفع ثانية. أول لاعب ينلحقه ينرفع بالأنياب. وراه رقع نار ──
  if (st.skill === "stampede") {
    if (st.stage === 0) {
      if (tp && st.t <= 20) st.dir = fwdTo(L, tp.location);
      const d = st.dir || { x: 0, z: 1 };
      face({ x: L.x + d.x * 5, z: L.z + d.z * 5 });
      if (st.t % 4 === 0) { rockBurst(dim, { x: L.x + d.x * 2.4, y: L.y, z: L.z + d.z * 2.4 }, 2, 0.5); MONSTER.mamPaw(dim, L, d); for (let q = 0; q < 2; q++) flame(dim, { x: L.x + d.x * 2.4 + (Math.random() - 0.5) * 1.5, y: L.y + 0.2, z: L.z + d.z * 2.4 + (Math.random() - 0.5) * 1.5 }, UP, 1.2); }
      if (st.t >= 26) { st.stage = 1; st.t = 0; st.hit = new Set(); setMState(e, 3); sfx(dim, "sh.stardash", L, 1.4, 0.5); MONSTER.mamCharge(dim, L, d); }
      return;
    }
    if (st.stage === 2) {                                      // وقفة قصيرة وإعادة تصويب
      if (tp) { st.dir = fwdTo(L, tp.location); face(tp.location); }
      if (st.t >= 10) { st.stage = 3; st.t = 0; setMState(e, 3); sfx(dim, "sh.stardash", L, 1.4, 0.6); MONSTER.mamCharge(dim, L, st.dir || { x: 0, z: 1 }); }
      return;
    }
    const d = st.dir || { x: 0, z: 1 };
    const nx = L.x + d.x * 1.5, nz = L.z + d.z * 1.5;
    const blocked = !airAt(dim, nx + d.x * 1.6, L.y + 0.6, nz + d.z * 1.6) || !airAt(dim, nx + d.x * 1.6, L.y + 1.8, nz + d.z * 1.6) || !airAt(dim, nx + d.x * 1.6, L.y + 3.0, nz + d.z * 1.6);
    const crash = () => {
      MONSTER.mamCrash(dim, { x: L.x + d.x * 1.8, y: L.y, z: L.z + d.z * 1.8 }); rockBurst(dim, L, 8, 1.2); sfx(dim, "sh.guard_slam", L, 1.4, 0.6);
      for (const q of dim.getPlayers({ location: L, maxDistance: 16 })) shake(q, 0.4, 0.4);
      try { e.addEffect("slowness", 50, { amplifier: 5, showParticles: false }); } catch (err) { /* */ }
      st.stage = 0; grimEnd(e, st, 90);
    };
    if (blocked) { crash(); return; }
    if (st.t > 14) {                                           // انتهت هالاندفاعة: إما وقفة وثانية، أو النهاية
      if (st.stage === 1) { st.stage = 2; st.t = 0; setMState(e, 6); return; }
      st.stage = 0; grimEnd(e, st, 85); return;
    }
    try { e.teleport({ x: nx, y: groundAt(dim, nx, nz, L.y), z: nz }, { facingLocation: { x: nx + d.x, y: L.y + 1, z: nz + d.z } }); } catch (err) { /* */ }
    addPatch(st, dim, L.x - d.x * 1.6, groundAt(dim, L.x, L.z, L.y), L.z - d.z * 1.6, 70);
    for (let i = 0; i < 4; i++) { const a = Math.random() * 6.28; flame(dim, { x: L.x + Math.cos(a) * 1.6, y: L.y + 0.2 + Math.random() * 1.0, z: L.z + Math.sin(a) * 1.6 }, UP, 1.0); }
    MONSTER.mamTrail(dim, L, d);
    const front = { x: L.x + d.x * 2.2, y: L.y + 1.2, z: L.z + d.z * 2.2 };
    for (const pl of dim.getPlayers({ location: front, maxDistance: 2.9 })) {
      if (st.hit.has(pl.id)) continue;
      st.hit.add(pl.id); hurtPlayer(pl, 12, e);
      try { pl.applyKnockback({ x: d.x * 0.5, z: d.z * 0.5 }, 1.1); } catch (err) { /* */ }          // رفع بالأنياب
      shake(pl, 0.5, 0.4); notify(pl, "§6Tusk Toss!", 30);
      MONSTER.mamToss(dim, pl.location); fireRing(dim, pl.location, 1.5, 14);
      st.stage = 0; grimEnd(e, st, 90); return;
    }
    return;
  }
  // ── 4) قصف بركاني: يقف على رجليه ويرمي 10 صخور نار ضخمة للسما، تسقط بقوس على أماكنكم (واحدة على كل لاعب) وتخلي رقع نار ──
  if (st.skill === "bombard") {
    if (st.t === 20) {
      sfx(dim, "sh.guard_slam", L, 1.6, 0.5); sfx(dim, "sh.supernova_boom", L, 1.0, 0.6);
      for (const q of dim.getPlayers({ location: L, maxDistance: 24 })) shake(q, 0.35, 0.4);
      MONSTER.mamEruptCrown(dim, { x: L.x, y: L.y + 3.9, z: L.z });
      const sites = [];
      for (const pl of dim.getPlayers({ location: L, maxDistance: 26 })) { sites.push({ x: pl.location.x, z: pl.location.z }); sites.push({ x: pl.location.x + (Math.random() - 0.5) * 5, z: pl.location.z + (Math.random() - 0.5) * 5 }); }
      while (sites.length < 10) { const a = Math.random() * 6.28, r = 4 + Math.random() * 10; sites.push({ x: L.x + Math.cos(a) * r, z: L.z + Math.sin(a) * r }); }
      sites.slice(0, 12).forEach((b, i) => later(i * 2, () => {
        const from = { x: L.x, y: L.y + 4.2, z: L.z }, gy = groundAt(dim, b.x, b.z, L.y), to = { x: b.x, y: gy, z: b.z }, T = 30 + (i % 4) * 4;
        const bomb = shapeFx(dim, "fireball", from, { r: 1.1, w: 500, life: T + 4 });
        later(T - 12, () => fireRing(dim, to, 1.6, 14, 0.2));
        tween(T, 1, (q) => {
          const pos = { x: from.x + (to.x - from.x) * q, y: from.y + (to.y - from.y) * q + Math.sin(Math.PI * q) * 11, z: from.z + (to.z - from.z) * q };
          moveShape(bomb, pos);
          const qt = Math.round(q * T);
          if (qt % 2 === 0) { for (let k = 0; k < 2; k++) flame(dim, { x: pos.x + (Math.random() - 0.5) * 0.5, y: pos.y + (Math.random() - 0.5) * 0.5, z: pos.z + (Math.random() - 0.5) * 0.5 }, UP, 0.5); MONSTER.mamBombTrail(dim, pos, qt / 2); }
        }, () => {
          removeFx(bomb);
          MONSTER.mamBombHit(dim, { x: to.x, y: gy, z: to.z }); rockBurst(dim, to, 3, 1.0);
          for (let k = 0; k < 10; k++) flame(dim, { x: to.x + (Math.random() - 0.5) * 1.6, y: gy + 0.2, z: to.z + (Math.random() - 0.5) * 1.6 }, UP, 2 + Math.random() * 2);
          sfx(dim, "sh.meteor_hit", to, 0.8, 1.2);
          for (const pl of dim.getPlayers({ location: { x: to.x, y: gy + 1, z: to.z }, maxDistance: 2.6 })) { hurtPlayer(pl, 9, valid(e) ? e : undefined); try { pl.setOnFire(3, true); } catch (err) { /* */ } pushAway(to, pl, 1.4, 0.4); notify(pl, "§6Volcanic Bomb!", 30); }
          addPatch(st, dim, to.x, gy, to.z, 60);
        });
      }));
    }
    if (st.t >= 76) grimEnd(e, st, 90);
    return;
  }
  // ── 5) درع الماغما: الشقوق تتوهج أبيض وأصفر ولهب حواليه، ويقل عليه الضرر (مقاومة) لـ 9 ثواني ──
  if (st.skill === "armor") {
    if (st.t === 14) {
      st.hot = 180; setHot(e, 1);
      try { e.addEffect("resistance", 190, { amplifier: 2, showParticles: false }); } catch (err) { /* */ }
      sfx(dim, "sh.supernova_boom", L, 1.0, 0.6); sfx(dim, "sh.chorus", L, 1.2, 0.4);
      MONSTER.mamArmor(dim, L);
      for (let h = 0; h < 4; h++) later(h * 2, () => fireRing(dim, L, 2.2 + h * 0.5, 24, 0.3 + h * 0.9));
      for (const pl of dim.getPlayers({ location: L, maxDistance: 24 })) notify(pl, "§6The Magmamoth's cracks blaze: damage reduced!", 50);
    }
    if (st.t % 4 === 0 && st.t < 14) MONSTER.mamArmorCharge(dim, L);
    if (st.t >= 30) grimEnd(e, st, 90);
  }
}
// ═════════════════════════ الدب الرمادي (Grey Bear، Vile) وجروه ═════════════════════════
// دب واقف على رجلين. أربع مهارات خاصة + جلد ثخين:
//  1) Bear Hug: يفتح ذراعيه ويمسكك ويعصرك 3 مرات ويرميك. تفلت إذا ضربته 3 مرات أو سويت داش.
//  2) Rending Claws (خرمشة): أربع لطمات مخالب تخرمش جسمك (خطوط مخالب على جسمك) وتنزفك.
//  3) Cub Call: يزأر ويطلع جروين يتعلقون برجلك؛ إذا قتلت جرو يغضب الدب.
//  4) Deep Hibernation: عند صحة قليلة ينام ويتعافى؛ إذا ضربته يصحى بغضب ويدفعك.
//  جلد ثخين: الضرب من قدام ينقص 30%، ومن ورا يزيد 20%.
// كل المؤثرات جزيئات ماينكرافت الأصلية (glow_particle، critical_hit_emitter، explosion_particle، villager_angry، villager_happy).
const BEAR = "sh:grey_bear", CUB = "sh:bear_cub";
const BLOOD = [0.62, 0.04, 0.05], FURG = [0.62, 0.6, 0.58];
const bleeds = new Map();                                                    // player.id → { n: طبقات النزف (حد 3), until }
function addBleed(pl, n = 1) {
  const b = bleeds.get(pl.id) || { n: 0, until: 0 };
  b.n = Math.min(3, b.n + n); b.until = system.currentTick + 80; bleeds.set(pl.id, b);      // النزف 4 ثواني من آخر خرمشة
}
system.runInterval(() => {                                                   // النزف: ضرر كل ثانية حسب الطبقات + قطرات حمرا
  const now = system.currentTick;
  for (const pl of world.getAllPlayers()) {
    const b = bleeds.get(pl.id);
    if (!b) continue;
    if (now > b.until || !valid(pl)) { bleeds.delete(pl.id); continue; }
    hurtPlayer(pl, b.n, undefined);
    for (let i = 0; i < 2 + b.n; i++) mcP(pl.dimension, { x: pl.location.x + (Math.random() - 0.5) * 0.6, y: pl.location.y + 0.4 + Math.random() * 0.9, z: pl.location.z + (Math.random() - 0.5) * 0.6 }, "minecraft:glow_particle", BLOOD, { x: 0, y: -0.6, z: 0 });
  }
}, 20);
const hpOf = (e) => { try { return e.getComponent("minecraft:health").currentValue; } catch (err) { return 0; } };
// خرمشة على جسم اللاعب: 3 خطوط مخالب مائلة ومتوازية على وجهه المقابل للدب (شرار عظمي + بكسلات حمرا)
function clawMarks(dim, at, from, side, top = 1.35) { MONSTER.bearClaw(dim, at, from, side, top); }
function bearRage(e, st, ticks) {
  st.rage = Math.max(st.rage || 0, ticks); setHot(e, 1);
  try { e.addEffect("speed", ticks, { amplifier: 0, showParticles: false }); e.addEffect("strength", ticks, { amplifier: 0, showParticles: false }); } catch (err) { /* */ }
}
// نفَس الزئير: نفخات دخان ماينكرافت (explosion_particle) طالعة من الفم لقدام
function roarPuff(dim, L, f, n = 14) {
  const m = { x: L.x + f.x * 1.6, y: L.y + 2.7, z: L.z + f.z * 1.6 };
  for (let i = 0; i < n; i++) mcP(dim, m, "minecraft:explosion_particle", undefined, undefined, { "velocity.x": f.x * 0.45 + (Math.random() - 0.5) * 0.25, "velocity.y": (Math.random() - 0.3) * 0.12, "velocity.z": f.z * 0.45 + (Math.random() - 0.5) * 0.25 });
}
// عصرة العناق: حلقة شرار عظمي تنضغط على خصر اللاعب (بعيد عن عيونه حتى ما تغطي الشاشة) + شرارة ضربة حرجة
function crushFx(dim, at) { MONSTER.bearCrush(dim, at); }
// أثر لطمة المخالب بالهوا: 3 أقواس متوازية قرب كف الدب، من فوق لتحت ومن جهة لجهة حسب اليد
function swipeArc(dim, L, f, side) { MONSTER.bearSwipe(dim, L, f, side); }
// حلقة دخان على الأرض تنتشر لبرا (زئير/صحوة/سقوط)
function dustRing(dim, c, n, speed, r0 = 0.8) {
  for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2; mcP(dim, { x: c.x + Math.cos(a) * r0, y: c.y + 0.25, z: c.z + Math.sin(a) * r0 }, "minecraft:explosion_particle", undefined, undefined, { "velocity.x": Math.cos(a) * speed, "velocity.y": 0.02, "velocity.z": Math.sin(a) * speed }); }
}
function bearTick(e, st) {
  const dim = e.dimension, L = e.location;
  if (st.rage > 0) {                                                        // الغضب: عيون حمرا ومخالب حمرا + غضب قروي فوق راسه
    st.rage -= 2;
    if (st.rage % 10 === 0) mcP(dim, { x: L.x + (Math.random() - 0.5) * 0.8, y: L.y + 3.5, z: L.z + (Math.random() - 0.5) * 0.8 }, "minecraft:villager_angry");
    if (st.rage <= 0) setHot(e, 0);
  }
  if (st.hibCd > 0) st.hibCd -= 2;
  if (st.cubCd > 0) st.cubCd -= 2;
  const face = (loc) => { try { e.teleport(e.location, { facingLocation: { x: loc.x, y: e.location.y + 1, z: loc.z } }); } catch (err) { /* */ } };
  const stepTo = (loc, k) => { const u = fwdTo(L, loc), nx = L.x + u.x * k, nz = L.z + u.z * k; if (airAt(dim, nx + u.x, L.y + 0.5, nz + u.z) && airAt(dim, nx + u.x, L.y + 1.6, nz + u.z)) { try { e.teleport({ x: nx, y: groundAt(dim, nx, nz, L.y), z: nz }, { facingLocation: { x: loc.x, y: L.y + 1, z: loc.z } }); } catch (err) { /* */ } } };
  if (st.phase === 0) {
    st.cd -= 2;
    if (st.cd > 0) return;
    const np = nearestPlayer(e, 22);
    if (!np) { st.cd = 10; return; }
    st.target = np.p; st.t = 0; st.stage = 0; st.victim = undefined;
    const opts = [];
    if (np.d < 3.8) opts.push("hug", "scratch");
    else if (np.d <= 10) opts.push("scratch");
    const cubsAlive = (st.cubs || []).some((id) => { const c = world.getEntity(id); return c && valid(c); });
    if (np.d >= 4 && !cubsAlive && !(st.cubCd > 0)) opts.push("cubs");
    if (hpFrac(e) < 0.45 && !(st.hibCd > 0)) opts.push("sleep", "sleep");
    if (!opts.length) { st.cd = 10; return; }
    st.skill = pickSkill(opts, st.last); st.last = st.skill;
    setMState(e, { hug: 1, scratch: 4, cubs: 5, sleep: 6 }[st.skill]);
    st.phase = 1;
    return;
  }
  const tp = valid(st.target) ? st.target : undefined;
  st.t += 2;
  // ── 1) Bear Hug: يفتح ذراعيه ويخطو، يمسك اللي قدامه ويعصره 3 مرات، ثم يلف ويرميه ──
  if (st.skill === "hug") {
    if (st.stage === 0) {
      if (tp) { face(tp.location); if (st.t > 4 && Math.hypot(tp.location.x - L.x, tp.location.z - L.z) > 2.0) stepTo(tp.location, 0.35); }
      if (st.t === 4) { sfx(dim, "mob.polarbear.warning", L, 1.3, 0.8); MONSTER.bearRoar(dim, L, tp ? fwdTo(L, tp.location) : { x: 0, z: 1 }); }
      if (st.t >= 16) {
        const f = tp ? fwdTo(L, tp.location) : { x: 0, z: 1 };
        for (const pl of dim.getPlayers({ location: L, maxDistance: 3.4 })) {
          const vx = pl.location.x - L.x, vz = pl.location.z - L.z, l = Math.hypot(vx, vz) || 1;
          if ((vx * f.x + vz * f.z) / l < 0.4) continue;
          st.victim = pl; break;
        }
        if (!st.victim) { grimEnd(e, st, 50); return; }                       // فلت من المسكة
        st.stage = 1; st.t = 0; st.f = f; st.hits = 0; st.hpLast = hpOf(e); setMState(e, 2);
        notify(st.victim, "§cThe Grey Bear grabs you! §7Hit it 3 times or dash to break free", 40); MONSTER.bearGrab(dim, { x: L.x + f.x * 1.25, y: L.y + 0.7, z: L.z + f.z * 1.25 });
        sfx(dim, "mob.polarbear.warning", L, 1.5, 0.6);
      }
      return;
    }
    const pl = st.victim;
    if (!pl || !valid(pl)) { grimEnd(e, st, 60); return; }
    const f = st.f, hold = { x: L.x + f.x * 1.25, y: L.y + 0.7, z: L.z + f.z * 1.25 };
    if (st.stage === 1) {
      if (st.t > 2 && Math.hypot(pl.location.x - hold.x, pl.location.z - hold.z) > 1.1) {   // انفلت (داش أو دفع)
        notify(pl, "§aYou slipped out of the Bear Hug!", 30); MONSTER.bearBreak(dim, center3(pl));
        try { e.addEffect("slowness", 30, { amplifier: 3, showParticles: false }); } catch (err) { /* */ }
        grimEnd(e, st, 60); return;
      }
      const h = hpOf(e);
      if (h < st.hpLast - 0.01) st.hits++;
      st.hpLast = h;
      if (st.hits >= 3) {                                                     // 3 ضربات: يترنح ويفلتك
        notify(pl, "§aYou broke free! The bear staggers.", 35);
        try { e.addEffect("slowness", 50, { amplifier: 5, showParticles: false }); e.addEffect("weakness", 50, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
        MONSTER.bearBreak(dim, { x: L.x, y: L.y + 0.9, z: L.z });
        grimEnd(e, st, 80); return;
      }
      try { pl.teleport(hold, { facingLocation: { x: L.x, y: L.y + 2.4, z: L.z } }); } catch (err) { /* */ }
      if (st.t === 10 || st.t === 20 || st.t === 30) {                         // عصرة
        hurtPlayer(pl, 3, e); shake(pl, 0.25, 0.2);
        crushFx(dim, hold);
        sfx(dim, "sh.guard_slam", hold, 0.6, 1.6);
      }
      if (st.t >= 36) { st.stage = 2; st.t = 0; setMState(e, 3); }
      return;
    }
    // stage 2: يلف ويرمي
    if (st.t <= 6) { const a = Math.atan2(f.z, f.x) - st.t * 0.22, sp = { x: L.x + Math.cos(a) * 1.25, y: L.y + 0.9, z: L.z + Math.sin(a) * 1.25 }; try { pl.teleport(sp, { facingLocation: { x: L.x, y: L.y + 2.4, z: L.z } }); } catch (err) { /* */ } }
    if (st.t === 8) {
      const a = Math.atan2(f.z, f.x) - 1.4, d = { x: Math.cos(a), z: Math.sin(a) };
      hurtPlayer(pl, 6, e);
      try { pl.applyKnockback({ x: d.x * 2.4, z: d.z * 2.4 }, 0.9); } catch (err) { /* */ }
      shake(pl, 0.5, 0.45); notify(pl, "§cThrown by the Bear Hug!", 30);
      roarPuff(dim, L, d, 10); MONSTER.bearRoar(dim, L, d); sfx(dim, "mob.polarbear.warning", L, 1.6, 0.5);
      for (let k = 1; k <= 9; k++) later(k * 2, () => { if (valid(pl)) mcP(dim, { x: pl.location.x, y: pl.location.y + 0.6, z: pl.location.z }, "minecraft:explosion_particle", undefined, undefined, { "velocity.x": 0, "velocity.y": 0, "velocity.z": 0 }); });   // أثر غبار ورا اللاعب وهو طاير
      later(22, () => { if (valid(pl)) dustRing(dim, pl.location, 14, 0.4, 0.5); });                                                                                // غبار الطيحة
    }
    if (st.t >= 14) grimEnd(e, st, 80);
    return;
  }
  // ── 2) Rending Claws (خرمشة): 4 لطمات بالتناوب يمين/يسار والأخيرة بالكفين، كل وحدة تخرمش جسمك وتنزفك ──
  if (st.skill === "scratch") {
    if (tp) { face(tp.location); if (st.t < 34 && Math.hypot(tp.location.x - L.x, tp.location.z - L.z) > 2.4) stepTo(tp.location, 0.45); }
    const side = { 8: 1, 16: -1, 24: 1, 32: 0 }[st.t];
    if (side !== undefined) {
      const f = tp ? fwdTo(L, tp.location) : { x: 0, z: 1 };
      sfx(dim, "sh.dagger_hit", L, 0.9, side === 0 ? 0.5 : 0.7);
      swipeArc(dim, L, f, side); if (side === 0) swipeArc(dim, L, f, -1);
      let hit = false;
      for (const pl of dim.getPlayers({ location: L, maxDistance: 3.6 })) {
        const vx = pl.location.x - L.x, vz = pl.location.z - L.z, l = Math.hypot(vx, vz) || 1;
        if ((vx * f.x + vz * f.z) / l < 0.2) continue;
        hit = true;
        if (side === 0) {                                                   // الخرمشة الأخيرة بالكفين: أقوى + دفع
          hurtPlayer(pl, 6, e); addBleed(pl, 1); pushAway(L, pl, 1.0, 0.35); shake(pl, 0.3, 0.25);
          clawMarks(dim, pl.location, L, 1); later(1, () => { if (valid(pl)) clawMarks(dim, pl.location, L, -1); });
          notify(pl, "§cRending Claws! You are bleeding", 30);
        } else { hurtPlayer(pl, 3, e); addBleed(pl, 1); clawMarks(dim, pl.location, L, side); }
      }
      if (!hit) { const P = { x: L.x + f.x * 2.4, y: L.y, z: L.z + f.z * 2.4 }; clawMarks(dim, P, L, side || 1, 1.9); }   // لطمة بالهوا: خطوط المخالب قدامه
    }
    if (st.t >= 42) grimEnd(e, st, 70);
    return;
  }
  // ── 3) Cub Call: زئير ونفس دخان، ويطلع جروين على جنبيه يركضون عليك ويتعلقون برجلك ──
  if (st.skill === "cubs") {
    if (tp && st.t < 10) face(tp.location);
    if (st.t === 10) {
      const f = tp ? fwdTo(L, tp.location) : { x: 0, z: 1 }, r = { x: -f.z, z: f.x };
      sfx(dim, "mob.polarbear.warning", L, 1.8, 0.55); roarPuff(dim, L, f, 8); MONSTER.bearCall(dim, L, f);
      for (const q of dim.getPlayers({ location: L, maxDistance: 18 })) { shake(q, 0.25, 0.4); notify(q, "§6The Grey Bear calls its cubs!", 40); }
      st.cubs = [];
      for (const sgn of [-1, 1]) {
        const pos = { x: L.x + r.x * sgn * 1.7, y: L.y, z: L.z + r.z * sgn * 1.7 };
        try {
          const c = dim.spawnEntity(CUB, pos);
          gst.set(c.id, { phase: 0, t: 0, cd: 0, skill: "", mom: e.id, age: 0 });
          st.cubs.push(c.id);
          MONSTER.bearCubPop(dim, pos);
        } catch (err) { /* */ }
      }
      st.cubCd = 600;
    }
    if (st.t >= 30) grimEnd(e, st, 70);
    return;
  }
  // ── 4) Deep Hibernation: ينام ويتعافى 3% كل ثانية (5 ثواني). أي ضربة تصحيه بغضب: موجة دفع وضرر وغضب 7 ثواني ──
  if (st.skill === "sleep") {
    if (st.t === 2) {
      st.hpLast = hpOf(e); sfx(dim, "mob.polarbear.idle", L, 1.2, 0.5);
      for (const q of dim.getPlayers({ location: L, maxDistance: 20 })) notify(q, "§7The Grey Bear falls into a deep sleep... §8(it heals; strike it and it wakes in a wrath)", 50);
    }
    const h = hpOf(e);
    if (st.t > 4 && h < st.hpLast - 0.01) { st.skill = "wrath"; st.t = 0; setMState(e, 5); return; }   // انضرب: يصحى بغضب
    if (st.t % 20 === 0) {
      try { const hc = e.getComponent("minecraft:health"); hc.setCurrentValue(Math.min(hc.effectiveMax, hc.currentValue + hc.effectiveMax * 0.03)); } catch (err) { /* */ }
      MONSTER.bearHeal(dim, L);
    }
    st.hpLast = hpOf(e);
    if (st.t % 40 === 0) {
      sfx(dim, "mob.polarbear.idle", L, 0.8, 0.45);                                                         // شخير
      let yaw = 0; try { yaw = (e.getRotation().y * Math.PI) / 180; } catch (err) { /* */ }
      const nx = L.x - Math.sin(yaw) * 1.5, nz = L.z + Math.cos(yaw) * 1.5;
      for (let i = 0; i < 3; i++) mcP(dim, { x: nx, y: L.y + 1.1, z: nz }, "minecraft:explosion_particle", undefined, undefined, { "velocity.x": -Math.sin(yaw) * 0.06, "velocity.y": 0.04, "velocity.z": Math.cos(yaw) * 0.06 });   // نفس من الخشم
    }
    if (st.t >= 100) { st.hibCd = 900; grimEnd(e, st, 40); }
    return;
  }
  if (st.skill === "wrath") {
    if (st.t === 2) {
      bearRage(e, st, 140);
      const f = tp ? fwdTo(L, tp.location) : { x: 0, z: 1 };
      sfx(dim, "mob.polarbear.warning", L, 2.0, 0.45); roarPuff(dim, L, f, 10);
      MONSTER.bearWrath(dim, L, f);                                                            // موجتين دخان
      for (const pl of dim.getPlayers({ location: L, maxDistance: 5 })) { hurtPlayer(pl, 6, e); pushAway(L, pl, 1.6, 0.5); shake(pl, 0.45, 0.4); notify(pl, "§cYou woke the Grey Bear: WRATH!", 35); }
    }
    if (st.t >= 20) { st.hibCd = 900; grimEnd(e, st, 50); }
  }
}
// الجرو: يركض عليك، وإذا وصلك يتعلق برجلك (بطء خفيف + ضرر 1 كل ثانية) لحد ما تضربه. يختفي بعد 45 ثانية
function cubTick(e, st) {
  const dim = e.dimension, L = e.location;
  st.age = (st.age || 0) + 2;
  if (st.age > 900) {
    for (let i = 0; i < 6; i++) mcP(dim, { x: L.x, y: L.y + 0.4, z: L.z }, "minecraft:explosion_particle", undefined, undefined, { "velocity.x": (Math.random() - 0.5) * 0.3, "velocity.y": 0.05, "velocity.z": (Math.random() - 0.5) * 0.3 });
    try { e.remove(); } catch (err) { /* */ }
    return;
  }
  if (st.cling) {
    const pl = world.getAllPlayers().find((q) => q.id === st.cling);
    if (!pl || !valid(pl) || pl.dimension.id !== dim.id) { st.cling = undefined; return; }
    const v = pl.getViewDirection(), l = Math.hypot(v.x, v.z) || 1, fx = v.x / l, fz = v.z / l;
    try { e.teleport({ x: pl.location.x - fx * 0.3 - fz * st.side * 0.35, y: pl.location.y, z: pl.location.z - fz * 0.3 + fx * st.side * 0.35 }, { facingLocation: { x: pl.location.x, y: pl.location.y + 0.5, z: pl.location.z } }); } catch (err) { /* */ }
    try { pl.addEffect("slowness", 12, { amplifier: 0, showParticles: false }); } catch (err) { /* */ }
    st.ct = (st.ct || 0) + 2;
    if (st.ct % 20 === 0) hurtPlayer(pl, 1, e);
    return;
  }
  const np = nearestPlayer(e, 1.3);
  if (np) { st.cling = np.p.id; st.side = Math.random() < 0.5 ? -1 : 1; notify(np.p, "§eA bear cub clings to your legs! §7Hit it to shake it off", 40); sfx(dim, "mob.polarbear.warning", L, 0.6, 1.8); }
}
// موت جرو: الأم تغضب (إذا قريبة)
function onCubDeath(dead) {
  const cs = gst.get(dead.id);
  if (!cs || !cs.mom) return;
  const mom = world.getEntity(cs.mom);
  if (!mom || !valid(mom)) return;
  let ms = gst.get(mom.id);
  if (!ms) { ms = { phase: 0, t: 0, cd: 20, skill: "" }; gst.set(mom.id, ms); }
  bearRage(mom, ms, 160);
  const L = mom.location;
  sfx(mom.dimension, "mob.polarbear.warning", L, 2.0, 0.5); MONSTER.bearRoar(mom.dimension, L, { x: 0, z: 1 });
  for (let i = 0; i < 6; i++) mcP(mom.dimension, { x: L.x + (Math.random() - 0.5), y: L.y + 3.4, z: L.z + (Math.random() - 0.5) }, "minecraft:villager_angry");
  for (const q of mom.dimension.getPlayers({ location: L, maxDistance: 24 })) notify(q, "§cThe Grey Bear roars: you hurt its cub! (enraged)", 50);
}
// الجلد الثخين: من قدام ينقص 30% (نرجع الصحة)، ومن ورا يزيد 20%
let bearPelting = false;
world.afterEvents.entityHurt.subscribe((ev) => {
  try {
    const e = ev.hurtEntity;
    if (bearPelting || !e || e.typeId !== BEAR) return;
    const src = ev.damageSource && ev.damageSource.damagingEntity;
    if (!src || src.typeId !== "minecraft:player") return;
    const yaw = (e.getRotation().y * Math.PI) / 180, fx = -Math.sin(yaw), fz = Math.cos(yaw);
    const dx = src.location.x - e.location.x, dz = src.location.z - e.location.z, l = Math.hypot(dx, dz) || 1, dot = (dx * fx + dz * fz) / l;
    const hc = e.getComponent("minecraft:health");
    if (dot > 0.35) {
      hc.setCurrentValue(Math.min(hc.effectiveMax, hc.currentValue + ev.damage * 0.3));
      mcP(e.dimension, { x: e.location.x + fx * 0.8, y: e.location.y + 2.0, z: e.location.z + fz * 0.8 }, "minecraft:glow_particle", FURG, rndDir(0.3));
    } else if (dot < -0.35) {
      bearPelting = true;
      try { e.applyDamage(ev.damage * 0.2); } finally { bearPelting = false; }
      for (let i = 0; i < 4; i++) mcP(e.dimension, { x: e.location.x - fx * 0.8, y: e.location.y + 1.6 + Math.random() * 0.8, z: e.location.z - fz * 0.8 }, "minecraft:glow_particle", BLOOD, rndDir(0.4));
    }
  } catch (err) { /* */ }
});
// ═════════════════════════ السرعوف المصلّي (Prayer Mantis، Cursed) ═════════════════════════
// أربع مهارات أسطورية، كل وحدة إلها شكل 3D (gen_fx_shapes.py) + جزيئات ماينكرافت الأصلية (أوراق شجر، حروف سحر، شرر):
//  1) Prayer Stance: هالة ملعونة ورا راسه ويرفع المنجلين 4 ثواني؛ أي ضربة توصله ترجع للضارب مضاعفة (منجلين X يطيرون عليه).
//  2) Leaf Camouflage: دوامة أوراق ويصير شبه شفاف (بدون اسم)، يزحف لحد ما يقرب ويطعن بالمنجلين؛ تضربه = ينكشف.
//  3) Scissor Lock: منجلين كبار ينسدون حول خصرك ويثبتونك 1.5 ثانية ثم قصة أخيرة؛ الداش يكسره.
//  4) Molt: عند نص الصحة يطلع من قشرته القديمة، القشرة تنفجر بعد ثانية ونص، والسرعوف الجديد أسرع ومهاراته أقرب.
const MANTIS = "sh:prayer_mantis";
const setCamo = (e, v) => { try { e.setProperty("sh:camo", v); if (v) e.addTag("sh_camo"); else e.removeTag("sh_camo"); } catch (err) { /* */ } };
const mantisYaw = (e) => { try { return e.getRotation().y; } catch (err) { return 0; } };
function mantisEnd(e, st, cd) {
  if (st.halo) { removeFx(st.halo); st.halo = undefined; }
  if (st.lockFx) { removeFx(st.lockFx); st.lockFx = undefined; }
  setCamo(e, 0);
  grimEnd(e, st, st.molted ? cd * 0.6 : cd);
}
function mantisTick(e, st) {
  const dim = e.dimension, L = e.location;
  const face = (loc) => { try { e.teleport(e.location, { facingLocation: { x: loc.x, y: e.location.y + 1, z: loc.z } }); } catch (err) { /* */ } };
  // الانسلاخ له الأولوية: أول ما تنزل صحته للنص (وهو مو بنص مهارة ثانية) — مرة وحدة بس
  if (!st.molted && st.phase === 0 && hpFrac(e) <= 0.5) {
    st.skill = "molt"; st.phase = 1; st.t = 0; st.molted = true; setMState(e, 5);
    return;
  }
  if (st.phase === 0) {
    st.cd -= 2;
    if (st.cd > 0) return;
    const np = nearestPlayer(e, 24);
    if (!np) { st.cd = 10; return; }
    st.target = np.p; st.t = 0; st.stage = 0; st.victim = undefined;
    const opts = [];
    if (np.d < 4.2) opts.push("lock", "stance");
    else if (np.d <= 10) opts.push("stance");
    if (np.d >= 3.5 && np.d <= 18) opts.push("camo");
    if (!opts.length) { st.cd = 10; return; }
    st.skill = pickSkill(opts, st.last); st.last = st.skill;
    setMState(e, { stance: 1, camo: 2, lock: 3 }[st.skill]);
    st.phase = 1;
    return;
  }
  const tp = st.target && valid(st.target) ? st.target : undefined;
  st.t += 2;
  // ── 1) Prayer Stance: هالة ورا الراس + المنجلين مرفوعة؛ الضربة ترجع مضاعفة (onMantisHurt) ──
  if (st.skill === "stance") {
    if (tp) face(tp.location);
    try { e.addEffect("slowness", 6, { amplifier: 6, showParticles: false }); } catch (err) { /* */ }
    // الهالة ورا راسه بالضبط (الراس قدام الجسم ~0.8 بلوكة لأن الرقبة مايلة، وعلوه ~2.5)
    const yaw = mantisYaw(e), hx = -Math.sin((yaw * Math.PI) / 180), hz = Math.cos((yaw * Math.PI) / 180);
    const haloAt = { x: L.x + hx * 0.5, y: L.y + 2.55, z: L.z + hz * 0.5 };
    if (st.t === 2) {
      st.halo = shapeFx(dim, "prayer_halo", haloAt, { r: 0.1, yaw, w: 40, life: 84 });
      if (st.halo) tween(6, 1, (k) => setShape(st.halo, "sh:r", 0.1 + 1.1 * k));
      MONSTER.mantisPray(dim, L);
      sfx(dim, "block.bell.hit", L, 1.2, 0.6);
      for (const q of dim.getPlayers({ location: L, maxDistance: 18 })) notify(q, "§dThe Prayer Mantis takes its PRAYER STANCE §7(don't hit it: every blow comes back doubled)", 50);
    }
    else if (st.halo) moveShape(st.halo, haloAt, yaw);
    if (st.t % 6 === 0) MONSTER.mantisPrayTick(dim, L);
    if (st.t >= 80) mantisEnd(e, st, 60);
    return;
  }
  if (st.skill === "counter") {
    if (st.t >= 16) mantisEnd(e, st, 60);
    return;
  }
  // ── 2) Leaf Camouflage: دوامة أوراق، شبه شفاف، يزحف ويطعن ──
  if (st.skill === "camo") {
    if (st.t === 2) {
      st.hpLast = hpOf(e);
      setCamo(e, 1);
      const sw = shapeFx(dim, "leaf_swirl", L, { r: 1.25, life: 34 });
      if (sw) later(22, () => tween(10, 1, (k) => setShape(sw, "sh:r", 1.25 * (1 - k) + 0.02)));
      MONSTER.mantisLeaves(dim, L, 22);
      sfx(dim, "dig.azalea_leaves", L, 1.4, 0.7);
      try { e.addEffect("speed", 120, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
    }
    if (st.t % 8 === 0) MONSTER.mantisCamoTick(dim, L);
    const h = hpOf(e);
    if (st.t > 4 && h < st.hpLast - 0.01) {                                  // انضرب: ينكشف
      setCamo(e, 0); MONSTER.mantisLeaves(dim, L, 14); sfx(dim, "dig.azalea_leaves", L, 1.2, 1.2);
      for (const q of dim.getPlayers({ location: L, maxDistance: 16 })) notify(q, "§aYou found the Prayer Mantis!", 30);
      try { e.removeEffect("speed"); } catch (err) { /* */ }
      mantisEnd(e, st, 50); return;
    }
    st.hpLast = h;
    if (tp && st.t > 6 && Math.hypot(tp.location.x - L.x, tp.location.z - L.z) < 2.8) { st.skill = "stab"; st.t = 0; setMState(e, 3); return; }
    if (st.t >= 130) { setCamo(e, 0); MONSTER.mantisLeaves(dim, L, 10); mantisEnd(e, st, 40); }
    return;
  }
  if (st.skill === "stab") {
    if (tp) face(tp.location);
    if (st.t === 2) {
      setCamo(e, 0);
      try { e.removeEffect("speed"); } catch (err) { /* */ }
      const f = tp ? fwdTo(L, tp.location) : { x: 0, z: 1 };
      const from = { x: L.x + f.x * 1.0, y: L.y + 1.7, z: L.z + f.z * 1.0 }, to = { x: L.x + f.x * 3.2, y: L.y + 1.3, z: L.z + f.z * 3.2 };
      popShape(dim, "scythe_thrust", { x: L.x + f.x * 2.0, y: L.y + 1.5, z: L.z + f.z * 2.0 }, 0.6, 1.3, 6, { yaw: dirYaw({ x: f.x, y: 0, z: f.z }), p: 8, ease: "out" });
      MONSTER.mantisStab(dim, from, to);
      sfx(dim, "sh.dagger_hit", L, 1.0, 0.6); sfx(dim, "dig.azalea_leaves", L, 1.0, 1.4);
      for (const pl of dim.getPlayers({ location: L, maxDistance: 3.8 })) {
        const vx = pl.location.x - L.x, vz = pl.location.z - L.z, l = Math.hypot(vx, vz) || 1;
        if ((vx * f.x + vz * f.z) / l < 0.3) continue;
        hurtPlayer(pl, 9, e); shake(pl, 0.35, 0.25);
        try { pl.addEffect("slowness", 40, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
        notify(pl, "§cThe Prayer Mantis strikes from its camouflage!", 30);
      }
    }
    if (st.t >= 14) mantisEnd(e, st, 60);
    return;
  }
  // ── 3) Scissor Lock: يمد المنجلين، يمسك اللي قدامه ويثبته 1.5 ثانية ثم قصة؛ الداش يكسره ──
  if (st.skill === "lock") {
    if (st.stage === 0) {
      if (tp) face(tp.location);
      if (st.t === 2) sfx(dim, "mob.sheep.shear", L, 1.2, 0.6);
      if (st.t >= 6) {
        const f = tp ? fwdTo(L, tp.location) : { x: 0, z: 1 };
        for (const pl of dim.getPlayers({ location: L, maxDistance: 3.9 })) {
          const vx = pl.location.x - L.x, vz = pl.location.z - L.z, l = Math.hypot(vx, vz) || 1;
          if ((vx * f.x + vz * f.z) / l < 0.4) continue;
          st.victim = pl; break;
        }
        if (!st.victim) { mantisEnd(e, st, 50); return; }                       // طاح بالهوا
        const pl = st.victim;
        st.stage = 1; st.t = 0; st.f = f; setMState(e, 4);
        st.hold = { x: L.x + f.x * 1.9, y: pl.location.y, z: L.z + f.z * 1.9 };
        st.lockFx = shapeFx(dim, "scissor_lock", st.hold, { r: 1.0, yaw: dirYaw({ x: f.x, y: 0, z: f.z }), life: 40 });
        hurtPlayer(pl, 3, e); shake(pl, 0.3, 0.2);
        MONSTER.mantisGrab(dim, st.hold); sfx(dim, "mob.sheep.shear", st.hold, 1.6, 0.5); sfx(dim, "random.anvil_land", st.hold, 0.5, 1.8);
        notify(pl, "§cSCISSOR LOCK! §7Dash to break free", 35);
      }
      return;
    }
    const pl = st.victim;
    if (!pl || !valid(pl)) { mantisEnd(e, st, 60); return; }
    const hold = st.hold;
    if (st.t > 2 && Math.hypot(pl.location.x - hold.x, pl.location.z - hold.z) > 1.1) {   // داش: انكسر القفل
      notify(pl, "§aYou broke the Scissor Lock!", 30); MONSTER.mantisBreak(dim, pl.location);
      sfx(dim, "random.anvil_land", hold, 0.6, 2.0);
      try { e.addEffect("slowness", 30, { amplifier: 3, showParticles: false }); } catch (err) { /* */ }
      mantisEnd(e, st, 60); return;
    }
    try { pl.teleport(hold, { facingLocation: { x: L.x, y: L.y + 2.0, z: L.z } }); } catch (err) { /* */ }
    if (st.t % 10 === 0) { MONSTER.mantisLockTick(dim, hold); sfx(dim, "mob.sheep.shear", hold, 0.6, 0.8 + st.t * 0.01); }
    if (st.t >= 30) {                                                         // القصة الأخيرة
      hurtPlayer(pl, 7, e); shake(pl, 0.5, 0.35);
      try { pl.addEffect("slowness", 40, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
      popShape(dim, "scythe_x", { x: hold.x, y: hold.y + 1.0, z: hold.z }, 0.4, 0.9, 5, { yaw: dirYaw({ x: st.f.x, y: 0, z: st.f.z }), ease: "out" });
      MONSTER.mantisSnip(dim, hold); sfx(dim, "mob.sheep.shear", hold, 2.0, 0.5); sfx(dim, "sh.dagger_hit", hold, 1.0, 0.5);
      try { pl.applyKnockback({ x: st.f.x * 0.8, z: st.f.z * 0.8 }, 0.3); } catch (err) { /* */ }
      mantisEnd(e, st, 70);
    }
    return;
  }
  // ── 4) Molt: يرتجف ويطلع من قشرته؛ القشرة تنفجر بعد ثانية ونص؛ بعدها أسرع ──
  if (st.skill === "molt") {
    try { e.addEffect("slowness", 6, { amplifier: 6, showParticles: false }); e.addEffect("resistance", 6, { amplifier: 2, showParticles: false }); } catch (err) { /* */ }
    if (st.t === 2) {
      sfx(dim, "mob.silverfish.step", L, 1.5, 0.5); sfx(dim, "block.bell.hit", L, 1.0, 0.45);
      for (const q of dim.getPlayers({ location: L, maxDistance: 20 })) notify(q, "§5The Prayer Mantis begins to MOLT...", 40);
    }
    if (st.t % 4 === 0 && st.t < 24) MONSTER.mantisMoltTick(dim, L);
    if (st.t === 24) {
      const yaw = mantisYaw(e), fx = -Math.sin((yaw * Math.PI) / 180), fz = Math.cos((yaw * Math.PI) / 180);
      const husk = { x: L.x, y: L.y, z: L.z };
      shapeFx(dim, "molt_husk", husk, { r: 1.0, yaw, life: 34 });
      setHot(e, 1);
      sfx(dim, "mob.silverfish.kill", L, 1.4, 0.6);
      const nx = L.x + fx * 2.2, nz = L.z + fz * 2.2;
      if (airAt(dim, nx, L.y + 0.5, nz) && airAt(dim, nx, L.y + 1.6, nz)) { try { e.teleport({ x: nx, y: groundAt(dim, nx, nz, L.y), z: nz }); } catch (err) { /* */ } }
      MONSTER.mantisLeaves(dim, husk, 12);
      for (let k = 2; k <= 28; k += 6) later(k, () => MONSTER.mantisMoltTick(dim, husk));
      later(30, () => {
        popShape(dim, "husk_burst", { x: husk.x, y: husk.y + 1.4, z: husk.z }, 0.3, 1.5, 7, { ease: "out", s: 200 });
        MONSTER.mantisHuskBoom(dim, husk);
        sfx(dim, "random.explode", husk, 1.2, 1.3);
        for (const pl of dim.getPlayers({ location: husk, maxDistance: 3.6 })) { hurtPlayer(pl, 8, e); pushAway(husk, pl, 1.3, 0.45); shake(pl, 0.5, 0.4); }
      });
    }
    if (st.t >= 40) {
      try { e.addEffect("speed", 20000000, { amplifier: 1, showParticles: false }); } catch (err) { /* */ }
      for (const q of dim.getPlayers({ location: e.location, maxDistance: 20 })) notify(q, "§dThe molted mantis is faster now!", 40);
      mantisEnd(e, st, 30);
    }
  }
}
// الرد بوضعية الصلاة: أي ضربة (لاعب أو قذيفته) ترجع للضارب مضاعفة، والسرعوف ما ياخذ ضرر
let mantisCountering = false;
world.afterEvents.entityHurt.subscribe((ev) => {
  try {
    const e = ev.hurtEntity;
    if (mantisCountering || !e || e.typeId !== MANTIS) return;
    const st = gst.get(e.id);
    if (!st || st.phase !== 1 || st.skill !== "stance" || st.t < 2) return;
    const src = ev.damageSource && ev.damageSource.damagingEntity;
    if (!src || !valid(src)) return;
    const hc = e.getComponent("minecraft:health");
    hc.setCurrentValue(Math.min(hc.effectiveMax, hc.currentValue + ev.damage));     // صد كامل
    const L = e.location, f = fwdTo(L, src.location), dim = e.dimension;
    const c = { x: L.x + f.x * 0.9, y: L.y + 1.9, z: L.z + f.z * 0.9 };
    MONSTER.mantisParry(dim, c, { x: f.x, y: 0, z: f.z });
    sfx(dim, "random.anvil_land", L, 0.8, 1.9); sfx(dim, "sh.dagger_hit", L, 1.0, 0.7);
    if (st.halo) { removeFx(st.halo); st.halo = undefined; }
    st.skill = "counter"; st.t = 0; setMState(e, 6);
    const dmg = Math.min(24, Math.max(4, ev.damage * 2));                         // مضاعف (بحد 24 حتى ما يقتل بضربة وحدة)
    const to = center3(src), d = { x: to.x - c.x, y: to.y - c.y, z: to.z - c.z }, l = Math.hypot(d.x, d.y, d.z) || 1;
    flyShape(dim, "scythe_x", c, { x: d.x / l, y: d.y / l, z: d.z / l }, 0.8, Math.min(24, l + 0.5), { r: 1.15, w: 0 }, undefined, (pos) => {
      if (!valid(src)) return;
      mantisCountering = true;
      try {
        if (src.typeId === "minecraft:player") hurtPlayer(src, dmg, e);
        else src.applyDamage(dmg, { cause: EntityDamageCause.entityAttack, damagingEntity: e });
      } catch (err) { /* */ } finally { mantisCountering = false; }
      MONSTER.mantisCounterHit(dim, center3(src), d);
      sfx(dim, "sh.dagger_hit", src.location, 1.0, 0.5);
      if (src.typeId === "minecraft:player") { shake(src, 0.45, 0.3); notify(src, `§cYour blow came back DOUBLED! §7(-${Math.round(dmg)})`, 35); }
    });
  } catch (err) { /* */ }
});
const CUSTOM_TICK = { "sh:gloomhorn": gloomTick, "sh:hollow_seer": seerTick, "sh:veilfox": veilTick, "sh:magmamoth": mammothTick, [BEAR]: bearTick, [CUB]: cubTick, [MANTIS]: mantisTick };
system.runInterval(() => {
  for (const dimId of ["overworld", "nether", "the_end"]) {
    let dim;
    try { dim = world.getDimension(dimId); } catch (e) { continue; }
    for (const type of Object.keys(CUSTOM_TICK)) {
      let list = [];
      try { list = dim.getEntities({ type }); } catch (e) { continue; }
      for (const e of list) {
        try {
          let st = gst.get(e.id);
          if (!st) { st = { phase: 0, t: 0, cd: 30 + Math.random() * 40, skill: "" }; gst.set(e.id, st); }
          CUSTOM_TICK[type](e, st);
        } catch (err) { gst.delete(e.id); }
      }
    }
  }
}, 2);

const MON_NAMES = { "sh:training_archer": "Training Archer", "sh:ember_imp": "Ember Imp", "sh:rust_guard": "Rust Guard", "sh:shadow_hound": "Shadow Hound", "sh:sand_scorpion": "Sand Scorpion", "sh:gloomhorn": "Gloomhorn", "sh:hollow_seer": "Hollow Seer", "sh:veilfox": "Veilfox", "sh:magmamoth": "Magmamoth", "sh:grey_bear": "Grey Bear", "sh:bear_cub": "Bear Cub", "sh:prayer_mantis": "Prayer Mantis" };
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
          if (e.hasTag("sh_camo")) { if (e.nameTag) e.nameTag = ""; continue; } // السرعوف المتمويه بدون اسم
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
    } else if (ev.id === "sh:cdreset_cd_only") {                       // للاختبار: يصفر الكولداون بس (المانا تبقى)
      cooldowns.clear(); weaponCd.clear();
    } else if (ev.id === "sh:clearbuffs") {                           // للاختبار: يشيل كل التقويات ويملي المانا
      BUFFS.set(p.id, {}); try { p.setDynamicProperty("sh_buffs", "{}"); } catch (e3) { /* */ }
      MANA.set(p.id, manaMax(getState(p)));
    } else if (ev.id === "sh:cdreset") {
      cooldowns.clear(); weaponCd.clear();
      try { MANA.set(p.id, manaMax(getState(p))); } catch (e2) { /* */ }
      say(p, "§aCooldowns reset");
    }
  } catch (e) { /* */ }
});

// ═════════════════════════ v1.35: مواد الوحوش، دروع الوحوش، المانا والجرعات ═════════════════════════
// المواد: كل وحش يطيح مادته (جلد، قشرة، قرن، مخلب...). تنصنع منها دروع بطاولة الصناعة أو تنطبخ جرعات عند الخيميائي.
const MAT_DROPS = {
  "sh:shadow_hound": [["sh:shadow_pelt", 0.55, 1, 2]],
  "sh:ember_imp": [["sh:ember_horn", 0.45, 1, 1]],
  "sh:sand_scorpion": [["sh:sand_carapace", 0.5, 1, 2]],
  "sh:rust_guard": [["sh:rust_core", 0.45, 1, 1]],
  "sh:gloomhorn": [["sh:gloom_antler", 0.75, 1, 2]],
  "sh:hollow_seer": [["sh:hollow_lens", 0.75, 1, 1]],
  "sh:veilfox": [["sh:spirit_fur", 0.8, 1, 3]],
  "sh:magmamoth": [["sh:magma_scale", 0.95, 2, 4]],
  "sh:grey_bear": [["sh:bear_hide", 1.0, 3, 5], ["sh:bear_claw", 0.65, 1, 2]],
  "sh:prayer_mantis": [["sh:mantis_chitin", 1.0, 3, 6], ["sh:mantis_scythe", 0.6, 1, 2]],
};
function dropMaterials(e) {
  const list = MAT_DROPS[e.typeId];
  if (!list) return;
  for (const [id, ch, lo, hi] of list) {
    if (Math.random() > ch) continue;
    const n = lo + Math.floor(Math.random() * (hi - lo + 1));
    try { e.dimension.spawnItem(new ItemStack(id, n), e.location); } catch (err) { /* */ }
  }
}
const dropNames = (id) => (MAT_DROPS[id] || []).map(([m]) => (GEAR.materials[m] || {}).name || m).join("§7, ");

// ───── دروع الوحوش: لما تلبس القطع الأربعة من نفس الطقم ينفتح بونص الطقم ─────
const SET_OF = {};
for (const [k, st] of Object.entries(GEAR.sets)) for (const id of st.pieces) SET_OF[id] = k;
const PIECE_OF = {};
for (const [k, st] of Object.entries(GEAR.sets)) st.pieces.forEach((id, i) => { PIECE_OF[id] = { set: k, slot: i }; });
const setActive = new Map(), absorbAt = new Map();
function wornSet(p) {
  try {
    const eq = p.getComponent("minecraft:equippable");
    if (!eq) return null;
    let key = null;
    for (const slot of [MC.EquipmentSlot.Head, MC.EquipmentSlot.Chest, MC.EquipmentSlot.Legs, MC.EquipmentSlot.Feet]) {
      const it = eq.getEquipment(slot);
      const k = it && SET_OF[it.typeId];
      if (!k || (key && k !== key)) return null;
      key = k;
    }
    return key;
  } catch (err) { return null; }
}
function gearEffect(p, id, amp, ticks = 80) { try { p.addEffect(id, ticks, { amplifier: amp, showParticles: false }); } catch (err) { /* */ } }
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      const k = wornSet(p), prev = setActive.get(p.id);
      if (k !== prev) {
        setActive.set(p.id, k);
        if (k) { notify(p, `§aSet bonus: ${GEAR.sets[k].name}§a! §7${GEAR.sets[k].bonus}`, 90); sfxPlayer(p, "random.levelup", 0.6, 1.6); }
      }
      if (!k) continue;
      if (k === "hunter") { if (!hasBuff(p, "swift")) gearEffect(p, "speed", 0); gearEffect(p, "jump_boost", 0); }
      else if (k === "grizzly") {
        if (!hasBuff(p, "bulwark")) gearEffect(p, "resistance", 0);
        if (system.currentTick - (absorbAt.get(p.id) ?? -9999) >= 600) { absorbAt.set(p.id, system.currentTick); gearEffect(p, "absorption", 0, 600); }
      } else if (k === "mantis") { if (!hasBuff(p, "swift")) gearEffect(p, "speed", 0); if (!hasBuff(p, "might")) gearEffect(p, "strength", 0); }
    } catch (err) { /* */ }
  }
}, 40);
// طقم السرعوف: 20% من الضربات القريبة ترجع نصها للضارب (مثل وضعية الصلاة)
let gearCountering = false;
world.afterEvents.entityHurt.subscribe((ev) => {
  try {
    const p = ev.hurtEntity;
    if (gearCountering || !p || p.typeId !== "minecraft:player" || setActive.get(p.id) !== "mantis") return;
    const src = ev.damageSource && ev.damageSource.damagingEntity;
    if (!src || src.id === p.id || !valid(src) || ev.damageSource.damagingProjectile) return;
    if (Math.random() >= 0.2) return;
    gearCountering = true;
    try { src.applyDamage(Math.max(1, ev.damage * 0.5), { cause: EntityDamageCause.entityAttack, damagingEntity: p }); } catch (err) { /* */ } finally { gearCountering = false; }
    MONSTER.mantisParry(p.dimension, { x: p.location.x, y: p.location.y + 1.2, z: p.location.z }, fwdTo(p.location, src.location));
    sfx(p.dimension, "random.anvil_land", p.location, 0.5, 2.0);
  } catch (err) { /* */ }
});

// ───── المانا: خزان يكبر مع الرتبة ويتجدد كل ثانية؛ مهارات القدرة تكلف مانا (الأسلحة لا) ─────
const MANA = new Map();
function manaMax(st) { return 100 + 20 * Math.max(0, (st && st.rank) || 0); }
function manaOf(p, st) {
  let v = MANA.get(p.id);
  if (v === undefined) {
    try { const s = p.getDynamicProperty("sh_mana"); v = typeof s === "number" ? s : manaMax(st || getState(p)); } catch (err) { v = 100; }
    MANA.set(p.id, v);
  }
  return v;
}
function spendMana(p, n) { MANA.set(p.id, Math.max(0, manaOf(p) - n)); }
function manaCost(skill) { return Math.max(8, Math.min(45, Math.round((skill.cooldown / 20) * 3) + 6)); }

// ───── الجرعات: تنشرب (مسكة الاستعمال)، وتأثيرات التقوية تبقى 6-8 دقائق ─────
const BUFF_LEN = { might: 480, bulwark: 480, focus: 360, swift: 360 };          // بالثواني
const BUFF_NAME = { might: "§6Might", bulwark: "§7Bulwark", focus: "§dFocus", swift: "§aSwiftness" };
const BUFFS = new Map();
function buffsOf(p) {
  let b = BUFFS.get(p.id);
  if (!b) {
    try { const raw = p.getDynamicProperty("sh_buffs"); b = typeof raw === "string" ? JSON.parse(raw) : {}; } catch (err) { b = {}; }
    BUFFS.set(p.id, b);
  }
  return b;
}
function hasBuff(p, k) { try { return (buffsOf(p)[k] || 0) > 0; } catch (err) { return false; } }
function mightMul(by) { return by && by.typeId === "minecraft:player" && hasBuff(by, "might") ? 1.25 : 1; }
function focusMul(p) { return hasBuff(p, "focus") ? 0.7 : 1; }
system.runInterval(() => {
  const save = system.currentTick % 100 < 20;
  for (const p of world.getAllPlayers()) {
    try {
      const b = buffsOf(p);
      for (const k of Object.keys(b)) {
        b[k] -= 1;
        if (b[k] <= 0) { delete b[k]; notify(p, `${BUFF_NAME[k] || k} §7wore off`, 40); }
      }
      const st = getState(p);
      if (st.power) {
        const max = manaMax(st), rate = (4 + 0.5 * (st.rank || 0)) * (hasBuff(p, "focus") ? 2 : 1);
        MANA.set(p.id, Math.min(max, manaOf(p, st) + rate));
      }
      if (save) {
        p.setDynamicProperty("sh_buffs", JSON.stringify(b));
        if (MANA.has(p.id)) p.setDynamicProperty("sh_mana", Math.round(MANA.get(p.id)));
      }
    } catch (err) { /* */ }
  }
}, 20);
const POTION_FX_COL = { "sh:potion_vitality": [0.9, 0.2, 0.25], "sh:potion_mana": [0.25, 0.45, 1], "sh:potion_might": [1, 0.55, 0.12], "sh:potion_bulwark": [0.6, 0.66, 0.74], "sh:potion_focus": [0.7, 0.35, 1], "sh:potion_swift": [0.35, 0.9, 0.5] };
function drinkPotion(p, id) {
  const b = buffsOf(p), dim = p.dimension, L = p.location;
  if (id === "sh:potion_vitality") {
    try { const hc = p.getComponent("minecraft:health"); hc.setCurrentValue(Math.min(hc.effectiveMax, hc.currentValue + hc.effectiveMax * 0.5)); } catch (err) { /* */ }
    gearEffect(p, "regeneration", 1, 100);
    for (let i = 0; i < 6; i++) mcP(dim, { x: L.x + (Math.random() - 0.5), y: L.y + 0.8 + Math.random() * 1.2, z: L.z + (Math.random() - 0.5) }, "minecraft:heart_particle");
    notify(p, "§cVitality! §7Half your health restored", 50);
  } else if (id === "sh:potion_mana") {
    const st = getState(p);
    MANA.set(p.id, manaMax(st));
    notify(p, st.power ? "§9Mana refilled" : "§7You have no power to use mana with", 50);
  } else {
    const k = { "sh:potion_might": "might", "sh:potion_bulwark": "bulwark", "sh:potion_focus": "focus", "sh:potion_swift": "swift" }[id];
    if (!k) return;
    b[k] = BUFF_LEN[k];
    const ticks = BUFF_LEN[k] * 20;
    if (k === "might") gearEffect(p, "strength", 0, ticks);
    if (k === "bulwark") gearEffect(p, "resistance", 0, ticks);
    if (k === "swift") { gearEffect(p, "speed", 1, ticks); gearEffect(p, "jump_boost", 0, ticks); }
    notify(p, `${BUFF_NAME[k]} §7for ${Math.round(BUFF_LEN[k] / 60)} minutes`, 60);
  }
  try { p.setDynamicProperty("sh_buffs", JSON.stringify(b)); } catch (err) { /* */ }
  const c = POTION_FX_COL[id] || [1, 1, 1];
  for (let i = 0; i < 3; i++) mcP(dim, { x: L.x, y: L.y + 1.0, z: L.z }, "minecraft:mobspell_emitter", c);
  sfxPlayer(p, "random.levelup", 0.4, 1.8);
}
world.afterEvents.itemCompleteUse.subscribe((ev) => {
  try {
    const p = ev.source, id = ev.itemStack && ev.itemStack.typeId;
    if (!p || p.typeId !== "minecraft:player" || !id || !GEAR.potions[id]) return;
    drinkPotion(p, id);
  } catch (err) { /* */ }
});
// سطر الـHUD: المانا والتقويات الشغالة
function manaHudLine(p, st, plain) {
  const parts = [];
  if (st.power) {
    const max = manaMax(st), m = Math.min(max, manaOf(p, st));
    parts.push(plain ? `§9✦ Mana ${bar(m / max, 6, "§9", "§8", true)} §b${Math.floor(m)}§7/${max}` : `§f${GL(GI.mana)} ${gbar(m / max, 6, GI.mana_full, GI.mana_empty)} §b${Math.floor(m)}§7/${max}`);
  }
  const b = buffsOf(p);
  for (const k of Object.keys(b)) {
    const left = b[k], mm = Math.floor(left / 60), ss = String(left % 60).padStart(2, "0");
    parts.push(plain ? `${BUFF_NAME[k]} §f${mm}:${ss}` : `§f${GL(GI["buff_" + k])} §f${mm}:${ss}`);
  }
  return parts.join("  ");
}
// معلومات الأيتم بالإيد (مواد، جرعات، دروع)
function gearHeld(id, showTip) {
  const m = GEAR.materials[id];
  if (m) return { line: `${m.name} §8│ §7Monster material (${m.mob})`, tip: showTip ? "§7Craft monster armor at a crafting table, or brew potions with the Alchemist (Sakura Village)" : "" };
  const po = GEAR.potions[id];
  if (po) return { line: `${po.name}`, tip: showTip ? `§7${po.desc} §8(hold use to drink)` : "" };
  const pc = PIECE_OF[id];
  if (pc) { const s = GEAR.sets[pc.set]; return { line: `${s.name} armor §8│ §7piece ${pc.slot + 1}/4`, tip: showTip ? `§7${s.bonus}` : "" }; }
  return null;
}

// ───── الخيميائي (قرية الساكورا): يطبخ الجرعات من مواد الوحوش ─────
const ALCHEMY = [
  ["sh:potion_vitality", [["sh:shadow_pelt", 3], ["sh:spirit_fur", 1]]],
  ["sh:potion_mana", [["sh:hollow_lens", 2], ["sh:ember_horn", 2]]],
  ["sh:potion_might", [["sh:magma_scale", 2], ["sh:ember_horn", 2]]],
  ["sh:potion_bulwark", [["sh:rust_core", 2], ["sh:bear_hide", 1]]],
  ["sh:potion_focus", [["sh:gloom_antler", 2], ["sh:hollow_lens", 1]]],
  ["sh:potion_swift", [["sh:spirit_fur", 2], ["sh:sand_carapace", 2]]],
];
function countItem(p, typeId) {
  let n = 0;
  try { const c = inv(p); for (let i = 0; i < c.size; i++) { const it = c.getItem(i); if (it && it.typeId === typeId) n += it.amount; } } catch (err) { /* */ }
  return n;
}
function takeItems(p, typeId, n) {
  const c = inv(p);
  for (let i = 0; i < c.size && n > 0; i++) {
    const it = c.getItem(i);
    if (!it || it.typeId !== typeId) continue;
    const k = Math.min(n, it.amount);
    n -= k;
    if (it.amount > k) { it.amount -= k; c.setItem(i, it); } else c.setItem(i, undefined);
  }
}
const matName = (id) => ((GEAR.materials[id] || {}).name || id).replace(/§./g, "");
async function openAlchemist(p, npc) {
  const f = new ActionFormData().title("Alchemist").body("§7\"Bring me what the monsters leave behind, and I will brew you something worth drinking.\"\n\n§fChoose a potion:");
  const ok = ALCHEMY.map(([, cost]) => cost.every(([id, n]) => countItem(p, id) >= n));
  ALCHEMY.forEach(([pid, cost], i) => {
    const need = cost.map(([id, n]) => `${countItem(p, id) >= n ? "§2" : "§c"}${n} ${matName(id)}`).join("§8 + ");
    f.button(`${ok[i] ? "" : "§8"}${GEAR.potions[pid].name.replace(/§./g, ok[i] ? "" : "")}\n${need}`);
  });
  f.button("§7Leave");
  const r = await showForm(p, f);
  if (r.canceled || r.selection === undefined || r.selection >= ALCHEMY.length) return;
  const [pid, cost] = ALCHEMY[r.selection];
  if (!cost.every(([id, n]) => countItem(p, id) >= n)) { notify(p, "§cYou don't have the materials for that potion", 50); sfxPlayer(p, "note.bass", 0.6, 0.7); return; }
  for (const [id, n] of cost) takeItems(p, id, n);
  giveItem(p, pid, 1);
  const L = npc && valid(npc) ? npc.location : p.location;
  for (let i = 0; i < 3; i++) mcP(p.dimension, { x: L.x, y: L.y + 1.6, z: L.z }, "minecraft:mobspell_emitter", POTION_FX_COL[pid] || [1, 1, 1]);
  sfx(p.dimension, "random.potion.brewed", L, 1.0, 1.0);
  sfx(p.dimension, "bottle.fill", L, 0.8, 1.1);
  notify(p, `§aBrewed: ${GEAR.potions[pid].name}`, 60);
}
const alchemistTalk = new Map();
world.afterEvents.playerInteractWithEntity.subscribe((ev) => {
  try {
    if (!ev.target || ev.target.typeId !== "sh:alchemist") return;
    const p = ev.player, last = alchemistTalk.get(p.id) ?? -100;
    if (system.currentTick - last < 10) return;
    alchemistTalk.set(p.id, system.currentTick);
    openAlchemist(p, ev.target);
  } catch (err) { /* */ }
});

