"""فحص سلامة المود قبل التغليف. يرجع كود خروج 1 إذا في خطأ.

الفحوصات:
  1. كل ملفات JSON صحيحة.
  2. صياغة سكربتات JS سليمة (يحتاج node، يتخطى إذا مو موجود).
  3. UUID المنفستين مطابقة لـ tools/uuids.lock.json (حتى ما ينكسر التحديث).
  4. نسخة BP = نسخة RP، وكل منهما رقم صحيح.
  5. كل أيتم له أيقونة بـ item_texture.json وملف الصورة موجود.
  6. كل sh:skill_* المذكور بالسكربت له ملف أيتم.
  7. كل صوت مستعمل معرّف بـ sound_definitions وملف .ogg موجود.
  8. كل كيان BP له كيان RP، وكل مفتاح اسم موجود بملف اللغة الإنجليزي.
  8b. الأسلحة 3D (attachables): الأيتم والموديل والتكستشر والحركات موجودة.
  8c. كل مادة (material) من مواد اللعبة الأصلية (tools/vanilla_materials.txt).
  9. المحاكي (tools/sim): يشغل المهارات والكاتانا والبوصلة والـHUD والضريحين والداش على عالم وهمي (يحتاج node، وتتخطاه --no-sim).
 10. المخططات: قرية الساكورا (check_village.py) وضريحا السيف (check_shrines.py).
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rel(p):
    return os.path.relpath(p, ROOT)


# 1) JSON
for f in glob.glob(os.path.join(ROOT, "AnimePowers", "**", "*.json"), recursive=True):
    try:
        load(f)
    except Exception as e:  # noqa: BLE001
        err(f"JSON غلط: {rel(f)} ({e})")

# 2) صياغة JS
node = shutil.which("node")
if node:
    for f in sorted(glob.glob(os.path.join(BP, "scripts", "*.js"))):
        with open(f, "rb") as fh:
            r = subprocess.run([node, "--input-type=module", "--check"], stdin=fh, capture_output=True)
        if r.returncode != 0:
            err(f"صياغة JS غلط: {rel(f)}\n{r.stderr.decode('utf-8', 'replace')}")
else:
    warnings.append("node مو موجود، تخطيت فحص صياغة JS")

# 3) و 4) المنفستات
try:
    bp_m, rp_m = load(os.path.join(BP, "manifest.json")), load(os.path.join(RP, "manifest.json"))
    lock = load(os.path.join(ROOT, "tools", "uuids.lock.json"))
    for key, m in (("BP", bp_m), ("RP", rp_m)):
        if m["header"]["uuid"] != lock[key]["header"]:
            err(f"{key}: uuid الهيدر تغير عن uuids.lock.json (راح يكسر التحديث)")
        if [x["uuid"] for x in m["modules"]] != lock[key]["modules"]:
            err(f"{key}: uuid المديولات تغيرت عن uuids.lock.json")
    vb, vr = bp_m["header"]["version"], rp_m["header"]["version"]
    if vb != vr:
        err(f"نسخة BP {vb} غير نسخة RP {vr}")
    if not (len(vb) == 3 and all(isinstance(n, int) for n in vb)):
        err(f"صيغة النسخة غلط: {vb}")
except Exception as e:  # noqa: BLE001
    err(f"فحص المنفست فشل: {e}")

# 5) الأيتمات والأيقونات
try:
    tex = load(os.path.join(RP, "textures", "item_texture.json"))["texture_data"]
    item_ids = set()
    for f in glob.glob(os.path.join(BP, "items", "*.json")):
        it = load(f)["minecraft:item"]
        item_ids.add(it["description"]["identifier"])
        name = it["components"]["minecraft:icon"]["textures"]["default"]
        if name not in tex:
            err(f"{rel(f)}: الأيقونة '{name}' مو بـ item_texture.json")
            continue
        png = os.path.join(RP, tex[name]["textures"] + ".png")
        if not os.path.exists(png):
            err(f"{rel(f)}: ملف الصورة ناقص {rel(png)}")
except Exception as e:  # noqa: BLE001
    err(f"فحص الأيتمات فشل: {e}")
    item_ids = set()

js = ""
for f in glob.glob(os.path.join(BP, "scripts", "*.js")):
    with open(f, encoding="utf-8") as fh:
        js += fh.read()

# 6) أيتمات المهارات
for sid in sorted(set(re.findall(r'"(sh:skill_[a-z_]+)"', js))):
    if sid not in item_ids:
        err(f"السكربت يستعمل {sid} وما له ملف أيتم")

# 7) الأصوات
try:
    defs = load(os.path.join(RP, "sounds", "sound_definitions.json"))["sound_definitions"]
    for s in sorted(set(re.findall(r'"(sh\.[a-z_]+)"', js))):
        if s.endswith("_"):  # بادئة صوت يكمّلها الكود (مثل sh.trait_ + id)
            if not any(d.startswith(s) for d in defs):
                err(f"ما كو أصوات تبدأ بـ {s}")
            continue
        if s not in defs:
            err(f"صوت مستعمل وغير معرّف: {s}")
    for name, d in defs.items():
        for snd in d.get("sounds", []):
            path = snd["name"] if isinstance(snd, dict) else snd
            if not os.path.exists(os.path.join(RP, path + ".ogg")):
                err(f"ملف الصوت ناقص لـ {name}: {path}.ogg")
except Exception as e:  # noqa: BLE001
    err(f"فحص الأصوات فشل: {e}")

# 8) الكيانات واللغة
bp_ents = set()
for f in glob.glob(os.path.join(BP, "entities", "*.json")):
    bp_ents.add(load(f)["minecraft:entity"]["description"]["identifier"])
rp_ents = set()
for f in glob.glob(os.path.join(RP, "entity", "*.entity.json")):
    rp_ents.add(load(f)["minecraft:client_entity"]["description"]["identifier"])
for e in sorted(bp_ents - rp_ents):
    err(f"كيان BP بدون كيان RP: {e}")
for e in sorted(rp_ents - bp_ents):
    err(f"كيان RP بدون كيان BP: {e}")

langs = {}
for code in ("ar_SA", "en_US"):
    path = os.path.join(RP, "texts", f"{code}.lang")
    if not os.path.exists(path):
        continue
    keys = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if "=" in line and not line.startswith("#"):
                keys.add(line.split("=", 1)[0].strip())
    langs[code] = keys
if "en_US" not in langs:
    err("ملف اللغة en_US ناقص")
if "ar_SA" in langs and langs["ar_SA"] != langs.get("en_US"):
    err(f"مفاتيح اللغة مختلفة بين ar_SA و en_US: {sorted(langs['ar_SA'] ^ langs.get('en_US', set()))}")
for e in sorted(bp_ents):
    if "fx_" in e:
        continue
    if f"entity.{e}.name" not in langs.get("en_US", set()):
        warnings.append(f"ما لقيت اسم للكيان {e} بملف اللغة")

# 8b) الأسلحة 3D (Attachables): الأيتم، الموديل، التكستشر، والحركات لازم تكون كلها موجودة
anim_ids = set()
for f in glob.glob(os.path.join(RP, "animations", "*.json")):
    try:
        anim_ids |= set(load(f).get("animations", {}).keys())
    except Exception:  # noqa: BLE001
        pass
geo_ids = set()
for f in glob.glob(os.path.join(RP, "models", "entity", "*.geo.json")):
    try:
        for g in load(f).get("minecraft:geometry", []):
            geo_ids.add(g["description"]["identifier"])
    except Exception:  # noqa: BLE001
        pass
for f in glob.glob(os.path.join(RP, "attachables", "*.json")):
    d = load(f)["minecraft:attachable"]["description"]
    if d["identifier"] not in item_ids:
        err(f"{rel(f)}: الأيتم {d['identifier']} مو موجود")
    for g in d.get("geometry", {}).values():
        if g.startswith("geometry.humanoid.armor"):                 # موديلات الدروع الأصلية باللعبة (مثل درع الحديد)
            continue
        if g not in geo_ids:
            err(f"{rel(f)}: الموديل {g} مو موجود")
    for t in d.get("textures", {}).values():
        if t.startswith("textures/misc"):
            continue
        if not os.path.exists(os.path.join(RP, t + ".png")):
            err(f"{rel(f)}: التكستشر {t}.png ناقص")
    for a in d.get("animations", {}).values():
        if a not in anim_ids:
            err(f"{rel(f)}: الحركة {a} مو معرّفة")

# 8c) المواد: كل مادة بالكيانات والأسلحة والدروع لازم تكون من مواد اللعبة الأصلية (مادة غلط مثل entity_alpha = الكيان ما ينرسم)
try:
    with open(os.path.join(ROOT, "tools", "vanilla_materials.txt"), encoding="utf-8") as fh:
        vmats = {ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")}
    for f in glob.glob(os.path.join(RP, "entity", "*.json")) + glob.glob(os.path.join(RP, "attachables", "*.json")):
        d = load(f)
        desc = (d.get("minecraft:client_entity") or d.get("minecraft:attachable"))["description"]
        for m in desc.get("materials", {}).values():
            if m not in vmats:
                err(f"{rel(f)}: المادة {m} مو من مواد اللعبة الأصلية")
except Exception as e:  # noqa: BLE001
    err(f"فحص المواد فشل: {e}")

# 8d) الواجهة (RP/ui/hud_screen.json): الخط مصغر (اللوحة 0.75، الكتابة فوق الهوت بار 0.85) وكل عنصر نعدله موجود بملف Mojang الأصلي
try:
    ui = load(os.path.join(RP, "ui", "hud_screen.json"))
    if ui.get("hud_actionbar_text/actionbar_message", {}).get("font_scale_factor") != 0.75:
        err("hud_screen.json: خط اللوحة لازم يكون مصغر (font_scale_factor 0.75)")
    if ui.get("hud_title_text/title_frame/title", {}).get("font_scale_factor") != 0.85:
        err("hud_screen.json: الكتابة فوق الهوت بار لازم تكون مصغرة (font_scale_factor 0.85)")
    vanilla_paths = {"hud_actionbar_text", "hud_actionbar_text/actionbar_message", "hud_title_text", "hud_title_text/title_frame/title_background",
                     "hud_title_text/title_frame/title", "hud_title_text/subtitle_frame", "root_panel", "root_panel/boss_health_panel/boss_hud_panel/boss_health_grid"}
    for k in ui:
        if k in ("namespace", "sh_player_doll") or k.startswith("sh_"):
            continue
        if k not in vanilla_paths:
            err(f"hud_screen.json: عنصر {k} مو من المسارات المتأكد منها بملف Mojang")
except Exception as e:  # noqa: BLE001
    err(f"فحص الواجهة فشل: {e}")

# 9) المحاكي: يشغل كل المهارات والكاتانا والبوصلة والـHUD على عالم وهمي ويكشف الأخطاء المبلوعة
if node and "--no-sim" not in sys.argv:
    r = subprocess.run([node, os.path.join(ROOT, "tools", "sim", "run_sim.mjs")], capture_output=True)
    if r.returncode != 0:
        err("المحاكي فشل:\n" + r.stdout.decode("utf-8", "replace")[-1800:] + r.stderr.decode("utf-8", "replace")[-600:])

# قرية الساكورا: أسماء بلوكات وحالاتها حقيقية، صندوقين لكل بيت، سرير وطاولة صناعة وفرن، والوصول للداخل والعلية، والأشجار ما تخرب المباني
if node:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run([node, os.path.join(ROOT, "tools", "sim", "dump_plans.mjs"), td], capture_output=True)
        if r.returncode != 0:
            err("طباعة المخططات فشلت:\n" + r.stderr.decode("utf-8", "replace")[-600:])
        else:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_village.py"), os.path.join(td, "plan_village.json")], capture_output=True)
            if r.returncode != 0:
                err("فحص قرية الساكورا فشل:\n" + r.stdout.decode("utf-8", "replace")[-1500:])
            r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_shrines.py"), td], capture_output=True)   # ضريحا السيف: 45×45، أعمدة، مفتوح للسما، بدون صناديق، منارة، وصول
            if r.returncode != 0:
                err("فحص ضريحي السيف فشل:\n" + r.stdout.decode("utf-8", "replace")[-1800:])
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check_plans.py")], capture_output=True)            # أسماء البلوكات بكل البنايات (القصر، الخرائب، المعبد...) موجودة بـBedrock
    if r.returncode != 0:
        err("أسماء بلوكات غلط بالبنايات:\n" + r.stdout.decode("utf-8", "replace")[-1500:])

for w in warnings:
    print("تحذير:", w)
if errors:
    print(f"\nفشل الفحص: {len(errors)} خطأ")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("الفحص نظيف: JSON، صياغة JS، UUID، النسخ، الأيتمات، الأصوات، الكيانات، اللغة، المحاكي.")
