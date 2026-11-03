// الداش: ضغطتين سريعتين على يمين أو يسار أو خلف = داش بنفس الاتجاه (حسب وين تباوع). كول داون حسب الرتبة (ثانيتين عند Trainee لحد 0.9 ثانية عند Master)، وبدون أي جزيئات (صوت خفيف بس).
// ينفتح أول ما اللاعب يحصل أول رتبة (يترقى من Novice إلى Trainee)، ويبقى له للأبد (علم sh_dash على اللاعب، حتى لو انعادت حالته).
// يقرا حركة اللاعب من player.inputInfo.getMovementVector() (x يمين/يسار، y قدام/خلف) كل تك:
//  • يشتغل على لوحة المفاتيح وشاشة اللمس (جويستك) وعلى يد التحكم (عتبات ضغط/إفلات مع تأخير حتى ما يتلخبط).
//  • ما نعرف اتجاه إشارة x,y بالضبط عند كل جهاز، فنعايرها تلقائياً: لما اللاعب يتحرك فعلاً نقارن إشارة المتجه بإشارة سرعته نسبة لاتجاه البصر
//    ونحفظ النتيجة (sh_dashcal) حتى تبقى بالجلسات الجاية. أول ضغطة وحدة كافية لأن السرعة تبين خلال تك أو تكين.
//  • الحركة بخطوات teleport قصيرة (3 تكات، 3 بلوكات بالضبط) مع فحص عوائق (بلوكتين ارتفاع) وصعود درجة بلوكة، ويوقف قبل الجدار.
import { world, system } from "@minecraft/server";

export const DASH = {
  cooldown: [40, 40, 36, 31, 27, 22, 18],   // الكول داون حسب الرتبة (تك، 20 = ثانية): Trainee ثانيتين ويقصر كل رتبة لحد 0.9 ثانية عند Master
  window: 10,          // أقصى فاصل بين بداية الضغطتين (تك) ≈ نص ثانية
  dist: 3,             // مسافة الداش: 3 بلوكات بالضبط (يمين/يسار/خلف بس، للأمام ماكو داش)
  steps: 3,            // يتوزع على 3 تكات
  on: 0.6,             // عتبة الضغط
  off: 0.3,            // عتبة الإفلات (أقل من عتبة الضغط حتى ما يتذبذب)
};
const DIRS = ["left", "right", "back"];
const SOFT = /(grass|fern|flower|tulip|dandelion|poppy|orchid|allium|azure_bluet|daisy|cornflower|lily|rose|peony|lilac|sapling|carpet|torch|button|pressure_plate|sign|rail|vine|cane|web|petals|snow_layer|mushroom|sweet_berry|crop|wheat|carrots|potatoes|beetroot|melon_stem|pumpkin_stem|redstone_wire|tripwire|lever|flower_pot|candle)/;

export const DASH_FROM_RANK = 1;     // أول رتبة تنكسب: Trainee (الرتبة 0 Novice يبدأ فيها اللاعب)
// رتبة اللاعب من حالته المحفوظة (sh)
function rankOf(p) {
  try { const raw = p.getDynamicProperty("sh"); return typeof raw === "string" ? (JSON.parse(raw).rank || 0) : 0; } catch (e) { return 0; }
}
export const dashCooldown = (rank) => DASH.cooldown[Math.max(0, Math.min(DASH.cooldown.length - 1, rank))];
const unlocked = (p) => { try { return p.getDynamicProperty("sh_dash") === 1; } catch (e) { return false; } };
// يتحقق كل نص ثانية من رتبة اللاعب (حالته محفوظة بـ sh)؛ أول ما توصل DASH_FROM_RANK نحط العلم الدائم ونخبره
function checkUnlock(p) {
  try {
    const rank = rankOf(p);
    if (rank < DASH_FROM_RANK) return false;
    p.setDynamicProperty("sh_dash", 1);
    try { p.sendMessage("§6[Dash] §fDash unlocked! §7Double-tap §eleft§7, §eright§7 or §eback§7 to dash that way. It stays with you forever. Cooldown: 2 s, and it gets shorter with every rank (0.9 s at Master)."); } catch (e) { /* */ }
    try { p.playSound("sh.ready", { volume: 0.9, pitch: 1.2 }); } catch (e) { /* */ }
    return true;
  } catch (e) { return false; }
}

const state = new Map();   // player.id → { down, last, released, cd, vx, vy, plan }
const stOf = (p) => {
  let s = state.get(p.id);
  if (!s) {
    s = { down: { left: false, right: false, back: false }, last: { left: -999, right: -999, back: -999 }, released: { left: true, right: true, back: true }, cd: 0, vx: 0, vy: 0, plan: null };
    try { const c = p.getDynamicProperty("sh_dashcal"); if (typeof c === "string") { const [a, b] = c.split(",").map(Number); s.vx = a || 0; s.vy = b || 0; } } catch (e) { /* */ }
    state.set(p.id, s);
  }
  return s;
};

function passable(dim, x, y, z) {
  try {
    const b = dim.getBlock({ x: Math.floor(x), y: Math.floor(y), z: Math.floor(z) });
    if (!b || b.isAir || b.isLiquid) return true;
    if (typeof b.isSolid === "boolean") return !b.isSolid;
    return SOFT.test(b.typeId);
  } catch (e) { return false; }
}

// اتجاه البصر الأفقي (f) واليمين (r)
function basis(p) {
  const v = p.getViewDirection(), l = Math.hypot(v.x, v.z) || 1;
  const f = { x: v.x / l, z: v.z / l };
  return { f, r: { x: -f.z, z: f.x } };           // يمين: لو تباوع جنوب (0,+1) اليمين غرب (-1,0)
}

// معايرة إشارة المتجه: نقارن بسرعة اللاعب الحقيقية
function calibrate(p, s, v, b) {
  let vel;
  try { vel = p.getVelocity(); } catch (e) { return; }
  const lat = vel.x * b.r.x + vel.z * b.r.z, fw = vel.x * b.f.x + vel.z * b.f.z;
  let changed = false;
  if (Math.abs(v.x) > 0.5 && Math.abs(lat) > 0.06) { s.vx = Math.max(-6, Math.min(6, s.vx + Math.sign(lat) * Math.sign(v.x))); changed = true; }
  if (Math.abs(v.y) > 0.5 && Math.abs(fw) > 0.06) { s.vy = Math.max(-6, Math.min(6, s.vy + Math.sign(fw) * Math.sign(v.y))); changed = true; }
  if (changed && (s.vx === 3 || s.vx === -3 || s.vy === 3 || s.vy === -3)) { try { p.setDynamicProperty("sh_dashcal", `${s.vx},${s.vy}`); } catch (e) { /* */ } }
}

// مستمعين للداش (main.js يعد الداشات لإنجاز Blink)
export const dashHooks = [];
function startDash(p, s, d) {
  for (const f of dashHooks) { try { f(p); } catch (e) { /* */ } }
  const b = basis(p);
  const dir = d === "right" ? { x: b.r.x, z: b.r.z } : d === "left" ? { x: -b.r.x, z: -b.r.z } : { x: -b.f.x, z: -b.f.z };
  s.plan = { dir, left: DASH.steps, per: DASH.dist / DASH.steps };
  s.cd = system.currentTick + dashCooldown(rankOf(p));
  try { p.dimension.playSound("sh.stardash", p.location, { volume: 0.45, pitch: 1.7 }); } catch (e) { /* */ }
}

// خطوة داش وحدة: نتقدم per بلوكة بخطوات نص بلوكة ونوقف عند أول عائق (مع صعود درجة بلوكة)
function stepDash(p, s) {
  const pl = s.plan;
  if (!pl) return;
  const dim = p.dimension;
  let { x, y, z } = p.location;
  let moved = 0;
  const n = Math.max(1, Math.ceil(pl.per / 0.5)), sub = pl.per / n;           // خطوات صغيرة (≤ نص بلوكة) مجموعها المسافة بالضبط
  for (let q = 0; q < n; q++) {
    const nx = x + pl.dir.x * sub, nz = z + pl.dir.z * sub;
    if (passable(dim, nx, y, nz) && passable(dim, nx, y + 1, nz)) { x = nx; z = nz; moved += sub; continue; }
    if (passable(dim, nx, y + 1, nz) && passable(dim, nx, y + 2, nz) && passable(dim, x, y + 2, z)) { x = nx; z = nz; y += 1; moved += sub; continue; }   // درجة بلوكة
    pl.left = 0;                                                                                                                                   // جدار: نوقف
    break;
  }
  if (moved > 0) { try { p.teleport({ x, y, z }, { keepVelocity: false }); } catch (e) { /* */ } }
  pl.left--;
  if (pl.left <= 0) s.plan = null;
}

function canDash(p) {
  try {
    if (p.isSleeping || p.isGliding || p.isSwimming) return false;
    if (p.getComponent("minecraft:riding")) return false;
    const h = p.getComponent("minecraft:health");
    if (h && h.currentValue <= 0) return false;
  } catch (e) { /* */ }
  return true;
}

export function setupDash() {
  system.runInterval(() => {
    const now = system.currentTick;
    for (const p of world.getAllPlayers()) {
      try {
        const s = stOf(p);
        if (!unlocked(p)) { if (now % 10 === 0) checkUnlock(p); s.plan = null; continue; }   // مقفول لحد أول رتبة
        if (s.plan) stepDash(p, s);
        let v;
        try { v = p.inputInfo.getMovementVector(); } catch (e) { continue; }
        if (!v) continue;
        const b = basis(p);
        calibrate(p, s, v, b);
        const sx = s.vx > 0 ? 1 : -1;                          // قبل المعايرة نفترض x موجب = يسار (مثل Java)، وy موجب = قدام
        const sy = s.vy >= 0 ? 1 : -1;
        const right = v.x * sx, fwd = v.y * sy;                  // right موجب = يمين، fwd موجب = قدام
        const comp = { left: -right, right, back: -fwd };
        for (const d of DIRS) {
          const was = s.down[d], isDown = was ? comp[d] > DASH.off : comp[d] >= DASH.on;
          if (isDown && !was) {                                  // بداية ضغطة
            for (const o of DIRS) if (o !== d) s.last[o] = -999; // اتجاه ثاني يلغي الضغطة السابقة
            if (s.released[d] && now - s.last[d] <= DASH.window) {
              s.last[d] = -999;
              if (now >= s.cd && !s.plan && canDash(p)) startDash(p, s, d);
            } else s.last[d] = now;
            s.released[d] = false;
          }
          if (!isDown && was) s.released[d] = true;
          s.down[d] = isDown;
        }
      } catch (e) { /* */ }
    }
  }, 1);
  world.afterEvents.playerLeave.subscribe((ev) => { try { state.delete(ev.playerId); } catch (e) { /* */ } });
}
