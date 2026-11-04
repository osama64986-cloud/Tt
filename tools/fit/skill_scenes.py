"""مشاهد مهارات وحوش Grim (الغزال والرائي) والسيوف. ملاحظة: مهارات الثعلب والماموث ما تنرسم هنا بعد اليوم (كانت مشاهد مرسومة باليد وما تطابق السكربت)؛
استعمل tools/sim/record_skill.mjs + tools/fit/skill_capture.py اللي يسجلان السكربت الحقيقي ويرسمان جزيئات ماينكرافت بتعريفاتها الأصلية.
النص القديم: يركب الوحش (بوضعية الأنيميشن) + أشكال المهارات (نفس المواقع والأحجام والزوايا اللي بالسكربت)
+ لاعب + بكسلات، ويرسمها من زاوية وحدة. الاستعمال: python3 tools/fit/skill_scenes.py <مجلد_الإخراج>"""
import json, math, os, sys, random
import numpy as np
from PIL import Image, ImageOps, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import render as R

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "AnimePowers", "RP")
GEO, TEX = os.path.join(ROOT, "models", "entity"), os.path.join(ROOT, "textures", "entity")
ANIM = json.load(open(os.path.join(ROOT, "animations", "sh_grim.animation.json"), encoding="utf-8"))["animations"]
FXA = json.load(open(os.path.join(ROOT, "animations", "sh_fx.animation.json"), encoding="utf-8"))["animations"]

# كل أشكال المهارات بموديل واحد لكل اسم
_shape_geo = json.load(open(os.path.join(GEO, "sh_fx_shapes.geo.json"), encoding="utf-8"))["minecraft:geometry"]
_shape_tex = os.path.join(TEX, "sh_fx_shapes.png")


def _model_from(g, tex):
    m = R.Model.__new__(R.Model)
    m.bones = {b["name"]: b for b in g["bones"]}
    m.tex = np.array(Image.open(tex).convert("RGBA"))
    m.tw, m.th = g["description"]["texture_width"], g["description"]["texture_height"]
    return m


SHAPES = {g["description"]["identifier"].split("sh_shape_")[1]: _model_from(g, _shape_tex) for g in _shape_geo}


def roty(th):
    c, s = math.cos(th), math.sin(th)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def yaw_for(d):  # يخلي -z بالموديل يتوجه للاتجاه d (مثل dirYaw باللعبة)
    return math.atan2(-d[0], -d[1])


class Scene:
    def __init__(self):
        self.faces = []  # (pts[4x3] بالبلوكات, kind, data)
        self.sprites = []  # (مركز, حجم بالبلوكات, صورة RGBA) لوحات جزيئات تواجه الكاميرا

    def sprite(self, pos, size, img):
        self.sprites.append((np.array(pos, float), float(size), img))

    def model(self, m, pose, pos, d=(0, 1), scale=1.0):
        Rm = roty(yaw_for(d))
        for pts, rect, _ in m.world_cubes(pose):
            p = (pts / 16.0 * scale) @ Rm.T + np.array(pos)
            self.faces.append((p, "tex", (m, rect)))

    def shape(self, name, pos, d=(0, 1), r=1.0, p=0.0, a=0.0, life=None, s=0.0, w=0.0, l=1.0):
        """نفس animation.sh_fx.shape: spin (Y = الوقت×sh:s)، tilt (X = sh:p)، roll (Z = sh:a + الوقت×sh:w)، ونبضة الظهور،
        والشعاع النجمي يتمدد بطوله sh:l"""
        lt = life or 0.0
        pose = {"spin": {"rot": [0, lt * s, 0], "pos": [0, 0, 0]}, "tilt": {"rot": [p, 0, 0], "pos": [0, 0, 0]}, "roll": {"rot": [0, 0, a + lt * w], "pos": [0, 0, 0]}}
        if name == "star_beam":
            pose["body"] = {"rot": [0, 0, 0], "pos": [0, 0, 0], "scale": [1, 1, max(0.05, l)]}
        if name in ("wind_ring", "nova_ring"):
            pose["body"] = {"rot": [0, 0, 0], "pos": [0, 0, 0], "scale": [1, min(1.0, 2.5 / max(0.1, r)), 1]}
        if name in ("sound_wave", "echo_pulse"):
            pose["body"] = {"rot": [0, 0, 0], "pos": [0, 0, 0], "scale": [1, min(1.0, 3.0 / max(0.1, r)), 1]}
        grow = min(1.0, 0.3 + lt * 7.0) if life is not None else 1.0
        self.model(SHAPES[name], pose, pos, d, r * grow)

    def cube(self, c, s, col, glow=False):
        x0, y0, z0 = c[0] - s / 2, c[1] - s / 2, c[2] - s / 2
        fc = R.face_corners(x0, y0, z0, x0 + s, y0 + s, z0 + s)
        for f in R.FACES:
            self.faces.append((np.array(fc[f], dtype=float), "col", (np.array(col, dtype=float), glow)))

    def box(self, lo, hi, col):
        fc = R.face_corners(*lo, *hi)
        for f in R.FACES:
            self.faces.append((np.array(fc[f], dtype=float), "col", (np.array(col, dtype=float), False)))

    def player(self, pos, d=(0, -1)):
        """لاعب بسيط بالبلوكات (2 بلوكة)، يباوع للاتجاه d."""
        Rm = roty(yaw_for(d))
        parts = [((-0.25, 0, -0.125), (0.0, 0.75, 0.125), (40, 60, 150)), ((0.0, 0, -0.125), (0.25, 0.75, 0.125), (40, 60, 150)),
                 ((-0.25, 0.75, -0.125), (0.25, 1.5, 0.125), (0, 170, 170)),
                 ((-0.5, 0.75, -0.125), (-0.25, 1.5, 0.125), (200, 150, 110)), ((0.25, 0.75, -0.125), (0.5, 1.5, 0.125), (200, 150, 110)),
                 ((-0.25, 1.5, -0.25), (0.25, 2.0, 0.25), (200, 150, 110)), ((-0.26, 1.82, -0.26), (0.26, 2.01, 0.26), (70, 45, 25))]
        for lo, hi, col in parts:
            fc = R.face_corners(*lo, *hi)
            for f in R.FACES:
                self.faces.append((np.array(fc[f], dtype=float) @ Rm.T + np.array(pos), "col", (np.array(col, dtype=float), False)))

    def ground(self, cx, cz, n=9, y=0.0):
        for i in range(-n, n + 1):
            for k in range(-n, n + 1):
                g = 92 + ((i + k) % 2) * 10
                self.faces.append((np.array(R.face_corners(cx + i - 0.5, y - 1, cz + k - 0.5, cx + i + 0.5, y, cz + k + 0.5)["up"], dtype=float),
                                   "col", (np.array((g * 0.55, g * 0.85, g * 0.5)), False)))

    def render(self, center, yaw=30, pitch=26, dist=12, size=760, bg=(150, 185, 225)):
        yr, pr = math.radians(yaw), math.radians(pitch)
        cam = np.array(center) + dist * np.array([math.sin(yr) * math.cos(pr), math.sin(pr), -math.cos(yr) * math.cos(pr)])
        f = np.array(center) - cam; f /= np.linalg.norm(f)
        right = np.cross(f, [0, 1, 0]); right /= np.linalg.norm(right)
        up = np.cross(right, f)
        focal = size * 0.5 / math.tan(math.radians(30))
        img = np.zeros((size, size, 3), np.float32); img[:] = bg
        zb = np.full((size, size), 1e9, np.float32)
        light = np.array([0.4, 0.8, -0.5]); light /= np.linalg.norm(light)
        for p, kind, data in self.faces:
            n = -np.cross(p[1] - p[0], p[3] - p[0]); ln = np.linalg.norm(n)
            if ln < 1e-12: continue
            n /= ln
            if np.dot(n, p[0] - cam) > 0: continue
            rel = p - cam; dep = rel @ f
            if (dep <= 0.05).any(): continue
            sx = (rel @ right) / dep * focal + size / 2; sy = -(rel @ up) / dep * focal + size / 2
            shade = 0.55 + 0.45 * max(0.0, float(np.dot(n, light)))
            if kind == "tex":
                m, (ru, rv, rw, rh) = data
                uv = np.array([(ru, rv), (ru + rw, rv), (ru + rw, rv + rh), (ru, rv + rh)], float)
            for a, b, c in ((0, 1, 2), (0, 2, 3)):
                xs, ys = sx[[a, b, c]], sy[[a, b, c]]
                x0, x1 = int(max(0, math.floor(xs.min()))), int(min(size - 1, math.ceil(xs.max())))
                y0, y1 = int(max(0, math.floor(ys.min()))), int(min(size - 1, math.ceil(ys.max())))
                if x0 > x1 or y0 > y1: continue
                gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
                den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
                if abs(den) < 1e-9: continue
                l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
                l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
                l2 = 1 - l0 - l1
                msk = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
                if not msk.any(): continue
                iw = np.stack([l0 / dep[a], l1 / dep[b], l2 / dep[c]]); s = iw.sum(0)
                z = 1.0 / np.where(s == 0, 1, s)
                if kind == "tex":
                    pl = iw / np.where(s == 0, 1, s)
                    u = pl[0] * uv[a, 0] + pl[1] * uv[b, 0] + pl[2] * uv[c, 0]
                    v = pl[0] * uv[a, 1] + pl[1] * uv[b, 1] + pl[2] * uv[c, 1]
                    tx = np.clip((u - 1e-3).astype(int), 0, m.tw - 1); ty = np.clip((v - 1e-3).astype(int), 0, m.th - 1)
                    tex = m.tex[ty, tx]
                    ok = msk & (tex[..., 3] > 128) & (z < zb[y0:y1 + 1, x0:x1 + 1])
                    col = tex[..., :3].astype(np.float32) * shade
                    semi = msk & (tex[..., 3] > 8) & (tex[..., 3] <= 128) & (z < zb[y0:y1 + 1, x0:x1 + 1])   # alphablend (تمويه): مزج بدون عمق
                    if semi.any():
                        al = tex[..., 3:4].astype(np.float32) / 255.0
                        reg = img[y0:y1 + 1, x0:x1 + 1]
                        reg[semi] = (col * al + reg * (1 - al))[semi]
                else:
                    cc, glow = data
                    ok = msk & (z < zb[y0:y1 + 1, x0:x1 + 1])
                    col = np.broadcast_to(cc * (1.0 if glow else shade), ok.shape + (3,))
                if not ok.any(): continue
                sub = zb[y0:y1 + 1, x0:x1 + 1]; sub[ok] = z[ok]
                img[y0:y1 + 1, x0:x1 + 1][ok] = col[ok]
        for pos, sz, im in sorted(self.sprites, key=lambda q: -float(np.dot(q[0] - cam, f))):    # الجزيئات: من الأبعد للأقرب، اختبار عمق مقابل المجسمات
            rel = pos - cam; dep = float(rel @ f)
            if dep <= 0.15: continue
            cx = float(rel @ right) / dep * focal + size / 2; cy = -float(rel @ up) / dep * focal + size / 2
            n = max(2, int(round(sz * focal / dep)))
            x0, y0 = int(round(cx - n / 2)), int(round(cy - n / 2))
            if x0 + n < 0 or y0 + n < 0 or x0 >= size or y0 >= size: continue
            tile = np.array(Image.fromarray(im.astype(np.uint8), "RGBA").resize((n, n), Image.BOX), np.float32)
            xs0, ys0 = max(0, x0), max(0, y0); xs1, ys1 = min(size, x0 + n), min(size, y0 + n)
            t = tile[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
            a = (t[..., 3:4] / 255.0) * (zb[ys0:ys1, xs0:xs1] > dep - 0.03)[..., None]
            img[ys0:ys1, xs0:xs1] = img[ys0:ys1, xs0:xs1] * (1 - a) + t[..., :3] * a
        return ImageOps.mirror(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)))


def mon(name):
    return R.Model(os.path.join(GEO, f"sh_{name}.geo.json"), os.path.join(TEX, f"sh_{name}.png"))


def pose(names, t):
    return R.pose_from_anims([ANIM[n] for n in names], t, {"q": {"life_time": t, "modified_move_speed": 0, "modified_distance_moved": 0}})


SOUL, VIO, ICE = (102, 230, 255), (185, 140, 255), [(235, 247, 255), (184, 224, 255), (133, 189, 255), (217, 242, 255)]
ORANGE = (255, 140, 30)
rnd = random.Random(7)


def seer_roots(out):
    S = Scene(); S.ground(0, 4)
    S.model(mon("hollow_seer"), pose(["animation.sh_hollow_seer.idle", "animation.sh_hollow_seer.thorns"], 0.6), (0, 0.4, 0), (0, 1))
    P = (0, 0, 7.5)
    S.player(P, (0, -1))
    for k in range(4):                       # خط الجذور (نفس السكربت: r=1.8)
        z = 1.5 + k * 1.1
        S.shape("root_spike", (0.15 * (-1) ** k, 0, z), (rnd.uniform(-1, 1), rnd.uniform(-1, 1)), 1.8, rnd.uniform(-8, 8))
    for i in range(6):                       # قفص الجذور: نصف قطر 1.75، r=1.7، متوجه للاعب
        a = i / 6 * math.tau; x, z = P[0] + math.cos(a) * 1.75, P[2] + math.sin(a) * 1.75
        S.shape("root_spike", (x, 0, z), (P[0] - x, P[2] - z), 1.7)
    return S.render((0, 1.2, 4.2), yaw=-58, pitch=24, dist=11.5)


def seer_frost(out):
    S = Scene(); S.ground(0, 3)
    S.model(mon("hollow_seer"), pose(["animation.sh_hollow_seer.idle", "animation.sh_hollow_seer.breath"], 0.8), (0, 0.4, 0), (0, 1))
    orb = (0, 2.2 + 0.4, 1.4)
    S.shape("soul_orb", orb, (0, 1), 0.95, 0, 30)
    P = (0, 0, 5.5); S.player(P, (0, -1))
    for i in range(170):                     # مخروط بكسلات الزفير (نفس معادلة السكربت)
        dd = 0.4 + rnd.random() * 6.5; spread = dd * 0.32
        side, upv = (rnd.random() - 0.5) * 2 * spread, (rnd.random() - 0.5) * spread
        dy = (1.0 - orb[1]) / 4.5
        S.cube((side, orb[1] + dy * dd + upv, 1.9 + dd), 0.09 + rnd.random() * 0.05, ICE[i % 4], True)
    for dx, dz in ((0, 0), (0.6, 0.2)):        # ثلج ناعم عند اللاعب
        pass
    return S.render((0, 1.6, 3.0), yaw=-62, pitch=16, dist=10)


def seer_beam(out):
    S = Scene(); S.ground(0, 5)
    S.model(mon("hollow_seer"), pose(["animation.sh_hollow_seer.idle", "animation.sh_hollow_seer.beam"], 1.0), (0, 0.4, 0), (0, 1))
    hand = np.array([0, 2.3 + 0.4, 0.95]); P = (0, 0, 10); S.player(P, (0, -1))
    tgt = np.array([0, 1.0, 10]); d = tgt - hand; L = np.linalg.norm(d); d /= L
    pitch = math.degrees(math.asin(-d[1])) * -1
    k = 0
    while k * 1.43 < L:
        c = hand + d * min(L - 0.3, k * 1.43 + 0.715)
        S.shape("beam_orange", tuple(c), (0, 1), 1.4, -math.degrees(math.asin(d[1])))
        k += 1
    return S.render((0, 1.5, 5), yaw=-70, pitch=18, dist=12)


def deer_spirit(out):
    S = Scene(); S.ground(0, 5)
    S.model(mon("gloomhorn"), pose(["animation.sh_gloomhorn.idle", "animation.sh_gloomhorn.lanterns"], 0.5), (0, 0, 0), (0, 1))
    S.player((0, 0, 11), (0, -1))
    S.shape("spirit_stag", (0, 0, 4.6), (0, 1), 1.5)                     # الروح الرئيسية بنص طريقها
    for sx in (-1, 1):                                                  # الروحين بمروحة 0.42 راديان
        ang = math.pi / 2 + sx * 0.42; dv = (math.cos(ang), math.sin(ang))
        S.shape("spirit_stag", (dv[0] * 2.8, 0, dv[1] * 2.8), dv, 1.0)
    for k in range(10):                                                  # آثار الحوافر
        S.cube((0.18 * (-1) ** k, 0.03, 1.6 + k * 0.3), 0.16, SOUL, True)
    for i in range(30):                                                  # من القلب للروح
        s = rnd.random(); S.cube((rnd.uniform(-.2, .2), 1.3 + (1.2 - 1.3) * s, 4.6 * s), 0.1, SOUL if i % 2 else (230, 255, 255), True)
    return S.render((0, 1.0, 4.5), yaw=-55, pitch=24, dist=12.5)


def deer_heart(out):
    S = Scene(); S.ground(0, 3)
    S.model(mon("gloomhorn"), pose(["animation.sh_gloomhorn.idle", "animation.sh_gloomhorn.heartbeat"], 1.5), (0, 0, 0), (0, 1))
    P = (1.2, 0, 4.5); S.player(P, (-0.25, -1))
    for r, col in ((2.4, SOUL), (4.6, VIO)):                            # موجات الدقات
        n = int(10 + r * 6)
        for i in range(n):
            a = i / n * math.tau; S.cube((math.cos(a) * r, 0.14, math.sin(a) * r), 0.2, col, True)
    H = np.array([0, 1.3, -0.1]); B = np.array([P[0], 1.0, P[2]])        # سلسلة الروح المتدلية
    for i in range(15):
        s = i / 14; sag = math.sin(math.pi * s) * 0.55; p = H + (B - H) * s; p[1] -= sag
        S.cube(tuple(p), 0.17 if i % 2 == 0 else 0.13, (184, 140, 255) if i % 2 == 0 else SOUL, True)
    return S.render((0.5, 1.0, 2.3), yaw=-65, pitch=22, dist=8.5)


def deer_charge(out):
    S = Scene(); S.ground(0, 4)
    S.model(mon("gloomhorn"), pose(["animation.sh_gloomhorn.charge"], 0.1), (0, 0, 2.5), (0, 1))
    S.player((0, 0, 5.6), (0, -1))
    S.shape("nova", (0, 1.2, 4.9), (0, 1), 0.9)
    for k in range(22):                                                  # خط التحذير الأحمر
        S.cube((0, 0.06, -1 + k * 0.5), 0.14, (255, 64, 76), True)
    for k in range(8):
        S.cube((0.35 * (-1) ** k, 0.04, -0.5 + k * 0.35), 0.18, SOUL if k % 2 else (217, 255, 255), True)
    return S.render((0, 1.0, 3.2), yaw=-62, pitch=20, dist=9)


def sword_light(out):
    S = Scene(); S.ground(0, 5)
    S.player((0, 0, 0), (0, 1))
    S.shape("slash_silver", (0, 1.0, 1.6), (0, 1), 2.4, 90)
    for dist, off in ((3.6, 0), (5.4, -1.7), (5.4, 1.7)):
        S.shape("light_lance", (off, 0, dist), (0, 1), 1.25)
    return S.render((0, 1.4, 3), yaw=-55, pitch=22, dist=9.5)


def sword_shadow(out):
    S = Scene(); S.ground(0, 4)
    S.player((0, 0, 3), (0, -1))                              # العدو
    for i in range(3):
        a = i * 2.0944 + 0.5
        S.shape("ghost_sword", (3 * 0 + math.cos(a) * 1.8, 0, 3 + math.sin(a) * 1.8), (0, 1), 1.1)
    S.shape("slash_violet", (0, 1.0, 3), (0, 1), 1.5, 90 + 45, 45)
    S.shape("slash_violet", (0, 1.0, 3), (0, 1), 1.5, 90 - 45, -45)
    S.shape("afterimage", (0, 0, 7), (0, -1), 1.0)
    return S.render((0, 1.2, 3), yaw=-55, pitch=22, dist=8.5)


def sword_katana(out):
    S = Scene(); S.ground(0, 4)
    S.player((0, 0, 3), (0, -1))
    S.shape("ghost_sword", (0, 0, 3), (0, 1), 1.9)
    S.shape("slash_violet", (0, 1.0, 3), (0, 1), 1.5, 90 + 45, 45)
    S.shape("slash_violet", (0, 1.0, 3), (0, 1), 1.5, 90 - 45, -45)
    return S.render((0, 1.2, 3), yaw=-50, pitch=20, dist=8)


if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    scenes = [("الرائي: جذور الأرض + قفص الجذور", seer_roots), ("الرائي: زفير التجميد من كرة الجليد", seer_frost),
              ("الرائي: الشعاع البرتقالي", seer_beam), ("الغزال: روح الغزال", deer_spirit),
              ("الغزال: الاندفاع والنطح", deer_charge), ("الغزال: نبض القلب + سلاسل الروح", deer_heart),
              ("سيف النور", sword_light), ("شادو بليد", sword_shadow), ("كاتانا الهاوية", sword_katana)]
    for name, fn in scenes:
        im = fn(out); fname = os.path.join(out, fn.__name__ + ".png"); im.save(fname); print(fname)
