"""يغلف المود بملف واحد .mcaddon  (يحافظ على الـ UUID الموجودة، ما يولد جديدة).

الاستعمال (من أي مكان):
    python3 tools/package.py            # يفحص ثم يغلف إلى dist/Etheria_V1.mcaddon (الاسم العام للنسخة، والرقم الداخلي بالمانيفست)
    python3 tools/package.py --no-check # يتخطى الفحص
    python3 tools/package.py -o اسم.mcaddon

البنية داخل الملف: SH_BP/ و SH_RP/ وكل واحد منهم منفستة بجذره.
"""
import argparse
import json
import os
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "AnimePowers")
PACKS = (("BP", "SH_BP"), ("RP", "SH_RP"))
SKIP_DIRS = {"__pycache__", ".git", "node_modules"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}
FIXED_TIME = (2020, 1, 1, 0, 0, 0)  # حتى يطلع الملف نفسه لنفس المحتوى


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    if not args.no_check:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check.py")])
        if r.returncode != 0:
            print("وقفت التغليف بسبب أخطاء الفحص.")
            return 1

    with open(os.path.join(SRC, "BP", "manifest.json"), encoding="utf-8") as f:
        ver = ".".join(str(n) for n in json.load(f)["header"]["version"])
    out = args.out or os.path.join(ROOT, "dist", "Etheria_V1.mcaddon")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, arc_root in PACKS:
            base = os.path.join(SRC, folder)
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
                for fn in sorted(filenames):
                    if fn in SKIP_FILES or fn.endswith(".pyc"):
                        continue
                    full = os.path.join(dirpath, fn)
                    arc = arc_root + "/" + os.path.relpath(full, base).replace(os.sep, "/")
                    info = zipfile.ZipInfo(arc, FIXED_TIME)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    with open(full, "rb") as fh:
                        z.writestr(info, fh.read())
                    count += 1
    print(f"تم: {os.path.relpath(out, ROOT)}  ({count} ملف، {os.path.getsize(out) / 1024:.0f} KB، نسخة {ver})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
