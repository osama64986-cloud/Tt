import { world, system, ItemStack, MolangVariableMap, EntityDamageCause } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import {
  RANKS, LEVELS_PER_RANK, HARD_RANK_FROM, RARITIES, unlockLevel, powerXpNeeded, addPowerXp, xpNeeded, defaultState, addXp, monsterReward, isSkillUnlocked, addSkillXp, skillXpNeeded, skillLevel, SKILL_UNLOCK_LEVEL,
} from "./logic.js";
import { setupStructures } from "./structures.js";

// ───────────────────────── البيانات ─────────────────────────
const TRAIN_NEED = 3;

const POWERS = {
  accountant: {
    name: "المحاسب", color: "§6",
    desc: "كل عدو عنده رقم فوق راسه، وانت تتلاعب بالأرقام. إذا وصل الرقم صفر ينهار.",
  },
  law: {
    name: "كاتب القوانين", color: "§5",
    desc: "تكتب قانون على منطقة حواليك، وكل من يدخلها يخضع له.",
  },
  distance: {
    name: "محرف المسافة", color: "§b",
    desc: "تتلاعب بالمسافة بينك وبين أي شي: تقرب وتبعد وتبدل وتطوي المكان.",
  },
  echo: {
    name: "ناسج الصدى", color: "§3",
    desc: "كل فعل تسويه يترك صدى يرجع بعد لحظة ويضرب مرة ثانية.",
  },
  iron: {
    name: "جسد الحديد", color: "§7",
    desc: "تقسي جسمك كالحديد وتضرب بقبضة ثقيلة.",
  },
  crystal: {
    name: "سيد البلورات", color: "§d",
    desc: "تنبت بلورات حادة: ترميها، تتدرع بيها، تسجن بيها العدو، وتفجرها.",
  },
  borrower: {
    name: "مستعير الصفات", color: "§e",
    desc: "تستعير صفة من الطبيعة (صخر، أنياب، ريح، عين صياد) وتدمج صفتين مع بعض.",
  },
  wind: {
    name: "متتبع الريح", color: "§a",
    desc: "سرعة وقفزات وعواصف، تتحرك أسرع من أي عدو.",
  },
  star: {
    name: "سيد النجوم", color: "§9",
    desc: "تستدعي النجوم: نيازك وجاذبية ومدارات وكوكبات وثقوب سوداء، لحد المستعر الأعظم اللي يقلب المعركة.",
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
  mk("seal", "accountant", "ختم الرقم", "sh:skill_seal", 0, 10, "تعلم عدو برقم 10. الرقم ينقص لحاله كل ثانيتين وكل ضربة تنقصه، وعند الصفر ينهار ويتضرر."),
  mk("subtract", "accountant", "طرح", "sh:skill_subtract", 1, 60, "تنقص 3 من رقم العدو (إذا ما معلم، تعلمه برقم 7)."),
  mk("transfer", "accountant", "نقل", "sh:skill_transfer", 2, 200, "تنقل رقم عدو لأقرب عدو ثاني."),
  mk("ironskin", "iron", "جلد الحديد", "sh:skill_ironskin", 0, 300, "جسمك يتقسى: مقاومة عالية 6 ثواني."),
  mk("ironfist", "iron", "لكمة الحديد", "sh:skill_ironfist", 1, 100, "لكمة ثقيلة للعدو اللي قدامك: ضرر عالي ودفع."),
  mk("windrun", "wind", "ركضة الريح", "sh:skill_windrun", 0, 200, "سرعة عالية 5 ثواني مع أثر ريح."),
  mk("windleap", "wind", "قفزة الريح", "sh:skill_windleap", 1, 140, "تقفز للأمام بقوة وتنزل بخفة."),
  mk("gale", "wind", "العاصفة", "sh:skill_gale", 2, 360, "عاصفة تدفع كل الأعداء القريبين وتأذيهم."),
  mk("divide", "accountant", "قسمة", "sh:skill_divide", 3, 240, "تقسم رقم العدو نصين: نص له ونص لأقرب عدو ثاني (إذا ما معلم، تبدأ من 10)."),
  mk("zero", "accountant", "الصفر", "sh:skill_zero", 3, 900, "إذا رقم العدو 5 أو أقل ينهار فورا، وإلا تنقص منه 5."),

  mk("weight", "law", "قانون الثقل", "sh:skill_weight", 0, 16, "دائرة تبطئ الأعداء جدا وتمنعهم من القفز وتأذيهم نقطة كل ثانية."),
  mk("silence", "law", "قانون الصمت", "sh:skill_silence", 1, 120, "الرماة داخل الدائرة ما يقدرون يرمون وكل الأعداء ضربهم يضعف."),
  mk("reflect", "law", "قانون الانعكاس", "sh:skill_reflect", 2, 300, "أي ضربة تنضربها داخل الدائرة ترجع على اللي ضربك."),
  mk("boundary", "law", "قانون الحدود", "sh:skill_boundary", 3, 600, "الأعداء داخل الدائرة ما يقدرون يطلعون منها."),
  mk("time", "law", "قانون الزمن", "sh:skill_time", 4, 700, "الأعداء حواليك يتجمدون 3 ثواني."),
  mk("absolute", "law", "القانون المطلق", "sh:skill_absolute", 5, 1500, "تختار قانون يمشي 5 ثواني."),

  mk("pull", "distance", "تقريب", "sh:skill_pull", 0, 12, "العدو يقرب لعندك فجأة بدون ما يمشي."),
  mk("push", "distance", "تبعيد", "sh:skill_push", 1, 60, "تنطرد العدو بعيد بدون ما تلمسه."),
  mk("swap", "distance", "تبديل", "sh:skill_swap", 2, 160, "تبدل مكانك مع العدو."),
  mk("fold", "distance", "طي", "sh:skill_fold", 3, 420, "تطوي المسافة وتضرب العدو كأنه جنبك."),
  mk("spacecollapse", "distance", "الانهيار", "sh:skill_spacecollapse", 4, 1200, "كل الأعداء القريبين يتجمعون بنقطة وحدة."),

  mk("echostrike", "echo", "صدى الضربة", "sh:skill_echostrike", 0, 14, "ضربتك الجاية تنعاد بعد ثانية."),
  mk("echoseal", "echo", "ختم الصدى", "sh:skill_echoseal", 1, 100, "تعلم عدو وكل ضرر ياخذه ينعاد عليه وينفجر."),
  mk("echowave", "echo", "موجة الصدى", "sh:skill_echowave", 2, 480, "موجة قدامك وبعدها صدى ثاني يضرب مرة ثانية."),
  mk("chorus", "echo", "جوقة الصدى", "sh:skill_chorus", 3, 1000, "ثلاث موجات صدى تتوسع حواليك وكل وحدة أقوى من اللي قبلها."),
  mk("spacerewind", "distance", "الارتداد المكاني", "sh:skill_spacerewind", 5, 20, "أول استعمال: يحفظ مكانك 15 ثانية. ثاني استعمال: ترجع لنفس المكان وتسترد جزء من صحتك."),

  mk("shards", "crystal", "شظايا البلور", "sh:skill_shards", 0, 30, "ثلاث شظايا بنظرك. وانت جالس (شفت): رمح بلور واحد قوي يخترق كل اللي بطريقه. الشظايا تترك بلورات بالأعداء."),
  mk("crystalshield", "crystal", "درع البلور", "sh:skill_crystalshield", 1, 400, "بلورات تدور حولك وتعطيك درع امتصاص 10 ثواني."),
  mk("prison", "crystal", "سجن البلور", "sh:skill_prison", 2, 700, "تسجن عدو ببلورات: يتجمد مكانه ويضعف (البوسات مدة أقصر)."),
  mk("burst", "crystal", "انفجار البلور", "sh:skill_burst", 3, 500, "تفجر كل البلورات اللي بالأعداء. كل بلورة ضرر وانفجار صغير يضرب اللي حواليه."),

  mk("rockskin", "borrower", "صفة الصخر", "sh:skill_rockskin", 0, 260, "تستعير جلد الصخر: مقاومة عالية وبطء خفيف."),
  mk("fangs", "borrower", "صفة الأنياب", "sh:skill_fangs", 1, 300, "8 ثواني ضرباتك تسمم العدو وتسترد لك جزء من صحتك."),
  mk("windwings", "borrower", "صفة الأجنحة", "sh:skill_windwings", 2, 360, "قفزة عالية وسقوط بطيء وسرعة 10 ثواني."),
  mk("huntereye", "borrower", "صفة عين الصياد", "sh:skill_huntereye", 3, 480, "رؤية بالليل وتعلم كل الأعداء القريبين، وضرباتك عليهم أقوى."),
  mk("adapt", "borrower", "التكيف", "sh:skill_adapt", 4, 900, "تدمج آخر صفتين استعملتهم (خلال 40 ثانية) وتشتغلان مع بعض بمدة أقصر."),
  mk("meteor", "star", "نيزك", "sh:skill_meteor", 0, 80, "تنزل نيزك على المكان اللي تصوب عليه بعد ثانية، ضرر وحرق بمنطقة."),
  mk("gravwell", "star", "بئر الجاذبية", "sh:skill_gravwell", 1, 300, "بئر يسحب الأعداء لنقطة 4 ثواني ويبطئهم ويأذيهم."),
  mk("orbit", "star", "مدار النجوم", "sh:skill_orbit", 2, 500, "3 نجوم تدور حولك 10 ثواني وتضرب كل من يلمسها وتقللك الضرر."),
  mk("constellation", "star", "كوكبة", "sh:skill_constellation", 3, 700, "تربط الأعداء القريبين بخطوط نجمية وبعد ثانيتين تصعقهم كلهم."),
  mk("stardash", "star", "ومضة نجمية", "sh:skill_stardash", 4, 160, "اندفاع نجمي للأمام يضرب ويبطئ كل من بالطريق."),
  mk("blackhole", "star", "ثقب أسود", "sh:skill_blackhole", 5, 1100, "ثقب أسود يسحب كل شي 6 ثواني ثم ينهار وينفجر بقوة."),
  mk("supernova", "star", "المستعر الأعظم", "sh:skill_supernova", 6, 1800, "تشحن ثانيتين ثم انفجار نجمي هائل يضرب ويعمي كل الأعداء بمدى 14 بلوكة، وتضعف بعده."),
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
  seal: "صوّب على عدو واضغط استعمال: يتعلم برقم 10 وينقص لحاله، وكل ضربة تنقصه",
  subtract: "صوّب على عدو واضغط استعمال: تنقص 3 من رقمه",
  transfer: "صوّب على عدو معلّم: ينتقل رقمه لأقرب عدو",
  divide: "صوّب على عدو معلّم: رقمه ينقسم بينه وبين أقرب عدو",
  zero: "صوّب على عدو: إذا رقمه 5 أو أقل ينهار فورا",
  shards: "استعمال: 3 شظايا. جلوس (سنيك) + استعمال: رمح بلور واحد قوي يخترق",
  crystalshield: "استعمال: بلورات تدور حولك وتمتص الضرر",
  prison: "صوّب على عدو: تسجنه ببلورات (يتجمد مكانه)",
  burst: "استعمل شظايا البلور على الأعداء أول، ثم استعمل: تفجر كل البلورات",
  spacerewind: "أول استعمال: يحفظ مكانك. ثاني استعمال: ترجع لنفس المكان",
  spacecollapse: "استعمال: كل الأعداء القريبين يتجمعون بنقطة وحدة",
  absolute: "استعمال: تفتح قائمة، اختر القانون اللي يمشي 5 ثواني",
  adapt: "استعمل صفتين مختلفتين بالتتابع، بعدها استعمل التكيف لدمجهما",
  weight: "استعمال: دائرة حولك تبطئ الأعداء وتأذيهم",
  silence: "استعمال: دائرة تمنع الرماة من الرمي وتضعف ضرب الأعداء",
  reflect: "استعمال: دائرة ترجع أي ضربة على اللي ضربك",
  boundary: "استعمال: دائرة ما أحد يطلع منها",
  time: "استعمال: كل الأعداء حواليك يتجمدون 3 ثواني",
  meteor: "صوّب على المكان واضغط استعمال: دائرة تحذير ثم ينزل نيزك بعد ثانية",
  gravwell: "صوّب على مكان: بئر يسحب الأعداء 4 ثواني ويبطئهم",
  orbit: "استعمال: 3 نجوم تدور حولك 10 ثواني وتضرب كل من يلمسها",
  constellation: "استعمال قرب أعداء (2 أو أكثر): تربطهم بخطوط نجمية ثم تصعقهم كلهم بعد ثانيتين",
  stardash: "استعمال: اندفاع للأمام يضرب كل من بالطريق",
  blackhole: "صوّب على مكان: ثقب أسود يسحب كل شي 6 ثواني ثم ينفجر",
  supernova: "استعمال: اثبت ثانيتين ثم انفجار نجمي هائل (تضعف بعده 6 ثواني)",
};
function usageOf(s) {
  if (SKILL_USAGE[s.id]) return SKILL_USAGE[s.id];
  return AIMED.has(s.id) ? "صوّب على عدو واضغط استعمال" : "اضغط استعمال (تشتغل حواليك)";
}


// وحوش: rank -1 = وحش تدريب (بلا رتبة)
const MONSTERS = {
  "sh:training_archer": { rank: -1, xp: [20, 50], training: true },
  // وحوش الرتبة الأولى (index 0 = مبتدئ)
  "sh:ember_imp": { rank: 0, xp: 12 },
  "sh:rust_guard": { rank: 0, xp: 20 },
  "sh:shadow_hound": { rank: 0, xp: 16 },
  "sh:sand_scorpion": { rank: 0, xp: 24 },
};
const RANK0_TYPES = ["sh:ember_imp", "sh:rust_guard", "sh:shadow_hound", "sh:sand_scorpion"];

// أسلحة الدفاع: ضرر إضافي فوق ضرر اليد، تشتغل حتى بدون قدرة
const WEAPONS = {
  // خفيف: ضرر واطي، بس بيده تقييد وضربة الفجر
  "sh:dawn_dagger": { extra: 3, sound: "sh.dagger_hit", color: "gold", knock: 0.0, name: "خنجر الفجر", special: "combo", active: "bind", cd: 140,
    desc: "ضربة ثالثة متتالية = ضربة الفجر (ضرر مضاعف). استعماله: يقيد أقرب عدو بنظرك ويبطئه. ضعفه: ضرره واطي." },
  // ثقيل: يضرب أكثر من عدو بكل ضربة وضرره عالي، بس يبطئك
  "sh:ember_cleaver": { extra: 9, sound: "sh.cleaver_hit", color: "orange", knock: 1.2, name: "ساطور الجمر", cleave: 4, active: "slam", cd: 160, heavy: 1,
    desc: "كل ضربة تشق أكثر من عدو. استعماله: قوس نار قدامك. ضعفه: يبطئك وانت حامله." },
  // سريع: ضربتين بالحركة، بس كل ضربة ضعيفة
  "sh:shadow_blade": { extra: 2, sound: "sh.dagger_hit", color: "purple", knock: 0.0, name: "سيف الظل", fast: true, active: "dash", cd: 100,
    desc: "كل ضربة تنعاد بسرعة (ضربة ثانية بعدها). استعماله: اندفاع للأمام. ضعفه: ضرر الضربة الواحدة واطي وما يدفع." },
  // كاتانا ظلامية: سيف نحيف بعدة مهارات (شفت + استعمال يبدل المهارة)
  "sh:dark_katana": { extra: 4, sound: "sh.dagger_hit", color: "purple", knock: 0.0, name: "كاتانا الهاوية",
    desc: "ثلاث مهارات: الشطر، الضربة المزدوجة (علامة X)، الاختراق. استعمل وانت جالس (شفت) حتى تبدل المهارة، واستعمل عادي حتى تنفذها." },
  // مخالب: ضربة تمزيق تنزف (سم قصير)، استعمالها قفزة خلف العدو
  "sh:shadow_claws": { extra: 3, sound: "sh.dagger_hit", color: "purple", knock: 0.0, name: "مخالب الظل", special: "rend", active: "dash", cd: 120,
    desc: "كل ضربة تمزق العدو وتنزفه (سم قصير). استعماله: اندفاع للأمام. ضعفه: ضرر الضربة الواحدة واطي وقصيرة المدى." },
  // ثقيل جدا: تضرب الأرض وتدمر اللي حواليها
  "sh:stone_maul": { extra: 11, sound: "sh.cleaver_hit", color: "green", knock: 2.0, name: "مطرقة الصخر", shock: true, active: "quake", cd: 200, heavy: 2,
    desc: "كل ضربة ترج الأرض وتضرب اللي حول العدو. استعماله: رجة كبيرة. ضعفه: تبطئك كثير." },
  // مرمى: ترميه ويرجع لك
  "sh:sunset_spear": { extra: 5, sound: "sh.dagger_hit", color: "red", knock: 0.4, name: "رمح الغروب", active: "throw", cd: 100,
    desc: "استعماله: ترميه ويضرب بالذهاب والرجعة ويرجع لك، تقدر تستعمله بلا حدود. ضعفه: ضرره بالضرب القريب متوسط." },
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
function hudText(p, st, plain) {
  const pw = POWERS[st.power];
  let l1;
  if (pw) {
    const r = rarityOf(st.power);
    l1 = `§6◆ ${RANKS[st.rank]} §8│ ${pw.color}${pw.name} §8│ ${rarityStars(st.power)} §8│ §dLv ${st.plevel || 1}/${r.maxLv}`;
  } else l1 = `§6◆ ${RANKS[st.rank]} §8│ §7بلا قدرة`;
  let hp = "";
  try {
    const h = p.getComponent("minecraft:health");
    hp = `§c♥ ${bar(h.currentValue / h.effectiveMax, 8, "§c", "§8", plain)} §f${Math.ceil(h.currentValue)}`;
  } catch (e) { /* */ }
  const need = xpNeeded(st.level);
  const xp = `§bLv ${st.level} ${bar(st.xp / need, 8, "§b", "§8", plain)} §7${Math.floor((st.xp / need) * 100)}%`;
  return `${l1}\n${hp} §8│ ${xp}`;
}

// شريط المهارات + نغمة خفيفة لما تخلص مهارة طويلة الكولداون
const wasCooling = new Map();
function skillStrip(p, st, heldId) {
  if (!st.power) return "";
  const now = system.currentTick;
  const mine = Object.values(SKILLS).filter((s) => s.power === st.power);
  const parts = mine.map((s, i) => {
    const n = i + 1;
    let txt;
    if (!isSkillUnlocked(st, s)) txt = `§8${n}✖`;
    else {
      const key = `${p.id}:${s.id}`;
      const left = (cooldowns.get(key) ?? 0) - now;
      const cooling = left > 0;
      if (wasCooling.get(key) && !cooling && s.cooldown >= 100) {
        sfxPlayer(p, "sh.ready", 0.5);
        const m = tempMsg.get(p.id);
        if (!m || m.until <= now) notify(p, `§a✔ ${s.name} جاهزة`, 25);
      }
      wasCooling.set(key, cooling);
      txt = cooling ? `§c${n}·${fmtSec(left)}` : `§a${n}✔`;
    }
    return heldId === s.id ? `§e[${txt}§e]` : txt;
  });
  return `§8مهارات: ${parts.join(" ")}`;
}

// معلومات الأيتم اللي بإيدك + تلميح طريقة الاستعمال
const heldSeen = new Map();
const WEAPON_USE = { bind: "يقيد أقرب عدو بنظرك", slam: "قوس نار قدامك", dash: "اندفاع للأمام", quake: "رجة أرض كبيرة", throw: "ترمي الرمح ويرجع لك" };
function heldLine(p, st, plain) {
  const now = system.currentTick;
  const held = inv(p).getItem(p.selectedSlotIndex);
  const id = held ? held.typeId : "";
  const seen = heldSeen.get(p.id);
  if (!seen || seen.id !== id) heldSeen.set(p.id, { id, tick: now });
  const showTip = now - heldSeen.get(p.id).tick < 120;
  const none = { line: "", tip: "" };
  if (!id) return none;
  const stateOf = (left) => (left > 0 ? `§c⏳ ${fmtSec(left)}ث` : "§a✔ جاهزة");

  const sk = ITEM_TO_SKILL[id];
  if (sk) {
    if (st.power !== sk.power) return { line: `§c${sk.name}: مو من قدرتك`, tip: "" };
    const lv = skillLevel(st, sk.id);
    const x = (st.skills && st.skills[sk.id] && st.skills[sk.id].xp) || 0;
    const left = (cooldowns.get(`${p.id}:${sk.id}`) ?? 0) - now;
    return {
      skillId: sk.id,
      line: `${POWERS[sk.power].color}${sk.name} §8│ §bمستوى ${lv} ${bar(x / skillXpNeeded(lv), 5, "§b", "§8", plain)} §8│ ${stateOf(left)}`,
      tip: showTip ? `§7${usageOf(sk)}` : "",
    };
  }
  if (id === KATANA) {
    const kat = getKat(p), mode = katanaMode(p), m = KATANA_MODES[mode];
    const left = (weaponCd.get(`${p.id}:katana${mode}`) ?? 0) - now;
    const open = KATANA_MODES.filter((x) => x.lv <= kat.lv).length;
    const prog = kat.lv >= KAT_MAX ? "§6أقصى" : bar(kat.xp / KAT_NEED[kat.lv], 4, "§5", "§8", plain);
    return {
      line: `§5⚔ كاتانا §8Lv${kat.lv} ${prog} §8│ §d${m.name} §7(${mode + 1}/${open}) §8│ ${stateOf(left)}`,
      tip: showTip ? "§7سنيك (جلوس): تبديل المهارة §8│ §7استعمال: تنفيذ" : "",
    };
  }
  if (id === "sh:explorer_compass") {
    const key = compassKey(p), tg = compassFind(p, key);
    const nm = (COMPASS_TARGETS.find((t) => t.key === key) || COMPASS_TARGETS[5]).name;
    const line = tg
      ? `§6◎ ${tg.name} §8│ §f${Math.round(Math.hypot(tg.x - p.location.x, tg.z - p.location.z))}م §e${compassArrow(p, tg)}`
      : `§6◎ ${nm} §8│ §7ما انكشفت بعد، استكشف أكثر`;
    return { line, tip: showTip ? "§7استعمال: اختيار الوجهة §8│ §7سنيك+استعمال: خط إرشاد" : "" };
  }
  if (id === "sh:evolution_book") return { line: "§eكتاب التطور", tip: showTip ? "§7استعمال: المهارات، نافذة الحالة، الرتب" : "" };
  if (id === "sh:monster_book") return { line: "§5كتاب الوحوش", tip: showTip ? "§7استعمال: معلومات الوحوش اللي قتلتها" : "" };
  const w = WEAPONS[id];
  if (w && w.active) {
    const left = (weaponCd.get(`${p.id}:${id}`) ?? 0) - now;
    return { line: `§f⚔ ${w.name} §8│ ${stateOf(left)}`, tip: showTip ? `§7استعمال: ${WEAPON_USE[w.active] || "مهارة السلاح"}` : "" };
  }
  return none;
}

system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      if (p.hasTag("sh_hud_off")) continue;
      const plain = p.hasTag("sh_hud_plain");
      const st = getState(p);
      const h = heldLine(p, st, plain);
      let text = hudText(p, st, plain);
      const strip = skillStrip(p, st, h.skillId);
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
}, 5);

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

function glow(dim, loc, o = {}) {
  try {
    const c = o.color || COLORS.gold;
    const m = new MolangVariableMap();
    m.setFloat("variable.r", c[0]);
    m.setFloat("variable.g", c[1]);
    m.setFloat("variable.b", c[2]);
    m.setFloat("variable.size", o.size ?? 0.18);
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
function pix(dim, loc, o = {}) {
  try {
    const c = o.color || COLORS.gold;
    const m = new MolangVariableMap();
    m.setFloat("variable.r", c[0]);
    m.setFloat("variable.g", c[1]);
    m.setFloat("variable.b", c[2]);
    m.setFloat("variable.size", o.size ?? 0.14);
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
function giveItem(p, typeId) {
  const left = inv(p).addItem(new ItemStack(typeId, 1));
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
const NO_POWER_CHANCE = 0.3;

function grantPower(player, key) {
  const pw = POWERS[key];
  const st = getState(player);
  st.power = key;
  saveState(player, st);
  sfxPlayer(player, "sh.select");
  burst(player.dimension, headPos(player), 24, POWER_COLOR[key], 3);
  notify(player, `${pw.color}صارت قدرتك: ${pw.name}`, 80);
  const rar = rarityOf(key);
  say(player, `§e[القدرة] §fطلعت لك ${pw.color}${pw.name}§f بندرة ${rar.color}${rar.name}§f (${rar.skills} مهارات، أعلى ليفل ${rar.maxLv}). ${pw.desc}`);
  say(player, "§e[القدرة] §fدور على المدرب حتى يعلمك الأساسيات.");
  const t = ensureTrainerNear(player, true);
  if (t) say(player, `§e[المدرب] §f${describeDir(player, t)}`);
}

function rollPower(player) {
  const st = getState(player);
  if (st.power) return;
  if (st.rolledRank === st.rank) {
    say(player, "§7[القدرة] §fما عندك قدرة. تعيد المحاولة لما ترتقي رتبة جديدة. هسه تطور بالأسلحة.");
    return;
  }
  st.rolledRank = st.rank;
  saveState(player, st);
  sfxPlayer(player, "sh.select", 0.8, 0.8);
  if (Math.random() < NO_POWER_CHANCE) {
    notify(player, "§7ما طلعت لك قدرة", 80);
    say(player, "§7[القدرة] §fما طلعت لك قدرة هالمرة. الأسلحة اللي بإيدك تساعدك تهزم الوحوش وتتطور، وتعيد المحاولة لما ترتقي رتبة.");
    return;
  }
  let total = 0;
  for (const k of POWER_KEYS) total += rarityOf(k).weight;
  let roll = Math.random() * total, pick = POWER_KEYS[0];
  for (const k of POWER_KEYS) { roll -= rarityOf(k).weight; if (roll <= 0) { pick = k; break; } }
  grantPower(player, pick);
}

async function openPowerMenu(player) {
  const st0 = getState(player);
  if (st0.power) return openBook(player);
  if (RANDOM_POWERS && !player.hasTag("sh_menu")) return rollPower(player);

  const form = new ActionFormData()
    .title("اختر قدرتك")
    .body(
      POWER_KEYS.map((k) => `${POWERS[k].color}${POWERS[k].name}§r\n${POWERS[k].desc}`).join("\n\n") +
      "\n\n§7الاختيار نهائي: باقي القدرات تختفي."
    );
  for (const k of POWER_KEYS) form.button(`${POWERS[k].color}${POWERS[k].name}`);
  const r = await showForm(player, form);
  if (r.canceled) { notify(player, "§7افتح كتاب التطور حتى تختار قدرتك، أو تطور بدونها", 100); return; }
  const key = POWER_KEYS[r.selection];
  const pw = POWERS[key];

  const conf = new ActionFormData()
    .title("تأكيد")
    .body(`تثبت قدرة ${pw.color}${pw.name}§r؟\n\n${pw.desc}`)
    .button("§aتثبيت")
    .button("§cرجوع");
  const c = await showForm(player, conf);
  if (c.canceled || c.selection !== 0) return openPowerMenu(player);

  const st = getState(player);
  if (st.power) return;
  st.power = key;
  saveState(player, st);
  sfxPlayer(player, "sh.select");
  burst(player.dimension, headPos(player), 24, POWER_COLOR[key], 3);
  notify(player, `${pw.color}صارت قدرتك: ${pw.name}`, 80);
  say(player, `§e[القدرة] §fاخترت ${pw.color}${pw.name}§f. دور على المدرب حتى يعلمك الأساسيات.`);
  const t = ensureTrainerNear(player, true);
  if (t) say(player, `§e[المدرب] §f${describeDir(player, t)}`);
}

function nextRankLine(st) {
  if (st.rank >= RANKS.length - 1) return "§6وصلت لأعلى رتبة";
  const need = (st.rank + 1) * LEVELS_PER_RANK;
  return `§7الرتبة الجاية: §e${RANKS[st.rank + 1]}§7 عند ليفل §b${need}§7 (باقي ${Math.max(0, need - st.level)})`;
}

async function showRanks(player) {
  const st = getState(player);
  let body = "§eالرتب وطريقة الترقي§r\n\n";
  RANKS.forEach((n, i) => {
    const mark = i === st.rank ? "§a◀ انت هنا" : "";
    body += `${i === st.rank ? "§a" : "§f"}${i + 1}. ${n}§7 (من ليفل ${i * LEVELS_PER_RANK}) ${mark}\n`;
  });
  body += `\n§bالترقية العادية:§f كل ${LEVELS_PER_RANK} ليفل ترتقي رتبة.\n`;
  body += `§bالقفزة:§f إذا قتلت وحش رتبته أعلى منك بدرجتين أو أكثر ترتقي فورا (للرتب الأولى لحد ${RANKS[HARD_RANK_FROM]}).\n`;
  body += `§bبعدها:§f قتل وحش أقوى منك يعطيك خبرة مضاعفة 3 مرات بس ما يرقيك.\n`;
  body += "§bالضعيف:§f وحش أضعف منك بثلاث رتب يعطي ربع الخبرة.\n\n";
  body += "§7الخبرة تجي من: قتل الوحوش، لفائف الخبرة، وبعضها بصناديق البنايات.";
  await showForm(player, new ActionFormData().title("الرتب").body(body).button("§aتمام"));
}

// ───────────────────────── كتاب الوحوش ─────────────────────────
const MONSTER_INFO = [
  ["sh:training_archer", "رامي التدريب", "بلا رتبة", "سهم بأثر بنفسجي. قريب منه يضعف، وقانون الصمت يمنعه من الرمي."],
  ["sh:ember_imp", "عفريت الرماد", "مبتدئ", "يحذرك بخط أحمر ثم يقفز عليك ويخدش بمخالبه."],
  ["sh:rust_guard", "حارس الصخر", "مبتدئ", "ضخم وبطيء. يضرب الأرض ويكنس بمخالبه. ابتعد وقت التحضير."],
  ["sh:shadow_hound", "ذئب الظل", "مبتدئ", "يعوي فتبطؤ حركتك، بعدها يعض عضتين سريعة. اضربه قبل العواء."],
  ["sh:sand_scorpion", "عقرب الرمل", "مبتدئ", "ذيله الأخضر يضربك من بعيد نسبيا ويسممك. لا تقف قدامه وقت ما يرفع ذيله."],
];
async function openMonsterBook(player) {
  const st = getState(player);
  const kills = st.kills || {};
  let body = "§5كتاب الوحوش§r\n\n";
  for (const [id, name, rank, tip] of MONSTER_INFO) {
    const k = kills[id] || 0;
    body += `§e${name} §7(${rank}) §fقتلت: §b${k}\n§7${k > 0 || id === "sh:training_archer" ? tip : "قتل وحدة حتى تنكشف معلوماته."}\n\n`;
  }
  await showForm(player, new ActionFormData().title("كتاب الوحوش").body(body).button("§aتمام"));
}

// ───────────────────────── نافذة الحالة ─────────────────────────
// ملخص كامل: الرتبة والليفل والقدرة وكل مهارة (مستواها، حالتها، طريقة استعمالها) وتطور الكاتانا.
async function showStatus(player) {
  const st = getState(player);
  const pw = POWERS[st.power];
  let b = `§6◆ ${RANKS[st.rank]}§r  §bLv ${st.level}§r  §7(${st.xp}/${xpNeeded(st.level)} XP)\n${nextRankLine(st)}\n`;
  if (pw) {
    const r = rarityOf(st.power);
    b += `\n${pw.color}${pw.name}§r ${rarityStars(st.power)}§r ${r.color}${r.name}§r\n§dليفل القدرة ${st.plevel || 1}/${r.maxLv}§r ${(st.plevel || 1) >= r.maxLv ? "§6(أقصى)" : `§7(${st.pxp || 0}/${powerXpNeeded(st.plevel || 1)})`}\n`;
    const tr = st.training && st.training[st.power];
    if (!tr || tr.status !== "done") b += "§e⚠ كمل تدريب المدرب حتى تنفتح باقي المهارات\n";
    b += "\n§eالمهارات:§r\n";
    Object.values(SKILLS).filter((s) => s.power === st.power).forEach((s, i) => {
      if (isSkillUnlocked(st, s)) {
        const lv = skillLevel(st, s.id), x = (st.skills[s.id] && st.skills[s.id].xp) || 0;
        b += `§a${i + 1}. ${s.name}§r §bمستوى ${lv}§7 (${x}/${skillXpNeeded(lv)})\n§7   ${usageOf(s)}\n`;
      } else {
        b += `§8${i + 1}. ${s.name} §c(تنفتح عند ليفل القدرة ${s.unlock}${tr && tr.status === "done" ? "" : " + التدريب"})\n`;
      }
    });
  } else b += "\n§7ما عندك قدرة. ترتقي رتبة جديدة وتعيد القرعة.\n";
  if (hasItem(player, KATANA) || player.getDynamicProperty("sh_kat")) {
    const k = getKat(player);
    b += `\n§5⚔ كاتانا الهاوية§r §dLv ${k.lv}/${KAT_MAX}§r ${k.lv >= KAT_MAX ? "§6(أقصى)" : `§7(${k.xp}/${KAT_NEED[k.lv]} XP، تزيد بقتل الأعداء وهي بيدك)`}\n`;
    KATANA_MODES.forEach((m, i) => { b += `${m.lv <= k.lv ? "§d" : "§8"}${i + 1}. ${m.name}§r${m.lv <= k.lv ? "" : ` §c(ليفل ${m.lv})`}\n`; });
    b += "§7السنيك: تبديل المهارة | استعمال: تنفيذ\n";
  }
  await showForm(player, new ActionFormData().title("نافذة الحالة").body(b).button("§aتمام"));
}

async function openBook(player) {
  const st = getState(player);
  if (!st.power) return openPowerMenu(player);
  const pw = POWERS[st.power];
  const mine = Object.values(SKILLS).filter((s) => s.power === st.power);

  const form = new ActionFormData()
    .title("كتاب التطور")
    .body(
      `${pw.color}${pw.name} ${rarityOf(st.power).color}[${rarityOf(st.power).name}]§r\nليفل القدرة: §d${st.plevel || 1}/${rarityOf(st.power).maxLv}§r ${(st.plevel || 1) >= rarityOf(st.power).maxLv ? "§6(أقصى)" : `§7(XP ${st.pxp || 0}/${powerXpNeeded(st.plevel || 1)})`}§r\nالرتبة: §e${RANKS[st.rank]}§r\nالليفل: §b${st.level}§r\nXP: §a${st.xp}/${xpNeeded(st.level)}§r\n${nextRankLine(st)}\n\n§7اختر مهارة وتجيك بإيدك. القدرة تتطور بقتل الأعداء وانت تستعمل مهاراتها.`
    );
  for (const s of mine) {
    if (isSkillUnlocked(st, s)) {
      const lv = skillLevel(st, s.id);
      const sk = st.skills[s.id] || { xp: 0 };
      form.button(`§a${s.name} §bمستوى ${lv} §7(${sk.xp}/${skillXpNeeded(lv)}) §e${AIMED.has(s.id) ? "[تصويب]" : "[حولك]"}\n§7${usageOf(s)}`);
    }
    else {
      const tr = st.training[st.power];
      const need = !tr || tr.status !== "done" ? "كمل تدريب المدرب" : `تنفتح عند ليفل القدرة ${s.unlock}`;
      form.button(`§8${s.name}\n§c${need}`);
    }
  }
  form.button("§e[الرتب وطريقة الترقي]");
  form.button("§b[نافذة الحالة وطريقة الاستعمال]");
  const r = await showForm(player, form);
  if (r.canceled) return;
  if (r.selection === mine.length) { showRanks(player); return; }
  if (r.selection === mine.length + 1) { showStatus(player); return; }
  const s = mine[r.selection];
  if (!s) return;
  if (!isSkillUnlocked(st, s)) { notify(player, `§c${s.name}: مقفولة بعد`, 60); return; }
  const c = inv(player);
  let has = false;
  for (let i = 0; i < c.size; i++) { const it = c.getItem(i); if (it && it.typeId === s.item) { has = true; break; } }
  if (has) { notify(player, `§e${s.name} موجودة عندك بالانفنتوري`, 50); return; }
  giveItem(player, s.item);
  sfxPlayer(player, "sh.select", 0.7, 1.3);
  notify(player, `§aصارت بإيدك: ${s.name}`, 60);
  say(player, `§e[${s.name}] §f${s.desc}\n§7الاستعمال: ${usageOf(s)}. تقدر تاخذ أكثر من مهارة وتوزعها بالهوتبار.`);
}

// ───────────────────────── المدرب ─────────────────────────
const talkCd = new Map();

function describeDir(player, trainer) {
  const dx = trainer.location.x - player.location.x;
  const dz = trainer.location.z - player.location.z;
  const dist = Math.round(Math.hypot(dx, dz));
  let dir;
  if (Math.abs(dx) > Math.abs(dz) * 2) dir = dx > 0 ? "شرق" : "غرب";
  else if (Math.abs(dz) > Math.abs(dx) * 2) dir = dz > 0 ? "جنوب" : "شمال";
  else dir = (dz > 0 ? "جنوب" : "شمال") + (dx > 0 ? " شرق" : " غرب");
  return `المدرب ظهر على بعد ${dist} بلوكة باتجاه ال${dir}.`;
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
  if (t) t.nameTag = "§6المدرب";
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
    notify(player, "§7اختر قدرتك أول من كتاب التطور", 80);
    return openPowerMenu(player);
  }
  const pw = POWERS[st.power];
  const tr = st.training[st.power] || { status: "none", kills: 0 };

  if (tr.status === "none") {
    const f = new ActionFormData()
      .title("المدرب")
      .body(`§eأهلا بيك يا ${pw.color}${pw.name}§e.\n\n§fتدريبك هو هزيمة §e${TRAIN_NEED}§f وحوش أساسية بدون رتب. كل واحد يعطيك خبرة من 20 لـ 50.\n\n§7توافق على المهمة؟`)
      .button("§aأوافق")
      .button("§7لاحقا");
    const r = await showForm(player, f);
    if (r.canceled || r.selection !== 0) return;
    const s2 = getState(player);
    s2.training[s2.power] = { status: "active", kills: 0 };
    const giveMB = !s2.gotMonsterBook;
    s2.gotMonsterBook = true;
    saveState(player, s2);
    if (giveMB) { giveItem(player, "sh:monster_book"); say(player, "§5[المدرب] §fخذ كتاب الوحوش. يعلمك نقاط ضعفهم وكل ما تقتل نوع تنكشف معلوماته."); }
    const made = spawnTrainingMonsters(player, TRAIN_NEED);
    say(player, `§6[مهمة] §fاهزم ${TRAIN_NEED} وحوش تدريب (0/${TRAIN_NEED})`);
    notify(player, `§eالمهمة بدأت: اهزم ${TRAIN_NEED} وحوش (${made} ظهروا)`, 100);
    return;
  }

  if (tr.status === "active") {
    if (tr.kills < TRAIN_NEED) {
      const f = new ActionFormData()
        .title("المدرب")
        .body(`تقدمك: §e${tr.kills}/${TRAIN_NEED}§r\nكمل هزيمة وحوش التدريب.`)
        .button("§bاستدع وحوش مرة ثانية")
        .button("§7رجوع");
      const r = await showForm(player, f);
      if (r.canceled || r.selection !== 0) return;
      const made = spawnTrainingMonsters(player, TRAIN_NEED - tr.kills);
      notify(player, `§e${made} وحوش ظهروا قريب منك`, 80);
      return;
    }
    // خلص التدريب
    const s2 = getState(player);
    s2.training[s2.power] = { status: "done", kills: tr.kills };
    const ups = addXp(s2, 15);
    saveState(player, s2);
    if (!hasItem(player, "sh:evolution_book")) giveItem(player, "sh:evolution_book");
    sfxPlayer(player, "sh.mission");
    say(player, `§e[المدرب] §fأحسنت! تعلمت أساسيات ${pw.color}${pw.name}§f. افتح كتاب التطور واختر مهارتك.`);
    announceUps(player, ups);
    return;
  }

  // done
  const nextSkill = Object.values(SKILLS).find((s) => s.power === st.power && !isSkillUnlocked(st, s));
  const f = new ActionFormData()
    .title("المدرب")
    .body(
      nextSkill
        ? `أساسياتك خلصت.\nالمهارة الجاية: §e${nextSkill.name}§r. تنفتح لما تصير قدرتك ليفل §b${nextSkill.unlock}§r (حاليا ${st.plevel || 1}). تطورها بقتل الأعداء وانت تستعمل مهاراتك.`
        : "أساسياتك خلصت. اكتشف باقي المهارات وانت تتطور."
    )
    .button("§bاستدع وحوش تدريب")
    .button("§7رجوع");
  const r = await showForm(player, f);
  if (r.canceled || r.selection !== 0) return;
  const made = spawnTrainingMonsters(player, 3);
  notify(player, `§e${made} وحوش ظهروا قريب منك`, 80);
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
      say(player, `§b[ليفل] §fوصلت ليفل §b${u.level}`);
    } else if (u.type === "plevel") {
      sfxPlayer(player, "sh.level_up", 1, 0.8);
      burst(player.dimension, headPos(player), 24, COLORS.purple, 3, 0.22);
      const stx = getState(player);
      say(player, `§d[القدرة] §fقدرتك صارت ليفل §d${u.level}`);
      for (const sk of Object.values(SKILLS)) {
        if (sk.power === stx.power && !sk.first && sk.unlock === u.level) say(player, `§a[مهارة جديدة] §f${sk.name} انفتحت${(stx.training[stx.power] || {}).status === "done" ? " — افتح كتاب التطور." : " (تحتاج تدريب المدرب)."}`);
      }
    } else if (u.type === "skill") {
      sfxPlayer(player, "sh.level_up", 0.8, 1.3);
      const sk = SKILLS[u.id];
      say(player, `§d[مهارة] §f${sk.name} صارت مستوى §d${u.level}`);

    } else if (u.type === "rank") {
      sfxPlayer(player, "sh.rank_up");
      burst(player.dimension, headPos(player), 30, COLORS.gold, 3.5, 0.25);
      notify(player, `§6ارتقيت إلى رتبة ${RANKS[u.rank]}!`, 100);
      say(player, `§6[رتبة] §fصارت رتبتك §e${RANKS[u.rank]}`);
      try { if (!getState(player).power) system.runTimeout(() => rollPower(player), 60); } catch (e) { /* */ }
    }
  }
}

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
      notify(player, tr.kills >= TRAIN_NEED ? "§aخلصت! ارجع للمدرب" : `§eتدريب ${tr.kills}/${TRAIN_NEED}`, 70);
    }
  }
  const res = monsterReward(st, info);
  if (st.power) res.ups.push(...addPowerXp(st, Math.max(1, Math.round(res.xp * 0.3)), rarityOf(st.power).maxLv));
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
      if (held && held.typeId === KATANA) addKatXp(killer, info ? (Array.isArray(info.xp) ? info.xp[0] : info.xp) : 2);
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
    handleKill(killer, info);
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

function setNum(e, n) {
  e.setDynamicProperty("sh_num", n);
  e.nameTag = `${numColor(n)}⟦${n}⟧`;
}
function clearNum(e) {
  try { e.setDynamicProperty("sh_num", undefined); e.nameTag = ""; } catch (err) { /* */ }
}

function collapse(e, p) {
  const dim = e.dimension;
  const loc = headPos(e);
  clearNum(e);
  sfx(dim, "sh.collapse", loc, 1.2);
  burst(dim, loc, 40, COLORS.red, 4, 0.25);
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
    if (e.id === p.id || e.typeId === "sh:trainer") continue;
    let hp;
    try { hp = e.getComponent("minecraft:health"); } catch (err) { continue; }
    if (!hp) continue;
    return e;
  }
  return undefined;
}

// ───────────────────────── أدوات الأعداء ─────────────────────────
function enemiesNear(dim, center, r, excludeId) {
  let list = [];
  try {
    list = dim.getEntities({
      location: center, maxDistance: r,
      excludeTypes: ["minecraft:player", "sh:trainer"],
      excludeFamilies: ["inanimate"],
    });
  } catch (e) { return []; }
  return list.filter((e) => {
    if (e.id === excludeId) return false;
    try { return !!e.getComponent("minecraft:health"); } catch (err) { return false; }
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
function hurt(e, amount, by) {
  try { e.applyDamage(amount, { cause: EntityDamageCause.entityAttack, damagingEntity: by }); } catch (err) { /* */ }
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
  zones.push(z);
}

function unsilenceAll(z) {
  for (const e of z.silenced.values()) { try { e.triggerEvent("sh:unsilence"); } catch (err) { /* */ } }
  z.silenced.clear();
}

const ZONE_COLORS = { weight: COLORS.red, silence: COLORS.blue, reflect: COLORS.white, boundary: COLORS.purple };

function endZone(i) {
  const z = zones[i];
  removeFx(z.fx);
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
            if (!z.silenced.has(e.id)) { e.triggerEvent("sh:silence"); z.silenced.set(e.id, e); }
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
    if (now % 10 === 0) {
      const col = ZONE_COLORS[z.kind] || COLORS.gold;
      const second = z.kind === "weight" ? COLORS.gold : z.kind === "boundary" ? COLORS.white : COLORS.white;
      ring(z.dim, z.c, z.r, 28, now * 0.03, z.kind === "weight" ? COLORS.gold : col, 0.2);
      ring(z.dim, z.c, z.r * 0.6, 14, -now * 0.04, z.kind === "weight" ? COLORS.red : second, 0.16);
      if (z.kind === "boundary") {
        for (let h = 1; h <= 3; h++) ring(z.dim, { x: z.c.x, y: z.c.y + h * 0.9, z: z.c.z }, z.r - 0.5, 22, h, col, 0.18);
      }
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
      line(victim.dimension, headPos(victim), headPos(attacker), COLORS.white);
      burst(attacker.dimension, headPos(attacker), 14, COLORS.white, 3);
    } finally { reflecting = false; }
  } catch (e) { reflecting = false; }
});

// ───────────────────────── المهارات ─────────────────────────
const SKILL_FN = {
  seal(p) {
    const t = raycastTarget(p);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    setNum(t, 10);
    numOwners.set(t.id, { e: t, pid: p.id });
    followFx(t, 0, 400, 1.2);
    try { t.addEffect("slowness", 60, { amplifier: 0, showParticles: false }); } catch (e) { /* */ }
    notify(p, "§6الرقم ينقص كل ثانيتين وكل ضربة تنقصه. عند الصفر ينهار", 70);
    line(p.dimension, headPos(p), headPos(t), COLORS.gold);
    burst(t.dimension, headPos(t), 14, COLORS.gold, 2);
    sfx(p.dimension, "sh.seal", p.location);
    shake(p, 0.05, 0.1);
    return true;
  },
  subtract(p) {
    const t = raycastTarget(p);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    line(p.dimension, headPos(p), headPos(t), COLORS.red);
    sfx(p.dimension, "sh.subtract", p.location);
    shake(p, 0.08, 0.12);
    const n = t.getDynamicProperty("sh_num");
    if (typeof n !== "number") { setNum(t, 7); numOwners.set(t.id, { e: t, pid: p.id }); followFx(t, 0, 280, 1.0); burst(t.dimension, headPos(t), 12, COLORS.orange, 2); }
    else decNum(t, 3, p);
    return true;
  },
  weight(p) {
    startZone(p, "weight", 6, 120);
    sfx(p.dimension, "sh.weight", p.location, 1.2);
    shake(p, 0.15, 0.2);
    ring(p.dimension, p.location, 6, 40, 0, COLORS.gold, 0.28);
    return true;
  },
  silence(p) {
    startZone(p, "silence", 8, 100);
    sfx(p.dimension, "sh.silence", p.location, 1.1);
    ring(p.dimension, p.location, 8, 48, 0, COLORS.blue, 0.26);
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
    if (!t || n === undefined) { notify(p, "§cاستهدف عدو عليه رقم", 40); return false; }
    const o = nearestEnemy(t, 12);
    if (!o) { notify(p, "§cما كو عدو ثاني قريب", 40); return false; }
    clearNum(t);
    setNum(o, n);
    line(t.dimension, headPos(t), headPos(o), COLORS.gold);
    burst(o.dimension, headPos(o), 16, COLORS.gold, 2.5);
    sfx(p.dimension, "sh.transfer", p.location);
    return true;
  },
  divide(p) {
    const t = raycastTarget(p);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    let n = numberOf(t);
    if (n === undefined) n = 10;
    if (n < 2) { notify(p, "§cالرقم 1 ما ينقسم", 40); return false; }
    const o = nearestEnemy(t, 12);
    if (!o) { notify(p, "§cما كو عدو ثاني قريب", 40); return false; }
    const a = Math.ceil(n / 2), b = Math.floor(n / 2);
    setNum(t, a);
    setNum(o, b);
    line(t.dimension, headPos(t), headPos(o), COLORS.orange);
    burst(t.dimension, headPos(t), 12, COLORS.orange, 2);
    burst(o.dimension, headPos(o), 12, COLORS.orange, 2);
    sfx(p.dimension, "sh.divide", p.location);
    shake(p, 0.08, 0.1);
    return true;
  },
  zero(p) {
    const t = raycastTarget(p);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    line(p.dimension, headPos(p), headPos(t), COLORS.red);
    sfx(p.dimension, "sh.zero", p.location, 1.2);
    shake(p, 0.18, 0.25);
    const n = numberOf(t);
    if (n === undefined || n <= 5) collapse(t, p);
    else decNum(t, 5, p);
    return true;
  },

  // ── كاتب القوانين ──
  reflect(p) {
    startZone(p, "reflect", 5, 140);
    sfx(p.dimension, "sh.reflect", p.location, 1.1);
    ring(p.dimension, p.location, 5, 36, 0, COLORS.white, 0.26);
    return true;
  },
  boundary(p) {
    startZone(p, "boundary", 7, 160);
    sfx(p.dimension, "sh.boundary", p.location, 1.2);
    shake(p, 0.12, 0.2);
    for (let h = 0; h < 4; h++) ring(p.dimension, { x: p.location.x, y: p.location.y + h * 0.8, z: p.location.z }, 7, 40, h, COLORS.purple, 0.26);
    return true;
  },
  async absolute(p) {
    const laws = [
      ["§aما أحد يتأذى غيري", "حصانة كاملة"],
      ["§cالكل ثقيل", "كل الأعداء حواليك يتبطؤون ويضعفون"],
      ["§6ضرب الملك", "ضررك مضاعف"],
    ];
    const f = new ActionFormData().title("القانون المطلق").body("§7اكتب قانونك. يمشي 5 ثواني.");
    for (const l of laws) f.button(`${l[0]}\n§7${l[1]}`);
    const r = await showForm(p, f);
    if (r.canceled) return false;
    spawnFx(p.dimension, "circle", p.location, 0, 4, 106);
    spawnFx(p.dimension, "plate", { x: p.location.x, y: p.location.y + 2.6, z: p.location.z }, 0, 2, 100);
    sfx(p.dimension, "sh.absolute", p.location, 1.3);
    shake(p, 0.2, 0.4);
    for (let h = 0; h < 3; h++) ring(p.dimension, { x: p.location.x, y: p.location.y + h * 0.7, z: p.location.z }, 3 + h, 36, h, COLORS.gold, 0.3);
    try {
      if (r.selection === 0) {
        p.addEffect("resistance", 100, { amplifier: 4, showParticles: false });
      } else if (r.selection === 1) {
        for (const e of enemiesNear(p.dimension, p.location, 14, p.id)) {
          e.addEffect("slowness", 100, { amplifier: 4, showParticles: false });
          e.addEffect("weakness", 100, { amplifier: 2, showParticles: false });
        }
      } else {
        p.addEffect("strength", 100, { amplifier: 2, showParticles: false });
      }
    } catch (e) { /* */ }
    notify(p, `${laws[r.selection][0]}§r: 5 ثواني`, 100);
    return true;
  },

  // ── محرف المسافة ──
  pull(p) {
    const t = raycastTarget(p, 32);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    const d = flatDir(p);
    line(p.dimension, headPos(t), headPos(p), COLORS.blue);
    const dest = { x: p.location.x + d.x * 2.2, y: p.location.y, z: p.location.z + d.z * 2.2 };
    if (!safeTeleport(t, dest)) {
      const dx = p.location.x - t.location.x, dz = p.location.z - t.location.z, l = Math.hypot(dx, dz) || 1;
      try { t.applyKnockback({ x: (dx / l) * 3, z: (dz / l) * 3 }, 0.3); } catch (e) { /* */ }
    }
    burst(t.dimension, headPos(t), 14, COLORS.blue, 2);
    portalFx(p.dimension, { x: t.location.x, y: t.location.y, z: t.location.z }, 2, 1.4, t.location, p.location);
    portalFx(p.dimension, { x: p.location.x + d.x * 2.2, y: p.location.y, z: p.location.z + d.z * 2.2 }, 2, 1.2, t.location, p.location);
    sfx(p.dimension, "sh.pull", p.location);
    shake(p, 0.06, 0.1);
    return true;
  },
  push(p) {
    const t = raycastTarget(p, 24);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    line(p.dimension, headPos(p), headPos(t), COLORS.blue);
    pushAway(p.location, t, 6, 0.6);
    hurt(t, 2, p);
    burst(t.dimension, headPos(t), 14, COLORS.white, 3);
    portalFx(p.dimension, { x: p.location.x, y: p.location.y, z: p.location.z }, 2, 1.2, p.location, t.location);
    sfx(p.dimension, "sh.push", p.location);
    shake(p, 0.08, 0.12);
    return true;
  },
  swap(p) {
    const t = raycastTarget(p, 30);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    const a = { ...p.location }, b = { ...t.location };
    burst(p.dimension, headPos(p), 12, COLORS.blue, 2);
    burst(t.dimension, headPos(t), 12, COLORS.blue, 2);
    try { p.teleport(b, { facingLocation: a }); t.teleport(a); } catch (e) { return false; }
    portalFx(p.dimension, a, 2, 1.4, a, b); portalFx(p.dimension, b, 2, 1.4, a, b);
    line(p.dimension, a, b, COLORS.white);
    burst(p.dimension, headPos(p), 14, COLORS.white, 2);
    sfx(p.dimension, "sh.swap", p.location);
    return true;
  },
  fold(p) {
    const t = raycastTarget(p, 40);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    const dx = t.location.x - p.location.x, dz = t.location.z - p.location.z, l = Math.hypot(dx, dz) || 1;
    const from = headPos(p), to = headPos(t);
    for (let i = 0; i <= 18; i++) {
      const k = i / 18, w = Math.sin(k * Math.PI * 6) * 0.35;
      glow(p.dimension, { x: from.x + (to.x - from.x) * k - (dz / l) * w, y: from.y + (to.y - from.y) * k + w, z: from.z + (to.z - from.z) * k + (dx / l) * w },
        { color: COLORS.white, size: 0.16, life: 0.5 });
    }
    const dest = { x: t.location.x - (dx / l) * 1.8, y: t.location.y, z: t.location.z - (dz / l) * 1.8 };
    portalFx(p.dimension, p.location, 2, 1.5, p.location, t.location, 20);
    safeTeleport(p, dest, t.location);
    portalFx(p.dimension, dest, 2, 1.5, p.location, t.location, 20);
    hurt(t, 9, p);
    pushAway(p.location, t, 1.2, 0.3);
    burst(t.dimension, headPos(t), 20, COLORS.blue, 3.5, 0.24);
    sfx(p.dimension, "sh.fold", t.location, 1.1);
    shake(p, 0.15, 0.15);
    return true;
  },
  spacecollapse(p) {
    const list = enemiesNear(p.dimension, p.location, 12, p.id);
    if (list.length === 0) { notify(p, "§cما كو أعداء قريبين", 40); return false; }
    const d = flatDir(p);
    const c = { x: p.location.x + d.x * 5, y: p.location.y, z: p.location.z + d.z * 5 };
    portalFx(p.dimension, c, 2, 3.2, p.location, c, 50);
    portalFx(p.dimension, { x: c.x, y: c.y + 0.5, z: c.z }, 4, 2.0, c, p.location, 50);
    sfx(p.dimension, "sh.spacecollapse", p.location, 1.3);
    shake(p, 0.25, 0.5);
    [5, 3, 1.5].forEach((r, i) => system.runTimeout(() => ring(p.dimension, c, r, 28, i, COLORS.blue, 0.3), i * 4));
    for (const e of list) {
      const dest = { x: c.x + (Math.random() - 0.5) * 2.4, y: c.y, z: c.z + (Math.random() - 0.5) * 2.4 };
      safeTeleport(e, dest);
      hurt(e, 5, p);
    }
    system.runTimeout(() => burst(p.dimension, c, 40, COLORS.white, 4, 0.3), 12);
    return true;
  },

  // ── ناسج الصدى ──
  echostrike(p) {
    echoReady.set(p.id, { until: system.currentTick + 160 });
    sfx(p.dimension, "sh.echostrike", p.location);
    ring(p.dimension, p.location, 1.6, 20, 0, POWER_COLOR.echo, 0.22);
    waveFx(p.dimension, p.location, 2.5, 3, 10);
    notify(p, "§3ضربتك الجاية تنعاد", 50);
    return true;
  },
  echoseal(p) {
    const t = raycastTarget(p, 24);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    echoMarks.set(t.id, { sum: 0 });
    followFx(t, 3, 100, 1.1);
    line(p.dimension, headPos(p), headPos(t), POWER_COLOR.echo);
    sfx(p.dimension, "sh.echoseal", p.location);
    for (let i = 0; i < 5; i++) system.runTimeout(() => { if (valid(t)) ring(t.dimension, t.location, 1 + i * 0.1, 14, i, POWER_COLOR.echo, 0.18); }, i * 20);
    system.runTimeout(() => {
      const m = echoMarks.get(t.id);
      echoMarks.delete(t.id);
      if (!m || !valid(t)) return;
      hurt(t, Math.max(4, m.sum), p);
      burst(t.dimension, headPos(t), 36, POWER_COLOR.echo, 4, 0.26);
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
    const d = flatDir(p), c = { ...p.location };
    const wave = (dmg, rmax, pitch) => {
      sfx(p.dimension, "sh.echowave", c, 1, pitch);
      shake(p, 0.12, 0.15);
      for (let r = 2; r <= rmax; r += 2) arc(p.dimension, c, d, r, 0.87, POWER_COLOR.echo, 14);
      for (const e of enemiesNear(p.dimension, c, rmax, p.id)) {
        const vx = e.location.x - c.x, vz = e.location.z - c.z, l = Math.hypot(vx, vz) || 1;
        if ((vx / l) * d.x + (vz / l) * d.z < 0.64) continue;
        hurt(e, dmg, p);
        pushAway(c, e, 1.6, 0.35);
        burst(e.dimension, headPos(e), 10, POWER_COLOR.echo, 2.5);
      }
    };
    waveFx(p.dimension, c, 12, 3, 12);
    wave(7, 12, 1);
    system.runTimeout(() => { if (valid(p)) { waveFx(p.dimension, c, 14, 3, 12); wave(4, 14, 0.8); } }, 10);
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
        waveFx(p.dimension, p.location, r, 3, 14);
        for (const f of [0.4, 0.7, 1]) ring(p.dimension, p.location, r * f, 40, f * 3, POWER_COLOR.echo, 0.3);
        for (const e of enemiesNear(p.dimension, p.location, r, p.id)) {
          hurt(e, dmgs[i], p);
          pushAway(p.location, e, 1.4, 0.3);
          burst(e.dimension, headPos(e), 10, POWER_COLOR.echo, 3);
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
    spawnFx(p.dimension, "circle", p.location, 4, 1.8, 124);
    ring(p.dimension, p.location, 1.1, 20, 0, COLORS.white, 0.2);
    burst(p.dimension, headPos(p), 20, [0.7, 0.72, 0.8], 2.5, 0.2);
    sfx(p.dimension, "sh.guard_slam", p.location, 0.8, 1.4);
    notify(p, "§7جسمك صار حديد: مقاومة عالية", 50);
    return true;
  },
  ironfist(p) {
    const t = raycastTarget(p, 5);
    if (!t) { notify(p, "§cما كو عدو قريب قدامك", 30); return false; }
    hurt(t, 9, p);
    pushAway(p.location, t, 2.4, 0.4);
    waveFx(t.dimension, t.location, 3, 4, 8);
    burst(t.dimension, headPos(t), 22, [0.8, 0.82, 0.9], 3.5, 0.24);
    sfx(p.dimension, "sh.cleaver_hit", t.location, 1.1, 0.7);
    shake(p, 0.2, 0.2);
    return true;
  },
  // ── متتبع الريح ──
  windrun(p) {
    try { p.addEffect("speed", 100, { amplifier: 2, showParticles: false }); } catch (e) { return false; }
    sfx(p.dimension, "sh.push", p.location, 0.8, 1.5);
    let n = 0;
    const h = system.runInterval(() => {
      try {
        if (!valid(p) || n++ > 50) { system.clearRun(h); return; }
        ring(p.dimension, p.location, 0.7, 8, n, COLORS.green, 0.12);
        glow(p.dimension, { x: p.location.x, y: p.location.y + 0.2, z: p.location.z }, { color: COLORS.white, size: 0.22, life: 0.6 });
      } catch (e) { system.clearRun(h); }
    }, 2);
    return true;
  },
  windleap(p) {
    const d = flatDir(p);
    try {
      p.applyKnockback({ x: d.x * 2.6, z: d.z * 2.6 }, 0.9);
      p.addEffect("slow_falling", 80, { amplifier: 0, showParticles: false });
    } catch (e) { return false; }
    spawnFx(p.dimension, "circle", p.location, 3, 1.6, 20);
    burst(p.dimension, p.location, 24, COLORS.green, 3, 0.22);
    sfx(p.dimension, "sh.push", p.location, 1, 1.3);
    return true;
  },
  gale(p) {
    const list = enemiesNear(p.dimension, p.location, 7, p.id);
    waveFx(p.dimension, p.location, 7, 3, 14);
    for (const k of [0, 5, 10]) system.runTimeout(() => { if (valid(p)) ring(p.dimension, p.location, 2 + k * 0.5, 28, k, COLORS.green, 0.24); }, k);
    for (const e of list) {
      hurt(e, 3, p);
      pushAway(p.location, e, 2.6, 0.55);
      burst(e.dimension, headPos(e), 10, COLORS.green, 2.5, 0.2);
    }
    sfx(p.dimension, "sh.push", p.location, 1.3, 0.8);
    shake(p, 0.18, 0.3);
    return true;
  },
  // ── قانون الزمن ──
  time(p) {
    const list = enemiesNear(p.dimension, p.location, 9, p.id);
    if (list.length === 0) { notify(p, "§cما كو أعداء قريبين", 40); return false; }
    spawnFx(p.dimension, "circle", p.location, 0, 9, 66);
    for (const e of list) {
      try {
        e.addEffect("slowness", 60, { amplifier: 9, showParticles: false });
        e.addEffect("weakness", 60, { amplifier: 3, showParticles: false });
      } catch (err) { /* */ }
      followFx(e, 0, 60, 0.9);
    }
    sfx(p.dimension, "sh.weight", p.location, 1.2, 0.6);
    shake(p, 0.15, 0.3);
    return true;
  },
});

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
const weaponCd = new Map();

function weaponActive(p, id) {
  const w = WEAPONS[id];
  const now = system.currentTick;
  const ready = weaponCd.get(`${p.id}:${id}`) ?? 0;
  if (now < ready) { notify(p, `§7${w.name}: انتظر ${((ready - now) / 20).toFixed(1)}ث`, 15); return; }
  const dim = p.dimension;
  const o = p.location;
  const d = flatDir(p);
  let ok = false;
  if (w.active === "slam") {
    // قوس نار قدامك: أعداء بمدى 4.5 وبزاوية أمامية
    for (const e of enemiesNear(dim, o, 4.8, p.id)) {
      const dx = e.location.x - o.x, dz = e.location.z - o.z, l = Math.hypot(dx, dz) || 1;
      if ((dx / l) * d.x + (dz / l) * d.z < 0.35) continue;
      hurt(e, 6, p);
      try { e.setOnFire(4, true); } catch (err) { /* */ }
      pushAway(o, e, 1.0, 0.3);
      burst(dim, headPos(e), 10, COLORS.orange, 2.5, 0.2);
    }
    for (let i = 0; i <= 24; i++) {
      const a = Math.atan2(d.z, d.x) - 1.0 + (i / 24) * 2.0;
      for (const r of [1.6, 2.6, 3.6]) glow(dim, { x: o.x + Math.cos(a) * r, y: o.y + 1.0, z: o.z + Math.sin(a) * r }, { color: COLORS.orange, size: 0.22, life: 0.5, rise: 0.8 });
    }
    sfx(dim, "sh.cleaver_hit", o, 1.2, 0.7);
    shake(p, 0.15, 0.2);
    ok = true;
  } else if (w.active === "bind") {
    // أقرب عدو بنظرك خلال 10 بلوكات
    const v = viewDir(p);
    let best, bd = 1e9;
    for (const e of enemiesNear(dim, o, 10, p.id)) {
      const dx = e.location.x - o.x, dy = e.location.y + 0.8 - (o.y + 1.5), dz = e.location.z - o.z;
      const l = Math.hypot(dx, dy, dz) || 1;
      const dot = (dx * v.x + dy * v.y + dz * v.z) / l;
      if (dot < 0.9) continue;
      if (l < bd) { bd = l; best = e; }
    }
    if (!best) { notify(p, "§7ما في عدو بنظرك", 20); return; }
    hurt(best, 2, p);
    try { best.addEffect("slowness", 100, { amplifier: 2, showParticles: false }); } catch (err) { /* */ }
    line(dim, { x: o.x, y: o.y + 1.4, z: o.z }, { x: best.location.x, y: best.location.y + 1, z: best.location.z }, COLORS.gold);
    ring(dim, { x: best.location.x, y: best.location.y + 0.2, z: best.location.z }, 0.9, 16, 0, COLORS.gold, 0.22);
    ring(dim, { x: best.location.x, y: best.location.y + 1.0, z: best.location.z }, 0.7, 14, 1, COLORS.white, 0.18);
    burst(dim, headPos(best), 14, COLORS.gold, 2, 0.2);
    // سلاسل ضوئية تدور حول العدو 5 ثواني
    let n = 0;
    const tgt = best;
    const h = system.runInterval(() => {
      try {
        if (!valid(tgt) || n++ > 12) { system.clearRun(h); return; }
        ring(dim, { x: tgt.location.x, y: tgt.location.y + 0.2 + (n % 4) * 0.4, z: tgt.location.z }, 0.8, 8, n * 0.6, COLORS.gold, 0.14);
      } catch (err) { system.clearRun(h); }
    }, 8);
    sfx(dim, "sh.dagger_hit", o, 1, 1.5);
    ok = true;
  } else if (w.active === "throw") {
    const v = viewDir(p);
    const start = { x: o.x, y: o.y + 1.4, z: o.z };
    const pos = { ...start };
    let dist = 0, out = true;
    const hit = new Set();
    const MAXD = 16;
    const h = system.runInterval(() => {
      try {
        const step = 1.5;
        if (out) {
          pos.x += v.x * step; pos.y += v.y * step; pos.z += v.z * step; dist += step;
          const b = dim.getBlock({ x: Math.floor(pos.x), y: Math.floor(pos.y), z: Math.floor(pos.z) });
          if (dist >= MAXD || !b || !b.isAir) { out = false; hit.clear(); }
        } else {
          const tx = p.location.x, ty = p.location.y + 1.2, tz = p.location.z;
          const dx = tx - pos.x, dy = ty - pos.y, dz = tz - pos.z;
          const l = Math.hypot(dx, dy, dz) || 1;
          if (l < 1.6) { sfxPlayer(p, "sh.select", 0.6, 1.6); system.clearRun(h); return; }
          const k = Math.min(step * 1.3, l);
          pos.x += (dx / l) * k; pos.y += (dy / l) * k; pos.z += (dz / l) * k;
        }
        // رمح من جزيئات: رأس أبيض/أحمر وذيل
        const fx = out ? v : { x: 0, y: 0, z: 0 };
        glow(dim, pos, { color: COLORS.white, size: 0.3, life: 0.3 });
        glow(dim, { x: pos.x - fx.x * 0.4, y: pos.y - fx.y * 0.4, z: pos.z - fx.z * 0.4 }, { color: COLORS.red, size: 0.22, life: 0.4 });
        glow(dim, { x: pos.x - fx.x * 0.8, y: pos.y - fx.y * 0.8, z: pos.z - fx.z * 0.8 }, { color: COLORS.red, size: 0.16, life: 0.4 });
        for (const e of enemiesNear(dim, pos, 1.5, p.id)) {
          if (hit.has(e.id)) continue;
          hit.add(e.id);
          hurt(e, out ? 8 : 5, p);
          burst(dim, headPos(e), 10, COLORS.red, 2.5, 0.2);
          sfx(dim, "sh.dagger_hit", e.location, 1, 0.8);
        }
      } catch (err) { system.clearRun(h); }
    }, 1);
    sfx(dim, "sh.dagger_hit", o, 1, 0.5);
    ok = true;
  } else if (w.active === "dash") {
    let last = { x: o.x, y: o.y, z: o.z };
    const hitIds = new Set();
    for (let i = 1; i <= 14; i++) {
      const pos = { x: o.x + d.x * i * 0.5, y: o.y, z: o.z + d.z * i * 0.5 };
      try {
        const b1 = dim.getBlock({ x: Math.floor(pos.x), y: Math.floor(pos.y), z: Math.floor(pos.z) });
        const b2 = dim.getBlock({ x: Math.floor(pos.x), y: Math.floor(pos.y) + 1, z: Math.floor(pos.z) });
        if (!b1 || !b2 || !b1.isAir || !b2.isAir) break;
      } catch (err) { break; }
      last = pos;
      for (const e of enemiesNear(dim, { x: pos.x, y: pos.y, z: pos.z }, 1.6, p.id)) {
        if (hitIds.has(e.id)) continue;
        hitIds.add(e.id);
        hurt(e, 5, p);
        burst(dim, headPos(e), 8, COLORS.purple, 2.5, 0.2);
      }
      glow(dim, { x: pos.x, y: pos.y + 1, z: pos.z }, { color: COLORS.purple, size: 0.3, life: 0.5 });
      glow(dim, { x: pos.x, y: pos.y + 0.5, z: pos.z }, { color: COLORS.blue, size: 0.2, life: 0.4 });
    }
    safeTeleport(p, last);
    sfx(dim, "sh.dagger_hit", o, 1, 0.6);
    ok = true;
  } else if (w.active === "quake") {
    for (const e of enemiesNear(dim, o, 4.8, p.id)) {
      hurt(e, 6, p);
      try { e.applyKnockback({ x: 0, z: 0 }, 0.9); } catch (err) { /* */ }
      try { e.addEffect("slowness", 40, { amplifier: 2, showParticles: false }); } catch (err) { /* */ }
      burst(dim, e.location, 8, [0.6, 0.62, 0.58], 2, 0.25);
    }
    ring(dim, o, 1.5, 18, 0, COLORS.teal, 0.3);
    ring(dim, o, 3.0, 28, 0.5, [0.6, 0.62, 0.58], 0.3);
    ring(dim, o, 4.5, 36, 1, COLORS.teal, 0.28);
    sfx(dim, "sh.guard_slam", o, 1.3, 0.9);
    shake(p, 0.3, 0.3);
    ok = true;
  }
  if (ok) weaponCd.set(`${p.id}:${id}`, now + w.cd);
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
      ring(t.dimension, t.location, 1.2, 18, 0, POWER_COLOR.echo, 0.22);
      burst(t.dimension, headPos(t), 14, POWER_COLOR.echo, 3);
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
function flyShard(p, d, len, r = 0.8) {
  const o = eyePos(p);
  const e = crystalEnt(p.dimension, { x: o.x + d.x, y: o.y - 0.3 + d.y, z: o.z + d.z }, d, r, 40, 0);
  if (!e) return;
  let t = 1;
  const h = system.runInterval(() => {
    try {
      t += 2.4;
      if (!valid(e) || t > len) { system.clearRun(h); removeFx(e); return; }
      e.teleport({ x: o.x + d.x * t, y: o.y - 0.3 + d.y * t, z: o.z + d.z * t });
      glow(p.dimension, e.location, { color: CRYSTAL_PINK, size: 0.3, life: 0.4 });
    } catch (err) { system.clearRun(h); removeFx(e); }
  }, 1);
}
function rayTrail(p, d, len, color, size = 0.24) {
  const o = eyePos(p);
  for (let t = 0.8; t <= len; t += 0.6) {
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
  glow(e.dimension, headPos(e), { color: CRYSTAL_PINK, size: 0.4, life: 0.6 });
}
// بلورات عالقة بالهدف: تدور حول راسه وتتبعه
system.runInterval(() => {
  const now = system.currentTick;
  for (const [id, c] of [...crystals.entries()]) {
    if (!valid(c.e) || now > c.until) { dropCrystal(id); continue; }
    c.fx = c.fx.filter((f) => valid(f));
    while (c.fx.length < c.n) {
      const f = crystalEnt(c.e.dimension, c.e.location, { x: 0, y: 1, z: 0 }, 0.7, 320, 0);
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
const TRAIT_NAMES = { rock: "الصخر", fangs: "الأنياب", wings: "الأجنحة", eye: "عين الصياد" };

function effect(p, id, ticks, amp) {
  try { p.addEffect(id, Math.max(20, Math.round(ticks)), { amplifier: amp, showParticles: false }); } catch (e) { /* */ }
}
function applyTrait(p, id, m) {
  const now = system.currentTick;
  const col = { rock: [0.7, 0.62, 0.5], fangs: COLORS.red, wings: COLORS.green, eye: COLORS.gold }[id];
  if (id === "rock") {
    effect(p, "resistance", 200 * m, 1);
    effect(p, "slowness", 200 * m, 0);
    spawnFx(p.dimension, "circle", p.location, 4, 1.7, 40);
  } else if (id === "fangs") {
    fangsUntil.set(p.id, now + 160 * m);
    effect(p, "strength", 160 * m, 0);
    spawnFx(p.dimension, "circle", p.location, 5, 1.5, 30);
  } else if (id === "wings") {
    const d = flatDir(p);
    try { p.applyKnockback({ x: d.x * 0.9, z: d.z * 0.9 }, 1.1); } catch (e) { /* */ }
    effect(p, "slow_falling", 240 * m, 0);
    effect(p, "jump_boost", 200 * m, 1);
    effect(p, "speed", 200 * m, 1);
    spawnFx(p.dimension, "circle", p.location, 3, 1.8, 24);
  } else if (id === "eye") {
    effect(p, "night_vision", 300 * m, 0);
    const list = enemiesNear(p.dimension, p.location, 24, p.id).slice(0, 10);
    for (const e of list) {
      huntMarks.set(e.id, { pid: p.id, until: now + 200 * m });
      followFx(e, 5, 200 * m, 0.9);
    }
    notify(p, list.length ? `§eعلمت ${list.length} عدو` : "§7ما كو أعداء قريبين، بس رؤيتك تحسنت", 50);
  }
  ring(p.dimension, p.location, 1.3, 22, 0, col, 0.22);
  burst(p.dimension, headPos(p), 20, col, 2.5);
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
    burst(t.dimension, headPos(t), 8, COLORS.red, 2);
    if (now - (fangsHeal.get(p.id) || -99) >= 10) {
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
      const hits = rayHits(p, base, 20, 1.3);
      flyShard(p, base, hits.length ? Math.min(20, hits[hits.length - 1].t) : 20, 2.2);
      rayTrail(p, base, hits.length ? Math.min(20, hits[hits.length - 1].t) : 20, CRYSTAL_PINK, 0.3);
      for (const h of hits) { hurt(h.e, 9, p); pushAway(p.location, h.e, 0.6, 0.15); burst(h.e.dimension, headPos(h.e), 12, CRYSTAL_PINK, 3); addCrystal(h.e, p, 1); }
      sfx(p.dimension, "sh.push", p.location, 1.1, 1.6);
      shake(p, 0.1, 0.12);
      return true;
    }
    for (const ang of [-12, 0, 12]) {
      const d = rotY(base, ang);
      const hits = rayHits(p, d, 15, 1.1);
      const len = hits.length ? hits[0].t : 15;
      flyShard(p, d, len, 1.0);
      rayTrail(p, d, len, CRYSTAL_PINK, 0.14);
      if (hits.length) {
        const e = hits[0].e;
        hurt(e, 4, p);
        burst(e.dimension, headPos(e), 8, CRYSTAL_PINK, 2.5);
        addCrystal(e, p, 1);
      }
    }
    sfx(p.dimension, "sh.push", p.location, 0.9, 1.9);
    return true;
  },
  crystalshield(p) {
    effect(p, "absorption", 200, 2);
    spawnFx(p.dimension, "circle", p.location, 4, 1.8, 30);
    sfx(p.dimension, "sh.reflect", p.location, 1, 1.5);
    let t = 0;
    const orb = [0, 1, 2, 3].map(() => crystalEnt(p.dimension, p.location, { x: 0, y: 1, z: 0 }, 0.9, 215, 0));
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p) || t > 200) { system.clearRun(h); orb.forEach(removeFx); return; }
        orb.forEach((f, i) => {
          if (!f) return;
          const a = t * 0.2 + (i / 4) * Math.PI * 2;
          f.teleport({ x: p.location.x + Math.cos(a) * 1.2, y: p.location.y + 0.9 + (i % 2) * 0.5, z: p.location.z + Math.sin(a) * 1.2 });
        });
      } catch (e) { system.clearRun(h); orb.forEach(removeFx); }
    }, 2);
    return true;
  },
  prison(p) {
    const t = raycastTarget(p, 20);
    if (!t) { notify(p, "§cما كو هدف قدامك", 30); return false; }
    const dur = BOSS_TYPES.has(t.typeId) ? 40 : 100;
    effect(t, "slowness", dur, 8);
    effect(t, "jump_boost", dur, 200);
    effect(t, "weakness", dur, 1);
    addCrystal(t, p, 2);
    const fx = spawnFx(t.dimension, "circle", t.location, 4, 1.4, dur + 4);
    const pillars = [];
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      const pe = crystalEnt(t.dimension, { x: t.location.x + Math.cos(a) * 1.2, y: t.location.y + 0.9, z: t.location.z + Math.sin(a) * 1.2 }, { x: 0, y: 1, z: 0 }, 1.7, dur + 6, 0);
      if (pe) pillars.push(pe);
    }
    sfx(p.dimension, "sh.boundary", t.location, 1, 1.4);
    line(p.dimension, headPos(p), headPos(t), CRYSTAL_PINK);
    let k = 0;
    const h = system.runInterval(() => {
      try {
        k += 4;
        if (!valid(t) || k > dur) { system.clearRun(h); removeFx(fx); pillars.forEach(removeFx); return; }
        pillars.forEach((pe, i) => { const a = (i / 6) * Math.PI * 2; try { pe.teleport({ x: t.location.x + Math.cos(a) * 1.2, y: t.location.y + 0.9, z: t.location.z + Math.sin(a) * 1.2 }); } catch (e2) { /* */ } });
      } catch (e) { system.clearRun(h); removeFx(fx); pillars.forEach(removeFx); }
    }, 4);
    notify(p, BOSS_TYPES.has(t.typeId) ? "§dالبوس يقاوم: سجن قصير" : "§dانسجن", 40);
    return true;
  },
  burst(p) {
    const mine = [...crystals.entries()].filter(([, c]) => c.pid === p.id && valid(c.e));
    if (!mine.length) { notify(p, "§cما كو بلورات بالأعداء. استعمل الشظايا أو السجن", 50); return false; }
    let total = 0;
    for (const [id, c] of mine) {
      dropCrystal(id);
      total += c.n;
      const e = c.e;
      hurt(e, 5 * c.n, p);
      const hp = headPos(e);
      burst(e.dimension, hp, 24, CRYSTAL_PINK, 4, 0.26);
      ring(e.dimension, e.location, 1.8, 20, 0, CRYSTAL_PINK, 0.24);
      waveFx(e.dimension, e.location, 3.5, 4, 8);
      for (const o of enemiesNear(e.dimension, e.location, 3, p.id)) {
        if (o.id === e.id) continue;
        hurt(o, 3, p);
        pushAway(e.location, o, 0.8, 0.2);
      }
    }
    sfx(p.dimension, "sh.collapse", p.location, 1.1, 1.5);
    shake(p, 0.15, 0.2);
    notify(p, `§dفجرت ${total} بلورة`, 40);
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
    if (arr.length < 2) { notify(p, "§cاستعمل صفتين مختلفتين خلال 40 ثانية أول", 60); return false; }
    const two = arr.slice(-2);
    for (const x of two) applyTrait(p, x.id, 0.7);
    spawnFx(p.dimension, "circle", p.location, 0, 2.4, 30);
    notify(p, `§eدمجت: ${TRAIT_NAMES[two[0].id]} + ${TRAIT_NAMES[two[1].id]}`, 60);
    return true;
  },

  // ── محرف المسافة: الارتداد ──
  spacerewind(p) {
    const now = system.currentTick;
    const a = rewindAnchors.get(p.id);
    if (a && now <= a.until) {
      removeFx(a.fx);
      rewindAnchors.delete(p.id);
      if (a.dim.id !== p.dimension.id) { notify(p, "§cانت بعالم ثاني، الارتداد ضاع", 50); return 20; }
      const from = { ...p.location };
      if (!safeTeleport(p, a.loc)) { notify(p, "§cمكان الارتداد مسدود", 50); return 20; }
      const hp = p.getComponent("minecraft:health");
      if (hp && a.hp > hp.currentValue) hp.setCurrentValue(Math.min(hp.effectiveMax, a.hp, hp.currentValue + 8));
      effect(p, "slow_falling", 40, 0);
      portalFx(p.dimension, from, 1, 1.6, undefined, undefined, 20);
      portalFx(p.dimension, a.loc, 1, 1.6, undefined, undefined, 20);
      burst(p.dimension, headPos(p), 30, COLORS.blue, 3);
      sfx(p.dimension, "sh.swap", p.location, 1, 0.8);
      shake(p, 0.1, 0.15);
      return 1200;
    }
    const hp = p.getComponent("minecraft:health");
    const fx = spawnFx(p.dimension, "circle", p.location, 2, 1.3, 305);
    rewindAnchors.set(p.id, { loc: { ...p.location }, dim: p.dimension, hp: hp ? hp.currentValue : 20, until: now + 300, fx });
    ring(p.dimension, p.location, 1.3, 20, 0, COLORS.blue, 0.22);
    sfx(p.dimension, "sh.select", p.location, 1, 0.7);
    notify(p, "§bحفظت مكانك 15 ثانية. استعملها مرة ثانية للرجوع", 80);
    return 20;
  },
});


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
    const top = { x: c.x + 5, y: c.y + 24, z: c.z - 5 };
    spawnFx(dim, "circle", c, 0, 3.8, 30);
    pixRing(dim, { x: c.x, y: c.y + 0.2, z: c.z }, 3.8, 30, 0, STAR_GOLD, 0.2);
    sfx(dim, "sh.meteor_fall", c, 1.3, 1);
    later(8, () => {
      const steps = 10;
      for (let i = 0; i <= steps; i++) {
        later(i, () => {
          const k = i / steps;
          const loc = { x: top.x + (c.x - top.x) * k, y: top.y + (c.y - top.y) * k, z: top.z + (c.z - top.z) * k };
          glow(dim, loc, { color: [1, 0.55, 0.2], size: 1.1, life: 0.4 });
          glow(dim, loc, { color: [1, 0.95, 0.7], size: 0.6, life: 0.3 });
          for (let j = 0; j < 4; j++) pix(dim, { x: loc.x + (Math.random() - 0.5) * 1.0, y: loc.y + (Math.random() - 0.5) * 1.0, z: loc.z + (Math.random() - 0.5) * 1.0 }, { color: STAR_GOLD, size: 0.22, life: 0.8, speed: 0.3, rise: -1 });
        });
      }
    });
    later(20, () => {
      sfx(dim, "sh.meteor_hit", c, 1.5, 1);
      waveFx(dim, c, 7, 0, 12);
      glow(dim, c, { color: STAR_WHITE, size: 3, life: 0.35 });
      burst(dim, { x: c.x, y: c.y + 0.6, z: c.z }, 36, STAR_GOLD, 5, 0.3);
      for (let i = 0; i < 30; i++) pix(dim, { x: c.x, y: c.y + 0.4, z: c.z }, { color: i % 2 ? STAR_GOLD : [1, 0.5, 0.2], size: 0.24, life: 1.0, speed: 6, rise: -2 });
      for (const e of enemiesNear(dim, c, 4, p.id)) { hurtS(e, 14, p); pushAway(c, e, 1.1, 0.5); try { e.setOnFire(4, false); } catch (err) { /* */ } }
      shake(p, 0.2, 0.2);
    });
    return true;
  },
  // 2) بئر الجاذبية: يسحب الأعداء لنقطة 4 ثواني
  gravwell(p) {
    const dim = p.dimension, c = aimPoint(p, 24), life = 80;
    spawnFx(dim, "circle", c, 2, 6, life + 6);
    sfx(dim, "sh.gravwell", c, 1.2, 1);
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        for (let i = 0; i < 12; i++) {
          const a = t * 0.3 + i * 0.52, r = 7.5 * (1 - ((i / 12 + t * 0.04) % 1));
          pix(dim, { x: c.x + Math.cos(a) * r, y: c.y + 0.3 + r * 0.12, z: c.z + Math.sin(a) * r }, { color: i % 3 ? STAR_BLUE : STAR_WHITE, size: 0.2, life: 0.5 });
        }
        glow(dim, { x: c.x, y: c.y + 0.6, z: c.z }, { color: [0.3, 0.4, 1], size: 0.9, life: 0.3 });
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
    for (let i = 0; i < 3; i++) { const o = crystalEnt(dim, p.location, { x: 0, y: 1, z: 0 }, 0.8, life + 10, i % 2 ? 4 : 0); if (o) orbs.push(o); }
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
          if (orbs[i] && valid(orbs[i])) { try { orbs[i].teleport(loc); } catch (err) { /* */ } }
          glow(dim, loc, { color: i % 2 ? STAR_WHITE : STAR_GOLD, size: 0.5, life: 0.3 });
          pix(dim, loc, { color: STAR_BLUE, size: 0.14, life: 0.5, speed: 0.4 });
          for (const e of enemiesNear(dim, loc, 1.5, p.id)) {
            if ((hitCd.get(e.id) ?? 0) > t) continue;
            hitCd.set(e.id, t + 10);
            hurtS(e, 4, p);
            pushAway(p.location, e, 0.5, 0.2);
            burst(dim, headPos(e), 6, STAR_GOLD, 2.5, 0.16);
          }
        }
        if (t % 40 === 0) pixRing(dim, p.location, 2.3, 18, t * 0.1, STAR_BLUE, 0.14, 0.5);
      } catch (err) { system.clearRun(h); for (const o of orbs) removeFx(o); }
    }, 2);
    return true;
  },
  // 4) كوكبة: توصل الأعداء بخطوط نجمية وبعد ثانيتين تصعقهم كلهم
  constellation(p) {
    const dim = p.dimension;
    let list = enemiesNear(dim, p.location, 18, p.id).filter((e) => valid(e));
    if (list.length < 2) { notify(p, "§cتحتاج عدوين قريبين على الأقل", 40); return false; }
    list.sort((a, b) => Math.hypot(a.location.x - p.location.x, a.location.z - p.location.z) - Math.hypot(b.location.x - p.location.x, b.location.z - p.location.z));
    list = list.slice(0, 6);
    list.sort((a, b) => Math.atan2(a.location.z - p.location.z, a.location.x - p.location.x) - Math.atan2(b.location.z - p.location.z, b.location.x - p.location.x));
    sfx(dim, "sh.const_mark", p.location, 1.2, 1);
    for (const e of list) { followFx(e, 0, 60, 1.0); burst(dim, headPos(e), 10, STAR_GOLD, 2, 0.2); }
    const draw = (bright) => {
      for (let i = 0; i < list.length - 1; i++) {
        const a = list[i], b = list[i + 1];
        if (!valid(a) || !valid(b)) continue;
        pixLine(dim, center3(a), center3(b), bright ? STAR_WHITE : STAR_BLUE, bright ? 24 : 12, bright ? 0.24 : 0.12, bright ? 0.6 : 0.45);
      }
    };
    for (let k = 4; k <= 40; k += 6) later(k, () => draw(false));
    later(44, () => {
      draw(true);
      const bonus = list.length >= 4 ? 4 : 0;
      for (const e of list) {
        if (!valid(e)) continue;
        hurtS(e, 8 + bonus, p);
        burst(dim, headPos(e), 14, STAR_WHITE, 3, 0.22);
        glow(dim, headPos(e), { color: STAR_GOLD, size: 1.0, life: 0.35 });
        sfx(dim, "sh.const_zap", e.location, 1, 1 + Math.random() * 0.2);
      }
      shake(p, 0.12, 0.15);
    });
    notify(p, `§9كوكبة من ${list.length} نجوم... الصعقة بعد ثانيتين`, 50);
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
    if (!to) { notify(p, "§cما كو مجال للاندفاع", 30); return false; }
    const dim = p.dimension;
    for (let i = 0; i <= 26; i++) {
      const k = i / 26, loc = { x: from.x + (to.x - from.x) * k, y: from.y + 1.0, z: from.z + (to.z - from.z) * k };
      glow(dim, loc, { color: STAR_WHITE, size: 0.5, life: 0.3 });
      pix(dim, loc, { color: i % 2 ? STAR_GOLD : STAR_BLUE, size: 0.2, life: 0.9, speed: 0.8, rise: 0.2 });
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
    sfx(dim, "sh.blackhole", g, 1.5, 1);
    shake(p, 0.1, 0.4);
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        glow(dim, c, { color: [0.2, 0.08, 0.45], size: 1.6, life: 0.3 });
        glow(dim, c, { color: [0.05, 0.02, 0.15], size: 0.9, life: 0.3 });
        for (const [r, n, sp] of [[1.3, 10, 0.5], [2.2, 16, -0.36], [3.3, 22, 0.26]]) pixRing(dim, c, r, n, t * sp, r < 2 ? STAR_WHITE : VOID_PURPLE, 0.17, 0.4);
        for (let i = 0; i < 6; i++) {
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
          for (let i = 0; i < 30; i++) {
            const a = Math.random() * Math.PI * 2, r = 5 + Math.random() * 3;
            pix(dim, { x: c.x + Math.cos(a) * r, y: c.y + (Math.random() - 0.5) * 3, z: c.z + Math.sin(a) * r }, { color: VOID_PURPLE, size: 0.2, life: 0.4, speed: -9 });
          }
          later(8, () => {
            glow(dim, c, { color: STAR_WHITE, size: 4, life: 0.4 });
            burst(dim, c, 50, VOID_PURPLE, 7, 0.3);
            burst(dim, c, 24, STAR_WHITE, 6, 0.25);
            waveFx(dim, g, 10, 1, 14);
            waveFx(dim, g, 6, 4, 10);
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
    notify(p, "§9§lالمستعر الأعظم... اثبت مكانك", 50);
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p)) { system.clearRun(h); return; }
        const c = { x: p.location.x, y: p.location.y + 1.0, z: p.location.z };
        const k = t / charge;
        for (let i = 0; i < 10; i++) {
          const a = Math.random() * Math.PI * 2, r = 10 * (1 - k) + 1.2, up = (Math.random() - 0.3) * 3;
          pix(dim, { x: c.x + Math.cos(a) * r, y: c.y + up, z: c.z + Math.sin(a) * r }, { color: i % 2 ? STAR_GOLD : STAR_WHITE, size: 0.18, life: 0.35, speed: -6 * (1 - k) - 1 });
        }
        glow(dim, c, { color: i2c(k), size: 0.6 + 2.2 * k, life: 0.25 });
        pixRing(dim, { x: c.x, y: p.location.y + 0.2, z: c.z }, 1 + 3 * k, 20, t * 0.4, STAR_BLUE, 0.2, 0.3);
        if (t % 10 === 0) shake(p, 0.05 + 0.12 * k, 0.12);
        if (t >= charge) {
          system.clearRun(h);
          sfx(dim, "sh.supernova_boom", p.location, 2, 1);
          shake(p, 0.5, 0.5);
          glow(dim, c, { color: STAR_WHITE, size: 6, life: 0.5 });
          burst(dim, c, 70, STAR_GOLD, 9, 0.34);
          burst(dim, c, 50, STAR_WHITE, 7, 0.3);
          for (let i = 0; i < 60; i++) pix(dim, c, { color: i % 3 ? STAR_BLUE : STAR_GOLD, size: 0.26, life: 1.4, speed: 10, rise: -1.5 });
          for (let y = 0; y < 14; y += 1.2) pix(dim, { x: c.x, y: c.y + y, z: c.z }, { color: STAR_WHITE, size: 0.5, life: 0.8, rise: 1 });
          waveFx(dim, p.location, 16, 0, 16);
          later(3, () => waveFx(dim, p.location, 13, 4, 14));
          later(6, () => waveFx(dim, p.location, 10, 2, 12));
          for (const e of enemiesNear(dim, p.location, 14, p.id)) {
            hurtS(e, 28, p);
            pushAway(p.location, e, 2.2, 0.8);
            try { e.addEffect("blindness", 60, { amplifier: 0, showParticles: false }); } catch (err) { /* */ }
          }
          effect(p, "weakness", 120, 1);
          notify(p, "§9انفجرت النجمة. تعبت لست ثواني", 80);
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
const KATANA_MODES = [
  { name: "الشطر", lv: 1, cd: 30, desc: "شطرة وحدة قوية تشق كل اللي قدامك" },
  { name: "الضربة المزدوجة", lv: 1, cd: 60, desc: "قطعتين على شكل X على العدو اللي قدامك" },
  { name: "الاختراق", lv: 1, cd: 100, desc: "تخترق جسم العدو وتطلع من ظهره وتشطر كل اللي بالطريق" },
  { name: "خطوة الظل", lv: 2, cd: 80, desc: "تختفي وتظهر خلف العدو وتشطره من ظهره" },
  { name: "موجة الهاوية", lv: 3, cd: 110, desc: "هلال بنفسجي يطير قدامك ويشق كل من يعترضه" },
  { name: "عاصفة الشفرات", lv: 4, cd: 200, desc: "شفرات تدور حولك وتسحب وتقطع كل الأعداء القريبين" },
  { name: "إعدام الهاوية", lv: 5, cd: 300, desc: "ضربة هائلة: تنهي أي عدو صحته أقل من 35% (البوسات مستثنين)" },
];
const KATANA_PURPLE = [0.7, 0.35, 1.0];
const KAT_PALETTE = [[0.7, 0.35, 1.0], [0.45, 0.35, 1.0], [0.95, 0.45, 1.0], [0.3, 0.5, 1.0], [1, 1, 1]];

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
    const m = KATANA_MODES.filter((x) => x.lv === k.lv);
    say(p, `§5[الكاتانا] §fتطورت للمستوى §d${k.lv}§f، ضررها زاد.` + (m.length ? ` §aمهارة جديدة: ${m.map((x) => x.name).join("، ")}§f. بدّل بالسنيك.` : ""));
    notify(p, `§5الكاتانا ليفل ${k.lv}!`, 80);
  }
  if (k.lv >= KAT_MAX) k.xp = 0;
  saveKat(p, k);
}
function katanaMode(p) {
  const v = p.getDynamicProperty("sh_kmode");
  if (typeof v !== "number" || v < 0 || v >= KATANA_MODES.length) return 0;
  return KATANA_MODES[v].lv <= katLv(p) ? v : 0;
}

// موقع النصل التقريبي بيد اللاعب (للهالة)
function bladePoint(p, u) {
  const d = flatDir(p), r = katanaRight(d);
  return { x: p.location.x + d.x * (0.5 + u * 0.55) + r.x * 0.38, y: p.location.y + 0.9 + u * 1.35, z: p.location.z + d.z * (0.5 + u * 0.55) + r.z * 0.38 };
}
// هالة شظايا بكسل بنفسجية حول النصل (مثل صورة "مهارة فعالة")
function katanaAura(p, ticks, strong) {
  let t = 0;
  const h = system.runInterval(() => {
    try {
      t += 2;
      if (!valid(p) || t > ticks) { system.clearRun(h); return; }
      const n = strong ? 6 : 3;
      for (let i = 0; i < n; i++) {
        const b = bladePoint(p, Math.random());
        pix(p.dimension, { x: b.x + (Math.random() - 0.5) * 0.5, y: b.y + (Math.random() - 0.5) * 0.3, z: b.z + (Math.random() - 0.5) * 0.5 },
          { color: KAT_PALETTE[Math.floor(Math.random() * KAT_PALETTE.length)], size: 0.12 + Math.random() * 0.1, life: 0.5 + Math.random() * 0.5, speed: 0.5, rise: 0.6 });
      }
      if (strong) glow(p.dimension, bladePoint(p, 0.6), { color: KATANA_PURPLE, size: 0.6, life: 0.3 });
    } catch (e) { system.clearRun(h); }
  }, 2);
}
// هالة هادئة دائمة وانت ماسكها (تقوى مع الليفل)
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      const held = inv(p).getItem(p.selectedSlotIndex);
      if (!held || held.typeId !== KATANA) continue;
      const lv = katLv(p);
      for (let i = 0; i < 1 + (lv >= 3 ? 1 : 0); i++) {
        const b = bladePoint(p, 0.2 + Math.random() * 0.8);
        pix(p.dimension, b, { color: KAT_PALETTE[Math.floor(Math.random() * 3)], size: 0.1, life: 0.9, speed: 0.2, rise: 0.4 });
      }
    } catch (e) { /* */ }
  }
}, 8);

// السنيك يبدل المهارة (يتفحص كل 2 تك: ضغطة جلوس جديدة وانت ماسك الكاتانا)
const sneakPrev = new Map();
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      const sn = !!p.isSneaking, was = sneakPrev.get(p.id) || false;
      sneakPrev.set(p.id, sn);
      if (!sn || was) continue;
      const held = inv(p).getItem(p.selectedSlotIndex);
      if (held && held.typeId === KATANA) katanaCycle(p);
    } catch (e) { /* */ }
  }
}, 2);
world.afterEvents.playerLeave.subscribe((ev) => { sneakPrev.delete(ev.playerId); });

function katanaCycle(p) {
  const lv = katLv(p), cur = katanaMode(p);
  let next = cur;
  for (let i = 1; i <= KATANA_MODES.length; i++) {
    const idx = (cur + i) % KATANA_MODES.length;
    if (KATANA_MODES[idx].lv <= lv) { next = idx; break; }
  }
  if (next === cur) { notify(p, "§7ما عندك غير مهارة وحدة مفتوحة. طور الكاتانا بقتل الوحوش", 50); return; }
  p.setDynamicProperty("sh_kmode", next);
  sfxPlayer(p, "sh.select", 0.8, 1.1 + next * 0.1);
  notify(p, `§5${KATANA_MODES[next].name}§r: ${KATANA_MODES[next].desc}`, 70);
  katanaAura(p, 10, false);
}

// خط قطع (جزيئات) يمر بنقطة c بزاوية angle داخل مستوى (right, up) ويرسم تدريجيا
function katanaSlash(dim, c, right, angleDeg, len = 3.4, ticks = 3) {
  const a = (angleDeg * Math.PI) / 180;
  const dx = right.x * Math.cos(a), dz = right.z * Math.cos(a), dy = Math.sin(a);
  const steps = 14;
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps - 0.5) * len;
    const loc = { x: c.x + dx * t, y: c.y + dy * t, z: c.z + dz * t };
    system.runTimeout(() => {
      glow(dim, loc, { color: [1, 1, 1], size: 0.34, life: 0.25 });
      glow(dim, loc, { color: KATANA_PURPLE, size: 0.5, life: 0.55 });
      pix(dim, loc, { color: KAT_PALETTE[i % KAT_PALETTE.length], size: 0.16, life: 0.7, speed: 1.2, rise: 0.3 });
    }, Math.floor((i / steps) * ticks));
  }
}
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
function katanaUse(p) {
  const mode = katanaMode(p);
  const key = `${p.id}:katana${mode}`;
  const now = system.currentTick;
  if (now < (weaponCd.get(key) ?? 0)) { notify(p, `§7${KATANA_MODES[mode].name}: انتظر ${(((weaponCd.get(key) ?? 0) - now) / 20).toFixed(1)}ث`, 15); return; }
  let ok = false;
  try { ok = KATANA_FN[mode](p); } catch (e) { ok = false; }
  if (ok) katanaAura(p, 30, true);
  weaponCd.set(key, now + (ok ? KATANA_MODES[mode].cd : 6));
}
function katanaRight(d) { return { x: -d.z, z: d.x }; }
const KATANA_FN = [
  // 0: الشطر — شطرة وحدة على كل أعداء المخروط الأمامي
  (p) => {
    const d = flatDir(p), r = katanaRight(d);
    const c = { x: p.location.x + d.x * 2, y: p.location.y + 1.2, z: p.location.z + d.z * 2 };
    katanaSlash(p.dimension, c, r, 35, 4.2, 3);
    sfx(p.dimension, "sh.dagger_hit", p.location, 1.1, 0.6);
    shake(p, 0.1, 0.12);
    for (const e of enemiesNear(p.dimension, p.location, 5.2, p.id)) {
      const vx = e.location.x - p.location.x, vz = e.location.z - p.location.z, l = Math.hypot(vx, vz) || 1;
      if ((vx / l) * d.x + (vz / l) * d.z < 0.45) continue;
      hurt(e, kd(p, 11), p); pushAway(p.location, e, 0.5, 0.15);
      burst(e.dimension, headPos(e), 12, KATANA_PURPLE, 3, 0.22);
    }
    return true;
  },
  // 1: الضربة المزدوجة — X على العدو
  (p) => {
    const t = katanaTarget(p, 6);
    if (!t) { notify(p, "§cما كو عدو قدامك", 30); return false; }
    const dx = t.location.x - p.location.x, dz = t.location.z - p.location.z, l = Math.hypot(dx, dz) || 1;
    const r = katanaRight({ x: dx / l, z: dz / l });
    const c = { x: t.location.x - (dx / l) * 0.5, y: t.location.y + 1.0, z: t.location.z - (dz / l) * 0.5 };
    try { t.addEffect("slowness", 25, { amplifier: 3, showParticles: false }); } catch (e) { /* */ }
    katanaSlash(p.dimension, c, r, 45, 3.2, 3);
    sfx(p.dimension, "sh.dagger_hit", t.location, 1.1, 0.8);
    system.runTimeout(() => { if (valid(t)) hurt(t, kd(p, 7), p); }, 1);
    system.runTimeout(() => {
      if (!valid(t)) return;
      katanaSlash(p.dimension, c, r, -45, 3.2, 3);
      sfx(p.dimension, "sh.dagger_hit", t.location, 1.2, 1.1);
      hurt(t, kd(p, 8), p);
      burst(t.dimension, headPos(t), 22, KATANA_PURPLE, 3.5, 0.26);
      glow(t.dimension, c, { color: [1, 1, 1], size: 0.9, life: 0.4 });
    }, 6);
    shake(p, 0.12, 0.15);
    return true;
  },
  // 2: الاختراق — تعبر جسم العدو وتطلع من ظهره
  (p) => {
    const t = katanaTarget(p, 9);
    if (!t) { notify(p, "§cما كو عدو قدامك", 30); return false; }
    const from = { ...p.location };
    const dx = t.location.x - from.x, dz = t.location.z - from.z, l = Math.hypot(dx, dz) || 1;
    const ux = dx / l, uz = dz / l;
    let to;
    for (const k of [2.6, 2.0, 1.4]) {
      const dest = { x: t.location.x + ux * k, y: t.location.y, z: t.location.z + uz * k };
      if (safeTeleport(p, dest, { x: dest.x + ux * 3, y: dest.y, z: dest.z + uz * 3 })) { to = dest; break; }
    }
    const end = to || { x: t.location.x + ux * 0.5, y: t.location.y, z: t.location.z + uz * 0.5 };
    for (let i = 0; i <= 20; i++) {
      const k = i / 20;
      const loc = { x: from.x + (end.x - from.x) * k, y: from.y + 1.0, z: from.z + (end.z - from.z) * k };
      glow(p.dimension, loc, { color: [1, 1, 1], size: 0.4, life: 0.3 });
      glow(p.dimension, loc, { color: KATANA_PURPLE, size: 0.55, life: 0.8 });
      pix(p.dimension, loc, { color: KAT_PALETTE[i % KAT_PALETTE.length], size: 0.16, life: 0.9, speed: 1, rise: 0.4 });
    }
    const seg = { x: end.x - from.x, z: end.z - from.z }, sl = Math.hypot(seg.x, seg.z) || 1;
    const seen = new Set();
    for (const e of enemiesNear(p.dimension, from, sl + 4, p.id)) {
      if (seen.has(e.id)) continue;
      seen.add(e.id);
      const vx = e.location.x - from.x, vz = e.location.z - from.z;
      const proj = (vx * seg.x + vz * seg.z) / sl;
      if (proj < -0.5 || proj > sl + 0.5) continue;
      if (Math.abs(vx * seg.z - vz * seg.x) / sl > 1.4) continue;
      hurt(e, kd(p, 13), p);
      burst(e.dimension, headPos(e), 20, KATANA_PURPLE, 3.5, 0.26);
      glow(e.dimension, headPos(e), { color: [1, 1, 1], size: 1.0, life: 0.4 });
    }
    try { p.addEffect("resistance", 20, { amplifier: 4, showParticles: false }); } catch (e) { /* */ }
    spawnFx(p.dimension, "circle", from, 1, 1.4, 14);
    sfx(p.dimension, "sh.fold", end, 1.1, 1.5);
    shake(p, 0.2, 0.2);
    return true;
  },
  // 3: خطوة الظل — تظهر خلف العدو وتشطره
  (p) => {
    const t = katanaTarget(p, 10);
    if (!t) { notify(p, "§cما كو عدو قدامك", 30); return false; }
    const from = { ...p.location };
    const dx = t.location.x - from.x, dz = t.location.z - from.z, l = Math.hypot(dx, dz) || 1;
    const ux = dx / l, uz = dz / l;
    let to;
    for (const k of [1.6, 1.2, 2.2]) {
      const dest = { x: t.location.x + ux * k, y: t.location.y, z: t.location.z + uz * k };
      if (safeTeleport(p, dest, { x: t.location.x, y: dest.y, z: t.location.z })) { to = dest; break; }
    }
    if (!to) { notify(p, "§cما كو مكان خلف العدو", 30); return false; }
    const dim = p.dimension;
    for (let i = 0; i < 26; i++) pix(dim, { x: from.x + (Math.random() - 0.5) * 0.8, y: from.y + Math.random() * 1.9, z: from.z + (Math.random() - 0.5) * 0.8 }, { color: KAT_PALETTE[i % KAT_PALETTE.length], size: 0.2, life: 0.8, speed: 1.5, rise: 0.5 });
    pixLine(dim, { x: from.x, y: from.y + 1, z: from.z }, { x: to.x, y: to.y + 1, z: to.z }, KATANA_PURPLE, 18, 0.16, 0.6);
    const c = { x: t.location.x, y: t.location.y + 1.0, z: t.location.z };
    katanaSlash(dim, c, katanaRight({ x: -ux, z: -uz }), 20, 3.2, 3);
    later(2, () => {
      if (!valid(t)) return;
      hurt(t, kd(p, 12), p);
      burst(dim, headPos(t), 20, KATANA_PURPLE, 3.5, 0.25);
      glow(dim, c, { color: [1, 1, 1], size: 0.9, life: 0.35 });
    });
    effect(p, "resistance", 20, 3);
    sfx(dim, "sh.kat_step", to, 1.1, 1);
    shake(p, 0.1, 0.12);
    return true;
  },
  // 4: موجة الهاوية — هلال يطير للأمام
  (p) => {
    const d = flatDir(p), r = katanaRight(d), dim = p.dimension;
    const start = { x: p.location.x + d.x * 1.2, y: p.location.y + 1.2, z: p.location.z + d.z * 1.2 };
    const hit = new Set();
    sfx(dim, "sh.kat_wave", p.location, 1.2, 1);
    shake(p, 0.12, 0.12);
    let dist = 0;
    const h = system.runInterval(() => {
      try {
        dist += 1.7;
        const c = { x: start.x + d.x * dist, y: start.y, z: start.z + d.z * dist };
        let blocked = false;
        try { const b = dim.getBlock(c); blocked = !!(b && !b.isAir && !b.isLiquid); } catch (e) { /* */ }
        if (dist > 22 || blocked) {
          system.clearRun(h);
          burst(dim, c, 14, KATANA_PURPLE, 3, 0.22);
          return;
        }
        for (let i = -7; i <= 7; i++) {
          const s = i * 0.3, back = Math.abs(s) * 0.5;
          const loc = { x: c.x + r.x * s - d.x * back, y: c.y + (Math.abs(i) < 2 ? 0.1 : 0), z: c.z + r.z * s - d.z * back };
          glow(dim, loc, { color: [1, 1, 1], size: 0.28, life: 0.2 });
          pix(dim, loc, { color: KAT_PALETTE[Math.abs(i) % KAT_PALETTE.length], size: 0.18, life: 0.6, speed: 0.5, rise: 0.3 });
        }
        for (const e of enemiesNear(dim, c, 2.4, p.id)) {
          if (hit.has(e.id)) continue;
          hit.add(e.id);
          hurt(e, kd(p, 10), p);
          pushAway(p.location, e, 0.7, 0.2);
          burst(dim, headPos(e), 14, KATANA_PURPLE, 3, 0.22);
        }
      } catch (err) { system.clearRun(h); }
    }, 1);
    return true;
  },
  // 5: عاصفة الشفرات — شفرات تدور وتسحب وتقطع
  (p) => {
    const dim = p.dimension;
    sfx(dim, "sh.kat_storm", p.location, 1.2, 1);
    effect(p, "resistance", 30, 2);
    spawnFx(dim, "circle", p.location, 1, 3, 28);
    let t = 0;
    const h = system.runInterval(() => {
      try {
        t += 2;
        if (!valid(p) || t > 26) { system.clearRun(h); return; }
        const c = { x: p.location.x, y: p.location.y + 1.0, z: p.location.z };
        const rad = 1.5 + t * 0.15;
        for (let b = 0; b < 4; b++) {
          const a = t * 0.55 + (b * Math.PI) / 2;
          for (let k = 0; k < 5; k++) {
            const rr = rad * (0.5 + k * 0.13), aa = a - k * 0.12;
            const loc = { x: c.x + Math.cos(aa) * rr, y: c.y + Math.sin(t * 0.3 + b) * 0.3, z: c.z + Math.sin(aa) * rr };
            glow(dim, loc, { color: [1, 1, 1], size: 0.22, life: 0.2 });
            pix(dim, loc, { color: KAT_PALETTE[(b + k) % KAT_PALETTE.length], size: 0.16, life: 0.5, speed: 0.4 });
          }
        }
        if (t % 6 === 0) {
          for (const e of enemiesNear(dim, p.location, 5.2, p.id)) {
            hurt(e, kd(p, 6), p);
            pullTo(p.location, e, 0.35, 0.1);
            burst(dim, headPos(e), 8, KATANA_PURPLE, 2.5, 0.2);
          }
          shake(p, 0.08, 0.1);
        }
      } catch (err) { system.clearRun(h); }
    }, 2);
    return true;
  },
  // 6: إعدام الهاوية — تحضير ثم ضربة تنهي الضعفاء
  (p) => {
    const dim = p.dimension, d = flatDir(p), r = katanaRight(d);
    sfx(dim, "sh.kat_exec", p.location, 1.3, 1);
    katanaAura(p, 16, true);
    for (let i = 0; i < 4; i++) later(i * 3, () => pixRing(dim, { x: p.location.x, y: p.location.y + 0.2, z: p.location.z }, 4 - i, 20, i, KATANA_PURPLE, 0.18, 0.4));
    later(14, () => {
      const c = { x: p.location.x + d.x * 3, y: p.location.y + 1.3, z: p.location.z + d.z * 3 };
      katanaSlash(dim, c, r, 40, 6.5, 3);
      katanaSlash(dim, c, r, -40, 6.5, 3);
      katanaSlash(dim, c, r, 90, 6, 3);
      spawnFx(dim, "circle", p.location, 1, 3.4, 16);
      waveFx(dim, p.location, 8, 1, 12);
      glow(dim, c, { color: [1, 1, 1], size: 2.4, life: 0.4 });
      shake(p, 0.3, 0.25);
      for (const e of enemiesNear(dim, p.location, 7, p.id)) {
        const vx = e.location.x - p.location.x, vz = e.location.z - p.location.z, l = Math.hypot(vx, vz) || 1;
        if ((vx / l) * d.x + (vz / l) * d.z < 0.3) continue;
        let low = false;
        try { const hp = e.getComponent("minecraft:health"); low = hp.currentValue <= hp.effectiveMax * 0.35; } catch (err) { /* */ }
        if (low && !BOSS_TYPES.has(e.typeId)) { hurt(e, 9999, p); burst(dim, headPos(e), 40, KATANA_PURPLE, 5, 0.3); notify(p, "§5إعدام!", 25); }
        else hurt(e, kd(p, 18), p);
        pushAway(p.location, e, 0.9, 0.3);
        glow(dim, headPos(e), { color: [1, 1, 1], size: 1.2, life: 0.35 });
      }
    });
    return true;
  },
];

const cooldowns = new Map();

function useSkill(p, skill) {
  const st = getState(p);
  if (st.power !== skill.power || !isSkillUnlocked(st, skill)) {
    notify(p, "§cهاي المهارة مو متاحة لك", 40);
    return;
  }
  const key = `${p.id}:${skill.id}`;
  const ready = cooldowns.get(key) ?? 0;
  const now = system.currentTick;
  if (now < ready) {
    notify(p, `§7${skill.name}: انتظر ${((ready - now) / 20).toFixed(1)}ث`, 15);
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
    if (id === KATANA) { katanaUse(p); return; }
    if (WEAPONS[id] && WEAPONS[id].active) { weaponActive(p, id); return; }
    if (SCROLLS[id]) { useScroll(p, id); return; }
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
      if (!st.power) openPowerMenu(p);
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
    if (w.special === "combo") {
      const c = comboMap.get(p.id) || { n: 0, t: -999 };
      c.n = system.currentTick - c.t < 60 ? c.n + 1 : 1;
      c.t = system.currentTick;
      if (c.n >= 3) {
        extra += 6; c.n = 0;
        ring(target.dimension, { x: target.location.x, y: target.location.y + 0.8, z: target.location.z }, 1.2, 20, 0, COLORS.gold, 0.22);
        burst(target.dimension, headPos(target), 18, COLORS.gold, 3.5, 0.2);
        sfx(target.dimension, "sh.dagger_hit", target.location, 1.1, 1.5);
        notify(p, "§6ضربة الفجر!", 20);
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
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    try {
      const st = getState(p);
      if (p.dimension.id !== "minecraft:overworld") continue;
      const near = p.dimension.getEntities({ location: p.location, maxDistance: 64, families: ["sh_rank0"] });
      if (near.length >= 2) continue;
      if (Math.random() < 0.5) continue; // ظهور بطيء وطبيعي
      const id = RANK0_TYPES[Math.floor(Math.random() * RANK0_TYPES.length)];
      spawnOnSurface(p.dimension, id, p.location.x, p.location.z, 10, 26, 44);
    } catch (e) { /* */ }
  }
}, 2400);




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
    const o = tp ? { x: tp.location.x, y: tp.location.y + 1.2, z: tp.location.z } : { x: e.location.x + fx * 1.3, y: e.location.y + 1, z: e.location.z + fz * 1.3 };
    slashFx(dim, o, fx, fz, idx % 2 === 1);
    sfx(dim, "sh.imp_pounce", e.location, 0.8, 1.2 + idx * 0.15);
  } else {
    for (let i = 0; i <= 22; i++) {
      const a = Math.atan2(fz, fx) - 1.2 + (i / 22) * 2.4;
      for (const r of [1.6, 2.2, 2.8]) glow(dim, { x: e.location.x + Math.cos(a) * r, y: e.location.y + 1.3, z: e.location.z + Math.sin(a) * r }, { color: [1, 1, 1], size: 0.16, life: 0.4 });
    }
    burst(dim, { x: e.location.x + fx * 1.8, y: e.location.y + 0.2, z: e.location.z + fz * 1.8 }, 10, [0.6, 0.62, 0.58], 2, 0.25);
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
  try { pl.applyDamage(amount, { cause: EntityDamageCause.entityAttack, damagingEntity: by }); } catch (err) { /* */ }
}

function setMState(e, v) { try { e.setProperty("sh:state", v); } catch (err) { /* */ } }


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
            const np = nearestPlayer(e, cfg.range[1]);
            const cl = CLOSE[type];
            if (cl && np && np.d < cl.trig && Math.random() < cl.chance) {
              st.phase = 3; st.t = 0; st.hit = 0; st.target = np.p;
              setMState(e, 3);
              sfx(dim, type === "sh:ember_imp" ? "sh.imp_windup" : "sh.guard_windup", e.location, 0.8, 1.2);
              continue;
            }
            if (!np || np.d < cfg.range[0]) { st.cd = 10; continue; }
            st.phase = 1; st.t = 0; st.target = np.p;
            setMState(e, 1);
            sfx(dim, type === "sh:ember_imp" ? "sh.imp_windup" : "sh.guard_windup", e.location, 1);
            continue;
          }
          if (st.phase === 1) {
            st.t += 4;
            if (type === "sh:ember_imp") {
              for (let i = 0; i < 3; i++) glow(dim, { x: e.location.x + (Math.random() - 0.5) * 0.8, y: e.location.y + 0.1, z: e.location.z + (Math.random() - 0.5) * 0.8 }, { color: COLORS.orange, size: 0.2, life: 0.5, rise: 1.5 });
              if (valid(st.target)) {
                // خط تحذير باتجاه الهدف
                const tx = st.target.location.x - e.location.x, tz = st.target.location.z - e.location.z, tl = Math.hypot(tx, tz) || 1;
                for (let k = 1; k <= 6; k++) glow(dim, { x: e.location.x + (tx / tl) * k * 0.7, y: e.location.y + 0.15, z: e.location.z + (tz / tl) * k * 0.7 }, { color: COLORS.red, size: 0.12, life: 0.3 });
              }
            } else {
              ring(dim, e.location, 4 * Math.min(1, st.t / cfg.windup), 26, st.t * 0.1, COLORS.teal, 0.24);
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
                ring(dim, e.location, 1.5, 20, 0, COLORS.teal, 0.3);
                ring(dim, e.location, 3, 30, 0.5, COLORS.green, 0.3);
                ring(dim, e.location, 4.5, 36, 1, COLORS.teal, 0.28);
                burst(dim, e.location, 24, [0.6, 0.62, 0.58], 4, 0.3);
                burst(dim, e.location, 12, COLORS.teal, 3, 0.2);
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

// الرامي: وضعية السحب لما يكون لاعب قريب
system.runInterval(() => {
  for (const dimId of ["overworld", "nether", "the_end"]) {
    let dim;
    try { dim = world.getDimension(dimId); } catch (e) { continue; }
    let list = [];
    try { list = dim.getEntities({ type: "sh:training_archer" }); } catch (e) { continue; }
    for (const e of list) {
      try {
        const near = dim.getPlayers({ location: e.location, maxDistance: 18 }).length > 0;
        setMState(e, near ? 1 : 0);
      } catch (err) { /* */ }
    }
  }
}, 10);


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
            // وميض عند إطلاق السهم
            burst(dim, L, 10, [0.62, 0.35, 1], 2.5, 0.16);
            ring(dim, L, 0.6, 10, 0, [0.62, 0.35, 1], 0.15);
            sfx(dim, "sh.imp_windup", L, 0.5, 1.8);
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

try { setupStructures(); } catch (e) { /* */ }




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
            const np = nearestPlayer(e, hound ? 14 : 5);
            if (!np) { st.cd = 10; continue; }
            if (np.d < 2.4) {
              st.phase = 3; st.t = 0; st.hit = 0; st.target = np.p; setMState(e, 3);
              sfx(dim, "sh.imp_windup", L, 0.7, hound ? 0.7 : 1.4);
            } else if (hound ? np.d > 4 : np.d < 3.8) {
              st.phase = 1; st.t = 0; st.target = np.p; setMState(e, 1);
              sfx(dim, "sh.imp_windup", L, 0.9, hound ? 0.6 : 1.0);
            } else st.cd = 8;
            continue;
          }
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
                  notify(pl, "§5العواء يبطئك!", 40);
                  shake(pl, 0.12, 0.4);
                }
              } else if (tp) {
                // ضربة الذيل: خط أخضر من الإبرة للهدف + تسمم
                try { e.applyImpulse({ x: (tp.location.x - L.x) * 0.12, y: 0.2, z: (tp.location.z - L.z) * 0.12 }); } catch (err) { /* */ }
                const hx = L.x, hy = L.y + 1.9, hz = L.z;
                line(dim, { x: hx, y: hy, z: hz }, headPos(tp), VENOM);
                ring(dim, { x: tp.location.x, y: tp.location.y + 1, z: tp.location.z }, 0.8, 14, 0, VENOM, 0.2);
                burst(dim, headPos(tp), 18, VENOM, 3, 0.2);
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
              if (hound) slashFx(dim, o, fx, fz, st.hit % 2 === 0);
              else { ring(dim, o, 0.8, 14, 0, VENOM, 0.16); burst(dim, o, 10, [0.8, 0.6, 0.3], 2.5, 0.2); }
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
  { key: "shrine", name: "ضريح السيف المظلم" },
  { key: "palace", name: "قصر الغروب" },
  { key: "ruins", name: "خرائب المعبد" },
  { key: "village", name: "قرية الساكورا" },
  { key: "trainer", name: "المدرب" },
  { key: "nearest", name: "الأقرب (أي وجهة)" },
];
const COMPASS_NAMES = { village: "قرية الساكورا", palace: "قصر الغروب", ruins: "خرائب المعبد", shrine: "ضريح السيف المظلم" };
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
      if (d < bd) { bd = d; best = { x: s.x, z: s.z, name: COMPASS_NAMES[s.type] || "بناية" }; }
    }
  }
  if (key === "trainer" || key === "nearest") {
    const t = trainerPos(p);
    if (t && dist(t) < bd) best = { x: t.x, z: t.z, name: "المدرب" };
  }
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
  if (!tg) { notify(p, "§7هالوجهة ما انكشفت بعد. تحرك بالعالم وجرب مرة ثانية", 60); return; }
  const dx = tg.x - p.location.x, dz = tg.z - p.location.z, dist = Math.round(Math.hypot(dx, dz));
  const dirs = ["شرق", "جنوب شرق", "جنوب", "جنوب غرب", "غرب", "شمال غرب", "شمال", "شمال شرق"];
  const dir = dirs[((Math.round((Math.atan2(dz, dx) * 180) / Math.PI / 45) % 8) + 8) % 8];
  notify(p, `§6${tg.name}§r: ${dist} بلوكة باتجاه ال${dir}`, 100);
  const l = Math.hypot(dx, dz) || 1;
  for (let i = 1; i <= 10; i++) glow(p.dimension, { x: p.location.x + (dx / l) * i * 1.2, y: p.location.y + 1.2, z: p.location.z + (dz / l) * i * 1.2 }, { color: COLORS.gold, size: 0.2, life: 1.2, rise: 0.2 });
  sfxPlayer(p, "sh.compass", 0.8, 1);
}
async function openCompassMenu(p) {
  const cur = compassKey(p);
  const form = new ActionFormData().title("بوصلة المستكشف").body("§7اختر الوجهة اللي تريد البوصلة تدلك عليها. تنعرض أثناء ما تمسكها أعلى الشاشة.");
  for (const t of COMPASS_TARGETS) {
    const f = compassFind(p, t.key);
    const d = f ? `§a${Math.round(Math.hypot(f.x - p.location.x, f.z - p.location.z))} بلوكة` : "§8ما انكشفت بعد";
    form.button(`${t.key === cur ? "§6✔ " : "§f"}${t.name}\n${d}`);
  }
  const r = await showForm(p, form);
  if (r.canceled) return;
  const pick = COMPASS_TARGETS[r.selection];
  if (!pick) return;
  p.setDynamicProperty("sh_ctarget", pick.key);
  sfxPlayer(p, "sh.compass", 0.8, 1.2);
  if (compassFind(p, pick.key)) compassPulse(p);
  else notify(p, `§7${pick.name}: ما انكشفت بعد. البنايات تظهر وانت تتحرك بالعالم`, 80);
}
function useCompass(p) {
  if (p.isSneaking) compassPulse(p);
  else openCompassMenu(p);
}


// ───────────────────────── رؤية الرتب: رتبة الوحش فوق راسه بلون حسب خطره عليك ─────────────────────────
const MON_NAMES = { "sh:training_archer": "رامي التدريب", "sh:ember_imp": "عفريت الرماد", "sh:rust_guard": "حارس الصخر", "sh:shadow_hound": "ذئب الظل", "sh:sand_scorpion": "عقرب الرمل" };
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
          let near, nd = 48;
          for (const p of players) {
            if (p.dimension.id !== e.dimension.id) continue;
            const d = Math.hypot(p.location.x - e.location.x, p.location.z - e.location.z);
            if (d < nd) { nd = d; near = p; }
          }
          if (!near) continue;
          const st = getState(near);
          let col = "§f", tag = "";
          const rk = info.rank;
          if (rk < 0) { col = "§7"; tag = "تدريب"; }
          else {
            const diff = rk - st.rank;
            tag = RANKS[rk];
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
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  try {
    const p = ev.sourceEntity;
    if (!p || p.typeId !== "minecraft:player") return;
    const msg = (ev.message || "").trim();
    if (ev.id === "sh:power") {
      if (!POWERS[msg]) { say(p, `§cاستعمل: ${POWER_KEYS.join(" ")}`); return; }
      grantPower(p, msg);
    } else if (ev.id === "sh:unlock") {
      const st = getState(p);
      if (!st.power) { say(p, "§cما عندك قدرة"); return; }
      st.training[st.power] = { status: "done", kills: TRAIN_NEED };
      st.plevel = rarityOf(st.power).maxLv;
      saveState(p, st);
      say(p, "§aانفتحت كل المهارات. افتح كتاب التطور.");
    } else if (ev.id === "sh:katlv") {
      const n = Math.min(KAT_MAX, Math.max(1, parseInt(msg, 10) || 1));
      saveKat(p, { lv: n, xp: 0 });
      say(p, `§aليفل الكاتانا: ${n}`);
    } else if (ev.id === "sh:cdreset") {
      cooldowns.clear(); weaponCd.clear();
      say(p, "§aتصفّر الكولداون");
    }
  } catch (e) { /* */ }
});
