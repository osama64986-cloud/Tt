"""معاينة مجسمة (إسومترية) لمخططات البنايات من plan_*.json (يولدها tools/sim/dump_plans.mjs).
التشغيل: node tools/sim/dump_plans.mjs /tmp/plans && python3 tools/preview_structures.py /tmp/plans out_dir
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

COL = [
    ("water", (60, 110, 200)), ("lava", (230, 90, 20)), ("cherry_leaves", (246, 170, 196)), ("pink_petals", (250, 190, 210)),
    ("cherry_log", (120, 80, 90)), ("dark_oak", (70, 50, 30)), ("red_nether", (130, 30, 40)), ("red_concrete", (190, 40, 36)),
    ("red_wool", (200, 50, 50)), ("white_wool", (235, 235, 235)), ("red_carpet", (180, 30, 30)), ("green_carpet", (90, 140, 60)),
    ("white_concrete", (230, 232, 236)), ("white_stained", (210, 225, 235)), ("smooth_quartz", (236, 230, 222)), ("quartz", (236, 230, 222)),
    ("black_concrete", (20, 20, 24)), ("polished_blackstone", (40, 36, 48)), ("blackstone", (40, 36, 48)), ("crying_obsidian", (70, 20, 120)),
    ("purple", (120, 50, 170)), ("deepslate", (70, 72, 78)), ("mossy", (100, 130, 80)), ("moss", (90, 130, 60)), ("gold", (240, 200, 60)),
    ("end_rod", (250, 250, 240)), ("lantern", (255, 200, 90)), ("soul", (80, 200, 220)), ("gravel", (140, 140, 140)),
    ("light_gray", (190, 190, 190)), ("dirt_path", (170, 140, 80)), ("coarse_dirt", (110, 80, 50)), ("dirt", (110, 80, 50)),
    ("grass_block", (96, 160, 64)), ("stone_brick", (130, 130, 130)), ("stone", (130, 130, 130)), ("cobble", (120, 120, 120)),
    ("andesite", (140, 140, 140)), ("planks", (140, 100, 60)), ("fence", (110, 80, 50)), ("glass", (200, 220, 230)),
    ("barrel", (120, 90, 50)), ("hay", (200, 170, 40)), ("melon", (100, 160, 50)), ("pumpkin", (220, 120, 20)),
    ("chest", (160, 110, 40)), ("iron_bars", (150, 150, 155)), ("lightning", (200, 120, 60)), ("azalea", (80, 140, 60)),
    ("waterlily", (40, 140, 60)), ("bamboo", (140, 170, 60)), ("campfire", (240, 120, 30)), ("torch", (255, 200, 80)),
]


def color(bid):
    n = bid.replace("minecraft:", "")
    for k, c in COL:
        if k in n:
            return c
    return (200, 0, 200)


def build(plan, rot=0):
    vox = {}
    for op in plan["ops"]:
        k = op[0]
        if k == "box":
            _, x1, y1, z1, x2, y2, z2, bid = op
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    for y in range(min(y1, y2), max(y1, y2) + 1):
                        if bid == "minecraft:air":
                            vox.pop((x, y, z), None)
                        else:
                            vox[(x, y, z)] = bid
        elif k in ("set", "stair", "perm"):
            x, y, z, bid = op[1], op[2], op[3], op[4]
            vox[(x, y, z)] = bid
        elif k == "chest":
            vox[(op[1], op[2], op[3])] = "minecraft:chest"
    return vox


def render(vox, size=900, yaw=35):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    pts = []
    for (x, y, z), bid in vox.items():
        if y < -1:  # نخفي الأساس الترابي
            continue
        rx, rz = x * c - z * s, x * s + z * c
        pts.append((rz, y, rx, bid, x, y, z))
    pts.sort(key=lambda p: (p[0], p[1]))
    sc = 12.0
    proj = [(rx * sc, rz * sc * 0.5 - y * sc * 0.9) for rz, y, rx, *_ in pts]
    minx, maxx = min(p[0] for p in proj), max(p[0] for p in proj)
    miny, maxy = min(p[1] for p in proj), max(p[1] for p in proj)
    k = min((size - 40) / (maxx - minx + sc), (size * 0.8 - 40) / (maxy - miny + sc * 2))
    sc *= k
    ox = size / 2 - ((minx + maxx) / 2) * k
    oy = size * 0.4 - ((miny + maxy) / 2) * k
    img = Image.new("RGB", (size, int(size * 0.8)), (170, 205, 235))
    d = ImageDraw.Draw(img)
    for rz, y, rx, bid, x, yy, z in pts:
        px = ox + rx * sc
        py = oy + rz * sc * 0.5 - y * sc * 0.9
        base = color(bid)
        w = sc
        top = [(px, py - sc * 0.5), (px + w * 0.5, py), (px, py + sc * 0.5), (px - w * 0.5, py)]
        left = [(px - w * 0.5, py), (px, py + sc * 0.5), (px, py + sc * 0.5 + sc * 0.9), (px - w * 0.5, py + sc * 0.9)]
        right = [(px + w * 0.5, py), (px, py + sc * 0.5), (px, py + sc * 0.5 + sc * 0.9), (px + w * 0.5, py + sc * 0.9)]
        d.polygon(left, fill=tuple(int(v * 0.72) for v in base))
        d.polygon(right, fill=tuple(int(v * 0.55) for v in base))
        d.polygon(top, fill=tuple(min(255, int(v * 1.05)) for v in base))
    return img


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for name in ("village", "palace", "ruins", "shrine"):
        plan = json.load(open(os.path.join(src, f"plan_{name}.json")))
        vox = build(plan)
        render(vox, size=1100, yaw=35).save(os.path.join(out, f"{name}.png"))
        print(name, len(vox), "blocks")
