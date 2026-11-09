#!/usr/bin/env python3
"""فحص مدينة إثيريا (Aetheria) من نفس كود اللعبة (tools/sim/dump_city.mjs → city_plan.js + city_raster.js):
  1) كل اسم بلوكة موجود بـ Bedrock (tools/vanilla_block_ids.txt) وكل حالة واسمها وقيمتها صحيحة (tools/vanilla_block_states.json)
  2) الحجم 248×248 بالضبط: كل عمود بيه سطح، والسور يغطي الحافة كلها (إلا ممر البوابة)
  3) الوصول: بحث مشي (BFS) من برا البوابة: كل صندوق وسرير ومكان شخصية لازم يوصله اللاعب مشي (أبواب، درج، سلالم)
  4) (اختياري) رسم: --render out_dir يرسم المدينة من فوق ومجسم (إسومتري)
التشغيل: python3 tools/check_city.py [--render out_dir]"""
import json
import os
import subprocess
import sys
import tempfile
from collections import deque

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS = set(open(os.path.join(ROOT, "tools", "vanilla_block_ids.txt"), encoding="utf-8").read().split())
STATES = json.load(open(os.path.join(ROOT, "tools", "vanilla_block_states.json"), encoding="utf-8"))


def load(out):
    r = subprocess.run(["node", os.path.join(ROOT, "tools", "sim", "dump_city.mjs"), out], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        sys.exit(1)
    meta = json.load(open(os.path.join(out, "city_meta.json")))
    X, Y, Z = meta["dims"]
    g = np.fromfile(os.path.join(out, "city_grid.bin"), dtype="<u2").reshape(Y, Z, X)
    return meta, g


PASS = ("air", "carpet", "pressure_plate", "poppy", "dandelion", "cornflower", "allium", "daisy", "tulip", "bluet", "lily_of", "short_grass",
        "tall_grass", "fern", "_door", "torch", "wheat", "carrots", "potatoes", "beetroot", "sapling", "ladder", "fence_gate", "waterlily", "reeds",
        "peony", "rose_bush", "lilac", "sunflower")
# ما تقدر توقف فوقه (أو ما تنطه: السياج والجدار والقضبان أعلى من قفزة)
NOSTAND = ("air", "water", "lava", "pressure_plate", "poppy", "dandelion", "cornflower", "allium", "daisy", "tulip", "bluet", "lily_of",
           "short_grass", "tall_grass", "fern", "torch", "_door", "sapling", "ladder", "lantern", "fence", "_wall", "iron_bars", "pane", "reeds",
           "peony", "rose_bush", "lilac", "sunflower", "waterlily")


def classify(pal):
    """لكل رقم باللوحة: passable (تقدر تمشي داخله)، standable (تقدر توقف فوقه)، ladder، fence (عالي 1.5: ما تنطه)"""
    n = len(pal)
    pas = np.zeros(n, bool); std = np.zeros(n, bool); lad = np.zeros(n, bool)
    pas[0] = True                                                     # فراغ = هواء (الموقع منظف قبل البناء)
    for i, p in enumerate(pal):
        if not p:
            continue
        nm = p["id"].split(":")[1]
        pas[i] = nm == "air" or any(k in nm for k in PASS if k != "air")          # "stairs" بيها "air": نطابق الهواء بالضبط
        std[i] = nm != "air" and not any(k in nm for k in NOSTAND if k != "air")
        lad[i] = nm == "ladder"
    return pas, std, lad


def reach(meta, g):
    ymin = meta["ymin"]
    Y, Z, X = g.shape
    pas, std, lad = classify(meta["pal"])
    P = pas[g]; S = std[g]; L = lad[g]
    # خلية (y,z,x) ممكن يوقف بيها اللاعب: هي ورا راسه عابرة، وتحتها شي يتوقف عليه (أو سلم)
    ok = np.zeros_like(P)
    ok[1:-1] = P[1:-1] & P[2:] & (S[:-2] | L[1:-1])
    seen = np.zeros_like(ok)
    q = deque()
    sx, sz = 124, Z - 1
    for yy in range(1, Y - 1):
        if ok[yy, sz, sx]:
            seen[yy, sz, sx] = True; q.append((yy, sz, sx)); break
    while q:
        y, z, x = q.popleft()
        for dz, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nz, nx = z + dz, x + dx
            if not (0 <= nz < Z and 0 <= nx < X):
                continue
            for dy in (0, 1, -1, -2, -3):
                ny = y + dy
                if not (1 <= ny < Y - 1) or not ok[ny, nz, nx] or seen[ny, nz, nx]:
                    continue
                if dy == 1 and not P[y + 2, z, x]:                    # طلعة بلوكة: لازم فوق راسك فاضي
                    continue
                if dy < 0 and not all(P[y + k, nz, nx] for k in range(dy + 1, 2)):
                    continue
                seen[ny, nz, nx] = True; q.append((ny, nz, nx))
                break
        if L[y, z, x]:                                                  # راس السلم: تنزل منه على الأرضية اللي جنبه (مثل اللعبة)
            for dz, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nz, nx = z + dz, x + dx
                if 0 <= nz < Z and 0 <= nx < X and y + 1 < Y - 1 and ok[y + 1, nz, nx] and not seen[y + 1, nz, nx] and P[y + 1, z, x]:
                    seen[y + 1, nz, nx] = True; q.append((y + 1, nz, nx))
        if L[y, z, x] or (y + 1 < Y - 1 and L[y + 1, z, x]):           # تسلق السلم
            for ny in (y + 1, y - 1):
                if 1 <= ny < Y - 1 and not seen[ny, z, x] and (L[ny, z, x] or ok[ny, z, x]) and P[ny, z, x] and P[min(ny + 1, Y - 1), z, x]:
                    seen[ny, z, x] = True; q.append((ny, z, x))
    return seen


def main():
    out = tempfile.mkdtemp(prefix="shcity-")
    meta, g = load(out)
    pal = meta["pal"]
    errs = []
    # 1) الأسماء والحالات
    used = set(np.unique(g).tolist())
    for i in used:
        p = pal[i]
        if not p:
            continue
        if p["id"] not in IDS:
            errs.append(f"اسم بلوكة مو موجود: {p['id']}")
            continue
        allowed = STATES.get(p["id"], {})
        for k, v in (p.get("st") or {}).items():
            if k not in allowed:
                errs.append(f"{p['id']}: حالة مو موجودة {k}")
            elif v not in allowed[k]:
                errs.append(f"{p['id']}: قيمة غلط {k}={v} (المسموح {allowed[k]})")
    # 2) الحجم والسور
    Y, Z, X = g.shape
    if (X, Z) != (248, 248):
        errs.append(f"الحجم {X}×{Z} مو 248×248")
    surf = g[0]
    if int((surf == 0).sum()):
        errs.append(f"{int((surf == 0).sum())} عمود بدون سطح")
    ymin = meta["ymin"]
    wall_layer = g[3 - ymin]                                          # y=3
    edge = np.zeros((Z, X), bool); edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    holes = [(x, z) for z in range(Z) for x in range(X) if edge[z, x] and wall_layer[z, x] == 0 and not (z == Z - 1 and 122 <= x <= 126)]
    hole_air = [(x, z) for (x, z) in holes]
    air_ids = {i for i, p in enumerate(pal) if p and p["id"] == "minecraft:air"}
    holes = [(x, z) for z in range(Z) for x in range(X) if edge[z, x] and (wall_layer[z, x] == 0 or wall_layer[z, x] in air_ids) and not (z == Z - 1 and 122 <= x <= 126)]
    if holes:
        errs.append(f"السور بيه فتحات بالحافة: {holes[:8]}")
    # 3) الوصول
    seen = reach(meta, g)
    total = int(seen.sum())
    def reachable(x, y, z, r=1):
        for yy in range(y - ymin - 1, y - ymin + 3):
            for dz in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if 0 <= yy < Y and 0 <= z + dz < Z and 0 <= x + dx < X and seen[yy, z + dz, x + dx]:
                        return True
        return False
    bad_c = [c for c in meta["chests"] if not reachable(c["x"], c["y"], c["z"])]
    bad_b = [b for b in meta["beds"] if not (reachable(b["fx"], b["y"], b["fz"]) or reachable(b["hx"], b["y"], b["hz"]))]
    bad_p = [p for p in meta["posts"] if not reachable(p["x"], p["y"], p["z"], 2)]
    print(f"مدينة إثيريا: {len(meta['pal']) - 1} نوع بلوكة، {meta['ops']} عملية، {meta['homes']} بيت، {len(meta['chests'])} صندوق، {len(meta['beds'])} سرير، "
          f"{len(meta['posts'])} مكان شخصية، {meta['lights']} فانوس؛ خلايا يوصلها المشي من البوابة: {total}")
    # الصندوق والسرير لازم يكونون موجودين فعلاً بمكانهم (مو مغطيين بسجاد أو بلوكة لاحقة)، وفوقهم فاضي (الصندوق ما ينفتح تحت بلوكة)
    pas, _, _ = classify(pal)
    def blk(x, y, z):
        return pal[int(g[y - ymin, z, x])] or {"id": "void"}
    def open_above(x, y, z):
        return y + 1 - ymin < Y and bool(pas[int(g[y + 1 - ymin, z, x])])
    gone_c = [c for c in meta["chests"] if not blk(c["x"], c["y"], c["z"])["id"].endswith(":chest")]
    shut_c = [c for c in meta["chests"] if c not in gone_c and not open_above(c["x"], c["y"], c["z"])]
    gone_b = [b for b in meta["beds"] if blk(b["fx"], b["y"], b["fz"])["id"] != "minecraft:bed" or blk(b["hx"], b["y"], b["hz"])["id"] != "minecraft:bed"]
    wall_b = [b for b in meta["beds"] if b not in gone_b and not (open_above(b["fx"], b["y"], b["fz"]) and open_above(b["hx"], b["y"], b["hz"]))]
    if gone_c: errs.append(f"صناديق انمسحت بمكانها: {len(gone_c)} مثل {gone_c[:4]}")
    if shut_c: errs.append(f"صناديق فوقها بلوكة (ما تنفتح): {len(shut_c)} مثل {shut_c[:4]}")
    if gone_b: errs.append(f"أسرّة انمسحت بمكانها: {len(gone_b)} مثل {gone_b[:4]}")
    if wall_b: errs.append(f"أسرّة مدفونة بجدار/سقف: {len(wall_b)} مثل {wall_b[:4]}")
    if bad_c: errs.append(f"صناديق ما توصلها: {len(bad_c)} مثل {bad_c[:4]}")
    if bad_b: errs.append(f"أسرّة ما توصلها: {len(bad_b)} مثل {bad_b[:4]}")
    if bad_p: errs.append(f"أماكن شخصيات ما توصلها: {len(bad_p)} مثل {bad_p[:4]}")
    if "--render" in sys.argv:
        render(meta, g, sys.argv[sys.argv.index("--render") + 1], seen)
    if errs:
        print("أخطاء المدينة:")
        for e in errs[:40]:
            print(" -", e)
        sys.exit(1)
    print("المدينة سليمة: الأسماء والحالات، الحجم 248×248، السور، والوصول لكل صندوق وسرير وشخصية")


# ───────────── الرسم ─────────────
COLS = [
    ("water", (52, 98, 200)), ("lava", (230, 100, 20)), ("grass_block", (98, 152, 62)), ("grass_path", (168, 140, 90)), ("coarse_dirt", (112, 82, 58)),
    ("gravel", (128, 122, 118)), ("farmland", (96, 62, 40)), ("wheat", (214, 190, 80)), ("carrots", (230, 140, 50)), ("potatoes", (190, 170, 70)),
    ("beetroot", (150, 50, 60)), ("azalea_leaves_flowered", (170, 120, 170)), ("azalea_leaves", (84, 120, 50)), ("spruce_leaves", (54, 86, 54)),
    ("birch_leaves", (110, 150, 70)), ("oak_leaves", (70, 118, 46)), ("short_grass", (100, 160, 70)), ("poppy", (200, 40, 40)), ("dandelion", (230, 210, 60)),
    ("cornflower", (80, 110, 220)), ("allium", (190, 120, 220)), ("tulip", (240, 120, 160)), ("daisy", (235, 235, 230)), ("bluet", (210, 220, 240)), ("lily_of", (240, 240, 240)),
    ("deepslate_tile", (58, 58, 66)), ("dark_oak", (70, 48, 28)), ("spruce_log", (64, 46, 28)), ("stripped_spruce", (120, 92, 60)), ("spruce", (112, 82, 50)),
    ("oak_log", (104, 82, 50)), ("birch_log", (210, 206, 196)), ("mossy_stone", (110, 126, 96)), ("cracked_stone", (122, 120, 118)), ("chiseled_stone", (130, 128, 126)),
    ("stone_brick", (130, 128, 126)), ("mossy_cobble", (104, 120, 90)), ("cobblestone", (118, 116, 114)), ("polished_andesite", (150, 152, 152)), ("andesite", (138, 138, 138)),
    ("smooth_stone", (160, 160, 160)), ("smooth_quartz", (236, 230, 222)), ("quartz", (236, 230, 222)), ("gold_block", (246, 208, 60)), ("stone", (126, 126, 126)),
    ("blue_stained", (60, 80, 180)), ("yellow_stained", (220, 200, 60)), ("light_blue_stained", (120, 180, 230)), ("glass", (190, 220, 235)), ("iron_bars", (110, 110, 112)),
    ("blue_wool", (50, 60, 160)), ("yellow_wool", (240, 200, 40)), ("red_wool", (170, 40, 36)), ("green_wool", (90, 120, 30)), ("orange_wool", (230, 120, 30)),
    ("purple_wool", (120, 50, 170)), ("light_blue_wool", (80, 170, 220)), ("lime_wool", (120, 190, 40)), ("cyan_wool", (30, 140, 150)), ("white_wool", (235, 235, 235)),
    ("red_carpet", (160, 36, 34)), ("brown_carpet", (110, 76, 46)), ("green_carpet", (84, 110, 30)), ("light_gray_carpet", (150, 150, 145)), ("blue_carpet", (50, 60, 160)),
    ("bookshelf", (120, 90, 56)), ("hay_block", (200, 170, 50)), ("pumpkin", (220, 130, 30)), ("melon", (120, 160, 40)), ("barrel", (120, 88, 52)), ("bed", (180, 40, 44)),
    ("lantern", (250, 210, 120)), ("campfire", (240, 150, 60)), ("brick", (150, 80, 66)), ("black_concrete", (24, 24, 28)), ("beehive", (190, 150, 80)),
    ("calcite", (222, 222, 216)), ("birch", (196, 178, 123)), ("fern", (80, 140, 60)), ("waterlily", (40, 120, 40)), ("reeds", (130, 180, 90)),
    ("peony", (230, 160, 200)), ("rose_bush", (190, 30, 40)), ("lilac", (190, 140, 200)), ("magenta_wool", (190, 70, 180)), ("gray_wool", (70, 75, 80)),
    ("brown_wool", (115, 75, 45)), ("pink_wool", (235, 140, 170)), ("cake", (240, 230, 220)), ("target", (230, 200, 190)), ("lime_carpet", (120, 190, 40)),
    ("light_blue_carpet", (80, 170, 220)), ("cyan_carpet", (30, 140, 150)), ("dirt", (120, 86, 60)), ("oak", (162, 130, 78)),
]


def col_of(pid):
    for k, c in COLS:
        if k in pid:
            return np.array(c, float)
    return np.array((150, 140, 130), float)


def render(meta, g, out_dir, seen=None):
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    pal = meta["pal"]
    Y, Z, X = g.shape
    air = np.array([not p or p["id"] == "minecraft:air" for p in pal])
    colors = np.array([col_of(p["id"]) if p else (0, 0, 0) for p in pal])
    # من فوق: أعلى بلوكة بكل عمود، بتظليل حسب الارتفاع وضوء من الشمال الغربي
    solid = ~air[g]
    top = np.where(solid.any(0), Y - 1 - np.argmax(solid[::-1], 0), 0)
    idx = np.take_along_axis(g, top[None], 0)[0]
    img = colors[idx] * (0.70 + 0.30 * (top / Y))[..., None]
    sh = np.zeros_like(top, float); sh[1:, 1:] = np.clip((top[1:, 1:] - top[:-1, :-1]) * 0.06, -0.25, 0.25)
    img = np.clip(img * (1 + sh)[..., None], 0, 255).astype(np.uint8)
    im = Image.fromarray(img, "RGB").resize((X * 4, Z * 4), Image.NEAREST)
    im.save(os.path.join(out_dir, "city_top.png"))
    # مجسم إسومتري (من الجنوب الشرقي): وجوه مكشوفة بس، من البعيد للقريب
    S = 3
    W, H = (X + Z) * S + 40, (X + Z) * S // 2 + Y * S * 2 + 60
    can = np.zeros((H, W, 3), np.uint8); can[:] = (150, 185, 225)
    from PIL import ImageDraw
    pim = Image.fromarray(can); d = ImageDraw.Draw(pim)
    def proj(x, y, z):
        return (W // 2 + (x - z) * S, 40 + (x + z) * S // 2 - y * S * 2 + Y * S * 2)
    for s_ in range(X + Z - 1):
        for x in range(max(0, s_ - Z + 1), min(X, s_ + 1)):
            z = s_ - x
            col = g[:, z, x]
            for y in range(Y):
                k = col[y]
                if air[k] or k == 0:
                    continue
                if y + 1 < Y and not air[g[y + 1, z, x]] and g[y + 1, z, x] != 0 and x + 1 < X and not air[g[y, z, x + 1]] and g[y, z, x + 1] != 0 and z + 1 < Z and not air[g[y, z + 1, x]] and g[y, z + 1, x] != 0:
                    continue
                c = colors[k]
                px, py = proj(x, y - meta["ymin"], z)
                top_c = tuple(int(v) for v in c)
                left_c = tuple(int(v * 0.78) for v in c)
                right_c = tuple(int(v * 0.62) for v in c)
                d.polygon([(px, py - S), (px + S, py - S // 2 - S // 2 + S // 2 - S), (px, py - S), (px - S, py)], fill=top_c)
                d.polygon([(px - S, py), (px, py - S), (px + S, py), (px, py + S)], fill=top_c)
                d.polygon([(px - S, py), (px, py + S), (px, py + S + 2 * S), (px - S, py + 2 * S)], fill=left_c)
                d.polygon([(px, py + S), (px + S, py), (px + S, py + 2 * S), (px, py + S + 2 * S)], fill=right_c)
    pim.save(os.path.join(out_dir, "city_iso.png"))
    print("رسمت:", os.path.join(out_dir, "city_top.png"), os.path.join(out_dir, "city_iso.png"))


if __name__ == "__main__":
    main()
