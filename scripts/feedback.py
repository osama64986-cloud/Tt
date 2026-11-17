#!/usr/bin/env python3
"""Approve or remove visitor feedback (GitHub issues made from the feedback form).

Runs in .github/workflows/feedback.yml. Everything in the event is untrusted except
the facts GitHub itself sets (who wrote the comment, their association). Nothing is
shown on the site until the REPOSITORY OWNER comments a command on the issue:

    /approve  (or: موافق)  -> snapshot the issue into feedback.json
    /remove   (or: احذف)   -> remove it from feedback.json

A snapshot is taken at approval time, so editing the issue later changes nothing on
the site. Output is plain validated data; pages escape it again when rendering.

Env: GITHUB_EVENT_PATH, GITHUB_EVENT_NAME, GITHUB_REPOSITORY_OWNER (set by Actions),
     SITE_ROOT (default: current directory).
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(os.environ.get("SITE_ROOT", ".")).resolve()
DB = ROOT / "feedback.json"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
KINDS = {"👍 شي عجبني": "pro", "👎 شي ما عجبني": "con", "🐞 مشكلة أو خطأ": "bug", "💡 اقتراح": "idea"}
DEVICES = {"📱 جوال": "phone", "💻 كمبيوتر": "pc", "🎮 كونسول": "console"}
LABELS = {"العمل": "mod", "نوع الرأي": "kind", "رأيك": "text", "جهازك": "device"}
APPROVE = {"/approve", "موافق"}
REMOVE = {"/remove", "احذف"}
MAX_TEXT = 600
MAX_PER_MOD = 50
MAX_TOTAL = 2000


class Stop(Exception):
    """Not an error: nothing to do (e.g. a normal comment)."""


class Invalid(Exception):
    pass


def text(value, limit):
    """Plain single-paragraph text: no control/invisible characters, collapsed spaces."""
    s = unicodedata.normalize("NFC", str(value or ""))
    out = []
    for ch in s:
        cat = unicodedata.category(ch)
        if ch in "\n\r\t":
            out.append(" ")
        elif cat in ("Cc", "Cs", "Co", "Cn") or (cat == "Cf" and ch not in "\u200c\u200d"):
            continue
        elif cat == "Mn" and len(out) >= 2 and all(unicodedata.category(c) == "Mn" for c in out[-2:]):
            continue  # at most 2 stacked marks (no "zalgo" text)
        else:
            out.append(ch)
    return re.sub(r"\s+", " ", "".join(out)).strip()[:limit]


# Markdown/HTML that GitHub hides or disguises when it shows an issue. The owner must see
# exactly what will be published, so feedback containing any of it is refused.
HIDDEN_RE = re.compile(r"[<>]|\]\(|^\s*\[[^\]]*\]:|&#|&[a-z]+;", re.I | re.M)


def safe_msg(value, limit=200):
    return re.sub(r"[\x00-\x1f\x7f-\x9f  ]", "?", str(value))[:limit]


def parse_form(body):
    """Issue-form body ('### Label\\n\\nvalue' blocks) -> {field: value}. Unknown labels ignored;
    a label appearing twice is rejected (someone hand-crafting the body)."""
    fields, current, buf = {}, None, []
    for line in str(body or "").replace("\r\n", "\n").split("\n"):
        heading = LABELS.get(line[4:].strip()) if line.startswith("### ") else None
        # Inside the free-text field only the next form label ("### جهازك") ends it, so
        # a visitor's own "### ..." lines stay part of their text instead of cutting it.
        if current == "text" and heading != "device":
            heading = None
        if heading or (line.startswith("### ") and current != "text"):
            if current:
                fields[current] = "\n".join(buf).strip()
            if heading and heading in fields:
                raise Invalid("duplicate form field")
            current, buf = heading, []
        elif current:
            buf.append(line)
    if current:
        fields[current] = "\n".join(buf).strip()
    return {k: ("" if v == "_No response_" else v) for k, v in fields.items()}


def load_db():
    try:
        db = json.loads(DB.read_text(encoding="utf-8"))
    except FileNotFoundError:
        db = {"items": []}
    if not isinstance(db, dict) or not isinstance(db.get("items"), list):
        raise Invalid("feedback.json is malformed")
    db["items"] = [i for i in db["items"] if isinstance(i, dict)]
    return db


def save_db(db):
    DB.write_text(json.dumps(db, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def mod_ids():
    mods = json.loads((ROOT / "mods.json").read_text(encoding="utf-8")).get("mods") or []
    return {m["id"] for m in mods if isinstance(m, dict) and ID_RE.fullmatch(str(m.get("id") or ""))}


def main():
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    ev = json.loads(pathlib.Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    if not isinstance(ev, dict):
        raise Stop("bad event")
    issue = ev.get("issue") if isinstance(ev.get("issue"), dict) else {}
    number = issue.get("number")
    if type(number) is not int or number < 1:
        raise Stop("no issue number")
    db = load_db()

    if event_name == "issues":
        if ev.get("action") not in ("deleted", "transferred"):
            raise Stop("issue event ignored")
        before = len(db["items"])
        db["items"] = [i for i in db["items"] if i.get("n") != number]
        if len(db["items"]) == before:
            raise Stop("deleted issue was not on the site")
        save_db(db)
        return f"removed #{number} (issue deleted)"

    if event_name != "issue_comment" or ev.get("action") != "created":
        raise Stop("event ignored")
    if issue.get("pull_request"):
        raise Stop("pull request comment ignored")
    comment = ev.get("comment") if isinstance(ev.get("comment"), dict) else {}
    author = (comment.get("user") if isinstance(comment.get("user"), dict) else {}).get("login", "")
    # Only the repository owner can approve; double-checked with GitHub's own association.
    if not owner or author != owner or comment.get("author_association") != "OWNER":
        raise Stop("comment is not from the owner")
    command = str(comment.get("body") or "").strip()
    if command in REMOVE:
        before = len(db["items"])
        db["items"] = [i for i in db["items"] if i.get("n") != number]
        if len(db["items"]) == before:
            raise Stop("not on the site")
        save_db(db)
        return f"removed #{number}"
    if command not in APPROVE:
        raise Stop("not a command")

    f = parse_form(issue.get("body"))
    if "mod" not in f or "kind" not in f or "text" not in f:
        raise Invalid("this issue was not made with the feedback form")
    mod = text(f.get("mod"), 50).lower()
    if not ID_RE.fullmatch(mod) or mod not in mod_ids():
        raise Invalid("the mod in this feedback does not exist on the site (check the mod field)")
    kind = KINDS.get(text(f.get("kind"), 40))
    if not kind:
        raise Invalid("unknown feedback kind")
    raw_text = str(f.get("text") or "")
    if HIDDEN_RE.search(raw_text):
        raise Invalid("feedback contains HTML, hidden comments or link markup; only plain text can be published")
    body = text(raw_text, MAX_TEXT)
    if len(body) < 2:
        raise Invalid("empty feedback")
    user = (issue.get("user") if isinstance(issue.get("user"), dict) else {}).get("login", "")
    if not LOGIN_RE.fullmatch(str(user)):
        raise Invalid("bad user name")
    created = str(issue.get("created_at") or "")[:10]
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", created):
        created = dt.date.today().isoformat()
    item = {"n": number, "mod": mod, "kind": kind, "text": body, "user": user, "date": created}
    device = DEVICES.get(text(f.get("device"), 20))
    if device:
        item["device"] = device

    items = [i for i in db["items"] if i.get("n") != number]
    if sum(1 for i in items if i.get("mod") == mod) >= MAX_PER_MOD:
        raise Invalid(f"this mod already shows {MAX_PER_MOD} opinions; remove one first")
    items.insert(0, item)
    db["items"] = items[:MAX_TOTAL]
    save_db(db)
    # Show the owner exactly what went live (in a fence longer than any backtick run).
    reply = os.environ.get("CONFIRM_FILE")
    if reply:
        fence = "`" * max(3, max((len(r) for r in re.findall(r"`+", body)), default=0) + 1)
        pathlib.Path(reply).write_text(f"✅ انضاف للموقع بهذا النص بالضبط:\n\n{fence}text\n{body}\n{fence}\n\nإذا مو هذا اللي قريته، اكتب «احذف».\n", encoding="utf-8")
    return f"approved #{number} for {mod}"


def is_form_issue():
    """For the labelling job: was this new issue made with the feedback form?"""
    ev = json.loads(pathlib.Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    try:
        f = parse_form((ev.get("issue") or {}).get("body"))
    except Invalid:
        return False
    return all(k in f for k in ("mod", "kind", "text"))


if __name__ == "__main__" and sys.argv[1:] == ["--is-form"]:
    print("yes" if is_form_issue() else "no")
    sys.exit(0)

if __name__ == "__main__":
    try:
        msg = main()
        print(msg)
        pathlib.Path(ROOT / ".commit-msg").write_text(f"feedback: {msg}\n", encoding="utf-8")
    except Stop as s:
        print(f"skip: {safe_msg(s)}")
    except Exception as exc:  # any failure: clear message, no traceback details posted
        print(f"::error::Rejected: {safe_msg(exc)}")
        msg_file = os.environ.get("REPLY_FILE")
        if msg_file:
            pathlib.Path(msg_file).write_text(f"ما انضاف للموقع: {safe_msg(exc)}\n", encoding="utf-8")
        sys.exit(1)
