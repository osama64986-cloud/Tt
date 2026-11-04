"""دوائر السحر على الأرض (كيان sh:fx_circle): تكستشر بكسل آرت دقيق 256×256 بدل 32×32 القديم.
القديم كان 32 بكسل يتمدد على عرض لحد 18 بلوكة (2 بكسل بالبلوكة) فيطلع مربعات كبار. هسه 256 بكسل = ~14-16 بكسل بالبلوكة بأكبر دائرة
(نفس كثافة تكستشرات ماينكرافت)، وخطوط حادة بدون تنعيم (Pixel Art حقيقي)، وحروف رونية بحزام الدائرة مستوحاة من حروف طاولة السحر.
المتغيرات (sh:c): 0 ذهبي، 1 بنفسجي، 2 أزرق، 3 تركواز، 4 أبيض، 5 أحمر، 6 ساعة (قانون الزمن).
الاستعمال: python3 tools/gen_magic_circles.py [--preview مجلد]"""
import json, math, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AnimePowers")
N = 256
C = (N - 1) / 2.0
PALETTES = [
    ((255, 243, 180), (255, 200, 60), (176, 112, 18)),   # 0 ذهبي
    ((236, 200, 255), (176, 96, 255), (92, 40, 168)),    # 1 بنفسجي
    ((206, 236, 255), (92, 172, 255), (36, 82, 176)),    # 2 أزرق
    ((205, 255, 240), (60, 232, 200), (18, 122, 110)),   # 3 تركواز
    ((255, 255, 255), (222, 228, 246), (132, 142, 178)), # 4 أبيض
    ((255, 205, 190), (255, 84, 62), (150, 28, 24)),     # 5 أحمر
    ((255, 243, 180), (255, 200, 60), (176, 112, 18)),   # 6 ساعة (ذهبي)
]
# حروف رونية 7×7 (مستوحاة من أبجدية طاولة السحر، مو منسوخة): 1 = بكسل
GLYPHS = [
    ["0011100", "0100010", "0000010", "0011100", "0100000", "0100000", "0111110"],
    ["0100010", "0100010", "0111110", "0000010", "0000010", "0001100", "0010000"],
    ["0111110", "0000100", "0001000", "0111110", "0001000", "0000100", "0111110"],
    ["0010000", "0010000", "0111110", "0010010", "0010010", "0010010", "0000110"],
    ["0110110", "1001001", "1001001", "0110110", "0001000", "0001000", "0011100"],
    ["0001000", "0010100", "0100010", "1111111", "0000000", "0111110", "0000000"],
    ["0100000", "0110000", "0101000", "0100100", "0100010", "0100000", "0111110"],
    ["0011100", "0010100", "0011100", "0001000", "0111110", "0001000", "0010100"],
    ["1000001", "0100010", "0010100", "0001000", "0010100", "0100010", "0000000"],
    ["0111000", "1000100", "1000100", "0111000", "0000100", "0000010", "0000001"],
    ["0001000", "0001000", "1101011", "0011100", "1101011", "0001000", "0001000"],
    ["0111110", "0100010", "0101010", "0101010", "0100010", "0111110", "0000000"],
]


def polar():
    y, x = np.mgrid[0:N, 0:N].astype(np.float64)
    dx, dy = x - C, y - C
    return np.hypot(dx, dy), np.arctan2(dy, dx), dx, dy


def ring(r, r0, r1):
    return (r >= r0) & (r < r1)


def seg_mask(dx, dy, a, b, w):
    ax, ay = a; bx, by = b
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = np.clip(((dx - ax) * vx + (dy - ay) * vy) / L2, 0, 1)
    px, py = ax + t * vx - dx, ay + t * vy - dy
    return np.hypot(px, py) <= w


def glyph_band(r, th, rc, h, count, phase, seed):
    """حزام حروف: count حرف حول نصف القطر rc، كل حرف بارتفاع h بكسل (يتمدد من 7×7). يرجع قناع البكسلات المشتعلة"""
    m = np.zeros(r.shape, bool)
    rng = np.random.RandomState(seed)
    order = rng.permutation(len(GLYPHS))
    s = h / 7.0
    for k in range(count):
        tk = phase + k * 2 * math.pi / count
        d = (th - tk + math.pi) % (2 * math.pi) - math.pi
        u = d * r / s + 3.5                 # على طول المحيط (يمين الحرف)
        v = 3.5 - (r - rc) / s              # نصف قطري (فوق الحرف = للخارج)
        inside = (u >= 0) & (u < 7) & (v >= 0) & (v < 7)
        g = GLYPHS[order[k % len(GLYPHS)]]
        gi = np.zeros((7, 7), bool)
        for yy in range(7):
            for xx in range(7):
                gi[yy, xx] = g[yy][xx] == "1"
        ui, vi = np.clip(u.astype(int), 0, 6), np.clip(v.astype(int), 0, 6)
        m |= inside & gi[vi, ui]
    return m


def draw(variant):
    L, M, D = PALETTES[variant]
    r, th, dx, dy = polar()
    img = np.zeros((N, N, 4), np.uint8)
    def put(mask, col, a=255):
        img[mask] = (*col, a)
    R = 127.0
    # طبقة الإضاءة الخافتة (تبين إذا المادة تمزج الشفافية)
    put(ring(r, 101, 118), D, 70)
    put(ring(r, 58, 66), D, 60)
    # الحلقات الخارجية
    put(ring(r, R - 4, R - 1), M); put(ring(r, R - 1, R), D)
    put(ring(r, R - 7.5, R - 6.5), L)
    put(ring(r, 117.5, 118.5), M)
    put(ring(r, 100, 102), M)
    if variant == 6:
        # ساعة: 12 علامة ساعة سميكة + 60 علامة دقيقة + عقربين + أرقام نقطية
        for k in range(60):
            a = k * 2 * math.pi / 60
            big = k % 5 == 0
            r0, r1, w = (103, 116, 2.2) if big else (110, 116, 0.6)
            put(seg_mask(dx, dy, (math.cos(a) * r0, math.sin(a) * r0), (math.cos(a) * r1, math.sin(a) * r1), w), L if big else M)
        for k in range(12):
            a = k * 2 * math.pi / 12 + math.pi / 12
            put(np.hypot(dx - math.cos(a) * 109, dy - math.sin(a) * 109) <= 1.6, M)
        put(seg_mask(dx, dy, (0, 0), (0, -88), 2.4), L)            # عقرب الدقائق
        put(seg_mask(dx, dy, (0, 0), (52, 30), 3.0), M)             # عقرب الساعات
        put(ring(r, 62, 64), M); put(ring(r, 56.5, 57.5), L)
        for k in range(8):
            a = k * math.pi / 4
            put(np.hypot(dx - math.cos(a) * 80, dy - math.sin(a) * 80) <= 3.2, D)
            put(np.hypot(dx - math.cos(a) * 80, dy - math.sin(a) * 80) <= 1.8, L)
        put(r <= 7, M); put(r <= 4, L)
    else:
        # حزام الحروف الرونية بين 103 و117 + نقاط بين الحروف
        put(glyph_band(r, th, 109.5, 11, 22, 0.0, 7 + variant), L)
        for k in range(22):
            a = (k + 0.5) * 2 * math.pi / 22
            put(np.hypot(dx - math.cos(a) * 109.5, dy - math.sin(a) * 109.5) <= 1.4, M)
        # نجمة ثمانية (مربعين مدورين 45°) مرسومة داخل 98
        for rot in (0.0, math.pi / 4):
            pts = [(math.cos(rot + k * math.pi / 2) * 98, math.sin(rot + k * math.pi / 2) * 98) for k in range(4)]
            for k in range(4):
                put(seg_mask(dx, dy, pts[k], pts[(k + 1) % 4], 1.1), M)
        # مثلثين (نجمة سداسية) أصغر داخل 64
        for rot in (-math.pi / 2, math.pi / 2):
            pts = [(math.cos(rot + k * 2 * math.pi / 3) * 62, math.sin(rot + k * 2 * math.pi / 3) * 62) for k in range(3)]
            for k in range(3):
                put(seg_mask(dx, dy, pts[k], pts[(k + 1) % 3], 0.9), L)
        put(ring(r, 62, 64.2), M); put(ring(r, 56.5, 57.5), D)
        # حلقة حروف صغيرة داخلية + علامات شعاعية
        put(glyph_band(r, th, 47, 7, 14, 0.2, 31 + variant), M)
        for k in range(28):
            a = k * 2 * math.pi / 28
            put(seg_mask(dx, dy, (math.cos(a) * 64.5, math.sin(a) * 64.5), (math.cos(a) * 70, math.sin(a) * 70), 0.6), L)
        # الختم بالنص: حلقة + نجمة رباعية + نقطة
        put(ring(r, 18, 20.2), M); put(ring(r, 24.5, 25.5), D)
        for a in (0, math.pi / 2):
            put(seg_mask(dx, dy, (math.cos(a) * 15, math.sin(a) * 15), (-math.cos(a) * 15, -math.sin(a) * 15), 1.0), L)
        put(r <= 4.5, L)
    img[r > R] = 0
    return Image.fromarray(img, "RGBA")


def main():
    tex_dir = os.path.join(ROOT, "RP", "textures", "entity")
    for v in range(len(PALETTES)):
        draw(v).save(os.path.join(tex_dir, f"sh_fx_circle_{v}.png"))
    # الموديل: نفس المكعب (عرض بلوكتين × sh:r) بس الوجه الفوقاني والتحتاني ياخذون التكستشر كله (256×256)، والجوانب بكسل شفاف
    gp = os.path.join(ROOT, "RP", "models", "entity", "sh_fx_circle.geo.json")
    g = json.load(open(gp, encoding="utf-8"))
    d = g["minecraft:geometry"][0]
    d["description"]["texture_width"] = N
    d["description"]["texture_height"] = N
    cube = d["bones"][1]["cubes"][0]
    full = {"uv": [0, 0], "uv_size": [N, N]}
    side = {"uv": [0, 0], "uv_size": [1, 1]}
    cube["uv"] = {"up": full, "down": full, "north": side, "south": side, "east": side, "west": side}
    json.dump(g, open(gp, "w", encoding="utf-8"), indent=1)
    # التكستشر السابع (الساعة) بالكيان ومتحكم الرسم، ومدى الخاصية sh:c لحد 6
    ep = os.path.join(ROOT, "RP", "entity", "sh_fx_circle.entity.json")
    e = json.load(open(ep, encoding="utf-8"))
    e["minecraft:client_entity"]["description"]["textures"] = {f"c{v}": f"textures/entity/sh_fx_circle_{v}" for v in range(len(PALETTES))}
    json.dump(e, open(ep, "w", encoding="utf-8"), indent=1)
    rp = os.path.join(ROOT, "RP", "render_controllers", "sh_fx.render_controllers.json")
    rc = json.load(open(rp, encoding="utf-8"))
    rc["render_controllers"]["controller.render.sh_fx_circle"]["arrays"]["textures"]["Array.t"] = [f"Texture.c{v}" for v in range(len(PALETTES))]
    json.dump(rc, open(rp, "w", encoding="utf-8"), indent=1)
    bp = os.path.join(ROOT, "BP", "entities", "sh_fx_circle.json")
    b = json.load(open(bp, encoding="utf-8"))
    b["minecraft:entity"]["description"]["properties"]["sh:c"]["range"] = [0, len(PALETTES) - 1]
    json.dump(b, open(bp, "w", encoding="utf-8"), indent=1)
    print("circles ok:", len(PALETTES), "متغيرات 256×256")
    if "--preview" in sys.argv:
        out = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(out, exist_ok=True)
        sheet = Image.new("RGBA", (N * 4, N * 2), (38, 52, 34, 255))
        for v in range(len(PALETTES)):
            sheet.alpha_composite(draw(v), ((v % 4) * N, (v // 4) * N))
        sheet.save(os.path.join(out, "circles.png"))
        print("preview:", os.path.join(out, "circles.png"))


if __name__ == "__main__":
    main()
