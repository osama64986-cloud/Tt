"""Naruto (four ages), Sasuke, Ichigo and Tanjiro in the house style (style 1): 8x8 head,
32 px faces, pixel-art cel shading, strand hair — the same look as Goku/Luffy/Zoro.
Built on the helpers of models.py; imported at the end of it."""
import math

import models as M
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


def leg_paint(col, shoe, band=None, shoe_from=0.86, toes=True):
    ex = [region((0, shoe_from, 1, 1), shoe)]
    if toes:
        ex.append(region((0.15, shoe_from, 0.85, shoe_from + 0.06), SKIN, faces=("north",)))
    if band:
        ex.append(region((0, band[1], 1, band[2]), band[0]))
    return layered(col, ex)


# ------------------------------------------------------------------ faces (marks on the 32 px face)
M.FACE32.update({
    "naruto": dict(eye="anime", brow="angled", mouth="smile", marks=["whiskers"]),
    "naruto_kid": dict(eye="anime", brow="angled", mouth="big_grin", marks=["whiskers"]),
    "naruto_fox": dict(eye="narrow", brow="sharp", mouth="clench", marks=["whiskers", "fox"]),
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
        if form == "cloak":  # Version 1: a red, bubbling chakra skin, fox ears and one tail
            red = (226, 66, 34)
            sh = layered(red, [holes])
            m.box("body", [-4.4, 11.6, -2.4], [8.8, 13.0, 4.8], sh)
            both_arms(m, [3.6, 11.6, -2.4], [4.8, 12.8, 4.8], sh)
            both_legs(m, [-0.5, -0.4, -2.4], [4.8, 12.8, 4.8], sh)
            for s in (1, -1):
                m.strand([s * 2.4, 32.4, -0.5], [s * 0.3, 1, 0.1], 3.6, 2.4, solid(red), bone="hair", segs=2, thick=0.6)
            m.strand([0, 12.6, 2.2], [0, 0.5, 1], 11, 3.2, solid(red), bone="body", segs=3, thick=1.0, bend=(0, 0.25, -0.1))
        return
    if char == "naruto_teen" and form in ("v2", "eight"):  # Version 2 (four tails) / the Eight-Tails' skeletal form
        eight = form == "eight"
        red, deep = ((150, 24, 18), (70, 6, 10)) if not eight else ((196, 52, 26), (110, 18, 12))
        skinp = layered(red, [lambda f, px, w, h, b: [_put(px, w, h, x, y, deep) for y in range(h) for x in range(w) if (x * 5 + y * 3) % 9 == 0]])
        base_body(m, skinp, skinp, skinp, skin_swap(head_paint(deep, (250, 246, 236), False, "naruto_v2"), deep))
        for s_ in (1, -1):  # fox ears
            m.strand([s_ * 2.6, 32.0, -0.5], [s_ * 0.35, 1, 0.1], 4.6 if eight else 3.6, 2.6, solid(red), bone="head", segs=2, thick=0.6)
        n = 8 if eight else 4
        for k in range(n):  # the tails, fanned out behind him
            a = math.radians(-60 + 120 * k / (n - 1))
            m.strand([math.sin(a) * 1.2, 12.4, 2.4], [math.sin(a) * 1.1, 0.9, 1], 12 if eight else 10, 3.0, solid(red), bone="body", segs=3, thick=1.0,
                     bend=(math.sin(a) * 0.15, 0.3, -0.25))
        if eight:  # the bones of the fox growing over him: ribs, spine, skull
            bone_c = solid((236, 226, 210))
            for i in range(3):
                m.box("body", [-4.8, 15.0 + i * 2.6, -2.9], [9.6, 0.8, 0.5], bone_c)
            m.box("body", [-0.5, 12.0, 2.3], [1.0, 12.0, 0.8], bone_c)
            m.box("head", [-4.4, 30.4, -4.6], [8.8, 1.2, 9.2], bone_c)
            for s_ in (1, -1):
                m.box("head", [s_ * 3.9 - 0.4, 24.4, -4.6], [0.8, 6.0, 0.5], bone_c)
        return
    if char == "naruto_teen":
        sage = form == "sage"
        key = "naruto_sage" if sage else "naruto"
        iris = (246, 206, 46) if sage else (46, 120, 230)
        torso = layered(ORANGE, [region((0, 0, 1, 0.45), BLACK), zipper((200, 200, 206)), spiral(N_RED, cy=0.7)])
        base_body(m, torso, arm_paint(ORANGE, top=(BLACK, 0.3)), leg_paint(ORANGE, BLACK, band=(WHITE, 0.78, 0.84)),
                  head_paint(N_HAIR, iris, True, key))
        m.box("body", [-2.2, 22.8, -2.4], [4.4, 2.0, 4.8], layered(BLACK, [zipper((200, 200, 206))]))      # high collar
        naruto_hair(m, N_HAIR, "teen")
        headband(m, BLACK, tails=True)
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
              head_paint(N_HAIR, iris, True, key if not baryon else "naruto_kcm"))
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
    else:  # Baryon Mode: a red chakra hood and cloak, horn-like flames
        red, deep = (214, 34, 40), (150, 14, 24)
        m.box("head", [-4.5, 27.0, -1.0], [9.0, 6.0, 5.6], layered(red, [region((0, 0.8, 1, 1), deep)]))
        m.box("body", [-5.0, 2.0, 2.2], [10.0, 22.4, 0.5], layered(red, [region((0, 0.8, 1, 1), deep)]))
        m.box("body", [-5.0, 22.2, -2.6], [10.0, 2.2, 5.2], solid(red))
        for s in (1, -1):
            m.strand([s * 1.8, 32.8, -0.4], [s * 0.2, 1, 0.05], 10, 2.6, solid(red), bone="hair", segs=3, thick=0.6)
            m.strand([s * 4.6, 23.0, 1.8], [s * 0.45, 1, 0.3], 10, 3.0, solid(red), bone="body", segs=3, thick=0.5)
            m.strand([s * 4.6, 17.0, 2.2], [s * 0.8, 0.7, 0.4], 8.5, 2.8, solid(red), bone="body", segs=3, thick=0.5)


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
    """Cursed Seal Lv2: the two great webbed hands growing from his shoulder blades."""
    hp = layered(col, [lines((SIDES, [[(0.5, 0), (0.5, 1)]]), dark(col, 0.7))])
    for s_ in (1, -1):
        m.strand([s_ * 1.6, 20.5, 2.6], [s_ * 0.9, 0.5, 0.5], 7.5 * size, 2.2 * size, hp, bone="body", segs=2, thick=0.8)
        root = [s_ * (1.6 + 4.46 * size), 20.5 + 2.48 * size, 2.6 + 2.48 * size]
        for k, a in enumerate((-35, -5, 25, 55, 85)):
            r = math.radians(a)
            m.strand(root, [s_ * math.cos(r), math.sin(r), 0.35], (8.5 - abs(k - 2) * 0.9) * size, 1.6 * size, hp, bone="body", segs=3, thick=0.6)
        m.box("body", [root[0] - (3.2 if s_ > 0 else 0.4) * size, root[1] - 1.0, root[2] - 0.3], [3.6 * size, 3.4 * size, 0.6], solid(dark(col, 0.85)))


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
            base_body(m, torso, arm, leg_paint((40, 44, 80), BLACK), head)
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
        hand_wings(m, size=0.8 if kid else 1.0)
    if form == "susanoo":
        susanoo(m, 1)
    elif form == "ems" or form == "adult_sus":
        susanoo(m, 2 if form == "ems" else 3)
    elif form in ("perfect", "rinnegan"):
        susanoo(m, 3)
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
        m.box("body", [-5.0, 22.4, -2.9], [10.0, 2.8, 5.8], fur)                                                 # fur collar
        for s in (1, -1):
            m.strand([s * 3.4, 24.0, -2.4], [s * 0.6, 1, -0.4], 3.2, 2.6, fur, bone="body", segs=2, thick=0.7)
            m.strand([s * 3.4, 24.0, 2.0], [s * 0.6, 1, 0.4], 3.2, 2.6, fur, bone="body", segs=2, thick=0.7)
        both_arms(m, [3.3, 11.6, -2.7], [5.4, 3.4, 5.4], fur)                                                     # fur cuffs
        for s in (1, -1):  # horns: out from the temples, curving forward
            m.strand([s * 4.0, 30.4, -1.0], [s * 1, 0.55, -0.1], 7.5, 2.0, layered(MASK_W, [region((0, 0, 1, 0.25), BLACK)]),
                     bone="head", segs=3, thick=0.9, bend=(-s * 0.12, 0.05, -0.45))
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
TAN_HAIR = (138, 40, 44)
NICHIRIN = dict(wrap=(30, 30, 36), diamond=(200, 60, 50), tsuba="round", metal=(30, 30, 34),
                blade=(36, 36, 42), edge=(120, 124, 140), hamon=None, saya=(30, 30, 30), saya_band=(200, 200, 200))


def tanjiro(m, form):
    mark = form == "mark"
    uni = (28, 30, 40)
    base_body(m, layered(uni, [region((0.45, 0, 0.55, 1), (200, 170, 70), faces=("north",))]), arm_paint(uni),
              leg_paint(uni, (60, 50, 44), band=(WHITE, 0.55, 0.86)),
              head_paint(TAN_HAIR, (150, 30, 44), True, "tanjiro_mark" if mark else "tanjiro"))
    m.box("body", [-4.4, 11.6, -2.5], [8.8, 1.4, 5.0], solid(WHITE))                                          # belt
    hao = layered((40, 130, 90), [checker((40, 130, 90), (24, 24, 28))])
    m.box("body", [-4.6, 7.5, 2.1], [9.2, 16.7, 0.5], hao)                                                    # checkered haori
    for x0 in (-4.6, 2.0):
        m.box("body", [x0, 7.5, -2.6], [2.6, 16.7, 0.5], hao)
    both_arms(m, [3.6, 15.0, -2.6], [4.8, 9.2, 5.2], hao)                                                     # wide sleeves
    m.box("body", [-3.0, 13.0, 2.7], [6.0, 9.0, 4.2], layered((150, 104, 60), [lines((SIDES, [[(0, 0.2), (1, 0.2)], [(0, 0.8), (1, 0.8)]]), (90, 60, 34))]))  # Nezuko's box
    for s in (1, -1):  # hanafuda earrings
        m.box("head", [s * 4.0 - (0.5 if s > 0 else 0.1), 24.6, -0.4], [0.6, 1.6, 0.8], layered(WHITE, [region((0.2, 0.3, 0.8, 0.7), (200, 40, 30))]))
    M.katana2(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 14, NICHIRIN)
    shell(m, TAN_HAIR, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(TAN_HAIR)
    for x, z, lean in ((0, -2.0, 0), (2.2, -1.2, 0.5), (-2.2, -1.2, -0.5), (3.0, 1.2, 0.9), (-3.0, 1.2, -0.9), (0, 2.4, 0)):
        m.strand([x, 32.0, z], [lean, 1.0, z * 0.25], 3.2, 2.8, hp, bone="hair", segs=3, thick=0.75, bend=(x * 0.05, -0.1, z * 0.05))
    for x, tilt in ((-2.6, -0.3), (-0.6, 0), (1.6, 0.2)):
        m.strand([x, 31.6, -4.1], [tilt, -0.6, -0.5], 2.8, 2.2, hp, bone="hair", segs=3, thick=0.7)


FORMS = {
    "naruto_kid": ["base", "cloak"],
    "naruto_teen": ["base", "v2", "sage", "eight"],
    "naruto_war": ["kcm", "kurama", "sagekurama", "spsm"],
    "naruto_adult": ["hokage", "sage", "link", "baryon"],
    "sasuke_kid": ["sharingan", "cs1", "cs2"],
    "sasuke": ["sharingan", "cs2", "susanoo"],
    "sasuke_war": ["ems", "perfect", "rinnegan"],
    "sasuke_adult": ["adult", "adult_sus"],
    "ichigo": ["shikai", "fullbring", "bankai", "hollow", "vasto", "mugetsu", "true"],
    "tanjiro": ["water", "mark"],
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
    if char in ("naruto_kid", "sasuke_kid"):  # kid proportions: a bigger head on the small body
        f, P = 1.15, (0.0, 24.0, 0.0)
        for c in m.cubes:
            if c["bone"] in ("head", "hair", "hat"):
                c["frm"] = [P[i] + (c["frm"][i] - P[i]) * f for i in range(3)]
                c["size"] = [round(v * f * 4) / 4 for v in c["size"]]
                if c["pivot"]:
                    c["pivot"] = [round(P[i] + (c["pivot"][i] - P[i]) * f, 3) for i in range(3)]
    return m
