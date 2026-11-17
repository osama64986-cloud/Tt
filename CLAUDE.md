# Project notes for Claude

Minecraft mods website (Arabic, RTL) on GitHub Pages. The owner is not technical:
explain in simple Iraqi/Gulf Arabic, keep the site very easy for visitors.

## Golden rule: security first
Every change must be checked for security **before** it is pushed:
1. Run `python3 -I tests/attack_publish.py . /tmp/redteam-work` `python3 -I tests/attack_build.py . /tmp/redteam-build` and `python3 -I tests/attack_feedback.py . /tmp/redteam-feedback` → every line must be `BLOCKED` (both exit non-zero otherwise).
   For comment/database changes also run `tests/attack_comments.py` as a NON-root user (local Postgres only; never the live Supabase project).
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
- Visitor feedback: `.github/ISSUE_TEMPLATE/feedback.yml` → GitHub issue; owner comments `موافق`/`/approve` → `.github/workflows/feedback.yml` runs `scripts/feedback.py` (owner-only, snapshot into `feedback.json`); shown via `MC.feedbackHtml` and `build.py feedback_html`.
- On-site comments (no account): `assets/comments.js` → Supabase project `eqcexrzutbqaubzyelce` (publishable key is public by design).
  The `comments` table is closed; only the RPCs in `supabase/migrations/*.sql` are exposed (submit/list for visitors, mod_list/mod_set need the
  owner's moderation key; the DB stores only its sha256 in `private.moderation_key`). Owner approves in admin.html «آراء الزوار».
  Visitors: `post_comment` (clean → published at once; `private.needs_review` words/spam → held), `comments_for`, `report_comment`
  (3 visitors hide an auto-published comment). Supabase's MCP asks the owner to confirm any SQL containing DROP/DELETE and the
  prompt does not reach the owner's phone: write migrations without them where possible, otherwise give the owner a paste page.
  Any DB change = new migration file + apply it + rerun attack_comments.py.
- Deploy target is the `gh-pages` branch (Pages source). Do not edit it by hand.
- `MC.LATEST` in `assets/common.js` holds the latest Minecraft versions; update it when Mojang releases.
- actions/checkout v6+ stores credentials outside .git/config: pages.yml builds its own auth header.

## Security audits
- Cloudflare's MIT-licensed `security-audit` skill lives in `.claude/skills/security-audit` (never published: build.py copies only PUBLIC).
  Use it (guidance mode, or full mode when the owner asks for a full audit) for every security review, and red-team every new
  feature with a separate agent on a local copy only, never the live site or Supabase project.
