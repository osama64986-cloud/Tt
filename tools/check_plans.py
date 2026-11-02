"""فحص أسماء البلوكات بكل البنايات (القرية، القصر، الخرائب، المعبد، الضريحين): كل اسم لازم يكون موجود بقائمة Mojang الرسمية
(tools/vanilla_block_ids.txt). الاسم الغلط ما ينحط باللعبة (يفشل بصمت)، مثل dirt_path (اسمه grass_path بـBedrock) وchain (iron_chain).
التشغيل: python3 tools/check_plans.py  (يشغله tools/check.py)"""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS = set(open(os.path.join(ROOT, "tools", "vanilla_block_ids.txt"), encoding="utf-8").read().split())


def main():
    out = tempfile.mkdtemp(prefix="shplans-")
    r = subprocess.run(["node", os.path.join(ROOT, "tools", "sim", "dump_plans.mjs"), out], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(r.stdout, r.stderr); sys.exit(1)
    bad = {}
    for f in sorted(os.listdir(out)):
        plan = json.load(open(os.path.join(out, f)))
        for op in plan["ops"]:
            for v in op:
                if isinstance(v, str) and v.startswith("minecraft:") and v not in IDS:
                    bad.setdefault(f, set()).add(v)
    if bad:
        for f, s in bad.items():
            print(f"بلوكات مو موجودة بـBedrock بـ {f}: {sorted(s)}")
        sys.exit(1)
    print("أسماء البلوكات بكل البنايات صحيحة")


if __name__ == "__main__":
    main()
