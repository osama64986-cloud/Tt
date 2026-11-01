"""محاكي جزيئات ماينكرافت (Bedrock): يقرأ تعريفات Mojang الأصلية (ملفات resource_pack/particles من bedrock-samples) ويحسب لكل جزيء طلبه السكربت:
المكان، الاتجاه، السرعة الابتدائية، التسارع والاحتكاك، العمر، الحجم، إطار اللوحة (flipbook)، واللون (tinting). هذا هو الشكل اللي تنرسم فيه الجزيئات باللعبة.

يغطي المكونات اللي تستعملها جزيئات المود: emitter_rate_instant/steady/manual، emitter_shape_point/sphere/box/custom/disc/entity_aabb،
particle_initial_speed، particle_lifetime_expression، particle_motion_dynamic (تسارع + احتكاك)، particle_motion_parametric، particle_motion_collision (أرض مستوية)،
particle_appearance_billboard (حجم، uv، flipbook)، particle_appearance_tinting (gradient أو تعبيرات)، emitter_initialization.
ما يغطي: أحداث (events/timeline)، الإضاءة، دوران اللوحة نحو السرعة، وجزيئات بتكستشر غير أطلس particles.png.

ملفات Mojang مو داخل المستودع: حمّلها من https://github.com/Mojang/bedrock-samples (resource_pack/particles + textures/particle/particles.png)
وحط مسارهم بمتغير البيئة SH_VANILLA_PARTICLES (مجلد فيه particles/*.json و particles.png)."""
import glob
import json
import math
import os
import random
import re

import numpy as np
from PIL import Image

VP = os.environ.get("SH_VANILLA_PARTICLES", "/tmp/claude-0/-home-user-Tt/0411a7b6-807a-5373-b9a7-bb7ee38240a7/scratchpad/vanilla_p")
DEF_DIR = os.path.join(VP, "all") if os.path.isdir(os.path.join(VP, "all")) else os.path.join(VP, "particles")

# ───────────── Molang مصغّر ─────────────
_TOK = re.compile(r"\s*(?:(\d+\.?\d*|\.\d+)|([A-Za-z_][\w.]*)|(\?\?|&&|\|\||==|!=|<=|>=|[-+*/()<>?:,!;=]))")


def _tokens(s):
    out, i = [], 0
    s = s.strip()
    while i < len(s):
        m = _TOK.match(s, i)
        if not m:
            raise ValueError("molang: " + s)
        i = m.end()
        if m.group(1) is not None:
            out.append(("n", float(m.group(1))))
        elif m.group(2) is not None:
            out.append(("id", m.group(2).lower()))
        else:
            out.append(("op", m.group(3)))
    return out


class _P:
    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def eat(self, v=None):
        tk = self.peek()
        if v is not None and tk[1] != v:
            raise ValueError("expected " + v)
        self.i += 1
        return tk

    def expr(self):
        c = self.coal()
        if self.peek() == ("op", "?"):
            self.eat()
            a = self.expr()
            self.eat(":")
            b = self.expr()
            return ("?", c, a, b)
        return c

    def coal(self):
        l = self.orr()
        while self.peek() == ("op", "??"):
            self.eat()
            l = ("??", l, self.orr())
        return l

    def orr(self):
        l = self.andd()
        while self.peek() == ("op", "||"):
            self.eat()
            l = ("||", l, self.andd())
        return l

    def andd(self):
        l = self.cmp()
        while self.peek() == ("op", "&&"):
            self.eat()
            l = ("&&", l, self.cmp())
        return l

    def cmp(self):
        l = self.add()
        while self.peek()[0] == "op" and self.peek()[1] in ("<", ">", "<=", ">=", "==", "!="):
            o = self.eat()[1]
            l = (o, l, self.add())
        return l

    def add(self):
        l = self.mul()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            o = self.eat()[1]
            l = (o, l, self.mul())
        return l

    def mul(self):
        l = self.un()
        while self.peek()[0] == "op" and self.peek()[1] in ("*", "/"):
            o = self.eat()[1]
            l = (o, l, self.un())
        return l

    def un(self):
        if self.peek() == ("op", "-"):
            self.eat()
            return ("neg", self.un())
        if self.peek() == ("op", "!"):
            self.eat()
            return ("not", self.un())
        return self.prim()

    def prim(self):
        k, v = self.eat()
        if k == "n":
            return ("c", v)
        if k == "id":
            if self.peek() == ("op", "("):
                self.eat()
                args = []
                if self.peek() != ("op", ")"):
                    args.append(self.expr())
                    while self.peek() == ("op", ","):
                        self.eat()
                        args.append(self.expr())
                self.eat(")")
                return ("f", v, args)
            return ("v", v)
        if (k, v) == ("op", "("):
            e = self.expr()
            self.eat(")")
            return e
        raise ValueError("bad token")


RNG = random.Random(11)


def _call(name, a):
    n = name.replace("math.", "")
    if n == "random":
        return a[0] + (a[1] - a[0]) * RNG.random()
    if n == "max": return max(a)
    if n == "min": return min(a)
    if n == "abs": return abs(a[0])
    if n == "sin": return math.sin(math.radians(a[0]))
    if n == "cos": return math.cos(math.radians(a[0]))
    if n == "pow": return math.pow(a[0], a[1]) if not (a[0] < 0 and a[1] != int(a[1])) else 0.0
    if n == "sqrt": return math.sqrt(max(0.0, a[0]))
    if n == "floor": return math.floor(a[0])
    if n == "ceil": return math.ceil(a[0])
    if n == "round": return round(a[0])
    if n == "clamp": return max(a[1], min(a[2], a[0]))
    if n == "lerp": return a[0] + (a[1] - a[0]) * a[2]
    if n == "mod": return math.fmod(a[0], a[1]) if a[1] else 0.0
    if n == "exp": return math.exp(a[0])
    return 0.0


def _ev(n, env):
    k = n[0]
    if k == "c": return n[1]
    if k == "v": return env.get(n[1], 0.0)
    if k == "neg": return -_ev(n[1], env)
    if k == "not": return 0.0 if _ev(n[1], env) else 1.0
    if k == "f": return _call(n[1], [_ev(x, env) for x in n[2]])
    if k == "?": return _ev(n[2], env) if _ev(n[1], env) else _ev(n[3], env)
    if k == "??":
        if n[1][0] == "v" and n[1][1] not in env:
            return _ev(n[2], env)
        return _ev(n[1], env)
    a, b = _ev(n[1], env), _ev(n[2], env)
    if k == "+": return a + b
    if k == "-": return a - b
    if k == "*": return a * b
    if k == "/": return a / b if b else 0.0
    if k == "<": return float(a < b)
    if k == ">": return float(a > b)
    if k == "<=": return float(a <= b)
    if k == ">=": return float(a >= b)
    if k == "==": return float(a == b)
    if k == "!=": return float(a != b)
    if k == "&&": return float(bool(a) and bool(b))
    if k == "||": return float(bool(a) or bool(b))
    return 0.0


_CACHE = {}


def mo(x, env):
    """يقيّم تعبير Molang (رقم أو نص) ويرجع رقم"""
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, bool):
        return float(x)
    ast = _CACHE.get(x)
    if ast is None:
        ast = _CACHE[x] = _P(_tokens(x)).expr()
    return float(_ev(ast, env))


def run_statements(s, env):
    for st in s.split(";"):
        st = st.strip()
        if not st or "{" in st:
            continue
        m = re.match(r"^([\w.]+)\s*=\s*(?!=)(.+)$", st)
        if m:
            env[m.group(1).lower()] = mo(m.group(2), env)


# ───────────── تعريفات Mojang ─────────────
DEFS = {}
for _f in glob.glob(os.path.join(DEF_DIR, "*.json")):
    try:
        _d = json.load(open(_f, encoding="utf-8"))
        _pe = _d["particle_effect"]
        DEFS[_pe["description"]["identifier"]] = _pe
    except Exception:
        pass
def _load(name):
    try:
        return np.array(Image.open(os.path.join(VP, name)).convert("RGBA"))
    except Exception:
        return None


ATLAS = _load("particles.png")                       # textures/particle/particles.png (128x128)
TEXTURES = {"textures/particle/particles": ATLAS, "textures/flame_atlas": _load("flame_atlas.png")}   # flame_atlas: 16x512 (32 إطار لهب مخلوق محترق)


def _vec(v, env, n=3):
    if isinstance(v, list):
        return [mo(x, env) for x in v[:n]] + [0.0] * (n - len(v))
    return [0.0] * n


class Particle:
    __slots__ = ("id", "t0", "pos", "vel", "life", "env", "c", "r", "rec")


def spawn_event(ev, rng=None):
    """حدث سجّله المحاكي {t,id,x,y,z,v} ← قائمة جزيئات بخصائصها الابتدائية (t0 بالثواني)"""
    pe = DEFS.get(ev["id"])
    if not pe:
        return []
    c = pe["components"]
    g = lambda k: c.get("minecraft:" + k)
    ee = {k.lower(): float(v) for k, v in ev["v"].items()}
    if g("emitter_initialization"):
        run_statements(g("emitter_initialization").get("creation_expression", ""), ee)
    t0 = ev["t"] / 20.0
    n, span = 1, 0.0
    if g("emitter_rate_instant"):
        n = int(mo(g("emitter_rate_instant").get("num_particles", 1), ee))
    elif g("emitter_rate_steady"):
        rs = g("emitter_rate_steady")
        span = float((g("emitter_lifetime_once") or g("emitter_lifetime_looping") or {}).get("active_time", 1.0))
        n = int(min(mo(rs.get("max_particles", 50), ee), mo(rs.get("spawn_rate", 1), ee) * span))
    out = []
    for k in range(max(1, n)):
        p = Particle()
        p.id = ev["id"]
        p.t0 = t0 + (k / max(1, n)) * span
        env = dict(ee)
        for i in range(1, 5):
            env[f"variable.particle_random_{i}"] = RNG.random()
        env["variable.particle_age"] = 0.0
        env["query.frame_alpha"] = 0.0
        # الشكل: مكان وبداية الاتجاه
        off, dr = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        for sh in ("point", "sphere", "box", "custom", "disc", "entity_aabb"):
            s = g("emitter_shape_" + sh)
            if s is None:
                continue
            off = _vec(s.get("offset"), env) if s.get("offset") is not None else [0.0, 0.0, 0.0]
            d = s.get("direction")
            if sh == "sphere":
                rad = mo(s.get("radius", 1), env)
                a, b = RNG.random() * 6.2832, RNG.random() * 2 - 1
                rr = math.sqrt(1 - b * b)
                u = [math.cos(a) * rr, b, math.sin(a) * rr]
                rad = rad if s.get("surface_only") else rad * RNG.random() ** (1 / 3)
                off = [off[i] + u[i] * rad for i in range(3)]
                dr = u if d == "outwards" else [-x for x in u] if d == "inwards" else _vec(d, env)
            elif sh == "box":
                hd = _vec(s.get("half_dimensions"), env)
                off = [off[i] + (RNG.random() * 2 - 1) * hd[i] for i in range(3)]
                dr = _vec(d, env)
            elif sh == "disc":
                rad = mo(s.get("radius", 1), env)
                a = RNG.random() * 6.2832
                rr = rad if s.get("surface_only") else rad * math.sqrt(RNG.random())
                off = [off[0] + math.cos(a) * rr, off[1], off[2] + math.sin(a) * rr]
                dr = _vec(d, env) if isinstance(d, list) else [math.cos(a), 0, math.sin(a)]
            else:
                dr = _vec(d, env) if isinstance(d, list) else [0.0, 0.0, 0.0]
            break
        p.pos = [ev["x"] + off[0], ev["y"] + off[1], ev["z"] + off[2]]
        ln = math.sqrt(sum(x * x for x in dr))
        sp = g("particle_initial_speed")
        if isinstance(sp, list):
            vel = [mo(x, env) for x in sp[:3]]
        else:
            s_ = mo(sp, env) if sp is not None else 1.0
            vel = [dr[i] / ln * s_ for i in range(3)] if ln > 1e-9 else [0.0, 0.0, 0.0]
        p.vel = vel
        lt = g("particle_lifetime_expression") or {}
        p.life = max(0.05, mo(lt.get("max_lifetime", 1.0), env))
        env["variable.particle_lifetime"] = p.life
        p.env = env
        p.c = c
        out.append(p)
    return out


def state_at(p, T, ground=None):
    """مكان وعمر وحجم ولون وإطار الجزيء بالوقت T (ثواني). يرجع None إذا ما انولد أو مات"""
    age = T - p.t0
    if age < 0 or age > p.life:
        return None
    c, env = p.c, p.env
    g = lambda k: c.get("minecraft:" + k)
    pos, vel = list(p.pos), list(p.vel)
    dyn, col, par = g("particle_motion_dynamic"), g("particle_motion_collision"), g("particle_motion_parametric")
    dt, a = 0.05, 0.0
    while a < age - 1e-9:
        h = min(dt, age - a)
        env["variable.particle_age"] = a
        acc = _vec(dyn.get("linear_acceleration"), env) if dyn and dyn.get("linear_acceleration") is not None else [0.0, 0.0, 0.0]
        drag = mo(dyn.get("linear_drag_coefficient", 0), env) if dyn else 0.0
        for i in range(3):
            vel[i] += (acc[i] - drag * vel[i]) * h
            pos[i] += vel[i] * h
        if col and ground is not None:
            rad = float(col.get("collision_radius", 0.1))
            if pos[1] - rad < ground:
                pos[1] = ground + rad
                if vel[1] < 0:
                    vel[1] = -vel[1] * float(col.get("coefficient_of_restitution", 0.0))
                k = math.exp(-float(col.get("collision_drag", 0)) * h)
                vel[0] *= k
                vel[2] *= k
        a += h
    env["variable.particle_age"] = age
    env["query.frame_alpha"] = 0.0
    if par and par.get("relative_position") is not None:
        rp = _vec(par["relative_position"], env)
        pos = [p.pos[i] + rp[i] for i in range(3)]
    bb = g("particle_appearance_billboard")
    if not bb:
        return None
    sz = [mo(x, env) for x in bb["size"]]
    uv = bb.get("uv", {})
    tw, th = uv.get("texture_width", 128), uv.get("texture_height", 128)
    fb = uv.get("flipbook")
    if fb:
        mf = int(fb.get("max_frame", 1))
        if fb.get("stretch_to_lifetime"):
            fr = min(mf - 1, int(age / p.life * mf))
        else:
            fr = min(mf - 1, int(age * float(fb.get("frames_per_second", 1)))) if True else 0
        b, st = fb["base_UV"], fb["step_UV"]
        sUV = fb.get("size_UV", uv.get("uv_size", [8, 8]))
        rect = (b[0] + st[0] * fr, b[1] + st[1] * fr, sUV[0], sUV[1])
    else:
        u0, s0 = uv.get("uv", [0, 0]), uv.get("uv_size", [8, 8])
        rect = (mo(u0[0], env), mo(u0[1], env), mo(s0[0], env), mo(s0[1], env))      # الـuv ممكن يكون تعبير (portal: يختار إطار عشوائي)
    color = (1.0, 1.0, 1.0)
    tn = g("particle_appearance_tinting")
    if tn:
        cc = tn.get("color")
        if isinstance(cc, dict) and "gradient" in cc:
            stops = sorted(((float(k), v) for k, v in cc["gradient"].items()), key=lambda kv: kv[0])
            x = mo(cc.get("interpolant", 0), env)
            def col_of(v):
                if isinstance(v, str):
                    h_ = v.lstrip("#")
                    return tuple(int(h_[i:i + 2], 16) / 255 for i in (2, 4, 6)) if len(h_) == 8 else (1, 1, 1)
                return tuple(mo(q, env) for q in v[:3])
            if x <= stops[0][0] or len(stops) == 1:
                color = col_of(stops[0][1])
            elif x >= stops[-1][0]:
                color = col_of(stops[-1][1])
            else:
                for (k0, v0), (k1, v1) in zip(stops, stops[1:]):
                    if k0 <= x <= k1:
                        f = (x - k0) / (k1 - k0) if k1 > k0 else 0
                        c0, c1 = col_of(v0), col_of(v1)
                        color = tuple(c0[i] + (c1[i] - c0[i]) * f for i in range(3))
                        break
        elif isinstance(cc, list):
            color = tuple(mo(q, env) for q in cc[:3])
    tex = pe_texture(p.id)
    if "texture_width" not in uv and "texture_height" in uv:
        tw = 1                                       # مثل mobflame: الـuv بوحدات إطار كامل (العرض = 1 وحدة)
    return {"pos": pos, "size": max(0.0, sz[0]), "rect": rect, "tw": tw, "th": th, "color": color, "tex": tex, "vel": vel, "age": age}


def pe_texture(pid):
    pe = DEFS.get(pid)
    return pe["description"].get("basic_render_parameters", {}).get("texture") if pe else None


def sprite(st):
    """صورة اللوحة (RGBA numpy float) بعد التلوين. None إذا التكستشر مو الأطلس"""
    tex = TEXTURES.get(st["tex"])
    if tex is None:
        return None
    sx, sy = tex.shape[1] / float(st["tw"]), tex.shape[0] / float(st["th"])      # وحدات الـuv ← بكسلات
    u, v, w, h = int(round(st["rect"][0] * sx)), int(round(st["rect"][1] * sy)), int(round(st["rect"][2] * sx)), int(round(st["rect"][3] * sy))
    if w <= 0 or h <= 0:
        return None
    sp = tex[v:v + h, u:u + w].astype(np.float32)
    if sp.size == 0:
        return None
    sp[..., :3] *= np.array(st["color"], np.float32).clip(0, 4)
    sp[..., :3] = sp[..., :3].clip(0, 255)
    return sp
