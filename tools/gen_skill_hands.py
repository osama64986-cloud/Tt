"""مهارات القدرات ما تطلع بإيد اللاعب: كل أيتم مهارة (sh:skill_*) ياخذ attachable فاضي.
الأيقونة تبقى بالإنفنتوري والهوتبار، بس الإيد تبين فاضية (بالمنظور الأول والثالث ومجسم الـHUD).
الأسلحة ما تنلمس (لها attachables خاصة)، ولفافة تطور المهارة تبقى ظاهرة لأنها لفافة حقيقية.
التشغيل: python3 tools/gen_skill_hands.py
"""
import glob
import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "AnimePowers", "BP")
RP = os.path.join(ROOT, "AnimePowers", "RP")
KEEP_VISIBLE = {"sh:skill_scroll"}


def main():
    os.makedirs(os.path.join(RP, "textures", "models"), exist_ok=True)
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(os.path.join(RP, "textures", "models", "sh_empty.png"))
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry.sh_empty_hand", "texture_width": 4, "texture_height": 4,
                        "visible_bounds_width": 1, "visible_bounds_height": 1, "visible_bounds_offset": [0, 0, 0]},
        # مكعب صغير جداً على بكسل شفاف (الماتيريال alphatest يتجاهله): الإيد تبين فاضية
        "bones": [{"name": "sh_hand", "pivot": [0, 0, 0], "cubes": [{"origin": [0, 0, 0], "size": [0.01, 0.01, 0.01], "uv": [0, 0]}]}],
    }]}
    with open(os.path.join(RP, "models", "entity", "sh_empty_hand.geo.json"), "w") as f:
        json.dump(geo, f, separators=(",", ":"))
    n = 0
    for path in sorted(glob.glob(os.path.join(BP, "items", "*.json"))):
        ident = json.load(open(path, encoding="utf-8"))["minecraft:item"]["description"]["identifier"]
        if not ident.startswith("sh:skill_") or ident in KEEP_VISIBLE:
            continue
        name = ident.split(":")[1]
        att = {"format_version": "1.10.0", "minecraft:attachable": {"description": {
            "identifier": ident,
            "materials": {"default": "entity_alphatest"},
            "textures": {"default": "textures/models/sh_empty"},
            "geometry": {"default": "geometry.sh_empty_hand"},
            "render_controllers": ["controller.render.item_default"],
        }}}
        with open(os.path.join(RP, "attachables", f"{name}.attachable.json"), "w") as f:
            json.dump(att, f, separators=(",", ":"))
        n += 1
    print(f"skill hands ok: {n} مهارة ما تطلع بالإيد")


if __name__ == "__main__":
    main()
