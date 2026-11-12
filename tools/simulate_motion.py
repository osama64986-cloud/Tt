"""Plays our player animations on a simulated player, frame by frame, with the
same queries the game provides, and renders the result.

Timeline (seconds): stand, walk, run, running jump, walk backwards, stand,
crouch down, stand up, crouch-walk, stand up while walking, standing jump,
walk off a 5-block ledge (long fall + hard landing), sidestep.

Outputs preview/motion_full.gif plus contact sheets of the key moments, and
prints the largest joint angles so runaway values show up.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import molang  # noqa: E402
import render_player as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = json.load(open(os.path.join(ROOT, "pack_src", "animations", "nabd_player.animation.json")))["animations"]
ORDER = ["animation.player.move.arms", "animation.player.move.legs", "animation.player.sneaking", "animation.player.bob"]

FPS = 60
WALK, SPRINT, SNEAK = 4.317, 5.612, 1.31

# (start, end, forward, side, sprint, sneak, jump_at_start, ledge)
PLAN = [
    (0.0, 1.0, 0, 0, 0, 0, 0, 0),
    (1.0, 3.0, 1, 0, 0, 0, 0, 0),
    (3.0, 4.2, 1, 0, 1, 0, 0, 0),
    (4.2, 5.4, 1, 0, 1, 0, 1, 0),
    (5.4, 7.4, -1, 0, 0, 0, 0, 0),
    (7.4, 8.0, 0, 0, 0, 0, 0, 0),
    (8.0, 9.2, 0, 0, 0, 1, 0, 0),
    (9.2, 9.9, 0, 0, 0, 0, 0, 0),
    (9.9, 11.4, 1, 0, 0, 1, 0, 0),
    (11.4, 12.6, 1, 0, 0, 0, 0, 0),
    (12.6, 13.8, 0, 0, 0, 0, 1, 0),
    (13.8, 16.0, 1, 0, 0, 0, 0, 1),
    (16.0, 17.5, 0, 1, 0, 0, 0, 0),
]
LABELS = ["stand", "walk", "run", "running jump", "walk backwards", "stand", "crouch down", "stand up",
          "crouch-walk", "stand up while walking", "standing jump", "walk off a ledge", "sidestep"]


def segment(t, plan=None):
    plan = plan or PLAN
    for i, s in enumerate(plan):
        if s[0] <= t < s[1]:
            return i, s
    return len(plan) - 1, plan[-1]


def simulate(plan=None):
    plan = plan or PLAN
    dt = 1.0 / FPS
    st = {"x": 0.0, "y": 0.0, "z": 0.0, "vx": 0.0, "vz": 0.0, "vy": 0.0, "floor": 0.0, "dist": 0.0, "life": 0.0}
    ctx = {"v": {}, "q": {}}
    frames, last_seg = [], -1
    worst = 0.0
    t = 0.0
    while t < plan[-1][1]:
        i, (t0, t1, fw, sd, spr, snk, jump, ledge) = segment(t, plan)
        if i != last_seg:
            if jump and st["y"] <= st["floor"] + 1e-6:
                st["vy"] = 8.4
            if ledge:
                st["floor_drop_at"] = t + 0.5
            last_seg = i
        if st.get("floor_drop_at") and t >= st["floor_drop_at"]:
            st["floor"] = -5.0
            st["floor_drop_at"] = None
            st["edge_z"] = st["z"]
        on_ground = st["y"] <= st["floor"] + 1e-6
        target = SPRINT if spr else (SNEAK if snk else WALK)
        # body faces +z (yaw 0); forward is +z, the right-hand side is -x
        tx, tz = -sd * target, fw * target
        if fw and sd:
            tx, tz = tx * 0.707, tz * 0.707
        k = min(1.0, dt * (12.0 if on_ground else 3.0))
        st["vx"] += (tx - st["vx"]) * k
        st["vz"] += (tz - st["vz"]) * k
        st["x"] += st["vx"] * dt
        st["z"] += st["vz"] * dt
        if not on_ground or st["vy"] > 0:
            st["vy"] = (st["vy"] - 32.0 * dt) * (0.98 ** (dt * 20))
            st["y"] += st["vy"] * dt
            if st["y"] <= st["floor"]:
                st["y"], st["vy"] = st["floor"], 0.0
        on_ground = st["y"] <= st["floor"] + 1e-6
        hs = math.hypot(st["vx"], st["vz"])
        st["dist"] += min(hs / 20.0 * 4.0, 1.0) * 20.0 * dt
        st["life"] += dt
        q = {
            "delta_time": dt, "ground_speed": hs, "is_sprinting": float(bool(spr)), "is_sneaking": float(bool(snk)),
            "position": (lambda a, s=dict(st): [s["x"], s["y"], s["z"]][int(a)]),
            "body_y_rotation": 0.0, "is_on_ground": float(on_ground), "vertical_speed": st["vy"],
            "is_in_water": 0.0, "is_riding": 0.0, "is_gliding": 0.0, "is_sleeping": 0.0, "is_swimming": 0.0,
            "is_crawling": 0.0, "is_in_ui": 0.0, "modified_distance_moved": st["dist"], "life_time": st["life"],
            "target_x_rotation": 0.0, "is_first_person": 0.0, "is_local_player": 0.0,
        }
        ctx["q"] = q
        ctx["v"].setdefault("attack_time", 0.0)
        pose = {}
        for name in ORDER:
            for bone, ch in A.get(name, {}).get("bones", {}).items():
                p = pose.setdefault(bone, [np.zeros(3), np.zeros(3), np.ones(3)])
                if "rotation" in ch:
                    p[0] = p[0] + np.array([molang.run(x, ctx) for x in ch["rotation"]])
                if "position" in ch:
                    p[1] = p[1] + np.array([molang.run(x, ctx) for x in ch["position"]])
                if "scale" in ch:
                    p[2] = p[2] * np.array([molang.run(x, ctx) for x in ch["scale"]])
        for bone, (r, _, _s) in pose.items():
            if bone in ("root",):
                continue
            worst = max(worst, float(np.max(np.abs(r))))
        frames.append((t, i, dict(st), pose, dict(ctx["v"])))
        t += dt
    return frames, worst


def place(boxes, st):
    off = np.array([0.0, st["y"] * 16.0, 0.0])
    return [([c + off for c in corners], col) for corners, col in boxes]


def render(frame, view, size=(300, 330), scale=5.2, label=""):
    t, i, st, pose, v = frame
    boxes = place(R.world_boxes(pose), st)
    floor_y = st["floor"] * 16.0
    # the camera follows the player down a ledge, like the game's camera
    im = R.draw(boxes, view, size=size, scale=scale, centre=(size[0] / 2, size[1] - 40 + st["y"] * 16.0 * scale), label=label)
    return im


def main():
    frames, worst = simulate()
    print(f"{len(frames)} frames, largest joint angle {worst:.1f} deg")
    side = R.camera(270, 6)
    three = R.camera(215, 14)
    gif = []
    for n, fr in enumerate(frames):
        if n % 3:
            continue
        t, i, st, pose, v = fr
        a = render(fr, side, label=f"{LABELS[i]}  t={t:4.1f}s")
        b = render(fr, three, label="")
        both = Image.new("RGB", (600, 330))
        both.paste(a, (0, 0)); both.paste(b, (300, 0))
        gif.append(both)
    out = os.path.join(ROOT, "preview")
    gif[0].save(os.path.join(out, "motion_full.gif"), save_all=True, append_images=gif[1:], duration=50, loop=0)
    # contact sheets: 8 frames from each phase
    for i, label in enumerate(LABELS):
        sel = [f for f in frames if f[1] == i]
        if not sel:
            continue
        step = max(1, int(0.08 * FPS)) if i in (1, 2, 4, 8, 12) else max(1, (len(sel) - 1) // 7)
        start = int(len(sel) * 0.35) if i in (1, 2, 4, 8, 12) else 0
        pick = [sel[min(len(sel) - 1, start + k * step)] for k in range(8)]
        sheet = Image.new("RGB", (300 * 8, 330))
        for k, fr in enumerate(pick):
            sheet.paste(render(fr, side, label=f"{label} {fr[0]:.2f}s"), (300 * k, 0))
        sheet.save(os.path.join(out, f"motion_{i:02d}.png"))
    print("wrote preview/motion_full.gif and preview/motion_XX.png")
    return frames


if __name__ == "__main__":
    main()
