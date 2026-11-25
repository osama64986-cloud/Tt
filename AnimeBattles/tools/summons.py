"""Giant constructs, sculpted from hundreds of small cubes (see sculpt.py):
0 Perfect Susanoo, 1 Kurama, 2 Gamabunta, 3 Susanoo ribcage (Mangekyo), 4 armoured Susanoo (Eternal Mangekyo),
5 Muzan's giant infant form. Built at model scale, grown in game through `ab:size`."""
import math

import models as M
from models import dark, layered, light, _put, solid, lines, SIDES
from chars_extra import region
import sculpt as S
from sculpt import blob, box_at, chakra, curve_tube, tube, blade, spline, flesh, stripes, speckle, rim, alpha, smooth

PUR, PUR_D, PUR_L = (146, 78, 228), (86, 40, 160), (222, 196, 255)


def _bones(pivots):
    parents = {"body": "root", "head": "body", "rightArm": "body", "leftArm": "body",
               "rightWing": "body", "leftWing": "body", "tails": "body", "jaw": "head", "wheel": "head",
               "rightWingTip": "rightWing", "leftWingTip": "leftWing", "rightLeg": "body", "leftLeg": "body", "sword": "rightArm"}
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
def _seg_box(m, bone, p, d, w, L, paint):
    """One square segment of length L along direction d from point p (the hair-strand rotation)."""
    d = M.norm(d)
    ax, az = math.degrees(math.asin(max(-1, min(1, d[2])))), math.degrees(math.atan2(-d[0], d[1]))
    m.box(bone, [p[0] - w / 2, p[1], p[2] - w / 2], [w, L, w], paint, rot=[round(ax, 2), 0, round(az, 2)],
          pivot=[round(p[0], 3), round(p[1], 3), round(p[2], 3)])
    return [p[k] + d[k] * L * 0.8 for k in range(3)]


def kurama():
    """Kurama, the Nine-Tailed Fox, in the mod's clean block style (opaque, like Mahoraga): an orange fox with a LONG
    muzzle and black nose, a black mask round red slit eyes running back over the crown to the ears, big pointed ears
    black inside, white fangs, a neck ruff, clean black lines on the limbs, and exactly nine thick tails fanned out
    behind in three rows, each tapering in six segments to a lighter tip. Faces -z."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 24, 0], "head": [0, 36, -16], "rightArm": [10, 30, -12], "leftArm": [-10, 30, -12],
                      "rightWing": [0, 30, 0], "leftWing": [0, 30, 0], "tails": [0, 24, 14], "jaw": [0, 33.6, -22]})
    OR, SH, LI, BLK = (240, 140, 40), (206, 104, 26), (255, 196, 110), (34, 24, 22)
    WHT, RED = (248, 244, 232), (200, 34, 30)

    def stripes_on(faces, fys, col=BLK):
        def p(face, px, w, h, base):
            if face in faces:
                for fy in fys:
                    for x in range(w):
                        _put(px, w, h, x, int(h * fy), col); _put(px, w, h, x, int(h * fy) + 1, col)
        return p
    fur = solid(OR)
    body = layered(OR, [stripes_on(("east", "west"), (0.3, 0.55))])
    # body: deep chest, long barrel, neck ruff
    m.box("body", [-11, 18, -19], [22, 20, 17], body)
    m.box("body", [-10, 15, -3], [20, 17, 20], layered(OR, [stripes_on(("east", "west"), (0.35, 0.6))]))
    m.box("body", [-9.5, 14, -17], [19, 5, 30], solid(SH))                                  # the paler belly underneath
    m.box("body", [-10, 30, -24], [20, 10, 7], solid(SH))                                   # neck ruff
    for s_ in (1, -1):
        m.box("body", [s_ * 9 - 2, 31, -25], [4, 7, 4], solid(OR), rot=[0, 0, -s_ * 25], pivot=[s_ * 9, 33, -23])

    # head: skull with the black mask, the long muzzle, nose, eyes, brows, cheek tufts and ears
    def skull_paint(face, px, w, h, base):
        if face == "north":  # black mask patches round the eyes
            for y in range(int(h * 0.28), int(h * 0.58)):
                for x in range(w):
                    if 0.06 < x / w < 0.42 or 0.58 < x / w < 0.94:
                        _put(px, w, h, x, y, BLK)
        if face == "up":  # two black lines running back from the eyes over the crown to the ears
            for y in range(h):
                for fx in (0.22, 0.26, 0.74, 0.78):
                    _put(px, w, h, int(w * fx), y, BLK)
    m.box("head", [-8, 31, -31], [16, 14, 14], layered(OR, [skull_paint]))
    m.box("head", [-4.2, 32.6, -40], [8.4, 6.0, 9.5], layered(OR, [lines((("up",), [[(0.5, 0), (0.5, 1)]]), SH)]))   # muzzle
    m.box("head", [-3.2, 33.2, -43], [6.4, 4.8, 3.2], fur)                                 # muzzle tip
    m.box("head", [-1.7, 36.4, -43.8], [3.4, 2.2, 1.6], solid(BLK))                       # nose
    m.box("head", [-3.0, 32.4, -42.6], [6.0, 0.6, 10.0], solid((150, 24, 30)))            # mouth line / gum
    for s_ in (1, -1):
        ex = s_ * 4.2
        m.box("head", [ex - 2.2, 37.2, -31.6], [4.4, 2.6, 0.7], solid(WHT))               # sclera
        m.box("head", [ex - 1.2, 37.2, -31.9], [2.4, 2.6, 0.7], solid(RED))               # red iris
        m.box("head", [ex - 0.3, 37.2, -32.1], [0.6, 2.6, 0.6], solid(BLK))               # slit pupil
        m.box("head", [ex - 2.8, 40.2, -31.8], [5.6, 1.0, 1.0], solid(BLK), rot=[0, 0, s_ * 14], pivot=[ex, 40.6, -31.3])  # brow
        m.box("head", [s_ * 2.4 - 0.45, 30.0, -42.2], [0.9, 3.0, 0.9], solid(WHT))        # the long fangs
        for k in range(4):
            m.box("head", [s_ * (2.9 - k * 0.1) - 0.3, 31.4, -40.5 + k * 2.2], [0.6, 1.2, 0.6], solid(WHT))
        m.box("head", [s_ * 8.6 - 2, 31.5, -28], [4, 6, 7], fur, rot=[0, 0, -s_ * 22], pivot=[s_ * 8, 34, -24])  # cheek tufts
        def ear_shape(xf, u):  # a tall triangle: orange rim, black inside, black tip
            half = 0.5 * (1 - u) ** 0.9
            dd = abs(xf - 0.5)
            if dd > half:
                return None
            return BLK if u > 0.78 or (dd < half * 0.55 and u < 0.85) else OR
        ear = M._sprite(ear_shape)
        m.box("head", [s_ * 5.0 - 4.5, 44.0, -23.0], [9.0, 13.0, 0], ear, rot=[-10, 0, -s_ * 16], pivot=[s_ * 5.0, 44.0, -23.0])
        m.cubes[-1]["hires"] = 2
        m.box("head", [s_ * 5.0 - 4.0, 43.6, -24.2], [8.0, 3.0, 2.4], fur, rot=[0, 0, -s_ * 16], pivot=[s_ * 5.0, 44.0, -23.0])
    m.box("jaw", [-3.6, 29.4, -41.5], [7.2, 3.0, 11.0], solid(SH))                         # lower jaw
    m.box("jaw", [-3.0, 32.2, -41.0], [6.0, 0.4, 10.0], solid((190, 60, 70)))             # tongue
    for s_ in (1, -1):
        m.box("jaw", [s_ * 2.2 - 0.4, 32.0, -41.2], [0.8, 2.0, 0.8], solid(WHT))          # lower fangs

    # legs: blocky, clean black lines, black claws
    leg = layered(OR, [stripes_on(SIDES, (0.25, 0.5))])
    for s_, bone in ((1, "rightArm"), (-1, "leftArm")):
        m.box(bone, [s_ * 11 - 3.5, 6, -22], [7, 26, 8], leg)                              # foreleg
        m.box(bone, [s_ * 11 - 4, 0, -26], [8, 6, 11], fur)                                 # paw
        for k in (-1, 0, 1):
            m.box(bone, [s_ * 11 + k * 2.4 - 0.5, 0, -27.6], [1.0, 1.6, 1.8], solid(BLK))  # claws
    for s_ in (1, -1):
        m.box("body", [s_ * 10 - 4.5, 8, 4], [9, 14, 13], layered(OR, [stripes_on(("east", "west"), (0.4,))]))  # haunch
        m.box("body", [s_ * 10 - 2.5, 2, 12], [5, 8, 5], leg)                              # hind shin
        m.box("body", [s_ * 10 - 3, 0, 6], [6, 3, 9], fur)                                  # hind paw
        for k in (-1, 0, 1):
            m.box("body", [s_ * 10 + k * 2 - 0.5, 0, 4.4], [1.0, 1.4, 1.6], solid(BLK))

    # nine thick tails, three rows of three, each curling up and out and tapering to a lighter tip
    tail_c = solid(OR)
    tip_c = solid(LI)
    for row, (up, back) in enumerate(((1.0, 0.35), (0.6, 0.8), (0.2, 1.0))):
        for k, yaw in enumerate((-1, 0, 1)):
            spread = yaw * (0.55 + row * 0.25)
            p = [yaw * 2.5, 27 - row * 2.5, 16]
            d = [spread, up, back]
            for i, w in enumerate((8.0, 7.4, 6.6, 5.6, 4.6, 3.4)):
                p = _seg_box(m, "tails", p, d, w, 7.5, tip_c if i == 5 else tail_c)
                d = [d[0] + spread * 0.3, d[1] + 0.18, d[2] - 0.25]
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
    """Eight-Handled Sword Divergent Sila Divine General Mahoraga, built in the mod's clean block style (like the
    fighters): a tall, athletic, pale-white body whose muscles are PAINTED on (pecs, abs, arms) instead of lumpy blobs;
    a tall eyeless head with ridges up its face and a wide painted grin of teeth; two pairs of broad wing-horns sweeping
    out from where its eyes would be; the golden eight-handled wheel lying FLAT above its head on a short post, eight
    spokes and eight knobs; a black ring-chain necklace with tassels; black cloth at the waist and black wrist bands;
    the Sword of Extermination on its right forearm. Faces -z."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 20, 0], "head": [0, 41, 0], "rightArm": [10.6, 37, 0], "leftArm": [-10.6, 37, 0],
                      "rightWing": [0, 30, 0], "leftWing": [0, 30, 0], "tails": [0, 20, 6], "jaw": [0, 42, -2], "wheel": [0, 55, 0], "sword": [13.7, 23, 0]})
    SKC, MUS, RID = (232, 232, 236), (176, 176, 186), (150, 150, 162)
    BLKC = (30, 30, 34)

    def line_h(px, w, h, fy, x0, x1, col, curve=0.0):
        for x in range(int(w * x0), int(w * x1)):
            t = (x / max(1, w - 1)) - 0.5
            _put(px, w, h, x, int(h * fy + curve * h * (t * t * 4 - 1)), col)

    def line_v(px, w, h, fx, y0, y1, col):
        for y in range(int(h * y0), int(h * y1)):
            _put(px, w, h, int(w * fx), y, col)

    def chest_paint(face, px, w, h, base):  # pecs, the line between them, and the top of the abs
        if face == "north":
            line_h(px, w, h, 0.44, 0.08, 0.48, MUS, curve=0.04); line_h(px, w, h, 0.44, 0.52, 0.92, MUS, curve=0.04)
            line_v(px, w, h, 0.5, 0.05, 1.0, MUS)
            for fy in (0.66, 0.86):
                line_h(px, w, h, fy, 0.3, 0.7, MUS)
            for fx in (0.3, 0.7):
                line_v(px, w, h, fx, 0.5, 1.0, MUS)
        elif face in ("east", "west"):
            for fy in (0.55, 0.7, 0.85):  # serratus ribs
                line_h(px, w, h, fy, 0.2, 0.6, MUS)

    def waist_paint(face, px, w, h, base):  # the lower abs and the V-lines of the hips
        if face == "north":
            line_v(px, w, h, 0.5, 0, 1.0, MUS)
            line_h(px, w, h, 0.4, 0.3, 0.7, MUS)
            for fx in (0.3, 0.7):
                line_v(px, w, h, fx, 0, 0.85, MUS)
            for k in range(int(h * 0.5), h):
                _put(px, w, h, int(w * 0.18) + (k - int(h * 0.5)) // 2, k, MUS)
                _put(px, w, h, int(w * 0.82) - (k - int(h * 0.5)) // 2, k, MUS)

    def arm_paint(face, px, w, h, base):  # bicep / tricep split
        if face in ("north", "south"):
            line_v(px, w, h, 0.5, 0.15, 0.85, MUS)

    def head_paint(face, px, w, h, base):  # ridges up the eyeless face, and the wide grin of teeth
        if face == "north":
            for fx in (0.32, 0.5, 0.68):
                line_v(px, w, h, fx, 0.0, 0.46, RID)
            for fx in (0.14, 0.86):
                line_v(px, w, h, fx, 0.2, 0.55, RID)
            y0, y1, x0, x1 = int(h * 0.56), int(h * 0.82), int(w * 0.14), int(w * 0.86)
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    edge = y in (y0, y1) or x in (x0, x1)
                    _put(px, w, h, x, y, (30, 28, 32) if edge else (246, 246, 240))
            for x in range(x0 + 1, x1):  # the thin seam between the upper and lower teeth
                _put(px, w, h, x, (y0 + y1) // 2, (150, 150, 156))
            for k in range(1, 5):  # four gaps: five big teeth
                xx = x0 + (x1 - x0) * k // 5
                for y in range(y0, y1 + 1):
                    _put(px, w, h, xx, y, (90, 88, 96))
            for fx in (0.36, 0.5, 0.64):
                line_v(px, w, h, fx, 0.84, 1.0, RID)

    def cloth_paint(face, px, w, h, base):  # folds in the black cloth
        for fx in (0.25, 0.5, 0.75):
            line_v(px, w, h, fx, 0.1, 1.0, (52, 52, 58))

    SKIN_ = layered(SKC, [])
    # legs in loose black trousers, white feet
    for s_ in (1, -1):
        m.box("body", [s_ * 3.1 - 2.9, 2.0, -2.9], [5.8, 16.5, 5.8], layered(BLKC, [cloth_paint]))
        m.box("body", [s_ * 3.1 - 2.7, 0.0, -3.9], [5.4, 2.0, 6.8], SKIN_)
    m.box("body", [-6.6, 14.0, -3.6], [13.2, 6.0, 7.2], layered(BLKC, [cloth_paint]))              # the black cloth round its hips
    m.box("body", [-6.8, 19.4, -3.8], [13.6, 1.8, 7.6], layered((54, 54, 60), []))                  # the black sash
    # an athletic V-shaped torso
    m.box("body", [-5.2, 21.0, -3.0], [10.4, 4.6, 6.0], layered(SKC, [waist_paint]))               # narrow waist
    m.box("body", [-7.6, 25.4, -3.7], [15.2, 11.8, 7.4], layered(SKC, [chest_paint]))              # broad chest
    m.box("body", [-5.0, 37.0, -2.8], [10.0, 2.2, 5.8], SKIN_)                                     # traps
    m.box("body", [-2.6, 38.6, -2.6], [5.2, 3.0, 5.2], SKIN_)                                      # neck
    # the black ring-chain necklace across the chest, with tassels
    pts = [(-6.6, 36.2), (-4.9, 35.2), (-3.2, 34.5), (-1.6, 34.1), (0, 34.0), (1.6, 34.1), (3.2, 34.5), (4.9, 35.2), (6.6, 36.2)]
    for k, (x, y) in enumerate(pts):
        if k < len(pts) - 1:  # the cord between rings
            x2, y2 = pts[k + 1]
            ang = math.degrees(math.atan2(y2 - y, x2 - x))
            box_at(m, "body", [(x + x2) / 2, (y + y2) / 2, -3.85], [math.hypot(x2 - x, y2 - y), 0.45, 0.3], solid(BLKC), rot=[0, 0, ang])
        if k % 2 == 0:
            box_at(m, "body", [x, y, -3.95], [1.4, 1.4, 0.4], solid(BLKC))                          # ring
            box_at(m, "body", [x, y, -4.1], [0.55, 0.55, 0.2], SKIN_)                               # the hole of the ring
        if k in (1, 3, 5, 7):
            box_at(m, "body", [x, y - 1.3, -3.9], [0.5, 1.8, 0.3], solid(BLKC))                     # tassel
            box_at(m, "body", [x, y - 2.4, -3.9], [0.9, 0.7, 0.3], solid(BLKC))
    box_at(m, "body", [0, 32.6, -4.0], [2.0, 1.5, 0.45], solid(BLKC))                               # the centre piece
    box_at(m, "body", [0, 31.0, -3.95], [0.7, 2.0, 0.35], solid(BLKC))
    # the tall, eyeless head
    m.box("head", [-3.5, 41.0, -3.5], [7.0, 9.6, 7.0], layered(SKC, [head_paint]))
    m.box("head", [-3.0, 50.6, -3.0], [6.0, 1.0, 6.0], SKIN_)                                      # the rounded crown
    # two pairs of broad wing-horns sweeping out and up from where its eyes would be
    for s_ in (1, -1):
        for k, (up, L, w) in enumerate(((0.8, 13.0, 3.0), (0.32, 11.0, 2.6))):
            base = [s_ * 1.2, 47.0 - k * 1.4, -3.6]
            d = [s_ * 1.0, up, -0.2]
            blade(m, "head", base, d, L, w, 0.9, smooth((236, 236, 240)), width_dir=[0, 0.35, 1])
            blade(m, "head", [base[0] + s_ * 0.6, base[1] + 0.25, base[2] - 0.5], d, L * 0.85, w * 0.2, 0.3, smooth(RID), width_dir=[0, 0.35, 1])
    # the golden eight-handled wheel lying FLAT above its head on a short post
    GOLD, GOLD2 = layered((176, 142, 74), []), layered((204, 172, 104), [])
    m.box("head", [-0.6, 51.6, -0.6], [1.2, 3.2, 1.2], GOLD)                                     # post
    R, cy = 6.4, 55.0
    for i in range(16):  # the rim: 16 straight segments round the circle
        a = (i + 0.5) * math.pi / 8
        box_at(m, "wheel", [math.cos(a) * R, cy, math.sin(a) * R], [2.6, 0.9, 0.9], GOLD, rot=[0, -math.degrees(a) + 90, 0])
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        box_at(m, "wheel", [math.cos(a) * R / 2, cy, math.sin(a) * R / 2], [R, 0.6, 0.6], GOLD, rot=[0, -math.degrees(a), 0])          # spoke
        box_at(m, "wheel", [math.cos(a) * (R + 1.0), cy, math.sin(a) * (R + 1.0)], [1.6, 0.5, 0.5], GOLD, rot=[0, -math.degrees(a), 0])  # handle
        box_at(m, "wheel", [math.cos(a) * (R + 2.4), cy, math.sin(a) * (R + 2.4)], [2.2, 2.2, 2.2], GOLD2)                              # knob
    box_at(m, "wheel", [0, cy, 0], [2.0, 1.2, 2.0], GOLD2)
    # strong, lean arms: deltoid, upper arm, forearm, black wrist band, fist
    for s_, bone in ((1, "rightArm"), (-1, "leftArm")):
        cx = s_ * 10.6
        m.box(bone, [cx - 3.2, 33.0, -3.2], [6.4, 5.0, 6.4], SKIN_)                                # deltoid
        m.box(bone, [cx - 2.7, 27.0, -2.7], [5.4, 6.4, 5.4], layered(SKC, [arm_paint]))            # upper arm
        m.box(bone, [cx - 2.5, 20.6, -2.5], [5.0, 6.6, 5.0], SKIN_)                                # forearm
        m.box(bone, [cx - 2.8, 18.8, -2.8], [5.6, 2.0, 5.6], solid(BLKC))                          # black wrist band
        m.box(bone, [cx - 2.4, 15.0, -2.4], [4.8, 3.8, 4.8], SKIN_)                                # fist
    # the Sword of Extermination grows out of the SKIN on the back of the right forearm, just above the wrist: the blade
    # runs down alongside the fist and past it (it never sits in the hand). Two crossed painted sheets; the "sword" bone
    # grows it out of the arm when Mahoraga appears.
    L, W, top = 22.0, 5.0, 23.0
    bx = 10.6 + 3.1  # the outer (back) side of the forearm

    def blade_paint(face, img):
        w, h = img.size
        if w < 2 or h < 2:
            return
        px = img.load()
        ink, steel, spine, edge, fuller = (34, 34, 44), (204, 210, 224), (150, 156, 172), (248, 250, 255), (112, 118, 134)
        for y in range(h):
            t = y / (h - 1)
            frac = 1.0 if t < 0.72 else max(0.0, 1 - (t - 0.72) / 0.28)  # the edge sweeps in to the point
            xe = max(0, int(round((w - 1) * frac)))
            for x in range(w):
                if x > xe:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                if x == 0 or x == xe or y == h - 1 or y == 0:
                    c = ink
                elif x == 1:
                    c = spine
                elif x >= xe - 1:
                    c = edge
                elif x == max(2, int(w * 0.36)) and t < 0.7:
                    c = fuller
                else:
                    c = steel
                px[x, y] = c + (255,)

    m.box("sword", [bx, top - L, -W / 2], [0, L, W], blade_paint)                     # sheet seen from the side
    m.cubes[-1]["hires"] = 2
    m.box("sword", [bx - W / 2 + 0.4, top - L, 0], [W - 0.8, L, 0], blade_paint)      # sheet seen from the front
    m.cubes[-1]["hires"] = 2
    m.box("rightArm", [10.6 + 2.4, 21.6, -1.4], [1.0, 2.6, 2.8], layered((176, 176, 186), []))  # the split in the skin it grows from
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


def hound(fur=(178, 118, 62), cream=(238, 216, 178), dark=(92, 60, 38), ninja=True, big=1.0):
    """Kakashi's ninja hound: a compact, sharp-eared tan dog with a cream muzzle and chest, tongue out, a curled
    tail, a navy vest and the Leaf headband; four slim legs with paws (front and hind legs move). Faces -z."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 10, 0], "head": [0, 12.6, -5.8], "jaw": [0, 13.0, -8.4], "rightArm": [1.7, 9.6, -3.6],
                      "leftArm": [-1.7, 9.6, -3.6], "rightLeg": [1.8, 10.0, 3.8], "leftLeg": [-1.8, 10.0, 3.8], "tails": [0, 11.6, 5.0]})
    FUR, CREAM, DARK, NOSE, PINK = smooth(fur), smooth(cream), smooth(dark), smooth((24, 20, 22)), smooth((226, 110, 120))
    NAVY, STEEL, BAND = smooth((44, 54, 92)), smooth((198, 204, 214)), smooth((34, 40, 70))
    blob(m, "body", [0, 10.2, 0.4], [2.5, 2.4, 5.2], FUR, slices=5, axis="z")                 # body
    blob(m, "body", [0, 10.4, -3.2], [2.7, 2.7, 2.2], FUR, slices=4)                          # chest
    blob(m, "body", [0, 9.4, -3.4], [1.9, 2.0, 1.8], CREAM, slices=3)                         # cream chest
    if ninja:
        blob(m, "body", [0, 11.6, -0.6], [2.7, 1.3, 3.0], NAVY, slices=3, axis="z")          # ninja vest over the back
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
    if ninja:
        box_at(m, "head", [0, 15.5, -7.0], [4.5, 0.9, 4.6], BAND)                             # headband
        box_at(m, "head", [0, 15.5, -9.35], [2.0, 1.0, 0.3], STEEL)                           # Leaf plate
    for sx, bone in ((1, "rightArm"), (-1, "leftArm")):                                       # front legs
        tube(m, bone, [[sx * 1.7, 9.6, -3.6], [sx * 1.75, 4.8, -3.9], [sx * 1.75, 1.3, -4.0]], [0.95, 0.72, 0.66], FUR)
        box_at(m, bone, [sx * 1.75, 0.6, -4.5], [1.5, 1.2, 1.9], CREAM)                       # paw
    for sx, bone in ((1, "rightLeg"), (-1, "leftLeg")):                                       # hind legs: thigh, hock, paw
        blob(m, bone, [sx * 1.8, 9.0, 3.9], [1.25, 2.0, 1.6], FUR, slices=3)
        tube(m, bone, [[sx * 1.8, 7.6, 4.4], [sx * 1.9, 4.2, 5.2], [sx * 1.9, 1.3, 4.6]], [0.85, 0.66, 0.62], FUR)
        box_at(m, bone, [sx * 1.9, 0.6, 4.1], [1.5, 1.2, 1.9], CREAM)
    if ninja:
        curve_tube(m, "tails", [[0, 11.6, 5.0], [0, 13.8, 6.4], [0, 15.2, 5.4], [0, 14.6, 3.8]], 0.9, 0.5, [FUR, CREAM], n=2)  # curled tail
    else:  # a wolf's bushy tail, held out straight
        curve_tube(m, "tails", [[0, 11.6, 5.0], [0, 11.0, 8.0], [0, 9.6, 10.6]], 1.2, 0.6, [FUR, FUR], n=2)
        for sx in (1, -1):  # a mane of rough fur at the neck
            blade(m, "body", [sx * 1.6, 12.4, -4.2], [sx * 0.6, 0.5, 0.3], 2.0, 1.4, 0.5, FUR)
        blade(m, "head", [0, 15.0, -5.2], [0, 0.6, 1], 2.4, 1.6, 0.5, FUR)
    if big != 1.0:
        for c in m.cubes:
            c["frm"] = [v * big for v in c["frm"]]; c["size"] = [v * big for v in c["size"]]
            if c.get("pivot"):
                c["pivot"] = [v * big for v in c["pivot"]]
    return m


def divine_dog_black():
    """Megumi's Divine Dog: Black — a big black wolf, no vest, a white muzzle and a wild ruff."""
    return hound((30, 30, 36), (210, 210, 216), (14, 14, 18), ninja=False)


def divine_dog_white():
    """Megumi's Divine Dog: White — a big white wolf with a dark muzzle tip."""
    return hound((236, 236, 240), (250, 250, 252), (180, 180, 190), ninja=False)


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


def nen_fist():
    """Gon's Jajanken: Rock — a giant fist of blazing yellow nen."""
    return fire_fist(((255, 222, 70), (255, 250, 200), (220, 160, 30)))


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
           ("crow", crow), ("hound", hound), ("flame_tiger", flame_tiger), ("yoyo", yoyo), ("fire_fist", fire_fist), ("ofa_fist", ofa_fist),
           ("dog_black", divine_dog_black), ("dog_white", divine_dog_white), ("nen_fist", nen_fist)]
SOLID = {"gamabunta", "muzan_infant", "mahoraga", "crow", "hound", "yoyo", "dog_black", "dog_white"}   # opaque flesh; the rest are glowing chakra


# ------------------------------------------------------------------ 1.22: Kaido's dragon, Netero's Bodhisattva, Aki's Fox Devil
def kaido_dragon():
    """Kaido's true form: an azure Eastern dragon. A long serpentine body of sky-blue scales coiling up from the ground,
    cream belly plates underneath, a black flame-like mane along its spine, branching orange-brown antlers, long black
    whiskers, yellow eyes and a jaw full of fangs. Faces -z; the jaw opens for Bolo Breath."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 24, 0], "head": [0, 34, -8], "jaw": [0, 33.6, -14], "tails": [0, 10, 26],
                      "rightArm": [5, 26, 2], "leftArm": [-5, 26, 2]})
    BLUE, BLUE_D, BELLY, MANE = S.swatch((110, 180, 236)), S.swatch((70, 130, 200)), S.swatch((236, 200, 130)), S.swatch((26, 24, 30))
    HORN, WHITE, YEL = S.swatch((196, 120, 70)), S.swatch((246, 244, 236)), S.swatch((255, 214, 60))
    path = [[0, 33.0, -8.0], [3.0, 29.0, 0.0], [-4.0, 22.0, 8.0], [5.0, 14.0, 16.0], [-2.0, 8.0, 24.0], [4.0, 5.0, 32.0], [8.0, 7.0, 40.0]]
    pts = curve_tube(m, "body", path, 3.6, 0.9, [BLUE, BLUE_D], n=3)
    curve_tube(m, "body", [[p[0], p[1] - 1.8, p[2]] for p in path[:-1]], 2.6, 0.8, [BELLY, BELLY], n=3)   # the belly plates
    for k in range(1, len(pts) - 2, 2):                                                    # the mane of black flame along its spine
        p = pts[k]
        blade(m, "body", [p[0], p[1] + 2.6, p[2]], [0.0, 1, 0.45], 3.6 - k * 0.05, 1.6, 0.5, MANE)
    blob(m, "head", [0, 36.0, -12.0], [3.6, 3.0, 4.0], BLUE, slices=4)                    # the skull
    blob(m, "head", [0, 35.0, -18.0], [2.6, 1.8, 4.0], BLUE, slices=3, axis="z")           # the long snout
    blob(m, "head", [0, 35.4, -21.8], [1.6, 1.3, 0.9], BLUE_D, slices=2)                   # the nose
    for sx in (1, -1):
        box_at(m, "head", [sx * 2.4, 37.0, -15.0], [0.9, 0.6, 0.6], YEL)                    # eyes
        box_at(m, "head", [sx * 2.3, 37.7, -15.0], [1.4, 0.4, 1.0], MANE)                   # the heavy brow
        curve_tube(m, "head", [[sx * 1.8, 38.2, -11.0], [sx * 3.4, 42.0, -8.0], [sx * 5.6, 45.0, -4.0], [sx * 6.6, 46.6, 0.0]], 0.7, 0.2, [HORN, HORN], n=2)
        curve_tube(m, "head", [[sx * 3.4, 42.0, -8.0], [sx * 5.8, 42.6, -9.0], [sx * 7.4, 44.4, -8.4]], 0.45, 0.15, [HORN, HORN], n=1)
        curve_tube(m, "head", [[sx * 2.0, 34.6, -21.0], [sx * 5.0, 34.0, -20.0], [sx * 9.0, 31.0, -15.0], [sx * 12.0, 27.0, -10.0]], 0.22, 0.12, [MANE, MANE], n=3)  # whiskers
        blade(m, "head", [sx * 1.6, 34.0, -20.4], [0, -1, -0.2], 1.0, 0.4, 0.3, WHITE)      # fangs
        blade(m, "jaw", [sx * 1.4, 33.4, -19.4], [0, 1, -0.1], 0.9, 0.4, 0.3, WHITE)
        tube(m, "rightArm" if sx > 0 else "leftArm", [[sx * 3.0, 26.0, 2.0], [sx * 6.0, 23.0, -1.0], [sx * 7.0, 20.0, -3.0]], [1.0, 0.8, 0.6], BLUE)
        for c in (-1, 0, 1):
            blade(m, "rightArm" if sx > 0 else "leftArm", [sx * 7.0 + c * 0.5, 20.0, -3.0], [c * 0.3, -0.6, -1], 1.4, 0.4, 0.3, WHITE)
    blob(m, "jaw", [0, 33.0, -17.6], [2.2, 0.8, 3.6], BELLY, slices=2, axis="z")           # the lower jaw
    for k in range(5):                                                                       # the mane behind its head
        blade(m, "head", [(k - 2) * 1.4, 37.6, -7.6], [(k - 2) * 0.2, 0.6, 1], 4.0, 1.4, 0.5, MANE)
    return m


def guanyin():
    """Netero's 100-Type Guanyin Bodhisattva: a towering golden Buddha of nen behind him — a calm face with long ears
    and a topknot, a halo, hands joined in prayer before the chest, two great arms with open palms (the First Hand
    comes down from above), and a fan of many more hands spread behind it like a thousand-armed aureole."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 20, 0], "head": [0, 30, 0], "rightArm": [8, 27, 0], "leftArm": [-8, 27, 0]})
    G, G2, G3 = S.swatch((255, 206, 70), 215), S.swatch((255, 232, 140), 205), S.swatch((214, 160, 40), 220)
    blob(m, "body", [0, 20.0, 0.0], [7.0, 9.0, 4.6], G, slices=5)                         # the robed body
    blob(m, "body", [0, 8.0, -1.0], [10.0, 3.6, 7.0], G3, slices=3)                        # folded legs on the lotus
    for k in range(10):                                                                     # the lotus petals
        a = 2 * math.pi * k / 10
        blade(m, "body", [math.cos(a) * 9.0, 5.0, math.sin(a) * 6.0 - 1.0], [math.cos(a) * 0.5, 1, math.sin(a) * 0.5], 4.0, 3.0, 0.5, G2)
    blob(m, "head", [0, 33.4, 0.0], [3.6, 4.2, 3.6], G2, slices=4)                         # the calm face
    blob(m, "head", [0, 38.4, 0.4], [1.8, 1.6, 1.8], G3, slices=2)                         # the topknot
    for sx in (1, -1):
        box_at(m, "head", [sx * 3.8, 32.0, 0.0], [0.8, 3.6, 1.2], G)                         # long ears
        box_at(m, "head", [sx * 1.4, 34.2, -3.5], [1.4, 0.3, 0.3], G3)                       # closed eyes
    for k in range(20):                                                                     # the halo
        a = 2 * math.pi * k / 20
        box_at(m, "head", [math.cos(a) * 6.6, 34.0 + math.sin(a) * 6.6, 4.2], [1.4, 1.4, 0.5], G3)
    for k in range(14):                                                                     # the fan of hands behind it
        a = math.pi * (0.08 + 0.84 * k / 13)
        d = [math.cos(a), math.sin(a) * 0.9 + 0.1, 0]
        base = [d[0] * 5.0, 24.0 + d[1] * 4.0, 4.0]
        end = [d[0] * 15.0, 22.0 + d[1] * 13.0, 5.0]
        tube(m, "body", [base, end], [0.9, 0.7], G2, knuckles=False)
        blob(m, "body", end, [1.3, 1.6, 0.4], G, slices=2)
    for k in range(2):                                                                      # hands joined in prayer
        box_at(m, "body", [0.0, 23.0 + k * 1.6, -5.0], [1.6, 2.4, 1.2], G2)
    for bone, sx in (("rightArm", 1), ("leftArm", -1)):                                    # the two great arms: open palms
        tube(m, bone, [[sx * 8.0, 27.0, 0.0], [sx * 10.0, 19.0, -2.0], [sx * 10.5, 11.0, -4.0]], [2.0, 1.7, 1.4], G)
        blob(m, bone, [sx * 10.6, 7.6, -4.8], [3.0, 3.8, 1.2], G2, slices=3)
        for f in range(4):
            box_at(m, bone, [sx * 10.6 + (f - 1.5) * 1.3, 3.0, -4.8], [1.0, 3.2, 1.0], G2)
    return m


def fox_devil():
    """Aki's Fox Devil ('Kon!'): a giant white fox head with pointed ears, red markings round slit eyes and a long
    snout whose jaws open wide to bite."""
    m = M.Model()
    m.bones = _bones({"root": [0, 0, 0], "body": [0, 6, 0], "head": [0, 10, 0], "jaw": [0, 10.4, -5]})
    W, W2, RED, BLK, PINK = S.swatch((246, 244, 240)), S.swatch((222, 218, 214)), S.swatch((210, 40, 40)), S.swatch((24, 20, 22)), S.swatch((230, 140, 150))
    tube(m, "body", [[0, 0, 4.0], [0, 6.0, 2.0], [0, 10.0, 0.0]], [3.6, 3.4, 3.4], W2)       # the neck rising out of nowhere
    blob(m, "head", [0, 12.0, -1.5], [5.0, 4.4, 5.0], W, slices=4)
    blob(m, "head", [0, 11.4, -8.0], [2.6, 2.0, 4.0], W, slices=3, axis="z")
    blob(m, "head", [0, 12.0, -12.0], [1.1, 0.9, 0.7], BLK, slices=2)                       # the nose
    for sx in (1, -1):
        blade(m, "head", [sx * 3.0, 15.4, -0.4], [sx * 0.3, 1, 0.2], 5.0, 3.0, 1.0, W, width_dir=[0, 0, 1])   # ears
        blade(m, "head", [sx * 3.0, 15.6, -0.9], [sx * 0.3, 1, 0.2], 3.6, 1.8, 0.4, PINK, width_dir=[0, 0, 1])
        box_at(m, "head", [sx * 2.4, 13.8, -5.6], [1.6, 0.5, 0.4], BLK)                         # slit eyes
        box_at(m, "head", [sx * 2.6, 14.6, -5.2], [2.2, 0.5, 0.4], RED)                         # red markings
        box_at(m, "head", [sx * 3.6, 12.6, -4.8], [0.6, 1.6, 0.4], RED)
        for k in range(3):
            blade(m, "head", [sx * (0.8 + k * 0.6), 10.4, -10.4 + k * 1.4], [0, -1, 0], 1.0, 0.4, 0.3, W)   # fangs
    blob(m, "jaw", [0, 9.6, -7.6], [2.2, 0.9, 3.6], W2, slices=2, axis="z")
    blob(m, "jaw", [0, 10.2, -7.6], [1.8, 0.3, 3.0], S.swatch((180, 60, 70)), slices=1, axis="z")
    return m


SUMMONS += [("kaido_dragon", kaido_dragon), ("guanyin", _ghost(guanyin, 0.62)), ("fox_devil", fox_devil)]
SOLID |= {"kaido_dragon", "fox_devil"}
