"""HD character models for Anime Battles.

Models are authored in Blockbench space (front = -Z, the character's right = +X,
rotations in degrees, Euler order ZYX) and converted to Bedrock geometry on export
the same way Blockbench does it. Textures are painted at S pixels per model unit.
"""
import math

from PIL import Image, ImageDraw

S = 4  # texture pixels per model unit (4 = HD, like 32px faces)

# ------------------------------------------------------------------ colour helpers


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dark(c, f=0.75):
    return tuple(max(0, int(v * f)) for v in c)


def light(c, f=0.35):
    return mix(c, (255, 255, 255), f)


SKIN = (246, 205, 170)
SKIN_SH = (222, 168, 135)

# ------------------------------------------------------------------ model building


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
# A painter is f(face, img) where img is the face's own RGBA image (w*S x h*S).
# face is one of north (front), south (back), east (character's right), west, up, down.


def shade_face(img, base, face, outline=True, grad=0.18):
    w, h = img.size
    dr = ImageDraw.Draw(img)
    top = light(base, 0.12) if face != "down" else dark(base, 0.8)
    for y in range(h):
        t = y / max(1, h - 1)
        c = mix(top, dark(base, 1 - grad), t) if face not in ("up", "down") else base
        dr.line([(0, y), (w - 1, y)], fill=c + (255,))
    if outline and w > 2 and h > 2:
        dr.rectangle([0, 0, w - 1, h - 1], outline=dark(base, 0.62) + (255,))


def solid(base, outline=True, grad=0.18):
    def p(face, img):
        shade_face(img, base, face, outline, grad)
    return p


def hair_paint(base):
    """Cel-shaded hair strand: dark root, bright tip, highlight streak, crisp outline."""
    def p(face, img):
        w, h = img.size
        px = img.load()
        hi = light(base, 0.45)
        for y in range(h):
            t = 1 - y / max(1, h - 1)  # 1 at top (tip), 0 at root
            row = mix(dark(base, 0.62), light(base, 0.12), t)
            for x in range(w):
                c = row
                if face in ("north", "south", "east", "west") and w > 3:
                    edge = min(x, w - 1 - x)
                    if edge == 0:
                        c = dark(base, 0.62)
                    elif x == w // 3 and t > 0.25:
                        c = mix(row, hi, 0.55)
                if face in ("up", "down"):
                    c = mix(dark(base, 0.8), base, 0.5)
                px[x, y] = c + (255,)
    return p


def layered(base, details):
    """Solid base + list of detail drawers f(face, draw, w, h)."""
    def p(face, img):
        shade_face(img, base, face)
        dr = ImageDraw.Draw(img)
        for f in details:
            f(face, dr, img.size[0], img.size[1])
    return p


# ------------------------------------------------------------------ faces


def head_paint(hair, eyes, brows=True, style="goku", blindfold=False):
    """Head cube: hair on top/back/sides, an anime face on the front (32x32)."""
    def p(face, img):
        w, h = img.size
        dr = ImageDraw.Draw(img)
        if face == "up":
            shade_face(img, hair, face, outline=False)
            return
        if face == "down":
            shade_face(img, SKIN_SH, face, outline=False)
            return
        shade_face(img, SKIN, face, outline=False, grad=0.08)
        if face == "south":
            dr.rectangle([0, 0, w, int(h * 0.85)], fill=hair + (255,))
            return
        if face in ("east", "west"):
            dr.rectangle([0, 0, w, int(h * 0.34)], fill=hair + (255,))
            front = w - 1 if face == "east" else 0
            sb = [front - 5, int(h * 0.34), front + 5, int(h * 0.58)]
            dr.rectangle(sb, fill=hair + (255,))
            if blindfold:
                dr.rectangle([0, 9, w, 18], fill=(14, 14, 20, 255))
            return
        # ---- front face (32x32)
        dr.rectangle([0, 0, w, 7], fill=hair + (255,))
        dr.rectangle([0, 8, w, 10], fill=SKIN_SH + (255,))  # hair shadow on forehead
        if style == "vegeta":
            dr.polygon([(9, 7), (16, 15), (23, 7)], fill=hair + (255,))  # widow's peak
        if blindfold:
            dr.rectangle([0, 9, w, 18], fill=(14, 14, 20, 255))
            dr.line([(0, 10), (w, 10)], fill=(40, 40, 52, 255))
            dr.line([(3, 14), (12, 13)], fill=(34, 34, 44, 255))
            dr.line([(20, 13), (29, 14)], fill=(34, 34, 44, 255))
        else:
            draw_eyes(dr, eyes, style, brows, hair)
        # nose + mouth + cheeks
        dr.line([(16, 21), (16, 22)], fill=SKIN_SH + (255,))
        dr.point((15, 23), fill=SKIN_SH + (255,))
        if style == "gojo":
            dr.line([(13, 26), (18, 26)], fill=(170, 90, 90, 255))
            dr.point((19, 25), fill=(170, 90, 90, 255))  # smirk
        elif style == "vegeta":
            dr.line([(13, 26), (19, 26)], fill=(150, 80, 70, 255))
            dr.point((12, 25), fill=(150, 80, 70, 255))
        else:
            dr.line([(13, 26), (19, 26)], fill=(160, 85, 75, 255))
            dr.line([(14, 27), (18, 27)], fill=SKIN_SH + (255,))
        dr.line([(5, 31), (26, 31)], fill=SKIN_SH + (255,))  # jaw shade
    return p


def draw_eyes(dr, iris, style, brows, hair):
    lash = (20, 16, 18, 255)
    white = (255, 255, 255, 255)
    for side in (0, 1):
        # side 0 = viewer's left; eyes mirror around x = 15.5
        def X(x):
            return x if side == 0 else 31 - x
        if style == "gojo":
            top, bot = 15, 21
            dr.polygon([(X(6), top + 1), (X(13), top), (X(14), top + 2), (X(13), bot), (X(7), bot)], fill=white)
            dr.rectangle(sorted_box(X(9), top + 1, X(13), bot), fill=iris + (255,))
            dr.rectangle(sorted_box(X(10), top + 1, X(12), top + 3), fill=light(iris, 0.6) + (255,))
            dr.rectangle(sorted_box(X(10), top + 4, X(12), bot - 1), fill=dark(iris, 0.6) + (255,))
            dr.point((X(10), top + 2), fill=white)
            dr.line([(X(5), top), (X(14), top - 1)], fill=(235, 235, 245, 255), width=2)  # white lashes
            if brows:
                dr.line([(X(6), top - 4), (X(13), top - 5)], fill=(240, 240, 248, 255), width=1)
            continue
        top, bot = 16, 20
        sharp = style in ("goku", "vegeta")
        dr.polygon([(X(6), top + 1), (X(13), top), (X(14), top + 2), (X(13), bot), (X(7), bot - 1)], fill=white)
        dr.rectangle(sorted_box(X(10), top + 1, X(13), bot), fill=iris + (255,))
        dr.rectangle(sorted_box(X(11), top + 2, X(12), bot - 1), fill=dark(iris, 0.35) + (255,))
        dr.point((X(11), top + 1), fill=white)
        dr.line([(X(5), top + 1), (X(9), top), (X(14), top - (1 if sharp else 0))], fill=lash, width=2)
        if brows:
            bc = dark(hair, 0.7) + (255,) if sum(hair) < 200 else hair + (255,)
            if style == "vegeta":
                dr.line([(X(5), top - 5), (X(14), top - 2)], fill=bc, width=2)
            else:
                dr.line([(X(5), top - 4), (X(14), top - 2)], fill=bc, width=2)
        else:
            dr.line([(X(6), top - 3), (X(13), top - 2)], fill=SKIN_SH + (255,), width=1)  # SSJ3 brow ridge


def sorted_box(x0, y0, x1, y1):
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


# ------------------------------------------------------------------ shared parts


def ears(m):
    for sx in (1, -1):
        x = 4 if sx == 1 else -4.75
        m.box("head", [x, 26.5, -0.75], [0.75, 2.25, 1.5], solid(SKIN, grad=0.1))


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


# ------------------------------------------------------------------ Goku

GI = (247, 128, 28)
GI_BLUE = (36, 62, 176)
BOOT_BLUE = (32, 50, 140)


def kanji_front(face, dr, w, h):
    if face != "north":
        return
    # chest symbol on the character's left (viewer's right)
    cx, cy = w - 9, 9
    dr.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(252, 250, 242, 255), outline=(30, 30, 30, 255))
    dr.line([(cx - 2, cy - 2), (cx + 2, cy - 2)], fill=(20, 20, 20, 255))
    dr.line([(cx, cy - 3), (cx, cy + 3)], fill=(20, 20, 20, 255))
    dr.line([(cx - 2, cy + 1), (cx + 2, cy + 1)], fill=(20, 20, 20, 255))
    # V-neck showing the blue undershirt
    dr.polygon([(w // 2 - 7, 0), (w // 2 + 7, 0), (w // 2, 12)], fill=GI_BLUE + (255,))
    dr.line([(w // 2 - 7, 0), (w // 2, 12), (w // 2 + 7, 0)], fill=dark(GI, 0.7) + (255,), width=1)
    # fabric folds
    for x in (8, 22):
        dr.line([(x, 20), (x + 2, h - 2)], fill=dark(GI, 0.86) + (255,))


def kanji_back(face, dr, w, h):
    if face != "south":
        return
    cx, cy = w // 2, 14
    dr.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(252, 250, 242, 255), outline=(30, 30, 30, 255), width=2)
    k = (20, 20, 20, 255)
    dr.line([(cx - 5, cy - 4), (cx + 5, cy - 4)], fill=k, width=2)
    dr.line([(cx, cy - 7), (cx, cy + 6)], fill=k, width=2)
    dr.line([(cx - 5, cy + 1), (cx + 5, cy + 1)], fill=k, width=2)
    dr.line([(cx - 4, cy + 5), (cx + 4, cy + 5)], fill=k, width=2)


def laces(face, dr, w, h):
    if face != "north":
        return
    for y in range(3, h - 6, 4):
        dr.line([(3, y), (w - 4, y + 2)], fill=(210, 40, 40, 255), width=1)
        dr.line([(w - 4, y), (3, y + 2)], fill=(210, 40, 40, 255), width=1)


def goku_body(m, hair, iris, brows=True):
    base_body(m, solid(GI_BLUE), solid(SKIN, grad=0.12), solid(GI),
              head_paint(hair, iris, brows, "goku"))
    # gi vest + skirt
    m.box("body", [-4.25, 12.5, -2.3], [8.5, 11.75, 4.6], layered(GI, [kanji_front, kanji_back]))
    m.box("body", [-4.4, 9.5, -2.45], [8.8, 3.25, 4.9], solid(GI))
    # lapels
    m.box("body", [-0.5, 18, -2.6], [1, 6.5, 0.5], solid(dark(GI, 0.9)), rot=[0, 0, -26], pivot=[0, 18, -2.6])
    m.box("body", [-0.5, 18, -2.6], [1, 6.5, 0.5], solid(dark(GI, 0.9)), rot=[0, 0, 26], pivot=[0, 18, -2.6])
    # obi belt + knot with tails at the back
    m.box("body", [-4.6, 12, -2.6], [9.2, 1.75, 5.2], solid(GI_BLUE))
    m.box("body", [-1.25, 11.5, 2.4], [2.5, 2.25, 1], solid(dark(GI_BLUE, 0.9)))
    m.strand([-0.6, 12, 3], [-0.35, -1, 0.25], 4.5, 1.25, solid(GI_BLUE), bone="body", segs=2)
    m.strand([0.6, 12, 3], [0.35, -1, 0.3], 4, 1.25, solid(GI_BLUE), bone="body", segs=2)
    # undershirt sleeves, shoulders, wristbands
    both_arms(m, [3.75, 19.25, -2.25], [4.5, 5, 4.5], solid(GI_BLUE))
    both_arms(m, [3.6, 12, -2.4], [4.8, 3.25, 4.8], solid(GI_BLUE))
    # baggy pants + boots
    both_legs(m, [-0.4, 5, -2.4], [4.6, 7, 4.8], layered(GI, [lambda f, d, w, h: d.line([(w // 2, 2), (w // 2 + 1, h - 3)], fill=dark(GI, 0.85) + (255,)) if f == "north" else None]))
    both_legs(m, [-0.3, 0, -2.3], [4.4, 5.25, 4.6], layered(BOOT_BLUE, [laces]))
    both_legs(m, [-0.5, 4.5, -2.5], [4.8, 1.25, 5], solid(dark(BOOT_BLUE, 0.85)))
    both_legs(m, [0.1, 0, -3.3], [3.6, 1.75, 1.25], solid(BOOT_BLUE))
    both_legs(m, [-0.35, 0, -2.4], [4.5, 0.5, 4.8], solid((235, 220, 190)))  # soles


def goku_hair_base(m, c):
    hp = hair_paint(c)
    m.box("hair", [-4.4, 27.75, -4.4], [8.8, 5, 8.8], hp)
    m.box("hair", [-4.5, 25, 0.25], [9, 7.5, 4.25], hp)
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


def goku_hair_ssj(m, c):
    hp = hair_paint(c)
    m.box("hair", [-4.4, 28, -4.4], [8.8, 4.75, 8.8], hp)
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
    m.box("hair", [-4.4, 28, -4.4], [8.8, 4.75, 8.8], hp)
    m.box("hair", [-4.6, 22, 0.25], [9.2, 10, 4.5], hp)
    m.strand([0, 29, 4.2], [0, -1, 0.12], 22, 8.5, hp, thick=0.5)
    m.mirror_strand([3.2, 29, 3.2], [0.22, -1, 0.15], 19, 5, hp, thick=0.6)
    m.mirror_strand([4.4, 29.5, 0.2], [0.28, -1, 0.05], 11, 3.5, hp)
    m.strand([0, 32.25, -0.5], [0, 1, 0.35], 6.5, 5, hp)
    m.mirror_strand([2.6, 32, -0.5], [0.6, 1, 0.15], 6, 4.25, hp)
    m.strand([-2.3, 31.5, -4.1], [-0.3, -1, -0.4], 5, 3.25, hp)
    m.strand([0.4, 31.75, -4.2], [0.05, -1, -0.45], 5.5, 3, hp)
    m.strand([2.6, 31.5, -4.1], [0.4, -1, -0.35], 4.5, 2.75, hp)


# ------------------------------------------------------------------ Vegeta

SUIT = (34, 52, 154)
ARMOR = (240, 240, 232)
ARMOR_GOLD = (226, 176, 52)


def armor_detail(face, dr, w, h):
    if face == "north":
        dr.rectangle([0, h - 9, w, h], fill=ARMOR_GOLD + (255,))
        dr.line([(0, h - 9), (w, h - 9)], fill=dark(ARMOR_GOLD, 0.7) + (255,))
        for x in (w // 3, 2 * w // 3):
            dr.line([(x, h - 8), (x, h - 1)], fill=dark(ARMOR_GOLD, 0.7) + (255,))
        dr.line([(w // 2, 3), (w // 2, h - 12)], fill=dark(ARMOR, 0.86) + (255,))
        dr.arc([4, 2, w // 2 - 1, 16], 20, 160, fill=dark(ARMOR, 0.82) + (255,))
        dr.arc([w // 2 + 1, 2, w - 4, 16], 20, 160, fill=dark(ARMOR, 0.82) + (255,))
    if face in ("south", "east", "west"):
        dr.rectangle([0, h - 9, w, h], fill=ARMOR_GOLD + (255,))


def vegeta_body(m, hair, iris):
    base_body(m, solid(SUIT), solid(SUIT), solid(SUIT), head_paint(hair, iris, True, "vegeta"))
    m.box("body", [-4.5, 14.5, -2.75], [9, 9.25, 5.5], layered(ARMOR, [armor_detail]))
    m.box("body", [-3, 23.5, -2.25], [6, 1, 4.5], solid(SUIT))  # suit collar
    both_arms(m, [3.6, 21.5, -2.6], [4.8, 2.5, 5.2], solid(ARMOR_GOLD))  # shoulder straps
    both_arms(m, [3.6, 12, -2.4], [4.8, 4.75, 4.8], layered(ARMOR, [lambda f, d, w, h: d.line([(0, 4), (w, 4)], fill=dark(ARMOR, 0.8) + (255,))]))
    both_legs(m, [-0.35, 0, -2.35], [4.5, 6.5, 4.7], layered(ARMOR, [lambda f, d, w, h: d.rectangle([0, 0, w, 3], fill=ARMOR_GOLD + (255,))]))
    both_legs(m, [0.1, 0, -3.45], [3.6, 2, 1.25], solid(ARMOR_GOLD))


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


# ------------------------------------------------------------------ Gojo

UNI = (24, 27, 42)
UNI_HI = (44, 50, 74)


def jacket_detail(face, dr, w, h):
    if face == "north":
        dr.line([(w // 2, 0), (w // 2, h)], fill=UNI_HI + (255,), width=1)
        for y in range(6, h - 4, 9):
            dr.point((w // 2 + 2, y), fill=(60, 66, 92, 255))
    if face in ("east", "west"):
        dr.line([(w // 2, 8), (w // 2, h)], fill=dark(UNI, 0.7) + (255,))


def collar_detail(face, dr, w, h):
    if face == "north":
        cx, cy = w // 2, h // 2
        dr.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(206, 168, 72, 255), outline=(120, 90, 30, 255))
        dr.arc([cx - 2, cy - 2, cx + 2, cy + 2], 0, 270, fill=(120, 90, 30, 255))


def gojo_body(m, hair, iris, blindfold):
    base_body(m, solid(UNI), layered(UNI, [lambda f, d, w, h: d.rectangle([0, h - 5, w, h], fill=SKIN + (255,))]),
              solid(UNI), head_paint(hair, iris, not blindfold, "gojo", blindfold))
    m.box("body", [-4.3, 9, -2.3], [8.6, 15, 4.6], layered(UNI, [jacket_detail]))
    m.box("body", [-3.25, 23.5, -2.6], [6.5, 2.5, 5.2], layered(UNI_HI, [collar_detail]))
    both_arms(m, [3.8, 15, -2.2], [4.4, 9, 4.4], solid(UNI))
    both_arms(m, [3.7, 13.5, -2.3], [4.6, 1.5, 4.6], solid(UNI_HI))  # cuffs
    both_legs(m, [-0.3, 0, -2.6], [4.4, 1.5, 5], solid((14, 14, 18)))  # shoes
    if blindfold:
        band = layered((14, 14, 20), [lambda f, d, w, h: d.line([(0, 2), (w, 3)], fill=(40, 40, 52, 255))])
        m.box("head", [-4.3, 26.25, -4.3], [8.6, 2.5, 8.6], band)
        m.box("head", [-0.75, 26.25, 4.2], [1.5, 2.25, 0.75], solid((14, 14, 20)))
        m.strand([-0.4, 26.5, 4.6], [-0.3, -1, 0.35], 3.5, 1, solid((14, 14, 20)), bone="head", segs=2)
        m.strand([0.4, 26.5, 4.6], [0.3, -1, 0.4], 3, 1, solid((14, 14, 20)), bone="head", segs=2)


def gojo_hair_up(m, c):
    hp = hair_paint(c)
    m.box("hair", [-4.25, 28.5, -4.25], [8.5, 4, 8.5], hp)
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
    m.box("hair", [-4.3, 28, -4.3], [8.6, 4.5, 8.6], hp)
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
        hair, iris, brows, hair_fn = {
            "base": ((30, 28, 38), (34, 30, 36), True, goku_hair_base),
            "ssj": ((255, 214, 54), (0, 176, 166), True, goku_hair_ssj),
            "ssj3": ((255, 204, 44), (0, 176, 166), False, goku_hair_ssj3),
            "ssb": ((54, 182, 255), (40, 136, 240), True, goku_hair_ssj),
            "ui": ((214, 220, 236), (170, 176, 200), True, goku_hair_base),
        }[form]
        goku_body(m, hair, iris, brows)
        hair_fn(m, hair)
    elif char == "vegeta":
        hair, iris = {
            "base": ((26, 26, 36), (30, 28, 34)),
            "ssj": ((255, 214, 54), (0, 176, 166)),
            "ssb": ((54, 182, 255), (40, 136, 240)),
            "ue": ((172, 58, 226), (216, 70, 196)),
        }[form]
        vegeta_body(m, hair, iris)
        vegeta_hair(m, hair)
    elif char == "gojo":
        hair = (246, 246, 252)
        if form == "blindfold":
            gojo_body(m, hair, None, True)
            gojo_hair_up(m, hair)
        else:
            gojo_body(m, hair, (64, 196, 255), False)
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
