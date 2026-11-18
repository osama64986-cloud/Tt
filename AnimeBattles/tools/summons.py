"""Giant constructs, sculpted from hundreds of small cubes (see sculpt.py):
0 Perfect Susanoo, 1 Kurama, 2 Gamabunta, 3 Susanoo ribcage (Mangekyo), 4 armoured Susanoo (Eternal Mangekyo),
5 Muzan's giant infant form. Built at model scale, grown in game through `ab:size`."""
import math

import models as M
from models import dark, layered, light, _put
import sculpt as S
from sculpt import blob, box_at, chakra, curve_tube, tube, blade, spline, flesh, stripes, speckle, rim, alpha, smooth

PUR, PUR_D, PUR_L = (146, 78, 228), (86, 40, 160), (222, 196, 255)


def _bones(pivots):
    parents = {"body": "root", "head": "body", "rightArm": "body", "leftArm": "body",
               "rightWing": "body", "leftWing": "body", "tails": "body", "jaw": "head", "wheel": "head",
               "rightWingTip": "rightWing", "leftWingTip": "leftWing", "rightLeg": "body", "leftLeg": "body"}
    return S.bones_from(pivots, parents)


def frustum(m, bone, base, height, r0, r1, paint, slices=4, cross=0.74):
    """A flared drum (armoured skirt, chakra flame base): radius r0 at the bottom to r1 at the top."""
    for i in range(slices):
        t = (i + 0.5) / slices
        rx, rz = r0[0] + (r1[0] - r0[0]) * t, r0[1] + (r1[1] - r0[1]) * t
        y = base[1] + height * i / slices
        h = height / slices + 0.1
        m.box(bone, [base[0] - rx, y, base[2] - rz * cross], [2 * rx, h, 2 * rz * cross], paint)
        m.box(bone, [base[0] - rx * cross, y, base[2] - rz], [2 * rx * cross, h, 2 * rz], paint)


# ------------------------------------------------------------------ Susanoo (shared upper body)
def _susanoo_upper(m, dy, sword=True):
    arm = chakra(PUR, 205)
    plate = chakra(PUR_D, 215, PUR_L)
    glow = chakra(PUR_L, 235, (255, 255, 255))
    blob(m, "body", [0, 29 + dy, 0], [8.5, 3, 6.5], arm, slices=3)                              # waist
    blob(m, "body", [0, 39 + dy, 0], [12, 8.5, 8], arm, slices=6)                               # chest
    for y, w in ((34, 17), (38, 20), (42, 21)):                                                 # breastplate bands
        box_at(m, "body", [0, y + dy, -7.4], [w, 2.4, 2.2], plate)
    box_at(m, "body", [0, 39 + dy, -8.4], [3, 12, 1.6], plate)                                   # centre ridge
    blob(m, "body", [0, 47.5 + dy, 0], [8, 1.8, 6], plate, slices=2)                             # gorget
    for k in range(5):                                                                          # spine ridge on the back
        box_at(m, "body", [0, 30 + k * 4 + dy, 8.2], [2.4, 2.6, 2.4], plate, rot=[45, 0, 0])
    tube(m, "body", [[0, 47 + dy, 0], [0, 51 + dy, -0.5]], [3.6, 3.2], arm)                      # neck
    # head: rounded helmet, dark face plate, glowing eye slits, the long tengu nose and the crescent crest
    blob(m, "head", [0, 55.5 + dy, 0.5], [6.6, 6.2, 7], arm, slices=5)
    box_at(m, "head", [0, 54 + dy, -6.2], [9.4, 7.5, 1.6], plate)
    for s in (1, -1):
        box_at(m, "head", [s * 2.5, 55.5 + dy, -7.2], [3, 0.8, 0.6], glow)
        curve_tube(m, "head", [[s * 2.4, 60 + dy, -4], [s * 5, 65 + dy, -5], [s * 6.2, 70 + dy, -2], [s * 5, 74 + dy, 2]], 1.7, 0.4, plate, n=2)
        blob(m, "head", [s * 6.6, 54 + dy, 0], [1.4, 4.5, 4.5], plate, slices=3)              # cheek guards
    tube(m, "head", [[0, 55.5 + dy, -7], [0, 53.8 + dy, -12], [0, 51.6 + dy, -16.5]], [1.9, 1.1, 0.4], plate)
    blob(m, "head", [0, 59 + dy, -6.6], [1.6, 1.6, 1.0], glow, slices=2)                         # the forehead jewel
    for s, bone in ((1, "rightArm"), (-1, "leftArm")):
        blob(m, bone, [s * 14.2, 46 + dy, 0], [6.8, 4.6, 7.6], plate, slices=4)                 # pauldrons, layered
        blob(m, bone, [s * 15.6, 41.8 + dy, 0], [6.2, 2.2, 7.8], plate, slices=2)
        tube(m, bone, [[s * 14.5, 44 + dy, 0], [s * 16, 34 + dy, -1]], [3.5, 3.1], arm)           # upper arm
        tube(m, bone, [[s * 16, 34 + dy, -1], [s * 15.6, 25.5 + dy, -6]], [3.2, 2.8], arm)      # forearm
        blob(m, bone, [s * 15.8, 28 + dy, -4.8], [3.8, 4.2, 3.8], plate, slices=3)              # gauntlet
        blob(m, bone, [s * 15.5, 22.8 + dy, -7], [3.1, 3.1, 3.1], arm, slices=3)                # fist
    if sword:  # the great chakra sword in the right hand
        box_at(m, "rightArm", [15.5, 23 + dy, -9.6], [7, 1.6, 1.6], plate)
        blade(m, "rightArm", [15.5, 22.9 + dy, -10.2], [0, 0.12, -1], 48, 5.2, 1.1, glow)


def susanoo_madara():
    """Madara's Perfect Susanoo: the same giant, in deep blue."""
    global PUR, PUR_D, PUR_L
    old = (PUR, PUR_D, PUR_L)
    PUR, PUR_D, PUR_L = (60, 90, 220), (30, 44, 140), (170, 196, 255)
    try:
        return susanoo_perfect()
    finally:
        PUR, PUR_D, PUR_L = old


def _recolor(fn, cols):
    global PUR, PUR_D, PUR_L
    old = (PUR, PUR_D, PUR_L)
    PUR, PUR_D, PUR_L = cols
    try:
        return fn()
    finally:
        PUR, PUR_D, PUR_L = old


def susanoo_itachi():
    """Itachi's Susanoo: the armoured giant in red-orange chakra."""
    return _recolor(susanoo_armour, ((236, 70, 46), (150, 30, 24), (255, 176, 140)))


def susanoo_kakashi():
    """Kakashi's Susanoo (Double Mangekyo): the full giant in bright cyan-blue."""
    return _recolor(susanoo_perfect, ((70, 190, 230), (30, 104, 150), (190, 240, 255)))


def susanoo_perfect():
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 30, 0], "head": [0, 52, 0], "rightArm": [14, 47, 0], "leftArm": [-14, 47, 0],
                      "rightWing": [5, 46, 6], "leftWing": [-5, 46, 6], "tails": [0, 20, 8]})
    arm = chakra(PUR, 205)
    plate = chakra(PUR_D, 215, PUR_L)
    _susanoo_upper(m, 0)
    frustum(m, "body", [0, 14, 0], 14, (13.5, 10.5), (9.5, 7.5), alpha(smooth(PUR_D, [stripes(PUR_L, 4, "x")]), 215), slices=4)  # armoured skirt
    for s in (1, -1):  # legs and armoured boots
        tube(m, "body", [[s * 5, 16, 0], [s * 6, 8, -1], [s * 6, 2, 0]], [3.9, 3.5, 3.2], arm)
        blob(m, "body", [s * 6, 8, -2], [3.6, 2.4, 3], plate, slices=2)                         # knee guards
        box_at(m, "body", [s * 6, 1.1, -2], [6.4, 2.2, 9.5], plate)
    # wings: a long wing bone sweeping up and out, broad feathers hanging from it (primaries longest at the tip)
    feather = alpha(smooth(PUR, [stripes(PUR_L, 4, "x")]), 195)
    covert = alpha(smooth(PUR_D, [stripes(PUR, 3, "x")]), 205)
    for s, bone in ((1, "rightWing"), (-1, "leftWing")):
        arm_pts = curve_tube(m, bone, [[s * 5, 46, 6.5], [s * 14, 56, 12], [s * 24, 60, 14], [s * 33, 57, 12]], 2.6, 1.2, chakra(PUR_D, 215), n=3)
        for i, p in enumerate(arm_pts[1:]):
            t = i / max(1, len(arm_pts) - 2)
            blade(m, bone, p, [s * (0.1 + 0.55 * t), -1, 0.35], 15 + t * 20, 7.0, 0.9, feather)
            blade(m, bone, [p[0], p[1] + 0.8, p[2] - 0.9], [s * (0.1 + 0.4 * t), -1, 0.2], 8 + t * 6, 6.2, 1.0, covert)
    return m


def susanoo_armour():
    """Eternal Mangekyo: the armoured upper body rising from a base of chakra flame (Sasuke stands inside)."""
    m = M.Model()
    dy = -18
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 12, 0], "head": [0, 52 + dy, 0], "rightArm": [14, 47 + dy, 0], "leftArm": [-14, 47 + dy, 0],
                      "rightWing": [0, 30, 6], "leftWing": [0, 30, 6], "tails": [0, 10, 8]})
    _susanoo_upper(m, dy)
    flame = chakra(PUR, 170)
    frustum(m, "body", [0, 0, 0], 11, (14, 11), (8.5, 6.5), flame, slices=4)                    # chakra flame base
    for k in range(10):  # flame tongues licking up round the base
        a = 2 * math.pi * k / 10
        blade(m, "body", [math.cos(a) * 12, 1, math.sin(a) * 9], [math.cos(a) * 0.3, 1, math.sin(a) * 0.3], 9 + (k % 3) * 3, 3.2, 1.2, flame)
    return m


def susanoo_ribs():
    """Mangekyo Susanoo, first stages: spine, ribcage, skull and skeletal arms round his body."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 12, 0], "head": [0, 36, 2], "rightArm": [12, 31, 2], "leftArm": [-12, 31, 2],
                      "rightWing": [0, 30, 6], "leftWing": [0, 30, 6], "tails": [0, 10, 8]})
    bone_p = chakra(PUR, 200)
    joint = chakra(PUR_D, 215, PUR_L)
    for k in range(9):  # vertebrae
        box_at(m, "body", [0, 9 + k * 3, 8.5], [2.6, 2.2, 2.6], joint, rot=[0, 0, 45])
    for i in range(5):  # five pairs of ribs curving round to the sternum
        y = 27 - i * 3
        for s in (1, -1):
            curve_tube(m, "body", [[s * 1.2, y, 8.2], [s * 7.5, y + 0.8, 6.5], [s * 11.5, y, 0], [s * 9.5, y - 1, -6.5], [s * 3, y - 2, -9]],
                       1.0, 0.6, bone_p, n=2, knuckles=False)
    tube(m, "body", [[0, 27, -9.4], [0, 15, -9.4]], [1.2, 0.9], joint)                              # sternum
    curve_tube(m, "body", [[-12, 31, 2], [-6, 32.5, 5], [0, 32, 7], [6, 32.5, 5], [12, 31, 2]], 1.2, 1.2, bone_p, n=2)   # collar bones
    blob(m, "body", [0, 8, 6], [7, 2.6, 4], joint, slices=2)                                       # pelvis
    # skull with dark sockets and a jaw of teeth
    blob(m, "head", [0, 41.5, 1.5], [6.2, 6, 7], bone_p, slices=5)
    for s in (1, -1):
        box_at(m, "head", [s * 2.4, 41.5, -5.4], [2.8, 2.6, 0.8], alpha(smooth((60, 20, 100)), 230))
        box_at(m, "head", [s * 2.4, 41.5, -5.9], [1.0, 1.0, 0.4], alpha(smooth((255, 230, 255)), 255))
    box_at(m, "head", [0, 36.4, -1], [8.4, 2.2, 8], bone_p)
    for x in range(-3, 4):
        box_at(m, "head", [x * 1.1, 37.8, -4.9], [0.7, 1.2, 0.6], alpha(smooth(PUR_L), 240))
    for s, bone in ((1, "rightArm"), (-1, "leftArm")):  # skeletal arms reaching forward
        tube(m, bone, [[s * 12, 31, 2], [s * 16, 22, -2]], [1.3, 1.1], bone_p)
        for off in (-0.7, 0.7):
            tube(m, bone, [[s * 16, 22, -2 + off], [s * 15, 15, -10 + off]], [0.8, 0.7], bone_p, knuckles=False)
        for f in range(4):
            tube(m, bone, [[s * 15, 15, -10], [s * (14 + f * 0.8), 13, -13], [s * (14 + f * 0.9), 11.5, -14.5]], [0.5, 0.45, 0.3], bone_p)
    return m


# ------------------------------------------------------------------ Kurama (Nine-Tails Chakra Mode avatar)
def kurama():
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 24, 0], "head": [0, 36, -16], "rightArm": [10, 30, -12], "leftArm": [-10, 30, -12],
                      "rightWing": [0, 30, 0], "leftWing": [0, 30, 0], "tails": [0, 24, 14], "jaw": [0, 33.6, -22]})
    G, D, INK = (255, 178, 38), (228, 112, 22), (40, 18, 10)
    fur = chakra(G, 215, (255, 236, 150))
    deep = chakra(D, 220, (255, 200, 90))
    seal = fur
    ink = alpha(smooth(INK), 240)
    blob(m, "body", [0, 30, -8], [12, 10, 10], seal, slices=6)                                     # chest
    blob(m, "body", [0, 24, 8], [10, 9, 11.5], seal, slices=6, axis="z")                          # belly and hips
    tube(m, "body", [[0, 31, -13], [0, 35.5, -18]], [6.5, 6], fur)                                  # neck
    # head
    blob(m, "head", [0, 38.5, -20.5], [9, 7.6, 8], fur, slices=5)
    for s in (1, -1):  # fur tufts on the cheeks
        for k in range(2):
            blade(m, "head", [s * 7.5, 36 - k * 2.4, -20 + k], [s * 1, -0.35, 0.3], 6, 3.4, 1.6, deep)
    tooth = smooth((250, 246, 232))
    gum, tongue = smooth((120, 20, 26)), smooth((214, 70, 84))
    blob(m, "head", [0, 36.6, -30], [4.4, 2.6, 6.2], fur, slices=5, axis="z")                       # upper jaw / muzzle
    blob(m, "head", [0, 37.6, -27], [3.6, 1.8, 4.0], fur, slices=3, axis="z")                       # bridge of the nose
    box_at(m, "head", [0, 36.4, -36.4], [3.2, 2.2, 1.8], ink)                                        # nose
    blob(m, "head", [0, 34.6, -29], [3.6, 0.5, 5.4], gum, slices=2, axis="z")                       # roof of the mouth
    for side in (1, -1):  # upper teeth following the curve of the muzzle, long fangs at the front
        for k in range(6):
            z = -34.6 + k * 1.7
            x = side * (1.3 + k * 0.42)
            L = 2.2 if k == 1 else 1.3
            S.blade(m, "head", [x, 34.6, z], [0, -1, 0], L, 0.8, 0.7, tooth)
    blob(m, "jaw", [0, 32.4, -28.4], [3.5, 1.1, 5.6], deep, slices=4, axis="z")                    # lower jaw
    blob(m, "jaw", [0, 33.0, -28.4], [2.6, 0.45, 4.4], tongue, slices=2, axis="z")                 # tongue
    for side in (1, -1):
        for k in range(5):
            z = -33.4 + k * 1.7
            x = side * (1.2 + k * 0.4)
            S.blade(m, "jaw", [x, 33.1, z], [0, 1, 0], 1.6 if k == 0 else 1.1, 0.75, 0.65, tooth)
    for s in (1, -1):
        box_at(m, "head", [s * 4.3, 39.6, -27.1], [3.8, 2.1, 0.8], alpha(smooth((214, 28, 20)), 250))        # red eyes
        box_at(m, "head", [s * 4.3, 39.6, -27.6], [0.7, 2.1, 0.4], ink)                                    # slit pupils
        blade(m, "head", [s * 2.4, 41.8, -26.6], [s * 1, 0.45, 0.2], 6.5, 0.9, 0.6, ink, taper=False)    # brow markings
        blade(m, "head", [s * 3, 37.9, -26.9], [s * 1, -0.35, 0.3], 5.5, 0.9, 0.6, ink, taper=False)     # under-eye markings
        ear = curve_tube(m, "head", [[s * 5.5, 44, -18], [s * 7.6, 52, -17], [s * 9, 60, -15]], 3.9, 0.6, fur, n=2, flat=0.55)
        tube(m, "head", ear[-3:], [1.4, 1.0, 0.5], ink, flat=0.6)                                        # black ear tips
    for s, bone in ((1, "rightArm"), (-1, "leftArm")):  # front legs (arms), paws and claws
        tube(m, bone, [[s * 10, 30, -12], [s * 13, 20, -16], [s * 12.5, 8, -20]], [5.6, 4.5, 3.9], seal)
        blob(m, bone, [s * 12.5, 4, -22.5], [4.6, 3, 5.6], fur, slices=3)
        for k in (-1, 0, 1):
            blade(m, bone, [s * 12.5 + k * 2, 2.6, -27.6], [0, -0.45, -1], 3, 1.1, 0.9, ink)
    for s_ in (1, -1):  # the black seal bands of the chakra cloak: shoulders, forelegs, flanks
        for y, z, r in ((27, -12.5, 6.0), (19, -16.3, 4.8), (12, -18.7, 4.2)):
            blob(m, "rightArm" if s_ > 0 else "leftArm", [s_ * (10.6 + (27 - y) * 0.2), y, z], [r * 1.02, 0.55, r * 1.02], ink, slices=1)
        for z in (-2, 4, 10):
            box_at(m, "body", [s_ * 10.6, 26, z], [0.8, 9, 1.0], ink)
    for s in (1, -1):  # hind legs
        blob(m, "body", [s * 9, 20, 12], [5, 8, 7], seal, slices=4)
        tube(m, "body", [[s * 10, 14, 16], [s * 10.5, 6, 12], [s * 10, 1.8, 8]], [4, 3.3, 3], fur)
        blob(m, "body", [s * 10, 1.8, 5.5], [3.7, 1.8, 4.6], fur, slices=2)
    for k in range(9):  # nine tails: thick at the root, curling up and forward at the tip, banded fur
        a = math.radians(-72 + 144 * k / 8)
        b = [0, 23, 17]
        ctrl = [b, [math.sin(a) * 8, 29, 25], [math.sin(a) * 15, 40, 28], [math.sin(a) * 19, 51, 23], [math.sin(a) * 20, 58, 14]]
        curve_tube(m, "tails", ctrl, 4.8, 1.3, [fur, deep], n=2)
    return m


# ------------------------------------------------------------------ Gamabunta
def gamabunta():
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 16, 0], "head": [0, 26, -10], "rightArm": [14, 16, -14], "leftArm": [-14, 16, -14],
                      "rightWing": [0, 30, 0], "leftWing": [0, 30, 0], "tails": [0, 16, 14], "jaw": [0, 21.4, -8]})
    SK, BELLY, VEST = (188, 80, 46), (234, 200, 146), (62, 58, 146)
    skin = flesh(SK)
    darker = flesh(dark(SK, 0.8))
    blob(m, "body", [0, 18, 4], [20, 13, 18], skin, slices=7)                                      # body
    blob(m, "body", [0, 12.5, -8], [15, 8, 8], smooth(BELLY), slices=4)                           # pale belly
    blob(m, "head", [0, 25, -14], [19, 8, 12], skin, slices=7, axis="x")                           # wide flat head
    blob(m, "jaw", [0, 19.6, -17.5], [13, 2.6, 7], smooth(BELLY), slices=3, axis="x")             # chin / lower jaw
    blob(m, "jaw", [0, 21.0, -18], [11, 0.6, 6], smooth((214, 96, 110)), slices=2, axis="x")      # pink inside of the mouth
    curve_tube(m, "head", [[-16, 22.4, -14], [-10, 21.6, -22], [0, 21.2, -25.8], [10, 21.6, -22], [16, 22.4, -14]], 0.8, 0.8,
               smooth((96, 28, 22)), n=2, knuckles=False)                                         # the long mouth
    for s in (1, -1):  # bulging eyes with a black bar pupil and heavy brows
        blob(m, "head", [s * 10, 33, -16], [5, 4.6, 5], smooth((242, 204, 64)), slices=4)
        box_at(m, "head", [s * 10, 33, -20.9], [6.2, 1.3, 1], smooth((16, 12, 10)))
        blob(m, "head", [s * 10, 37, -15], [6.2, 1.7, 4.4], darker, slices=2)
    tube(m, "head", [[-12.4, 39.5, -17], [-9.4, 33, -21.4], [-7.4, 28, -22.4]], [0.7, 0.7, 0.6], smooth((120, 30, 26)))  # the scar
    for i in range(22):  # warts
        a = i * 2.39996
        y = 14 + (i * 7 % 15)
        box_at(m, "body", [math.cos(a) * 19, y, 4 + math.sin(a) * 17], [1.6, 1.6, 1.6], darker, rot=[0, 0, 45])
    # the blue haori over his back, with its big white kanji
    blob(m, "body", [0, 25, 8], [21, 7.5, 16.5], smooth(VEST, []), slices=3)
    def kanji(face, px, w, h, base):
        if face == "up":
            for k in range(w // 5, w - w // 5):
                _put(px, w, h, k, h // 3, (240, 240, 236)); _put(px, w, h, k, 2 * h // 3, (240, 240, 236))
                _put(px, w, h, w // 2, k * h // w, (240, 240, 236))
    box_at(m, "body", [0, 32.8, 9], [14, 0.8, 14], smooth(VEST, [kanji]))
    curve_tube(m, "head", [[13, 21.6, -20], [17, 25, -30], [19, 28, -38]], 1.0, 1.0, smooth((96, 64, 40)), n=2)   # pipe
    blob(m, "head", [19.4, 29, -40], [2.2, 2.6, 2.2], smooth((70, 46, 30)), slices=3)
    for s, bone in ((1, "rightArm"), (-1, "leftArm")):  # front legs with three webbed fingers
        tube(m, bone, [[s * 14, 14, -14], [s * 17, 8, -20], [s * 16, 2, -24]], [4.3, 3.7, 3.1], skin)
        for k in (-1, 0, 1):
            tube(m, bone, [[s * 16, 1.4, -25], [s * (16 + k * 2.6), 1.0, -30.5]], [1.3, 1.0], skin)
            blob(m, bone, [s * (16 + k * 2.6), 1.0, -31], [1.3, 1.0, 1.3], darker, slices=2)
    for s in (1, -1):  # big folded hind legs
        blob(m, "body", [s * 17, 11, 12], [6, 9, 9], skin, slices=4)
        tube(m, "body", [[s * 18, 2.2, 8], [s * 20.5, 1.4, -2]], [3.2, 2.5], skin)
        for k in (-1, 0, 1):
            tube(m, "body", [[s * 20.5, 1.2, -2], [s * (20.5 + k * 2.4), 0.9, -7]], [1.2, 0.9], skin)
    # the dosu, drawn and held forward in his right hand
    tube(m, "rightArm", [[16, 3.2, -24], [16, 3.6, -28]], [1.2, 1.2], smooth((80, 50, 30)))         # hilt
    box_at(m, "rightArm", [16, 3.6, -28.6], [4.2, 1.2, 1.0], smooth((200, 170, 90)))              # guard
    S.blade(m, "rightArm", [16, 3.7, -29], [0, 0.18, -1], 26, 3.2, 0.7, smooth((214, 220, 230)), width_dir=[0, 1, 0])
    tube(m, "body", [[21.5, 17, 10], [23.5, 12, -6]], [1.3, 1.2], smooth((80, 50, 30)))          # its sheath at his side
    return m


# ------------------------------------------------------------------ Muzan's giant infant form (manga, chapter 200)
def muzan_infant():
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 18, 0], "head": [0, 30, -6], "rightArm": [11, 26, -4], "leftArm": [-11, 26, -4],
                      "rightWing": [0, 30, 0], "leftWing": [0, 30, 0], "tails": [0, 16, 8], "jaw": [0, 31, -6]})
    SKIN_P, VEIN = (234, 198, 188), (176, 26, 40)
    skin = smooth(SKIN_P)
    vein = smooth(VEIN)
    blob(m, "body", [0, 20, 2], [12, 13, 10], skin, slices=6)                                    # torso
    blob(m, "body", [0, 14, -4], [10, 8, 7], skin, slices=4)                                     # belly
    blob(m, "head", [0, 37, -4], [11, 11, 10], skin, slices=6)                                   # the huge infant head
    blob(m, "head", [0, 42, -2], [11.6, 6.4, 10.6], smooth((22, 16, 22)), slices=3)            # black hair
    for k in range(5):
        blade(m, "head", [(k - 2) * 3.2, 43, -10.5], [(k - 2) * 0.15, -1, -0.25], 6, 2.6, 1.2, smooth((22, 16, 22)))
    for s in (1, -1):
        box_at(m, "head", [s * 4.2, 36.6, -13.7], [3.4, 1.8, 0.8], smooth((214, 20, 30)))       # red eyes, cat pupils
        box_at(m, "head", [s * 4.2, 36.6, -14.2], [0.6, 1.8, 0.4], smooth((10, 6, 8)))
        tube(m, "head", [[s * 7, 40, -11], [s * 8.5, 35, -12], [s * 7.5, 30, -12]], [0.45, 0.4, 0.35], vein, knuckles=False)  # veins over the face
    box_at(m, "head", [0, 31.2, -12.8], [7.4, 1.4, 2.0], smooth((60, 6, 14)))                    # the mouth
    for x in range(-3, 4):
        S.blade(m, "head", [x * 1.05, 31.8, -13.4], [0, -1, 0], 1.1, 0.6, 0.5, smooth((250, 246, 236)))
    blob(m, "jaw", [0, 29.4, -9], [7.5, 1.6, 4.6], skin, slices=2, axis="x")                      # lower jaw
    for x in range(-3, 4):
        S.blade(m, "jaw", [x * 1.05, 30.4, -12.6], [0, 1, 0], 0.9, 0.6, 0.5, smooth((250, 246, 236)))
    for i in range(14):  # pulsing blood vessels over the body
        a = i * 2.2
        y0 = 8 + (i * 5 % 22)
        tube(m, "body", [[math.cos(a) * 11.5, y0, 2 + math.sin(a) * 9.5], [math.cos(a + 0.4) * 11.8, y0 + 5, 2 + math.sin(a + 0.4) * 9.6]], [0.5, 0.4], vein, knuckles=False)
    for s, bone in ((1, "rightArm"), (-1, "leftArm")):  # chubby arms, clawed hands
        tube(m, bone, [[s * 11, 26, -4], [s * 15, 16, -10], [s * 14, 4.5, -14]], [4.8, 4.1, 3.7], skin)
        blob(m, bone, [s * 14, 3, -16], [4, 2.6, 4.6], skin, slices=3)
        for k in (-1, 0, 1):
            blade(m, bone, [s * 14 + k * 1.8, 2, -20.4], [0, -0.4, -1], 2.6, 1.0, 0.8, smooth((60, 90, 140)))
    for s in (1, -1):  # kneeling legs
        tube(m, "body", [[s * 7, 9, 4], [s * 9, 4, -6]], [5.8, 5], skin)
        tube(m, "body", [[s * 9, 3, -6], [s * 9, 2.4, 8]], [4.2, 3.6], skin)
        blob(m, "body", [s * 9, 2.4, 9.5], [3.6, 2.4, 3], skin, slices=2)
    return m


# ------------------------------------------------------------------ Mahoraga (Ten Shadows, Sukuna)
def mahoraga():
    """Eight-Handled Sword Divergent Sila Divine General Mahoraga: a towering white figure, the Sword of
    Extermination on its right arm, wing-like folds round its head, the eight-handled wheel above it."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 24, 0], "head": [0, 40, 0], "rightArm": [9, 36, 0], "leftArm": [-9, 36, 0],
                      "rightWing": [0, 30, 0], "leftWing": [0, 30, 0], "tails": [0, 20, 6], "jaw": [0, 40, -2], "wheel": [0, 53, 1.5]})
    SK, CL, DK, GOLD = smooth((234, 230, 222)), smooth((204, 200, 190)), smooth((62, 60, 72)), smooth((176, 146, 86))
    for s_ in (1, -1):  # legs and feet
        tube(m, "body", [[s_ * 4, 24, 0], [s_ * 4.6, 12, -0.6], [s_ * 4.6, 2.2, 0]], [3.1, 2.7, 2.3], SK)
        box_at(m, "body", [s_ * 4.6, 1.0, -1.4], [4.2, 2.0, 6.2], SK)
    frustum(m, "body", [0, 13, 0], 13, (7.6, 5.6), (6.2, 4.6), CL, slices=4)                      # the white wrap round its hips
    blob(m, "body", [0, 26.5, 0], [6.2, 4.0, 4.3], SK, slices=4)                                  # abdomen
    blob(m, "body", [0, 32.5, 0], [8.2, 6.0, 5.2], SK, slices=6)                                  # chest
    for k in range(3):
        box_at(m, "body", [0, 24.5 + k * 2.2, -4.1], [5.0, 0.4, 0.6], smooth((210, 206, 198)))     # abdominal lines
    tube(m, "body", [[0, 37.5, 0], [0, 40, -0.2]], [2.6, 2.4], SK)                                 # neck
    blob(m, "head", [0, 42.8, 0], [3.7, 4.2, 3.9], SK, slices=5)
    for s_ in (1, -1):  # the wing-like folds round its head (it has no visible eyes)
        for k in range(2):
            blade(m, "head", [s_ * 3.0, 43.5 + k * 2.0, 0.5], [s_ * 1, 0.55 - k * 0.2, 0.25], 6.5 - k, 2.8, 0.7, SK, width_dir=[0, 1, 0])
    box_at(m, "head", [0, 41.2, -3.8], [3.2, 0.5, 0.5], DK)                                       # mouth
    # the eight-handled wheel: a rim, eight spokes and eight handles, spinning above its head
    pts = [[math.cos(a) * 6, 53 + math.sin(a) * 6, 1.5] for a in [i * math.pi / 8 for i in range(17)]]
    tube(m, "wheel", pts, [0.7] * len(pts), GOLD, knuckles=False)
    for i in range(8):
        a = i * math.pi / 4
        d = [math.cos(a), math.sin(a), 0]
        tube(m, "wheel", [[0, 53, 1.5], [d[0] * 6, 53 + d[1] * 6, 1.5]], [0.45, 0.45], GOLD, knuckles=False)
        tube(m, "wheel", [[d[0] * 6, 53 + d[1] * 6, 1.5], [d[0] * 8.5, 53 + d[1] * 8.5, 1.5]], [0.6, 0.35], GOLD)
    box_at(m, "wheel", [0, 53, 1.5], [1.8, 1.8, 1.8], GOLD, rot=[0, 0, 45])
    for s_, bone in ((1, "rightArm"), (-1, "leftArm")):  # massive arms
        blob(m, bone, [s_ * 9, 36, 0], [3.3, 3.3, 3.3], SK, slices=3)
        tube(m, bone, [[s_ * 9.4, 35, 0], [s_ * 11, 28, -1], [s_ * 11, 21, -3]], [2.8, 2.4, 2.1], SK)
        blob(m, bone, [s_ * 11, 19.6, -3.6], [2.3, 2.3, 2.3], SK, slices=3)
    # the Sword of Extermination grows from the right forearm, blade forward
    box_at(m, "rightArm", [11, 22, -4.2], [3.6, 3.0, 2.4], DK)
    blade(m, "rightArm", [11, 21.6, -5.2], [0, -0.25, -1], 24, 3.4, 0.8, smooth((220, 226, 236)), width_dir=[0, 1, 0])
    return m


def crow():
    """Itachi's crow: glossy black body, hooked beak, Sharingan-red eyes; each wing has a shoulder part (coverts and
    secondaries) and a hinged wingtip (five fingered primaries), so it beats and folds like a real bird. Faces -z."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 9, 0], "head": [0, 10, -3.6], "rightWing": [1.5, 9.8, -0.8], "leftWing": [-1.5, 9.8, -0.8],
                      "rightWingTip": [6.2, 10.1, -0.4], "leftWingTip": [-6.2, 10.1, -0.4], "tails": [0, 9, 3.2]})
    BLK, SHEEN, GREY, EYE, PUP = smooth((24, 24, 32)), smooth((46, 52, 84)), smooth((62, 62, 70)), smooth((232, 30, 36)), smooth((10, 8, 10))
    blob(m, "body", [0, 9.0, 0], [1.9, 1.9, 3.6], BLK, slices=5, axis="z")                     # body
    blob(m, "body", [0, 9.3, -2.3], [1.75, 1.75, 1.8], SHEEN, slices=3)                        # chest
    blob(m, "body", [0, 9.9, 0.4], [1.5, 0.9, 2.6], SHEEN, slices=3, axis="z")                # glossy back
    blob(m, "head", [0, 10.4, -4.2], [1.4, 1.4, 1.5], BLK, slices=4)                          # head
    blade(m, "head", [0, 10.3, -5.4], [0, -0.25, -1], 2.4, 0.95, 0.8, GREY, width_dir=[1, 0, 0])  # hooked upper beak
    blade(m, "head", [0, 9.8, -5.3], [0, -0.05, -1], 1.6, 0.7, 0.5, GREY, width_dir=[1, 0, 0])    # lower beak
    for sx in (1, -1):
        box_at(m, "head", [sx * 1.08, 10.7, -4.85], [0.32, 0.5, 0.5], EYE)                    # Sharingan eyes
        box_at(m, "head", [sx * 1.12, 10.7, -4.85], [0.3, 0.2, 0.2], PUP)
        wing, tip = ("rightWing", "rightWingTip") if sx > 0 else ("leftWing", "leftWingTip")
        blade(m, wing, [sx * 1.5, 9.9, -1.1], [sx, 0.06, 0.12], 5.0, 3.4, 0.45, SHEEN, taper=False, width_dir=[0, 0, 1])   # coverts
        for k in range(4):                                                                    # secondaries hanging back
            blade(m, wing, [sx * (2.2 + k * 1.1), 9.7, -0.2], [sx * 0.12, -0.04, 1], 3.0 - k * 0.2, 1.2, 0.3, BLK, width_dir=[1, 0, 0])
        for k in range(5):                                                                    # primaries spread like fingers
            blade(m, tip, [sx * 6.2, 10.1, -0.9 + k * 0.55], [sx, 0.04, -0.15 + k * 0.28], 4.6 - k * 0.45, 1.1, 0.3, BLK, width_dir=[0, 0, 1])
        tube(m, "body", [[sx * 0.7, 7.6, 0.6], [sx * 0.7, 6.6, 1.4]], [0.22, 0.18], GREY, knuckles=False)  # tucked legs
    for k in (-2, -1, 0, 1, 2):                                                               # fan tail
        blade(m, "tails", [k * 0.4, 9.0, 3.0], [k * 0.22, -0.08, 1], 3.8 - abs(k) * 0.3, 1.3, 0.3, BLK, width_dir=[1, 0, 0])
    return m


def hound():
    """Kakashi's ninja hound: a compact, sharp-eared tan dog with a cream muzzle and chest, tongue out, a curled
    tail, a navy vest and the Leaf headband; four slim legs with paws (front and hind legs move). Faces -z."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 10, 0], "head": [0, 12.6, -5.8], "jaw": [0, 13.0, -8.4], "rightArm": [1.7, 9.6, -3.6],
                      "leftArm": [-1.7, 9.6, -3.6], "rightLeg": [1.8, 10.0, 3.8], "leftLeg": [-1.8, 10.0, 3.8], "tails": [0, 11.6, 5.0]})
    FUR, CREAM, DARK, NOSE, PINK = smooth((178, 118, 62)), smooth((238, 216, 178)), smooth((92, 60, 38)), smooth((24, 20, 22)), smooth((226, 110, 120))
    NAVY, STEEL, BAND = smooth((44, 54, 92)), smooth((198, 204, 214)), smooth((34, 40, 70))
    blob(m, "body", [0, 10.2, 0.4], [2.5, 2.4, 5.2], FUR, slices=5, axis="z")                 # body
    blob(m, "body", [0, 10.4, -3.2], [2.7, 2.7, 2.2], FUR, slices=4)                          # chest
    blob(m, "body", [0, 9.4, -3.4], [1.9, 2.0, 1.8], CREAM, slices=3)                         # cream chest
    blob(m, "body", [0, 11.6, -0.6], [2.7, 1.3, 3.0], NAVY, slices=3, axis="z")              # ninja vest over the back
    tube(m, "body", [[0, 11.6, -4.4], [0, 13.0, -5.6]], [1.6, 1.5], FUR, knuckles=False)        # neck
    blob(m, "head", [0, 14.2, -7.0], [2.1, 2.0, 2.2], FUR, slices=4)                          # head
    blob(m, "head", [0, 13.4, -9.3], [1.15, 1.0, 1.6], CREAM, slices=3, axis="z")            # muzzle
    box_at(m, "head", [0, 13.9, -10.8], [0.95, 0.75, 0.6], NOSE)                              # nose
    for sx in (1, -1):
        blade(m, "head", [sx * 1.2, 15.8, -6.6], [sx * 0.28, 1, 0.12], 2.6, 1.7, 0.5, FUR, width_dir=[0, 0, 1])  # pointed ears
        blade(m, "head", [sx * 1.2, 15.9, -6.85], [sx * 0.28, 1, 0.12], 1.8, 0.9, 0.2, PINK, width_dir=[0, 0, 1])
        box_at(m, "head", [sx * 0.95, 14.8, -8.9], [0.45, 0.45, 0.3], NOSE)                   # eyes
        box_at(m, "head", [sx * 0.85, 14.95, -9.06], [0.15, 0.15, 0.05], smooth((255, 255, 255)))
    blob(m, "jaw", [0, 12.75, -9.1], [0.95, 0.4, 1.3], CREAM, slices=2, axis="z")           # lower jaw
    blade(m, "jaw", [0, 12.6, -9.9], [0, -1, -0.35], 1.4, 0.8, 0.25, PINK, width_dir=[1, 0, 0])  # tongue
    box_at(m, "head", [0, 15.5, -7.0], [4.5, 0.9, 4.6], BAND)                                 # headband
    box_at(m, "head", [0, 15.5, -9.35], [2.0, 1.0, 0.3], STEEL)                               # Leaf plate
    for sx, bone in ((1, "rightArm"), (-1, "leftArm")):                                       # front legs
        tube(m, bone, [[sx * 1.7, 9.6, -3.6], [sx * 1.75, 4.8, -3.9], [sx * 1.75, 1.3, -4.0]], [0.95, 0.72, 0.66], FUR)
        box_at(m, bone, [sx * 1.75, 0.6, -4.5], [1.5, 1.2, 1.9], CREAM)                       # paw
    for sx, bone in ((1, "rightLeg"), (-1, "leftLeg")):                                       # hind legs: thigh, hock, paw
        blob(m, bone, [sx * 1.8, 9.0, 3.9], [1.25, 2.0, 1.6], FUR, slices=3)
        tube(m, bone, [[sx * 1.8, 7.6, 4.4], [sx * 1.9, 4.2, 5.2], [sx * 1.9, 1.3, 4.6]], [0.85, 0.66, 0.62], FUR)
        box_at(m, bone, [sx * 1.9, 0.6, 4.1], [1.5, 1.2, 1.9], CREAM)
    curve_tube(m, "tails", [[0, 11.6, 5.0], [0, 13.8, 6.4], [0, 15.2, 5.4], [0, 14.6, 3.8]], 0.9, 0.5, [FUR, CREAM], n=2)  # curled tail
    return m


def flame_tiger():
    """Rengoku's Fifth Form: a tiger made of flame — glowing orange body with red stripes, a roaring open jaw, four
    legs mid-leap and a whipping tail of fire. Faces -z."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 10, 0], "head": [0, 13, -7], "jaw": [0, 12.4, -10], "rightArm": [2.2, 9.6, -4.6],
                      "leftArm": [-2.2, 9.6, -4.6], "rightLeg": [2.2, 10, 4.6], "leftLeg": [-2.2, 10, 4.6], "tails": [0, 11.5, 6.2]})
    F, F2, R, W = S.swatch((255, 150, 40), 200), S.swatch((255, 200, 80), 185), S.swatch((210, 50, 20), 215), S.swatch((255, 245, 210), 220)
    blob(m, "body", [0, 10.4, 0.5], [3.0, 2.8, 6.2], F, slices=5, axis="z")
    blob(m, "body", [0, 10.6, -3.6], [3.3, 3.2, 2.8], F2, slices=4)                          # chest
    for k in range(5):                                                                        # stripes
        S.obox(m, "body", [0, 12.8, -2.0 + k * 1.9], [5.2, 0.8, 0.6], R, (0, 1, 0), 0, [1, 0, 0])
    blob(m, "head", [0, 14.0, -8.0], [2.6, 2.4, 2.6], F, slices=4)
    blob(m, "head", [0, 13.0, -10.4], [1.6, 1.2, 1.6], F2, slices=3, axis="z")              # muzzle
    for sx in (1, -1):
        blade(m, "head", [sx * 1.7, 16.0, -7.6], [sx * 0.3, 1, 0.1], 2.0, 1.6, 0.5, R, width_dir=[0, 0, 1])   # ears
        box_at(m, "head", [sx * 1.1, 14.9, -10.2], [0.6, 0.5, 0.3], W)                         # blazing eyes
        blade(m, "jaw", [sx * 0.7, 12.2, -11.2], [0, 1, 0], 1.0, 0.4, 0.3, W)                 # fangs
    blob(m, "jaw", [0, 11.9, -10.6], [1.3, 0.5, 1.6], R, slices=2, axis="z")                 # open lower jaw
    for sx, bone in ((1, "rightArm"), (-1, "leftArm")):
        tube(m, bone, [[sx * 2.2, 9.6, -4.6], [sx * 2.3, 5, -6.2], [sx * 2.3, 1.4, -7.4]], [1.3, 1.0, 0.9], F)
        blob(m, bone, [sx * 2.3, 0.9, -7.8], [1.2, 0.8, 1.4], F2, slices=2)
    for sx, bone in ((1, "rightLeg"), (-1, "leftLeg")):
        blob(m, bone, [sx * 2.2, 9.6, 4.8], [1.5, 2.4, 1.9], F, slices=3)
        tube(m, bone, [[sx * 2.2, 8, 5.2], [sx * 2.3, 4, 7.0], [sx * 2.3, 1.2, 6.2]], [1.0, 0.8, 0.8], F)
    curve_tube(m, "tails", [[0, 11.5, 6.2], [0, 13.5, 9.4], [0, 16.5, 11.0], [0, 18.0, 10.2]], 0.9, 0.3, [F, R], n=2)
    for k in range(6):                                                                        # flames licking off its back
        blade(m, "body", [(k % 2 - 0.5) * 2.4, 13.2, -3 + k * 1.6], [(k % 2 - 0.5) * 0.4, 1, 0.3], 3.2, 1.4, 0.5, F2)
    return m


def yoyo():
    """Killua's yo-yo: two heavy steel discs on an axle with a dark rim — each one weighs 50 kg. Built small; the
    'spin' animation rolls it about its axle."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 4, 0]})
    STEEL, RIM, CORE = S.swatch((200, 204, 214)), S.swatch((60, 64, 80)), S.swatch((110, 90, 160))
    for sx in (1, -1):
        blob(m, "body", [sx * 0.9, 4, 0], [0.7, 3.0, 3.0], STEEL, slices=3, axis="x")      # the two discs
        blob(m, "body", [sx * 1.4, 4, 0], [0.25, 3.1, 3.1], RIM, slices=2, axis="x")       # their dark outer rims
        box_at(m, "body", [sx * 1.7, 4, 0], [0.3, 1.2, 1.2], CORE)                           # purple centre caps
    box_at(m, "body", [0, 4, 0], [1.2, 0.8, 0.8], RIM)                                       # axle
    return m


def fire_fist(cols=None):
    """Ace's Hiken: a giant fist made of flame, knuckles forward (-z), trailing fire behind it."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 8, 0], "tails": [0, 8, 6]})
    c1, c2, c3 = cols or ((255, 150, 40), (255, 214, 100), (220, 60, 20))
    F, F2, R = S.swatch(c1, 210), S.swatch(c2, 200), S.swatch(c3, 220)
    blob(m, "body", [0, 8, 0.5], [4.2, 3.8, 3.4], F, slices=5, axis="z")                     # back of the hand
    for k, x in enumerate((-2.7, -0.9, 0.9, 2.7)):                                           # four curled fingers
        blob(m, "body", [x, 9.6, -3.0], [0.95, 1.2, 1.4], F2, slices=3, axis="z")            # knuckle
        tube(m, "body", [[x, 9.4, -3.6], [x, 7.6, -4.4], [x, 5.8, -3.6]], [0.9, 0.85, 0.8], F, knuckles=False)
    tube(m, "body", [[-4.0, 7.0, -0.5], [-3.6, 5.6, -2.8], [-1.8, 5.2, -4.0]], [1.0, 0.9, 0.8], F2, knuckles=False)  # thumb
    curve_tube(m, "body", [[0, 8, 3.5], [0, 8, 6.5]], 3.0, 2.6, F, n=1)                      # wrist
    for k in range(8):                                                                        # flames streaming back
        a = 2 * math.pi * k / 8
        blade(m, "tails", [math.cos(a) * 2.6, 8 + math.sin(a) * 2.6, 6], [math.cos(a) * 0.3, math.sin(a) * 0.3, 1], 6 + (k % 3) * 2, 2.2, 0.6, R if k % 2 else F2)
    return m


def ofa_fist():
    """Deku's Detroit Smash: the same giant fist, made of One For All's green wind."""
    return fire_fist(((110, 240, 140), (210, 255, 220), (40, 160, 80)))


def _ghost(fn, k=0.38):
    """A see-through Susanoo: every part keeps its colour but only ~38% of its opacity, so the fighter standing in its
    chest stays clearly visible."""
    def build():
        m = fn()
        for c in m.cubes:
            p = c["paint"]
            sw = getattr(p, "swatch", None)
            if sw:
                c["paint"] = S.swatch(sw[0], max(40, int(sw[1] * k)))
                continue

            def faded(face, img, _p=p):
                _p(face, img)
                px = img.load()
                w, h = img.size
                for y in range(h):
                    for x in range(w):
                        r, g, b, a = px[x, y]
                        if a:
                            px[x, y] = (r, g, b, max(40, int(min(a, 235) * k)))
            c["paint"] = faded
        return m
    build.__name__ = fn.__name__
    return build


SUMMONS = [("susanoo", _ghost(susanoo_perfect)), ("kurama", kurama), ("gamabunta", gamabunta),
           ("susanoo_ribs", _ghost(susanoo_ribs)), ("susanoo_armour", _ghost(susanoo_armour)), ("muzan_infant", muzan_infant), ("mahoraga", mahoraga),
           ("susanoo_madara", _ghost(susanoo_madara)), ("susanoo_itachi", _ghost(susanoo_itachi)), ("susanoo_kakashi", _ghost(susanoo_kakashi)),
           ("crow", crow), ("hound", hound), ("flame_tiger", flame_tiger), ("yoyo", yoyo), ("fire_fist", fire_fist), ("ofa_fist", ofa_fist)]
SOLID = {"gamabunta", "muzan_infant", "mahoraga", "crow", "hound", "yoyo"}   # opaque flesh; the rest are glowing chakra
