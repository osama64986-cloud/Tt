"""فحص الإشارات بكل المود (v1.44): كل شي يأشر على شي ثاني لازم يكون موجود.

- الكيانات بحزمة الموارد (RP/entity): كل تكستشر ملفه موجود، كل موديل (geometry) معرّف، كل أنميشن ومتحكم أنميشن
  معرّف بالحزمة أو من أسماء ماينكرافت، وكل render controller موجود، وكل أنميشن بـ scripts.animate معرّف بنفس الكيان.
- عظام الأنميشن: كل عظمة يحركها أنميشن الكيان موجودة بموديله (تحذير بس: ماينكرافت يتجاهلها).
- السكربتات: كل كيان sh:* ينطلب (spawnEntity، type: ...) موجود بـ BP/entities، وكل أيتم sh:* ينعطى أو ينفحص موجود بـ BP/items أو بلوكة.
- حزمة السلوك: جداول الغنائم وقواعد الظهور تأشر على أشياء موجودة.
التشغيل: python3 tools/audit_refs.py   (يرجع 1 إذا لگى خطأ)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")
errors, warns = [], []


def load(p):
    t = open(p, encoding="utf-8").read()
    t = re.sub(r"^\s*//.*$", "", t, flags=re.M)
    return json.loads(t)


def rel(p):
    return os.path.relpath(p, ROOT)


# ───── الموديلات والأنميشن والمتحكمات ─────
geos = {}
for f in glob.glob(os.path.join(RP, "models", "**", "*.json"), recursive=True):
    d = load(f)
    for g in d.get("minecraft:geometry", []):
        geos[g["description"]["identifier"]] = {b["name"].lower() for b in g.get("bones", [])}
    for k, v in d.items():                                         # الصيغة القديمة "geometry.x": {...}
        if k.startswith("geometry.") and isinstance(v, dict):
            geos[k.split(":")[0]] = {b["name"].lower() for b in v.get("bones", [])}
anims, ctrls, rcs = {}, set(), set()
for f in glob.glob(os.path.join(RP, "animations", "*.json")):
    for k, v in load(f).get("animations", {}).items():
        anims[k] = {b.lower() for b in v.get("bones", {})}
for f in glob.glob(os.path.join(RP, "animation_controllers", "*.json")):
    ctrls |= set(load(f).get("animation_controllers", {}))
for f in glob.glob(os.path.join(RP, "render_controllers", "*.json")):
    rcs |= set(load(f).get("render_controllers", {}))


def mine(name):
    """أسماء المود (sh_ / .sh / sh:): هاي نقدر نتأكد منها؛ أسماء ماينكرافت الأصلية (مثل controller.render.armor) مو بالمستودع."""
    return "sh_" in name or ".sh" in name or "sh:" in name


def tex_ok(path):
    return any(os.path.exists(os.path.join(RP, path + ext)) for ext in (".png", ".tga", ".jpg"))


VANILLA_PREFIX = ("animation.player.", "animation.humanoid.", "controller.animation.player.", "controller.animation.humanoid.",
                  "animation.common.", "controller.render.player", "controller.render.default", "controller.render.item_default",
                  "animation.villager.", "controller.animation.villager.")
for f in sorted(glob.glob(os.path.join(RP, "entity", "*.json")) + glob.glob(os.path.join(RP, "attachables", "*.json"))):
    d = load(f)
    desc = (d.get("minecraft:client_entity") or d.get("minecraft:attachable") or {}).get("description", {})
    if not desc:
        continue
    for k, t in desc.get("textures", {}).items():
        if mine(t) and not tex_ok(t):
            errors.append(f"{rel(f)}: التكستشر {k} = {t} ملفه مو موجود")
    used_geos = []
    for k, g in desc.get("geometry", {}).items():
        if g in geos:
            used_geos.append(g)
        elif mine(g):
            errors.append(f"{rel(f)}: الموديل {g} مو معرّف")
    names = desc.get("animations", {})
    for k, a in names.items():
        if a.startswith("controller."):
            if a not in ctrls and mine(a):
                errors.append(f"{rel(f)}: متحكم الأنميشن {a} مو معرّف")
        elif a not in anims and mine(a):
            errors.append(f"{rel(f)}: الأنميشن {a} مو معرّف")
    for item in desc.get("scripts", {}).get("animate", []):
        key = item if isinstance(item, str) else next(iter(item))
        if key not in names:
            errors.append(f"{rel(f)}: scripts.animate يشغل {key} وهو مو بقائمة animations")
    for rc in desc.get("render_controllers", []):
        rc = rc if isinstance(rc, str) else next(iter(rc))
        if rc not in rcs and mine(rc):
            errors.append(f"{rel(f)}: render controller {rc} مو موجود")
    # العظام: أنميشن الكيان يحرك عظام موجودة بموديله (أي موديل من موديلاته)
    bones = set().union(*[geos[g] for g in used_geos]) if used_geos else set()
    if bones:
        for k, a in names.items():
            if a in anims:
                miss = sorted(b for b in anims[a] if b not in bones)
                if miss and len(miss) == len(anims[a]):
                    warns.append(f"{rel(f)}: الأنميشن {a} ما يلگى ولا عظمة من عظامه بالموديل ({', '.join(miss[:4])})")

# ───── حزمة السلوك ─────
bp_ents = {load(f)["minecraft:entity"]["description"]["identifier"] for f in glob.glob(os.path.join(BP, "entities", "*.json"))}
bp_items = {load(f)["minecraft:item"]["description"]["identifier"] for f in glob.glob(os.path.join(BP, "items", "*.json"))}
bp_blocks = {load(f)["minecraft:block"]["description"]["identifier"] for f in glob.glob(os.path.join(BP, "blocks", "*.json"))}
for f in glob.glob(os.path.join(BP, "entities", "*.json")):
    raw = open(f, encoding="utf-8").read()
    for lt in re.findall(r'"table"\s*:\s*"([^"]+)"', raw):
        if not os.path.exists(os.path.join(BP, lt)):
            errors.append(f"{rel(f)}: جدول الغنائم {lt} مو موجود")
for f in glob.glob(os.path.join(BP, "spawn_rules", "*.json")):
    ident = load(f)["minecraft:spawn_rules"]["description"]["identifier"]
    if ident.startswith("sh:") and ident not in bp_ents:
        errors.append(f"{rel(f)}: قاعدة ظهور لكيان مو موجود {ident}")
for f in glob.glob(os.path.join(BP, "loot_tables", "**", "*.json"), recursive=True):
    for it in re.findall(r'"name"\s*:\s*"(sh:[a-z0-9_]+)"', open(f, encoding="utf-8").read()):
        if it not in bp_items and it not in bp_blocks:
            errors.append(f"{rel(f)}: أيتم {it} مو موجود")

# ───── السكربتات ─────
src = "\n".join(open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(BP, "scripts", "*.js")) if not f.endswith("lang_ar.js"))
ent_refs = set(re.findall(r'spawnEntity\(\s*"(sh:[a-z0-9_]+)"', src)) | set(re.findall(r'type:\s*"(sh:[a-z0-9_]+)"', src))
for e in sorted(ent_refs):
    if e not in bp_ents:
        errors.append(f"scripts: الكيان {e} مو موجود بـ BP/entities")
item_refs = set(re.findall(r'(?:new ItemStack|giveItem|hasItem|countItem|removeItem)\(\s*(?:[a-z]+,\s*)?"(sh:[a-z0-9_]+)"', src))
item_refs |= set(re.findall(r'(?:const|let)\s+[A-Z_]+\s*=\s*"(sh:[a-z0-9_]+)"', src))
for it in sorted(item_refs):
    if it not in bp_items and it not in bp_blocks and it not in bp_ents:
        errors.append(f"scripts: الأيتم {it} مو موجود بـ BP/items")
for it in sorted(set(re.findall(r'"sh:skill_[a-z]+"', src))):
    if it.strip('"') not in bp_items:
        errors.append(f"scripts: أيتم المهارة {it} مو موجود")

# ───── الواجهات (RP/ui): كل "@namespace.عنصر" موجود بنفس الملف، وكل معادلة binding أقواسها وعلاماتها متوازنة ─────
ui_n = 0
for f in glob.glob(os.path.join(RP, "ui", "*.json")):
    d = load(f)
    ns = d.get("namespace")

    def walk(node, where):
        global ui_n
        if isinstance(node, dict):
            for k, v in node.items():
                if "@" in k and isinstance(v, dict):
                    ref = k.split("@", 1)[1]
                    if ref.startswith(ns + ".") and ref[len(ns) + 1:] not in d:
                        errors.append(f"{rel(f)}: {where}/{k}: العنصر {ref} مو موجود")
                if k == "bindings" and isinstance(v, list):
                    for b in v:
                        for kk in ("source_property_name", "binding_name"):
                            e = b.get(kk, "")
                            if e.startswith("("):
                                ui_n += 1
                                body = re.sub(r"'[^']*'", "", e)
                                if e.count("'") % 2 or body.count("(") != body.count(")"):
                                    errors.append(f"{rel(f)}: {where}: معادلة غلط (أقواس/علامات): {e[:80]}")
                walk(v, where if not isinstance(v, dict) else f"{where}/{k}"[-60:])
        elif isinstance(node, list):
            for x in node:
                walk(x, where)
    walk(d, os.path.basename(f))

for w in warns:
    print("تحذير:", w)
if errors:
    print(f"\nفحص الإشارات: {len(errors)} خطأ")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"فحص الإشارات نظيف: {ui_n} معادلة واجهة، {len(geos)} موديل، {len(anims)} أنميشن، {len(bp_ents)} كيان، {len(bp_items)} أيتم، {len(ent_refs)} كيان و{len(item_refs)} أيتم بالسكربت"
      + (f" ({len(warns)} تحذير)" if warns else ""))
