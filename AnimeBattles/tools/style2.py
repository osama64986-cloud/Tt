"""STYLE 2 — "anime toon".

A second, deliberately different look for comparison with the original style:
  * anime proportions on a jointed skeleton: forearms, shins, hands and feet are separate
    bones (elbows and knees bend), narrow waist, tapered chest, pointed chin;
  * twice the texel density (8 px per unit, 64 px faces);
  * cel shading like an anime frame: flat colour, one hard cool shadow, and a dark ink
    line around every part instead of the 5-tone ramp + bevel of style 1.
Used by the four Naruto fighters. Coordinates are Blockbench space like models.py
(front = -Z, the character's right = +X).
"""
import math

from PIL import Image

import models as M

S2 = 8

SKIN = (252, 214, 176)
HAIR = (255, 214, 48)
GOLD = (255, 206, 64)       # Nine-Tails chakra glow
ORANGE = (255, 128, 28)
BLUE_P1 = (40, 64, 150)
BLACK = (38, 38, 46)
WHITE = (246, 246, 242)
RED = (214, 40, 36)
METAL = (196, 202, 212)

BONES2 = [
    {"name": "root", "pivot": [0, 0, 0]},
    {"name": "body", "parent": "root", "pivot": [0, 13, 0]},
    {"name": "head", "parent": "body", "pivot": [0, 25.2, 0]},
    {"name": "hair", "parent": "head", "pivot": [0, 25.2, 0]},
    {"name": "hat", "parent": "head", "pivot": [0, 25.2, 0]},
    {"name": "rightArm", "parent": "body", "pivot": [-4.65, 23.4, 0]},
    {"name": "rightForearm", "parent": "rightArm", "pivot": [-4.65, 18.2, 0]},
    {"name": "leftArm", "parent": "body", "pivot": [4.65, 23.4, 0]},
    {"name": "leftForearm", "parent": "leftArm", "pivot": [4.65, 18.2, 0]},
    {"name": "rightLeg", "parent": "root", "pivot": [-1.75, 13, 0]},
    {"name": "rightShin", "parent": "rightLeg", "pivot": [-1.75, 7, 0]},
    {"name": "leftLeg", "parent": "root", "pivot": [1.75, 13, 0]},
    {"name": "leftShin", "parent": "leftLeg", "pivot": [1.75, 7, 0]},
    {"name": "tail", "parent": "body", "pivot": [0, 13.5, 1.6]},
    {"name": "cape", "parent": "body", "pivot": [0, 24, 1.9]},
    {"name": "orbs", "parent": "body", "pivot": [0, 21, 4.5]},
]


# ------------------------------------------------------------------ colour helpers
def ink(c):
    return M.mix(M.dark(c, 0.32), (22, 14, 26), 0.35)


def cel(c):
    return M.mix(M.dark(c, 0.8), (64, 44, 112), 0.16)


def hi(c, t=0.35):
    return M.mix(c, (255, 255, 255), t)


def _putter(px, w, h):
    def put(x, y, col):
        x, y = int(x), int(y)
        if 0 <= x < w and 0 <= y < h:
            px[x, y] = col if len(col) == 4 else col + (255,)
    return put


def toon(base, detail=None, outline=True, line=None, shade=True, alpha=None):
    """Flat anime fill: lit front/top/right, one hard cool shadow on the back/left/bottom, ink border."""
    def p(face, img):
        w, h = img.size
        px = img.load()
        c = base
        if shade and face in ("south", "west"):
            c = cel(base)
        elif shade and face == "down":
            c = M.dark(cel(base), 0.9)
        for y in range(h):
            for x in range(w):
                px[x, y] = c + (255,)
        put = _putter(px, w, h)
        if detail:
            detail(face, put, w, h, c)
        if alpha:
            alpha(face, px, w, h)
        if outline and w >= 3 and h >= 3:
            ln = (line or ink(base)) + (255,)
            for x in range(w):
                for y in (0, h - 1):
                    if px[x, y][3]:
                        px[x, y] = ln
            for y in range(h):
                for x in (0, w - 1):
                    if px[x, y][3]:
                        px[x, y] = ln
    return p


def stripes(rows, col, faces=("north", "south", "east", "west")):
    """Horizontal bands at fractions of the height."""
    def d(face, put, w, h, c):
        if face not in faces:
            return
        for (a, b) in rows:
            for y in range(int(h * a), max(int(h * a) + 1, int(h * b))):
                for x in range(w):
                    put(x, y, col if face in ("north", "east") else cel(col))
    return d


def chain(*ds):
    def d(face, put, w, h, c):
        for f in ds:
            if f:
                f(face, put, w, h, c)
    return d


# ------------------------------------------------------------------ face (64 px wide)
def _ellipse(cx, cy, rx, ry, x, y):
    return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2


def draw_eye(put, cx, cy, k, side, expr):
    """side = -1 for the eye on the viewer's left, +1 on the right; k = face kind dict."""
    lash = (24, 16, 22)
    outer = cx - 7 if side < 0 else cx + 7
    if expr == "blink":
        for x in range(cx - 7, cx + 8):
            t = (x - cx) / 7.0
            y = cy + 2 + int(round(2 * (1 - t * t)))
            put(x, y, lash); put(x, y + 1, lash)
        put(outer, cy + 1, lash); put(outer + side, cy, lash)
        return
    if expr == "hurt":
        inner = cx + 4 if side < 0 else cx - 4
        o = cx - 6 if side < 0 else cx + 6
        pts = []
        for i in range(11):
            t = i / 10
            pts.append((o + (inner - o) * t, cy - 4 + 5 * t))
        for i in range(11):
            t = i / 10
            pts.append((inner + (o - inner) * t, cy + 1 + 5 * t))
        for x, y in pts:
            put(round(x), round(y), lash); put(round(x), round(y) + 1, lash)
        return
    # sclera
    for y in range(cy - 5, cy + 7):
        for x in range(cx - 8, cx + 9):
            if _ellipse(cx, cy + 0.6, 7.6, 6.4, x, y) < 1:
                put(x, y, (252, 252, 252))
    iris, irl, ird = k["iris"], hi(k["iris"], 0.4), M.dark(k["iris"], 0.55)
    icx = cx + side * 0.5
    for y in range(cy - 5, cy + 7):
        for x in range(cx - 6, cx + 7):
            e = _ellipse(icx, cy + 1, 4.8, 5.8, x, y)
            if e < 1 and _ellipse(cx, cy + 0.6, 7.6, 6.4, x, y) < 1:
                rel = (y - (cy - 5)) / 11.0
                col = ird if rel < 0.32 else (iris if rel < 0.72 else irl)
                if e > 0.72:
                    col = M.dark(iris, 0.45)
                put(x, y, col)
    pup = k.get("pupil", "round")
    pc = (16, 10, 20)
    if pup == "round":
        for y in range(cy - 2, cy + 5):
            for x in range(cx - 3, cx + 4):
                if _ellipse(icx, cy + 1.2, 2.2, 3.0, x, y) < 1:
                    put(x, y, pc)
    if pup in ("slit", "cross"):
        for y in range(cy - 4, cy + 7):
            put(round(icx), y, pc)
            if abs(y - (cy + 1)) < 3:
                put(round(icx) - 1, y, pc)
    if pup in ("bar", "cross"):
        for x in range(round(icx) - 3, round(icx) + 4):
            put(x, cy + 1, pc)
            if abs(x - icx) < 2.5:
                put(x, cy + 2, pc)
    # catchlights: one light source, same side in both eyes
    for dx in range(3):
        for dy in range(3):
            if (dx, dy) != (2, 2):
                put(icx - 3 + dx, cy - 3 + dy, (255, 255, 255))
    put(icx + 2, cy + 4, (236, 244, 255)); put(icx + 3, cy + 4, (236, 244, 255))
    # lashes: heavy upper line flicking out at the outer corner, light lower line
    for x in range(cx - 7, cx + 8):
        t = (x - cx) / 7.0
        y = cy - 6 + int(round(1.2 * t * t))
        put(x, y, lash); put(x, y + 1, lash)
        if k.get("heavy"):
            put(x, y - 1, lash)
    put(outer, cy - 4, lash); put(outer + side, cy - 5, lash); put(outer + 2 * side, cy - 6, lash)
    for x in range(cx - 2, cx + 6) if side < 0 else range(cx - 5, cx + 3):
        xx = x if side < 0 else x
        put(xx if side > 0 else 2 * cx - xx, cy + 7, M.dark(SKIN, 0.62))


def skull_paint(k):
    """Upper head: hair cap, forehead, eyes (brows under the headband or visible), sides with hair."""
    hc = k["hair"]
    skin = k.get("skin", SKIN)

    def p(face, img):
        if face == "north" and img.size != (60, 40):  # drawn on the 60x40 design grid, scaled to this head
            tmp = Image.new("RGBA", (60, 40), (0, 0, 0, 0))
            p(face, tmp)
            img.paste(tmp.resize(img.size, Image.NEAREST), (0, 0))
            return
        w, h = img.size
        px = img.load()
        put = _putter(px, w, h)
        expr = M.EXPR
        if face in ("up",):
            toon(hc)(face, img)
            return
        if face == "down":
            toon(skin)(face, img)
            return
        base = skin if face != "west" else cel(skin)
        hb = hc if face != "west" else cel(hc)
        for y in range(h):
            for x in range(w):
                px[x, y] = base + (255,)
        if face == "south":
            for y in range(h):
                for x in range(w):
                    px[x, y] = cel(hc) + (255,)
        elif face in ("east", "west"):
            for y in range(h):
                for x in range(w):
                    # hair over the top and back; the sideburn comes down in front of the ear
                    back = x > w * 0.45 if face == "east" else x < w * 0.55
                    if y < h * 0.42 or (back and y < h * 0.92) or (abs(x - w / 2) < w * 0.08 and y < h * 0.7):
                        px[x, y] = hb + (255,)
        else:  # north: the face
            for y in range(h):
                for x in range(w):
                    if y < 12:
                        px[x, y] = hc + (255,)
            if k.get("pigment"):
                for cx, side in ((17, -1), (43, 1)):
                    for y in range(16, 31):
                        for x in range(cx - 11, cx + 12):
                            outer = (x - cx) * side
                            if _ellipse(cx + side * 1.5, 23, 11, 7.5, x, y) < 1 and (y < 24 or outer > 4):
                                put(x, y, k["pigment"])
            if k.get("brows"):
                bc = M.dark(hc, 0.55)
                for cx, s in ((17, -1), (43, 1)):
                    for i in range(-7, 8):
                        y = 18 - (1 if abs(i) < 3 else 0)
                        if expr == "shout":
                            y = 17 + (i * -s) // 4
                        put(cx + i, y, bc); put(cx + i, y + 1, bc)
            for cx, side in ((17, -1), (43, 1)):
                draw_eye(put, cx, 28, k, side, expr)
            if k.get("fox"):  # thick dark rims of the Nine-Tails' eyes
                for cx in (17, 43):
                    for x in range(cx - 8, cx + 9):
                        put(x, 21, (24, 10, 12))
        # ink border
        ln = ink(skin) + (255,)
        for x in range(w):
            px[x, 0] = ln if face != "north" else px[x, 0]
            px[x, h - 1] = ln if face not in ("north",) else px[x, h - 1]
        for y in range(h):
            px[0, y] = ln
            px[w - 1, y] = ln
    return p


def jaw_paint(k):
    """Lower face: nose, whiskers, mouth (expressions), chin shading."""
    skin = k.get("skin", SKIN)

    def p(face, img):
        if face == "north" and img.size != (52, 22):
            tmp = Image.new("RGBA", (52, 22), (0, 0, 0, 0))
            p(face, tmp)
            img.paste(tmp.resize(img.size, Image.NEAREST), (0, 0))
            return
        w, h = img.size
        px = img.load()
        put = _putter(px, w, h)
        expr = M.EXPR
        if face != "north":
            toon(skin)(face, img)
            if face == "south":
                for y in range(int(h * 0.5)):
                    for x in range(1, w - 1):
                        put(x, y, cel(k["hair"]))
            return
        for y in range(h):
            for x in range(w):
                px[x, y] = skin + (255,)
        cx = w // 2
        sh = M.dark(skin, 0.82)
        ln = (40, 22, 26)
        # nose: a small shadow and tip
        put(cx + 1, 2, sh); put(cx + 1, 3, sh); put(cx, 4, M.dark(skin, 0.7)); put(cx + 1, 4, M.dark(skin, 0.7))
        # whiskers: three on each cheek
        wc = k.get("whisker", (70, 44, 40))
        thick = k.get("fox", False)
        for y0, slope in ((4, -0.22), (8, 0.0), (12, 0.22)):
            for j in range(10):
                y = round(y0 + j * slope)
                for s in (-1, 1):
                    x = cx + s * (13 + j)
                    put(x, y, wc)
                    if thick or j < 7:
                        put(x, y + 1, wc if thick else M.mix(wc, skin, 0.45))
        # mouth
        m = k.get("mouth", "smile")
        if expr == "shout":
            for y in range(7, 18):
                for x in range(cx - 7, cx + 8):
                    e = _ellipse(cx, 12, 7.5, 5.8, x, y)
                    if e < 1:
                        put(x, y, ln if e > 0.75 else ((150, 40, 50) if y > 13 else (90, 18, 30)))
            for x in range(cx - 5, cx + 6):
                put(x, 8, (250, 250, 250))
            if thick:
                put(cx - 4, 9, (250, 250, 250)); put(cx + 4, 9, (250, 250, 250))
        elif expr in ("hurt",):
            for x in range(cx - 7, cx + 8):
                put(x, 10, ln); put(x, 14, ln)
                for y in (11, 12, 13):
                    put(x, y, (248, 248, 248) if (x - cx) % 3 else (180, 180, 188))
            for y in range(10, 15):
                put(cx - 8, y, ln); put(cx + 8, y, ln)
        elif m == "grin":  # kid Naruto's huge grin
            for x in range(cx - 8, cx + 9):
                t = (x - cx) / 8.0
                y = 10 + int(round(3 * (1 - t * t)))
                put(x, 10, ln)
                for yy in range(11, y):
                    put(x, yy, (248, 248, 248) if yy < 12 else (150, 40, 50))
                put(x, y, ln)
            put(cx - 9, 9, ln); put(cx + 9, 9, ln)
        else:
            for x in range(cx - 5, cx + 6):
                t = (x - cx) / 5.0
                put(x, 12 - int(round(1.2 * t * t)), ln)
            if m == "fang":
                put(cx + 3, 12, (250, 250, 250)); put(cx + 3, 13, (250, 250, 250))
        for x in range(cx - 6, cx + 7):  # chin shadow
            put(x, h - 2, sh)
        for x in range(w):
            put(x, h - 1, ink(skin))
        for y in range(h):
            put(0, y, ink(skin)); put(w - 1, y, ink(skin))
    return p


# ------------------------------------------------------------------ geometry helpers
def mx(x0, width, s):
    return x0 if s > 0 else -(x0 + width)


def LEG(s):
    return "rightLeg" if s > 0 else "leftLeg"


def SHIN(s):
    return "rightShin" if s > 0 else "leftShin"


def ARM(s):
    return "rightArm" if s > 0 else "leftArm"


def FORE(s):
    return "rightForearm" if s > 0 else "leftForearm"


def head(m, k, band=None):
    m.box("head", [-3.75, 28, -3.75], [7.5, 5, 7.5], skull_paint(k))       # FIRST cube: the egg icon is cut from it
    m.box("head", [-3.25, 25.2, -3.45], [6.5, 2.8, 6.6], jaw_paint(k))
    m.box("head", [-1.75, 24.9, -3.25], [3.5, 0.5, 3.0], toon(k.get("skin", SKIN)))
    for s in (1, -1):
        m.box("head", [mx(3.6, 0.55, s), 27.3, -0.7], [0.55, 1.9, 1.3], toon(k.get("skin", SKIN)))
    if band:
        cloth, tails = band
        m.box("head", [-3.95, 30.4, -3.95], [7.9, 1.55, 7.9], toon(cloth))
        m.box("head", [-2.55, 30.15, -4.25], [5.1, 2.05, 0.35], toon(METAL, detail=leaf_symbol, line=(90, 94, 104)))
        if tails:
            for s in (1, -1):
                m.strand([s * 0.8, 31.0, 4.0], [s * 0.35, -1, 0.9], 6.5, 1.2, toon(cloth), bone="hair", segs=3, thick=0.25,
                         bend=(s * 0.05, 0, 0.12))


def leaf_symbol(face, put, w, h, c):
    """Hidden Leaf mark engraved on the forehead plate: a spiral with a point."""
    if face != "north":
        return
    ln = (70, 74, 86)
    cx, cy = w * 0.47, h * 0.52
    for i in range(70):
        a = i / 70 * math.pi * 2 * 1.35
        r = 1.0 + i / 70 * h * 0.33
        put(cx + math.cos(a) * r, cy + math.sin(a) * r, ln)
    for i in range(7):
        put(cx + h * 0.33 + i * 0.8, cy - h * 0.33 + i * 0.3, ln)
    for x in range(3, w - 3):  # rivets / bevel
        put(x, 2, hi(METAL, 0.5))


def neck(m, paint):
    m.box("body", [-1.0, 24.0, -1.0], [2.0, 1.4, 2.0], paint)


def torso(m, chest, waist, hips):
    m.box("body", [-3.6, 19.0, -1.85], [7.2, 5.0, 3.7], chest)
    m.box("body", [-2.8, 15.2, -1.55], [5.6, 3.8, 3.1], waist)
    m.box("body", [-3.1, 12.6, -1.7], [6.2, 2.6, 3.4], hips)


def arms(m, upper, fore, hand):
    for s in (1, -1):
        m.box(ARM(s), [mx(3.55, 2.25, s), 18.2, -1.125], [2.25, 5.8, 2.25], upper)
        m.box(FORE(s), [mx(3.6, 2.1, s), 13.9, -1.05], [2.1, 4.35, 2.1], fore)
        m.box(FORE(s), [mx(3.5, 2.3, s), 11.7, -1.2], [2.3, 2.25, 2.4], hand)


def legs(m, thigh, shin, foot):
    for s in (1, -1):
        m.box(LEG(s), [mx(0.25, 3.0, s), 7.0, -1.5], [3.0, 6.0, 3.0], thigh)
        m.box(SHIN(s), [mx(0.375, 2.75, s), 1.5, -1.375], [2.75, 5.55, 2.75], shin)
        m.box(SHIN(s), [mx(0.25, 3.0, s), 0.0, -2.45], [3.0, 1.5, 3.95], foot)


def sandal(col, skin=SKIN):
    """Open-toed shinobi sandal: sole and straps in colour, toes showing at the front."""
    def d(face, put, w, h, c):
        if face == "north":
            for y in range(int(h * 0.6)):
                for x in range(1, w - 1):
                    put(x, y, skin if (x % 5) else M.dark(skin, 0.8))
        if face == "up":
            for y in range(int(h * 0.42)):
                for x in range(1, w - 1):
                    put(x, y, skin if (x % 5) else M.dark(skin, 0.8))
            for x in range(1, w - 1):
                put(x, int(h * 0.42), M.dark(col, 0.7))
    return toon(col, detail=d)


def hand_paint(skin=SKIN):
    def d(face, put, w, h, c):
        if face == "north":  # knuckles
            for x in range(2, w - 2, 4):
                put(x, int(h * 0.3), M.dark(c, 0.78))
    return toon(skin, detail=d)


def zipper(col):
    def d(face, put, w, h, c):
        if face == "north":
            for y in range(h):
                put(w // 2, y, col)
                if y % 3 == 0:
                    put(w // 2 - 1, y, M.dark(col, 0.8))
    return d


def uzumaki_spiral(col, faces=("south",), r=0.32, cy=0.45):
    """The Uzumaki clan swirl."""
    def d(face, put, w, h, c):
        if face not in faces:
            return
        cx, cyy = w / 2, h * cy
        R = min(w, h) * r
        for i in range(160):
            a = i / 160 * math.pi * 2 * 2.2
            rr = R * (i / 160)
            for t in (0, 0.6):
                put(cx + math.cos(a) * (rr + t), cyy + math.sin(a) * (rr + t), col)
        for i in range(90):
            a = i / 90 * math.pi * 2
            put(cx + math.cos(a) * R, cyy + math.sin(a) * R, col)
    return d


def spike(m, base, d, length, width, col, thick=None, bone="hair"):
    """A broad anime hair spike: a wide base plate and a narrow tip, softly outlined, lighter at the root."""
    d = M.norm(d)
    rot = M._rot_for(d)
    t = thick if thick is not None else max(0.75, width * 0.45)
    soft = M.dark(col, 0.72)

    def grad(face, put, w, h, c):
        if face in ("north", "south", "east", "west"):
            for y in range(h):
                for x in range(w):
                    if x > w * 0.62:
                        put(x, y, cel(col) if face in ("north", "east") else M.dark(cel(col), 0.95))
            for y in range(int(h * 0.15), int(h * 0.75)):
                put(int(w * 0.28), y, hi(col, 0.55))
    paint = toon(col, detail=grad, line=soft)
    L1, L2 = length * 0.62, length * 0.5
    b = list(base)
    m.box(bone, [b[0] - width / 2, b[1], b[2] - t / 2], [width, L1, t], paint, rot=rot, pivot=[round(v, 3) for v in b])
    p2 = [b[i] + d[i] * L1 * 0.9 for i in range(3)]
    w2 = max(0.5, width * 0.55)
    m.box(bone, [p2[0] - w2 / 2, p2[1], p2[2] - t * 0.4], [w2, L2 * 0.8, t * 0.8], paint, rot=rot, pivot=[round(v, 3) for v in p2])
    p3 = [p2[i] + d[i] * L2 * 0.7 for i in range(3)]           # the point
    w3 = max(0.375, width * 0.22)
    m.box(bone, [p3[0] - w3 / 2, p3[1], p3[2] - t * 0.25], [w3, L2 * 0.6, max(0.375, t * 0.5)], paint, rot=rot, pivot=[round(v, 3) for v in p3])


def hair_strands(m, col, style):
    """Naruto's spiky hair. style: kid / teen / war / adult; horns=True adds the Nine-Tails 'horn' tufts."""
    # a full hair cap over the skull, then broad spikes
    m.box("hair", [-4.0, 31.9, -4.0], [8.0, 1.9, 8.0], toon(col, line=M.dark(col, 0.72)))
    m.box("hair", [-4.0, 27.6, -0.6], [8.0, 4.4, 4.6], toon(col, line=M.dark(col, 0.72)))   # back and sides
    short = style == "adult"
    L = 0.62 if short else 1.0
    # crown: big spikes fanning up and out (Naruto's silhouette)
    crown = [(0, -2.2, 0.0, 6.2), (2.2, -1.4, 0.45, 5.8), (-2.2, -1.4, -0.45, 5.8), (3.0, 1.0, 0.9, 5.4),
             (-3.0, 1.0, -0.9, 5.4), (1.4, 2.6, 0.3, 5.2), (-1.4, 2.6, -0.3, 5.2)]
    for x, z, lean, ln in crown:
        spike(m, [x, 33.2, z], [lean, 1.0, z * 0.18], ln * L, 3.0, col)
    # back spikes, down and out
    for x in (-2.4, 0.0, 2.4):
        spike(m, [x, 31.6, 3.4], [x * 0.18, -0.5, 1], 4.8 * L, 3.0, col)
    # bangs: up-swept above the headband (Part I / Shippuden), short fringe on the adult
    for x, tilt in ((-2.5, -0.25), (-0.8, -0.05), (0.9, 0.08), (2.5, 0.25)):
        if style in ("teen", "war", "kid"):
            spike(m, [x, 32.4, -3.8], [tilt, 0.85, -0.6], 3.4 * L, 2.2, col, thick=0.7)
        else:
            spike(m, [x, 32.9, -3.7], [tilt, -0.45, -0.7], 2.6, 2.0, col, thick=0.7)
    # side bangs framing the face: long in Shippuden, short as a kid or an adult
    side_len = {"kid": 3.0, "teen": 5.2, "war": 5.2, "adult": 2.4}[style]
    for s in (1, -1):
        spike(m, [s * 3.7, 31.4, -3.0], [s * 0.1, -1, -0.12], side_len, 1.8, col, thick=0.6)
        spike(m, [s * 3.9, 31.6, -0.4], [s * 0.7, -0.35, 0.25], 3.6 * L, 2.4, col)


def horns(m, col, length=5.0):
    for s in (1, -1):
        spike(m, [s * 1.9, 33.6, -0.6], [s * 0.22, 1, 0.05], length, 2.6, col)


def chakra_shell(col, holes=True):
    """Version-1 cloak skin: bubbling red chakra, see-through in the middle (alpha-tested holes)."""
    def alpha(face, px, w, h):
        if not holes or w < 6 or h < 6:
            return
        for y in range(2, h - 2):
            for x in range(2, w - 2):
                n = (x * 7 + y * 11) % 13
                if not (x < 3 or y < 3 or x > w - 4 or y > h - 4) and n not in (0, 1):
                    px[x, y] = (0, 0, 0, 0)
    return toon(col, alpha=alpha, line=M.dark(col, 0.55))


# ------------------------------------------------------------------ the four Narutos
FACE = {
    "kid": dict(hair=HAIR, iris=(46, 120, 230), mouth="grin"),
    "kid_cloak": dict(hair=HAIR, iris=(220, 30, 30), pupil="slit", mouth="fang", fox=True, whisker=(60, 10, 14), heavy=True),
    "teen": dict(hair=HAIR, iris=(46, 120, 230), mouth="smile"),
    "sage": dict(hair=HAIR, iris=(246, 206, 46), pupil="bar", pigment=(236, 104, 30), mouth="smile"),
    "kcm": dict(hair=GOLD, skin=GOLD, iris=(255, 120, 20), pupil="slit", fox=True, whisker=(30, 18, 10), heavy=True, mouth="smile"),
    "spsm": dict(hair=GOLD, skin=GOLD, iris=(250, 170, 50), pupil="cross", pigment=(240, 120, 30), fox=True, whisker=(30, 18, 10), mouth="smile"),
    "adult": dict(hair=HAIR, iris=(46, 120, 230), mouth="smile", brows=True),
    "baryon": dict(hair=HAIR, iris=(255, 90, 40), pupil="slit", fox=True, whisker=(60, 12, 14), heavy=True, brows=True, mouth="smile"),
}


def kid(m, cloak=False):
    k = FACE["kid_cloak" if cloak else "kid"]
    head(m, k, band=(BLUE_P1, False))
    hair_strands(m, HAIR, "kid")
    orange = ORANGE
    neck(m, toon(SKIN))
    # Part I jumpsuit: orange with navy shoulders, white fur collar, swirl on the back
    chest = toon(orange, detail=chain(stripes([(0, 0.3)], BLUE_P1), zipper((236, 236, 236)), uzumaki_spiral(RED)))
    torso(m, chest, toon(orange, detail=zipper((236, 236, 236))), toon(orange))
    m.box("body", [-3.2, 23.2, -2.3], [6.4, 1.6, 4.6], toon(WHITE, line=(150, 150, 150)))          # white collar
    arms(m, toon(orange, detail=stripes([(0, 0.25)], BLUE_P1)), toon(orange, detail=stripes([(0.85, 1)], WHITE)), hand_paint())
    legs(m, toon(orange), toon(orange, detail=stripes([(0.75, 0.9)], WHITE)), sandal(BLUE_P1))
    m.box("rightLeg", [3.05, 9.2, -1.0], [0.6, 1.8, 2.0], toon(BLUE_P1))                            # kunai holster
    m.box("rightLeg", [0.2, 10.4, -1.55], [3.1, 0.6, 3.1], toon(WHITE))                            # bandage
    if cloak:  # Version 1: a red chakra skin over everything, fox ears and one tail
        red = (226, 66, 34)
        sh = chakra_shell(red)
        m.box("body", [-3.85, 12.3, -2.1], [7.7, 12.1, 4.2], sh)
        for s in (1, -1):
            m.box(ARM(s), [mx(3.35, 2.65, s), 18.0, -1.35], [2.65, 6.2, 2.7], sh)
            m.box(FORE(s), [mx(3.35, 2.6, s), 11.4, -1.35], [2.6, 7.0, 2.7], sh)
            m.box(LEG(s), [mx(0.05, 3.4, s), 6.8, -1.7], [3.4, 6.4, 3.4], sh)
            m.box(SHIN(s), [mx(0.1, 3.3, s), -0.1, -2.6], [3.3, 7.3, 4.3], sh)
            m.strand([s * 2.3, 32.6, -0.5], [s * 0.3, 1, 0.1], 3.6, 2.4, toon(red, line=M.dark(red, 0.5)), bone="hair", segs=2, thick=0.6)
        m.box("head", [-4.15, 24.7, -4.15], [8.3, 9.0, 8.3], chakra_shell(red))
        m.strand([0, 13.8, 2.0], [0, 0.5, 1], 11, 3.4, toon(red, line=M.dark(red, 0.5)), bone="tail", segs=3, thick=1.0, bend=(0, 0.25, -0.1))


def teen_outfit(m, k):
    head(m, k, band=(BLACK, True))
    hair_strands(m, k["hair"], "teen")
    neck(m, toon(BLACK))
    chest = toon(ORANGE, detail=chain(stripes([(0, 0.55)], BLACK), zipper((200, 200, 206)), uzumaki_spiral(RED, faces=("south",), r=0.3, cy=0.7)))
    torso(m, chest, toon(ORANGE, detail=zipper((200, 200, 206))), toon(ORANGE))
    m.box("body", [-1.9, 23.3, -2.15], [3.8, 2.0, 4.3], toon(BLACK, detail=zipper((200, 200, 206))))   # high collar
    arms(m, toon(ORANGE, detail=stripes([(0, 0.35)], BLACK)), toon(ORANGE), hand_paint())
    legs(m, toon(ORANGE), toon(ORANGE, detail=stripes([(0.78, 0.95)], WHITE)), sandal(BLACK))
    m.box("rightLeg", [3.05, 9.2, -1.0], [0.6, 1.8, 2.0], toon(BLACK))
    m.box("rightLeg", [0.2, 10.4, -1.55], [3.1, 0.6, 3.1], toon(WHITE))


def flame_hem(col):
    """Black flame pattern licking up from the hem (Sage cloak / Hokage cloak style)."""
    def d(face, put, w, h, c):
        if face not in ("north", "south", "east", "west"):
            return
        for x in range(w):
            t = (x % 10) / 10.0
            top = int(h * (0.78 - 0.22 * abs(math.sin(t * math.pi))))
            for y in range(top, h):
                put(x, y, col)
    return d


def sage_cloak(m):
    red = (204, 44, 40)
    cl = toon(red, detail=flame_hem(BLACK))
    m.box("cape", [-3.9, 8.0, 1.85], [7.8, 16.0, 0.5], cl)
    for s in (1, -1):
        m.box("body", [mx(1.4, 2.45, s), 8.5, -2.25], [2.45, 15.6, 0.45], cl)   # open front panels
        m.box(ARM(s), [mx(3.35, 2.75, s), 19.6, -1.5], [2.75, 4.6, 3.0], cl)   # short wide sleeves
    m.box("body", [-4.0, 22.6, -2.1], [8.0, 1.8, 4.3], toon(red))
    m.box("body", [-4.6, 14.0, 2.4], [9.2, 2.2, 2.2], toon(WHITE, detail=stripes([(0.0, 0.25), (0.75, 1)], (180, 40, 40))))  # big scroll


def kcm_body(m, k, coat=False, hair_style="war", band=True):
    """Nine-Tails Chakra Mode: the whole body is golden chakra with black seal markings."""
    g = GOLD
    mark = (28, 18, 12)
    head(m, k, band=((60, 40, 20), True) if band else None)
    hair_strands(m, g, hair_style)
    horns(m, g, 4.2)
    neck(m, toon(g))

    def seals(face, put, w, h, c):
        if face == "north":
            for i in range(6):  # the six magatama around the collar
                a = math.pi * (0.15 + 0.7 * i / 5)
                x, y = w / 2 + math.cos(a) * w * 0.36, h * 0.1 + math.sin(a) * h * 0.25
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        put(x + dx, y + dy, mark)
            for y in range(int(h * 0.3), h):
                put(w * 0.35, y, mark); put(w * 0.65, y, mark)
    def belly(face, put, w, h, c):
        if face == "north":
            uzumaki_spiral(mark, faces=("north",), r=0.36, cy=0.5)(face, put, w, h, c)
    chest = toon(g, detail=seals, line=(150, 90, 10))
    torso(m, chest, toon(g, detail=belly, line=(150, 90, 10)), toon(g, line=(150, 90, 10)))
    lines = stripes([(0.0, 0.0)], mark)
    def leg_lines(face, put, w, h, c):
        if face == "north":
            for y in range(h):
                put(w // 2, y, mark)
    arms(m, toon(g, line=(150, 90, 10)), toon(g, detail=stripes([(0.7, 0.85)], mark), line=(150, 90, 10)),
         toon(g, detail=stripes([(0.6, 1.0)], mark), line=(150, 90, 10)))
    legs(m, toon(g, detail=leg_lines, line=(150, 90, 10)), toon(g, detail=leg_lines, line=(150, 90, 10)),
         toon(g, detail=stripes([(0.0, 0.4)], mark), line=(150, 90, 10)))
    if coat:  # Kurama Mode / Six Paths: a flared coat with flame-tipped tails
        cl = toon(hi(g, 0.15), detail=flame_hem(mark), line=(150, 90, 10))
        m.box("cape", [-4.0, 7.0, 1.85], [8.0, 17.0, 0.5], cl)
        for s in (1, -1):
            m.box("body", [mx(1.5, 2.45, s), 7.5, -2.3], [2.45, 16.6, 0.45], cl)
            m.box(ARM(s), [mx(3.35, 2.75, s), 18.6, -1.45], [2.75, 5.0, 2.9], cl)
    return mark


def spsm_extras(m, mark):
    # the six magatama on the collar and Truth-Seeking Balls floating behind
    m.box("body", [-3.9, 22.4, -2.15], [7.8, 1.9, 4.3], toon(GOLD, detail=lambda f, put, w, h, c: [put(x, h // 2, (20, 14, 10)) for x in range(2, w - 2) if (x // 3) % 2 == 0] if f == "north" else None))
    black = (20, 18, 24)
    for i in range(9):
        a = math.pi * (0.1 + 0.8 * i / 8)
        x, y = math.cos(a) * 5.2, 21 + math.sin(a) * 5.2
        m.box("orbs", [x - 0.8, y - 0.8, 4.0], [1.6, 1.6, 1.6], toon(black, detail=lambda f, put, w, h, c: put(2, 2, (120, 120, 140)), line=(4, 4, 6)))


def adult_outfit(m, k, cloak=True):
    head(m, k, band=None)
    hair_strands(m, k["hair"], "adult")
    neck(m, toon(BLACK))
    chest = toon(ORANGE, detail=chain(zipper((40, 40, 46)), stripes([(0.0, 0.08)], BLACK)))
    torso(m, chest, toon(ORANGE, detail=zipper((40, 40, 46))), toon(ORANGE, detail=stripes([(0.2, 0.42), (0.6, 0.82)], BLACK)))
    m.box("body", [-2.0, 23.4, -2.1], [4.0, 1.6, 4.2], toon(BLACK))
    arms(m, toon(ORANGE), toon(ORANGE, detail=stripes([(0.45, 0.6), (0.72, 0.87)], BLACK)), hand_paint())
    legs(m, toon(BLACK), toon(BLACK, detail=stripes([(0.4, 0.5), (0.62, 0.72)], (70, 70, 80))), sandal((30, 30, 36)))
    if cloak:  # the Seventh Hokage's white cloak, red lining, 七代目火影 down the back
        def kanji(face, put, w, h, c):
            if face == "south":
                red = (200, 30, 30)
                for i in range(5):
                    y0 = int(h * (0.12 + i * 0.15))
                    for x in range(w // 2 - 4, w // 2 + 5):
                        put(x, y0, red)
                    for y in range(y0, y0 + int(h * 0.1)):
                        put(w // 2 + (1 if i % 2 else -1) * 2, y, red)
            if face == "north":
                for y in range(1, h - 1):
                    for x in range(1, w - 1):
                        put(x, y, (180, 30, 34))
        cl = toon(WHITE, detail=kanji, line=(150, 150, 156))
        m.box("cape", [-4.2, 4.5, 1.9], [8.4, 19.6, 0.5], cl)
        m.box("body", [-4.5, 22.7, -2.2], [9.0, 1.8, 4.6], toon(WHITE, line=(150, 150, 156)))
        for s in (1, -1):
            m.box("body", [mx(5.85, 0.6, s), 7.0, -1.6], [0.6, 16.8, 3.8], toon(WHITE, line=(150, 150, 156)))   # drapes over the arms


def baryon_extras(m):
    red = (214, 34, 40)
    deep = (150, 14, 24)
    hood = toon(red, line=deep)
    m.box("head", [-4.5, 27.0, -1.4], [9.0, 7.6, 6.2], hood)             # chakra hood around the back of the head
    m.box("cape", [-4.6, 3.5, 1.9], [9.2, 21.0, 0.5], toon(red, detail=flame_hem(deep), line=deep))
    m.box("body", [-4.6, 22.4, -2.3], [9.2, 2.2, 4.6], hood)
    for s in (1, -1):  # the horn-like flames: two tall over the head, two from the shoulders
        m.strand([s * 1.8, 34.0, -0.5], [s * 0.2, 1, 0.05], 10, 2.6, toon(red, line=deep), bone="hair", segs=3, thick=0.6, bend=(s * -0.04, 0, 0))
        m.strand([s * 4.2, 24.0, 1.5], [s * 0.45, 1, 0.3], 11, 3.0, toon(red, line=deep), bone="cape", segs=3, thick=0.5, bend=(s * -0.05, 0, 0))
        m.strand([s * 4.0, 18.0, 2.0], [s * 0.8, 0.7, 0.4], 9, 2.8, toon(red, line=deep), bone="cape", segs=3, thick=0.5, bend=(s * -0.06, 0.02, 0))


FORMS2 = {
    "naruto_kid": ["base", "cloak"],
    "naruto_teen": ["base", "sage"],
    "naruto_war": ["kcm", "kurama", "spsm"],
    "naruto_adult": ["hokage", "link", "baryon"],
}


def build(char, form):
    m = M.Model()
    m.bones = BONES2
    m.S = S2
    if char == "naruto_kid":
        kid(m, cloak=form == "cloak")
        f, P = 1.2, (0.0, 25.2, 0.0)   # kid proportions: head and hair 20% bigger around the neck
        for c in m.cubes:
            if c["bone"] in ("head", "hair", "hat"):
                c["frm"] = [P[i] + (c["frm"][i] - P[i]) * f for i in range(3)]
                c["size"] = [round(v * f * 8) / 8 for v in c["size"]]
                if c["pivot"]:
                    c["pivot"] = [round(P[i] + (c["pivot"][i] - P[i]) * f, 3) for i in range(3)]
    elif char == "naruto_teen":
        teen_outfit(m, FACE["sage" if form == "sage" else "teen"])
        if form == "sage":
            sage_cloak(m)
    elif char == "naruto_war":
        k = FACE["spsm" if form == "spsm" else "kcm"]
        mark = kcm_body(m, k, coat=form != "kcm")
        if form == "spsm":
            spsm_extras(m, mark)
    elif char == "naruto_adult":
        if form == "link":
            kcm_body(m, dict(FACE["kcm"], brows=True), coat=True, hair_style="adult", band=False)
        else:
            adult_outfit(m, FACE["baryon" if form == "baryon" else "adult"], cloak=form == "hokage")
            if form == "baryon":
                baryon_extras(m)
    return m
