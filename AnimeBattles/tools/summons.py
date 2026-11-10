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
               "rightWing": "body", "leftWing": "body", "tails": "body"}
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
                      "rightWing": [0, 30, 0], "leftWing": [0, 30, 0], "tails": [0, 24, 14]})
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
    tube(m, "head", [[0, 36.8, -26], [0, 35.8, -31], [0, 34.8, -35]], [4.6, 3.4, 2.4], fur, flat=0.85)   # muzzle
    box_at(m, "head", [0, 35.6, -36.3], [3, 2.2, 2], ink)                                            # nose
    tube(m, "head", [[0, 32.6, -24], [0, 32.1, -33]], [3.4, 2], deep, flat=0.8)                      # lower jaw
    box_at(m, "head", [0, 33.6, -30], [7, 0.6, 9], ink)                                              # mouth line
    for s in (1, -1):
        for z in (-29, -32):
            box_at(m, "head", [s * 1.9, 32.9, z], [0.8, 1.7, 0.8], alpha(smooth((250, 246, 232)), 255))   # fangs
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
                      "rightWing": [0, 30, 0], "leftWing": [0, 30, 0], "tails": [0, 16, 14]})
    SK, BELLY, VEST = (188, 80, 46), (234, 200, 146), (62, 58, 146)
    skin = flesh(SK)
    darker = flesh(dark(SK, 0.8))
    blob(m, "body", [0, 18, 4], [20, 13, 18], skin, slices=7)                                      # body
    blob(m, "body", [0, 12.5, -8], [15, 8, 8], smooth(BELLY), slices=4)                           # pale belly
    blob(m, "head", [0, 25, -14], [19, 8, 12], skin, slices=7, axis="x")                           # wide flat head
    blob(m, "head", [0, 19.6, -17.5], [13, 2.6, 7], smooth(BELLY), slices=3, axis="x")            # chin
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
    tube(m, "body", [[21.5, 17, 10], [23.5, 12, -6]], [1.3, 1.2], smooth((80, 50, 30)))          # the dosu at his side
    box_at(m, "body", [21.3, 17.6, 11.6], [3.6, 1.2, 3.6], smooth((200, 170, 90)))
    return m


# ------------------------------------------------------------------ Muzan's giant infant form (manga, chapter 200)
def muzan_infant():
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 18, 0], "head": [0, 30, -6], "rightArm": [11, 26, -4], "leftArm": [-11, 26, -4],
                      "rightWing": [0, 30, 0], "leftWing": [0, 30, 0], "tails": [0, 16, 8]})
    SKIN_P, VEIN = (234, 198, 188), (176, 26, 40)
    skin = smooth(SKIN_P, [speckle(VEIN, 13), stripes(dark(SKIN_P, 0.85), 9, "x")])
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
    box_at(m, "head", [0, 30.8, -13.6], [7.4, 1.8, 0.6], smooth((60, 6, 14)))                    # the fanged mouth
    for x in range(-3, 4):
        box_at(m, "head", [x * 1.05, 31.6 - (x % 2) * 0.9, -14], [0.6, 1.0, 0.4], smooth((250, 246, 236)))
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


SUMMONS = [("susanoo", susanoo_perfect), ("kurama", kurama), ("gamabunta", gamabunta),
           ("susanoo_ribs", susanoo_ribs), ("susanoo_armour", susanoo_armour), ("muzan_infant", muzan_infant)]
SOLID = {"gamabunta", "muzan_infant"}   # opaque flesh; the rest are glowing chakra
