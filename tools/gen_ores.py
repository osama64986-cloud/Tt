"""الخامات (v1.38): معدنين جديدين تحت الأرض، كل واحد بنسخة حجر ونسخة ديب سليت.
  Dawnsteel (ذهبي وردي): من ارتفاع 52 ونازل. Abyssium (بنفسجي غامق): من ارتفاع 26 ونازل (أندر، ودرعه أقوى).
الخام يطيح قطعة خام (Raw)، تذوبها بالفرن أو الـBlast Furnace فتصير سبيكة، ومن السبائك تصنع الدرع (tools/gen_gear.py).
البحث (Microsoft Learn: Features، minecraft:ore_feature، Feature Rules، Block Components، Vanilla Block Tags):
  - التوليد بـ ore_feature (replace_rules: الحجر/الغرانيت/الديورايت/الأنديسايت ← نسخة الحجر، الديب سليت/التف ← نسخة الديب سليت)
    + feature_rules بـ underground_pass وفلتر الأحياء overworld، والارتفاع y = نطاق ثابت بالـdistribution.
  - المعول يكسرها أسرع بالتاغ الرسمي tag:minecraft:is_pickaxe_item_destructible (item_specific_speeds يحتاج تجربة، فما نستعمله).
  - الهندسة minecraft:geometry.full_block (لازمة من 1.21.80) و material_instances بتكستشر وحدة لكل الوجوه.
  - الإسقاط بالسكربت (playerBreakBlock): لازم معول بالدرجة الصح، Silk Touch يطيح البلوكة نفسها، Fortune يزيد الخام.
الرسم: الحجر والديب سليت مرسومين بخوارزميتنا (4-5 درجات رمادي بقع أفقية مثل أسلوب ماينكرافت، مو منسوخة)،
والخام كتل صغيرة مرسومة باليد: فاتح فوك يسار، غامق تحت يمين (Dawnsteel كتل مدورة، Abyssium بلورات مايلة).
التشغيل: python3 tools/gen_ores.py [مجلد_معاينة]"""
import json
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_gear as GG  # noqa: E402

ROOT = os.path.dirname(HERE)
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")

STONE = [(104, 104, 104), (116, 116, 116), (127, 127, 127), (143, 143, 143)]
DEEP = [(47, 47, 55), (61, 61, 67), (81, 81, 81), (100, 100, 100), (121, 121, 121)]
# (المعرف، الاسم، أعلى ارتفاع، حجم العرق، محاولات بكل قطعة أرض، المعول الأقل، وقت الكسر، الشكل)
ORES = [
    ("dawnsteel", "Dawnsteel", 52, 7, 7, 1, "nugget"),
    ("abyssium", "Abyssium", 26, 5, 3, 2, "shard"),
]
TIER_TAG = {1: "minecraft:stone_tier_destructible", 2: "minecraft:iron_tier_destructible"}
NUGGETS = {
    # كتل مدورة (مثل حجم كتل خام الحديد بالفانيلا: 4-7 بكسل لكل كتلة): h لمعة، l فاتح، m أساس، d غامق
    "nugget": [((1, 1), [".hl.", "hlmd", ".mdd"]), ((9, 2), [".h.", "hlm", "lmd", ".d."]), ((12, 8), ["hl", "md"]),
               ((4, 7), [".hl.", "hlmd", "lmmd", ".dd."]), ((9, 11), [".hl", "hmd", "md."]), ((1, 12), ["hl.", "lmd"])],
    # بلورات مايلة سميكة تلمع
    "shard": [((1, 1), ["..hl", ".hlm", "hlmd", "lmd."]), ((10, 2), ["hl..", "lmh.", ".mlm", "..md"]),
              ((5, 8), ["..h", ".hl", "hlm", "lmd"]), ((11, 10), ["h..", "lh.", "mlh", ".md"]), ((1, 12), ["hl", "lm", "md"])],
}


def base(pal, seed, horiz):
    """حجر/ديب سليت 16×16 يتكرر بلا فواصل: لون وسطي وبقع أفتح وأغمق (أفقية أكثر بالديب سليت)"""
    rnd = random.Random(seed)
    mid = len(pal) // 2
    g = [[pal[mid] for _ in range(16)] for _ in range(16)]
    for _ in range(34 if horiz else 40):
        c = rnd.choice([i for i in range(len(pal)) if i != mid])
        w, h = (rnd.randint(2, 5), 1) if horiz else (rnd.randint(2, 4), rnd.randint(1, 2))
        x0, y0 = rnd.randrange(16), rnd.randrange(16)
        for dy in range(h):
            for dx in range(w):
                if dy and dx in (0, w - 1):
                    continue
                g[(y0 + dy) % 16][(x0 + dx) % 16] = pal[c]
    return g


def ore_texture(key, deep):
    ramp = GG.METALS[key]
    col = {"h": ramp[4], "l": ramp[3], "m": ramp[2], "d": ramp[1]}
    g = base(DEEP if deep else STONE, GG.stable((key, deep)), deep)
    shape = next(o[6] for o in ORES if o[0] == key)
    for (x0, y0), rows in NUGGETS[shape]:
        for dy, r in enumerate(rows):
            for dx, ch in enumerate(r):
                if ch in col:
                    g[(y0 + dy) % 16][(x0 + dx) % 16] = col[ch]
    im = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            im.putpixel((x, y), (*g[y][x], 255))
    return im


def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    prev = sys.argv[1] if len(sys.argv) > 1 else None
    tex_dir = os.path.join(RP, "textures", "blocks")
    os.makedirs(tex_dir, exist_ok=True)
    terrain = {"resource_pack_name": "anime_powers", "texture_name": "atlas.terrain", "padding": 8, "num_mip_levels": 4, "texture_data": {}}
    blocks_rp = {"format_version": "1.21.40"}
    lang = []
    sheet = []
    wjson(os.path.join(BP, "loot_tables", "blocks", "sh_ore_empty.json"), {"pools": []})     # الإسقاط بالسكربت (المعول ودرجته)
    for key, name, ymax, vein, iters, tier, _shape in ORES:
        for deep in (False, True):
            bid = f"{'deepslate_' if deep else ''}{key}_ore"
            tex = f"sh_{bid}"
            im = ore_texture(key, deep)
            im.save(os.path.join(tex_dir, f"{tex}.png")); sheet.append(im)
            terrain["texture_data"][tex] = {"textures": f"textures/blocks/{tex}"}
            blocks_rp[f"sh:{bid}"] = {"sound": "deepslate" if deep else "stone"}
            lang.append(f"tile.sh:{bid}.name={'Deepslate ' if deep else ''}{name} Ore")
            comps = {
                "minecraft:geometry": "minecraft:geometry.full_block",
                "minecraft:material_instances": {"*": {"texture": tex, "render_method": "opaque"}},
                "minecraft:destructible_by_mining": {"seconds_to_destroy": 4.5 if deep else 3.0},
                "minecraft:destructible_by_explosion": {"explosion_resistance": 3},
                "minecraft:map_color": "#3e3e46" if deep else "#7f7f7f",
                "minecraft:loot": "loot_tables/blocks/sh_ore_empty.json",
                "tag:minecraft:is_pickaxe_item_destructible": {},
                f"tag:{TIER_TAG[tier]}": {},
                "tag:stone": {},
            }
            wjson(os.path.join(BP, "blocks", f"sh_{bid}.json"), {"format_version": "1.21.80", "minecraft:block": {
                "description": {"identifier": f"sh:{bid}", "menu_category": {"category": "nature", "group": "minecraft:itemGroup.name.ore"}},
                "components": comps}})
        wjson(os.path.join(BP, "features", f"{key}_ore_feature.json"), {"format_version": "1.21.40", "minecraft:ore_feature": {
            "description": {"identifier": f"sh:{key}_ore_feature"}, "count": vein,
            "replace_rules": [
                {"places_block": f"sh:{key}_ore", "may_replace": ["minecraft:stone", "minecraft:granite", "minecraft:diorite", "minecraft:andesite"]},
                {"places_block": f"sh:deepslate_{key}_ore", "may_replace": ["minecraft:deepslate", "minecraft:tuff"]},
            ]}})
        wjson(os.path.join(BP, "feature_rules", f"{key}_ore_rule.json"), {"format_version": "1.21.40", "minecraft:feature_rules": {
            "description": {"identifier": f"sh:{key}_ore_rule", "places_feature": f"sh:{key}_ore_feature"},
            "conditions": {"placement_pass": "underground_pass",
                           "minecraft:biome_filter": [{"test": "has_biome_tag", "operator": "==", "value": "overworld"}]},
            "distribution": {"iterations": iters, "coordinate_eval_order": "zyx",
                             "x": {"distribution": "uniform", "extent": [0, 16]},
                             "y": {"distribution": "uniform", "extent": [-58, ymax]},
                             "z": {"distribution": "uniform", "extent": [0, 16]}}}})
        wjson(os.path.join(BP, "recipes", f"sh_smelt_{key}.json"), {"format_version": "1.20.10", "minecraft:recipe_furnace": {
            "description": {"identifier": f"sh:smelt_{key}"}, "unlock": [{"item": f"sh:raw_{key}"}],
            "tags": ["furnace", "blast_furnace"], "input": f"sh:raw_{key}", "output": f"sh:{key}_ingot"}})
    wjson(os.path.join(RP, "textures", "terrain_texture.json"), terrain)
    wjson(os.path.join(RP, "blocks.json"), blocks_rp)
    lp = os.path.join(RP, "texts", "en_US.lang")
    cur = [ln for ln in open(lp, encoding="utf-8").read().splitlines() if not ln.startswith("tile.sh:")]
    with open(lp, "w", encoding="utf-8") as f:
        f.write("\n".join(cur + lang) + "\n")
    # بيانات للسكربت: الخامات وإسقاطها
    data = {f"sh:{'deepslate_' if d else ''}{k}_ore": {"raw": f"sh:raw_{k}", "tier": t, "metal": k} for k, _n, _y, _v, _i, t, _s in ORES for d in (False, True)}
    with open(os.path.join(BP, "scripts", "ores.js"), "w", encoding="utf-8") as f:
        f.write("// يتولد تلقائياً من tools/gen_ores.py — لا تعدله يدوياً\n")
        f.write("export const ORES = " + json.dumps(data, indent=1) + ";\n")
    print("ores ok:", len(sheet), "blocks")
    if prev:
        S = 8
        W = Image.new("RGBA", (len(sheet) * (16 * S + 8), 16 * S), (40, 40, 40, 255))
        for i, im in enumerate(sheet):
            W.alpha_composite(im.resize((16 * S, 16 * S), Image.NEAREST), (i * (16 * S + 8), 0))
        W.save(os.path.join(prev, "ores.png"))


if __name__ == "__main__":
    main()
