"""فحص قرية الساكورا: يعيد تشغيل مخطط البناء (ops) على شبكة بلوكات ويتحقق من:
 1) كل اسم بلوك موجود فعلاً بماينكرافت Bedrock (قائمة tools/vanilla_block_ids.txt من Mojang/bedrock-samples)
 2) كل بيت فيه صندوقين بالضبط، سريرين (4 قطع)، طاولة صناعة، وفرن واحد على الأقل، والمعبد فيه صندوق الغنائم
 3) الوصول: من البوابة تمشي لباب كل بيت، وتدخل، وتطلع السلم للعلية، وتوصل للمزرعة وللباغودا (محاكاة حركة لاعب: وقوف على بلوك،
    ارتفاع رأس بلوكتين، قفز بلوكة، درجات)
 4) الأشجار ما تخرب المباني (أوراق الكرز ما تكتب فوق بلوك مبنى)
التشغيل: node tools/sim/dump_plans.mjs <مجلد>  ثم  python3 tools/check_village.py <مجلد>/plan_village.json [صورة_خريطة.png]"""
import json
import os
import re
import sys
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VANILLA = set(open(os.path.join(ROOT, "tools", "vanilla_block_ids.txt"), encoding="utf-8").read().split())

HOUSES = [(-26, -26), (26, -26), (0, -26), (-26, 0), (26, 0), (-26, 26)]
FARM, GATE, PAGODA = (26, 26), (0, 35), (0, 0)

PASS = re.compile(r"(air|carpet|tulip|petals|allium|cornflower|short_grass|fern|peony|lilac|waterlily|iron_chain|lantern|door|_button|pressure_plate|sapling|"
                  r"wheat|carrots|potatoes|beetroot|torch|flowering_azalea$|azalea$|redstone)")
HALF = re.compile(r"(stairs|slab|bed|farmland|grass_path|carpet|lectern|composter|trapdoor)")


def replay(plan):
    vox = {}
    bad_overwrite = []

    def put(x, y, z, bid):
        if bid == "minecraft:air":
            vox.pop((x, y, z), None)
            return
        if bid == "minecraft:cherry_leaves":
            old = vox.get((x, y, z))
            if old and old not in ("minecraft:cherry_leaves", "minecraft:cherry_log", "minecraft:cherry_wood") and not re.search(r"(grass|dirt|petals|tulip|fern|short_grass|allium|cornflower|azalea|peony|lilac|path|gravel)", old):
                bad_overwrite.append(((x, y, z), old))
        vox[(x, y, z)] = bid

    chests = []
    for op in plan["ops"]:
        k = op[0]
        if k == "box":
            _, x1, y1, z1, x2, y2, z2, bid = op
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    for y in range(min(y1, y2), max(y1, y2) + 1):
                        put(x, y, z, bid)
        elif k in ("set", "stair", "perm"):
            put(op[1], op[2], op[3], op[4])
        elif k == "chest":
            put(op[1], op[2], op[3], "minecraft:chest"); chests.append((op[1], op[2], op[3], op[4]))
        elif k == "bed":
            put(op[1], op[2], op[3], "minecraft:bed"); put(op[4], op[2], op[5], "minecraft:bed")
    return vox, chests, bad_overwrite


def block_kind(vox, p):
    b = vox.get(p)
    if b is None:
        return "air"
    n = b.replace("minecraft:", "")
    if PASS.search(n) and not n.endswith(("_stairs", "_slab")):
        return "half" if HALF.search(n) else "air"
    if HALF.search(n):
        return "half"
    if n in ("water",):
        return "water"
    return "solid"


def can_stand(vox, x, y, z):
    """لاعب واقف عند (x,y,z): القدم والراس بدون عائق، وتحت القدم سطح"""
    kf, kh, kb = block_kind(vox, (x, y, z)), block_kind(vox, (x, y + 1, z)), block_kind(vox, (x, y - 1, z))
    if kf == "solid" or kh in ("solid", "half"):
        return False
    if kf == "water":
        return False
    return kb in ("solid", "half") or kf == "half"


def reach(vox, start, limit=4000000):
    seen = {start}; dq = deque([start]); n = 0
    while dq and n < limit:
        x, y, z = dq.popleft(); n += 1
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dy in (0, 1, -1, -2, -3):
                nx, ny, nz = x + dx, y + dy, z + dz
                if (nx, ny, nz) in seen or not can_stand(vox, nx, ny, nz):
                    continue
                if dy == 1:  # قفزة بلوكة: لازم هواء فوق راس نقطة البداية
                    if block_kind(vox, (x, y + 2, z)) in ("solid",):
                        continue
                if dy < 0:   # نزول: لازم الخلية الأفقية فاضية بالارتفاع
                    if block_kind(vox, (nx, y, nz)) == "solid" or block_kind(vox, (nx, y + 1, nz)) == "solid":
                        continue
                seen.add((nx, ny, nz)); dq.append((nx, ny, nz))
    return seen


def main(path, img=None):
    plan = json.load(open(path))
    vox, chests, bad_over = replay(plan)
    fails = []
    # 1) أسماء البلوكات
    ids = {b for b in vox.values()} | {op[4] for op in plan["ops"] if op[0] in ("set", "stair", "perm")} | {op[7] for op in plan["ops"] if op[0] == "box"}
    # حالات البلوكات (perm/stair): الاسم والقيمة لازم يكونون صحيحين وإلا ماينكرافت يرفض الحالة ويتخطى البلوك
    states = json.load(open(os.path.join(ROOT, "tools", "vanilla_block_states.json"), encoding="utf-8"))
    bad_states = set()
    for op in plan["ops"]:
        if op[0] == "perm":
            allowed = states.get(op[4], {})
            for k, v in op[5].items():
                if k not in allowed or (allowed[k] and v not in allowed[k]):
                    bad_states.add((op[4], k, str(v)))
        elif op[0] == "stair":
            allowed = states.get(op[4], {})
            if "weirdo_direction" not in allowed:
                bad_states.add((op[4], "weirdo_direction", "?"))
    print(f"حالات البلوكات الخاطئة: {sorted(bad_states) or 'لا شي'}")
    if bad_states:
        fails.append(f"حالات غلط: {sorted(bad_states)}")
    unknown = sorted(i for i in ids if i not in VANILLA)
    print(f"أسماء البلوكات: {len(ids)} نوع، غير موجودة بماينكرافت: {unknown or 'لا شي'}")
    if unknown:
        fails.append(f"بلوكات مو موجودة: {unknown}")
    # 2) محتويات البيوت
    for hx, hz in HOUSES:
        inside = {p: b for p, b in vox.items() if abs(p[0] - hx) <= 7 and abs(p[2] - hz) <= 7 and p[1] >= 0}
        ch = [c for c in chests if abs(c[0] - hx) <= 7 and abs(c[2] - hz) <= 7]
        cnt = lambda name: sum(1 for b in inside.values() if b.endswith(name))
        beds, craft, furn = cnt(":bed"), cnt(":crafting_table"), cnt(":furnace")
        ok = len(ch) == 2 and beds == 4 and craft >= 1 and furn >= 1
        print(f"بيت ({hx},{hz}): صناديق={len(ch)} {[c[3] for c in ch]} | قطع سرير={beds} | طاولة صناعة={craft} | أفران={furn} | بوك شيلف={cnt(':bookshelf')} | {'✔' if ok else '✖'}")
        if not ok:
            fails.append(f"البيت ({hx},{hz}) ناقص")
    pag = [c for c in chests if abs(c[0]) <= 8 and abs(c[2]) <= 8]
    print(f"الباغودا: صناديق={len(pag)} {[c[3] for c in pag]}")
    if len(pag) != 1:
        fails.append("الباغودا لازم صندوق غنائم وحد")
    # 3) الوصول
    start = None
    for y in range(0, 6):
        if can_stand(vox, GATE[0], y, GATE[1] - 4):
            start = (GATE[0], y, GATE[1] - 4); break
    if not start:
        fails.append("ما لكيت نقطة بداية عند البوابة"); print("بداية؟", fails[-1])
    else:
        seen = reach(vox, start)
        print(f"الوصول من البوابة: {len(seen)} خلية مشي")
        def reached(x1, z1, x2, z2, y1, y2):
            return any(x1 <= p[0] <= x2 and z1 <= p[2] <= z2 and y1 <= p[1] <= y2 for p in seen)
        for hx, hz in HOUSES:
            f1 = reached(hx - 3, hz - 3, hx + 3, hz + 3, 1, 1)
            loft = reached(hx - 2, hz - 2, hx + 2, hz + 2, 6, 6)
            print(f"  بيت ({hx},{hz}): دور أول={'✔' if f1 else '✖'} علية={'✔' if loft else '✖'}")
            if not f1 or not loft:
                fails.append(f"ما تقدر توصل داخل البيت ({hx},{hz}) f1={f1} loft={loft}")
        pg = reached(-4, -4, 4, 4, 1, 1)
        fm = reached(FARM[0] - 6, FARM[1] - 6, FARM[0] + 6, FARM[1] + 6, 0, 1)
        print(f"  الباغودا الداخل={'✔' if pg else '✖'} المزرعة={'✔' if fm else '✖'}")
        if not pg: fails.append("ما تدخل الباغودا")
        if not fm: fails.append("ما توصل المزرعة")
    # 4) الأشجار فوق المباني
    print(f"أوراق كرز كتبت فوق بلوك مبنى: {len(bad_over)}", bad_over[:4])
    if bad_over:
        fails.append(f"الأشجار تخرب المباني ({len(bad_over)})")
    if img:
        topmap(vox, img)
    print("\nفشل:" if fails else "\nكل فحوصات القرية نجحت ✔")
    for f in fails:
        print(" -", f)
    return 1 if fails else 0


def topmap(vox, out):
    from PIL import Image
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from preview_structures import color
    xs = [p[0] for p in vox]; zs = [p[2] for p in vox]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    S = 10
    im = Image.new("RGB", ((x1 - x0 + 1) * S, (z1 - z0 + 1) * S), (60, 60, 70))
    top = {}
    for (x, y, z), b in vox.items():
        if y < -1:
            continue
        if (x, z) not in top or y > top[(x, z)][0]:
            top[(x, z)] = (y, b)
    px = im.load()
    for (x, z), (y, b) in top.items():
        c = color(b); sh = min(1.15, 0.8 + max(0, y) * 0.02)
        c = tuple(min(255, int(v * sh)) for v in c)
        for dx in range(S):
            for dz in range(S):
                px[(x - x0) * S + dx, (z - z0) * S + dz] = c
    im.save(out); print("خريطة علوية:", out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
