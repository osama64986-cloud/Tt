"""أسلحة بحجم 16x16 مثل سيوف ماينكرافت (نفس زاوية القبضة والنصل)، 4 أسلحة لكل واحد ميزة خاصة."""
import os, json, math
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
RP = ROOT + "/AnimePowers/RP"
BP = ROOT + "/AnimePowers/BP"
T = (0, 0, 0, 0)
OUT = (24, 20, 30, 255)


def mul(c, k): return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)


class Spr:
    def __init__(self): self.px = {}

    def p(self, x, y, c):
        if 0 <= x < 16 and 0 <= y < 16: self.px[(int(x), int(y))] = c

    def ribbon(self, a, b, cols, widthmap=None):
        """شريط قطري من a إلى b. cols = [فاتح، وسط، غامق] بعرض 3 بكسل على اتجاه (1,1)"""
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        for i in range(n + 1):
            t = i / max(1, n)
            x = round(a[0] + (b[0] - a[0]) * t); y = round(a[1] + (b[1] - a[1]) * t)
            w = widthmap(t) if widthmap else len(cols)
            ks = [0, 1, 2][:w] if w <= 3 else [0, 1, 2]
            for k in ks:
                self.p(x + (k - (1 if w == 3 else 0)) * 0 + (1 if k == 1 else 0) + (1 if k == 2 else 0),
                       y + (1 if k == 2 else 0) + (1 if k == 1 else 0) - (1 if k == 1 else 0), cols[k])

    def poly(self, pts, cols, light=(-1, -1)):
        ss = 8
        big = Image.new("L", (16 * ss, 16 * ss), 0)
        ImageDraw.Draw(big).polygon([(px * ss, py * ss) for px, py in pts], fill=255)
        im = big.resize((16, 16), Image.BOX).point(lambda v: 255 if v >= 128 else 0)
        for y in range(16):
            for x in range(16):
                if im.getpixel((x, y)) > 0:
                    inner = [im.getpixel((x + dx, y + dy)) > 0 if 0 <= x + dx < 16 and 0 <= y + dy < 16 else False
                             for dx, dy in ((-1, 0), (0, -1), (1, 0), (0, 1))]
                    tl = (not inner[0]) or (not inner[1])
                    br = (not inner[2]) or (not inner[3])
                    c = cols[0] if tl and not br else (cols[2] if br and not tl else cols[1])
                    self.p(x, y, c)

    def line(self, a, b, c, th=1):
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        for i in range(n + 1):
            t = i / max(1, n)
            x = round(a[0] + (b[0] - a[0]) * t); y = round(a[1] + (b[1] - a[1]) * t)
            self.p(x, y, c)
            if th > 1: self.p(x + 1, y, c)

    def img(self):
        im = Image.new("RGBA", (16, 16), T)
        out = {}
        for (x, y) in self.px:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (dx or dy) and (x + dx, y + dy) not in self.px and 0 <= x + dx < 16 and 0 <= y + dy < 16:
                        out[(x + dx, y + dy)] = OUT
        for k, c in out.items(): im.putpixel(k, c)
        for k, c in self.px.items(): im.putpixel(k, c)
        return im


def dagger():
    """خنجر هلالي منحني (شكل كريس/منجل صغير) بنصل ذهبي — مو شبه سيف"""
    s = Spr()
    G = [(255, 250, 225, 255), (255, 214, 120, 255), (196, 140, 50, 255)]
    # نصل هلالي: يطلع من الحارس ويلتف لفوق ثم يميل للداخل
    s.poly([(6.5, 9.5), (9, 8.5), (12, 6.5), (14, 3.5), (13.5, 0.5), (12.5, 0.2), (12.2, 3.0), (10.5, 5.2), (8, 6.8)], G)
    # حد لامع داخلي
    for (x, y) in ((11, 5), (12, 3), (12, 1)): s.p(x, y, (255, 255, 240, 255))
    # حارس مقوّس صغير
    for (x, y, c) in ((4, 8, (150, 90, 40, 255)), (5, 9, (230, 170, 70, 255)), (6, 10, (255, 210, 110, 255)), (7, 11, (230, 170, 70, 255)), (8, 12, (150, 90, 40, 255))):
        s.p(x, y, c)
    # قبضة ملفوفة + جوهرة بالنهاية
    s.p(5, 11, (110, 70, 44, 255)); s.p(4, 12, (84, 52, 32, 255)); s.p(3, 13, (110, 70, 44, 255))
    s.p(2, 14, (255, 96, 60, 255)); s.p(1, 15, (255, 96, 60, 255)); s.p(2, 15, (200, 50, 40, 255)); s.p(1, 14, (255, 170, 120, 255))
    return s


def spear():
    s = Spr()
    SH = [(150, 100, 56, 255), (104, 66, 38, 255), (64, 40, 24, 255)]
    # عمود طويل
    for i in range(11):
        x, y = 1 + i, 14 - i
        s.p(x, y, SH[1]); s.p(x + 1, y, SH[2])
    for p in ((1, 14), (2, 13), (3, 12)): s.p(*p, SH[0])
    # شرابة حمراء تحت الرأس
    for (x, y, c) in ((9, 7, (200, 40, 56, 255)), (8, 8, (160, 24, 44, 255)), (10, 8, (230, 70, 80, 255)), (9, 9, (160, 24, 44, 255)), (8, 9, (120, 16, 36, 255))):
        s.p(x, y, c)
    # رأس رمح ورقي (شفرة معدنية بشق قرمزي)
    ST = [(236, 240, 248, 255), (166, 176, 196, 255), (96, 106, 130, 255)]
    s.poly([(10, 6), (11, 2.5), (14.5, 0), (15.8, 0.3), (15.5, 4.5), (13, 7)], ST)
    for (x, y) in ((13, 2), (13, 3), (12, 4)): s.p(x, y, (214, 40, 70, 255))
    s.p(14, 1, (255, 255, 255, 255))
    return s


def cleaver():
    s = Spr()
    HA = [(150, 100, 56, 255), (104, 66, 38, 255), (64, 40, 24, 255)]
    for i in range(6):
        x, y = 2 + i, 13 - i
        s.p(x, y, HA[1]); s.p(x + 1, y, HA[2])
    for p in ((2, 13), (3, 12), (4, 11)): s.p(p[0], p[1], HA[0])
    s.p(1, 14, HA[2]); s.p(2, 14, HA[2])
    # حارس حديدي صغير
    for (x, y) in ((6, 8), (7, 9), (6, 9)): s.p(x, y, (90, 88, 104, 255))
    # نصل مستطيل عريض بالمحور مع المقبض: ظهر سميك غامق، حد متوهج جمري
    r2 = math.sqrt(.5)
    ux, uy = r2, -r2          # باتجاه المقبض -> الطرف
    vx, vy = r2, r2           # باتجاه الحد
    c = (10.6, 4.4); hl = 4.3; hw = 3.0
    IRD, IRM, IRL = (44, 42, 56, 255), (92, 94, 112, 255), (150, 152, 170, 255)
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - c[0], y + 0.5 - c[1]
            tu = dx * ux + dy * uy; tv = dx * vx + dy * vy
            if abs(tu) <= hl and abs(tv) <= hw:
                t = tv / hw
                if t < -0.5: col = IRD
                elif t < 0.25: col = IRM
                elif t < 0.62: col = IRL
                else: col = (255, 132, 40, 255)
                s.p(x, y, col)
    # شقوق جمر وثقب تعليق
    for (x, y) in ((9, 4), (10, 5), (11, 6)): s.p(x, y, (255, 100, 30, 255))
    s.p(8, 6, (24, 20, 30, 255)); s.p(9, 5, (255, 200, 90, 255))
    return s


def shadow_blade():
    s = Spr()
    BL = [(150, 130, 255, 255), (74, 52, 150, 255), (34, 22, 78, 255)]
    # نصل طويل رفيع بلون بنفسجي حبري، حد سماوي
    for i in range(11):
        x, y = 4 + i, 11 - i
        s.p(x, y, (170, 240, 255, 255) if i % 2 == 0 else (110, 200, 240, 255))
        s.p(x + 1, y, BL[1]); s.p(x, y + 1, BL[2])
    s.p(15, 0, (230, 250, 255, 255)); s.p(14, 0, (170, 240, 255, 255))
    # حارس صغير ملتوي
    for k, c in zip(range(-2, 3), [(80, 70, 110, 255), (130, 110, 190, 255), (190, 170, 240, 255), (130, 110, 190, 255), (80, 70, 110, 255)]):
        s.p(4 + k, 12 + k, c)
    # قبضة سوداء ملفوفة وجوهرة
    s.p(3, 13, (50, 40, 70, 255)); s.p(2, 14, (30, 24, 46, 255)); s.p(1, 15, (50, 40, 70, 255))
    s.p(0, 15, (140, 255, 230, 255))
    return s


def shadow_claws():
    """مخالب: ثلاث شفرات منحنية تتفرع من قبضة بقبضة اليد (مثل كاتار/مخالب ولفرين)"""
    s = Spr()
    BL = (150, 224, 250, 255); BT = (236, 252, 255, 255); BD = (86, 70, 170, 255)
    def blade(pts):
        for i, (x, y) in enumerate(pts):
            tip = i >= len(pts) - 2
            s.p(x, y, BT if tip else BL)
            s.p(x, y + 1, BD)
    blade([(5, 10), (6, 8), (6, 6), (6, 4), (6, 2), (7, 0)])
    blade([(7, 11), (9, 9), (10, 7), (11, 5), (12, 3), (13, 1)])
    blade([(8, 12), (10, 11), (12, 10), (13, 9), (14, 8), (15, 7)])
    # قبضة/قفاز
    GL = [(110, 92, 170, 255), (52, 40, 92, 255), (26, 20, 50, 255)]
    s.poly([(1.5, 11.5), (5.5, 10.2), (9.5, 12), (10, 14.5), (7, 15.8), (2.5, 15.5), (1, 13.5)], GL)
    s.p(3, 12, (170, 150, 235, 255)); s.p(5, 11, (170, 150, 235, 255)); s.p(8, 13, (170, 150, 235, 255))
    s.p(4, 14, (140, 255, 230, 255)); s.p(5, 14, (140, 255, 230, 255))
    return s


def katana():
    """كاتانا ظلامية: نصل نحيف منحني قليلا، تسوبا ذهبية مزخرفة، مقبض ملفوف بجوهرة اسطورية"""
    s = Spr()
    DK = (28, 24, 44, 255); ED = (170, 150, 255, 255); HM = (120, 70, 220, 255); TIP = (235, 225, 255, 255)
    # نصل: ينحني للأعلى بنهاية مائلة (انحناء الكاتانا)
    pts = [(5, 10), (6, 9), (7, 8), (8, 7), (9, 6), (10, 5), (11, 4), (12, 3), (13, 2), (14, 2), (15, 1)]
    for i, (x, y) in enumerate(pts):
        s.p(x, y + 1, DK)               # ظهر النصل غامق
        s.p(x, y, ED if i < len(pts) - 2 else TIP)   # الحد البنفسجي الفاتح
        if i % 3 == 1: s.p(x + 1, y + 1, HM)        # خط الهامون المتوهج
    s.p(15, 0, TIP)
    # تسوبا (الحارس): معين ذهبي مزخرف بجوهرة
    G1, G2, G3 = (255, 222, 120, 255), (206, 150, 52, 255), (120, 80, 24, 255)
    for (x, y, c) in ((3, 10, G2), (4, 9, G1), (5, 8, G2), (4, 10, G1), (5, 11, G2), (6, 10, G3), (3, 11, G3), (4, 11, (190, 60, 230, 255)), (2, 9, G3), (6, 9, G2)):
        s.p(x, y, c)
    # مقبض ملفوف بنفسجي/ذهبي
    for i, (x, y) in enumerate(((3, 12), (2, 13), (1, 14))):
        s.p(x, y, (60, 30, 100, 255) if i % 2 == 0 else (150, 90, 220, 255))
        s.p(x + 1, y, (36, 18, 64, 255))
    # رأس المقبض: جوهرة متوهجة بجناحين صغيرين
    s.p(0, 15, (255, 90, 220, 255)); s.p(1, 15, (255, 170, 240, 255)); s.p(0, 14, (230, 190, 90, 255))
    return s


def maul():
    s = Spr()
    ST = [(168, 170, 164, 255), (118, 120, 114, 255), (70, 72, 70, 255)]
    HA = [(150, 100, 56, 255), (104, 66, 38, 255), (64, 40, 24, 255)]
    for i in range(8):
        x, y = 2 + i, 13 - i
        s.p(x, y, HA[1]); s.p(x + 1, y, HA[2])
    for p in ((2, 13), (3, 12)): s.p(p[0], p[1], HA[0])
    s.p(1, 14, HA[2]); s.p(2, 14, HA[2])
    # رأس المطرقة: مستطيل مائل متعامد مع المقبض
    c = (10.6, 4.6); a = 4.8; b = 2.3
    ux, uy = math.sqrt(.5), math.sqrt(.5); vx, vy = math.sqrt(.5), -math.sqrt(.5)
    pts = [(c[0] + sa * a * ux + sb * b * vx, c[1] + sa * a * uy + sb * b * vy) for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    s.poly(pts, ST)
    # أحزمة معدنية وحجر متوهج فيروزي
    for (x, y) in ((9, 5), (11, 3)):
        s.p(x, y, (60, 62, 60, 255))
    for (x, y) in ((10, 4),):
        s.p(x, y, (110, 255, 205, 255))
    s.p(12, 6, (110, 255, 205, 255)); s.p(8, 2, (110, 255, 205, 255))
    # طحلب
    for (x, y) in ((8, 3), (9, 2), (13, 7)):
        s.p(x, y, (72, 122, 48, 255))
    return s


WEAP = [
    ("sh:dawn_dagger", "sh_dagger", "§6خنجر الفجر", dagger),
    ("sh:ember_cleaver", "sh_cleaver", "§cساطور الجمر", cleaver),
    ("sh:shadow_blade", "sh_shadow", "§5سيف الظل", shadow_blade),
    ("sh:shadow_claws", "sh_claws", "§5مخالب الظل", shadow_claws),
    ("sh:dark_katana", "sh_katana", "§5كاتانا الهاوية", katana),
    ("sh:stone_maul", "sh_maul", "§2مطرقة الصخر", maul),
    ("sh:sunset_spear", "sh_spear", "§4رمح الغروب", spear),
]


def wjson(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    tex = json.load(open(RP + "/textures/item_texture.json", encoding="utf-8"))
    ims = []
    for ident, key, name, fn in WEAP:
        im = fn().img()
        im.save(RP + f"/textures/items/{key}.png")
        ims.append(im)
        tex["texture_data"][key] = {"textures": f"textures/items/{key}"}
        wjson(BP + f"/items/{key}.json", {
            "format_version": "1.21.60",
            "minecraft:item": {"description": {"identifier": ident, "menu_category": {"category": "equipment"}},
                               "components": {"minecraft:icon": {"textures": {"default": key}},
                                              "minecraft:max_stack_size": 1,
                                              "minecraft:hand_equipped": True,
                                              "minecraft:display_name": {"value": name}}},
        })
    wjson(RP + "/textures/item_texture.json", tex)
    # إزالة المجسمات المخمّنة غير الموثوقة (نستعمل sprite hand_equipped مثل السيوف الأصلية)
    for f in ("sh_dagger", "sh_cleaver"):
        for pth in (RP + f"/attachables/{f}.attachable.json", RP + f"/models/entity/{f}.geo.json", RP + f"/textures/attachables/{f}.png"):
            if os.path.exists(pth): os.remove(pth)
    # معاينة: كل سلاح بجانب سيف ماينكرافت الحقيقي بنفس الشبكة
    van = Image.open(ROOT + "/ref/bedrock-samples/resource_pack/textures/items/iron_sword.png").convert("RGBA")
    S = 18
    sheet = Image.new("RGBA", (16 * S * 8 + 110, 16 * S + 10), (58, 60, 72, 255))
    for k, im in enumerate([van] + ims):
        big = im.resize((16 * S, 16 * S), Image.NEAREST)
        sheet.paste(big, (k * (16 * S + 12), 5), big)
    sheet.save(ROOT + "/weapons_preview.png")
