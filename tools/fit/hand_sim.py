"""محاكي مسك الأسلحة (Attachables) بالمنظور الأول والثالث، بنفس رياضيات ماينكرافت بيدروك كما ينفذها Blockbench
(js/formats/bedrock/attachable_preview.js، وهو المرجع اللي يطابق اللعبة):

  * العظمة المربوطة بـ q.item_slot_to_bone_name: نقطة الموديل (0,24,0) تنحط على pivot عظمة اليد rightItem (-6,15,1)،
    والموديل يتبع الذراع. (pivot العظمة نفسها ما يحدد مكان الربط؛ يحدد بس محور دوران حركة المسك.)
    تأكيد من ملفات موجانغ: المنظار (pivot [0,0,0]، حركة [1,22,0] و[0,-90,0]) يطلع بالضبط من الكف لقدام،
    والترايدنت pivot [0,24,0] = نقطة القبضة.
  * المنظور الثالث: الذراع مرفوعة لقدام ~15-18 درجة (animation.player.holding)، ومحورها الكتف (-5,22,0).
  * المنظور الأول: الذراع [95,-45,115] (animation.player.first_person.empty_hand)، والكاميرا مثل Blockbench.
  * الإحداثيات الداخلية مثل Blockbench/three.js: x مقلوب (x_int = -x)، الدوران الداخلي Euler(-rx, -ry, rz) بترتيب ZYX،
    والإزاحة (-tx, ty, tz)، والمصفوفة T·R·S حول pivot العظمة.
الاستعمال: python3 tools/fit/hand_sim.py out.png [سلاح1,سلاح2...]   (بدون أسماء = كل الأسلحة)
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RP = os.path.join(ROOT, "AnimePowers", "RP")
FACES = ("north", "south", "east", "west", "up", "down")


def euler_zyx(rx, ry, rz):
    """three.js Euler(rx,ry,rz,'ZYX') بالدرجات → مصفوفة Rz·Ry·Rx"""
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def bed_rot(r):
    """دوران بيدروك [rx,ry,rz] → مصفوفة داخلية"""
    return euler_zyx(-r[0], -r[1], r[2])


def to_int(p):
    return np.array([-p[0], p[1], p[2]], float)


def cube_faces(c):
    """زوايا وجوه مكعب (بإحداثيات بيدروك) + اسم الوجه"""
    o = np.array(c["origin"], float); s = np.array(c["size"], float)
    x0, y0, z0 = o; x1, y1, z1 = o + s
    f = {
        "north": [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
        "south": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        "west": [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)],
        "east": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
        "up": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        "down": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
    }
    if "rotation" in c:
        piv = np.array(c.get("pivot", o + s / 2), float); R = bed_rot_cube(c["rotation"])
        f = {k: [tuple(R @ (np.array(p) - piv) + piv) for p in v] for k, v in f.items()}
    return f


def bed_rot_cube(r):
    """دوران مكعب بإحداثيات بيدروك نفسها (نحوله داخلي ونرجعه)"""
    M = np.diag([-1, 1, 1.0])
    return M @ bed_rot(r) @ M


def load_weapon(ident):
    g = json.load(open(os.path.join(RP, "models", "entity", f"sh_w_{ident}.geo.json")))["minecraft:geometry"][0]
    tex = np.array(Image.open(os.path.join(RP, "textures", "models", f"sh_w_{ident}.png")).convert("RGBA"))
    anims = json.load(open(os.path.join(RP, "animations", "sh_hold.animation.json")))["animations"]
    return g, tex, anims


def weapon_polys(ident, view, anims=None, arm_tp_deg=18.0):
    """مضلعات السلاح بالإحداثيات الداخلية للمشهد (منظور أول أو ثالث)"""
    g, tex, A = load_weapon(ident)
    A = anims or A
    out = []
    for b in g["bones"]:
        a = A.get(f"animation.sh.hold_{ident}_{view}", {}).get("bones", {}).get(b["name"], {})
        rot = a.get("rotation", [0, 0, 0]); pos = a.get("position", [0, 0, 0]); sc = a.get("scale", 1)
        sc = np.array(sc if isinstance(sc, list) else [sc] * 3, float)
        R = bed_rot([rot[i] + (b.get("rotation") or [0, 0, 0])[i] for i in range(3)])
        P = to_int(b["pivot"]); T = np.array([-pos[0], pos[1], pos[2]], float)
        for c in b.get("cubes", []):
            for fn, pts in cube_faces(c).items():
                uv = c["uv"][fn]["uv"]; col = tex[int(uv[1]), int(uv[0])]
                if col[3] < 10: continue
                q = [P + T + R @ (sc * (to_int(p) - P)) for p in pts]
                out.append((np.array([place(x, view, arm_tp_deg) for x in q]), col[:3], fn))
    return out


R_FP = euler_zyx(-95, 45, 115)
FP_ARM_T = np.array([-13.5, -10, 12.0])            # rightarm position [13.5,-10,12] (x مقلوب)
FP_ITEM_T = np.array([0, 0, -1.0])                 # rightitem position [0, 22-15-7, -1] (empty_hand)
FP_EYE = np.array([0, 26.0, 0])                    # العين: 1.62 بلوكة؛ الكاميرا تباوع +z لأن الراس ملفوف 180 بالمنظور الأول


def place(m_int, view, arm_tp_deg=18.0):
    """نقطة الموديل (داخلي، بعد حركة المسك) → المشهد. نقطة الموديل (0,24,0) = pivot اليد (-6,15,1)"""
    q = m_int - np.array([0, 24, 0.0]) + np.array([6, 15, 1.0])
    S = np.array([5, 22, 0.0])
    if view == "fp":
        q = q + FP_ITEM_T
        return S + FP_ARM_T + R_FP @ (q - S)
    return S + euler_zyx(arm_tp_deg, 0, 0) @ (q - S)


def player_polys(view, arm_tp_deg=18.0):
    """جسم اللاعب (داخلي، مثل Blockbench): بالثالث كامل، بالأول الذراع اليمين بس"""
    boxes = []
    if view == "tp":
        boxes = [([-4, 24, -4], [8, 8, 8], (196, 150, 118), None), ([-4, 12, -2], [8, 12, 4], (40, 150, 160), None),
                 ([-8, 12, -2], [4, 12, 4], (196, 150, 118), "left"), ([-3.9, 0, -2], [4, 12, 4], (60, 60, 150), None),
                 ([-0.1, 0, -2], [4, 12, 4], (60, 60, 150), None), ([4, 12, -2], [4, 12, 4], (196, 150, 118), "right")]
    else:
        boxes = [([4, 12, -2], [4, 12, 4], (196, 150, 118), "rightfp")]
    out = []
    for o, s, col, kind in boxes:
        o = np.array(o, float); s = np.array(s, float)
        x0, y0, z0 = o; x1, y1, z1 = o + s
        F = {"north": [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], "south": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
             "east": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], "west": [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)],
             "up": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], "down": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]}
        for fn, pts in F.items():
            q = []
            for p in pts:
                p = np.array(p, float)
                if kind == "right":
                    p = np.array([5, 22, 0.0]) + euler_zyx(arm_tp_deg, 0, 0) @ (p - np.array([5, 22, 0.0]))
                elif kind == "rightfp":
                    S = np.array([5, 22, 0.0]); p = S + FP_ARM_T + R_FP @ (p - S)
                q.append(p)
            out.append((np.array(q), np.array(col), fn))
    return out


def render(polys, eye, target, size=360, fov=57.3, title="", flip=True, aspect=1.0):
    """كاميرا three.js: fov عمودي، والشاشة يمين = cross(fwd, up)"""
    eye = np.array(eye, float); fwd = np.array(target, float) - eye; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    W = int(size * aspect)
    img = Image.new("RGB", (W, size), (132, 170, 214)); d = ImageDraw.Draw(img)
    f = size / 2 / math.tan(math.radians(fov / 2))
    shade = {"north": .86, "south": .86, "east": .72, "west": .72, "up": 1.0, "down": .55}
    pl = []
    for pts, col, fn in polys:
        c = pts - eye; z = c @ fwd
        if np.any(z < 0.3): continue
        proj = [(W / 2 + f * (p @ right) / (p @ fwd), size / 2 - f * (p @ up) / (p @ fwd)) for p in c]
        pl.append((float(np.mean(z)), proj, tuple(int(min(255, v * shade[fn])) for v in col)))
    for _, pr, col in sorted(pl, key=lambda x: -x[0]):
        d.polygon(pr, fill=col)
    d.text((5, 4), title, fill=(0, 0, 0))
    return img


def views(ident, size=300, anims=None):
    """منظور أول بكاميرا Blockbench (16:9)، وثلاث زوايا للثالث. ملاحظة: قدام اللاعب = -z، ويمينه = x داخلي موجب"""
    fp = render(player_polys("fp") + weapon_polys(ident, "fp", anims), FP_EYE, FP_EYE + np.array([0, 0, 10.0]), size, 70, f"{ident}  FP (in-game camera)", aspect=16 / 9)
    tp = player_polys("tp") + weapon_polys(ident, "tp", anims)
    a = render(tp, [34, 24, -40], [0, 14, 0], size, 50, "TP front-right")
    b = render(tp, [48, 18, -4], [0, 14, -2], size, 50, "TP right side")
    c = render(tp, [-26, 34, 40], [0, 14, 0], size, 50, "TP back-left")
    ims = (fp, a, b, c)
    im = Image.new("RGB", (sum(x.size[0] for x in ims), size)); xx = 0
    for x in ims: im.paste(x, (xx, 0)); xx += x.size[0]
    return im


if __name__ == "__main__":
    out = sys.argv[1]
    names = sys.argv[2].split(",") if len(sys.argv) > 2 else ["dark_katana", "dawn_dagger", "ember_cleaver", "shadow_blade", "shadow_claws", "stone_maul", "sunset_spear", "silver_oath"]
    ims = [views(n) for n in names]
    sheet = Image.new("RGB", (ims[0].size[0], sum(i.size[1] for i in ims)))
    y = 0
    for i in ims: sheet.paste(i, (0, y)); y += i.size[1]
    sheet.save(out); print(out)


def generic_polys(geo_bones, anim_bones, view, col=(200, 200, 200), arm_tp_deg=18.0):
    """أي موديل مربوط (مثلاً ترايدنت/منظار/درع موجانغ) بلون واحد، للتحقق من المحاكي"""
    out = []
    for b in geo_bones:
        a = anim_bones.get(b["name"], {})
        rot = a.get("rotation", [0, 0, 0]); pos = a.get("position", [0, 0, 0]); sc = a.get("scale", 1)
        sc = np.array(sc if isinstance(sc, list) else [sc] * 3, float)
        R = bed_rot([rot[i] + (b.get("rotation") or [0, 0, 0])[i] for i in range(3)])
        P = to_int(b["pivot"]); T = np.array([-pos[0], pos[1], pos[2]], float)
        for k, c in enumerate(b.get("cubes", [])):
            cc = np.array(col) * (0.6 + 0.4 * (k % 3) / 2)
            for fn, pts in cube_faces(c).items():
                q = [P + T + R @ (sc * (to_int(p) - P)) for p in pts]
                out.append((np.array([place(x, view, arm_tp_deg) for x in q]), cc, fn))
    return out
