"""Builds "Nabd Shoulder View": a tiny stand-alone resource pack with only the
shoulder view and the third-person crosshair - no textures, no world look, no
movement changes.  It uses the classic pack slider (works on every version):
Left / Right / Both (follows the camera) / Off.

The shift rides on "animation.humanoid.base_pose" (the game plays it in third
person anyway), for your own player only, never in first person or in the
inventory doll.  It also sets v.nb_sh_on = 0 so the main Nabd pack does not
shift a second time when both packs are active.
"""
import json
import os
import shutil
import uuid
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_CROSS = os.path.join(ROOT, "pack_src", "textures", "ui", "nabd_cross.png")
SRC_UI = os.path.join(ROOT, "pack_src", "ui", "hud_crosshair_overlay.json")
ICON = os.path.join(ROOT, "pack", "pack_icon.png")
OUT = os.path.join(ROOT, "dist", "_shoulder")
ZIP = os.path.join(ROOT, "dist", "Nabd_Shoulder.mcpack")
# fixed ids so the game treats new builds as updates of the same pack
HEADER_UUID = "6b1f4c52-9a3e-4c7e-8f61-2d4a7b9e1c05"
MODULE_UUID = "0f7d2e94-3c18-4b6a-9e25-7a1c8d4f6b30"

TURN = ("t.dt = math.clamp(query.delta_time, 0.0, 0.05); "
        "t.hy = query.head_y_rotation(0); "
        "t.dy = math.mod(t.hy - (v.nb_hy ?? t.hy) + 540.0, 360.0) - 180.0; "
        "v.nb_hy = t.hy; "
        "v.nb_yr = math.lerp(v.nb_yr ?? 0.0, t.dy / math.max(t.dt, 0.001), math.clamp(t.dt * 10.0, 0.0, 1.0)); "
        "v.nb_swt = v.nb_yr > 70.0 ? 1.0 : (v.nb_yr < -70.0 ? -1.0 : (v.nb_swt ?? 1.0)); "
        "v.nb_sws = math.lerp(v.nb_sws ?? 1.0, v.nb_swt, math.clamp(t.dt * 6.0, 0.0, 1.0)); ")
ON = "(query.is_local_player && !query.is_first_person && !query.is_in_ui)"


def shift(side_expr):
    return (("!query.is_in_ui ? { " + TURN + "}; " if side_expr == "both" else "")
            + "v.nb_sh_on = 0.0; "
            + f"return {ON} ? -({'(v.nb_sws ?? 1.0)' if side_expr == 'both' else side_expr}) * 0.8 * 17.0667 : 0.0;")


def anim(side_expr):
    return {
        "format_version": "1.8.0",
        "animations": {
            "animation.humanoid.base_pose": {
                "loop": True,
                "bones": {
                    "waist": {"rotation": [0.0, 0.0, 0.0]},
                    "root": {"position": [shift(side_expr), 0.0, 0.0]},
                },
            }
        },
    }


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    subs = [("left", "Character left", "1.0"), ("right", "Character right", "-1.0"),
            ("both", "Both - follows the camera", "both"), ("off", "Off", None)]
    for folder, _, side in subs:
        d = os.path.join(OUT, "subpacks", folder)
        os.makedirs(d)
        if side is None:
            open(os.path.join(d, "README.txt"), "w").write("Shoulder view switched off.\n")
            continue
        os.makedirs(os.path.join(d, "animations"))
        json.dump(anim(side), open(os.path.join(d, "animations", "nabd_shoulder_view.animation.json"), "w"), indent=2)
        os.makedirs(os.path.join(d, "ui"))
        shutil.copy(SRC_UI, os.path.join(d, "ui", "hud_crosshair_overlay.json"))
        os.makedirs(os.path.join(d, "textures", "ui"))
        shutil.copy(SRC_CROSS, os.path.join(d, "textures", "ui", "nabd_cross.png"))
    manifest = {
        "format_version": 2,
        "header": {
            "name": "Nabd Shoulder View",
            "description": "Third person with your character to the side and a crosshair in the middle. Only the camera view - nothing else changes. Pick Left / Right / Both / Off with the pack slider.",
            "uuid": HEADER_UUID,
            "version": [1, 0, int(os.environ.get("NABD_BUILD", "1"))],
            "min_engine_version": [1, 21, 0],
        },
        "modules": [{"type": "resources", "uuid": MODULE_UUID, "version": [1, 0, int(os.environ.get("NABD_BUILD", "1"))]}],
        "subpacks": [{"folder_name": f, "name": n, "memory_tier": 0} for f, n, _ in subs],
        "metadata": {"authors": ["Nabd"]},
    }
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)
    if os.path.exists(ICON):
        shutil.copy(ICON, os.path.join(OUT, "pack_icon.png"))
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in os.walk(OUT):
            for f in sorted(fs):
                p = os.path.join(d, f)
                z.write(p, os.path.relpath(p, OUT))
    print("wrote", ZIP)


if __name__ == "__main__":
    main()
