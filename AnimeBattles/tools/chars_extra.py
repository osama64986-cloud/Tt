"""Naruto (four ages), Sasuke, Ichigo and Tanjiro in the house style (style 1): 8x8 head,
32 px faces, pixel-art cel shading, strand hair — the same look as Goku/Luffy/Zoro.
Built on the helpers of models.py; imported at the end of it."""
import math

import models as M
import sculpt as SC
from models import (SIDES, SKIN, _put, both_arms, both_legs, base_body, dark, head_paint, layered, light,
                    lines, ramp, shell, solid, tones)

ORANGE = (255, 128, 30)
NAVY = (36, 52, 120)
BLACK = (34, 34, 42)
WHITE = (240, 240, 236)
GOLD = (255, 204, 60)
MARK = (30, 20, 14)
N_HAIR = (255, 214, 60)
N_RED = (210, 40, 36)


# ------------------------------------------------------------------ painters
def region(box, col, faces=SIDES):
    x0, y0, x1, y1 = box

    def f(face, px, w, h, base):
        if face not in faces:
            return
        c = col if face in ("north", "east", "up") else dark(col, 0.86)
        for y in range(int(h * y0), int(math.ceil(h * y1))):
            for x in range(int(w * x0), int(math.ceil(w * x1))):
                _put(px, w, h, x, y, c)
    return f


def zipper(col):
    return lines((("north",), [[(0.5, 0), (0.5, 1)]]), col)


def spiral(col, face_="south", r=0.3, cy=0.4):
    def f(face, px, w, h, base):
        if face != face_:
            return
        cx, c_y, R = w / 2, h * cy, min(w, h) * r
        for i in range(120):
            a = i / 120 * math.pi * 2 * 2.0
            rr = R * i / 120
            _put(px, w, h, int(cx + math.cos(a) * rr), int(c_y + math.sin(a) * rr), col)
        for i in range(60):
            a = i / 60 * math.pi * 2
            _put(px, w, h, int(cx + math.cos(a) * R), int(c_y + math.sin(a) * R), col)
    return f


def checker(c1, c2, n=4):
    """Tanjiro's ichimatsu haori: green and black squares."""
    def f(face, px, w, h, base):
        if face in ("up", "down"):
            return
        s = max(2, w // n)
        for y in range(h):
            for x in range(w):
                c = c1 if ((x // s) + (y // s)) % 2 == 0 else c2
                _put(px, w, h, x, y, c if face in ("north", "east") else dark(c, 0.86))
    return f


def holes(face, px, w, h, base):
    """See-through chakra skin (alpha-tested gaps)."""
    if face in ("up", "down"):
        return
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if (x * 7 + y * 11) % 9 not in (0, 1):
                px[x, y] = (0, 0, 0, 0)


def skin_swap(painter, skin):
    """Paint a head with a different skin colour (golden Nine-Tails chakra, Hollow white)."""
    def p(face, img):
        old = M.SKIN
        M.SKIN = skin
        try:
            painter(face, img)
        finally:
            M.SKIN = old
    return p


def leaf_plate(face, px, w, h, base):
    if face != "north":
        return
    ln = (70, 74, 86)
    cx, cy, r = w / 2, h / 2, min(w, h) * 0.32
    for i in range(50):
        a = i / 50 * math.pi * 2 * 1.3
        rr = 0.6 + r * i / 50
        _put(px, w, h, int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr), ln)
    for i in range(4):
        _put(px, w, h, int(cx + r + i), int(cy - r + i * 0.4), ln)


def arm_paint(sleeve, hand=SKIN, cuff=None, top=None, sleeve_to=0.8):
    ex = [region((0, sleeve_to, 1, 1), hand)]
    if top:
        ex.append(region((0, 0, 1, top[1]), top[0]))
    if cuff:
        ex.append(region((0, sleeve_to - 0.07, 1, sleeve_to), cuff))
    return layered(sleeve, ex)


def leg_paint(col, shoe, band=None, shoe_from=0.86, toes=True, toe=None):
    ex = [region((0, shoe_from, 1, 1), shoe)]
    if toes:
        ex.append(region((0.15, shoe_from, 0.85, shoe_from + 0.06), toe or SKIN, faces=("north",)))
    if band:
        ex.append(region((0, band[1], 1, band[2]), band[0]))
    return layered(col, ex)


# ------------------------------------------------------------------ faces (marks on the 32 px face)
M.FACE32.update({
    "naruto": dict(eye="anime", brow="angled", mouth="smile", marks=["whiskers"]),
    "naruto_kid": dict(eye="anime", brow="angled", mouth="big_grin", marks=["whiskers"]),
    "naruto_fox": dict(eye="narrow", brow="sharp", mouth="clench", marks=["whiskers", "fox", "slit_eyes", "fangs"]),
    "naruto_baryon": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["whiskers", "fox", "slit_eyes", "baryon_eyes"]),
    "naruto_sage": dict(eye="anime", brow="angled", mouth="neutral", marks=["whiskers", "sage"]),
    "naruto_kcm": dict(eye="narrow", brow="angled", mouth="smile", marks=["whiskers", "fox"]),
    "naruto_spsm": dict(eye="anime", brow="angled", mouth="neutral", marks=["whiskers", "fox", "sage"]),
    "naruto_adult": dict(eye="anime", brow="angled", mouth="smile", marks=["whiskers"]),
    "naruto_adult_sage": dict(eye="anime", brow="angled", mouth="neutral", marks=["whiskers", "sage"]),
    "naruto_sk": dict(eye="narrow", brow="angled", mouth="smile", marks=["whiskers", "fox", "sage"]),
    "naruto_v2": dict(eye="narrow", brow="none", mouth="none", marks=["v2"]),
    "sasuke": dict(eye="narrow", brow="flat", mouth="neutral"),
    "sasuke_sh": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["sharingan"]),
    "sasuke_cs1": dict(eye="narrow", brow="sharp", mouth="smirk", marks=["sharingan", "cs1"]),
    "sasuke_cs2": dict(eye="narrow", brow="sharp", mouth="smirk", marks=["cs2", "sharingan"]),
    "sasuke_ms": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["ms"]),
    "sasuke_ems": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["ems"]),
    "sasuke_rinne": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["ems", "rinnegan"]),
    "sasuke_adult": dict(eye="narrow", brow="flat", mouth="neutral", marks=["rinnegan"]),
    "sasuke_adult_sh": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["ems", "rinnegan"]),
    "ichigo": dict(eye="narrow", brow="sharp", mouth="corner"),
    "ichigo_hollow": dict(eye="narrow", brow="sharp", mouth="none", marks=["hollow_mask"]),
    "ichigo_mugetsu": dict(eye="narrow", brow="flat", mouth="neutral"),
    "ichigo_vasto": dict(eye="narrow", brow="sharp", mouth="none", marks=["vasto_mask"]),
    "tanjiro": dict(eye="anime", brow="angled", mouth="smile", marks=["tanjiro_scar"]),
    "tanjiro_mark": dict(eye="anime", brow="sharp", mouth="neutral", marks=["tanjiro_mark"]),
    "tanjiro_demon": dict(eye="narrow", brow="sharp", mouth="clench", marks=["tanjiro_mark", "slit_eyes", "fangs", "jaw_mark"]),
    "tanjiro_demon_sun": dict(eye="narrow", brow="sharp", mouth="clench", marks=["tanjiro_mark", "slit_eyes", "fangs", "jaw_mark", "temple_mark"]),
    "muzan": dict(eye="narrow", brow="flat", mouth="neutral", marks=["slit_eyes"]),
    "broly": dict(eye="narrow", brow="sharp", mouth="clench", marks=["cheek_scar"]),
    "broly_wrath": dict(eye="narrow", brow="sharp", mouth="clench", marks=["cheek_scar", "glow_eyes"]),
    "broly_lssj": dict(eye="narrow", brow="sharp", mouth="clench", marks=["cheek_scar", "blank_eyes"]),
    "madara_edo": dict(eye="narrow", brow="flat", mouth="smirk", marks=["edo_cracks", "rinnegan_both"]),
    "madara_sixpaths": dict(eye="narrow", brow="flat", mouth="smirk", marks=["rinnegan_both", "third_eye"]),
    "muzan_final": dict(eye="narrow", brow="sharp", mouth="clench", marks=["slit_eyes", "fangs", "brow_scales", "face_veins"]),
})

_face32_prev = M.face32


def face32(px, W, H, spec, hair, iris, skin):
    marks = spec.get("marks", [])
    _face32_prev(px, W, H, spec, hair, iris, skin)
    k = W / 32.0

    def put(x, y, c):
        for dx in range(int(k)):
            for dy in range(int(k)):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    if "v2" in marks:  # Version 2: the face lost under the boiling chakra: white ringed eyes, a white jagged mouth
        for y in range(8, 32):
            for x in range(32):
                put(x, y, (92, 10, 12) if (x * 3 + y * 7) % 11 else (70, 6, 10))
        for cx in (10, 21):
            for a in range(24):
                t = a / 24 * math.pi * 2
                put(int(cx + 0.5 + math.cos(t) * 2.4), int(19 + math.sin(t) * 2.0), (250, 246, 236))
            put(cx, 19, (250, 246, 236)); put(cx + 1, 19, (250, 246, 236))
        for x in range(9, 23):
            put(x, 26 + (x % 2), (250, 246, 236))
        return
    if "sage" in marks:  # orange pigment over the lids and out to the corners
        for x in list(range(4, 14)) + list(range(18, 28)):
            put(x, 14, (232, 100, 30)); put(x, 15, (232, 100, 30))
        for y in range(16, 20):
            for x in (5, 6, 25, 26):
                put(x, y, (232, 100, 30))
    if "whiskers" in marks:
        wc = (40, 18, 14) if "fox" in marks else (110, 64, 50)
        for y0, slope in ((22, -1), (24, 0), (26, 1)):
            for j in range(5):
                yy = y0 + (slope if j >= 3 else 0)
                put(2 + j, yy, wc); put(29 - j, yy, wc)
                if "fox" in marks:
                    put(2 + j, yy + 1, wc); put(29 - j, yy + 1, wc)
    if "sharingan" in marks and M.EXPR not in ("blink", "hurt"):  # red iris, three tomoe around the pupil
        for cx in (10, 21):
            for x, y in ((cx - 1, 18), (cx + 2, 18), (cx, 21)):
                put(x, y, (10, 6, 8))
    open_eyes = M.EXPR not in ("blink", "hurt")
    if "cs2" in marks and open_eyes:  # black sclera, the dark cross over the bridge of the nose
        for cx in (10, 21):
            for y in range(17, 22):
                for x in range(cx - 2, cx + 4):
                    put(x, y, (16, 14, 20))
            for x, y in ((cx, 19), (cx + 1, 19), (cx, 20), (cx + 1, 20)):
                put(x, y, (200, 20, 30))
    if "cs2" in marks:
        for i in range(-2, 3):
            put(15 + i, 21 + i, (30, 24, 36)); put(16 - i, 21 + i, (30, 24, 36))
    if "cs1" in marks:  # the black flame marks spreading over the left side of his face
        for x, y in ((24, 12), (25, 13), (26, 14), (23, 15), (27, 16), (25, 24), (26, 25), (24, 26), (27, 27), (25, 28), (26, 29), (28, 23), (29, 24)):
            put(x, y, (20, 16, 22))
    if "ms" in marks and open_eyes:  # Sasuke's Mangekyo: a three-bladed pinwheel
        for cx in (10, 21):
            for x, y in ((cx, 19), (cx + 1, 19), (cx, 20), (cx + 1, 20), (cx - 1, 18), (cx + 2, 18), (cx + 2, 21), (cx - 1, 21), (cx - 2, 19), (cx + 3, 20)):
                put(x, y, (10, 6, 8))
    if "ems" in marks and open_eyes:  # Eternal Mangekyo: the pinwheel laid over a six-pointed star
        for cx in (10, 21):
            if "rinnegan" in marks and cx == 21:
                continue
            for x, y in ((cx, 19), (cx + 1, 19), (cx, 20), (cx + 1, 20), (cx - 2, 19), (cx + 3, 20), (cx - 1, 17), (cx + 2, 17), (cx - 1, 22), (cx + 2, 22),
                         (cx - 2, 21), (cx + 3, 18)):
                put(x, y, (10, 6, 8))
    if "rinnegan" in marks and open_eyes:  # his left eye: lavender rings with six tomoe
        cx, cy = 21.5, 19.5
        for y in range(17, 23):
            for x in range(19, 25):
                d = math.hypot(x - cx, y - cy)
                put(x, y, (120, 96, 170) if 1.2 < d < 1.9 or d > 2.7 else (196, 178, 232))
        put(21, 19, (60, 40, 90)); put(22, 20, (60, 40, 90))
        for x, y in ((19, 18), (24, 18), (19, 21), (24, 21), (21, 17), (22, 22)):
            put(x, y, (10, 6, 8))
    if "baryon_eyes" in marks:  # black pigment round the eyes, sweeping up toward the fox-ear tufts
        for x, y in ((5, 15), (6, 14), (7, 13), (8, 13), (26, 15), (25, 14), (24, 13), (23, 13), (4, 16), (27, 16)):
            put(x, y, (16, 12, 14))
    if "cheek_scar" in marks:  # Broly's scar across his left cheek
        for i in range(6):
            put(22 + i, 21 + i // 2, (150, 90, 70))
    if "glow_eyes" in marks and open_eyes:  # Wrathful: eyes burning red
        for cx in (10, 21):
            for y in range(18, 22):
                for x in range(cx - 1, cx + 3):
                    put(x, y, (230, 40, 30))
    if "blank_eyes" in marks and open_eyes:  # Legendary Super Saiyan: blank white eyes, no pupils
        for cx in (10, 21):
            for y in range(17, 22):
                for x in range(cx - 2, cx + 4):
                    put(x, y, (246, 250, 240))
    if "edo_cracks" in marks:  # Reanimation: grey sclerae, cracks running down the face
        for x, y in ((4, 14), (5, 16), (4, 18), (6, 20), (27, 15), (26, 17), (27, 19), (25, 21), (5, 24), (26, 25)):
            put(x, y, (120, 110, 110))
    if "rinnegan_both" in marks and open_eyes:  # the Rinnegan in both eyes (grey sclera round them)
        for cx in (10, 21):
            for y in range(17, 23):
                for x in range(cx - 2, cx + 4):
                    d = math.hypot(x - cx - 0.5, y - 19.5)
                    put(x, y, (120, 96, 170) if 1.2 < d < 1.9 or d > 2.7 else (196, 178, 232))
            put(cx, 19, (60, 40, 90)); put(cx + 1, 20, (60, 40, 90))
    if "third_eye" in marks:  # the Rinne Sharingan on his forehead
        for y in range(10, 14):
            for x in range(14, 18):
                put(x, y, (200, 20, 30) if (x - 15.5) ** 2 + (y - 11.5) ** 2 > 0.8 else (20, 6, 8))
    if "slit_eyes" in marks and open_eyes:  # demon eyes: cat-like vertical slits
        for cx in (10, 21):
            for y in range(17, 23):
                put(cx, y, (10, 4, 6))
                put(cx + 1, y, (10, 4, 6)) if y in (19, 20) else None
    if "fangs" in marks:
        for x in (13, 18):
            put(x, 26, (250, 250, 246)); put(x, 27, (250, 250, 246))
    if "jaw_mark" in marks:  # flame mark climbing his right jaw
        for x, y in ((4, 29), (5, 28), (5, 27), (6, 26), (7, 25), (6, 27), (7, 26), (8, 24), (4, 28), (6, 28)):
            put(x, y, (170, 30, 34))
    if "temple_mark" in marks:  # the third flame, from the right side of his head down to the brow
        for x, y in ((4, 9), (5, 10), (6, 11), (6, 12), (7, 13), (8, 14), (5, 11), (7, 12)):
            put(x, y, (170, 30, 34))
    if "brow_scales" in marks:  # Muzan's final form: dark red scales over the forehead
        for y in range(9, 14):
            for x in range(6, 26):
                if (x + y) % 3:
                    put(x, y, (110, 14, 24) if (x * y) % 4 else (150, 24, 34))
    if "face_veins" in marks:
        for y in range(15, 30):
            put(3 + (y % 3 == 0), y, (150, 20, 30)); put(28 - (y % 3 == 0), y, (150, 20, 30))
    if "hollow_mask" in marks:  # the white Hollow mask with the red stripes on the left
        for y in range(10, 32):
            for x in range(0, 32):
                if not (8 <= x <= 12 and 17 <= y <= 20) and not (19 <= x <= 23 and 17 <= y <= 20):
                    put(x, y, (238, 236, 228) if (x + y) % 11 else (220, 218, 210))
        for x in range(1, 9):
            put(x, 12 + x // 2, (190, 20, 24)); put(x, 13 + x // 2, (190, 20, 24))
        for y in range(22, 31):
            put(3, y, (190, 20, 24)); put(4, y, (190, 20, 24))
        for x in range(10, 22):  # teeth
            put(x, 27, (40, 30, 30))
            if x % 2:
                put(x, 26, (40, 30, 30)); put(x, 28, (40, 30, 30))
        for x, y in ((9, 18), (10, 18), (11, 18), (20, 18), (21, 18), (22, 18), (9, 19), (22, 19)):
            put(x, y, (10, 6, 8))
        for x, y in ((10, 19), (11, 19), (20, 19), (21, 19)):
            put(x, y, (250, 200, 40))
    if "vasto_mask" in marks:  # Vasto Lorde: all-white mask, black stripes over the brow and down from the eyes, bared teeth
        B = (14, 12, 16)
        for y in range(0, 16):
            for x in (15, 16):
                put(x, y, B)
        for y in range(4, 12):
            put(13 - (y - 4) // 3, y, B); put(18 + (y - 4) // 3, y, B)
        for cx in (10, 21):
            for y in range(16, 22):
                for x in range(cx - 3, cx + 3):
                    put(x, y, B)
            put(cx - 1, 18, (250, 200, 40)); put(cx, 18, (250, 200, 40)); put(cx - 1, 19, (250, 200, 40)); put(cx, 19, (250, 200, 40))
            for y in range(22, 31):
                put(cx - 2 + (1 if cx > 16 else -1) * ((y - 22) // 4), y, B)
        for x in range(9, 23):
            put(x, 26, B if x % 2 else (250, 250, 244)); put(x, 27, (40, 30, 30)); put(x, 28, B if x % 2 == 0 else (250, 250, 244))
    if "tanjiro_scar" in marks or "tanjiro_mark" in marks:  # the flame scar on the left forehead
        big = "tanjiro_mark" in marks
        col = (170, 40, 40) if big else (150, 70, 60)
        pts = [(20, 13), (21, 12), (22, 12), (23, 13), (21, 14), (22, 14), (23, 14), (24, 13)]
        if big:
            pts += [(19, 11), (20, 11), (24, 12), (25, 12), (22, 11), (21, 10), (25, 14), (20, 14)]
        for x, y in pts:
            put(x, y, col)


M.face32 = face32


def headband(m, cloth, tails=False):
    m.box("head", [-4.3, 28.6, -4.3], [8.6, 1.8, 8.6], solid(cloth))
    m.box("head", [-2.4, 28.4, -4.6], [4.8, 2.2, 0.35], layered((196, 202, 212), [leaf_plate]))
    if tails:
        for s in (1, -1):
            m.strand([s * 0.8, 29.4, 4.2], [s * 0.3, -1, 0.9], 6, 1.2, solid(cloth), bone="hair", segs=3, thick=0.3)


def naruto_hair(m, col, style):
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.6 if style != "adult" else 30.0, sideburn=False, teeth=0.6)
    L = 0.65 if style == "adult" else 1.0
    crown = [(0, -2.2, 0.0, 5.6), (2.2, -1.4, 0.45, 5.0), (-2.2, -1.4, -0.45, 5.0), (3.1, 0.8, 0.9, 4.6),
             (-3.1, 0.8, -0.9, 4.6), (1.5, 2.6, 0.3, 4.4), (-1.5, 2.6, -0.3, 4.4), (0, 0.6, 0, 5.0)]
    for x, z, lean, ln in crown:
        m.strand([x, 32.0, z], [lean, 1.0, z * 0.18], ln * L, 3.0, hp, bone="hair", segs=3, thick=0.8, bend=(x * 0.03, -0.05, z * 0.04))
    for x in (-2.4, 0.0, 2.4):
        m.strand([x, 30.5, 3.9], [x * 0.18, -0.4, 1], 4.4 * L, 2.8, hp, bone="hair", segs=3, thick=0.75)
    for x, tilt in ((-2.6, -0.25), (-0.9, -0.05), (0.9, 0.08), (2.6, 0.25)):
        if style == "adult":
            m.strand([x, 31.6, -4.0], [tilt, -0.5, -0.6], 2.4, 2.0, hp, bone="hair", segs=2, thick=0.7)
        else:
            m.strand([x, 31.0, -4.1], [tilt, 0.9, -0.55], 3.4, 2.2, hp, bone="hair", segs=3, thick=0.7)
    side = {"kid": 2.8, "teen": 4.8, "war": 4.8, "adult": 2.2}[style]
    for s in (1, -1):
        m.strand([s * 4.0, 29.8, -3.2], [s * 0.1, -1, -0.12], side, 1.8, hp, bone="hair", segs=3, thick=0.6)


def gold_body(m, key, iris, hair_style="war", band=True, coat=False, orbs=False):
    """Nine-Tails Chakra Mode: golden chakra all over with black seal markings."""
    def seals(face, px, w, h, base):
        if face == "north":
            for i in range(6):
                a = math.pi * (0.15 + 0.7 * i / 5)
                _put(px, w, h, int(w / 2 + math.cos(a) * w * 0.36), int(h * 0.05 + math.sin(a) * h * 0.2), MARK)
            for y in range(int(h * 0.28), h):
                _put(px, w, h, int(w * 0.32), y, MARK); _put(px, w, h, int(w * 0.68), y, MARK)
    head = skin_swap(head_paint(GOLD, iris, True, key), GOLD)
    base_body(m, layered(GOLD, [seals, spiral(MARK, face_="north", r=0.24, cy=0.62)]),
              layered(GOLD, [region((0, 0.62, 1, 0.7), MARK), region((0, 0.88, 1, 1), MARK)]),
              layered(GOLD, [lines((("north",), [[(0.5, 0), (0.5, 1)]]), MARK), region((0, 0.86, 1, 1), MARK)]), head)
    naruto_hair(m, GOLD, hair_style)
    for s in (1, -1):  # the two horn-like tufts of the chakra mode
        m.strand([s * 1.9, 32.2, -0.6], [s * 0.25, 1, 0.05], 4.6, 2.4, M.hair_paint(GOLD), bone="hair", segs=3, thick=0.75)
    if band:
        headband(m, (60, 40, 20), tails=True)
    if coat:  # Kurama Mode / Six Paths: the flared coat with the black flame hem
        g2 = light(GOLD, 0.15)
        hem = region((0, 0.82, 1, 1), MARK)
        m.box("body", [-4.6, 6.0, 2.1], [9.2, 18.2, 0.5], layered(g2, [hem]))
        for x0 in (-4.6, 1.7):
            m.box("body", [x0, 6.0, -2.6], [2.9, 18.2, 0.5], layered(g2, [hem]))
        m.box("body", [-4.4, 22.5, -2.5], [8.8, 1.8, 5.0], layered(g2, [lambda f, px, w, h, b: [_put(px, w, h, x, h // 2, MARK) for x in range(1, w - 1, 3)] if f == "north" else None]))
    if orbs:  # the Truth-Seeking Balls hovering behind his back
        for i in range(9):
            a = math.pi * (0.1 + 0.8 * i / 8)
            m.box("body", [math.cos(a) * 6.2 - 0.9, 20 + math.sin(a) * 6 - 0.9, 3.6], [1.8, 1.8, 1.8], solid((18, 16, 22)))


def v1_shroud(m, tails, kid=False):
    """Version 1: a translucent red shroud of the Nine-Tails' chakra over his whole body (he stays visible inside),
    boiling with bubbles, with chakra fox ears, claws and 1-3 tails. Lives on the blended "shroud" bones."""
    C1 = SC.swatch((236, 72, 30), 118)
    C2 = SC.swatch((255, 132, 60), 150)
    EDGE = SC.swatch((200, 34, 18), 140)
    m.box("shroudHead", [-4.7, 23.6, -4.7], [9.4, 9.0, 9.4], SC.swatch((236, 72, 30), 92))
    m.box("shroud", [-4.7, 11.6, -2.7], [9.4, 12.8, 5.4], C1)
    for bone, x0 in (("shroudRightArm", 3.5), ("shroudLeftArm", -8.5)):
        m.box(bone, [x0, 11.0, -2.5], [5.0, 13.2, 5.0], C1)
        cx = x0 + 2.5
        for k in (-1, 0, 1):  # chakra claws
            SC.blade(m, bone, [cx + k * 1.2, 11.2, -2.2], [0, -0.6, -1], 1.8, 0.6, 0.45, EDGE)
    for bone, x0 in (("shroudRightLeg", -0.5), ("shroudLeftLeg", -4.5)):
        m.box(bone, [x0, -0.3, -2.7], [5.0, 12.6, 5.4], C1)
    for s_ in (1, -1):  # fox ears of chakra
        SC.curve_tube(m, "shroudHead", [[s_ * 2.6, 32.4, -0.6], [s_ * 3.2, 35.2, -0.3], [s_ * 3.5, 37.6, 0.3]], 1.6, 0.3, C1, n=2, flat=0.45, width=[1, 0, 0])
    for i in range(30):  # bubbles boiling along the shroud
        a = i * 2.39996
        bone, cx, cy, h, rx, rz = [("shroud", 0, 18, 12, 4.8, 2.8), ("shroudHead", 0, 28, 8, 4.8, 4.8), ("shroudRightArm", 6, 17.5, 12, 2.6, 2.6),
                                   ("shroudLeftArm", -6, 17.5, 12, 2.6, 2.6), ("shroudRightLeg", 2, 6, 12, 2.6, 2.8), ("shroudLeftLeg", -2, 6, 12, 2.6, 2.8)][i % 6]
        y = cy + ((i * 7) % 11 - 5) / 10 * h
        r = 0.8 + (i % 3) * 0.35
        SC.obox(m, bone, [cx + math.cos(a) * rx, y, math.sin(a) * rz], [r, r, r], C2, (0, 1, 0), 45 * (i % 2))
    n = tails
    for k in range(n):  # tails of chakra swaying up behind him
        a = math.radians(0 if n == 1 else -40 + 80 * k / (n - 1))
        L = 0.85 if kid else 1.0
        SC.curve_tube(m, "shroud", [[math.sin(a) * 1.0, 12.8, 2.8], [math.sin(a) * 3 * L, 14, 6.5 * L], [math.sin(a) * 5 * L, 18.5 * L + 2, 9 * L],
                                    [math.sin(a) * 6 * L, 23 * L + 2, 8 * L], [math.sin(a) * 5.5 * L, 26 * L + 2, 5 * L]], 2.0, 0.7, [C1, C2], n=2)


def fox_jaw(m, R, D, W, glow, head_y=28.2, snout_z=-3.6):
    """The V2 snout as an upper jaw with jagged white teeth, and a lower jaw on the "jaw" bone (it drops open on a
    roar), white light glowing inside the mouth."""
    SC.blob(m, "head", [0, 26.9, snout_z], [2.3, 1.3, 1.9], R, slices=3, axis="z")                     # upper jaw / snout
    SC.obox(m, "head", [0, 27.2, snout_z - 1.95], [1.2, 0.9, 0.6], D)                                   # nose
    for k in range(-3, 4):  # upper teeth along the snout's edge
        SC.blade(m, "head", [k * 0.55, 25.9, snout_z - 1.0 + abs(k) * 0.35], [0, -1, 0], 0.7, 0.45, 0.35, W)
    SC.obox(m, "head", [0, 25.7, snout_z + 0.2], [3.2, 0.3, 2.8], glow)                                  # light inside the mouth
    SC.obox(m, "head", [0, 25.6, snout_z + 1.0], [3.0, 1.4, 0.3], glow)                                  # ...glowing at the back of it
    SC.blob(m, "jaw", [0, 25.1, snout_z + 0.4], [2.1, 0.75, 1.7], D, slices=2, axis="z")                # lower jaw
    for k in range(-3, 4):  # lower teeth
        SC.blade(m, "jaw", [k * 0.55, 25.6, snout_z - 0.7 + abs(k) * 0.35], [0, 1, 0], 0.6, 0.45, 0.35, W)


def v2_fox(m, eight):
    """Version 2: Naruto's whole body sealed inside a shroud of dark-red chakra shaped like a small fox — round head,
    ears, white ringed eyes and a jagged white mouth, clawed hands and feet, bubbles boiling off it, four tails.
    At eight tails the shroud turns red-orange and the fox's bones grow over him."""
    red, deep, bub = ((112, 12, 16), (72, 6, 10), (186, 34, 26)) if not eight else ((190, 50, 26), (130, 24, 14), (240, 110, 50))
    R, D, B = SC.swatch(red), SC.swatch(deep), SC.swatch(bub)
    W, BONE = SC.swatch((250, 246, 236)), SC.swatch((236, 226, 208))
    # head
    SC.blob(m, "head", [0, 28.2, 0.1], [4.3, 4.0, 4.2], R, slices=6)
    fox_jaw(m, R, D, W, SC.swatch((255, 250, 230)))
    for s_ in (1, -1):
        SC.curve_tube(m, "head", [[s_ * 2.3, 31.2, -0.2], [s_ * 3.0, 34.0, 0.2], [s_ * 3.3, 36.4, 0.9]], 1.5, 0.25, R, n=2, flat=0.45, width=[1, 0, 0])
        SC.obox(m, "head", [s_ * 1.75, 29.1, -4.5], [2.2, 1.4, 0.8], W)                                # white, pupil-less eyes
        SC.obox(m, "head", [s_ * 3.0, 29.6, -4.15], [1.0, 0.6, 0.8], W)                               # slanting outer corners
    # body
    SC.blob(m, "body", [0, 18.6, 0.3], [4.3, 6.0, 2.9], R, slices=6)
    SC.blob(m, "body", [0, 22.0, 0.1], [5.0, 2.3, 2.8], R, slices=3)
    SC.tube(m, "body", [[0, 23.4, 0], [0, 25.0, -0.3]], [1.9, 1.7], R)
    for s_, arm in ((1, "rightArm"), (-1, "leftArm")):
        SC.blob(m, arm, [s_ * 5.4, 21.4, 0], [2.0, 2.0, 2.0], R, slices=3)
        SC.tube(m, arm, [[s_ * 5.7, 21.2, 0], [s_ * 6.0, 17.0, -0.2], [s_ * 6.0, 12.9, -0.6]], [1.8, 1.55, 1.3], [R, D])
        SC.blob(m, arm, [s_ * 6.0, 11.7, -0.8], [1.5, 1.3, 1.6], R, slices=3)
        for k in (-1, 0, 1):
            SC.blade(m, arm, [s_ * 6.0 + k * 0.75, 10.9, -1.9], [0, -0.55, -1], 1.5, 0.45, 0.35, D)
    for s_, leg in ((1, "rightLeg"), (-1, "leftLeg")):
        SC.tube(m, leg, [[s_ * 2.0, 12.2, 0], [s_ * 2.1, 6.6, -0.3], [s_ * 2.1, 1.7, 0.2]], [2.0, 1.7, 1.4], [R, D])
        SC.blob(m, leg, [s_ * 2.1, 0.85, -1.0], [1.5, 0.85, 2.3], R, slices=2)
        for k in (-1, 0, 1):
            SC.blade(m, leg, [s_ * 2.1 + k * 0.7, 0.6, -3.2], [0, -0.3, -1], 1.2, 0.45, 0.35, D)
    for i in range(16):  # chakra boiling off the surface
        a = i * 2.39996
        y = 14 + (i * 5 % 12)
        SC.obox(m, "body", [math.cos(a) * 4.1, y, 0.3 + math.sin(a) * 2.8], [1.1, 1.1, 1.1], B, (0, 1, 0), 45)
    n = 8 if eight else 4
    L = 1.25 if eight else 1.0
    for k in range(n):  # the tails, fanned out behind him and curling up
        a = math.radians(-60 + 120 * k / (n - 1))
        SC.curve_tube(m, "body", [[math.sin(a) * 1.2, 12.6, 2.6], [math.sin(a) * 4 * L, 14, 6.5 * L], [math.sin(a) * 7 * L, 19 * L, 9 * L],
                                  [math.sin(a) * 8.5 * L, 24 * L, 8 * L], [math.sin(a) * 8 * L, 27 * L, 4.5 * L]], 1.8, 0.6, [R, D], n=2)
    if eight:  # the Nine-Tails' skeleton forming over him: skull plate, ribs, spine
        SC.blob(m, "head", [0, 30.8, 0.4], [4.5, 1.6, 4.4], BONE, slices=2)
        for s_ in (1, -1):
            SC.tube(m, "head", [[s_ * 3.9, 30.2, -2.5], [s_ * 4.1, 26.5, -2.9]], [0.45, 0.35], BONE, knuckles=False)
            for i in range(3):
                y = 21 - i * 2.2
                SC.curve_tube(m, "body", [[s_ * 0.6, y, -3.1], [s_ * 3.4, y - 0.3, -2.6], [s_ * 4.6, y - 0.6, 0.2]], 0.45, 0.35, BONE, n=2, knuckles=False)
        for i in range(6):
            SC.obox(m, "body", [0, 13 + i * 1.9, 3.4], [1.1, 1.1, 1.1], BONE, (0, 1, 0), 45)


def naruto(m, char, form):
    kid = char == "naruto_kid"
    if char == "naruto_war" or (char == "naruto_adult" and form == "link"):
        adult = char == "naruto_adult"
        key = "naruto_spsm" if form == "spsm" else "naruto_sk" if form == "sagekurama" else "naruto_kcm"
        gold_body(m, key, (255, 140, 20) if form != "spsm" else (250, 180, 50), hair_style="adult" if adult else "war",
                  band=not adult, coat=form in ("kurama", "sagekurama", "spsm", "link"), orbs=form == "spsm")
        if form == "sagekurama":  # Sage + Kurama: the Sage's red-and-black flame cloak flaps over the chakra coat
            m.box("body", [-4.9, 9.0, 2.7], [9.8, 15.0, 0.5], layered((200, 42, 40), [region((0, 0.78, 1, 1), BLACK)]))
        return
    if kid:
        key = "naruto_fox" if form == "cloak" else "naruto_kid"
        iris = (210, 30, 30) if form == "cloak" else (46, 120, 230)
        torso = layered(ORANGE, [region((0, 0, 1, 0.28), NAVY), zipper((230, 230, 230)), spiral(N_RED)])
        base_body(m, torso, arm_paint(ORANGE, cuff=WHITE, top=(NAVY, 0.22)), leg_paint(ORANGE, NAVY, band=(WHITE, 0.74, 0.8)),
                  head_paint(N_HAIR, iris, True, key))
        m.box("body", [-3.4, 22.6, -2.5], [6.8, 1.8, 5.0], solid(WHITE))                                     # white collar
        naruto_hair(m, N_HAIR, "kid")
        headband(m, NAVY)
        if form == "cloak":  # Version 1: the translucent red shroud of the Nine-Tails' chakra, one tail
            v1_shroud(m, 1, kid=True)
        return
    if char == "naruto_teen" and form in ("v2", "eight"):  # Version 2 (four tails) / Eight-Tails: a fox of boiling chakra
        v2_fox(m, form == "eight")
        return
    if char == "naruto_teen":
        sage = form == "sage"
        v1 = form == "v1"
        key = "naruto_sage" if sage else "naruto_fox" if v1 else "naruto"
        iris = (246, 206, 46) if sage else (210, 30, 30) if v1 else (46, 120, 230)
        torso = layered(ORANGE, [region((0, 0, 1, 0.45), BLACK), zipper((200, 200, 206)), spiral(N_RED, cy=0.7)])
        base_body(m, torso, arm_paint(ORANGE, top=(BLACK, 0.3)), leg_paint(ORANGE, BLACK, band=(WHITE, 0.78, 0.84)),
                  head_paint(N_HAIR, iris, True, key))
        m.box("body", [-2.2, 22.8, -2.4], [4.4, 2.0, 4.8], layered(BLACK, [zipper((200, 200, 206))]))      # high collar
        naruto_hair(m, N_HAIR, "teen")
        headband(m, BLACK, tails=True)
        if v1:  # Version 1, three tails
            v1_shroud(m, 3)
        if sage:  # the red Sage cloak with black flames, and the big scroll on his back
            red = (200, 42, 40)
            hem = region((0, 0.8, 1, 1), BLACK)
            m.box("body", [-4.6, 7.0, 2.1], [9.2, 17.2, 0.5], layered(red, [hem]))
            for x0 in (-4.6, 1.8):
                m.box("body", [x0, 7.0, -2.6], [2.8, 17.2, 0.5], layered(red, [hem]))
            both_arms(m, [3.6, 18.6, -2.6], [4.8, 5.6, 5.2], layered(red, [region((0, 0.75, 1, 1), BLACK)]))
            m.box("body", [-5.0, 13.6, 2.6], [10.0, 2.4, 2.4], layered(WHITE, [region((0, 0, 0.12, 1), (170, 40, 40)), region((0.88, 0, 1, 1), (170, 40, 40))]))
        return
    # adult: the Seventh Hokage
    baryon = form == "baryon"
    key = "naruto_adult_sage" if form == "sage" else "naruto_adult"
    iris = (255, 90, 40) if baryon else (246, 206, 46) if form == "sage" else (46, 120, 230)
    torso = layered(ORANGE, [zipper((40, 40, 46)), region((0, 0.82, 1, 0.88), BLACK), region((0, 0.92, 1, 0.98), BLACK)])
    base_body(m, torso, arm_paint(ORANGE, cuff=BLACK), leg_paint(BLACK, (28, 28, 34), band=((70, 70, 80), 0.6, 0.7)),
              head_paint(N_HAIR, iris, True, key if not baryon else "naruto_baryon"))
    m.box("body", [-2.2, 22.9, -2.3], [4.4, 1.6, 4.6], solid(BLACK))
    naruto_hair(m, N_HAIR, "adult")
    if not baryon:  # the white Hokage cloak with its red lining and the kanji down the back
        def kanji(face, px, w, h, base):
            if face == "south":
                for i in range(5):
                    y0 = int(h * (0.12 + i * 0.15))
                    for x in range(w // 2 - 3, w // 2 + 4):
                        _put(px, w, h, x, y0, (196, 30, 30))
                    for y in range(y0, y0 + int(h * 0.09)):
                        _put(px, w, h, w // 2 + (2 if i % 2 else -2), y, (196, 30, 30))
            if face == "north":
                for y in range(h):
                    for x in range(w):
                        _put(px, w, h, x, y, (176, 30, 34))
        m.box("body", [-4.8, 3.0, 2.2], [9.6, 21.2, 0.5], layered(WHITE, [kanji]))
        m.box("body", [-5.0, 22.4, -2.6], [10.0, 2.0, 5.2], solid(WHITE))
        for x0 in (8.0, -8.6):
            m.box("body", [x0, 5.0, -1.8], [0.6, 18.4, 4.0], solid(WHITE))
    else:  # Baryon Mode: spikier hair with fox-ear tufts, a chakra cape with a black swirl on the chest,
        # four tails flowing from the back of the cape and five more from its hem, each with a black line down the middle
        cape, ink = SC.swatch((236, 88, 34)), SC.swatch((20, 14, 14))
        hp = M.hair_paint(N_HAIR)
        for s_ in (1, -1):
            m.strand([s_ * 3.0, 31.6, -0.4], [s_ * 0.45, 1, 0.05], 6.5, 3.0, hp, bone="hair", segs=3, thick=0.8)
        for y0, r0, r1 in ((18.5, (5.6, 3.4), (4.6, 3.0)),):                 # the capelet over his shoulders
            for i in range(3):
                t = i / 3
                rx, rz = r0[0] + (r1[0] - r0[0]) * t, r0[1] + (r1[1] - r0[1]) * t
                for sp in (0, 30, 60):
                    SC.obox(m, "body", [0, y0 + i * 1.9, 0], [2 * rx * 0.95, 2.0, 2 * rz * 0.95], cape, (0, 1, 0), sp)
        def swirl(face, px, w, h, base):
            if face == "north":
                cx, cy = w / 2, h / 2
                for i in range(90):
                    a = i / 90 * math.pi * 4
                    rr = min(w, h) * 0.42 * i / 90
                    _put(px, w, h, int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr), (20, 14, 14))
        m.box("body", [-2.4, 17.6, -3.85], [4.8, 4.8, 0.5], layered((236, 88, 34), [swirl]))
        def tail(base_, ctrl):
            pts = SC.curve_tube(m, "body", [base_] + ctrl, 1.5, 0.55, cape, n=2)
            for p in pts[1:-1]:
                SC.obox(m, "body", p, [0.5, 0.5, 0.5], ink, (0, 1, 0), 45)
        for k in range(4):  # four from the back of the cape
            a = math.radians(-45 + 30 * k)
            tail([math.sin(a) * 1.5, 21, 2.8], [[math.sin(a) * 5, 23, 6], [math.sin(a) * 8, 26, 7.5], [math.sin(a) * 9, 29, 6]])
        for k in range(5):  # five from the hem
            a = math.radians(-60 + 30 * k)
            tail([math.sin(a) * 2, 12.6, 2.6], [[math.sin(a) * 5, 11, 6], [math.sin(a) * 8, 9, 8.5], [math.sin(a) * 9.5, 8, 11]])


# ------------------------------------------------------------------ Sasuke (Part I, Shippuden, War, Adult)
SAS_HAIR = (34, 36, 56)
CS2_SKIN = (138, 132, 146)
CS2_HAIR = (96, 104, 140)
PURPLE_ROPE = (120, 70, 170)
SUS = (150, 80, 222)


def uchiha_crest(cy=0.2, r=0.15, face_="south"):
    """The Uchiha fan: red top, white bottom, on the back."""
    def f(face, px, w, h, base):
        if face != face_:
            return
        cx, c_y, R = w / 2, h * cy, w * r
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - c_y)
                if d <= R:
                    _put(px, w, h, x, y, (200, 30, 36) if y < c_y else (240, 240, 236))
                if R < d <= R + 0.9 and y >= c_y - R:
                    _put(px, w, h, x, y, (30, 30, 36))
        for y in range(int(c_y + R), int(c_y + R * 1.9)):
            _put(px, w, h, int(cx), y, (240, 240, 236))
    return f


def chakra(col, density=3):
    """Susanoo chakra: a bright solid rim and a see-through diamond lattice, so it reads as energy, not a box."""
    def p(face, img):
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                rim = x in (0, w - 1) or y in (0, h - 1)
                if rim:
                    px[x, y] = light(col, 0.3) + (255,)
                elif (x + y) % density == 0 or (x - y) % density == 0:
                    px[x, y] = (col if (x // 2 + y // 2) % 2 else dark(col, 0.82)) + (255,)
                else:
                    px[x, y] = (0, 0, 0, 0)
    return p


def skull_paint(col):
    """The Susanoo skull around his head: only its outline, eye sockets, brow ridge and teeth glow."""
    def p(face, img):
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = (0, 0, 0, 0)
                if x in (0, w - 1) or y in (0, h - 1):
                    px[x, y] = light(col, 0.3) + (255,)
        if face == "north":
            for cx in (w * 0.3, w * 0.7):  # eye sockets
                for a in range(40):
                    t = a / 40 * math.pi * 2
                    _put(px, w, h, int(cx + math.cos(t) * w * 0.13), int(h * 0.42 + math.sin(t) * h * 0.1), col)
            for x in range(int(w * 0.15), int(w * 0.85)):  # brow ridge and teeth
                _put(px, w, h, x, int(h * 0.28), col)
                if x % 3:
                    _put(px, w, h, x, int(h * 0.86), light(col, 0.2))
        elif face in ("east", "west", "up"):
            for x in range(w):
                _put(px, w, h, x, h // 2, col)
    return p


def sasuke_hair(m, col, style):
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.4, sideburn=False, teeth=0.8)
    if style == "cs2":  # Cursed Seal Lv2: the hair grows long and pale
        long_hair(m, col, back_len=14, front=True)
        return
    k = {"kid": 0.85, "teen": 1.0, "war": 1.0, "adult": 0.85}[style]
    for x, y in ((-2.2, 31.5), (0, 32.0), (2.2, 31.5), (-1.2, 30.0), (1.2, 30.0), (0, 28.8), (-3.2, 29.6), (3.2, 29.6)):  # the spikes swept back
        m.strand([x, y, 2.8], [x * 0.12, 0.45, 1], 5.2 * k, 3.0, hp, bone="hair", segs=3, thick=0.75, bend=(0, 0.05, 0))
    side = {"kid": 5.4, "teen": 6.0, "war": 6.2, "adult": 7.0}[style]
    for s_ in (1, -1):  # long bangs framing the face
        m.strand([s_ * 3.4, 31.4, -4.1], [s_ * 0.15, -1, -0.1], side, 2.0, hp, bone="hair", segs=3, thick=0.6)
    if style == "adult":  # the long bang over his left eye, hiding the Rinnegan
        m.strand([-2.0, 31.8, -4.4], [-0.05, -1, -0.22], 6.8, 3.2, hp, bone="hair", segs=3, thick=0.6)
        m.strand([0.9, 31.7, -4.2], [0.2, -1, -0.3], 3.0, 1.8, hp, bone="hair", segs=2, thick=0.6)
    else:
        m.strand([0.8, 31.6, -4.1], [0.1, -1, -0.2], 3.0, 1.8, hp, bone="hair", segs=2, thick=0.6)
        m.strand([-1.2, 31.6, -4.1], [-0.1, -1, -0.2], 2.6, 1.8, hp, bone="hair", segs=2, thick=0.6)


def hand_wings(m, col=(84, 90, 116), size=1.0):
    """Cursed Seal Lv2: two great webbed hands growing from his shoulder blades — a jointed arm, five jointed fingers
    and a membrane stretched between them."""
    bone_p = SC.smooth(col)
    web = SC.alpha(SC.smooth(dark(col, 0.78)), 235)
    k = size
    for s_ in (1, -1):
        arm = SC.curve_tube(m, "body", [[s_ * 1.6, 20.5, 2.6], [s_ * 4.5 * k, 22.5 * k ** 0.2 + 1, 5 * k], [s_ * 7.5 * k, 25, 6.5 * k]], 1.2 * k, 0.9 * k, bone_p, n=2)
        root = arm[-1]
        tips = []
        for i, ang in enumerate((15, 40, 65, 90, 115)):
            r = math.radians(ang)
            L = (10.5 - abs(i - 2) * 1.1) * k
            d = [s_ * math.cos(r), math.sin(r), 0.25]
            mid = SC.add(root, SC.mul(d, L * 0.5))
            tip = SC.add(SC.add(root, SC.mul(d, L)), [0, -0.8 * k, 0.6])
            SC.tube(m, "body", [root, mid, tip], [0.6 * k, 0.5 * k, 0.3 * k], bone_p)
            tips.append((mid, tip))
        for (m1, t1), (m2, t2) in zip(tips, tips[1:]):  # webbing: thin panels between neighbouring fingers
            for u in (0.3, 0.55, 0.8):
                p1 = SC.add(root, SC.mul(SC.sub(t1, root), u))
                p2 = SC.add(root, SC.mul(SC.sub(t2, root), u))
                SC.tube(m, "body", [p1, p2], [1.5 * k * u + 0.4, 1.5 * k * u + 0.4], web, knuckles=False, flat=0.18)

def susanoo(m, stage):
    """stage 1: ribcage + skull + skeletal arms (Mangekyo); 2: armoured (Eternal); 3: perfect, with wings."""
    pur = SUS if stage < 3 else (170, 110, 240)
    ch = chakra(pur)
    for i in range(4):  # ribs
        y = 13.6 + i * 2.6
        m.box("body", [-6.4, y, -3.9], [12.8, 0.9, 0.7], ch)
        m.box("body", [-6.4, y, -3.9], [0.7, 0.9, 7.8], ch)
        m.box("body", [5.7, y, -3.9], [0.7, 0.9, 7.8], ch)
    m.box("body", [-0.5, 12.0, 3.4], [1.0, 14.5, 1.0], ch)                                                     # spine
    m.box("body", [-6.6, 23.0, -4.0], [13.2, 1.2, 8.0], ch)                                                    # shoulder girdle
    for s_ in (1, -1):  # skeletal arms reaching forward
        m.strand([s_ * 7.0, 23.0, 0.0], [s_ * 0.5, -0.5, -0.7], 10, 2.2, ch, bone="body", segs=3, thick=0.9)
        m.box("body", [s_ * 10.2 - 1.3, 14.6, -6.8], [2.6, 2.6, 2.6], ch)
    if stage >= 2:  # armour: breastplate, pauldrons, the long-nosed helmet with its crescent
        plate = chakra(dark(pur, 0.92), 2)
        m.box("head", [-4.7, 30.2, -4.9], [9.4, 1.4, 9.8], solid(light(pur, 0.15)))                             # helmet band
        m.box("body", [-6.6, 12.4, -4.6], [13.2, 11.0, 0.8], plate)
        for s_ in (1, -1):
            m.box("body", [s_ * 7.6 - 2.0, 21.4, -4.2], [4.0, 3.2, 8.4], plate)
            m.strand([s_ * 3.0, 31.0, -4.6], [s_ * 0.8, 1, -0.3], 5.5, 1.8, solid(light(pur, 0.15)), bone="head", segs=3, thick=0.6, bend=(-s_ * 0.2, 0, 0))  # crescent horns
    if stage >= 3:  # Perfect Susanoo: the great wings
        for s_ in (1, -1):
            for k in range(5):
                m.strand([s_ * 2.0, 22.0 - k * 1.6, 4.0], [s_ * (1.0 - k * 0.12), 0.9 - k * 0.35, 0.6], 15 - k * 1.6, 3.0, ch, bone="body", segs=3, thick=0.4)


def sasuke(m, char, form):
    kid, war, adult = char == "sasuke_kid", char == "sasuke_war", char == "sasuke_adult"
    cs2 = form == "cs2"
    skin = CS2_SKIN if cs2 else SKIN
    hair = CS2_HAIR if cs2 else SAS_HAIR
    key = {"base": "sasuke", "sharingan": "sasuke_sh", "cs1": "sasuke_cs1", "cs2": "sasuke_cs2", "susanoo": "sasuke_ms",
           "ems": "sasuke_ems", "perfect": "sasuke_ems", "rinnegan": "sasuke_rinne", "adult": "sasuke_adult", "adult_sus": "sasuke_adult_sh"}[form]
    iris = (30, 28, 36) if form in ("base", "adult") else (200, 20, 30)
    head = head_paint(hair, iris, True, key)
    if cs2:
        head = skin_swap(head, CS2_SKIN)
    if kid:  # Part I: navy high-collared short-sleeved shirt, white shorts, white arm warmers, the Leaf headband
        navy = (44, 62, 138)
        torso = layered(navy, [uchiha_crest(0.18, 0.16)] + ([lambda f, px, w, h, b: [_put(px, w, h, x, y, (20, 16, 22)) for y in range(h) for x in range(w)
                                                                                         if f == "north" and x > w * 0.6 and (x * 3 + y * 5) % 7 == 0]] if form == "cs1" else []))
        base_body(m, torso, layered(skin, [region((0, 0, 1, 0.28), navy), region((0, 0.45, 1, 0.85), WHITE)]),
                  layered(skin, [region((0, 0, 1, 0.5), (226, 226, 216)), region((0, 0.86, 1, 1), navy), region((0, 0.55, 1, 0.75), WHITE)]), head)
        m.box("body", [-4.0, 22.2, -2.6], [8.0, 3.0, 5.2], layered(navy, [uchiha_crest(0.45, 0.2)]))           # the big collar
        if not cs2:
            headband(m, navy)
    else:
        if adult:  # grey long-sleeved shirt, periwinkle vest, black trousers, purple belt
            shirt = (150, 152, 162)
            vest = (150, 156, 204)
            base_body(m, layered(vest, [zipper(dark(vest, 0.7)), region((0, 0, 1, 0.08), shirt)]), layered(shirt, [region((0, 0.82, 1, 1), (50, 50, 58))]),
                      leg_paint((36, 36, 42), (40, 40, 52), band=((40, 40, 52), 0.7, 0.86)), head)
            m.box("body", [-2.4, 22.8, -2.5], [4.8, 1.8, 5.0], solid(shirt))                                    # collar
            m.box("body", [-4.5, 11.6, -2.6], [9.0, 1.2, 5.2], solid(PURPLE_ROPE))                              # belt
            m.box("body", [3.6, 7.6, -1.0], [1.2, 4.0, 2.0], layered(NAVY, [region((0, 0, 1, 0.4), (196, 202, 212))]))  # headband at the hip
        else:  # Shippuden: white open shirt, black arm guards / War: grey zipped high-collar shirt, blue wrist warmers
            shirt = (196, 198, 206) if war else (236, 236, 240)

            def open_v(face, px, w, h, base):
                if face == "north" and not war:
                    for y in range(int(h * 0.55)):
                        half = int((h * 0.55 - y) / (h * 0.55) * w * 0.22)
                        for x in range(w // 2 - half, w // 2 + half + 1):
                            _put(px, w, h, x, y, skin)
            torso = layered(shirt, [open_v, uchiha_crest(0.12, 0.14)] + ([zipper((120, 120, 130))] if war else []))
            arm = (layered(skin, [region((0, 0, 1, 0.3), shirt), region((0, 0.7, 1, 0.9), (60, 80, 150))]) if war
                   else layered(shirt, [region((0, 0.5, 1, 0.88), (30, 30, 36)), region((0, 0.88, 1, 1), skin)]))
            base_body(m, torso, arm, leg_paint((40, 44, 80), BLACK, toe=skin), head)
            m.box("body", [-4.3, 22.0, -2.4], [8.6, 2.4, 4.8], layered(shirt, [uchiha_crest(0.5, 0.18)]))       # high collar
            m.box("body", [-4.6, 11.4, -2.7], [9.2, 2.0, 5.4], layered(PURPLE_ROPE, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), (90, 50, 130))]))  # rope belt
            for s_ in (1, -1):  # the big rope bow at the back
                m.strand([s_ * 0.6, 12.4, 2.8], [s_ * 1, 0.2, 0.3], 3.4, 2.0, solid(PURPLE_ROPE), bone="body", segs=2, thick=0.8)
            m.box("body", [-4.5, 6.5, -2.6], [9.0, 5.0, 5.2], layered((40, 44, 90), [lambda f, px, w, h, b: [px.__setitem__((x, y), (0, 0, 0, 0)) for y in range(h) for x in range(w // 3, 2 * w // 3)] if f == "north" else None]))  # cloth over the hips
        # Kusanagi, sheathed across the small of his back
        m.box("body", [-6.0, 13.8, 2.6], [12.0, 0.8, 0.8], solid((30, 30, 36) if not adult else (40, 30, 34)))
        m.box("body", [-8.6, 13.7, 2.5], [2.6, 1.0, 1.0], solid((60, 60, 70)))
    sasuke_hair(m, hair, "cs2" if cs2 else ("kid" if kid else "adult" if adult else "war" if war else "teen"))
    if cs2:
        hand_wings(m, size=1.0 if kid else 1.35)
    # the Susanoo itself is a separate giant entity (summons.py) that stays with him in these forms
    if adult:  # the black cloak with purple lining; he lost his left arm in the Valley of the End
        m.cubes = [c for c in m.cubes if c["bone"] != "leftArm"]
        cloak, lining = (30, 30, 38), (110, 70, 160)
        m.box("body", [-5.2, 3.0, 2.3], [10.4, 21.6, 0.6], layered(cloak, [region((0, 0, 1, 1), lining, faces=("north",))]))
        m.box("body", [-8.4, 3.6, -2.9], [3.6, 21.0, 5.8], layered(cloak, [region((0, 0, 1, 1), lining, faces=("east",))]))  # drapes over the missing arm
        m.box("body", [-5.3, 22.0, -3.0], [10.6, 2.6, 6.0], solid(cloak))                                     # shoulder cape
        m.box("body", [-2.6, 23.6, -2.8], [5.2, 1.6, 5.6], layered(cloak, [region((0, 0.3, 1, 0.7), (120, 30, 40))]))  # collar with its maroon cinch
        m.box("rightArm", [3.7, 11.6, -2.2], [4.6, 2.2, 4.4], solid((50, 50, 58)))                              # fingerless glove


# ------------------------------------------------------------------ Ichigo (Bleach)
ICH_HAIR = (255, 132, 40)
SHIHAK = (30, 30, 36)
MASK_W = (238, 236, 228)
FUR = (196, 44, 40)
TENSA = dict(wrap=(30, 30, 36), diamond=(120, 20, 24), tsuba="cross", metal=(40, 40, 46),
             blade=(28, 28, 34), edge=(150, 150, 170), hamon=None, saya=(30, 30, 30), saya_band=(200, 200, 200))
FULLBRING = dict(wrap=(30, 30, 36), diamond=(236, 236, 236), tsuba="cross", metal=(236, 236, 236),
                 blade=(232, 232, 236), edge=(40, 40, 46), hamon=None, saya=(30, 30, 30), saya_band=(200, 200, 200))


def ichigo_hair(m, col):
    """Messy orange spikes in every direction, bangs falling over the scowl."""
    shell(m, col, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(col)
    spikes = [([0, 32.0, -1.8], [0.0, 1, -0.35], 4.6, 3.0), ([2.4, 31.8, -2.2], [0.7, 1, -0.4], 4.8, 2.8),
              ([-2.4, 31.8, -2.2], [-0.7, 1, -0.4], 4.8, 2.8), ([3.6, 31.2, 0.2], [1, 0.8, 0.0], 5.0, 2.8),
              ([-3.6, 31.2, 0.2], [-1, 0.8, 0.0], 5.0, 2.8), ([1.6, 32.0, 1.4], [0.4, 1, 0.5], 4.6, 2.8),
              ([-1.6, 32.0, 1.4], [-0.4, 1, 0.5], 4.6, 2.8), ([0, 31.4, 3.4], [0, 0.6, 1], 4.8, 3.0),
              ([4.2, 29.6, -1.8], [1, -0.4, -0.3], 3.6, 2.2), ([-4.2, 29.6, -1.8], [-1, -0.4, -0.3], 3.6, 2.2),
              ([4.2, 29.0, 1.4], [1, -0.2, 0.5], 4.2, 2.4), ([-4.2, 29.0, 1.4], [-1, -0.2, 0.5], 4.2, 2.4),
              ([2.4, 29.4, 4.2], [0.5, -0.3, 1], 4.4, 2.6), ([-2.4, 29.4, 4.2], [-0.5, -0.3, 1], 4.4, 2.6),
              ([0, 27.6, 4.2], [0, -0.7, 1], 4.0, 2.6), ([3.6, 27.4, 3.6], [0.6, -0.8, 0.6], 3.6, 2.0),
              ([-3.6, 27.4, 3.6], [-0.6, -0.8, 0.6], 3.6, 2.0),
              # bangs, and two spikes jutting forward over them
              ([-2.9, 31.6, -4.2], [-0.35, -1, -0.45], 3.4, 2.4), ([-0.9, 31.8, -4.3], [-0.05, -1, -0.4], 3.8, 2.2),
              ([1.2, 31.8, -4.3], [0.15, -1, -0.45], 3.2, 2.2), ([3.0, 31.6, -4.2], [0.4, -1, -0.45], 3.0, 2.2),
              ([1.8, 32.2, -3.8], [0.3, 0.6, -1], 3.6, 2.4), ([-1.6, 32.2, -3.8], [-0.4, 0.5, -1], 3.4, 2.4)]
    for base, d, ln, w in spikes:
        m.strand(base, d, ln, w, hp, bone="hair", segs=3, thick=0.75)


def long_hair(m, col, back_len=15, z=4.0, front=True, bone="hair"):
    """Waist-long hair (Vasto Lorde orange, Mugetsu black)."""
    hp = M.hair_paint(col)
    for x in (-3.2, -1.6, 0, 1.6, 3.2):
        m.strand([x, 30.6, z], [x * 0.04, -1, 0.18], back_len - abs(x) * 0.6, 2.8, hp, bone=bone, segs=3, thick=0.6)
    for s in (1, -1):
        m.strand([s * 4.2, 30.4, 1.6], [s * 0.15, -1, 0.3], back_len * 0.7, 2.4, hp, bone=bone, segs=3, thick=0.6)
        if front:
            m.strand([s * 3.8, 31.2, -3.6], [s * 0.12, -1, -0.15], 7, 2.0, hp, bone=bone, segs=3, thick=0.6)


def cleaver(m, bone, cx, cy, L=17.0, W=3.8, blade=(212, 216, 228), edge=(246, 248, 255), spine=(36, 36, 42),
            core=None, grip=(236, 236, 236), chain=False, cloth=True):
    """Zangetsu's Shikai: a huge guardless cleaver, the hilt in line with its black spine, the edge below.
    With `core` it is the True Bankai blade: silver edges round a black core and a long chain."""
    m.box(bone, [cx - 0.45, cy - 0.45, -2.0], [0.9, 0.9, 4.8], M.wrap_paint(grip, dark(grip, 0.55) if grip[0] > 120 else (120, 20, 24)))
    top = cy + 0.7
    ex = [region((0, 0, 1, 0.14), spine, faces=("east", "west")), region((0, 0.84, 1, 1), edge, faces=("east", "west"))]
    if core:
        ex.append(region((0.04, 0.3, 0.92, 0.62), core, faces=("east", "west")))
    paint = layered(blade, ex)
    m.box(bone, [cx - 0.4, top - W, -2.0 - L], [0.8, W, L], paint)
    for k, f in enumerate((0.72, 0.46, 0.22)):  # the slanted cut of the tip, edge side longest
        m.box(bone, [cx - 0.38, top - W, -2.0 - L - (k + 1) * 1.0], [0.76, W * f, 1.0],
              layered(blade, [region((0, 0.7, 1, 1), edge, faces=("east", "west"))]))
    if cloth:  # the long white cloth trailing from the hilt
        m.strand([cx, cy, 2.6], [0, -0.35, 1], 8, 1.0, solid((236, 236, 236)), bone=bone, segs=3, thick=0.4)
    if chain:
        for i in range(9):
            m.box(bone, [cx - 0.3, cy - 0.3 - i * 0.7, 2.8 + i * 0.35], [0.6, 0.6, 0.6], solid((60, 60, 70) if i % 2 else (110, 110, 124)))


def tensa_chain(m, bone, x, y, z):
    for i in range(6):
        m.box(bone, [x - 0.3, y - i * 0.6, z + i * 0.18], [0.6, 0.6, 0.6], solid((60, 60, 70) if i % 2 else (110, 110, 124)))


def ichigo(m, form):
    hair = ICH_HAIR
    key = {"shikai": "ichigo", "fullbring": "ichigo", "bankai": "ichigo", "hollow": "ichigo_hollow", "vasto": "ichigo_vasto",
           "mugetsu": "ichigo_mugetsu", "true": "ichigo"}[form]
    iris = {"mugetsu": (200, 20, 30), "vasto": (250, 200, 40)}.get(form, (130, 76, 34))

    def kosode(face, px, w, h, base):
        if face == "north":  # white under-kimono showing in a V
            for y in range(int(h * 0.5)):
                half = int((h * 0.5 - y) / (h * 0.5) * w * 0.2)
                for x in range(w // 2 - half - 1, w // 2 + half + 2):
                    _put(px, w, h, x, y, WHITE if abs(x - w // 2) > half - 1 else SKIN)

    def tatters(face, px, w, h, base):  # torn hem
        if face in SIDES:
            for x in range(w):
                for y in range(h - 1 - (x * 7 % 5), h):
                    if (x // 2) % 2 == 0:
                        px[x, y] = (0, 0, 0, 0)

    hakama = layered(SHIHAK, [region((0, 0.92, 1, 1), WHITE)])
    if form in ("shikai", "bankai", "hollow"):
        base_body(m, layered(SHIHAK, [kosode]), arm_paint(SHIHAK, sleeve_to=0.86), leg_paint(SHIHAK, WHITE, toes=False),
                  head_paint(hair, iris, True, key))
        m.box("body", [-4.5, 11.6, -2.6], [9.0, 1.4, 5.2], solid(WHITE))                                       # white sash
        both_legs(m, [-0.6, 1.6, -2.6], [4.9, 10.4, 5.2], layered(SHIHAK, [tatters]))                           # wide hakama
    if form == "shikai":
        cleaver(m, "rightArm", 6.0, 12.2)
        m.box("body", [-4.0, 15.0, -2.7], [8.0, 0.8, 0.4], solid((200, 30, 30)), rot=[0, 0, -38], pivot=[0, 18, -2.7])  # the red strap
        m.box("body", [-4.0, 15.0, 2.3], [8.0, 0.8, 0.4], solid((200, 30, 30)), rot=[0, 0, 38], pivot=[0, 18, 2.3])
    elif form in ("bankai", "hollow"):  # Tensa Zangetsu and the long, torn black coat with its red lining
        M.katana2(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 15, TENSA)
        tensa_chain(m, "rightArm", 6.0, 11.7, 2.0)
        lining = (150, 20, 26)

        def edge(side):
            def f(face, px, w, h, base):
                if face == "south":
                    for y in range(h):
                        for x in range(w):
                            _put(px, w, h, x, y, lining)
                if face == "north":
                    for y in range(h):
                        _put(px, w, h, (w - 1) if side > 0 else 0, y, lining)
            return f
        m.box("body", [-4.6, 1.0, 2.2], [9.2, 23.0, 0.5], layered(SHIHAK, [tatters, lambda f, px, w, h, b: [_put(px, w, h, x, y, lining) for y in range(h) for x in range(w)] if f == "north" else None]))
        m.box("body", [-4.7, 1.0, -2.75], [2.8, 23.0, 0.5], layered(SHIHAK, [edge(1), tatters]))
        m.box("body", [1.9, 1.0, -2.75], [2.8, 23.0, 0.5], layered(SHIHAK, [edge(-1), tatters]))
        m.box("body", [-4.7, 1.0, -2.75], [0.5, 23.0, 5.45], layered(SHIHAK, [tatters]))
        m.box("body", [4.2, 1.0, -2.75], [0.5, 23.0, 5.45], layered(SHIHAK, [tatters]))
        both_arms(m, [3.5, 12.0, -2.5], [5.0, 2.4, 5.0], layered(SHIHAK, [region((0, 0.82, 1, 1), lining)]))   # flared cuffs
        m.box("leftArm", [-8.2, 11.6, -2.2], [4.4, 1.6, 4.4], solid((24, 24, 28)))                              # black glove
    elif form == "fullbring":  # Complete Fullbring: the white suit with black stripes, the skull-hilted blade
        def stripes(face, px, w, h, base):
            if face == "north":
                for y in range(h):
                    off = int(abs(y - h * 0.3) * 0.12)
                    for x in (int(w * 0.28) - off, int(w * 0.28) - off + 1, int(w * 0.72) + off, int(w * 0.72) + off - 1):
                        _put(px, w, h, x, y, BLACK)
                for x in range(w // 2 - 1, w // 2 + 1):
                    for y in range(int(h * 0.15), h):
                        _put(px, w, h, x, y, (200, 200, 204))
        base_body(m, layered(MASK_W, [stripes]), layered(MASK_W, [region((0.4, 0, 0.6, 0.9), BLACK, faces=("north", "south", "east", "west"))]),
                  layered(BLACK, [region((0, 0, 0.35, 0.8), MASK_W), region((0, 0.85, 1, 1), MASK_W)]), head_paint(hair, iris, True, key))
        m.box("body", [-4.4, 22.4, -2.6], [8.8, 2.4, 5.2], layered(MASK_W, [region((0.35, 0, 0.65, 1), BLACK, faces=("north",))]))  # high collar
        m.box("body", [-4.6, 3.0, 2.2], [9.2, 9.6, 0.5], layered(MASK_W, [region((0.45, 0, 0.55, 1), BLACK)]))  # coat tails
        both_arms(m, [3.4, 19.4, -2.6], [5.2, 4.8, 5.2], layered(MASK_W, [region((0, 0.8, 1, 1), BLACK)]))     # shoulder plates
        M.katana2(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 11, FULLBRING)
    elif form == "vasto":  # Vasto Lorde: white skin, black markings, the hole in his chest, red fur, horns, long orange hair
        def markings(face, px, w, h, base):
            if face == "north":
                for x in range(w):  # collar-bone bands
                    y = int(h * 0.12 + abs(x - w / 2) * 0.35)
                    _put(px, w, h, x, y, BLACK); _put(px, w, h, x, y + 1, BLACK)
                cx, cy, r = w / 2, h * 0.3, w * 0.13
                for y in range(h):
                    for x in range(w):
                        d = math.hypot(x - cx, y - cy)
                        if d < r:
                            px[x, y] = (0, 0, 0, 0) if d < r * 0.55 else (220, 120, 40, 255)
                for y in range(int(h * 0.5), int(h * 0.85), 3):  # abs
                    for x in range(int(w * 0.3), int(w * 0.7)):
                        _put(px, w, h, x, y, (196, 194, 188))
                for y in range(int(h * 0.45), h):
                    _put(px, w, h, w // 2, y, (196, 194, 188))
            if face == "south":
                for x in range(w):
                    _put(px, w, h, x, int(h * 0.2 + abs(x - w / 2) * 0.3), BLACK)
        arm = layered(MASK_W, [region((0, 0.12, 1, 0.2), BLACK), region((0, 0.3, 1, 0.36), BLACK)])
        base_body(m, layered(MASK_W, [markings]), arm, layered(SHIHAK, [region((0, 0.9, 1, 1), MASK_W)]),
                  skin_swap(head_paint(MASK_W, iris, False, key), MASK_W))
        both_legs(m, [-0.6, 1.6, -2.6], [4.9, 10.4, 5.2], layered(SHIHAK, [tatters]))                           # torn hakama
        m.box("body", [-4.5, 11.6, -2.6], [9.0, 1.4, 5.2], solid(WHITE))                                       # white sash and its knot
        m.box("body", [-1.0, 8.4, -3.2], [2.0, 3.6, 0.6], solid(WHITE))
        fur = layered(FUR, [lambda f, px, w, h, b: [_put(px, w, h, x, y, dark(FUR, 0.75)) for y in range(h) for x in range(w) if (x * 5 + y * 3) % 7 == 0]])
        F1, F2 = SC.swatch(FUR), SC.swatch(dark(FUR, 0.78))
        for ring, (y, rx, rz, up) in enumerate(((23.0, 4.6, 3.0, 0.9), (24.2, 4.0, 2.6, 1.3))):   # the red fur ruff round his neck
            for k in range(16):
                a = 2 * math.pi * (k + ring * 0.5) / 16
                base_ = [math.cos(a) * rx, y, math.sin(a) * rz]
                SC.blade(m, "body", base_, [math.cos(a), up, math.sin(a) * 0.8], 2.6 + (k % 3) * 0.5, 1.7, 0.7, F1 if (k + ring) % 2 else F2,
                         width_dir=[-math.sin(a), 0, math.cos(a)])
        for s_, arm in ((1, "rightArm"), (-1, "leftArm")):  # fur cuffs at the wrists
            for k in range(12):
                a = 2 * math.pi * k / 12
                base_ = [s_ * 6 + math.cos(a) * 2.2, 13.4, math.sin(a) * 2.2]
                SC.blade(m, arm, base_, [math.cos(a), -0.35, math.sin(a)], 2.4, 1.5, 0.6, F1 if k % 2 else F2, width_dir=[-math.sin(a), 0, math.cos(a)])
        for s in (1, -1):  # horns: out from the temples, curving forward
            SC.curve_tube(m, "head", [[s * 4.0, 30.4, -1.0], [s * 7.2, 32.4, -1.6], [s * 8.4, 34.2, -4.2], [s * 7.6, 35.0, -7.4]], 1.3, 0.35,
                          [SC.smooth(MASK_W), SC.smooth(MASK_W), SC.smooth(BLACK)], n=2)
        m.box("hair", [-4.3, 28.6, -4.3], [8.6, 3.6, 8.6], layered(MASK_W, [region((0.42, 0, 0.58, 1), BLACK, faces=("north", "up"))]))  # mask crown
        long_hair(m, ICH_HAIR, back_len=17, front=False)
        return
    elif form == "mugetsu":  # Final Getsuga Tensho: long black hair, black wrappings, red eyes
        hair = (22, 20, 26)
        wraps = layered((26, 24, 30), [lines((SIDES, [[(0, y / 7), (1, y / 7 + 0.12)] for y in range(7)]), (60, 56, 66))])
        base_body(m, wraps, layered((26, 24, 30), [lines((SIDES, [[(0, y / 6), (1, y / 6 + 0.1)] for y in range(6)]), (60, 56, 66))]),
                  layered(SHIHAK, [region((0, 0.92, 1, 1), (26, 24, 30))]), head_paint(hair, iris, True, key))
        both_legs(m, [-0.6, 1.6, -2.6], [4.9, 10.4, 5.2], layered(SHIHAK, [tatters]))
        for i in range(5):  # loose wrappings floating off the right arm
            m.strand([6.0, 13.0 + i * 2.0, 2.2], [0.4, -0.3, 1], 4.0, 0.9, solid((40, 36, 46)), bone="rightArm", segs=2, thick=0.4)
        shell(m, hair, hairline=30.6, sideburn=False, teeth=0.8)
        long_hair(m, hair, back_len=16)
        return
    elif form == "true":  # True Bankai: sleeveless black top, torn white hakama, the great cleaver and the short black blade
        base_body(m, layered(SHIHAK, [lambda f, px, w, h, b: [_put(px, w, h, x, y, WHITE) for y in range(int(h * 0.3)) for x in range(w // 2 - (int(h * 0.3) - y) // 2, w // 2 + (int(h * 0.3) - y) // 2 + 1)] if f == "north" else None]),
                  layered(SKIN, [region((0, 0, 1, 0.2), SHIHAK), region((0, 0.72, 1, 1), (24, 24, 28))]),
                  layered(WHITE, [lines((SIDES, [[(0.3, 0), (0.25, 0.9)], [(0.7, 0.1), (0.75, 1)]]), (40, 40, 46)), region((0, 0.9, 1, 1), (40, 40, 46))]),
                  head_paint(hair, iris, True, key))
        both_legs(m, [-0.7, 1.0, -2.7], [5.1, 11.0, 5.4], layered(WHITE, [tatters, lines((SIDES, [[(0.3, 0), (0.2, 1)], [(0.75, 0), (0.8, 1)]]), (40, 40, 46))]))
        m.box("body", [-4.5, 11.6, -2.6], [9.0, 1.4, 5.2], solid(SHIHAK))
        cleaver(m, "rightArm", 6.0, 12.2, L=19, W=4.2, blade=(196, 200, 214), edge=(244, 246, 255), spine=(196, 200, 214),
                core=(26, 26, 32), grip=(40, 30, 34), chain=True, cloth=False)
        M.katana2(m, "leftArm", (-6, 12.2, -1.2), (0, 0.1, -1), 8, TENSA)
    ichigo_hair(m, hair)


# ------------------------------------------------------------------ Tanjiro (Demon Slayer)
TAN_HAIR = (124, 36, 40)
NICHIRIN = dict(wrap=(34, 36, 56), diamond=(170, 40, 50), tsuba="round", metal=(30, 30, 34),
                blade=(36, 36, 42), edge=(120, 124, 140), hamon=None, saya=(30, 30, 34), saya_band=(200, 200, 200))
# Demon Slayer Mark: the blade glows crimson, Rengoku's flame guard
CRIMSON = dict(NICHIRIN, metal=(214, 92, 36), blade=(190, 40, 30), edge=(255, 150, 90))
UNIFORM = (86, 44, 50)


def tanjiro(m, form):
    mark = form == "mark"
    uni = UNIFORM
    buttons = lambda f, px, w, h, b: [_put(px, w, h, w // 2, y, (230, 200, 120)) for y in range(int(h * 0.1), int(h * 0.7), max(2, h // 6))] if f == "north" else None
    base_body(m, layered(uni, [buttons, region((0.47, 0, 0.53, 1), dark(uni, 0.8), faces=("north",))]),
              arm_paint(uni, sleeve_to=0.88),
              layered(uni, [region((0, 0.42, 1, 0.84), (232, 230, 222)),                                         # white kyahan leg wraps
                            lines((SIDES, [[(0, 0.5), (1, 0.52)], [(0, 0.62), (1, 0.64)], [(0, 0.74), (1, 0.76)]]), (196, 194, 186)),
                            region((0, 0.84, 1, 0.94), (236, 234, 228)), region((0, 0.94, 1, 1), (150, 40, 44))]),  # white tabi, red sandals
              head_paint(TAN_HAIR, (150, 30, 44), True, "tanjiro_mark" if mark else "tanjiro"))
    both_legs(m, [-0.7, 4.2, -2.7], [5.1, 8.0, 5.4], layered(uni, [lines((SIDES, [[(0.3, 0), (0.25, 1)], [(0.7, 0), (0.75, 1)]]), dark(uni, 0.78))]))  # baggy trousers
    m.box("body", [-4.4, 11.6, -2.5], [8.8, 1.4, 5.0], layered((240, 240, 236), [region((0.4, 0, 0.6, 1), (170, 172, 180), faces=("north",))]))  # white belt, buckle
    m.box("body", [-2.2, 22.6, -2.4], [4.4, 1.8, 4.8], solid(uni))                                                # high collar
    hao = layered((44, 168, 128), [checker((44, 168, 128), (26, 24, 28))])
    lining = solid((200, 200, 196))
    m.box("body", [-4.6, 6.5, 2.1], [9.2, 17.7, 0.5], hao)                                                        # checkered haori
    for x0 in (-4.6, 2.2):
        m.box("body", [x0, 6.5, -2.6], [2.4, 17.7, 0.5], hao)
    both_arms(m, [3.5, 13.6, -2.7], [5.0, 10.6, 5.4], hao)                                                        # wide sleeves
    both_arms(m, [3.6, 13.4, -2.6], [4.8, 0.4, 5.2], lining)
    box_c = (142, 90, 52)
    m.box("body", [-3.2, 12.6, 2.7], [6.4, 10.2, 4.4], layered(box_c, [lines((SIDES, [[(0, 0.15), (1, 0.15)], [(0, 0.5), (1, 0.5)], [(0, 0.85), (1, 0.85)]]), (40, 34, 30)),
                                                                     lines((("east", "west"), [[(0.5, 0), (0.5, 1)]]), dark(box_c, 0.75))]))  # Nezuko's box
    for x0 in (-2.9, 1.9):  # its shoulder straps
        m.box("body", [x0, 12.8, -2.75], [1.0, 11.4, 0.4], solid((214, 204, 176)))
    for s_ in (1, -1):  # hanafuda earrings
        m.box("head", [s_ * 4.0 - (0.5 if s_ > 0 else 0.1), 24.6, -0.4], [0.6, 1.6, 0.8], layered(WHITE, [region((0.2, 0.3, 0.8, 0.7), (200, 40, 30))]))
    st = CRIMSON if mark else dict(NICHIRIN, edge=(255, 150, 60), metal=(214, 92, 36)) if form == "hinokami" else NICHIRIN
    M.katana2(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 14, st)
    M.sheath(m, (-4.6, 12.4, -1.6), (0.05, -0.55, 1), 12, st)                                                     # the empty scabbard at his left hip
    shell(m, TAN_HAIR, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(TAN_HAIR)
    for x, z, lean in ((0, -2.0, 0), (2.2, -1.2, 0.5), (-2.2, -1.2, -0.5), (3.0, 1.2, 0.9), (-3.0, 1.2, -0.9), (0, 2.4, 0), (1.6, 3.0, 0.4), (-1.6, 3.0, -0.4)):
        m.strand([x, 32.0, z], [lean, 1.0, z * 0.25], 3.4, 2.8, hp, bone="hair", segs=3, thick=0.75, bend=(x * 0.05, -0.1, z * 0.05))
    for x, tilt in ((-2.6, -0.3), (-0.6, 0), (1.6, 0.2), (3.2, 0.4)):  # bangs (the forehead stays clear for the scar)
        m.strand([x, 31.8, -4.1], [tilt, -0.6, -0.5], 2.4, 2.0, hp, bone="hair", segs=3, thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 4.1, 30.0, -1.0], [s_ * 0.3, -1, 0.1], 3.2, 1.8, hp, bone="hair", segs=2, thick=0.6)
        m.strand([s_ * 2.6, 29.6, 4.2], [s_ * 0.4, -0.6, 1], 3.6, 2.4, hp, bone="hair", segs=3, thick=0.7)


# ------------------------------------------------------------------ Demon Tanjiro (manga, chapters 200-203)
def tanjiro_demon(m, form):
    sun = form == "sun"
    uni = UNIFORM
    blood = (118, 14, 22)

    def stains(face, px, w, h, base):  # his corps uniform soaked with blood
        for y in range(h):
            for x in range(w):
                if ((x * 7 + y * 5) % 23 < 3 and (x + y) % 3) or ((x // 3 + y // 4) % 9 == 0 and y > h // 3):
                    _put(px, w, h, x, y, blood)
    base_body(m, layered(uni, [stains, region((0.47, 0, 0.53, 1), dark(uni, 0.8), faces=("north",))]),
              arm_paint(uni, sleeve_to=0.88),
              layered(uni, [stains, region((0, 0.42, 1, 0.84), (214, 206, 196)), region((0, 0.94, 1, 1), (150, 40, 44))]),
              head_paint(TAN_HAIR, (214, 40, 64), True, "tanjiro_demon_sun" if sun else "tanjiro_demon"))
    both_legs(m, [-0.7, 4.2, -2.7], [5.1, 8.0, 5.4], layered(uni, [stains]))
    m.box("body", [-4.4, 11.6, -2.5], [8.8, 1.4, 5.0], layered((226, 224, 218), [stains]))
    # the left sleeve is torn away: the regrown arm is bare, veined
    m.box("leftArm", [-8.1, 11.9, -2.1], [4.2, 10.4, 4.2], layered(SKIN, [lines((SIDES, [[(0.3, 0), (0.4, 1)], [(0.7, 0.2), (0.6, 1)]]), (150, 40, 60))]))
    m.box("leftArm", [-8.3, 21.6, -2.3], [4.6, 1.6, 4.6], layered(uni, [lambda f, px, w, h, b: [px.__setitem__((x, h - 1), (0, 0, 0, 0)) for x in range(0, w, 2)] if f in SIDES else None]))
    claw = SC.swatch((44, 26, 40))
    for arm, s_ in (("rightArm", 1), ("leftArm", -1)):  # claws curving forward from the fingertips
        for k in range(4):
            x = s_ * (4.6 + k * 0.95)
            SC.tube(m, arm, [[x, 12.1, -1.6], [x, 11.2, -2.3], [x, 10.9, -3.0]], [0.32, 0.26, 0.12], claw, knuckles=False)
    for s_ in (1, -1):
        m.box("head", [s_ * 4.0 - (0.5 if s_ > 0 else 0.1), 24.6, -0.4], [0.6, 1.6, 0.8], layered(WHITE, [region((0.2, 0.3, 0.8, 0.7), (200, 40, 30))]))
    shell(m, TAN_HAIR, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(TAN_HAIR)
    for x, z, lean in ((0, -2.0, 0), (2.2, -1.2, 0.6), (-2.2, -1.2, -0.6), (3.0, 1.2, 1.0), (-3.0, 1.2, -1.0), (0, 2.4, 0), (1.6, 3.0, 0.5), (-1.6, 3.0, -0.5)):
        m.strand([x, 32.0, z], [lean, 1.0, z * 0.3], 4.2, 2.8, hp, bone="hair", segs=3, thick=0.75, bend=(x * 0.06, -0.1, z * 0.06))
    for x, tilt in ((-2.6, -0.3), (-0.6, 0), (1.6, 0.2), (3.2, 0.4)):
        m.strand([x, 31.8, -4.1], [tilt, -0.6, -0.5], 2.6, 2.0, hp, bone="hair", segs=3, thick=0.7)
    if sun:  # the Demon King's blood: flesh tendrils with bone tips burst from his back
        flesh_p = SC.smooth((150, 24, 34), [SC.speckle((96, 10, 20), 7)])
        tip = SC.smooth((236, 226, 210))
        for k, (dx, up) in enumerate(((5, 7), (-5, 7), (8, 2), (-8, 2))):
            pts = SC.curve_tube(m, "body", [[dx * 0.2, 19 - k % 2, 2.6], [dx * 0.7, 21 + up * 0.5, 6], [dx * 1.2, 22 + up, 8], [dx * 1.5, 20 + up * 1.4, 5]], 1.1, 0.5, flesh_p, n=2)
            SC.blade(m, "body", pts[-1], SC.sub(pts[-1], pts[-2]), 2.6, 1.2, 0.6, tip)


# ------------------------------------------------------------------ Muzan Kibutsuji
MUZAN_SKIN = (238, 228, 224)


def muzan_hair(m, col, long_=False):
    hp = M.hair_paint(col)
    shell(m, col, hairline=30.8, sideburn=False, teeth=0.8)
    if long_:  # final form: the hair grows long and white
        long_hair(m, col, back_len=17, front=True)
        return
    for x, z in ((-3.6, -1.4), (3.6, -1.4), (-3.8, 1.6), (3.8, 1.6), (-2.2, 3.8), (0, 4.2), (2.2, 3.8)):  # short, wavy curls
        m.strand([x, 30.5, z], [x * 0.08, -1, z * 0.08], 3.4, 2.4, hp, bone="hair", segs=3, thick=0.7, bend=(0.12 if x > 0 else -0.12, 0, 0.1))
    for s_ in (1, -1):  # the bangs, parted in the middle, curling at each side of his face
        m.strand([s_ * 1.2, 32.0, -4.2], [s_ * 0.5, -1, -0.35], 4.2, 2.4, hp, bone="hair", segs=3, thick=0.7, bend=(s_ * 0.18, 0, 0.05))
        m.strand([s_ * 3.4, 31.4, -4.1], [s_ * 0.2, -1, -0.15], 4.6, 2.0, hp, bone="hair", segs=3, thick=0.6, bend=(-s_ * 0.12, 0, 0))


def muzan(m, form):
    final = form == "final"
    if not final:  # Asakusa disguise: white fedora, embroidered black tuxedo, white tie over a black shirt, white trousers
        tux = (30, 28, 34)

        def suit(face, px, w, h, base):
            for y in range(h):
                for x in range(w):
                    if (x + 2 * y) % 7 == 0:
                        _put(px, w, h, x, y, (52, 48, 58))     # embroidery
            if face == "north":
                for y in range(int(h * 0.62)):
                    for x in range(w // 2 - 2, w // 2 + 2):
                        _put(px, w, h, x, y, (16, 14, 18))      # black shirt
                    _put(px, w, h, w // 2, y, WHITE); _put(px, w, h, w // 2 - 1, y, WHITE)   # white tie
                for y in (int(h * 0.68), int(h * 0.82)):
                    _put(px, w, h, w // 2 - 3, y, (120, 72, 40))  # brown buttons
        hands = layered(MUZAN_SKIN, [region((0, 0.92, 1, 1), (120, 160, 210))])   # blue nails
        base_body(m, layered(tux, [suit]), layered(tux, [region((0, 0.86, 1, 1), MUZAN_SKIN), region((0, 0.82, 1, 0.86), WHITE)]),
                  layered((232, 230, 224), [region((0, 0.9, 1, 1), (24, 22, 26))]),
                  skin_swap(head_paint((20, 18, 24), (214, 24, 34), True, "muzan"), MUZAN_SKIN))
        m.box("body", [-4.5, 6.0, 2.2], [9.0, 18.2, 0.5], layered(tux, [suit]))                        # tailcoat
        m.box("body", [-2.4, 22.6, -2.4], [4.8, 1.8, 4.8], solid(WHITE))                                # collar
        muzan_hair(m, (20, 18, 24))
        m.box("hat", [-5.6, 31.4, -5.6], [11.2, 0.6, 11.2], solid((236, 234, 228)))                   # fedora brim
        m.box("hat", [-4.3, 31.8, -4.3], [8.6, 3.4, 8.6], layered((236, 234, 228), [region((0, 0.68, 1, 1), (104, 42, 30))]))  # crown, ribbon
        return
    # Final form (manga): long white hair, mouths all over his limbs, a dark red scaled mass over the lower body,
    # bone-bladed whips from his arms, nine red spine-whips from his back
    scale_c = (112, 14, 24)

    def mouths(face, px, w, h, base):
        if face in ("up", "down"):
            return
        for k in range(2):
            y0 = int(h * (0.25 + 0.4 * k))
            for x in range(1, w - 1):
                _put(px, w, h, x, y0, (50, 4, 10)); _put(px, w, h, x, y0 + 1, (90, 10, 20))
                if x % 2:
                    _put(px, w, h, x, y0 - 1, (246, 242, 230)); _put(px, w, h, x, y0 + 2, (246, 242, 230))

    def scales(face, px, w, h, base):
        for y in range(h):
            for x in range(w):
                if (x + (y // 2) % 2) % 2 == 0:
                    _put(px, w, h, x, y, (150, 26, 36))
    torso = layered(MUZAN_SKIN, [lines((("north",), [[(0.5, 0.1), (0.5, 0.9)], [(0.2, 0.3), (0.8, 0.3)]]), (196, 170, 170)), region((0, 0.8, 1, 1), scale_c)])
    base_body(m, torso, layered(MUZAN_SKIN, [mouths, region((0, 0.92, 1, 1), (120, 160, 210))]), layered(scale_c, [scales]),
              skin_swap(head_paint((236, 236, 240), (214, 24, 34), True, "muzan_final"), MUZAN_SKIN))
    both_legs(m, [-0.6, 0.0, -2.6], [4.9, 12.2, 5.2], layered(scale_c, [scales, mouths]))
    muzan_hair(m, (236, 236, 240), long_=True)
    pink, bone_c, red = SC.smooth((232, 128, 150), [SC.speckle((190, 80, 104), 7)]), SC.smooth((238, 232, 220)), SC.smooth((170, 22, 34), [SC.speckle((110, 10, 20), 7)])
    for s_, arm in ((1, "rightArm"), (-1, "leftArm")):  # the arms become long spiked flesh whips
        pts = SC.curve_tube(m, arm, [[s_ * 6, 12, -0.5], [s_ * 7.5, 7, -3], [s_ * 9, 2, -1], [s_ * 11, 0.6, 4], [s_ * 13, 1.2, 9]], 1.3, 0.6, pink, n=2)
        for i in range(1, len(pts) - 1):  # bone spikes standing out of the whip, alternating sides
            T = SC.norm(SC.sub(pts[i + 1], pts[i - 1]))
            out = SC.norm(SC.vcross(T, [0, 1, 0]) if abs(T[1]) < 0.9 else SC.vcross(T, [1, 0, 0]))
            out = SC.mul(out, 1 if i % 2 else -1)
            SC.blade(m, arm, pts[i], SC.add(out, SC.mul(T, 0.5)), 1.6, 0.8, 0.45, bone_c, width_dir=T)
        SC.blade(m, arm, pts[-1], SC.sub(pts[-1], pts[-2]), 3.2, 1.4, 0.6, bone_c)
    for s_, leg in ((1, "rightLeg"), (-1, "leftLeg")):  # whips sprouting from his thighs
        for k in range(2):
            pts = SC.curve_tube(m, leg, [[s_ * 3.6, 9 - k * 2, 0.5], [s_ * (6 + k), 6 - k, 3], [s_ * (8 + k * 2), 1.2, 6 + k * 2], [s_ * (9 + k * 2), 0.6, 11 + k]],
                                0.7, 0.35, red, n=2)
            SC.blade(m, leg, pts[-1], SC.sub(pts[-1], pts[-2]), 1.8, 0.9, 0.45, bone_c)
    for k in range(9):  # nine spine-like red whips from his back, tipped with bone blades
        a = math.radians(-80 + 160 * k / 8)
        ctrl = [[math.sin(a) * 1.5, 19, 2.6], [math.sin(a) * 6, 24, 7], [math.sin(a) * 11, 26 + (k % 3) * 2, 11], [math.sin(a) * 14, 22 + (k % 2) * 4, 15]]
        pts = SC.curve_tube(m, "body", ctrl, 0.8, 0.45, red, n=2, knuckles=True)
        SC.blade(m, "body", pts[-1], SC.sub(pts[-1], pts[-2]), 2.4, 1.1, 0.5, bone_c)


# ------------------------------------------------------------------ Broly (Dragon Ball Super)
BROLY_SKIN = (196, 138, 94)


def broly(m, form):
    """Tan, hugely muscled; scar across his left cheek and an X-scar over his left pectoral; purple skin-tight
    trousers, white boots striped green at the toes, a green fur pelt round his waist flowing down his back, black
    wristbands; wild overgrown hair to his upper back — green-gold and spikier as he powers up."""
    key = {"base": "broly", "wrath": "broly_wrath", "ssj": "broly_lssj", "lssj": "broly_lssj"}[form]
    hair = {"base": (24, 22, 30), "wrath": (24, 22, 30), "ssj": (246, 222, 70), "lssj": (196, 232, 92)}[form]
    iris = {"base": (30, 26, 30), "wrath": (230, 40, 30), "ssj": (60, 180, 120), "lssj": (246, 250, 240)}[form]
    sk = BROLY_SKIN

    def chest(face, px, w, h, base):
        if face == "north":
            ln = dark(sk, 0.78)
            for x in range(w):
                _put(px, w, h, x, int(h * 0.36), ln)               # pecs
            for y in range(int(h * 0.4), int(h * 0.9)):
                _put(px, w, h, w // 2, y, ln)                     # abs
            for y in (int(h * 0.55), int(h * 0.7)):
                for x in range(int(w * 0.3), int(w * 0.7)):
                    _put(px, w, h, x, y, ln)
            for i in range(int(w * 0.35)):                          # the X scar over his left pectoral
                _put(px, w, h, int(w * 0.58) + i, int(h * 0.1) + i, (150, 90, 70))
                _put(px, w, h, int(w * 0.92) - i, int(h * 0.1) + i, (150, 90, 70))
    base_body(m, layered(sk, [chest]), layered(sk, [region((0, 0.78, 1, 0.9), (20, 18, 22))]),
              layered((108, 58, 150), [region((0, 0.8, 1, 1), (240, 240, 236)), region((0, 0.95, 1, 1), (60, 180, 90), faces=("north",))]),
              skin_swap(head_paint(hair, iris, True, key), sk))
    musc = layered(sk, [lines((("north", "east", "west"), [[(0.5, 0.15), (0.5, 0.85)]]), dark(sk, 0.82))])
    for s_, arm in ((1, "rightArm"), (-1, "leftArm")):  # bulging deltoids and biceps
        x0 = 3.5 if s_ > 0 else -8.5
        m.box(arm, [x0, 19.4, -2.5], [5.0, 4.8, 5.0], musc)
        m.box(arm, [x0 + 0.15, 15.2, -2.6], [4.7, 4.4, 4.9], musc)
        m.box(arm, [x0 + 0.1, 12.2, -2.4], [4.8, 1.6, 4.8], solid((20, 18, 22)))                          # wristband
    m.box("body", [-4.2, 18.6, -2.7], [8.4, 4.4, 0.8], layered(sk, [lines((("north",), [[(0.5, 0), (0.5, 1)]]), dark(sk, 0.78))]))  # pectorals
    fur, fur2 = SC.swatch((96, 140, 70)), SC.swatch((70, 110, 52))
    for k in range(18):  # the green fur pelt round his waist
        a = 2 * math.pi * k / 18
        SC.blade(m, "body", [math.cos(a) * 4.4, 13.4, math.sin(a) * 2.6], [math.cos(a) * 0.35, -1, math.sin(a) * 0.35], 3.6, 1.8, 0.7,
                 fur if k % 2 else fur2, width_dir=[-math.sin(a), 0, math.cos(a)])
    SC.curve_tube(m, "body", [[0, 12.5, 2.8], [0, 9, 4.2], [0, 4, 4.6], [0, 0.6, 4.4]], 2.6, 1.6, [fur, fur2], n=2, flat=0.45, width=[1, 0, 0])  # flowing down behind
    # hair: overgrown, spiky, down to the upper back
    shell(m, hair, hairline=30.8, sideburn=False, teeth=0.8)
    hp = M.hair_paint(hair)
    wild = 1.25 if form in ("ssj", "lssj") else (1.12 if form == "wrath" else 1.0)
    for x, z, lean in ((0, -2.0, 0), (2.4, -1.4, 0.6), (-2.4, -1.4, -0.6), (3.4, 1.2, 1.0), (-3.4, 1.2, -1.0), (1.4, 2.6, 0.4), (-1.4, 2.6, -0.4)):
        m.strand([x, 32.0, z], [lean, 1.0 if form in ("ssj", "lssj") else 0.7, z * 0.3 + 0.3], 4.2 * wild, 2.8, hp, bone="hair", segs=3, thick=0.75)
    for x in (-3.0, -1.5, 0, 1.5, 3.0):  # long spikes falling to the upper back
        m.strand([x, 30.5, 3.8], [x * 0.12, -0.8, 0.6], 7.5 * wild, 2.6, hp, bone="hair", segs=3, thick=0.7)
    for x, tilt in ((-2.6, -0.3), (-0.8, -0.05), (1.0, 0.1), (2.8, 0.35)):
        m.strand([x, 31.6, -4.1], [tilt, -0.6, -0.5], 3.0, 2.2, hp, bone="hair", segs=3, thick=0.7)


# ------------------------------------------------------------------ Madara Uchiha
MAD_HAIR = (30, 32, 50)


def madara(m, form):
    """Reanimated Madara: grey sclerae with cracks, the Rinnegan, waist-long spiky hair with bangs over his right eye,
    crimson plate armour over a dark blue outfit, bandaged shins, the war fan (gunbai) with its chain.
    Six Paths (Ten-Tails jinchuriki): white hair, pale grey skin, a white chakra robe with six black magatama below
    the neck, a horn on the left of his forehead, the Rinne Sharingan as a third eye, the black staff and the
    Truth-Seeking Balls."""
    six = form == "sixpaths"
    hair = (238, 236, 232) if six else MAD_HAIR
    skin = (224, 218, 214) if six else SKIN
    key = "madara_sixpaths" if six else "madara_edo"
    head = head_paint(hair, (196, 178, 232), True, key)
    if six:
        head = skin_swap(head, skin)
    if not six:
        armour, plate = (150, 28, 30), (110, 18, 22)
        blue = (40, 44, 80)

        def plates(face, px, w, h, base):
            for y in range(0, h, max(2, h // 6)):
                for x in range(w):
                    _put(px, w, h, x, y, plate)
        base_body(m, layered(armour, [plates]), layered(blue, [region((0, 0.86, 1, 1), skin)]),
                  layered(blue, [region((0, 0.55, 1, 0.86), (232, 230, 224)), region((0, 0.86, 1, 1), (40, 34, 30))]), head)
        for s_, arm in ((1, "rightArm"), (-1, "leftArm")):  # layered shoulder plates
            for k in range(3):
                m.box(arm, [s_ * 6 - 2.8, 21.4 - k * 1.6, -2.8], [5.6, 1.8, 5.6], layered(armour, [region((0, 0.7, 1, 1), plate)]),
                      rot=[0, 0, s_ * (12 + k * 6)], pivot=[s_ * 6, 22, 0])
        for k in range(5):  # the armoured skirt of plates
            a = math.radians(-60 + 30 * k)
            m.box("body", [math.sin(a) * 3.2 - 1.4, 6.0, -2.8 + (1 - math.cos(a)) * 2.5], [2.8, 6.6, 0.6], layered(armour, [plates]))
        m.box("body", [-4.6, 6.0, 2.3], [9.2, 6.6, 0.6], layered(armour, [plates]))
        m.box("body", [-4.6, 11.4, -2.7], [9.2, 1.4, 5.4], solid((150, 110, 70)))                  # obi
        # the gunbai war fan in his right hand, with its black chain
        gun, ink = SC.swatch((196, 110, 52)), SC.swatch((20, 18, 22))
        SC.tube(m, "rightArm", [[6, 11.5, -1.0], [6, 11.6, -6.5]], [0.45, 0.45], SC.swatch((60, 40, 30)), knuckles=False)
        SC.blob(m, "rightArm", [6, 11.8, -10.0], [0.45, 3.6, 3.6], gun, slices=4, axis="z")
        SC.blob(m, "rightArm", [5.5, 11.8, -10.0], [0.2, 1.2, 1.2], ink, slices=2, axis="z")
        for i in range(8):
            SC.obox(m, "rightArm", [6.3, 11.0 - i * 0.6, -1.2 + i * 0.5], [0.5, 0.5, 0.5], ink, (0, 1, 0), 45)
        # the kama (sickle) across his back
        SC.tube(m, "body", [[-3.6, 9.5, 2.9], [3.2, 21, 2.9]], [0.35, 0.35], SC.swatch((60, 40, 30)), knuckles=False)
        SC.blade(m, "body", [3.2, 21, 2.9], [-1, 0.25, 0], 4.2, 1.2, 0.35, SC.swatch((200, 206, 216)), width_dir=[0, 1, 0])
    else:
        robe = (240, 238, 232)

        def magatama(face, px, w, h, base):
            if face == "north":
                for k in range(6):
                    a = math.pi * (0.12 + 0.76 * k / 5)
                    cx, cy = w / 2 + math.cos(a) * w * 0.36, h * 0.06 + math.sin(a) * h * 0.18
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            _put(px, w, h, int(cx) + dx, int(cy) + dy, (16, 14, 18))
        base_body(m, layered(robe, [magatama, region((0.47, 0.25, 0.53, 1), (200, 198, 194), faces=("north",))]),
                  layered(robe, [region((0, 0.86, 1, 1), skin)]), layered((32, 30, 36), [region((0, 0.86, 1, 1), skin)]), head)
        m.box("body", [-4.8, 4.0, 2.2], [9.6, 20.2, 0.5], layered(robe, [lambda f, px, w, h, b: [_put(px, w, h, x, y, (40, 38, 44)) for y in range(h)
                                                                                                    for x in range(w) if f == "north" and (x - w / 2) ** 2 + (y - h * 0.3) ** 2 < (w * 0.18) ** 2]]))  # Hagoromo's pattern on the back
        horn = SC.swatch((236, 232, 226))
        SC.curve_tube(m, "head", [[-2.6, 30.2, -4.2], [-3.6, 32.6, -4.4], [-3.4, 35.0, -3.6]], 0.9, 0.2, horn, n=2)       # the horn on the left
        SC.curve_tube(m, "head", [[2.0, 30.4, -4.3], [3.2, 31.2, -4.4], [4.0, 32.4, -4.0]], 0.6, 0.2, horn, n=2)         # the upward curve on the right
        SC.tube(m, "rightArm", [[6, 2, -2.5], [6, 26, -2.5]], [0.45, 0.45], SC.swatch((20, 18, 22)), knuckles=False)  # the black staff
        SC.blob(m, "rightArm", [6, 26.6, -2.5], [1.4, 1.4, 1.4], SC.swatch((20, 18, 22)), slices=3)
        for i in range(9):  # Truth-Seeking Balls hovering behind him
            a = math.pi * (0.1 + 0.8 * i / 8)
            SC.blob(m, "body", [math.cos(a) * 6.4, 19 + math.sin(a) * 6.2, 4.2], [0.95, 0.95, 0.95], SC.swatch((18, 16, 22)), slices=2)
    # hair: waist-long and spiky, bangs over his right eye
    shell(m, hair, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(hair)
    for x in (-3.4, -2.0, -0.7, 0.7, 2.0, 3.4):
        m.strand([x, 30.8, 3.8], [x * 0.06, -1, 0.35], 15 - abs(x) * 0.8, 3.0, hp, bone="hair", segs=3, thick=0.75, bend=(x * 0.02, 0, 0.06))
    for x, z, lean in ((0, -1.6, 0), (2.2, -0.8, 0.5), (-2.2, -0.8, -0.5), (3.2, 1.6, 0.9), (-3.2, 1.6, -0.9)):
        m.strand([x, 32.0, z], [lean, 0.7, z * 0.3 + 0.4], 4.4, 2.8, hp, bone="hair", segs=3, thick=0.75)
    for s_ in (1, -1):
        m.strand([s_ * 4.0, 30.6, -2.6], [s_ * 0.2, -1, -0.1], 9, 2.4, hp, bone="hair", segs=3, thick=0.7)      # long side bangs
    m.strand([2.0, 31.8, -4.4], [0.1, -1, -0.3], 6.0, 3.2, hp, bone="hair", segs=3, thick=0.6)                    # covering his right eye


FORMS = {
    "naruto_kid": ["base", "cloak"],
    "naruto_teen": ["base", "v1", "v2", "sage", "eight"],
    "naruto_war": ["kcm", "kurama", "sagekurama", "spsm"],
    "naruto_adult": ["hokage", "sage", "link", "baryon"],
    "sasuke_kid": ["sharingan", "cs1", "cs2"],
    "sasuke": ["sharingan", "cs2", "susanoo"],
    "sasuke_war": ["ems", "perfect", "rinnegan"],
    "sasuke_adult": ["adult", "adult_sus"],
    "ichigo": ["shikai", "fullbring", "bankai", "hollow", "vasto", "mugetsu", "true"],
    "tanjiro": ["water", "hinokami", "mark"],
    "tanjiro_demon": ["feral", "sun"],
    "muzan": ["disguise", "final"],
    "broly": ["base", "wrath", "ssj", "lssj"],
    "madara": ["edo", "susanoo", "sixpaths"],
}


def build(char, form):
    m = M.Model()
    if char.startswith("naruto"):
        naruto(m, char, form)
    elif char.startswith("sasuke"):
        sasuke(m, char, form)
    elif char == "ichigo":
        ichigo(m, form)
    elif char == "tanjiro":
        tanjiro(m, form)
    elif char == "tanjiro_demon":
        tanjiro_demon(m, form)
    elif char == "muzan":
        muzan(m, form)
    elif char == "broly":
        broly(m, form)
    elif char == "madara":
        madara(m, "edo" if form == "susanoo" else form)
    if char in ("naruto_kid", "sasuke_kid"):  # kid proportions: a bigger head on the small body
        f, P = 1.15, (0.0, 24.0, 0.0)
        for c in m.cubes:
            if c["bone"] in ("head", "hair", "hat"):
                c["frm"] = [P[i] + (c["frm"][i] - P[i]) * f for i in range(3)]
                c["size"] = [round(v * f * 4) / 4 for v in c["size"]]
                if c["pivot"]:
                    c["pivot"] = [round(P[i] + (c["pivot"][i] - P[i]) * f, 3) for i in range(3)]
    return m
