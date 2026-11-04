"""معاين موديلات Bedrock (geo.json + texture + animation) بمحاكي برمجي بسيط.
الاتفاقيات (مأخوذة من ملفات ماينكرافت الأصلية): الأمام = -z، دوران x السالب يرفع الذراع للأمام."""
import json, math, re
import numpy as np
from PIL import Image, ImageDraw


# ───────────── تقييم Molang مبسّط ─────────────
class _NS:
    def __init__(self, d): self.__dict__.update(d)
    def __getattr__(self, k): return 0.0


def _rad(d): return math.radians(d)


class _Math:
    sin = staticmethod(lambda d: math.sin(_rad(d)))
    cos = staticmethod(lambda d: math.cos(_rad(d)))
    abs = staticmethod(abs)
    clamp = staticmethod(lambda v, a, b: max(a, min(b, v)))
    lerp = staticmethod(lambda a, b, t: a + (b - a) * t)
    mod = staticmethod(lambda a, b: a % b)
    pow = staticmethod(lambda a, b: a ** b)
    sqrt = staticmethod(math.sqrt)
    min = staticmethod(min)
    max = staticmethod(max)
    pi = math.pi


def _ternary(e):
    while "?" in e:
        q = e.index("?")
        d = 0; a = q
        while a > 0:
            a -= 1
            if e[a] == ")": d += 1
            elif e[a] == "(":
                if d == 0: break
                d -= 1
        else:
            a = -1
        d = 0; c = None; z = len(e)
        for i in range(q + 1, len(e)):
            ch = e[i]
            if ch == "(": d += 1
            elif ch == ")":
                if d == 0: z = i; break
                d -= 1
            elif ch == ":" and d == 0 and c is None: c = i
        cond, yes, no = e[a + 1:q], e[q + 1:c], e[c + 1:z]
        e = e[:a + 1] + f"(({yes}) if ({cond}) else ({no}))" + e[z:]
    return e


def meval(expr, env):
    if isinstance(expr, (int, float)):
        return float(expr)
    e = expr.replace("query.", "q.").replace("variable.", "v.")
    e = re.sub(r"\bthis\b", "0.0", e)
    e = _ternary(e)
    ns = {"math": _Math, "q": _NS(env.get("q", {})), "v": _NS(env.get("v", {}))}
    try:
        return float(eval(e, {"__builtins__": {}}, ns))
    except Exception:
        return 0.0


def vec(v, env):
    return [meval(c, env) for c in v]


def sample_channel(ch, t, env):
    """ch: قائمة 3 تعابير، أو dict زمن->قيمة"""
    if isinstance(ch, dict):
        ks = sorted((float(k), v) for k, v in ch.items())
        vals = [(k, vec(v["post"] if isinstance(v, dict) and "post" in v else v, env)) for k, v in ks]
        if t <= vals[0][0]: return vals[0][1]
        if t >= vals[-1][0]: return vals[-1][1]
        for (t0, a), (t1, b) in zip(vals, vals[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0 or 1)
                return [x + (y - x) * k for x, y in zip(a, b)]
    return vec(ch, env)


def pose_from_anims(anims, t, env, scale_default=1.0):
    """يجمع قنوات عدة أنيميشن (rotation/position) لكل عظمة."""
    pose = {}
    for a in anims:
        for bone, ch in a.get("bones", {}).items():
            p = pose.setdefault(bone, {"rot": [0, 0, 0], "pos": [0, 0, 0]})
            if "rotation" in ch:
                p["rot"] = [x + y for x, y in zip(p["rot"], sample_channel(ch["rotation"], t, env))]
            if "position" in ch:
                p["pos"] = [x + y for x, y in zip(p["pos"], sample_channel(ch["position"], t, env))]
    return pose


# ───────────── رياضيات ─────────────
def rot_matrix(rx, ry, rz):
    # اتفاقية: x موجب يميل الأعلى نحو -z (للأمام)
    a, b, c = _rad(-rx), _rad(-ry), _rad(rz)
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


FACES = ["north", "south", "east", "west", "up", "down"]


def face_corners(x0, y0, z0, x1, y1, z1):
    return {
        "north": [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
        "south": [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
        "east": [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
        "west": [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
        "up": [(x1, y1, z1), (x0, y1, z1), (x0, y1, z0), (x1, y1, z0)],
        "down": [(x1, y0, z0), (x0, y0, z0), (x0, y0, z1), (x1, y0, z1)],
    }


def face_rects(u, v, w, h, d):
    return {
        "north": (u + d, v + d, w, h), "south": (u + 2 * d + w, v + d, w, h),
        "east": (u, v + d, d, h), "west": (u + d + w, v + d, d, h),
        "up": (u + d, v, w, d), "down": (u + d + w, v, w, d),
    }


class Model:
    def __init__(self, geo_path, tex_path):
        g = json.load(open(geo_path, encoding="utf-8"))["minecraft:geometry"][0]
        self.bones = {b["name"]: b for b in g["bones"]}
        self.tex = np.array(Image.open(tex_path).convert("RGBA"))
        self.tw, self.th = g["description"]["texture_width"], g["description"]["texture_height"]

    def chain(self, name):
        out = []
        while name:
            b = self.bones[name]
            out.append(b)
            name = b.get("parent")
        return out  # من الطفل للأب

    def world_cubes(self, pose, game=False):
        """يرجع قائمة وجوه: (corners3d[4], uvrect, normal)
        game=True: نفس اللعبة (مثل Blockbench وtools/fit/hand_sim.py): x مقلوب (x_int = -x) للمكعبات والمحاور والإزاحة،
        الدوران نفسه Euler(-rx, -ry, rz)، والإزاحة (-tx, ty, tz). وجه east يصير بـ +x الداخلي (يمين الكيان).
        بدونها (القديم) الموديل يطلع معكوس يمين/يسار ودوران Y وZ يطلع بالاتجاه المعاكس."""
        faces = []
        sx = -1.0 if game else 1.0
        for name, b in self.bones.items():
            for c in b.get("cubes", []):
                ox, oy, oz = c["origin"]
                w, h, d = c["size"]
                inf = c.get("inflate", 0)
                x0, y0, z0 = ox - inf, oy - inf, oz - inf
                x1, y1, z1 = ox + w + inf, oy + h + inf, oz + d + inf
                if game:
                    x0, x1 = -x1, -x0
                fc = face_corners(x0, y0, z0, x1, y1, z1)
                if isinstance(c["uv"], dict):  # UV لكل وجه (مكعبات الإضافات)
                    rects = {f: (c["uv"][f]["uv"][0], c["uv"][f]["uv"][1], c["uv"][f]["uv_size"][0], c["uv"][f]["uv_size"][1]) for f in c["uv"]}
                else:
                    rects = face_rects(c["uv"][0], c["uv"][1], w, h, d)
                for fname in FACES:
                    if fname not in rects:
                        continue
                    pts = np.array(fc[fname], dtype=float)
                    # دوران المكعب نفسه
                    if "rotation" in c:
                        pv = np.array(c.get("pivot", [0, 0, 0]), dtype=float) * np.array([sx, 1, 1])
                        R = rot_matrix(*c["rotation"])
                        pts = (pts - pv) @ R.T + pv
                    # سلسلة العظام: الطفل ثم الأب
                    for bb in self.chain(name):
                        p = pose.get(bb["name"], {"rot": [0, 0, 0], "pos": [0, 0, 0]})
                        rot = [a + b2 for a, b2 in zip(bb.get("rotation", [0, 0, 0]), p["rot"])]
                        pv = np.array(bb.get("pivot", [0, 0, 0]), dtype=float) * np.array([sx, 1, 1])
                        R = rot_matrix(*rot)
                        if "scale" in p:                                   # تحجيم العظمة حول محورها (مثل اللعبة: قبل الدوران)
                            pts = (pts - pv) * np.array(p["scale"], dtype=float) + pv
                        pts = (pts - pv) @ R.T + pv
                        if game:
                            pts = pts + np.array([-p["pos"][0], p["pos"][1], p["pos"][2]], dtype=float)
                        else:
                            pts = pts + np.array([p["pos"][0], p["pos"][1], -p["pos"][2]])
                    faces.append((pts, rects[fname], c.get("mirror", False)))
        return faces


def render(model, pose, yaw=0, pitch=12, size=420, center=None, dist=None, bg=(46, 48, 56), scale=None, game=False):
    faces = model.world_cubes(pose, game=game)
    allp = np.concatenate([f[0] for f in faces]) / 16.0
    if center is None:
        center = (allp.min(0) + allp.max(0)) / 2
    ext = (allp.max(0) - allp.min(0)).max()
    if dist is None:
        dist = ext * 2.6 + 1.0
    yaw_r, pit_r = _rad(yaw), _rad(pitch)
    cam = np.array(center) + dist * np.array([math.sin(yaw_r) * math.cos(pit_r), math.sin(pit_r), -math.cos(yaw_r) * math.cos(pit_r)])
    f = np.array(center) - cam
    f /= np.linalg.norm(f)
    right = np.cross(f, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, f)
    focal = size * 0.5 / math.tan(_rad(18)) * (1.0 if scale is None else scale)
    img = np.zeros((size, size, 3), dtype=np.float32); img[:] = bg
    zbuf = np.full((size, size), 1e9, dtype=np.float32)
    light = np.array([0.4, 0.8, -0.5]); light /= np.linalg.norm(light)
    for pts, (ru, rv, rw, rh), _m in faces:
        p = pts / 16.0
        n = -np.cross(p[1] - p[0], p[3] - p[0])
        ln = np.linalg.norm(n)
        if ln < 1e-9: continue
        n /= ln
        # الوجه يواجه الكاميرا؟ (ترتيب TL,TR,BR,BL → الناتج الخارجي)
        if np.dot(n, p[0] - cam) > 0:  # الخلفي
            continue
        shade = 0.55 + 0.45 * max(0.0, float(np.dot(n, light)))
        rel = p - cam
        dep = rel @ f
        if (dep <= 0.05).any(): continue
        sx = (rel @ right) / dep * focal + size / 2
        sy = -(rel @ up) / dep * focal + size / 2
        uv = np.array([(ru, rv), (ru + rw, rv), (ru + rw, rv + rh), (ru, rv + rh)], dtype=float)
        for tri in ((0, 1, 2), (0, 2, 3)):
            a, b, c = tri
            xs, ys = sx[[a, b, c]], sy[[a, b, c]]
            x0, x1 = int(max(0, math.floor(xs.min()))), int(min(size - 1, math.ceil(xs.max())))
            y0, y1 = int(max(0, math.floor(ys.min()))), int(min(size - 1, math.ceil(ys.max())))
            if x0 > x1 or y0 > y1: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-9: continue
            l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
            l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
            l2 = 1 - l0 - l1
            m = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
            if not m.any(): continue
            iw = np.stack([l0 / dep[a], l1 / dep[b], l2 / dep[c]])
            s = iw.sum(0)
            pl = iw / np.where(s == 0, 1, s)
            u = pl[0] * uv[a, 0] + pl[1] * uv[b, 0] + pl[2] * uv[c, 0]
            v = pl[0] * uv[a, 1] + pl[1] * uv[b, 1] + pl[2] * uv[c, 1]
            z = 1.0 / np.where(s == 0, 1, s)
            tx = np.clip((u - 1e-3).astype(int), 0, model.tw - 1)
            ty = np.clip((v - 1e-3).astype(int), 0, model.th - 1)
            tex = model.tex[ty, tx]
            front = m & (z < zbuf[y0:y1 + 1, x0:x1 + 1])
            ok = front & (tex[..., 3] > 128)
            semi = front & (tex[..., 3] > 8) & (tex[..., 3] <= 128)          # مادة alphablend (تمويه شبه شفاف): تنمزج بدون كتابة عمق
            if not ok.any() and not semi.any(): continue
            col = tex[..., :3].astype(np.float32) * shade
            region = img[y0:y1 + 1, x0:x1 + 1]
            if semi.any():
                al = tex[..., 3:4].astype(np.float32) / 255.0
                region[semi] = (col * al + region * (1 - al))[semi]
            if not ok.any(): continue
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]; sub[ok] = z[ok]
            region[ok] = col[ok]
    # أرضية خفيفة
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def contact_sheet(model, poses, views=((0, 12), (45, 12), (90, 12), (180, 12)), size=300, label=None, game=False):
    rows = len(poses)
    W = size * len(views)
    H = size * rows
    sheet = Image.new("RGB", (W, H), (46, 48, 56))
    d = ImageDraw.Draw(sheet)
    # نفس الإطار لكل الصور حتى تقارن الحركة
    base = model.world_cubes({}, game=game)
    allp = np.concatenate([f[0] for f in base]) / 16.0
    center = (allp.min(0) + allp.max(0)) / 2
    ext = (allp.max(0) - allp.min(0)).max()
    for r, (name, pose) in enumerate(poses):
        for c, (yaw, pit) in enumerate(views):
            im = render(model, pose, yaw, pit, size, center=center, dist=ext * 2.9 + 1.0, game=game)
            sheet.paste(im, (c * size, r * size))
        d.text((6, r * size + 4), name, fill=(255, 255, 255))
    return sheet
