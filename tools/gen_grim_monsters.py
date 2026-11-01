"""وحوش رتبة Grim (القاتمة): القرن القاتم (Gloomhorn) والرائي الأجوف (Hollow Seer).
يبني الموديل (geometry) والتكستشر من الصفر بالكود: كل مادة (فرو، عظم، قماش، ذهب، توهج...) إلها مربع 32×32
بنقشة خاصة (ضوضاء، خطوط فرو، شقوق عظم، لمعة معدن)، وكل وجه مكعب يأخذ جزء من مربع مادته بحجمه الحقيقي.
القدام = -z، الأرض y=0. ما في مكعبات متطابقة الوجوه (فحص z-fighting بآخر الملف).
التشغيل: python3 tools/gen_grim_monsters.py [مجلد_معاينة]
"""
import json
import math
import os
import random
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
TILE = 32


def clamp(v):
    return max(0, min(255, int(v)))


BLK = {}


def tile_pattern(kind, base, alt, rnd):
    """يرجع مربع 32×32 (قائمة صفوف ألوان) حسب نوع المادة."""
    px = [[base] * TILE for _ in range(TILE)]
    for y in range(TILE):
        for x in range(TILE):
            n = rnd.uniform(-1, 1)
            if kind == "fur":           # خطوط فرو عمودية + ضوضاء
                streak = math.sin(x * 1.7 + rnd.uniform(0, .6)) * 0.5 + 0.5
                t = 0.12 * streak + 0.06 * n
                c = tuple(clamp(base[i] + (alt[i] - base[i]) * t * 2) for i in range(3))
            elif kind == "bone":        # عظم ناعم بشقوق خفيفة
                t = 0.05 * n
                c = tuple(clamp(base[i] * (1 + t)) for i in range(3))
                if (x * 7 + y * 3) % 23 == 0 or (x + 2 * y) % 29 == 0:
                    c = alt
            elif kind == "metal":       # معدن بتدرج ولمعة
                g = 1 - abs((x + y) / (2 * TILE) - 0.35) * 0.5
                c = tuple(clamp(base[i] * g + 18 * (1 if (x - y) % 11 == 0 else 0)) for i in range(3))
            elif kind == "cloth":       # قماش بنسيج
                w = 0.07 if (x % 2 == 0) ^ (y % 2 == 0) else -0.04
                c = tuple(clamp(base[i] * (1 + w + 0.05 * n)) for i in range(3))
            elif kind == "glow":        # توهج: قلب فاتح وحواف بلون
                d = abs(x - 15.5) / 16 + abs(y - 15.5) / 16
                c = tuple(clamp(alt[i] + (base[i] - alt[i]) * min(1, d)) for i in range(3))
            elif kind == "rock":        # حجر بركاني: كتل بكسل 4×4 بدرجات مختلفة (مثل صور ماينكرافت)
                v = BLK.setdefault((id(rnd), base, alt, x // 4, y // 4), rnd.uniform(-1, 1))
                t = 0.5 + 0.5 * v + 0.05 * n
                c = tuple(clamp(base[i] + (alt[i] - base[i]) * t) for i in range(3))
            elif kind == "lava":        # حمم: ضوضاء برتقالية مع بكسلات أصفر ساطعة وداكنة
                r = rnd.random()
                c = alt if r < 0.14 else tuple(clamp(base[i] * (0.78 + 0.3 * rnd.random())) for i in range(3))
            elif kind == "obsidian":
                c = tuple(clamp(base[i] + (alt[i] - base[i]) * (0.25 if rnd.random() < 0.06 else 0) + 6 * n) for i in range(3))
            else:                       # flat مع ضوضاء خفيفة
                c = tuple(clamp(base[i] * (1 + 0.04 * n)) for i in range(3))
            px[y][x] = c
    return px


class Rig:
    def __init__(self, ident, mats, seed=7):
        self.ident = ident
        self.bones = []
        self.mats = list(mats.keys())
        self.mat_def = mats
        self.seed = seed
        self.sc = (1.0, 1.0, 1.0)      # تحجيم x,y,z للهندسة (للماموث: أعرض وأقصر)
        self.rnd = random.Random(seed)
        n = len(self.mats)
        self.cols = 4
        self.rows = math.ceil(n / self.cols)
        self.tw, self.th = self.cols * TILE, self.rows * TILE

    def bone(self, name, parent=None, pivot=(0, 0, 0), rotation=None):
        pivot = (pivot[0] * self.sc[0], pivot[1] * self.sc[1], pivot[2] * self.sc[2])
        b = {"name": name, "pivot": [round(v, 3) for v in pivot], "cubes": []}
        if parent:
            b["parent"] = parent
        if rotation:
            b["rotation"] = list(rotation)
        self.bones.append(b)
        return name

    def _tile(self, mat):
        i = self.mats.index(mat)
        return (i % self.cols) * TILE, (i // self.cols) * TILE

    def box(self, bone, o, s, mat, rot=None, pivot=None, top=None):
        """o = الزاوية الدنيا، s = الحجم، mat = المادة (top = مادة الوجه الفوقاني اختياري)."""
        sx, sy, sz = self.sc
        o = (o[0] * sx, o[1] * sy, o[2] * sz); s = (s[0] * sx, s[1] * sy, s[2] * sz)
        if pivot is not None: pivot = (pivot[0] * sx, pivot[1] * sy, pivot[2] * sz)
        w, h, d = s
        def face(m, fw, fh, salt):
            tx, ty = self._tile(m)
            uw, uh = min(fw, TILE - 1), min(fh, TILE - 1)
            ox = (salt * 7) % max(1, int(TILE - uw)); oy = (salt * 5) % max(1, int(TILE - uh))
            return {"uv": [tx + ox, ty + oy], "uv_size": [round(uw, 3), round(uh, 3)]}
        salt = len(self._bone(bone)["cubes"]) + int(o[1] * 3)
        uv = {"north": face(mat, w, h, salt), "south": face(mat, w, h, salt + 1), "east": face(mat, d, h, salt + 2),
              "west": face(mat, d, h, salt + 3), "up": face(top or mat, w, d, salt + 4), "down": face(mat, w, d, salt + 5)}
        cube = {"origin": [round(v, 3) for v in o], "size": [round(v, 3) for v in s], "uv": uv}
        if rot:
            cube["rotation"] = list(rot)
            cube["pivot"] = [round(v, 3) for v in (pivot or (o[0] + w / 2, o[1] + h / 2, o[2] + d / 2))]
        self._bone(bone)["cubes"].append(cube)

    def boxc(self, bone, c, s, mat, **kw):
        """مكعب بمركزه c."""
        self.box(bone, (c[0] - s[0] / 2, c[1] - s[1] / 2, c[2] - s[2] / 2), s, mat, **kw)

    def _bone(self, name):
        for b in self.bones:
            if b["name"] == name:
                return b
        raise KeyError(name)

    def _png(self, defs, name, fixed):
        img = Image.new("RGBA", (self.tw, self.th), (0, 0, 0, 0))
        rnd = random.Random(self.seed) if fixed else self.rnd
        BLK.clear()
        for m in self.mats:
            kind, base, alt = defs[m]
            px = tile_pattern(kind, base, alt, rnd)
            tx, ty = self._tile(m)
            for y in range(TILE):
                for x in range(TILE):
                    img.putpixel((tx + x, ty + y), (*px[y][x], 255))
        img.save(os.path.join(RP, "textures", "entity", f"{name}.png"))

    def save(self, height_blocks, hot=None, width=5):
        """hot = {مادة: تعريف جديد}: يكتب نسخة ثانية من التكستشر (<الاسم>_hot.png) بنفس الـUV (للتوهج الأقوى)."""
        self._png(self.mat_def, self.ident, bool(hot))
        if hot:
            d = dict(self.mat_def); d.update(hot)
            self._png(d, self.ident + "_hot", True)
        geo = {"format_version": "1.12.0", "minecraft:geometry": [{
            "description": {"identifier": f"geometry.{self.ident}", "texture_width": self.tw, "texture_height": self.th,
                            "visible_bounds_width": width, "visible_bounds_height": height_blocks + 1, "visible_bounds_offset": [0, height_blocks / 2, 0]},
            "bones": self.bones}]}
        with open(os.path.join(RP, "models", "entity", f"{self.ident}.geo.json"), "w") as f:
            json.dump(geo, f, separators=(",", ":"))
        return sum(len(b["cubes"]) for b in self.bones)


# ════════════════════════════ القرن القاتم (Gloomhorn): أيل شبحي ════════════════════════════
def gloomhorn():
    M = {
        "fur": ("fur", (46, 43, 58), (78, 72, 96)),
        "fur_dk": ("fur", (30, 28, 40), (52, 48, 66)),
        "bone": ("bone", (228, 220, 200), (170, 160, 142)),
        "bone_dk": ("bone", (182, 172, 152), (130, 122, 108)),
        "antler": ("bone", (104, 92, 100), (70, 62, 70)),
        "antler_hi": ("bone", (214, 208, 226), (160, 152, 176)),
        "hoof": ("obsidian", (24, 20, 34), (120, 90, 200)),
        "glow": ("glow", (90, 220, 255), (235, 255, 255)),
        "heart": ("glow", (150, 90, 255), (255, 250, 255)),
        "gold": ("metal", (214, 170, 84), (255, 230, 150)),
        "chain": ("metal", (110, 110, 124), (160, 160, 176)),
        "mist": ("flat", (150, 130, 220), (150, 130, 220)),
        "eye": ("glow", (120, 250, 255), (255, 255, 255)),
        "void": ("flat", (14, 10, 22), (14, 10, 22)),
    }
    R = Rig("sh_gloomhorn", M, seed=11)
    R.bone("root", pivot=(0, 0, 0))
    R.bone("body", "root", (0, 20, 0))
    # ── الجذع: مقدمة صلبة، قفص أضلاع مفتوح بالنص، ومؤخرة صلبة ──
    R.box("body", (-4.5, 15.5, -13), (9, 10.5, 6), "fur", top="fur_dk")          # الصدر
    R.box("body", (-4.5, 16, 4), (9, 10, 8), "fur", top="fur_dk")                # المؤخرة
    R.box("body", (-2, 24, -7), (4, 2, 11), "fur_dk")                            # العمود الفقري بين القسمين
    R.box("body", (-2.5, 15, -7), (5, 1.5, 11), "fur_dk")                        # البطن
    for k, z in enumerate((-6.2, -3.6, -1.0, 1.6)):                              # الأضلاع (أقواس عظم)
        for sx in (-1, 1):
            R.box("body", (sx * 4.25 - 0.4, 17, z), (0.8, 6.5, 1.1), "bone")     # جنب الضلع
            x0 = min(sx * 2.0, sx * 4.65)
            R.box("body", (x0, 23.5, z), (2.65, 1.0, 1.1), "bone_dk")             # فوق
            R.box("body", (min(sx * 2.4, sx * 4.65), 16.1, z), (2.25, 0.9, 1.1), "bone_dk")  # تحت
    for z in (-12, -8.5, -5, -1.5, 2, 5.5, 9):                                   # صفائح عظم على الظهر
        R.box("body", (-0.9, 26.0 if -7 < z < 4 else 26.0, z), (1.8, 1.2, 2.2), "bone", top="bone_dk")
    # ── القلب العائم داخل القفص ──
    R.bone("heart", "body", (0, 20, -1.5))
    R.boxc("heart", (0, 20, -1.5), (2.4, 2.4, 2.4), "heart")
    R.boxc("heart", (0, 20, -1.5), (3.2, 1.2, 1.2), "glow")
    R.boxc("heart", (0, 20, -1.5), (1.2, 3.2, 1.2), "glow")
    R.boxc("heart", (0, 20, -1.5), (1.2, 1.2, 3.2), "glow")
    # ── الرقبة: سميكة بعرف ضباب يتدلى ──
    R.bone("neck", "body", (0, 24, -11), rotation=[28, 0, 0])
    R.box("neck", (-2.6, 24, -13.4), (5.2, 10, 5.2), "fur")
    R.box("neck", (-3.0, 24.5, -14.6), (6.0, 5.0, 1.2), "fur_dk")                  # صدر الرقبة (لبدة)
    for k, y in enumerate((25.0, 27.6, 30.2, 32.6)):                                # عرف ضباب خلف الرقبة
        R.box("neck", (-1.0, y, -8.2), (2.0, 2.2, 1.0 + 0.3 * (k % 2)), "mist" if k % 2 else "fur_dk")
    # ── الراس: قناع عظم طويل، فك، حاجب، عيون متوهجة، ورون مضيء على الجبهة ──
    R.bone("head", "neck", (0, 33.5, -11), rotation=[-30, 0, 0])
    R.box("head", (-2.8, 32.6, -15.8), (5.6, 5.4, 6.8), "bone", top="bone")          # الجمجمة
    R.box("head", (-2.0, 33.3, -21.2), (4.0, 3.0, 5.4), "bone_dk", top="bone")       # الخطم العلوي
    R.box("head", (-1.7, 31.4, -20.6), (3.4, 1.9, 4.8), "bone_dk")                    # الفك
    R.box("head", (-1.1, 34.4, -21.6), (2.2, 1.3, 0.4), "void")                       # الأنف
    R.box("head", (-1.4, 32.9, -20.9), (2.8, 0.4, 0.3), "void")                       # خط الفم
    R.box("head", (-3.2, 36.6, -16.1), (6.4, 1.0, 3.6), "bone_dk")                    # الحاجب
    R.box("head", (-0.6, 36.9, -16.5), (1.2, 1.6, 0.4), "glow")                       # رون الجبهة
    R.box("head", (-0.25, 38.5, -16.4), (0.5, 0.8, 0.3), "glow")
    for sx in (-1, 1):
        R.box("head", (sx * 2.8 + (0 if sx > 0 else -0.4), 34.4, -15.2), (0.4, 1.6, 2.2), "void")   # تجويف العين
        R.box("head", (sx * 3.2 + (0 if sx > 0 else -0.35), 34.7, -14.9), (0.35, 1.0, 1.6), "eye")  # العين
        en = f"ear_{'l' if sx > 0 else 'r'}"
        R.bone(en, "head", (sx * 2.6, 36.6, -10.8))
        R.box(en, (min(sx * 2.6, sx * 5.4), 36.2, -11.6), (2.8, 0.8, 1.6), "fur", top="fur_dk")
        R.box(en, (min(sx * 5.4, sx * 6.2), 36.4, -11.3), (0.8, 0.5, 1.0), "mist")
    # ── القرون: جذع متصل يرتفع ويتفرع (كل قطعة بزاوية اتجاهها)، أربع شعب لقدام/فوق، أطراف متوهجة ──
    R.bone("antlers", "head", (0, 37.5, -12))
    for sx in (-1, 1):
        R.boxc("antlers", (sx * 1.9, 37.9, -12.3), (2.4, 0.9, 2.4), "antler")        # حلقة القاعدة
        pts = [(1.9, 37.9, -12.3), (3.0, 40.4, -12.1), (4.5, 43.0, -11.6), (6.0, 45.6, -11.0), (7.1, 48.4, -10.2), (7.8, 51.2, -9.2), (8.0, 53.6, -8.2)]
        for i in range(len(pts) - 1):
            (x0, y0, z0), (x1, y1, z1) = pts[i], pts[i + 1]
            L = math.hypot(x1 - x0, y1 - y0)
            ang = -math.degrees(math.atan2(sx * (x1 - x0), y1 - y0))
            wdt = 1.7 - i * 0.18
            R.boxc("antlers", (sx * (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (wdt, L + 0.35, wdt),
                   "antler" if i < 3 else "antler_hi", rot=[0, 0, ang])
        R.boxc("antlers", (sx * 8.0, 54.4, -8.0), (0.8, 1.0, 0.8), "glow")
        # شعب: من نقاط الجذع لقدام وفوق (دوران x سالب = لفوق)
        for (bx, by, bz, L, rx) in ((2.6, 39.6, -12.2, 4.2, -38), (4.0, 42.2, -11.8, 5.2, -30), (5.6, 44.8, -11.2, 4.6, -22), (6.9, 47.8, -10.4, 3.4, -14)):
            R.box("antlers", (sx * bx - 0.45, by - 0.45, bz - L), (0.9, 0.9, L), "antler_hi", rot=[rx, 0, 0], pivot=(sx * bx, by, bz))
            R.box("antlers", (sx * bx - 0.3, by - 0.3, bz - L - 0.6), (0.6, 0.6, 0.6), "glow", rot=[rx, 0, 0], pivot=(sx * bx, by, bz))
        # فانوس روح معلق بسلسلة تحت الجذع (بعيد عن الراس)
        ln = f"lantern_{'l' if sx > 0 else 'r'}"
        lx = sx * 5.6
        R.bone(ln, "antlers", (lx, 44.2, -11.4))
        for k in range(3):
            R.box(ln, (lx - 0.25, 43.2 - k * 1.0, -11.65), (0.5, 0.9, 0.5), "chain")
        R.box(ln, (lx - 1.2, 39.9, -12.6), (2.4, 0.5, 2.4), "gold")                    # غطا
        R.box(ln, (lx - 1.2, 36.9, -12.6), (2.4, 0.5, 2.4), "gold")                    # قاعدة
        for cx, cz in ((-1.0, -12.4), (0.6, -12.4), (-1.0, -10.8), (0.6, -10.8)):
            R.box(ln, (lx + cx, 37.4, cz), (0.4, 2.5, 0.4), "gold")                     # أعمدة
        R.box(ln, (lx - 0.7, 37.7, -12.1), (1.4, 1.9, 1.4), "glow")                    # نار الروح
        R.box(ln, (lx - 0.35, 40.4, -11.75), (0.7, 0.6, 0.7), "gold")
    # ── الأرجل: نحيفة وطويلة، حوافر سبج، ضباب عند الكاحل ──
    for name, px, pz, back in (("leg_fl", 2.6, -10.5, False), ("leg_fr", -2.6, -10.5, False), ("leg_bl", 2.6, 8.5, True), ("leg_br", -2.6, 8.5, True)):
        R.bone(name, "body", (px, 18, pz))
        tw = 3.2 if back else 2.6
        R.box(name, (px - tw / 2, 10.5, pz - 1.6), (tw, 8.0, 3.2 if back else 2.8), "fur")          # الفخذ
        zo = 0.8 if back else -0.2
        R.box(name, (px - 0.8, 2.0, pz - 0.9 + zo), (1.6, 8.5, 1.6), "fur_dk")                     # الساق
        R.box(name, (px - 1.0, 0.0, pz - 1.3 + zo), (2.0, 2.0, 2.4), "hoof", top="hoof")           # الحافر
        R.box(name, (px - 1.15, 2.0, pz - 1.0 + zo), (2.3, 0.6, 1.8), "mist")                      # ضباب الكاحل
    # ── الذيل: خصلة ضباب ──
    R.bone("tail", "body", (0, 24, 12))
    R.box("tail", (-1.2, 21.5, 12), (2.4, 3.0, 2.0), "mist")
    R.box("tail", (-0.7, 19.6, 13.4), (1.4, 2.4, 1.4), "glow")
    return R


# ════════════════════════════ الرائي الأجوف (Hollow Seer) ════════════════════════════
def seer():
    M = {
        "robe": ("cloth", (60, 46, 122), (60, 46, 122)),
        "robe_dk": ("cloth", (36, 27, 78), (36, 27, 78)),
        "panel": ("cloth", (142, 98, 222), (142, 98, 222)),
        "gold": ("metal", (226, 184, 96), (255, 238, 164)),
        "gold_dk": ("metal", (170, 128, 60), (220, 180, 110)),
        "mask": ("bone", (242, 238, 230), (198, 192, 186)),
        "crack": ("flat", (54, 48, 66), (54, 48, 66)),
        "iris": ("glow", (255, 150, 30), (255, 236, 150)),
        "pupil": ("flat", (16, 10, 8), (16, 10, 8)),
        "core": ("glow", (255, 200, 110), (255, 255, 244)),
        "skin": ("bone", (150, 150, 174), (110, 110, 132)),
        "talon": ("obsidian", (38, 30, 52), (150, 110, 230)),
        "blade": ("metal", (210, 216, 234), (255, 255, 255)),
        "edge": ("glow", (166, 112, 255), (240, 226, 255)),
        "gem": ("glow", (120, 220, 255), (240, 255, 255)),
        "void": ("flat", (12, 8, 20), (12, 8, 20)),
    }
    R = Rig("sh_hollow_seer", M, seed=23)
    R.bone("root", pivot=(0, 0, 0))
    R.bone("body", "root", (0, 24, 0))
    # ── الرداء الجرسي: ثلاث طبقات تتوسع لتحت، حافة ذهب، ولوح أمامي فاتح ──
    tiers = ((18, 5, 9, 7), (13, 5, 11, 8.5), (8, 5, 13, 10))
    for y0, h, w, d in tiers:
        R.box("body", (-w / 2, y0, -d / 2), (w, h, d), "robe" if y0 != 13 else "robe_dk", top="robe_dk")
        R.box("body", (-1.3, y0 + 0.3, -d / 2 - 0.3), (2.6, h - 0.6, 0.3), "panel")             # لوح أمامي
        R.box("body", (-w / 2 - 0.3, y0 - 0.5, -d / 2 - 0.3), (w + 0.6, 0.5, d + 0.6), "gold" if y0 == 8 else "gold_dk")   # حواف
    # ── الخصر والحزام ──
    R.box("body", (-4.0, 23, -3.0), (8, 1.0, 6), "robe_dk")
    R.box("body", (-4.6, 23.0, -3.6), (9.2, 1.0, 0.4), "gold")
    R.box("body", (-4.6, 23.0, 3.2), (9.2, 1.0, 0.4), "gold")
    R.box("body", (-0.7, 22.8, -3.95), (1.4, 1.4, 0.35), "gem")
    # ── الجذع: عريض فوق، مجوف بالنص (إطار) والقلب يبين ──
    R.box("body", (-4.0, 24, -2.8), (8, 3.5, 5.6), "robe")                      # تحت الصدر
    R.box("body", (-5.0, 27.5, -3.0), (3.4, 6.0, 6.0), "robe")                  # يسار
    R.box("body", (1.6, 27.5, -3.0), (3.4, 6.0, 6.0), "robe")                   # يمين
    R.box("body", (-1.6, 31.5, -3.0), (3.2, 2.0, 6.0), "robe")                  # فوق الفتحة
    R.box("body", (-1.6, 27.5, -1.0), (3.2, 0.6, 2.0), "robe_dk")               # قاعدة الفتحة (القلب فوقها)
    for (x, y, w, h) in ((-2.0, 27.3, 4.0, 0.4), (-2.0, 31.5, 4.0, 0.4), (-2.0, 27.3, 0.4, 4.6), (1.6, 27.3, 0.4, 4.6)):
        R.box("body", (x, y, -3.35), (w, h, 0.35), "gold")                       # إطار الفتحة قدام
        R.box("body", (x, y, 3.0), (w, h, 0.35), "gold")                         # وورا
    R.bone("core", "body", (0, 29.7, 0))
    R.boxc("core", (0, 29.7, 0), (2.0, 2.0, 2.0), "core")
    R.boxc("core", (0, 29.7, 0), (2.9, 0.7, 0.7), "core")
    R.boxc("core", (0, 29.7, 0), (0.7, 2.9, 0.7), "core")
    # ── الوشاح: شريطين ينزلن من الكتف قدام الصدر والرداء ──
    for sx in (-1, 1):
        R.box("body", (sx * 2.7 - 0.7, 24.0, -3.45), (1.4, 9.5, 0.3), "panel")
        R.box("body", (sx * 2.9 - 0.7, 9.0, -5.6), (1.4, 14.0, 0.3), "panel")
        R.box("body", (sx * 2.9 - 0.7, 8.4, -5.65), (1.4, 0.6, 0.35), "gold")
    # ── الكتافات الكبيرة: طبقتين بحافة ذهب وأشواك ──
    for sx in (-1, 1):
        R.box("body", (min(sx * 4.6, sx * 8.4), 31.5, -3.4), (3.8, 3.0, 6.8), "robe_dk", top="gold_dk")
        R.box("body", (min(sx * 5.2, sx * 9.0), 30.9, -3.7), (3.8, 0.6, 7.4), "gold")
        R.box("body", (min(sx * 5.0, sx * 7.6), 34.5, -2.8), (2.6, 1.2, 5.6), "robe", top="gold")
        for z in (-2.0, 0.0, 2.0):
            R.box("body", (sx * 7.4 - 0.35, 35.7, z - 0.35), (0.7, 1.4, 0.7), "gold")
    # ── الأذرع الطويلة: زند، كم جرسي، كف، ومخالب ──
    for sx, nm in ((1, "arm_l"), (-1, "arm_r")):
        R.bone(nm, "body", (sx * 6.4, 33, 0), rotation=[0, 0, sx * 12])
        R.box(nm, (min(sx * 5.5, sx * 7.4), 24.0, -0.95), (1.9, 8.5, 1.9), "robe")
        R.box(nm, (min(sx * 4.8, sx * 8.2), 18.0, -1.7), (3.4, 6.0, 3.4), "robe_dk", top="panel")
        R.box(nm, (min(sx * 4.6, sx * 8.4), 17.4, -1.9), (3.8, 0.6, 3.8), "gold")
        hn = f"hand_{'l' if sx > 0 else 'r'}"
        R.bone(hn, nm, (sx * 6.5, 17.4, 0))
        R.box(hn, (sx * 6.5 - 0.85, 14.6, -0.85), (1.7, 2.8, 1.7), "skin")
        for k, dx in enumerate((-0.6, 0.0, 0.6)):
            L = 4.8 if k == 1 else 4.0
            R.box(hn, (sx * 6.5 + dx - 0.2, 14.6 - L, -0.95 + k * 0.06), (0.4, L, 0.5), "talon")
            R.box(hn, (sx * 6.5 + dx - 0.15, 14.6 - L - 0.6, -0.9 + k * 0.06), (0.3, 0.6, 0.4), "edge")
    # ── الراس: قلنسوة كبيرة بقمة مايلة لورا، تاج ذهب، وقناع خزفي بعين وحدة بحدقة شق ──
    R.bone("head", "body", (0, 34, 0))
    R.box("head", (-4.0, 34, -3.6), (8, 9, 7.6), "robe", top="robe_dk")
    R.box("head", (-3.0, 43, -1.2), (6.0, 2.2, 5.6), "robe_dk")
    R.box("head", (-2.0, 45.2, 0.6), (4.0, 1.6, 4.0), "robe_dk")
    R.box("head", (-1.0, 46.8, 2.2), (2.0, 1.4, 2.4), "robe")
    R.box("head", (-4.3, 41.6, -3.95), (8.6, 0.7, 0.35), "gold")                  # التاج قدام
    R.box("head", (-0.6, 42.3, -4.0), (1.2, 1.6, 0.4), "gem")
    # القناع: بيضوي (صفوف تتسع بالنص) بحافة ذهب، وبنصه عين وحدة دائرية: محجر غامق، قزحية برتقالية بحلقة،
    # بؤبؤ دائري، ولمعة. كل طبقة لقدام من اللي قبلها (بدون تطابق وجوه).
    rows = [(34.3, 3.0), (35.1, 4.8), (35.9, 5.8), (36.7, 6.2), (37.5, 6.2), (38.3, 5.8), (39.1, 4.8), (39.9, 3.0)]
    for y, w in rows:
        R.box("head", (-w / 2, y, -3.95), (w, 0.8, 0.35), "mask")
    for y, w in ((34.0, 2.6), (40.7, 2.6)):
        R.box("head", (-w / 2, y, -3.85), (w, 0.3, 0.3), "gold")
    for sx in (-1, 1):
        R.box("head", (sx * 3.3 - 0.15, 35.4, -3.85), (0.3, 4.0, 0.3), "gold")
    def disc(cy, radius, z0, depth, mat, step=0.4):
        y = -radius + step / 2
        while y < radius:
            w = 2 * math.sqrt(max(0.0, radius * radius - y * y))
            if w > 0.05:
                R.box("head", (-w / 2, cy + y - step / 2, z0), (w, step, depth), mat)
            y += step
    EYE_Y = 37.1
    disc(EYE_Y, 2.15, -4.12, 0.17, "void")                    # محجر غامق
    disc(EYE_Y, 1.85, -4.26, 0.14, "gold")                    # حلقة ذهب حول العين
    disc(EYE_Y, 1.55, -4.38, 0.12, "iris")                    # القزحية البرتقالية
    disc(EYE_Y, 0.7, -4.48, 0.1, "pupil", step=0.35)          # بؤبؤ دائري
    R.box("head", (-0.95, EYE_Y + 0.55, -4.56), (0.45, 0.45, 0.08), "mask")     # لمعة
    for (x, y, h) in ((-2.4, 38.6, 1.3), (-2.0, 34.8, 1.0), (2.1, 38.9, 1.1), (2.3, 35.0, 0.8)):
        R.box("head", (x, y, -4.06), (0.25, h, 0.1), "crack")
    # ── الهالة الكبيرة ورا الظهر: حلقة ذهب، ست شفرات للخارج، وجواهر عائمة ──
    R.bone("halo", "body", (0, 36, 6.0))
    for i in range(16):
        a = math.radians(i * 22.5)
        R.boxc("halo", (math.sin(a) * 8.6, 36 + math.cos(a) * 8.6, 6.0), (3.4, 0.7, 0.6), "gold", rot=[0, 0, -i * 22.5])
    for i in range(6):
        a = i * 60 + 30
        r = math.radians(a)
        R.boxc("halo", (math.sin(r) * 12.6, 36 + math.cos(r) * 12.6, 6.0), (1.6, 6.0, 0.5), "blade", rot=[0, 0, -a])
        R.boxc("halo", (math.sin(r) * 16.1, 36 + math.cos(r) * 16.1, 6.0), (0.8, 1.2, 0.42), "edge", rot=[0, 0, -a])
        R.boxc("halo", (math.sin(r) * 9.2, 36 + math.cos(r) * 9.2, 6.0), (1.2, 1.2, 0.8), "gold_dk", rot=[0, 0, -a])
        rg = math.radians(i * 60)
        R.boxc("halo", (math.sin(rg) * 10.6, 36 + math.cos(rg) * 10.6, 6.0), (0.9, 0.9, 0.9), "gem", rot=[0, 0, 45])
    # ── أشرطة ممزقة تحت الرداء تتموج ──
    for i, (x, z) in enumerate(((-5.4, -4.6), (-1.9, -5.1), (1.9, -5.1), (5.4, -4.6), (-6.3, 0.0), (6.3, 0.0), (-3.6, 4.9), (0.0, 5.2), (3.6, 4.9))):
        nm = f"rib_{i}"
        R.bone(nm, "body", (x, 7.5, z))
        R.box(nm, (x - 0.9, 2.6, z - 0.2), (1.8, 4.9, 0.4), "robe_dk" if i % 2 else "robe")
        R.box(nm, (x - 0.6, -0.6, z - 0.15), (1.2, 3.2, 0.3), "robe" if i % 2 else "panel")
        R.box(nm, (x - 0.3, -1.4, z - 0.1), (0.6, 0.8, 0.2), "gold")
    return R


# ════════════════════════════ ثعلب الحجاب (Veilfox): ثعلب أرواح بخمس أذيال، رتبة Grim ════════════════════════════
def veilfox():
    M = {
        "fur": ("fur", (44, 40, 66), (84, 76, 118)),
        "fur_dk": ("fur", (24, 22, 40), (46, 42, 70)),
        "white": ("fur", (236, 234, 248), (192, 188, 218)),
        "mask": ("bone", (242, 238, 234), (198, 190, 186)),
        "mark": ("flat", (196, 36, 74), (196, 36, 74)),
        "gold": ("metal", (218, 174, 88), (255, 232, 152)),
        "void": ("flat", (10, 8, 20), (10, 8, 20)),
        "flame": ("glow", (130, 96, 255), (235, 240, 255)),
        "flame_c": ("glow", (80, 200, 255), (240, 255, 255)),
        "eye": ("glow", (190, 120, 255), (255, 240, 255)),
        "paw": ("obsidian", (20, 18, 32), (110, 90, 190)),
        "rope": ("cloth", (176, 40, 72), (232, 84, 114)),
        "bead": ("glow", (70, 210, 255), (230, 255, 255)),
    }
    R = Rig("sh_veilfox", M, seed=31)
    R.bone("root", pivot=(0, 0, 0))
    R.bone("body", "root", (0, 17, 0))
    # ── الجذع: صدر عريض، مؤخرة قوية، فخذين، وبطن أبيض ──
    R.box("body", (-4.1, 13.6, -9.4), (8.2, 8.4, 9.2), "fur", top="fur_dk")                # الصدر
    R.box("body", (-3.7, 14.0, -0.4), (7.4, 7.6, 9.0), "fur", top="fur_dk")                # المؤخرة
    for sx in (-1, 1):
        R.box("body", (sx * 3.7 - (0.9 if sx < 0 else 0), 13.2, 3.2), (0.9, 6.0, 5.2), "fur_dk")   # فخذ الأرجل الخلفية
        R.box("body", (sx * 4.1 - (0.7 if sx < 0 else 0), 14.6, -8.0), (0.7, 5.6, 4.6), "fur_dk")  # كتف
    R.box("body", (-2.9, 13.2, -6.5), (5.8, 1.5, 12.8), "white")                           # البطن
    R.box("body", (-1.5, 21.2, -8.0), (3.0, 1.0, 15.0), "fur_dk")                           # خط الظهر
    for z, h in ((-6.5, 0.9), (-3.5, 1.3), (-0.5, 1.0), (2.5, 1.4), (5.5, 1.0)):            # خصل بيضا على الجنب (فرو)
        for sx in (-1, 1):
            R.box("body", (sx * 3.95 - (0.5 if sx < 0 else 0), 13.3, z - 0.9), (0.5, h, 1.8), "white")
    for k, z in enumerate((-6.0, -2.0, 2.0, 6.0)):                                          # علامات بنفسجية على الجنب
        for sx in (-1, 1):
            R.box("body", (sx * 3.8 - (0.3 if sx < 0 else 0), 16.4, z), (0.3, 3.2, 1.0), "flame")
    for sx in (-1, 1):                                                                      # حلقة رون سماوية على الكتف
        for (dy, dz, w, h) in ((1.2, 0, 2.4, 0.4), (-1.2, 0, 2.4, 0.4), (0, 1.2, 0.4, 2.4), (0, -1.2, 0.4, 2.4)):
            R.box("body", (sx * 4.45 - (0.2 if sx < 0 else 0), 18.2 + dy, -6.0 + dz - h / 2 * (1 if dz == 0 else 0)), (0.2, h if dz == 0 else h, w if dz == 0 else w), "bead")
    # ── عرف لهب على الظهر (يرفرف) ──
    R.bone("mane", "body", (0, 22.0, -2.0))
    for k, (z, h) in enumerate(((-9.0, 3.4), (-6.5, 4.6), (-4.0, 5.8), (-1.5, 6.6), (1.0, 6.0), (3.5, 5.0), (6.0, 3.8), (8.0, 2.8))):
        R.box("mane", (-0.5, 22.0, z), (1.0, h * 0.85, 1.1), "flame_c" if k % 2 else "flame", rot=[-8 - k, 0, 0], pivot=(0, 22.0, z + 0.55))
        R.box("mane", (-0.3, 22.0 + h * 0.85, z + 0.15 - k * 0.1), (0.6, 1.2, 0.7), "eye")
    # ── الرقبة: لبدة بيضا كثيفة + طوق حبل أحمر + أجراس ذهب + خرز ماجاتاما ──
    R.bone("neck", "body", (0, 20, -8.0), rotation=[14, 0, 0])
    R.box("neck", (-2.7, 19.4, -11.2), (5.4, 6.8, 4.8), "fur", top="fur_dk")               # الرقبة
    R.box("neck", (-3.4, 19.4, -12.6), (6.8, 3.2, 6.0), "white")                            # لبدة
    R.box("neck", (-3.8, 17.6, -12.4), (7.6, 2.4, 2.4), "white")                            # لبدة الصدر
    for sx in (-1, 1):
        R.box("neck", (sx * 3.4 - (1.2 if sx < 0 else 0), 21.2, -11.8), (1.2, 2.6, 3.6), "white")  # خصل جانبية
    R.box("neck", (-3.5, 20.9, -12.8), (7.0, 0.7, 6.3), "rope")                             # الحبل
    for i in range(7):                                                                      # خرز سماوي قوسي على الصدر
        x = (i - 3) * 1.0
        R.box("neck", (x - 0.4, 18.0 - (3 - abs(i - 3)) * -0.25 - 0.8, -13.1), (0.8, 0.8, 0.6), "bead")
    for sx in (-1, 0, 1):
        R.box("neck", (sx * 2.0 - 0.45, 17.2, -13.0), (0.9, 1.1, 0.9), "gold")
    # ── الراس: خطم طويل + قناع كيتسوني أبيض + هلال ذهبي + خصل خدود ──
    R.bone("head", "neck", (0, 24.0, -10.0))
    R.box("head", (-3.1, 22.4, -15.2), (6.2, 5.2, 5.6), "fur", top="fur_dk")               # الجمجمة
    R.box("head", (-1.9, 22.4, -20.8), (3.8, 3.1, 5.8), "white")                            # الخطم
    R.box("head", (-1.1, 24.3, -21.4), (2.2, 1.2, 0.7), "void")                             # الأنف
    R.box("head", (-1.7, 21.9, -20.4), (3.4, 0.6, 5.0), "fur_dk")                           # الفم
    R.box("head", (-3.35, 22.2, -15.6), (6.7, 5.8, 0.5), "mask")                            # القناع
    R.box("head", (-2.1, 22.5, -15.82), (4.2, 0.5, 0.2), "mark")                            # خط أحمر تحت العيون
    R.box("head", (-0.5, 27.0, -15.82), (1.0, 1.5, 0.2), "mark")                            # علامة الجبهة
    for i, (x, y, w, h) in enumerate(((-1.4, 28.4, 0.8, 0.8), (-0.7, 28.9, 1.4, 0.7), (0.7, 28.4, 0.8, 0.8))):   # هلال ذهبي على الجبهة
        R.box("head", (x, y, -15.9), (w, h, 0.35), "gold")
    R.box("head", (-0.35, 29.7, -15.9), (0.7, 0.7, 0.35), "bead")
    for sx in (-1, 1):
        R.box("head", (sx * 2.1 - 0.95, 24.3, -15.95), (1.9, 0.7, 0.3), "void")             # شق العين
        R.box("head", (sx * 2.1 - 0.65, 24.45, -16.2), (1.3, 0.4, 0.2), "eye")
        R.box("head", (sx * 3.05 - (0.2 if sx < 0 else 0), 22.8, -15.95), (0.2, 1.9, 0.3), "mark")   # علامة الخد
        for k in range(3):                                                                  # خصل الخد
            R.box("head", (sx * (3.2 + k * 0.5) - (0.9 if sx < 0 else 0), 21.8 - k * 0.5, -15.0 + k * 1.3), (0.9, 0.8, 1.6), "white")
        en = f"ear_{'l' if sx > 0 else 'r'}"
        R.bone(en, "head", (sx * 2.2, 27.2, -12.8))
        R.box(en, (sx * 2.2 - 1.2, 27.2, -13.3), (2.4, 3.6, 1.6), "fur_dk")
        R.box(en, (sx * 2.2 - 0.8, 30.8, -13.0), (1.6, 2.8, 1.2), "fur_dk")
        R.box(en, (sx * 2.2 - 0.4, 33.6, -12.8), (0.8, 1.8, 0.8), "flame")
        R.box(en, (sx * 2.2 - 0.6, 27.6, -13.42), (1.2, 3.2, 0.2), "mark")
        R.box(en, (sx * 2.2 - 0.3, 28.5 if True else 0, -13.1), (0.6, 0.5, 2.0), "gold")   # حلقة ذهب
    # ── الأرجل: جوارب سوداء وحلقة رون سماوية عند الكاحل ──
    for nm, x, z in (("leg_fl", 2.4, -7.0), ("leg_fr", -2.4, -7.0), ("leg_bl", 2.4, 6.2), ("leg_br", -2.4, 6.2)):
        R.bone(nm, "body", (x, 16.0, z))
        R.box(nm, (x - 1.4, 7.5, z - 1.4), (2.8, 8.5, 2.8), "fur")
        R.box(nm, (x - 1.0, 1.2, z - 1.0), (2.0, 6.4, 2.0), "fur_dk")
        R.box(nm, (x - 1.3, 4.0, z - 1.3), (2.6, 0.5, 2.6), "bead")                         # حلقة رون
        R.box(nm, (x - 1.25, 0.0, z - 2.0), (2.5, 1.4, 3.2), "paw", top="paw")
    # ── خمس أذيال: كل ذيل ست عقل تتسع ثم تضيق وتنتهي بلهب ──
    for ti, (yaw, tilt, base_col) in enumerate(((-64, 44, "fur"), (-32, 54, "fur"), (0, 64, "white"), (32, 54, "fur"), (64, 44, "fur"))):
        tn = f"tail_{'abcde'[ti]}"
        R.bone(tn, "body", (0, 20.0, 8.0), rotation=[tilt, yaw, 0])
        parent, y, z = tn, 20.0, 8.0
        for k, (w, L) in enumerate(((3.6, 4.6), (4.8, 4.6), (5.4, 4.6), (5.2, 4.4), (4.4, 4.0), (3.4, 3.6))):
            sn = f"{tn}{k}"
            R.bone(sn, parent, (0, y, z), rotation=[-4, 0, 0])
            R.box(sn, (-w / 2, y - 1.0, z), (w, w, L), base_col if k < 5 else "flame")
            R.box(sn, (-w / 2 + 0.3, y - 0.7, z + 0.4), (w - 0.6, w - 0.6, L - 0.8), "white" if k % 2 else "fur_dk")
            if k in (1, 3):                                                                 # خصلة جانبية
                for sx in (-1, 1):
                    R.box(sn, (sx * (w / 2 + 0.2) - 0.4, y - 0.2, z + 0.6), (0.8, w * 0.5, L - 1.6), "white")
            parent, z = sn, z + L - 0.6
        R.box(parent, (-1.5, y - 0.6, z), (3.0, 3.0, 2.8), "flame_c")
        R.box(parent, (-0.8, y - 0.1, z + 2.6), (1.6, 1.6, 2.4), "eye")
    # ── كرات نار تدور حواليه ──
    R.bone("orbs", "body", (0, 20, 0))
    for k in range(5):
        a = k * 1.2566
        R.boxc("orbs", (math.cos(a) * 10.5, 24.0 + (k % 3) * 1.6, math.sin(a) * 10.5), (2.0, 2.0, 2.0), "flame_c")
        R.boxc("orbs", (math.cos(a) * 10.5, 24.0 + (k % 3) * 1.6, math.sin(a) * 10.5), (1.0, 3.2, 1.0), "eye")
    return R


# ════════════════════════════ ماغماموث (Magmamoth): ماموث بركاني، رتبة Vile ════════════════════════════
def magmamoth():
    M = {
        "rock": ("rock", (46, 44, 50), (92, 90, 98)),
        "rock_dk": ("rock", (28, 27, 32), (62, 60, 68)),
        "rock_rd": ("rock", (84, 32, 26), (146, 62, 34)),
        "magma": ("lava", (255, 116, 28), (255, 224, 96)),
        "magma_dk": ("lava", (200, 58, 18), (255, 140, 44)),
        "tusk": ("bone", (240, 176, 112), (255, 222, 168)),
        "tusk_dk": ("bone", (206, 124, 70), (170, 92, 52)),
        "eye": ("glow", (255, 196, 60), (255, 255, 210)),
        "void": ("flat", (12, 8, 8), (12, 8, 8)),
        "ember": ("glow", (255, 120, 24), (255, 232, 140)),
    }
    R = Rig("sh_magmamoth", M, seed=41)
    R.sc = (1.12, 0.9, 1.0)           # جسم أعرض (+12%) وارتفاع كلي ~3.8 بلوكة
    rnd = random.Random(5)
    R.bone("root", pivot=(0, 0, 0))
    R.bone("body", "root", (0, 34, 0))
    # ── اللب الحار (يبين من الشقوق بين صفائح الصخر) ──
    R.box("body", (-17.0, 22.0, -26.0), (34.0, 30.0, 26.0), "magma_dk")                    # المقدمة أعلى (سنام)
    R.box("body", (-17.0, 22.0, 0.0), (34.0, 22.0, 26.0), "magma_dk")                      # المؤخرة أخفض
    R.box("body", (-14.0, 17.0, -24.0), (28.0, 5.5, 48.0), "rock_dk")                      # أسفل البطن
    # ── صفائح الصخر على الظهر والجنبين (فجوات 0.8 بينها تتوهج) ──
    def chunk(x, y, z, w, h, d, mat):
        R.box("body", (x, y, z), (w, h, d), mat)
    zs = [-26 + i * 6.6 for i in range(8)]
    for xi, x in enumerate((-17.0, -11.0, -5.0, 1.0, 7.0, 13.0)):
        for zi, z in enumerate(zs):
            w, d = 5.4 + rnd.random() * 0.5, 5.8 + rnd.random() * 0.5
            h = 3.0 + rnd.random() * 3.5
            chunk(x + 0.4, 52.0 if zi < 4 else 44.0, z + 0.4, w, h, d, ("rock", "rock_dk", "rock", "rock_rd")[(xi * 3 + zi) % 4])
    for sx in (-1, 1):                                                                      # الجنبين
        for yi, y in enumerate((22.0, 28.2, 34.4, 40.6, 46.8)):
            for zi, z in enumerate(zs):
                if (zi >= 4 and y > 38.0) or (zi < 4 and y > 47.0 and False):
                    continue
                t = 2.4 + rnd.random() * 2.4
                x0 = 17.0 if sx > 0 else -17.0 - t
                chunk(x0, y + 0.3, z + 0.4, t, 5.2 + rnd.random() * 0.6, 5.8 + rnd.random() * 0.5, ("rock_dk", "rock", "rock_rd", "rock")[(yi + zi) % 4])
    # ── تاج الصخر على الكتف (مثل الصورة): كتل داكنة طويلة متفاوتة ──
    for i in range(34):
        x = rnd.uniform(-15, 13); z = rnd.uniform(-27, -3)
        h = rnd.uniform(4, 12) * (1.0 - 0.012 * abs(x) * 1.5)
        w = rnd.uniform(4.6, 7.0); d = rnd.uniform(4.6, 7.0)
        R.box("body", (x, 56.0, z), (w, h, d), ("rock_dk", "rock", "rock_dk", "rock_rd")[i % 4])
    for i in range(14):                                                                     # ظهر أخفض نحو الذيل
        x = rnd.uniform(-14, 12); z = rnd.uniform(2, 24)
        R.box("body", (x, 48.0, z), (rnd.uniform(4.4, 6.4), rnd.uniform(3, 7.5), rnd.uniform(4.4, 6.4)), ("rock", "rock_dk")[i % 2])
    for i in range(10):                                                                     # بقع جمر صغيرة بين الصخر
        x = rnd.uniform(-15, 14); z = rnd.uniform(-26, 24)
        R.box("body", (x, 51.6 if z < 0 else 43.6, z), (1.4, 0.6, 1.4), "magma")
    # ── الراس: بني أحمر ببروز صخري وعيون متوهجة وفم فرن ──
    R.bone("head", "body", (0, 40.0, -27.0))
    R.box("head", (-10.0, 26.0, -46.0), (20.0, 22.0, 20.0), "rock_rd")                      # الجمجمة
    R.box("head", (-11.0, 46.0, -46.0), (22.0, 4.0, 18.0), "rock_dk")                       # صفيحة الجبهة
    for i in range(7):
        R.box("head", (-9.5 + i * 3.0, 50.0, -45.0 + (i % 3) * 3.0), (3.4, 4.0 + (i % 3) * 2, 3.8), "rock" if i % 2 else "rock_dk")
    for sx in (-1, 1):
        x0 = 10.0 if sx > 0 else -12.0
        R.box("head", (x0, 28.0, -44.0), (2.0, 16.0, 14.0), "rock")                          # الخد (صفيحة)
        R.box("head", (x0 + (0.0 if sx > 0 else 1.7), 33.0, -43.0), (0.3, 6.0, 1.0), "magma")     # عرق خد
        R.box("head", (sx * 6.0 - 2.4, 38.0, -46.35), (4.8, 2.6, 0.7), "void")               # محجر العين
        R.box("head", (sx * 6.0 - 2.0, 38.4, -46.9), (4.0, 1.8, 0.7), "eye")                  # العين
    R.box("head", (-4.5, 27.0, -46.3), (9.0, 6.0, 0.8), "magma")                             # الفم/الفرن
    R.box("head", (-3.0, 28.0, -46.9), (6.0, 3.6, 0.6), "ember")
    R.box("head", (-0.7, 40.0, -46.2), (1.4, 8.0, 0.5), "magma")                             # شق جبهة
    for sx in (-1, 1):                                                                      # الأذان
        en = f"ear_{'l' if sx > 0 else 'r'}"
        R.bone(en, "head", (sx * 10.0, 44.0, -34.0))
        x0 = 10.0 if sx > 0 else -10.0 - 9.0
        R.box(en, (x0, 36.0, -36.0), (9.0, 15.0, 2.4), "rock_dk")
        R.box(en, (x0 + (0.0 if sx > 0 else 8.4), 36.0, -36.2), (0.6, 14.0, 2.8), "magma")
    # ── الخرطوم: سلسلة عظام تنزل وتنحني، حلقات جمر، وفوهة ──
    R.bone("trunk0", "head", (0, 36.0, -46.0), rotation=[6, 0, 0])
    parent, y, z = "trunk0", 36.0, -46.0
    for k, (w, L) in enumerate(((11.0, 9.0), (10.0, 9.0), (9.0, 8.0), (8.0, 8.0), (7.0, 7.0))):
        nm = f"trunk{k}"
        if k: R.bone(nm, parent, (0, y, z), rotation=[10, 0, 0])
        R.box(nm, (-w / 2, y - L, z - w / 2), (w, L, w), "rock_rd" if k % 2 == 0 else "rock")
        R.box(nm, (-w / 2 - 0.3, y - L + 1.0, z - w / 2 - 0.3), (w + 0.6, 1.4, w + 0.6), "magma")   # حلقة جمر
        R.box(nm, (-w / 2 - 0.3, y - 2.6, z - w / 2 - 0.3), (w + 0.6, 0.9, w + 0.6), "rock_dk")
        parent, y = nm, y - L + 0.6
    R.box(parent, (-2.6, y - 3.0, z - 2.6), (5.2, 3.0, 5.2), "ember")                        # الفوهة
    # ── الأنياب: سلسلة عظام تنزل لقدام ثم تلتف لبرا وفوق (J) ──
    for sx in (-1, 1):
        side = "l" if sx > 0 else "r"
        parent = "head"; y, z, x = 32.0, -44.0, sx * 12.0
        steps = ((7, 20, 6), (7, 22, 8), (7, 18, 8), (6, 8, 9), (6, -8, 9), (6, -24, 9), (5, -34, 8), (4, -40, 6))
        for k, (L, pitch, yaw) in enumerate(steps):
            nm = f"tusk_{side}{k}"
            R.bone(nm, parent, (x, y, z), rotation=[pitch, sx * yaw, 0])
            w = 10.0 - k * 0.95
            R.box(nm, (x - w / 2, y - w / 2, z - L), (w, w, L), "tusk" if k % 2 == 0 else "tusk_dk")
            R.box(nm, (x - w / 2 - 0.25, y + w / 2 - 0.9, z - L + 1.0), (w + 0.5, 0.8, L - 2.0), "magma") if k in (0, 1) else None
            parent, z = nm, z - L
        R.box(parent, (x - 0.9, y - 0.9, z - 1.8), (1.8, 1.8, 1.8), "eye")                    # رأس النَّاب متوهج
    # ── الأرجل: أعمدة صخر بعروق جمر وأقدام ثقيلة ──
    for nm, x, z in (("leg_fl", 16.0, -19.0), ("leg_fr", -16.0, -19.0), ("leg_bl", 16.0, 19.0), ("leg_br", -16.0, 19.0)):
        R.bone(nm, "body", (x, 26.0, z))
        R.box(nm, (x - 7.0, 6.0, z - 7.0), (14.0, 20.0, 14.0), "rock_rd")
        for k in range(4):
            R.box(nm, (x - 7.4 + (k % 2) * 8.4, 8.0 + k * 4.4, z - 7.4 + (k // 2 % 2) * 8.4), (6.6, 4.0, 6.6), ("rock", "rock_dk")[(k + int(z > 0)) % 2])
        for sx in (-1, 1):
            R.box(nm, (x + sx * 7.15 - 0.15, 8.0, z - 0.5), (0.3, 14.0, 1.0), "magma")         # عرق جانبي
        R.box(nm, (x - 0.5, 8.0, z - 7.2), (1.0, 14.0, 0.4), "magma")                         # عرق أمامي
        R.box(nm, (x - 8.4, 0.0, z - 8.4), (16.8, 6.4, 16.8), "rock_dk")                       # القدم
        for k in range(3):
            R.box(nm, (x - 7.2 + k * 5.2, 0.4, z - 9.6), (4.4, 5.0, 2.0), "rock")             # أصابع حجر
        R.box(nm, (x - 8.7, 5.9, z - 8.7), (17.4, 0.9, 17.4), "magma_dk")                      # حلقة جمر عند الكاحل
    # ── الذيل ──
    R.bone("tail", "body", (0, 42.0, 26.0))
    for k in range(4):
        R.box("tail", (-1.6 + 0.0, 40.0 - k * 4.0, 26.0 + k * 1.2), (3.2, 4.4, 3.2), "rock_dk" if k % 2 else "rock")
    R.box("tail", (-2.4, 23.5, 30.5), (4.8, 5.0, 4.8), "ember")
    return R


def main():
    a = gloomhorn(); na = a.save(3.3)
    b = seer(); nb = b.save(2.8)
    d = veilfox(); nd = d.save(2.2)
    hot = {"magma": ("lava", (255, 176, 56), (255, 248, 190)), "magma_dk": ("lava", (255, 120, 32), (255, 220, 120)),
           "ember": ("glow", (255, 190, 60), (255, 255, 235)), "eye": ("glow", (255, 240, 120), (255, 255, 255))}
    e = magmamoth(); ne = e.save(4.2, hot=hot, width=7)
    print(f"gloomhorn cubes={na}  seer cubes={nb}  veilfox cubes={nd}  magmamoth cubes={ne}")


if __name__ == "__main__":
    main()
