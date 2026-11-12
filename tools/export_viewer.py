"""Exports separate, clean clips of each movement for the in-browser viewer:
for every frame, the world-space corners of every block of the test character
(exactly what the preview renderer draws), at 30 frames per second."""
import base64
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_player as R  # noqa: E402
import simulate_motion as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (start, end, forward, side, sprint, sneak, jump_at_start, ledge)
CLIPS = [
    ("walk", "المشي", "دورة المشي: الرجل ترتفع وتتقدم، الورك يهتز ويميل، الجذع يلف عكس الرجلين، والراس ثابت.",
     [(0, 0.5, 0, 0, 0, 0, 0, 0), (0.5, 4.0, 1, 0, 0, 0, 0, 0)]),
    ("run", "الركض", "خطوة أطول، الجسم مايل لكدام، والإيدين مرفوعات أكثر.",
     [(0, 0.5, 0, 0, 0, 0, 0, 0), (0.5, 4.0, 1, 0, 1, 0, 0, 0)]),
    ("back", "الرجوع للخلف", "نفس الدورة بالمقلوب، خطوات أقصر شوية وميلة خفيفة لورا.",
     [(0, 0.5, 0, 0, 0, 0, 0, 0), (0.5, 4.0, -1, 0, 0, 0, 0, 0)]),
    ("side", "المشي للجنب", "الرجل اللي تتحرك تنفتح للجنب بالتناوب.",
     [(0, 0.5, 0, 0, 0, 0, 0, 0), (0.5, 3.5, 0, 1, 0, 0, 0, 0)]),
    ("jump", "قفزة بمكانك", "الرجلين ما يركلن لكدام: يبقن تقريباً مستقيمات وركبة وحدة مثنية شوية، والإيدين منفتحات شوية. الهبطة: الركب تنثني والأصابع تلف للبرة وبعدين يستقر.",
     [(0, 0.7, 0, 0, 0, 0, 0, 0), (0.7, 2.6, 0, 0, 0, 0, 1, 0)]),
    ("runjump", "قفزة وانت راكض", "الجسم يبقى مستقيم بدون ما ينحني. الرجلين ينسحبن لورا شوية والإيدين يرجعن ويه القفزة، وويه الهبطة يكمل ركض.",
     [(0, 1.2, 1, 0, 1, 0, 0, 0), (1.2, 2.4, 1, 0, 1, 0, 1, 0), (2.4, 3.4, 1, 0, 1, 0, 0, 0)]),
    ("ledge", "سقوط من مكان عالي", "يطيح 5 بلوكات: الجسم مستقيم والرجلين لورا شوية، بالسقطة الطويلة الإيدين ينفتحن، وهبطة عميقة: ركب مثنية وجسم منضغط وبعدين يرجع بهدوء.",
     [(0, 0.4, 0, 0, 0, 0, 0, 0), (0.4, 3.4, 1, 0, 0, 0, 0, 1)]),
    ("crouch", "سنيك ونهوض", "نزول ناعم بحدود ربع ثانية بدون ما يطفر، ونهوض بنعومة ويه تعدّي بسيط للوقفة.",
     [(0, 0.6, 0, 0, 0, 0, 0, 0), (0.6, 2.0, 0, 0, 0, 1, 0, 0), (2.0, 3.4, 0, 0, 0, 0, 0, 0)]),
    ("sneakwalk", "المشي بالسنيك", "خطوات واضحة وبطيئة والإيدين واطيات وجاهزات.",
     [(0, 0.6, 0, 0, 0, 1, 0, 0), (0.6, 4.0, 1, 0, 0, 1, 0, 0)]),
    ("rise", "النهوض وانت ماشي", "يمشي بالسنيك وبعدين يكوم ويكمل مشي عادي بدون قفزة بالشكل.",
     [(0, 1.8, 1, 0, 0, 1, 0, 0), (1.8, 4.0, 1, 0, 0, 0, 0, 0)]),
]


def main():
    clips = []
    colours = None
    for cid, name, desc, plan in CLIPS:
        frames, _ = S.simulate(plan)
        step = 2  # 60 -> 30 fps
        pts, ys, xs, zs = [], [], [], []
        edge = None
        for fr in frames[::step]:
            t, i, st, pose, v = fr
            boxes = R.world_boxes(pose)
            if colours is None:
                colours = [list(c) for _, c in boxes]
            # world placement: the model faces -z; the simulated player walks along +z
            off = np.array([st["x"] * 16.0, st["y"] * 16.0, -st["z"] * 16.0])
            for corners, _ in boxes:
                for c in corners:
                    pts.extend(np.round((c + off) * 10).astype(int).tolist())
            ys.append(round(st["y"] * 16.0, 2))
            xs.append(round(st["x"] * 16.0, 2))
            zs.append(round(-st["z"] * 16.0, 2))
            if st.get("edge_z") is not None:
                edge = -st["edge_z"] * 16.0
        arr = np.array(pts, dtype="<i2")
        clips.append({"id": cid, "name": name, "desc": desc, "n": len(ys), "boxes": len(colours),
                      "data": base64.b64encode(arr.tobytes()).decode(), "x": xs, "y": ys, "z": zs,
                      "ledge": edge})
        print(cid, len(ys), "frames")
    out = {"fps": 30, "colours": colours, "clips": clips}
    p = os.path.join(ROOT, "preview", "viewer_data.json")
    json.dump(out, open(p, "w"), separators=(",", ":"), ensure_ascii=False)
    print("wrote", p, round(os.path.getsize(p) / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
