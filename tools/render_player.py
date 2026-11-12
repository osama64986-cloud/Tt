#!/usr/bin/env python3
"""A small 3D preview of our player animations.

A block character built with the game's humanoid proportions and joint
positions (pixels: body pivot y=24, arms at x=+-5 y=22, legs at x=+-1.9 y=12)
holds a sword in the right hand and is posed by evaluating the very same
Molang our animation file contains.  Faces are flat-shaded and drawn back to
front.  Forward is -z; rotations follow the game's convention (a limb with
x = -90 points forward, +z on the right arm lifts it away from the body).

    python3 tools/render_player.py            -> preview/motion_*.png / *.gif
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_animations as C          # noqa: E402

ROOT = C.ROOT
OUT = os.path.join(ROOT, "preview")

# an original test character (not any existing one): orange top, dark green trousers, black hair
SKIN, SHIRT, PANTS, HAIR, SHOE = (214, 168, 128), (232, 128, 44), (52, 92, 64), (30, 28, 34), (60, 50, 44)
EYE = (250, 250, 250)
BLADE, GUARD, GRIP = (190, 236, 236), (200, 150, 60), (110, 76, 46)


def rot(x, y, z):
    """Game-style bone rotation (degrees), applied X first, then Y, then Z."""
    x, y, z = (-math.radians(v) for v in (x, y, z))
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return rz @ ry @ rx


# bone: parent, pivot, boxes [(origin, size, colour)]
BONES = {
    "root": (None, (0, 0, 0), []),
    "waist": ("root", (0, 12, 0), []),
    "body": ("waist", (0, 24, 0), [((-4, 12, -2), (8, 12, 4), SHIRT)]),
    "head": ("body", (0, 24, 0), [((-4, 24, -4), (8, 8, 8), SKIN), ((-4, 30, -4), (8, 2, 8), HAIR),
                                  ((-3, 27, -4.3), (2, 1, 0.3), EYE), ((1, 27, -4.3), (2, 1, 0.3), EYE)]),
    "rightarm": ("body", (-5, 22, 0), [((-8, 12, -2), (4, 12, 4), SKIN), ((-8, 18, -2), (4, 6, 4), SHIRT)]),
    "leftarm": ("body", (5, 22, 0), [((4, 12, -2), (4, 12, 4), SKIN), ((4, 18, -2), (4, 6, 4), SHIRT)]),
    "rightleg": ("root", (-1.9, 12, 0), [((-3.9, 0, -2), (4, 12, 4), PANTS), ((-3.9, 0, -2), (4, 2, 4), SHOE)]),
    "leftleg": ("root", (1.9, 12, 0), [((-0.1, 0, -2), (4, 12, 4), PANTS), ((-0.1, 0, -2), (4, 2, 4), SHOE)]),
    # the sword sits in the right fist and points forward when the arm hangs down
    "rightitem": ("rightarm", (-6, 13, 0), [((-6.5, 12.0, -1.0), (1, 2, 3), GRIP), ((-7.5, 11.5, -2.0), (3, 3, 1), GUARD),
                                             ((-6.5, 12.0, -16.0), (1, 2, 14), BLADE)]),
}
ORDER = ["root", "waist", "body", "head", "rightarm", "leftarm", "rightleg", "leftleg", "rightitem"]


def pose_of(env, skip=()):
    """Sum every animation's rotation/position per bone, as the game layers them."""
    pose = {}
    for name, ad in C.A.items():
        if any(k in name for k in skip):
            continue
        for bone, ch in ad["bones"].items():
            p = pose.setdefault(bone, [np.zeros(3), np.zeros(3)])
            if "rotation" in ch:
                p[0] = p[0] + np.array([C.ev(v, env) for v in ch["rotation"]])
            if "position" in ch:
                p[1] = p[1] + np.array([C.ev(v, env) for v in ch["position"]])
    return pose


def world_boxes(pose):
    mats = {}
    out = []
    for b in ORDER:
        parent, pivot, boxes = BONES[b]
        r, t = pose.get(b, [np.zeros(3), np.zeros(3)])
        if b == "root" and "28.0 - this" in str(r):
            pass
        R = rot(*r)
        pv = np.array(pivot, float)
        # local transform: translate by animation position, rotate about the pivot
        def local(p, R=R, pv=pv, t=t):
            return (R @ (p - pv)) + pv + np.array([-t[0], t[1], -t[2]])
        if parent is None:
            mats[b] = local
        else:
            pm = mats[parent]
            mats[b] = (lambda p, f=local, g=pm: g(f(p)))
        for (o, s, col) in boxes:
            o, s = np.array(o, float), np.array(s, float)
            corners = [o + s * np.array(c) for c in
                       [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]]
            out.append(([mats[b](c) for c in corners], col))
    return out


FACES = [(0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)]


def draw(boxes, view, size=(360, 420), scale=7.5, centre=(180, 330), label=""):
    """view: 3x3 camera rotation.  Orthographic, light from the upper front-left."""
    im = Image.new("RGB", size, (46, 50, 60))
    d = ImageDraw.Draw(im)
    light = np.array([-0.4, 0.8, -0.45])
    light = light / np.linalg.norm(light)
    polys = []
    for corners, col in boxes:
        cam = [view @ c for c in corners]
        for f in FACES:
            pts = [cam[i] for i in f]
            n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            if np.linalg.norm(n) == 0 or n[2] >= 0:      # back face (camera looks down -z)
                continue
            wn = np.cross(corners[f[1]] - corners[f[0]], corners[f[2]] - corners[f[0]])
            wn = wn / (np.linalg.norm(wn) + 1e-9)
            shade = 0.55 + 0.45 * max(0.0, -float(wn @ light))
            depth = sum(p[2] for p in pts) / 4
            polys.append((depth, [(centre[0] + p[0] * scale, centre[1] - p[1] * scale) for p in pts],
                          tuple(int(c * shade) for c in col)))
    for _, pts, col in sorted(polys, key=lambda x: -x[0]):
        d.polygon(pts, fill=col, outline=tuple(int(c * 0.6) for c in col))
    if size[1] > 300:
        d.line([(10, centre[1]), (size[0] - 10, centre[1])], fill=(90, 120, 70), width=2)
    d.text((8, 6), label, fill=(240, 240, 240))
    return im


def camera(yaw, pitch):
    y, p = math.radians(yaw), math.radians(pitch)
    ry = np.array([[math.cos(y), 0, -math.sin(y)], [0, 1, 0], [math.sin(y), 0, math.cos(y)]])
    rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    flip = np.diag([-1.0, 1.0, -1.0])        # look at the character's front (it faces -z)
    return rx @ ry @ flip


def first_person(env, label):
    """Illustration of the first-person view: only the right arm and the sword,
    in front of the camera.  The arm rests low on the right pointing forward and
    up (as held items do in first person); our first-person animations then add
    their rotation and position on top.  The game's own first-person rig places
    the arm slightly differently, so treat this as a guide to the motion."""
    rest_r = np.array([-70.0, -18.0, 0.0])
    rest_t = np.array([0.0, 0.0, 0.0])
    for name in ("animation.player.first_person.attack_rotation", "animation.player.first_person.walk"):
        ad = C.A.get(name)
        if not ad:
            continue
        ch = ad["bones"].get("rightarm", {})
        if "rotation" in ch:
            rest_r = rest_r + np.array([C.ev(v, env) for v in ch["rotation"]])
        if "position" in ch:
            rest_t = rest_t + np.array([C.ev(v, env) for v in ch["position"]]) * 0.6
    item_r = np.zeros(3)
    ad = C.A.get("animation.player.first_person.breathing_bob")
    if ad and "rotation" in ad["bones"].get("rightitem", {}):
        item_r = np.array([C.ev(v, env) for v in ad["bones"]["rightitem"]["rotation"]])
    pose = {"rightarm": [rest_r, rest_t], "rightitem": [item_r, np.zeros(3)]}
    boxes = []
    for corners, col in world_boxes(pose):
        if col not in (SKIN, SHIRT, BLADE, GUARD, GRIP):
            continue
        boxes.append((corners, col))
    # keep only the arm and sword: they hang from the right shoulder pivot (-5, 22, 0)
    keep = [(c, col) for c, col in boxes if min(abs(p[0] + 6) for p in c) < 9 and max(p[0] for p in c) < 0]
    # camera at the eyes, a little behind and left of the shoulder, looking forward (-z)
    eye = np.array([1.0, 27.0, 6.0])
    moved = [([p - eye for p in c], col) for c, col in keep]
    view = camera(180, 4)
    return draw(moved, view, size=(360, 260), scale=12, centre=(180, 120), label=label + "  (illustration)")


def env_for(**kw):
    env = dict(C.BASE)
    env.update(kw)
    return env


def strip(frames, path, cols):
    w, h = frames[0].size
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), (30, 32, 38))
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % cols) * w, (i // cols) * h))
    sheet.save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    view = camera(215, 14)
    # step-by-step sword swing, third and first person
    steps = [0.0, 0.12, 0.25, 0.36, 0.48, 0.62, 0.8, 1.0]
    third, first = [], []
    for p in steps:
        env = env_for(**{"variable.attack_time": p, "_sword": 1})
        third.append(draw(world_boxes(pose_of(env, skip=("first_person", "swim", "sneak"))), view,
                          label=f"sword swing {int(p * 100)}%"))
        first.append(first_person(env, f"first person {int(p * 100)}%"))
    strip(third, os.path.join(OUT, "swing_third_person.png"), 4)
    strip(first, os.path.join(OUT, "swing_first_person.png"), 4)
    # sprint cycle, third person
    run = []
    for i in range(8):
        env = env_for(**{"variable.tcos0": math.cos(i / 8 * 2 * math.pi) * 57, "query.is_sprinting": 1})
        run.append(draw(world_boxes(pose_of(env, skip=("first_person", "swim", "sneak", "attack"))), view,
                        label=f"sprint {i + 1}/8"))
    strip(run, os.path.join(OUT, "sprint_third_person.png"), 4)
    # animated versions
    gif = []
    for i in range(24):
        p = i / 23
        env = env_for(**{"variable.attack_time": p, "_sword": 1})
        a = draw(world_boxes(pose_of(env, skip=("first_person", "swim", "sneak"))), view, label="sword swing")
        b = first_person(env, "first person")
        frame = Image.new("RGB", (720, 420), (30, 32, 38))
        frame.paste(a, (0, 0))
        frame.paste(b, (360, 80))
        gif.append(frame)
    for i in range(24):
        env = env_for(**{"variable.tcos0": math.cos(i / 24 * 2 * math.pi) * 57, "query.is_sprinting": 1,
                         "query.walk_distance": i / 24 * 2, "variable.hand_bob": 0.1})
        a = draw(world_boxes(pose_of(env, skip=("first_person", "swim", "sneak", "attack"))), view, label="sprint")
        b = first_person(env, "first person (sprint)")
        frame = Image.new("RGB", (720, 420), (30, 32, 38))
        frame.paste(a, (0, 0))
        frame.paste(b, (360, 80))
        gif.append(frame)
    gif[0].save(os.path.join(OUT, "motion_3d.gif"), save_all=True, append_images=gif[1:], duration=60, loop=0)
    print("wrote preview/swing_third_person.png, swing_first_person.png, sprint_third_person.png, motion_3d.gif")


if __name__ == "__main__":
    main()
