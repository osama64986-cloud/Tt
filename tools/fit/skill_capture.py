"""يرسم مهارة وحش من تسجيل السكربت الحقيقي (tools/sim/record_skill.mjs): المجسمات بوضعيات الأنيميشن الحقيقية، أشكال FX بمواقعها الفعلية،
والجزيئات محسوبة من تعريفات ماينكرافت الأصلية (particle_sim.py): نفس الأحجام والأعمار والسرعات والألوان.
الاستعمال: python3 tools/fit/skill_capture.py <capture.json> <out.png> [--t 10,20,40] [--cam yaw,pitch,dist,cx,cy,cz] [--size 640] [--cols 3]"""
import argparse, json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_scenes as SS
import particle_sim as PS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SHAPES_JS = open(os.path.join(ROOT, "AnimePowers", "BP", "scripts", "shapes.js"), encoding="utf-8").read()
SHAPE_BY_ID = {int(v): k for k, v in re.findall(r'"([a-z0-9_]+)":\s*(\d+)', SHAPES_JS)}
CTRL = json.load(open(os.path.join(ROOT, "AnimePowers", "RP", "animation_controllers", "sh_grim.ac.json"), encoding="utf-8"))["animation_controllers"]
MODEL = {"sh:magmamoth": "magmamoth", "sh:veilfox": "veilfox", "sh:gloomhorn": "gloomhorn", "sh:hollow_seer": "hollow_seer", "sh:grey_bear": "grey_bear", "sh:bear_cub": "bear_cub", "sh:prayer_mantis": "prayer_mantis", "sh:hollow_harvester": "hollow_harvester"}
SCALE = {}
ANIM_OF = {"sh:bear_cub": "grey_bear"}
_models = {}


def state_anims(mtype, state):
    short = mtype.split(":")[1]
    c = CTRL.get(f"controller.animation.sh_{short}.state")
    if not c or not state:
        return []
    for tr in c["states"]["default"].get("transitions", []):
        for name, cond in tr.items():
            if cond == f"query.property('sh:state') == {int(state)}":
                return [f"animation.sh_{short}.{a}" for a in c["states"][name].get("animations", [])]
    return []


# كيانات FX (دائرة رون، لوحة، بوابة، بلورة، قشرة الجسم): نفس الموديل والتكستشر حسب اللون (sh:c) والحجم (sh:r) ونفس أنميشن sh_fx
FX_ENT = {"sh:fx_circle": "circle", "sh:fx_plate": "plate", "sh:fx_portal": "portal", "sh:fx_crystal": "crystal", "sh:fx_body": "body"}
_fx_models = {}


def fx_model(kind, c):
    key = (kind, c)
    if key not in _fx_models:
        tex = f"sh_fx_{kind}_{int(c)}.png" if kind != "body" else f"sh_fx_body_{int(c) % 2}.png"
        _fx_models[key] = SS.R.Model(os.path.join(SS.GEO, f"sh_fx_{kind}.geo.json"), os.path.join(SS.TEX, tex))
    return _fx_models[key]


def fx_pose(kind, life, props):
    p = lambda bone, rot=(0, 0, 0), pos=(0, 0, 0): {bone: {"rot": list(rot), "pos": list(pos)}}
    if kind == "circle":
        return p("disc", (0, life * 40, 0)), 1.0
    if kind == "plate":
        q = p("plate", (0, life * 150, 0)); q.update(p("root", pos=(0, math.sin(math.radians(life * 180)) * 0.8, 0)))
        return q, min(1.0, life * 4)
    if kind == "portal":
        return p("ring", (0, 0, life * 240)), min(1.0, life * 5)
    if kind == "crystal":
        return p("spike", (props.get("sh:p", 0) or 0, 0, life * 60)), min(1.0, life * 6)
    if kind == "body":
        return p("head", (props.get("sh:p", 0) or 0, 0, 0)), 1.0
    return {}, 1.0


def zombie(S, pos, d=(0, -1)):
    """زومبي ماينكرافت مبسط بالبلوكات (2 بلوكة): جلد أخضر، قميص سماوي، بنطرون بنفسجي غامق، أذرع ممدودة لقدام."""
    Rm = SS.roty(SS.yaw_for(d))
    skin, shirt, pants = (78, 128, 70), (40, 140, 150), (60, 50, 120)
    parts = [((-0.25, 0, -0.125), (0.0, 0.75, 0.125), pants), ((0.0, 0, -0.125), (0.25, 0.75, 0.125), pants),
             ((-0.25, 0.75, -0.125), (0.25, 1.5, 0.125), shirt),
             ((-0.5, 1.25, -0.75), (-0.25, 1.5, 0.0), shirt), ((0.25, 1.25, -0.75), (0.5, 1.5, 0.0), shirt),
             ((-0.25, 1.5, -0.25), (0.25, 2.0, 0.25), skin)]
    for lo, hi, col in parts:
        fc = SS.R.face_corners(*lo, *hi)
        for f in SS.R.FACES:
            S.faces.append((np.array(fc[f], dtype=float) @ Rm.T + np.array(pos), "col", (np.array(col, dtype=float), False)))


def render_frame(cap, T, parts_by_t, cam, size, snaps, start_tick):
    S = SS.Scene()
    S.ground(0, cap["dist"] / 2, 14)
    fr = min(snaps, key=lambda f: abs(f["t"] - T))
    is_player_cap = cap.get("type") == "player"
    born = cap.setdefault("_born", {})
    if not born:
        for f in snaps:
            for e in f["ents"]:
                born.setdefault(e["id"], f["t"])
    for e in fr["ents"]:
        pos = (e["x"], e["y"] - 64, e["z"])
        yaw = math.radians(e["yaw"]); d = (-math.sin(yaw), math.cos(yaw))
        if e["type"] == "player":
            S.player(pos, (0, 1)); continue
        if e["type"] == "minecraft:zombie":
            zombie(S, pos, (0, -1)); continue
        if e["type"] in FX_ENT:
            kind = FX_ENT[e["type"]]
            life = max(0.0, (T - born.get(e["id"], T)) / 20.0)
            c = e["props"].get("sh:v" if kind == "body" else "sh:c", 0) or 0
            pose, grow = fx_pose(kind, life, e["props"])
            r = e["props"].get("sh:r", 1.0) or 1.0
            S.model(fx_model(kind, c), pose, pos, d, r * grow)
            continue
        if is_player_cap and e["type"] != "sh:fx_shape":
            continue                                            # وحوش طبيعية ظهرت بالمحاكي: مو جزء من المهارة
        if e["type"] in MODEL:
            nm = MODEL[e["type"]]
            hot = bool(e["props"].get("sh:hot", 0))
            camo = bool(e["props"].get("sh:camo", 0))
            key = (nm, hot, camo)
            if key not in _models:
                _models[key] = SS.R.Model(os.path.join(SS.GEO, f"sh_{nm}.geo.json"), os.path.join(SS.TEX, f"sh_{nm}{'_camo' if camo else '_hot' if hot else ''}.png"))
            m = _models[key]
            st = e["props"].get("sh:state", 0)
            an = "grey_bear" if nm == "bear_cub" else nm                 # الجرو يستعمل أنميشن الدب
            anims = [f"animation.sh_{an}.idle"] + state_anims(e["type"], st)
            t_anim = max(0.0, (T - start_tick) / 20.0)
            S.model(m, SS.pose(anims, t_anim), pos, d, SCALE.get(e["type"], 1.0))
        elif e["type"] == "sh:fx_shape":
            name = SHAPE_BY_ID.get(int(e["props"].get("sh:v", -1)))
            if name in SS.SHAPES:
                p = e["props"]
                life = max(0.0, (T - born.get(e["id"], T)) / 20.0)
                S.shape(name, pos, d, p.get("sh:r", 1.0) or 1.0, p.get("sh:p", 0.0) or 0.0, p.get("sh:a", 0.0) or 0.0,
                        life=life, s=p.get("sh:s", 0.0) or 0.0, w=p.get("sh:w", 0.0) or 0.0, l=p.get("sh:l", 1.0) or 1.0)
    Tsec = T / 20.0
    n = 0
    for pt in parts_by_t:
        st = PS.state_at(pt, Tsec, ground=0.0)
        if st is None:
            continue
        spr = PS.sprite(st)
        if spr is None or st["size"] <= 0:
            continue
        S.sprite((st["pos"][0], st["pos"][1] - 64, st["pos"][2]), st["size"], spr)
        n += 1
    yaw, pitch, dist, cx, cy, cz = cam
    im = S.render((cx, cy, cz), yaw=yaw, pitch=pitch, dist=dist, size=size)
    return im, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cap"); ap.add_argument("out")
    ap.add_argument("--t", default="10,30,50,70,90,110")
    ap.add_argument("--cam", default="-62,18,16,0,2,4")
    ap.add_argument("--size", type=int, default=640)
    ap.add_argument("--cols", type=int, default=3)
    a = ap.parse_args()
    cap = json.load(open(a.cap))
    start = cap["start"]
    parts = []
    for ev in cap["particles"]:
        parts += PS.spawn_event(ev)
    ticks = [start + int(x) for x in a.t.split(",")]
    cam = [float(x) for x in a.cam.split(",")]
    tiles = []
    for T in ticks:
        im, n = render_frame(cap, T, parts, cam, a.size, cap["frames"], start)
        ImageDraw.Draw(im).text((8, 6), f"+{T - start} tick  |  {n} جزيء", fill=(255, 255, 255))
        tiles.append(im)
    cols = min(a.cols, len(tiles)); rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * a.size, rows * a.size))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * a.size, (i // cols) * a.size))
    sheet.save(a.out); print(a.out, sheet.size)


if __name__ == "__main__":
    main()
