"""يولد أصول v1.7: أصوات جديدة (ogg)، أيقونات قدرة سيد النجوم، جزيء البكسل، وملفات الأيتمات.
يشغل من جذر المشروع:  python3 tools/gen_v17_assets.py
آمن لإعادة التشغيل (يكتب فوق نفس الملفات ولا يلمس الـ UUID).
"""
import json
import math
import os
import random
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "AnimePowers", "RP")
BP = os.path.join(ROOT, "AnimePowers", "BP")
SR = 44100
random.seed(17)
rng = np.random.default_rng(17)


# ───────────────────────── أدوات صوت بسيطة ─────────────────────────
def t_axis(dur):
    return np.arange(int(SR * dur)) / SR


def env(n, attack=0.005, decay=6.0):
    t = np.arange(n) / SR
    a = np.minimum(1.0, t / max(attack, 1e-4))
    return a * np.exp(-decay * t)


def sweep(f0, f1, dur, vol=0.5, decay=3.0, wave_kind="sine"):
    n = int(SR * dur)
    f = np.linspace(f0, f1, n)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if wave_kind == "saw":
        s = 2 * ((ph / (2 * np.pi)) % 1) - 1
    elif wave_kind == "square":
        s = np.sign(np.sin(ph))
    else:
        s = np.sin(ph)
    return s * env(n, 0.01, decay) * vol


def lowpass(x, k):
    """مرشح تمرير منخفض بسيط (k بين 0 و1، الأصغر أنعم)."""
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        y[i] = acc
    return y


def noise(dur, vol=0.5, decay=6.0, k=0.5, attack=0.003):
    n = int(SR * dur)
    x = rng.uniform(-1, 1, n)
    if k < 1:
        x = lowpass(x, k)
    return x * env(n, attack, decay) * vol


def whoosh(dur, f_from, f_to, vol=0.5):
    """ضجيج مع ترشيح متغير (يرتفع أو ينزل)."""
    n = int(SR * dur)
    x = rng.uniform(-1, 1, n)
    y = np.zeros(n)
    acc = 0.0
    ks = np.linspace(f_from, f_to, n)
    for i in range(n):
        acc += ks[i] * (x[i] - acc)
        y[i] = acc
    sh = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    return y * sh * vol * 2.2


def bell(freq, dur=0.5, vol=0.4, decay=8.0, vib=0.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = freq * (1 + vib * np.sin(2 * np.pi * 5 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.4 * np.sin(2.76 * ph) + 0.2 * np.sin(5.4 * ph)
    return s * env(n, 0.002, decay) * vol / 1.6


def drone(freq, dur, vol=0.4, wob=3.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t + 2 * np.sin(2 * np.pi * wob * t) * 0.5)
    s += 0.5 * np.sin(2 * np.pi * freq * 2.01 * t)
    sh = np.minimum(1, t / 0.15) * np.minimum(1, (dur - t) / 0.3)
    return s * sh * vol / 1.5


def place(total, parts):
    n = int(SR * total)
    out = np.zeros(n)
    for off, arr in parts:
        i = int(off * SR)
        j = min(n, i + len(arr))
        if i < n:
            out[i:j] += arr[: j - i]
    peak = np.max(np.abs(out)) or 1
    return out / peak * 0.9 if peak > 0.9 else out


def save_ogg(name, samples):
    path = os.path.join(RP, "sounds", "sh", name + ".ogg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tmp = tf.name
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", "4", path], check=True)
    os.unlink(tmp)


# اسم الصوت: (المسافة القصوى, المولّد)
SOUNDS = {
    # سيد النجوم
    "meteor_fall": (48, lambda: place(0.7, [(0, whoosh(0.7, 0.04, 0.5, 0.7)), (0, sweep(1100, 220, 0.7, 0.25, 2.0))])),
    "meteor_hit": (64, lambda: place(1.0, [(0, sweep(110, 32, 0.8, 0.9, 3.5)), (0, noise(0.9, 0.7, 4.0, 0.25)), (0.01, bell(190, 0.5, 0.4, 9))])),
    "gravwell": (40, lambda: place(1.4, [(0, drone(62, 1.4, 0.55, 2.5)), (0, whoosh(1.4, 0.02, 0.2, 0.4))])),
    "orbit": (32, lambda: place(0.9, [(0, bell(880, 0.8, 0.3, 4, 0.01)), (0.08, bell(1320, 0.7, 0.25, 5, 0.012)), (0.16, bell(1760, 0.6, 0.2, 6, 0.01))])),
    "const_mark": (32, lambda: place(0.4, [(0, bell(1318, 0.35, 0.5, 10)), (0.05, bell(1976, 0.3, 0.3, 12))])),
    "const_zap": (48, lambda: place(0.45, [(0, sweep(3400, 180, 0.3, 0.5, 5, "saw")), (0, noise(0.3, 0.6, 9, 0.9)), (0.02, bell(2400, 0.25, 0.3, 14))])),
    "stardash": (40, lambda: place(0.4, [(0, sweep(380, 2600, 0.28, 0.4, 5)), (0, whoosh(0.35, 0.1, 0.7, 0.5)), (0.12, bell(2200, 0.25, 0.25, 12))])),
    "blackhole": (64, lambda: place(2.0, [(0, drone(44, 2.0, 0.7, 1.6)), (0, sweep(700, 55, 1.9, 0.25, 1.2)), (0, whoosh(2.0, 0.03, 0.25, 0.5))])),
    "blackhole_end": (72, lambda: place(1.4, [(0, sweep(60, 1100, 0.45, 0.4, 1.5)), (0.42, sweep(130, 28, 0.9, 1.0, 3)), (0.42, noise(1.0, 0.8, 3.5, 0.3))])),
    "supernova_charge": (56, lambda: place(1.7, [(0, sweep(70, 2200, 1.6, 0.5, 0.4, "saw")), (0, whoosh(1.7, 0.02, 0.6, 0.35))])),
    "supernova_boom": (96, lambda: place(2.2, [(0, sweep(95, 20, 1.6, 1.0, 1.8)), (0, noise(1.8, 0.9, 2.2, 0.3)), (0.02, bell(120, 1.2, 0.5, 4)), (0.05, bell(2600, 0.9, 0.25, 4))])),
    # عام
    "ready": (16, lambda: place(0.5, [(0, bell(1175, 0.3, 0.35, 10)), (0.09, bell(1568, 0.35, 0.3, 9))])),
    "compass": (16, lambda: place(0.45, [(0, sweep(900, 1500, 0.2, 0.3, 6)), (0.1, bell(1760, 0.3, 0.3, 10))])),
    # كاتانا
    "kat_step": (40, lambda: place(0.35, [(0, whoosh(0.3, 0.6, 0.1, 0.7)), (0, sweep(1500, 260, 0.16, 0.3, 7)), (0.1, bell(1900, 0.2, 0.2, 14))])),
    "kat_wave": (48, lambda: place(0.5, [(0, sweep(600, 2100, 0.35, 0.4, 4, "saw")), (0, whoosh(0.45, 0.08, 0.6, 0.5)), (0.05, bell(2200, 0.3, 0.2, 10))])),
    "kat_storm": (48, lambda: place(0.9, [(i * 0.17, whoosh(0.2, 0.7, 0.1, 0.6)) for i in range(5)] + [(i * 0.17, bell(1500 + 120 * i, 0.15, 0.2, 18)) for i in range(5)])),
    "kat_exec": (64, lambda: place(1.0, [(0, sweep(180, 40, 0.5, 0.9, 5)), (0, noise(0.4, 0.7, 8, 0.4)), (0.02, bell(2100, 0.7, 0.35, 6)), (0.04, whoosh(0.4, 0.8, 0.1, 0.5))])),
    "kat_levelup": (24, lambda: place(1.1, [(0.0, bell(440, 0.7, 0.35, 5)), (0.12, bell(523, 0.7, 0.35, 5)), (0.24, bell(659, 0.7, 0.35, 5)), (0.36, bell(880, 0.9, 0.4, 4))])),
    # صفات مستعير الصفات
    "trait_rock": (32, lambda: place(0.6, [(0, sweep(130, 45, 0.4, 0.9, 6)), (0, noise(0.4, 0.5, 9, 0.2))])),
    "trait_fangs": (32, lambda: place(0.6, [(0, sweep(95, 70, 0.5, 0.5, 3, "saw")), (0, noise(0.5, 0.4, 5, 0.15))])),
    "trait_wings": (32, lambda: place(0.7, [(0, whoosh(0.65, 0.05, 0.5, 0.8)), (0.25, whoosh(0.4, 0.1, 0.6, 0.5))])),
    "trait_eye": (32, lambda: place(0.6, [(0, bell(1760, 0.5, 0.4, 7)), (0.1, bell(2640, 0.4, 0.2, 9))])),
}


def gen_sounds():
    sd_path = os.path.join(RP, "sounds", "sound_definitions.json")
    with open(sd_path, encoding="utf-8") as f:
        sd = json.load(f)
    for name, (maxd, fn) in SOUNDS.items():
        save_ogg(name, fn())
        sd["sound_definitions"]["sh." + name] = {
            "category": "player", "min_distance": 4, "max_distance": maxd,
            "sounds": [{"name": "sounds/sh/" + name, "volume": 1.0}],
        }
    with open(sd_path, "w", encoding="utf-8") as f:
        json.dump(sd, f, indent=2, ensure_ascii=False)
    print("sounds:", len(SOUNDS))


# ───────────────────────── أيقونات سيد النجوم ─────────────────────────
HI, MID, LO = (170, 200, 255), (40, 62, 150), (12, 18, 62)
GOLD = (255, 220, 120)
WHITE = (245, 248, 255)


def frame(d):
    """إطار دائري نجمي: حلقة ذهبية ونقاط نجوم."""
    d.ellipse([1, 1, 30, 30], fill=LO)
    d.ellipse([3, 3, 28, 28], fill=MID)
    d.ellipse([1, 1, 30, 30], outline=GOLD)
    d.ellipse([4, 4, 27, 27], outline=(70, 100, 200))
    for x, y in ((6, 8), (24, 6), (26, 22), (8, 25), (21, 27)):
        d.point((x, y), fill=WHITE)


def star(d, cx, cy, r, c):
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.38
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=c)


def glyph(d, k):
    if k == "meteor":
        d.line([(22, 8), (9, 21)], fill=(255, 150, 60), width=3)
        d.line([(24, 6), (12, 18)], fill=(255, 220, 120), width=2)
        d.ellipse([6, 18, 13, 25], fill=GOLD)
        d.ellipse([8, 20, 11, 23], fill=WHITE)
        d.point((20, 24), fill=WHITE); d.point((25, 19), fill=WHITE)
    elif k == "gravwell":
        for r, col in ((11, (120, 160, 255)), (8, (170, 200, 255)), (5, WHITE)):
            d.arc([16 - r, 16 - r, 16 + r, 16 + r], 20, 300, fill=col, width=2)
        d.ellipse([14, 14, 18, 18], fill=(10, 10, 30))
        d.polygon([(25, 8), (22, 9), (24, 12)], fill=WHITE)
    elif k == "orbit":
        d.ellipse([6, 11, 25, 21], outline=(150, 190, 255), width=1)
        d.ellipse([13, 13, 18, 18], fill=GOLD)
        for x, y in ((6, 15), (25, 15), (16, 11)):
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=WHITE)
    elif k == "constellation":
        pts = [(7, 22), (12, 11), (19, 15), (25, 8), (23, 23)]
        d.line(pts, fill=(130, 170, 255), width=1)
        for x, y in pts:
            star(d, x, y, 3.2, GOLD)
    elif k == "stardash":
        d.polygon([(28, 16), (17, 9), (17, 13), (5, 13), (5, 19), (17, 19), (17, 23)], fill=WHITE)
        d.line([(4, 9), (12, 9)], fill=(150, 190, 255)); d.line([(4, 23), (12, 23)], fill=(150, 190, 255))
        star(d, 24, 8, 3, GOLD)
    elif k == "blackhole":
        d.ellipse([5, 12, 26, 20], outline=GOLD, width=2)
        d.ellipse([10, 10, 21, 21], fill=(6, 6, 18))
        d.ellipse([10, 10, 21, 21], outline=(150, 100, 255))
        d.arc([5, 12, 26, 20], 200, 340, fill=WHITE)
    elif k == "supernova":
        star(d, 16, 16, 12, GOLD)
        star(d, 16, 16, 7, WHITE)
        for x, y in ((6, 6), (26, 7), (27, 26), (5, 26)):
            d.point((x, y), fill=WHITE)


STAR_SKILLS = [
    # (id, ملف, اسم الأيتم)
    ("meteor", "sh_meteor", "§9نيزك"),
    ("gravwell", "sh_gravwell", "§9بئر الجاذبية"),
    ("orbit", "sh_orbit", "§9مدار النجوم"),
    ("constellation", "sh_constellation", "§9كوكبة"),
    ("stardash", "sh_stardash", "§9ومضة نجمية"),
    ("blackhole", "sh_blackhole", "§9ثقب أسود"),
    ("supernova", "sh_supernova", "§9المستعر الأعظم"),
]


def gen_icons_and_items():
    tex_path = os.path.join(RP, "textures", "item_texture.json")
    with open(tex_path, encoding="utf-8") as f:
        tex = json.load(f)
    for sid, fname, disp in STAR_SKILLS:
        im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        frame(d)
        glyph(d, sid)
        im.save(os.path.join(RP, "textures", "items", fname + ".png"))
        tex["texture_data"][fname] = {"textures": "textures/items/" + fname}
        item = {
            "format_version": "1.21.60",
            "minecraft:item": {
                "description": {"identifier": f"sh:skill_{sid}", "menu_category": {"category": "none"}},
                "components": {
                    "minecraft:icon": {"textures": {"default": fname}},
                    "minecraft:max_stack_size": 1,
                    "minecraft:display_name": {"value": disp},
                },
            },
        }
        with open(os.path.join(BP, "items", fname + ".json"), "w", encoding="utf-8") as f:
            json.dump(item, f, indent=2, ensure_ascii=False)
    with open(tex_path, "w", encoding="utf-8") as f:
        json.dump(tex, f, indent=2, ensure_ascii=False)
    # contact sheet للمراجعة
    sheet = Image.new("RGBA", (32 * 7 + 8 * 8, 48), (90, 90, 96, 255))
    for i, (_, fname, _) in enumerate(STAR_SKILLS):
        sheet.alpha_composite(Image.open(os.path.join(RP, "textures", "items", fname + ".png")), (8 + i * 40, 8))
    out = os.path.join(os.environ.get("PREVIEW_DIR", tempfile.gettempdir()), "star_icons.png")
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(out)
    print("icons:", len(STAR_SKILLS), "preview", out)


if __name__ == "__main__":
    gen_sounds()
    gen_icons_and_items()
