"""Dev-time helper: reads Mojang's official bedrock-samples pack and records,
for every block texture, only neutral facts (file extension, size, whether it
uses alpha, average colour and a 5-step luminance ramp).  No pixels are copied.
The generator uses these numbers so our original textures keep the colours the
game (and biome tinting) expects.

usage: python3 tools/extract_vanilla_stats.py /path/to/bedrock-samples/resource_pack
"""
import json, os, sys
import numpy as np
from PIL import Image

src = sys.argv[1]
bdir = os.path.join(src, "textures", "blocks")
out = {}
for root, _, files in os.walk(bdir):
    for f in sorted(files):
        stem, ext = os.path.splitext(f)
        if ext not in (".png", ".tga"):
            continue
        if stem.endswith(("_mers", "_mer", "_heightmap")):
            continue
        rel = os.path.relpath(os.path.join(root, stem), bdir).replace(os.sep, "/")
        im = Image.open(os.path.join(root, f))
        a = np.array(im.convert("RGBA")).astype(float)
        w, h = im.size
        al = a[..., 3]
        px = a[..., :3][al > 0] if (al > 0).any() else a[..., :3].reshape(-1, 3)
        lum = px @ np.array([0.299, 0.587, 0.114])
        order = np.argsort(lum)
        bins = np.array_split(order, 5)
        ramp = [px[b].mean(0).round().astype(int).tolist() if len(b) else px.mean(0).round().astype(int).tolist() for b in bins]
        e = out.setdefault(rel, {"ext": []})
        e["ext"].append(ext[1:])
        e.setdefault("per_ext", {})[ext[1:]] = {
            "mean": px.mean(0).round().astype(int).tolist(),
            "alpha": sorted(set(int(v) for v in np.unique(al)))[:4],
        }
        e.update({
            "size": [w, h],
            "alpha": sorted(set(int(v) for v in np.unique(al)))[:4],
            "cover": round(float((al > 0).mean()), 3),
            "mean": px.mean(0).round().astype(int).tolist(),
            "ramp": ramp,
        })
        if rel in ("end_rod", "endframe_eye"):          # UV layout only: 1 = pixel used by the model
            e["mask"] = ["".join("1" if v > 0 else "0" for v in row) for row in al]
        m = os.path.join(root, stem + "_mers.tga")
        if os.path.exists(m):
            mm = np.array(Image.open(m).convert("RGBA")).reshape(-1, 4).mean(0)
            e["mers"] = mm.round().astype(int).tolist()
json.dump(out, open(os.path.join(os.path.dirname(__file__), "nabd", "vanilla_stats.json"), "w"), indent=0, sort_keys=True)
print(len(out), "entries")
