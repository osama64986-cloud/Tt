"""يحاكي منظور الشخص الأول بماينكرافت بيدروك للمخالب:
- ذراع الشخص الأول من ملف موجانغ: rightarm position [13.5,-10,12] rotation [95,-45,115]، و rightitem position [0, 22-15-7, -1].
- قاعدة الربط (مثبتة من الترايدنت الرسمي): pivot العظمة المربوطة ينحط على pivot العظمة الأم.
- كاميرا بمكان العين تباوع لقدام (-z) بمنظور 70°."""
import sys, json, numpy as np
sys.path.insert(0, '/home/user/Tt/tools'); import render as R
from PIL import Image, ImageDraw
RP = '/home/user/Tt/AnimePowers/RP'
geo = json.load(open(f'{RP}/models/entity/sh_w_shadow_claws.geo.json'))['minecraft:geometry'][0]
bones = {b['name']: b for b in geo['bones']}
tex = Image.open(f'{RP}/textures/models/sh_w_shadow_claws.png').convert('RGB'); T = np.array(tex)
hold = json.load(open(f'{RP}/animations/sh_hold.animation.json'))['animations']
ARM_PIV = np.array([-5, 22, 0.]); ITEM_PIV = np.array([-6, 15, 1.])
def M(rot): return R.rot_matrix(*rot)
def arm_xf(p, view):
    if view == "fp":
        p = (p - ARM_PIV) @ M([95, -45, 115]).T + ARM_PIV + np.array([13.5, -10, -12])
    else:
        p = (p - ARM_PIV) @ M([-18, 0, 0]).T + ARM_PIV
    return p
def faces_of(bone, xf):
    out = []
    for c in bone['cubes']:
        o = np.array(c['origin'], float); s = np.array(c['size'], float)
        corners = R.face_corners(*o, *(o + s))
        for fn, pts in corners.items():
            uv = c['uv'][fn]['uv']; col = T[int(uv[1]), int(uv[0])]
            out.append((np.array([xf(np.array(p, float)) for p in pts]), col, fn))
    return out
def item_chain(view, anim):
    a = hold[anim]['bones']['sh_weapon']; piv = np.array(bones['sh_weapon']['pivot'], float)
    rot = a.get('rotation', [0, 0, 0]); pos = np.array(a.get('position', [0, 0, 0]), float); sc = a.get('scale', 1)
    item_off = np.array([0, 0, 1.]) if view == "fp" else np.zeros(3)      # rightitem [0,0,-1] بالشخص الأول
    def xf(p):
        q = (p - piv) * sc
        q = q @ M(rot).T + np.array([pos[0], pos[1], -pos[2]])
        q = q + ITEM_PIV - item_off                                     # pivot على pivot اليد
        return arm_xf(q, view)
    return xf
def tp_bone_chain(view):
    piv = np.array(bones['tp_claws']['pivot'], float)
    return lambda p: arm_xf(p - piv + ARM_PIV, view)
def arm_faces(view):
    o = np.array([-8, 12, -2.]); s = np.array([4, 12, 4.])
    return [(np.array([arm_xf(np.array(p, float), view) for p in pts]), np.array([200, 160, 130]), fn) for fn, pts in R.face_corners(*o, *(o + s)).items()]
def draw_fp(fs, size=420, title=""):
    """كاميرا الشخص الأول: بمكان (0,14,-24) تباوع لـ+z (الذراع تطلع من يمين تحت الشاشة لنصها، مثل اللعبة)."""
    img = Image.new('RGB', (size, size), (120, 160, 210)); d = ImageDraw.Draw(img)
    eye = np.array([0, 14.0, -24.0]); f = size / 2 / np.tan(np.radians(35))
    polys = []
    for pts, col, fn in fs:
        c = pts - eye
        if np.any(c[:, 2] < 0.5): continue
        proj = [(size / 2 + f * p[0] / p[2], size / 2 - f * p[1] / p[2]) for p in c]
        sh = {"north": .9, "south": .9, "east": .75, "west": .75, "up": 1, "down": .6}[fn]
        polys.append((np.mean(np.linalg.norm(c, axis=1)), proj, tuple(int(min(255, v * sh)) for v in col)))
    for _, pr, col in sorted(polys, key=lambda x: -x[0]): d.polygon(pr, fill=col)
    d.text((6, 6), title, fill=(0, 0, 0)); return img
# ── المحاكاة بعد التعديل: عظمة وحدة مربوطة باليد ──
def body_faces(view):
    out = []
    for o, s, col in (([-4, 12, -2], [8, 12, 4], (60, 110, 190)), ([-4, 24, -4], [8, 8, 8], (200, 160, 130)), ([-4, 0, -2], [8, 12, 4], (50, 60, 120)), ([4, 12, -2], [4, 12, 4], (200, 160, 130))):
        o = np.array(o, float); s = np.array(s, float)
        out += [(np.array(pts, float), np.array(col), fn) for fn, pts in R.face_corners(*o, *(o + s)).items()]
    return out
def look_at(fs, eye, target, size=420, title=""):
    eye = np.array(eye, float); fwd = np.array(target, float) - eye; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    img = Image.new('RGB', (size, size), (120, 160, 210)); d = ImageDraw.Draw(img); f = size / 2 / np.tan(np.radians(30))
    polys = []
    for pts, col, fn in fs:
        c = pts - eye; z = c @ fwd
        if np.any(z < 0.5): continue
        proj = [(size / 2 - f * (p @ right) / (p @ fwd), size / 2 - f * (p @ up) / (p @ fwd)) for p in c]   # مقلوب أفقياً مثل اللعبة
        sh = {"north": .9, "south": .9, "east": .75, "west": .75, "up": 1, "down": .6}[fn]
        polys.append((np.mean(np.linalg.norm(c, axis=1)), proj, tuple(int(min(255, v * sh)) for v in col)))
    for _, pr, col in sorted(polys, key=lambda x: -x[0]): d.polygon(pr, fill=col)
    d.text((6, 6), title, fill=(0, 0, 0)); return img
geo = json.load(open(f'{RP}/models/entity/sh_w_shadow_claws.geo.json'))['minecraft:geometry'][0]
bones = {b['name']: b for b in geo['bones']}
hold = json.load(open(f'{RP}/animations/sh_hold.animation.json'))['animations']
out2 = Image.new('RGB', (1260, 420))
out2.paste(draw_fp(arm_faces("fp") + faces_of(bones['sh_weapon'], item_chain("fp", "animation.sh.hold_shadow_claws_fp")), title="FP new (hand channel)"), (0, 0))
tpf = arm_faces("tp") + body_faces("tp") + faces_of(bones['sh_weapon'], item_chain("tp", "animation.sh.hold_shadow_claws_tp"))
out2.paste(look_at(tpf, [-34, 22, -30], [-4, 14, 0], title="TP front-right"), (420, 0))
out2.paste(look_at(tpf, [-38, 18, 4], [-5, 12, 0], title="TP side"), (840, 0))
out2.save(sys.argv[1].replace(".png", "_new.png"))
