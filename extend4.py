import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from mobkit import *

ROOT = os.path.dirname(os.path.abspath(__file__))
RP = ROOT + "/AnimePowers/RP"
GEO = RP + "/models/entity/{}.geo.json"
TEX = RP + "/textures/entity/{}.png"


def band(img, reg, y0, y1, col, x0=0, x1=None, k=1.0):
    rx, ry, rw, rh = reg
    for yy in range(y0, min(y1, rh)):
        for xx in range(x0, rw if x1 is None else min(x1, rw)):
            put(img, rx + xx, ry + yy, mul(col, k))


def px(img, reg, x, y, col):
    put(img, reg[0] + x, reg[1] + y, col)


def sides(regs):
    return [regs[f] for f in ("north", "south", "east", "west")]


# ═════════════ المدرب: شاب عادي بجلد ماينكرافت (بدون لحية/هالة) ═════════════
def build_trainer():
    m = Mob("geometry.sh_trainer", 64, 64, seed=5)
    SKIN = (224, 178, 146); SKIN_D = (196, 146, 118)
    HAIR = (52, 36, 30); HAIR_L = (76, 54, 42)
    TUN = (40, 78, 112); TUN_L = (62, 108, 146); TRIM = (214, 176, 84)
    BELT = (96, 64, 40); PANT = (52, 54, 66); BOOT = (60, 42, 32); WRAP = (226, 218, 198)

    def head(img, regs):
        for f in ("north", "south", "east", "west", "up", "down"):
            band(img, regs[f], 0, 99, SKIN, k=1.0)
        n = regs["north"]
        band(img, n, 0, 2, HAIR)                       # الشعر
        for x in (0, 1, 6, 7): px(img, n, x, 2, HAIR)  # خصلات الجانب
        px(img, n, 3, 2, HAIR); px(img, n, 4, 2, HAIR_L)  # غرة
        for x in (1, 2, 5, 6): px(img, n, x, 3, HAIR_L if x in (2, 5) else HAIR)  # حواجب
        for x, c in ((1, (244, 244, 244)), (2, (66, 42, 30)), (5, (66, 42, 30)), (6, (244, 244, 244))):
            px(img, n, x, 4, c)
        px(img, n, 3, 5, SKIN_D); px(img, n, 4, 5, SKIN_D)  # أنف
        # لحية قصيرة: الفك والذقن + شارب، مع فتحة للفم
        for x in range(1, 7): px(img, n, x, 7, HAIR)
        for x in (0, 1, 2, 5, 6, 7): px(img, n, x, 6, HAIR)
        for x in (2, 3, 4, 5): px(img, n, x, 5, HAIR_L) if x in (2, 5) else None
        px(img, n, 3, 6, (160, 80, 76)); px(img, n, 4, 6, (160, 80, 76))  # فم
        px(img, n, 0, 5, HAIR); px(img, n, 7, 5, HAIR)
        # جوانب الرأس: شعر أعلى + أذن
        for f in ("east", "west"):
            band(img, regs[f], 0, 3, HAIR)
            px(img, regs[f], 3, 4, SKIN_D); px(img, regs[f], 4, 4, SKIN_D)
            band(img, regs[f], 5, 8, HAIR, x0=0, x1=3)
            band(img, regs[f], 5, 8, HAIR, x0=5, x1=8)
        band(img, regs["south"], 0, 8, HAIR)           # خلف الرأس شعر
        band(img, regs["up"], 0, 8, HAIR)
        for x in range(0, 8, 2): px(img, regs["up"], x, 3, HAIR_L)

    def torso(img, regs):
        for r in sides(regs): band(img, r, 0, 12, TUN)
        n = regs["north"]
        # ياقة وتطريز ذهبي، حزام
        band(img, n, 0, 1, TRIM)
        for y in range(1, 9): px(img, n, 4, y, TRIM)       # خط وسط
        for y in range(1, 9): px(img, n, 3, y, mul(TUN, 0.8))
        band(img, n, 9, 11, BELT)
        px(img, n, 4, 9, TRIM); px(img, n, 4, 10, TRIM); px(img, n, 3, 9, TRIM)
        band(img, regs["south"], 9, 11, BELT)
        for r in (regs["east"], regs["west"]): band(img, r, 9, 11, BELT)
        band(img, regs["up"], 0, 4, TUN_L)

    def arm(img, regs):
        for r in sides(regs): band(img, r, 0, 12, TUN)
        for r in sides(regs):
            band(img, r, 0, 1, TRIM)
            band(img, r, 8, 12, WRAP)         # لفافة على الساعد
            band(img, r, 9, 10, mul(WRAP, 0.8))
        band(img, regs["down"], 0, 4, SKIN)
        for r in sides(regs):
            band(img, r, 11, 12, SKIN)        # كف

    def leg(img, regs):
        for r in sides(regs): band(img, r, 0, 12, PANT)
        for r in sides(regs):
            band(img, r, 8, 12, BOOT)
            band(img, r, 8, 9, mul(BOOT, 1.3))
        band(img, regs["down"], 0, 4, mul(BOOT, 0.7))

    m.bone("body", [0, 12, 0])
    m.cube("body", [-4, 12, -2], [8, 12, 4], TUN, key="torso", detail=torso, noise=2, grad=0.1)
    m.bone("head", [0, 24, 0], "body")
    m.cube("head", [-4, 24, -4], [8, 8, 8], SKIN, key="head", detail=head, noise=2, grad=0.08)
    m.cube("head", [-3.6, 23.3, -4.5], [7.2, 3.0, 1.0], HAIR, key="beard", noise=4, grad=0.15)
    # حجم للشعر
    m.cube("head", [-4.3, 30.6, -4.3], [8.6, 2.0, 8.6], HAIR, key="hairtop", noise=4, grad=0.15)
    m.cube("head", [-4.3, 25.0, 3.4], [8.6, 6.0, 1.0], HAIR, key="hairback", noise=4, grad=0.15)
    m.bone("arm_l", [5, 22, 0], "body")
    m.cube("arm_l", [4, 10, -2], [4, 12, 4], TUN, key="arm", detail=arm, noise=2, grad=0.1)
    m.bone("arm_r", [-5, 22, 0], "body")
    m.cube("arm_r", [-8, 10, -2], [4, 12, 4], TUN, key="arm", detail=arm, noise=2, grad=0.1)
    m.bone("leg_l", [2, 12, 0], "body")
    m.cube("leg_l", [0, 0, -2], [4, 12, 4], PANT, key="leg", detail=leg, noise=2, grad=0.1)
    m.bone("leg_r", [-2, 12, 0], "body")
    m.cube("leg_r", [-4, 0, -2], [4, 12, 4], PANT, key="leg", detail=leg, noise=2, grad=0.1)
    return m


# ═════════════ الرامي: هيكل عظمي طويل بوشاح ممزق وقوس بلوري بنفسجي ═════════════
def build_archer(P=None):
    import math as _m
    m = Mob("geometry.sh_archer", 192, 192, seed=9)
    BONE = (222, 216, 204); BONE_D = (152, 146, 140); GAP = (26, 20, 34)
    INK = (58, 34, 112); INK_D = (30, 16, 62); INK_L = (104, 70, 176); INK_X = (150, 110, 230)
    WOOD = (84, 58, 44); WOOD_L = (120, 88, 60); SHAFT = (190, 170, 130); STRING = (214, 200, 240)
    CRY = (96, 56, 180); CRY_L = (160, 120, 255); GEM = (200, 160, 255)
    EYE = (110, 100, 255); EYE_L = (190, 200, 255)

    def clear(img, x, y):
        if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]: img[y, x] = (0, 0, 0, 0)

    def bn(img, regs, dark=BONE_D):
        for f in regs: patches(img, regs[f], m.rng, dark, density=0.22, seed_scale=2)

    def knob(img, regs):
        bn(img, regs)
        for r in sides(regs):
            band(img, r, 0, 1, BONE_D, k=0.8); band(img, r, max(0, r[3] - 1), r[3], BONE_D, k=0.8)

    def cranium(img, regs):
        bn(img, regs)
        n = regs["north"]
        for x in range(8):
            put(img, n[0] + x, n[1] + 0, mul(BONE, 1.05))
        for x in (1, 2, 5, 6): put(img, n[0] + x, n[1] + 2, mul(BONE_D, 0.9))       # ظل الحاجب
        for x0 in (1, 5):                                                          # محجران بزاوية
            for dx in range(2):
                for dy in range(2):
                    put(img, n[0] + x0 + dx, n[1] + 3 + dy, GAP)
            inner = 2 if x0 == 1 else 5
            put(img, n[0] + inner, n[1] + 3, EYE_L)
            put(img, n[0] + inner, n[1] + 4, mix(GAP, EYE, 0.55))
        put(img, n[0] + 3, n[1] + 4, BONE_D); put(img, n[0] + 4, n[1] + 4, BONE_D)    # جسر الأنف
        put(img, n[0] + 3, n[1] + 5, BONE_D); put(img, n[0] + 4, n[1] + 5, BONE_D)
        cracks(img, regs["up"], m.rng, GAP, n=1, length=3, halo=False)
        for f in ("east", "west"):
            r = regs[f]
            put(img, r[0] + 5, r[1] + 3, GAP); put(img, r[0] + 5, r[1] + 4, GAP)     # عمق المحجر
            for x in range(3, 8): put(img, r[0] + x, r[1] + 5, BONE_D)                 # قوس الوجنة

    def midface(img, regs):
        bn(img, regs)
        n = regs["north"]
        put(img, n[0] + 2, n[1] + 0, GAP); put(img, n[0] + 3, n[1] + 0, GAP); put(img, n[0] + 2, n[1] + 1, mix(GAP, BONE_D, 0.4)); put(img, n[0] + 3, n[1] + 1, mix(GAP, BONE_D, 0.4))
        for x in (0, 1, 4, 5): put(img, n[0] + x, n[1] + 0, mul(BONE_D, 0.85))         # حافة الوجنة
        for x in range(1, 5):                                                          # أسنان علوية
            put(img, n[0] + x, n[1] + 1, BONE if x in (1, 4) else (GAP if x == 2 else BONE_D)) if x not in (2, 3) else None

    def mandible(img, regs):
        bn(img, regs)
        n = regs["north"]
        for x in range(0, 4):
            put(img, n[0] + x, n[1] + 0, GAP if x % 2 == 0 else BONE)                  # أسنان سفلية
            put(img, n[0] + x, n[1] + 1, mul(BONE_D, 0.85) if x in (0, 3) else BONE)   # الذقن

    def cloth(img, regs, base=INK, fray=0, shade=True):
        for f, (x0, y0, w, h) in regs.items():
            for yy in range(h):
                t = yy / max(1, h - 1)
                for xx in range(w):
                    k = 0.78 + 0.34 * (((xx * 5 + yy * 3) % 7) / 6) - 0.25 * t * (1 if shade else 0)
                    put(img, x0 + xx, y0 + yy, mul(base, k))
            patches(img, regs[f], m.rng, INK_D, density=0.22, seed_scale=2)
            patches(img, regs[f], m.rng, INK_L, density=0.06, seed_scale=1)
        if fray:
            for f in ("north", "south", "east", "west"):
                x0, y0, w, h = regs[f]
                for xx in range(w):
                    cut = int(m.rng.integers(0, fray + 1))
                    for yy in range(h - cut, h): clear(img, x0 + xx, y0 + yy)

    def hood(img, regs):
        cloth(img, regs, INK, 0, False)

    def strip(fray):
        def d(img, regs): cloth(img, regs, INK, fray)
        return d

    def mantle(img, regs): cloth(img, regs, INK_L, 2, False)

    def wood(img, regs):
        for f in regs:
            x0, y0, w, h = regs[f]
            for yy in range(h):
                for xx in range(w):
                    k = 0.9 + 0.2 * ((xx * 3 + yy) % 4) / 3
                    put(img, x0 + xx, y0 + yy, mul(WOOD_L if (xx + yy // 3) % 2 else WOOD, k))

    def solid(col):
        def d(img, regs):
            for f in regs: band(img, regs[f], 0, 99, col)
        return d

    def crystal(img, regs):
        for f, (x0, y0, w, h) in regs.items():
            for yy in range(h):
                for xx in range(w):
                    k = 0.8 + 0.4 * (((xx + yy) % 3) / 2)
                    put(img, x0 + xx, y0 + yy, mul(CRY if (xx + yy) % 4 else CRY_L, k))

    # ── العظام: نحيفة مع مفاصل منتفخة ──
    m.bone("body", [0, 13, 0])
    m.cube("body", [-0.6, 13.4, 1.0], [1.2, 11.4, 1.2], BONE, key="spine", detail=knob, grad=0.1)
    m.cube("body", [-0.7, 15.0, -2.2], [1.4, 8.2, 1.0], BONE, key="sternum", detail=knob, grad=0.1)
    for i in range(5):
        y = 15.0 + i * 1.9
        w = 7.0 - abs(i - 1.5) * 0.4
        m.cube("body", [-w / 2, y, -2.0], [w, 0.9, 4.0], BONE, key="rib%d" % i, detail=knob, grad=0.12)
    m.cube("body", [-6.0, 23.0, -1.0], [12.0, 1.3, 1.6], BONE, key="clav", detail=knob, grad=0.1)
    m.cube("body", [-3.4, 12.4, -1.5], [6.8, 2.0, 3.0], BONE, key="pelvis", detail=knob, grad=0.1)

    # جعبة السهام على الظهر (تظهر من فتحة الوشاح)
    m.cube("body", [-2, 13.5, 3.6], [4, 9, 2.6], WOOD, key="quiver", detail=wood, grad=0.1)
    for i, (dx, rz) in enumerate(((-1.2, -8), (0, 0), (1.2, 8))):
        m.cube("body", [dx - 0.4, 22.2, 4.5], [0.8, 4.4, 0.8], SHAFT, key="arrow%d" % i, detail=solid(SHAFT), rot=[0, 0, rz], pivot=[dx, 22.2, 4.9], grad=0.05)
        m.cube("body", [dx - 0.7, 26.2, 4.4], [1.4, 1.6, 1.0], INK_X, key="fletchq", detail=solid(INK_X), grad=0.05)

    # ── الرأس: جمجمة + قلنسوة مدببة ──
    m.bone("head", [0, 25, 0], "body")
    # جمجمة بنِسب تشريحية: جمجمة عريضة، وجه أوسط أضيق، فك سفلي نحيف يضيق نحو الذقن
    m.cube("head", [-4, 27, -4], [8, 6, 8], BONE, key="cranium", detail=cranium, noise=3, grad=0.1)
    m.cube("head", [-3, 25, -3.4], [6, 2, 6], BONE, key="midface", detail=midface, noise=3, grad=0.1)
    m.cube("head", [-2, 23.6, -3.0], [4, 2, 5], BONE, key="mandible", detail=mandible, noise=3, grad=0.1)
    m.cube("head", [-4.1, 25.8, -3.4], [1.2, 1.2, 3.0], BONE_D, key="zyg", detail=knob, grad=0.1)
    m.cube("head", [2.9, 25.8, -3.4], [1.2, 1.2, 3.0], BONE_D, key="zyg", detail=knob, grad=0.1)
    m.cube("head", [-5.0, 31.6, -5.0], [10.0, 2.0, 10.0], INK, key="hoodtop", detail=hood, grad=0.1)
    m.cube("head", [-3.8, 33.4, -3.4], [7.6, 2.0, 7.6], INK, key="hoodtop2", detail=hood, grad=0.1)
    m.cube("head", [-2.0, 35.0, -0.6], [4.0, 2.4, 4.0], INK_D, key="hoodtop3", detail=hood, rot=[16, 0, 0], pivot=[0, 35, 1.4], grad=0.1)
    m.cube("head", [-5.0, 24.6, 3.2], [10.0, 7.2, 1.8], INK, key="hoodback", detail=hood, grad=0.1)
    m.cube("head", [-5.2, 24.6, -4.6], [1.6, 7.4, 8.8], INK, key="hoodL", detail=hood, grad=0.1)
    m.cube("head", [3.6, 24.6, -4.6], [1.6, 7.4, 8.8], INK, key="hoodR", detail=hood, grad=0.1)
    m.cube("head", [-5.2, 32.0, -5.6], [10.4, 1.2, 1.2], INK_D, key="hoodbrim", detail=hood, grad=0.1)
    # لفة وشاح حول الرقبة
    m.cube("body", [-5.0, 21.8, -4.6], [10.0, 1.9, 9.2], INK_L, key="scarf1", detail=mantle, grad=0.1)
    m.cube("body", [-4.2, 20.9, -5.0], [8.4, 1.6, 4.0], INK, key="scarf2", detail=mantle, rot=[0, 0, 6], pivot=[0, 23, -3], grad=0.1)
    # غطاء الأكتاف
    m.cube("body", [-7.4, 20.6, -3.6], [14.8, 2.2, 7.2], INK_L, key="mantle", detail=mantle, grad=0.1)

    # ── وشاح ممزق: شرائط طويلة تتحرك (4 مجموعات) ──
    import random as _r
    rr = _r.Random(4)
    def strips(bone, items):
        for i, (x, z, w, d, hgt) in enumerate(items):
            m.cube(bone, [x, 21.8 - hgt, z], [w, hgt, d], INK, key="%s%d" % (bone, i), detail=strip(3 if hgt > 14 else 2), grad=0.0, noise=3)
    m.bone("cape_b", [0, 21.8, 3.0], "body")
    strips("cape_b", [(-6.5 + i * 2.6, 3.0 + (i % 2) * 0.3, 2.4, 0.7, 19 + rr.choice([-4, -2, 0, 1, 2])) for i in range(6)])
    m.bone("cape_l", [6.8, 21.8, 0], "body")
    strips("cape_l", [(6.6 + (i % 2) * 0.3, -3.0 + i * 2.4, 0.7, 2.4, 17 + rr.choice([-3, -1, 0, 2, 3])) for i in range(3)])
    m.bone("cape_r", [-6.8, 21.8, 0], "body")
    strips("cape_r", [(-7.3 + (i % 2) * 0.3, -3.0 + i * 2.4, 0.7, 2.4, 17 + rr.choice([-3, -1, 0, 2, 3])) for i in range(3)])
    m.bone("cape_f", [0, 21.8, -3.4], "body")
    strips("cape_f", [(-6.3, -3.9, 2.2, 0.7, 15), (-3.9, -3.7, 1.8, 0.7, 11), (2.1, -3.7, 1.8, 0.7, 12), (4.1, -3.9, 2.2, 0.7, 16)])

    # ── ذراع القوس (يسار) ──
    m.bone("arm_l", [6, 23, 0], "body")
    m.cube("arm_l", [5.2, 17.6, -0.8], [1.6, 5.4, 1.6], BONE, key="uarm", detail=knob, grad=0.1)
    m.cube("arm_l", [4.9, 16.4, -1.1], [2.2, 2.2, 2.2], BONE_D, key="elb", detail=knob, grad=0.1)
    m.cube("arm_l", [5.2, 11.6, -0.8], [1.6, 4.8, 1.6], BONE, key="farm", detail=knob, grad=0.1)
    m.cube("arm_l", [4.8, 10.4, -1.2], [2.4, 1.6, 2.4], BONE_D, key="hand", detail=knob, grad=0.1)
    m.bone("bow", [6, 11, 0], "arm_l")
    # قوس بلوري مفصّل: كل طرف 3 قطع منحنية، جوهرة بالمنتصف
    m.cube("bow", [5.0, 10.2, -1.2], [2.0, 2.0, 2.4], WOOD_L, key="grip", detail=wood, grad=0.1)
    m.cube("bow", [5.1, 10.5, -0.9], [1.8, 1.8, 1.8], GEM, key="gem", detail=solid(GEM), rot=[45, 0, 0], pivot=[6, 11.4, 0], grad=0.05)
    for sg in (1, -1):
        y, z = 11.4, 1.2 * sg
        for k, ang in enumerate((8, 22, 40)):
            L = 3.6 - 0.3 * k
            a = _m.radians(ang)
            dy, dz = _m.sin(a) * L, _m.cos(a) * L * sg
            cy, cz = y + dy / 2, z + dz / 2
            m.cube("bow", [5.35, cy - 0.65, cz - L / 2], [1.3, 1.3, L], CRY, key="blimb%d" % k, detail=crystal, rot=[ang * sg, 0, 0], pivot=[6, cy, cz], grad=0.05)
            y, z = y + dy, z + dz
        P_tip = (y, z)
        if sg == 1: tipU = (y, z)
        else: tipD = (y, z)
    pull = 6 if (P and P.get("pull")) else 0
    # الوتر: خط مستقيم بين الطرفين (ثابت)، والسهم ممدود فوقه
    m.cube("bow", [5.9, tipU[0] - 0.1, tipD[1]], [0.2, 0.2, tipU[1] - tipD[1]], STRING, key="string", detail=solid(STRING), grad=0.0, noise=0)
    m.bone("arrow", [6, 11, 0], "bow")
    m.cube("arrow", [5.8, -4.0, -0.2], [0.4, 14.8, 0.4], SHAFT, key="shaft", detail=solid(SHAFT), grad=0.05, noise=2)
    m.cube("arrow", [5.45, -6.4, -0.55], [1.1, 2.6, 1.1], CRY_L, key="tip", detail=crystal, rot=[0, 0, 0], grad=0.2)
    m.cube("arrow", [5.7, 8.4, -0.9], [0.6, 2.6, 1.8], INK_X, key="fletchA", detail=solid(INK_X), grad=0.05)
    m.cube("arrow", [5.1, 8.4, -0.3], [1.8, 2.6, 0.6], INK_L, key="fletchB", detail=solid(INK_L), grad=0.05)
    # ── ذراع السحب (يمين) ──
    m.bone("arm_r", [-6, 23, 0], "body")
    m.cube("arm_r", [-6.8, 17.6, -0.8], [1.6, 5.4, 1.6], BONE, key="uarm", detail=knob, grad=0.1)
    m.bone("fore_r", [-6, 17.2, 0], "arm_r")
    m.cube("fore_r", [-7.1, 16.1, -1.1], [2.2, 2.2, 2.2], BONE_D, key="elb", detail=knob, grad=0.1)
    m.cube("fore_r", [-6.8, 11.4, -0.8], [1.6, 4.8, 1.6], BONE, key="farm", detail=knob, grad=0.1)
    m.cube("fore_r", [-7.2, 10.2, -1.2], [2.4, 1.6, 2.4], BONE_D, key="hand", detail=knob, grad=0.1)

    # ── الأرجل: فخذ + ركبة منتفخة + ساق + كاحل + قدم ──
    for s, nm in ((1, "leg_l"), (-1, "leg_r")):
        px = 2.4 * s
        m.bone(nm, [px, 13, 0], "body")
        m.cube(nm, [px - 0.8, 7.6, -0.8], [1.6, 5.4, 1.6], BONE, key="thigh", detail=knob, grad=0.1)
        m.cube(nm, [px - 1.2, 6.2, -1.2], [2.4, 2.4, 2.4], BONE_D, key="knee", detail=knob, grad=0.1)
        m.cube(nm, [px - 0.8, 1.8, -0.8], [1.6, 4.6, 1.6], BONE, key="shin", detail=knob, grad=0.1)
        m.cube(nm, [px - 1.1, 1.0, -1.1], [2.2, 1.6, 2.2], BONE_D, key="ankle", detail=knob, grad=0.1)
        m.cube(nm, [px - 1.5, 0, -2.6], [3, 1.0, 4], BONE_D, key="foot", detail=knob, grad=0.1)
    return m


def write_anims():
    f = RP + "/animations/sh.animation.json"
    d = json.load(open(f)); A = d["animations"]
    A["animation.sh_trainer.idle"] = {"loop": True, "bones": {
        "body": {"position": [0, "math.sin(query.life_time*90)*0.15", 0]},
        "head": {"rotation": ["math.sin(query.life_time*70)*2", "math.sin(query.life_time*35)*8", 0]},
        "arm_l": {"rotation": ["math.sin(query.life_time*90)*2", 0, "-2 - math.sin(query.life_time*90)*1.5"]},
        "arm_r": {"rotation": ["-math.sin(query.life_time*90)*2", 0, "2 + math.sin(query.life_time*90)*1.5"]}}}
    A["animation.sh_trainer.walk"] = {"loop": True, "bones": {
        "leg_l": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*40*query.modified_move_speed", 0, 0]},
        "leg_r": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*-40*query.modified_move_speed", 0, 0]},
        "arm_l": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*-30*query.modified_move_speed", 0, 0]},
        "arm_r": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*30*query.modified_move_speed", 0, 0]}}}
    A["animation.sh_archer.walk"] = {"loop": True, "bones": {
        "leg_l": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*38*query.modified_move_speed", 0, 0]},
        "leg_r": {"rotation": ["math.cos(query.modified_distance_moved*38.17)*-38*query.modified_move_speed", 0, 0]},
        "body": {"rotation": [0, "math.cos(query.modified_distance_moved*38.17)*3*query.modified_move_speed", 0]},
        "cape": {"rotation": ["12*query.modified_move_speed + math.sin(query.modified_distance_moved*38.17)*6*query.modified_move_speed", 0, 0]}}}
    A["animation.sh_archer.idle"] = {"loop": True, "bones": {
        "body": {"position": [0, "math.sin(query.life_time*80)*0.12", 0]},
        "arm_l": {"rotation": ["math.sin(query.life_time*100)*1.5", 0, 0]},
        "arm_r": {"rotation": ["math.sin(query.life_time*100 + 40)*2", "math.sin(query.life_time*100)*2", 0]},
        "head": {"rotation": [0, "math.sin(query.life_time*30)*10", "math.sin(query.life_time*55)*2"]},
        "cape": {"rotation": ["4 + math.sin(query.life_time*90)*3", 0, 0]}}}
    A.pop("animation.sh_archer.float", None)
    json.dump(d, open(f, "w"), indent=2)
    # كيانات العميل
    for n, geo, tex, anims in (("sh_trainer", "sh_trainer", "sh_trainer", {"idle": "animation.sh_trainer.idle", "walk": "animation.sh_trainer.walk", "look": "animation.sh.look"}),
                               ("sh_training_archer", "sh_archer", "sh_archer", {"walk": "animation.sh_archer.walk", "idle": "animation.sh_archer.idle", "look": "animation.sh.look"})):
        p = RP + f"/entity/{n}.entity.json"
        e = json.load(open(p)); de = e["minecraft:client_entity"]["description"]
        de["animations"] = anims
        de["scripts"] = {"animate": list(anims.keys())}
        json.dump(e, open(p, "w"), indent=2)


if __name__ == "__main__":
    build_trainer().save(GEO.format("sh_trainer"), TEX.format("sh_trainer"))
    build_archer().save(GEO.format("sh_archer"), TEX.format("sh_archer"))
    write_anims()
