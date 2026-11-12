"""A small Molang interpreter for testing our animations outside the game.

Supports what our files use: numbers, 'strings', variable./v., temp./t.,
query./q. (looked up in a dict, called or not), math.* in degrees, unary - !,
* / + - < <= > >= == != && || ??, the ternary a ? b : c, the statement form
cond ? { ... }, blocks, assignments, ';' separated statements and return.
"""
import math
import re

TOKEN = re.compile(r"\s*(?:(\d+\.\d*|\.\d+|\d+)|('[^']*')|([A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*)|(\?\?|&&|\|\||==|!=|<=|>=|[-+*/()<>!?:;,{}=]))")

MATH = {
    "sin": lambda d: math.sin(math.radians(d)), "cos": lambda d: math.cos(math.radians(d)),
    "abs": abs, "sqrt": lambda x: math.sqrt(max(0.0, x)), "pow": lambda a, b: math.copysign(abs(a) ** b, 1) if a >= 0 else a ** b,
    "clamp": lambda x, a, b: max(a, min(b, x)), "lerp": lambda a, b, t: a + (b - a) * t,
    "min": min, "max": max, "mod": math.fmod, "floor": math.floor, "ceil": math.ceil,
    "atan2": lambda y, x: math.degrees(math.atan2(y, x)), "exp": math.exp, "round": round,
    "hermite_blend": lambda t: 3 * t * t - 2 * t * t * t,
}


def tokenize(src):
    out, pos = [], 0
    src = src.strip()
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m or m.end() == pos:
            raise SyntaxError(f"bad token at {src[pos:pos + 20]!r}")
        pos = m.end()
        num, s, name, op = m.groups()
        if num is not None:
            out.append(("num", float(num)))
        elif s is not None:
            out.append(("str", s[1:-1]))
        elif name is not None:
            out.append(("name", name.lower()))
        else:
            out.append(("op", op))
    out.append(("end", None))
    return out


class Parser:
    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self, k=0):
        return self.t[self.i + k]

    def take(self, op=None):
        tok = self.t[self.i]
        if op is not None and tok != ("op", op):
            raise SyntaxError(f"expected {op} got {tok}")
        self.i += 1
        return tok

    def program(self, stop=("end",)):
        stmts = []
        while True:
            tok = self.peek()
            if tok[0] == "end" or tok == ("op", "}"):
                break
            if tok == ("op", ";"):
                self.take()
                continue
            stmts.append(self.statement())
        return ("block", stmts)

    def statement(self):
        tok = self.peek()
        if tok == ("name", "return"):
            self.take()
            return ("return", self.expr())
        if tok == ("op", "{"):
            self.take()
            b = self.program()
            self.take("}")
            return b
        if tok[0] == "name" and self.peek(1) == ("op", "=") and self.peek(2) != ("op", "="):
            self.take(); self.take("=")
            return ("assign", canon(tok[1]), self.expr())
        e = self.expr(allow_block=True)
        return ("expr", e)

    # precedence climbing
    def expr(self, allow_block=False):
        return self.ternary(allow_block)

    def ternary(self, allow_block=False):
        cond = self.coalesce()
        if self.peek() == ("op", "?") :
            self.take()
            if self.peek() == ("op", "{"):
                self.take()
                then = self.program()
                self.take("}")
                other = None
                if self.peek() == ("op", ":"):
                    self.take()
                    if self.peek() == ("op", "{"):
                        self.take(); other = self.program(); self.take("}")
                    else:
                        other = ("expr", self.ternary())
                return ("ifblock", cond, then, other)
            a = self.ternary()
            if self.peek() == ("op", ":"):
                self.take()
                b = self.ternary()
            else:
                b = ("num", 0.0)          # Molang: 'a ? b' alone gives b or 0
            return ("tern", cond, a, b)
        return cond

    def coalesce(self):
        left = self.oror()
        while self.peek() == ("op", "??"):
            self.take()
            left = ("??", left, self.oror())
        return left

    def binary(self, nxt, ops):
        left = nxt()
        while self.peek()[0] == "op" and self.peek()[1] in ops:
            op = self.take()[1]
            left = (op, left, nxt())
        return left

    def oror(self):
        return self.binary(self.andand, ("||",))

    def andand(self):
        return self.binary(self.compare, ("&&",))

    def compare(self):
        return self.binary(self.add, ("<", "<=", ">", ">=", "==", "!="))

    def add(self):
        return self.binary(self.mul, ("+", "-"))

    def mul(self):
        return self.binary(self.unary, ("*", "/"))

    def unary(self):
        tok = self.peek()
        if tok == ("op", "-"):
            self.take(); return ("neg", self.unary())
        if tok == ("op", "!"):
            self.take(); return ("not", self.unary())
        return self.atom()

    def atom(self):
        tok = self.take()
        if tok[0] == "num":
            return ("num", tok[1])
        if tok[0] == "str":
            return ("str", tok[1])
        if tok == ("op", "("):
            e = self.expr()
            self.take(")")
            return e
        if tok[0] == "name":
            name = canon(tok[1])
            if self.peek() == ("op", "("):
                self.take()
                args = []
                while self.peek() != ("op", ")"):
                    args.append(self.expr())
                    if self.peek() == ("op", ","):
                        self.take()
                self.take(")")
                return ("call", name, args)
            if name in ("true",):
                return ("num", 1.0)
            if name in ("false",):
                return ("num", 0.0)
            return ("var", name)
        raise SyntaxError(f"unexpected {tok}")


def canon(n):
    for a, b in (("variable.", "v."), ("temp.", "t."), ("query.", "q."), ("context.", "c.")):
        if n.startswith(a):
            return b + n[len(a):]
    return n


class Return(Exception):
    def __init__(self, v):
        self.v = v


_cache = {}


def compile_(src):
    if src not in _cache:
        p = Parser(tokenize(src))
        tree = p.program() if ";" in src else ("expr_only", p.expr())
        _cache[src] = (tree, ";" in src)
    return _cache[src]


def run(src, ctx):
    """ctx: {'v': {...}, 'q': {...}}; temps live for one evaluation."""
    if not isinstance(src, str):
        return float(src)
    tree, complex_ = compile_(src)
    temps = {}
    if not complex_:
        return num(ev(tree[1], ctx, temps))
    try:
        exe(tree, ctx, temps)
    except Return as r:
        return num(r.v)
    return 0.0


def num(x):
    if isinstance(x, bool):
        return 1.0 if x else 0.0
    return x if isinstance(x, (int, float)) else 0.0


def exe(node, ctx, temps):
    kind = node[0]
    if kind == "block":
        for s in node[1]:
            exe(s, ctx, temps)
    elif kind == "assign":
        val = ev(node[2], ctx, temps)
        scope, key = node[1].split(".", 1)
        (temps if scope == "t" else ctx["v"])[key] = val
    elif kind == "return":
        raise Return(ev(node[1], ctx, temps))
    elif kind == "expr":
        e = node[1]
        if e[0] == "ifblock":
            if truthy(ev(e[1], ctx, temps)):
                exe(e[2], ctx, temps)
            elif e[3] is not None:
                exe(e[3], ctx, temps)
        else:
            ev(e, ctx, temps)


def truthy(x):
    return bool(x) if not isinstance(x, str) else x != ""


def ev(n, ctx, temps):
    k = n[0]
    if k == "num" or k == "str":
        return n[1]
    if k == "var":
        scope, key = n[1].split(".", 1) if "." in n[1] else ("", n[1])
        if scope == "t":
            return temps.get(key)
        if scope == "v":
            return ctx["v"].get(key)
        if scope == "q":
            v = ctx["q"].get(key, 0.0)
            return v() if callable(v) else v
        return 0.0
    if k == "call":
        name, args = n[1], [ev(a, ctx, temps) for a in n[2]]
        if name.startswith("math."):
            return MATH[name[5:]](*[num(a) for a in args])
        if name.startswith("q."):
            v = ctx["q"].get(name[2:], 0.0)
            return v(*args) if callable(v) else v
        raise NameError(name)
    if k == "neg":
        return -num(ev(n[1], ctx, temps))
    if k == "not":
        return 0.0 if truthy(num(ev(n[1], ctx, temps))) else 1.0
    if k == "tern":
        return ev(n[2], ctx, temps) if truthy(num(ev(n[1], ctx, temps))) else ev(n[3], ctx, temps)
    if k == "??":
        a = ev(n[1], ctx, temps)
        return a if a is not None else ev(n[2], ctx, temps)
    if k == "&&":
        return 1.0 if truthy(num(ev(n[1], ctx, temps))) and truthy(num(ev(n[2], ctx, temps))) else 0.0
    if k == "||":
        return 1.0 if truthy(num(ev(n[1], ctx, temps))) or truthy(num(ev(n[2], ctx, temps))) else 0.0
    a, b = ev(n[1], ctx, temps), ev(n[2], ctx, temps)
    if k in ("==", "!=") and (isinstance(a, str) or isinstance(b, str)):
        return float((a == b) == (k == "=="))
    a, b = num(a), num(b)
    if k == "+": return a + b
    if k == "-": return a - b
    if k == "*": return a * b
    if k == "/": return a / b if b != 0 else 0.0
    if k == "<": return float(a < b)
    if k == "<=": return float(a <= b)
    if k == ">": return float(a > b)
    if k == ">=": return float(a >= b)
    if k == "==": return float(a == b)
    if k == "!=": return float(a != b)
    raise ValueError(k)
