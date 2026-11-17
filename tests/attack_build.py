"""Red-team the site builder (scripts/build.py).

Run:  python3 -I tests/attack_build.py . /tmp/redteam-build
Every line must say BLOCKED.
"""
import importlib.util, json, os, pathlib, shutil, subprocess, sys
REPO_DIR = pathlib.Path(sys.argv[1]).resolve(); W = pathlib.Path(sys.argv[2]).resolve()
res = []
def report(name, ok, extra=""):
    print(("BLOCKED " if ok else "!!! VULNERABLE ") + name + ("" if ok else "\n" + extra)); res.append(ok)

def fresh_site(mods=None):
    site = W / "site"; shutil.rmtree(site, ignore_errors=True)
    shutil.copytree(REPO_DIR, site, ignore=shutil.ignore_patterns(".git", "_site", "__pycache__"))
    if mods is not None:
        db = json.loads((site / "mods.json").read_text()); db["mods"] = mods
        (site / "mods.json").write_text(json.dumps(db))
    return site

def build(site):
    env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "REPO")}
    env.update(OUT=str(W / "out"), REPO="")
    return subprocess.run([sys.executable, "-I", str(site / "scripts/build.py")], capture_output=True, text=True, env=env)

# 1. a symlink under images/ must stop the build (it could publish a file from the build machine)
site = fresh_site()
(site / "images" / "leak.txt").symlink_to("/etc/hostname")
r = build(site)
report("symlink under images/ refuses to build", r.returncode != 0 and not (W / "out" / "images" / "leak.txt").exists(), r.stdout + r.stderr)

# 2. symlinked folder
site = fresh_site()
(site / "images" / "dir").symlink_to(site / "scripts", target_is_directory=True)
r = build(site)
report("symlinked folder under images/ refuses to build", r.returncode != 0, r.stdout + r.stderr)

# 3. draft and unknown releases never reach stats.json
spec = importlib.util.spec_from_file_location("b", REPO_DIR / "scripts" / "build.py"); b = importlib.util.module_from_spec(spec)
os.environ["OUT"] = str(W / "unused"); spec.loader.exec_module(b)
class Fake:
    def __init__(self, data): self.data = json.dumps(data).encode()
    def read(self, *a): return self.data
    def __enter__(self): return self
    def __exit__(self, *a): return False
b.REPO = "o/r"
b.urllib.request.urlopen = lambda req, timeout=0: Fake([
    {"tag_name": "pub-20260101000000", "draft": False, "assets": [{"download_count": 5}]},
    {"tag_name": "draft-secret", "draft": True, "assets": []},
    {"tag_name": "not-in-mods", "draft": False, "assets": [{"download_count": 1}]}])
out = b.fetch_stats({"pub-20260101000000", "draft-secret"})
report("draft / unknown releases are not published in stats.json", out == {"pub-20260101000000": 5}, str(out))

# 4. percent-encoded dot segments are rejected
report("safe_url rejects %2e%2e/", b.safe_url("%2e%2e/%2E%2E/other/x.png") == "" and b.safe_url("images/a/b.png") == "images/a/b.png")

# 5. a normal build still works and publishes only public files
site = fresh_site([{"id": "ok", "name": "Ok", "type": "mod", "edition": "java", "versions": ["26.3"], "description": "d", "file": "https://a.b/x.jar"}])
r = build(site)
files = sorted(str(p.relative_to(W / "out")) for p in (W / "out").rglob("*") if p.is_file())
bad = [f for f in files if f.endswith((".py", ".pyc", ".yml", ".md")) or f.startswith((".git/", "scripts/", "tests/"))]
report("normal build works and publishes only public files", r.returncode == 0 and "m/ok/index.html" in files and "terms.html" in files and not bad, r.stdout + r.stderr + str(bad))

print(f"\n{sum(res)}/{len(res)} attacks blocked")
sys.exit(0 if all(res) else 1)
