"""Red-team the visitor-feedback approval script (scripts/feedback.py) and its rendering.

Run:  python3 -I tests/attack_feedback.py . /tmp/redteam-feedback
Every line must say BLOCKED.
"""
import json, os, pathlib, shutil, subprocess, sys
REPO_DIR = pathlib.Path(sys.argv[1]).resolve(); W = pathlib.Path(sys.argv[2]).resolve()
OWNER = "osama64986-cloud"
XSS = '"><img src=x onerror=alert(1)><script>alert(2)</script>'
MODS = [{"id": "dragons", "name": "Dragons", "type": "addon", "edition": "bedrock", "versions": ["26.62"], "description": "d", "file": "https://a.b/x"}]

def form(mod="dragons", kind="👍 شي عجبني", text="حلو كلش", device="📱 جوال"):
    return f"### العمل\n\n{mod}\n\n### نوع الرأي\n\n{kind}\n\n### رأيك\n\n{text}\n\n### جهازك\n\n{device}"

def event(body=None, cbody="موافق", login=OWNER, assoc="OWNER", number=7, user="player-1", action="created", name="issue_comment", pr=False, **issue_extra):
    issue = {"number": number, "body": form() if body is None else body, "user": {"login": user}, "created_at": "2026-11-17T10:00:00Z", **issue_extra}
    if pr: issue["pull_request"] = {"url": "x"}
    ev = {"action": action, "issue": issue}
    if name == "issue_comment": ev["comment"] = {"id": 99, "body": cbody, "user": {"login": login}, "author_association": assoc}
    return name, ev

res = []
def run(title, ev_pair, expect_rc=0, check=None, seed=None, args=()):
    name, ev = ev_pair
    site = W / "site"; shutil.rmtree(site, ignore_errors=True); site.mkdir(parents=True)
    (site / "mods.json").write_text(json.dumps({"site": {}, "mods": MODS}))
    (site / "feedback.json").write_text(json.dumps({"items": seed or []}))
    evf = W / "event.json"; evf.write_text(json.dumps(ev, ensure_ascii=False))
    reply = W / "reply.txt"; reply.unlink(missing_ok=True)
    env = {"PATH": os.environ.get("PATH", ""), "GITHUB_EVENT_PATH": str(evf), "GITHUB_EVENT_NAME": name,
           "GITHUB_REPOSITORY_OWNER": OWNER, "SITE_ROOT": str(site), "REPLY_FILE": str(reply), "CONFIRM_FILE": str(W / "confirm.txt")}
    r = subprocess.run([sys.executable, "-I", str(REPO_DIR / "scripts" / "feedback.py"), *args], capture_output=True, text=True, env=env)
    db = json.loads((site / "feedback.json").read_text())
    ok = r.returncode == expect_rc and (check(db, r.stdout, reply) if check else True)
    print(("BLOCKED " if ok else "!!! VULNERABLE ") + title + ("" if ok else f"\n rc={r.returncode}\n{r.stdout}{r.stderr}\n{db}"))
    res.append(ok)

unchanged = lambda db, out, reply: db["items"] == []
run("stranger cannot approve", event(login="attacker", assoc="NONE"), check=unchanged)
run("collaborator-looking comment without OWNER association cannot approve", event(assoc="CONTRIBUTOR"), check=unchanged)
run("someone named like the owner but not OWNER cannot approve", event(login=OWNER, assoc="MEMBER"), check=unchanged)
run("comment on a pull request is ignored", event(pr=True), check=unchanged)
run("ordinary owner comment does nothing", event(cbody="شكراً على رأيك"), check=unchanged)
run("command must be the whole comment", event(cbody="موافق بس عدّل كذا"), check=unchanged)
run("edited issue events are ignored", event(name="issues", action="edited"), check=unchanged)
run("owner approval adds a clean snapshot", event(), check=lambda db, out, reply: db["items"] == [
    {"n": 7, "mod": "dragons", "kind": "pro", "text": "حلو كلش", "user": "player-1", "date": "2026-11-17", "device": "phone"}])
run("XSS / HTML text is refused at approval", event(body=form(text=XSS)), expect_rc=1, check=unchanged)
run("unknown mod is rejected with a reply", event(body=form(mod="nope")), expect_rc=1, check=lambda db, out, reply: unchanged(db, out, reply) and reply.read_text().startswith("ما انضاف"))
run("mod id with path tricks is rejected", event(body=form(mod="../mods")), expect_rc=1, check=unchanged)
run("fake kind is rejected", event(body=form(kind="⭐ admin")), expect_rc=1, check=unchanged)
run("free-form issue (not the form) is rejected", event(body="just text\n<script>"), expect_rc=1, check=unchanged)
run("duplicated form fields are rejected", event(body=form() + "\n\n### العمل\n\nother"), expect_rc=1, check=unchanged)
run("very long text is cut to 600 characters", event(body=form(text="أ" * 5000)), check=lambda db, out, reply: len(db["items"][0]["text"]) == 600)
run("control characters and newlines are removed", event(body=form(text="سطر‮\u0000\nثاني\r::warning::x")),
    check=lambda db, out, reply: "‮" not in db["items"][0]["text"] and "\n" not in db["items"][0]["text"] and "\n::" not in out)
run("newline in mod id cannot inject a workflow command", event(body=form(mod="nope\n::warning::INJECTED")), expect_rc=1,
    check=lambda db, out, reply: "\n::warning::" not in out)
run("weird user name is rejected", event(user="<b>x</b>"), expect_rc=1, check=unchanged)
run("bad issue number is ignored", event(number="7; rm -rf /"), check=unchanged)
run("unknown device is simply dropped", event(body=form(device="🛸 UFO")), check=lambda db, out, reply: "device" not in db["items"][0])
seed = [{"n": 7, "mod": "dragons", "kind": "pro", "text": "x", "user": "a", "date": "2026-11-17"}]
run("owner can remove", event(cbody="احذف"), check=unchanged, seed=seed)
run("deleting the issue removes it", event(name="issues", action="deleted"), check=unchanged, seed=seed)
run("approving twice does not duplicate", event(), seed=seed, check=lambda db, out, reply: len(db["items"]) == 1)
run("per-mod cap is enforced", event(number=500), expect_rc=1,
    seed=[{"n": i, "mod": "dragons", "kind": "pro", "text": "x", "user": "a", "date": "2026-11-17"} for i in range(1, 51)],
    check=lambda db, out, reply: len(db["items"]) == 50)
run("--is-form says yes for a form issue", ("issues", {"action": "opened", "issue": {"number": 1, "body": form()}}), args=("--is-form",),
    check=lambda db, out, reply: out.strip() == "yes")
run("--is-form says no for other issues", ("issues", {"action": "opened", "issue": {"number": 1, "body": "hello"}}), args=("--is-form",),
    check=lambda db, out, reply: out.strip() == "no")

# ---- added after the dedicated red-team review ----
for label, hidden in [("hidden HTML comment", "مود رهيب <!-- SPAM evil.example -->"), ("collapsed <details>", "حلو <details>buy evil</details>"),
                      ("markdown link with hidden address", "شوفوا [هنا](https://evil.example)"), ("invisible reference link", "حلو\n[a]: https://evil.example"),
                      ("HTML entity tricks", "حلو &#60;b&#62;"), ("named entity", "حلو &nbsp; evil")]:
    run(f"{label} cannot be approved", event(body=form(text=hidden)), expect_rc=1, check=unchanged)
run("visitor '### ' lines stay inside the text (no silent cut)", event(body=form(text="أول\n### ملاحظة\nثاني")),
    check=lambda db, out, reply: db["items"][0]["text"] == "أول ### ملاحظة ثاني")
run("rejection reply never echoes visitor text", event(body=form(mod="@everyone [x](https://evil.example)")), expect_rc=1,
    check=lambda db, out, reply: "@everyone" not in reply.read_text() and "evil" not in reply.read_text())
run("approve command must match exactly (no hidden characters)", event(cbody="موا\u200bفق"), check=unchanged)
run("event that is a JSON list is ignored safely", ("issue_comment", ["x"]), check=unchanged)
run("non-object items in feedback.json do not crash", event(), seed=["junk", 5], check=lambda db, out, reply: len(db["items"]) == 1)
run("non-ASCII digits in dates are not trusted", event(created_at="٢٠٢٦-١١-١٧T00:00:00Z"), check=lambda db, out, reply: db["items"][0]["date"].isascii())
run("transferred issue is removed", event(name="issues", action="transferred"), check=unchanged, seed=seed)
def confirm_ok(db, out, reply):
    c = (W / "confirm.txt")
    return c.exists() and "حلو ``` كلش" in c.read_text() and "````text" in c.read_text()
run("owner gets the exact published text back (fence longer than any backticks)", event(body=form(text="حلو ``` كلش")), check=confirm_ok)
# ---- rendering: a hostile feedback.json written by anyone with repo access ----
site = W / "build"; shutil.rmtree(site, ignore_errors=True)
shutil.copytree(REPO_DIR, site, ignore=shutil.ignore_patterns(".git", "_site", "__pycache__"))
(site / "mods.json").write_text(json.dumps({"site": {"repo": "o/r"}, "mods": MODS}))
(site / "feedback.json").write_text(json.dumps({"items": [
    {"n": 1, "mod": "dragons", "kind": "pro", "text": XSS, "user": "good-user", "date": "2026-11-17"},
    {"n": "2\" onmouseover=\"x", "mod": "dragons", "kind": "pro", "text": "bad n", "user": "u", "date": "2026-11-17"},
    {"n": 3, "mod": "dragons", "kind": "<script>", "text": "bad kind", "user": "u", "date": "2026-11-17"},
    {"n": 4, "mod": "other", "kind": "pro", "text": "unknown mod", "user": "u", "date": "2026-11-17"},
    {"n": 5, "mod": "dragons", "kind": "con", "text": "bad user", "user": "<x>", "date": "2026-11-17"},
    {"n": 6, "mod": "dragons", "kind": "bug", "text": "bad date", "user": "u", "date": "<x>"}]}))
env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "REPO")}; env.update(OUT=str(W / "out"), REPO="")
r = subprocess.run([sys.executable, "-I", str(site / "scripts" / "build.py")], capture_output=True, text=True, env=env)
page = (W / "out" / "m" / "dragons" / "index.html").read_text() if r.returncode == 0 else ""
pub = json.loads((W / "out" / "feedback.json").read_text()) if r.returncode == 0 else {}
ok = (r.returncode == 0 and "<img src=x" not in page and "<script>alert" not in page and "&lt;img src=x" in page
      and [i["n"] for i in pub.get("items", [])] == [1] and "issues/new?template=feedback.yml&amp;mod=dragons" in page)
print(("BLOCKED " if ok else "!!! VULNERABLE ") + "hostile feedback.json is filtered and escaped on item pages" + ("" if ok else f"\n{r.stdout}{r.stderr}"))
res.append(ok)

import importlib.util
def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO_DIR / "scripts" / f"{name}.py"); m = importlib.util.module_from_spec(spec)
    os.environ.setdefault("INBOX_DIR", str(W)); spec.loader.exec_module(m); return m
b, pub = load("build"), load("publish")
GOOD_FORMS = ["https://forms.gle/abc123", "https://docs.google.com/forms/d/e/x/viewform", "HTTPS://FORMS.GLE/x"]
BAD_FORMS = ["https://evil.com@forms.gle/x", "https://forms.gle:444/x", "https://docs.google.com/forms/../url?q=https://evil.com",
             "https://docs.google.com/forms/%2e%2e/url", "https://docs.google.com.evil/forms/x", "https://[forms.gle/x", "javascript:alert(1)//forms.gle",
             "http://forms.gle/x", "https://docs.google.com/document/x"]
same = all(b.google_form_ok(u) and pub.google_form_ok(u) for u in GOOD_FORMS) and not any(b.google_form_ok(u) or pub.google_form_ok(u) for u in BAD_FORMS)
print(("BLOCKED " if same else "!!! VULNERABLE ") + "Google Form rule is identical and strict in build.py and publish.py"); res.append(same)
print(f"\n{sum(res)}/{len(res)} attacks blocked")
sys.exit(0 if all(res) else 1)
