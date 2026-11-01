"""تحسينات خفيفة لمجسمات الوحوش (قرون، أشواك، عيون متوهجة، دروع، لهب) بدون ما نخرب الموديلات الأصلية.
المصدر الأصلي محفوظ بـ tools/monster_src (نسخة قبل التعديل)، والسكربت يبني منها كل مرة (آمن لإعادة التشغيل).
الإضافات مكعبات UV لكل وجه تشير لشريط ألوان يُلصق أسفل التكستشر (يزيد 16 بكسل بالارتفاع).
التشغيل: python3 tools/gen_monster_mods.py
"""
import json
import os
import shutil

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "monster_src")
GEO = os.path.join(ROOT, "AnimePowers", "RP", "models", "entity")
TEX = os.path.join(ROOT, "AnimePowers", "RP", "textures", "entity")


class Mod:
    def __init__(self, name):
        self.name = name
        with open(os.path.join(SRC, f"sh_{name}.geo.json"), encoding="utf-8") as f:
            self.geo = json.load(f)
        self.g = self.geo["minecraft:geometry"][0]
        self.tex = Image.open(os.path.join(SRC, f"sh_{name}.png")).convert("RGBA")
        self.w, self.h = self.tex.size
        self.palette = []
        self.bones = {b["name"]: b for b in self.g["bones"]}

    def _uv(self, rgb):
        rgb = tuple(int(v) for v in rgb[:3])
        if rgb not in self.palette:
            assert len(self.palette) < 256
            self.palette.append(rgb)
        i = self.palette.index(rgb)
        return {"uv": [i % 16, self.h + i // 16], "uv_size": [1, 1]}

    def box(self, bone, x, y, z, w, h, d, color, top=None):
        """مكعب بزاوية دنيا (x,y,z) داخل عظمة موجودة."""
        m = self._uv(color)
        t = self._uv(top) if top else m
        cube = {"origin": [round(x, 3), round(y, 3), round(z, 3)], "size": [w, h, d],
                "uv": {"north": m, "south": m, "east": m, "west": m, "up": t, "down": m}}
        self.bones[bone].setdefault("cubes", []).append(cube)

    def bone(self, name, parent, pivot, rotation=None):
        """عظمة جديدة (للأجزاء المتحركة مثل الأجنحة). rotation اختياري [x,y,z]."""
        b = {"name": name, "parent": parent, "pivot": list(pivot), "cubes": []}
        if rotation:
            b["rotation"] = list(rotation)
        self.g["bones"].append(b)
        self.bones[name] = b
        return name

    def save(self):
        strip_h = 16
        out = Image.new("RGBA", (self.w, self.h + strip_h), (0, 0, 0, 0))
        out.paste(self.tex, (0, 0))
        for i, c in enumerate(self.palette):
            out.putpixel((i % 16, self.h + i // 16), (*c, 255))
        self.g["description"]["texture_height"] = self.h + strip_h
        out.save(os.path.join(TEX, f"sh_{self.name}.png"))
        with open(os.path.join(GEO, f"sh_{self.name}.geo.json"), "w", encoding="utf-8") as f:
            json.dump(self.geo, f, separators=(",", ":"))
        return len(self.palette)


# ───────────── عفريت الرماد: قرون منحنية، عيون جمر، أشواك ظهر، لهب بالذيل ─────────────
def imp():
    m = Mod("imp")
    HORN, HORN_HI, EMB, EMB_HI, EMB_W = (226, 212, 180), (255, 246, 220), (255, 120, 28), (255, 190, 60), (255, 240, 170)
    ROCK = (58, 52, 62)
    # قرون منحنية ناعمة: 5 قطع تصغر تدريجياً وتنحني للخارج ثم للأعلى، ورأسها جمر
    for sx in (-1, 1):
        for k, (dx, y, w, h, col) in enumerate(((2.7, 21.0, 1.7, 1.8, HORN), (3.4, 22.5, 1.45, 1.7, HORN), (4.0, 23.9, 1.2, 1.6, HORN_HI),
                                                (4.35, 25.2, 0.95, 1.5, HORN_HI), (4.5, 26.4, 0.7, 1.2, EMB_HI))):
            m.box("head", sx * dx - w / 2, y, -1.35 + k * 0.08, w, h, w, col, top=HORN_HI if k < 4 else EMB_W)
    # (العيون المضافة انشالت بطلب اللاعب: العيون من التكستشر الأصلي)
    # تاج جمر صغير فوق الراس
    m.box("head", -0.6, 21.5, -0.2, 1.2, 1.4, 1.2, EMB)
    m.box("head", -0.35, 22.9, 0.0, 0.7, 1.0, 0.7, EMB_HI)
    # أشواك صخرية متوهجة على الظهر
    for k, (y, hh) in enumerate(((10.6, 1.6), (12.2, 2.0), (13.9, 1.8))):
        m.box("body", -0.6, y, 2.6, 1.2, hh, 1.5, ROCK, top=EMB)
        m.box("body", -0.3, y + 0.2, 4.0, 0.6, hh * 0.7, 0.6, EMB)
    # لهب نهاية الذيل: مدبب (قاعدة جمر، وسط ذهبي، رأس أبيض) بدل المكعب
    m.box("tail3", -0.7, 12.2, 13.3, 1.4, 1.6, 1.4, EMB)
    m.box("tail3", -0.5, 13.6, 13.5, 1.0, 1.5, 1.0, EMB_HI)
    m.box("tail3", -0.3, 14.9, 13.7, 0.6, 1.2, 0.6, EMB_W)
    # صخور جمر على الأكتاف
    for sx in (-1, 1):
        m.box("body", sx * 5.2 - 1.0, 15.2, -1.2, 2.0, 1.6, 2.4, ROCK, top=EMB)
    # (الأجنحة انشالت بطلب اللاعب)
    return m.save()


# ───────────── حارس الصخر (غولم حجري طحلبي ببلورات تركواز): بلورات كتف، عين، قلب مضيء، أعمدة ظهر ─────────────
def guard():
    m = Mod("guard")
    STONE, STONE_HI, STONE_LO = (96, 100, 94), (140, 146, 136), (52, 56, 52)
    MOSS = (78, 124, 62)
    TEAL, TEAL_HI, TEAL_W = (70, 220, 190), (150, 255, 232), (232, 255, 248)
    # بلورات تركواز على الأكتاف (3 لكل كتف، الوسطى أطول)
    for sx in (-1, 1):
        for k, (dx, hh) in enumerate(((-2.6, 3.0), (0.0, 4.6), (2.6, 3.2))):
            cx = sx * 9.6 + dx
            m.box("body", cx - 0.8, 27.4, -0.8, 1.6, hh, 1.6, TEAL, top=TEAL_HI)
            m.box("body", cx - 0.4, 27.4 + hh, -0.4, 0.8, 1.4, 0.8, TEAL_W)
    # عين متوهجة (شق أفقي)
    m.box("head", -2.6, 28.4, -3.75, 5.2, 0.9, 0.5, TEAL)
    m.box("head", -1.6, 28.45, -3.85, 3.2, 0.6, 0.3, TEAL_W)
    # قلب مضيء بالصدر بإطار حجري
    m.box("body", -2.8, 19.6, -4.8, 5.6, 5.6, 0.5, STONE_HI)
    m.box("body", -2.1, 20.3, -5.05, 4.2, 4.2, 0.4, TEAL)
    m.box("body", -1.1, 21.3, -5.3, 2.2, 2.2, 0.3, TEAL_W)
    # أعمدة بلورية بالظهر مع قواعد حجرية
    for sx in (-1, 1):
        m.box("body", sx * 3.6 - 1.3, 20.0, 6.7, 2.6, 2.0, 2.6, STONE_LO, top=STONE_HI)
        m.box("body", sx * 3.6 - 0.8, 22.0, 7.2, 1.6, 6.5, 1.6, TEAL, top=TEAL_HI)
        m.box("body", sx * 3.6 - 0.4, 28.5, 7.6, 0.8, 1.6, 0.8, TEAL_W)
    # بلورات تركواز على القبضات (الضربة من هنا)
    for arm, x0 in (("arm_l", 6.4), ("arm_r", -12.8)):
        for k, (dx, hh) in enumerate(((0.6, 2.8), (2.6, 3.6), (4.4, 2.6))):
            m.box(arm, x0 + dx, 12.6, -4.6, 1.5, hh, 1.4, TEAL if k != 1 else TEAL_HI)
            m.box(arm, x0 + dx + 0.3, 12.6 + hh, -4.4, 0.9, 0.9, 0.9, TEAL_W)
        m.box(arm, x0 - 0.2, 12.0, -3.4, 6.8, 0.9, 6.8, STONE_HI)
    # طحلب يغطي الأكتاف ويتدلى
    for arm, x0 in (("arm_l", 5.0), ("arm_r", -14.2)):
        m.box(arm, x0, 27.5, -4.6, 9.2, 0.9, 9.2, MOSS)
        for k in range(4):
            m.box(arm, x0 + 0.6 + k * 2.4, 25.2 - (k % 2) * 0.9, -4.7, 1.2, 2.4 + (k % 2) * 0.9, 0.4, MOSS)
    # حزام حجري بمسامير طحلبية
    m.box("body", -6.8, 13.0, -4.3, 13.6, 1.2, 0.6, STONE_LO)
    for x in (-5.5, -2.0, 1.5, 5.0):
        m.box("body", x, 13.2, -4.6, 0.8, 0.8, 0.4, MOSS)
    return m.save()


# ───────────── ذئب الظل: عرف شبحي، عيون بنفسجية، آذان شفرة، لهب بالذيل ─────────────
def hound():
    m = Mod("hound")
    BLK, BLK_HI = (24, 20, 40), (52, 44, 84)
    VIO, VIO_HI, VIO_W = (130, 80, 240), (180, 130, 255), (232, 214, 255)
    # عرف شبحي: أشواك تكبر باتجاه الكتفين
    for k, (z, hh) in enumerate(((-6.4, 2.0), (-4.4, 2.8), (-2.4, 3.2), (-0.4, 2.8), (1.6, 2.2), (3.4, 1.6))):
        m.box("body", -0.6, 12.6, z, 1.2, hh, 1.2, BLK_HI, top=VIO)
        m.box("body", -0.35, 12.6 + hh, z + 0.25, 0.7, 0.9, 0.7, VIO_HI)
    # (العيون المضافة انشالت بطلب اللاعب: العيون من التكستشر الأصلي)
    # آذان شفرة
    for sx in (-1, 1):
        m.box("head", sx * 1.9 - 0.6, 14.1, -8.6, 1.2, 2.4, 0.9, BLK_HI)
        m.box("head", sx * 2.0 - 0.4, 16.3, -8.5, 0.8, 1.6, 0.7, VIO)
    # طوق أشواك بالرقبة
    for sx in (-1, 1):
        m.box("body", sx * 3.5 - 0.5, 9.6, -6.4, 1.0, 1.6, 1.0, VIO_HI)
        m.box("body", sx * 3.7 - 0.4, 8.2, -6.0, 0.8, 1.4, 0.8, VIO)
    # مخالب عظمية بالأرجل الأمامية
    for leg, x0 in (("leg_fl", 0.8), ("leg_fr", -4.0)):
        for k in range(3):
            m.box(leg, x0 + 0.3 + k * 1.05, 0.0, -7.6, 0.55, 0.9, 0.9, (236, 228, 214))
    # لهب شبحي بنهاية الذيل
    m.box("tail3", -0.9, 13.4, 14.6, 1.8, 2.8, 1.8, VIO)
    m.box("tail3", -0.55, 16.0, 14.9, 1.1, 2.0, 1.1, VIO_HI)
    m.box("tail3", -0.3, 17.8, 15.1, 0.6, 1.2, 0.6, VIO_W)
    return m.save()


# ───────────── عقرب الرمل: عيون خضراء، صفائح ظهر، سم متوهج بالإبرة، أشواك الكماشة ─────────────
def scorpion():
    m = Mod("scorpion")
    CHI, CHI_HI, CHI_LO = (112, 82, 44), (170, 130, 70), (62, 44, 26)
    VEN, VEN_HI, VEN_W = (110, 235, 70), (180, 255, 110), (236, 255, 190)
    # (العيون المضافة انشالت: العيون من التكستشر الأصلي)
    # صفائح ظهر مسننة
    for k, z in enumerate((-4.4, -1.6, 1.2, 3.8)):
        m.box("body", -1.0 - 0.0, 6.2, z, 2.0, 1.2 + (k % 2) * 0.4, 1.6, CHI_LO, top=CHI_HI)
        m.box("body", -0.5, 7.2 + (k % 2) * 0.4, z + 0.3, 1.0, 0.9, 1.0, CHI_HI)
    # إبرة بسم متوهج وقطرات
    m.box("sting", -0.5, 22.9, 6.1, 1.0, 1.4, 1.0, VEN_HI)
    m.box("sting", -0.3, 24.1, 6.3, 0.6, 0.9, 0.6, VEN_W)
    m.box("sting", -0.6, 19.3, 7.4, 1.2, 1.2, 1.2, VEN)
    m.box("sting", -0.4, 17.4, 8.6, 0.8, 1.0, 0.8, VEN_HI)
    # أشواك على الكماشتين
    for bone, sx in (("claw_l", 1), ("claw_r", -1)):
        m.box(bone, sx * 3.5 - 0.4, 3.6, -14.0, 0.8, 1.2, 0.8, CHI_LO)
        m.box(bone, sx * 4.8 - 0.4, 4.4, -12.6, 0.8, 1.4, 0.8, CHI_HI)
        m.box(bone, sx * 3.5 - 0.3, 5.4, -11.2, 0.6, 1.0, 0.6, CHI_LO)
    # أشواك على الكماشات
    for claw, x0 in (("claw_l", 2.9), ("claw_r", -6.3)):
        for k in range(3):
            m.box(claw, x0 + 0.5 + k * 1.0, 5.6, -12.8 + k * 1.1, 0.6, 1.0 + (k == 1) * 0.6, 0.6, CHI_HI)
    # عقد الذيل: حلقات بارزة
    for b in ("tail2", "tail3", "tail4"):
        bb = m.bones[b]
        c = bb["cubes"][0]
        ox, oy, oz = c["origin"]; sx, sy, sz = c["size"]
        m.box(b, ox - 0.35, oy + sy * 0.35, oz - 0.35, sx + 0.7, 0.8, sz + 0.7, CHI_HI)
    return m.save()


# تلوين منطقة UV صندوقية (box UV) لمكعب بالتكستشر: عرضها 2*(w+d) وارتفاعها d+h
def recolor_box_uv(tex, u, v, size, col, hi=None):
    w, h, d = (max(1, int(round(x + 0.49))) for x in size)
    for y in range(v, v + d + h):
        for x in range(u, u + 2 * (w + d)):
            if 0 <= x < tex.width and 0 <= y < tex.height:
                top = y < v + d
                c = hi if (hi and (top or (x + y) % 3 == 0)) else col
                tex.putpixel((x, y), (*c, 255))


# ───────────── رامي التدريب: جعبة أسهم، حزام بإبزيم، كتافات، واقي ساعد ─────────────
def archer():
    m = Mod("archer")
    # القوس بنفسجي (من عائلة لون العباءة بس بدرجة ثانية فاتحة حتى ما يذوب بيها): أذرع بنفسجية بلمعة ليلكية،
    # أطراف ليلكية فاتحة، مقبض بنفسجي غامق، ووتر خزامي
    LIMB, LIMB_HI, TIP, TIP_HI, GRIP, GRIP_HI, STRING = (124, 72, 206), (176, 132, 250), (214, 186, 255), (240, 226, 255), (44, 26, 72), (96, 64, 150), (206, 192, 255)
    for c in m.bones["bow"]["cubes"]:
        u, v = c["uv"]
        sz = c["size"]
        if sz[2] > 15:                                   # الوتر
            recolor_box_uv(m.tex, u, v, sz, STRING)
        elif u in (183, 0):                              # المقبض
            recolor_box_uv(m.tex, u, v, sz, GRIP, GRIP_HI)
        elif u == 28:                                    # طرفي القوس
            recolor_box_uv(m.tex, u, v, sz, TIP, TIP_HI)
        else:                                            # الأذرع
            recolor_box_uv(m.tex, u, v, sz, LIMB, LIMB_HI)
    # السهم اللي بالقوس (يطلع بس وقت السحب): بنفسجي
    SHAFT, HEAD, FLETCH = (78, 44, 132), (226, 210, 255), (156, 96, 246)
    for c in m.bones["arrow"]["cubes"]:
        u, v = c["uv"]
        col = SHAFT if c["size"][1] > 10 else HEAD if c["origin"][1] < 0 else FLETCH
        recolor_box_uv(m.tex, u, v, c["size"], col)
    LEATHER, LEATHER_HI, GOLD = (92, 58, 34), (130, 86, 50), (226, 176, 60)
    VIO, VIO_HI = (84, 50, 150), (140, 100, 220)
    # الجعبة: على الجهة اليمنى من الظهر (جهة إيد السحب) ومايلة لكتفه اليمين، حتى السهم يطلع فوق الكتف
    # مو من ورا الراس (قبل كانت يسار الظهر فالسهم يخترق القلنسوة). عظمة خاصة بدوران [-10, 0, 18].
    m.bone("quiver", "body", (-3.6, 15.0, 5.4), rotation=[-10, 0, 18])
    m.box("quiver", -5.2, 15.0, 4.1, 3.2, 9.0, 2.6, LEATHER, top=LEATHER_HI)
    m.box("quiver", -5.4, 15.4, 3.9, 3.6, 0.6, 3.0, GOLD)
    m.box("quiver", -5.4, 22.8, 3.9, 3.6, 0.6, 3.0, GOLD)
    for k in range(4):
        x = -4.9 + k * 0.75
        m.box("quiver", x, 24.0, 4.9 + (k % 2) * 0.5, 0.4, 2.6 + (k % 2) * 0.8, 0.4, SHAFT)
        m.box("quiver", x - 0.2, 26.6 + (k % 2) * 0.8, 4.7 + (k % 2) * 0.5, 0.8, 1.3, 0.8, FLETCH)
    m.box("body", -4.3, 14.6, -2.5, 8.6, 1.1, 5.0, LEATHER)                         # حزام
    m.box("body", -0.8, 14.4, -2.8, 1.6, 1.5, 0.4, GOLD)                             # إبزيم
    m.box("arm_l", 4.6, 22.0, -1.6, 2.9, 1.6, 3.2, VIO, top=VIO_HI)                 # كتافات
    m.box("arm_r", -7.5, 22.0, -1.6, 2.9, 1.6, 3.2, VIO, top=VIO_HI)
    m.box("arm_l", 4.85, 12.9, -1.15, 2.3, 2.6, 2.3, LEATHER_HI)                    # واقي الساعد (يد القوس)
    # سهم باليد اليمنى (يطلع بس لما يسحبه من الجعبة): بنفسجي
    m.bone("hand_arrow", "fore_r", (-6, 10.6, 0))
    m.box("hand_arrow", -6.2, 4.0, -0.2, 0.4, 13.0, 0.4, SHAFT)
    m.box("hand_arrow", -6.45, 2.6, -0.45, 0.9, 1.6, 0.9, HEAD)
    m.box("hand_arrow", -6.6, 15.6, -0.15, 1.2, 2.0, 0.3, FLETCH)
    m.box("hand_arrow", -6.15, 15.6, -0.6, 0.3, 2.0, 1.2, FLETCH)
    return m.save()

if __name__ == "__main__":
    for fn in (imp, guard, hound, scorpion, archer):
        print(fn.__name__, "colors:", fn())
