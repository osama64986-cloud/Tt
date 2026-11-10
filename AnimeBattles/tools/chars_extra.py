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
    "sasuke": dict(eye="narrow", brow="flat", mouth="neutral"),
    "sasuke_ms": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["sharingan"]),
    "ichigo": dict(eye="narrow", brow="sharp", mouth="corner"),
    "ichigo_hollow": dict(eye="narrow", brow="sharp", mouth="none", marks=["hollow_mask"]),
    "ichigo_mugetsu": dict(eye="narrow", brow="flat", mouth="neutral"),
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
        key = "naruto_spsm" if form == "spsm" else "naruto_kcm"
        gold_body(m, key, (255, 140, 20) if form != "spsm" else (250, 180, 50), hair_style="adult" if adult else "war",
                  band=not adult, coat=form in ("kurama", "spsm", "link"), orbs=form == "spsm")
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
    key = "naruto_adult"
    iris = (255, 90, 40) if baryon else (46, 120, 230)
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


# ------------------------------------------------------------------ Sasuke (Shippuden, Taka)
SAS_HAIR = (34, 36, 56)


def sasuke(m, form):
    ms = form == "susanoo"
    shirt = (236, 236, 240)

    def open_v(face, px, w, h, base):
        if face == "north":
            for y in range(int(h * 0.55)):
                half = int((h * 0.55 - y) / (h * 0.55) * w * 0.22)
                for x in range(w // 2 - half, w // 2 + half + 1):
                    _put(px, w, h, x, y, SKIN)
    base_body(m, layered(shirt, [open_v]), arm_paint(shirt, cuff=NAVY, sleeve_to=0.55), leg_paint((40, 44, 80), BLACK),
              head_paint(SAS_HAIR, (200, 20, 30) if ms else (36, 30, 40), True, "sasuke_ms" if ms else "sasuke"))
    m.box("body", [-4.3, 22.0, -2.4], [8.6, 2.2, 4.8], solid(shirt))                                       # high open collar
    m.box("body", [-4.6, 11.4, -2.7], [9.2, 2.0, 5.4], layered((120, 70, 170), [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), (90, 50, 130))]))  # purple rope belt
    for s in (1, -1):  # the big rope bow at the back
        m.strand([s * 0.6, 12.4, 2.8], [s * 1, 0.2, 0.3], 3.4, 2.0, solid((120, 70, 170)), bone="body", segs=2, thick=0.8)
    m.box("body", [-4.5, 6.5, -2.6], [9.0, 5.0, 5.2], layered((40, 44, 90), [lambda f, px, w, h, b: [px.__setitem__((x, y), (0, 0, 0, 0)) for y in range(h) for x in range(w // 3, 2 * w // 3)] if f == "north" else None]))  # cloth over the hips
    # Kusanagi, sheathed across the small of his back
    m.box("body", [-6.0, 13.8, 2.6], [12.0, 0.8, 0.8], solid((30, 30, 36)))
    m.box("body", [-8.6, 13.7, 2.5], [2.6, 1.0, 1.0], solid((60, 60, 70)))
    hp = M.hair_paint(SAS_HAIR)
    shell(m, SAS_HAIR, hairline=30.4, sideburn=False, teeth=0.8)
    for x, y in ((-2.2, 31.5), (0, 32.0), (2.2, 31.5), (-1.2, 30.0), (1.2, 30.0), (0, 28.8)):  # the spikes swept back
        m.strand([x, y, 2.8], [x * 0.12, 0.45, 1], 5.2, 3.0, hp, bone="hair", segs=3, thick=0.75, bend=(0, 0.05, 0))
    for s in (1, -1):  # long bangs framing the face
        m.strand([s * 3.4, 31.4, -4.1], [s * 0.15, -1, -0.1], 6.0, 2.0, hp, bone="hair", segs=3, thick=0.6)
    m.strand([0.8, 31.6, -4.1], [0.1, -1, -0.2], 3.0, 1.8, hp, bone="hair", segs=2, thick=0.6)
    if ms:  # Susanoo: a purple chakra ribcage around him
        pur = (150, 70, 220)
        for i in range(4):
            y = 14 + i * 2.6
            m.box("body", [-5.6, y, -3.4], [11.2, 0.9, 0.6], solid(pur))
            m.box("body", [-5.6, y, -3.4], [0.6, 0.9, 6.8], solid(pur))
            m.box("body", [5.0, y, -3.4], [0.6, 0.9, 6.8], solid(pur))
        m.box("body", [-0.4, 12.5, 3.0], [0.8, 12.0, 0.8], solid(pur))                                         # spine


# ------------------------------------------------------------------ Ichigo (Bleach)
ICH_HAIR = (255, 132, 40)
ZANGETSU = dict(wrap=(236, 236, 236), diamond=(30, 30, 36), tsuba="round", metal=(40, 40, 46),
                blade=(200, 206, 218), edge=(246, 248, 255), hamon=None, saya=(30, 30, 30), saya_band=(200, 200, 200))
TENSA = dict(wrap=(30, 30, 36), diamond=(120, 20, 24), tsuba="cross", metal=(40, 40, 46),
             blade=(28, 28, 34), edge=(150, 150, 170), hamon=None, saya=(30, 30, 30), saya_band=(200, 200, 200))


def ichigo(m, form):
    shihak = (30, 30, 36)
    mugetsu = form == "mugetsu"
    hair = (20, 18, 24) if mugetsu else ICH_HAIR

    def kosode(face, px, w, h, base):
        if face == "north":  # white under-kimono showing in a V
            for y in range(int(h * 0.5)):
                half = int((h * 0.5 - y) / (h * 0.5) * w * 0.2)
                for x in range(w // 2 - half - 1, w // 2 + half + 2):
                    _put(px, w, h, x, y, WHITE if abs(x - w // 2) > half - 1 else SKIN)
    key = {"shikai": "ichigo", "bankai": "ichigo", "hollow": "ichigo_hollow", "mugetsu": "ichigo_mugetsu"}[form]
    iris = (200, 20, 30) if mugetsu else (130, 76, 34)
    base_body(m, layered(shihak, [kosode] if not mugetsu else []), arm_paint(shihak, sleeve_to=0.86),
              leg_paint(shihak, WHITE, toes=False), head_paint(hair, iris, True, key))
    m.box("body", [-4.5, 11.6, -2.6], [9.0, 1.4, 5.2], solid(WHITE if not mugetsu else shihak))              # sash
    if form == "shikai":  # the cleaver Zangetsu: a huge flat blade, no guard
        m.box("rightArm", [5.2, 12.4, -15.0], [1.6, 3.6, 14.0], layered((210, 214, 226), [region((0, 0, 1, 0.2), (40, 40, 46), faces=("east", "west"))]))
        m.box("rightArm", [5.6, 12.8, -1.0], [0.8, 0.8, 3.2], solid((236, 236, 236)))
        m.box("body", [-4.0, 15.0, -2.7], [8.0, 0.8, 0.4], solid((200, 30, 30)), rot=[0, 0, -38], pivot=[0, 18, -2.7])  # the strap
    else:  # Tensa Zangetsu: the black bankai katana and the long torn black coat
        M.katana2(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 15, TENSA)
        coat = layered(shihak, [region((0, 0, 1, 1), (150, 20, 26), faces=("north",))])
        m.box("body", [-4.6, 1.0, 2.2], [9.2, 23.0, 0.5], layered(shihak, [lambda f, px, w, h, b: [px.__setitem__((x, y), (0, 0, 0, 0)) for y in range(h - 6, h) for x in range(w) if (x // 3) % 2 == 0] if f in SIDES else None]))
        for x0 in (-4.6, 1.8):
            m.box("body", [x0, 1.0, -2.7], [2.8, 23.0, 0.5], coat if x0 > 0 else solid(shihak))
    shell(m, hair, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(hair)
    if mugetsu:  # Final Getsuga Tensho: long black hair down to the waist, bandages
        for x in (-2.8, -1, 1, 2.8):
            m.strand([x, 31.0, 3.6], [0, -1, 0.3], 14, 2.4, hp, bone="hair", segs=3, thick=0.7)
        both_arms(m, [3.8, 14.0, -2.2], [4.4, 6.0, 4.4], layered((26, 24, 30), [lines((SIDES, [[(0, y / 6), (1, y / 6 + 0.1)] for y in range(6)]), (60, 56, 66))]))
    else:  # messy orange spikes in every direction
        for x, z, lean in ((0, -2.2, 0), (2.2, -1.4, 0.5), (-2.2, -1.4, -0.5), (3.0, 1.0, 0.9), (-3.0, 1.0, -0.9), (1.4, 2.6, 0.4), (-1.4, 2.6, -0.4), (0, 0.4, 0.1)):
            m.strand([x, 32.0, z], [lean, 1.0, z * 0.25], 3.8, 2.8, hp, bone="hair", segs=3, thick=0.75, bend=(x * 0.05, -0.08, z * 0.05))
        for x, tilt in ((-2.4, -0.2), (0, 0.05), (2.4, 0.2)):
            m.strand([x, 31.4, -4.1], [tilt, -0.6, -0.55], 3.0, 2.2, hp, bone="hair", segs=3, thick=0.7)


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
    "naruto_teen": ["base", "sage"],
    "naruto_war": ["kcm", "kurama", "spsm"],
    "naruto_adult": ["hokage", "link", "baryon"],
    "sasuke": ["sharingan", "susanoo"],
    "ichigo": ["shikai", "bankai", "hollow", "mugetsu"],
    "tanjiro": ["water", "mark"],
}


def build(char, form):
    m = M.Model()
    if char.startswith("naruto"):
        naruto(m, char, form)
        if char == "naruto_kid":  # kid proportions: a bigger head on the small body
            f, P = 1.15, (0.0, 24.0, 0.0)
            for c in m.cubes:
                if c["bone"] in ("head", "hair", "hat"):
                    c["frm"] = [P[i] + (c["frm"][i] - P[i]) * f for i in range(3)]
                    c["size"] = [round(v * f * 4) / 4 for v in c["size"]]
                    if c["pivot"]:
                        c["pivot"] = [round(P[i] + (c["pivot"][i] - P[i]) * f, 3) for i in range(3)]
    elif char == "sasuke":
        sasuke(m, form)
    elif char == "ichigo":
        ichigo(m, form)
    elif char == "tanjiro":
        tanjiro(m, form)
    return m
