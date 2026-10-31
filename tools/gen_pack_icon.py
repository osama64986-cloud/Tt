"""يرسم أيقونة الحزمتين (pack_icon.png) بشكل الكاتانا فوق سماء نجمية. التشغيل: python3 tools/gen_pack_icon.py"""
import os
import random
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 256
random.seed(8)
bg = Image.new("RGB", (N, N))
px = bg.load()
for y in range(N):
    for x in range(N):
        t = y / N
        d = ((x - N * 0.62) ** 2 + (y - N * 0.4) ** 2) ** 0.5 / N
        base = (int(14 + 40 * (1 - t) + 40 * max(0, 0.45 - d)), int(10 + 14 * (1 - t) + 14 * max(0, 0.45 - d)), int(36 + 70 * (1 - t) + 90 * max(0, 0.45 - d)))
        px[x, y] = base
d = ImageDraw.Draw(bg)
for _ in range(70):
    x, y = random.randrange(N), random.randrange(N)
    c = random.choice([(255, 255, 255), (190, 200, 255), (255, 230, 150)])
    d.rectangle([x, y, x + random.choice([1, 1, 2]) - 1, y + random.choice([1, 1, 2]) - 1], fill=c)
icon = Image.open(os.path.join(ROOT, "AnimePowers/RP/textures/items/sh_katana.png")).convert("RGBA")
big = icon.resize((N - 24, N - 24), Image.NEAREST)
glow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
glow.paste(big, (12, 12), big)
halo = glow.filter(ImageFilter.GaussianBlur(10))
tint = Image.new("RGBA", (N, N), (150, 90, 255, 0))
tint.putalpha(halo.getchannel("A").point(lambda v: min(255, v * 2)))
out = bg.convert("RGBA")
out.alpha_composite(tint)
out.alpha_composite(glow)
for pk in ("BP", "RP"):
    out.convert("RGB").save(os.path.join(ROOT, "AnimePowers", pk, "pack_icon.png"))
out.convert("RGB").resize((N, N)).save(os.environ.get("PREVIEW_DIR", "/tmp") + "/pack_icon.png")
print("ok")
