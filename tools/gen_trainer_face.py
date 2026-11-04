"""وجه المدرب (sh:trainer): لحية وشوارب جديدة.
القديم: لحية مكعب مسطح غامق يغطي الوجه من تحت العيون، الفم جوه اللحية، والحواجب لازقة بالشعر، وماكو شوارب واضحة.
الجديد:
  - الوجه (8×8): خط شعر، جبين، حواجب ثخينة، عيون بيض وحدقة، أنف بظل، شوارب أفتح من اللحية بطرفين نازلين (هاندلبار)،
    شفايف، ولحية بخصل عمودية وشعرات شايبة قليلة (مدرب مخضرم)، وسوالف على الجوانب.
  - 3D: شوارب بارزة شوي عن الوجه بطرفين نازلين، ولحية مدببة بثلاث طبقات تحت الذقن (تضيق للتحت)، بـUV لكل وجه على رقعة مرسومة.
آمن لإعادة التشغيل (يشيل مكعبات اللحية/الشوارب القديمة قبل ما يضيف). التشغيل: python3 tools/gen_trainer_face.py"""
import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, "AnimePowers", "RP", "models", "entity", "sh_trainer.geo.json")
TEX = os.path.join(ROOT, "AnimePowers", "RP", "textures", "entity", "sh_trainer.png")

H, H2, H3, G = (58, 40, 30), (88, 63, 44), (36, 24, 18), (94, 82, 74)      # لحية: أساس، لمعة، ظل، شيب
S, S2 = (224, 178, 146), (196, 146, 118)                                       # جلد، ظل الجلد
W, I, B, M = (244, 244, 244), (70, 52, 40), (44, 30, 22), (104, 54, 48)       # بياض العين، حدقة، حاجب، شفايف
MU = (104, 76, 54)                                                             # الشوارب (أفتح من اللحية)

FRONT = [                                                                      # عمود 0 = يمين المدرب (يسار المشاهد)
    [H, H, H, H, H, H, H, H],
    [H, H2, S, S, S, S, H2, H],
    [H, B, B, S, S, B, B, H],
    [S, W, I, S, S, I, W, S],
    [H, S, S, S2, S2, S, S, H],
    [H, MU, MU, MU, MU, MU, MU, H],
    [H, MU, H, M, M, H, MU, H],
    [H, H2, H, H2, H, H, H2, H],
]


def strands(x, y):
    """نقشة اللحية: خصل عمودية، لمعة وظل متناوبين، وشعرات شايبة متفرقة"""
    if (x * 5 + y * 3) % 23 == 0:
        return G
    if (x + y) % 3 == 0:
        return H2
    if (x * 7 + y) % 5 == 0:
        return H3
    return H


def paint(img):
    for r, row in enumerate(FRONT):
        for c, col in enumerate(row):
            img.putpixel((32 + c, 8 + r), (*col, 255))
    # الجوانب: سوالف ولحية على الأعمدة القريبة من الوجه (يمين: الأعمدة 5-7، يسار: 0-2) بنفس نقشة الخصل
    for r in range(4, 8):
        for c in range(5, 8):
            img.putpixel((24 + c, 8 + r), (*strands(c, r), 255))
        for c in range(0, 3):
            img.putpixel((40 + c, 8 + r), (*strands(c + 3, r), 255))
    # رقعة اللحية 3D (16×8 عند 0,48) ورقعة الشوارب (8×4 عند 16,48)
    for y in range(8):
        for x in range(16):
            img.putpixel((x, 48 + y), (*strands(x, y), 255))
    for y in range(4):
        for x in range(8):
            edge = y == 3 or x in (0, 7)
            img.putpixel((16 + x, 48 + y), (*(H if edge else MU), 255))


def faces(size, u, v):
    w, h, d = size
    f = lambda fw, fh: {"uv": [u, v], "uv_size": [round(max(0.5, fw), 3), round(max(0.5, fh), 3)]}
    return {"north": f(w, h), "south": f(w, h), "east": f(d, h), "west": f(d, h), "up": f(w, d), "down": f(w, d)}


def cube(o, s, u, v):
    return {"origin": [round(x, 3) for x in o], "size": [round(x, 3) for x in s], "uv": faces(s, u, v)}


def main():
    geo = json.load(open(GEO, encoding="utf-8"))
    g = geo["minecraft:geometry"][0]
    head = next(b for b in g["bones"] if b["name"] == "head")
    keep = []
    for c in head["cubes"]:
        o, s = c["origin"], c["size"]
        if o[1] < 24 or (o[2] <= -4.2 and s[2] <= 0.4):                         # اللحية/الشوارب القديمة
            continue
        keep.append(c)
    keep += [
        cube((-2.7, 26.05, -4.3), (5.4, 0.8, 0.35), 16, 48),                    # الشوارب
        cube((-3.05, 25.1, -4.3), (0.75, 1.1, 0.35), 16, 48),                   # طرف الشوارب النازل (يمين)
        cube((2.3, 25.1, -4.3), (0.75, 1.1, 0.35), 16, 48),                     # (يسار)
        cube((-3.5, 22.8, -4.6), (7.0, 1.5, 1.2), 0, 48),                       # اللحية: طبقة 1 (عريضة)
        cube((-2.6, 21.55, -4.5), (5.2, 1.3, 1.05), 0, 50),                     # طبقة 2
        cube((-1.4, 20.5, -4.4), (2.8, 1.1, 0.9), 2, 52),                       # طبقة 3 (الطرف المدبب)
    ]
    head["cubes"] = keep
    with open(GEO, "w", encoding="utf-8") as f:
        json.dump(geo, f, indent=1, ensure_ascii=False)
    img = Image.open(TEX).convert("RGBA")
    paint(img)
    img.save(TEX)
    print("trainer face: head cubes", len(keep))


if __name__ == "__main__":
    main()
