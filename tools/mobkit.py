"""أدوات بناء الوحوش: عظام + مكعبات + رسم تكستشر بتظليل وتفاصيل."""
import json, math, os
import numpy as np
from PIL import Image
from render import face_rects


def mul(c, k):
    return tuple(int(max(0, min(255, v * k))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Sheet:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = np.zeros((h, w, 4), dtype=np.uint8)
        self.x = self.y = self.rowh = 0

    def alloc(self, w, h, d):
        bw, bh = int(math.ceil(2 * (d + w))), int(math.ceil(d + h))
        if self.x + bw > self.w:
            self.x = 0; self.y += self.rowh; self.rowh = 0
        assert self.y + bh <= self.h, f"الصفحة ممتلئة {self.w}x{self.h}"
        pos = (self.x, self.y)
        self.x += bw; self.rowh = max(self.rowh, bh)
        return pos


class Mob:
    def __init__(self, ident, W, H, seed=1):
        self.ident = ident
        self.sheet = Sheet(W, H)
        self.bones = {}
        self.rng = np.random.default_rng(seed)
        self.uvcache = {}

    def bone(self, name, pivot, parent=None, rot=None):
        b = {"name": name, "pivot": list(pivot)}
        if parent: b["parent"] = parent
        if rot: b["rotation"] = list(rot)
        self.bones[name] = b
        return b

    def cube(self, bone, origin, size, base, key=None, detail=None, rot=None, pivot=None, inflate=0.0,
             grad=0.16, ao=0.14, noise=5, faceK=None):
        w, h, d = size
        if key and key in self.uvcache:
            pos = self.uvcache[key]
        else:
            pos = self.sheet.alloc(w, h, d)
            self._paint(pos, size, base, detail, grad, ao, noise, faceK)
            if key: self.uvcache[key] = pos
        c = {"origin": list(origin), "size": list(size), "uv": [pos[0], pos[1]]}
        if inflate: c["inflate"] = inflate
        if rot:
            c["rotation"] = list(rot); c["pivot"] = list(pivot if pivot else origin)
        self.bones[bone].setdefault("cubes", []).append(c)

    def _paint(self, pos, size, base, detail, grad, ao, noise, faceK):
        w, h, d = size
        rects = face_rects(pos[0], pos[1], w, h, d)
        K = {"up": 1.12, "down": 0.62, "north": 1.0, "south": 0.9, "east": 0.84, "west": 0.84}
        if faceK: K.update(faceK)
        regs = {}
        for f, (x0, y0, rw, rh) in rects.items():
            x0, y0, rw, rh = int(x0), int(y0), int(math.ceil(rw)), int(math.ceil(rh))
            regs[f] = (x0, y0, rw, rh)
            for yy in range(rh):
                for xx in range(rw):
                    t = yy / max(1, rh - 1)
                    k = K[f] * (1 + grad * (0.5 - t))
                    e = min(xx, rw - 1 - xx, yy, rh - 1 - yy)
                    if e == 0: k *= (1 - ao)
                    n = self.rng.integers(-noise, noise + 1)
                    col = mul(base, k)
                    col = tuple(max(0, min(255, c + n)) for c in col)
                    self.sheet.img[y0 + yy, x0 + xx] = (*col, 255)
        if detail:
            detail(self.sheet.img, regs)

    def geo(self):
        return {
            "format_version": "1.12.0",
            "minecraft:geometry": [{
                "description": {"identifier": self.ident, "texture_width": self.sheet.w, "texture_height": self.sheet.h,
                                "visible_bounds_width": 4, "visible_bounds_height": 4, "visible_bounds_offset": [0, 1.2, 0]},
                "bones": list(self.bones.values()),
            }],
        }

    def save(self, geo_path, tex_path):
        os.makedirs(os.path.dirname(geo_path), exist_ok=True)
        os.makedirs(os.path.dirname(tex_path), exist_ok=True)
        json.dump(self.geo(), open(geo_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        Image.fromarray(self.sheet.img).save(tex_path)


# ───────── مساعدات رسم ─────────
def put(img, x, y, col):
    if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
        img[y, x] = (*col[:3], 255)


def glow_px(img, x, y, col, halo=0.45, r=1):
    """نقطة مضيئة مع هالة"""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx == 0 and dy == 0: continue
            cur = img[y + dy, x + dx][:3]
            put(img, x + dx, y + dy, mix(tuple(int(v) for v in cur), col, halo))
    put(img, x, y, col)


def cracks(img, reg, rng, col, n=2, length=None, halo=True):
    x0, y0, rw, rh = reg
    for _ in range(n):
        x = x0 + int(rng.integers(1, max(2, rw - 1)))
        y = y0 + int(rng.integers(0, max(1, rh // 3)))
        for _s in range(length or rh):
            if y >= y0 + rh: break
            if halo:
                for dx in (-1, 1):
                    xx = x + dx
                    if x0 <= xx < x0 + rw:
                        cur = tuple(int(v) for v in img[y, xx][:3])
                        put(img, xx, y, mix(cur, col, 0.3))
            put(img, x, y, col)
            y += 1
            x += int(rng.choice([-1, 0, 0, 1]))
            x = max(x0, min(x0 + rw - 1, x))


def rivet(img, x, y, col=(190, 188, 196)):
    put(img, x, y, col)
    put(img, x + 1, y, mul(col, 0.6)); put(img, x, y + 1, mul(col, 0.6))


def patches(img, reg, rng, col, density=0.18, seed_scale=3):
    """بقع (صدأ/عفن) عشوائية متجمعة"""
    x0, y0, rw, rh = reg
    for _ in range(max(1, int(rw * rh * density / 6))):
        cx = x0 + int(rng.integers(0, rw)); cy = y0 + int(rng.integers(0, rh))
        r = int(rng.integers(1, seed_scale + 1))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r + rng.integers(0, 2):
                    x, y = cx + dx, cy + dy
                    if x0 <= x < x0 + rw and y0 <= y < y0 + rh:
                        cur = tuple(int(v) for v in img[y, x][:3])
                        put(img, x, y, mix(cur, col, float(rng.uniform(0.35, 0.8))))
