"""Third-person view from behind, with and without the shoulder view, posed by
evaluating the real animation file (tools/molang.py) for the local player."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import molang  # noqa: E402
import render_player as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = json.load(open(os.path.join(ROOT, "pack_src", "animations", "nabd_player.animation.json")))["animations"]
ORDER = ["animation.player.move.arms", "animation.player.move.legs", "animation.player.bob"]


def pose(local, side=1.0):
    ctx = {"v": {"nb_sh_side": side}, "q": {"is_local_player": float(local), "is_first_person": 0.0, "is_in_ui": 0.0,
                                            "delta_time": 0.016, "position": lambda i: 0.0, "life_time": 2.0,
                                            "is_on_ground": 1.0, "modified_distance_moved": 0.0}}
    p = {}
    for name in ORDER:
        for bone, ch in A[name]["bones"].items():
            e = p.setdefault(bone, [np.zeros(3), np.zeros(3), np.ones(3)])
            for k, i in (("rotation", 0), ("position", 1)):
                if k in ch:
                    e[i] = e[i] + np.array([molang.run(x, ctx) for x in ch[k]])
    return p


def panel(local, label, side=1.0):
    W, H, scale = 420, 380, 6.0
    sky = Image.new("RGB", (W, H), (120, 170, 220))
    d = ImageDraw.Draw(sky)
    d.rectangle([0, 250, W, H], fill=(96, 150, 70))
    cx = W // 2
    # a target straight ahead, far away: it sits exactly behind the screen centre
    d.rectangle([cx - 3, 150, cx + 3, 252], fill=(140, 100, 55))
    d.rectangle([cx - 22, 175, cx + 22, 182], fill=(140, 100, 55))
    d.rectangle([cx - 14, 112, cx + 14, 150], fill=(210, 180, 100), outline=(150, 120, 60))
    fig = R.draw(R.world_boxes(pose(local, side)), R.camera(0, 4), size=(W, H), scale=scale, centre=(cx, 330), label="")
    a, b = np.array(fig), np.array(sky)
    m = np.any(a != (46, 50, 60), axis=2)
    b[m] = a[m]
    im = Image.fromarray(b)
    d = ImageDraw.Draw(im)
    if local:
        cy = 131
        d.rectangle([cx - 1, cy - 7, cx + 1, cy + 7], fill=(255, 255, 255), outline=(20, 20, 24))
        d.rectangle([cx - 7, cy - 1, cx + 7, cy + 1], fill=(255, 255, 255), outline=(20, 20, 24))
    d.rectangle([0, 0, W, 22], fill=(30, 32, 40))
    d.text((8, 5), label, fill=(240, 240, 240))
    return im


def main():
    a = panel(False, "Normal third person (you block the middle)")
    b = panel(True, "Nabd shoulder view (default: character left)")
    c = panel(True, "Setting: character right", side=-1.0)
    out = Image.new("RGB", (a.width * 3 + 20, a.height), (20, 20, 24))
    for i, p in enumerate((a, b, c)):
        out.paste(p, (i * (a.width + 10), 0))
    path = os.path.join(ROOT, "preview", "shoulder_view.png")
    out.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
