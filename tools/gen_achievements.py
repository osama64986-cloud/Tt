"""الإنجازات (v1.36): قائمة الإنجازات + صورة لكل إنجاز (مفتوح، ومقفول بعلامة استفهام) + ملف بيانات للسكربت.
الصور من أصول المود الحقيقية:
  - الأماكن: مخططات البنايات الحقيقية (tools/sim/dump_plans.mjs) مرسومة إسومترياً (preview_structures.py).
  - الوحوش والشخصيات والصدع: موديلاتهم وتكستشراتهم من RP (render.py).
  - الأيتمات والرتب والقدرات: أيقونات الأيتمات ورموز الـHUD (glyph_E5) مكبرة بكسلات.
المقفول: نفس الصورة معتمة (ظل) وعليها علامة استفهام كبيرة، والاسم يطلع ??? مع تلميح.
المخرجات: RP/textures/ui/sh_ach/<id>.png و<id>_x.png، RP/textures/ui/sh_ach/cat_<key>.png، BP/scripts/achievements.js
التشغيل: python3 tools/gen_achievements.py [مجلد_معاينة]"""
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RP = os.path.join(ROOT, "AnimePowers", "RP")
BP = os.path.join(ROOT, "AnimePowers", "BP")
OUT = os.path.join(RP, "textures", "ui", "sh_ach")
sys.path.insert(0, HERE)
import preview_structures as PS  # noqa: E402
import render as R  # noqa: E402
import gen_hud_art as HUD  # noqa: E402

S = 64  # حجم الصورة

CATS = [
    ("journey", "Journey", (28, 36, 88), (70, 92, 172)),
    ("ranks", "Ranks", (66, 46, 18), (150, 110, 40)),
    ("places", "Places", (40, 70, 110), (120, 170, 220)),
    ("conquest", "Conquest", (44, 18, 64), (112, 52, 152)),
    ("monsters", "Monsters", (58, 18, 18), (132, 52, 40)),
    ("gear", "Gear & Alchemy", (16, 56, 58), (48, 120, 112)),
    ("mastery", "Mastery", (22, 48, 28), (62, 112, 62)),
]

# (id, فئة, الاسم, الوصف بعد الفتح, التلميح وهو مقفول, خبرة, سري, مصدر الصورة)
ACH = [
    # ── الرحلة ──
    ("star_touched", "journey", "Star-Touched", "Draw your power at the Star Temple.", "A fallen star waits on a golden plate.", 60, False, "struct:temple"),
    ("unbound", "journey", "The Dark Star", "The crystal stayed dark for you: one in two hundred.", "Some are chosen by no star at all...", 250, True, "item:sh_star_shard:dark"),
    ("first_lesson", "journey", "First Lesson", "Finish the Trainer's training.", "The old Trainer in the village has a test.", 80, False, "mob:sh:trainer"),
    ("awakened", "journey", "Awakened", "Raise your power to level 3.", "Your power can grow stronger.", 80, False, "glyph:40"),
    ("peak_power", "journey", "Peak of Power", "Reach the highest level of your power.", "Every power has a peak.", 250, False, "glyph:40:gold"),
    ("honed", "journey", "Honed Edge", "Raise one skill to its maximum level.", "Practice one skill until it can grow no more.", 150, False, "item:sh_meteor"),
    ("scroll_reader", "journey", "Scroll Reader", "Use a Skill Upgrade Scroll.", "Some scrolls teach in an instant.", 40, False, "item:sh_skill_scroll"),
    ("lorekeeper", "journey", "Lorekeeper", "Read three chapters of the World Story.", "The Evolution Book remembers the old days.", 60, False, "item:sh_book"),
    # ── الرتب ──
    ("rank_trainee", "ranks", "Trainee", "Reach the rank of Trainee.", "Gain your first rank.", 40, False, "glyph:17"),
    ("rank_warrior", "ranks", "Warrior", "Reach the rank of Warrior.", "A higher rank awaits.", 80, False, "glyph:18"),
    ("rank_elite", "ranks", "Elite", "Reach the rank of Elite.", "A higher rank awaits.", 120, False, "glyph:19"),
    ("rank_commander", "ranks", "Commander", "Reach the rank of Commander.", "A higher rank awaits.", 180, False, "glyph:20"),
    ("rank_legend", "ranks", "Legend", "Reach the rank of Legend.", "Only a few become legends.", 260, False, "glyph:21"),
    ("rank_master", "ranks", "Master", "Reach the rank of Master.", "The last rank of all.", 400, False, "glyph:22"),
    # ── الأماكن ──
    ("visit_village", "places", "Cherry Blossom Road", "Visit a Sakura Village.", "Pink trees and paper lanterns, somewhere out there.", 40, False, "struct:village"),
    ("visit_palace", "places", "Sunset Throne", "Find the Sunset Palace.", "The last light fell on a palace.", 60, False, "struct:palace"),
    ("visit_ruins", "places", "Ruined Prayers", "Explore the Temple Ruins.", "Broken pillars remember the first shard.", 60, False, "struct:ruins"),
    ("visit_tower", "places", "Into the Abyss", "Enter an Abyss Tower.", "A black and violet tower, seven floors high.", 60, False, "struct:tower"),
    ("visit_shrine", "places", "Where Darkness Sleeps", "Find the Dark Sword Shrine.", "A shrine the Abyss sleeps beneath.", 80, False, "struct:shrine"),
    ("visit_lightshrine", "places", "Where Light Endures", "Find the Light Sword Shrine.", "A shrine of light the Abyss never swallowed.", 80, False, "struct:lightshrine"),
    ("meet_alchemist", "places", "The Old Brewer", "Meet the Alchemist in a Sakura Village.", "An old man in a tall hat brews strange things.", 40, False, "mob:sh:alchemist"),
    # ── الفتوحات ──
    ("shrine_dark_clear", "conquest", "Shrine of Darkness Cleansed", "Defeat both guardians of the Dark Sword Shrine.", "Two guardians watch over a dark blade.", 300, False, "struct:shrine:gold"),
    ("shrine_light_clear", "conquest", "Shrine of Light Cleansed", "Defeat both guardians of the Light Sword Shrine.", "Two guardians watch over a blade of light.", 300, False, "struct:lightshrine:gold"),
    ("tower_half", "conquest", "Halfway Up", "Clear the fourth floor of an Abyss Tower.", "Climb, floor by floor.", 150, False, "struct:tower:half"),
    ("tower_top", "conquest", "Master of the Tower", "Conquer the seventh floor of an Abyss Tower.", "Something strong waits at the very top.", 400, False, "struct:tower:gold"),
    ("rift_first", "conquest", "Rift Closer", "Seal your first rift.", "Tears in the world can be closed.", 100, False, "rift:blue"),
    ("rift_five", "conquest", "Rift Hunter", "Seal five rifts.", "Keep closing them.", 250, False, "rift:violet"),
    ("rift_crimson", "conquest", "Crimson Tide", "Seal a Crimson Rift.", "Some rifts bleed red.", 250, False, "rift:crimson"),
    ("rift_abyss", "conquest", "Abyss Gazer", "Seal an Abyssal Rift.", "The rarest rift burns gold.", 500, False, "rift:abyss"),
    # ── الوحوش ──
    ("first_blood", "monsters", "First Blood", "Defeat your first monster.", "The wilds are not safe.", 30, False, "mob:sh:shadow_hound"),
    ("hunter_100", "monsters", "Hundred Hunts", "Defeat 100 monsters.", "Keep hunting.", 250, False, "mob:sh:ember_imp"),
    ("scholar", "monsters", "Monster Scholar", "Fill eight pages of the Monster Book.", "Every new kind of monster adds a page.", 150, False, "item:sh_monster_book"),
    ("slay_gloom", "monsters", "Antler Breaker", "Defeat a Gloomhorn.", "A stag with a beating heart of shadow.", 80, False, "mob:sh:gloomhorn"),
    ("slay_seer", "monsters", "Blind the Seer", "Defeat a Hollow Seer.", "It watches with an orange eye.", 80, False, "mob:sh:hollow_seer"),
    ("slay_fox", "monsters", "Foxfire Out", "Defeat a Veilfox.", "Five tails, each one burning.", 120, False, "mob:sh:veilfox"),
    ("slay_bear", "monsters", "Bear Hug Survivor", "Defeat a Grey Bear.", "Do not let it hug you.", 150, False, "mob:sh:grey_bear"),
    ("slay_mammoth", "monsters", "Volcano Walker", "Defeat a Magmamoth.", "A mountain of fur and lava.", 150, False, "mob:sh:magmamoth"),
    ("slay_mantis", "monsters", "Molt and Fall", "Defeat a Prayer Mantis.", "It prays before it strikes.", 200, False, "mob:sh:prayer_mantis"),
    ("slay_harvester", "monsters", "Cut the Strings", "Defeat a Hollow Harvester.", "A scarecrow that moves like a puppet.", 200, False, "mob:sh:hollow_harvester"),
    # ── العتاد والخيمياء ──
    ("first_material", "gear", "Strike Metal", "Get a crafting material: raw metal, an ingot or a bear part.", "Dig deep: something shines under the stone.", 30, False, "item:sh_raw_dawnsteel"),
    ("tailored", "gear", "Forged", "Wear a piece of crafted armor.", "Ingots and hides make good armor.", 60, False, "item:sh_dawnsteel_chestplate"),
    ("full_set", "gear", "Full Set", "Wear a complete armor set.", "Four pieces of the same metal or beast.", 150, False, "item:sh_abyssium_chestplate"),
    ("first_brew", "gear", "First Brew", "Brew a potion with the Alchemist.", "The old brewer needs ingredients.", 60, False, "item:sh_potion_vitality"),
    ("potion_six", "gear", "Six Flavors", "Drink all six potions.", "Six rare potions exist.", 200, False, "item:sh_potion_focus"),
    ("mana_dry", "gear", "Running on Empty", "Try a skill without enough mana.", "Even powers run dry.", 20, False, "item:sh_potion_mana:dark"),
    # ── الإتقان ──
    ("armed", "mastery", "Legend in Hand", "Hold a legendary weapon.", "Old weapons lie in chests and shrines.", 40, False, "item:sh_cleaver"),
    ("weapon_max", "mastery", "Weapon Master", "Raise a weapon to its highest level.", "A weapon grows with the one who wields it.", 250, False, "item:sh_katana"),
    ("rhythm_finale", "mastery", "Drummer's Finale", "Land a Finale with Rhythm Strike.", "Hit in a steady beat, like a drum.", 150, False, "item:sh_chorus"),
    ("dash_50", "mastery", "Blink", "Dash fifty times.", "Tap a direction twice.", 60, False, "item:sh_stardash"),
    ("pathfinder", "mastery", "Pathfinder", "Use the Explorer Compass.", "A compass that knows where the old places are.", 30, False, "item:sh_compass"),
]
CAT_ICON = {"journey": "struct:temple", "ranks": "glyph:22", "places": "struct:village", "conquest": "rift:violet",
            "monsters": "mob:sh:grey_bear", "gear": "item:sh_potion_mana", "mastery": "item:sh_katana"}

QMARK = [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."]


def grad(top, bot, w=S, h=S):
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3)) + (255,))
    return img


def fit(img, box):
    """يصغر الصورة بنسبة ثابتة حتى تدخل بالمربع box×box."""
    w, h = img.size
    k = box / max(w, h)
    return img.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)


def key_out(img, bg):
    img = img.convert("RGBA")
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) < 12:
                px[x, y] = (0, 0, 0, 0)
    bb = img.getbbox()
    return img.crop(bb) if bb else img


_plans = None


def plans():
    global _plans
    if _plans is None:
        td = tempfile.mkdtemp()
        subprocess.run(["node", os.path.join(HERE, "sim", "dump_plans.mjs"), td], check=True, capture_output=True)
        _plans = td
    return _plans


def entity_info(ident):
    for f in os.listdir(os.path.join(RP, "entity")):
        d = json.load(open(os.path.join(RP, "entity", f)))["minecraft:client_entity"]["description"]
        if d["identifier"] == ident:
            return d["geometry"]["default"], d["textures"]["default"]
    raise KeyError(ident)


def geo_by_id(gid):
    for f in os.listdir(os.path.join(RP, "models", "entity")):
        try:
            d = json.load(open(os.path.join(RP, "models", "entity", f)))
        except Exception:  # noqa: BLE001
            continue
        for g in d.get("minecraft:geometry", []):
            if g["description"]["identifier"] == gid:
                tmp = os.path.join(tempfile.gettempdir(), "sh_ach_geo.json")
                json.dump({"format_version": "1.12.0", "minecraft:geometry": [g]}, open(tmp, "w"))
                return tmp
    raise KeyError(gid)


def picture(src):
    """الصورة (RGBA بنفس الخلفية أو شفافة) حسب المصدر."""
    kind, _, rest = src.partition(":")
    mod = None
    if kind in ("struct", "rift", "glyph", "item") and rest.count(":"):
        rest, mod = rest.rsplit(":", 1)
    if kind == "struct":
        vox = PS.build(json.load(open(os.path.join(plans(), f"plan_{rest}.json"))))
        if rest == "tower" and mod == "half":                                    # نص البرج: الطوابق الأربعة الأولى
            vox = {k: v for k, v in vox.items() if k[1] < 4 * 7}
        img = PS.render(vox, size=420, yaw=35).convert("RGBA")
        w, h = img.size
        side = min(w, h)
        img = img.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
        img = img.resize((S - 6, S - 6), Image.LANCZOS)
        if mod == "gold":                                                       # مفتوح/مُنتصر: لمعة ذهبية
            ov = Image.new("RGBA", img.size, (255, 210, 90, 60))
            img = Image.alpha_composite(img, ov)
        return img, True                                                        # True = تملأ الإطار (بخلفية السما)
    if kind == "mob" or kind == "rift":
        if kind == "mob":
            gid, tex = entity_info(rest)
            m = R.Model(geo_by_id(gid), os.path.join(RP, tex + ".png"))
            pose = {}
        else:
            m = R.Model(geo_by_id(f"geometry.sh_shape_rift_{rest}"), os.path.join(RP, "textures", "entity", "sh_fx_shapes.png"))
            pose = {"spin": {"rot": [0, 25, 0], "pos": [0, 0, 0]}}
        bg = (255, 0, 255)
        img = R.render(m, pose, yaw=35 if kind == "mob" else 20, pitch=12, size=320, bg=bg)
        img = key_out(ImageOps.mirror(img), bg)
        return fit(img, S - 12), False
    if kind == "item":
        img = Image.open(os.path.join(RP, "textures", "items", rest + ".png")).convert("RGBA")
        img = img.resize((44, 44), Image.NEAREST)
        if mod == "dark":
            img = Image.merge("RGBA", [c.point(lambda v: int(v * 0.35)) for c in img.split()[:3]] + [img.split()[3]])
        return img, False
    if kind == "glyph":
        sheet = Image.open(os.path.join(RP, "font", "glyph_E5.png")).convert("RGBA")
        i, C = int(rest), sheet.size[0] // 16
        img = sheet.crop(((i % 16) * C, (i // 16) * C, (i % 16) * C + C, (i // 16) * C + C))
        bb = img.getbbox()
        img = img.crop(bb).resize(((bb[2] - bb[0]) * 3, (bb[3] - bb[1]) * 3), Image.NEAREST)
        if mod == "gold":
            r, g, b, a = img.split()
            img = Image.merge("RGBA", [r.point(lambda v: min(255, v + 60)), g.point(lambda v: min(255, v + 30)), b.point(lambda v: int(v * 0.6)), a])
        return img, False
    raise ValueError(src)


def frame(pic, fills, cat, locked):
    top, bot = next((c[2], c[3]) for c in CATS if c[0] == cat)
    img = grad(top, bot)
    inner = Image.new("RGBA", (S - 6, S - 6), (0, 0, 0, 0))
    if fills:
        inner = pic.resize((S - 6, S - 6))
    else:
        inner.alpha_composite(pic, ((S - 6 - pic.size[0]) // 2, (S - 6 - pic.size[1]) // 2))
    if locked:                                                                   # ظل معتم + علامة استفهام
        g = ImageOps.grayscale(inner.convert("RGB"))
        a = inner.split()[3] if not fills else Image.new("L", inner.size, 255)
        dark = Image.merge("RGBA", [g.point(lambda v: int(18 + v * 0.18)), g.point(lambda v: int(18 + v * 0.18)), g.point(lambda v: int(26 + v * 0.22)), a])
        inner = dark
        img = grad((24, 24, 30), (44, 44, 52))
    img.alpha_composite(inner, (3, 3))
    d = ImageDraw.Draw(img)
    hi, lo = ((120, 120, 128), (64, 64, 70)) if locked else ((236, 196, 92), (150, 108, 36))
    d.rectangle([0, 0, S - 1, S - 1], outline=(14, 14, 18))
    d.rectangle([1, 1, S - 2, S - 2], outline=hi)
    d.line([(1, S - 2), (S - 2, S - 2)], fill=lo); d.line([(S - 2, 1), (S - 2, S - 2)], fill=lo)
    d.rectangle([2, 2, S - 3, S - 3], outline=(14, 14, 18))
    if locked:
        k = 4
        w, h = 5 * k, 7 * k
        ox, oy = (S - w) // 2, (S - h) // 2
        for yy, row in enumerate(QMARK):
            for xx, ch in enumerate(row):
                if ch == "#":
                    d.rectangle([ox + xx * k - 2, oy + yy * k - 2, ox + xx * k + k + 1, oy + yy * k + k + 1], fill=(10, 10, 14))
        for yy, row in enumerate(QMARK):
            for xx, ch in enumerate(row):
                if ch == "#":
                    d.rectangle([ox + xx * k, oy + yy * k, ox + xx * k + k - 1, oy + yy * k + k - 1], fill=(240, 240, 240))
    return img


def write_js():
    data = {
        "cats": [{"key": k, "name": n, "icon": f"textures/ui/sh_ach/cat_{k}"} for k, n, _, _ in CATS],
        "list": [{"id": a[0], "cat": a[1], "name": a[2], "desc": a[3], "hint": a[4], "xp": a[5], "secret": a[6],
                  "icon": f"textures/ui/sh_ach/{a[0]}", "iconLocked": f"textures/ui/sh_ach/{a[0]}_x"} for a in ACH],
    }
    with open(os.path.join(BP, "scripts", "achievements.js"), "w", encoding="utf-8") as f:
        f.write("// يتولد تلقائياً من tools/gen_achievements.py — لا تعدله يدوياً\n")
        f.write("export const ACH_CATS = " + json.dumps(data["cats"], ensure_ascii=False, indent=1) + ";\n")
        f.write("export const ACH = " + json.dumps(data["list"], ensure_ascii=False, indent=1) + ";\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    cache = {}
    sheet = Image.new("RGBA", (12 * (S + 4), ((len(ACH) * 2 + 11) // 12 + 1) * (S + 4)), (30, 30, 36, 255))
    n = 0
    for a in ACH:
        src = a[7]
        if src not in cache:
            cache[src] = picture(src)
        pic, fills = cache[src]
        for locked in (False, True):
            img = frame(pic, fills, a[1], locked)
            img.save(os.path.join(OUT, f"{a[0]}{'_x' if locked else ''}.png"))
            sheet.alpha_composite(img, ((n % 12) * (S + 4) + 2, (n // 12) * (S + 4) + 2)); n += 1
    for key, src in CAT_ICON.items():
        if src not in cache:
            cache[src] = picture(src)
        pic, fills = cache[src]
        frame(pic, fills, key, False).save(os.path.join(OUT, f"cat_{key}.png"))
    write_js()
    print("achievements:", len(ACH), "icons:", n, "dir:", OUT)
    if len(sys.argv) > 1:
        os.makedirs(sys.argv[1], exist_ok=True)
        sheet.resize((sheet.size[0] * 2, sheet.size[1] * 2), Image.NEAREST).save(os.path.join(sys.argv[1], "achievements_sheet.png"))


if __name__ == "__main__":
    main()
