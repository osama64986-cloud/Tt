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
    "sasuke_adult": dict(eye="narrow", brow="fine", mouth="neutral", marks=["rinnegan"]),
    "sasuke_adult_sh": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["ems", "rinnegan"]),
    "ichigo": dict(eye="narrow", brow="sharp", mouth="corner"),
    "ichigo_hollow": dict(eye="narrow", brow="sharp", mouth="none", marks=["hollow_mask"]),
    "ichigo_mugetsu": dict(eye="narrow", brow="fine", mouth="neutral"),
    "ichigo_vasto": dict(eye="narrow", brow="sharp", mouth="none", marks=["vasto_mask"]),
    "tanjiro": dict(eye="anime", brow="angled", mouth="smile", marks=["tanjiro_scar"]),
    "tanjiro_mark": dict(eye="anime", brow="sharp", mouth="neutral", marks=["tanjiro_mark"]),
    "tanjiro_demon": dict(eye="narrow", brow="sharp", mouth="clench", marks=["tanjiro_mark", "slit_eyes", "fangs", "jaw_mark"]),
    "tanjiro_demon_sun": dict(eye="narrow", brow="sharp", mouth="clench", marks=["tanjiro_mark", "slit_eyes", "fangs", "jaw_mark", "temple_mark"]),
    "muzan": dict(eye="narrow", brow="fine", mouth="neutral", marks=["slit_eyes"]),
    "broly": dict(eye="narrow", brow="sharp", mouth="none", marks=["broly_face", "cheek_scar"]),
    "broly_wrath": dict(eye="narrow", brow="sharp", mouth="none", marks=["broly_face", "cheek_scar", "glow_eyes", "veins"]),
    "broly_ssj": dict(eye="narrow", brow="sharp", mouth="none", marks=["broly_face", "cheek_scar", "veins"]),
    "broly_lssj": dict(eye="narrow", brow="sharp", mouth="none", marks=["broly_face", "cheek_scar", "blank_eyes", "veins"]),
    "madara_edo": dict(eye="narrow", brow="fine", mouth="smirk", marks=["madara_face", "edo_cracks", "rinnegan_both"]),
    "madara_sixpaths": dict(eye="narrow", brow="fine", mouth="smirk", marks=["madara_face", "rinnegan_both", "third_eye"]),
    "muzan_final": dict(eye="narrow", brow="sharp", mouth="clench", marks=["slit_eyes", "fangs", "brow_scales", "face_veins"]),
})

_face32_prev = M.face32


def face32(px, W, H, spec, hair, iris, skin):
    marks = spec.get("marks", [])
    _face32_prev(px, W, H, spec, hair, iris, skin)
    k = W / 32.0

    def put(x, y, c):
        for dx in range(max(1, int((x + 1) * k) - int(x * k))):
            for dy in range(max(1, int((y + 1) * k) - int(y * k))):
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
        if M.EXPR not in ("blink", "hurt"):
            for cx in (10, 21):
                for x in range(cx - 1, cx + 3):
                    for y in (18, 19, 20):
                        put(x, y, (240, 200, 40))
                for x in range(cx - 1, cx + 2):
                    put(x, 19, (16, 12, 14))               # the toad's horizontal bar pupil
    if "whiskers" in marks:
        wc = (40, 18, 14) if "fox" in marks else (110, 64, 50)
        rows = ((21, -1), (24, 0), (27, 1)) if "fox" in marks else ((22, -1), (24, 0), (26, 1))
        for y0, slope in rows:
            for j in range(5):
                yy = y0 + (slope if j >= 3 else 0)
                put(2 + j, yy, wc); put(29 - j, yy, wc)
                if "fox" in marks and j < 3:          # thick at the outer end, thin toward the nose
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
        for x, y in ((28, 31), (29, 31), (27, 30), (28, 30), (27, 29), (26, 28), (27, 28), (26, 27), (25, 26), (26, 26),
                     (25, 25), (25, 24), (26, 23),
                     (30, 28), (30, 27), (29, 26), (30, 26), (29, 25), (29, 24), (28, 23), (29, 23), (28, 22), (29, 21),
                     (28, 16), (27, 15), (28, 15), (27, 14), (26, 13), (27, 13), (26, 12)):
            put(x, y, (20, 16, 22))  # black flame tongues climbing his left side: jaw, cheek, temple
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
    if "broly_face" in marks:  # heavy brow ridge, deep-set fierce eyes, broad nose, thick jaw, a snarl of bared teeth
        sh = (150, 98, 64)
        for x in range(5, 27):
            put(x, 15, sh)                                    # brow-ridge shadow
        for i in range(6):                                    # thick brows slanting down to the nose
            for t in (0, 1):
                put(7 + i, 13 + i // 2 + t, (20, 16, 18)); put(24 - i, 13 + i // 2 + t, (20, 16, 18))
        for y in range(19, 24):                               # broad nose
            put(15, y, sh); put(17, y, sh)
        put(14, 23, sh); put(18, 23, sh)
        for y in range(21, 30):                               # cheekbones and jaw
            put(3, y, sh); put(28, y, sh)
        for x in range(4, 28):
            put(x, 30, sh)
        if M.EXPR != "blink":
            for x in range(11, 21):                           # the snarl: bared teeth in a dark mouth
                put(x, 25, (60, 20, 18)); put(x, 28, (60, 20, 18))
                put(x, 26, (246, 242, 230)); put(x, 27, (226, 222, 210) if x % 2 else (246, 242, 230))
            put(10, 26, (60, 20, 18)); put(21, 26, (60, 20, 18)); put(10, 27, (60, 20, 18)); put(21, 27, (60, 20, 18))
    if "veins" in marks:  # veins standing out on his temples
        for x, y in ((3, 10), (4, 11), (4, 12), (5, 13), (28, 10), (27, 11), (27, 12), (26, 13)):
            put(x, y, (150, 70, 50))
    if "madara_face" in marks:  # the creases under his eyes, a sharp jaw
        for cx in (10, 21):
            for x in range(cx - 2, cx + 3):
                put(x, 23 + (1 if x in (cx - 2, cx + 2) else 0), (176, 140, 120))
        for y in range(24, 30):
            put(4 + (y - 24) // 2, y, (200, 166, 146)); put(27 - (y - 24) // 2, y, (200, 166, 146))
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
    if "edo_cracks" in marks:  # Reanimation: cracks running down from the eyes and across the face
        for pts in (((7, 22), (6, 23), (6, 24), (5, 25), (5, 26), (4, 27)), ((24, 22), (25, 23), (25, 24), (26, 25), (27, 26)),
                    ((12, 9), (11, 10), (11, 11), (10, 12)), ((22, 9), (23, 10), (22, 11))):
            for x, y in pts:
                put(x, y, (110, 96, 92))
    if "rinnegan_both" in marks and open_eyes:  # the Rinnegan in both eyes: pale lavender, clear dark rings, grey sclera
        for cx in (10, 21):
            for y in range(16, 24):
                for x in range(cx - 3, cx + 5):
                    d = math.hypot(x - cx - 0.5, y - 19.5)
                    if d > 3.4:
                        continue
                    if d > 2.9:
                        c = (150, 146, 150) if "edo_cracks" in marks else (236, 234, 240)
                    elif 2.2 < d <= 2.9 or 0.9 < d <= 1.5:
                        c = (82, 56, 128)
                    else:
                        c = (206, 190, 238)
                    put(x, y, c)
            put(cx, 19, (40, 24, 60)); put(cx + 1, 19, (40, 24, 60)); put(cx, 20, (40, 24, 60)); put(cx + 1, 20, (40, 24, 60))
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
        col = (170, 40, 40) if big else (182, 56, 48)
        pts = [(19, 12), (20, 12), (21, 12), (22, 12), (23, 12), (24, 12), (25, 12),
               (19, 13), (20, 13), (21, 13), (22, 13), (23, 13), (24, 13), (25, 13),
               (20, 14), (21, 14), (22, 14), (23, 14)]
        if big:
            pts += [(19, 11), (20, 11), (24, 12), (25, 12), (22, 11), (21, 10), (25, 14), (20, 14)]
        for x, y in pts:
            put(x, y, col)
        for x, y in ((21, 13), (22, 13), (23, 13), (22, 12), (21, 14)):
            put(x, y, (132, 30, 34))                                       # darker core


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


def sage_toad(m, x, who):
    """Fukasaku / Shima, the two small elder Sage Toads of Mount Myoboku, sitting on Naruto's shoulder: a squat green toad
    with big yellow eyes and a little cloak; Fukasaku has white brows and a white beard, Shima purple lips."""
    skin = (150, 162, 98) if who == "fukasaku" else (140, 154, 96)
    cloak = (96, 66, 44) if who == "fukasaku" else (120, 84, 120)
    y = 24.0
    k = 1.3
    _box = m.box

    def box(bone, frm, size, paint):  # every part 30% bigger, scaled about the toad's seat on the shoulder
        _box(bone, [x + (frm[0] - x) * k, y + (frm[1] - y) * k, frm[2] * k], [v * k for v in size], paint)
    box("body", [x - 1.6, y, -1.4], [3.2, 2.2, 2.8], layered(skin, [region((0, 0.6, 1, 1), light(skin, 0.15), faces=("north",))]))   # body
    box("body", [x - 1.7, y + 0.2, -0.2], [3.4, 2.0, 1.6], solid(cloak))                                                            # cloak over the back
    box("body", [x - 1.4, y + 2.2, -1.2], [2.8, 1.6, 2.4], solid(skin))                                                            # head
    for ex in (-0.75, 0.75):  # big yellow eyes with a bar pupil
        box("body", [x + ex - 0.45, y + 3.4, -1.25], [0.9, 0.7, 0.6], solid((246, 214, 70)))
        box("body", [x + ex - 0.35, y + 3.6, -1.35], [0.7, 0.2, 0.2], solid((20, 16, 14)))
    if who == "fukasaku":
        for ex in (-0.75, 0.75):
            box("body", [x + ex - 0.55, y + 3.85, -1.3], [1.1, 0.3, 0.5], solid((244, 244, 240)))   # white brows
        box("body", [x - 0.9, y + 1.6, -1.6], [1.8, 0.8, 0.5], solid((244, 244, 240)))             # white beard
    else:
        box("body", [x - 0.7, y + 2.5, -1.3], [1.4, 0.35, 0.2], solid((150, 70, 150)))             # purple lips


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
            sage_toad(m, 6.4, "fukasaku")   # the two Great Sage Toads riding his shoulders (Pain arc)
            sage_toad(m, -6.4, "shima")
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
TENSA = dict(wrap=(30, 30, 36), diamond=(120, 20, 24), tsuba="manji", metal=(70, 70, 80),
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
    """Zangetsu's Shikai as a flat pixel-art sprite: a huge guardless cleaver with a cloth-wrapped hilt.
    With `core` it is the True Bankai blade (silver edges round a black core) and a chain."""
    hilt = 3.6
    M.flat_blade(m, bone, (cx, cy, -1.2), (0, 0.1, -1), hilt, L, W, M.zangetsu_shape(blade, edge, spine, core, grip, hilt / (hilt + L)), grip=0.6)
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
    if not final:  # Asakusa disguise: white fedora, a plain black suit with a white shirt and dark tie, dark trousers
        tux, skin = (26, 25, 31), (245, 228, 215)   # pale but warm: a gentleman, not a corpse

        def suit(face, px, w, h, base):
            if face != "north":
                return
            for y in range(int(h * 0.62)):  # the shirt's V between the lapels, the tie with its knot
                half = (w * 0.2) * (1 - y / (h * 0.62))
                for x in range(w):
                    d = abs(x + 0.5 - w / 2)
                    if d < half:
                        _put(px, w, h, x, y, (240, 238, 234))
                    elif d < half + 1:
                        _put(px, w, h, x, y, (60, 56, 66))  # lapel edge
            for y in range(int(h * 0.04), int(h * 0.5)):
                for x in (w // 2 - 1, w // 2):
                    _put(px, w, h, x, y, (60, 14, 24))
            for x in range(w // 2 - 2, w // 2 + 2):
                _put(px, w, h, x, int(h * 0.05), (60, 14, 24))
            for y in (int(h * 0.68), int(h * 0.82)):
                _put(px, w, h, w // 2, y, (120, 72, 40))  # brown buttons
        base_body(m, layered(tux, [suit]), layered(tux, [region((0, 0.86, 1, 1), skin), region((0, 0.82, 1, 0.86), WHITE)]),
                  layered((40, 38, 45), [region((0, 0.9, 1, 1), (18, 16, 20))]),
                  skin_swap(head_paint((20, 18, 24), (184, 20, 46), True, "muzan"), skin))
        m.box("body", [-4.5, 6.0, 2.2], [9.0, 18.2, 0.5], solid(tux))                                   # long jacket tails
        m.box("body", [-2.4, 22.6, -2.4], [4.8, 1.8, 4.8], solid(WHITE))                                # shirt collar
        muzan_hair(m, (20, 18, 24))
        hat = (238, 236, 230)
        m.box("hat", [-5.6, 30.8, -5.6], [11.2, 0.5, 11.2], solid(hat), rot=[-8, 0, 0], pivot=[0, 31.0, 0])   # brim, dipping at the front
        m.box("hat", [-4.3, 31.2, -4.3], [8.6, 2.4, 8.6], layered(hat, [region((0, 0.55, 1, 1), (40, 26, 30))]))  # crown and dark band
        m.box("hat", [-3.6, 33.6, -3.6], [7.2, 0.9, 7.2], layered(hat, [region((0.42, 0, 0.58, 1), dark(hat, 0.82), faces=("up",))]))  # pinched top, centre crease
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
    key = {"base": "broly", "wrath": "broly_wrath", "ssj": "broly_ssj", "lssj": "broly_lssj"}[form]
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
    m.box("body", [-3.0, 23.6, -1.6], [6.0, 1.6, 3.6], musc)                                                   # thick neck / traps
    if form == "lssj":  # Full Power: the body swells even further — wider chest, heavier shoulders
        m.box("body", [-4.8, 14.5, -2.9], [9.6, 9.6, 5.8], layered(sk, [lines((("north",), [[(0.5, 0.05), (0.5, 0.95)], [(0.2, 0.32), (0.8, 0.32)]]), dark(sk, 0.78))]))
        for s_, arm in ((1, "rightArm"), (-1, "leftArm")):
            m.box(arm, [3.2 if s_ > 0 else -8.8, 20.0, -2.8], [5.6, 4.6, 5.6], musc)
    fur, fur2 = SC.swatch((96, 140, 70)), SC.swatch((70, 110, 52))
    m.box("body", [-4.5, 11.6, -2.7], [9.0, 2.2, 5.4], solid((84, 124, 62)))  # the pelt wrapped tight round his waist
    for k in range(20):  # its ragged fur hem hanging all round (a little longer at the back) — no tail
        a = 2 * math.pi * k / 20
        back = max(0.0, math.sin(a))
        SC.blade(m, "body", [math.cos(a) * 4.3, 12.0, math.sin(a) * 2.6], [math.cos(a) * 0.3, -1, math.sin(a) * 0.3], 3.0 + back * 1.6, 1.9, 0.7,
                 fur if k % 2 else fur2, width_dir=[-math.sin(a), 0, math.cos(a)])
    broly_hair(m, hair, form)


@M.smooth_hair
def broly_hair(m, hair, form):
    """Broly's hair: a thick, overgrown, untamed mane. Base/Wrathful: heavy spikes swept back and down to the upper
    back with shaggy bangs; Super Saiyan / Legendary: the same mane thrown up and back, huge and jagged."""
    shell(m, hair, hairline=30.8, sideburn=False, teeth=0.8)
    hp = M.hair_paint(hair)
    up = form in ("ssj", "lssj")
    big = 1.3 if form == "lssj" else 1.15 if up else 1.0
    rise = 1.0 if up else 0.35
    for x, z, sx in ((-2.8, -1.6, -0.5), (-0.9, -2.0, -0.15), (0.9, -2.0, 0.15), (2.8, -1.6, 0.5)):    # front crown
        m.strand([x, 32.1, z], [sx, rise, 0.55], 6.0 * big, 3.4, hp, bone="hair", thick=0.8, bend=(0, -0.08 if not up else 0, 0.05))
    for x, z, sx in ((-3.2, 0.6, -0.8), (-1.1, 0.4, -0.25), (1.1, 0.4, 0.25), (3.2, 0.6, 0.8)):        # top, thrown back
        m.strand([x, 32.3, z], [sx, rise * 0.9, 0.9], 7.0 * big, 3.6, hp, bone="hair", thick=0.8, bend=(0, -0.1 if not up else 0, 0))
    for x in (-3.4, -1.7, 0.0, 1.7, 3.4):                                                          # the mane down the back
        m.strand([x, 31.0, 3.6], [x * 0.15, -0.75 + (0.6 if up else 0), 0.7], 8.5 * big, 3.2, hp, bone="hair", thick=0.75)
    for s_ in (1, -1):                                                                             # wild sides
        m.strand([s_ * 4.0, 31.2, -0.6], [s_ * 1, rise * 0.6, 0.3], 5.5 * big, 3.0, hp, bone="hair", thick=0.75)
        m.strand([s_ * 4.0, 29.8, 1.6], [s_ * 0.9, -0.3 + rise * 0.4, 0.6], 5.0 * big, 2.8, hp, bone="hair", thick=0.75)
    for x, tilt in ((-2.6, -0.3), (-0.9, -0.08), (1.0, 0.1), (2.7, 0.32)):                          # shaggy bangs
        m.strand([x, 31.6, -4.1], [tilt, -0.6 if not up else 0.2, -0.5], 3.2, 2.4, hp, bone="hair", thick=0.7)


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
    for x, z, lean in ((0, -1.6, 0), (2.2, -0.8, 0.5), (-2.2, -0.8, -0.5), (3.2, 1.6, 0.9), (-3.2, 1.6, -0.9), (1.2, 2.6, 0.3), (-1.2, 2.6, -0.3)):
        m.strand([x, 32.0, z], [lean, 0.7, z * 0.3 + 0.4], 5.2, 3.0, hp, bone="hair", segs=3, thick=0.75)
    for k in range(9):  # the wild mane: spikes thrusting back and out all down his back
        a = math.radians(-70 + 140 * k / 8)
        m.strand([math.sin(a) * 3.6, 29 - abs(math.sin(a)) * 2, 3.4], [math.sin(a) * 0.9, -0.15, 1], 6.5 - abs(k - 4) * 0.4, 2.6, hp, bone="hair", segs=3, thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 4.0, 30.6, -2.6], [s_ * 0.2, -1, -0.1], 9, 2.4, hp, bone="hair", segs=3, thick=0.7)      # long side bangs
    m.strand([2.0, 31.8, -4.4], [0.1, -1, -0.3], 6.0, 3.2, hp, bone="hair", segs=3, thick=0.6)                    # covering his right eye


# ------------------------------------------------------------------ Itachi and Kakashi (faces)
M.FACE32.update({
    "itachi": dict(eye="narrow", brow="fine", mouth="neutral", marks=["sharingan", "itachi_lines"]),
    "itachi_ms": dict(eye="narrow", brow="fine", mouth="neutral", marks=["itachi_ms", "itachi_lines"]),
    "kakashi": dict(eye="narrow", brow="fine", mouth="none", marks=["kakashi_mask", "kakashi_band"]),
    "kakashi_sh": dict(eye="narrow", brow="sharp", mouth="none", marks=["kakashi_mask", "kakashi_scar", "kakashi_sharingan"]),
    "kakashi_dms": dict(eye="narrow", brow="sharp", mouth="none", marks=["kakashi_mask", "kakashi_scar", "kakashi_ms_both"]),
})
_face32_prev2 = M.face32


def face32_more(px, W, H, spec, hair, iris, skin):
    _face32_prev2(px, W, H, spec, hair, iris, skin)
    marks = spec.get("marks", [])
    k = W / 32.0
    open_eyes = M.EXPR not in ("blink", "hurt")

    def put(x, y, c):
        for dx in range(max(1, int((x + 1) * k) - int(x * k))):
            for dy in range(max(1, int((y + 1) * k) - int(y * k))):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    if "itachi_lines" in marks:  # the long tear-trough lines running down from the inner corners of his eyes
        for x, y in ((13, 22), (13, 23), (12, 24), (12, 25), (12, 26)):
            put(x, y, (150, 104, 84)); put(31 - x, y, (150, 104, 84))
    if "itachi_ms" in marks and open_eyes:  # Itachi's Mangekyo: a black three-bladed shuriken on red
        for cx in (10, 21):
            for x, y in ((cx, 19), (cx + 1, 19), (cx, 20), (cx + 1, 20), (cx - 1, 17), (cx, 18), (cx + 2, 18), (cx + 3, 19),
                         (cx - 1, 21), (cx - 1, 22), (cx + 2, 21)):
                put(x, y, (10, 6, 8))
    if "kakashi_mask" in marks:  # the dark mask over his nose, mouth and neck
        navy = (40, 44, 66)
        for y in range(22, 32):
            for x in range(32):
                put(x, y, navy if (x + y) % 9 else (34, 38, 58))
        for x in range(13, 19):  # the ridge of the nose under the cloth
            put(x, 22, (56, 60, 86))
        put(15, 23, (56, 60, 86)); put(16, 23, (56, 60, 86))
    if "kakashi_band" in marks:  # the forehead protector pulled down over his left eye
        for y in range(15, 22):
            for x in range(17, 32):
                put(x, y, (36, 40, 62) if y < 21 else (24, 26, 40))
    if "kakashi_scar" in marks:  # the vertical scar through his left eye
        for y in list(range(13, 17)) + list(range(22, 24)):
            put(21, y, (150, 90, 80))
    if "kakashi_sharingan" in marks and open_eyes:  # Obito's Sharingan in his left eye only
        for y in range(17, 22):
            for x in range(20, 24):
                put(x, y, (196, 22, 30))
        for x, y in ((21, 19), (22, 19), (21, 20), (22, 20)):
            put(x, y, (10, 6, 8))
        for x, y in ((20, 17), (23, 18), (21, 21)):
            put(x, y, (10, 6, 8))
    if "kakashi_ms_both" in marks and open_eyes:  # Mangekyo in both eyes: a curved three-armed pinwheel
        for cx in (10, 21):
            for y in range(17, 22):
                for x in range(cx - 1, cx + 3):
                    put(x, y, (196, 22, 30))
            for x, y in ((cx, 19), (cx + 1, 19), (cx, 20), (cx + 1, 20), (cx - 1, 18), (cx, 17), (cx + 2, 18), (cx + 2, 21), (cx - 1, 21), (cx + 1, 21)):
                put(x, y, (10, 6, 8))


M.face32 = face32_more


def akatsuki_cloud(cx, cy, r, faces=("north", "south", "east", "west")):
    """A red Akatsuki cloud with its white outline."""
    def f(face, px, w, h, base):
        if face not in faces:
            return
        lobes = [(-0.9, 0.15, 0.55), (-0.35, -0.2, 0.62), (0.3, -0.25, 0.6), (0.85, 0.1, 0.5), (0.0, 0.25, 0.6)]
        R = r * w
        for pass_, col in ((1.25, (240, 240, 236)), (1.0, (196, 28, 34))):
            for ox, oy, rr in lobes:
                X, Y, RR = cx * w + ox * R, cy * h + oy * R, rr * R * pass_
                for y in range(int(Y - RR) - 1, int(Y + RR) + 2):
                    for x in range(int(X - RR) - 1, int(X + RR) + 2):
                        if (x - X) ** 2 + (y - Y) ** 2 <= RR * RR:
                            _put(px, w, h, x, y, col)
    return f


# ------------------------------------------------------------------ Itachi Uchiha
ITA_HAIR = (26, 26, 34)


def itachi(m, form):
    """Akatsuki Itachi: black cloak with red clouds and its high collar, the scratched Leaf headband, long hair tied in a
    low ponytail with long bangs framing his face, the lines under his eyes. Sharingan, then the Mangekyo."""
    key = "itachi" if form == "sharingan" else "itachi_ms"
    head = head_paint(ITA_HAIR, (200, 20, 30), True, key)
    cloak = (24, 24, 30)
    torso = layered(cloak, [akatsuki_cloud(0.3, 0.55, 0.16, ("north",)), akatsuki_cloud(0.62, 0.3, 0.14, ("south",)),
                            akatsuki_cloud(0.5, 0.5, 0.22, ("east", "west")), region((0, 0, 1, 1), (150, 24, 30), faces=("down",))])
    arm = layered(cloak, [akatsuki_cloud(0.5, 0.3, 0.3, ("east", "west")), region((0, 0.86, 1, 1), SKIN)])
    base_body(m, torso, arm, leg_paint((40, 40, 56), (40, 40, 56), toe=SKIN), head)
    # the long cloak skirt: front flaps parted in the middle, a back panel and the sides (red lining inside)
    lining = (150, 24, 30)
    for s_ in (1, -1):
        m.box("body", [s_ * 2.35 - 2.05, 2.8, -2.75], [4.1, 9.4, 0.5], layered(cloak, [akatsuki_cloud(0.5 - s_ * 0.1, 0.45, 0.22, ("north",)),
                                                                                  region((0, 0, 1, 1), lining, faces=("south",))]))
        m.box("body", [s_ * 4.5 - 0.3, 2.8, -2.4], [0.6, 9.4, 4.8], layered(cloak, [akatsuki_cloud(0.5, 0.5, 0.3, ("east", "west"))]))
    m.box("body", [-4.6, 2.8, 2.25], [9.2, 9.4, 0.5], layered(cloak, [akatsuki_cloud(0.35, 0.4, 0.17, ("south",)), akatsuki_cloud(0.72, 0.68, 0.13, ("south",))]))
    # the high collar standing up round his chin (open at the front), red inside
    m.box("body", [-4.4, 23.6, -2.7], [8.8, 2.4, 5.4], layered(cloak, [region((0, 0, 1, 1), lining, faces=("up",)),
                                                                      region((0.4, 0, 0.6, 1), lining, faces=("north",))]))
    # headband with the scratch through the Leaf
    headband(m, (34, 36, 50))
    m.box("head", [-2.0, 29.3, -4.72], [4.0, 0.3, 0.12], solid((40, 40, 50), outline=False), rot=[0, 0, -14], pivot=[0, 29.45, -4.66])
    # hair: long bangs framing the face, the low ponytail
    shell(m, ITA_HAIR, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(ITA_HAIR)
    for s_ in (1, -1):
        m.strand([s_ * 3.6, 31.6, -4.1], [s_ * 0.12, -1, -0.05], 7.6, 2.2, hp, bone="hair", segs=3, thick=0.6)
        m.strand([s_ * 1.4, 31.9, -4.2], [s_ * 0.45, -1, -0.15], 3.0, 1.8, hp, bone="hair", segs=2, thick=0.6)
    m.box("hair", [-0.7, 25.6, 3.9], [1.4, 1.0, 1.0], solid((40, 40, 50)))                       # the tie
    m.strand([0, 25.8, 4.3], [0, -1, 0.25], 6.5, 1.6, hp, bone="hair", segs=3, thick=0.7)       # the ponytail
    # the ring on his right ring finger (Suzaku, red)
    m.box("rightArm", [3.9, 12.6, -2.15], [0.6, 0.6, 0.3], solid((200, 40, 40), outline=False))


# ------------------------------------------------------------------ Kakashi Hatake
@M.smooth_hair
def kakashi_hair(m):
    """Kakashi's hair: separate silver spikes standing up and all sweeping over to his left (-x), the tallest
    over the middle, short ones at the back, two short bangs framing the headband."""
    shell(m, KAK_HAIR, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(KAK_HAIR)
    for x, z, L in ((2.8, -1.8, 6.0), (1.2, -2.2, 7.6), (-0.4, -2.0, 8.4), (-2.0, -1.4, 8.0), (-3.4, -0.6, 6.6)):     # front row
        m.strand([x, 32.0, z], [-0.55, 1, -0.05], L, 3.0, hp, bone="hair", thick=0.8, bend=(-0.06, 0, 0))
    for x, z, L in ((2.4, 0.8, 6.4), (0.6, 0.6, 7.6), (-1.2, 0.8, 7.8), (-2.9, 1.0, 6.6)):                          # middle row
        m.strand([x, 32.2, z], [-0.6, 1, 0.25], L, 3.1, hp, bone="hair", thick=0.8, bend=(-0.06, 0, 0))
    for x, z, L in ((1.6, 3.0, 5.0), (-0.4, 3.2, 5.6), (-2.4, 3.0, 5.0)):                                          # back row
        m.strand([x, 31.6, z], [-0.5, 0.8, 0.7], L, 3.0, hp, bone="hair", thick=0.8)
    for s_ in (1, -1):
        m.strand([s_ * 3.4, 31.4, -3.9], [s_ * 0.1, -1, -0.1], 3.6, 2.0, hp, bone="hair", segs=2, thick=0.6)
    m.strand([0.6, 31.6, -4.1], [0.15, -1, -0.2], 2.8, 2.2, hp, bone="hair", segs=2, thick=0.6)

KAK_HAIR = (206, 210, 222)


def kakashi(m, form):
    """Kakashi: gravity-defying silver hair swept up and to his left, the mask, green flak jacket over the navy
    shinobi suit with the red swirl on the back, taped shins. Base: headband down over his left eye; Sharingan:
    headband up, the scar and Obito's eye; Double Mangekyo (war, both eyes)."""
    key = {"base": "kakashi", "sharingan": "kakashi_sh", "dms": "kakashi_dms"}[form]
    head = head_paint(KAK_HAIR, (30, 30, 36), True, key)
    navy, vest = (40, 44, 70), (92, 112, 70)

    def pockets(face, px, w, h, base):
        if face == "north":
            for x0 in (0.08, 0.3, 0.6, 0.82):
                for y in range(int(h * 0.2), int(h * 0.5)):
                    for x in range(int(w * x0), int(w * (x0 + 0.12))):
                        _put(px, w, h, x, y, dark(vest, 0.82) if y == int(h * 0.2) else light(vest, 0.1))
        if face == "south":  # the red Uzumaki swirl on the back
            cx, cy, r = w / 2, h * 0.42, min(w, h) * 0.24
            for i in range(60):
                a = i / 60 * math.pi * 2 * 1.4
                rr = 0.5 + r * i / 60
                _put(px, w, h, int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr), (196, 40, 36))
    torso = layered(vest, [pockets, zipper(dark(vest, 0.7)), region((0, 0, 1, 0.1), navy)])
    arm = layered(navy, [region((0, 0.86, 1, 1), SKIN), region((0, 0, 1, 0.22), vest)])
    leg = layered(navy, [region((0, 0.58, 1, 0.84), (232, 232, 226)), region((0, 0.84, 1, 1), (40, 44, 70)),
                         region((0.15, 0.86, 0.85, 0.92), SKIN, faces=("north",))])
    base_body(m, torso, arm, leg, head)
    m.box("body", [-2.4, 23.2, -2.5], [4.8, 1.6, 5.0], solid(navy))                             # the mask's neck

    def mask_front(face, px, w, h, base):  # the ridge of the nose under the cloth
        if face == "north":
            for x in range(int(w * 0.4), int(w * 0.6)):
                _put(px, w, h, x, 0, light(navy, 0.25))
    # the mask wraps all the way round the lower head: nose, mouth, cheeks, jaw and the back of the neck
    m.box("head", [-4.15, 23.95, -4.15], [8.3, 2.55, 8.3], layered(navy, [mask_front]))
    m.box("body", [-4.4, 21.4, -2.6], [8.8, 2.4, 5.2], solid(vest))                              # the vest's thick collar
    # headband: tilted down over the left eye in base form, up on the forehead otherwise
    if form == "base":
        m.box("head", [-4.3, 28.2, -4.3], [8.6, 2.0, 8.6], solid((36, 40, 62)), rot=[0, 0, -12], pivot=[0, 29.2, 0])
        m.box("head", [-2.4, 28.2, -4.65], [4.8, 2.2, 0.35], layered((196, 202, 212), [leaf_plate]), rot=[0, 0, -12], pivot=[0, 29.2, 0])
    else:
        headband(m, (36, 40, 62))
    kakashi_hair(m)
    # the kunai pouch on his right thigh
    m.box("rightLeg", [2.2, 6.6, -1.2], [1.0, 2.4, 2.4], solid((36, 38, 46)))


# ------------------------------------------------------------------ five new fighters: faces
M.FACE32.update({
    "deku": dict(eye="round", brow="angled", mouth="clench", marks=["freckles"]),
    "deku_cowl": dict(eye="round", brow="sharp", mouth="clench", marks=["freckles", "cowl_veins"]),
    "deku_dark": dict(eye="narrow", brow="sharp", mouth="none", marks=["freckles", "deku_scars", "dark_mask"]),
    "killua": dict(eye="narrow", brow="flat", mouth="smirk", marks=[]),
    "killua_god": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["bolt_eyes"]),
    "denji": dict(eye="narrow", brow="angled", mouth="big_grin", marks=["shark_teeth"]),
    "chainsaw": dict(eye="round", brow="none", mouth="none", marks=["chainsaw_face"]),
    "chainsaw_black": dict(eye="round", brow="none", mouth="none", marks=["chainsaw_face", "chainsaw_black"]),
    "rengoku": dict(eye="round", brow="sharp", mouth="smile", marks=["rengoku_brows", "rengoku_eyes"]),
    "rengoku_ninth": dict(eye="round", brow="sharp", mouth="clench", marks=["rengoku_brows", "rengoku_eyes", "flame_aura_face"]),
    "ace": dict(eye="narrow", brow="angled", mouth="smirk", marks=["freckles"]),
    "ace_flame": dict(eye="narrow", brow="sharp", mouth="smirk", marks=["freckles", "ember_eyes"]),
})
_face32_prev3 = M.face32


def face32_new5(px, W, H, spec, hair, iris, skin):
    _face32_prev3(px, W, H, spec, hair, iris, skin)
    marks = spec.get("marks", [])
    k = W / 32.0
    open_eyes = M.EXPR not in ("blink", "hurt")

    def put(x, y, c):
        for dx in range(max(1, int((x + 1) * k) - int(x * k))):
            for dy in range(max(1, int((y + 1) * k) - int(y * k))):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    if "freckles" in marks:  # freckles across both cheeks
        for x, y in ((6, 22), (8, 23), (7, 24), (25, 22), (23, 23), (24, 24)):
            put(x, y, (176, 112, 84))
    if "cowl_veins" in marks:  # One For All's green lightning crackling over his face
        for x, y in ((3, 12), (4, 13), (4, 14), (5, 15), (28, 26), (27, 27), (27, 28), (26, 29), (2, 27), (3, 28)):
            put(x, y, (120, 255, 150))
    if "deku_scars" in marks:
        for i in range(5):
            put(22 + i, 12 + i, (150, 90, 80))
    if "dark_mask" in marks:  # the cloth over his mouth and nose, Dark Deku
        for y in range(23, 32):
            for x in range(32):
                put(x, y, (36, 40, 38) if (x + y) % 7 else (28, 32, 30))
    if "cat_mouth" in marks:  # Killua's cat-like smirk
        for x, y in ((14, 26), (15, 27), (16, 26), (17, 27), (18, 26)):
            put(x, y, (110, 60, 60))
    if "bolt_eyes" in marks and open_eyes:  # Godspeed: the eyes glow electric blue
        for cx in (10, 21):
            for x in range(cx - 1, cx + 3):
                for y in (18, 19, 20):
                    put(x, y, (150, 230, 255))
            put(cx, 19, (255, 255, 255)); put(cx + 1, 19, (255, 255, 255))
    if "shark_teeth" in marks:  # Denji's jagged shark grin
        for x in range(10, 22, 2):
            put(x, 26, (250, 250, 250)); put(x + 1, 27, (250, 250, 250))
    if "chainsaw_face" in marks:  # Chainsaw Man: the devil's head — no human face, wide sockets and a mouth full of jagged teeth
        base = (226, 96, 50) if "chainsaw_black" not in marks else (40, 38, 42)
        dark_ = (150, 52, 30) if "chainsaw_black" not in marks else (16, 14, 18)
        for y in range(32):
            for x in range(32):
                put(x, y, base if (x * 3 + y * 5) % 13 else dark_)
        for cx in (9, 22):  # round empty eye sockets with pinpoint pupils
            for y in range(15, 21):
                for x in range(cx - 3, cx + 3):
                    if (x - cx + 0.5) ** 2 + (y - 17.5) ** 2 < 9:
                        put(x, y, (250, 246, 236))
            put(cx, 17, (20, 16, 18)); put(cx - 1, 18, (20, 16, 18))
        for y in range(22, 30):  # the gaping mouth
            for x in range(6, 26):
                put(x, y, (40, 10, 12))
        for x in range(6, 26, 2):  # rows of sharp teeth top and bottom
            put(x, 22, (250, 250, 244)); put(x + 1, 23, (250, 250, 244))
            put(x, 29, (250, 250, 244)); put(x + 1, 28, (250, 250, 244))
    if "rengoku_brows" in marks:  # thick forked eyebrows: yellow, tipped red
        for cx, sgn in ((10, -1), (21, 1)):
            for i in range(6):
                put(cx - 2 + i, 14 - (i // 3), (250, 196, 40))
            put(cx + 4, 12, (210, 50, 30)); put(cx + 4, 13, (210, 50, 30))
    if "rengoku_eyes" in marks and open_eyes:  # wide gold eyes fading to red at the centre
        for cx in (10, 21):
            for x in range(cx - 1, cx + 3):
                for y in (17, 18, 19, 20):
                    put(x, y, (250, 190, 40))
            for x in (cx, cx + 1):
                for y in (18, 19):
                    put(x, y, (226, 80, 30))
            put(cx - 1, 17, (255, 250, 230))
    if "flame_aura_face" in marks:
        for x, y in ((2, 8), (3, 9), (29, 8), (28, 9), (1, 12), (30, 12)):
            put(x, y, (255, 150, 40))
    if "ember_eyes" in marks and open_eyes:
        for cx in (10, 21):
            put(cx, 19, (255, 140, 40)); put(cx + 1, 19, (255, 140, 40))


M.face32 = face32_new5


# ------------------------------------------------------------------ Izuku Midoriya (Deku) — My Hero Academia
DEKU_HAIR = (36, 104, 72)


@M.smooth_hair
def deku_hair(m, col):
    shell(m, col, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(col)
    # a bushy, messy mop of curls: short spikes in every direction
    for x, z, dx, dz, L in ((0, -2.0, 0.0, -0.5, 4.2), (2.4, -1.6, 0.6, -0.4, 4.0), (-2.4, -1.6, -0.6, -0.4, 4.0), (3.4, 0.6, 1.0, 0.1, 3.8),
                            (-3.4, 0.6, -1.0, 0.1, 3.8), (1.4, 1.2, 0.4, 0.4, 4.2), (-1.4, 1.2, -0.4, 0.4, 4.2), (0, 3.0, 0, 1.0, 4.0),
                            (2.6, 2.8, 0.7, 0.8, 3.6), (-2.6, 2.8, -0.7, 0.8, 3.6)):
        m.strand([x, 32.0, z], [dx, 0.9, dz], L, 3.2, hp, bone="hair", thick=0.85, bend=(dx * 0.1, -0.12, dz * 0.1))
    for x, tilt in ((-2.6, -0.35), (-0.9, -0.1), (0.9, 0.1), (2.6, 0.35)):  # curly bangs
        m.strand([x, 31.6, -4.1], [tilt, -0.7, -0.5], 2.8, 2.4, hp, bone="hair", thick=0.8, bend=(0, 0.2, -0.1))
    for s_ in (1, -1):
        m.strand([s_ * 4.1, 30.0, -0.6], [s_ * 0.5, -0.6, 0.1], 3.0, 2.2, hp, bone="hair", thick=0.7)


def deku(m, form):
    """Deku's hero costume (the green jumpsuit with dark accents, red boots, white gloves, the mouthguard round his
    neck). Full Cowl: green lightning crackles over him. Dark Deku: the torn, dirty dark cloak and mask of his
    vigilante days."""
    dark_form = form == "dark"
    cowl = form in ("cowl20", "cowl45")
    key = "deku_dark" if dark_form else ("deku_cowl" if cowl else "deku")
    head = head_paint(DEKU_HAIR, (40, 150, 90), True, key)
    suit, accent = ((40, 60, 52) if dark_form else (46, 120, 78)), (26, 30, 32)
    bolt = (120, 255, 150)

    def suit_lines(face, px, w, h, base):  # the black lines down the jumpsuit (and the green lightning in Full Cowl)
        for y in range(h):
            for x in (int(w * 0.25), int(w * 0.75)):
                if face in ("north", "south"):
                    _put(px, w, h, x, y, accent)
        # Full Cowl's green lightning is a moving effect round him in the game, not dots painted on the suit
    torso = layered(suit, [suit_lines, region((0, 0, 1, 0.1), accent)])
    arm = layered(suit, [suit_lines, region((0, 0.7, 1, 1), (238, 238, 232) if not dark_form else (60, 62, 60)), region((0, 0.7, 1, 0.74), (200, 40, 40))])
    leg = layered(suit, [suit_lines, region((0, 0.66, 1, 1), (210, 40, 40)), region((0, 0.92, 1, 1), (40, 30, 30)),
                         region((0.15, 0.72, 0.85, 0.8), (240, 240, 236), faces=("north",))])  # chunky red boots, white straps
    base_body(m, torso, arm, leg, head)
    m.box("body", [-2.4, 22.4, -2.6], [4.8, 1.6, 5.2], solid((236, 236, 228)))  # the mouthguard pulled down round his neck
    m.box("body", [-4.3, 11.6, -2.3], [8.6, 1.2, 4.6], solid(accent))            # utility belt
    for x0 in (-3.8, 2.4):
        m.box("body", [x0, 11.0, -2.5], [1.4, 1.8, 1.2], solid((60, 64, 62)))
    both_legs(m, [0.2, 5.6, -2.5], [3.6, 1.4, 0.6], solid((40, 44, 42)))      # knee pads
    both_arms(m, [4.1, 15.4, -2.2], [3.8, 0.8, 4.4], solid((200, 40, 40)))    # red glove cuffs
    if dark_form:  # the ragged dark cloak and hood of his vigilante days
        cloak = (34, 36, 34)

        def rags(face, px, w, h, base):
            for x in range(w):
                for y in range(int(h * 0.88) + (x * 7 % 3), h):
                    px[x, y] = (0, 0, 0, 0)
        m.box("body", [-4.8, 4.0, 2.2], [9.6, 20.4, 0.6], layered(cloak, [rags]))
        m.box("body", [-5.0, 21.0, -2.8], [10.0, 3.2, 5.6], solid(cloak))
        both_arms(m, [3.9, 18.0, -2.4], [4.3, 6.2, 4.8], layered(cloak, [rags]))
        # Blackwhip: black tendrils of energy writhing up out of his back, edged in green
        whip, glow = SC.swatch((16, 22, 18), 225), SC.swatch((90, 220, 120), 200)
        for k, (sx, up) in enumerate(((1, 1.0), (-1, 1.0), (1, 0.3), (-1, 0.3))):
            pts = SC.curve_tube(m, "body", [[sx * 1.2, 21 - k, 2.6], [sx * 4.5, 23 + up * 3, 5.5], [sx * 8.5, 22 + up * 5, 6.5], [sx * 11, 18 + up * 6, 4.5]],
                                0.7, 0.25, [whip, whip, glow], n=2)
            SC.blade(m, "body", pts[-1], [sx * 0.6, -0.4, -0.5], 1.6, 0.8, 0.4, glow)
    deku_hair(m, DEKU_HAIR)


# ------------------------------------------------------------------ Killua Zoldyck — Hunter x Hunter
KIL_HAIR = (232, 234, 242)


@M.smooth_hair
def killua_hair(m, col, god):
    shell(m, col, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(col)
    # fluffy silver hair bursting out in every direction
    up = 1.0 if god else 0.8
    for k in range(10):
        a = 2 * math.pi * k / 10
        dx, dz = math.sin(a), -math.cos(a)
        m.strand([dx * 2.8, 31.8, dz * 2.8], [dx * 0.95, up * 0.6, dz * 0.95], 4.4 if not god else 5.2, 3.2, hp, bone="hair", thick=0.8)
    for x, z in ((0, 0), (1.6, 1.2), (-1.6, 1.2), (0, -1.6)):
        m.strand([x, 32.2, z], [x * 0.3, 1, z * 0.3], 4.6 if not god else 5.6, 3.2, hp, bone="hair", thick=0.8)
    for x, tilt in ((-2.6, -0.3), (-0.8, -0.05), (1.0, 0.1), (2.8, 0.35)):
        m.strand([x, 31.6, -4.1], [tilt, -0.7, -0.5], 2.6, 2.2, hp, bone="hair", thick=0.75)


def killua(m, form):
    """Killua: a white short-sleeved top over a navy long-sleeved shirt, white shorts, purple boots, pale skin,
    fluffy silver hair. Godspeed: the hair crackles with blue lightning and the eyes glow."""
    god = form == "godspeed"
    head = head_paint(KIL_HAIR if not god else (214, 236, 255), (60, 130, 220), True, "killua_god" if god else "killua")
    navy, white = (40, 44, 92), (240, 240, 236)

    def zig(face, px, w, h, base):  # Godspeed: lightning zigzags over the body
        if god:
            for i in range(0, h, 2):
                _put(px, w, h, int(w * 0.5 + (i % 6 - 3) * w * 0.08), i, (170, 230, 255))
    torso = layered(white, [zig, region((0, 0, 1, 0.08), navy)])
    arm = layered(navy, [zig, region((0, 0, 1, 0.28), white), region((0, 0.86, 1, 1), SKIN)])
    leg = layered(white, [region((0, 0.5, 1, 0.82), SKIN), region((0, 0.82, 1, 1), (110, 70, 160))])
    base_body(m, torso, arm, leg, head)
    m.box("body", [-4.3, 11.4, -2.3], [8.6, 1.0, 4.6], solid((60, 60, 70)))  # belt
    claw = SC.swatch((236, 238, 246))
    for s_, arm_ in ((1, "rightArm"), (-1, "leftArm")):  # the assassin's hand: nails grown into blades
        for k in range(4):
            SC.blade(m, arm_, [s_ * (4.6 + k * 0.9), 12.2, -1.6], [0, -1, -0.35], 1.8, 0.45, 0.3, claw)
    killua_hair(m, (214, 236, 255) if god else KIL_HAIR, god)
    if god:  # little arcs of electricity standing off his hair and arms
        bolt = SC.swatch((170, 230, 255))
        for k in range(6):
            a = 2 * math.pi * k / 6
            SC.blade(m, "hair", [math.sin(a) * 4.2, 33.5, -math.cos(a) * 4.2], [math.sin(a) * 0.6, 1, -math.cos(a) * 0.6], 2.4, 0.5, 0.3, bolt)


# ------------------------------------------------------------------ Denji — Chainsaw Man
DEN_HAIR = (232, 200, 96)


def chainsaw_blade(m, bone, base, d, length, width, metal, teeth):
    """A chainsaw bar sticking out of the body: the steel bar with a row of teeth along its edge."""
    SC.blade(m, bone, base, d, length, width, 0.7, metal, taper=False, width_dir=[1, 0, 0] if abs(d[0]) < 0.5 else [0, 0, 1])
    dn = SC.norm(d)
    for i in range(int(length / 1.2)):
        p = [base[j] + dn[j] * (0.8 + i * 1.2) for j in range(3)]
        SC.obox(m, bone, [p[0], p[1], p[2]], [0.5, 0.5, 0.5], teeth, d, 45)


def denji(m, form):
    """Denji: devil hunter uniform (white shirt, black tie, black trousers), the pull-cord hanging from his chest,
    messy blond hair. Chainsaw Man: his head becomes the devil's (an orange head, a chainsaw bar out of his
    forehead, a jagged grin) and chainsaws burst from both forearms. The true black Chainsaw Man is darker still."""
    saw = form in ("chainsaw", "black")
    black = form == "black"
    key = "chainsaw_black" if black else ("chainsaw" if saw else "denji")
    head = head_paint(DEN_HAIR, (70, 60, 50), True, key)
    shirt, tie, pants = (238, 238, 232), (24, 24, 28), (30, 30, 36)
    if black:
        shirt = (52, 50, 56)

    def tie_cord(face, px, w, h, base):
        if face == "north":
            for y in range(int(h * 0.05), int(h * 0.62)):
                for x in range(int(w * 0.44), int(w * 0.56)):
                    _put(px, w, h, x, y, tie)
            for y in range(int(h * 0.45), int(h * 0.9)):  # the starter cord hanging from his chest
                _put(px, w, h, int(w * 0.62), y, (220, 120, 40))
    torso = layered(shirt, [tie_cord, region((0, 0.92, 1, 1), pants)])
    arm = layered(shirt, [region((0, 0.86, 1, 1), SKIN if not black else (60, 56, 60))])
    leg = layered(pants, [region((0, 0.9, 1, 1), (20, 20, 22))])
    base_body(m, torso, arm, leg, head)
    m.box("body", [0.6, 15.2, -2.6], [1.2, 1.4, 0.6], solid((220, 120, 40)))  # the cord's handle
    metal, teeth = SC.swatch((196, 200, 208)), SC.swatch((90, 92, 100))
    if black:
        metal, teeth = SC.swatch((70, 70, 78)), SC.swatch((30, 30, 34))
    if saw:  # the devil's head all round (sides, back, top), not only the face
        hc = (226, 96, 50) if not black else (40, 38, 42)
        hd = dark(hc, 0.78)

        def grain(face, px, w, h, b):
            for y in range(h):
                for x in range(w):
                    if (x * 3 + y * 5) % 13 == 0:
                        _put(px, w, h, x, y, hd)
        head_skin = layered(hc, [grain])
        m.cubes = [c for c in m.cubes if not (c["bone"] == "head" and c["size"] == [0.75, 2.25, 1.5])]  # no human ears on the devil's head
        m.box("head", [-4.25, 24.0, 3.9], [8.5, 8.25, 0.35], head_skin)          # back
        m.box("head", [-4.25, 32.0, -4.25], [8.5, 0.35, 8.5], head_skin)         # top
        for x0 in (3.9, -4.25):
            m.box("head", [x0, 24.0, -4.25], [0.35, 8.25, 8.5], head_skin)       # sides
        # the chainsaw bar out of his forehead and one out of each forearm
        chainsaw_blade(m, "head", [0, 30.0, -4.2], [0, 0.55, -1], 9.0, 2.0, metal, teeth)
        SC.box_at(m, "head", [0, 30.0, -4.4], [2.6, 2.4, 1.2], SC.swatch((60, 60, 66)))
        for s_, arm_ in ((1, "rightArm"), (-1, "leftArm")):
            chainsaw_blade(m, arm_, [s_ * 6.0, 13.0, -2.2], [0, -0.35, -1], 10.0, 1.8, metal, teeth)
            SC.box_at(m, arm_, [s_ * 6.0, 13.6, -2.2], [2.2, 2.2, 1.4], SC.swatch((60, 60, 66)))
        if black:  # the true form: ragged scarf of guts and a darker body
            SC.curve_tube(m, "body", [[0, 23.5, 2.6], [1.5, 20, 4.8], [3, 14, 5.5]], 1.2, 0.5, SC.swatch((140, 30, 36)), n=2, flat=0.4, width=[1, 0, 0])
    else:
        shell(m, DEN_HAIR, hairline=30.6, sideburn=False, teeth=0.8)
        hp = M.hair_paint(DEN_HAIR)
        for x, z, lean in ((0, -1.6, 0), (2.4, -1.0, 0.6), (-2.4, -1.0, -0.6), (3.2, 1.4, 0.9), (-3.2, 1.4, -0.9), (1.2, 2.6, 0.3), (-1.2, 2.6, -0.3)):
            m.strand([x, 32.0, z], [lean, 0.8, z * 0.3], 3.6, 2.8, hp, bone="hair", segs=3, thick=0.75, bend=(x * 0.05, -0.1, 0))
        for x, tilt in ((-2.6, -0.3), (-0.8, -0.05), (1.0, 0.1), (2.8, 0.35)):
            m.strand([x, 31.6, -4.1], [tilt, -0.7, -0.5], 2.8, 2.2, hp, bone="hair", segs=3, thick=0.7)


# ------------------------------------------------------------------ Kyojuro Rengoku — Demon Slayer
REN_HAIR, REN_TIP = (250, 200, 50), (220, 60, 30)


@M.smooth_hair
def rengoku_hair(m):
    """A flaming mane: yellow spikes flaring up and back, each tipped in red — and two long bangs."""
    shell(m, REN_HAIR, hairline=30.8, sideburn=False, teeth=0.8)
    hp, tp = M.hair_paint(REN_HAIR), M.hair_paint(REN_TIP)
    spikes = [(0, -1.8, 0.0, 0.9, -0.2, 5.0), (2.4, -1.2, 0.6, 0.9, 0.0, 5.0), (-2.4, -1.2, -0.6, 0.9, 0.0, 5.0),
              (3.4, 1.0, 1.0, 0.7, 0.4, 5.4), (-3.4, 1.0, -1.0, 0.7, 0.4, 5.4), (1.4, 1.8, 0.4, 0.8, 0.8, 5.6),
              (-1.4, 1.8, -0.4, 0.8, 0.8, 5.6), (0, 3.2, 0, 0.4, 1.0, 6.0), (2.6, 3.0, 0.8, 0.3, 1.0, 5.4), (-2.6, 3.0, -0.8, 0.3, 1.0, 5.4)]
    spikes = [(x, z, dx, dy, dz, L * 1.2) for x, z, dx, dy, dz, L in spikes]  # a bigger, longer mane
    for x, z, dx, dy, dz, L in spikes:
        m.strand([x, 32.0, z], [dx, dy, dz], L, 3.4, hp, bone="hair", thick=0.8)
        n = SC.norm([dx, dy, dz])
        tip = [x + n[0] * L * 0.78, 32.0 + n[1] * L * 0.78, z + n[2] * L * 0.78]
        m.strand(tip, [dx, dy, dz], L * 0.45, 1.8, tp, bone="hair", segs=3, thick=0.7)  # red flame tips
    for s_ in (1, -1):  # the two long bangs framing his face
        m.strand([s_ * 2.0, 31.8, -4.2], [s_ * 0.3, -1, -0.15], 5.0, 2.2, hp, bone="hair", thick=0.7)
        m.strand([s_ * 4.1, 30.6, -1.0], [s_ * 0.3, -1, 0.2], 7.0, 2.6, hp, bone="hair", thick=0.7)
    for x in (-3.0, -1.0, 1.0, 3.0):  # long hair falling down his back to the shoulder blades, red at the ends
        L = 9.5 - abs(x) * 0.5
        d = [x * 0.1, -1, 0.42]
        m.strand([x, 29.6, 4.0], d, L, 3.2, hp, bone="hair", thick=0.8)
        nn = SC.norm(d)
        m.strand([x + nn[0] * L * 0.8, 29.6 + nn[1] * L * 0.8, 4.0 + nn[2] * L * 0.8], d, L * 0.35, 1.8, tp, bone="hair", segs=3, thick=0.7)


def rengoku(m, form):
    """The Flame Hashira: black Demon Slayer uniform, a white haori whose hem burns with orange and red flames, a
    flame-guard sword, gold eyes and forked brows. Ninth Form: flames lick round him."""
    ninth = form == "ninth"
    head = head_paint(REN_HAIR, (250, 190, 40), True, "rengoku_ninth" if ninth else "rengoku")
    uni = (30, 30, 40)
    buttons = lambda f, px, w, h, b: [_put(px, w, h, w // 2, y, (230, 200, 120)) for y in range(int(h * 0.1), int(h * 0.7), max(2, h // 6))] if f == "north" else None
    base_body(m, layered(uni, [buttons]), arm_paint(uni, sleeve_to=0.88),
              layered(uni, [region((0, 0.5, 1, 0.84), (236, 234, 228)), region((0, 0.84, 1, 1), (40, 34, 30))]), head)
    m.box("body", [-4.4, 11.6, -2.5], [8.8, 1.4, 5.0], solid((240, 240, 236)))  # white belt
    m.box("body", [-2.2, 22.6, -2.4], [4.4, 1.8, 4.8], solid(uni))

    def flames_hem(face, px, w, h, base):  # the haori's flame pattern: orange flames with red tips rising from the hem
        for x in range(w):
            top = int(h * (0.55 + 0.12 * math.sin(x * 1.3)))
            for y in range(top, h):
                _put(px, w, h, x, y, (240, 120, 30) if y > top + 2 else (210, 50, 30))
    haori = layered((244, 242, 236), [flames_hem])
    m.box("body", [-4.6, 4.5, 2.1], [9.2, 19.7, 0.5], haori)
    for x0 in (-4.6, 2.2):
        m.box("body", [x0, 4.5, -2.6], [2.4, 19.7, 0.5], haori)
    both_arms(m, [3.5, 13.6, -2.7], [5.0, 10.6, 5.4], haori)
    flame_st = dict(NICHIRIN, wrap=(30, 30, 40), diamond=(220, 60, 30), metal=(214, 92, 36), blade=(220, 100, 40), edge=(255, 200, 120))
    M.katana2(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 14, flame_st)
    M.sheath(m, (-4.6, 12.4, -1.6), (0.05, -0.55, 1), 12, flame_st)
    rengoku_hair(m)
    if ninth:  # flames rising round his shoulders
        fl = SC.swatch((255, 140, 40), 210)
        for k in range(6):
            a = math.pi * (0.1 + 0.8 * k / 5)
            SC.blade(m, "body", [math.cos(a) * 5.5, 20, math.sin(a) * 3 + 2], [math.cos(a) * 0.4, 1, 0.3], 4.5, 1.8, 0.6, fl)


# ------------------------------------------------------------------ Portgas D. Ace — One Piece
ACE_HAIR = (26, 24, 30)


def ace(m, form):
    """Fire Fist Ace: bare-chested and freckled, black shorts, an orange belt with his 'A' buckle and a dagger,
    black boots, the red bead necklace, the ASCE tattoo on his left arm, Whitebeard's mark on his back and the
    orange cowboy hat with its two faces. Flame Emperor: his arms and shoulders become living fire."""
    flame = form == "flame"
    head = head_paint(ACE_HAIR, (40, 30, 30), True, "ace_flame" if flame else "ace")

    def back_mark(face, px, w, h, base):  # Whitebeard's jolly roger, purple, across his back
        if face == "south":
            cx, cy, r = w / 2, h * 0.4, min(w, h) * 0.28
            for y in range(h):
                for x in range(w):
                    d = math.hypot(x - cx, y - cy)
                    if abs(d - r) < 0.9 or (abs(x - cx) - abs(y - cy) < 0.6 and abs(x - cx) - abs(y - cy) > -0.6 and d > r * 1.1 and d < r * 1.8):
                        _put(px, w, h, x, y, (110, 50, 140))
                    elif d < r - 0.9:
                        _put(px, w, h, x, y, (150, 90, 175))  # the skull, a lighter purple
            # the crescent moustache: a wide bow curling up at both ends, under the eyes
            for x in range(w):
                dx = (x - cx) / (r * 1.25)
                if abs(dx) <= 1:
                    yy = cy + r * 0.25 - r * 0.45 * dx * dx
                    for t in (0, 1):
                        _put(px, w, h, x, int(round(yy)) + t, (70, 25, 95))
            for ex in (-1, 1):  # the two eye holes
                _put(px, w, h, int(cx + ex * r * 0.4), int(cy - r * 0.3), (70, 25, 95))
    def pecs(face, px, w, h, base):
        if face == "north":
            for x in range(int(w * 0.2), int(w * 0.8)):
                _put(px, w, h, x, int(h * 0.35), dark(SKIN, 0.82))
            for y in range(int(h * 0.4), int(h * 0.85)):
                _put(px, w, h, w // 2, y, dark(SKIN, 0.84))
    torso = layered(SKIN, [pecs, back_mark, region((0, 0.86, 1, 1), (40, 36, 40))])

    def asce(face, px, w, h, base):  # A S C E down his left upper arm (the S crossed out)
        if face == "west":
            for i, y in enumerate(range(int(h * 0.12), int(h * 0.5), max(2, int(h * 0.09)))):
                for x in range(int(w * 0.35), int(w * 0.65)):
                    _put(px, w, h, x, y, (40, 50, 110))
            _put(px, w, h, int(w * 0.3), int(h * 0.22), (180, 30, 30)); _put(px, w, h, int(w * 0.7), int(h * 0.2), (180, 30, 30))
    arm = layered(SKIN, [asce] + ([region((0, 0.5, 1, 0.8), (255, 170, 60)), region((0, 0.8, 1, 1), (255, 220, 120))] if flame else []))  # Flame Emperor: forearms and hands burning bright
    leg = layered((26, 26, 30), [region((0, 0.6, 1, 0.68), (40, 40, 46)), region((0, 0.68, 1, 1), (20, 20, 24))])
    base_body(m, torso, arm, leg, head)
    m.box("body", [-4.4, 11.4, -2.4], [8.8, 1.6, 4.8], layered((236, 140, 40), [region((0.4, 0.1, 0.6, 0.9), (250, 210, 80), faces=("north",))]))  # belt + A buckle
    m.box("body", [3.6, 9.0, -1.2], [1.0, 3.6, 1.2], solid((90, 60, 40)))  # dagger at his hip
    for i in range(10):  # the red bead necklace
        a = math.pi * (0.15 + 0.7 * i / 9)
        SC.box_at(m, "body", [math.cos(a) * 3.6, 22.2 - math.sin(a) * 2.4, -2.3], [0.9, 0.9, 0.9], SC.swatch((200, 30, 30)))
    # hair: black, wavy, falling to his neck
    shell(m, ACE_HAIR, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(ACE_HAIR)
    for x, tilt in ((-2.8, -0.35), (-1.0, -0.1), (0.8, 0.1), (2.6, 0.35)):
        m.strand([x, 31.6, -4.1], [tilt, -0.8, -0.4], 3.2, 2.4, hp, bone="hair", segs=3, thick=0.7)
    for s_ in (1, -1):
        m.strand([s_ * 4.1, 30.4, -0.6], [s_ * 0.3, -1, 0.2], 4.2, 2.6, hp, bone="hair", segs=3, thick=0.7)
        m.strand([s_ * 2.4, 30.4, 4.2], [s_ * 0.3, -1, 0.5], 4.4, 2.8, hp, bone="hair", segs=3, thick=0.7)
    # the orange cowboy hat: crown (one smiling face, one sad face on the front), red band, wide brim
    hat_c = (236, 130, 40)

    def faces(face, px, w, h, base):
        if face == "north":
            for cx, smile in ((w * 0.32, True), (w * 0.68, False)):
                _put(px, w, h, int(cx - 1), int(h * 0.3), (30, 30, 30)); _put(px, w, h, int(cx + 1), int(h * 0.3), (30, 30, 30))
                for dx in (-1, 0, 1):
                    _put(px, w, h, int(cx + dx), int(h * (0.5 if smile else 0.45)) + (0 if dx == 0 else (-1 if smile else 1)), (30, 30, 30))
    m.box("hat", [-3.6, 32.0, -3.6], [7.2, 3.6, 7.2], layered(hat_c, [faces, region((0, 0.7, 1, 0.95), (200, 50, 40))]))
    m.box("hat", [-6.4, 31.6, -6.4], [12.8, 0.6, 12.8], solid(hat_c))
    for s_ in (1, -1):  # the upturned brim edges
        m.box("hat", [s_ * 6.4 - (0.6 if s_ > 0 else 0), 31.8, -6.4], [0.6, 1.2, 12.8], solid(hat_c))
    if flame:  # living fire pouring off his shoulders, forearms and fists
        fl, fl2 = SC.swatch((255, 140, 40), 215), SC.swatch((255, 210, 90), 200)
        for s_, arm_ in ((1, "rightArm"), (-1, "leftArm")):
            for k in range(3):                                              # shoulders
                SC.blade(m, arm_, [s_ * (5.0 + k * 1.2), 24.0, -1.2 + k * 1.2], [s_ * 0.45, 1, 0.15 * (k - 1)], 5.5 - k, 2.4, 0.7, fl if k % 2 == 0 else fl2)
            for k in range(4):                                              # forearms and fists, flames streaming back
                SC.blade(m, arm_, [s_ * (8.2 if k % 2 else 3.8), 16 - k * 1.2, -0.5 + k * 0.6], [s_ * 0.7, 0.6, 0.3], 3.6, 1.8, 0.6, fl2 if k % 2 else fl)
        for k in range(4):                                                  # a crown of flame along his back
            SC.blade(m, "body", [-3 + k * 2, 23.5, 2.2], [(k - 1.5) * 0.2, 1, 0.5], 4.5, 2.0, 0.6, fl)


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
    "itachi": ["sharingan", "ms", "susanoo"],
    "kakashi": ["base", "sharingan", "dms"],
    "deku": ["cowl20", "cowl45", "dark"],
    "killua": ["base", "godspeed"],
    "denji": ["human", "chainsaw", "black"],
    "rengoku": ["flame", "ninth"],
    "ace": ["base", "flame"],
}


def _scaled_paint(paint, size):
    """Paint a face at its ORIGINAL size, then enlarge the finished picture — drawing pixel by pixel straight onto the
    enlarged face left unpainted rows and columns (a grid of squares across the kids' faces)."""
    if getattr(paint, "swatch", None):
        return paint

    def p(face, img):
        w, h = img.size
        k = 1.15
        ow, oh = max(1, round(w / k)), max(1, round(h / k))
        tmp = M.Image.new("RGBA", (ow, oh), (0, 0, 0, 0))
        paint(face, tmp)
        img.paste(tmp.resize((w, h), M.Image.NEAREST), (0, 0))
    return p


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
    elif char == "itachi":
        itachi(m, "ms" if form == "susanoo" else form)
    elif char == "kakashi":
        kakashi(m, form)
    elif char == "deku":
        deku(m, form)
    elif char == "killua":
        killua(m, form)
    elif char == "denji":
        denji(m, form)
    elif char == "rengoku":
        rengoku(m, form)
    elif char == "ace":
        ace(m, form)
    if char in ("naruto_kid", "sasuke_kid"):  # kid proportions: a bigger head on the small body
        f, P = 1.15, (0.0, 24.0, 0.0)
        for c in m.cubes:
            if c["bone"] in ("head", "hair", "hat", "shroudHead", "jaw"):
                c["paint"] = _scaled_paint(c["paint"], c["size"])
                c["frm"] = [P[i] + (c["frm"][i] - P[i]) * f for i in range(3)]
                c["size"] = [round(v * f * 4) / 4 for v in c["size"]]
                if c["pivot"]:
                    c["pivot"] = [round(P[i] + (c["pivot"][i] - P[i]) * f, 3) for i in range(3)]
    return m


# ==================================================================================
# 1.19: Gohan, Bakugo, Gon, Akaza, Megumi
# ==================================================================================
M.FACE32.update({
    "gohan": dict(eye="anime", brow="angled", mouth="neutral", marks=["glasses"]),
    "gohan_ssj": dict(eye="narrow", brow="angled", mouth="neutral", marks=[]),
    "gohan_ssj2": dict(eye="narrow", brow="sharp", mouth="clench", marks=[]),
    "gohan_ult": dict(eye="narrow", brow="sharp", mouth="neutral", marks=[]),
    "gohan_beast": dict(eye="narrow", brow="sharp", mouth="clench", marks=["beast_eyes"]),
    "bakugo": dict(eye="narrow", brow="sharp", mouth="big_grin", marks=["bakugo_mask"]),
    "bakugo_cluster": dict(eye="narrow", brow="sharp", mouth="clench", marks=["bakugo_mask", "scorch"]),
    "gon": dict(eye="round", brow="angled", mouth="smile", marks=[]),
    "gon_jaja": dict(eye="round", brow="sharp", mouth="clench", marks=[]),
    "gon_adult": dict(eye="anime", brow="sharp", mouth="neutral", marks=[]),               # settled: his eyes clear and sharp
    "gon_vow": dict(eye="round", brow="sharp", mouth="none", marks=["adult_eyes"]),        # mid-transformation: empty white eyes
    "gon_dark": dict(eye="round", brow="sharp", mouth="none", marks=["hidden_eyes"]),
    "akaza": dict(eye="narrow", brow="none", mouth="smirk", marks=["akaza_lines", "akaza_eyes"]),
    "akaza_compass": dict(eye="narrow", brow="none", mouth="clench", marks=["akaza_lines", "akaza_eyes"]),
    "megumi": dict(eye="narrow", brow="fine", mouth="neutral", marks=[]),
    "megumi_shadow": dict(eye="narrow", brow="sharp", mouth="neutral", marks=["shadow_eyes"]),
})
_face32_prev4 = M.face32


def face32_new19(px, W, H, spec, hair, iris, skin):
    _face32_prev4(px, W, H, spec, hair, iris, skin)
    marks = spec.get("marks", [])
    k = W / 32.0
    open_eyes = M.EXPR not in ("blink", "hurt")

    def put(x, y, c):
        for dx in range(max(1, int((x + 1) * k) - int(x * k))):
            for dy in range(max(1, int((y + 1) * k) - int(y * k))):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    if "glasses" in marks:  # Gohan's round-ish glasses (base form only)
        fr = (40, 40, 48)
        for cx in (10, 21):
            for x in range(cx - 3, cx + 4):
                put(x, 16, fr); put(x, 21, fr)
            for y in range(16, 22):
                put(cx - 3, y, fr); put(cx + 3, y, fr)
        for x in (14, 15, 16, 17):
            put(x, 17, fr)
    if "beast_eyes" in marks and open_eyes:  # Beast: piercing red eyes
        for cx in (10, 21):
            for x in (cx, cx + 1):
                put(x, 18, (230, 30, 40)); put(x, 19, (170, 20, 30))
    if "bakugo_mask" in marks:  # the black eye mask with orange edges, sweeping out to the sides
        for x in list(range(3, 15)) + list(range(17, 29)):
            put(x, 15, (240, 130, 30))
            for y in (16, 21):
                put(x, y, (24, 24, 28))
        for y in range(16, 22):
            for x in (3, 4, 5, 26, 27, 28):
                put(x, y, (24, 24, 28))
        if open_eyes:
            for cx in (10, 21):
                put(cx, 18, (220, 30, 30)); put(cx + 1, 18, (220, 30, 30))
    if "scorch" in marks:
        for x, y in ((6, 25), (7, 26), (24, 24), (25, 25), (23, 26)):
            put(x, y, (70, 50, 46))
    if "adult_shadow" in marks:  # a dark, emotionless shadow across the eyes
        for x in range(4, 28):
            put(x, 15, (40, 30, 30))
    if "hidden_eyes" in marks:  # the Vow: his eyes vanish into a band of shadow
        for y in range(13, 23):
            for x in range(3, 29):
                put(x, y, (26, 26, 30) if 14 <= y <= 21 else (60, 60, 64))
    if "adult_eyes" in marks:  # the Vow: blank, empty WHITE round eyes with a solid black rim, no pupils
        ring = ["..####..", ".#WWWW#.", "#WWWWWW#", "#WWWWWW#", "#WWWWWW#", "#WWWWWW#", ".#WWWW#.", "..####.."]
        for x in range(5, 27):
            put(x, 13, (40, 30, 34))                       # the heavy shadow line over the eyes
        if open_eyes:
            for y in range(14, 23):                        # clear the base eye and brow tails under the rings
                for x in range(5, 16):
                    put(x, y, tuple(skin)); put(31 - x, y, tuple(skin))
            for r, row in enumerate(ring):                 # rows 14-21; left ring x7-14, right ring x17-24
                for c, ch in enumerate(row):
                    if ch != ".":
                        col = (250, 250, 250) if ch == "W" else (18, 16, 20)
                        put(7 + c, 14 + r, col); put(24 - c, 14 + r, col)
    if "akaza_lines" in marks:  # the dark blue tattoo lines across his face
        ln = (40, 60, 150)
        for x in range(2, 30):
            if x not in (14, 15, 16, 17):
                put(x, 13, ln)
        for y in range(20, 30):  # down the cheeks from the corners of the eyes
            put(5, y, ln); put(26, y, ln)
        for x in (6, 7, 24, 25):
            put(x, 25, ln)
        for x in (6, 7, 8, 23, 24, 25):  # flicks along the lower lids
            put(x, 20, ln)
        for x in range(13, 19):  # the band across his chin
            put(x, 30, ln)
    if "akaza_eyes" in marks and open_eyes:  # yellow irises on dark blue sclera
        for cx in (10, 21):
            for x in range(cx - 2, cx + 3):
                for y in (17, 18, 19):
                    put(x, y, (40, 70, 170))
            put(cx, 18, (250, 220, 70)); put(cx + 1, 18, (250, 220, 70)); put(cx, 17, (250, 220, 70))
    if "shadow_eyes" in marks and open_eyes:
        for cx in (10, 21):
            put(cx, 18, (40, 120, 120)); put(cx + 1, 18, (40, 120, 120))


M.face32 = face32_new19


def spiky_crown(m, col, up=1.0, n=9, L=5.0, spread=0.8, hairline=30.6, bangs=None, back=True):
    """Spiky anime hair standing up: a shell plus a crown of spikes, optional bangs over the forehead."""
    shell(m, col, hairline=hairline, sideburn=False, teeth=0.8)
    hp = M.hair_paint(col)
    for k in range(n):
        a = 2 * math.pi * k / n
        dx, dz = math.sin(a), -math.cos(a)
        if not back and dz > 0.5:
            continue
        m.strand([dx * 2.6, 31.8, dz * 2.6], [dx * spread, up, dz * spread], L, 3.2, hp, bone="hair", thick=0.8)
    for x, z in ((0, 0), (1.5, 1.4), (-1.5, 1.4)):
        m.strand([x, 32.2, z], [x * 0.2, 1, z * 0.25], L * 1.05, 3.2, hp, bone="hair", thick=0.8)
    for x, tilt, ln in (bangs or ()):
        m.strand([x, 31.6, -4.1], [tilt, -0.7, -0.5], ln, 2.2, hp, bone="hair", thick=0.75)


# ------------------------------------------------------------------ Son Gohan — Dragon Ball
GOHAN_BLACK, GOHAN_GOLD, GOHAN_BEAST = (24, 24, 34), (255, 214, 70), (226, 228, 240)


@M.smooth_hair
def gohan_hair(m, form):
    if form == "base":
        spiky_crown(m, GOHAN_BLACK, up=0.7, n=8, L=3.8, spread=0.9, bangs=((-1.2, -0.2, 2.6), (1.4, 0.25, 2.4)))
    elif form == "ssj":  # teen Super Saiyan: gold, spiky but lower than SSJ2, two bangs
        spiky_crown(m, GOHAN_GOLD, up=0.85, n=9, L=4.6, spread=0.75, bangs=((-1.0, -0.15, 3.0), (1.3, 0.2, 2.8)))
    elif form == "ssj2":  # gold, swept up, one bang hanging down
        spiky_crown(m, GOHAN_GOLD, up=1.0, n=9, L=5.4, spread=0.6, bangs=((0.6, 0.05, 3.6),))
    elif form == "ultimate":  # black, wild and spiky, a single bang
        spiky_crown(m, GOHAN_BLACK, up=0.95, n=10, L=5.0, spread=0.75, bangs=((0.6, 0.05, 3.4),))
    else:  # Beast: tall silver-white spikes swept up and back
        spiky_crown(m, GOHAN_BEAST, up=1.2, n=11, L=7.6, spread=0.55, bangs=((0.8, 0.05, 3.8),))
        hp = M.hair_paint(GOHAN_BEAST)
        for x in (-2.0, 0, 2.0):
            m.strand([x, 32.4, 2.6], [x * 0.1, 0.7, 1], 7.0, 3.0, hp, bone="hair", thick=0.8)


def gohan(m, form):
    """Gohan in Piccolo's colours: a purple gi with a red sash, blue wristbands, brown boots. Base: glasses.
    Super Saiyan 2: gold with sparks of lightning. Ultimate: black spiky hair. Beast: towering silver hair, red eyes."""
    key = {"base": "gohan", "ssj": "gohan_ssj", "ssj2": "gohan_ssj2", "ultimate": "gohan_ult", "beast": "gohan_beast"}[form]
    hair = {"base": GOHAN_BLACK, "ssj": GOHAN_GOLD, "ssj2": GOHAN_GOLD, "ultimate": GOHAN_BLACK, "beast": GOHAN_BEAST}[form]
    iris = {"base": (40, 40, 50), "ssj": (40, 160, 160), "ssj2": (40, 160, 160), "ultimate": (40, 40, 50), "beast": (220, 30, 40)}[form]
    head = head_paint(hair, iris, True, key)
    gi = (78, 50, 120)

    def collar(face, px, w, h, base):  # the gi's crossed front
        if face == "north":
            for y in range(int(h * 0.45)):
                _put(px, w, h, int(w * 0.5 - y * 0.6), y, dark(gi, 0.6)); _put(px, w, h, int(w * 0.5 + y * 0.6), y, dark(gi, 0.6))
    sparks = None  # SSJ2's lightning is an effect around his body (in the game), never dots on his clothes
    torso = layered(gi, [collar] + ([sparks] if sparks else []))
    arm = layered(gi, ([sparks] if sparks else []) + [region((0, 0.66, 1, 0.84), (40, 80, 200)), region((0, 0.84, 1, 1), SKIN)])
    leg = layered(gi, [region((0, 0.8, 1, 1), (110, 64, 40))])
    base_body(m, torso, arm, leg, head)
    m.box("body", [-4.4, 11.0, -2.5], [8.8, 2.0, 5.0], solid((200, 36, 36)))  # red sash
    m.box("body", [2.0, 6.5, -2.6], [1.6, 4.6, 0.6], solid((200, 36, 36)))    # the sash's hanging end
    gohan_hair(m, form)
    if form == "beast":  # a crackling white-purple aura of spikes round his shoulders
        au = SC.swatch((230, 210, 255), 170)
        for k in range(5):
            a = math.pi * (0.15 + 0.7 * k / 4)
            SC.blade(m, "body", [math.cos(a) * 5.2, 21, math.sin(a) * 2.5 + 2.4], [math.cos(a) * 0.3, 1, 0.25], 4.0, 1.4, 0.5, au)


# ------------------------------------------------------------------ Katsuki Bakugo — My Hero Academia
BAKU_HAIR = (236, 222, 170)


@M.smooth_hair
def bakugo_hair(m):
    # an explosion of ash-blond spikes in every direction
    shell(m, BAKU_HAIR, hairline=30.4, sideburn=False, teeth=0.8)
    hp = M.hair_paint(BAKU_HAIR)
    for k in range(12):
        a = 2 * math.pi * k / 12
        dx, dz = math.sin(a), -math.cos(a)
        m.strand([dx * 3.0, 31.0, dz * 3.0], [dx * 1.0, 0.5, dz * 1.0], 4.8, 3.0, hp, bone="hair", thick=0.8)
    for x, z in ((0, 0), (2, 1.5), (-2, 1.5), (0, -2), (2, -1.6), (-2, -1.6)):
        m.strand([x, 32.0, z], [x * 0.3, 1, z * 0.3], 4.6, 3.0, hp, bone="hair", thick=0.8)
    for x, tilt in ((-2.6, -0.4), (-0.6, -0.1), (1.2, 0.15), (2.8, 0.45)):
        m.strand([x, 31.4, -4.1], [tilt, -0.6, -0.6], 3.0, 2.2, hp, bone="hair", thick=0.75)


def bakugo(m, form):
    """Bakugo's hero costume: a black sleeveless top with an orange X across the chest, black trousers with orange
    knee pads, the huge grenade gauntlets, the black eye mask. Cluster: the costume scorched, his palms burning orange."""
    cluster = form == "cluster"
    head = head_paint(BAKU_HAIR, (220, 30, 30), True, "bakugo_cluster" if cluster else "bakugo")
    top, orange = (30, 30, 34), (240, 130, 30)

    def xmark(face, px, w, h, base):  # the orange X across his chest
        if face == "north":
            for y in range(int(h * 0.1), int(h * 0.75)):
                t = (y - h * 0.1) / (h * 0.65)
                for d in (0, 1):
                    _put(px, w, h, int(w * (0.15 + 0.7 * t)) + d, y, orange); _put(px, w, h, int(w * (0.85 - 0.7 * t)) + d, y, orange)
    def burns(face, px, w, h, base):
        if cluster:
            for x, y in ((0.2, 0.3), (0.7, 0.6), (0.4, 0.8)):
                _put(px, w, h, int(w * x), int(h * y), (90, 60, 50)); _put(px, w, h, int(w * x) + 1, int(h * y), (90, 60, 50))
    torso = layered(top, [xmark, burns])
    arm = layered(SKIN, [region((0, 0.0, 1, 0.12), top)])
    leg = layered((26, 26, 30), [region((0, 0.42, 1, 0.56), orange), region((0, 0.86, 1, 1), (20, 20, 24))])
    base_body(m, torso, arm, leg, head)
    m.box("body", [-4.4, 11.4, -2.5], [8.8, 1.4, 5.0], solid((80, 70, 60)))      # belt with grenade pouches
    for x0 in (-4.0, -1.0, 2.0):
        m.box("body", [x0, 10.6, -2.8], [1.8, 2.2, 0.8], solid((90, 110, 70)))
    m.box("body", [-4.2, 22.2, -2.6], [8.4, 1.6, 5.2], solid((50, 50, 56)))     # neck guard
    # the grenade gauntlets: big hand-grenade bracers with a pin ring
    glow = (255, 160, 50) if cluster else (240, 210, 70)
    for s_, arm_ in ((1, "rightArm"), (-1, "leftArm")):
        m.box(arm_, [s_ * 6.2 - 3.0, 12.0, -3.0], [6.0, 6.6, 6.0], layered((52, 52, 58), [region((0, 0.0, 1, 0.14), (30, 30, 34)), region((0, 0.86, 1, 1), (30, 30, 34)),
                                                                                       region((0, 0.42, 1, 0.56), (240, 130, 30)), lines((SIDES, [[(0.5, 0), (0.5, 0.4)]]), (80, 80, 88))]))
        m.box(arm_, [s_ * 6.2 - 0.8, 18.4, -0.8], [1.6, 1.2, 1.6], solid(glow))  # the pin
        m.box(arm_, [s_ * 6.2 - 2.4, 10.5, -2.4], [4.8, 1.6, 4.8], solid(SKIN))
    bakugo_hair(m)
    if cluster:  # explosions sparking from his palms
        ex = SC.swatch((255, 170, 60), 200)
        for s_, arm_ in ((1, "rightArm"), (-1, "leftArm")):
            for k in range(4):
                a = 2 * math.pi * k / 4
                SC.blade(m, arm_, [s_ * 6.2, 10.4, 0], [math.cos(a) * 0.8, -0.6, math.sin(a) * 0.8], 2.6, 1.2, 0.5, ex)


# ------------------------------------------------------------------ Gon Freecss — Hunter x Hunter
GON_HAIR = (24, 30, 26)


@M.smooth_hair
def gon_hair(m, adult):
    if not adult:  # spiky black hair all standing straight up, tinted green at the tips
        spiky_crown(m, GON_HAIR, up=1.4, n=10, L=6.2, spread=0.35, back=True)
        hp = M.hair_paint((30, 60, 40))
        for x in (-1.6, 0, 1.6):
            m.strand([x, 32.4, -1.2], [x * 0.1, 1, -0.1], 6.8, 2.8, hp, bone="hair", thick=0.8)
    else:  # Adult Gon: a huge mane of spiky hair falling past his waist
        spiky_crown(m, GON_HAIR, up=1.2, n=10, L=7.0, spread=0.45)
        long_hair(m, GON_HAIR, back_len=19, z=4.2, front=False)


def _greyed(paint, keep_white=False):
    """The Vow: everything about Gon drains to grey."""
    if getattr(paint, "swatch", None) or not callable(paint):
        return paint

    def p(face, img):
        paint(face, img)
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a:
                    if keep_white and face == "north" and min(r, g, b) >= 240:
                        continue                           # the Vow's empty eyes stay pure white
                    l = int((0.3 * r + 0.59 * g + 0.11 * b) * 0.78)
                    px[x, y] = (l, l, l + 4, a)
    return p


def gon(m, form):
    """Gon: the green jacket and shorts, white socks and boots, the fishing rod on his back. Jajanken: his fist blazes
    with yellow nen. Adult Gon: grown in an instant, his clothes torn to rags, a towering mane of hair, a dark aura."""
    if form == "dark":  # the Vow: already the grown body, but drained GREY, the eyes empty, black nen pouring off him
        M._GON_DARK = True
        try:
            gon(m, "adult")
        finally:
            M._GON_DARK = False
        for c in m.cubes:
            c["paint"] = _greyed(c["paint"], keep_white=c["bone"] == "head")
        return
    adult = form == "adult"
    jaja = form == "jajanken"
    key = "gon_adult" if adult else ("gon_jaja" if jaja else "gon")
    if adult and getattr(M, "_GON_DARK", False):
        key = "gon_vow"
    head = head_paint(GON_HAIR, (120, 70, 40), True, key)
    green = (50, 130, 70)
    if adult:
        def shreds(face, px, w, h, base):
            for x in range(w):
                for y in range(int(h * 0.15) + (x * 5 % 4), h):
                    px[x, y] = (0, 0, 0, 0)
        mus = dark(SKIN, 0.82)

        def abs_(face, px, w, h, base):  # a heavily muscled chest and stomach
            if face == "north":
                for x in range(w):
                    _put(px, w, h, x, int(h * 0.36), mus)
                for y in range(int(h * 0.36), h):
                    _put(px, w, h, w // 2, y, mus)
                for fy in (0.55, 0.72, 0.88):
                    for x in range(int(w * 0.25), int(w * 0.75)):
                        _put(px, w, h, x, int(h * fy), mus)
        torso = layered(SKIN, [abs_])
        arm = layered(SKIN, [lines((SIDES, [[(0.5, 0.2), (0.5, 0.45)]]), mus)])
        base_body(m, torso, arm, layered(green, [region((0, 0.5, 1, 1), SKIN)]), head)
        m.box("body", [-4.4, 10.6, -2.5], [8.8, 1.6, 5.0], layered(green, [shreds]))  # the torn waistband of his shorts
        skp = layered(SKIN, [])
        for s_ in (1, -1):  # broad shoulders and thick upper arms
            arm_ = "rightArm" if s_ > 0 else "leftArm"
            m.box(arm_, [s_ * 6.0 - 2.6, 18.5, -2.6], [5.2, 5.6, 5.2], layered(SKIN, [lines((SIDES, [[(0.5, 0.3), (0.5, 0.8)]]), mus)]))
        m.box("body", [-4.4, 18.6, -2.7], [8.8, 3.8, 0.6], layered(SKIN, [lines((("north",), [[(0.5, 0), (0.5, 1)], [(0, 0.95), (1, 0.95)]]), mus)]))  # pecs
        m.box("body", [-3.0, 23.0, -1.6], [6.0, 1.4, 4.4], skp)  # thick traps at the neck
        # (his ominous black aura is energy, not part of the body: the game draws it as black smoke pouring off him)
    else:
        torso = layered(green, [region((0.42, 0, 0.58, 1), (230, 120, 40), faces=("north",)), region((0, 0, 1, 0.08), (36, 80, 46))])
        arm = layered(green, [region((0, 0, 1, 0.12), (36, 80, 46)), region((0, 0.82, 1, 1), SKIN)])
        leg = layered(green, [region((0, 0.36, 1, 0.66), SKIN), region((0, 0.66, 1, 0.8), (240, 240, 236)), region((0, 0.8, 1, 1), (60, 120, 60))])
        base_body(m, torso, arm, leg, head)
        m.box("body", [-4.3, 11.4, -2.3], [8.6, 1.0, 4.6], solid((100, 70, 40)))
        m.strand([-2.5, 4, 2.6], [0.25, 1, 0.05], 22, 0.7, solid((160, 120, 70)), bone="body", segs=2)  # fishing rod
        if jaja:  # the Rock: a fist of blazing yellow nen
            nen = SC.swatch((255, 230, 90), 200)
            SC.blob(m, "rightArm", [6.2, 10.6, 0], [2.6, 2.6, 2.6], nen)
    gon_hair(m, adult)


# ------------------------------------------------------------------ Akaza — Demon Slayer (Upper Moon Three)
AKA_HAIR = (238, 140, 170)


@M.smooth_hair
def akaza_hair(m):
    spiky_crown(m, AKA_HAIR, up=0.6, n=10, L=3.6, spread=1.0, bangs=((-2.4, -0.3, 2.8), (-0.6, -0.05, 3.0), (1.2, 0.15, 2.8), (2.8, 0.4, 2.6)))


def compass_paint(face, img):
    """Akaza's Destructive Death: Compass Needle, seen from above: a light-blue snowflake of twelve needles,
    each with two pairs of branches, inside two thin rings."""
    if face != "up":
        return
    w, h = img.size
    px = img.load()
    cx, cy = (w - 1) / 2, (h - 1) / 2
    R = min(w, h) / 2 - 1
    ice, glow = (150, 226, 255, 255), (70, 150, 230, 255)
    def dot(x, y, c):  # a 2x2 stroke so the needles read from a distance
        x, y = int(round(x)), int(round(y))
        for dx in (0, 1):
            for dy in (0, 1):
                if 0 <= x + dx < w and 0 <= y + dy < h:
                    px[x + dx, y + dy] = c
    def seg(a, r0, r1, c, thick=0.0):
        n = int(abs(r1 - r0) * 3) + 2
        for i in range(n + 1):
            r = r0 + (r1 - r0) * i / n
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
            dot(x, y, c)
            if thick:
                dot(x + math.cos(a + math.pi / 2) * thick, y + math.sin(a + math.pi / 2) * thick, c)
    for k in range(720):  # the two rings
        a = 2 * math.pi * k / 720
        dot(cx + math.cos(a) * R, cy + math.sin(a) * R, glow)
        dot(cx + math.cos(a) * R * 0.93, cy + math.sin(a) * R * 0.93, ice)
        dot(cx + math.cos(a) * R * 0.22, cy + math.sin(a) * R * 0.22, ice)
    for k in range(12):
        a = 2 * math.pi * k / 12
        L = R * (0.9 if k % 2 == 0 else 0.68)
        seg(a, R * 0.22, L, ice, 0.6)
        for f in (0.45, 0.68):  # the branches of each needle
            if f * R > L:
                continue
            bx, by = cx + math.cos(a) * R * f, cy + math.sin(a) * R * f
            for s_ in (-1, 1):
                b = a + s_ * 0.75
                for i in range(int(R * 0.16)):
                    dot(bx + math.cos(b) * i, by + math.sin(b) * i, ice)
        tx, ty = cx + math.cos(a) * L, cy + math.sin(a) * L  # a diamond at the tip
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            dot(tx + dx, ty + dy, (230, 250, 255, 255))


def akaza(m, form):
    """Akaza: an Upper Moon demon, so his skin is pale grey all over (face included), covered in dark blue tattoo
    rings; short pink hair, a sleeveless pink-purple vest open over his chest, light hakama, bare striped feet.
    Compass Needle: a light-blue snowflake of twelve needles glows on the ground under his feet."""
    compass = form == "compass"
    skin = (218, 208, 216)
    head = skin_swap(head_paint(AKA_HAIR, (250, 220, 70), True, "akaza_compass" if compass else "akaza"), skin)
    ln = (36, 56, 150)

    def rings(face, px, w, h, base):  # seven thin tattoo rings round the arm, the lowest one at the wrist
        if face in ("up", "down"):
            return
        for k in range(7):
            y = int(h * (0.08 + 0.13 * k))
            for x in range(w):
                _put(px, w, h, x, y + (1 if (x * 4 // max(1, w)) % 2 and k % 2 else 0), ln)
    def chest(face, px, w, h, base):
        if face == "north":  # the lines that cross his chest and stomach, ending in short hooks at the sides
            for fy in (0.2, 0.36, 0.52, 0.68, 0.84):
                y = int(h * fy)
                for x in range(int(w * 0.12), int(w * 0.88)):
                    _put(px, w, h, x, y, ln)
                _put(px, w, h, int(w * 0.12), y - 1, ln); _put(px, w, h, int(w * 0.88) - 1, y - 1, ln)
        elif face in ("east", "west", "south"):
            for fy in (0.2, 0.36, 0.52, 0.68, 0.84):
                for x in range(w):
                    _put(px, w, h, x, int(h * fy), ln)
    vest = (196, 110, 160)
    torso = layered(skin, [chest])
    arm = layered(skin, [rings])
    leg = layered((236, 230, 240), [region((0, 0.0, 1, 0.12), (120, 160, 220)), region((0, 0.82, 1, 1), skin),
                                    lines((SIDES, [[(0, 0.88), (1, 0.88)], [(0, 0.95), (1, 0.95)]]), ln)])
    base_body(m, torso, arm, leg, head)
    for x0 in (-4.6, 2.6):  # the open vest
        m.box("body", [x0, 12.0, -2.6], [2.0, 12.2, 5.2], layered(vest, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), dark(vest, 0.7))]))
    m.box("body", [-4.6, 12.0, 2.1], [9.2, 12.2, 0.5], solid(vest))
    m.box("body", [-4.4, 11.2, -2.5], [8.8, 1.4, 5.0], solid((120, 160, 220)))
    akaza_hair(m)
    if compass:  # the snowflake compass on the ground at his feet
        m.box("root", [-12, 0.15, -12], [24, 0, 24], compass_paint)
        m.cubes[-1]["hires"] = 4


# ------------------------------------------------------------------ Megumi Fushiguro — Jujutsu Kaisen
MEG_HAIR = (20, 22, 34)


@M.smooth_hair
def megumi_hair(m):
    # big spiky black hair flaring up and out like a sea urchin
    shell(m, MEG_HAIR, hairline=30.6, sideburn=False, teeth=0.8)
    hp = M.hair_paint(MEG_HAIR)
    for k in range(12):
        a = 2 * math.pi * k / 12
        dx, dz = math.sin(a), -math.cos(a)
        m.strand([dx * 2.8, 31.6, dz * 2.8], [dx * 0.9, 0.9, dz * 0.9], 5.6, 3.2, hp, bone="hair", thick=0.8)
    for x, z in ((0, 0), (1.8, 1.4), (-1.8, 1.4), (0, -1.6)):
        m.strand([x, 32.2, z], [x * 0.3, 1, z * 0.3], 5.8, 3.2, hp, bone="hair", thick=0.8)
    for x, tilt in ((-2.4, -0.3), (0, 0), (2.4, 0.3)):
        m.strand([x, 31.4, -4.1], [tilt, -0.7, -0.5], 2.6, 2.2, hp, bone="hair", thick=0.75)


def megumi(m, form):
    """Megumi in the Jujutsu High uniform (dark navy, high collar, gold buttons). Ten Shadows: black shadow pools
    under his feet and ink-black shadow tendrils rising round him."""
    shadow = form == "shadows"
    head = head_paint(MEG_HAIR, (40, 110, 110), True, "megumi_shadow" if shadow else "megumi")
    uni = (28, 32, 52)
    buttons = lambda f, px, w, h, b: [_put(px, w, h, w // 2, y, (220, 190, 90)) for y in range(int(h * 0.1), int(h * 0.8), max(2, h // 6))] if f == "north" else None
    base_body(m, layered(uni, [buttons]), arm_paint(uni, sleeve_to=0.88), layered(uni, [region((0, 0.86, 1, 1), (20, 20, 24))]), head)
    m.box("body", [-4.2, 21.6, -2.6], [8.4, 2.6, 5.2], solid(uni))  # high collar
    megumi_hair(m)
    if shadow:
        ink = SC.swatch((10, 10, 16), 230)
        m.box("body", [-6, 0.05, -6], [12, 0.2, 12], solid((8, 8, 12)))
        for k in range(5):
            a = 2 * math.pi * k / 5
            SC.curve_tube(m, "body", [[math.cos(a) * 3, 0.2, math.sin(a) * 3], [math.cos(a) * 5, 5, math.sin(a) * 5], [math.cos(a) * 4, 10, math.sin(a) * 4]],
                          0.8, 0.2, [ink, ink, ink], n=2)


FORMS.update({
    "gohan": ["base", "ssj", "ssj2", "ultimate", "beast"],
    "bakugo": ["base", "cluster"],
    "gon": ["base", "jajanken", "dark", "adult"],
    "akaza": ["base", "compass"],
    "megumi": ["base", "shadows"],
})
_build_prev19 = build
_NEW19 = {"gohan": gohan, "bakugo": bakugo, "gon": gon, "akaza": akaza, "megumi": megumi}


def build(char, form):  # noqa: F811
    if char in _NEW19:
        m = M.Model()
        _NEW19[char](m, form)
        return m
    return _build_prev19(char, form)


# ==================================================================================
# 1.20: Aizen, Byakuya (Bleach) · Power, Makima (Chainsaw Man) · All Might, Todoroki (MHA) · Hisoka, Kurapika (HxH)
# ==================================================================================
M.FACE32.update({
    "aizen": dict(eye="narrow", brow="fine", mouth="smirk", marks=[]),
    "aizen_hogyoku": dict(eye="narrow", brow="none", mouth="neutral", marks=["purple_eyes", "hogyoku_lines"]),
    "aizen_final": dict(eye="narrow", brow="none", mouth="none", marks=["purple_eyes", "hogyoku_lines", "aizen_mask"]),
    "aizen_hatched": dict(eye="narrow", brow="fine", mouth="smirk", marks=[]),
    "byakuya": dict(eye="narrow", brow="fine", mouth="neutral", marks=[]),
    "byakuya_bankai": dict(eye="narrow", brow="sharp", mouth="neutral", marks=[]),
    "power": dict(eye="round", brow="angled", mouth="big_grin", marks=["shark_teeth", "power_eyes"]),
    "power_devil": dict(eye="round", brow="sharp", mouth="big_grin", marks=["shark_teeth", "power_eyes", "blood_drip"]),
    "makima": dict(eye="round", brow="fine", brow_col=(150, 60, 44), mouth="smile", marks=["makima_eyes"]),
    "makima_devil": dict(eye="round", brow="fine", brow_col=(150, 60, 44), mouth="neutral", marks=["makima_eyes", "makima_glow"]),
    "allmight": dict(eye="round", brow="sharp", mouth="none", marks=["allmight_shadow"]),
    "allmight_uss": dict(eye="round", brow="sharp", mouth="none", marks=["allmight_shadow", "am_blood"]),
    "todoroki": dict(eye="narrow", brow="flat", mouth="neutral", marks=["todoroki_scar"]),
    "todoroki_flash": dict(eye="narrow", brow="sharp", mouth="clench", marks=["todoroki_scar"]),
    "hisoka": dict(eye="narrow", brow="arch", mouth="smirk", marks=["hisoka_marks"]),
    "hisoka_serious": dict(eye="narrow", brow="arch", mouth="big_grin", marks=["hisoka_marks"]),
    "kurapika": dict(eye="round", brow="fine", mouth="neutral", marks=[]),
    "kurapika_scarlet": dict(eye="round", brow="angled", mouth="clench", marks=[]),
})
_face32_prev5 = M.face32


def face32_new20(px, W, H, spec, hair, iris, skin):
    _face32_prev5(px, W, H, spec, hair, iris, skin)
    marks = spec.get("marks", [])
    k = W / 32.0
    open_eyes = M.EXPR not in ("blink", "hurt")

    def put(x, y, c):
        for dx in range(max(1, int((x + 1) * k) - int(x * k))):
            for dy in range(max(1, int((y + 1) * k) - int(y * k))):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    if "purple_eyes" in marks and open_eyes:
        for cx in (10, 21):
            put(cx, 18, (170, 60, 220)); put(cx + 1, 18, (170, 60, 220))
    if "hogyoku_lines" in marks:  # the Hogyoku's white cracks across the face
        for x, y in ((6, 12), (7, 13), (8, 14), (25, 12), (24, 13), (23, 14), (15, 9), (16, 10)):
            put(x, y, (150, 110, 190))
    if "aizen_mask" in marks:  # the final form's mask-like face: a dark band across the eyes
        for x in range(4, 28):
            put(x, 16, (60, 30, 80))
    if "power_eyes" in marks and open_eyes:  # yellow eyes with red cross-shaped pupils
        for cx in (10, 21):
            for x in range(cx - 1, cx + 2):  # a 3x3 orange-yellow iris with a symmetric red plus in the middle
                for y in (17, 18, 19):
                    put(x, y, (240, 150, 40))
            for x, y in ((cx, 18), (cx - 1, 18), (cx + 1, 18), (cx, 17), (cx, 19)):
                put(x, y, (200, 20, 30))
    if "blood_drip" in marks:
        for x, y in ((9, 29), (9, 30), (22, 29), (22, 30), (22, 31)):
            put(x, y, (170, 20, 26))  # blood at the corners of her grin
    if "makima_eyes" in marks and open_eyes:  # golden eyes with concentric rings
        for cx in (10, 21):
            for x in range(cx - 2, cx + 4):
                for y in range(16, 21):
                    d = max(abs(x - (cx + 0.5)), abs(y - 18))
                    put(x, y, (236, 190, 64) if d >= 2 else ((206, 96, 52) if d >= 1 else (250, 226, 120)))  # yellow, a red-orange ring, yellow
        for cx in (10, 21):
            for x in range(cx - 2, cx + 4):
                put(x, 16, (20, 12, 14) if x in (cx - 2, cx + 3) else (196, 140, 50))   # lid shadow on the iris
        for x in range(7, 14):
            put(x, 15, (20, 12, 14)); put(31 - x, 15, (20, 12, 14))                  # heavy calm upper lid
    if "makima_glow" in marks:
        for x, y in ((4, 18), (27, 18)):
            put(x, y, (250, 220, 120))
    if "allmight_shadow" in marks:  # two deep, dark eye slots with a blue glint; the huge clenched grin; laugh lines
        SOCK, SOCK_E, BROW = (44, 40, 56), (96, 72, 62), (200, 150, 40)
        for cx in (10, 21):
            for x in range(cx - 4, cx + 5):
                for y in range(15, 22):
                    put(x, y, tuple(skin))                         # wipe the base round eye
            for x in range(cx - 3, cx + 5):
                for y in range(16, 21):
                    put(x, y, SOCK_E if (y == 20 or x in (cx - 3, cx + 4)) else SOCK)
            for x in range(cx - 4, cx + 6):
                put(x, 15, BROW)                                   # heavy golden brow ridge
            if open_eyes:
                put(cx + 1, 18, (70, 170, 255)); put(cx, 19, (40, 110, 210)); put(cx + 1, 19, (40, 110, 210))
                put(cx, 18, (235, 250, 255))                        # glint
        for x, y in ((5, 20), (5, 21), (6, 22), (6, 23), (26, 20), (26, 21), (25, 22), (25, 23)):
            put(x, y, (170, 139, 117))                             # laugh lines
        if M.EXPR in (None, "blink"):                              # shout/hurt keep their own mouths
            T, GAP, LINE, INK = (250, 250, 246), (196, 196, 204), (70, 40, 44), (20, 12, 14)
            for x in range(8, 24):
                put(x, 24, INK); put(x, 28, INK); put(x, 26, LINE)
                put(x, 25, GAP if x % 3 == 1 else T); put(x, 27, GAP if x % 3 == 1 else T)
            for y in (25, 26, 27):
                put(7, y, INK); put(24, y, INK)
            put(6, 24, INK); put(25, 24, INK); put(5, 23, INK); put(26, 23, INK)   # corners turned up
    if "am_blood" in marks:  # USS: blood from the corners of the mouth
        for x, y in ((24, 28), (24, 29), (25, 30), (25, 31), (7, 28), (7, 29)):
            put(x, y, (170, 20, 26))
    if "todoroki_scar" in marks:  # his left side (x >= 16): red hair band, red brow, a burn patch round a NORMAL eye
        get = lambda x, y: px[min(W - 1, int(x * k)), min(H - 1, int(y * k))][:3]
        brow_c = dark(hair, 0.8) if sum(hair) > 360 else (28, 22, 26)
        brow_px = [(31 - x, y) for y in range(11, 17) for x in range(2, 16) if get(x, y) == tuple(brow_c)]  # mirror of his right brow
        for y in range(0, 12):                                                  # face-painted hair: red on his left half
            for x in range(16, 32):
                put(x, y, (200, 50, 50))
        rows = {12: (21, 25), 13: (19, 27), 14: (18, 28), 15: (18, 29), 16: (17, 29), 17: (17, 29), 18: (17, 29),
                19: (18, 29), 20: (18, 29), 21: (18, 28), 22: (19, 28), 23: (20, 27), 24: (22, 27), 25: (24, 26)}
        notch = {(18, 14), (17, 18), (18, 22), (25, 12), (29, 15), (29, 20), (27, 23)}   # ragged edge
        for y, (x0, x1) in rows.items():
            for x in range(x0, x1 + 1):
                if (x, y) in notch or (17 <= y <= 20 and 18 <= x <= 26):
                    continue                     # never paint inside the eye box: lashes, white and iris stay intact
                edge = x in (x0, x1) or y in (12, 25) or (x + 1, y) in notch or (x - 1, y) in notch
                put(x, y, (160, 74, 64) if edge else (190, 104, 90))
        for x, y in brow_px:                                                    # his left brow: red, over the scar
            put(x, y, (176, 36, 44))
        if open_eyes:
            put(10, 18, (120, 130, 140)); put(11, 18, (120, 130, 140))           # right eye grey
            for x in (20, 21, 22):                                              # left eye turquoise, whole iris
                put(x, 18, (24, 110, 120)); put(x, 20, (40, 190, 190))
            put(22, 19, (40, 190, 190)); put(21, 19, (16, 60, 70)); put(20, 19, (252, 252, 252))
    if "hisoka_marks" in marks:  # a star on one cheek, a teardrop on the other
        star = ["..#..", "#####", ".###.", ".#.#.", "#...#"]
        for r, row in enumerate(star):
            for c, ch in enumerate(row):
                if ch == "#":
                    put(22 + c, 21 + r, (70, 110, 200))
        tear = [".#.", ".#.", "###", "###", ".#."]
        for r, row in enumerate(tear):
            for c, ch in enumerate(row):
                if ch == "#":
                    put(6 + c, 21 + r, (220, 60, 140))
    if "scarlet_eyes" in marks and open_eyes:
        for cx in (10, 21):
            for x in (cx, cx + 1):
                for y in (17, 18, 19):
                    put(x, y, (230, 20, 40))


M.face32 = face32_new20


def _shell_strands(m, col, strands, hairline=30.6):
    shell(m, col, hairline=hairline, sideburn=False, teeth=0.8)
    hp = M.hair_paint(col)
    for base, d, L, wd in strands:
        m.strand(base, d, L, wd, hp, bone="hair", thick=0.8)


# ------------------------------------------------------------------ Sosuke Aizen — Bleach
AIZEN_HAIR = (150, 96, 58)


def _long_hair_paint(col):
    """Waist-length hair: strand streaks running down, a jagged torn bottom edge (transparent notches)."""
    sh, hi = dark(col, 0.86), tuple(min(255, int(v * 1.06)) for v in col)
    def p(face, img):
        w, h = img.size
        px = img.load()
        for x in range(w):
            cut = int(h * (0.04 + 0.1 * ((x * 7919 // max(1, w)) % 5) / 4)) if face in SIDES else 0
            for y in range(h):
                if face in SIDES and y >= h - cut:
                    continue
                c = col
                if (x * 3 + y // 9) % 7 == 0:
                    c = sh
                elif (x * 5 + y // 6) % 11 == 0:
                    c = hi
                px[x, y] = c + (255,)
    return p


def _plate_shape(col, rim):
    """One of the jagged dark violet plates that rise behind Aizen's head in his hatched form."""
    def f(xf, u):
        half = 0.48 * (1 - 0.6 * u) if u < 0.85 else 0.48 * 0.49 * (1 - (u - 0.85) / 0.15)
        k = (u * 4.5) % 1
        if k < 0.3:  # torn notches, alternating sides
            if (int(u * 4.5) % 2 == 0 and xf > 0.5 + half * 0.35) or (int(u * 4.5) % 2 == 1 and xf < 0.5 - half * 0.35):
                return None
        if abs(xf - 0.5) > half:
            return None
        return rim if abs(xf - 0.5) > half * 0.7 else col
    return f


@M.smooth_hair
def aizen_hair(m, final):
    if not final:
        _shell_strands(m, AIZEN_HAIR, [([x, 32.0, -2.5 + abs(x) * 0.2], [x * 0.05, 0.35, 1], 6.0, 3.4) for x in (-2.6, -0.9, 0.9, 2.6)]
                       + [([0.6, 31.2, -4.2], [0.15, -1, -0.25], 4.0, 1.4)])  # slicked back, one strand on the forehead
        return
    # hatched form: wild hair falling to his waist, one lock across his face
    col = AIZEN_HAIR_LONG
    shell(m, col, hairline=31.0, sideburn=False, teeth=0.8)
    m.box("hair", [-4.4, 13.0, 4.0], [8.8, 18.6, 1.8], _long_hair_paint(col))
    hp = M.hair_paint(col)
    for x in (-3.4, -1.2, 1.2, 3.4):
        m.strand([x, 16.0, 4.9], [x * 0.06, -1, 0.25], 6.0 + abs(x) * 0.6, 2.6, hp, bone="hair", thick=0.9)
    for s_ in (1, -1):  # long side locks down past the shoulders
        m.strand([s_ * 4.4, 29.0, -0.4], [s_ * 0.12, -1, 0.15], 13.0, 2.4, hp, bone="hair", thick=0.9)
        m.strand([s_ * 4.3, 30.4, 2.0], [s_ * 0.2, -1, 0.3], 15.0, 2.6, hp, bone="hair", thick=0.9)
    for x in (-3.0, -1.0, 1.0, 3.0):  # rough top
        m.strand([x, 32.0, 0.6], [x * 0.12, 0.4, 1], 4.0, 2.6, hp, bone="hair", thick=0.9)
    m.box("hair", [0.7, 25.2, -4.45], [1.1, 6.0, 0.45], solid(col))  # the lock over one eye


AIZEN_HAIR_LONG = (135, 100, 55)


def aizen(m, form):
    """Aizen. Base: the white Arrancar coat over a black hakama, slicked-back brown hair, Kyoka Suigetsu at his
    side. Hogyoku: the Hogyoku fused into his chest, a black cross cut into the coat round its violet glow.
    Final (the hatched form): waist-length wild hair, a pure white body-suit with a deep V at the chest and the
    black cross seam over the Hogyoku, two torn dark violet plates rising behind his head."""
    hog = form in ("hogyoku", "final")
    final = form == "final"
    key = {"base": "aizen", "hogyoku": "aizen_hogyoku", "final": "aizen_hatched"}[form]
    hair = AIZEN_HAIR_LONG if final else AIZEN_HAIR
    head = head_paint(hair, (110, 70, 40) if not hog else (150, 70, 200), True, key)
    coat, sash, ink, core = (238, 238, 240), (30, 30, 36), (18, 18, 22), (170, 70, 230)
    lap = lambda f, px, w, h, b: [_put(px, w, h, int(w * 0.5 + (y - h * 0.1) * 0.25) if y < h * 0.45 else w // 2, y, (190, 190, 196)) for y in range(h)] if f == "north" else None

    def cross(face, px, w, h, base):  # the black cross seam round the Hogyoku, a line down to the belt
        if face != "north":
            return
        cx, cy, r = w // 2, int(h * 0.3), max(2, w // 4)
        for d in range(-r, r + 1):
            _put(px, w, h, cx + d, cy, ink); _put(px, w, h, cx, cy + d, ink)
        for y in range(cy + r, h):
            _put(px, w, h, cx, y, ink)
        _put(px, w, h, cx, cy, core); _put(px, w, h, cx - 1, cy, core)

    def vee(face, px, w, h, base):  # the deep V of skin at the chest
        if face != "north":
            return
        for y in range(int(h * 0.55)):
            half = (w * 0.26) * (1 - y / (h * 0.55))
            for x in range(w):
                if abs(x + 0.5 - w / 2) < half:
                    _put(px, w, h, x, y, SKIN)

    def side_shade(face, px, w, h, base):
        if face in ("east", "west"):
            for y in range(h):
                for x in range(w):
                    if (x + y) % 3 == 0:
                        _put(px, w, h, x, y, (205, 210, 224))
    if final:
        suit = (250, 250, 252)
        torso = layered(suit, [vee, cross])
        arm = layered(suit, [region((0, 0.88, 1, 1), SKIN)])
        leg = layered(suit, [region((0, 0.9, 1, 1), (230, 230, 236))])
    else:
        torso = layered(coat, [lap] + ([cross] if hog else []))
        arm = layered(coat, [region((0, 0.86, 1, 1), SKIN)])
        leg = layered((34, 34, 40), [region((0, 0.88, 1, 1), (20, 20, 24))])
    base_body(m, torso, arm, leg, head)
    if not final:
        m.box("body", [-4.4, 11.4, -2.5], [8.8, 1.6, 5.0], solid(sash))                         # black sash
        m.box("body", [-4.6, 3.0, 2.1], [9.2, 21.2, 0.5], solid(coat))                         # long coat tails
        for x0 in (-4.6, 2.6):
            m.box("body", [x0, 3.0, -2.6], [2.0, 9.0, 0.5], solid(coat))
        m.box("body", [-4.2, 22.4, -2.6], [8.4, 1.6, 5.2], solid(coat))                        # high collar
        kyoka = dict(wrap=(60, 90, 70), diamond=(200, 190, 140), tsuba="round", metal=(150, 140, 90),
                     blade=(206, 214, 226), edge=(248, 250, 255), hamon=None, saya=(40, 60, 50), saya_band=(200, 190, 140))
        M.katana2(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 14, kyoka)
    if hog:
        SC.blob(m, "body", [0, 20.4, -2.2], [0.8, 0.8, 0.45], SC.swatch(core, 235))              # the Hogyoku
    if final:  # two torn dark violet plates rising from behind his shoulders
        plate = M._sprite(_plate_shape((78, 82, 112), (118, 124, 160)))
        for s_ in (1, -1):
            m.box("body", [s_ * 3.2 - 3.0, 21.0, 6.3], [6.0, 15.0, 0], plate, rot=[-14, 0, -s_ * 22], pivot=[s_ * 3.2, 21.0, 6.3])
            m.cubes[-1]["hires"] = 4
    aizen_hair(m, final)


# ------------------------------------------------------------------ Byakuya Kuchiki — Bleach
BYA_HAIR = (24, 24, 32)


@M.smooth_hair
def byakuya_hair(m):
    _shell_strands(m, BYA_HAIR, [([x, 31.0, 3.6], [x * 0.04, -1, 0.15], 8.0, 2.6) for x in (-2.6, -0.8, 0.8, 2.6)]
                   + [([s * 3.9, 30.6, -1.0], [s * 0.1, -1, 0], 7.0, 2.0) for s in (1, -1)]
                   + [([x, 31.4, -4.1], [x * 0.05, -0.8, -0.4], 3.4, 1.8) for x in (-1.6, 0.0, 1.6)])
    for s in (1, -1):  # the white kenseikan pieces clipping his hair
        for k in range(3):
            m.box("hair", [s * 4.2 - 0.4, 29.6, -2.8 + k * 1.8], [0.8, 2.6, 0.8], solid((240, 240, 244)))


def byakuya(m, form):
    """Byakuya: the white captain's haori (the 6th division) over black shihakusho, the pale Ginpaku Kazahana scarf,
    the white kenseikan in his black hair, Senbonzakura at his side. Bankai: pink petals swirl round him."""
    bankai = form == "bankai"
    head = head_paint(BYA_HAIR, (60, 70, 100), True, "byakuya_bankai" if bankai else "byakuya")
    shk = (22, 22, 28)
    base_body(m, layered(shk, [lines((("north",), [[(0.5, 0), (0.5, 0.45)]]), (230, 230, 236))]),
              arm_paint(shk, sleeve_to=0.86), layered(shk, [region((0, 0.88, 1, 1), (236, 236, 236))]), head)
    m.box("body", [-4.4, 11.4, -2.5], [8.8, 1.4, 5.0], solid((236, 236, 236)))                  # white obi
    haori = layered((244, 244, 246), [region((0, 0.92, 1, 1), (30, 30, 36), faces=("south",))])
    m.box("body", [-4.6, 3.6, 2.1], [9.2, 20.6, 0.5], haori)
    for x0 in (-4.6, 2.8):
        m.box("body", [x0, 3.6, -2.6], [1.8, 20.6, 0.5], haori)
    both_arms(m, [3.5, 14.0, -2.7], [5.0, 10.2, 5.4], haori)
    m.box("body", [-4.4, 21.6, -2.8], [8.8, 2.4, 5.6], solid((214, 220, 210)))                  # the pale scarf
    m.strand([-1.5, 22, 2.8], [-0.1, -1, 0.35], 9, 2.0, solid((214, 220, 210)), bone="body", segs=3)
    senbon = dict(wrap=(50, 40, 70), diamond=(220, 200, 230), tsuba="cross", metal=(180, 170, 200),
                  blade=(220, 200, 214) if bankai else (206, 214, 226), edge=(255, 230, 240), hamon=(240, 160, 200), saya=(30, 30, 36), saya_band=(200, 200, 200))
    M.katana2(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 14, senbon)
    byakuya_hair(m)
    if bankai:  # a swirl of pink petals
        pet = SC.swatch((250, 150, 200), 200)
        for k in range(14):
            a = k * 2.399
            SC.blade(m, "body", [math.cos(a) * 6.5, 4 + k * 1.5, math.sin(a) * 4], [math.sin(a), 0.2, -math.cos(a)], 1.4, 0.8, 0.2, pet)


# ------------------------------------------------------------------ Power — Chainsaw Man
POW_HAIR = (244, 214, 176)


@M.smooth_hair
def power_hair(m, devil):
    _shell_strands(m, POW_HAIR, [([x, 30.8, 3.6], [x * 0.05, -1, 0.15], 13.0, 2.8) for x in (-2.8, -1.0, 1.0, 2.8)]
                   + [([s * 4.0, 30.6, -0.6], [s * 0.08, -1, 0], 11.0, 2.2) for s in (1, -1)]
                   + [([x, 31.4, -4.1], [x * 0.05, -0.75, -0.45], 3.4, 1.8) for x in (-2.2, -0.6, 1.0, 2.6)])
    horn, tip = SC.swatch((214, 34, 40)), SC.swatch((150, 16, 24))
    for s in (1, -1):  # two short, straight red cone horns pointing up from the front of her head
        H = 1.0 if not devil else 1.6
        for i, (w, c) in enumerate(((1.4, (200, 24, 34)), (1.0, (200, 24, 34)), (0.6, (226, 46, 56)))):
            m.box("hair", [s * 1.9 - w / 2, 32.0 + i * H, -2.6 - w / 2], [w, H + 0.1, w], solid(c, outline=False),
                  rot=[0, 0, -s * 10], pivot=[s * 1.9, 32.0, -2.6])


def power(m, form):
    """Power, the Blood Fiend: long blonde hair, two red horns, yellow eyes with red cross pupils, shark teeth, in the
    Public Safety white shirt, black tie and dark trousers. Blood Devil: bigger horns, blood running down."""
    devil = form == "devil"
    head = head_paint(POW_HAIR, (230, 60, 40), True, "power_devil" if devil else "power")
    shirt, jacket, pants = (238, 238, 235), (44, 112, 160), (30, 30, 35)

    def tie(face, px, w, h, base):  # a 2 px black tie with a knot under the collar
        if face != "north":
            return
        for y in range(int(h * 0.04), int(h * 0.72)):
            for x in (w // 2 - 1, w // 2):
                _put(px, w, h, x, y, (25, 25, 30))
        for x in range(w // 2 - 2, w // 2 + 2):
            for y in range(int(h * 0.04), int(h * 0.04) + 2):
                _put(px, w, h, x, y, (25, 25, 30))
    base_body(m, layered(shirt, [tie]), layered(jacket, [region((0, 0.86, 1, 1), SKIN)]),
              layered(pants, [region((0, 0.8, 1, 0.84), (50, 50, 55)), region((0, 0.84, 1, 1), (190, 40, 50))]), head)
    for x0 in (-4.6, 2.6):  # the open blue jacket over her white shirt
        m.box("body", [x0, 11.6, -2.6], [2.0, 12.6, 5.2], layered(jacket, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), dark(jacket, 0.75))]))
    m.box("body", [-4.6, 11.6, 2.1], [9.2, 12.6, 0.5], solid(jacket))
    m.box("body", [-4.3, 11.4, -2.3], [8.6, 1.0, 4.6], solid((40, 26, 34)))
    if devil:
        bl = SC.swatch((180, 20, 28))
        SC.blade(m, "rightArm", [6.2, 10.0, -2.0], [0, -0.1, -1], 9, 2.6, 1.0, bl)               # a blood blade in her hand
    power_hair(m, devil)


# ------------------------------------------------------------------ Makima — Chainsaw Man
MAK_HAIR = (190, 92, 70)


@M.smooth_hair
def makima_hair(m):
    _shell_strands(m, MAK_HAIR, [([x, 31.6, -4.1], [x * 0.05, -0.8, -0.4], 2.4, 2.0) for x in (-2.8, -1.0, 1.0, 2.8)]  # bangs stop above the eyes
                   + [([s * 3.9, 30.6, -0.8], [s * 0.05, -1, 0], 6.0, 2.0) for s in (1, -1)])
    hp = M.hair_paint(MAK_HAIR)
    for k in range(5):  # the long braid down her back
        m.box("hair", [-0.9, 28.6 - k * 2.4, 4.0 + k * 0.1], [1.8, 2.2, 1.6], hp)


def makima(m, form):
    """Makima: copper-red hair in a long braid, golden ringed eyes, Public Safety white shirt and black tie, black
    trousers and shoes. As the Control Devil, chains of control trail from her hands."""
    devil = form == "devil"
    head = head_paint(MAK_HAIR, (230, 190, 90), True, "makima_devil" if devil else "makima")
    shirt = (244, 242, 236)
    tie = lambda f, px, w, h, b: [_put(px, w, h, w // 2, y, (24, 24, 30)) for y in range(int(h * 0.05), int(h * 0.7))] if f == "north" else None
    base_body(m, layered(shirt, [tie]), arm_paint(shirt, sleeve_to=0.86),
              layered((26, 26, 32), [region((0, 0.88, 1, 1), (14, 14, 18))]), head)
    m.box("body", [-4.3, 11.4, -2.3], [8.6, 1.0, 4.6], solid((30, 28, 34)))
    if devil:
        ch = SC.swatch((140, 140, 150))
        for s, arm_ in ((1, "rightArm"), (-1, "leftArm")):
            SC.curve_tube(m, arm_, [[s * 6, 12, 0], [s * 8, 9, -3], [s * 10, 8, -7]], 0.35, 0.25, [ch, ch], n=2)
    makima_hair(m)


# ------------------------------------------------------------------ All Might — My Hero Academia
AM_HAIR = (250, 214, 70)


@M.smooth_hair
def allmight_hair(m):
    _shell_strands(m, AM_HAIR, [([x, 31.6, 1.4], [x * 0.2, 0.5, 0.9], 4.0, 3.0) for x in (-2.6, -0.8, 0.8, 2.6)])
    hp = M.hair_paint(AM_HAIR)
    for s in (1, -1):  # his two famous V-shaped bangs standing straight up
        m.strand([s * 1.4, 31.4, -3.6], [s * 0.35, 1, -0.05], 9.0, 2.6, hp, bone="hair", thick=0.85)


def allmight(m, form):
    """All Might in his Silver Age costume: a huge muscled body in a blue suit with red and yellow stripes, white
    gloves, red boots, the two golden V bangs, eyes lost in shadow with two blue glints, the grin."""
    uss = form == "uss"
    head = head_paint(AM_HAIR, (90, 200, 255), True, "allmight_uss" if uss else "allmight")
    blue, red, yel = (40, 70, 170), (210, 40, 40), (250, 200, 50)

    def stripes(face, px, w, h, base):
        if face == "north":
            for y in range(int(h * 0.05), int(h * 0.5)):
                d = y - int(h * 0.05)
                _put(px, w, h, int(w * 0.5 - d * 0.6), y, yel); _put(px, w, h, int(w * 0.5 + d * 0.6), y, yel)
            for x in range(w):
                _put(px, w, h, x, int(h * 0.62), red)
    base_body(m, layered(blue, [stripes]), layered(blue, [region((0, 0.0, 1, 0.12), red), region((0, 0.78, 1, 1), (244, 244, 244))]),
              layered(blue, [region((0, 0.62, 1, 1), red)]), head)
    sk = layered(blue, [])
    for s_ in (1, -1):  # an enormous frame: broad shoulders and chest
        arm_ = "rightArm" if s_ > 0 else "leftArm"
        m.box(arm_, [s_ * 6.0 - 2.7, 18.4, -2.7], [5.4, 5.8, 5.4], layered(blue, [region((0, 0, 1, 0.3), red)]))
    m.box("body", [-4.6, 17.0, -2.8], [9.2, 6.4, 0.6], layered(blue, [stripes]))
    if uss:  # the last ember of One For All blazing round his fist
        gl = SC.swatch((180, 230, 255), 200)
        SC.blob(m, "rightArm", [6.2, 10.4, 0], [2.4, 2.4, 2.4], gl)
    allmight_hair(m)


# ------------------------------------------------------------------ Shoto Todoroki — My Hero Academia
def _split_shell_paint(neg, pos, **kw):
    """A hair cap split exactly down the middle: the model's -x half one colour, the +x half the other."""
    pn, pp = M.shell_paint(neg, **kw), M.shell_paint(pos, **kw)

    def p(face, img):
        w, h = img.size
        if face in ("east", "west"):
            (pp if face == "east" else pn)(face, img)
            return
        a = img.copy(); b = img.copy()
        pn(face, a); pp(face, b)
        left_is_neg = face in ("north", "up", "down")
        for y in range(h):
            for x in range(w):
                src = a if ((x < w / 2) == left_is_neg) else b
                img.putpixel((x, y), src.getpixel((x, y)))
    return p


@M.smooth_hair
def todoroki_hair(m):
    white, red = (236, 236, 240), (200, 50, 50)
    m.box("hair", [-4, 24, -4], [4, 8, 8], M.shell_paint(red, hairline=30.6, sideburn=False, teeth=0.8), inflate=0.45)    # his left half: red
    m.box("hair", [0, 24, -4], [4, 8, 8], M.shell_paint(white, hairline=30.6, sideburn=False, teeth=0.8), inflate=0.45)   # his right half: white
    hw, hr = M.hair_paint(white), M.hair_paint(red)
    for x in (-3.2, -1.8, -0.6):  # his left side red (the model's -x is his left)
        m.strand([x, 31.6, -0.5], [x * 0.1, 0.3, 0.6], 4.2, 3.4, hr, bone="hair", thick=0.8)
        m.strand([x, 31.6, -4.1], [x * 0.05, -0.8, -0.4], 2.2, 1.8, hr, bone="hair", thick=0.8)
    for x in (0.6, 1.8, 3.2):
        m.strand([x, 31.6, -0.5], [x * 0.1, 0.3, 0.6], 4.2, 3.4, hw, bone="hair", thick=0.8)
        m.strand([x, 31.6, -4.1], [x * 0.05, -0.8, -0.4], 2.2, 1.8, hw, bone="hair", thick=0.8)
    for s, hp in ((1, hw), (-1, hr)):
        m.strand([s * 2.2, 31.0, 3.6], [s * 0.1, -0.6, 0.6], 4.0, 3.0, hp, bone="hair", thick=0.8)


def todoroki(m, form):
    """Todoroki: hair split white (right) and red (left), the burn scar round his left eye, a dark navy hero suit with
    a utility belt; ice crusted over his right side, fire licking off his left (stronger after Flashfire)."""
    flash = form == "flashfire"
    head = head_paint((236, 236, 240), (120, 130, 140), True, "todoroki_flash" if flash else "todoroki")
    navy = (36, 46, 80)
    base_body(m, layered(navy, [region((0, 0, 1, 0.08), (26, 30, 52))]), arm_paint(navy, sleeve_to=0.86),
              layered(navy, [region((0, 0.86, 1, 1), (24, 24, 30))]), head)
    m.box("body", [-4.4, 11.4, -2.5], [8.8, 1.4, 5.0], solid((150, 130, 90)))
    ice, fire = SC.swatch((200, 236, 255), 210), SC.swatch((255, 120, 40), 200)
    for k in range(4):  # ice on his right arm and shoulder
        SC.blade(m, "rightArm", [6.4, 22 - k * 3, -1 + k * 0.6], [0.7, 0.6, -0.2], 2.2 + k * 0.3, 1.2, 0.8, ice)
    if flash:
        for k in range(5):
            SC.blade(m, "leftArm", [-6.4, 22 - k * 2.6, 0], [-0.4, 1, 0.1], 3.6, 1.4, 0.5, fire)
    todoroki_hair(m)


# ------------------------------------------------------------------ Hisoka Morow — Hunter x Hunter
HIS_HAIR = (220, 70, 120)


SUIT_ART = {  # 5x5 card suits
    "spade": ["..#..", ".###.", "#####", "#####", "..#.."],
    "club": [".###.", ".###.", "#####", "#####", "..#.."],
    "heart": [".#.#.", "#####", "#####", ".###.", "..#.."],
    "diamond": ["..#..", ".###.", "#####", ".###.", "..#.."],
}


def _suit_drawer(face_name, items):
    """Detail drawer: solid 5x5 card suits at (fx, fy) on one face, scaled to the texture resolution."""
    def p(face, px, w, h, base):
        if face != face_name:
            return
        k = max(1, w // 16)
        for kind, fx, fy, col in items:
            art = SUIT_ART[kind]
            x0, y0 = int(w * fx) - 2 * k, int(h * fy) - 2 * k
            for r, row in enumerate(art):
                for c, ch in enumerate(row):
                    if ch == "#":
                        for dx in range(k):
                            for dy in range(k):
                                _put(px, w, h, x0 + c * k + dx, y0 + r * k + dy, col)
    return p


@M.smooth_hair
def hisoka_hair(m):
    # slicked straight back from a high forehead, spikes sweeping back off the crown, one loose strand at the temple
    shell(m, HIS_HAIR, hairline=31.5, sideburn=False, teeth=0.25)
    hp = M.hair_paint(HIS_HAIR)
    for x in (-2.6, -0.9, 0.9, 2.6):
        for k in range(2):
            m.strand([x, 32.0, -1.5 + k * 2.4], [x * 0.12, 0.65 - k * 0.25, 1.0], 5.8 - k * 0.6, 2.8, hp, bone="hair", thick=0.8)
    m.strand([-3.3, 31.4, -3.9], [-0.1, -1, -0.15], 3.2, 1.0, hp, bone="hair", thick=0.6)


def hisoka(m, form):
    """Hisoka: pink-red hair slicked back from a high forehead, a star and a teardrop painted on his cheeks, a loose
    light top with a deep V neck and a big spade and club, a heart and a diamond on his trousers, a belt, pointed
    jester shoes. Serious: his magenta aura (Bungee Gum) clings to his hands."""
    serious = form == "serious"
    head = head_paint(HIS_HAIR, (230, 180, 60), True, "hisoka_serious" if serious else "hisoka")
    top, pants, ink, red = (232, 222, 240), (240, 238, 232), (40, 30, 60), (210, 40, 80)

    def vee(face, px, w, h, base):
        if face != "north":
            return
        for y in range(int(h * 0.42)):
            half = (w * 0.22) * (1 - y / (h * 0.42))
            for x in range(w):
                if abs(x + 0.5 - w / 2) < half:
                    _put(px, w, h, x, y, SKIN)
    torso = layered(top, [vee, _suit_drawer("north", [("spade", 0.27, 0.6, ink), ("club", 0.73, 0.6, ink)]),
                          _suit_drawer("south", [("diamond", 0.5, 0.45, red)])])
    arm = layered(top, [region((0, 0.82, 1, 1), SKIN)])
    leg_r = layered(pants, [region((0, 0.86, 1, 1), (60, 40, 80)), _suit_drawer("north", [("heart", 0.5, 0.35, red)])])
    leg_l = layered(pants, [region((0, 0.86, 1, 1), (60, 40, 80)), _suit_drawer("north", [("diamond", 0.5, 0.35, red)])])
    base_body(m, torso, arm, leg_r, head)
    for c in m.cubes:  # the other trouser leg carries the diamond
        if c["bone"] == "leftLeg":
            c["paint"] = leg_l
    m.box("body", [-4.4, 11.6, -2.5], [8.8, 1.2, 5.0], solid((90, 60, 140)))
    for leg_, x in (("rightLeg", 1.9), ("leftLeg", -1.9)):  # pointed jester toes curling up
        m.box(leg_, [x - 0.6, 0.2, -3.6], [1.2, 1.0, 1.8], solid((60, 40, 80)), rot=[-30, 0, 0], pivot=[x, 0.4, -2.2])
    if serious:
        gum = SC.swatch((255, 120, 200), 190)
        for s_, arm_ in ((1, "rightArm"), (-1, "leftArm")):
            SC.curve_tube(m, arm_, [[s_ * 6, 11, -1], [s_ * 8, 12, -5], [s_ * 7, 14, -9]], 0.4, 0.2, [gum, gum], n=2)
    hisoka_hair(m)


# ------------------------------------------------------------------ Kurapika — Hunter x Hunter
KUR_HAIR = (246, 216, 120)


@M.smooth_hair
def kurapika_hair(m):
    _shell_strands(m, KUR_HAIR, [([s * 3.9, 30.8, -0.6], [s * 0.1, -1, 0.05], 6.0, 2.6) for s in (1, -1)]
                   + [([x, 30.8, 3.6], [x * 0.05, -1, 0.1], 5.4, 2.6) for x in (-2.4, 0, 2.4)]
                   + [([x, 31.4, -4.1], [x * 0.05, -0.8, -0.4], 3.6, 1.9) for x in (-2.4, -0.6, 1.2, 2.8)])


def kurapika(m, form):
    """Kurapika in the Kurta clan's blue tabard with gold trim over a white robe, a blonde bob; on his right hand the
    five chains of his nen. Emperor Time: his eyes burn scarlet and the chains glow."""
    scarlet = form == "emperor"
    head = head_paint(KUR_HAIR, (120, 96, 76) if not scarlet else (230, 20, 40), True, "kurapika_scarlet" if scarlet else "kurapika")
    white, blue, gold = (238, 238, 232), (40, 70, 160), (230, 190, 70)
    tab = lambda f, px, w, h, b: [[_put(px, w, h, x, y, gold if (x in (int(w * 0.18), int(w * 0.82)) or y == int(h * 0.12)) else blue) for x in range(int(w * 0.18), int(w * 0.83))] for y in range(int(h * 0.12), h)] if f in ("north", "south") else None
    base_body(m, layered(white, [tab]), arm_paint(white, sleeve_to=0.86), layered(white, [region((0, 0.86, 1, 1), (60, 50, 40))]), head)
    m.box("body", [-3.0, 2.0, -2.4], [6.0, 10.0, 0.4], layered(blue, [region((0, 0, 0.08, 1), gold), region((0.92, 0, 1, 1), gold)]))  # the tabard's front panel
    m.box("body", [-3.0, 2.0, 2.0], [6.0, 10.0, 0.4], layered(blue, [region((0, 0, 0.08, 1), gold), region((0.92, 0, 1, 1), gold)]))
    ch = SC.swatch((200, 200, 210) if not scarlet else (255, 120, 140), 230)
    for k in range(5):  # the five chains hanging from his right fingers
        SC.curve_tube(m, "rightArm", [[5.0 + k * 0.5, 12, -1.2], [5.2 + k * 0.6, 8, -2.2], [5.0 + k * 0.7, 5 - k * 0.4, -1.5]], 0.22, 0.2, [ch, ch], n=2)
    kurapika_hair(m)


FORMS.update({
    "aizen": ["base", "hogyoku", "final"],
    "byakuya": ["shikai", "bankai"],
    "power": ["fiend", "devil"],
    "makima": ["base", "devil"],
    "allmight": ["base", "uss"],
    "todoroki": ["base", "flashfire"],
    "hisoka": ["base", "serious"],
    "kurapika": ["base", "emperor"],
})
_build_prev20 = build
_NEW20 = {"aizen": aizen, "byakuya": byakuya, "power": power, "makima": makima, "allmight": allmight,
          "todoroki": todoroki, "hisoka": hisoka, "kurapika": kurapika}


def build(char, form):  # noqa: F811
    if char in _NEW20:
        m = M.Model()
        _NEW20[char](m, form)
        return m
    return _build_prev20(char, form)


# ==================================================================================
# 1.21: Beerus (God of Destruction) and Whis (Angel) — Dragon Ball Super
M.FACE32.update({
    "beerus": dict(eye="narrow", brow="none", mouth="neutral", marks=["beerus_eyes"]),
    "beerus_serious": dict(eye="narrow", brow="none", mouth="clench", marks=["beerus_eyes", "beerus_fangs"]),
    "beerus_full": dict(eye="narrow", brow="none", mouth="clench", marks=["beerus_eyes", "beerus_fangs", "beerus_glow"]),
    "whis": dict(eye="narrow", brow="none", mouth="smile", marks=["whis_eyes"]),
    "whis_angel": dict(eye="narrow", brow="none", mouth="neutral", marks=["whis_eyes", "whis_glow"]),
})
_face32_prev21 = M.face32


def face32_new21(px, W, H, spec, hair, iris, skin):
    _face32_prev21(px, W, H, spec, hair, iris, skin)
    marks = spec.get("marks", [])
    k = W / 32.0
    open_eyes = M.EXPR not in ("blink", "hurt")

    def put(x, y, c):
        for dx in range(max(1, int((x + 1) * k) - int(x * k))):
            for dy in range(max(1, int((y + 1) * k) - int(y * k))):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    if "beerus_eyes" in marks:  # almond cat eyes: pale yellow with a small dark pupil, thick black liner flicking outward
        glow = "beerus_glow" in marks
        for side, cx in ((-1, 10), (1, 21)):
            if open_eyes:
                for x in range(cx - 2, cx + 3):
                    for y in (17, 18):
                        put(x, y, (255, 250, 200) if glow else (236, 222, 140))
                put(cx, 17, (20, 16, 24)); put(cx, 18, (20, 16, 24))
            for x in range(cx - 3, cx + 4):
                put(x, 16, (16, 12, 20))
            for x in range(cx - 2, cx + 3):
                put(x, 19, (16, 12, 20))
            ox = cx + 4 * side if side > 0 else cx - 4
            put(ox, 16, (16, 12, 20)); put(ox + side, 15, (16, 12, 20))  # the liner's flick
        put(15, 21, (90, 70, 100)); put(16, 21, (90, 70, 100))  # the cat nose
    if "beerus_fangs" in marks:
        put(13, 25, (250, 250, 250)); put(18, 25, (250, 250, 250))
    if "whis_eyes" in marks:  # calm violet eyes under heavy lids, lavender lips
        glow = "whis_glow" in marks
        for cx in (10, 21):
            for x in range(cx - 3, cx + 3):
                put(x, 16, (40, 40, 60))
            if open_eyes:
                for x in range(cx - 2, cx + 2):
                    put(x, 17, (230, 235, 255) if glow else (245, 245, 250))
                put(cx - 1, 18, (150, 90, 190)); put(cx, 18, (150, 90, 190))
                put(cx - 1, 17, (190, 140, 230) if glow else (110, 60, 150)); put(cx, 17, (110, 60, 150))
        for x in range(14, 18):
            put(x, 25, (150, 110, 170))


M.face32 = face32_new21

BEERUS_SKIN = (150, 125, 160)
BEERUS_GOLD = (235, 190, 40)


def _strip_ears(m):
    m.cubes[:] = [c for c in m.cubes if not (c["bone"] == "head" and c["size"] == [0.75, 2.25, 1.5])]


def _diamonds(cols, at_y, size_):
    """Detail drawer: a column of diamonds down the centre of a face."""
    def p(face, px, w, h, base):
        if face != "north":
            return
        for (fy, col) in zip(at_y, cols):
            cy, r = int(h * fy), max(1, int(w * size_))
            for y in range(cy - r, cy + r + 1):
                half = r - abs(y - cy)
                for x in range(w // 2 - half, w // 2 + half + (0 if w % 2 else 0)):
                    _put(px, w, h, x, y, col)
    return p


def beerus(m, form):
    """Beerus: a hairless purple sphynx cat in Egyptian dress — huge pointed ears, gold earrings and bands, a striped
    turquoise-and-black usekh collar with an orange gem, a black front sash with white and orange diamonds, baggy
    blue harem pants gathered at gold ankle cuffs, pointed brown slippers, a thin tail. Serious: fangs bared;
    Full Power: glowing eyes and the purple aura of destruction."""
    key = {"bored": "beerus", "serious": "beerus_serious", "full": "beerus_full"}[form]
    skin, sh = BEERUS_SKIN, (110, 88, 128)
    head = skin_swap(head_paint(skin, (236, 222, 140), False, key), skin)
    gold, pants, black, turq, orange = BEERUS_GOLD, (30, 145, 205), (34, 32, 38), (40, 190, 200), (240, 130, 25)

    def chest(face, px, w, h, base):  # a slim, toned chest
        if face == "north":
            for y in range(int(h * 0.3), int(h * 0.36)):
                for x in range(int(w * 0.15), int(w * 0.45)):
                    _put(px, w, h, x, y, sh); _put(px, w, h, w - 1 - x, y, sh)
            for y in range(int(h * 0.45), int(h * 0.85)):
                _put(px, w, h, w // 2, y, sh)
    torso = layered(skin, [chest])
    arm = layered(skin, [region((0, 0.76, 1, 0.86), gold), region((0, 0.3, 1, 0.36), gold)])
    leg = layered(pants, [lines((SIDES, [[(0.3, 0), (0.25, 0.8)], [(0.7, 0), (0.75, 0.8)]]), dark(pants, 0.7)),
                          region((0, 0.8, 1, 0.88), gold), region((0, 0.88, 1, 1), (120, 100, 80))])
    base_body(m, torso, arm, leg, head)
    _strip_ears(m)
    both_legs(m, [-0.5, 2.6, -2.5], [4.9, 9.6, 5.0], layered(pants, [lines((SIDES, [[(0.5, 0), (0.45, 1)]]), dark(pants, 0.75))]))  # baggy
    both_legs(m, [0.4, 0, -3.6], [3.2, 1.2, 1.8], solid((120, 100, 80)))  # pointed slippers
    usekh = layered(turq, [lines((SIDES, [[(0, 0.33), (1, 0.33)], [(0, 0.66), (1, 0.66)]]), black, 2),
                           region((0, 0, 1, 0.12), gold), region((0, 0.88, 1, 1), gold), _diamonds([orange], [0.5], 0.16)])
    m.box("body", [-4.8, 20.4, -2.8], [9.6, 3.6, 5.6], usekh)                            # the usekh collar
    m.box("body", [-4.5, 11.0, -2.6], [9.0, 1.8, 5.2], layered(black, [region((0, 0, 1, 0.25), gold), region((0, 0.75, 1, 1), gold)]))
    sash = layered(black, [region((0, 0, 0.12, 1), gold), region((0.88, 0, 1, 1), gold),
                           _diamonds([(245, 245, 245), orange, (245, 245, 245)], [0.2, 0.5, 0.8], 0.2)])
    m.box("body", [-1.9, 3.2, -2.9], [3.8, 8.0, 0.4], sash)                              # the front sash panel
    def ear_shape(xf, u):  # a tall triangle, pink inside
        half = 0.5 * (1 - u) ** 0.85
        d = abs(xf - 0.5)
        if d > half:
            return None
        return (200, 150, 178) if d < half * 0.55 and u < 0.8 else skin
    ear = M._sprite(ear_shape)
    for s_ in (1, -1):  # the huge pointed ears, pink inside, gold rings at the base
        m.box("head", [s_ * 2.5 - 2.6, 30.6, 0.2], [5.2, 8.4, 0], ear, rot=[-8, 0, -s_ * 18], pivot=[s_ * 2.5, 30.6, 0.2])
        m.cubes[-1]["hires"] = 4
        m.box("head", [s_ * 2.5 - 2.2, 30.4, -0.2], [4.4, 1.4, 0.8], solid(skin), rot=[0, 0, -s_ * 18], pivot=[s_ * 2.5, 30.6, 0.2])
        m.box("head", [s_ * 4.2 - 0.35, 25.0, -0.5], [0.7, 1.6, 0.7], solid(gold))        # earrings
    tail = SC.swatch(skin)
    SC.curve_tube(m, "body", [[0, 12.5, 2.2], [0.5, 9, 5.5], [1.6, 4, 6.5], [2.6, 2.0, 4.6]], 0.45, 0.3, [tail, tail], n=2)
    if form == "full":  # wisps of destruction energy round his shoulders
        au = SC.swatch((150, 60, 210), 180)
        for k in range(5):
            a = math.pi * (0.15 + 0.7 * k / 4)
            SC.blade(m, "body", [math.cos(a) * 5.0, 21, math.sin(a) * 2.4 + 2.2], [math.cos(a) * 0.25, 1, 0.2], 4.4, 1.3, 0.4, au)


WHIS_SKIN = (130, 190, 205)


@M.smooth_hair
def whis_hair(m):
    # pure white hair combed straight up into one tall smooth column
    col = (245, 245, 250)
    hp = M.hair_paint(col)
    m.box("hair", [-4.2, 30.4, -3.6], [8.4, 2.2, 7.8], hp)
    m.box("hair", [-3.4, 32.4, -2.4], [6.8, 3.4, 6.0], hp)
    m.box("hair", [-2.8, 35.6, -1.8], [5.6, 3.4, 4.8], hp)
    m.box("hair", [-2.2, 38.8, -1.2], [4.4, 2.4, 3.6], hp)
    m.box("hair", [-1.4, 41.0, -0.6], [2.8, 1.0, 2.2], hp)


def whis(m, form):
    """Whis: a tall teal-skinned angel. White hair combed up into a tall column, violet eyes, a light-blue halo ring
    floating round his neck, a long maroon robe with a black chest cuirass and a diamond emblem, a blue sash, and his
    long silver staff topped by a floating dark orb. Angel: the halo and the orb glow, silver light round him."""
    angel = form == "angel"
    skin = WHIS_SKIN
    head = skin_swap(head_paint((245, 245, 250), (150, 90, 190), False, "whis_angel" if angel else "whis"), skin)
    robe, black, sash = (125, 25, 45), (30, 30, 36), (90, 130, 200)
    cuirass = lambda f, px, w, h, b: [[_put(px, w, h, x, y, (240, 240, 240) if (y == int(h * 0.55) or x in (0, w - 1)) else black)
                                       for x in range(w)] for y in range(int(h * 0.06), int(h * 0.56))] if f in ("north", "south") else None
    torso = layered(robe, [cuirass, _diamonds([(240, 130, 25)], [0.28], 0.13)])
    arm = layered(robe, [region((0, 0.0, 1, 0.3), black), region((0, 0.88, 1, 1), skin)])
    leg = layered(robe, [region((0, 0.9, 1, 1), (20, 20, 26))])
    base_body(m, torso, arm, leg, head)
    m.box("body", [-4.4, 11.2, -2.5], [8.8, 1.6, 5.0], solid(sash))                        # the sash
    m.box("body", [-4.7, 2.0, -2.7], [9.4, 9.2, 5.4], layered(robe, [lines((SIDES, [[(0.5, 0), (0.5, 1)]]), dark(robe, 0.7))]))  # robe skirt
    for s_ in (1, -1):  # white shoulder pads of the cuirass
        m.box("body", [s_ * 4.6 - 1.6, 22.0, -2.6], [3.2, 1.6, 5.2], layered(black, [region((0, 0.7, 1, 1), (240, 240, 240))]))
    halo = SC.swatch((150, 225, 255) if angel else (90, 190, 235), 235)
    for k in range(16):  # the halo ring round his neck
        a = 2 * math.pi * k / 16
        x, z = math.cos(a) * 6.2, math.sin(a) * 5.2
        m.box("body", [x - 0.8, 23.6, z - 0.8], [1.6, 0.8, 1.6], halo, rot=[0, -math.degrees(a), 0], pivot=[x, 24.0, z])
    staff = SC.swatch((205, 205, 215))
    m.box("rightArm", [5.75, -4.0, -0.3], [0.6, 36.0, 0.6], solid((205, 205, 215)))         # the long silver staff
    for k in range(10):  # its ring head
        a = 2 * math.pi * k / 10
        x, y = 6.05 + math.cos(a) * 1.8, 34.0 + math.sin(a) * 1.8
        m.box("rightArm", [x - 0.3, y - 0.3, -0.3], [0.6, 0.6, 0.6], staff)
    SC.blob(m, "rightArm", [6.05, 34.0, 0.0], [1.1, 1.1, 1.1], SC.swatch((20, 30, 60)))      # the floating dark orb
    SC.blob(m, "rightArm", [6.05, 34.0, 0.0], [0.55, 0.55, 0.55], SC.swatch((90, 230, 255) if angel else (60, 160, 220), 240))
    whis_hair(m)


FORMS.update({"beerus": ["bored", "serious", "full"], "whis": ["attendant", "angel"]})
_build_prev21 = build
_NEW21 = {"beerus": beerus, "whis": whis}


def build(char, form):  # noqa: F811
    if char in _NEW21:
        m = M.Model()
        _NEW21[char](m, form)
        return m
    return _build_prev21(char, form)
