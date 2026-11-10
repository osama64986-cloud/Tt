"""HD character models for Anime Battles.

Models are authored in Blockbench space (front = -Z, the character's right = +X,
rotations in degrees, Euler order ZYX) and converted to Bedrock geometry on export
the same way Blockbench does it. Textures are painted at S pixels per model unit
(S = 8 gives 64 x 64 faces) with anime cel shading.
"""
import math

from PIL import Image, ImageDraw

S = 8


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dark(c, f=0.75):
    return tuple(max(0, int(v * f)) for v in c)


def light(c, f=0.35):
    return mix(c, (255, 255, 255), f)


class Model:
    def __init__(self):
        self.cubes = []  # dict(bone, frm, size, pivot, rot, inflate, paint)

    def box(self, bone, frm, size, paint, rot=None, pivot=None, inflate=0.0):
        size = [max(0.0, round(s * 4) / 4) for s in size]
        self.cubes.append(dict(bone=bone, frm=list(frm), size=size, rot=rot, pivot=pivot, inflate=inflate, paint=paint))

    def strand(self, base, d, length, width, paint, bend=(0, 0, 0), segs=3, bone="hair", thick=None):
        """A tapered hair spike from `base` along direction `d`, optionally curving by `bend`."""
        widths = [width, width * 0.64, width * 0.32][:segs]
        lens = [0.46, 0.38, 0.34][:segs]
        p = list(base)
        d = norm(d)
        for i in range(segs):
            w = max(0.5, round(widths[i] * 4) / 4)
            t = max(0.5, round((thick or 0.8) * w * 4) / 4)
            seg_len = max(0.75, round(length * lens[i] * 4) / 4) + (0.5 if i < segs - 1 else 0)
            ax, az = math.degrees(math.asin(clampf(d[2]))), math.degrees(math.atan2(-d[0], d[1]))
            self.box(bone, [p[0] - w / 2, p[1], p[2] - t / 2], [w, seg_len, t], paint,
                     rot=[round(ax, 2), 0, round(az, 2)], pivot=[round(p[0], 3), round(p[1], 3), round(p[2], 3)])
            step = seg_len * 0.72
            p = [p[k] + d[k] * step for k in range(3)]
            d = norm([d[k] + bend[k] for k in range(3)])

    def mirror_strand(self, base, d, length, width, paint, bend=(0, 0, 0), **kw):
        self.strand(base, d, length, width, paint, bend, **kw)
        self.strand([-base[0], base[1], base[2]], [-d[0], d[1], d[2]], length, width, paint, (-bend[0], bend[1], bend[2]), **kw)


def norm(v):
    l = math.sqrt(sum(x * x for x in v)) or 1
    return [x / l for x in v]


def clampf(x):
    return max(-1.0, min(1.0, x))


# ------------------------------------------------------------------ painters
# A painter is f(face, img); img is the face's own RGBA image (w*S x h*S).
# face: north (front), south (back), east (character's right), west, up, down.

LIGHT = {"north": 1.0, "east": 0.9, "west": 0.8, "south": 0.74, "up": 1.06, "down": 0.55}
OUTLINE_K = 0.5


def _rng(seed):
    import random
    return random.Random(seed)


def cel(img, base, face, shadow=0.26, outline=True, grain=0.0, rim=True, seed=1):
    """Anime cel shading: flat lit tone, hard shadow band, rim light, dark outline, optional fabric grain."""
    w, h = img.size
    px = img.load()
    lit = mix(base, (255, 255, 255), 0.06) if face in ("north", "up") else base
    lit = tuple(min(255, int(v * LIGHT[face])) for v in lit)
    sh = mix(dark(lit, 0.74), (40, 30, 90), 0.08)
    r = _rng(seed + w * 31 + h)
    cut = h * (1 - shadow) if face not in ("up", "down") else h + 1
    for y in range(h):
        for x in range(w):
            c = sh if y >= cut else lit
            if grain:
                n = r.uniform(-grain, grain)
                c = tuple(max(0, min(255, int(v * (1 + n)))) for v in c)
            px[x, y] = c + (255,)
    if rim and face not in ("down",) and h > 6:
        for x in range(w):
            for y in range(max(1, S // 4)):
                px[x, y] = light(lit, 0.22) + (255,)
    if outline and w > 3 and h > 3:
        oc = dark(base, OUTLINE_K) + (255,)
        for x in range(w):
            px[x, 0] = oc if not rim else px[x, 0]
            px[x, h - 1] = oc
        for y in range(h):
            px[0, y] = oc
            px[w - 1, y] = oc


def solid(base, outline=True, grain=0.0, shadow=0.26):
    def p(face, img):
        cel(img, base, face, shadow=shadow, outline=outline, grain=grain)
    return p


def layered(base, details, grain=0.0, shadow=0.26):
    """Cel base + detail drawers f(face, draw, w, h, k) where k = S / 4 (pixel scale)."""
    def p(face, img):
        cel(img, base, face, shadow=shadow, grain=grain)
        dr = ImageDraw.Draw(img)
        for f in details:
            f(face, dr, img.size[0], img.size[1], S / 4)
    return p


def hair_paint(base):
    """Anime hair: dark root, bright tip, hard shadow side, glossy highlight streak, ink outline."""
    bright = sum(base) > 360

    def p(face, img):
        w, h = img.size
        px = img.load()
        tip = mix(base, (255, 255, 255), 0.28 if bright else 0.18)
        root = dark(base, 0.55 if bright else 0.5)
        shadow = mix(dark(base, 0.72), (60, 40, 120), 0.12)
        gloss = mix(base, (255, 255, 255), 0.7 if bright else 0.42)
        ink = dark(base, 0.35) if bright else (8, 8, 14)
        for y in range(h):
            t = 1 - y / max(1, h - 1)  # 1 at the tip
            row = mix(root, tip, t ** 0.8)
            for x in range(w):
                c = row
                if face in ("north", "south", "east", "west"):
                    u = x / max(1, w - 1)
                    if face in ("west", "south"):
                        c = mix(row, shadow, 0.55)
                    elif u < 0.3:
                        c = mix(row, shadow, 0.7)
                    if face in ("north", "east") and x == w - 2 and t > 0.35:
                        c = mix(c, gloss, 0.35)
                    if x == 0 or x == w - 1:
                        c = ink
                else:
                    c = mix(base, shadow, 0.35) if face == "up" else dark(base, 0.5)
                px[x, y] = c + (255,)
    return p


# ------------------------------------------------------------------ skin & muscles

SKIN = (250, 214, 182)
SKIN_SH = (222, 162, 132)
SKIN_INK = (120, 62, 48)


def muscle_arm(face, dr, w, h, k):
    """Bicep / forearm definition on a bare arm."""
    sh = SKIN_SH + (255,)
    hl = light(SKIN, 0.35) + (255,)
    if face in ("north", "south", "east", "west"):
        dr.arc([w * 0.12, h * 0.02, w * 0.88, h * 0.44], 20, 160, fill=sh, width=max(1, int(k)))
        dr.line([(w * 0.3, h * 0.12), (w * 0.4, h * 0.3)], fill=hl, width=max(1, int(k)))
        dr.line([(w * 0.2, h * 0.47), (w * 0.8, h * 0.5)], fill=sh, width=max(1, int(k)))
        dr.line([(w * 0.6, h * 0.55), (w * 0.7, h * 0.85)], fill=sh, width=1)


def skin_arm():
    return layered(SKIN, [muscle_arm], shadow=0.22)


def ears(m):
    for sx in (1, -1):
        x = 4 if sx == 1 else -4.75
        m.box("head", [x, 26.25, -0.75], [0.75, 2.25, 1.5], solid(SKIN, shadow=0.3))


# ------------------------------------------------------------------ faces (drawn on a 64 x 64 grid)

def _pt(pts, k, side):
    out = []
    for x, y in pts:
        xx = x if side == 0 else 63 - x
        out.append((xx * k, y * k))
    return out


def face_front(dr, w, style, hair, iris, brows, blindfold):
    k = w / 64.0
    ink = (24, 14, 14, 255)
    white = (255, 255, 255, 255)
    skin_sh = SKIN_SH + (255,)
    # hair shadow on the forehead (jagged like bangs)
    jag = [(0, 18)] + [(x, 28 if (x // 8) % 2 else 23) for x in range(0, 65, 4)] + [(64, 18)]
    dr.polygon([(x * k, y * k) for x, y in jag], fill=skin_sh)
    dr.rectangle([0, 0, w, 19 * k], fill=hair + (255,))
    if style == "vegeta":
        dr.polygon([(16 * k, 18 * k), (32 * k, 34 * k), (48 * k, 18 * k)], fill=hair + (255,))  # widow's peak
    # side shading (angular jaw)
    for side in (0, 1):
        dr.polygon(_pt([(0, 32), (3, 32), (5, 50), (11, 62), (11, 64), (0, 64)], k, side), fill=skin_sh)
    # nose + mouth
    dr.polygon([(33 * k, 40 * k), (35 * k, 46 * k), (31 * k, 46 * k)], fill=skin_sh)
    dr.line([(31 * k, 46 * k), (34 * k, 46 * k)], fill=SKIN_INK + (255,), width=max(1, int(k)))
    if style == "vegeta":
        dr.line([(25 * k, 53 * k), (27 * k, 51 * k), (37 * k, 51 * k), (39 * k, 53 * k)], fill=SKIN_INK + (255,), width=max(1, int(k)))
        dr.line([(18 * k, 42 * k), (21 * k, 45 * k)], fill=skin_sh, width=max(1, int(k)))
        dr.line([(46 * k, 42 * k), (43 * k, 45 * k)], fill=skin_sh, width=max(1, int(k)))
    elif style == "gojo":
        dr.line([(27 * k, 52 * k), (37 * k, 52 * k), (40 * k, 50 * k)], fill=SKIN_INK + (255,), width=max(1, int(k)))
    else:
        dr.line([(26 * k, 52 * k), (38 * k, 52 * k)], fill=SKIN_INK + (255,), width=max(1, int(k)))
        dr.line([(29 * k, 55 * k), (35 * k, 55 * k)], fill=skin_sh, width=max(1, int(k)))
    dr.line([(18 * k, 63 * k), (46 * k, 63 * k)], fill=skin_sh, width=max(1, int(k)))  # chin line

    if blindfold:
        band = (16, 16, 22, 255)
        dr.rectangle([0, 22 * k, w, 41 * k], fill=band)
        dr.line([(0, 23 * k), (w, 23 * k)], fill=(52, 52, 66, 255), width=max(1, int(k)))
        for x0, y0, x1, y1 in ((6, 30, 22, 27), (40, 27, 58, 31), (24, 36, 40, 35)):
            dr.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=(40, 40, 54, 255), width=max(1, int(k)))
        dr.line([(0, 40 * k), (w, 40 * k)], fill=(6, 6, 10, 255), width=max(1, int(k)))
        return

    for side in (0, 1):
        P = lambda pts: _pt(pts, k, side)  # noqa: E731
        if style == "gojo":
            dr.polygon(P([(10, 33), (15, 28), (27, 28), (29, 31), (27, 41), (14, 41)]), fill=white)
            dr.ellipse(sorted_pts(P([(17, 28), (27, 41)])), fill=mix(iris, (255, 255, 255), 0.25) + (255,))
            dr.ellipse(sorted_pts(P([(18, 32), (26, 41)])), fill=iris + (255,))
            dr.ellipse(sorted_pts(P([(19, 36), (25, 41)])), fill=dark(iris, 0.55) + (255,))
            dr.ellipse(sorted_pts(P([(20, 33), (24, 38)])), fill=(18, 40, 90, 255))
            dr.rectangle(sorted_pts(P([(19, 30), (21, 33)])), fill=white)
            dr.point(P([(24, 38)])[0], fill=white)
            dr.line(P([(8, 34), (14, 28), (28, 27), (31, 30)]), fill=(245, 245, 252, 255), width=max(2, int(2 * k)))
            dr.line(P([(8, 34), (14, 28), (28, 27), (31, 30)]), fill=(150, 150, 170, 255), width=1)
            dr.line(P([(9, 30), (6, 28)]), fill=(245, 245, 252, 255), width=max(1, int(k)))
            if brows:
                dr.line(P([(9, 22), (20, 20), (29, 22)]), fill=(240, 240, 248, 255), width=max(1, int(1.5 * k)))
            continue
        angry = style == "vegeta"
        top = 33 if angry else 31
        bot = 38 if angry else 39
        dr.polygon(P([(12, top + 3), (16, top), (26, top), (28, top + 2), (26, bot), (15, bot)]), fill=white)
        dr.ellipse(sorted_pts(P([(19, top - 1), (26, bot + 1)])), fill=iris + (255,))
        dr.ellipse(sorted_pts(P([(21, top + 2), (25, bot)])), fill=dark(iris, 0.3) + (255,))
        dr.rectangle(sorted_pts(P([(20, top + 1), (21, top + 3)])), fill=white)
        lash_w = max(2, int((4 if angry else 3) * k))
        if angry:
            dr.line(P([(10, top + 1), (16, top - 1), (27, top + 1), (29, top + 3)]), fill=ink, width=lash_w)
        else:
            dr.line(P([(11, top + 4), (15, top), (26, top), (28, top + 2)]), fill=ink, width=lash_w)
        dr.line(P([(16, bot), (25, bot)]), fill=SKIN_INK + (255,), width=max(1, int(k)))
        brow_col = (dark(hair, 0.75) if sum(hair) > 360 else (22, 18, 22)) + (255,)
        if brows:
            if angry:
                dr.polygon(P([(9, 24), (29, 30), (29, 33), (9, 27)]), fill=brow_col)
                dr.line(P([(30, 26), (31, 31)]), fill=skin_sh, width=max(1, int(k)))  # frown crease
            elif style == "calm":
                dr.polygon(P([(10, 25), (28, 26), (28, 28), (10, 27)]), fill=brow_col)
            else:
                dr.polygon(P([(9, 24), (28, 27), (28, 30), (9, 27)]), fill=brow_col)
                dr.line(P([(30, 27), (31, 30)]), fill=skin_sh, width=max(1, int(k)))
        else:
            dr.line(P([(10, 27), (29, 29)]), fill=skin_sh, width=max(2, int(2 * k)))  # SSJ3 brow ridge
            dr.line(P([(14, 24), (28, 26)]), fill=skin_sh, width=max(1, int(k)))


def sorted_pts(p):
    (x0, y0), (x1, y1) = p
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def sorted_box(x0, y0, x1, y1):
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def head_paint(hair, iris, brows=True, style="goku", blindfold=False):
    def p(face, img):
        w, h = img.size
        if face == "up":
            cel(img, hair, face, outline=False)
            return
        if face == "down":
            cel(img, SKIN_SH, face, outline=False)
            return
        cel(img, SKIN, face, shadow=0.0 if face == "north" else 0.18, outline=False, rim=False)
        dr = ImageDraw.Draw(img)
        k = w / 64.0
        if face == "south":
            dr.rectangle([0, 0, w, h * 0.85], fill=hair + (255,))
            return
        if face in ("east", "west"):
            dr.rectangle([0, 0, w, h * 0.38], fill=hair + (255,))
            front = w if face == "east" else 0
            dr.rectangle(sorted_box(front - 10 * k, h * 0.38, front + 10 * k, h * 0.62), fill=hair + (255,))
            dr.rectangle([0, h * 0.78, w, h], fill=SKIN_SH + (255,))
            if blindfold:
                dr.rectangle([0, 22 * k, w, 41 * k], fill=(16, 16, 22, 255))
            return
        face_front(dr, w, style, hair, iris, brows, blindfold)
    return p


def base_body(m, torso, arm, leg, head):
    m.box("head", [-4, 24, -4], [8, 8, 8], head)
    m.box("body", [-4, 12, -2], [8, 12, 4], torso)
    m.box("rightArm", [4, 12, -2], [4, 12, 4], arm)
    m.box("leftArm", [-8, 12, -2], [4, 12, 4], arm)
    m.box("rightLeg", [-0.1, 0, -2], [4, 12, 4], leg)
    m.box("leftLeg", [-3.9, 0, -2], [4, 12, 4], leg)
    ears(m)


def both_arms(m, frm, size, paint, **kw):
    """frm is given for the right arm (+X); the left arm is mirrored."""
    m.box("rightArm", frm, size, paint, **kw)
    m.box("leftArm", [-(frm[0] + size[0]), frm[1], frm[2]], size, paint, **kw)


def both_legs(m, frm, size, paint, **kw):
    m.box("rightLeg", frm, size, paint, **kw)
    m.box("leftLeg", [-(frm[0] + size[0]), frm[1], frm[2]], size, paint, **kw)


def lines(spec, col, width=1):
    """Detail drawer: list of polylines in 0..1 face coordinates, for the given faces."""
    faces, polys = spec

    def f(face, dr, w, h, k):
        if face not in faces:
            return
        for poly in polys:
            dr.line([(x * (w - 1), y * (h - 1)) for x, y in poly], fill=col + (255,), width=max(1, int(width * k)))
    return f


# ------------------------------------------------------------------ Goku

GI = (238, 112, 18)
GI_BLUE = (28, 50, 160)
BOOT_BLUE = (26, 42, 128)
SIDES = ("north", "south", "east", "west")


def gi_front(face, dr, w, h, k):
    if face != "north":
        return
    # V-neck with the blue undershirt
    dr.polygon([(w * 0.28, 0), (w * 0.72, 0), (w * 0.5, h * 0.36)], fill=GI_BLUE + (255,))
    dr.line([(w * 0.26, 0), (w * 0.5, h * 0.38), (w * 0.74, 0)], fill=dark(GI, 0.55) + (255,), width=max(2, int(k * 1.5)))
    # chest symbol (character's left = viewer's right)
    cx, cy, r = w * 0.76, h * 0.2, w * 0.11
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(252, 250, 244, 255), outline=(20, 20, 20, 255), width=max(1, int(k)))
    kanji(dr, cx, cy, r * 0.7, k)
    # folds
    for a, b in (((0.08, 0.38), (0.34, 0.95)), ((0.92, 0.38), (0.66, 0.95)), ((0.2, 0.6), (0.38, 0.98))):
        dr.line([(a[0] * w, a[1] * h), (b[0] * w, b[1] * h)], fill=dark(GI, 0.7) + (255,), width=max(1, int(k)))
        dr.line([(a[0] * w + 2 * k, a[1] * h), (b[0] * w + 2 * k, b[1] * h)], fill=light(GI, 0.25) + (255,), width=1)


def gi_back(face, dr, w, h, k):
    if face != "south":
        return
    cx, cy, r = w * 0.5, h * 0.3, w * 0.24
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(252, 250, 244, 255), outline=(20, 20, 20, 255), width=max(2, int(2 * k)))
    kanji(dr, cx, cy, r * 0.72, k * 2)
    for x in (0.2, 0.8):
        dr.line([(x * w, h * 0.62), (x * w + 3 * k, h)], fill=dark(GI, 0.7) + (255,), width=max(1, int(k)))


def kanji(dr, cx, cy, r, k):
    """A bold brush-style kanji (悟-like) built from strokes."""
    c = (18, 18, 18, 255)
    wd = max(1, int(1.3 * k))
    dr.line([(cx - r * 0.75, cy - r * 0.55), (cx - r * 0.75, cy + r * 0.8)], fill=c, width=wd)
    dr.line([(cx - r * 1.0, cy - r * 0.15), (cx - r * 0.5, cy - r * 0.35)], fill=c, width=wd)
    dr.line([(cx - r * 0.2, cy - r * 0.75), (cx + r * 0.9, cy - r * 0.75)], fill=c, width=wd)
    dr.line([(cx + r * 0.3, cy - r * 0.75), (cx + r * 0.2, cy - r * 0.05)], fill=c, width=wd)
    dr.line([(cx - r * 0.2, cy - r * 0.05), (cx + r * 0.9, cy - r * 0.05)], fill=c, width=wd)
    dr.rectangle([cx - r * 0.1, cy + r * 0.25, cx + r * 0.8, cy + r * 0.85], outline=c, width=wd)


def goku_body(m, hair, iris, brows=True, style="goku"):
    base_body(m, solid(GI_BLUE), skin_arm(), solid(GI), head_paint(hair, iris, brows, style))
    m.box("body", [-4.25, 12.5, -2.3], [8.5, 11.75, 4.6], layered(GI, [gi_front, gi_back], grain=0.03))
    m.box("body", [-4.4, 9.5, -2.45], [8.8, 3.25, 4.9],
          layered(GI, [lines((SIDES, [[(0.2, 0), (0.15, 1)], [(0.75, 0), (0.85, 1)]]), dark(GI, 0.7))], grain=0.03))
    m.box("body", [-0.5, 18, -2.6], [1, 6.5, 0.5], solid(dark(GI, 0.85)), rot=[0, 0, -26], pivot=[0, 18, -2.6])
    m.box("body", [-0.5, 18, -2.6], [1, 6.5, 0.5], solid(dark(GI, 0.85)), rot=[0, 0, 26], pivot=[0, 18, -2.6])
    belt = layered(GI_BLUE, [lines((SIDES, [[(0, 0.5), (1, 0.45)]]), light(GI_BLUE, 0.25))])
    m.box("body", [-4.6, 12, -2.6], [9.2, 1.75, 5.2], belt)
    m.box("body", [-1.25, 11.5, 2.4], [2.5, 2.25, 1], solid(dark(GI_BLUE, 0.9)))
    m.strand([-0.6, 12, 3], [-0.35, -1, 0.25], 4.5, 1.25, solid(GI_BLUE), bone="body", segs=2)
    m.strand([0.6, 12, 3], [0.35, -1, 0.3], 4, 1.25, solid(GI_BLUE), bone="body", segs=2)
    both_arms(m, [3.75, 19.25, -2.25], [4.5, 5, 4.5], layered(GI_BLUE, [lines((SIDES, [[(0, 0.85), (1, 0.85)]]), dark(GI_BLUE, 0.6))]))
    wb = layered(GI_BLUE, [lines((SIDES, [[(0, 0.18), (1, 0.18)], [(0, 0.82), (1, 0.82)]]), light(GI_BLUE, 0.3))])
    both_arms(m, [3.6, 12, -2.4], [4.8, 3.25, 4.8], wb)
    pants = layered(GI, [lines((SIDES, [[(0.5, 0.05), (0.55, 0.6), (0.4, 1)], [(0.15, 0.3), (0.3, 0.9)]]), dark(GI, 0.68))], grain=0.03)
    both_legs(m, [-0.4, 5, -2.4], [4.6, 7, 4.8], pants)
    both_legs(m, [-0.3, 0, -2.3], [4.4, 5.25, 4.6], layered(BOOT_BLUE, [laces]))
    both_legs(m, [-0.5, 4.5, -2.5], [4.8, 1.25, 5], solid(dark(BOOT_BLUE, 0.8)))
    both_legs(m, [0.1, 0, -3.3], [3.6, 1.75, 1.25], solid(BOOT_BLUE))
    both_legs(m, [-0.35, 0, -2.4], [4.5, 0.5, 4.8], solid((228, 214, 186)))


def laces(face, dr, w, h, k):
    if face != "north":
        return
    red = (214, 34, 34, 255)
    step = int(6 * k)
    for y in range(int(3 * k), h - int(4 * k), step):
        dr.line([(w * 0.2, y), (w * 0.8, y + step * 0.6)], fill=red, width=max(1, int(k)))
        dr.line([(w * 0.8, y), (w * 0.2, y + step * 0.6)], fill=red, width=max(1, int(k)))


# ------------------------------------------------------------------ Vegeta

SUIT = (24, 38, 120)
ARMOR = (238, 238, 230)
ARMOR_SH = (176, 178, 186)
ARMOR_GOLD = (214, 164, 40)


def armor_chest(face, dr, w, h, k):
    gold_top = h * 0.7
    if face in SIDES:
        dr.rectangle([0, gold_top, w, h], fill=ARMOR_GOLD + (255,))
        dr.line([(0, gold_top), (w, gold_top)], fill=dark(ARMOR_GOLD, 0.55) + (255,), width=max(1, int(k)))
        dr.line([(0, gold_top + 3 * k), (w, gold_top + 3 * k)], fill=light(ARMOR_GOLD, 0.5) + (255,), width=1)
        for x in (0.25, 0.5, 0.75):
            dr.line([(x * w, gold_top), (x * w, h)], fill=dark(ARMOR_GOLD, 0.6) + (255,), width=max(1, int(k)))
    if face == "north":
        sh = ARMOR_SH + (255,)
        dr.arc([w * 0.06, h * 0.05, w * 0.5, h * 0.55], 15, 165, fill=sh, width=max(2, int(1.5 * k)))
        dr.arc([w * 0.5, h * 0.05, w * 0.94, h * 0.55], 15, 165, fill=sh, width=max(2, int(1.5 * k)))
        dr.line([(w * 0.5, h * 0.05), (w * 0.5, gold_top)], fill=sh, width=max(1, int(k)))
        dr.line([(w * 0.2, h * 0.12), (w * 0.35, h * 0.1)], fill=(255, 255, 255, 255), width=max(1, int(k)))


def suit_muscle(face, dr, w, h, k):
    if face in SIDES:
        hl = light(SUIT, 0.25) + (255,)
        dr.arc([w * 0.15, h * 0.05, w * 0.85, h * 0.6], 200, 340, fill=hl, width=max(1, int(k)))
        dr.line([(w * 0.25, h * 0.7), (w * 0.75, h * 0.72)], fill=dark(SUIT, 0.6) + (255,), width=max(1, int(k)))


def vegeta_body(m, hair, iris):
    base_body(m, solid(SUIT), layered(SUIT, [suit_muscle]), layered(SUIT, [lines((SIDES, [[(0.5, 0.1), (0.45, 0.9)]]), dark(SUIT, 0.65))]), head_paint(hair, iris, True, "vegeta"))
    m.box("body", [-4.5, 14.5, -2.75], [9, 9.25, 5.5], layered(ARMOR, [armor_chest], shadow=0.0))
    m.box("body", [-3, 23.5, -2.25], [6, 1, 4.5], solid(SUIT))
    pad = layered(ARMOR_GOLD, [lines((SIDES + ("up",), [[(0.1, 0.3), (0.9, 0.3)]]), light(ARMOR_GOLD, 0.6))])
    both_arms(m, [3.6, 21.5, -2.6], [4.8, 2.5, 5.2], pad)
    glove = layered(ARMOR, [lines((SIDES, [[(0, 0.25), (1, 0.25)], [(0.3, 0.6), (0.3, 1)], [(0.6, 0.6), (0.6, 1)]]), ARMOR_SH)])
    both_arms(m, [3.6, 12, -2.4], [4.8, 4.75, 4.8], glove)
    boot = layered(ARMOR, [band(SIDES, 0, 0.2, "gold"),
                           lines((SIDES, [[(0.2, 0.4), (0.5, 0.55), (0.8, 0.4)]]), ARMOR_SH)])
    both_legs(m, [-0.35, 0, -2.35], [4.5, 6.5, 4.7], boot)
    both_legs(m, [0.1, 0, -3.45], [3.6, 2, 1.25], layered(ARMOR_GOLD, [lines((("north", "up"), [[(0.1, 0.25), (0.9, 0.25)]]), light(ARMOR_GOLD, 0.6))]))


# ------------------------------------------------------------------ Gojo

UNI = (20, 23, 38)
UNI_HI = (52, 60, 92)


def jacket(face, dr, w, h, k):
    if face == "north":
        dr.line([(w * 0.5, 0), (w * 0.5, h)], fill=(6, 6, 12, 255), width=max(1, int(k)))
        dr.line([(w * 0.5 + k * 1.5, 0), (w * 0.5 + k * 1.5, h)], fill=UNI_HI + (255,), width=1)
        for x in (0.15, 0.85):
            dr.line([(w * x, h * 0.1), (w * x, h)], fill=UNI_HI + (255,), width=1)
    if face in ("east", "west", "south"):
        dr.line([(w * 0.5, h * 0.05), (w * 0.5, h)], fill=(8, 8, 14, 255), width=max(1, int(k)))
        dr.line([(w * 0.2, 0), (w * 0.2, h)], fill=UNI_HI + (255,), width=1)


def collar(face, dr, w, h, k):
    if face == "north":
        cx, cy, r = w / 2, h / 2, min(w, h) * 0.32
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(216, 176, 70, 255), outline=(110, 80, 24, 255), width=max(1, int(k)))
        dr.arc([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55], 0, 290, fill=(110, 80, 24, 255), width=max(1, int(k)))
    if face in SIDES:
        dr.line([(0, 1), (w, 1)], fill=UNI_HI + (255,), width=1)


def gojo_body(m, hair, iris, blindfold):
    hand = layered(UNI, [band(SIDES + ("down",), 0.9, 1.0, "skin"),
                         lines((SIDES, [[(0, 0.1), (1, 0.1)]]), UNI_HI)])
    base_body(m, solid(UNI), hand, layered(UNI, [lines((SIDES, [[(0.5, 0), (0.5, 1)]]), UNI_HI)]),
              head_paint(hair, iris, not blindfold, "gojo", blindfold))
    m.box("body", [-4.3, 9, -2.3], [8.6, 15, 4.6], layered(UNI, [jacket], grain=0.04))
    m.box("body", [-3.25, 23.5, -2.6], [6.5, 2.5, 5.2], layered(UNI_HI, [collar]))
    both_arms(m, [3.8, 15, -2.2], [4.4, 9, 4.4], layered(UNI, [lines((SIDES, [[(0.3, 0.2), (0.35, 0.9)]]), UNI_HI)], grain=0.04))
    both_arms(m, [3.7, 13.5, -2.3], [4.6, 1.5, 4.6], solid(UNI_HI))
    shoe = layered((12, 12, 16), [lines((("north", "up"), [[(0.2, 0.3), (0.8, 0.3)]]), (90, 90, 110))])
    both_legs(m, [-0.3, 0, -2.6], [4.4, 1.5, 5], shoe)
    if blindfold:
        bf = layered((16, 16, 22), [lines((SIDES, [[(0, 0.2), (1, 0.3)], [(0, 0.7), (1, 0.6)]]), (46, 46, 60))])
        m.box("head", [-4.3, 26.25, -4.3], [8.6, 2.5, 8.6], bf)
        m.box("head", [-0.75, 26.25, 4.2], [1.5, 2.25, 0.75], solid((16, 16, 22)))
        m.strand([-0.4, 26.5, 4.6], [-0.3, -1, 0.35], 3.5, 1, solid((16, 16, 22)), bone="head", segs=2)
        m.strand([0.4, 26.5, 4.6], [0.3, -1, 0.4], 3, 1, solid((16, 16, 22)), bone="head", segs=2)


def goku_hair_base(m, c):
    hp = hair_paint(c)
    m.box("hair", [-4.4, 29, -4.4], [8.8, 3.75, 8.8], hp)
    m.box("hair", [-4.5, 25, 0.25], [9, 7.5, 4.25], hp)
    # bangs over the forehead
    m.strand([-2.3, 31.75, -4.1], [-0.3, -1, -0.45], 3.25, 3.25, hp)
    m.strand([0.4, 32, -4.2], [0.05, -1, -0.5], 3, 3, hp)
    m.strand([2.6, 31.75, -4.1], [0.4, -1, -0.4], 2.75, 2.75, hp)
    # big tufts
    m.strand([0.3, 32.25, -1.2], [0.1, 1, 0.3], 7, 5, hp, bend=(0, 0, 0.2))
    m.mirror_strand([2.8, 32, -0.4], [0.85, 1, 0.05], 7, 4.75, hp, bend=(0.15, -0.25, 0))
    m.mirror_strand([4.1, 30, 0.8], [1, 0.25, 0.2], 6, 4.25, hp, bend=(0, -0.25, 0))
    m.mirror_strand([3.7, 28.5, 2.6], [0.9, -0.35, 0.6], 5, 3.5, hp)
    m.strand([0, 31.5, 3], [0, 0.5, 1], 6.5, 4.75, hp, bend=(0, -0.15, 0))
    m.mirror_strand([2.4, 30, 3.6], [0.5, 0, 1], 5.5, 3.75, hp)
    m.strand([0, 27.75, 4.1], [0, -0.6, 1], 4.5, 3.75, hp)
    m.mirror_strand([4.2, 28.75, -2.3], [0.05, -1, -0.1], 2.75, 1.75, hp, segs=2)


def goku_hair_ssj(m, c):
    hp = hair_paint(c)
    m.box("hair", [-4.4, 29, -4.4], [8.8, 3.75, 8.8], hp)
    m.box("hair", [-4.5, 25.5, 0.5], [9, 7, 4], hp)
    m.strand([-1, 31.75, -4.3], [-0.15, -1, -0.3], 5, 2, hp)  # the single bang
    m.mirror_strand([2.2, 32, -3.3], [0.3, 1, -0.35], 6, 3.75, hp)
    m.strand([0, 32.25, -0.5], [0, 1, 0.12], 9, 5.25, hp)
    m.mirror_strand([2.6, 32, -0.25], [0.45, 1, 0.05], 8.5, 4.75, hp)
    m.mirror_strand([4, 30.75, 1], [0.95, 0.9, 0.15], 7, 4.25, hp)
    m.mirror_strand([3.9, 29, 2.6], [1, 0.4, 0.5], 5.5, 3.5, hp)
    m.strand([0, 31.5, 3], [0, 0.85, 0.65], 8, 4.75, hp)
    m.mirror_strand([2.4, 30.75, 3.4], [0.45, 0.75, 0.65], 6.5, 3.75, hp)
    m.strand([0, 28.25, 4.1], [0, 0.1, 1], 4.75, 3.75, hp)
    m.mirror_strand([4.2, 28.75, -2.3], [0.05, -1, -0.1], 2.75, 1.75, hp, segs=2)


def goku_hair_ssj3(m, c):
    hp = hair_paint(c)
    m.box("hair", [-4.4, 29, -4.4], [8.8, 3.75, 8.8], hp)
    m.box("hair", [-4.6, 22, 0.25], [9.2, 10, 4.5], hp)
    m.strand([0, 29, 4.2], [0, -1, 0.12], 22, 8.5, hp, thick=0.5)
    m.mirror_strand([3.2, 29, 3.2], [0.22, -1, 0.15], 19, 5, hp, thick=0.6)
    m.mirror_strand([4.4, 29.5, 0.2], [0.28, -1, 0.05], 11, 3.5, hp)
    m.strand([0, 32.25, -0.5], [0, 1, 0.35], 6.5, 5, hp)
    m.mirror_strand([2.6, 32, -0.5], [0.6, 1, 0.15], 6, 4.25, hp)
    m.strand([-2.3, 31.5, -4.1], [-0.3, -1, -0.4], 5, 3.25, hp)
    m.strand([0.4, 31.75, -4.2], [0.05, -1, -0.45], 5.5, 3, hp)
    m.strand([2.6, 31.5, -4.1], [0.4, -1, -0.35], 4.5, 2.75, hp)


def vegeta_hair(m, c):
    hp = hair_paint(c)
    m.box("hair", [-4.4, 29.25, -4.4], [8.8, 3.5, 8.8], hp)
    m.box("hair", [-4.5, 26, 0], [9, 6.5, 4.5], hp)
    m.box("hair", [-0.75, 28.75, -4.35], [1.5, 2.5, 0.5], hp, rot=[0, 0, 45], pivot=[0, 29.5, -4.1])  # widow's peak
    m.box("hair", [-3.75, 31.5, -3.25], [7.5, 5, 6.75], hp)  # flame body
    m.box("hair", [-2.75, 35.5, -2.25], [5.5, 3.5, 5], hp)
    m.strand([0, 37.5, 0], [0, 1, 0.12], 7.5, 4.5, hp)
    m.mirror_strand([2.2, 34, -1.6], [0.18, 1, -0.05], 7.5, 4, hp)
    m.mirror_strand([3.2, 32.5, 1], [0.32, 1, 0.2], 7.5, 4, hp)
    m.strand([0, 34, 2.4], [0, 1, 0.35], 8, 4.5, hp)
    m.strand([0, 34, -2.4], [0, 1, -0.06], 6.5, 4, hp)
    m.mirror_strand([3.9, 30.5, -1.5], [0.4, 1, 0], 5, 3, hp)


def gojo_hair_up(m, c):
    hp = hair_paint(c)
    m.box("hair", [-4.25, 29, -4.25], [8.5, 3.5, 8.5], hp)
    m.box("hair", [-4.3, 25, 0.75], [8.6, 3.75, 3.6], hp)
    m.strand([0, 32, 0], [0, 1, 0.05], 6.5, 4.25, hp)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, z = math.sin(a) * 3.1, -math.cos(a) * 3.1
        m.strand([x, 31.5, z], [math.sin(a) * 0.75, 1, -math.cos(a) * 0.75], 5.5, 3.5, hp, bend=(0, -0.1, 0))
    for k in range(8):
        a = k * math.pi / 4
        x, z = math.sin(a) * 4, -math.cos(a) * 4
        if z < -3:
            continue  # keep the blindfold visible
        m.strand([x, 29.25, z], [math.sin(a), 0.55, -math.cos(a)], 4, 3, hp)


def gojo_hair_down(m, c):
    hp = hair_paint(c)
    m.box("hair", [-4.3, 29.25, -4.3], [8.6, 3.25, 8.6], hp)
    m.box("hair", [-4.6, 30.25, -4.6], [9.2, 2, 9.2], hp)
    for x, l in ((-3.1, 3.5), (-1.6, 3.75), (0, 4.75), (1.6, 3.75), (3.1, 3.5)):
        m.strand([x, 31.5, -4.2], [x * 0.06, -1, -0.45], l, 2, hp)
    m.mirror_strand([4.2, 30.5, -1.5], [0.15, -1, -0.05], 4.75, 2.5, hp)
    m.mirror_strand([4.2, 30.5, 1.5], [0.2, -1, 0.15], 5.25, 2.5, hp)
    for x in (-2.6, 0, 2.6):
        m.strand([x, 31.5, 4.1], [x * 0.05, -1, 0.3], 6, 3, hp)
    m.strand([0, 32.5, 0], [0, 1, 0.5], 2.75, 3, hp)
    m.mirror_strand([2, 32.25, 1], [0.6, 1, 0.3], 2.5, 2.25, hp)


# ------------------------------------------------------------------ registry

def build(char, form):
    m = Model()
    if char == "goku":
        hair, iris, brows, hair_fn, style = {
            "base": ((26, 24, 34), (40, 34, 40), True, goku_hair_base, "goku"),
            "ssj": ((255, 208, 40), (0, 172, 160), True, goku_hair_ssj, "goku"),
            "ssj3": ((255, 198, 30), (0, 172, 160), False, goku_hair_ssj3, "goku"),
            "ssg": ((228, 46, 96), (210, 30, 60), True, goku_hair_base, "goku"),   # Super Saiyan God: crimson hair, red eyes, base silhouette
            "ssb": ((40, 176, 255), (30, 126, 236), True, goku_hair_ssj, "goku"),
            "ui": ((214, 222, 240), (176, 186, 214), True, goku_hair_base, "calm"),
        }[form]
        goku_body(m, hair, iris, brows, style)
        hair_fn(m, hair)
    elif char == "vegeta":
        hair, iris = {
            "base": ((22, 22, 32), (36, 30, 36)),
            "ssj": ((255, 208, 40), (0, 172, 160)),
            "ssg": ((214, 38, 78), (204, 28, 54)),
            "ssb": ((40, 176, 255), (30, 126, 236)),
            "ue": ((164, 48, 222), (214, 56, 186)),
        }[form]
        vegeta_body(m, hair, iris)
        vegeta_hair(m, hair)
    elif char == "gojo":
        hair = (244, 246, 252)
        if form == "blindfold":
            gojo_body(m, hair, None, True)
            gojo_hair_up(m, hair)
        else:
            gojo_body(m, hair, (70, 205, 255), False)
            gojo_hair_down(m, hair)
    return m


FORMS = {
    "goku": ["base", "ssj", "ssj3", "ssg", "ssb", "ui"],
    "vegeta": ["base", "ssj", "ssg", "ssb", "ue"],
    "gojo": ["blindfold", "eyes"],
}

BONES = [
    {"name": "root", "pivot": [0, 0, 0]},
    {"name": "body", "parent": "root", "pivot": [0, 24, 0]},
    {"name": "head", "parent": "body", "pivot": [0, 24, 0]},
    {"name": "hair", "parent": "head", "pivot": [0, 24, 0]},
    {"name": "rightArm", "parent": "body", "pivot": [-5, 22, 0]},
    {"name": "leftArm", "parent": "body", "pivot": [5, 22, 0]},
    {"name": "rightLeg", "parent": "root", "pivot": [-1.9, 12, 0]},
    {"name": "leftLeg", "parent": "root", "pivot": [1.9, 12, 0]},
]


# ------------------------------------------------------------------ texture + geometry export


def face_rects(u, v, size):
    w, h, d = [int(round(s * S)) for s in size]
    return {
        "east": (u, v + d, d, h), "north": (u + d, v + d, w, h), "west": (u + d + w, v + d, d, h),
        "south": (u + 2 * d + w, v + d, w, h), "up": (u + d, v, w, d), "down": (u + d + w, v, w, d),
    }


def pack(cubes):
    rects = []
    for i, c in enumerate(cubes):
        w, h, d = [int(round(s * S)) for s in c["size"]]
        rects.append((i, 2 * d + 2 * w, d + h))
    order = sorted(rects, key=lambda r: -r[2])
    for tex in (256, 512, 1024):
        x = y = shelf = 0
        out = {}
        ok = True
        for i, bw, bh in order:
            if x + bw > tex:
                x, y, shelf = 0, y + shelf, 0
            if y + bh > tex:
                ok = False
                break
            out[i] = (x, y)
            x += bw
            shelf = max(shelf, bh)
        if ok:
            return tex, [out[i] for i in range(len(cubes))]
    raise RuntimeError("texture too small")


def export(m, identifier):
    tex, uvs = pack(m.cubes)
    img = Image.new("RGBA", (tex, tex), (0, 0, 0, 0))
    for c, (u, v) in zip(m.cubes, uvs):
        for face, (x, y, w, h) in face_rects(u, v, c["size"]).items():
            if w <= 0 or h <= 0:
                continue
            fimg = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            c["paint"](face, fimg)
            img.paste(fimg, (x, y))
    bone_list = getattr(m, "bones", BONES)
    bones = {b["name"]: dict(b, cubes=[]) for b in bone_list}
    for c, (u, v) in zip(m.cubes, uvs):
        fx, fy, fz = c["frm"]
        sx, sy, sz = c["size"]
        cube = {"origin": [round(-(fx + sx), 3), round(fy, 3), round(fz, 3)], "size": c["size"], "uv": [u / S, v / S]}
        if c["inflate"]:
            cube["inflate"] = c["inflate"]
        if c["rot"]:
            px, py, pz = c["pivot"]
            cube["pivot"] = [round(-px, 3), py, pz]
            rx, ry, rz = c["rot"]
            cube["rotation"] = [round(-rx, 2), round(-ry, 2), round(rz, 2)]
        bones[c["bone"]]["cubes"].append(cube)
    out_bones = []
    for b in bone_list:
        bb = bones[b["name"]]
        if not bb["cubes"]:
            del bb["cubes"]
        out_bones.append(bb)
    geo = {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": identifier, "texture_width": tex // S, "texture_height": tex // S,
                "visible_bounds_width": 4, "visible_bounds_height": 4.5, "visible_bounds_offset": [0, 1.75, 0],
            },
            "bones": out_bones,
        }],
    }
    head = face_rects(*uvs[0], m.cubes[0]["size"])["north"]
    return geo, img, head


# ==================================================================================
# PIXEL-ART PASS (overrides the HD painters above).
# Research on the most downloaded Bedrock Dragon Ball add-ons showed that the
# "premium Minecraft" look comes from native-resolution pixel art: hand-picked
# 5-tone shade ramps, per-pixel noise/dithering, edge occlusion, and faces drawn
# pixel by pixel. Smooth HD shading reads as soft/plastic, so we paint like that.
# ==================================================================================
S = 2  # 16 x 16 faces, crisp pixel art

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
FACE_LIGHT = {"north": 0.0, "east": -0.35, "west": -0.7, "south": -0.9, "up": 0.5, "down": -1.6}


def ramp(base):
    """5-tone ramp: deep shadow (hue-shifted cool), shadow, base, light, highlight (warm)."""
    return [
        mix(dark(base, 0.52), (30, 20, 70), 0.18),
        mix(dark(base, 0.74), (40, 30, 80), 0.08),
        base,
        mix(light(base, 0.18), (255, 240, 200), 0.05),
        mix(light(base, 0.4), (255, 245, 210), 0.1),
    ]


def _hash(x, y, s):
    v = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    v = (v ^ (v >> 13)) * 1274126177 & 0xFFFFFFFF
    return (v & 0xFFFF) / 65535.0


def pixel_mat(img, base, face, noise=0.35, vgrad=1.0, ao=True, seed=0):
    """Paint a material with ramp shading, ordered dithering and occluded edges."""
    w, h = img.size
    px = img.load()
    rp = ramp(base)
    for y in range(h):
        for x in range(w):
            t = 2.0 + FACE_LIGHT[face]
            if face not in ("up", "down"):
                t += 0.45 - vgrad * (y / max(1, h - 1)) * 0.9
            if ao:
                if y == h - 1 or (x in (0, w - 1) and face not in ("up", "down")):
                    t -= 0.8
                if y == 0 and face not in ("down",):
                    t += 0.6
            t += (_hash(x, y, seed + w * 7 + h) - 0.5) * noise
            t += (BAYER[y % 4][x % 4] / 16.0 - 0.5) * (0.3 if sum(base) > 200 else 0.12)
            if sum(base) < 200:
                t = min(t, 3.2)
            px[x, y] = rp[max(0, min(4, int(round(t))))] + (255,)


def solid(base, outline=True, grain=0.0, shadow=0.26):
    def p(face, img):
        pixel_mat(img, base, face, seed=sum(base))
    return p


def layered(base, details, grain=0.0, shadow=0.26):
    def p(face, img):
        pixel_mat(img, base, face, seed=sum(base))
        px = img.load()
        for f in details:
            f(face, px, img.size[0], img.size[1], base)
    return p


def hair_paint(base):
    """Pixel hair: strand streaks along the spike, dark root, bright tip, ink edges."""
    rp = ramp(base)
    ink = dark(base, 0.38) if sum(base) > 360 else (10, 10, 16)

    def p(face, img):
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                t = 1 - y / max(1, h - 1)
                v = 1.0 + 2.4 * t + FACE_LIGHT[face] * 0.8
                v += 0.8 if x % 3 == 1 and t > 0.3 else 0.0  # strand highlight lines
                v -= 0.7 if x % 3 == 0 and t < 0.6 else 0.0  # strand separations
                c = rp[max(0, min(4, int(v)))]
                if face in ("north", "south", "east", "west") and (x == 0 or x == w - 1) and w > 2:
                    c = ink if t < 0.85 else rp[1]
                if face == "down":
                    c = rp[0]
                px[x, y] = c + (255,)
    return p


def skin_arm():
    def p(face, img):
        pixel_mat(img, SKIN, face, noise=0.45, seed=5)
        px = img.load()
        w, h = img.size
        rp = ramp(SKIN)
        if face in ("north", "south", "east", "west") and h >= 20:
            # bicep bulge (upper), elbow crease, forearm muscle line
            for x in range(1, w - 1):
                px[x, int(h * 0.42)] = rp[1] + (255,)
            for y in range(2, int(h * 0.38)):
                px[w // 2 - 1 if face in ("north", "east") else w // 2, y] = rp[3] + (255,)
            for y in range(int(h * 0.5), int(h * 0.8)):
                px[1 if face != "south" else w - 2, y] = rp[1] + (255,)
    return p


# ---------------------------------------------------------------- pixel faces (16 x 16)
# Rows 0-5 sit under the hair cap. Legend:
#  . skin   , skin shadow   h hair   H hair dark   b brow   k lash/ink   w eye white
#  i iris   I iris dark   p pupil   g grey lash   n nose   m mouth   x band   X band light
FACES = {
    "goku": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hHhhhHhhhhHhhhHh", ",H,,,,H,,H,,,,H,",
        ".bb..........bb.", "..bbb......bbb..",
        ".kkkkk....kkkkk.", ".wwiIp....pIiww.", "..wII,....,IIw..",
        ".......n........", "......,n,.......", "......mmmm......", ",..............,", ",,............,,",
    ],
    "calm": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hHhhhHhhhhHhhhHh", ",H,,,,H,,H,,,,H,",
        "................", ".bbbb......bbbb.",
        ".kkkkk....kkkkk.", ".wwiIi....iIiww.", "..wII,....,IIw..",
        ".......n........", "......,n,.......", "......mmmm......", ",..............,", ",,............,,",
    ],
    "ssj3": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hHhhhHhhhhHhhhHh", ",H,,,,H,,H,,,,H,",
        ",,,,,,....,,,,,,", "..,,,,....,,,,..",
        ".kkkkk....kkkkk.", ".wwiIp....pIiww.", "..wII,....,IIw..",
        ".......n........", "......,n,.......", "......mmmm......", ",..............,", ",,............,,",
    ],
    "vegeta": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hhHhhhhhhhhhhHhh", ",,,,,,hhhh,,,,,,",
        ".bb....hh....bb.", "..bbb.,..,.bbb..",
        "...kkkk..kkkk...", "..wwiI....Iiww..", "...,,......,,...",
        ".......n........", "......,n,.......", "......mmmm......", ".....m....m.....", ",,............,,",
    ],
    "gojo": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hhhhhhhhhhhhhhhh", ",h,,h,,hh,,h,,h,",
        "..ggg......ggg..", ".WWWWW....WWWWW.",
        ".wiiIw....wIiiw.", ".wiPIw....wIPiw.", "..wIw......wIw..",
        ".......n........", "......,n,.......", "......mmm.m.....", ",..............,", ",,............,,",
    ],
    "gojo_band": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hhhhhhhhhhhhhhhh", ",h,,h,,hh,,h,,h,",
        "................", "XXXXXXXXXXXXXXXX",
        "xxxxxxxxxxxxxxxx", "xxXxxxxxxxxxXxxx", "xxxxxxxxxxxxxxxx",
        ".......n........", "......,n,.......", "......mmm.m.....", ",..............,", ",,............,,",
    ],
}


def head_paint(hair, iris, brows=True, style="goku", blindfold=False):
    if style == "goku" and not brows:
        style = "ssj3"
    key = "gojo_band" if blindfold else style
    grid = FACES[key]
    hr = ramp(hair)
    sr = ramp(SKIN)
    iris = iris or (60, 60, 60)
    brow = hair if sum(hair) > 360 else (24, 20, 26)
    pal = {
        ".": sr[2], ",": sr[1], "h": hr[2], "H": hr[0], "b": dark(brow, 0.85), "k": (18, 12, 14),
        "w": (250, 250, 250), "i": iris, "I": dark(iris, 0.55), "p": (12, 10, 14), "P": (18, 40, 96),
        "g": (190, 190, 205), "W": (246, 246, 252), "n": sr[1], "m": (140, 70, 62),
        "x": (18, 18, 24), "X": (44, 44, 58),
    }

    def p(face, img):
        w, h = img.size
        px = img.load()
        if face == "north":
            for y in range(h):
                row = grid[y * 16 // h]
                for x in range(w):
                    ch = row[x * 16 // w]
                    c = pal[ch]
                    if ch == "." and _hash(x, y, 3) > 0.82:
                        c = sr[3]
                    px[x, y] = c + (255,)
            return
        if face == "up":
            pixel_mat(img, hair, face, seed=11)
            return
        if face == "down":
            pixel_mat(img, SKIN_SH, face, seed=12)
            return
        pixel_mat(img, SKIN, face, noise=0.4, seed=13)
        hair_rows = h * 7 // 8 if face == "south" else h * 6 // 16
        for y in range(hair_rows):
            for x in range(w):
                px[x, y] = hr[2] + (255,)
        if face in ("east", "west"):
            front = w - 1 if face == "east" else 0
            for y in range(hair_rows, h * 10 // 16):  # sideburn
                for dx in range(2):
                    xx = front - dx if face == "east" else front + dx
                    px[xx, y] = hr[1] + (255,)
            if blindfold:
                for y in range(h * 7 // 16, h * 11 // 16):
                    for x in range(w):
                        px[x, y] = pal["x"] + (255,)
    return p


# ---------------------------------------------------------------- pixel details (f(face, px, w, h, base))

def _put(px, w, h, x, y, c):
    if 0 <= x < w and 0 <= y < h:
        px[x, y] = c + (255,)


def gi_front(face, px, w, h, base):
    if face != "north":
        return
    blue = ramp(GI_BLUE)
    rp = ramp(GI)
    cx = w // 2
    for y in range(0, h // 3 + 1):  # V-neck
        half = max(0, (h // 3 - y) * 3 // 4)
        for x in range(cx - half, cx + half):
            _put(px, w, h, x, y, blue[2 if (x + y) % 3 else 1])
        _put(px, w, h, cx - half - 1, y, rp[0])
        _put(px, w, h, cx + half, y, rp[0])
    # symbol: 4x4 white disc with black glyph, on the character's left chest
    sx, sy = w - 6, 3
    disc = ["." "ww" ".", "wkww", "wkkw", ".ww."]
    for j, row in enumerate(disc):
        for i, ch in enumerate(row):
            if ch == "w":
                _put(px, w, h, sx + i, sy + j, (248, 246, 238))
            elif ch == "k":
                _put(px, w, h, sx + i, sy + j, (16, 16, 16))
    for x, y in ((3, h - 7), (4, h - 6), (4, h - 5), (5, h - 4), (w - 4, h - 7), (w - 5, h - 6), (w - 5, h - 5), (w - 6, h - 4)):
        _put(px, w, h, x, y, rp[1])


def gi_back(face, px, w, h, base):
    if face != "south":
        return
    cx, cy = w // 2, h // 3
    disc = [
        "..wwww..",
        ".wwwwww.",
        "wwkkkkww",
        "wwwkwwww",
        "wwkkkkww",
        "wwwkwkww",
        ".wwkkkw.",
        "..wwww..",
    ]
    for j, row in enumerate(disc):
        for i, ch in enumerate(row):
            if ch == "w":
                _put(px, w, h, cx - 4 + i, cy - 4 + j, (248, 246, 238))
            elif ch == "k":
                _put(px, w, h, cx - 4 + i, cy - 4 + j, (16, 16, 16))


def laces(face, px, w, h, base):
    if face != "north":
        return
    for y in range(1, h - 2, 2):
        for x in range(1, w - 1):
            if (x + y) % 3 == 0:
                _put(px, w, h, x, y, (200, 30, 30))


def band(faces, y0, y1, colour):
    """Horizontal band of a material (looked up at paint time so palettes can change)."""
    def f(face, px, w, h, base):
        if face not in faces:
            return
        c = {"gold": ARMOR_GOLD, "skin": SKIN}[colour]
        rp = ramp(c)
        a, b = int(y0 * h), max(int(y0 * h) + 1, int(round(y1 * h)))
        if face == "down":
            a, b = 0, h
        for y in range(a, b):
            for x in range(w):
                _put(px, w, h, x, y, rp[3] if y == a else rp[2])
    return f


def lines(spec, col, width=1):
    faces, polys = spec

    def f(face, px, w, h, base):
        if face not in faces:
            return
        for poly in polys:
            for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
                n = max(abs((x1 - x0) * w), abs((y1 - y0) * h), 1)
                for s in range(int(n) + 1):
                    t = s / n
                    _put(px, w, h, int((x0 + (x1 - x0) * t) * (w - 1)), int((y0 + (y1 - y0) * t) * (h - 1)), col)
    return f


def armor_chest(face, px, w, h, base):
    gr = ramp(ARMOR_GOLD)
    ar = ramp(ARMOR)
    top = int(h * 0.7)
    if face in SIDES:
        for y in range(top, h):
            for x in range(w):
                c = gr[3] if y == top else gr[2 if (x + y) % 5 else 1]
                if x % 4 == 0 and face == "north":
                    c = gr[0]
                _put(px, w, h, x, y, c)
    if face == "north":
        cx = w // 2
        for y in range(1, top - 1):
            _put(px, w, h, cx, y, ar[1])
        for x in range(2, cx - 1):
            _put(px, w, h, x, top // 2 + abs(x - cx // 2) // 3, ar[1])
            _put(px, w, h, w - 1 - x, top // 2 + abs(x - cx // 2) // 3, ar[1])
        for x in (2, 3):
            _put(px, w, h, x, 2, ar[4])


def suit_muscle(face, px, w, h, base):
    rp = ramp(SUIT)
    if face in SIDES:
        for y in range(2, int(h * 0.4)):
            _put(px, w, h, w // 2, y, rp[3])
        for x in range(1, w - 1):
            _put(px, w, h, x, int(h * 0.45), rp[0])


def jacket(face, px, w, h, base):
    rp = ramp(UNI)
    if face == "north":
        for y in range(h):
            _put(px, w, h, w // 2, y, (6, 6, 12))
            _put(px, w, h, w // 2 + 1, y, rp[3])
    if face in ("east", "west", "south"):
        for y in range(h):
            _put(px, w, h, w // 2, y, rp[0])


def collar(face, px, w, h, base):
    if face == "north":
        cx, cy = w // 2, h // 2
        for dx, dy in ((0, 0), (-1, 0), (0, -1), (-1, -1)):
            _put(px, w, h, cx + dx, cy + dy, (220, 180, 70))
        _put(px, w, h, cx, cy, (120, 86, 26))


# Stronger, more saturated anime palette at pixel scale
SKIN = (246, 202, 164)
SKIN_SH = (214, 150, 118)
GI = (240, 110, 20)
GI_BLUE = (30, 52, 168)
BOOT_BLUE = (28, 44, 136)
SUIT = (26, 40, 128)
ARMOR = (236, 236, 228)
ARMOR_GOLD = (222, 168, 36)
UNI = (22, 25, 40)


# ==================================================================================
# CUT-OUT HAIR (studied from Dragon Universe / Dragon Evolution): hair silhouettes are
# drawn as 2D spike shapes with transparent pixels on zero-thickness planes placed
# around the head at several angles, so the anime silhouette reads from every side.
# ==================================================================================

def _plane(m, bone, center, w, h, ry, rx, paint):
    cx, cy, cz = center
    m.cubes.append(dict(bone=bone, frm=[cx - w / 2, cy - h / 2, cz], size=[w, h, 0], rot=[rx, ry, 0],
                        pivot=[cx, cy, cz], inflate=0.0, paint=paint))


Model.plane = _plane


def spike_paint(base, spikes, core, w, h, cut_below=None, place=None):
    """Silhouette of spikes radiating from `core` (cx, cy, r) in plane units, pixel shaded.

    spikes: (angle_deg, length, base_width) in plane units. `place` = (center, ry) lets us
    drop pixels that would sit in front of the face.
    """
    rp = ramp(base)
    ink = dark(base, 0.4) if sum(base) > 360 else (8, 8, 12)
    cx, cy, cr = core
    axes = [(math.cos(math.radians(a)), math.sin(math.radians(a)), L, bw) for a, L, bw in spikes]

    def inside(u, v):
        du, dv = u - cx, v - cy
        if du * du + dv * dv <= cr * cr:
            return 0.05
        best = None
        for ax, ay, L, bw in axes:
            along = du * ax + dv * ay
            if along <= 0 or along > L:
                continue
            perp = abs(du * ay - dv * ax)
            k = max(0.0, (along - cr) / max(0.1, L - cr))
            half = bw / 2 * (1 - k) ** 0.9 + 0.15
            if perp <= half:
                t = along / L
                best = t if best is None else max(best, t)
        return best

    def blocked(u, v):
        if not place:
            return False
        (pcx, pcy, pcz), ry = place
        lx = w / 2 - u  # north-face texture runs from local +X to -X
        th = math.radians(ry)
        wx, wy, wz = pcx + lx * math.cos(th), pcy + (v - h / 2), pcz - lx * math.sin(th)
        return wz < -2.6 and wy < 31.6 and abs(wx) < 5.2

    def p(face, img):
        if face not in ("north", "south"):
            return
        W, H = img.size
        px = img.load()
        mask = [[None] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                u = (x + 0.5) / S
                if face == "south":
                    u = w - u
                v = h - (y + 0.5) / S
                if (cut_below is not None and v < cut_below) or blocked(u, v):
                    continue
                mask[y][x] = inside(u, v)
        for y in range(H):
            for x in range(W):
                t = mask[y][x]
                if t is None:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                edge = any(not (0 <= x + dx < W and 0 <= y + dy < H) or mask[y + dy][x + dx] is None
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge:
                    c = ink
                else:
                    k = 1.0 + 3.0 * t + (0.5 if (x + 2 * y) % 5 == 0 else 0) - (0.7 if (2 * x + y) % 7 == 0 else 0)
                    c = rp[max(0, min(4, int(k)))]
                px[x, y] = c + (255,)
    return p


def cap_paint(base, teeth=True):
    """Hair cap whose lower edge is cut into jagged locks (front and sides)."""
    hp = hair_paint(base)

    def p(face, img):
        hp(face, img)
        if not teeth or face not in ("north", "east", "west"):
            return
        W, H = img.size
        px = img.load()
        tooth = max(3, W // 6)
        for x in range(W):
            k = x % tooth
            depth = int(H * 0.45 * (1 - abs(k - tooth / 2) / (tooth / 2)))
            for y in range(H - 1, H - 1 - (int(H * 0.5) - depth), -1):
                if y >= 0:
                    px[x, y] = (0, 0, 0, 0)
    return p


def hair_set(m, base, layout):
    """layout: list of (center, w, h, ry, rx, spikes, core) planes."""
    for center, w, h, ry, rx, spikes, core in layout:
        m.plane("hair", center, w, h, ry, rx, spike_paint(base, spikes, core, w, h, place=(center, ry)))


def _ring(y, spikes_for, size=22, core_r=3.6, angles=(0, 45, 90, 135)):
    out = []
    for i, ry in enumerate(angles):
        out.append(((0, y, 0), size, size, ry, 0, spikes_for(i), (size / 2, size / 2, core_r)))
    return out


def goku_hair_base(m, c):
    m.box("hair", [-4.35, 28.75, -4.35], [8.7, 4, 8.7], cap_paint(c, teeth=False))
    sets = [
        [(15, 9.5, 5), (48, 10.5, 5), (82, 10, 4.5), (115, 10, 4.5), (148, 10, 5), (180, 9, 4.5), (-15, 7.5, 4)],
        [(28, 10, 5), (64, 11, 4.5), (98, 10, 4.5), (132, 10.5, 5), (165, 9.5, 4.5), (-5, 8, 4)],
        [(5, 9, 4.5), (38, 10.5, 5), (72, 10, 4.5), (108, 10.5, 5), (142, 10, 4.5), (175, 8.5, 4.5), (205, 7, 4)],
        [(20, 9.5, 4.5), (55, 10, 5), (90, 10.5, 4.5), (125, 10, 5), (160, 9.5, 4.5), (195, 7.5, 4)],
    ]
    hair_set(m, c, _ring(28.5, lambda i: sets[i]))
    bang = [(245, 5.5, 3.2), (272, 5.2, 3), (300, 5.5, 3.2)]
    m.plane("hair", (0, 31.6, -4.6), 10, 8, 0, 0, spike_paint(c, bang, (5, 7.4, 2.2), 10, 8))


def goku_hair_ssj(m, c):
    m.box("hair", [-4.35, 28.75, -4.35], [8.7, 4, 8.7], cap_paint(c, teeth=False))
    def sp(i):
        base = [(22, 11, 5), (48, 13, 5), (72, 14.5, 5), (96, 14.5, 5), (120, 13.5, 5), (146, 12, 5), (170, 9.5, 4.5), (0, 9, 4.5)]
        return [(a + (i * 9) % 18 - 9, l, bw) for a, l, bw in base]
    hair_set(m, c, _ring(28.5, sp, size=30))
    m.plane("hair", (-0.6, 31.6, -4.6), 8, 9, 0, 0, spike_paint(c, [(262, 6.8, 2.6)], (4, 8.6, 1.4), 8, 9))


def goku_hair_ssj3(m, c):
    m.box("hair", [-4.35, 28.75, -4.35], [8.7, 4, 8.7], cap_paint(c, teeth=False))
    def sp(i):
        return [(35, 9.5, 5), (70, 10.5, 5), (105, 10.5, 5), (140, 9.5, 5), (5, 8, 4.5), (175, 8, 4.5)]
    hair_set(m, c, _ring(28.5, sp))
    mane = [(252, 22, 7), (270, 23, 8), (288, 22, 7), (236, 17, 6), (304, 17, 6)]
    for ry, z in ((0, 4.6), (40, 3.4), (-40, 3.4)):
        m.plane("hair", (0, 25, z), 18, 30, ry, 6, spike_paint(c, mane, (9, 26, 3.5), 18, 30))
    bang = [(250, 6.5, 3.4), (272, 7, 3.2), (294, 6.5, 3.4)]
    m.plane("hair", (0, 31.6, -4.6), 10, 9, 0, 0, spike_paint(c, bang, (5, 8.4, 2.2), 10, 9))


def vegeta_hair(m, c):
    m.box("hair", [-4.35, 29.5, -4.35], [8.7, 3.25, 8.7], cap_paint(c, teeth=False))
    m.box("hair", [-0.75, 28.75, -4.45], [1.5, 2.5, 0.5], hair_paint(c), rot=[0, 0, 45], pivot=[0, 29.5, -4.2])
    def sp(i):
        return [(64, 13, 6), (77, 16.5, 6), (90, 19, 6.5), (103, 16.5, 6), (116, 13, 6), (48, 9.5, 5.5), (132, 9.5, 5.5)]
    hair_set(m, c, _ring(29, sp, size=42, core_r=3.8))


def gojo_hair_up(m, c):
    m.box("hair", [-4.3, 29, -4.3], [8.6, 3.75, 8.6], cap_paint(c, teeth=False))
    def sp(i):
        off = (i % 2) * 12
        return [(a + off, l, 4.2) for a, l in ((20, 8), (46, 9), (72, 9.5), (98, 9.5), (124, 9), (150, 8), (176, 6.5))]
    hair_set(m, c, _ring(28.8, sp, size=22))


def gojo_hair_down(m, c):
    m.box("hair", [-4.3, 29.25, -4.3], [8.6, 3.5, 8.6], cap_paint(c, teeth=False))
    def sp(i):
        off = (i % 2) * 10
        return [(a + off, l, 4) for a, l in ((-35, 6.8), (-10, 6.8), (20, 6.5), (55, 6.5), (90, 6.2), (125, 6.5), (160, 6.8), (190, 6.8), (215, 6.5))]
    hair_set(m, c, _ring(28.5, sp, size=18))
    bang = [(242, 6.2, 3.2), (258, 6.8, 3), (276, 7, 3), (294, 6.6, 3), (310, 5.8, 3.2)]
    m.plane("hair", (0, 31.2, -4.6), 11, 9, 0, 0, spike_paint(c, bang, (5.5, 8, 2.2), 11, 9))


def shell_paint(base, hairline=29.3, peak=False, back_to=25.0, sideburn=True, teeth=1.0):
    """Head-hugging hair layer: transparent face, jagged hairline, hair on top/sides/back."""
    rp = ramp(base)
    ink = dark(base, 0.4) if sum(base) > 360 else (8, 8, 12)

    def p(face, img):
        W, H = img.size
        px = img.load()
        if face == "down":
            for y in range(H):
                for x in range(W):
                    px[x, y] = (0, 0, 0, 0)
            return
        mask = [[False] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                yy = 32 - (y + 0.5) * 8 / H  # model y of this row
                fx = (x + 0.5) / W
                if face == "up":
                    on = True
                elif face == "south":
                    on = yy >= back_to - 0.8 * abs(math.sin(fx * math.pi * 4)) * teeth
                elif face in ("east", "west"):
                    front = fx if face == "east" else 1 - fx  # 1 = at the face
                    lim = 28.6 - 0.7 * abs(math.sin(fx * math.pi * 3)) * teeth
                    if sideburn and front > 0.8:
                        lim = 26.6
                    lim = min(lim, back_to + (28.6 - back_to) * front)
                    on = yy >= lim
                else:  # north: jagged locks over the forehead
                    lim = hairline - 0.9 * teeth * abs(math.sin(fx * math.pi * 5))
                    if peak:
                        lim = min(lim, hairline + 0.6 - 2.2 * max(0.0, 1 - abs(fx - 0.5) * 6))
                    on = yy >= lim
                mask[y][x] = on
        for y in range(H):
            for x in range(W):
                if not mask[y][x]:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                edge = face != "up" and (y + 1 >= H or not mask[y + 1][x])
                t = 1 - y / max(1, H - 1)
                k = 1.6 + 2.0 * t + FACE_LIGHT[face] * 0.6 + (0.6 if x % 3 == 1 else 0) - (0.6 if x % 3 == 0 and t < 0.6 else 0)
                px[x, y] = (ink if edge else rp[max(0, min(4, int(k)))]) + (255,)
    return p


def shell(m, c, **kw):
    m.box("hair", [-4, 24, -4], [8, 8, 8], shell_paint(c, **kw), inflate=0.45)


_orig_box = Model.box


def _box_no_caps(self, bone, frm, size, paint, rot=None, pivot=None, inflate=0.0):
    # Old cube caps are replaced by the head-hugging shell (see hair_* functions below).
    if getattr(paint, "_is_cap", False):
        return
    return _orig_box(self, bone, frm, size, paint, rot, pivot, inflate)


Model.box = _box_no_caps
_cap_paint = cap_paint


def cap_paint(base, teeth=True):  # noqa: F811
    p = _cap_paint(base, teeth)
    p._is_cap = True
    return p


def _with_shell(fn, **kw):
    def wrapped(m, c):
        shell(m, c, **kw)
        fn(m, c)
    return wrapped


goku_hair_base = _with_shell(goku_hair_base, hairline=29.0)
goku_hair_ssj = _with_shell(goku_hair_ssj, hairline=29.2)
goku_hair_ssj3 = _with_shell(goku_hair_ssj3, hairline=29.0, back_to=24.2)
vegeta_hair = _with_shell(vegeta_hair, hairline=30.0, peak=True, teeth=0.4)
gojo_hair_up = _with_shell(gojo_hair_up, hairline=29.6, sideburn=False)
gojo_hair_down = _with_shell(gojo_hair_down, hairline=28.6)


def _fix_bangs(fn):
    """Front bang planes: hide the part above the head top (y > 32.4); drop the old widow's-peak stick."""
    def wrapped(m, c):
        start = len(m.cubes)
        fn(m, c)
        keep = []
        for cube in m.cubes[start:]:
            if cube["size"] == [1.5, 2.5, 0.5]:
                continue
            if cube["size"][2] == 0 and cube["frm"][2] < -4.4:
                top = cube["pivot"][1] + cube["size"][1] / 2
                inner = cube["paint"]

                def clipped(face, img, inner=inner, top=top):
                    inner(face, img)
                    px = img.load()
                    W, H = img.size
                    for y in range(H):
                        if top - (y + 0.5) / S > 32.4:
                            for x in range(W):
                                px[x, y] = (0, 0, 0, 0)
                cube["paint"] = clipped
            keep.append(cube)
        m.cubes[start:] = keep
    return wrapped


goku_hair_base = _fix_bangs(goku_hair_base)
goku_hair_ssj = _fix_bangs(goku_hair_ssj)
goku_hair_ssj3 = _fix_bangs(goku_hair_ssj3)
vegeta_hair = _fix_bangs(vegeta_hair)
gojo_hair_down = _fix_bangs(gojo_hair_down)


# ==================================================================================
# 3D HAIR (final): volumetric tapered tufts (rotated, overlapping cubes) on top of the
# head-hugging shell, painted with the pixel-art strand shading. Replaces the flat planes.
# ==================================================================================
_strand_orig = Model.strand


def _strand_chunky(self, base, d, length, width, paint, bend=(0, 0, 0), segs=3, bone="hair", thick=None):
    if bone == "hair":
        width *= 1.12
        thick = thick or 0.92
    return _strand_orig(self, base, d, length, width, paint, bend, segs, bone, thick)


Model.strand = _strand_chunky

def goku_hair_base_3d(m, c):
    hp = hair_paint(c)
    # bangs over the forehead
    m.strand([-2.3, 31.5, -4.1], [-0.3, -1, -0.4], 4.25, 3.25, hp)
    m.strand([0.4, 31.75, -4.2], [0.05, -1, -0.45], 3.75, 3, hp)
    m.strand([2.6, 31.5, -4.1], [0.4, -1, -0.35], 3.5, 2.75, hp)
    # big tufts
    m.strand([0.3, 32.25, -1.2], [0.1, 1, 0.3], 7, 5, hp, bend=(0, 0, 0.2))
    m.mirror_strand([2.8, 32, -0.4], [0.85, 1, 0.05], 7, 4.75, hp, bend=(0.15, -0.25, 0))
    m.mirror_strand([4.1, 30, 0.8], [1, 0.25, 0.2], 6, 4.25, hp, bend=(0, -0.25, 0))
    m.mirror_strand([3.7, 28.5, 2.6], [0.9, -0.35, 0.6], 5, 3.5, hp)
    m.strand([0, 31.5, 3], [0, 0.5, 1], 6.5, 4.75, hp, bend=(0, -0.15, 0))
    m.mirror_strand([2.4, 30, 3.6], [0.5, 0, 1], 5.5, 3.75, hp)
    m.strand([0, 27.75, 4.1], [0, -0.6, 1], 4.5, 3.75, hp)
    m.mirror_strand([4.2, 28.75, -2.3], [0.05, -1, -0.1], 2.75, 1.75, hp, segs=2)


def goku_hair_ssj_3d(m, c):
    hp = hair_paint(c)
    m.strand([-1, 31.75, -4.3], [-0.15, -1, -0.3], 5, 2, hp)  # the single bang
    m.mirror_strand([2.2, 32, -3.3], [0.3, 1, -0.35], 6, 3.75, hp)
    m.strand([0, 32.25, -0.5], [0, 1, 0.12], 9, 5.25, hp)
    m.mirror_strand([2.6, 32, -0.25], [0.45, 1, 0.05], 8.5, 4.75, hp)
    m.mirror_strand([4, 30.75, 1], [0.95, 0.9, 0.15], 7, 4.25, hp)
    m.mirror_strand([3.9, 29, 2.6], [1, 0.4, 0.5], 5.5, 3.5, hp)
    m.strand([0, 31.5, 3], [0, 0.85, 0.65], 8, 4.75, hp)
    m.mirror_strand([2.4, 30.75, 3.4], [0.45, 0.75, 0.65], 6.5, 3.75, hp)
    m.strand([0, 28.25, 4.1], [0, 0.1, 1], 4.75, 3.75, hp)
    m.mirror_strand([4.2, 28.75, -2.3], [0.05, -1, -0.1], 2.75, 1.75, hp, segs=2)


def goku_hair_ssj3_3d(m, c):
    hp = hair_paint(c)
    m.strand([0, 29, 4.2], [0, -1, 0.12], 22, 8.5, hp, thick=0.5)
    m.mirror_strand([3.2, 29, 3.2], [0.22, -1, 0.15], 19, 5, hp, thick=0.6)
    m.mirror_strand([4.4, 29.5, 0.2], [0.28, -1, 0.05], 11, 3.5, hp)
    m.strand([0, 32.25, -0.5], [0, 1, 0.35], 6.5, 5, hp)
    m.mirror_strand([2.6, 32, -0.5], [0.6, 1, 0.15], 6, 4.25, hp)
    m.strand([-2.3, 31.5, -4.1], [-0.3, -1, -0.4], 5, 3.25, hp)
    m.strand([0.4, 31.75, -4.2], [0.05, -1, -0.45], 5.5, 3, hp)
    m.strand([2.6, 31.5, -4.1], [0.4, -1, -0.35], 4.5, 2.75, hp)


def vegeta_hair_3d(m, c):
    hp = hair_paint(c)
    m.box("hair", [-3.75, 31.5, -3.25], [7.5, 5, 6.75], hp)  # flame body
    m.box("hair", [-2.75, 35.5, -2.25], [5.5, 3.5, 5], hp)
    m.strand([0, 37.5, 0], [0, 1, 0.12], 7.5, 4.5, hp)
    m.mirror_strand([2.2, 34, -1.6], [0.18, 1, -0.05], 7.5, 4, hp)
    m.mirror_strand([3.2, 32.5, 1], [0.32, 1, 0.2], 7.5, 4, hp)
    m.strand([0, 34, 2.4], [0, 1, 0.35], 8, 4.5, hp)
    m.strand([0, 34, -2.4], [0, 1, -0.06], 6.5, 4, hp)
    m.mirror_strand([3.9, 30.5, -1.5], [0.4, 1, 0], 5, 3, hp)


def gojo_hair_up_3d(m, c):
    hp = hair_paint(c)
    m.strand([0, 32, 0], [0, 1, 0.05], 6.5, 4.25, hp)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, z = math.sin(a) * 3.1, -math.cos(a) * 3.1
        m.strand([x, 31.5, z], [math.sin(a) * 0.75, 1, -math.cos(a) * 0.75], 5.5, 3.5, hp, bend=(0, -0.1, 0))
    for k in range(8):
        a = k * math.pi / 4
        x, z = math.sin(a) * 4, -math.cos(a) * 4
        if z < -3:
            continue  # keep the blindfold visible
        m.strand([x, 29.25, z], [math.sin(a), 0.55, -math.cos(a)], 4, 3, hp)


def gojo_hair_down_3d(m, c):
    hp = hair_paint(c)
    for x, l in ((-3.1, 3.5), (-1.6, 3.75), (0, 4.75), (1.6, 3.75), (3.1, 3.5)):
        m.strand([x, 31.5, -4.2], [x * 0.06, -1, -0.45], l, 2, hp)
    m.mirror_strand([4.2, 30.5, -1.5], [0.15, -1, -0.05], 4.75, 2.5, hp)
    m.mirror_strand([4.2, 30.5, 1.5], [0.2, -1, 0.15], 5.25, 2.5, hp)
    for x in (-2.6, 0, 2.6):
        m.strand([x, 31.5, 4.1], [x * 0.05, -1, 0.3], 6, 3, hp)
    m.strand([0, 32.5, 0], [0, 1, 0.5], 2.75, 3, hp)
    m.mirror_strand([2, 32.25, 1], [0.6, 1, 0.3], 2.5, 2.25, hp)




def _hair3d(fn, **kw):
    def wrapped(m, c):
        shell(m, c, **kw)
        fn(m, c)
    return wrapped


goku_hair_base = _hair3d(goku_hair_base_3d, hairline=29.2)
goku_hair_ssj = _hair3d(goku_hair_ssj_3d, hairline=29.3)
goku_hair_ssj3 = _hair3d(goku_hair_ssj3_3d, hairline=29.2, back_to=24.2)
vegeta_hair = _hair3d(vegeta_hair_3d, hairline=30.0, peak=True, teeth=0.4)
gojo_hair_up = _hair3d(gojo_hair_up_3d, hairline=28.9, sideburn=False)
gojo_hair_down = _hair3d(gojo_hair_down_3d, hairline=28.8)

# Vegeta: natural face, only one mouth corner turned down (proud, not angry)
FACES["vegeta"] = [
    "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
    "hhHhhhhhhhhhhHhh", ",,,,,,hhhh,,,,,,",
    ".bb....hh....bb.", "..bbbb....bbbb..",
    ".kkkkk....kkkkk.", ".wwiIp....pIiww.", "..wII,....,IIw..",
    ".......n........", "......,n,.......", "......mmmmm.....", "...........m....", ",,............,,",
]


# ---------------------------------------------------------------- SSJ3 (improved)
def goku_hair_ssj3_v2(m, c):
    hp = hair_paint(c)
    # crown rising up and back
    m.strand([0, 32, -0.6], [0, 1, 0.5], 7.5, 5.25, hp, bend=(0, -0.1, 0.1))
    m.mirror_strand([2.6, 32, -0.4], [0.55, 1, 0.35], 7, 4.75, hp, bend=(0.05, -0.15, 0.1))
    m.mirror_strand([3.9, 30.5, 0.6], [1, 0.55, 0.45], 6, 4.25, hp, bend=(0, -0.2, 0.1))
    # short front bangs that stay above the eyes
    m.strand([-2.3, 31.9, -4.1], [-0.3, -1, -0.65], 2.9, 3.1, hp)
    m.strand([0.2, 32.1, -4.2], [0.05, -1, -0.7], 2.6, 2.8, hp)
    m.strand([2.5, 31.9, -4.1], [0.35, -1, -0.6], 2.7, 2.9, hp)
    # the mane: long jagged locks fanning down the back to the knees
    for x, L in ((-3.6, 21), (-1.8, 24), (0, 25), (1.8, 24), (3.6, 21)):
        m.strand([x, 30.6, 3.9], [x * 0.07, -1, 0.2], L, 4.75, hp, thick=0.72, bend=(x * 0.01, 0, 0.02))
    for x in (-2.6, 0, 2.6):
        m.strand([x, 27.5, 4.7], [x * 0.06, -1, 0.28], 19, 5.25, hp, thick=0.7)
    m.mirror_strand([4.3, 30, 1.4], [0.18, -1, 0.14], 17, 4.25, hp, thick=0.75)
    m.mirror_strand([4.4, 31, -1.6], [0.25, -1, 0.05], 8, 3.25, hp)


goku_hair_ssj3 = _hair3d(goku_hair_ssj3_v2, hairline=29.2, back_to=24.0)


# ==================================================================================
# NEW CHARACTERS: Itadori Yuji (3 versions) and Monkey D. Luffy (all gears)
# ==================================================================================
EXTRA_PAL = {"t": (16, 12, 16), "r": (200, 30, 40), "s": (196, 120, 108), "R": (230, 40, 40), "y": (250, 210, 60)}


def head_paint2(hair, iris, style, brows=True, blindfold=False):
    """head_paint + extra palette keys (tattoos t, extra eyes r, scars s, red eyes R)."""
    base = head_paint(hair, iris, brows, "goku", blindfold)
    grid = FACES[style]
    hr = ramp(hair)
    sr = ramp(SKIN_NOW())
    pal = {
        ".": sr[2], ",": sr[1], "h": hr[2], "H": hr[0], "b": dark(hair if sum(hair) > 360 else (24, 20, 26), 0.85), "k": (18, 12, 14),
        "w": (250, 250, 250), "i": iris or (60, 60, 60), "I": dark(iris or (60, 60, 60), 0.55), "p": (12, 10, 14),
        "g": (190, 190, 205), "W": (246, 246, 252), "n": sr[1], "m": (140, 70, 62), "x": (18, 18, 24), "X": (44, 44, 58),
        **EXTRA_PAL,
    }

    def p(face, img):
        if face != "north":
            base(face, img)
            return
        w, h = img.size
        px = img.load()
        for y in range(h):
            row = grid[y * 16 // h]
            for x in range(w):
                ch = row[x * 16 // w]
                c = pal[ch]
                if ch == "." and _hash(x, y, 3) > 0.82:
                    c = sr[3]
                px[x, y] = c + (255,)
    return p


def SKIN_NOW():
    return SKIN


FACES.update({
    "yuji": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hhhhhhh..hhhhhhh", ",,,,,,,..,,,,,,,",
        ".bbb........bbb.", "................",
        ".kkkkk....kkkkk.", ".wwiIp....pIiww.", "..wII,....,IIw..",
        "..ss........ss..", ".......n........", "......mmmm......", "................", ",,............,,",
    ],
    "yuji_final": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hhhhhhh..hhhhhhh", ",,,,,,,..,,,,,,,",
        ".bb..........bb.", "..bbbb....bbbb..",
        ".kkkkk....kkkkk.", ".wwiIp....pIiww.", "..wII,....,IIw..",
        "..ss.......s.ss.", ".ss....n...s....", "......mmmm......", "................", ",,............,,",
    ],
    "sukuna": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hhhhhhhhhhhhhhhh", ",,,,,tt..tt,,,,,",
        ".bbb..t..t..bbb.", "..bbb......bbb..",
        ".kkkkk....kkkkk.", ".wwRRp....pRRww.", "..kkkk....kkkk..",
        "..rr........rr..", ".tt....n.....tt.", "......mmmmm.....", ".tt...m...m...t.", ",,t..........t,,",
    ],
    "luffy": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hHhhhHhhhhHhhhHh", ",H,,,,H,,H,,,,H,",
        "..bbb......bbb..", "................",
        "..kkkk....kkkk..", "..wpIw....wIpw..", "..wwww....wwww..",
        "...........ss...", ".......n...s.s..", ".....kmmmmmk....", "......kkkkk.....", ",,............,,",
    ],
    "luffy_g5": [
        "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh",
        "hhhhhhhhhhhhhhhh", ",h,,h,,hh,,h,,h,",
        "..bbb......bbb..", "................",
        "..kkkk....kkkk..", "..wRRw....wRRw..", "..wwww....wwww..",
        "...........ss...", ".......n...s.s..", "....kmmmmmmmk...", ".....kwwwwwk....", "......kkkkk.....",
    ],
})

# ---------------------------------------------------------------- Itadori
JJ_UNI = (30, 34, 56)
HOOD_RED = (196, 36, 40)
PINK = (238, 150, 150)
UNDERCUT = (92, 56, 46)


def yuji_body(m, style, iris=(120, 70, 40)):
    hand = layered(JJ_UNI, [band(SIDES + ("down",), 0.9, 1.0, "skin")])
    base_body(m, solid(JJ_UNI), hand, layered(JJ_UNI, [lines((SIDES, [[(0.5, 0), (0.5, 1)]]), (52, 58, 90))]),
              head_paint2(PINK if style != "sukuna" else (226, 140, 150), iris if style != "sukuna" else (200, 30, 40), style))
    jacket = layered(JJ_UNI, [lines((("north",), [[(0.5, 0), (0.5, 1)]]), (10, 10, 18)),
                              lines((("north",), [[(0.55, 0.05), (0.55, 1)]]), (60, 66, 100))])
    m.box("body", [-4.3, 10, -2.3], [8.6, 14, 4.6], jacket)
    # the red hood folded around the neck and down the back
    m.box("body", [-3.75, 22.5, -2.75], [7.5, 2.25, 5.5], layered(HOOD_RED, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), dark(HOOD_RED, 0.6))]))
    m.box("body", [-3.25, 18.5, 2.2], [6.5, 5, 1.25], solid(HOOD_RED))
    both_arms(m, [3.8, 15, -2.2], [4.4, 9, 4.4], layered(JJ_UNI, [lines((SIDES, [[(0.3, 0.2), (0.35, 0.9)]]), (52, 58, 90))]))
    both_arms(m, [3.7, 13.5, -2.3], [4.6, 1.5, 4.6], solid((44, 50, 78)))
    both_legs(m, [-0.35, 0, -2.6], [4.5, 1.75, 5], layered((236, 236, 232), [band(SIDES, 0.0, 0.3, "gold")]))  # sneakers
    if style == "sukuna":  # wrist tattoo bands
        both_arms(m, [3.85, 12.5, -2.15], [4.3, 0.75, 4.3], solid((16, 12, 16)))
    if style == "yuji_final":  # torn sleeve + bandaged forearm on the right arm
        m.box("rightArm", [3.75, 12, -2.25], [4.5, 3, 4.5], layered((230, 226, 214), [lines((SIDES, [[(0, 0.3), (1, 0.4)], [(0, 0.7), (1, 0.8)]]), (190, 180, 160))]))


def yuji_hair(m, c, style):
    hp = hair_paint(c)
    if style == "sukuna":  # swept up and back
        m.strand([0, 32, -2], [0, 1, 0.6], 4.5, 4.5, hp)
        m.mirror_strand([2.4, 31.8, -2], [0.35, 1, 0.65], 4.2, 4, hp)
        m.mirror_strand([3.6, 31, 0.5], [0.6, 0.7, 0.8], 3.8, 3.5, hp)
        m.strand([0, 31.5, 1.5], [0, 0.6, 1], 4, 4.5, hp)
        return
    m.strand([-1.2, 32, -1.6], [-0.35, 1, -0.2], 3.8, 4.2, hp)
    m.strand([1.2, 32, -1.6], [0.35, 1, -0.2], 3.8, 4.2, hp)
    m.mirror_strand([2.9, 31.8, 0], [0.5, 1, 0.1], 3.4, 3.8, hp)
    m.strand([0, 32, 1.5], [0, 1, 0.45], 3.6, 4.2, hp)
    m.mirror_strand([1.9, 31.5, 2.8], [0.3, 0.6, 0.8], 3.2, 3.5, hp)
    m.strand([-1.6, 32, -4.0], [-0.2, -1, -0.8], 2.2, 2.8, hp)
    m.strand([1.6, 32, -4.0], [0.2, -1, -0.8], 2.2, 2.8, hp)
    if style == "yuji_final":
        m.mirror_strand([3.8, 30.5, -1], [0.5, 0.2, -0.1], 3, 2.8, hp)


def yuji_shell(m, c):
    """Pink top with a darker undercut on the sides and back."""
    def p(face, img):
        shell_paint(c, hairline=29.6, sideburn=False)(face, img)
        if face in ("east", "west", "south"):
            px = img.load()
            W, H = img.size
            ur = ramp(UNDERCUT)
            for y in range(H):
                yy = 32 - (y + 0.5) * 8 / H
                if 26.5 < yy < 29.6:
                    for x in range(W):
                        if px[x, y][3] > 0:
                            px[x, y] = ur[2 if (x + y) % 3 else 1] + (255,)
    m.box("hair", [-4, 24, -4], [8, 8, 8], p, inflate=0.45)


# ---------------------------------------------------------------- Luffy
VEST = (206, 34, 38)
SHORTS = (46, 86, 170)
SASH = (236, 196, 60)
STRAW = (238, 206, 104)
G4_HAKI = (24, 20, 26)


def x_scar(face, px, w, h, base):
    if face != "north":
        return
    cx, cy = w // 2, h // 4
    for d in range(-3, 4):
        _put(px, w, h, cx + d, cy + d, (190, 110, 96))
        _put(px, w, h, cx + d, cy - d, (190, 110, 96))


def vest_front(face, px, w, h, base):
    """Open red shirt: skin shows down the middle (with the X scar), yellow buttons on the edge."""
    if face != "north":
        return
    sr = ramp(SKIN)
    for y in range(h):
        for x in range(w // 2 - 3, w // 2 + 3):
            _put(px, w, h, x, y, sr[2] if (x + y) % 5 else sr[1])
    for y in range(3, h, 6):
        _put(px, w, h, w // 2 - 4, y, SASH)
    cx, cy = w // 2, h // 4
    for d in range(-2, 3):
        _put(px, w, h, cx + d, cy + d, (190, 110, 96))
        _put(px, w, h, cx + d, cy - d, (190, 110, 96))


def hat(m, straw=STRAW):
    weave = layered(straw, [lines((SIDES + ("up",), [[(0, 0.33), (1, 0.33)], [(0, 0.66), (1, 0.66)]]), dark(straw, 0.75))])
    m.box("hat", [-3.9, 31.4, -3.9], [7.8, 3, 7.8], weave)
    m.box("hat", [-4.0, 31.4, -4.0], [8.0, 1.1, 8.0], solid((200, 30, 34)))
    m.box("hat", [-7.5, 31.2, -7.5], [15, 0.5, 15], weave)
    m.box("hat", [-7.5, 31.2, -7.5], [15, 0.5, 15], weave, rot=[0, 45, 0], pivot=[0, 31.2, 0])


def luffy_hair(m, c, g5=False):
    hp = hair_paint(c)
    if g5:  # Nika: white hair rising like flames / clouds
        for x, z, L in ((-2.4, -2, 6.5), (0, -2.4, 7.5), (2.4, -2, 6.5), (-3.3, 0.8, 6), (3.3, 0.8, 6), (-1.5, 2.6, 6.5), (1.5, 2.6, 6.5)):
            m.strand([x, 31.8, z], [x * 0.15, 1, z * 0.1 + 0.15], L, 4.2, hp, bend=(x * 0.03, 0, 0.12))
        m.mirror_strand([4.2, 30, -1], [0.6, 0.6, 0], 4.5, 3.2, hp)
        return
    m.strand([-2.2, 31.4, -4.1], [-0.3, -1, -0.6], 2.8, 2.8, hp)
    m.strand([0.2, 31.5, -4.2], [0.1, -1, -0.7], 2.6, 2.6, hp)
    m.strand([2.4, 31.4, -4.1], [0.35, -1, -0.6], 2.8, 2.8, hp)
    m.mirror_strand([4.2, 30.5, -1.8], [0.3, -1, -0.15], 3, 2.4, hp)
    m.mirror_strand([4.2, 30.5, 1.2], [0.35, -1, 0.2], 3.2, 2.6, hp)
    for x in (-2.5, 0, 2.5):
        m.strand([x, 30.5, 4.2], [x * 0.08, -1, 0.35], 3.4, 3, hp)


def luffy_body(m, form):
    g5 = form == "g5"
    skin_tone = (236, 120, 120) if form == "g2" else SKIN
    vest = (240, 240, 236) if g5 else VEST
    shorts = (236, 236, 232) if g5 else SHORTS
    sash = (200, 40, 60) if g5 else SASH
    face = "luffy_g5" if g5 else "luffy"
    hair = (246, 246, 250) if g5 else (22, 20, 26)
    iris = (220, 40, 40) if g5 else (40, 30, 30)
    haki = form in ("g4b", "g4s", "g4t")
    arm_col = G4_HAKI if haki else skin_tone
    skin_arm_p = layered(arm_col, [lines((SIDES, [[(0.2, 0.2), (0.5, 0.5), (0.3, 0.9)]]), (170, 30, 30))]) if haki else solid(skin_tone)
    base_body(m, layered(skin_tone, [x_scar]), skin_arm_p, solid(shorts), head_paint2(hair, iris, face))
    if form == "g4b":  # Boundman: huge muscular upper body, haki-black limbs, steam scarf
        m.box("body", [-5.5, 12, -3.5], [11, 12, 7], layered((236, 120, 110), [x_scar]))
        m.box("body", [-6, 20, -3.8], [12, 4.5, 7.6], layered(vest, [band(SIDES, 0.8, 1.0, "gold")]))
        both_arms(m, [4, 9.5, -3.2], [6.5, 14.5, 6.5], skin_arm_p)
        both_legs(m, [-0.6, 0, -2.6], [5.2, 12, 5.2], layered(G4_HAKI, [lines((SIDES, [[(0.2, 0.1), (0.6, 0.5), (0.3, 0.95)]]), (170, 30, 30))]))
        m.box("body", [-5, 23.5, -4], [10, 2.5, 8], solid((245, 245, 245)))  # steam scarf
    elif form == "g4s":  # Snakeman: lean, black arms, long steam mantle
        m.box("body", [-4.3, 12, -2.3], [8.6, 12, 4.6], layered(vest, [vest_front]))
        both_arms(m, [3.8, 11, -2.3], [4.6, 13, 4.6], skin_arm_p)
        m.box("body", [-4.6, 21.5, -2.9], [9.2, 3, 5.8], solid((245, 245, 245)))
        m.strand([0, 23, 2.8], [0, -1, 0.25], 16, 7, solid((240, 240, 240)), bone="body", thick=0.3, segs=3)
    elif form == "g4t":  # Tankman: enormous round belly
        m.box("body", [-7, 9, -6], [14, 15, 12], layered((236, 120, 110), [x_scar]))
        m.box("body", [-6, 6, -5], [12, 4, 10], solid(shorts))
        both_arms(m, [5, 11, -3], [6, 13, 6], skin_arm_p)
        m.box("body", [-5, 23, -4], [10, 2.5, 8], solid((245, 245, 245)))
    else:
        m.box("body", [-4.3, 12, -2.3], [8.6, 12, 4.6], layered(vest, [vest_front]))
        both_arms(m, [3.8, 19, -2.3], [4.6, 5, 4.6], solid(vest))  # short sleeves
    m.box("body", [-4.5, 11, -2.6], [9, 1.75, 5.2], solid(sash))
    if form not in ("g4b", "g4t"):
        both_legs(m, [-0.4, 4.5, -2.4], [4.6, 7.5, 4.8], layered(shorts, [band(SIDES, 0.0, 0.18, "skin")]))
    both_legs(m, [-0.3, 0, -2.6], [4.4, 0.75, 5], solid((150, 96, 52)))  # sandals
    if g5:  # Nika cloud around the neck
        for k in range(8):
            a = k * math.pi / 4
            m.box("body", [math.cos(a) * 4.4 - 1.6, 21.6, math.sin(a) * 3.4 - 1.6], [3.2, 2.6, 3.2], solid((250, 250, 255)))
    if form != "g5" and form not in ("g4b", "g4s", "g4t"):
        hat(m)


_build_orig = build


def build(char, form):  # noqa: F811
    if char in ("yuji", "yuji_final", "yuji_sukuna"):
        style = {"yuji": "yuji", "yuji_final": "yuji_final", "yuji_sukuna": "sukuna"}[char]
        m = Model()
        yuji_body(m, style)
        yuji_shell(m, PINK if style != "sukuna" else (226, 140, 150))
        yuji_hair(m, PINK if style != "sukuna" else (226, 140, 150), style)
        return m
    if char == "luffy":
        m = Model()
        luffy_body(m, form)
        hair = (246, 246, 250) if form == "g5" else (22, 20, 26)
        shell(m, hair, hairline=29.4)
        luffy_hair(m, hair, form == "g5")
        return m
    return _build_orig(char, form)


FORMS.update({
    "yuji": ["base"], "yuji_final": ["base"], "yuji_sukuna": ["base"],
    "luffy": ["base", "g2", "g3", "g4b", "g4s", "g4t", "g5"],
})
BONES.append({"name": "hat", "parent": "head", "pivot": [0, 24, 0]})


# ==================================================================================
# 128 x 128 PASS: HD-skin density (4 px per unit, 32 x 32 faces) with faces drawn
# pixel by pixel from per-character specs, still painted with pixel-art shade ramps.
# ==================================================================================
S = 4

FACE32 = {
    # eye: anime | narrow | big | round | calm ; brow: angled | sharp | flat | thin | none | worried
    "goku": dict(eye="anime", brow="angled", mouth="neutral"),
    "calm": dict(eye="calm", brow="flat", mouth="neutral"),
    "ssj3": dict(eye="anime", brow="none", mouth="neutral"),
    "vegeta": dict(eye="narrow", brow="sharp", mouth="corner", marks=["widow_peak"]),
    "gojo": dict(eye="big", brow="thin", mouth="smirk"),
    "gojo_band": dict(eye="band", brow="none", mouth="smirk"),
    "yuji": dict(eye="anime", brow="flat", mouth="smile", marks=["yuji"]),
    "yuji_final": dict(eye="anime", brow="angled", mouth="neutral", marks=["yuji", "scars"]),
    "sukuna": dict(eye="narrow", brow="sharp", mouth="grin_evil", marks=["second_eyes", "tattoo"]),
    "sukuna_megumi": dict(eye="narrow", brow="sharp", mouth="grin_evil", marks=["second_eyes", "tattoo"]),
    "sukuna_heian": dict(eye="narrow", brow="sharp", mouth="grin_evil", marks=["second_eyes", "tattoo", "mask"]),
    "luffy": dict(eye="round", brow="flat", mouth="grin", marks=["luffy_scar"]),
    "luffy_fight": dict(eye="round", brow="angled", mouth="neutral", marks=["luffy_scar"]),
    "luffy_g5": dict(eye="g5", brow="flat", mouth="big_grin", marks=["luffy_scar"]),
}


def face32(px, W, H, spec, hair, iris, skin):
    sr = ramp(skin)
    ink, white = (20, 12, 14), (252, 252, 252)
    iris = iris or (60, 60, 60)
    hr = ramp(hair)
    k = W / 32.0

    def put(x, y, c):
        for dx in range(int(k)):
            for dy in range(int(k)):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)

    def both(x, y, c):
        put(x, y, c)
        put(31 - x, y, c)

    # base skin with soft side shading and hair shadow under the hairline
    for y in range(32):
        for x in range(32):
            c = sr[2]
            if x < 2 or x > 29:
                c = sr[1]
            if y >= 30 and 5 < x < 26:
                c = sr[1]
            put(x, y, c)
    for y in range(0, 12):
        for x in range(32):
            put(x, y, hr[2])
    for x in range(32):
        put(x, 12, sr[1])
        if x % 4 in (1, 2):
            put(x, 13, sr[1])
    brow_c = dark(hair, 0.8) if sum(hair) > 360 else (28, 22, 26)
    e = spec["eye"]
    # ---- eyes (left side drawn, mirrored)
    if e == "band":
        for y in range(14, 22):
            for x in range(32):
                put(x, y, (18, 18, 24) if y not in (14, 21) else (40, 40, 52))
        for x in range(4, 12):
            put(x, 17 + (x % 3 == 0), (34, 34, 44))
            put(31 - x, 18, (34, 34, 44))
    elif e == "big":
        for y in range(16, 23):
            for x in range(6, 14):
                both(x, y, white)
        for y in range(16, 23):
            for x in range(8, 13):
                t = (y - 16) / 6
                both(x, y, mix(light(iris, 0.45), dark(iris, 0.55), t))
        for y in range(18, 21):
            both(10, y, (16, 40, 96)); both(11, y, (16, 40, 96))
        put(9, 17, white); put(20, 17, white); put(12, 20, white); put(23, 20, white)  # one light source
        for x in range(5, 15):
            both(x, 15, (246, 246, 252))
        both(4, 16, (246, 246, 252)); both(5, 16, (200, 200, 214))
    elif e == "round":
        for y in range(16, 22):
            for x in range(7, 13):
                if (x in (7, 12)) and y in (16, 21):
                    continue
                both(x, y, white)
        for y in range(17, 21):
            for x in range(9, 12):
                both(x, y, (14, 12, 14))
        both(10, 17, white)
        for x in range(7, 13):
            both(x, 15, ink)
    elif e == "g5":
        for y in range(16, 22):
            for x in range(7, 13):
                both(x, y, white)
        for y in range(16, 22):
            for x in range(8, 12):
                both(x, y, (214, 30, 40))
        for y in range(18, 20):
            both(9, y, white); both(10, y, white)
        for x in range(6, 14):
            both(x, 15, ink)
    elif e != "__none__":
        narrow = e == "narrow"
        top = 17 if narrow else 16
        bot = 20 if narrow else 21
        for y in range(top + 1, bot + 1):
            for x in range(7, 13):
                both(x, y, white)
        ic = iris
        for y in range(top + 1, bot + 1):
            for x in range(9, 12 if narrow else 13):
                both(x, y, dark(ic, 0.6) if y == top + 1 else ic)
        for y in range(top + 2, bot):
            both(10, y, dark(ic, 0.3)); both(11, y, dark(ic, 0.3)) if not narrow else None
        # catchlights from one light source: same side in both eyes, a bigger upper one and a soft lower glint
        r0 = 20 if narrow else 19
        put(9, top + 2, white); put(r0, top + 2, white)
        if not narrow:
            put(10, top + 2, white); put(r0 + 1, top + 2, white)
            put(9, top + 3, (232, 236, 244)); put(r0, top + 3, (232, 236, 244))
            put(12, bot, light(ic, 0.45)); put(22, bot, light(ic, 0.45))
        lash = ink
        for x in range(6, 14):
            both(x, top, lash)
        both(5, top + 1, lash)
        if narrow:
            for x in range(8, 14):
                both(x, top + 1, lash) if x > 10 else None
        else:
            both(13, top + 1, lash)
        for x in range(8, 13):
            both(x, bot + 1, sr[1])
        if e == "calm":
            for x in range(7, 13):
                both(x, top + 1, lash) if x < 9 else None
    # ---- brows
    b = spec["brow"]
    if b == "angled":
        for x in range(5, 14):
            y = 12 + (x - 5) // 3
            both(x, y + 1, brow_c); both(x, y + 2, brow_c)
    elif b == "sharp":
        for x in range(4, 14):
            y = 11 + (x - 4) // 2
            both(x, y + 1, brow_c); both(x, y + 2, brow_c) if x > 6 else None
    elif b == "flat":
        for x in range(6, 13):
            both(x, 13, brow_c); both(x, 14, brow_c)
    elif b == "thin":
        for x in range(6, 13):
            both(x, 13 if 7 < x < 12 else 14, (240, 240, 248))
    elif b == "none":
        for x in range(6, 14):
            both(x, 14, sr[1])
        for x in range(8, 13):
            both(x, 13, sr[0])
    # ---- nose
    put(16, 23, sr[1]); put(16, 24, sr[1]); put(15, 24, sr[0])
    # ---- mouth
    m = spec["mouth"]
    mc = (130, 62, 56)
    if m == "neutral":
        for x in range(13, 19):
            put(x, 27, mc)
    elif m == "smile":
        for x in range(13, 19):
            put(x, 27, mc)
        put(12, 26, mc); put(19, 26, mc)
    elif m == "smirk":
        for x in range(13, 19):
            put(x, 27, mc)
        put(19, 26, mc); put(20, 25, mc)
    elif m == "corner":
        for x in range(13, 19):
            put(x, 27, mc)
        put(19, 28, mc)
    elif m in ("grin", "big_grin", "grin_evil"):
        x0, x1 = (10, 21) if m == "big_grin" else (11, 20)
        for x in range(x0, x1 + 1):
            put(x, 25, ink); put(x, 29 if m == "big_grin" else 28, ink)
        for x in range(x0 + 1, x1):
            put(x, 26, white)
            put(x, 27, (120, 30, 40) if m != "grin_evil" else white)
            if m == "big_grin":
                put(x, 28, (150, 40, 50))
        put(x0, 26, ink); put(x1, 26, ink); put(x0 - 1, 25, ink); put(x1 + 1, 25, ink)
        if m == "grin_evil":
            for x in range(x0 + 1, x1, 2):
                put(x, 27, ink)
    # ---- marks
    for mk in spec.get("marks", []):
        if mk == "yuji":
            for x in (8, 9, 10):
                both(x, 23, sr[0])
        if mk == "scars":
            for d in range(4):
                put(21 + d, 22 + d, (196, 120, 110))
            put(6, 24, (196, 120, 110)); put(7, 25, (196, 120, 110))
        if mk == "luffy_scar":
            for x in range(19, 25):
                put(x, 23, (180, 96, 86))
            for x in (20, 22, 24):
                put(x, 22, (180, 96, 86)); put(x, 24, (180, 96, 86))
        if mk == "second_eyes":
            for x in range(8, 13):
                both(x, 23, ink)
            for x in range(9, 12):
                both(x, 24, (210, 30, 40))
        if mk == "tattoo":
            t = (18, 12, 16)
            for x in range(1, 6):
                both(x, 25, t); both(x, 27, t)
            for y in range(27, 32):
                put(15, y, t) if y > 28 else None
            for x in range(13, 19):
                put(x, 31, t)
            for y in range(13, 16):
                put(15, y, t); put(16, y, t)
        if mk == "mask":  # bony second face over the character's right side (viewer's left)
            bone = (226, 214, 196)
            for y in range(12, 30):
                for x in range(1, 11):
                    if (x - 5) ** 2 / 30 + (y - 20) ** 2 / 90 < 1:
                        put(x, y, bone if (x + y) % 6 else (196, 184, 168))
            for x in range(4, 8):
                put(x, 18, ink); put(x, 19, (210, 30, 40) if 4 < x < 7 else ink)
            for x in range(3, 9):
                put(x, 26, ink)


def head_paint(hair, iris, brows=True, style="goku", blindfold=False):  # noqa: F811
    if style == "goku" and not brows:
        style = "ssj3"
    key = "gojo_band" if blindfold else style
    spec = FACE32.get(key, FACE32["goku"])
    hr = ramp(hair)

    def p(face, img):
        w, h = img.size
        px = img.load()
        if face == "north":
            face32(px, w, h, spec, hair, iris, SKIN)
            return
        if face == "up":
            pixel_mat(img, hair, face, seed=11)
            return
        if face == "down":
            pixel_mat(img, SKIN_SH, face, seed=12)
            return
        pixel_mat(img, SKIN, face, noise=0.4, seed=13)
        hair_rows = h * 7 // 8 if face == "south" else h * 6 // 16
        for y in range(hair_rows):
            for x in range(w):
                px[x, y] = hr[2] + (255,)
        if face in ("east", "west"):
            front = w - 1 if face == "east" else 0
            for y in range(hair_rows, h * 10 // 16):
                for dx in range(max(2, w // 8)):
                    xx = front - dx if face == "east" else front + dx
                    px[xx, y] = hr[1] + (255,)
            if blindfold:
                for y in range(h * 7 // 16, h * 11 // 16):
                    for x in range(w):
                        px[x, y] = (18, 18, 24, 255)
            if "mask" in spec.get("marks", []) and face == "east":
                # the second face on the right side of the head
                for y in range(h * 6 // 16, h * 15 // 16):
                    for x in range(w // 4, w):
                        px[x, y] = (220, 208, 190, 255) if (x + y) % 7 else (190, 178, 160, 255)
                for x in range(w // 3, w * 2 // 3):
                    px[x, h // 2] = (20, 12, 14, 255)
                    px[x, h // 2 + 1] = (210, 30, 40, 255)
    return p


def head_paint2(hair, iris, style, brows=True, blindfold=False):  # noqa: F811
    return head_paint(hair, iris, brows, style, blindfold)


# ---------------------------------------------------------------- Sukuna tattoos as bands, not whiskers
_face32_orig = face32


def face32(px, W, H, spec, hair, iris, skin):  # noqa: F811
    _face32_orig(px, W, H, spec, hair, iris, skin)
    if "tattoo" not in spec.get("marks", []):
        return
    k = W / 32.0
    sr = ramp(skin)
    t = (18, 12, 16)

    def put(x, y, c):
        for dx in range(int(k)):
            for dy in range(int(k)):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    for side in (0, 1):
        X = (lambda x: x) if side == 0 else (lambda x: 31 - x)
        for x in range(1, 6):  # wipe the thin lines, draw thick cheek bands that taper toward the nose
            for y in (25, 27):
                put(X(x), y, sr[2])
        for x in range(0, 7):
            put(X(x), 25, t); put(X(x), 26, t) if x < 5 else None
        for x in range(0, 4):
            put(X(x), 28, t)


# ---------------------------------------------------------------- bones with extra arms (Heian Sukuna)
BONES_4ARMS = BONES + [
    {"name": "rightArm2", "parent": "body", "pivot": [-5, 18.5, 0.5], "rotation": [10, 0, 22]},
    {"name": "leftArm2", "parent": "body", "pivot": [5, 18.5, 0.5], "rotation": [10, 0, -22]},
]

KIMONO = (238, 234, 226)
OBI = (24, 20, 30)
MEGUMI_UNI = (22, 24, 34)


def sukuna_heian_body(m):
    m.bones = BONES_4ARMS
    hand = layered(SKIN, [band(SIDES, 0.0, 0.08, "skin")])
    def belly_mouth(face, px, w, h, base):
        if face != "north":
            return
        cy, cx = int(h * 0.62), w // 2
        for x in range(cx - 7, cx + 8):
            _put(px, w, h, x, cy, (20, 12, 14)); _put(px, w, h, x, cy + 4, (20, 12, 14))
            if x % 2 == 0:
                _put(px, w, h, x, cy + 1, (250, 250, 250)); _put(px, w, h, x, cy + 3, (250, 250, 250))
            _put(px, w, h, x, cy + 2, (110, 20, 30))
        for y in range(2, int(h * 0.45)):  # chest tattoo lines
            _put(px, w, h, cx - 6, y, (18, 12, 16)); _put(px, w, h, cx + 5, y, (18, 12, 16))
    base_body(m, layered(SKIN, [belly_mouth]), solid(SKIN), solid(KIMONO), head_paint(PINK, (200, 30, 40), True, "sukuna_heian"))
    # open white kimono (chest + belly mouth stay visible), black obi, wide sleeves
    def kimono_open(face, px, w, h, base):
        if face == "north":
            sr = ramp(SKIN)
            for y in range(h):
                half = max(2, int((1 - y / h) * w * 0.32) + 3)
                for x in range(w // 2 - half, w // 2 + half):
                    if y < h * 0.8:
                        px[x, y] = (0, 0, 0, 0)
    m.box("body", [-4.4, 12, -2.4], [8.8, 12, 4.8], layered(KIMONO, [kimono_open, lines((SIDES, [[(0.5, 0.8), (0.5, 1)]]), dark(KIMONO, 0.8))]))
    m.box("body", [-4.6, 11, -2.6], [9.2, 2.5, 5.2], layered(OBI, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), (60, 50, 70))]))
    both_arms(m, [3.6, 15, -2.6], [5.2, 9, 5.2], layered(KIMONO, [lines((SIDES, [[(0, 0.9), (1, 0.9)]]), dark(KIMONO, 0.75))]))
    both_legs(m, [-0.4, 0, -2.6], [4.8, 11, 5.2], layered(KIMONO, [lines((SIDES, [[(0.5, 0), (0.45, 1)]]), dark(KIMONO, 0.78))]))
    # the lower pair of arms (bare, tattooed wrists)
    for bone, x in (("rightArm2", 4.2), ("leftArm2", -7.8)):
        m.box(bone, [x, 7.5, -1.4], [3.6, 11, 3.6], layered(SKIN, [lines((SIDES, [[(0, 0.82), (1, 0.82)], [(0, 0.86), (1, 0.86)]]), (18, 12, 16))]))
        m.box(bone, [x - 0.3, 14, -1.7], [4.2, 4.5, 4.2], solid(KIMONO))
    both_arms(m, [3.85, 12.4, -2.15], [4.3, 0.75, 4.3], solid((16, 12, 16)))


def megumi_body(m):
    hand = layered(MEGUMI_UNI, [band(SIDES + ("down",), 0.9, 1.0, "skin")])
    base_body(m, solid(MEGUMI_UNI), hand, layered(MEGUMI_UNI, [lines((SIDES, [[(0.5, 0), (0.5, 1)]]), (46, 50, 72))]),
              head_paint((20, 20, 28), (200, 30, 40), True, "sukuna_megumi"))
    m.box("body", [-4.3, 10, -2.3], [8.6, 14, 4.6], layered(MEGUMI_UNI, [lines((("north",), [[(0.5, 0), (0.5, 1)]]), (8, 8, 14))]))
    m.box("body", [-3.25, 23.5, -2.6], [6.5, 2.25, 5.2], solid((34, 38, 56)))
    both_arms(m, [3.8, 15, -2.2], [4.4, 9, 4.4], solid(MEGUMI_UNI))
    both_arms(m, [3.85, 12.5, -2.15], [4.3, 0.75, 4.3], solid((16, 12, 16)))
    both_legs(m, [-0.3, 0, -2.6], [4.4, 1.5, 5], solid((14, 14, 18)))


def megumi_hair(m, c):
    hp = hair_paint(c)
    shell(m, c, hairline=29.5, sideburn=False)
    for k in range(9):
        a = k * 2 * math.pi / 9
        x, z = math.sin(a) * 2.8, -math.cos(a) * 2.8
        if z < -2.2:
            continue
        m.strand([x, 31.6, z], [math.sin(a) * 0.8, 1, -math.cos(a) * 0.8 + 0.3], 5.2, 3.6, hp, bend=(0, -0.15, 0.05))
    m.strand([0, 32, 0], [0, 1, 0.3], 5.5, 4, hp)
    m.mirror_strand([1.6, 31.8, -3.4], [0.3, 1, -0.4], 4, 3.2, hp)
    m.strand([0, 31.5, -4.1], [0, -1, -0.8], 2.4, 2.6, hp)


def heian_hair(m, c):
    hp = hair_paint(c)
    shell(m, c, hairline=29.8, sideburn=False)
    for x, z, dz in ((-2.6, -1.5, 0.6), (0, -2, 0.7), (2.6, -1.5, 0.6), (-3.4, 1, 0.9), (3.4, 1, 0.9), (0, 1.8, 1)):
        m.strand([x, 31.8, z], [x * 0.12, 1, dz], 5.2, 4, hp, bend=(0, -0.1, 0.1))


# ---------------------------------------------------------------- Luffy redesign (slim build, real outfit details)
def luffy_base_body(m, skin_col, arm_paint, shorts, vest, sash, face_style, hair, iris, slim=True):
    aw = 3 if slim else 4
    m.box("head", [-4, 24, -4], [8, 8, 8], head_paint(hair, iris, True, face_style))
    m.box("body", [-4, 12, -2], [8, 12, 4], layered(skin_col, [x_scar]))
    m.box("rightArm", [4, 12, -2], [aw, 12, 4], arm_paint)
    m.box("leftArm", [-4 - aw, 12, -2], [aw, 12, 4], arm_paint)
    m.box("rightLeg", [-0.1, 0, -2], [4, 12, 4], solid(skin_col))
    m.box("leftLeg", [-3.9, 0, -2], [4, 12, 4], solid(skin_col))
    ears(m)
    return aw


def luffy_outfit(m, vest, shorts, sash, aw):
    def vest_detail(face, px, w, h, base):
        if face != "north":
            return
        sr = ramp(SKIN)
        for y in range(h):  # open front: chest with the X scar
            for x in range(w // 2 - 5, w // 2 + 5):
                px[x, y] = (sr[2] if (x + y) % 7 else sr[1]) + (255,)
        cx, cy = w // 2, h // 4
        for d in range(-4, 5):
            _put(px, w, h, cx + d, cy + d, (186, 104, 92)); _put(px, w, h, cx + d, cy - d, (186, 104, 92))
        for y in range(4, h, 8):
            _put(px, w, h, w // 2 - 7, y, (240, 200, 60)); _put(px, w, h, w // 2 - 7, y + 1, (200, 160, 40))
        dk = dark(vest, 0.6)
        for y in range(h):
            _put(px, w, h, w // 2 - 6, y, dk); _put(px, w, h, w // 2 + 5, y, dk)
    m.box("body", [-4.3, 12.5, -2.3], [8.6, 11.75, 4.6], layered(vest, [vest_detail]))
    m.box("rightArm", [3.75, 19.5, -2.3], [aw + 0.5, 4.75, 4.6], layered(vest, [lines((SIDES, [[(0, 0.9), (1, 0.9)]]), dark(vest, 0.6))]))
    m.box("leftArm", [-3.75 - aw - 0.5, 19.5, -2.3], [aw + 0.5, 4.75, 4.6], layered(vest, [lines((SIDES, [[(0, 0.9), (1, 0.9)]]), dark(vest, 0.6))]))
    m.box("body", [-4.5, 11, -2.6], [9, 1.75, 5.2], layered(sash, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), dark(sash, 0.7))]))
    m.strand([-3.6, 11.2, -2.4], [-0.25, -1, -0.1], 4.5, 1.5, solid(sash), bone="body", segs=2)
    both_legs(m, [-0.4, 4.25, -2.4], [4.6, 7.75, 4.8], layered(shorts, [lines((SIDES, [[(0.3, 0), (0.35, 1)], [(0.7, 0.2), (0.65, 0.8)]]), dark(shorts, 0.72))]))
    both_legs(m, [-0.55, 4, -2.55], [4.9, 1.25, 5.1], solid(light(shorts, 0.55)))  # rolled cuffs
    both_legs(m, [-0.3, 0, -2.6], [4.4, 0.6, 5], solid((150, 96, 52)))
    both_legs(m, [0.3, 0.6, -2.62], [3.2, 0.8, 0.3], solid((120, 72, 40)))  # sandal strap


def flame_pattern(face, px, w, h, base):
    """Red flame lines over haki-black limbs (Gear 4)."""
    if face not in SIDES:
        return
    for x in range(1, w - 1, 3):
        for y in range(h):
            if int(h * 0.15 + (math.sin((x + y * 0.5) * 0.9) + 1) * h * 0.08) == y % (h // 2 or 1):
                _put(px, w, h, x, y, (200, 40, 30))


def luffy_body(m, form):  # noqa: F811
    g5 = form == "g5"
    skin_col = (240, 132, 128) if form == "g2" else SKIN
    vest = (244, 244, 240) if g5 else VEST
    shorts = (236, 236, 232) if g5 else SHORTS
    sash = (190, 120, 210) if g5 else SASH
    hair = (246, 246, 250) if g5 else (22, 20, 26)
    iris = (220, 40, 40) if g5 else (40, 30, 30)
    face = "luffy_g5" if g5 else ("luffy_fight" if form.startswith("g4") or form == "g2" else "luffy")
    if form in ("g4b", "g4s", "g4t"):
        haki_limb = layered(G4_HAKI, [flame_pattern])
        torso = layered((236, 128, 118), [x_scar, flame_pattern])
        m.box("head", [-4, 24, -4], [8, 8, 8], head_paint(hair, iris, True, face))
        ears(m)
        if form == "g4b":
            m.box("body", [-6, 11, -3.5], [12, 13, 7], torso)
            both_arms(m, [4.5, 8, -3.4], [7, 16, 6.8], haki_limb)
            both_arms(m, [4.2, 20, -3.8], [7.6, 5, 7.6], layered((236, 128, 118), [flame_pattern]))  # huge shoulders
            both_legs(m, [-0.6, 0, -2.8], [5.4, 12, 5.6], haki_limb)
            m.box("body", [-6.5, 22.5, -4.2], [13, 3.5, 8.4], solid((246, 246, 246)))  # steam scarf
            m.box("body", [-6.2, 10, -3.8], [12.4, 2, 7.6], solid(SASH))
        elif form == "g4s":
            m.box("body", [-4.6, 12, -2.6], [9.2, 12, 5.2], torso)
            both_arms(m, [3.8, 10, -2.4], [4.8, 14, 4.8], haki_limb)
            both_legs(m, [-0.4, 0, -2.4], [4.8, 12, 4.8], haki_limb)
            m.box("body", [-4.8, 21.5, -3], [9.6, 3.2, 6], solid((246, 246, 246)))
            m.strand([0, 23, 2.9], [0, -1, 0.3], 17, 8, solid((240, 240, 240)), bone="body", thick=0.3)
            m.box("body", [-4.8, 10.5, -2.8], [9.6, 2, 5.6], solid(SASH))
        else:  # Tankman
            m.box("body", [-7.5, 8, -6.5], [15, 16, 13], torso)
            both_arms(m, [5.5, 10, -3.2], [6.4, 14, 6.4], haki_limb)
            both_legs(m, [-0.6, 0, -2.8], [5.4, 9, 5.6], haki_limb)
            m.box("body", [-5.5, 22.5, -4.5], [11, 2.5, 9], solid((246, 246, 246)))
        return
    aw = luffy_base_body(m, skin_col, layered(skin_col, [lines((SIDES, [[(0.5, 0.45), (0.5, 0.55)]]), dark(skin_col, 0.8))]),
                         shorts, vest, sash, face, hair, iris)
    luffy_outfit(m, vest, shorts, sash, aw)
    if g5:
        for k in range(10):
            a = k * math.pi / 5
            m.box("body", [math.cos(a) * 4.6 - 1.7, 21.4 + (k % 2) * 0.6, math.sin(a) * 3.6 - 1.7], [3.4, 2.8, 3.4], solid((252, 252, 255)))
    else:
        hat(m)


def luffy_hair(m, c, g5=False, form="base"):  # noqa: F811
    hp = hair_paint(c)
    if g5:
        for x, z, L in ((-2.4, -2, 7), (0, -2.4, 8), (2.4, -2, 7), (-3.3, 0.8, 6.5), (3.3, 0.8, 6.5), (-1.5, 2.6, 7), (1.5, 2.6, 7), (0, 0.5, 8.5)):
            m.strand([x, 31.8, z], [x * 0.18, 1, z * 0.12 + 0.15], L, 4.6, hp, bend=(x * 0.04, -0.05, 0.12))
        m.mirror_strand([4.2, 30, -1], [0.7, 0.6, 0], 5, 3.4, hp, bend=(0, 0.1, 0))
        return
    if form in ("g4b", "g4s", "g4t"):  # hair flares up and back like a flame
        for x, z in ((-2.2, -1.5), (0, -2), (2.2, -1.5), (-3, 1), (3, 1), (0, 1.5)):
            m.strand([x, 31.8, z], [x * 0.2, 1, 0.5], 6 if form == "g4s" else 5, 3.6, hp, bend=(0, -0.1, 0.15))
        if form == "g4s":
            for x in (-2.5, 0, 2.5):
                m.strand([x, 30, 4], [x * 0.05, -0.3, 1], 7, 3.2, hp)
        m.strand([0.2, 31.5, -4.2], [0.1, -1, -0.7], 2.6, 2.6, hp)
        return
    m.strand([-2.2, 31.4, -4.1], [-0.3, -1, -0.6], 2.8, 2.8, hp)
    m.strand([0.2, 31.5, -4.2], [0.1, -1, -0.7], 2.6, 2.6, hp)
    m.strand([2.4, 31.4, -4.1], [0.35, -1, -0.6], 2.8, 2.8, hp)
    m.mirror_strand([4.2, 30.5, -1.8], [0.3, -1, -0.15], 3, 2.4, hp)
    m.mirror_strand([4.2, 30.5, 1.2], [0.35, -1, 0.2], 3.2, 2.6, hp)
    for x in (-2.5, 0, 2.5):
        m.strand([x, 30.5, 4.2], [x * 0.08, -1, 0.35], 3.4, 3, hp)


_build_prev = build


def build(char, form):  # noqa: F811
    if char == "sukuna":
        m = Model()
        if form == "yuji":
            yuji_body(m, "sukuna")
            yuji_shell(m, (226, 140, 150))
            yuji_hair(m, (226, 140, 150), "sukuna")
        elif form == "megumi":
            megumi_body(m)
            megumi_hair(m, (20, 20, 28))
        else:
            sukuna_heian_body(m)
            heian_hair(m, (226, 140, 150))
        return m
    if char == "luffy":
        m = Model()
        luffy_body(m, form)
        hair = (246, 246, 250) if form == "g5" else (22, 20, 26)
        shell(m, hair, hairline=29.4)
        luffy_hair(m, hair, form == "g5", form)
        return m
    return _build_prev(char, form)


FORMS.pop("yuji_sukuna", None)
FORMS["sukuna"] = ["yuji", "megumi", "heian"]


def flame_pattern(face, px, w, h, base):  # noqa: F811
    """Clear red flame strokes over haki-black limbs / skin (Gear 4)."""
    if face not in SIDES:
        return
    for c in range(1, w, 5):
        for y in range(int(h * 0.15), h):
            x = int(c + math.sin(y * 0.35 + c) * 1.6)
            _put(px, w, h, x, y, (214, 40, 30))
            _put(px, w, h, x + 1, y, (150, 24, 20))
            if (y + c) % 7 == 0:
                _put(px, w, h, x - 1, y, (250, 120, 40))


_heian_orig = sukuna_heian_body


def sukuna_heian_body(m):  # noqa: F811
    _heian_orig(m)
    # move the lower arms outward/back so they show even without the bone tilt
    for cube in m.cubes:
        if cube["bone"] == "rightArm2":
            cube["frm"][0] += 1.6; cube["frm"][2] += 1.2
        if cube["bone"] == "leftArm2":
            cube["frm"][0] -= 1.6; cube["frm"][2] += 1.2


def torso_flames(face, px, w, h, base):
    """Sparse black haki flames creeping onto the shoulders and chest edges."""
    if face not in SIDES:
        return
    for c in (1, w - 3):
        for y in range(0, int(h * 0.55)):
            x = int(c + math.sin(y * 0.4 + c) * 1.4)
            _put(px, w, h, x, y, (24, 20, 26)); _put(px, w, h, x + 1, y, (24, 20, 26))
            if y % 5 == 0:
                _put(px, w, h, x + 2, y, (200, 40, 30))


_luffy_body_v2 = luffy_body


def luffy_body(m, form):  # noqa: F811
    _luffy_body_v2(m, form)
    if form in ("g4b", "g4s", "g4t"):
        for cube in m.cubes:
            if cube["bone"] == "body" and cube["size"][1] >= 12 and cube["frm"][1] <= 12:
                cube["paint"] = layered((236, 128, 118), [x_scar, torso_flames])


# ==================================================================================
# CLEAN CEL PIXEL ART (final art style)
# No random noise. One fixed key light (front-top-left), 5 hand-picked tones per
# material, deliberate ambient occlusion at the bottom of each part, rim light on top,
# anime shine bands on hair and crisp dark separations between hair tufts.
# ==================================================================================
def tones(base):
    return [
        mix(dark(base, 0.48), (22, 18, 60), 0.18),   # 0 deep
        mix(dark(base, 0.74), (34, 28, 86), 0.08),   # 1 shadow
        tuple(base),                                  # 2 base
        mix(light(base, 0.2), (255, 244, 220), 0.06),  # 3 light
        mix(light(base, 0.46), (255, 248, 230), 0.1),  # 4 shine
    ]


FACE_TONE = {"up": 3, "north": 2, "west": 2, "east": 1, "south": 1, "down": 0}


def pixel_mat(img, base, face, noise=0.0, vgrad=1.0, ao=True, seed=0):  # noqa: F811
    w, h = img.size
    px = img.load()
    t = tones(base)
    main = FACE_TONE[face]
    for y in range(h):
        for x in range(w):
            k = main
            if face not in ("up", "down") and h >= 6:
                if y >= h - max(1, h // 9):
                    k = max(0, main - 1)          # contact shadow at the bottom of the part
                elif y == 0 and face in ("north", "west"):
                    k = min(4, main + 1)          # rim light
            px[x, y] = t[k] + (255,)


def hair_paint(base):  # noqa: F811
    t = tones(base)
    dark_hair = sum(base) < 200
    if dark_hair:  # black hair needs blue-grey lights to read in game
        t = [(8, 8, 14), (20, 20, 30), tuple(base), (58, 62, 86), (104, 112, 146)]

    def p(face, img):
        w, h = img.size
        px = img.load()
        main = {"up": 3, "north": 2, "west": 3, "east": 1, "south": 1, "down": 0}[face]
        for y in range(h):
            v = 1 - y / max(1, h - 1)  # 1 at the tip
            for x in range(w):
                k = main
                if face not in ("up", "down"):
                    if v > 0.78:
                        k += 1                      # tips catch the light
                    elif v < 0.22:
                        k -= 1                      # roots sit in shadow
                    if w >= 6 and x % 4 == 0 and 0.15 < v < 0.7:
                        k -= 1                      # strand separation
                    if face in ("north", "west") and 0.5 < v < 0.62 and x % 4 in (1, 2):
                        k = 4                       # anime shine band
                    if (x == 0 or x == w - 1) and face in ("east", "south"):
                        k = 0                       # crisp edge between tufts
                px[x, y] = t[max(0, min(4, k))] + (255,)
    return p


_shell_paint_masked = shell_paint


def shell_paint(base, **kw):  # noqa: F811
    inner = _shell_paint_masked(base, **kw)
    t = tones(base)
    if sum(base) < 200:
        t = [(8, 8, 14), (20, 20, 30), tuple(base), (58, 62, 86), (104, 112, 146)]

    def p(face, img):
        inner(face, img)
        px = img.load()
        w, h = img.size
        main = {"up": 3, "north": 2, "west": 2, "east": 1, "south": 1, "down": 0}[face]
        for y in range(h):
            for x in range(w):
                if px[x, y][3] == 0:
                    continue
                k = main
                if face == "up" and (x + y) % 9 == 0:
                    k = 4
                below_empty = y + 1 >= h or px[x, y + 1][3] == 0
                if face != "up" and below_empty:
                    k = 0                           # dark line along the hairline / lock tips
                elif face != "up" and w >= 8 and x % 5 == 0:
                    k = max(0, main - 1)
                px[x, y] = t[k] + (255,)
    return p


# ---------------------------------------------------------------- clean art, pass 2
DARK_HAIR = [(10, 10, 14), (24, 24, 32), (40, 40, 52), (70, 72, 92), (112, 116, 142)]


def hair_tones(base):
    return DARK_HAIR if sum(base) < 200 else tones(base)


def pixel_mat(img, base, face, noise=0.0, vgrad=1.0, ao=True, seed=0):  # noqa: F811
    """Clean tones + bevel: darker outer columns give each part a rounded, sculpted read."""
    w, h = img.size
    px = img.load()
    t = tones(base)
    main = FACE_TONE[face]
    for y in range(h):
        for x in range(w):
            k = main
            if face not in ("up", "down"):
                if h >= 6 and y >= h - max(1, h // 9):
                    k -= 1
                elif y == 0 and face in ("north", "west") and h >= 6:
                    k += 1
                if w >= 8 and (x == 0 or x == w - 1):
                    k -= 1
                elif w >= 12 and face in ("north", "west") and x in (2, 3) and y < h * 0.6:
                    k += 1                          # soft highlight down the lit side
            px[x, y] = t[max(0, min(4, k))] + (255,)


def hair_paint(base):  # noqa: F811
    t = hair_tones(base)

    def p(face, img):
        w, h = img.size
        px = img.load()
        main = {"up": 3, "north": 2, "west": 3, "east": 1, "south": 1, "down": 0}[face]
        for y in range(h):
            v = 1 - y / max(1, h - 1)
            for x in range(w):
                k = main
                if face not in ("up", "down"):
                    if v > 0.8:
                        k += 1
                    elif v < 0.25:
                        k -= 1
                    if face in ("north", "west") and w >= 4 and 0.52 < v < 0.64 and 0 < x < w - 1:
                        k = 4
                    if face == "north" and x == w - 1:
                        k = min(k, 1)
                px[x, y] = t[max(0, min(4, k))] + (255,)
    return p


_shell_paint_masked2 = _shell_paint_masked


def shell_paint(base, **kw):  # noqa: F811
    inner = _shell_paint_masked2(base, **kw)
    t = hair_tones(base)

    def p(face, img):
        inner(face, img)
        px = img.load()
        w, h = img.size
        main = {"up": 3, "north": 2, "west": 2, "east": 1, "south": 1, "down": 0}[face]
        for y in range(h):
            for x in range(w):
                if px[x, y][3] == 0:
                    continue
                k = main
                below_empty = y + 1 >= h or px[x, y + 1][3] == 0
                if face != "up" and below_empty:
                    k = 0
                elif face == "up" and 0.35 < y / h < 0.45:
                    k = 4
                px[x, y] = t[k] + (255,)
    return p


# flatter, sharper anime hair blades
def _strand_blade(self, base, d, length, width, paint, bend=(0, 0, 0), segs=3, bone="hair", thick=None):
    if bone == "hair":
        width *= 1.15
        thick = thick or 0.62
    return _strand_orig(self, base, d, length, width, paint, bend, segs, bone, thick)


Model.strand = _strand_blade


# ---------------------------------------------------------------- smooth tapered hair blades
def _strand_smooth(self, base, d, length, width, paint, bend=(0, 0, 0), segs=3, bone="hair", thick=None):
    if bone != "hair":
        return _strand_orig(self, base, d, length, width, paint, bend, segs, bone, thick)
    n = 6 if length >= 5 else 4 if length >= 3 else 3
    width *= 1.15
    thick = thick or 0.62
    p = list(base)
    d = norm(d)
    step = length / n
    seg_len = step * 1.7
    bscale = 3.0 / n
    for i in range(n):
        f = i / (n - 1)
        w = max(0.5, round(width * (1 - 0.8 * f) * 4) / 4)
        tk = max(0.5, round(thick * w * 4) / 4)
        L = max(0.75, round(seg_len * 4) / 4)
        ax, az = math.degrees(math.asin(clampf(d[2]))), math.degrees(math.atan2(-d[0], d[1]))
        self.box(bone, [p[0] - w / 2, p[1], p[2] - tk / 2], [w, L, tk], paint,
                 rot=[round(ax, 2), 0, round(az, 2)], pivot=[round(p[0], 3), round(p[1], 3), round(p[2], 3)])
        p = [p[k] + d[k] * step for k in range(3)]
        d = norm([d[k] + bend[k] * bscale for k in range(3)])


Model.strand = _strand_smooth


def hair_paint(base):  # noqa: F811
    t = hair_tones(base)

    def p(face, img):
        w, h = img.size
        px = img.load()
        main = {"up": 3, "north": 2, "west": 3, "east": 1, "south": 1, "down": 0}[face]
        for y in range(h):
            for x in range(w):
                k = main
                if face == "north" and x == w - 1 and w >= 3:
                    k = min(k, 1)
                if face == "west" and x == 0 and w >= 3:
                    k = 4
                px[x, y] = t[max(0, min(4, k))] + (255,)
    return p


def yuji_hair(m, c, style):  # noqa: F811
    hp = hair_paint(c)
    if style == "sukuna":  # swept up and back, spikier
        for x, z in ((-2.4, -2.2), (0, -2.6), (2.4, -2.2), (-3.4, 0.4), (3.4, 0.4), (-1.6, 2), (1.6, 2)):
            m.strand([x, 31.8, z], [x * 0.14, 1, 0.75], 5.2, 3.8, hp, bend=(0, -0.12, 0.08))
        return
    # Itadori: short spiky hair standing up, parted spikes over the forehead
    for x, z, dx, dz in ((-2.4, -2.4, -0.35, -0.35), (0, -2.7, 0.0, -0.4), (2.4, -2.4, 0.35, -0.35),
                         (-3.4, 0, -0.55, 0.05), (3.4, 0, 0.55, 0.05), (-1.8, 1.4, -0.25, 0.4), (1.8, 1.4, 0.25, 0.4), (0, 2.8, 0, 0.6)):
        m.strand([x, 31.8, z], [dx, 1, dz], 4.6, 3.6, hp, bend=(dx * 0.1, -0.05, dz * 0.1))
    for x in (-1.8, 1.8):
        m.strand([x, 31.9, -4.0], [x * 0.12, -1, -0.9], 2.4, 2.8, hp)
    if style == "yuji_final":
        m.mirror_strand([3.9, 30.6, -1.2], [0.7, 0.35, -0.1], 3.4, 2.8, hp)


_luffy_hair_prev_impl = luffy_hair

# ==================================================================================
# SUKUNA (redraw) + LUFFY GEARS (redraw)
# ==================================================================================
FACE32["sukuna"] = dict(eye="narrow", brow="sharp", mouth="none", marks=["sukuna_face"])
FACE32["sukuna_megumi"] = dict(eye="narrow", brow="sharp", mouth="none", marks=["sukuna_face"])
FACE32["sukuna_heian"] = dict(eye="narrow", brow="sharp", mouth="none", marks=["sukuna_face", "heian_mask"])
FACE32["luffy_g4"] = dict(eye="round", brow="angled", mouth="clench", marks=["luffy_scar"])
_face32_v2 = face32


def face32(px, W, H, spec, hair, iris, skin):  # noqa: F811
    marks = spec.get("marks", [])
    base_spec = dict(spec, marks=[m for m in marks if m not in ("sukuna_face", "heian_mask")])
    if base_spec.get("mouth") in ("none", "clench"):
        base_spec["mouth"] = "neutral" if base_spec["mouth"] == "clench" else "none"
    _face32_v2(px, W, H, base_spec, hair, iris, skin)
    k = W / 32.0
    sr = ramp(skin)
    ink, t, white, red = (20, 12, 14), (16, 10, 14), (250, 250, 250), (210, 28, 38)

    def put(x, y, c):
        for dx in range(int(k)):
            for dy in range(int(k)):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)

    def both(x, y, c):
        put(x, y, c); put(31 - x, y, c)
    if spec.get("mouth") == "clench":  # Gear 4: gritted teeth
        for x in range(12, 20):
            put(x, 26, ink); put(x, 28, ink); put(x, 27, white if x % 2 else (200, 200, 200))
    if "sukuna_face" in marks:
        # second pair of eyes opening under the natural eyes
        for x in range(8, 13):
            both(x, 23, ink)
        for x in (10, 11):
            both(x, 24, red)
        both(9, 24, ink); both(12, 24, ink)
        # one thick band across each cheek, angled down toward the nose
        for x in range(0, 7):
            both(x, 26 + (x > 3), t); both(x, 27 + (x > 3), t) if x < 6 else None
        # streak across the bridge of the nose
        for x in range(13, 19):
            put(x, 21, t)
        # forehead mark
        for y in (12, 13, 14):
            put(15, y, t); put(16, y, t)
        put(14, 12, t); put(17, 12, t)
        # chin marks
        for y in (29, 30, 31):
            put(13, y, t); put(18, y, t)
        # confident smirk, a glimpse of fangs on one side
        mc = (110, 40, 40)
        for x in range(12, 19):
            put(x, 27, mc)
        put(19, 26, mc); put(20, 25, mc)
        put(17, 28, white); put(18, 28, white)
    if "heian_mask" in marks:
        bone, bone_sh = (228, 218, 200), (196, 184, 166)
        for y in range(12, 31):
            for x in range(0, 12):
                if (x - 5) ** 2 / 36 + (y - 21) ** 2 / 100 < 1:
                    put(x, y, bone if (x * 2 + y) % 9 else bone_sh)
        for x in range(3, 9):
            put(x, 18, ink)
        for x in (5, 6):
            put(x, 19, red)
        for x in range(2, 10, 2):
            put(x, 27, ink); put(x + 1, 28, ink)


# ---------------------------------------------------------------- Sukuna bodies
def sukuna_yuji_hair(m, c):
    hp = hair_paint(c)
    shell(m, c, hairline=30.2, sideburn=False, teeth=0.3)
    for x, z, dz in ((-2.6, -2.6, 0.9), (-0.9, -2.9, 0.95), (0.9, -2.9, 0.95), (2.6, -2.6, 0.9),
                     (-3.5, -0.2, 1.0), (3.5, -0.2, 1.0), (-1.8, 1.6, 1.0), (1.8, 1.6, 1.0)):
        m.strand([x, 31.6, z], [x * 0.12, 0.85, dz], 5.6, 3.4, hp, bend=(0, -0.18, 0.08))


def megumi_hair(m, c):  # noqa: F811 — Megumi's porcupine hair
    hp = hair_paint(c)
    shell(m, c, hairline=29.4, sideburn=False)
    for k in range(12):
        a = k * 2 * math.pi / 12
        x, z = math.sin(a) * 3.1, -math.cos(a) * 3.1
        up = 1.0 if z > -2 else 0.7
        m.strand([x, 31.4, z], [math.sin(a) * 0.9, up, -math.cos(a) * 0.9 + 0.25], 6, 3.4, hp, bend=(0, -0.2, 0))
    m.strand([0, 32, 0.3], [0, 1, 0.2], 6.5, 3.8, hp)
    for x in (-2, 0, 2):
        m.strand([x, 31.6, -4.1], [x * 0.15, -1, -0.9], 2.6, 2.4, hp)


def heian_hair(m, c):  # noqa: F811
    hp = hair_paint(c)
    shell(m, c, hairline=30.0, sideburn=False, teeth=0.3)
    for k in range(10):
        a = k * 2 * math.pi / 10
        x, z = math.sin(a) * 3, -math.cos(a) * 3
        if z < -2.4:
            continue
        m.strand([x, 31.5, z], [math.sin(a) * 0.7, 0.9, -math.cos(a) * 0.7 + 0.6], 6.5, 3.8, hp, bend=(0, -0.2, 0.1))
    m.strand([0, 31.8, -1], [0, 1, 0.5], 6, 4, hp)


def sukuna_heian_body(m):  # noqa: F811
    m.bones = BONES_4ARMS
    tat = (16, 10, 14)

    def torso(face, px, w, h, base):
        if face != "north":
            return
        cx, cy = w // 2, int(h * 0.64)
        for x in range(cx - 7, cx + 8):  # the mouth on his abdomen
            _put(px, w, h, x, cy, tat); _put(px, w, h, x, cy + 5, tat)
            _put(px, w, h, x, cy + 1, (250, 250, 250) if x % 2 == 0 else (120, 20, 30))
            _put(px, w, h, x, cy + 4, (250, 250, 250) if x % 2 == 1 else (120, 20, 30))
            _put(px, w, h, x, cy + 2, (110, 16, 26)); _put(px, w, h, x, cy + 3, (90, 10, 20))
        for y in range(3, int(h * 0.5)):  # chest tattoo lines
            _put(px, w, h, cx - 8, y, tat); _put(px, w, h, cx + 7, y, tat)
        for x in range(cx - 8, cx + 8):
            _put(px, w, h, x, int(h * 0.5), tat)
    base_body(m, layered(SKIN, [torso]), layered(SKIN, [lines((SIDES, [[(0, 0.86), (1, 0.86)], [(0, 0.92), (1, 0.92)]]), tat)]),
              solid((200, 196, 190)), head_paint((226, 140, 150), (200, 30, 40), True, "sukuna_heian"))

    def open_robe(face, px, w, h, base):
        if face == "north":
            for y in range(h):
                half = int(w * 0.3 * (1 - y / h)) + 4
                for x in range(w // 2 - half, w // 2 + half):
                    if y < h * 0.85:
                        px[x, y] = (0, 0, 0, 0)
    robe = (238, 236, 230)
    m.box("body", [-4.5, 11.5, -2.5], [9, 12.5, 5], layered(robe, [open_robe]))
    m.box("body", [-4.7, 10.5, -2.7], [9.4, 2.2, 5.4], layered((40, 34, 46), [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), (90, 80, 100))]))
    m.strand([-1.5, 10.6, -2.8], [-0.2, -1, -0.15], 5, 1.6, solid((40, 34, 46)), bone="body", segs=2)
    # wide kimono sleeves hanging from the upper arms
    both_arms(m, [3.4, 14, -3], [5.6, 10, 6], layered(robe, [lines((SIDES, [[(0, 0.95), (1, 0.95)]]), dark(robe, 0.75))]))
    # hakama
    both_legs(m, [-0.6, 0, -2.8], [5.2, 11, 5.6], layered((206, 200, 194), [lines((SIDES, [[(0.3, 0), (0.25, 1)], [(0.7, 0), (0.75, 1)]]), (160, 154, 148))]))
    # the second pair of arms: bare, tattooed, coming out below the sleeves
    for bone, x in (("rightArm2", 5.4), ("leftArm2", -9.0)):
        m.box(bone, [x, 7.5, -0.4], [3.6, 11, 3.6], layered(SKIN, [lines((SIDES, [[(0, 0.8), (1, 0.8)], [(0, 0.86), (1, 0.86)], [(0, 0.15), (1, 0.15)]]), tat)]))
        m.box(bone, [x - 0.4, 15.5, -0.8], [4.4, 3.5, 4.4], solid(robe))


# ---------------------------------------------------------------- Luffy gears
HAKI = (22, 18, 24)


def haki_flames(face, px, w, h, base):
    if face not in SIDES:
        return
    for c in range(2, w, 6):
        for y in range(int(h * 0.1), h - 1):
            x = int(c + math.sin(y * 0.3 + c * 0.7) * 1.8)
            _put(px, w, h, x, y, (196, 34, 28))
            if y % 9 < 3:
                _put(px, w, h, x + 1, y, (240, 110, 40))


def haki():
    return layered(HAKI, [haki_flames])


def steam_puffs(m, ring_y, rx, rz, n=9, size=3.2, bone="body"):
    for k in range(n):
        a = k * 2 * math.pi / n
        s = size * (0.85 + 0.3 * ((k * 37) % 5) / 5)
        m.box(bone, [math.cos(a) * rx - s / 2, ring_y + (k % 3) * 0.4, math.sin(a) * rz - s / 2], [s, s * 0.8, s], solid((250, 250, 252)))


def luffy_gear_head(m, hair, face, iris=(40, 30, 30)):
    m.box("head", [-4, 24, -4], [8, 8, 8], head_paint(hair, iris, True, face))
    ears(m)


def luffy_body(m, form):  # noqa: F811
    if form in ("base", "g2", "g3", "g5"):
        _luffy_body_v2(m, form)
        if form == "g2":  # steam rising off pink skin
            steam_puffs(m, 22.5, 5.2, 3.2, n=7, size=2.4)
            m.box("rightArm", [5.5, 14, -1.2], [2.2, 2, 2.2], solid((250, 246, 248)))
            m.box("leftArm", [-7.7, 16, 0.2], [2.2, 2, 2.2], solid((250, 246, 248)))
        if form == "g3":  # Bone Balloon: the right arm is inflated into a giant haki fist
            m.cubes = [c for c in m.cubes if c["bone"] != "rightArm"]
            m.box("rightArm", [3.6, 16, -2.6], [5.2, 8, 5.2], solid(SKIN))
            m.box("rightArm", [3.75, 19.5, -2.8], [5, 4.75, 5.6], solid(VEST))
            m.box("rightArm", [2.2, 5, -4.2], [8.5, 11.5, 8.5], haki())
            m.box("rightArm", [1.6, 1, -4.8], [9.7, 5.5, 9.7], layered(HAKI, [lines((("north", "east", "west"), [[(0.25, 0.3), (0.25, 0.7)], [(0.5, 0.3), (0.5, 0.7)], [(0.75, 0.3), (0.75, 0.7)]]), (70, 64, 80))]))
        return
    face = "luffy_g4"
    hair = (22, 20, 26)
    luffy_gear_head(m, hair, face)
    skin_t = (238, 132, 118)
    if form == "g4b":  # Boundman: giant haki-coated upper body, huge forearms, cloud scarf
        m.box("body", [-6.5, 17, -4], [13, 7.5, 8], haki())                          # broad haki chest
        m.box("body", [-4.5, 12, -2.6], [9, 5.5, 5.2], layered(skin_t, [x_scar]))     # skin abdomen
        for sx in (1, -1):  # round shoulders
            x = 5.2 if sx == 1 else -11.2
            m.box("body", [x, 18, -3.2], [6, 6, 6.4], haki())
            m.box("body", [x, 18, -3.2], [6, 6, 6.4], haki(), rot=[0, 0, 45], pivot=[x + 3, 21, 0])
        both_arms(m, [5.2, 13, -2.8], [5.5, 6, 5.6], haki())                          # upper arm
        both_arms(m, [4.6, 4, -3.8], [7.6, 9.5, 7.6], haki())                         # massive forearm + fist
        m.box("body", [-5, 10.5, -3], [10, 2, 6], solid(SASH))
        both_legs(m, [-0.5, 6, -2.6], [5, 6, 5.2], solid(SHORTS))
        both_legs(m, [-0.7, 0, -2.8], [5.4, 6.5, 5.6], haki())
        steam_puffs(m, 23.2, 7.2, 4.6, n=11, size=3.4)
        return
    if form == "g4s":  # Snakeman: lean, long haki arms, a long steam cape
        m.box("body", [-4.2, 12, -2.2], [8.4, 12, 4.4], layered(skin_t, [x_scar, torso_flames]))
        m.box("body", [-5.2, 19.5, -2.8], [10.4, 4.5, 5.6], haki())                  # haki across the shoulders
        both_arms(m, [4, 9, -2], [3.8, 15, 4], haki())
        m.box("body", [-4.6, 10.5, -2.6], [9.2, 1.8, 5.2], solid(SASH))
        both_legs(m, [-0.3, 5, -2.3], [4.6, 7, 4.6], solid(SHORTS))
        both_legs(m, [-0.2, 0, -2.2], [4.4, 5.5, 4.4], haki())
        steam_puffs(m, 23, 5.4, 3.4, n=8, size=2.8)
        for k, x in enumerate((-3, 0, 3)):
            m.strand([x, 24, 3], [x * 0.06, -1, 0.22], 18 - abs(x), 4.2, solid((248, 248, 250)), bone="body", thick=0.35)
        return
    # Tankman: a huge round rubber belly
    m.box("body", [-8, 8, -7], [16, 15, 14], layered(skin_t, [x_scar]))
    m.box("body", [-8, 8, -7], [16, 15, 14], layered(skin_t, []), rot=[0, 45, 0], pivot=[0, 15.5, 0])
    m.box("body", [-6.5, 20, -5], [13, 4.5, 10], haki())
    both_arms(m, [6.5, 12, -2.6], [5, 10, 5.2], haki())
    m.box("body", [-6, 6.5, -5], [12, 2, 10], solid(SASH))
    both_legs(m, [-0.6, 0, -2.6], [5.2, 7, 5.2], haki())
    steam_puffs(m, 23, 5.8, 4.2, n=9, size=3)


def luffy_hair(m, c, g5=False, form="base"):  # noqa: F811
    hp = hair_paint(c)
    if g5:  # Nika: white hair billowing upward like clouds of flame
        for x, z, L in ((-2.6, -2.2, 7.5), (0, -2.6, 8.5), (2.6, -2.2, 7.5), (-3.6, 0.6, 7), (3.6, 0.6, 7),
                        (-1.8, 2.6, 7.5), (1.8, 2.6, 7.5), (0, 0.4, 9)):
            m.strand([x, 31.8, z], [x * 0.2, 1, z * 0.12 + 0.2], L, 4.8, hp, bend=(x * 0.05, -0.05, 0.14))
        m.mirror_strand([4.3, 30, -1], [0.8, 0.6, 0], 5.5, 3.6, hp, bend=(0, 0.12, 0))
        return
    if form.startswith("g4"):  # hair blown up and back by the haki
        for x, z in ((-2.4, -1.8), (0, -2.2), (2.4, -1.8), (-3.3, 0.8), (3.3, 0.8), (-1.2, 1.8), (1.2, 1.8)):
            m.strand([x, 31.8, z], [x * 0.18, 1, 0.7], 6.5 if form == "g4s" else 5.5, 3.6, hp, bend=(0, -0.15, 0.15))
        m.strand([0.2, 31.6, -4.2], [0.1, -1, -0.8], 2.6, 2.6, hp)
        return
    _luffy_hair_prev(m, c, False, form)


_luffy_hair_prev = _luffy_hair_prev_impl


_build_v3 = build


def build(char, form):  # noqa: F811
    if char == "sukuna" and form == "yuji":
        m = Model()
        yuji_body(m, "sukuna")
        sukuna_yuji_hair(m, (226, 140, 150))
        return m
    return _build_v3(char, form)


# ==================================================================================
# LUFFY — rebuilt from the official reference art (One Piece Wiki):
#  base: open red shirt with rolled sleeves, X scar, long yellow sash tail, blue shorts with
#        white fuzzy cuffs, sandals, straw hat
#  Gear 2: red-pink skin wrapped in big steam clouds
#  Gear 3: one gigantic inflated fist
#  Gear 4: haki = black with glowing red contour lines; Boundman (huge chest + colossal fists,
#        hat on the back), Snakeman (lean, long wild hair, open black vest, red pants with fur
#        cuffs), Tankman (giant black haki ball body)
# ==================================================================================
HAKI_BLACK = (20, 10, 16)
HAKI_RED = (226, 44, 74)
FUR = (246, 244, 240)
CLOUD = (250, 250, 255)


def haki_glow(face, img):
    """Armament haki: near-black with glowing red contours and a soft pink shine."""
    w, h = img.size
    px = img.load()
    t = tones(HAKI_BLACK)
    for y in range(h):
        for x in range(w):
            k = 2 if face in ("north", "west", "up") else 1
            c = t[k]
            edge = x == 0 or x == w - 1 or y == 0 or y == h - 1
            inner = x == 1 or x == w - 2 or y == 1 or y == h - 2
            if face != "down":
                if edge:
                    c = HAKI_RED
                elif inner and w > 4 and h > 4:
                    c = (120, 18, 40)
            px[x, y] = c + (255,)
    if face in ("north", "west", "east", "south") and w >= 8 and h >= 8:
        for y in range(2, h - 2):  # one muscle contour line
            x = int(w * 0.55 + math.sin(y / h * math.pi * 1.5) * w * 0.15)
            px[x, y] = HAKI_RED + (255,)
        for dx in range(2):
            for dy in range(2):
                px[2 + dx, 2 + dy] = (240, 150, 170, 255)  # shine


def fur_cuff(face, img):
    w, h = img.size
    px = img.load()
    t = tones(FUR)
    for y in range(h):
        for x in range(w):
            k = 2 if face in ("north", "west", "up") else 1
            if y == h - 1 and x % 2 == 0:
                k = 0
            if y == 0 and x % 3 == 1:
                k = 3
            px[x, y] = t[k] + (255,)


def cloud(m, bone, c, s):
    """A puffy steam cloud: three overlapping, rotated soft cubes."""
    x, y, z = c
    p = solid(CLOUD)
    m.box(bone, [x - s / 2, y - s / 2, z - s / 2], [s, s * 0.8, s], p)
    m.box(bone, [x - s * 0.45, y - s * 0.35, z - s * 0.45], [s * 0.9, s * 0.7, s * 0.9], p, rot=[0, 45, 0], pivot=[x, y, z])
    m.box(bone, [x + s * 0.2 - s * 0.3, y + s * 0.15 - s * 0.3, z - s * 0.3], [s * 0.6, s * 0.6, s * 0.6], p, rot=[45, 0, 45], pivot=[x + s * 0.2, y + s * 0.15, z])


def abs_chest(face, px, w, h, base):
    """Bare muscular chest: pecs, abs and the X scar."""
    if face != "north":
        return
    t = tones(base)
    cx = w // 2
    for x in range(2, w - 2):
        _put(px, w, h, x, int(h * 0.36), t[1])  # under the pecs
    for y in range(int(h * 0.4), h - 2):
        _put(px, w, h, cx, y, t[1])            # centre line
    for row in (0.52, 0.66, 0.8):
        for x in range(cx - 4, cx + 5):
            _put(px, w, h, x, int(h * row), t[1])
    for d in range(-5, 6):                     # X scar
        _put(px, w, h, cx + d, int(h * 0.2) + d, (176, 96, 84))
        _put(px, w, h, cx + d, int(h * 0.2) - d, (176, 96, 84))


def luffy_head(m, hair, face_style, iris=(30, 24, 26)):
    m.box("head", [-4, 24, -4], [8, 8, 8], head_paint(hair, iris, True, face_style))
    ears(m)


def luffy_shirt_and_shorts(m, skin, shirt=VEST, shorts=SHORTS, sash=SASH, sleeves=True, fur=True):
    # bare torso, open shirt panels at the sides of the chest, red back
    m.box("body", [-4, 12, -2], [8, 12, 4], layered(skin, [abs_chest]))
    for x0 in (-4.3, 1.75):
        m.box("body", [x0, 12.5, -2.35], [2.55, 11.75, 0.6], layered(shirt, [lines((("north",), [[(0.9 if x0 < 0 else 0.1, 0), (0.9 if x0 < 0 else 0.1, 1)]]), dark(shirt, 0.55))]))
    m.box("body", [-4.3, 12.5, -2.3], [8.6, 11.75, 4.6], layered(shirt, [lambda f, px, w, h, b: [px.__setitem__((x, y), (0, 0, 0, 0)) for y in range(h) for x in range(w)] if f == "north" else None]))
    m.box("body", [-4.4, 22.8, -2.5], [8.8, 1.4, 5], solid(dark(shirt, 0.85)))  # collar
    if sleeves:  # sleeves rolled up to the forearm, with a thick cuff
        both_arms(m, [3.75, 16, -2.3], [3.5, 8.3, 4.6], solid(shirt))
        both_arms(m, [3.6, 15, -2.45], [3.8, 1.6, 4.9], solid(dark(shirt, 0.8)))
    m.box("body", [-4.6, 10.8, -2.6], [9.2, 1.9, 5.2], layered(sash, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), dark(sash, 0.7))]))
    m.strand([-3.9, 11, -1.8], [-0.15, -1, -0.15], 9, 2.2, layered(sash, [lines((SIDES, [[(0.5, 0), (0.5, 1)]]), dark(sash, 0.75))]), bone="body", segs=3, thick=0.25)
    both_legs(m, [-0.4, 4.5, -2.4], [4.6, 7.5, 4.8], layered(shorts, [lines((SIDES, [[(0.35, 0), (0.3, 1)]]), dark(shorts, 0.72))]))
    if fur:
        both_legs(m, [-0.7, 3.5, -2.7], [5.2, 1.6, 5.4], fur_cuff)
    both_legs(m, [-0.3, 0, -2.6], [4.4, 0.6, 5], solid((150, 96, 52)))
    both_legs(m, [0.3, 0.6, -2.62], [3.2, 0.8, 0.3], solid((120, 72, 40)))


def luffy_slim_limbs(m, skin):
    m.box("rightArm", [4, 12, -2], [3, 12, 4], solid(skin))
    m.box("leftArm", [-7, 12, -2], [3, 12, 4], solid(skin))
    m.box("rightLeg", [-0.1, 0, -2], [4, 12, 4], solid(skin))
    m.box("leftLeg", [-3.9, 0, -2], [4, 12, 4], solid(skin))


def hat_on_back(m):
    weave = layered(STRAW, [lines((SIDES + ("up",), [[(0, 0.33), (1, 0.33)], [(0, 0.66), (1, 0.66)]]), dark(STRAW, 0.75))])
    for rz in (0, 45):
        m.box("body", [-7, 9.5, 2.6], [14, 14, 0.5], weave, rot=[0, 0, rz], pivot=[0, 16.5, 2.85])
    m.box("body", [-3.6, 12.9, 3.1], [7.2, 7.2, 2.6], weave)
    m.box("body", [-3.7, 12.9, 3.0], [7.4, 1.1, 2.8], solid((200, 30, 34)))


FACE32["luffy_g4"] = dict(eye="round", brow="angled", mouth="clench", marks=["luffy_scar", "g4_marks"])
_face32_v3 = face32


def face32(px, W, H, spec, hair, iris, skin):  # noqa: F811
    marks = spec.get("marks", [])
    _face32_v3(px, W, H, dict(spec, marks=[m for m in marks if m != "g4_marks"]), hair, iris, skin)
    if "g4_marks" not in marks:
        return
    k = W / 32.0
    t = (16, 10, 14)

    def put(x, y, c):
        for dx in range(int(k)):
            for dy in range(int(k)):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    for side in (0, 1):  # haki marks flaring out from the eyes
        X = (lambda x: x) if side == 0 else (lambda x: 31 - x)
        for i, (x, y) in enumerate(((5, 15), (4, 14), (3, 13), (2, 13), (6, 22), (5, 23), (4, 24))):
            put(X(x), y, t)
        put(X(14), 13, t); put(X(13), 12, t)


def luffy_body(m, form):  # noqa: F811
    skin = SKIN
    if form in ("base", "g2", "g3"):
        if form == "g2":
            skin = (236, 124, 120)
        luffy_head(m, (22, 20, 26), "luffy_fight" if form != "base" else "luffy")
        luffy_slim_limbs(m, skin)
        luffy_shirt_and_shorts(m, skin)
        hat(m)
        if form == "g2":  # big steam clouds rolling off his body
            for c, s in (((5.5, 22, 0), 3.4), ((-5.5, 22.5, 0.5), 3.2), ((0, 23, 3.6), 3.6), ((3, 15, 3.2), 2.8), ((-3.2, 13, 3), 2.6),
                         ((6.6, 13, -0.5), 2.4), ((-6.8, 15, 0.5), 2.4), ((2.4, 2, -3.4), 2.2), ((-2.6, 3, 3.2), 2.4)):
                cloud(m, "body" if c[1] > 10 else "root", c, s)
        if form == "g3":  # Bone Balloon: one gigantic fist
            m.cubes = [c for c in m.cubes if c["bone"] != "rightArm"]
            m.box("rightArm", [3.6, 13, -2.6], [5, 11, 5.2], solid(skin))
            m.box("rightArm", [3.6, 16, -2.45], [5.2, 8.3, 5.1], solid(VEST))
            fist = layered(skin, [lines((("north", "east", "west"), [[(0.25, 0.25), (0.25, 0.55)], [(0.5, 0.25), (0.5, 0.55)], [(0.75, 0.25), (0.75, 0.55)], [(0.08, 0.6), (0.92, 0.6)]]), (186, 120, 96))])
            m.box("rightArm", [1, -1, -5.5], [10.5, 14, 11], fist)
            m.box("rightArm", [0.4, 5, -6.2], [3, 6, 4], solid(skin))  # thumb
        return
    hair = (22, 20, 26)
    luffy_head(m, hair, "luffy_g4")
    if form == "g4b":  # BOUNDMAN
        m.box("body", [-6.5, 15, -4], [13, 9.5, 8], layered(skin, [abs_chest]))
        m.box("body", [-4.6, 11, -2.8], [9.2, 4.2, 5.6], layered(skin, [abs_chest]))
        for x0 in (-7, 3.5):  # haki creeping over the shoulders
            m.box("body", [x0, 18, -4.3], [3.5, 6.5, 8.6], haki_glow)
        m.box("body", [-6.6, 23, -4.2], [13.2, 1.5, 8.4], solid((120, 24, 34)))  # torn shirt collar
        both_arms(m, [5.4, 15, -3.2], [5.6, 8, 6.4], haki_glow)          # upper arm
        both_arms(m, [4.6, 2, -4.8], [8.2, 13, 9.6], haki_glow)          # colossal forearm + fist
        m.box("body", [-5, 10, -3.2], [10, 2.2, 6.4], solid(SASH))
        m.strand([-4.2, 10.3, -2.6], [-0.2, -1, -0.1], 7, 2, solid(SASH), bone="body", segs=3, thick=0.25)
        both_legs(m, [-0.6, 5.5, -2.7], [5.2, 6.5, 5.4], solid(SHORTS))
        both_legs(m, [-0.9, 4.4, -3], [5.8, 1.8, 6], fur_cuff)
        both_legs(m, [-0.4, 0, -2.5], [4.8, 4.8, 5], haki_glow)
        hat_on_back(m)
        for c, s in (((7.5, 25, 1), 4.2), ((-7.5, 25, 1), 4.2), ((0, 26, 4.5), 4.6), ((4, 27, 3.5), 3.6), ((-4, 27, 3.5), 3.6),
                     ((9, 21, 3), 3.2), ((-9, 21, 3), 3.2), ((0, 20, 6.5), 3.6)):
            cloud(m, "body", c, s)
        return
    if form == "g4s":  # SNAKEMAN
        m.box("body", [-4, 12, -2], [8, 12, 4], layered(skin, [abs_chest]))
        vest = (24, 22, 30)
        for x0 in (-4.3, 1.9):
            m.box("body", [x0, 12.5, -2.35], [2.4, 11.75, 0.6], solid(vest))
        m.box("body", [-4.3, 12.5, -2.3], [8.6, 11.75, 4.6], layered(vest, [lambda f, px, w, h, b: [px.__setitem__((x, y), (0, 0, 0, 0)) for y in range(h) for x in range(w)] if f == "north" else None]))
        both_arms(m, [4, 9, -2], [3.6, 15, 4], haki_glow)
        m.box("body", [-4.6, 10.8, -2.6], [9.2, 1.9, 5.2], solid(SASH))
        pants = (198, 40, 44)
        both_legs(m, [-0.4, 4, -2.4], [4.6, 8, 4.8], layered(pants, [lines((SIDES, [[(0.35, 0), (0.3, 1)]]), dark(pants, 0.7))]))
        both_legs(m, [-0.7, 3, -2.7], [5.2, 1.6, 5.4], fur_cuff)
        both_legs(m, [-0.3, 0, -2.3], [4.6, 3.6, 4.6], haki_glow)
        for c, s in (((5, 24, 1), 3.4), ((-5, 24, 1), 3.4), ((0, 24.5, 3.4), 3.6), ((6.5, 20, 2.5), 2.6), ((-6.5, 20, 2.5), 2.6)):
            cloud(m, "body", c, s)
        return
    # TANKMAN
    for rot in ([0, 0, 0], [0, 45, 0], [45, 0, 0], [0, 0, 45]):
        m.box("body", [-9, 4, -9], [18, 18, 18], haki_glow, rot=rot, pivot=[0, 13, 0])
    m.box("body", [-5.5, 20, -4.5], [11, 4.5, 8], layered(skin, [abs_chest]))
    both_arms(m, [7.5, 14, -2.8], [5, 9, 5.6], haki_glow)
    both_legs(m, [-0.6, 0, -2.6], [5, 4, 5.2], haki_glow)
    for c, s in (((7, 25, 0), 3.2), ((-7, 25, 0), 3.2), ((0, 25.5, 3.5), 3.4)):
        cloud(m, "body", c, s)


def luffy_hair(m, c, g5=False, form="base"):  # noqa: F811
    hp = hair_paint(c)
    if g5:
        return _luffy_hair_g5(m, c)
    if form.startswith("g4"):  # wild spiky hair swept up and back (longer in Snakeman)
        L = 7.5 if form == "g4s" else 6
        for x, z in ((-2.6, -1.8), (-0.9, -2.3), (0.9, -2.3), (2.6, -1.8), (-3.4, 0.6), (3.4, 0.6), (-1.6, 2), (1.6, 2)):
            m.strand([x, 31.8, z], [x * 0.2, 0.9, 0.75], L, 3.4, hp, bend=(0, -0.2, 0.12))
        if form == "g4s":
            for x in (-2.6, 0, 2.6):
                m.strand([x, 30.5, 4], [x * 0.1, -0.5, 1], 8, 3.4, hp, bend=(0, -0.1, 0))
        m.strand([-1.6, 31.7, -4.1], [-0.2, -1, -0.8], 2.8, 2.6, hp)
        m.strand([1.6, 31.7, -4.1], [0.2, -1, -0.8], 2.8, 2.6, hp)
        return
    _luffy_hair_prev(m, c, False, form)


def _luffy_hair_g5(m, c):
    hp = hair_paint(c)
    for x, z, L in ((-2.6, -2.2, 7.5), (0, -2.6, 8.5), (2.6, -2.2, 7.5), (-3.6, 0.6, 7), (3.6, 0.6, 7),
                    (-1.8, 2.6, 7.5), (1.8, 2.6, 7.5), (0, 0.4, 9)):
        m.strand([x, 31.8, z], [x * 0.2, 1, z * 0.12 + 0.2], L, 4.8, hp, bend=(x * 0.05, -0.05, 0.14))
    m.mirror_strand([4.3, 30, -1], [0.8, 0.6, 0], 5.5, 3.6, hp, bend=(0, 0.12, 0))


_build_v4 = build


def build(char, form):  # noqa: F811
    if char == "luffy" and form != "g5":
        m = Model()
        luffy_body(m, form)
        shell(m, (22, 20, 26), hairline=29.4)
        luffy_hair(m, (22, 20, 26), False, form)
        return m
    return _build_v4(char, form)


def cloud_paint(face, img):
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = (252, 252, 255) if face in ("up", "north", "west") else (238, 238, 248)
            if face not in ("up", "down") and y >= h - max(1, h // 5):
                c = (222, 220, 238)
            if face == "down":
                c = (214, 212, 232)
            px[x, y] = c + (255,)


def cloud(m, bone, c, s):  # noqa: F811 — soft round puff (octagonal), no hard edges
    x, y, z = c
    m.box(bone, [x - s / 2, y - s * 0.35, z - s / 2], [s, s * 0.7, s], cloud_paint)
    m.box(bone, [x - s / 2, y - s * 0.35, z - s / 2], [s, s * 0.7, s], cloud_paint, rot=[0, 45, 0], pivot=[x, y, z])
    m.box(bone, [x - s * 0.32, y - s * 0.1, z - s * 0.32], [s * 0.64, s * 0.75, s * 0.64], cloud_paint)


def steam_wreath(m, y, rx, rz, n, s, bone="body", back=0.0):
    for k in range(n):
        a = k * 2 * math.pi / n
        cloud(m, bone, (math.cos(a) * rx, y + (k % 2) * 0.8, math.sin(a) * rz + back), s * (0.85 + 0.3 * (k % 3) / 2))


def haki_ball(m, cy, R):
    """Tankman's round haki belly: stacked octagonal slices."""
    n = 7
    for i in range(n):
        yy = -R + (i + 0.5) * (2 * R / n)
        r = math.sqrt(max(0.5, R * R - yy * yy))
        top = cy + yy - R / n
        for rot in ([0, 0, 0], [0, 45, 0]):
            m.box("body", [-r, top, -r], [2 * r, 2 * R / n + 0.6, 2 * r], haki_glow, rot=rot, pivot=[0, cy, 0])


_luffy_body_v5 = luffy_body


def luffy_body(m, form):  # noqa: F811
    if form == "g5":
        return _luffy_body_v2(m, "g5")
    if form == "g4t":
        luffy_head(m, (22, 20, 26), "luffy_g4")
        haki_ball(m, 12.5, 9.5)
        m.box("body", [-5.5, 20.5, -4.5], [11, 4, 8], layered(SKIN, [abs_chest]))
        both_arms(m, [7, 15, -2.8], [5, 8, 5.6], haki_glow)
        both_legs(m, [-0.6, 0, -2.6], [5, 3.5, 5.2], haki_glow)
        steam_wreath(m, 22.8, 6.8, 4.8, 8, 4.0)
        return
    _luffy_body_v5(m, form)
    # replace the scattered small clouds with big steam wreaths
    m.cubes = [c for c in m.cubes if c["paint"] is not cloud_paint]
    if form == "g2":
        steam_wreath(m, 22.5, 6, 4, 8, 4.4)
        steam_wreath(m, 13, 6.5, 4.5, 6, 3.6, back=1)
        steam_wreath(m, 2, 5, 4, 5, 3.4, bone="root")
    elif form == "g4b":
        steam_wreath(m, 22.6, 9, 5.8, 10, 5.0)
        steam_wreath(m, 19, 10, 6, 6, 4.4, back=2.5)
    elif form == "g4s":
        steam_wreath(m, 22.4, 6.4, 4.2, 8, 4.0)


# ==================================================================================
# ITADORI YUJI — MODULO (2086), from the JJK wiki + Modulo chapter art:
# silver reflective hooded jacket, hood up (face hidden), cap under the hood, face mask,
# same scars, longer relaxed hair, black trousers.
# ==================================================================================
SILVER = (198, 202, 214)

FACE32["yuji_modulo"] = dict(eye="anime", brow="flat", mouth="none", marks=["yuji", "scars", "hood_shadow", "mask"])
_face32_v4 = face32


def face32(px, W, H, spec, hair, iris, skin):  # noqa: F811
    marks = spec.get("marks", [])
    _face32_v4(px, W, H, dict(spec, marks=[m for m in marks if m not in ("hood_shadow", "mask")]), hair, iris, skin)
    k = W / 32.0

    def put(x, y, c):
        for dx in range(int(k)):
            for dy in range(int(k)):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    if "hood_shadow" in marks:  # the hood and cap throw the upper face into darkness
        for y in range(0, 21):
            for x in range(32):
                xx, yy = int(x * k), int(y * k)
                r, g, b, a = px[xx, yy]
                put(x, y, (int(r * 0.22), int(g * 0.2), int(b * 0.24)))
        for x in (20, 21):  # a single eye glinting out of the shadow
            put(x, 18, (230, 230, 236))
        put(21, 17, (150, 110, 80))
    if "mask" in marks:
        for y in range(21, 32):
            for x in range(2, 30):
                put(x, y, (26, 26, 32) if (x + y) % 9 else (40, 40, 48))
        for x in range(4, 28):
            put(x, 21, (54, 54, 64))


def silver_jacket(face, px, w, h, base):
    t = tones(SILVER)
    for y in range(h):  # reflective sheen bands
        for x in range(w):
            if (x + y) % 11 in (0, 1) and face in ("north", "west"):
                _put(px, w, h, x, y, t[4])
    if face == "north":
        for y in range(h):
            _put(px, w, h, w // 2, y, (90, 92, 104))       # zipper
        for y in (2, 3):
            _put(px, w, h, w // 2 - 3, y + 4, (240, 240, 244)); _put(px, w, h, w // 2 + 2, y + 4, (240, 240, 244))


def hood_paint(face, img):
    """Raised hood: open at the front where the face is."""
    w, h = img.size
    px = img.load()
    t = tones(SILVER)
    for y in range(h):
        for x in range(w):
            k = {"up": 3, "north": 2, "west": 2, "east": 1, "south": 1, "down": 0}[face]
            if (x + y) % 13 == 0 and face in ("north", "west", "up"):
                k = 4
            px[x, y] = t[k] + (255,)
    if face == "north":  # opening
        for y in range(int(h * 0.12), h):
            for x in range(int(w * 0.12), int(w * 0.88)):
                px[x, y] = (0, 0, 0, 0)
        for x in range(int(w * 0.1), int(w * 0.9)):
            px[x, int(h * 0.1)] = t[0] + (255,)
    if face == "down":
        for y in range(h):
            for x in range(w):
                px[x, y] = (0, 0, 0, 0)


def yuji_modulo(m):
    hand = layered(SILVER, [silver_jacket, band(SIDES + ("down",), 0.9, 1.0, "skin")])
    base_body(m, layered(SILVER, [silver_jacket]), hand, solid((24, 24, 30)),
              head_paint((226, 150, 152), (120, 70, 40), True, "yuji_modulo"))
    m.box("body", [-4.4, 9.5, -2.4], [8.8, 14.5, 4.8], layered(SILVER, [silver_jacket]))  # long parka
    both_arms(m, [3.8, 13.5, -2.3], [4.4, 10.5, 4.6], layered(SILVER, [silver_jacket]))
    both_arms(m, [3.7, 12.6, -2.4], [4.6, 1.2, 4.8], solid((150, 154, 166)))          # cuffs
    both_legs(m, [-0.3, 0, -2.6], [4.4, 1.6, 5], solid((16, 16, 20)))                  # black shoes
    # hood up, cap visor peeking out, drawstrings
    m.box("head", [-4, 24, -4], [8, 8, 8], hood_paint, inflate=0.7)
    m.box("head", [-4.5, 31.2, -1], [9, 1.6, 5.8], hood_paint)                         # hood peak
    m.box("head", [-3.2, 29.6, -6.6], [6.4, 0.6, 2.8], solid((22, 22, 28)))           # cap visor
    m.box("head", [-3.6, 29.6, -4.6], [7.2, 2.6, 1.2], solid((22, 22, 28)))           # cap front
    for x in (-1.6, 1.4):
        m.strand([x, 24.2, -4.9], [0, -1, -0.1], 3.2, 0.5, solid((236, 236, 240)), bone="body", segs=2)
    hp = hair_paint((226, 150, 152))  # longer, relaxed hair peeking out under the hood
    for x in (-2.6, 2.4):
        m.strand([x, 29.8, -4.3], [x * 0.05, -1, -0.4], 2.4, 2.2, hp)


_build_v5 = build


def build(char, form):  # noqa: F811
    if char == "yuji_final":
        m = Model()
        yuji_modulo(m)
        return m
    return _build_v5(char, form)


_yuji_modulo_v1 = yuji_modulo


def yuji_modulo(m):  # noqa: F811
    _yuji_modulo_v1(m)
    drop = {id(c) for c in m.cubes if (c["bone"] == "head" and c["size"] == [0.75, 2.25, 1.5]) or (c["bone"] == "hair")}
    m.cubes = [c for c in m.cubes if id(c) not in drop]


# ==================================================================================
# REFERENCE PASS (wiki infobox art): Modulo black jacket, smooth Tankman, Itadori red shoes
# + zipper + high collar, Goku front belt knot, Sukuna thick tattoo bands.
# ==================================================================================
SILVER = (34, 34, 42)  # Modulo jacket: black (as requested)


def silver_jacket(face, px, w, h, base):  # noqa: F811 — black parka: subtle sheen, zipper, toggles
    t = tones(SILVER)
    if face in ("north", "west"):
        for y in range(h):
            for x in range(w):
                if (x + y) % 13 == 0:
                    _put(px, w, h, x, y, t[3])
    if face == "north":
        for y in range(h):
            _put(px, w, h, w // 2, y, (120, 122, 134))
        for y in (2, 3):
            _put(px, w, h, w // 2 - 3, y + 4, (220, 220, 228)); _put(px, w, h, w // 2 + 2, y + 4, (220, 220, 228))


def haki_ball(m, cy, R):  # noqa: F811 — smooth sphere: 11 slices x 3 rotations (12-sided)
    n = 11
    for i in range(n):
        yy = -R + (i + 0.5) * (2 * R / n)
        r = math.sqrt(max(0.3, R * R - yy * yy)) * 0.93
        top = cy + yy - R / n
        for rot in ([0, 0, 0], [0, 30, 0], [0, 60, 0]):
            m.box("body", [-r, top, -r], [2 * r, 2 * R / n + 0.35, 2 * r], haki_glow, rot=rot, pivot=[0, cy, 0])


def round_limb(m, bone, frm, size, paint):
    """A limb with softened corners: the box plus a 45°-turned copy slightly inset."""
    m.box(bone, frm, size, paint)
    x, y, z = frm
    w, h, d = size
    m.box(bone, [x + w * 0.08, y, z + d * 0.08], [w * 0.84, h, d * 0.84], paint, rot=[0, 45, 0], pivot=[x + w / 2, y, z + d / 2])


_luffy_body_v6 = luffy_body


def luffy_body(m, form):  # noqa: F811
    if form != "g4t":
        return _luffy_body_v6(m, form)
    luffy_head(m, (22, 20, 26), "luffy_g4")
    haki_ball(m, 12.5, 10)
    # upper torso rising out of the ball, rounded
    for rot in ([0, 0, 0], [0, 45, 0]):
        m.box("body", [-4.6, 19.5, -3.6], [9.2, 5, 7.2], layered(SKIN, [abs_chest]), rot=rot, pivot=[0, 19.5, 0])
    for bone, x0 in (("rightArm", 7.2), ("leftArm", -12.2)):
        round_limb(m, bone, [x0, 15, -2.6], [5, 8, 5.2], haki_glow)
    for bone, x0 in (("rightLeg", -0.6), ("leftLeg", -4.4)):
        round_limb(m, bone, [x0, 0, -2.6], [5, 3.5, 5.2], haki_glow)
    steam_wreath(m, 22.8, 6.8, 4.8, 8, 4.0)


# ---------------------------------------------------------------- Itadori uniform details
_yuji_body_ref = yuji_body


def yuji_body(m, style, iris=(120, 70, 40)):  # noqa: F811
    _yuji_body_ref(m, style, iris)
    # red sneakers (anime colour) instead of white ones
    m.cubes = [c for c in m.cubes if not (c["bone"] in ("rightLeg", "leftLeg") and c["frm"][1] == 0 and c["size"][1] == 1.75)]
    shoe = layered((196, 30, 36), [band(SIDES, 0.0, 0.25, "skin")])
    both_legs(m, [-0.35, 0, -2.7], [4.5, 1.9, 5.2], layered((196, 30, 36), [lines((SIDES, [[(0, 0.15), (1, 0.15)]]), (240, 236, 230))]))
    both_legs(m, [-0.5, 1.9, -2.6], [4.8, 1.0, 5], solid((26, 28, 44)))  # trouser cuffs
    # high collar with the red hood lining showing, and a zipper
    m.box("body", [-3.6, 23.2, -2.7], [7.2, 2.6, 5.4], layered((30, 32, 50), [lines((("north",), [[(0.5, 0), (0.5, 1)]]), (140, 142, 160))]))
    m.box("body", [-3.1, 25.4, -2.1], [6.2, 0.4, 4.2], solid(HOOD_RED))


# ---------------------------------------------------------------- Goku: belt knot in front
_goku_body_ref = goku_body


def goku_body(m, hair, iris, brows=True, style="goku"):  # noqa: F811
    _goku_body_ref(m, hair, iris, brows, style)
    m.box("body", [-2.6, 11.4, -3.2], [2.6, 2.4, 1.2], solid(GI_BLUE))
    m.strand([-2.2, 11.6, -3.1], [-0.25, -1, -0.15], 4.2, 1.4, solid(GI_BLUE), bone="body", segs=2, thick=0.4)
    m.strand([-1.2, 11.6, -3.1], [0.1, -1, -0.15], 3.6, 1.4, solid(GI_BLUE), bone="body", segs=2, thick=0.4)


# ---------------------------------------------------------------- Sukuna Heian: thick tattoo bands
def heian_torso(face, px, w, h, base):
    tat = (36, 16, 30)
    if face == "north":
        cx = w // 2
        for side in (-1, 1):  # thick curved bands across the pecs and ribs
            for row, span in ((0.3, 0.42), (0.46, 0.38)):
                for i in range(int(w * span)):
                    x = cx + side * (2 + i)
                    y = int(h * row + (i / (w * span)) ** 2 * h * 0.08)
                    for dy in range(3):
                        _put(px, w, h, x, y + dy, tat)
        cy = int(h * 0.66)  # the abdominal mouth
        for x in range(cx - 8, cx + 9):
            _put(px, w, h, x, cy, tat); _put(px, w, h, x, cy + 6, tat)
            for yy in range(cy + 1, cy + 6):
                _put(px, w, h, x, yy, (110, 16, 26))
            if x % 2 == 0:
                _put(px, w, h, x, cy + 1, (250, 250, 250)); _put(px, w, h, x, cy + 5, (250, 250, 250))
    if face in ("east", "west", "south"):
        for y in range(int(h * 0.3), int(h * 0.3) + 3):
            for x in range(w):
                _put(px, w, h, x, y, tat)


_heian_ref = sukuna_heian_body


def sukuna_heian_body(m):  # noqa: F811
    _heian_ref(m)
    for c in m.cubes:
        if c["bone"] == "body" and c["size"] == [8, 12, 4]:
            c["paint"] = layered(SKIN, [heian_torso])
    # thick wrist/forearm bands on all four arms
    tatp = solid((36, 16, 30))
    both_arms(m, [3.85, 13.2, -2.15], [4.3, 1.2, 4.3], tatp)
    for bone, x in (("rightArm2", 5.35), ("leftArm2", -9.05)):
        m.box(bone, [x, 9.2, -0.45], [3.7, 1.2, 3.7], tatp)


def ball_slice_paint(i, n):
    """Glossy black haki sphere: no seams, a red rim light on the outer slices, a pink shine up top."""
    def p(face, img):
        w, h = img.size
        px = img.load()
        rim = i in (0, 1, n - 2, n - 1)
        for y in range(h):
            for x in range(w):
                c = (14, 6, 12) if face in ("east", "south", "down") else (24, 10, 18)
                if rim and face != "up" and face != "down":
                    c = (150, 22, 46)
                if face in ("east", "west") and (x == 0 or x == w - 1):
                    c = (190, 30, 60)
                px[x, y] = c + (255,)
        if face == "north" and i == n - 3:
            for y in range(h // 4, h // 4 + max(2, h // 2)):
                for x in range(w // 4, w // 4 + max(2, w // 8)):
                    if 0 <= x < w and 0 <= y < h:
                        px[x, y] = (236, 140, 168, 255)
    return p


def haki_ball(m, cy, R):  # noqa: F811
    n = 11
    for i in range(n):
        yy = -R + (i + 0.5) * (2 * R / n)
        r = math.sqrt(max(0.3, R * R - yy * yy)) * 0.93
        top = cy + yy - R / n
        paint = ball_slice_paint(i, n)
        for rot in ([0, 0, 0], [0, 30, 0], [0, 60, 0]):
            m.box("body", [-r, top, -r], [2 * r, 2 * R / n + 0.35, 2 * r], paint, rot=rot, pivot=[0, cy, 0])


_luffy_body_v7 = luffy_body


def luffy_body(m, form):  # noqa: F811
    if form != "g4t":
        return _luffy_body_v7(m, form)
    luffy_head(m, (22, 20, 26), "luffy_g4")
    haki_ball(m, 10.5, 9.5)
    for rot in ([0, 0, 0], [0, 45, 0]):  # bare chest rising out of the ball
        m.box("body", [-4.8, 17.5, -3.8], [9.6, 7, 7.6], layered(SKIN, [abs_chest, torso_flames]), rot=rot, pivot=[0, 17.5, 0])
    for bone, x0 in (("rightArm", 9.6), ("leftArm", -14.6)):
        round_limb(m, bone, [x0, 16, -2.6], [5, 7.5, 5.2], haki_glow)
        m.box(bone, [x0 - 4.6 if x0 > 0 else x0 + 4.6, 20, -2.2], [5, 3.6, 4.4], layered(SKIN, [torso_flames]))  # shoulder
    for bone, x0 in (("rightLeg", -0.6), ("leftLeg", -4.4)):
        round_limb(m, bone, [x0, 0, -2.6], [5, 2.5, 5.2], haki_glow)
    steam_wreath(m, 23.2, 7.2, 5, 8, 3.8)


# ==================================================================================
# SUKUNA — full redesign from the JJK wiki art (no abdominal mouth):
#  Yuji's body (anime): Yuji's uniform, red hood with gold buttons, face tattoos, pink hair swept up
#  Megumi's body (incarnated): white kimono with wide sleeves, black obi, black fluffy scarf,
#      wide white trousers, Megumi's spiky black hair
#  True form: bare upper body with thick tattoo bands, kimono tied at the waist, four arms,
#      pink spiky hair, black scarf
# ==================================================================================
KIMONO_W = (240, 234, 232)
OBI_B = (22, 20, 26)
SCARF = (30, 26, 36)
TAT = (34, 14, 28)


def kimono_front(face, px, w, h, base):
    t = tones(KIMONO_W)
    if face == "north":  # overlapping collar folds forming a V
        for y in range(h):
            x1 = int(w * 0.5 - (1 - y / h) * w * 0.28)
            x2 = int(w * 0.5 + (1 - y / h) * w * 0.28)
            if y < h * 0.45:
                _put(px, w, h, x1, y, t[0]); _put(px, w, h, x2, y, t[0])
                _put(px, w, h, x1 + 1, y, t[3])
        for x in (int(w * 0.3), int(w * 0.72)):
            for y in range(int(h * 0.5), h):
                _put(px, w, h, x, y, t[1])
    if face in ("east", "west", "south"):
        for y in range(int(h * 0.3), h, 7):
            for x in range(w):
                _put(px, w, h, x, y, t[1]) if (x + y) % 3 else None


def scarf_ring(m, y=22.0, rx=4.3, rz=3.1, n=10, s=2.3):
    p = solid(SCARF)
    for k in range(n):
        a = k * 2 * math.pi / n
        x, z = math.cos(a) * rx, math.sin(a) * rz
        m.box("body", [x - s / 2, y, z - s / 2], [s, s * 0.85, s], p)
        m.box("body", [x - s / 2, y, z - s / 2], [s, s * 0.85, s], p, rot=[0, 45, 0], pivot=[x, y, z])


def obi(m):
    band_p = layered(OBI_B, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), (64, 58, 76))])
    m.box("body", [-4.7, 10.6, -2.75], [9.4, 2.6, 5.5], band_p)
    m.box("body", [-3.2, 10.8, -3.4], [2.6, 2.2, 1], solid(OBI_B))
    m.strand([-2.6, 11, -3.3], [-0.2, -1, -0.15], 5.5, 1.8, solid(OBI_B), bone="body", segs=3, thick=0.3)
    m.strand([-1.4, 11, -3.3], [0.1, -1, -0.2], 4.5, 1.8, solid(OBI_B), bone="body", segs=3, thick=0.3)


def wide_sleeves(m):
    sleeve = layered(KIMONO_W, [lines((SIDES, [[(0, 0.96), (1, 0.96)], [(0.5, 0), (0.5, 0.9)]]), tones(KIMONO_W)[1])])
    both_arms(m, [3.3, 13.5, -3.2], [5.8, 10.8, 6.4], sleeve)
    both_arms(m, [3.6, 9.5, -2.8], [5.2, 4.2, 5.6], sleeve, rot=[8, 0, 0], pivot=[6, 13.5, 0])  # hanging drape


def hakama(m):
    pants = layered(KIMONO_W, [lines((SIDES, [[(0.3, 0), (0.25, 1)], [(0.72, 0), (0.78, 1)]]), tones(KIMONO_W)[1])])
    both_legs(m, [-0.7, 1.4, -2.9], [5.4, 9.8, 5.8], pants)
    both_legs(m, [-0.3, 0, -2.4], [4.6, 1.4, 4.8], solid((40, 34, 40)))  # ankle wraps / zori


def arm_bands(m, bone_pairs):
    p = solid(TAT)
    for bone, x, w in bone_pairs:
        for y in (12.6, 14.0):
            m.box(bone, [x, y, -2.15], [w, 0.9, 4.3], p)


def bare_tattooed_torso(face, px, w, h, base):
    t = tones(SKIN)
    cx = w // 2
    if face == "north":
        for x in range(2, w - 2):  # pec line + ab lines (muscle)
            _put(px, w, h, x, int(h * 0.36), t[1])
        for y in range(int(h * 0.4), h - 2):
            _put(px, w, h, cx, y, t[1])
        for side in (-1, 1):  # thick curved tattoo bands over the chest and ribs
            for row in (0.24, 0.5, 0.7):
                for i in range(int(w * 0.36)):
                    x = cx + side * (3 + i)
                    y = int(h * row + (i / (w * 0.36)) ** 2 * h * 0.07)
                    for dy in range(3):
                        _put(px, w, h, x, y + dy, TAT)
    else:
        for row in (0.24, 0.5):
            for x in range(w):
                for dy in range(3):
                    _put(px, w, h, x, int(h * row) + dy, TAT)


def sukuna_kimono_body(m, hair, face_style, four_arms=False, bare=False):
    if four_arms:
        m.bones = BONES_4ARMS
    arm_skin = layered(SKIN, [lines((SIDES, [[(0, 0.1), (1, 0.1)]]), TAT)])
    torso = layered(SKIN, [bare_tattooed_torso]) if bare else layered(KIMONO_W, [kimono_front])
    base_body(m, torso, arm_skin, solid(KIMONO_W), head_paint(hair, (200, 30, 40), True, face_style))
    if not bare:
        m.box("body", [-4.3, 11.5, -2.3], [8.6, 12.5, 4.6], layered(KIMONO_W, [kimono_front]))
        wide_sleeves(m)
    else:  # kimono slipped down and tied at the waist
        m.box("body", [-4.6, 9.5, -2.6], [9.2, 3.2, 5.2], layered(KIMONO_W, [kimono_front]))
        both_arms(m, [3.85, 15.5, -2.15], [4.3, 1.2, 4.3], solid(TAT))                 # upper-arm bands
    obi(m)
    hakama(m)
    scarf_ring(m)
    arm_bands(m, [("rightArm", 3.85, 4.3), ("leftArm", -8.15, 4.3)])
    if four_arms:
        for bone, x in (("rightArm2", 5.4), ("leftArm2", -9.0)):
            m.box(bone, [x, 7.5, -0.4], [3.6, 11, 3.6], layered(SKIN, []))
            for y in (9.0, 10.4, 14.5):
                m.box(bone, [x - 0.05, y, -0.45], [3.7, 0.9, 3.7], solid(TAT))


FACE32["sukuna_heian2"] = dict(eye="narrow", brow="sharp", mouth="none", marks=["sukuna_face", "heian_mask"])


def sukuna_v2(form):
    m = Model()
    if form == "yuji":
        yuji_body(m, "sukuna")
        for x in (-1.6, 1.0):  # gold buttons on the red hood collar (anime)
            m.box("body", [x, 23.9, -2.95], [0.6, 0.6, 0.3], solid((226, 180, 60)))
        sukuna_yuji_hair(m, (226, 140, 150))
    elif form == "megumi":
        sukuna_kimono_body(m, (20, 20, 28), "sukuna_megumi")
        megumi_hair(m, (20, 20, 28))
    else:
        sukuna_kimono_body(m, (226, 140, 150), "sukuna_heian2", four_arms=True, bare=True)
        heian_hair(m, (226, 140, 150))
    return m


_build_v6 = build


def build(char, form):  # noqa: F811
    if char == "sukuna":
        return sukuna_v2(form)
    if char == "luffy" and form == "g2":
        m = _build_v6(char, form)
        for c in m.cubes:
            c["paint"] = pinkify(c["paint"])
        return m
    return _build_v6(char, form)


# ---------------------------------------------------------------- Gear 2: the whole body turns pink
def pinkify(inner):
    import colorsys

    def p(face, img):
        inner(face, img)
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                # skin tones (orange-ish hue, mid saturation, bright) -> vivid pink
                if (0.02 <= hh <= 0.11) and 0.12 <= ss <= 0.6 and vv >= 0.45:
                    nr, ng, nb = colorsys.hsv_to_rgb(0.955, min(1, ss * 1.25 + 0.12), min(1, vv * 1.02))
                    px[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    return p


# ==================================================================================
# NEW: RORONOA ZORO (post-timeskip, One Piece Wiki infobox) and FRIEZA (DBS, DB Wiki)
# ==================================================================================
ZORO_COAT = (58, 92, 64)
ZORO_HARAMAKI = (120, 176, 92)
ZORO_SASH = (128, 30, 52)
ZORO_HAIR = (104, 170, 104)

FACE32["zoro"] = dict(eye="anime", brow="angled", mouth="neutral", marks=["zoro_eye"])
FACE32["zoro_king"] = dict(eye="anime", brow="sharp", mouth="clench", marks=["zoro_eye", "zoro_king"])
_face32_v5 = face32


def face32(px, W, H, spec, hair, iris, skin):  # noqa: F811
    _face32_v5(px, W, H, spec, hair, iris, skin)
    if "zoro_eye" not in spec.get("marks", []):
        return
    k = W / 32.0
    sr = ramp(skin)

    def put(x, y, c):
        for dx in range(int(k)):
            for dy in range(int(k)):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    # the left eye (viewer's right) is closed: a curved lash line with the long vertical scar through its middle
    for y in range(15, 23):
        for x in range(18, 27):
            put(x, y, sr[2])
    for x in range(19, 27):
        put(x, 19 if 20 <= x <= 25 else 18, (30, 20, 22))
    for y in range(12, 26):
        put(23, y, (176, 88, 82))
    put(22, 13, (200, 120, 110)); put(24, 24, (200, 120, 110))
    if "zoro_king" in spec.get("marks", []):  # King of Hell: shadowed brow and a glowing red eye
        for y in range(13, 16):
            for x in range(3, 14):
                put(x, y, sr[0])
        for x, y in ((8, 18), (9, 18), (8, 19), (9, 19), (8, 20), (9, 20)):
            put(x, y, (220, 30, 40))
        put(8, 18, (255, 120, 120))


def katana(m, bone, hilt, direction, length, hilt_col, blade_col=(214, 220, 232), guard_col=(206, 168, 64)):
    """A katana as a straight blade + square guard + wrapped hilt, along `direction` (BB space)."""
    hx, hy, hz = hilt
    d = norm(direction)
    ax, az = math.degrees(math.asin(clampf(d[2]))), math.degrees(math.atan2(-d[0], d[1]))
    rot = [round(ax, 2), 0, round(az, 2)]
    piv = [hx, hy, hz]
    wrap = layered(hilt_col, [lines((SIDES, [[(0, 0.2), (1, 0.4)], [(0, 0.6), (1, 0.8)]]), (236, 236, 236))])
    m.box(bone, [hx - 0.35, hy - 3.2, hz - 0.35], [0.7, 3.2, 0.7], wrap, rot=rot, pivot=piv)          # hilt (behind the hand)
    m.box(bone, [hx - 0.9, hy - 0.2, hz - 0.9], [1.8, 0.4, 1.8], solid(guard_col), rot=rot, pivot=piv)  # tsuba
    blade = layered(blade_col, [lines((SIDES, [[(0, 0.0), (0, 1)]]), (250, 250, 255))])
    m.box(bone, [hx - 0.15, hy + 0.2, hz - 0.45], [0.3, length, 0.9], blade, rot=rot, pivot=piv)


def zoro_body(m, king=False):
    coat = layered(ZORO_COAT, [lines((("north",), [[(0.5, 0.4), (0.5, 1)]]), dark(ZORO_COAT, 0.6))])
    face = "zoro_king" if king else "zoro"
    def chest(face_, px, w, h, base):
        if face_ != "north":
            return
        t = tones(SKIN)
        for x in range(2, w - 2):
            _put(px, w, h, x, int(h * 0.34), t[1])
        for i in range(int(w * 0.8)):  # the great diagonal scar
            x = int(w * 0.85) - i
            y = int(h * 0.08) + int(i * h * 0.75 / (w * 0.8))
            _put(px, w, h, x, y, (176, 104, 90))
            if i % 2 == 0:
                _put(px, w, h, x - 1, y - 1, (176, 104, 90)); _put(px, w, h, x + 1, y + 1, (176, 104, 90))
    base_body(m, layered(SKIN, [chest]), solid(ZORO_COAT), solid((26, 26, 30)),
              head_paint(ZORO_HAIR, (40, 40, 30), True, face))
    # haramaki (striped belly band) under the open coat
    m.box("body", [-4.2, 12.4, -2.2], [8.4, 4.6, 4.4], layered(ZORO_HARAMAKI, [lines((SIDES, [[(x / 8, 0), (x / 8, 1)] for x in range(1, 8)]), dark(ZORO_HARAMAKI, 0.7))]))
    # open long coat: side panels at the front, full back, skirt down to the knees
    for x0 in (-4.5, 1.6):
        m.box("body", [x0, 9.5, -2.55], [2.9, 14.7, 0.6], solid(ZORO_COAT))
    m.box("body", [-4.5, 9.5, -2.5], [9, 14.7, 5], layered(ZORO_COAT, [lambda f, px, w, h, b: [px.__setitem__((x, y), (0, 0, 0, 0)) for y in range(h) for x in range(w)] if f == "north" else None]))
    for bone, x0 in (("rightLeg", -0.6), ("leftLeg", -4.4)):
        m.box(bone, [x0, 4.5, -2.6], [5, 7.6, 5.2], layered(ZORO_COAT, [lambda f, px, w, h, b: [px.__setitem__((x, y), (0, 0, 0, 0)) for y in range(h) for x in range(w // 3, w * 2 // 3)] if f == "north" else None]))
    m.box("body", [-4.6, 22.4, -2.7], [9.2, 1.8, 5.4], solid(dark(ZORO_COAT, 0.85)))  # collar
    both_arms(m, [3.7, 12.3, -2.3], [4.6, 11.8, 4.6], coat)                         # sleeves
    # sash with the knot on his left side
    m.box("body", [-4.8, 10.6, -2.8], [9.6, 2.2, 5.6], layered(ZORO_SASH, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), dark(ZORO_SASH, 0.7))]))
    m.box("body", [-5.6, 10.2, -1.6], [1.6, 2.6, 3], solid(ZORO_SASH))
    m.strand([-5, 10.4, -0.6], [-0.2, -1, 0.05], 5, 1.8, solid(ZORO_SASH), bone="body", segs=3, thick=0.3)
    if king:  # serious: the black bandana comes off the arm and is tied over his head, shading his eyes
        band = layered((26, 26, 30), [lines((SIDES, [[(0, 0.35), (1, 0.45)], [(0, 0.75), (1, 0.7)]]), (48, 48, 56))])
        m.box("head", [-4.4, 28.75, -4.45], [8.8, 3.75, 8.85], band)
        m.box("head", [-3.9, 32.45, -3.9], [7.8, 0.35, 7.8], solid((26, 26, 30)))
        m.box("head", [-1.2, 28.9, 4.3], [2.4, 1.8, 1.0], solid((22, 22, 26)))       # knot at the back
        for sx in (-1, 1):
            m.strand([sx * 0.7, 29.6, 4.9], [sx * 0.35, -1, 0.5], 4.2, 1.5, solid((26, 26, 30)), bone="head", segs=3, thick=0.3)
    else:  # black bandana tied around the left upper arm
        m.box("leftArm", [-8.75, 19.5, -2.45], [4.9, 1.6, 4.9], solid((20, 20, 24)))
        m.strand([-8.8, 20.3, 1.8], [-0.4, -1, 0.5], 2.6, 1, solid((20, 20, 24)), bone="leftArm", segs=2, thick=0.4)
    both_legs(m, [-0.35, 0, -2.6], [4.6, 3.2, 5.1], solid((20, 18, 20)))           # boots
    # three gold earrings on the left ear
    for i in range(3):
        m.box("head", [-4.95, 26.0 + i * 0.75, -0.2], [0.35, 0.45, 0.35], solid((230, 190, 70)))
    # SANTORYU: Enma in the left hand, Sandai Kitetsu in the right, Wado Ichimonji in the mouth
    enma = dict(SWORDS["enma"], blade=(34, 26, 40), edge=(150, 40, 60)) if king else SWORDS["enma"]
    katana2(m, "leftArm", (-6, 12.2, -1.2), (0, 0.1, -1), 16, enma)
    katana2(m, "rightArm", (6, 12.2, -1.2), (0, 0.1, -1), 15, SWORDS["kitetsu"])
    katana2(m, "head", (-2.4, 25.3, -4.75), (1, 0, -0.1), 14, SWORDS["wado"], grip=0.4)
    for i, key in enumerate(("wado", "kitetsu", "enma")):  # the three empty scabbards tied at the left hip
        sheath(m, (-4.3 - i * 0.55, 13.6 - i * 0.35, -0.6 + i * 0.8), (-0.18, -0.5, 1), 14, SWORDS[key])


def zoro_hair(m, c):
    hp = hair_paint(c)
    shell(m, c, hairline=30.2, sideburn=False, teeth=0.5)
    m.box("head", [-4.25, 31.4, -4.25], [8.5, 0.9, 8.5], hp)          # short, close-cropped volume
    for x, z, dz in ((-2.6, -2.6, -0.4), (0, -3.0, -0.4), (2.6, -2.6, -0.4), (-3.2, 0.4, 0.1), (3.2, 0.4, 0.1),
                     (0, 0.2, 0.1), (-1.8, 2.6, 0.5), (1.8, 2.6, 0.5)):
        m.strand([x, 32.0, z], [x * 0.15, 1, dz], 1.4, 2.8, hp)


# ---------------------------------------------------------------- Frieza
FRIEZA_WHITE = (238, 238, 246)
FRIEZA_PURPLE = (126, 64, 190)
FRIEZA_GOLD = (236, 190, 48)


def gem(face, img):
    """Glossy purple bio-gem."""
    w, h = img.size
    px = img.load()
    t = tones(FRIEZA_PURPLE)
    for y in range(h):
        for x in range(w):
            k = 2 if face in ("north", "west", "up") else 1
            if y < h * 0.35 and x < w * 0.45 and face in ("north", "west", "up"):
                k = 4
            px[x, y] = t[k] + (255,)


def frieza_head(skin, golden):  # noqa: F811  (expressions handled in frieza_head_x)
    return frieza_head_x(skin, golden)


def _frieza_head_orig(skin, golden):
    def p(face, img):
        w, h = img.size
        px = img.load()
        pixel_mat(img, skin, face, seed=21)
        if face != "north":
            return
        k = w / 32.0

        def put(x, y, c):
            for dx in range(int(k)):
                for dy in range(int(k)):
                    xx, yy = int(x * k) + dx, int(y * k) + dy
                    if 0 <= xx < w and 0 <= yy < h:
                        px[xx, yy] = c + (255,)
        if golden:  # purple face: the gold runs down the sides like a hood and frames it
            fp = tones(FRIEZA_PURPLE)
            for y in range(11, 32):
                for x in range(5, 27):
                    top = y - 11
                    if top < 4 and (min(x - 5, 26 - x) + top) < 4:
                        continue                                   # rounded brow corners
                    if y > 27 and (x < 5 + (y - 27) or x > 26 - (y - 27)):
                        continue                                   # narrowing chin
                    put(x, y, fp[2] if (x in (5, 26) or y == 11) else fp[3])
        for side in (0, 1):  # sharp red eyes with black outline
            X = (lambda x: x) if side == 0 else (lambda x: 31 - x)
            for x in range(7, 14):
                put(X(x), 16 + (x - 7) // 3, (20, 12, 18))
            for x in range(8, 13):
                put(X(x), 18, (250, 250, 250)); put(X(x), 19, (250, 250, 250))
            for x in (10, 11):
                put(X(x), 18, (210, 30, 40)); put(X(x), 19, (150, 14, 24))
            put(X(6), 15, (20, 12, 18))
        for x in range(13, 19):  # dark purple lips, smug
            put(x, 26, (70, 30, 80))
        put(19, 25, (70, 30, 80))
        put(16, 23, tones(skin)[1])
    return p


def oval_cuff(skin, faces=("north",)):
    """A bracer in the skin colour carrying a glossy purple oval gem (shins; forearms when golden)."""
    def p(face, img):
        pixel_mat(img, skin, face, seed=5)
        if face not in faces:
            return
        w, h = img.size
        px = img.load()
        t = tones(FRIEZA_PURPLE)
        for y in range(h):
            for x in range(w):
                dx = (x + 0.5 - w / 2) / (w * 0.34)
                dy = (y + 0.5 - h / 2) / (h * 0.42)
                r = dx * dx + dy * dy
                if r < 1:
                    k = 4 if (-0.75 < dx < -0.2 and -0.8 < dy < -0.1) else (2 if r < 0.7 else 1)
                    px[x, y] = t[k] + (255,)
    return p


def dome_front(face, img):
    """Head dome: glossy purple, its front edge rounded down onto the forehead."""
    gem(face, img)
    if face != "north":
        return
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            dx = (x + 0.5 - w / 2) / (w / 2)
            if (y + 0.5) / h > 0.25 + 0.75 * (1 - dx * dx) ** 0.5:
                px[x, y] = (0, 0, 0, 0)


def frieza_chest(face, px, w, h, base):
    """Smooth alien chest: soft pecs and abs lines, no scars."""
    if face != "north":
        return
    t = tones(base)
    cx = w // 2
    for x in range(3, w - 3):
        if abs(x - cx) > 1:
            _put(px, w, h, x, int(h * 0.38) - abs(x - cx) // 4, t[1])
    for y in range(int(h * 0.48), h - 3):
        _put(px, w, h, cx, y, t[1])
    for row in (0.6, 0.74):
        for x in range(cx - 4, cx + 5):
            if x != cx:
                _put(px, w, h, x, int(h * row), t[1])


def frieza_body(m, golden=False):
    skin = FRIEZA_GOLD if golden else FRIEZA_WHITE
    limb = solid(skin)
    m.box("head", [-4, 24, -4], [8, 8, 8], frieza_head(skin, golden))
    m.box("head", [-3.2, 29.4, -4.3], [6.4, 3.0, 8.4], dome_front)                # dome: crown down onto the forehead
    m.box("head", [-2.6, 32.4, -3.6], [5.2, 0.7, 7.2], gem)
    m.box("body", [-4, 12, -2], [8, 12, 4], layered(skin, [frieza_chest]))
    for i, (wd, ht) in enumerate([(4.8, 1.5), (4.0, 0.9), (2.8, 0.7), (1.4, 0.5)]):  # shield-shaped chest gem
        y = 20.6 - sum(hh for _, hh in [(4.8, 1.5), (4.0, 0.9), (2.8, 0.7), (1.4, 0.5)][:i + 1])
        m.box("body", [-wd / 2, y, -2.45], [wd, ht, 0.5], gem if i == 0 else solid(tones(FRIEZA_PURPLE)[2]))
    m.box("rightArm", [4, 12, -2], [3.4, 12, 4], limb)
    m.box("leftArm", [-7.4, 12, -2], [3.4, 12, 4], limb)
    m.box("rightLeg", [-0.1, 0, -2], [4, 12, 4], limb)
    m.box("leftLeg", [-3.9, 0, -2], [4, 12, 4], limb)
    both_arms(m, [3.6, 20, -2.6], [4.4, 3.8, 5.2], solid(skin) if golden else gem)  # shoulder domes (gold when golden)
    if golden:
        both_arms(m, [3.75, 13.4, -2.25], [3.9, 4.2, 4.5], oval_cuff(skin, ("north", "east", "west")))  # forearm bracers
    both_legs(m, [-0.35, 2.2, -2.45], [4.5, 5.6, 4.9], oval_cuff(skin))              # shin bracers with oval gems
    if golden:
        both_arms(m, [3.85, 11.6, -2.1], [3.7, 2, 4.2], solid(FRIEZA_PURPLE))       # purple hands
        both_legs(m, [-0.25, 0, -2.4], [4.3, 1.4, 4.8], solid(FRIEZA_PURPLE))        # purple feet
    both_legs(m, [0.2, 0, -3.3], [3.4, 1.1, 1.4], solid(FRIEZA_PURPLE if golden else skin))  # toes
    tail = layered(skin, [lines((SIDES, [[(0, 0.5), (1, 0.5)]]), tones(skin)[1])])
    m.bones = BONES + [{"name": "tail", "parent": "body", "pivot": [0, 12.4, 2.1]}]
    m.strand([0, 12.4, 2.1], [0, -0.55, 1], 15, 3.2, tail, bone="tail", segs=3, thick=1.0, bend=(0.25, 0.15, -0.1))


_build_v7 = build


def build(char, form):  # noqa: F811
    if char == "zoro":
        m = Model()
        zoro_body(m, king=form == "king")
        if form == "king":  # hair hidden under the bandana; the painted head shows the cropped sides
            pass
        else:
            zoro_hair(m, ZORO_HAIR)
        return m
    if char == "frieza":
        m = Model()
        frieza_body(m, golden=form == "golden")
        return m
    return _build_v7(char, form)


FORMS["zoro"] = ["base", "king"]
FORMS["frieza"] = ["final", "golden"]


# ================================================================ facial expressions
# build.py renders every form four times with EXPR = None / "shout" / "hurt" / "blink"; the script picks the face.
EXPR = None


def _expr_put(px, W, H):
    k = W / 32.0

    def put(x, y, c):
        for dx in range(int(k)):
            for dy in range(int(k)):
                xx, yy = int(x * k) + dx, int(y * k) + dy
                if 0 <= xx < W and 0 <= yy < H:
                    px[xx, yy] = c + (255,)
    return put


def draw_expr(px, W, H, expr, skin, marks=(), eye_type="", left_only=False, mouth=True, mouth_skin=None, mouth_type=""):
    put = _expr_put(px, W, H)
    sr = ramp(skin)
    ms = ramp(mouth_skin) if mouth_skin else sr
    ink, white = (20, 12, 14), (250, 250, 250)
    sides = (False,) if left_only else (False, True)

    def P(x, y, c):
        for mirror in sides:
            put(31 - x if mirror else x, y, c)
    lid = (238, 238, 246) if eye_type == "big" else ink  # Gojo's lashes are white
    if expr == "blink" and eye_type != "band":
        for x in range(6, 14):  # relaxed closed lids with lashes
            P(x, 20 if 7 <= x <= 12 else 19, lid)
            if eye_type == "big":
                P(x, 21 if 7 <= x <= 12 else 20, sr[0])  # lid crease so the white lashes read on the skin
        P(5, 19, lid); P(13, 19, lid)
        for x in (7, 9, 11):
            P(x, 21, sr[1])
    if expr == "hurt" and eye_type != "band":
        for x, y in ((6, 16), (7, 17), (8, 17), (9, 18), (10, 18), (11, 19), (12, 19), (11, 20), (10, 20),
                     (9, 21), (8, 21), (7, 22), (6, 22)):
            P(x, y, ink if eye_type != "big" else sr[0])  # squeezed shut: > <
        for x in range(5, 13):
            P(x, 14 if x > 7 else 15, dark(skin, 0.55))  # knitted brow
    if expr == "shout" and eye_type == "g5":  # Gear 5 toon mode: the eyes pop out of his head
        for cx in (9.5, 21.5):
            for y in range(12, 24):
                for x in range(3, 29):
                    d = ((x + 0.5 - cx - 0.5) ** 2 + (y + 0.5 - 18) ** 2) ** 0.5
                    if d < 5.2:
                        put(x, y, ink if d > 4.3 else white)
            for x, y in ((int(cx), 18), (int(cx) + 1, 18), (int(cx), 19), (int(cx) + 1, 19)):
                put(x, y, ink)
    if not mouth:
        return
    if expr == "shout" and "sukuna_face" in marks:  # Sukuna's maniacal grin: wide, fangs bared
        for y in range(24, 30):
            for x in range(9, 23):
                put(x, y, ms[2])
        rows = {24: (11, 20), 25: (10, 21), 26: (10, 21), 27: (11, 20), 28: (13, 18)}
        for y, (a, b) in rows.items():
            for x in range(a, b + 1):
                edge = x in (a, b) or y in (24, 28)
                put(x, y, ink if edge else (white if y == 25 else (70, 14, 22)))
        put(9, 24, ink); put(22, 24, ink); put(8, 23, ink); put(23, 23, ink)  # corners pulled up
        for x in (12, 19):
            put(x, 26, white)  # fangs
        for x in range(13, 19, 2):
            put(x, 25, (190, 190, 196))
        return
    if expr == "shout" and mouth_type == "smirk" and eye_type in ("big", "band"):  # Gojo: a cocky open grin
        for y in range(24, 30):
            for x in range(10, 22):
                put(x, y, ms[2])
        rows = {25: (12, 20), 26: (12, 20), 27: (13, 19)}
        for y, (a, b) in rows.items():
            for x in range(a, b + 1):
                edge = x in (a, b) or y == 27
                put(x, y, ink if edge else (white if y == 25 else (150, 50, 60)))
        put(11, 24, ink); put(21, 24, ink); put(20, 24, ink)  # one corner hitched higher
        put(21, 23, ink)
        return
    if expr == "shout" and (mouth_type == "corner" or "zoro_eye" in marks):  # Vegeta, and Zoro biting Wado
        for y in range(24, 30):
            for x in range(10, 22):
                put(x, y, ms[2])
        for x in range(11, 21):
            put(x, 24, ink); put(x, 29, ink)
            for y in (25, 26, 27, 28):
                put(x, y, white if y in (25, 28) else ((150, 30, 40) if y == 26 else (120, 24, 34)))
        for y in range(25, 29):
            put(10, y, ink); put(21, y, ink)
        for x in (13, 15, 17, 19):
            put(x, 25, (170, 170, 178)); put(x, 28, (170, 170, 178))
        return
    if expr == "shout":
        for y in range(24, 31):
            for x in range(11, 21):
                put(x, y, ms[2])
        rows = {24: (13, 18), 25: (12, 19), 26: (11, 20), 27: (11, 20), 28: (11, 20), 29: (12, 19), 30: (13, 18)}
        for y, (a, b) in rows.items():
            for x in range(a, b + 1):
                edge = x in (a, b) or y in (24, 30)
                c = ink if edge else ((246, 246, 246) if y == 25 else ((196, 74, 86) if y >= 29 else (96, 22, 34)))
                put(x, y, c)
    if expr in ("hurt", "mouth_hurt"):
        for y in range(24, 30):
            for x in range(11, 21):
                put(x, y, ms[2])
        for x in range(12, 20):
            put(x, 25, ink); put(x, 28, ink)
            put(x, 26, white); put(x, 27, white)
        put(11, 26, ink); put(11, 27, ink); put(20, 26, ink); put(20, 27, ink)
        for x in (14, 16, 18):
            put(x, 26, (160, 160, 168)); put(x, 27, (160, 160, 168))


_face32_v6 = face32


def face32(px, W, H, spec, hair, iris, skin):  # noqa: F811
    expr = EXPR
    marks = spec.get("marks", [])
    eye = spec.get("eye", "")
    own_eyes = "heian_mask" in marks  # Heian Sukuna's masked eye is painted by the mask layer: keep it, change the mouth
    closed = expr in ("blink", "hurt") and eye != "band" and not own_eyes
    _face32_v6(px, W, H, dict(spec, eye="__none__") if closed else spec, hair, iris, skin)
    if "widow_peak" in marks:  # Vegeta's sharp M-shaped hairline
        put = _expr_put(px, W, H)
        hr = ramp(hair)
        for y, (a, b) in {12: (10, 21), 13: (12, 19), 14: (13, 18), 15: (14, 17), 16: (15, 16)}.items():
            for x in range(a, b + 1):
                put(x, y, hr[1] if x in (a, b) else hr[2])
    if expr:
        if closed and "zoro_king" in marks:
            put = _expr_put(px, W, H)
            for x in (8, 9):
                for y in (18, 19, 20):
                    put(x, y, ramp(skin)[2])
        if closed and "sukuna_face" in marks:  # the second pair of eyes closes too
            put = _expr_put(px, W, H)
            for x in (9, 10, 11, 12):
                put(x, 24, ramp(skin)[2]); put(31 - x, 24, ramp(skin)[2])
        masked = any(m in marks for m in ("mask", "heian_mask"))
        draw_expr(px, W, H, expr if (closed or expr == "shout") else ("mouth_" + expr), skin, marks, eye,
                  left_only="zoro_eye" in marks, mouth=not masked, mouth_type=spec.get("mouth", ""))


def frieza_head_x(skin, golden):
    base = _frieza_head_orig(skin, golden)

    def p(face, img):
        if face != "north" or not EXPR:
            base(face, img)
            return
        before = EXPR
        base(face, img)
        w, h = img.size
        px = img.load()
        k = w / 32.0
        face_c = px[int(16 * k) + 1, int(21 * k) + 1][:3]  # sample the actual face tone between the eyes
        if before in ("blink", "hurt"):
            put = _expr_put(px, w, h)
            for y in range(14, 21):
                for x in list(range(5, 15)) + list(range(17, 27)):
                    put(x, y, face_c)
        draw_expr(px, w, h, before, face_c, mouth_skin=face_c)
    return p


# ================================================================ Zoro's three swords (wiki reference art)
SWORDS = {
    # white hilt with black diamond wrap, round brass guard, white scabbard
    "wado": dict(wrap=(236, 236, 240), diamond=(26, 24, 30), tsuba="round", metal=(196, 160, 72),
                 blade=(206, 214, 226), edge=(248, 250, 255), hamon=None, saya=(234, 234, 238), saya_band=(30, 28, 34)),
    # crimson hilt wrap, four-lobed gold guard, wavy (cursed) hamon, dark red scabbard
    "kitetsu": dict(wrap=(150, 26, 34), diamond=(54, 14, 20), tsuba="cross", metal=(184, 160, 84),
                    blade=(204, 210, 222), edge=(246, 248, 255), hamon=(232, 168, 120), saya=(120, 24, 32), saya_band=(196, 196, 204)),
    # purple hilt with gold bands and a pink flower, three-ring gold guard, black scabbard
    "enma": dict(wrap=(120, 52, 170), diamond=(84, 30, 128), tsuba="trio", metal=(214, 176, 70), flower=(250, 180, 220),
                 blade=(70, 74, 86), edge=(220, 232, 244), hamon=None, saya=(28, 26, 32), saya_band=(214, 176, 70)),
}


def _rot_for(d):
    ax, az = math.degrees(math.asin(clampf(d[2]))), math.degrees(math.atan2(-d[0], d[1]))
    return [round(ax, 2), 0, round(az, 2)]


def _width_axis(d):
    c = max(1e-4, math.sqrt(max(0.0, 1 - d[2] * d[2])))
    return (-d[2] * d[0] / c, -d[2] * d[1] / c, c)


def wrap_paint(col, diamond, flower=None, metal=None):
    """Tsuka: silk wrap crossing over the ray skin, so a chain of diamonds runs down the hilt."""
    def p(face, img):
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = col
                if face in SIDES and ((x + y) % 4 == 0 or (x - y) % 4 == 0):
                    c = diamond
                if face in ("up", "down"):
                    c = dark(col, 0.7)
                px[x, y] = c + (255,)
        if flower and face in ("east", "west") and h > 6:
            cy = h // 2
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= w // 2 + dx < w:
                    px[w // 2 + dx, cy + dy] = (flower if (dx or dy) else (255, 240, 120)) + (255,)
        if metal and face in SIDES:  # gold bands (Enma)
            for y in (1, h - 2):
                for x in range(w):
                    px[x, y] = metal + (255,)
    return p


def blade_paint(st, tip=False):
    def p(face, img):
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                if face == "north":
                    c = st["edge"]
                elif face == "south":
                    c = dark(st["blade"], 0.72)
                elif face in ("up", "down"):
                    c = st["blade"]
                else:  # the flat: polished edge band, the shinogi ridge line, darker spine side
                    u = x / max(1, w - 1)
                    c = st["edge"] if u < 0.3 else (dark(st["blade"], 0.86) if u > 0.75 else st["blade"])
                    if st.get("hamon") and 0.3 <= u <= 0.6:
                        c = st["hamon"]
                px[x, y] = c + (255,)
    return p


def katana2(m, bone, hand, direction, length, st, grip=1.2):
    """A katana built like the real thing: kashira, diamond-wrapped tsuka, fuchi, shaped tsuba, habaki and a
    curved blade (several segments bending toward the spine) ending in a kissaki."""
    d = norm(direction)
    gx, gy, gz = hand
    # the guard sits a little in front of the fist
    hx, hy, hz = gx + d[0] * grip, gy + d[1] * grip, gz + d[2] * grip
    rot, piv = _rot_for(d), [hx, hy, hz]
    metal = solid(st["metal"])
    m.box(bone, [hx - 0.42, hy - 4.2, hz - 0.36], [0.84, 0.45, 0.72], metal, rot=rot, pivot=piv)               # kashira
    m.box(bone, [hx - 0.38, hy - 3.8, hz - 0.32], [0.76, 3.4, 0.64],
          wrap_paint(st["wrap"], st["diamond"], st.get("flower"), st["metal"] if st.get("flower") else None), rot=rot, pivot=piv)
    m.box(bone, [hx - 0.42, hy - 0.45, hz - 0.36], [0.84, 0.4, 0.72], metal, rot=rot, pivot=piv)              # fuchi
    t = st["tsuba"]
    if t == "round":
        m.box(bone, [hx - 1.1, hy - 0.05, hz - 0.75], [2.2, 0.3, 1.5], metal, rot=rot, pivot=piv)
        m.box(bone, [hx - 0.75, hy - 0.05, hz - 1.1], [1.5, 0.3, 2.2], metal, rot=rot, pivot=piv)
    elif t == "cross":
        m.box(bone, [hx - 1.3, hy - 0.05, hz - 0.55], [2.6, 0.3, 1.1], metal, rot=rot, pivot=piv)
        m.box(bone, [hx - 0.55, hy - 0.05, hz - 1.3], [1.1, 0.3, 2.6], metal, rot=rot, pivot=piv)
        m.box(bone, [hx - 0.85, hy - 0.06, hz - 0.85], [1.7, 0.32, 1.7], solid(dark(st["metal"], 0.8)), rot=rot, pivot=piv)
    else:  # Enma's three gold rings
        for ox, oz in ((0, -0.95), (-0.85, 0.5), (0.85, 0.5)):
            m.box(bone, [hx + ox - 0.6, hy - 0.05, hz + oz - 0.6], [1.2, 0.3, 1.2], metal, rot=rot, pivot=piv)
        m.box(bone, [hx - 0.5, hy - 0.06, hz - 0.5], [1.0, 0.32, 1.0], metal, rot=rot, pivot=piv)
    m.box(bone, [hx - 0.2, hy + 0.25, hz - 0.5], [0.4, 0.6, 1.0], solid(st["metal"]), rot=rot, pivot=piv)     # habaki
    # curved blade
    p = [hx + d[0] * 0.85, hy + d[1] * 0.85, hz + d[2] * 0.85]
    seg = 5
    cur = d
    for i in range(seg):
        L = length / seg
        wdt = 0.86 - 0.06 * i
        r = _rot_for(cur)
        m.box(bone, [p[0] - 0.13, p[1], p[2] - wdt / 2], [0.26, L + 0.05, wdt], blade_paint(st), rot=r, pivot=list(p))
        p = [p[k] + cur[k] * L for k in range(3)]
        W = _width_axis(cur)
        cur = norm(tuple(cur[k] + W[k] * 0.055 for k in range(3)))
    W = _width_axis(cur)
    tipd = norm(tuple(cur[k] + W[k] * 0.25 for k in range(3)))
    m.box(bone, [p[0] - 0.12, p[1], p[2] - 0.28], [0.24, 1.3, 0.5], blade_paint(st, True), rot=_rot_for(tipd), pivot=list(p))  # kissaki


def sheath(m, top, direction, length, st):
    """An empty saya hanging from the sash: koiguchi collar, lacquered body with bands, kojiri cap."""
    d = norm(direction)
    rot, piv = _rot_for(d), list(top)
    x, y, z = top
    lacq = layered(st["saya"], [lines((SIDES, [[(0.5, 0), (0.5, 1)]]), light(st["saya"], 0.18))])
    m.box("body", [x - 0.4, y, z - 0.55], [0.8, length, 1.1], lacq, rot=rot, pivot=piv)
    m.box("body", [x - 0.46, y - 0.05, z - 0.6], [0.92, 0.5, 1.2], solid(st["saya_band"]), rot=rot, pivot=piv)         # koiguchi
    m.box("body", [x - 0.46, y + 2.2, z - 0.6], [0.92, 0.35, 1.2], solid(st["saya_band"]), rot=rot, pivot=piv)         # kurikata band
    m.box("body", [x - 0.46, y + length - 0.6, z - 0.6], [0.92, 0.7, 1.2], solid(st["saya_band"]), rot=rot, pivot=piv)  # kojiri



# ================================================================ Goku's "Go" (悟) emblem, Super-era gi
GO_GLYPH = [
    "............",
    "............",
    "...#.######.",
    "...#...#....",
    "..###.####..",
    "...#.....#..",
    "...#.######.",
    "...#..####..",
    "...#..#..#..",
    "...#..#..#..",
    "...#..####..",
    "............",
]


def emblem_paint(face, img):
    w, h = img.size
    px = img.load()
    show = face in ("north", "south")
    for y in range(h):
        for x in range(w):
            if not show:
                px[x, y] = (244, 244, 240, 255)
                continue
            dx, dy = (x + 0.5) / w - 0.5, (y + 0.5) / h - 0.5
            if dx * dx + dy * dy > 0.25:
                px[x, y] = (0, 0, 0, 0)
                continue
            g = GO_GLYPH[min(11, int(y * 12 / h))][min(11, int(x * 12 / w))]
            px[x, y] = ((22, 18, 22) if g == "#" else (246, 246, 242)) + (255,)


_goku_body_v3 = goku_body


def torn_undershirt(face, img):
    """Ultra Instinct (Tournament of Power): the gi top is gone, the blue undershirt is shredded open."""
    w, h = img.size
    px = img.load()
    bt, st = tones(GI_BLUE), tones(SKIN)
    for y in range(h):
        for x in range(w):
            u, v = (x + 0.5) / w, (y + 0.5) / h
            n = (x * 7 + y * 13) % 5
            c = bt[2] if face not in ("east",) else bt[1]
            if face in ("up", "down"):
                px[x, y] = c + (255,)
                continue
            hole = False
            n2 = ((x * 5 + y * 3) % 7 - 3) * 0.09 + (n - 2) * 0.1
            if face == "north":  # a diagonal rip from the left shoulder across the chest
                ru, rv = u - 0.46, v - 0.42
                a1 = ru * 0.87 + rv * 0.5
                b1 = -ru * 0.5 + rv * 0.87
                hole = (a1 / 0.44) ** 2 + (b1 / 0.17) ** 2 < 1 + n2
                hole = hole or ((u - 0.15) / 0.12) ** 2 + ((v - 0.12) / 0.1) ** 2 < 1 + n2
            elif face == "south":
                ru, rv = u - 0.55, v - 0.5
                a1 = ru * 0.8 - rv * 0.6
                b1 = ru * 0.6 + rv * 0.8
                hole = (a1 / 0.32) ** 2 + (b1 / 0.12) ** 2 < 1 + n2
            else:
                hole = ((u - 0.5) / 0.22) ** 2 + ((v - 0.25) / 0.1) ** 2 < 1 + n2
            if v > 0.9 - (n % 3) * 0.05:  # ragged hem
                hole = True
            if hole:
                c = st[2] if face != "east" else st[1]
                if face == "north" and abs(u - 0.5) < 0.03 and 0.4 < v < 0.7:
                    c = st[1]  # sternum line
            px[x, y] = c + (255,)
        # dark frayed edge around the openings
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if px[x, y][:3] in (bt[2], bt[1]) and any(px[x + dx, y + dy][:3] in (st[2], st[1]) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = bt[0] + (255,)


def goku_body(m, hair, iris, brows=True, style="goku"):  # noqa: F811
    _goku_body_v3(m, hair, iris, brows, style)
    if style == "calm":  # Ultra Instinct: torn undershirt instead of the gi top, no emblem
        m.box("body", [-4.45, 13.7, -2.75], [8.9, 10.6, 5.5], torn_undershirt)
        return
    m.box("body", [-4.0, 19.2, -2.62], [3.0, 3.0, 0.25], emblem_paint)   # left chest
    m.box("body", [-2.75, 15.0, 2.36], [5.5, 5.5, 0.25], emblem_paint)   # back



# ================================================================ Gojo: Jujutsu High uniform collar + swirl button
def swirl_button(face, img):
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5) / w - 0.5, (y + 0.5) / h - 0.5
            r = (dx * dx + dy * dy) ** 0.5
            ang = math.atan2(dy, dx)
            ring = (r * 9 + ang / 1.4) % 2 < 1
            px[x, y] = ((214, 178, 76) if ring else (150, 118, 40)) + (255,) if r <= 0.5 else (0, 0, 0, 0)


_gojo_body_v2 = gojo_body


def gojo_body(m, hair, iris, blindfold):  # noqa: F811
    _gojo_body_v2(m, hair, iris, blindfold)
    navy = (24, 26, 44)
    col = layered(navy, [lines((SIDES, [[(0, 0.15), (1, 0.15)]]), (44, 48, 76))])
    m.box("body", [-4.15, 21.9, -2.85], [8.3, 2.1, 0.6], col)        # high collar, front (stands up to the chin)
    m.box("body", [-4.15, 21.9, 2.25], [8.3, 2.1, 0.6], col)         # back
    m.box("body", [-4.35, 21.9, -2.85], [0.6, 2.1, 5.7], col)        # sides
    m.box("body", [3.75, 21.9, -2.85], [0.6, 2.1, 5.7], col)
    m.box("body", [-3.5, 22.3, -3.1], [1.3, 1.3, 0.25], swirl_button)  # swirl button on the collar



# ================================================================ Naruto x4, Sasuke, Ichigo, Tanjiro (house style)
import chars_extra  # noqa: E402  (imported last: it builds on everything above)

FORMS.update(chars_extra.FORMS)
_build_v8 = build


def build(char, form):  # noqa: F811
    if char in chars_extra.FORMS:
        return chars_extra.build(char, form)
    return _build_v8(char, form)
