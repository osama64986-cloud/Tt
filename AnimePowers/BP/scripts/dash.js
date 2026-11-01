// الداش: ضغطتين سريعتين على يمين أو يسار أو خلف = داش بنفس الاتجاه (حسب وين تباوع). كول داون 1.8 ثانية، وبدون أي جزيئات (صوت خفيف بس).
// يقرا حركة اللاعب من player.inputInfo.getMovementVector() (x يمين/يسار، y قدام/خلف) كل تك:
//  • يشتغل على لوحة المفاتيح وشاشة اللمس (جويستك) وعلى يد التحكم (عتبات ضغط/إفلات مع تأخير حتى ما يتلخبط).
//  • ما نعرف اتجاه إشارة x,y بالضبط عند كل جهاز، فنعايرها تلقائياً: لما اللاعب يتحرك فعلاً نقارن إشارة المتجه بإشارة سرعته نسبة لاتجاه البصر
//    ونحفظ النتيجة (sh_dashcal) حتى تبقى بالجلسات الجاية. أول ضغطة وحدة كافية لأن السرعة تبين خلال تك أو تكين.
//  • الحركة بخطوات teleport قصيرة (4 تكات) مع فحص عوائق (بلوكتين ارتفاع) وصعود درجة بلوكة، ويوقف قبل الجدار.
import { world, system } from "@minecraft/server";

export const DASH = {
  cooldown: 36,        // 1.8 ثانية (20 تك = ثانية)
  window: 10,          // أقصى فاصل بين بداية الضغطتين (تك) ≈ نص ثانية
  dist: 6,             // مسافة الداش (بلوكات)
  steps: 4,            // يتوزع على 4 تكات
  on: 0.6,             // عتبة الضغط
  off: 0.3,            // عتبة الإفلات (أقل من عتبة الضغط حتى ما يتذبذب)
};
const DIRS = ["left", "right", "back"];
const SOFT = /(grass|fern|flower|tulip|dandelion|poppy|orchid|allium|azure_bluet|daisy|cornflower|lily|rose|peony|lilac|sapling|carpet|torch|button|pressure_plate|sign|rail|vine|cane|web|petals|snow_layer|mushroom|sweet_berry|crop|wheat|carrots|potatoes|beetroot|melon_stem|pumpkin_stem|redstone_wire|tripwire|lever|flower_pot|candle)/;

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

function startDash(p, s, d) {
  const b = basis(p);
  const dir = d === "right" ? { x: b.r.x, z: b.r.z } : d === "left" ? { x: -b.r.x, z: -b.r.z } : { x: -b.f.x, z: -b.f.z };
  s.plan = { dir, left: DASH.steps, per: DASH.dist / DASH.steps };
  s.cd = system.currentTick + DASH.cooldown;
  try { p.dimension.playSound("sh.stardash", p.location, { volume: 0.45, pitch: 1.7 }); } catch (e) { /* */ }
}

// خطوة داش وحدة: نتقدم per بلوكة بخطوات نص بلوكة ونوقف عند أول عائق (مع صعود درجة بلوكة)
function stepDash(p, s) {
  const pl = s.plan;
  if (!pl) return;
  const dim = p.dimension;
  let { x, y, z } = p.location;
  let moved = 0;
  for (let q = 0; q < pl.per; q += 0.5) {
    const nx = x + pl.dir.x * 0.5, nz = z + pl.dir.z * 0.5;
    if (passable(dim, nx, y, nz) && passable(dim, nx, y + 1, nz)) { x = nx; z = nz; moved += 0.5; continue; }
    if (passable(dim, nx, y + 1, nz) && passable(dim, nx, y + 2, nz) && passable(dim, x, y + 2, z)) { x = nx; z = nz; y += 1; moved += 0.5; continue; }   // درجة بلوكة
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
  // تلميح مرة وحدة
  world.afterEvents.playerSpawn.subscribe((ev) => {
    try {
      if (!ev.initialSpawn || ev.player.getDynamicProperty("sh_dashhint")) return;
      ev.player.setDynamicProperty("sh_dashhint", 1);
      system.runTimeout(() => { try { ev.player.sendMessage("§6[Dash] §fDouble-tap §eleft§f, §eright§f or §eback§f to dash that way. §7(1.8 s cooldown)"); } catch (e) { /* */ } }, 100);
    } catch (e) { /* */ }
  });
}
