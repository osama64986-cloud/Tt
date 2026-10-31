// منطق الرتب والـ XP — بدون أي اعتماد على ماينكرافت (يتفحص لحاله)

export const RANKS = ["مبتدئ", "متدرب", "محارب", "نخبة", "قائد", "أسطورة", "السيد"];
export const LEVELS_PER_RANK = 15;
// من هاي الرتبة (index) وطالع: قتل وحش أقوى ما يرقيك بالقفزة
export const HARD_RANK_FROM = 2;

export function xpNeeded(level) {
  return 14 + level * 5;
}

// تقدم اللاعب نحو الرتبة الجاية: frac من 0 إلى 1 (يشمل خبرة الليفل الحالي)، وcur/need بالليفلات
export function rankProgress(st) {
  if (st.rank >= RANKS.length - 1) return { frac: 1, cur: LEVELS_PER_RANK, need: LEVELS_PER_RANK, max: true };
  const cur = Math.max(0, st.level - st.rank * LEVELS_PER_RANK);
  const frac = Math.min(1, (cur + st.xp / xpNeeded(st.level)) / LEVELS_PER_RANK);
  return { frac, cur: Math.min(cur, LEVELS_PER_RANK), need: LEVELS_PER_RANK, max: false };
}

// زيادة الصحة مع الرتبة: كل رتبة +4 نقاط صحة (قلبين) عبر تأثير health_boost
export function rankHealthBonus(rank) {
  return Math.max(0, rank) * 4;
}

export function defaultState() {
  return { power: null, level: 1, xp: 0, rank: 0, training: {}, gotBook: false, skills: {}, plevel: 1, pxp: 0 };
}

// ترقية الرتبة بالليفل: كل 30 ليفل رتبة
export function checkPromotion(st) {
  const ups = [];
  while (st.rank < RANKS.length - 1 && st.level >= (st.rank + 1) * LEVELS_PER_RANK) {
    st.rank++;
    ups.push({ type: "rank", rank: st.rank });
  }
  return ups;
}

// مستوى المهارة نفسها (غير ليفل اللاعب): يزيد من استعمالها بقتل الأعداء
export const SKILL_UNLOCK_LEVEL = 3;
export function skillXpNeeded(level) {
  return 30 + level * 20;
}
export function skillLevel(st, id) {
  return (st.skills && st.skills[id] && st.skills[id].lvl) || 1;
}
export function addSkillXp(st, id, amount) {
  if (!st.skills) st.skills = {};
  const sk = st.skills[id] || (st.skills[id] = { lvl: 1, xp: 0 });
  const ups = [];
  sk.xp += amount;
  while (sk.xp >= skillXpNeeded(sk.lvl)) {
    sk.xp -= skillXpNeeded(sk.lvl);
    sk.lvl++;
    ups.push({ type: "skill", id, level: sk.lvl });
  }
  return ups;
}

export function addXp(st, amount) {
  const ups = [];
  st.xp += amount;
  while (st.xp >= xpNeeded(st.level)) {
    st.xp -= xpNeeded(st.level);
    st.level++;
    ups.push({ type: "level", level: st.level });
  }
  ups.push(...checkPromotion(st));
  return ups;
}

// monster: { rank: -1 للتدريب أو 0..6, xp }
export function monsterReward(st, monster) {
  const base = Array.isArray(monster.xp)
    ? monster.xp[0] + Math.floor(Math.random() * (monster.xp[1] - monster.xp[0] + 1))
    : monster.xp;
  monster = { ...monster, xp: base };
  const res = { xp: base, jumped: false, ups: [] };
  if (monster.rank >= 0) {
    const diff = monster.rank - st.rank;
    if (diff >= 2) {
      if (st.rank < HARD_RANK_FROM && st.rank < RANKS.length - 1) {
        st.rank++;
        res.jumped = true;
        res.ups.push({ type: "rank", rank: st.rank });
        res.xp = Math.round(monster.xp * 1.5);
      } else {
        // رتبة عالية: ياخذ XP أكثر بس ما يرتقي بالقفزة
        res.xp = monster.xp * 3;
      }
    } else if (diff <= -3) {
      res.xp = Math.max(1, Math.round(monster.xp * 0.5));
    }
  }
  res.ups.push(...addXp(st, res.xp));
  return res;
}

// ───────── ندرة القدرات: كل قدرة لها ندرة تحدد عدد مهاراتها وأعلى ليفل لها ─────────
export const RARITIES = [
  { key: "common", name: "شائعة", color: "§7", skills: 2, maxLv: 4, weight: 34 },
  { key: "uncommon", name: "غير شائعة", color: "§a", skills: 3, maxLv: 5, weight: 26 },
  { key: "rare", name: "نادرة", color: "§9", skills: 4, maxLv: 6, weight: 18 },
  { key: "epic", name: "ملحمية", color: "§5", skills: 5, maxLv: 7, weight: 13 },
  { key: "legendary", name: "أسطورية", color: "§6", skills: 6, maxLv: 8, weight: 7 },
  { key: "mythic", name: "خرافية", color: "§c", skills: 7, maxLv: 10, weight: 2 },
];

// ليفل القدرة اللي تنفتح عنده المهارة رقم idx (الأولى دائما 1، والأخيرة عند الحد الأقصى)
export function unlockLevel(idx, n, maxLv) {
  if (idx === 0 || n <= 1) return 1;
  return 1 + Math.round((idx * (maxLv - 1)) / (n - 1));
}

export function powerXpNeeded(level) {
  return 40 + level * 35;
}

export function addPowerXp(st, amount, maxLv) {
  const ups = [];
  if (!st.plevel) st.plevel = 1;
  if (!st.pxp) st.pxp = 0;
  if (st.plevel >= maxLv) return ups;
  st.pxp += amount;
  while (st.plevel < maxLv && st.pxp >= powerXpNeeded(st.plevel)) {
    st.pxp -= powerXpNeeded(st.plevel);
    st.plevel++;
    ups.push({ type: "plevel", level: st.plevel });
  }
  if (st.plevel >= maxLv) st.pxp = 0;
  return ups;
}

// أول مهارة بكل قدرة مفتوحة دائما. الباقي: يخلص التدريب + ليفل القدرة يوصل لليفل فتح المهارة
export function isSkillUnlocked(st, skill) {
  if (st.power !== skill.power) return false;
  if (skill.first) return true;
  const tr = st.training && st.training[skill.power];
  if (!tr || tr.status !== "done") return false;
  return (st.plevel || 1) >= skill.unlock;
}
