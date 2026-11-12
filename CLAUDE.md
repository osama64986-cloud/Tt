# Project notes for Claude

Minecraft mods website (Arabic, RTL) on GitHub Pages. The owner is not technical:
explain in simple Iraqi/Gulf Arabic, keep the site very easy for visitors.

## Golden rule: security first
Every change must be checked for security **before** it is pushed:
1. Run `python3 -I tests/attack_publish.py . /tmp/redteam-work` → every line must be `BLOCKED`.
2. Any new field shown on a page must be escaped (`MC.esc` in JS, `html.escape` in build.py),
   links must pass `MC.safeUrl` / `safe_url`, and it must be validated in `scripts/publish.py`.
3. Never add inline scripts or `'unsafe-inline'` scripts; keep the CSP meta tags.
4. Try an XSS payload (`"><img src=x onerror=alert(1)>`) in the new field and render the page
   in Playwright; no dialog may fire.
5. Never ask for, read or store the owner's GitHub token. It lives only in their browser.

## Layout
- `index.html`, `assets/app.js` public site · `admin.html`, `assets/admin.js` owner panel
- `assets/common.js` shared escaping, URL checks, social links (host allowlist), install guides · `assets/item.js` item pages · `assets/block.js` hero block
- `scripts/publish.py` validates admin requests (runs in Actions) · `scripts/build.py` builds `_site`
- `.github/workflows/publish.yml` admin uploads → Release + mods.json · `pages.yml` builds and pushes `gh-pages`
- Deploy target is the `gh-pages` branch (Pages source). Do not edit it by hand.
