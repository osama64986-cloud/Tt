import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import render_player as R

env = R.env_for()
pose = R.pose_of(env)
boxes = R.world_boxes(pose)
view = R.camera(0, 8)

def dummy():
    # a plain straw training post, ahead of the player (player faces -z)
    out = []
    def box(x0, y0, z0, x1, y1, z1, col):
        c = [np.array([x, y, z], float) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        out.append((c, col))
    box(-1.5, 0, -60, 1.5, 22, -57, (150, 110, 60))
    box(-6, 14, -59.5, 6, 17, -58, (150, 110, 60))
    box(-4, 22, -62, 4, 30, -55, (205, 175, 95))
    return out

def panel(shift, label, marker, red=False):
    W, H = 420, 380
    im = Image.new("RGB", (W, H), (120, 170, 220))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 250, W, H], fill=(96, 150, 70))
    # a straw training post far ahead, straight in front of the camera (screen centre)
    cx = W // 2
    d.rectangle([cx - 3, 150, cx + 3, 252], fill=(140, 100, 55))
    d.rectangle([cx - 22, 175, cx + 22, 182], fill=(140, 100, 55))
    d.rectangle([cx - 14, 112, cx + 14, 150], fill=(210, 180, 100), outline=(150, 120, 60))
    centre = (W // 2 + shift, 300)
    fig = R.draw(boxes, view, size=(W, H), scale=6.0, centre=centre, label="")
    # paste figure over the sky/ground background
    arr = np.array(fig); bg = np.array(im)
    mask = np.any(arr != (46, 50, 60), axis=2)
    bg[mask] = arr[mask]
    im = Image.fromarray(bg); d = ImageDraw.Draw(im)
    if marker:
        cx, cy = W // 2, 131
        col = (255, 90, 80) if red else (255, 255, 255)
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], outline=(30, 30, 36), width=5)
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=col, width=3)
        d.rectangle([cx - 2, cy - 2, cx + 2, cy + 2], fill=col, outline=(30, 30, 36))
    d.rectangle([0, 0, W, 22], fill=(30, 32, 40))
    d.text((8, 5), label, fill=(240, 240, 240))
    return im

a = panel(0, "Normal 3rd person (game)", False)
b = panel(-95, "Shoulder view - right (marker = hit point)", True)
c = panel(95, "Shoulder view - left", True, red=True)
out = Image.new("RGB", (a.width * 3 + 20, a.height), (20, 20, 24))
for i, p in enumerate((a, b, c)):
    out.paste(p, (i * (a.width + 10), 0))
out.save(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "preview", "shoulder_view.png"))
print("ok")
