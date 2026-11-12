#!/usr/bin/env python3
"""Apply one admin request (inbox/meta.json + files) to the site.

Runs inside the "publish" GitHub Actions workflow. Everything coming from the
inbox is treated as untrusted input and validated here, so a broken or
malicious request can never write anything unexpected into mods.json.

Env:
  INBOX_DIR  directory that contains meta.json, files/, images/
  REPO       owner/repo (for release download URLs)
  SITE_ROOT  site checkout (default: current directory)
  DRY_RUN=1  print gh commands instead of running them (local testing)
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata

ROOT = pathlib.Path(os.environ.get("SITE_ROOT", ".")).resolve()
INBOX = pathlib.Path(os.environ["INBOX_DIR"]).resolve()
REPO = os.environ.get("REPO", "")
DRY = os.environ.get("DRY_RUN") == "1"

TYPES = {"mod", "addon", "texture", "shader", "map", "world"}
EDITIONS = {"java", "bedrock"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HTTPS_RE = re.compile(r"^https://[^\s\"'<>\\`]+$", re.I)
SITE_FIELDS = {"name": 60, "author": 60, "tagline": 160, "about": 600}
SITE_LINKS = ("donate", "youtube", "discord", "tiktok", "website")
MAX_FILE = 100 * 1024 * 1024
MAX_IMAGE = 5 * 1024 * 1024
# Only Minecraft content. Executables and scripts are refused even if the token leaks.
ALLOWED_EXT = {"jar", "zip", "mcaddon", "mcpack", "mcworld", "mctemplate", "7z", "rar"}
ZIP_EXT = {"jar", "zip", "mcaddon", "mcpack", "mcworld", "mctemplate"}


class Invalid(Exception):
    pass


def text(value, limit, multiline=False):
    """Plain text only: strip control/invisible chars, collapse spaces, cap length."""
    s = unicodedata.normalize("NFC", str(value or ""))
    keep = []
    for ch in s:
        cat = unicodedata.category(ch)
        if ch == "\n" and multiline:
            keep.append(ch)
        elif cat in ("Cc", "Cs", "Co", "Cn") or (cat == "Cf" and ch not in "‌‍"):
            keep.append(" " if ch in "\t\r\n" else "")
        else:
            keep.append(ch)
    s = "".join(keep)
    s = re.sub(r"[ \t]+", " ", s)
    if multiline:
        s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()[:limit]


def text_list(values, limit_each, max_items):
    if not isinstance(values, list):
        return []
    out = []
    for v in values:
        t = text(v, limit_each)
        if t and t not in out:
            out.append(t)
    return out[:max_items]


def safe_filename(name):
    base = pathlib.PurePosixPath(str(name)).name
    stem, dot, ext = base.rpartition(".")
    if not dot:
        stem, ext = base, ""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", unicodedata.normalize("NFKD", stem)).strip("-.") or "file"
    ext = re.sub(r"[^A-Za-z0-9]", "", ext)[:12]
    return f"{stem[:80]}.{ext}" if ext else stem[:80]


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def image_ext(path):
    head = path.read_bytes()[:12]
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if head[:3] == b"\xff\xd8\xff":
        return "jpg"
    raise Invalid(f"{path.name} is not a valid image")


def gh(*args):
    if DRY:
        print("[dry-run] gh", *args)
        return ""
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def inbox_file(rel):
    """Resolve a path inside the inbox, refusing anything that escapes it."""
    p = (INBOX / rel).resolve()
    if INBOX not in p.parents or not p.is_file() or p.is_symlink():
        raise Invalid(f"missing or invalid inbox file: {rel}")
    return p


def load_db():
    with open(ROOT / "mods.json", encoding="utf-8") as f:
        db = json.load(f)
    db.setdefault("site", {})
    db.setdefault("mods", [])
    return db


def save_db(db):
    with open(ROOT / "mods.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        f.write("\n")


def clean_entry(raw):
    if not isinstance(raw, dict):
        raise Invalid("entry must be an object")
    e = {
        "name": text(raw.get("name"), 80),
        "type": raw.get("type") if raw.get("type") in TYPES else None,
        "edition": raw.get("edition") if raw.get("edition") in EDITIONS else None,
        "loader": text(raw.get("loader"), 40),
        "versions": [v for v in text_list(raw.get("versions"), 20, 12) if re.fullmatch(r"[0-9A-Za-z.\-+ ]+", v)],
        "version": text(raw.get("version"), 30),
        "description": text(raw.get("description"), 200),
        "details": text(raw.get("details"), 4000, multiline=True),
        "tags": text_list(raw.get("tags"), 30, 10),
        "video": raw.get("video") if re.fullmatch(r"[\w-]{11}", str(raw.get("video") or "")) else "",
        "color": raw.get("color") if re.fullmatch(r"#[0-9a-fA-F]{6}", str(raw.get("color") or "")) else "#5d9c3b",
        "featured": raw.get("featured") is True,
    }
    if not e["name"] or not e["type"] or not e["edition"] or not e["versions"] or not e["description"]:
        raise Invalid("name, type, edition, versions and description are required")
    return e


def upsert(db, meta, log):
    item_id = str(meta.get("id") or "")
    if not ID_RE.fullmatch(item_id) or len(item_id) > 50:
        raise Invalid("bad id")
    mods = db["mods"]
    current = next((m for m in mods if m.get("id") == item_id), None)
    if meta.get("isNew") is True and current:
        raise Invalid(f"id '{item_id}' already exists")
    entry = clean_entry(meta.get("entry"))
    today = dt.date.today().isoformat()
    item = dict(current or {"id": item_id, "date": today, "releases": [], "changelog": []})
    item.update(entry)
    item["id"] = item_id

    # --- the downloadable file ---
    ext = meta.get("external")
    file_name = meta.get("fileName")
    if ext:
        url = str(ext.get("url") or "")
        if not HTTPS_RE.fullmatch(url) or len(url) > 500:
            raise Invalid("external link must be https://")
        item.update(file=url, external=True, size=text(ext.get("size"), 20), updated=today)
        item.pop("sha256", None)
    elif file_name:
        src = inbox_file(f"files/{pathlib.PurePosixPath(str(file_name)).name}")
        if src.stat().st_size > MAX_FILE:
            raise Invalid("file too large")
        asset = safe_filename(file_name)
        ext_name = asset.rpartition(".")[2].lower() if "." in asset else ""
        if ext_name not in ALLOWED_EXT:
            raise Invalid(f"file type .{ext_name} is not allowed ({', '.join(sorted(ALLOWED_EXT))})")
        head = src.read_bytes()[:8] if src.stat().st_size else b""
        if ext_name in ZIP_EXT and not head.startswith(b"PK"):
            raise Invalid(f".{ext_name} file is not a valid zip archive")
        digest = hashlib.sha256()
        with open(src, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        staged = INBOX / "upload" / asset
        staged.parent.mkdir(exist_ok=True)
        shutil.copyfile(src, staged)
        tag = f"{item_id}-{dt.datetime.now(dt.timezone.utc):%Y%m%d%H%M%S}"
        notes = f"{entry['name']} {entry['version']}".strip()
        if meta.get("changelogNote"):
            notes += "\n\n" + text(meta.get("changelogNote"), 200)
        # "--flag=value" so user text can never be parsed as another flag.
        gh("release", "create", tag, str(staged), f"--repo={REPO}", "--target=main",
           f"--title={notes.splitlines()[0][:100]}", f"--notes={notes}")
        item.update(
            file=f"https://github.com/{REPO}/releases/download/{tag}/{asset}",
            size=human_size(src.stat().st_size),
            external=False,
            updated=today,
            sha256=digest.hexdigest(),
        )
        item["releases"] = [tag] + [t for t in item.get("releases", []) if t != tag]
        log.append(f"release {tag} ({asset})")
    elif not current or not item.get("file"):
        raise Invalid("a file or an external link is required")

    # --- images ---
    img_dir = ROOT / "images" / item_id
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
    if meta.get("cover") is True:
        src = inbox_file("images/cover.webp")
        if src.stat().st_size > MAX_IMAGE:
            raise Invalid("cover too large")
        img_dir.mkdir(parents=True, exist_ok=True)
        dest = img_dir / f"cover-{stamp}.{image_ext(src)}"
        shutil.copyfile(src, dest)
        item["image"] = dest.relative_to(ROOT).as_posix()
    shots = meta.get("screenshots")
    if isinstance(shots, int) and 0 < shots <= 6:
        img_dir.mkdir(parents=True, exist_ok=True)
        out = []
        for i in range(1, shots + 1):
            src = inbox_file(f"images/shot-{i}.webp")
            if src.stat().st_size > MAX_IMAGE:
                raise Invalid("screenshot too large")
            dest = img_dir / f"shot-{stamp}-{i}.{image_ext(src)}"
            shutil.copyfile(src, dest)
            out.append(dest.relative_to(ROOT).as_posix())
        item["screenshots"] = out
    if img_dir.is_dir():  # drop images that are no longer referenced
        keep = {item.get("image")} | set(item.get("screenshots") or [])
        for f in img_dir.iterdir():
            if f.relative_to(ROOT).as_posix() not in keep:
                f.unlink()

    note = text(meta.get("changelogNote"), 200)
    if note:
        label = f"{entry['version']} — {note}" if entry["version"] else note
        item["changelog"] = ([label] + list(item.get("changelog") or []))[:30]

    if current:
        mods[mods.index(current)] = item
    else:
        mods.insert(0, item)
    log.append(f"{'updated' if current else 'added'} {item_id}")


def delete(db, meta, log):
    item_id = str(meta.get("id") or "")
    if not ID_RE.fullmatch(item_id):
        raise Invalid("bad id")
    item = next((m for m in db["mods"] if m.get("id") == item_id), None)
    if not item:
        raise Invalid(f"'{item_id}' not found")
    for tag in item.get("releases") or []:
        if re.fullmatch(rf"{re.escape(item_id)}-\d{{14}}", str(tag)):
            try:
                gh("release", "delete", tag, f"--repo={REPO}", "--yes", "--cleanup-tag")
                log.append(f"deleted release {tag}")
            except subprocess.CalledProcessError as exc:
                log.append(f"could not delete release {tag}: {exc.stderr.strip()}")
    shutil.rmtree(ROOT / "images" / item_id, ignore_errors=True)
    db["mods"].remove(item)
    log.append(f"deleted {item_id}")


def settings(db, meta, log):
    raw = meta.get("site")
    if not isinstance(raw, dict):
        raise Invalid("site must be an object")
    site = db["site"]
    for key, limit in SITE_FIELDS.items():
        site[key] = text(raw.get(key), limit, multiline=(key == "about"))
    for key in SITE_LINKS:
        url = str(raw.get(key) or "").strip()
        if url and (not HTTPS_RE.fullmatch(url) or len(url) > 300):
            raise Invalid(f"{key} must be an https:// link")
        site[key] = url
    verify = str(raw.get("googleVerify") or "").strip()
    if verify and not re.fullmatch(r"[A-Za-z0-9_-]{10,100}", verify):
        raise Invalid("googleVerify must be the code only (letters, digits, - and _)")
    site["googleVerify"] = verify
    if REPO:
        site["repo"] = REPO
    log.append("updated site settings")


def main():
    try:
        meta = json.loads(inbox_file("meta.json").read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            raise Invalid("meta.json must be an object")
        db = load_db()
        log = []
        action = meta.get("action")
        if action == "upsert":
            upsert(db, meta, log)
        elif action == "delete":
            delete(db, meta, log)
        elif action == "settings":
            settings(db, meta, log)
        else:
            raise Invalid(f"unknown action {action!r}")
        if REPO and not db["site"].get("repo"):
            db["site"]["repo"] = REPO
        save_db(db)
    except (Invalid, ValueError) as exc:  # ValueError covers broken JSON
        print(f"::error::Rejected: {exc}")
        sys.exit(1)
    summary = "\n".join(f"- {line}" for line in log)
    print(summary)
    (ROOT / ".commit-msg").write_text(f"admin: {'; '.join(log)}\n", encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary + "\n")


if __name__ == "__main__":
    main()
