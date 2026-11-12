"""Side and top views of the swimming stroke (the game lays the body flat
itself; here the whole figure is tilted the same way for the picture)."""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_player as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = ("swim",)


def pose(t):
    env = R.env_for(**{"query.life_time": t, "query.is_swimming": 1, "query.is_in_water": 1, "variable.swim_amount": 1})
    p = {}
    for name, ad in R.C.A.items():
        if not any(k in name for k in KEEP) or "no_right_arm" in name:
            continue
        for bone, ch in ad["bones"].items():
            q = p.setdefault(bone, [np.zeros(3), np.zeros(3)])
            if "rotation" in ch:
                q[0] = q[0] + np.array([R.C.ev(v, env) for v in ch["rotation"]])
    p.setdefault("root", [np.zeros(3), np.zeros(3)])[0] = np.array([-90.0, 0.0, 0.0])
    return p


def main():
    frames, gif = [], []
    period = 1 / 0.9
    for i in range(8):
        t = 3.0 + period * i / 8
        boxes = R.world_boxes(pose(t))
        side = R.draw(boxes, R.camera(270, 10), size=(360, 260), scale=5.0, centre=(250, 130), label=f"swim side {i + 1}/8")
        top = R.draw(boxes, R.camera(180, 80), size=(360, 260), scale=5.0, centre=(180, 40), label=f"swim from above {i + 1}/8")
        both = Image.new("RGB", (360, 520))
        both.paste(side, (0, 0)); both.paste(top, (0, 260))
        frames.append(both)
    sheet = Image.new("RGB", (360 * 8, 520))
    for i, f in enumerate(frames):
        sheet.paste(f, (360 * i, 0))
    sheet.save(os.path.join(ROOT, "preview", "swim_stroke.png"))
    frames[0].save(os.path.join(ROOT, "preview", "swim_stroke.gif"), save_all=True, append_images=frames[1:], duration=140, loop=0)
    print("wrote preview/swim_stroke.png and swim_stroke.gif")


if __name__ == "__main__":
    main()
