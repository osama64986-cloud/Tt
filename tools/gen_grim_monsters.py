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
            elif kind == "pelt":        # فرو بكسلات 2×2 بدرجات (مثل دب ماينكرافت) وشعرات أغمق عمودية
                v = BLK.setdefault((id(rnd), base, alt, "p", x // 2, y // 2), rnd.uniform(-1, 1))
                t = 0.42 + 0.22 * v + 0.04 * n
                if (x * 5 + (y // 3) * 7) % 11 == 0:                # شعرات أغمق قصيرة (عمودية)
                    t -= 0.3
                elif (x * 3 + (y // 2) * 5) % 17 == 0:              # لمعة فرو
                    t += 0.25
                c = tuple(clamp(base[i] + (alt[i] - base[i]) * t) for i in range(3))
            elif kind == "shag":        # فرو ماينكرافت (مثل الذئب/دب القطب): لون أساسي هادئ، شعرات غامقة قصيرة عمودية متفرقة، ولمعات فاتحة قليلة
                dark = BLK.setdefault((id(rnd), base, alt, "sd", x, y // 3), rnd.random()) < 0.16
                lite = BLK.setdefault((id(rnd), base, alt, "sl", x, y // 2), rnd.random()) < 0.10
                t = 0.42 + 0.06 * n - (y / TILE - 0.5) * 0.12
                if dark:
                    t -= 0.22
                elif lite:
                    t += 0.24
                c = tuple(clamp(base[i] + (alt[i] - base[i]) * t) for i in range(3))
            elif kind == "wool":        # صوف ماموث: خصل عمودية (كل عمود بطوره)، رأس كل خصلة غامق وتحته لمعة، وتفاوت بين الأعمدة
                ph = BLK.setdefault((id(rnd), base, alt, "wp", x), rnd.randint(0, 5))
                vx = BLK.setdefault((id(rnd), base, alt, "wv", x), rnd.uniform(-1, 1))
                k = (y + ph) % 6
                t = 0.42 + 0.16 * vx + 0.04 * n
                if k == 0:
                    t -= 0.3
                elif k == 1:
                    t += 0.22
                elif k == 5:
                    t -= 0.1
                c = tuple(clamp(base[i] + (alt[i] - base[i]) * t) for i in range(3))
            elif kind == "chitin":      # درع حشرة (عقرب): أحزمة أفقية 4 بكسل، سطر لمعة فوق كل حزام وفاصل غامق تحته، وتفاوت كتل 4×4 ونقاط رمل
                band = y % 4
                v = BLK.setdefault((id(rnd), base, alt, "ch", x // 4, y // 4), rnd.uniform(-1, 1))
                t = 0.45 + 0.12 * v + 0.04 * n
                if band == 0:
                    t -= 0.22
                elif band == 3:
                    t += 0.34
                if rnd.random() < 0.03:
                    t -= 0.3
                c = tuple(clamp(base[i] + (alt[i] - base[i]) * t) for i in range(3))
            elif kind == "leaf":        # ورقة (أجنحة السرعوف): عرق وسطي غامق عمودي وعروق جانبية مايلة كل 5 بكسل، ولمعة خفيفة بين العروق
                d = x - 15.5
                vein = abs(d) < 1.0 or (abs(d) > 1.5 and (y + abs(d) * 0.8) % 5 < 0.9)
                t = 0.62 + 0.05 * n + (0.08 if (x + y) % 9 == 0 else 0)
                if vein:
                    t = 0.18 + 0.04 * n
                c = tuple(clamp(alt[i] + (base[i] - alt[i]) * t) for i in range(3))
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
        self.vmap = None               # دالة y -> y جديد (تمديد الأرجل وضغط الجسم)، تطبق على الجسم والأرجل
        self.rigid = {}                # عظمة جذر -> y الأصلي لمحور ربطها: كل أبنائها (راس، خرطوم، أنياب...) تنزاح بنفس المقدار بدون تشويه
        self.rnd = random.Random(seed)
        n = len(self.mats)
        self.cols = 4
        self.rows = math.ceil(n / self.cols)
        self.tw, self.th = self.cols * TILE, self.rows * TILE

    def _root(self, name):
        """الجذر الصلب (إن وجد) الذي تنتمي له العظمة، وإلا None (هيكلية: جسم/أرجل)"""
        seen = 0
        while name and seen < 40:
            if name in self.rigid:
                return name
            b = next((x for x in self.bones if x["name"] == name), None)
            name = b.get("parent") if b else None
            seen += 1
        return None

    def _dy(self, bone, y, h=0.0):
        """يرجع (y جديد، ارتفاع جديد) حسب القاعدة: صلب = إزاحة موحدة، هيكلي = خريطة f على الطرفين"""
        if not self.vmap:
            return y, h
        r = self._root(bone)
        if r is not None:
            return y + (self.vmap(self.rigid[r]) - self.rigid[r]), h
        y0, y1 = self.vmap(y), self.vmap(y + h)
        return y0, y1 - y0

    def bone(self, name, parent=None, pivot=(0, 0, 0), rotation=None):
        if self.vmap:
            r = self._root(parent) if parent else None
            if name in self.rigid:
                r = name
            if r is not None:
                pivot = (pivot[0], pivot[1] + (self.vmap(self.rigid[r]) - self.rigid[r]), pivot[2])
            else:
                pivot = (pivot[0], self.vmap(pivot[1]), pivot[2])
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

    def box(self, bone, o, s, mat, rot=None, pivot=None, top=None, bottom=None):
        """o = الزاوية الدنيا، s = الحجم، mat = المادة (top = مادة الوجه الفوقاني اختياري)."""
        sx, sy, sz = self.sc
        if self.vmap:
            r = self._root(bone)
            oy, hy = self._dy(bone, o[1], s[1])
            if pivot is not None:
                pivot = (pivot[0], pivot[1] + (self.vmap(self.rigid[r]) - self.rigid[r]) if r is not None else self.vmap(pivot[1]), pivot[2])
            o = (o[0], oy, o[2]); s = (s[0], hy, s[2])
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
              "west": face(mat, d, h, salt + 3), "up": face(top or mat, w, d, salt + 4), "down": face(bottom or mat, w, d, salt + 5)}
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

    def _dezfight(self):
        """يمنع الوميض (z-fighting): إذا وجهين من مكعبين بنفس الإطار (نفس دوران العظام والمكعب) بنفس المستوى والاتجاه ويتداخلون،
        المكعب الأحدث (التفصيلة اللي فوق) يطلع وجهه 0.035 لبرا. يرجع عدد الوجوه المصلحة"""
        E = 1e-4
        bones = {b["name"]: b for b in self.bones}
        def frame(n):
            ch = []
            while n:
                b = bones[n]
                if any(abs(v) > E for v in b.get("rotation", [0, 0, 0])):
                    ch.append(n)
                n = b.get("parent")
            return tuple(ch)
        groups = {}
        for b in self.bones:
            for c in b["cubes"]:
                key = (frame(b["name"]), tuple(c.get("rotation", ())), tuple(c.get("pivot", ())))
                groups.setdefault(key, []).append(c)
        fixed = 0
        for cs in groups.values():
            for _ in range(3):
                moved = 0
                for j in range(len(cs)):
                    b = cs[j]
                    for i in range(j):
                        a = cs[i]
                        for ax in range(3):
                            o1 = [k for k in range(3) if k != ax]
                            if any(min(a["origin"][k] + a["size"][k], b["origin"][k] + b["size"][k]) - max(a["origin"][k], b["origin"][k]) <= E for k in o1):
                                continue
                            for sg in (-1, 1):
                                pa = a["origin"][ax] + (a["size"][ax] if sg > 0 else 0)
                                pb = b["origin"][ax] + (b["size"][ax] if sg > 0 else 0)
                                if abs(pa - pb) < E:
                                    if sg < 0:
                                        b["origin"][ax] = round(b["origin"][ax] - 0.035, 4)
                                    b["size"][ax] = round(b["size"][ax] + 0.035, 4)
                                    moved += 1
                fixed += moved
                if not moved:
                    break
        return fixed

    def save(self, height_blocks, hot=None, width=5):
        """hot = {مادة: تعريف جديد}: يكتب نسخة ثانية من التكستشر (<الاسم>_hot.png) بنفس الـUV (للتوهج الأقوى)."""
        self.zfixed = self._dezfight()
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
    """ثعلب الحجاب v3: كيتسوني أنيق بنفس العظام (الأنميشن والمهارات ما تتغير).
    صدر عميق يضيق للخصر ثم أفخاذ قوية، أرجل نحيفة بجوارب غامقة، لبدة كريمية كثيفة بطبقات حول الرقبة بحبل أحمر وجرس ذهبي،
    قناع كيتسوني أبيض بعلامات قرمزية وعيون بنفسجية متوهجة، أذان طويلة مدببة بداخل كريمي ورأس لهب، وخمس أذيال منفوشة
    (تثخن بالنص بخصل بارزة، تتدرج من الغامق للكريمي، وتنتهي بلهب روح). الألوان مقللة: نيلي غامق + كريمي + لمسة بنفسجي/سماوي بالأطراف بس."""
    M = {
        "fur": ("pelt", (30, 26, 50), (96, 86, 134)),
        "fur_dk": ("pelt", (16, 14, 28), (56, 50, 84)),
        "cream": ("wool", (206, 198, 222), (255, 252, 255)),
        "cream_dk": ("wool", (160, 150, 182), (226, 220, 238)),
        "mask": ("bone", (246, 242, 236), (206, 198, 192)),
        "mark": ("flat", (212, 40, 62), (212, 40, 62)),
        "gold": ("metal", (222, 178, 90), (255, 232, 150)),
        "void": ("flat", (12, 10, 20), (12, 10, 20)),
        "flame": ("glow", (150, 100, 255), (240, 236, 255)),
        "flame_c": ("glow", (90, 210, 255), (240, 255, 255)),
        "eye": ("glow", (200, 130, 255), (255, 240, 255)),
        "paw": ("obsidian", (16, 14, 26), (90, 80, 140)),
        "rope": ("cloth", (180, 40, 70), (232, 86, 112)),
    }
    R = Rig("sh_veilfox", M, seed=37)
    R.bone("root", pivot=(0, 0, 0))
    R.bone("body", "root", (0, 17, 0))
    B = lambda o, s, m, **k: R.box("body", o, s, m, **k)
    # ── الجذع: صدر عميق، خصر أنحف، أفخاذ قوية، بطن كريمي، وحواف علوية أضيق (مقطع مدور) ──
    B((-3.8, 12.8, -9.8), (7.6, 8.6, 6.8), "fur", bottom="cream_dk")                         # الصدر
    B((-3.1, 14.0, -3.0), (6.2, 6.8, 6.0), "fur", bottom="cream_dk")                         # الخصر
    B((-3.6, 13.6, 3.0), (7.2, 7.2, 5.8), "fur", bottom="fur_dk")                            # الورك
    B((-2.4, 21.4, -9.0), (4.8, 0.9, 5.6), "fur_dk")                                         # أعلى الكتف
    B((-2.0, 20.8, -3.0), (4.0, 0.9, 11.0), "fur_dk")                                        # خط الظهر
    B((-2.6, 12.4, -8.6), (5.2, 1.0, 6.0), "cream")                                          # صدر/بطن كريمي
    for sx in (-1, 1):
        B((sx * 3.3 - (1.2 if sx < 0 else 0), 13.2, 3.4), (1.2, 6.4, 4.8), "fur_dk")         # الفخذ الخلفي
        B((sx * 3.5 - (0.8 if sx < 0 else 0), 14.4, -8.6), (0.8, 5.4, 4.2), "fur")          # الكتف
        for k, z in enumerate((-5.0, -1.0, 3.0)):                                            # خصل كريمية صغيرة على الجنب السفلي
            B((sx * 2.9 - (0.6 if sx < 0 else 0), 13.6, z), (0.6, 1.0 + (k % 2) * 0.4, 1.6), "cream_dk")
        B((sx * 3.55 - (0.25 if sx < 0 else 0), 17.0, -6.4), (0.25, 2.4, 0.5), "flame")     # علامة لهب صغيرة على الكتف
    # ── عرف روح رفيع على الظهر (يرفرف بالأنميشن) ──
    R.bone("mane", "body", (0, 22.0, -2.0))
    for k, (z, h) in enumerate(((-7.0, 1.6), (-4.4, 2.2), (-1.8, 2.4), (0.8, 2.0), (3.4, 1.4))):     # عرف فرو ناعم ورأس لهب صغير بس
        R.box("mane", (-0.7, 21.2, z), (1.4, h, 2.2), "fur_dk", rot=[-18, 0, 0], pivot=(0, 21.2, z + 1.1))
        R.box("mane", (-0.3, 21.2 + h - 0.2, z + 0.6 - h * 0.3), (0.6, 0.8, 0.8), "flame" if k % 2 == 0 else "flame_c")
    # ── الرقبة: لبدة كريمية كثيفة بطبقات + حبل أحمر + جرس ذهبي ──
    R.bone("neck", "body", (0, 20, -8.0), rotation=[14, 0, 0])
    N = lambda o, s, m, **k: R.box("neck", o, s, m, **k)
    N((-2.4, 19.6, -11.0), (4.8, 6.2, 4.4), "fur", top="fur_dk")
    N((-3.6, 17.4, -12.8), (7.2, 4.4, 5.6), "cream", top="cream")                            # اللبدة
    N((-4.1, 18.4, -12.2), (8.2, 2.8, 4.4), "cream_dk")
    for k in range(5):                                                                       # خصل اللبدة النازلة على الصدر
        x = -3.0 + k * 1.5
        N((x, 15.6 - (k % 2) * 0.6, -13.2), (1.2, 2.6 + (k % 2) * 0.6, 1.6), "cream")
    for sx in (-1, 1):
        N((sx * 3.9 - (1.4 if sx < 0 else 0), 19.0, -12.4), (1.4, 3.0, 3.6), "cream")        # خصل جانبية بارزة
    N((-3.7, 20.6, -12.95), (7.4, 0.7, 6.0), "rope")                                         # الحبل
    N((-0.6, 18.2, -13.6), (1.2, 1.3, 1.0), "gold")                                          # الجرس
    N((-0.2, 17.8, -13.7), (0.4, 0.4, 0.4), "void")
    # ── الراس: جمجمة، خطم مدبب بدرجتين، خدود منفوشة للجنب، قناع كيتسوني وعلامات قرمزية، وعيون بنفسجية ──
    R.bone("head", "neck", (0, 24.0, -10.0))
    H = lambda o, s, m, **k: R.box("head", o, s, m, **k)
    H((-2.9, 22.4, -15.4), (5.8, 5.0, 5.4), "fur", top="fur_dk")                             # الجمجمة
    H((-1.9, 22.4, -18.8), (3.8, 2.8, 3.6), "cream")                                         # بداية الخطم
    H((-1.3, 22.6, -21.0), (2.6, 2.0, 2.4), "cream")                                         # طرف الخطم
    H((-0.8, 24.0, -21.5), (1.6, 0.9, 0.7), "void")                                          # الأنف
    H((-1.6, 22.0, -20.4), (3.2, 0.5, 4.4), "fur_dk")                                        # الفك
    H((-3.1, 23.4, -15.7), (6.2, 4.4, 0.4), "mask")                                          # القناع
    H((-0.45, 25.8, -15.92), (0.9, 1.6, 0.2), "mark")                                        # علامة الجبهة
    H((-1.3, 27.0, -15.92), (2.6, 0.4, 0.2), "gold")                                         # هلال ذهبي صغير
    for sx in (-1, 1):
        H((sx * 1.6 - 0.9, 24.6, -15.92), (1.8, 0.6, 0.2), "void")                          # شق العين
        H((sx * 1.6 - 0.6, 24.7, -16.05), (1.2, 0.4, 0.2), "eye")
        H((sx * 2.4 - 0.25, 23.6, -15.95), (0.5, 0.9, 0.25), "mark")                        # كحل قرمزي
        H((sx * 1.2 - 0.2, 22.9, -18.85), (0.4, 1.4, 0.15), "mark")                         # خط على الخطم
        for k in range(3):                                                                   # خدود منفوشة للجنب
            H((sx * (2.9 + k * 0.55) - (0.9 if sx < 0 else 0), 22.2 - k * 0.45, -14.6 + k * 1.0), (0.9, 1.4 - k * 0.2, 1.6), "cream")
        en = f"ear_{'l' if sx > 0 else 'r'}"
        R.bone(en, "head", (sx * 2.2, 27.2, -12.8))
        R.box(en, (sx * 2.2 - 1.3, 27.2, -13.4), (2.6, 3.4, 1.8), "fur_dk")
        R.box(en, (sx * 2.2 - 0.9, 30.6, -13.2), (1.8, 2.8, 1.4), "fur_dk")
        R.box(en, (sx * 2.2 - 0.45, 33.4, -13.0), (0.9, 1.8, 1.0), "flame")
        R.box(en, (sx * 2.2 - 0.8, 27.6, -13.55), (1.6, 3.6, 0.2), "cream_dk")               # داخل الأذن
    # ── الأرجل: نحيفة بجوارب غامقة وكف ──
    for nm, x, z in (("leg_fl", 2.4, -7.0), ("leg_fr", -2.4, -7.0), ("leg_bl", 2.4, 6.2), ("leg_br", -2.4, 6.2)):
        R.bone(nm, "body", (x, 16.0, z))
        back = z > 0
        R.box(nm, (x - 1.3, 8.0, z - 1.3), (2.6, 8.0, 2.6), "fur")
        R.box(nm, (x - 0.9, 1.2, z - 0.9), (1.8, 6.8, 1.8), "fur_dk")
        if back:
            R.box(nm, (x - 0.8, 6.6, z + 0.6), (1.6, 2.2, 1.0), "fur_dk")                    # كعب الرجل الخلفية
        R.box(nm, (x - 1.15, 0.0, z - 1.8), (2.3, 1.3, 2.9), "paw", top="paw")
    # ── خمس أذيال منفوشة: كل عقلة لب + غلاف فرو أكبر + خصل بارزة، تتدرج للكريمي وتنتهي بلهب روح ──
    # كل عقلة تتداخل مع اللي بعدها (L + 0.6) فما تبين حلقات، والسطح العلوي أفتح شوي، والعقلتين الأخيرات كريمي (طرف الذيل الأبيض)
    seg = ((3.2, 4.4, "fur"), (4.4, 4.6, "fur"), (5.2, 4.8, "fur"), (5.0, 4.6, "fur"), (4.2, 4.0, "cream_dk"), (3.0, 3.6, "cream"))
    for ti, (yaw, tilt) in enumerate(((-64, 44), (-32, 54), (0, 64), (32, 54), (64, 44))):
        tn = f"tail_{'abcde'[ti]}"
        R.bone(tn, "body", (0, 20.0, 8.0), rotation=[tilt, yaw, 0])
        parent, y, z = tn, 20.0, 8.0
        for k, (w, L, mat) in enumerate(seg):
            sn = f"{tn}{k}"
            R.bone(sn, parent, (0, y, z), rotation=[-4, 0, 0])
            R.box(sn, (-w / 2, y - w / 2, z), (w, w, L + (0.6 if k < 5 else 0.0)), mat, top="cream" if k >= 4 else mat, bottom="fur_dk" if k < 4 else "cream_dk")
            if k == 2:                                                                       # نفشة جانبية بأعرض نقطة
                for sx in (-1, 1):
                    R.box(sn, (sx * (w / 2 - 0.1) - (0.7 if sx < 0 else 0), y - w / 2 + 1.0, z + 0.8), (0.7, w - 2.0, L - 1.4), "fur")
            parent, z = sn, z + L - 0.6
        R.box(parent, (-1.3, y - 1.3, z), (2.6, 2.6, 2.2), "flame")                          # لهب الروح بطرف الذيل
        R.box(parent, (-0.75, y - 0.75, z + 2.0), (1.5, 1.5, 1.6), "flame_c")
        R.box(parent, (-0.35, y - 0.35, z + 3.4), (0.7, 0.7, 1.0), "eye")
    # ── كرات نار الثعلب: لهب صغير طاير (قاعدة + لسان) ──
    R.bone("orbs", "body", (0, 20, 0))
    for k in range(5):
        a = k * 1.2566
        cx, cy, cz = math.cos(a) * 10.5, 24.0 + (k % 3) * 1.6, math.sin(a) * 10.5
        R.boxc("orbs", (cx, cy, cz), (1.8, 1.8, 1.8), "flame")
        R.boxc("orbs", (cx, cy + 1.4, cz), (1.0, 1.4, 1.0), "flame_c")
        R.boxc("orbs", (cx, cy + 2.4, cz), (0.5, 0.8, 0.5), "eye")
    return R


# ════════════════════════════ ماغماموث (Magmamoth): ماموث بركاني، رتبة Vile ════════════════════════════
def magmamoth():
    """ماغماموث v3: ماموث صوفي حقيقي بلمسة بركانية. نفس العظام والمحاور بالضبط (الأنميشن ومخرج النار من الخرطوم ما يتغيرون).
    الشكل: راس قبة عالي، سنام كتف واضح ينزل بانحدار للمؤخرة المدورة (شرائح بعرض يضيق لفوق = مقطع مدور)، صوف أشعث بطبقتين
    (طبقة وسطى وتنورة طويلة بحافة مسننة)، لحية صدر، صفائح بازلت متراكبة مايلة على خط الظهر بس (الصوف يبين على الجنبين) بفواصل ماغما،
    أنياب عاج تغمق نحو الرأس، خرطوم صوف بحلقات بازلت وجمر وفوهة جمر، وأحذية بازلت بحلقة جمر وأظافر عاج."""
    M = {
        "fur": ("wool", (70, 46, 36), (134, 92, 66)),
        "fur_dk": ("wool", (40, 28, 24), (82, 58, 44)),
        "fur_top": ("wool", (104, 66, 44), (170, 116, 78)),
        "fur_ember": ("wool", (126, 58, 30), (206, 118, 56)),
        "rock": ("rock", (48, 46, 52), (88, 86, 94)),
        "basalt": ("flat", (34, 32, 38), (34, 32, 38)),
        "magma": ("lava", (255, 116, 28), (255, 224, 96)),
        "magma_dk": ("lava", (200, 58, 18), (255, 140, 44)),
        "tusk": ("bone", (236, 220, 188), (255, 244, 214)),
        "tusk_dk": ("bone", (196, 166, 120), (150, 112, 74)),
        "eye": ("glow", (255, 196, 60), (255, 255, 210)),
        "ember": ("glow", (255, 120, 24), (255, 232, 140)),
    }
    R = Rig("sh_magmamoth", M, seed=43)
    R.sc = (1.12, 1.0, 1.0)
    R.vmap = lambda y: y * 1.53 if y <= 17 else (26.0 + (y - 17) * 0.8 if y <= 56 else 57.2 + (y - 56) * 0.5)
    R.rigid = {"head": 40.0, "tail": 42.0}
    rnd = random.Random(9)
    R.bone("root", pivot=(0, 0, 0))
    R.bone("body", "root", (0, 34, 0))
    B = lambda o, s, m, **k: R.box("body", o, s, m, **k)
    # ── الجذع بشرائح على طول الجسم: ارتفاع كل شريحة يتبع منحنى السنام، ومقطعها مدور (يضيق لفوق) ──
    prof = [(-27.0, 5.0, 56.0, 16.0), (-22.0, 5.0, 61.0, 16.5), (-17.0, 5.0, 64.0, 16.5), (-12.0, 5.0, 62.5, 16.5), (-7.0, 5.0, 59.0, 16.0),
            (-2.0, 5.0, 56.0, 15.5), (3.0, 5.0, 53.5, 15.0), (8.0, 5.0, 51.0, 14.5), (13.0, 5.0, 49.0, 14.0), (18.0, 5.0, 47.0, 13.5), (23.0, 4.0, 45.0, 12.5)]
    for z0, d, top, W in prof:
        B((-W, 18.0, z0), (2 * W, top - 24.0, d), "fur", bottom="fur_dk")
        B((-W + 3.0, top - 6.0, z0), (2 * W - 6.0, 4.0, d), "fur_top")
        B((-W + 6.5, top - 2.0, z0), (2 * W - 13.0, 2.0, d), "fur_top")
    B((-11.0, 22.0, 27.0), (22.0, 20.0, 2.0), "fur_dk")                                       # المؤخرة المدورة
    B((-13.0, 15.0, -24.0), (26.0, 3.0, 48.0), "fur_dk")                                      # البطن
    # ── صفائح بازلت متراكبة مايلة على خط الظهر بس، بفواصل ماغما، وأشواك جمر صغيرة على العمود الفقري ──
    for z0, d, top, W in prof[1:]:
        n = 3 if top > 52 else 2
        for i in range(n):
            w = 5.2 + rnd.random() * 1.2
            x = -n * 3.0 + i * 6.0 + rnd.uniform(-0.6, 0.6)
            y = top - 0.6 - abs(x + w / 2) * 0.28
            B((x, y, z0 - 0.6), (w, 1.8 + rnd.random() * 0.8, d + 1.0), "rock" if (i + int(z0)) % 3 else "basalt", top="rock",
              rot=[-12, 0, 0], pivot=[x + w / 2, y, z0 - 0.6])
        B((-n * 3.0 + 0.4, top - 0.5, z0 + d - 0.3), (n * 6.0 - 0.8, 0.5, 0.35), "magma")
    for z0, d, top, W in prof[:9]:
        B((-0.9, top + 1.4, z0 + 1.2), (1.8, 2.6, 2.0), "basalt")
        B((-0.5, top + 3.6, z0 + 1.6), (1.0, 1.0, 1.2), "magma")
    # ── الصوف الأشعث: طبقة وسطى على الجنب وتنورة طويلة بحافة مسننة، ولحية صدر، وصوف مؤخرة ──
    for sx in (-1, 1):
        for i in range(26):
            z = -26.0 + i * 1.95
            W = next(w for z0, d, top, w in reversed(prof) if z >= z0 - 0.01) if z >= prof[0][0] else prof[0][3]
            x_out = W + 0.2 if sx > 0 else -W - 2.0
            top_a = 44.0 - max(0, z) * 0.2
            la = 12.0 + (i * 5 % 4)
            B((x_out, top_a - la, z), (1.8, la, 1.9), ("fur", "fur_top", "fur", "fur_dk")[i % 4])            # الطبقة الوسطى
            lb = 14.0 + (i * 7 % 5) + (3.0 if z < -4 else 0.0)
            x_skirt = W + 1.0 if sx > 0 else -W - 2.8
            B((x_skirt, 30.0 - lb, z + 0.4), (1.8, lb, 1.6), ("fur_dk", "fur", "fur_ember", "fur", "fur_dk")[i % 5])   # التنورة
            if i % 6 == 2:
                B((x_skirt + (1.75 if sx > 0 else -0.25), 22.0, z + 0.7), (0.3, 6.0, 1.0), "magma_dk")    # عرق جمر بين الصوف
    for i in range(10):                                                                        # لحية الصدر (بين الرجلين الأماميتين)
        x = -12.0 + i * 2.6
        L = 13.0 + (i * 3 % 4) * 2.0
        B((x, 28.0 - L, -28.6), (2.4, L + 2.0, 2.2), ("fur_dk", "fur", "fur_ember", "fur")[i % 4])
    for i in range(8):                                                                         # صوف المؤخرة المتدلي
        x = -10.5 + i * 2.8
        B((x, 14.0 + (i % 3) * 1.5, 27.6), (2.4, 14.0 - (i % 3) * 1.5, 1.8), ("fur", "fur_dk")[i % 2])
    # ── الراس: قبة عالية مكسية صوف، خصلة غرة تتدلى على الجبهة، عيون صغيرة كهرمانية تحت حواجب صوف، تاج بازلت صغير بشق ماغما ──
    R.bone("head", "body", (0, 40.0, -27.0))
    H = lambda o, s, m, **k: R.box("head", o, s, m, **k)
    H((-9.0, 27.0, -44.0), (18.0, 23.0, 16.0), "fur", top="fur_top", bottom="fur_dk")
    H((-7.5, 50.0, -42.5), (15.0, 7.0, 14.0), "fur_top")
    H((-5.0, 57.0, -40.5), (10.0, 4.0, 10.0), "fur_top")
    H((-2.6, 61.0, -38.5), (5.2, 2.0, 6.0), "fur_top")
    for i in range(7):                                                                         # غرة الجبهة (خصل نازلة)
        x = -6.5 + i * 1.9
        H((x, 44.0 - (i % 3) * 1.5, -45.2), (1.8, 9.0 + (i % 3) * 1.5, 1.4), ("fur_top", "fur", "fur_top")[i % 3])
    for sx in (-1, 1):
        H((sx * 9.0 - (0.0 if sx > 0 else 2.4), 28.0, -43.5), (2.4, 17.0, 13.0), "fur_dk")     # خدود صوف
        H((sx * 6.3 - 1.2, 39.0, -44.6), (2.4, 1.6, 0.8), "eye")                               # عين صغيرة
        H((sx * 6.3 - 1.9, 40.6, -45.0), (3.8, 1.4, 1.2), "fur_dk")                            # حاجب صوف
    H((-3.0, 57.4, -44.0), (6.0, 2.4, 6.0), "basalt")                                          # تاج بازلت فوق القبة
    H((-0.5, 59.6, -43.0), (1.0, 1.2, 4.0), "magma")
    H((-4.2, 27.0, -45.0), (8.4, 6.0, 1.0), "fur_dk")
    for sx in (-1, 1):                                                                         # الأذان (صغيرة وصوف)
        en = f"ear_{'l' if sx > 0 else 'r'}"
        R.bone(en, "head", (sx * 10.0, 44.0, -34.0))
        x0 = 9.0 if sx > 0 else -9.0 - 6.0
        R.box(en, (x0, 37.0, -37.0), (6.0, 9.0, 2.6), "fur_dk")
        R.box(en, (x0 + (0.0 if sx > 0 else 5.4), 38.0, -37.3), (0.6, 7.0, 3.2), "fur_ember")
    # ── الخرطوم: صوف، حلقة بازلت وسطر جمر بكل عقلة، وفوهة جمر (مخرج النار) ──
    R.bone("trunk0", "head", (0, 36.0, -46.0), rotation=[6, 0, 0])
    parent, y, z = "trunk0", 36.0, -46.0
    for k, (w, L) in enumerate(((10.0, 9.0), (9.0, 9.0), (8.0, 8.0), (7.0, 8.0), (6.0, 7.0))):
        nm = f"trunk{k}"
        if k: R.bone(nm, parent, (0, y, z), rotation=[10, 0, 0])
        R.box(nm, (-w / 2, y - L, z - w / 2), (w, L, w), "fur" if k % 2 == 0 else "fur_top")
        R.box(nm, (-w / 2 - 0.3, y - L + 1.2, z - w / 2 - 0.3), (w + 0.6, 1.2, w + 0.6), "basalt")
        R.box(nm, (-w / 2 - 0.35, y - L + 2.4, z - w / 2 - 0.35), (w + 0.7, 0.5, w + 0.7), "magma")
        parent, y = nm, y - L + 0.6
    R.box(parent, (-2.4, y - 2.6, z - 2.4), (4.8, 2.6, 4.8), "ember")
    R.box(parent, (-3.0, y - 0.9, z - 3.0), (6.0, 1.0, 6.0), "basalt")
    # ── الأنياب: عاج يغمق نحو الرأس، عروق ماغما قرب الأصل، ورأس متوهج ──
    for sx in (-1, 1):
        side = "l" if sx > 0 else "r"
        parent = "head"; y, z, x = 32.0, -44.0, sx * 12.0
        steps = ((7, 20, 6), (7, 22, 8), (7, 18, 8), (6, 8, 9), (6, -8, 9), (6, -24, 9), (5, -34, 8), (4, -40, 6))
        for k, (L, pitch, yaw) in enumerate(steps):
            nm = f"tusk_{side}{k}"
            R.bone(nm, parent, (x, y, z), rotation=[pitch, sx * yaw, 0])
            w = 8.4 - k * 0.8
            R.box(nm, (x - w / 2, y - w / 2, z - L), (w, w, L), "tusk" if k < 5 else "tusk_dk", top="tusk")
            if k in (0, 1):
                R.box(nm, (x - w / 2 - 0.25, y + w / 2 - 0.9, z - L + 1.0), (w + 0.5, 0.7, L - 2.0), "magma")
            parent, z = nm, z - L
        R.box(parent, (x - 0.9, y - 0.9, z - 1.8), (1.8, 1.8, 1.8), "eye")
    # ── الأرجل: فخذ صوف أشعث (خصل متدلية حواليه)، حذاء بازلت بعروق جمر وحلقة جمر بالكاحل، وقدم عريضة بأظافر عاج ──
    for nm, x, z in (("leg_fl", 16.0, -19.0), ("leg_fr", -16.0, -19.0), ("leg_bl", 16.0, 19.0), ("leg_br", -16.0, 19.0)):
        R.bone(nm, "body", (x, 26.0, z))
        R.box(nm, (x - 6.5, 10.0, z - 6.5), (13.0, 16.0, 13.0), "fur", top="fur_top")
        for k in range(12):
            a = k * math.pi / 6
            cx, cz = x + math.cos(a) * 6.4, z + math.sin(a) * 6.4
            R.box(nm, (cx - 1.1, 7.5 + (k % 3) * 1.2, cz - 1.1), (2.2, 11.0 - (k % 3) * 1.2, 2.2), ("fur_dk", "fur", "fur_ember", "fur")[k % 4])
        R.box(nm, (x - 6.0, 2.0, z - 6.0), (12.0, 8.0, 12.0), "rock", top="basalt")
        for sx in (-1, 1):
            R.box(nm, (x + sx * 6.05 - 0.15, 3.0, z - 0.5), (0.3, 6.0, 1.0), "magma")
        R.box(nm, (x - 0.5, 3.0, z - 6.2), (1.0, 6.0, 0.4), "magma")
        R.box(nm, (x - 6.4, 9.4, z - 6.4), (12.8, 0.8, 12.8), "magma_dk")
        R.box(nm, (x - 7.4, 0.0, z - 7.4), (14.8, 2.4, 14.8), "basalt")
        for k in range(4):
            R.box(nm, (x - 6.2 + k * 3.4, 0.2, z - 8.4), (2.6, 2.0, 1.4), "tusk")
    # ── الذيل: قصير بخصلة صوف ونهاية جمر ──
    R.bone("tail", "body", (0, 42.0, 26.0))
    R.box("tail", (-3.0, 34.0, 27.0), (6.0, 8.0, 4.0), "fur_dk")
    for k in range(3):
        w = 4.4 - k * 0.8
        R.box("tail", (-w / 2, 30.0 - k * 3.6, 29.5 + k * 1.4), (w, 4.0, w), "fur" if k % 2 else "fur_dk")
    R.box("tail", (-2.6, 17.0, 32.5), (5.2, 6.0, 4.0), "fur_ember")
    R.box("tail", (-1.4, 16.0, 33.3), (2.8, 2.0, 2.4), "ember")
    return R


# ════════════════════════════ الدب الرمادي (Grey Bear، Vile): دب أشيب واقف على رجلين ════════════════════════════
# التصميم (v2): حدبة عضلات ضخمة على الكتف (علامة الدب الأشيب)، الراس أوطى من الحدبة ومايل لقدام، خطم طويل متدرج بخشم أسود،
# فرو مرسوم (شعرات + أفتح فوق وأغمق تحت) وخصل بارزة على الحواف تكسر الشكل الصندوقي، أطراف أغمق وظهر أشيب فضي،
# وقصة على جسمه: سهمين صيادين مكسورين مغروزين بالحدبة، قيد حديد مكسور بسلسلة على معصمه اليسار، وثلاث ندبات مخالب على عينه.
def _bear_mats():
    return {
        "fur": ("shag", (92, 88, 86), (138, 132, 126)),
        "fur_top": ("shag", (140, 136, 130), (196, 192, 186)),
        "fur_dk": ("shag", (54, 50, 50), (88, 84, 80)),
        "fur_under": ("shag", (64, 60, 60), (86, 82, 80)),
        "silver": ("shag", (168, 166, 162), (226, 224, 218)),
        "muzzle": ("shag", (164, 142, 112), (210, 190, 158)),
        "nose": ("flat", (22, 20, 24), (22, 20, 24)),
        "mouth": ("flat", (92, 28, 34), (92, 28, 34)),
        "bone": ("bone", (236, 230, 214), (132, 122, 110)),
        "eye": ("glow", (255, 166, 28), (255, 242, 196)),
        "pupil": ("flat", (24, 14, 10), (24, 14, 10)),
        "scar": ("flat", (150, 98, 100), (150, 98, 100)),
        "iron": ("metal", (90, 92, 98), (152, 154, 162)),
        "wood": ("cloth", (110, 78, 46), (140, 104, 64)),
        "feather": ("flat", (226, 224, 216), (226, 224, 216)),
        "feather_r": ("flat", (168, 44, 40), (168, 44, 40)),
        "bfur": ("wool", (84, 80, 78), (128, 122, 116)),          # فرو الجسم: خصل عمودية (v4)
        "bfur_top": ("wool", (124, 120, 114), (176, 172, 164)),
        "bfur_dk": ("wool", (50, 47, 47), (82, 78, 76)),
        "bfur_under": ("wool", (58, 54, 54), (82, 78, 76)),
        "bsilver": ("wool", (164, 162, 158), (222, 220, 214)),     # أطراف فضية للحدبة (Grizzled)
    }


def grey_bear():
    R = Rig("sh_grey_bear", _bear_mats(), seed=63)

    def mass(bone, cx, y0, cz, w, h, d, mat, top=None, bottom=None):
        """كتلة مستديرة (صندوقين متقاطعين بحواف مشطوفة)، مع وجه فوقاني/تحتاني بمادة مختلفة للتظليل"""
        R.box(bone, (cx - w / 2 + 1, y0, cz - d / 2), (w - 2, h, d), mat, top=top, bottom=bottom)
        R.box(bone, (cx - w / 2, y0 + 0.15, cz - d / 2 + 1), (w, h - 0.3, d - 2), mat, top=top, bottom=bottom)

    def tuft(bone, x, y, z, w, h, d, mat):
        R.box(bone, (x, y, z), (w, h, d), mat, top=mat, bottom="bfur_under" if mat != "bsilver" else mat)

    R.bone("root", pivot=(0, 0, 0))
    # ═══ الجسم v3 (تصميم بطل): أكتاف وصدر عريضين، خصر أنحف، وركين، أرجل ثابتة؛ وعباءة فرو فضية متراكبة على الحدبة ═══
    # ── الأرجل: فخذ، ساق، قدم مسطحة بمخالب لقدام على الأرض (مو مقلوبة) ──
    for sx, nm in ((1, "leg_l"), (-1, "leg_r")):
        cx = sx * 6.0
        R.bone(nm, "root", (cx, 19.0, 2.0))
        mass(nm, cx, 8.0, 2.5, 9.6, 12.0, 11.0, "bfur", top="bfur_top", bottom="bfur_under")
        R.box(nm, (cx - 3.6, 3.0, -1.4), (7.2, 6.0, 7.4), "bfur_dk", bottom="bfur_dk")
        R.box(nm, (cx - 4.2, 0.0, -7.5), (8.4, 3.2, 12.0), "bfur_dk", top="bfur_dk", bottom="nose")
        for k in range(4):
            R.box(nm, (cx - 3.4 + k * 2.2, 0.3, -9.7), (1.3, 1.3, 2.2), "bone")              # مخلب لقدام
            R.box(nm, (cx - 3.3 + k * 2.2, 0.0, -10.6), (1.1, 0.9, 1.0), "bone")             # طرفه ينحني للأرض
        tuft(nm, cx - 3.2, 10.5, 7.9, 2.8, 5.0, 1.3, "bfur")
        tuft(nm, cx + 0.4, 9.0, 7.9, 2.8, 5.6, 1.3, "bfur_top")
        tuft(nm, cx - 3.0, 3.0, 5.9, 6.0, 3.6, 1.2, "bfur_dk")
    # ── الوركين والخصر ──
    R.bone("body", "root", (0, 20.0, 2.0))
    mass("body", 0, 13.0, 2.5, 20.0, 10.0, 15.0, "bfur", top="bfur_top", bottom="bfur_under")       # الوركين
    mass("body", 0, 21.5, 2.0, 17.0, 9.0, 13.5, "bfur", top="bfur_top")                            # الخصر (أنحف من الصدر)
    mass("body", 0, 14.5, -5.6, 13.0, 9.0, 2.6, "bfur_top", bottom="bfur_under")                   # بطن فاتح
    for i in range(5):                                                                           # حافة البطن المشعثة
        tuft("body", -6.8 + i * 3.0, 12.2 - (i % 2) * 1.0, -6.5, 2.4, 3.0 + (i % 2), 1.2, "bfur_dk" if i % 2 else "bfur")
    R.bone("tail", "body", (0, 19.0, 10.0))
    mass("tail", 0, 16.6, 11.4, 4.6, 4.6, 3.8, "bfur_dk", top="bfur")
    # ── الصدر: صدر سفلي، ثم أكتاف أعرض (شكل V)، عضلات صدر فاتحة بهلال فضي، وندبات مخالب قديمة على الصدر ──
    R.bone("chest", "body", (0, 30.0, 2.0), rotation=[14, 0, 0])
    mass("chest", 0, 29.0, 1.5, 23.0, 7.0, 15.5, "bfur", top="bfur_top", bottom="bfur_under")
    mass("chest", 0, 35.5, 1.5, 28.0, 8.0, 17.0, "bfur", top="bfur_top", bottom="bfur_under")   # الأكتاف (أعرض جزء)
    for sx in (-1, 1):
        R.box("chest", (sx * 5.2 - 4.6, 34.6, -7.6), (9.2, 6.4, 1.0), "bfur_top")             # عضلات الصدر (فاتحة)
    for x, y, w, h in ((-8.6, 35.6, 3.2, 2.4), (-5.8, 33.9, 3.2, 2.4), (-2.7, 33.0, 5.4, 2.2), (2.6, 33.9, 3.2, 2.4), (5.4, 35.6, 3.2, 2.4)):
        R.box("chest", (x, y, -7.9), (w, h, 0.4), "bsilver")                                  # هلال فضي
    for k in range(3):                                                                       # ثلاث ندبات قديمة على الصدر
        R.box("chest", (-6.8 + k * 1.5, 36.4, -8.2), (0.5, 5.2, 0.3), "scar", rot=[0, 0, 32], pivot=[-6.55 + k * 1.5, 39.0, -8.05])
    # ── حدبة الكتف (علامة الدب الأشيب): شرائح على طول الظهر ترسم منحنى الحدبة (نفس طريقة الماموث) ──
    for (z0, dz, top, w) in ((-3.0, 3.0, 45.5, 18.0), (0.0, 3.0, 48.5, 20.0), (3.0, 3.0, 50.0, 20.5), (6.0, 3.0, 49.4, 19.5), (9.0, 2.6, 47.4, 17.0)):
        mass("chest", 0, 41.0, z0 + dz / 2, w, top - 43.0, dz + 2.0, "bfur", top="bfur_top")
        mass("chest", 0, top - 3.0, z0 + dz / 2, w - 5.0, 3.0, dz + 2.0, "bfur_top", top="bsilver")
    for sx in (-1, 1):                                                                         # خصل شيباء تكسر حافة الحدبة فوق الأكتاف
        for i, (z, y) in enumerate(((-1.0, 45.6), (2.6, 46.6), (6.2, 46.2), (9.4, 44.6))):
            x = sx * (9.4 - abs(i - 1.5) * 0.6)
            R.box("chest", (x - 0.8, y - 4.6, z), (1.6, 5.0, 3.0), ("bsilver", "bfur_top")[i % 2],
                  rot=[0, 0, -sx * 20], pivot=[x, y, z + 1.5])
    # ── فرو الظهر: ثلاث طبقات خصل متراكبة (مثل القش) تنزل من الحدبة للخصر، أطرافها مسننة، وتغمق كل ما تنزل (أشيب فوق) ──
    def drape(bone, y0, z, half, lens, mats, wdt=3.4):
        n = len(lens)
        for i, L in enumerate(lens):
            x = -half + i * (2 * half / (n - 1)) - wdt / 2
            R.box(bone, (x, y0 - L, z + (i % 2) * 0.22), (wdt, L, 1.3), mats[i % len(mats)])
    drape("chest", 48.2, 11.3, 7.6, (8.0, 9.6, 8.6, 10.2, 8.4, 9.8), ("bsilver", "bfur_top", "bfur_top", "bsilver"))
    drape("chest", 41.4, 10.0, 11.2, (6.4, 8.0, 7.0, 8.6, 7.4, 8.8, 6.6, 7.8), ("bfur_top", "bfur", "bfur", "bfur_top"))
    drape("body", 28.4, 8.7, 7.4, (7.0, 8.4, 7.6, 8.8, 7.2), ("bfur", "bfur_top", "bfur"))
    for sx in (-1, 1):                                                                         # أطراف مشعثة على جنب الخصر والورك
        for i in range(4):
            tuft("body", sx * 9.6 - (1.2 if sx < 0 else 0.0), 15.0 + i * 3.2 - (i % 2) * 0.6, -3.5 + i * 2.6, 1.2, 4.0, 2.4, ("bfur", "bfur_top")[i % 2])
    # ── ياقة الرقبة المتراكبة ──
    mass("chest", 0, 37.0, -7.6, 18.0, 6.5, 4.5, "bfur_top", top="bsilver")
    for i in range(6):
        tuft("chest", -8.0 + i * 3.0, 34.8 - (i % 2) * 0.8, -10.1, 2.4, 3.2 + (i % 2) * 1.2, 1.2, "bfur" if i % 2 else "bfur_top")
    # سهمين صيادين مكسورين مغروزين بالعباءة (قصته)
    for (ox, oy, oz, rx, ry) in ((4.5, 45.5, 9.0, -38, 24), (-5.5, 44.0, 9.8, -52, -28)):
        R.box("chest", (ox - 0.4, oy, oz), (0.8, 0.8, 7.5), "wood", rot=[rx, ry, 0], pivot=[ox, oy + 0.4, oz])
        R.box("chest", (ox - 0.1, oy - 0.6, oz + 5.3), (0.2, 2.0, 2.2), "feather", rot=[rx, ry, 0], pivot=[ox, oy + 0.4, oz])
        R.box("chest", (ox - 1.0, oy + 0.3, oz + 5.3), (2.0, 0.2, 2.2), "feather_r", rot=[rx, ry, 0], pivot=[ox, oy + 0.4, oz])
    # ── الراس: أوطى من الحدبة، جبهة ببروز، خطم طويل متدرج، خشم أسود، عيون كهرمانية بحدقة، أذان مدورة، خصل خدود، ندبات ──
    R.bone("head", "chest", (0, 41.0, -8.0), rotation=[-6, 0, 0])
    mass("head", 0, 37.0, -13.0, 15.0, 12.5, 13.0, "fur", top="fur_top", bottom="fur_under")
    R.box("head", (-5.0, 47.90, -19.60), (10.0, 1.8, 5.2), "fur", top="fur_top")          # الجبهة
    for sx in (-1, 1):
        R.box("head", (sx * 3.5 - 2.2, 46.25, -19.95), (4.4, 1.25, 1.0), "fur_dk", rot=[0, 0, sx * 22], pivot=[sx * 3.5, 46.9, -19.45])   # حاجب معصب: طرفه الداخلي نازل على العين (شكل V)
    mass("head", 0, 37.8, -22.0, 9.6, 6.0, 5.4, "muzzle", top="fur", bottom="fur_under")   # الخطم (ظهره فرو أغمق)
    R.box("head", (-3.4, 38.20, -26.40), (6.8, 4.2, 2.8), "muzzle", top="fur")            # طرف الخطم
    R.box("head", (-1.9, 41.20, -26.95), (3.8, 1.7, 1.3), "nose", top="nose")              # الخشم على حافة الطرف
    R.box("head", (-1.2, 39.40, -26.55), (2.4, 1.0, 0.2), "fur_under")                     # خط الفم تحت الخشم
    for sx in (-1, 1):
        R.box("head", (sx * 3.4 - 1.2, 44.80, -19.75), (2.4, 1.6, 0.4), "eye")                # عيون كهرمانية فوق الخطم
        R.box("head", (sx * 3.4 - 0.3, 44.85, -19.85), (0.6, 1.4, 0.2), "pupil")              # حدقة شق عمودي
        ex = 3.8 if sx > 0 else -7.8
        R.box("head", (ex, 48.00, -14.60), (4.0, 3.8, 2.4), "fur_dk")                      # أذن مدورة
        R.box("head", (ex + 0.6, 51.80, -14.30), (2.8, 0.8, 1.8), "fur_dk")
        R.box("head", (ex + 0.9, 48.70, -14.90), (2.2, 2.4, 0.4), "muzzle")
        tuft("head", 7.3 if sx > 0 else -8.9, 37.40, -18.60, 1.6, 6.4, 7.0, "fur")       # خصل الخدود (برا الجمجمة)
        tuft("head", 7.1 if sx > 0 else -8.7, 35.60, -16.80, 1.6, 2.6, 4.6, "fur_dk")
    for k in range(3):                                                               # ثلاث ندبات مخالب على العين اليسرى
        R.box("head", (2.3 + k * 1.1, 43.40, -19.62), (0.45, 4.6, 0.15), "scar", rot=[0, 0, -22], pivot=[2.5 + k * 1.1, 45.7, -19.55])
    R.bone("jaw", "head", (0, 39.6, -16.0))
    R.box("jaw", (-3.4, 35.80, -25.00), (6.8, 2.4, 7.4), "muzzle", bottom="fur_dk")
    R.box("jaw", (-2.9, 38.15, -24.60), (5.8, 0.4, 6.4), "mouth")
    for sx in (-1, 1):
        R.box("jaw", (sx * 2.2 - 0.4, 38.15, -24.80), (0.8, 1.5, 0.8), "bone")            # أنياب
    # ── الذراعين: دالية ضخمة ← عضد ← ساعد غامق بحلقة فرو ← كف (عظمة رسغ) مثني للأرض ومخالبه لقدام (مو مقلوبة) ──
    for sx, nm, fn, pn in ((1, "arm_l", "fore_l", "paw_l"), (-1, "arm_r", "fore_r", "paw_r")):
        cx = sx * 16.0
        R.bone(nm, "chest", (sx * 14.0, 42.0, 1.0), rotation=[-14, 0, -sx * 6])
        mass(nm, cx, 35.0, 1.0, 11.0, 9.5, 12.0, "bfur", top="bfur_top", bottom="bfur_under")     # الدالية
        mass(nm, cx + sx * 0.2, 28.0, 0.5, 9.0, 8.0, 9.6, "bfur", bottom="bfur_under")
        tuft(nm, cx - 3.6, 28.0, 4.9, 2.6, 6.0, 1.3, "bfur")
        tuft(nm, cx + 0.8, 27.0, 4.9, 2.6, 7.0, 1.3, "bfur_dk")
        R.bone(fn, nm, (cx + sx * 0.2, 28.5, 0.5), rotation=[-26, 0, 0])
        fx = cx + sx * 0.2
        mass(fn, fx, 18.0, 0.2, 8.6, 11.0, 8.8, "bfur_dk", top="bfur", bottom="bfur_dk")
        for (dx, dz) in ((-4.6, -1.2), (3.4, -1.2), (-1.2, 4.0), (-1.2, -5.0)):                  # حلقة فرو عند الرسغ
            tuft(fn, fx + dx, 16.8, dz + 0.2, 2.4 if abs(dx) < 2 else 1.2, 2.8, 1.2 if abs(dx) < 2 else 2.4, "bfur")
        if sx > 0:                                                                            # قيد حديد مكسور بسلسلة (قصته)
            R.box(fn, (fx - 4.7, 19.6, -4.6), (9.4, 2.4, 9.6), "iron", top="iron", bottom="iron")
            for k in range(3):
                R.box(fn, (fx + 4.4 - (k % 2) * 0.3, 18.8 - k * 1.7, -0.6 + (k % 2) * 0.4), (0.9, 1.9, 0.6), "iron", rot=[0, 0, (k % 2) * 30 - 10], pivot=[fx + 4.8, 19.7 - k * 1.7, -0.3])
        R.bone(pn, fn, (fx, 17.6, 0.2), rotation=[42, 0, 0])                                  # الرسغ مثني: باطن الكف للأرض
        mass(pn, fx, 12.4, -0.4, 10.0, 5.4, 10.6, "bfur_dk", top="bfur_dk", bottom="nose")
        R.box(pn, (fx - 3.8, 12.4, -5.75), (7.6, 2.0, 0.4), "bfur_dk")
        for k in range(4):
            R.box(pn, (fx - 3.7 + k * 2.4, 12.8, -8.3), (1.4, 1.6, 2.7), "bone")               # المخلب يطلع لقدام من أطراف الأصابع
            R.box(pn, (fx - 3.6 + k * 2.4, 11.6, -9.4), (1.2, 1.7, 1.2), "bone")               # طرفه منحني لتحت (مثل مخلب الدب الحقيقي)
    return R


# ── الجرو: موديل خاص (مو نسخة مصغرة): راس كبير بالنسبة لجسمه، أطراف قصيرة سمينة، عيون لامعة، أذان كبيرة، فرو أفتح ──
# نفس أسماء العظام (حتى يستعمل أنميشن الدب)، طوله ~1.2 بلوكة
def bear_cub():
    mats = _bear_mats()
    mats["fur"] = ("shag", (122, 118, 114), (168, 162, 156))
    mats["fur_top"] = ("shag", (170, 166, 160), (214, 210, 204))
    mats["eye"] = ("flat", (26, 20, 18), (26, 20, 18))
    mats["pupil"] = ("flat", (250, 250, 246), (250, 250, 246))
    R = Rig("sh_bear_cub", mats, seed=64)
    R.bone("root", pivot=(0, 0, 0))
    for sx, nm in ((1, "leg_l"), (-1, "leg_r")):
        cx = sx * 2.6
        R.bone(nm, "root", (cx, 6.5, 0.5))
        R.box(nm, (cx - 2.0, 1.5, -1.5), (4.0, 5.5, 4.4), "fur", top="fur_top", bottom="fur_under")
        R.box(nm, (cx - 2.2, 0.0, -3.0), (4.4, 1.8, 5.4), "fur_dk", bottom="nose")
    R.bone("body", "root", (0, 7.0, 0.5))
    R.box("body", (-4.5, 5.0, -3.5), (9.0, 7.5, 8.0), "fur", top="fur_top", bottom="fur_under")
    R.box("body", (-3.4, 5.8, -4.1), (6.8, 5.6, 0.8), "fur_top")                        # كرش فاتح
    R.bone("tail", "body", (0, 7.0, 4.5))
    R.box("tail", (-1.0, 6.0, 4.4), (2.0, 2.0, 1.6), "fur_dk")
    R.bone("chest", "body", (0, 12.0, 0.5), rotation=[6, 0, 0])
    R.box("chest", (-4.0, 11.5, -3.0), (8.0, 4.5, 7.0), "fur", top="fur_top", bottom="fur_under")
    R.box("chest", (-2.6, 12.8, -3.5), (5.2, 2.2, 0.6), "silver")                        # هلال صغير
    R.bone("head", "chest", (0, 15.5, -1.0), rotation=[-4, 0, 0])
    R.box("head", (-4.5, 15.0, -6.5), (9.0, 7.5, 7.5), "fur", top="fur_top", bottom="fur_under")
    R.box("head", (-2.2, 15.4, -8.8), (4.4, 3.0, 2.4), "muzzle", top="muzzle")
    R.box("head", (-1.0, 17.2, -9.2), (2.0, 1.2, 0.6), "nose")
    for sx in (-1, 1):
        R.box("head", (sx * 2.2 - 0.8, 18.4, -6.75), (1.6, 1.8, 0.4), "eye")              # عيون لامعة
        R.box("head", (sx * 2.2 - 0.5 + (0.4 if sx < 0 else 0), 19.3, -6.85), (0.5, 0.5, 0.2), "pupil")   # لمعة
        ex = 2.6 if sx > 0 else -5.6
        R.box("head", (ex, 21.6, -3.6), (3.0, 3.0, 1.6), "fur_dk")
        R.box("head", (ex + 0.7, 22.2, -3.8), (1.6, 1.8, 0.4), "muzzle")
    R.bone("jaw", "head", (0, 15.6, -5.0))
    R.box("jaw", (-1.8, 14.4, -8.6), (3.6, 1.2, 3.0), "muzzle")
    for sx, nm, fn in ((1, "arm_l", "fore_l"), (-1, "arm_r", "fore_r")):
        cx = sx * 5.0
        R.bone(nm, "chest", (sx * 4.2, 15.0, 0.5), rotation=[-12, 0, -sx * 8])
        R.box(nm, (cx - 1.7, 11.0, -1.3), (3.4, 4.6, 3.6), "fur", top="fur_top")
        R.bone(fn, nm, (cx, 11.2, 0.5), rotation=[-20, 0, 0])
        R.box(fn, (cx - 1.6, 7.4, -1.4), (3.2, 4.0, 3.4), "fur_dk", bottom="nose")
        for k in range(3):
            R.box(fn, (cx - 1.2 + k * 1.0, 6.6, -1.9), (0.6, 1.0, 0.8), "bone")
    return R

def main():
    a = gloomhorn(); na = a.save(3.3)
    b = seer(); nb = b.save(2.8)
    d = veilfox(); nd = d.save(2.2)
    hot = {"magma": ("lava", (255, 176, 56), (255, 248, 190)), "magma_dk": ("lava", (255, 120, 32), (255, 220, 120)),
           "ember": ("glow", (255, 190, 60), (255, 255, 235)), "eye": ("glow", (255, 240, 120), (255, 255, 255))}
    e = magmamoth(); ne = e.save(4.4, hot=hot, width=7)
    bhot = {"eye": ("glow", (255, 40, 30), (255, 210, 180)), "bone": ("bone", (255, 150, 130), (150, 40, 40)), "scar": ("flat", (210, 40, 40), (210, 40, 40))}   # الغضب: عيون حمرا ومخالب محمرة وندبات تحمر
    gb = grey_bear(); ng = gb.save(3.6, hot=bhot, width=4)
    cb = bear_cub(); cb.save(1.6, width=1.5)
    print(f"gloomhorn cubes={na}  seer cubes={nb}  veilfox cubes={nd}  magmamoth cubes={ne}  grey_bear cubes={ng}")


if __name__ == "__main__":
    main()
