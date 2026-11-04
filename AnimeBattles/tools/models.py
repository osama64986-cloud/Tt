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
        size = [max(0.25, round(s * 4) / 4) for s in size]
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
            "ssb": ((40, 176, 255), (30, 126, 236), True, goku_hair_ssj, "goku"),
            "ui": ((214, 222, 240), (176, 186, 214), True, goku_hair_base, "calm"),
        }[form]
        goku_body(m, hair, iris, brows, style)
        hair_fn(m, hair)
    elif char == "vegeta":
        hair, iris = {
            "base": ((22, 22, 32), (36, 30, 36)),
            "ssj": ((255, 208, 40), (0, 172, 160)),
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
    "goku": ["base", "ssj", "ssj3", "ssb", "ui"],
    "vegeta": ["base", "ssj", "ssb", "ue"],
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
    bones = {b["name"]: dict(b, cubes=[]) for b in BONES}
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
    for b in BONES:
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
                px[x, y] = hr[2 if (x + y) % 4 else 1] + (255,)
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
                _put(px, w, h, x, y, rp[3] if y == a else rp[2 if (x + y) % 4 else 1])
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
