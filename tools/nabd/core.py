"""Nabd pack - procedural pixel-art toolkit.

Everything here paints 16x16 block textures from scratch (noise, cells,
strokes).  Each texture is described by a height field plus a colour ramp, so
the colour map, the normal map and the MERS map always agree with each other.
"""
import colorsys
import hashlib
import json
import os

import numpy as np
from PIL import Image

N = 16
HERE = os.path.dirname(os.path.abspath(__file__))
STATS = json.load(open(os.path.join(HERE, "vanilla_stats.json")))


# --------------------------------------------------------------------------- rng
def seed_of(name):
    return int(hashlib.sha1(("nabd:" + name).encode()).hexdigest()[:8], 16)


def rng_of(name):
    return np.random.default_rng(seed_of(name))


# ------------------------------------------------------------------------- noise
def _smooth(t):
    return t * t * (3 - 2 * t)


def value_noise(r, px, py=None, w=N, h=N):
    """Tileable value noise with `px` x `py` lattice cells across the tile."""
    py = py or px
    g = r.random((py, px))
    ys = np.arange(h) * py / h
    xs = np.arange(w) * px / w
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = _smooth(ys - y0)[:, None]
    fx = _smooth(xs - x0)[None, :]
    y1 = (y0 + 1) % py
    x1 = (x0 + 1) % px
    a = g[y0][:, x0]
    b = g[y0][:, x1]
    c = g[y1][:, x0]
    d = g[y1][:, x1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def norm01(a):
    lo, hi = float(a.min()), float(a.max())
    if hi - lo < 1e-9:
        return np.full_like(a, 0.5, dtype=float)
    return (a - lo) / (hi - lo)


def fbm(r, layers=((2, 1.0), (4, 0.6), (8, 0.35)), w=N, h=N, sx=1, sy=1):
    """Sum of tileable noise octaves, normalised to 0..1.
    sx / sy > 1 stretch the pattern along that axis (fewer cells)."""
    out = np.zeros((h, w))
    for p, wt in layers:
        px = max(1, int(round(p / sx)))
        py = max(1, int(round(p / sy)))
        out += wt * value_noise(r, px, py, w, h)
    return norm01(out)


def white(r, w=N, h=N):
    return r.random((h, w))


def voronoi(r, count, w=N, h=N, min_dist=None, tries=4000):
    """Toroidal Voronoi cells. Returns (ids, f1, f2, points)."""
    if min_dist is None:
        min_dist = 0.72 * np.sqrt(w * h / count)
    pts = []
    t = 0
    while len(pts) < count and t < tries:
        t += 1
        p = np.array([r.random() * w, r.random() * h])
        ok = True
        for q in pts:
            d = np.abs(p - q)
            d = np.minimum(d, np.array([w, h]) - d)
            if np.hypot(*d) < min_dist:
                ok = False
                break
        if ok:
            pts.append(p)
        elif t % 400 == 0:
            min_dist *= 0.9
    pts = np.array(pts)
    yy, xx = np.mgrid[0:h, 0:w]
    dx = np.abs(xx[..., None] + 0.5 - pts[:, 0])
    dy = np.abs(yy[..., None] + 0.5 - pts[:, 1])
    dx = np.minimum(dx, w - dx)
    dy = np.minimum(dy, h - dy)
    d = np.hypot(dx, dy)
    order = np.argsort(d, axis=-1)
    ids = order[..., 0]
    ds = np.sort(d, axis=-1)
    f1 = ds[..., 0]
    f2 = ds[..., 1] if pts.shape[0] > 1 else ds[..., 0] + 9
    return ids, f1, f2, pts


def cell_edges(ids):
    """True where a pixel's right or lower neighbour belongs to another cell
    (gives 1px seams that sit on the shadow side of every cell)."""
    return (ids != np.roll(ids, -1, 1)) | (ids != np.roll(ids, -1, 0))


def emboss(hgt, amount=1.0):
    """Top-left light: positive where the surface rises towards the light."""
    return amount * (hgt - np.roll(np.roll(hgt, 1, 0), 1, 1))


BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0


def bayer(w=N, h=N):
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


# ------------------------------------------------------------------------ colour
def _clip8(c):
    return tuple(int(max(0, min(255, round(v)))) for v in c)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def mix(a, b, t):
    return _clip8(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def shift(c, dv=0.0, ds=0.0, dh=0.0):
    h, s, v = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
    h = (h + dh) % 1.0
    s = min(1, max(0, s + ds))
    v = min(1, max(0, v + dv))
    return _clip8(tuple(x * 255 for x in colorsys.hsv_to_rgb(h, s, v)))


def _toward(h, target, amt):
    d = ((target - h + 0.5) % 1.0) - 0.5
    return (h + d * amt) % 1.0


def make_ramp(base, steps=5, contrast=0.30, warm=0.10, grey=False, sat=1.5, lift=0.05):
    """Our house ramp (v3, "cheerful"): calm value steps, bright punchy colour.
    `base` is the middle tone.  Muted colours are enriched the most, the whole
    material is lifted a little, shadows stay colourful instead of going grey.
    With grey=True nothing but value changes (biome-tinted textures)."""
    h, s, v = colorsys.rgb_to_hsv(base[0] / 255, base[1] / 255, base[2] / 255)
    c = contrast * 0.6
    coloured = (not grey) and s >= 0.04
    if coloured:
        s = min(1.0, s * (1 + (sat - 1) * (1 - 0.8 * s)))
        v = min(1.0, v * (1 + lift) + lift * 0.4)
    out = []
    for i in range(steps):
        t = (i / (steps - 1)) * 2 - 1 if steps > 1 else 0.0  # -1 .. 1
        vv = v * (1 + c * t) if t < 0 else v + min(1 - v, v * c * 0.9) * t
        if not coloured:
            out.append(_clip8(tuple(x * 255 for x in colorsys.hsv_to_rgb(h, s, vv))))
            continue
        if t < 0:
            hh = _toward(h, 0.68, warm * 0.18 * -t)
            ss = min(1.0, s * (1 + 0.16 * -t))
        else:
            hh = _toward(h, 0.13, warm * 0.18 * t)
            ss = s * (1 - 0.12 * t)
        out.append(_clip8(tuple(x * 255 for x in colorsys.hsv_to_rgb(hh, ss, vv))))
    return out


def stat(name):
    return STATS[name]


def vbase(name):
    """Median tone of the vanilla texture (colour reference only)."""
    return tuple(STATS[name]["ramp"][2])


def vcontrast(name, floor=0.16, ceil=0.42):
    rp = STATS[name]["ramp"]
    lo, hi, mid = lum(rp[0]), lum(rp[4]), max(1.0, lum(rp[2]))
    return float(min(ceil, max(floor, (hi - lo) / (2 * mid) * 1.15)))


def vramp(name, steps=5, grey=False, contrast=None, warm=0.10):
    return make_ramp(vbase(name), steps, contrast if contrast is not None else vcontrast(name), warm, grey)


def paint(val, ramp, dither=0.0):
    """Map a 0..1 field onto a colour ramp (hard pixel-art steps).
    `dither` is accepted for compatibility but ignored: the v2 style uses
    clean clusters, never checkerboard dithering."""
    n = len(ramp)
    idx = np.clip(np.floor(np.clip(val, 0, 0.9999) * n), 0, n - 1).astype(int)
    return np.array(ramp, dtype=np.uint8)[idx]


def paint_idx(idx, ramp):
    """Paint from an integer tone map (0 = darkest)."""
    return np.array(ramp, dtype=np.uint8)[np.clip(idx, 0, len(ramp) - 1)]


def dashes(r, idx, hgt, count, tone, length=(3, 7), thick=0.35, vertical=False, lift=0.0, wobble=0.25):
    """Soft lens-shaped strokes of a single tone: the basic mark of the v2
    style.  Tile-wrapped.  `lift` raises (+) or sinks (-) the height map."""
    h, w = idx.shape
    for _ in range(count):
        x, y = int(r.integers(w)), int(r.integers(h))
        ln = int(r.integers(length[0], length[1] + 1))
        fat = r.random() < thick
        for i in range(ln):
            if r.random() < wobble and 0 < i < ln - 1:
                if vertical:
                    x += int(r.choice([-1, 1]))
                else:
                    y += int(r.choice([-1, 1]))
            px, py = ((x, y + i) if vertical else (x + i, y))
            idx[py % h, px % w] = tone
            hgt[py % h, px % w] += lift
            if fat and 0 < i < ln - 1:
                qx, qy = ((px + 1, py) if vertical else (px, py + 1))
                idx[qy % h, qx % w] = tone
                hgt[qy % h, qx % w] += lift


# ----------------------------------------------------------------------- texture
class Tex:
    """rgb: HxWx3 uint8, alpha: HxW uint8, height: HxW float 0..1,
    metal / emis / rough / sss: scalars or HxW arrays in 0..255."""

    def __init__(self, rgb, height=None, alpha=None, metal=0, emis=0, rough=200, sss=0, bump=1.0):
        self.rgb = np.asarray(rgb, dtype=np.uint8)
        h, w = self.rgb.shape[:2]
        self.h, self.w = h, w
        self.height = np.full((h, w), 0.5) if height is None else np.asarray(height, dtype=float)
        self.alpha = np.full((h, w), 255, np.uint8) if alpha is None else np.asarray(alpha, np.uint8)
        self.metal, self.emis, self.rough, self.sss = metal, emis, rough, sss
        self.bump = bump

    def _plane(self, v):
        if np.isscalar(v):
            return np.full((self.h, self.w), int(v), np.uint8)
        return np.clip(np.asarray(v), 0, 255).astype(np.uint8)

    def color_image(self):
        return Image.fromarray(np.dstack([self.rgb, self.alpha]), "RGBA")

    def mers_image(self):
        return Image.fromarray(np.dstack([self._plane(self.metal), self._plane(self.emis),
                                          self._plane(self.rough), self._plane(self.sss)]), "RGBA")

    def normal_image(self, frame_h=None):
        """Tangent-space normal map (DirectX / Y- convention), tile-wrapped.
        frame_h: wrap vertically per animation frame instead of whole strip."""
        hgt = self.height
        fh = frame_h or self.h
        out = np.zeros((self.h, self.w, 3), np.uint8)
        for y0 in range(0, self.h, fh):
            hh = hgt[y0:y0 + fh]
            dx = (np.roll(hh, -1, 1) - np.roll(hh, 1, 1)) * 0.5
            dy = (np.roll(hh, -1, 0) - np.roll(hh, 1, 0)) * 0.5
            k = 2.6 * self.bump
            nx, ny, nz = -dx * k, dy * k, np.ones_like(hh)
            ln = np.sqrt(nx * nx + ny * ny + nz * nz)
            nx, ny, nz = nx / ln, ny / ln, nz / ln
            out[y0:y0 + fh, :, 0] = np.clip((nx * 0.5 + 0.5) * 255, 0, 255)
            out[y0:y0 + fh, :, 1] = np.clip((-ny * 0.5 + 0.5) * 255, 0, 255)
            out[y0:y0 + fh, :, 2] = np.clip((nz * 0.5 + 0.5) * 255, 0, 255)
        return Image.fromarray(out, "RGB")

    def copy(self):
        t = Tex(self.rgb.copy(), self.height.copy(), self.alpha.copy(), bump=self.bump)
        for k in ("metal", "emis", "rough", "sss"):
            v = getattr(self, k)
            setattr(t, k, v if np.isscalar(v) else np.array(v))
        return t


def plane(v, h=N, w=N):
    return np.full((h, w), float(v)) if np.isscalar(v) else np.asarray(v, dtype=float)


def stack_frames(frames):
    """Vertical animation strip from equally sized Tex frames."""
    t = Tex(np.vstack([f.rgb for f in frames]), np.vstack([f.height for f in frames]),
            np.vstack([f.alpha for f in frames]), bump=frames[0].bump)
    for k in ("metal", "emis", "rough", "sss"):
        setattr(t, k, np.vstack([plane(getattr(f, k), f.h, f.w) for f in frames]))
    return t
