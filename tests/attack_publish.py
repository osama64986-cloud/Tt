"""Red-team the server-side validator with malicious admin requests.

Run:  python3 -I tests/attack_publish.py . /tmp/redteam-work
Every line must say BLOCKED.
"""
import json, os, pathlib, shutil, subprocess, sys, zipfile, io
REPO_DIR = pathlib.Path(sys.argv[1]); W = pathlib.Path(sys.argv[2])
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 64
ZIP = io.BytesIO(); zipfile.ZipFile(ZIP, "w").writestr("a", "b"); ZIP = ZIP.getvalue()
GOOD = {"name": "Ok", "type": "mod", "edition": "java", "versions": ["1.21"], "description": "d"}

def run(name, meta, files=None, expect_fail=True, check=None, seed=None):
    site = W / "site"; shutil.rmtree(site, ignore_errors=True)
    shutil.copytree(REPO_DIR, site, ignore=shutil.ignore_patterns(".git"))
    db = json.loads((site / "mods.json").read_text()); db["mods"] = seed or []
    (site / "mods.json").write_text(json.dumps(db))
    inbox = W / "inbox"; shutil.rmtree(inbox, ignore_errors=True); inbox.mkdir()
    (inbox / "meta.json").write_text(json.dumps(meta) if not isinstance(meta, str) else meta)
    for rel, data in (files or {}).items():
        p = inbox / rel; p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, tuple): os.symlink(data[1], p)
        else: p.write_bytes(data)
    r = subprocess.run([sys.executable, str(site / "scripts/publish.py")], capture_output=True, text=True,
                       env={**os.environ, "INBOX_DIR": str(inbox), "SITE_ROOT": str(site), "REPO": "o/r", "DRY_RUN": "1"})
    failed = r.returncode != 0
    db = json.loads((site / "mods.json").read_text())
    ok = failed == expect_fail and (check(db, r.stdout) if check else True)
    print(("BLOCKED " if ok else "!!! VULNERABLE ") + name + ("" if ok else f"\n{r.stdout}{r.stderr}"))
    return ok

res = []
res.append(run("path traversal in fileName", {"action": "upsert", "id": "x", "isNew": True, "entry": GOOD, "fileName": "../../mods.json"}))
res.append(run("bad id ../..", {"action": "upsert", "id": "../../etc", "entry": GOOD, "external": {"url": "https://a.b"}}))
res.append(run("XSS in id", {"action": "upsert", "id": "<script>", "entry": GOOD, "external": {"url": "https://a.b"}}))
res.append(run("meta not object", "[1,2,3]"))
res.append(run("broken json", "{not json"))
res.append(run("unknown action", {"action": "rm -rf /"}))
res.append(run("fake type", {"action": "upsert", "id": "x", "isNew": True, "entry": {**GOOD, "type": "<script>"}, "external": {"url": "https://a.b"}}))
res.append(run("javascript: link", {"action": "upsert", "id": "x", "isNew": True, "entry": GOOD, "external": {"url": "javascript:alert(1)"}}))
res.append(run("attribute-breaking link", {"action": "upsert", "id": "x", "isNew": True, "entry": GOOD, "external": {"url": "https://a.b/\" onmouseover=\"alert(1)"}}))
res.append(run(".exe upload", {"action": "upsert", "id": "x", "isNew": True, "entry": GOOD, "fileName": "game.jar.exe"}, {"files/game.jar.exe": b"MZ" + b"\0" * 99}))
res.append(run(".exe renamed to .jar", {"action": "upsert", "id": "x", "isNew": True, "entry": GOOD, "fileName": "a.jar"}, {"files/a.jar": b"MZ" + b"\0" * 99}))
res.append(run("symlink cover -> /etc/passwd", {"action": "upsert", "id": "x", "isNew": True, "entry": GOOD, "fileName": "a.jar", "cover": True}, {"files/a.jar": ZIP, "images/cover.webp": ("link", "/etc/passwd")}))
res.append(run("symlink file -> mods.json", {"action": "upsert", "id": "x", "isNew": True, "entry": GOOD, "fileName": "a.jar"}, {"files/a.jar": ("link", str(W / "site" / "mods.json"))}))
res.append(run("cover is not an image", {"action": "upsert", "id": "x", "isNew": True, "entry": GOOD, "fileName": "a.jar", "cover": True}, {"files/a.jar": ZIP, "images/cover.webp": b"<svg onload=alert(1)>"}))
res.append(run("overwrite existing id as new", {"action": "upsert", "id": "x", "isNew": True, "entry": GOOD, "external": {"url": "https://a.b"}}, seed=[{"id": "x", "name": "old", "file": "https://a"}]))
res.append(run("delete missing item", {"action": "delete", "id": "nope"}))
res.append(run("settings javascript: link", {"action": "settings", "site": {"youtube": "javascript:alert(1)"}}))
res.append(run("settings verify tag injection", {"action": "settings", "site": {"googleVerify": "\"><script>alert(1)</script>"}}))
# These are accepted, but the dangerous parts must be neutralised:
res.append(run("junk fields neutralised", {"action": "upsert", "id": "x", "isNew": True, "external": {"url": "https://a.b"}, "screenshots": 1000,
    "entry": {**GOOD, "name": "A" * 10000 + "‮\u0000", "video": "\"><script>", "color": "red;background:url(x)", "versions": ["1.21", "<b>x</b>"], "featured": "yes", "evil": "x"}},
    expect_fail=False, check=lambda db, out: (m := db["mods"][0]) and len(m["name"]) == 80 and "‮" not in m["name"] and m["video"] == ""
        and m["color"] == "#5d9c3b" and m["versions"] == ["1.21"] and m["featured"] is False and "evil" not in m and "screenshots" not in m))
res.append(run("flag injection via name", {"action": "upsert", "id": "x", "isNew": True, "entry": {**GOOD, "name": "--repo=evil/x"}, "fileName": "a.jar"}, {"files/a.jar": ZIP},
    expect_fail=False, check=lambda db, out: "--title=--repo=evil/x" in out and " --repo=o/r" in out))
print(f"\n{sum(res)}/{len(res)} attacks blocked")
