"""صور شاشة الخيميائي (v1.37.1، تشبه شاشة طاولة السحر): القدر يسار الشاشة (بمكان الكتاب)، صور الخانات الفارغة
(مثل صورة اللازورد الباهتة بخانة طاولة السحر)، وأيقونة كتاب الوصفات. كلها بكسل آرت مرسوم باليد بنفس دقة أيتمات ماينكرافت (16 بكسل).
المخرجات (RP/textures/ui): sh_alc_cauldron.png (48×44)، sh_alc_ghost_water.png، sh_alc_ghost_flame.png، sh_alc_book.png (16×16)
وصورة لوحة الخيميائي (للكتاب والصفحة) لما تعطيه مسار: python3 tools/gen_alchemy_ui.py [مجلد]"""
import json
import os
import sys
import tempfile

from PIL import Image, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
RP = os.path.join(os.path.dirname(HERE), "AnimePowers", "RP")
sys.path.insert(0, HERE)
import render as R  # noqa: E402
import gen_gear as GG  # noqa: E402

UI = os.path.join(RP, "textures", "ui")


def grad(w, h, top, bot):
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        k = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3)) + (255,))
    return im


CAUL_PAL = {"0": (18, 16, 26), "1": (38, 36, 50), "2": (60, 58, 76), "3": (88, 86, 108), "4": (126, 124, 150), "5": (176, 174, 198),
            "a": (74, 30, 124), "b": (134, 72, 214), "c": (196, 150, 255), "d": (244, 232, 255)}
# قدر مرسوم باليد 20×16: حافة خلفية فاتحة، سائل بنفسجي بفقاعات، شفة أمامية، جسم مدور ضوءه من اليسار، ظل تحت الشفة، رجلين
CAUL_ROWS = [
    "...00000000000000...",
    "..034444444444430...",
    ".03bbcbbbdbbbcbb30..",
    ".02aabbbbbbbbbaa20..",
    "0234444444444444310.",
    "0211111111111111110.",
    "0353322222222211110.",
    "0353322222222221110.",
    "0433322222222221110.",
    ".03332222222222110..",
    ".03322222222221110..",
    "..032222222221110...",
    "...0112222211110....",
    "....000000000000....",
    "....010......010....",
    "....000......000....",
]


def cauldron(scale=4):
    assert all(len(r) == 20 for r in CAUL_ROWS), [len(r) for r in CAUL_ROWS]
    im = Image.new("RGBA", (20, 16), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(CAUL_ROWS):
        for x, ch in enumerate(row):
            if ch != ".":
                px[x, y] = CAUL_PAL[ch] + (255,)
    return im.resize((20 * scale, 16 * scale), Image.NEAREST)


def alchemist_render(size=300):
    d = None
    for f in os.listdir(os.path.join(RP, "models", "entity")):
        g = json.load(open(os.path.join(RP, "models", "entity", f)))
        for geo in g.get("minecraft:geometry", []):
            if geo["description"]["identifier"] == "geometry.sh_alchemist":
                d = geo
    tmp = os.path.join(tempfile.gettempdir(), "sh_alch.geo.json")
    json.dump({"format_version": "1.12.0", "minecraft:geometry": [d]}, open(tmp, "w"))
    m = R.Model(tmp, os.path.join(RP, "textures", "entity", "sh_alchemist.png"))
    bg = (255, 0, 255)
    img = ImageOps.mirror(R.render(m, {}, yaw=28, pitch=8, size=size, bg=bg)).convert("RGBA")
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            if abs(r - 255) + g + abs(b - 255) < 12:
                px[x, y] = (0, 0, 0, 0)
    return img.crop(img.getbbox())


def cauldron_art():
    """القدر (×2) وفوكه ثلاث أرواح صغيرة طالعة منه (بألوان مختلفة): بمكان كتاب طاولة السحر (48×44)"""
    im = Image.new("RGBA", (48, 44), (0, 0, 0, 0))
    im.alpha_composite(cauldron(2), (4, 12))
    for x, y, c in ((-1, 2, 0), (16, -1, 4), (31, 2, 1)):
        fl = GG.icon_soul_flame(GG.SOUL_FLAMES[c][4]).image(1)
        im.alpha_composite(fl, (max(0, x), y) if x >= 0 else (0, y), (max(0, -x), 0) if x < 0 else (0, 0))
    return im


def ghost(px_img):
    """صورة الخانة الفارغة: ظل رصاصي مسطح للأيتم (نفس لون صورة اللازورد الباهتة بطاولة السحر)"""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    src = px_img.convert("RGBA")
    for y in range(16):
        for x in range(16):
            if src.getpixel((x, y))[3] > 0:
                im.putpixel((x, y), (90, 87, 89, 255))
    return im


def banner():
    W, H = 248, 124
    im = grad(W, H, (34, 22, 58), (14, 10, 24))
    d = ImageDraw.Draw(im)
    for i in range(40):                                                         # نجوم/غبار سحري خفيف
        x, y = (i * 53) % W, (i * 29) % (H - 30)
        d.point((x, y), fill=(120 + (i * 7) % 100, 90, 200, 255))
    al = alchemist_render()
    k = (H - 6) / al.size[1]
    al = al.resize((max(1, int(al.size[0] * k)), H - 6), Image.LANCZOS)
    im.alpha_composite(al, (14, 3))
    c = cauldron(4)
    cx, cy = W - c.size[0] - 26, H - c.size[1] - 8
    im.alpha_composite(c, (cx, cy))
    for i, (dx, dy) in enumerate(((-2, -40), (24, -50), (50, -40))):            # ثلاث شعلات روح طالعة من القدر (بدون ما تغطيه)
        fl = GG.icon_soul_flame(GG.SOUL_FLAMES[(0, 3, 4)[i]][4]).image(2)
        im.alpha_composite(fl, (cx + dx, cy + dy))
    d.rectangle([0, 0, W - 1, H - 1], outline=(214, 164, 64, 255), width=2)
    d.rectangle([3, 3, W - 4, H - 4], outline=(90, 60, 30, 255), width=1)
    return im


def icon_book():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, 13, 13], fill=(90, 40, 120, 255), outline=(30, 10, 40, 255))
    d.rectangle([4, 3, 13, 12], fill=(232, 220, 196, 255))
    d.line([(4, 2), (4, 13)], fill=(60, 24, 80, 255))
    fl = GG.icon_soul_flame(GG.SOUL_FLAMES[4][4]).image(1).resize((8, 8), Image.NEAREST)
    im.alpha_composite(fl, (5, 4))
    return im


def main():
    os.makedirs(UI, exist_ok=True)
    cauldron_art().save(os.path.join(UI, "sh_alc_cauldron.png"))
    ghost(GG.icon_potion_kind("water", GG.WATER_COLOR).image(1)).save(os.path.join(UI, "sh_alc_ghost_water.png"))
    ghost(GG.icon_soul_flame(GG.SOUL_FLAMES[0][4]).image(1)).save(os.path.join(UI, "sh_alc_ghost_flame.png"))
    icon_book().save(os.path.join(UI, "sh_alc_book.png"))
    for old in ("sh_alchemy_banner.png", "sh_alc_takeout.png"):                 # صور التصميم القديم (v1.37.1 قبل التعديل)
        if os.path.exists(os.path.join(UI, old)):
            os.remove(os.path.join(UI, old))
    print("alchemy ui ok")
    if len(sys.argv) > 1:
        banner().resize((496, 248), Image.NEAREST).save(os.path.join(sys.argv[1], "alchemist_card.png"))


if __name__ == "__main__":
    main()
