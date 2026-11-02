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
MODEL = {"sh:magmamoth": "magmamoth", "sh:veilfox": "veilfox", "sh:gloomhorn": "gloomhorn", "sh:hollow_seer": "hollow_seer", "sh:grey_bear": "grey_bear", "sh:bear_cub": "bear_cub"}
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


def render_frame(cap, T, parts_by_t, cam, size, snaps, start_tick):
    S = SS.Scene()
    S.ground(0, cap["dist"] / 2, 14)
    fr = min(snaps, key=lambda f: abs(f["t"] - T))
    for e in fr["ents"]:
        pos = (e["x"], e["y"] - 64, e["z"])
        yaw = math.radians(e["yaw"]); d = (-math.sin(yaw), math.cos(yaw))
        if e["type"] == "player":
            S.player(pos, (0, 1)); continue
        if e["type"] in MODEL:
            nm = MODEL[e["type"]]
            hot = bool(e["props"].get("sh:hot", 0))
            key = (nm, hot)
            if key not in _models:
                _models[key] = SS.R.Model(os.path.join(SS.GEO, f"sh_{nm}.geo.json"), os.path.join(SS.TEX, f"sh_{nm}{'_hot' if hot else ''}.png"))
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
                S.shape(name, pos, d, p.get("sh:r", 1.0) or 1.0, p.get("sh:p", 0.0) or 0.0, p.get("sh:a", 0.0) or 0.0)
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
