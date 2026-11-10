"""Many-cube sculpting: organic shapes built from lots of small, rotated, overlapping cubes (the Blockbench
"high-cube" look) — ellipsoid blobs from stacked crossed slabs, tapered limbs through smooth splines with
joint knuckles and colour bands, flat plates and feathers. Used for the giant summons and body constructs."""
import math

import models as M
from models import dark, layered, light, _put


# ------------------------------------------------------------------ vector helpers
def add(a, b): return [a[i] + b[i] for i in range(3)]
def sub(a, b): return [a[i] - b[i] for i in range(3)]
def mul(a, k): return [a[i] * k for i in range(3)]
def length(a): return math.sqrt(sum(x * x for x in a))
def norm(a):
    l = length(a) or 1.0
    return [x / l for x in a]


def rot_for(d):
    """Rotation that turns a box's local +Y onto direction d (same convention as Model.strand)."""
    d = norm(d)
    ax = math.degrees(math.asin(max(-1.0, min(1.0, d[2]))))
    az = math.degrees(math.atan2(-d[0], d[1]))
    return [round(ax, 2), 0, round(az, 2)]


def spline(points, n=4):
    """Catmull-Rom curve through the control points, n samples per span."""
    if len(points) < 3:
        return [list(p) for p in points]
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append([0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                               (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(3)])
    out.append(list(points[-1]))
    return out


# ------------------------------------------------------------------ paints
def alpha(painter, a):
    """See-through version of a painter (chakra constructs)."""
    def p(face, img):
        painter(face, img)
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, al = px[x, y]
                if al:
                    px[x, y] = (r, g, b, min(al, a))
    return p


def rim(edge):
    def f(face, px, w, h, base):
        for y in range(h):
            for x in range(w):
                if x in (0, w - 1) or y in (0, h - 1):
                    _put(px, w, h, x, y, edge)
    return f


def speckle(col, mod=11):
    def f(face, px, w, h, base):
        for y in range(h):
            for x in range(w):
                if (x * 7 + y * 13) % mod == 0:
                    _put(px, w, h, x, y, col)
    return f


def stripes(col, every=4, axis="y"):
    def f(face, px, w, h, base):
        if face in ("up", "down"):
            return
        for y in range(h):
            for x in range(w):
                if (y if axis == "y" else x) % every == 0:
                    _put(px, w, h, x, y, col)
    return f


FACE_TONE = {"up": 3, "north": 2, "west": 3, "east": 1, "south": 1, "down": 0}


def smooth(base, details=()):
    """Sculpt material: one tone per face (lit from above-front), a faint dither, NO outline or bevel —
    so hundreds of small cubes melt into one smooth surface instead of reading as bricks."""
    t = M.tones(base)

    def p(face, img):
        w, h = img.size
        px = img.load()
        k = FACE_TONE[face]
        for y in range(h):
            for x in range(w):
                kk = k + (1 if (x * 5 + y * 3) % 23 == 0 else -1 if (x * 3 + y * 7) % 29 == 0 else 0)
                px[x, y] = t[max(0, min(4, kk))] + (255,)
        for f in details:
            f(face, px, w, h, base)
    return p


def chakra(col, a=200, edge=None):
    """A chakra-construct material: smooth, translucent, a slightly brighter top."""
    return alpha(smooth(col, [speckle(light(col, 0.25), 13)]), a)


def flesh(col, vein=None):
    return smooth(col, [speckle(dark(col, 0.85), 9)] + ([stripes(vein, 7, "x")] if vein else []))


# ------------------------------------------------------------------ shapes
def box_at(m, bone, center, size, paint, rot=None):
    """A box centred on `center`, optionally rotated about its own centre."""
    frm = [center[i] - size[i] / 2 for i in range(3)]
    m.box(bone, frm, size, paint, rot=rot, pivot=list(center) if rot else None)


def blob(m, bone, center, radii, paint, slices=6, axis="y", rot=None, cross=0.72):
    """Ellipsoid from stacked slabs; every slab is two crossed boxes, so the section is an octagon.
    `rot` turns the whole blob about its centre."""
    cx, cy, cz = center
    rx, ry, rz = radii
    along = {"x": 0, "y": 1, "z": 2}[axis]
    R = radii[along]
    for i in range(slices):
        a0 = -R + 2 * R * i / slices
        a1 = a0 + 2 * R / slices
        am = (a0 + a1) / 2
        k = math.sqrt(max(0.0, 1 - (am / R) ** 2))
        k = max(k, 0.35)
        dims = [radii[j] * k for j in range(3)]
        dims[along] = (a1 - a0) / 2 + 0.05
        others = [j for j in range(3) if j != along]
        for wide in others:  # two crossed slabs
            s = list(dims)
            narrow = [j for j in others if j != wide][0]
            s[narrow] *= cross
            frm = [center[j] - s[j] for j in range(3)]
            frm[along] = center[along] + a0
            size = [2 * s[j] for j in range(3)]
            size[along] = a1 - a0 + 0.1
            m.box(bone, frm, size, paint, rot=rot, pivot=list(center) if rot else None)


def tube(m, bone, points, radii, paints, knuckles=True, cross=0.72, flat=1.0):
    """A tapered limb through `points` (use spline() for curves). `radii` per point; `paints` is one painter
    or a list cycled per segment (colour bands, like an insect's segments). `flat` < 1 squashes the section."""
    if not isinstance(paints, (list, tuple)):
        paints = [paints]
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        d = sub(b, a)
        L = length(d)
        if L < 0.05:
            continue
        r = (radii[i] + radii[i + 1]) / 2
        rot = rot_for(d)
        p = paints[i % len(paints)]
        ext = r * 0.35
        start = sub(a, mul(norm(d), ext * 0.5))
        m.box(bone, [start[0] - r, start[1], start[2] - r * cross * flat], [2 * r, L + ext, 2 * r * cross * flat], p, rot=rot, pivot=start)
        m.box(bone, [start[0] - r * cross, start[1], start[2] - r * flat], [2 * r * cross, L + ext, 2 * r * flat], p, rot=rot, pivot=start)
        if knuckles and 0 < i:
            k = radii[i] * 1.12
            box_at(m, bone, a, [k * 1.6, k * 1.6, k * 1.6 * flat], p, rot=rot)


def curve_tube(m, bone, ctrl, r0, r1, paints, n=3, **kw):
    pts = spline(ctrl, n)
    radii = [r0 + (r1 - r0) * i / max(1, len(pts) - 1) for i in range(len(pts))]
    tube(m, bone, pts, radii, paints, **kw)
    return pts


def blade(m, bone, base, direction, length_, width, thick, paint, taper=True):
    """A flat blade / feather / plate grown from `base` along `direction`, tapering to a point."""
    d = norm(direction)
    rot = rot_for(d)
    segs = 3 if taper else 1
    p = list(base)
    for i in range(segs):
        w = width * (1 - i / (segs + 0.6)) if taper else width
        L = length_ / segs
        m.box(bone, [p[0] - w / 2, p[1], p[2] - thick / 2], [w, L + 0.2, thick], paint, rot=rot, pivot=list(p))
        p = add(p, mul(d, L))


def bones_from(pivots, parents):
    """Bone list from model-space pivots (export mirrors x)."""
    out = []
    for name, pv in pivots.items():
        b = {"name": name, "pivot": [-pv[0], pv[1], pv[2]]}
        if parents.get(name):
            b["parent"] = parents[name]
        out.append(b)
    return out
