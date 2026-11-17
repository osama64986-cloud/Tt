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


def vcross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def orient(d, spin=0.0, width=None):
    """Euler angles (model space = Blockbench/three.js, order ZYX) that put a box's local +Y along d,
    its local +X along `width` (if given) and then spin it `spin` degrees about its own axis."""
    Y = norm(d)
    if width is not None:
        X = sub(width, mul(Y, dot(width, Y)))
        if length(X) < 1e-4:
            width = None
        else:
            X = norm(X)
    if width is None:
        ref = [0, 0, 1] if abs(Y[2]) < 0.9 else [1, 0, 0]
        X = norm(vcross(Y, ref))
    Z = vcross(X, Y)
    if spin:
        c, s_ = math.cos(math.radians(spin)), math.sin(math.radians(spin))
        X, Z = add(mul(X, c), mul(Z, -s_)), add(mul(X, s_), mul(Z, c))
    m31, m32, m33 = X[2], Y[2], Z[2]
    m21, m11, m12, m22 = X[1], X[0], Y[0], Y[1]
    y = math.asin(max(-1.0, min(1.0, -m31)))
    if abs(m31) < 0.9999999:
        x, z = math.atan2(m32, m33), math.atan2(m21, m11)
    else:
        x, z = 0.0, math.atan2(-m12, m22)
    return [round(math.degrees(x), 3), round(math.degrees(y), 3), round(math.degrees(z), 3)]


def obox(m, bone, center, size, paint, d=(0, 1, 0), spin=0.0, width=None):
    """A box centred on `center`, its height along d (rotation about its own centre)."""
    frm = [center[i] - size[i] / 2 for i in range(3)]
    rot = orient(d, spin, width)
    if not any(abs(r) > 1e-3 for r in rot):
        m.box(bone, frm, size, paint)
    else:
        m.box(bone, frm, size, paint, rot=rot, pivot=list(center))


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
    if getattr(painter, "swatch", None):
        return swatch(painter.swatch[0], min(a, painter.swatch[1]))

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


def swatch(base, a=255):
    """Plain sculpt material: a flat tone per face. Cubes painted with it share a tiny colour tile on the texture
    (per-face UVs), so a model can use hundreds of them without the texture growing."""
    t = M.tones(base)

    def p(face, img):
        w, h = img.size
        px = img.load()
        c = t[FACE_TONE[face]] + (a,)
        for y in range(h):
            for x in range(w):
                px[x, y] = c
    p.swatch = (tuple(base), a)
    return p


def smooth(base, details=()):
    """Sculpt material: one tone per face (lit from above-front), a faint dither, NO outline or bevel —
    so hundreds of small cubes melt into one smooth surface instead of reading as bricks."""
    if not details:
        return swatch(base)
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
    """A chakra-construct material: smooth and translucent."""
    return swatch(col, a)


def flesh(col, vein=None):
    return swatch(col) if not vein else smooth(col, [stripes(vein, 7, "x")])


# ------------------------------------------------------------------ shapes
def box_at(m, bone, center, size, paint, rot=None):
    """A box centred on `center`, optionally rotated about its own centre."""
    frm = [center[i] - size[i] / 2 for i in range(3)]
    m.box(bone, frm, size, paint, rot=rot, pivot=list(center) if rot else None)


def _rad(radii, v):
    return 1.0 / math.sqrt(sum((v[i] / radii[i]) ** 2 for i in range(3)))


AXES = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}


def blob(m, bone, center, radii, paint, slices=6, axis="y", rot=None, cross=0.72, spins=(0, 30, 60)):
    """Ellipsoid from stacked slices; every slice is three slabs turned 0/30/60 degrees about the axis, each sized to
    the ellipse — a near-round 12-sided section. `axis` may be "x"/"y"/"z" or a direction vector."""
    A = norm(AXES[axis] if isinstance(axis, str) else axis)
    R = _rad(radii, A)
    for i in range(slices):
        t0 = -R + 2 * R * i / slices
        t1 = t0 + 2 * R / slices
        tm = (t0 + t1) / 2
        k = max(0.3, math.sqrt(max(0.0, 1 - (tm / R) ** 2)))
        c = add(center, mul(A, tm))
        for sp in spins:
            X = norm(vcross(A, [0, 0, 1] if abs(A[2]) < 0.9 else [1, 0, 0]))
            Z = vcross(X, A)
            cs, sn = math.cos(math.radians(sp)), math.sin(math.radians(sp))
            Xs, Zs = add(mul(X, cs), mul(Z, -sn)), add(mul(X, sn), mul(Z, cs))
            wx, wz = _rad(radii, Xs) * k * 0.94, _rad(radii, Zs) * k * 0.94
            obox(m, bone, c, [2 * wx, (t1 - t0) + 0.12, 2 * wz], paint, A, sp)


def tube(m, bone, points, radii, paints, knuckles=True, cross=0.72, flat=1.0, spins=(0, 30, 60), width=None):
    """A tapered limb through `points` (use spline() for curves). Each segment is three boxes turned about the
    segment's own axis (a round 12-sided section); `paints` is one painter or a list cycled per segment (colour
    bands). `flat` < 1 makes a flat ribbon (one box, its wide side along `width` if given)."""
    if not isinstance(paints, (list, tuple)):
        paints = [paints]
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        d = sub(b, a)
        L = length(d)
        if L < 0.05:
            continue
        r = (radii[i] + radii[i + 1]) / 2
        p = paints[i % len(paints)]
        ext = r * 0.45
        c = add(a, mul(d, 0.5))
        if flat < 0.999:
            obox(m, bone, c, [2 * r, L + ext, max(0.25, 2 * r * flat)], p, d, 0, width)
        else:
            for sp in spins:
                obox(m, bone, c, [2 * r * 0.9, L + ext, 2 * r * 0.9], p, d, sp)
        if knuckles and 0 < i and flat >= 0.999:
            k = radii[i] * 1.05
            obox(m, bone, a, [2 * k * 0.9, 2 * k * 0.8, 2 * k * 0.9], p, d, 45)


def curve_tube(m, bone, ctrl, r0, r1, paints, n=3, **kw):
    pts = spline(ctrl, n)
    radii = [r0 + (r1 - r0) * i / max(1, len(pts) - 1) for i in range(len(pts))]
    tube(m, bone, pts, radii, paints, **kw)
    return pts


def blade(m, bone, base, direction, length_, width, thick, paint, taper=True, width_dir=None):
    """A flat blade / feather / claw grown from `base` along `direction`, its flat side spanning `width_dir`
    (if given), tapering to a point in three steps."""
    d = norm(direction)
    segs = 3 if taper else 1
    p = list(base)
    for i in range(segs):
        w = width * (1 - i / (segs + 0.6)) if taper else width
        L = length_ / segs
        obox(m, bone, add(p, mul(d, L / 2)), [w, L + 0.2, thick], paint, d, 0, width_dir)
        p = add(p, mul(d, L))


def plate(m, bone, center, along, across, length_, width, thick, paint):
    """A flat panel: length along `along`, width along `across` (membranes, armour plates)."""
    obox(m, bone, center, [width, length_, thick], paint, along, 0, across)


def bones_from(pivots, parents):
    """Bone list from model-space pivots (export mirrors x)."""
    out = []
    for name, pv in pivots.items():
        b = {"name": name, "pivot": [-pv[0], pv[1], pv[2]]}
        if parents.get(name):
            b["parent"] = parents[name]
        out.append(b)
    return out
