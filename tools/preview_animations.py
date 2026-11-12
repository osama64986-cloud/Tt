#!/usr/bin/env python3
"""Renders our player animations as a looping GIF (side view and front view)
for walk, sprint and a full jump, by evaluating the same Molang the game runs.
Writes preview/player_motion.gif."""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_animations as C          # noqa: E402  (reuses its tiny Molang evaluator)

A = C.A
OUT = os.path.join(C.ROOT, "preview", "player_motion.gif")


def pose(env):
    """Sum every animation's contribution per bone (rotation x, z and waist offset)."""
    bones = {}
    for name, ad in A.items():
        if "first_person" in name or "swim" in name or "sneak" in name or "attack" in name:
            continue
        for bone, ch in ad["bones"].items():
            b = bones.setdefault(bone, [0.0, 0.0, 0.0, 0.0])
            if "rotation" in ch:
                v = [C.ev(x, env) for x in ch["rotation"]]
                b[0] += v[0]
                b[2] += v[2]
            if "position" in ch:
                b[3] += C.ev(ch["position"][1], env)
    return bones


def limb(d, px, py, length, ang_deg, width, col, scale):
    a = math.radians(ang_deg)
    ex, ey = px + math.sin(a) * length * scale, py + math.cos(a) * length * scale
    d.line([(px, py), (ex, ey)], fill=col, width=int(width * scale))


def frame(env, label):
    s = 7
    im = Image.new("RGB", (420, 260), (44, 48, 58))
    d = ImageDraw.Draw(im)
    p = pose(env)
    lift = 0
    if env.get("query.is_on_ground", 1) == 0:
        lift = env.get("_height", 0) * 6
    for view, ox in (("side", 110), ("front", 310)):
        hip_y = 170 - lift - p.get("waist", [0, 0, 0, 0])[3] * s
        lean = p.get("waist", [0, 0, 0, 0])[0] if view == "side" else 0
        sh_x = ox + math.sin(math.radians(lean)) * 12 * s
        sh_y = hip_y - math.cos(math.radians(lean)) * 12 * s
        d.line([(ox, hip_y), (sh_x, sh_y)], fill=(90, 160, 200), width=4 * s)                     # body
        d.rectangle([sh_x - 4 * s, sh_y - 8 * s, sh_x + 4 * s, sh_y], fill=(230, 190, 150))         # head
        for side, col_arm, col_leg, sign in (("left", (200, 170, 140), (60, 70, 140), -1), ("right", (240, 210, 175), (80, 90, 170), 1)):
            arm, leg = p.get(side + "arm", [0, 0, 0]), p.get(side + "leg", [0, 0, 0])
            if view == "side":   # +x swings the tip backwards, -x raises it forwards
                limb(d, sh_x, sh_y + s, 11, -arm[0], 3, col_arm, s)
                limb(d, ox, hip_y, 12, -leg[0], 3.5, col_leg, s)
            else:                # front view: z spreads the limbs sideways
                limb(d, sh_x + sign * 6 * s, sh_y + s, 11, sign * abs(arm[2]), 3, col_arm, s)
                limb(d, ox + sign * 2 * s, hip_y, 12, sign * abs(leg[2]), 3.5, col_leg, s)
        d.text((ox - 30, 230), view, fill=(200, 200, 200))
    d.line([(20, 170 + 12 * s), (400, 170 + 12 * s)], fill=(90, 120, 70), width=3)
    d.text((10, 8), label, fill=(240, 240, 240))
    return im


def main():
    frames = []
    base = dict(C.BASE)
    for label, sprint, n in (("walk", 0, 24), ("sprint", 1, 24)):
        for i in range(n):
            env = dict(base)
            env.update({"variable.tcos0": math.cos(i / n * 2 * math.pi) * (40 if not sprint else 57), "query.is_sprinting": sprint})
            frames.append(frame(env, label))
    g, v0 = 32.0, 8.4                      # a jump: up at 8.4 m/s, gravity 32 m/s^2
    t_air = 2 * v0 / g
    for i in range(22):
        t = i / 21 * t_air
        vs = v0 - g * t
        h = v0 * t - g * t * t / 2
        env = dict(base)
        env.update({"query.is_on_ground": 0, "query.vertical_speed": vs, "_height": h})
        frames.append(frame(env, f"jump  (vertical speed {vs:+.1f} m/s)"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=50, loop=0)
    print("wrote", OUT, len(frames), "frames")


if __name__ == "__main__":
    main()
