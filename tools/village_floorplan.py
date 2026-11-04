"""مخطط أرضي للبيت من مخطط القرية: الدور الأول والعلية من فوق (بدون سقف) مع رموز للأثاث.
python3 tools/village_floorplan.py plan_village.json out.png [house_x house_z]"""
import json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_village as C
import preview_structures as PV

def plan(vox, hx, hz, y0, y1, S=34):
    n = 17
    im = Image.new("RGB", (n * S, n * S), (40, 38, 46)); d = ImageDraw.Draw(im)
    for i, x in enumerate(range(hx - 8, hx + 9)):
        for j, z in enumerate(range(hz - 8, hz + 9)):
            top = None
            for y in range(y1, y0 - 1, -1):
                b = vox.get((x, y, z))
                if b and b != "minecraft:air":
                    top = (y, b); break
            if not top:
                continue
            col = PV.color(top[1]); sh = 0.75 + 0.06 * (top[0] - y0)
            col = tuple(max(0, min(255, int(v * sh))) for v in col)
            d.rectangle([i * S, j * S, (i + 1) * S - 1, (j + 1) * S - 1], fill=col, outline=(20, 20, 24))
            n_ = top[1].replace("minecraft:", "")
            lab = {"bed": "BED", "crafting_table": "CRAFT", "furnace": "FURN", "chest": "CHEST", "bookshelf": "BOOK", "lectern": "LECT", "loom": "LOOM", "cartography_table": "MAP",
                   "composter": "COMP", "flowering_azalea": "AZ", "moss_block": "MOSS", "pink_tulip": "TUL", "spruce_door": "DOOR", "lantern": "L"}.get(n_)
            if "stairs" in n_: lab = "^"
            if lab:
                d.text((i * S + 3, j * S + S // 2 - 5), lab, fill=(255, 255, 255))
    return im

if __name__ == "__main__":
    pl = json.load(open(sys.argv[1])); vox, _, _ = C.replay(pl)
    hx, hz = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, -26)
    a = plan(vox, hx, hz, 1, 4); b = plan(vox, hx, hz, 5, 7)
    out = Image.new("RGB", (a.width * 2 + 20, a.height + 30), (24, 22, 30)); dd = ImageDraw.Draw(out)
    out.paste(a, (0, 30)); out.paste(b, (a.width + 20, 30))
    dd.text((8, 8), "1st floor (roof removed)", fill=(255, 255, 255)); dd.text((a.width + 28, 8), "2nd floor / loft", fill=(255, 255, 255))
    out.save(sys.argv[2]); print("saved", sys.argv[2])
