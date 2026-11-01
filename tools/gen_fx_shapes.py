"""مكتبة أشكال المهارات 3D (كيان واحد sh:fx_shape بعدة موديلات يختارها السكربت بالخاصية sh:v).

كل شكل مصنوع هنا من مكعبات (بلورات، قبضة حديد، أجنحة، حلقات صوت، أرقام ذهبية، ساعة، مطرقة قاضي، نيزك، ثقب أسود...).
الاتفاقيات:
  * الأشكال اللي تطير مبنية باتجاه -Z (الأمام). الأرضية قاعدتها y=0. الباقي مركزها نقطة الأصل.
  * الدوران: عظام spin (Y يدور بسرعة sh:s) ← tilt (X = sh:p) ← roll (Z = sh:a + الوقت×sh:w) ← body.
    الحجم = sh:r مع نبضة ظهور سريعة. كل دوران مكعب على محور واحد بس (حتى ما يختلف الترتيب باللعبة).
  * التكستشر لوحة ألوان واحدة 64x64 لكل الأشكال، وكل وجه يشير لبكسل لونه (فاتح فوق، أغمق بالجوانب والأسفل).
المخرجات: geo + تكستشر + كيان BP/RP + render controller + حركات + BP/scripts/shapes.js (أرقام الأشكال للسكربت).
التشغيل: python3 tools/gen_fx_shapes.py  (يطلع معاينة بـ /tmp إذا انطى --preview مجلد)
"""
import json
import math
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")
ATLAS_W = 64
ATLAS = []  # ألوان مشتركة لكل الأشكال


def _cl(v):
    return max(0, min(255, int(round(v))))


def uv_of(rgb):
    rgb = tuple(_cl(v) for v in rgb[:3])
    if rgb not in ATLAS:
        assert len(ATLAS) < ATLAS_W * ATLAS_W, "اللوحة ممتلئة"
        ATLAS.append(rgb)
    i = ATLAS.index(rgb)
    return {"uv": [i % ATLAS_W, i // ATLAS_W], "uv_size": [1, 1]}


def mul(c, k):
    return tuple(_cl(v * k) for v in c)


def mix(a, b, t):
    return tuple(_cl(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Shape:
    def __init__(self, name, ground=False):
        self.name = name
        self.ground = ground
        self.bones = [
            {"name": "spin", "pivot": [0, 0, 0]},
            {"name": "tilt", "parent": "spin", "pivot": [0, 0, 0]},
            {"name": "roll", "parent": "tilt", "pivot": [0, 0, 0]},
            {"name": "body", "parent": "roll", "pivot": [0, 0, 0], "cubes": []},
        ]
        self.extra_anim = None

    def bone(self, name, parent="body", pivot=(0, 0, 0), rot=None):
        b = {"name": name, "parent": parent, "pivot": [round(v, 3) for v in pivot], "cubes": []}
        if rot:
            b["rotation"] = [round(v, 3) for v in rot]
        self.bones.append(b)
        return name

    def _bone(self, name):
        for b in self.bones:
            if b["name"] == name:
                b.setdefault("cubes", [])
                return b
        raise KeyError(name)

    def box(self, c, size, col, bone="body", rot=None, pivot=None, top=None, flat=False):
        """مكعب مركزه c. rot = [x,y,z] على محور واحد بس. flat = بدون تظليل (ألوان مضيئة)."""
        w, h, d = size
        if flat:
            m = s = u = dn = uv_of(col)
        else:
            m = uv_of(col)
            s = uv_of(mul(col, 0.84))
            u = uv_of(top or mix(col, (255, 255, 255), 0.18))
            dn = uv_of(mul(col, 0.66))
        cube = {
            "origin": [round(c[0] - w / 2, 3), round(c[1] - h / 2, 3), round(c[2] - d / 2, 3)],
            "size": [round(w, 3), round(h, 3), round(d, 3)],
            "uv": {"north": m, "south": m, "east": s, "west": s, "up": u, "down": dn},
        }
        if rot and any(rot):
            assert sum(1 for v in rot if v) == 1, "دوران على محور واحد بس"
            cube["rotation"] = [round(v, 3) for v in rot]
            cube["pivot"] = [round(v, 3) for v in (pivot if pivot is not None else c)]
        self._bone(bone)["cubes"].append(cube)

    def geometry(self):
        pts = []
        for b in self.bones:
            for cb in b.get("cubes", []):
                o, s = cb["origin"], cb["size"]
                pts += [o, [o[0] + s[0], o[1] + s[1], o[2] + s[2]]]
        ext = max(max(abs(v) for p in pts for v in p), 8) / 16.0
        vb = round(min(30, ext * 2 * 3 + 2), 1)
        return {
            "description": {"identifier": f"geometry.sh_shape_{self.name}", "texture_width": ATLAS_W, "texture_height": ATLAS_W,
                            "visible_bounds_width": vb, "visible_bounds_height": vb, "visible_bounds_offset": [0, vb / 4 if self.ground else 0, 0]},
            "bones": [b for b in self.bones if b.get("cubes") or b["name"] in ("spin", "tilt", "roll", "body") or any(x.get("parent") == b["name"] for x in self.bones)],
        }


# ───────────────────────── أدوات بناء ─────────────────────────
def spike_up(S, base, length, w0, cols, tilt=0.0, bone="body", n=5, tip=None, twist=True):
    """شوكة بلورية عمودية (+Y) من base. tilt = دوران X حول القاعدة (سالب = تميل لـ+Z). مقطعها على شكل + أو مثمن."""
    h = length / n
    for k in range(n):
        t = k / max(1, n - 1)
        w = max(0.6, w0 * (1 - 0.82 * t ** 1.3))
        col = cols[min(len(cols) - 1, int(t * len(cols)))]
        cy = base[1] + h * k + h / 2
        c = (base[0], cy, base[2])
        rot = [tilt, 0, 0] if tilt else None
        if tilt or not twist:
            S.box(c, (w, h * 1.02, w * 0.55), col, bone=bone, rot=rot, pivot=base)
            S.box(c, (w * 0.55, h * 1.02, w), mul(col, 0.92), bone=bone, rot=rot, pivot=base)
        else:
            S.box(c, (w, h * 1.02, w), col, bone=bone)
            S.box(c, (w * 0.72, h * 1.02, w * 0.72), mix(col, (255, 255, 255), 0.25), bone=bone, rot=[0, 45, 0])
    tcol = tip or mix(cols[-1], (255, 255, 255), 0.6)
    tw = max(0.5, w0 * 0.16)
    c = (base[0], base[1] + length + 0.6, base[2])
    S.box(c, (tw, 1.6, tw), tcol, bone=bone, rot=[tilt, 0, 0] if tilt else None, pivot=base, flat=True)


def ring(S, center, r, n, seg, col, axis="y", bone="body", skip=None, phase=0.0, col2=None):
    """حلقة من n قطع مماسية. axis=y أفقية، axis=z عمودية تواجه -Z. seg=(طول، سمك1، سمك2)."""
    L, a, b = seg
    for i in range(n):
        if skip and skip(i):
            continue
        ang = phase + i * 360.0 / n
        c_col = col2 if (col2 and i % 2) else col
        if axis == "y":
            S.box((center[0], center[1], center[2] + r), (L, a, b), c_col, bone=bone, rot=[0, ang, 0], pivot=center)
        else:
            S.box((center[0], center[1] + r, center[2]), (L, a, b), c_col, bone=bone, rot=[0, 0, ang], pivot=center)


def disc_rows(S, center, r, depth, col, step=2.0, axis="z", col2=None):
    """قرص مدور تقريبي من صفوف. axis=z يواجه -Z، axis=y أفقي."""
    y = -r + step / 2
    k = 0
    while y < r:
        w = 2 * math.sqrt(max(0.0, r * r - y * y))
        cc = col2 if (col2 and k % 2) else col
        if axis == "z":
            S.box((center[0], center[1] + y, center[2]), (w, step * 1.02, depth), cc)
        else:
            S.box((center[0], center[1], center[2] + y), (w, depth, step * 1.02), cc)
        y += step
        k += 1


def sphere(S, center, r, col, rim=None, step=2.0):
    y = -r + step / 2
    while y < r:
        w = 2 * math.sqrt(max(0.0, r * r - y * y))
        S.box((center[0], center[1] + y, center[2]), (w, step * 1.02, w), col, top=rim)
        S.box((center[0], center[1] + y, center[2]), (w * 0.72, step * 1.02, w * 0.72), col, rot=[0, 45, 0], top=rim)
        y += step


def radial_spikes(S, dirs, length, w0, cols, start=1.5, prefix="sp"):
    """أشواك من المركز باتجاهات (tilt, yaw): tilt زاوية عن +Y (0 فوق، 180 جوه)."""
    for i, (tilt, yaw) in enumerate(dirs):
        bn = S.bone(f"{prefix}{i}", pivot=(0, 0, 0), rot=[0, yaw, 0] if yaw else None)
        L = length[i % len(length)] if isinstance(length, (list, tuple)) else length
        if tilt == 180:
            spike_down(S, start, L, w0, cols, bn)
        elif tilt == 0:
            spike_up(S, (0, start, 0), L, w0, cols, bone=bn, n=4, twist=False)
        else:
            # الدوران حول المركز (مو القاعدة) حتى الشوكة تطلع من الكرة
            spike_up_pivot(S, start, L, w0, cols, -tilt, bn)


def spike_up_pivot(S, start, L, w0, cols, tilt, bone, n=4):
    h = L / n
    for k in range(n):
        t = k / (n - 1)
        w = max(0.6, w0 * (1 - 0.82 * t ** 1.3))
        col = cols[min(len(cols) - 1, int(t * len(cols)))]
        c = (0, start + h * k + h / 2, 0)
        S.box(c, (w, h * 1.02, w * 0.55), col, bone=bone, rot=[tilt, 0, 0], pivot=(0, 0, 0))
        S.box(c, (w * 0.55, h * 1.02, w), mul(col, 0.92), bone=bone, rot=[tilt, 0, 0], pivot=(0, 0, 0))


def spike_down(S, start, L, w0, cols, bone):
    n = 4
    h = L / n
    for k in range(n):
        t = k / (n - 1)
        w = max(0.6, w0 * (1 - 0.82 * t ** 1.3))
        col = cols[min(len(cols) - 1, int(t * len(cols)))]
        c = (0, -start - h * k - h / 2, 0)
        S.box(c, (w, h * 1.02, w * 0.55), col, bone=bone)
        S.box(c, (w * 0.55, h * 1.02, w), mul(col, 0.92), bone=bone)


def spike_z(S, profile, cols, ridge=None, y=0.0):
    """جسم على طول -Z: profile = [(z_back, z_front, عرض)]. مقطع + مع خط لامع فوق."""
    for i, (z0, z1, w) in enumerate(profile):
        col = cols[min(len(cols) - 1, i)]
        L = abs(z0 - z1)
        c = (0, y, (z0 + z1) / 2)
        S.box(c, (w, w * 0.56, L * 1.02), col)
        S.box(c, (w * 0.56, w, L * 1.02), mul(col, 0.9))
        if ridge and w > 1.6:
            S.box((0, y + w * 0.5, (z0 + z1) / 2), (0.7, 0.5, L * 0.9), ridge, flat=True)


# ───────────────────────── الألوان ─────────────────────────
PINK, PINK_HI, PINK_W, MAGENTA, VIOLET = (255, 110, 200), (255, 175, 228), (255, 240, 250), (196, 50, 150), (160, 95, 240)
IRON, IRON_HI, IRON_LO, BRONZE = (158, 165, 178), (214, 220, 232), (88, 93, 106), (205, 132, 52)
WIND, WIND_HI, WIND_W, WIND_LO = (110, 235, 140), (180, 255, 200), (240, 255, 245), (60, 170, 110)
TEAL, TEAL_HI, TEAL_W, TEAL_LO = (60, 235, 225), (150, 255, 245), (235, 255, 255), (20, 140, 160)
GOLD, GOLD_HI, GOLD_LO, RED = (255, 196, 50), (255, 236, 140), (160, 100, 18), (255, 72, 56)
LAW, LAW_HI, LAW_LO = (170, 90, 255), (215, 170, 255), (70, 35, 120)
BLUE, BLUE_HI, BLUE_W, BLUE_LO = (70, 160, 255), (150, 210, 255), (230, 245, 255), (25, 70, 170)
AMBER, BONE, GUM = (255, 175, 40), (246, 238, 214), (165, 40, 55)
STAR_G, STAR_W, VOIDC, VOID_RIM = (255, 214, 90), (255, 250, 225), (14, 8, 26), (120, 60, 220)
WHITE = (255, 255, 255)

SHAPES = []


def shape(name, ground=False):
    def deco(fn):
        SHAPES.append((name, ground, fn))
        return fn
    return deco


# ───────────────────────── البلورة ─────────────────────────
@shape("crystal_spike")
def _(S):
    spike_z(S, [(10, 6, 3.0), (6, 0, 5.0), (0, -6, 5.6), (-6, -11, 4.2), (-11, -14.5, 2.6), (-14.5, -17, 1.2)],
            [MAGENTA, PINK, PINK_HI, PINK, PINK_HI, PINK_W], ridge=PINK_W)


@shape("crystal_lance")
def _(S):
    spike_z(S, [(26, 18, 4.0), (18, 8, 7.0), (8, -4, 8.0), (-4, -16, 7.0), (-16, -26, 5.0), (-26, -33, 3.0), (-33, -38, 1.4)],
            [MAGENTA, PINK, PINK_HI, PINK, PINK_HI, PINK_W, WHITE], ridge=PINK_W)
    for z in (14, 2, -10):
        S.box((0, 0, z), (9.6, 4.8, 1.6), VIOLET)
        S.box((0, 0, z), (4.8, 9.6, 1.6), VIOLET)


@shape("crystal_gem")
def _(S):
    for y, w, col in ((-3.5, 1.4, MAGENTA), (-2.5, 3.0, PINK), (-1.0, 4.6, PINK_HI), (0.6, 4.6, PINK), (2.1, 3.0, PINK_HI), (3.3, 1.4, PINK_W)):
        S.box((0, y, 0), (w, 1.55, w), col)
        S.box((0, y, 0), (w * 0.72, 1.55, w * 0.72), mix(col, WHITE, 0.2), rot=[0, 45, 0])


@shape("crystal_cluster", ground=True)
def _(S):
    cols = [MAGENTA, PINK, PINK_HI, PINK_W]
    spike_up(S, (0, 0, 0), 30, 7, cols)
    for i, (L, w, tilt, r) in enumerate(((20, 5, 26, 3), (15, 4, 34, 3.5), (22, 5, 22, 3), (14, 4, 38, 3.5), (18, 4.5, 30, 3), (16, 4, 32, 3.5))):
        bn = S.bone(f"c{i}", rot=[0, i * 60 + 15, 0])
        spike_up(S, (0, 0, r), L, w, cols, tilt=-tilt, bone=bn, n=4)
    for i in range(7):
        a = math.radians(i * 51)
        S.box((math.cos(a) * 6, 0.9, math.sin(a) * 6), (3.4, 1.8, 3.4), mul(MAGENTA, 0.7))


@shape("crystal_cage", ground=True)
def _(S):
    cols = [MAGENTA, PINK, PINK_HI, PINK_W]
    for i in range(8):
        bn = S.bone(f"p{i}", rot=[0, i * 45, 0])
        spike_up(S, (0, 0, 13), 32, 4.6, cols, tilt=7, bone=bn, n=5)
    for y in (3, 24):
        ring(S, (0, y, 0), 13.4 if y == 3 else 11.2, 16, (5.4 if y == 3 else 4.6, 1.8, 1.6), VIOLET, col2=PINK_HI)
    ring(S, (0, 0.8, 0), 15.5, 12, (3.2, 1.6, 3.2), mul(MAGENTA, 0.75))


@shape("crystal_plate")
def _(S):
    for s, z, col in ((7.2, 0.6, MAGENTA), (6.0, -0.4, PINK), (3.8, -1.2, PINK_HI), (1.7, -1.8, PINK_W)):
        for a in (0, 60, 120):
            S.box((0, 0, z), (s, s * math.sqrt(3), 1.6 if s > 4 else 1.0), col, rot=[0, 0, a], pivot=(0, 0, z), flat=s < 2)


@shape("crystal_nova")
def _(S):
    sphere(S, (0, 0, 0), 4.5, PINK_HI, rim=PINK_W)
    dirs = [(0, 0), (180, 0)] + [(55, i * 60) for i in range(6)] + [(125, i * 60 + 30) for i in range(6)] + [(90, i * 90 + 45) for i in range(4)]
    radial_spikes(S, dirs, [18, 14, 16], 4.2, [PINK, PINK_HI, PINK_W], start=3.0)


# ───────────────────────── الحديد ─────────────────────────
@shape("iron_fist")
def _(S):
    S.box((0, 0, -1), (14, 11, 9), IRON)
    for x in (-5.25, -1.75, 1.75, 5.25):
        S.box((x, 3.0, -6.0), (3.3, 4.4, 3.0), IRON_HI)          # مفاصل
        S.box((x, 4.6, -6.1), (1.4, 0.8, 3.2), WHITE, flat=True)   # لمعة
        S.box((x, -2.6, -6.2), (3.1, 4.2, 2.6), mul(IRON, 0.95))  # أصابع ملفوفة
    for x in (-3.5, 0, 3.5):
        S.box((x, -0.6, -7.4), (0.5, 9.0, 0.4), IRON_LO, flat=True)
    S.box((-7.6, -0.8, -2.6), (3.0, 4.4, 7.4), IRON)               # إبهام
    S.box((-5.2, -3.6, -6.4), (5.6, 2.8, 2.4), IRON_HI)
    S.box((0, 0, 5.8), (15.6, 13.2, 4.6), BRONZE)                  # سوار
    for x in (-5.5, 0, 5.5):
        S.box((x, 6.7, 5.8), (1.4, 0.6, 1.4), GOLD_HI, flat=True)
        S.box((x, -6.7, 5.8), (1.4, 0.6, 1.4), GOLD_HI, flat=True)
    S.box((0, 0, 12.5), (11.5, 10.5, 9), IRON_LO)                  # ساعد
    for z in (10, 14):
        S.box((0, 0, z), (12, 11, 0.8), IRON, flat=False)


# ───────────────────────── الريح ─────────────────────────
@shape("wind_crescent")
def _(S):
    for k in range(15):
        ang = -70 + k * 10
        t = 1 - abs(ang) / 75
        S.box((0, 0, 8 - 16), (4.4, 0.6 + 1.6 * t, 0.8 + 1.8 * t), WIND_W, rot=[0, ang, 0], pivot=(0, 0, 8))
        S.box((0, 0, 8 - 14.2), (3.8, 0.5 + 1.2 * t, 0.8 + 1.4 * t), WIND, rot=[0, ang, 0], pivot=(0, 0, 8))
        if abs(ang) < 50:
            S.box((0, 0, 8 - 12.6), (3.4, 0.4 + 0.8 * t, 0.8), WIND_LO, rot=[0, ang, 0], pivot=(0, 0, 8))


@shape("tornado", ground=True)
def _(S):
    for lv in range(8):
        y = 1 + lv * 4.2
        r = 3.5 + lv * 1.6
        n = 10
        L = 2 * math.pi * r / n * 0.68
        col = mix(WIND_LO, WIND_W, lv / 7)
        ring(S, (0, y, 0), r, n, (L, 2.2, 1.3), col, phase=lv * 19, skip=lambda i: i % 5 == 4, col2=mix(col, WHITE, 0.3))


@shape("wings")
def _(S):
    for side, name in ((-1, "wl"), (1, "wr")):
        base = S.bone(name + "b", pivot=(side * 1.5, 0, 1), rot=[0, side * -18, 0])
        wing = S.bone(name, parent=base, pivot=(side * 1.5, 0, 1))
        S.box((side * 9, 1.2, 1), (15, 2.6, 1.4), WHITE, bone=wing)
        S.box((side * 4, 2.4, 1), (6, 2.0, 1.6), WIND_HI, bone=wing)
        for k in range(7):
            x = side * (3 + k * 2.1)
            L = 6 + k * 1.3
            S.box((x, 1.2 - L / 2, 1.2), (1.9, L, 0.8), WHITE, bone=wing)
            S.box((x, 1.2 - L + 1.2, 1.25), (1.9, 2.4, 0.9), WIND, bone=wing)
        for k in range(5):
            x = side * (4 + k * 2.4)
            S.box((x, -0.6, 0.5), (2.2, 3.5, 0.9), WIND_HI, bone=wing)


# ───────────────────────── الصدى ─────────────────────────
@shape("sound_ring")
def _(S):
    ring(S, (0, 0, 0), 14, 18, (5.2, 2.2, 1.6), TEAL, axis="z", col2=TEAL_W)
    ring(S, (0, 0, 1.5), 9.5, 14, (4.4, 1.6, 1.2), TEAL_HI, axis="z", skip=lambda i: i % 3 == 2)
    ring(S, (0, 0, 3), 5, 8, (3.8, 1.4, 1.0), TEAL_LO, axis="z")


@shape("echo_glyph")
def _(S):
    for (c, s) in (((0, 7, 0), (14, 1.8, 1.6)), ((0, -7, 0), (14, 1.8, 1.6)), ((7, 0, 0), (1.8, 14, 1.6)), ((-7, 0, 0), (1.8, 14, 1.6))):
        S.box(c, s, TEAL, rot=[0, 0, 45], pivot=(0, 0, 0))
    for (c, s) in (((0, 4, -0.6), (8, 1.4, 1.2)), ((0, -4, -0.6), (8, 1.4, 1.2)), ((4, 0, -0.6), (1.4, 8, 1.2)), ((-4, 0, -0.6), (1.4, 8, 1.2))):
        S.box(c, s, TEAL_HI)
    S.box((0, 0, -1.2), (3, 3, 2), TEAL_W, flat=True)
    for (c, s) in (((0, 13, 0), (1.6, 3, 1.4)), ((0, -13, 0), (1.6, 3, 1.4)), ((13, 0, 0), (3, 1.6, 1.4)), ((-13, 0, 0), (3, 1.6, 1.4))):
        S.box(c, s, TEAL_W, flat=True)


# ───────────────────────── المحاسب: أرقام ورموز ذهبية ─────────────────────────
FONT = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"], "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"], "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "010", "010", "010"], "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"], "-": ["000", "000", "111", "000", "000"], "/": ["010", "000", "111", "000", "010"],
}


def glyph(S, rows, col, back):
    cell = 4.0
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != "1":
                continue
            x = (c - 1) * cell        # +X = يمين المشاهد باللعبة (نفس قراءة الرقم)
            y = (2 - r) * cell
            S.box((x, y, 0), (3.7, 3.7, 3.0), col, top=GOLD_HI if col == GOLD else None)
            S.box((x, y, 1.8), (4.6, 4.6, 1.0), back)


for _d in "0123456789":
    shape(f"digit_{_d}")(lambda S, d=_d: glyph(S, FONT[d], GOLD, GOLD_LO))


@shape("sym_minus")
def _(S):
    glyph(S, FONT["-"], RED, mul(RED, 0.45))


@shape("sym_divide")
def _(S):
    glyph(S, FONT["/"], (255, 140, 40), (120, 60, 10))


def arrow(S, col, hi):
    S.box((0, 0, 4), (3, 3, 16), col)
    for k, w in enumerate((11, 8.5, 6, 3.5, 1.4)):
        S.box((0, 0, -4.8 - k * 2), (w, 3.2, 2.1), hi if k % 2 else col)


@shape("arrow_gold")
def _(S):
    arrow(S, GOLD, GOLD_HI)


@shape("arrow_blue")
def _(S):
    arrow(S, BLUE, BLUE_W)


# ───────────────────────── كاتب القوانين ─────────────────────────
@shape("weight", ground=True)
def _(S):
    DARK = (58, 56, 70)
    for y0, y1, w in ((0, 4, 24), (4, 9, 22), (9, 14, 20), (14, 18, 18)):
        S.box((0, (y0 + y1) / 2, 0), (w, y1 - y0, w), DARK)
    S.box((0, 6.5, 0), (22.6, 1.4, 22.6), GOLD, flat=False)
    for z in (-11.4, 11.4):
        S.box((0, 9.5, z), (9, 6, 0.8), LAW_HI, flat=True)
        S.box((0, 9.5, z * 1.02), (5, 2.2, 0.8), WHITE, flat=True)
    for x in (-6, 6):
        S.box((x, 21, 0), (3, 6, 3), GOLD_LO)
    S.box((0, 25.5, 0), (15, 3, 3), GOLD)


@shape("rune_pillar", ground=True)
def _(S):
    STONE = (78, 66, 104)
    S.box((0, 2, 0), (9, 4, 9), mul(STONE, 0.8))
    S.box((0, 19, 0), (5.4, 30, 5.4), STONE)
    for y in (9, 17, 25, 32):
        S.box((0, y, 0), (6.4, 1.4, 6.4), LAW_HI, flat=True)
    S.box((0, 34.6, 0), (7.4, 1.8, 7.4), mul(STONE, 0.9))
    for y, w in ((38, 1.6), (39.5, 3.0), (41, 3.6), (42.5, 2.6), (43.8, 1.2)):
        S.box((0, y, 0), (w, 1.5, w), LAW_HI if w > 2 else WHITE, rot=[0, 45, 0], flat=w < 2)


@shape("mirror")
def _(S):
    for s, z, col, fl in ((8.6, 0.6, LAW, False), (7.4, -0.3, (226, 232, 246), False), (5.6, -0.6, (246, 250, 255), True)):
        for a in (0, 60, 120):
            S.box((0, 0, z), (s, s * math.sqrt(3), 1.4), col, rot=[0, 0, a], pivot=(0, 0, z), flat=fl)
    S.box((-2, 1.5, -1.1), (1.0, 9, 0.4), WHITE, rot=[0, 0, 30], flat=True)
    S.box((1.5, -2.5, -1.1), (0.7, 5, 0.4), WHITE, rot=[0, 0, 30], flat=True)


@shape("clock")
def _(S):
    ring(S, (0, 0, 0), 14, 20, (4.8, 2.4, 2.4), GOLD, axis="z", col2=GOLD_HI)
    disc_rows(S, (0, 0, 0.8), 13, 1.2, (238, 228, 200), col2=(228, 216, 186))
    for i in range(12):
        S.box((0, 10.8, -0.4), (1.2 if i % 3 else 1.8, 2.8 if i % 3 else 3.6, 1.0), LAW_LO, rot=[0, 0, i * 30] if i else None, pivot=(0, 0, 0))
    hm = S.bone("hand_m", pivot=(0, 0, 0))
    S.box((0, 5, -1.2), (1.1, 10, 0.8), (40, 26, 60), bone=hm)
    hh = S.bone("hand_h", pivot=(0, 0, 0))
    S.box((0, 3.2, -1.8), (1.8, 6.4, 0.8), LAW, bone=hh)
    S.box((0, 0, -2.4), (2.6, 2.6, 1.0), GOLD_HI, flat=True)


@shape("gavel")
def _(S):
    WOOD = (110, 62, 34)
    S.box((0, 13, 0), (3, 26, 3), WOOD)
    for y in (3, 22):
        S.box((0, y, 0), (3.6, 1.4, 3.6), GOLD)
    S.box((0, 29, 0), (20, 8, 8), WOOD)
    S.box((0, 29, 0), (20, 6.2, 6.2), mul(WOOD, 1.15), rot=[45, 0, 0], pivot=(0, 29, 0))
    S.box((0, 29, 0), (3, 8.6, 8.6), LAW, flat=False)
    for x in (-10.5, 10.5):
        S.box((x, 29, 0), (1.6, 9, 9), GOLD)
        S.box((x * 1.03, 29, 0), (0.8, 4, 4), GOLD_HI, flat=True)


@shape("padlock")
def _(S):
    S.box((0, 0, 0), (14, 11, 6), (110, 70, 200))
    S.box((0, 0, 0), (14.6, 1.4, 6.6), GOLD)
    S.box((0, 1.0, -3.2), (2.2, 2.2, 0.6), (20, 10, 30), flat=True)
    S.box((0, -1.4, -3.2), (1.0, 3.0, 0.6), (20, 10, 30), flat=True)
    for x in (-4.4, 4.4):
        S.box((x, 8.4, 0), (2.4, 6, 2.4), (200, 205, 220))
    S.box((0, 12.2, 0), (11.2, 2.4, 2.4), (220, 225, 240))


# ───────────────────────── محرف المسافة ─────────────────────────
@shape("space_cube")
def _(S):
    h = 12
    for a in (-h, h):
        for b in (-h, h):
            S.box((0, a, b), (2 * h + 1.6, 1.6, 1.6), BLUE_HI)
            S.box((a, 0, b), (1.6, 2 * h + 1.6, 1.6), BLUE)
            S.box((a, b, 0), (1.6, 1.6, 2 * h + 1.6), BLUE_HI)
            for c in (-h, h):
                S.box((a, b, c), (3.2, 3.2, 3.2), BLUE_W, flat=True)
    g = 6
    for a in (-g, g):
        for b in (-g, g):
            S.box((a, 0, b), (1.2, 2 * g + 1.2, 1.2), BLUE_W, rot=[0, 45, 0], pivot=(0, 0, 0))
            S.box((0, a, b), (2 * g + 1.2, 1.2, 1.2), BLUE, rot=[0, 45, 0], pivot=(0, 0, 0))
            S.box((a, b, 0), (1.2, 1.2, 2 * g + 1.2), BLUE, rot=[0, 45, 0], pivot=(0, 0, 0))


@shape("hourglass")
def _(S):
    WOOD = (150, 98, 48)
    for y in (-11.5, 11.5):
        S.box((0, y, 0), (14, 2, 14), WOOD, top=GOLD)
    for x in (-5.6, 5.6):
        for z in (-5.6, 5.6):
            S.box((x, 0, z), (1.6, 21, 1.6), GOLD)
    GL = (178, 220, 255)
    for k, w in enumerate((10, 8, 5.4, 2.6)):
        S.box((0, 9 - k * 2.2, 0), (w, 2.3, w), GL)
        S.box((0, -9 + k * 2.2, 0), (w, 2.3, w), GL)
    SAND = (242, 202, 110)
    for k, w in enumerate((9.2, 7.6)):
        S.box((0, -9.6 + k * 2.2, 0), (w, 2.0, w), SAND)
    S.box((0, 0, 0), (0.8, 6, 0.8), SAND, flat=True)


# ───────────────────────── مستعير الصفات ─────────────────────────
@shape("fang_jaw")
def _(S):
    up = S.bone("jaw_u", pivot=(0, 0, 6))
    lo = S.bone("jaw_l", pivot=(0, 0, 6))
    S.box((0, 6, 0), (17, 3.4, 5), GUM, bone=up)
    S.box((0, -6, 0), (17, 3.4, 5), GUM, bone=lo)
    for x, L, w in ((-6, 8, 2.8), (6, 8, 2.8), (-3, 4, 1.8), (3, 4, 1.8), (-1, 3.4, 1.6), (1, 3.4, 1.6)):
        for k in range(3):
            ww = w * (1 - k * 0.3)
            S.box((x, 4.4 - (k + 0.5) * L / 3, -1), (ww, L / 3 * 1.05, ww), BONE, bone=up)
            S.box((x * 0.95, -4.4 + (k + 0.5) * L / 3 * 0.8, -1), (ww * 0.9, L / 3 * 0.85, ww * 0.9), BONE, bone=lo)


@shape("hunter_eye")
def _(S):
    for y, w in ((-4, 6), (-2, 12), (0, 16), (2, 12), (4, 6)):
        S.box((0, y, 0.8), (w + 1.6, 2.2, 1.2), (60, 36, 10))
        S.box((0, y, 0), (w, 2.05, 1.6), (250, 244, 228))
    for y, w in ((-2.4, 4), (-0.8, 6), (0.8, 6), (2.4, 4)):
        S.box((0, y, -0.9), (w, 1.65, 0.8), AMBER, top=GOLD_HI)
    S.box((0, 0, -1.4), (1.2, 6.2, 0.6), (10, 6, 4), flat=True)
    for x, h in ((-4, 2.5), (0, 3.4), (4, 2.5)):
        S.box((x, 6.6, 0.4), (1.2, h, 1.2), GOLD)


# ───────────────────────── سيد النجوم ─────────────────────────
@shape("meteor")
def _(S):
    ROCK, ROCK2, LAVA = (74, 44, 38), (52, 34, 32), (255, 120, 30)
    S.box((0, 0, 0), (10, 9, 10), ROCK)
    S.box((0, 0.5, 0), (8, 10, 7), ROCK2, rot=[0, 30, 0])
    S.box((0, -0.5, 0), (7, 7, 11), ROCK, rot=[40, 0, 0])
    for (c, s) in (((0, 4.6, -2), (6, 0.5, 0.8)), ((5.1, 0, 1), (0.5, 5, 0.8)), ((-3, -4.6, 0), (5, 0.5, 0.8)), ((0, 0, -5.2), (4, 0.8, 0.5))):
        S.box(c, s, LAVA, flat=True)
    for k, (w, col) in enumerate(((9, (255, 236, 140)), (7.6, (255, 190, 60)), (6, (255, 130, 40)), (4.4, (240, 80, 30)), (3, (190, 40, 25)), (1.8, (120, 24, 18)))):
        z = 7 + k * 4
        S.box((0, 0, z), (w, w * 0.6, 4.2), col, flat=True)
        S.box((0, 0, z), (w * 0.6, w, 4.2), col, flat=True)


@shape("star5")
def _(S):
    for i in range(5):
        for y0, y1, w in ((2, 6, 5.2), (6, 9, 3.8), (9, 11.5, 2.4), (11.5, 13.2, 1.1)):
            col = STAR_G if y1 < 11 else STAR_W
            S.box((0, (y0 + y1) / 2, 0), (w, y1 - y0, 3), col, rot=[0, 0, i * 72] if i else None, pivot=(0, 0, 0))
    S.box((0, 0, 0), (7, 7, 4), STAR_W)
    S.box((0, 0, 0), (6, 6, 4.2), STAR_G, rot=[0, 0, 45])


@shape("black_hole")
def _(S):
    sphere(S, (0, 0, 0), 9, VOIDC, rim=(40, 20, 70))
    disk = S.bone("disk", pivot=(0, 0, 0), rot=[16, 0, 0])
    ring(S, (0, 0, 0), 12, 22, (3.6, 1.0, 3.2), (255, 170, 60), bone=disk, col2=(255, 220, 140))
    ring(S, (0, 0, 0), 16, 26, (4.0, 0.8, 3.6), VOID_RIM, bone=disk, col2=(200, 120, 255))
    ring(S, (0, 0, 0), 20, 30, (4.2, 0.6, 2.4), (90, 40, 170), bone=disk, skip=lambda i: i % 4 == 3)
    ring(S, (0, 0, 0), 10.2, 20, (3.4, 0.9, 0.9), (255, 236, 200), axis="z")


@shape("vortex", ground=True)
def _(S):
    S.box((0, 0.5, 0), (6, 1, 6), BLUE_LO)
    for arm in range(4):
        for k in range(12):
            r = 3 + k * 1.65
            col = mix(BLUE_W, BLUE_LO, k / 11)
            S.box((0, 0.5, r), (3.4 - k * 0.12, 0.9, 2.2), col, rot=[0, arm * 90 + k * 26 + 1, 0], pivot=(0, 0, 0))


@shape("nova")
def _(S):
    sphere(S, (0, 0, 0), 6, STAR_W, rim=WHITE)
    dirs = [(0, 0), (180, 0)] + [(45, i * 60) for i in range(6)] + [(90, i * 60 + 30) for i in range(6)] + [(135, i * 60) for i in range(6)]
    radial_spikes(S, dirs, [22, 17], 5, [STAR_G, (255, 236, 160), STAR_W], start=4.5)


# ───────────────────────── الأسلحة ─────────────────────────
def crescent(S, outer, mid, core):
    for k in range(17):
        ang = -80 + k * 10
        t = math.cos(math.radians(ang) * 90 / 82) ** 0.8 if abs(ang) < 82 else 0.05
        w = 0.8 + 4.2 * t
        for r, col, f, d in ((20.2, outer, 0.35, 1.0), (18.6, mid, 0.6, 1.6), (17.0, core, 0.45, 1.2)):
            S.box((0, r, 0), (3.9, max(0.5, w * f), d), col, rot=[0, 0, ang] if ang else None, pivot=(0, 0, 0), flat=col == core)


@shape("slash_violet")
def _(S):
    crescent(S, (70, 20, 140), (160, 80, 255), (250, 240, 255))


@shape("slash_fire")
def _(S):
    crescent(S, (190, 40, 10), (255, 130, 30), (255, 240, 170))


@shape("slash_gold")
def _(S):
    crescent(S, (170, 100, 10), (255, 200, 60), (255, 250, 220))


@shape("claw_marks")
def _(S):
    for x in (-6, 0, 6):
        for k in range(13):
            t = (k - 6) / 6
            w = 0.5 + 2.6 * (1 - t * t)
            y = t * 13
            S.box((x + 1.2 * t * t, y, 0.6), (w + 1.2, 2.3, 1.2), (150, 30, 70))
            S.box((x + 1.2 * t * t, y, -0.2), (w * 0.55, 2.2, 1.0), (255, 235, 245), flat=True)


@shape("spear_proj")
def _(S):
    WOOD, RING = (120, 40, 30), GOLD
    S.box((0, 0, 11), (1.8, 1.8, 34), WOOD)
    for z in (-2, 8, 18, 26):
        S.box((0, 0, z), (2.4, 2.4, 1.2), RING)
    S.box((0, 0, -6), (8, 1.8, 1.8), GOLD)
    for k, w in enumerate((4.2, 4.8, 4.2, 3.2, 2.0, 0.9)):
        z = -8 - k * 2.4
        S.box((0, 0, z), (w, 1.2, 2.5), (255, 120, 50) if k < 3 else (255, 200, 120))
        S.box((0, 0, z), (w * 0.35, 1.6, 2.5), (255, 245, 220), flat=True)


@shape("afterimage", ground=True)
def _(S):
    D, L = (36, 18, 64), (92, 60, 156)
    S.box((0, 28, 0), (8, 8, 8), D, top=L)
    S.box((0, 18, 0), (8, 12, 4), D, top=L)
    for x in (-6, 6):
        S.box((x, 18, 0), (4, 12, 4), mul(D, 1.15), top=L)
    for x in (-2, 2):
        S.box((x, 6, 0), (4, 12, 4), mul(D, 0.9), top=L)
    for y in (4, 10, 16, 22, 30):
        S.box((0, y, -2.6 if y < 24 else -4.1), (8.4 if y < 24 else 8.4, 0.8, 0.4), L, flat=True)


@shape("rock_chunk")
def _(S):
    R1, R2, MOSS = (112, 104, 92), (86, 80, 72), (88, 128, 64)
    S.box((0, 0, 0), (6, 5, 6), R1, top=MOSS)
    S.box((0.8, 0.6, 0), (5, 6, 4), R2, rot=[0, 25, 0])
    S.box((-0.6, -0.4, 0.4), (4, 4, 5), R1, rot=[40, 0, 0])


@shape("sun_chain")
def _(S):
    for i in range(14):
        if i % 2 == 0:
            S.box((0, 0, 11), (4.6, 1.3, 2.4), GOLD, rot=[0, i * 360 / 14, 0] if i else None, pivot=(0, 0, 0))
        else:
            S.box((0, 0, 11), (4.6, 2.6, 1.2), GOLD_HI, rot=[0, i * 360 / 14, 0], pivot=(0, 0, 0))


# ───────────────────────── الإخراج ─────────────────────────
EXTRA_ANIMS = {
    "wings": {"wl": {"rotation": [0, 0, "-18 - math.sin(q.life_time * 640) * 28"]}, "wr": {"rotation": [0, 0, "18 + math.sin(q.life_time * 640) * 28"]}},
    "clock": {"hand_m": {"rotation": [0, 0, "q.life_time * 900"]}, "hand_h": {"rotation": [0, 0, "q.life_time * 75"]}},
    "fang_jaw": {"jaw_u": {"rotation": ["-math.max(0, 38 - q.life_time * 230)", 0, 0]}, "jaw_l": {"rotation": ["math.max(0, 38 - q.life_time * 230)", 0, 0]}},
}


def build():
    shapes = []
    for name, ground, fn in SHAPES:
        S = Shape(name, ground)
        fn(S)
        shapes.append(S)
    return shapes


def write(path, data, compact=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if compact:
            json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
        else:
            json.dump(data, f, indent=1, ensure_ascii=False)


def main():
    shapes = build()
    assert len(shapes) <= 64
    write(os.path.join(RP, "models", "entity", "sh_fx_shapes.geo.json"),
          {"format_version": "1.12.0", "minecraft:geometry": [s.geometry() for s in shapes]})
    img = Image.new("RGBA", (ATLAS_W, ATLAS_W), (0, 0, 0, 0))
    for i, c in enumerate(ATLAS):
        img.putpixel((i % ATLAS_W, i // ATLAS_W), (*c, 255))
    img.save(os.path.join(RP, "textures", "entity", "sh_fx_shapes.png"))
    names = [s.name for s in shapes]
    # كيان BP
    write(os.path.join(BP, "entities", "sh_fx_shape.json"), {
        "format_version": "1.21.50",
        "minecraft:entity": {
            "description": {
                "identifier": "sh:fx_shape", "is_spawnable": False, "is_summonable": True, "is_experimental": False,
                "properties": {
                    "sh:v": {"type": "int", "range": [0, 63], "default": 0, "client_sync": True},
                    "sh:r": {"type": "float", "range": [0, 40], "default": 1, "client_sync": True},
                    "sh:p": {"type": "float", "range": [-180, 180], "default": 0, "client_sync": True},
                    "sh:a": {"type": "float", "range": [-360, 360], "default": 0, "client_sync": True},
                    "sh:s": {"type": "float", "range": [-3000, 3000], "default": 0, "client_sync": True},
                    "sh:w": {"type": "float", "range": [-3000, 3000], "default": 0, "client_sync": True},
                },
            },
            "component_groups": {"sh:gone": {"minecraft:instant_despawn": {}}},
            "components": {
                "minecraft:type_family": {"family": ["sh_fx", "inanimate"]},
                "minecraft:collision_box": {"width": 0.1, "height": 0.1},
                "minecraft:physics": {"has_gravity": False, "has_collision": False},
                "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
                "minecraft:timer": {"time": 60, "looping": False, "time_down_event": {"event": "sh:die"}},
                "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": "no"}]},
                "minecraft:fire_immune": {},
            },
            "events": {"sh:die": {"add": {"component_groups": ["sh:gone"]}}},
        },
    }, compact=False)
    # كيان RP
    geos = {f"s{i}": f"geometry.sh_shape_{n}" for i, n in enumerate(names)}
    anims = {"fx": "animation.sh_fx.shape"}
    animate = ["fx"]
    for key, bones in EXTRA_ANIMS.items():
        anims[key] = f"animation.sh_fx.shape_{key}"
        animate.append({key: f"q.property('sh:v') == {names.index(key)}"})
    write(os.path.join(RP, "entity", "sh_fx_shape.entity.json"), {
        "format_version": "1.10.0",
        "minecraft:client_entity": {"description": {
            "identifier": "sh:fx_shape",
            "materials": {"default": "entity_alphatest"},
            "textures": {"default": "textures/entity/sh_fx_shapes"},
            "geometry": geos,
            "animations": anims,
            "scripts": {"animate": animate},
            "render_controllers": ["controller.render.sh_fx_shape"],
        }},
    }, compact=False)
    rc_path = os.path.join(RP, "render_controllers", "sh_fx.render_controllers.json")
    rc = json.load(open(rc_path, encoding="utf-8"))
    rc["render_controllers"]["controller.render.sh_fx_shape"] = {
        "arrays": {"geometries": {"Array.g": [f"Geometry.s{i}" for i in range(len(names))]}},
        "geometry": "Array.g[query.property('sh:v')]",
        "materials": [{"*": "Material.default"}],
        "textures": ["Texture.default"],
    }
    write(rc_path, rc, compact=False)
    an_path = os.path.join(RP, "animations", "sh_fx.animation.json")
    an = json.load(open(an_path, encoding="utf-8"))
    an["animations"]["animation.sh_fx.shape"] = {
        "loop": True,
        "bones": {
            "spin": {"rotation": [0, "query.life_time * query.property('sh:s')", 0],
                     "scale": "query.property('sh:r') * math.min(1.0, 0.3 + query.life_time * 7.0)"},
            "tilt": {"rotation": ["query.property('sh:p')", 0, 0]},
            "roll": {"rotation": [0, 0, "query.property('sh:a') + query.life_time * query.property('sh:w')"]},
        },
    }
    for key, bones in EXTRA_ANIMS.items():
        an["animations"][f"animation.sh_fx.shape_{key}"] = {"loop": True, "bones": bones}
    write(an_path, an, compact=False)
    # أرقام الأشكال للسكربت
    with open(os.path.join(BP, "scripts", "shapes.js"), "w", encoding="utf-8") as f:
        f.write("// يتولد تلقائياً من tools/gen_fx_shapes.py — لا تعدله يدوياً\n")
        f.write("export const SHAPE = " + json.dumps({n: i for i, n in enumerate(names)}) + ";\n")
    print(f"shapes ok: {len(names)} أشكال، {len(ATLAS)} لون")
    if "--preview" in sys.argv:
        preview(shapes, sys.argv[sys.argv.index("--preview") + 1])


def preview(shapes, out):
    """صور معاينة (مقلوبة أفقياً حتى تطابق اللعبة: +X يمين المشاهد من الأمام)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tempfile
    from PIL import ImageDraw, ImageOps
    import render as R
    os.makedirs(out, exist_ok=True)
    tex = os.path.join(RP, "textures", "entity", "sh_fx_shapes.png")
    cell = 260
    cols = 6
    rows = math.ceil(len(shapes) / cols)
    sheet = Image.new("RGB", (cols * cell, rows * cell), (40, 42, 50))
    d = ImageDraw.Draw(sheet)
    for i, S in enumerate(shapes):
        g = S.geometry()
        tmp = os.path.join(tempfile.gettempdir(), "sh_shape_tmp.geo.json")
        json.dump({"format_version": "1.12.0", "minecraft:geometry": [g]}, open(tmp, "w"))
        m = R.Model(tmp, tex)
        pose = {}
        if S.name == "fang_jaw":
            pose = {"jaw_u": {"rot": [-20, 0, 0], "pos": [0, 0, 0]}, "jaw_l": {"rot": [20, 0, 0], "pos": [0, 0, 0]}}
        im = R.render(m, pose, yaw=28, pitch=22, size=cell)
        im = ImageOps.mirror(im)
        sheet.paste(im, ((i % cols) * cell, (i // cols) * cell))
        d.text(((i % cols) * cell + 6, (i // cols) * cell + 4), f"{i} {S.name}", fill=(255, 255, 255))
    sheet.save(os.path.join(out, "shapes_sheet.png"))
    print("preview:", os.path.join(out, "shapes_sheet.png"))


if __name__ == "__main__":
    main()
