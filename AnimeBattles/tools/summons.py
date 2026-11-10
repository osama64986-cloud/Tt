"""Giant summons that appear during the big techniques: Sasuke's Perfect Susanoo, Naruto's Kurama avatar
and Gamabunta. Built small (about 40 units) with the house painters and scaled up in game by `ab:size`."""
import math

import models as M
from models import dark, layered, light, lines, solid, SIDES, _put

# bones in geometry space (x is mirrored on export, so +x in the model is -x here)
BONES = [
    {"name": "root", "pivot": [0, 0, 0]},
    {"name": "body", "parent": "root", "pivot": [0, 12, 0]},
    {"name": "head", "parent": "body", "pivot": [0, 26, 0]},
    {"name": "rightArm", "parent": "body", "pivot": [-9, 24, 0]},
    {"name": "leftArm", "parent": "body", "pivot": [9, 24, 0]},
    {"name": "rightWing", "parent": "body", "pivot": [-4, 22, 4]},
    {"name": "leftWing", "parent": "body", "pivot": [4, 22, 4]},
    {"name": "tails", "parent": "body", "pivot": [0, 16, 12]},
]


def alpha(painter, a):
    """Chakra constructs are see-through: keep the painted colours, lower the opacity."""
    def p(face, img):
        painter(face, img)
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, al = px[x, y]
                if al:
                    px[x, y] = (r, g, b, min(al, a))
    return p


def rim(col, edge):
    def f(face, px, w, h, base):
        for y in range(h):
            for x in range(w):
                if x in (0, w - 1) or y in (0, h - 1):
                    _put(px, w, h, x, y, edge)
    return f


def plates(col):
    def f(face, px, w, h, base):
        if face in ("up", "down"):
            return
        for y in range(0, h, max(3, h // 4)):
            for x in range(w):
                _put(px, w, h, x, y, dark(col, 0.65))
    return f


# ------------------------------------------------------------------ Perfect Susanoo
def susanoo():
    m = M.Model()
    m.bones = BONES
    pur, glow = (150, 84, 230), (226, 196, 255)
    armour = alpha(layered(pur, [plates(pur), rim(pur, glow)]), 200)
    bright = alpha(layered(light(pur, 0.2), [rim(pur, glow)]), 220)
    m.box("body", [-6.5, 0, -4.5], [13, 12, 9], armour)                      # armoured skirt
    m.box("body", [-7.5, 12, -5], [15, 14, 10], armour)                      # breastplate
    m.box("body", [-3, 18, -5.6], [6, 6, 0.8], alpha(solid(glow), 230))       # the glowing core
    for s in (1, -1):
        m.box("body", [s * 9.5 - 3, 23, -5.5], [6, 4, 11], bright)            # pauldrons
    m.box("head", [-4, 26, -4.5], [8, 8, 9], armour)                         # helmet
    m.box("head", [-0.8, 28.5, -8.5], [1.6, 1.6, 4.2], bright)               # the tengu nose
    m.box("head", [-3.2, 30.2, -4.8], [2.4, 0.8, 0.6], alpha(solid((255, 240, 255)), 255))   # eye slits
    m.box("head", [0.8, 30.2, -4.8], [2.4, 0.8, 0.6], alpha(solid((255, 240, 255)), 255))
    for s in (1, -1):  # the crescent crest
        m.strand([s * 2.2, 33.5, -4.0], [s * 0.7, 1, -0.4], 7, 2.0, bright, bone="head", segs=3, thick=0.5, bend=(-s * 0.25, 0, -0.1))
    m.box("rightArm", [7.5, 13, -2.5], [4, 12, 5], armour)
    m.box("leftArm", [-11.5, 13, -2.5], [4, 12, 5], armour)
    # the sword: a long blade of chakra held forward in the right hand
    m.box("rightArm", [8.9, 12.6, -4], [1.2, 1.2, 4], bright)
    m.box("rightArm", [8.3, 11.6, -34], [0.6, 3.2, 30], alpha(layered(glow, [rim(glow, (255, 255, 255))]), 230))
    # wings: long feathered blades
    feather = alpha(layered(pur, [rim(pur, glow), lines((("north", "south"), [[(0.5, 0), (0.5, 1)]]), glow)]), 185)
    for s, bone in ((1, "rightWing"), (-1, "leftWing")):
        for k in range(6):  # wide feathered blades fanning from straight up to out-and-down
            L = 22 - k * 1.8
            m.box(bone, [s * 4.0 - 2.0, 22.0, 4.6 + k * 0.15], [4.0, L, 0.5], feather, rot=[8, 0, -s * (18 + k * 24)], pivot=[s * 4.0, 22.0, 4.6])
    return m


# ------------------------------------------------------------------ Kurama avatar (Kurama Mode / Kurama Link)
def kurama():
    m = M.Model()
    m.bones = BONES
    gold, ink = (255, 186, 40), (40, 20, 10)

    def seals(face, px, w, h, base):  # the black seal stripes running down his chakra body
        if face in ("up", "east", "west", "south"):
            for x in range(w):
                for k in range(0, h, max(6, h // 3)):
                    y = int(k + 2 * math.sin(x * 0.5))
                    _put(px, w, h, x, y, ink); _put(px, w, h, x, y + 1, ink)
    fur = alpha(layered(gold, [seals, rim(gold, light(gold, 0.5))]), 215)
    plain = alpha(layered(gold, [rim(gold, light(gold, 0.5))]), 215)
    m.box("body", [-7, 8, -10], [14, 14, 22], fur)                            # crouched body
    m.box("body", [-6, 20, -12], [12, 8, 8], fur)                             # shoulders
    for x0, z0 in ((3, -10), (-7, -10), (3, 6), (-7, 6)):                    # four legs
        m.box("body", [x0, 0, z0], [4.5, 9, 4.5], plain)
        m.box("body", [x0 - 0.5, 0, z0 - 1.5], [5.5, 2, 2], alpha(solid(ink), 230))   # black paws
    # the head: wide skull, long snout, red slit eyes, black markings
    def face_paint(face, img):
        plain(face, img)
        if face != "north":
            return
        px = img.load()
        w, h = img.size
        for cx in (w * 0.27, w * 0.73):
            for y in range(int(h * 0.3), int(h * 0.5)):
                for x in range(int(cx - w * 0.12), int(cx + w * 0.12)):
                    _put(px, w, h, x, y, (220, 30, 20))
            for y in range(int(h * 0.28), int(h * 0.52)):
                _put(px, w, h, int(cx), y, ink)
            for k in range(int(w * 0.2)):  # the black streaks under the eyes
                _put(px, w, h, int(cx - w * 0.1) + k, int(h * 0.55) + k // 2, ink)
    m.box("head", [-6.5, 18, -21], [13, 11, 10], face_paint)
    def snout(face, img):
        plain(face, img)
        px = img.load()
        w, h = img.size
        if face == "north":
            for x in range(w):
                _put(px, w, h, x, int(h * 0.75), ink)
            for x in range(int(w * 0.4), int(w * 0.6)):
                for y in range(0, int(h * 0.25)):
                    _put(px, w, h, x, y, ink)
    m.box("head", [-3.5, 18, -27], [7, 5.5, 6], snout)
    m.box("head", [-3.2, 16.5, -26.6], [6.4, 1.5, 5], alpha(layered((250, 240, 220), [lambda f, px, w, h, b: [_put(px, w, h, x, 0, ink) for x in range(0, w, 2)] if f == "north" else None]), 230))  # fangs
    for s in (1, -1):  # the tall pointed ears, black-tipped
        m.strand([s * 4.2, 28.5, -16], [s * 0.4, 1, 0.2], 11, 5.0, alpha(layered(gold, [lambda f, px, w, h, b: [_put(px, w, h, x, y, ink) for y in range(h // 5) for x in range(w)]]), 215),
                 bone="head", segs=3, thick=0.45)
    for k in range(9):  # nine thick tails fanned out behind him, curling up
        a = math.radians(-75 + 150 * k / 8)
        m.strand([math.sin(a) * 2.0, 17, 11], [math.sin(a) * 1.1, 0.7, 0.8], 26, 7.0, fur, bone="tails", segs=3, thick=0.75,
                 bend=(math.sin(a) * 0.12, 0.35, -0.15))
    return m


# ------------------------------------------------------------------ Gamabunta, the toad boss
def gamabunta():
    m = M.Model()
    m.bones = BONES
    skin, belly = (176, 74, 44), (232, 196, 142)

    def warts(face, px, w, h, base):
        for y in range(h):
            for x in range(w):
                if (x * 7 + y * 13) % 17 == 0:
                    _put(px, w, h, x, y, dark(skin, 0.7))
    body = layered(skin, [warts])
    vest = (66, 60, 140)

    def kanji(face, px, w, h, base):  # the big white character on the back of his haori
        if face == "south":
            cx, cy = w // 2, h // 2
            for k in range(-w // 4, w // 4):
                _put(px, w, h, cx + k, cy - h // 6, (240, 240, 236)); _put(px, w, h, cx + k, cy + h // 6, (240, 240, 236))
                _put(px, w, h, cx, cy + k * h // w, (240, 240, 236))
    m.box("body", [-12, 3, -9], [24, 15, 20], body)                           # body
    m.box("body", [-10, 3, -9.5], [20, 8, 0.6], solid(belly))                  # pale belly
    m.box("body", [-12.5, 6, -6], [25, 12.5, 17.6], layered(vest, [kanji, rim(vest, (40, 36, 90))]))   # haori
    m.box("head", [-11, 13, -17], [22, 9, 11], body)                          # wide flat head
    m.box("head", [-10, 13, -17.4], [20, 1.0, 0.6], solid((90, 30, 24)))       # the long mouth
    for s in (1, -1):  # eyes on top: yellow with a black slit; the scar over his left eye
        m.box("head", [s * 6 - 2.6, 21, -15], [5.2, 4, 5.2], layered((240, 200, 60), [
            lambda f, px, w, h, b: [_put(px, w, h, x, h // 2, (16, 12, 10)) for x in range(1, w - 1)] if f in ("north", "east", "west") else None]))
    m.box("head", [-7.8, 20, -15.6], [0.6, 6.5, 0.6], solid((110, 40, 30)))     # the scar
    # the long pipe hanging from his mouth
    m.box("head", [4, 13.5, -24], [1.2, 1.2, 8], solid((90, 60, 40)), rot=[-15, 0, 0], pivot=[4.6, 14, -17])
    m.box("head", [3.4, 13.5, -26], [2.4, 3, 2.4], solid((60, 40, 30)), rot=[-15, 0, 0], pivot=[4.6, 14, -17])
    for x0 in (7, -11):  # front legs
        m.box("body", [x0, 0, -10], [4, 6, 5], body)
    for x0 in (8, -14):  # big back legs
        m.box("body", [x0, 0, 2], [6, 7, 9], body)
    m.box("body", [12, 4, -4], [1.4, 2, 14], solid((90, 56, 34)), rot=[0, 0, -20], pivot=[12, 6, 0])   # the dosu at his side
    return m


SUMMONS = [("susanoo", susanoo), ("kurama", kurama), ("gamabunta", gamabunta)]
