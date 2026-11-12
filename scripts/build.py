#!/usr/bin/env python3
"""Build the public site into _site/ (run by the Pages workflow).

- copies only public files
- one static page per item at m/<id>/ so Google can index each one
- sitemap.xml + robots.txt
- stats.json with download counts (so visitors never hit GitHub's API limits)

All values from mods.json are escaped; nothing is trusted.
Env: GH_TOKEN (optional, for stats), REPO (owner/repo), OUT (default _site)
"""
import datetime as dt
import html
import json
import os
import pathlib
import re
import shutil
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(os.environ.get("OUT", ROOT / "_site")).resolve()
REPO = os.environ.get("REPO", "")
PUBLIC = ["index.html", "admin.html", "404.html", "privacy.html", "mods.json", "assets", "images", "downloads"]
TYPES = {
    "mod": ("مود", "⚒"), "addon": ("إضافة بيدروك", "🧩"), "texture": ("تكستر", "🎨"),
    "shader": ("شيدر", "✨"), "map": ("خريطة", "🗺"), "world": ("عالم", "🌍"),
}
EDITIONS = {"java": "Java", "bedrock": "Bedrock"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.github.com; "
       "frame-src https://www.youtube-nocookie.com; object-src 'none'; base-uri 'self'; form-action 'none'")


def e(v):
    return html.escape(str(v if v is not None else ""), quote=True)


def safe_url(u):
    u = str(u or "").strip()
    if re.fullmatch(r"https://[^\s\"'<>\\`]+", u, re.I):
        return u
    if re.fullmatch(r"[\w\-./%]+", u) and not u.startswith("//") and ".." not in u:
        return u
    return ""


def base_url(site):
    repo = site.get("repo") if re.fullmatch(r"[\w.-]+/[\w.-]+", str(site.get("repo") or "")) else REPO
    owner, _, name = repo.partition("/")
    if name.lower() == f"{owner.lower()}.github.io":
        return f"https://{owner.lower()}.github.io/"
    return f"https://{owner.lower()}.github.io/{name}/"


SOCIALS = [("youtube", "يوتيوب", "▶", ("youtube.com", "youtu.be")), ("tiktok", "تيك توك", "♪", ("tiktok.com",)),
           ("instagram", "إنستغرام", "◎", ("instagram.com",)), ("discord", "ديسكورد", "💬", ("discord.gg", "discord.com"))]


def social_url(site, key):
    u = safe_url(site.get(key))
    hosts = next((h for k, _, _, h in SOCIALS if k == key), ())
    if not u.startswith("https://"):
        return ""
    host = (urllib.parse.urlsplit(u).hostname or "").lower()
    return u if any(host == h or host.endswith("." + h) for h in hosts) else ""


def socials_html(site):
    out = []
    for key, label, icon, _ in SOCIALS:
        u = social_url(site, key)
        out.append(f'<a class="social social-{key}" href="{e(u)}" target="_blank" rel="noopener noreferrer"><span aria-hidden="true">{icon}</span> {label}</a>'
                   if u else f'<span class="social social-{key} soon" title="قريباً"><span aria-hidden="true">{icon}</span> {label} <small>قريباً</small></span>')
    return "".join(out)


def fetch_stats():
    """Sum of asset downloads per release tag."""
    if not REPO:
        return {}
    out = {}
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "site-build"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    try:
        for page in range(1, 11):
            req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases?per_page=100&page={page}", headers=headers)
            with urllib.request.urlopen(req, timeout=20) as r:
                rels = json.load(r)
            for rel in rels:
                out[str(rel.get("tag_name"))] = sum(int(a.get("download_count") or 0) for a in rel.get("assets") or [])
            if len(rels) < 100:
                break
    except Exception as exc:  # stats are optional; never fail the deploy
        print(f"stats skipped: {exc}")
    return out


def fmt_num(n):
    return f"{n/1e6:.1f}M" if n >= 1e6 else f"{n/1e3:.1f}K" if n >= 1e3 else str(n)


def item_page(m, site, base, stats):
    t_label, t_icon = TYPES.get(m.get("type"), ("", "📦"))
    name, desc = m.get("name", ""), m.get("description", "")
    url = f"{base}m/{m['id']}/"
    img = safe_url(m.get("image"))
    img_abs = img if img.startswith("https://") else (base + img if img else "")
    og_img = img_abs or base + "assets/og.png"
    report = social_url(site, "discord") or social_url(site, "instagram")
    rel = lambda u: u if u.startswith("https://") else "../../" + u  # noqa: E731
    file = safe_url(m.get("file"))
    color = m.get("color") if re.fullmatch(r"#[0-9a-fA-F]{6}", str(m.get("color") or "")) else "#5d5d5d"
    versions = [str(v) for v in m.get("versions") or []]
    downloads = sum(stats.get(t, 0) for t in m.get("releases") or [])
    shots = [s for s in (safe_url(x) for x in m.get("screenshots") or []) if s]
    video = m.get("video") if re.fullmatch(r"[\w-]{11}", str(m.get("video") or "")) else ""
    sha = m.get("sha256") if re.fullmatch(r"[0-9a-f]{64}", str(m.get("sha256") or "")) else ""
    site_name = site.get("name") or "نبض"
    rows = [("النوع", t_label), ("النسخة", EDITIONS.get(m.get("edition"), "")), ("المحمّل / الصيغة", m.get("loader")),
            ("إصدارات ماين كرافت", "، ".join(versions)), ("إصدار الملف", m.get("version")), ("الحجم", m.get("size")),
            ("التحميلات", fmt_num(downloads) if downloads else ""), ("تاريخ النشر", m.get("date")),
            ("آخر تحديث", m.get("updated") if m.get("updated") != m.get("date") else "")]
    ld = {
        "@context": "https://schema.org", "@type": "SoftwareApplication", "name": name, "description": desc,
        "applicationCategory": "GameApplication", "operatingSystem": "Minecraft " + EDITIONS.get(m.get("edition"), ""),
        "softwareVersion": m.get("version") or None, "url": url, "image": img_abs or None,
        "datePublished": m.get("date") or None, "dateModified": m.get("updated") or None,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "author": {"@type": "Person", "name": site.get("author") or site_name},
    }
    ld = {k: v for k, v in ld.items() if v}
    ld_json = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    title = f"تحميل {name} — {t_label} ماين كرافت {EDITIONS.get(m.get('edition'), '')} {versions[0] if versions else ''}".strip()
    share = urllib.parse.quote(f"{name} — {url}", safe="")
    details = e(m.get("details")).replace("\n", "<br>")

    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="{e(CSP)}">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <link rel="canonical" href="{e(url)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{e(site_name)}">
  <meta property="og:title" content="{e(name)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:url" content="{e(url)}">
  <meta property="og:image" content="{e(og_img)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#5d9c3b">
  <link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&family=Press+Start+2P&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../assets/style.css">
  <script type="application/ld+json">{ld_json}</script>
</head>
<body class="item-body">
  <nav class="nav item-nav">
    <a href="../../" class="logo"><span class="logo-block" aria-hidden="true"></span>{e(site_name)}</a>
    <div class="nav-links"><a href="../../#mods">← كل الأعمال</a><a href="../../#faq">مساعدة</a></div>
  </nav>
  <main class="section item-page">
    <article class="panel item-article">
      <div class="thumb{'' if img else ' generated'}" data-color="{e(color)}">
        {f'<img src="{e(rel(img))}" alt="{e(name)}" decoding="async">' if img else f'<span class="thumb-icon">{t_icon}</span>'}
        <div class="badges"><span class="badge">{e(t_label)}</span></div>
      </div>
      <div class="modal-content">
        <h1 class="item-title">{e(name)}</h1>
        <p class="lead">{e(desc)}</p>
        <div class="dl-box">
          {f'<a class="mc-btn mc-btn-green mc-btn-big" id="dlBtn" href="{e(file)}" rel="noopener">⬇ تحميل {e(m.get("size"))}</a>' if file else '<p>رابط التحميل غير متوفر حالياً.</p>'}
          <p class="fits">✔ يشتغل على: <b>{e(EDITIONS.get(m.get("edition"), ""))} {e("، ".join(versions))}</b>{f' · يحتاج <b>{e(m.get("loader"))}</b>' if m.get("loader") else ''}</p>
          <p class="dl-started" id="dlStarted" hidden>✔ بدأ التحميل! الحين سوّ الخطوات اللي تحت 👇</p>
        </div>
        <div class="guide" id="guide" data-type="{e(m.get('type'))}" data-edition="{e(m.get('edition'))}" data-loader="{e(m.get('loader'))}">
          <h2 class="h3">🛠 شلون أثبّته؟</h2>
          <noscript><p>شوف قسم <a href="../../#install">طريقة التثبيت</a>.</p></noscript>
        </div>
        {f'<p class="muted-note">الرابط خربان أو فيه مشكلة؟ <a href="{e(report)}" target="_blank" rel="noopener noreferrer">بلّغني</a>.</p>' if report else ''}
        {f'<h2 class="h4">عن هذا العمل</h2><div class="details-text">{details}</div>' if details else ''}
        {('<h2 class="h4">صور</h2><div class="gallery">' + ''.join(f'<a class="shot" href="{e(rel(s))}" target="_blank" rel="noopener"><img src="{e(rel(s))}" alt="{e(name)} صورة {i}" loading="lazy"></a>' for i, s in enumerate(shots, 1)) + '</div>') if shots else ''}
        {f'<h2 class="h4">فيديو</h2><div class="video"><iframe src="https://www.youtube-nocookie.com/embed/{video}" title="فيديو {e(name)}" loading="lazy" allow="encrypted-media; picture-in-picture; fullscreen" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>' if video else ''}
        <h2 class="h4">معلومات</h2>
        <table class="info-table">{''.join(f'<tr><td>{e(k)}</td><td>{e(v)}</td></tr>' for k, v in rows if v)}</table>
        {('<div class="meta tags">' + ''.join(f'<span class="chip">{e(x)}</span>' for x in m.get('tags') or []) + '</div>') if m.get('tags') else ''}
        {('<h2 class="h4">سجل التحديثات</h2><ul class="changelog">' + ''.join(f'<li>{e(c)}</li>' for c in m.get('changelog') or []) + '</ul>') if m.get('changelog') else ''}
        {f'<details class="hash"><summary>🔒 بصمة الملف (SHA-256) للتأكد إنه أصلي</summary><code dir="ltr">{sha}</code></details>' if sha else ''}
        <div class="actions">
          <a class="mc-btn mc-btn-wa" href="https://wa.me/?text={share}" target="_blank" rel="noopener noreferrer">📤 واتساب</a>
          <a class="mc-btn" href="../../#mods">← كل الأعمال</a>
        </div>
      </div>
    </article>
  </main>
  <footer class="footer">
    <div class="socials footer-socials">{socials_html(site)}</div>
    <p><a href="../../privacy.html">سياسة الخصوصية</a></p>
    <p>{e(site_name)} — موقع غير رسمي، غير تابع لـ Mojang أو Microsoft.</p>
  </footer>
  <script src="../../assets/common.js"></script>
  <script src="../../assets/item.js"></script>
</body>
</html>
"""


def main():
    db = json.loads((ROOT / "mods.json").read_text(encoding="utf-8"))
    site = db.get("site") or {}
    mods = [m for m in db.get("mods") or [] if isinstance(m, dict) and ID_RE.fullmatch(str(m.get("id") or ""))]
    base = base_url(site)

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    for p in PUBLIC:
        src = ROOT / p
        if src.is_dir():
            shutil.copytree(src, OUT / p, symlinks=False, ignore=shutil.ignore_patterns(".gitkeep"))
        elif src.is_file():
            shutil.copyfile(src, OUT / p)
    (OUT / ".nojekyll").touch()

    stats = fetch_stats()
    (OUT / "stats.json").write_text(json.dumps({"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "tags": stats}), encoding="utf-8")

    for m in mods:
        d = OUT / "m" / m["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(item_page(m, site, base, stats), encoding="utf-8")

    # Home page: canonical, optional Search Console tag, and plain links to every item.
    index = (OUT / "index.html").read_text(encoding="utf-8")
    head = (f'<link rel="canonical" href="{e(base)}">\n  <meta property="og:url" content="{e(base)}">'
            f'\n  <meta property="og:image" content="{e(base)}assets/og.png">\n  <meta name="twitter:card" content="summary_large_image">')
    verify = str(site.get("googleVerify") or "")
    if re.fullmatch(r"[A-Za-z0-9_-]{10,100}", verify):
        head += f'\n  <meta name="google-site-verification" content="{e(verify)}">'
    index = index.replace("<!--HEAD-->", head, 1)
    links = "".join(f'<li><a href="m/{e(m["id"])}/">{e(m.get("name"))}</a></li>' for m in mods)
    index = index.replace("<!--ITEM_LINKS-->", f'<ul class="all-links">{links}</ul>' if links else "", 1)
    (OUT / "index.html").write_text(index, encoding="utf-8")

    today = dt.date.today().isoformat()
    urls = [(base, today), (base + "privacy.html", today)] + [(f"{base}m/{m['id']}/", str(m.get("updated") or m.get("date") or today)) for m in mods]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{e(u)}</loc><lastmod>{e(d[:10])}</lastmod></url>\n" for u, d in urls)
        + "</urlset>\n", encoding="utf-8")
    # Note: for a project site Google only reads robots.txt at the domain root, so the
    # sitemap must also be submitted in Search Console. admin.html is kept out via noindex.
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}sitemap.xml\n", encoding="utf-8")
    print(f"built {len(mods)} item pages -> {OUT}")


if __name__ == "__main__":
    main()
