"""Red-team the on-site comment database against a LOCAL Postgres copy (never the real one).

Run as a NON-root user (Postgres refuses root):
    python3 -I tests/attack_comments.py . /tmp/redteam-comments
Needs PostgreSQL 15+ binaries (initdb, pg_ctl, psql). Every line must say BLOCKED.
"""
import glob, os, pathlib, shutil, subprocess, sys, time
REPO = pathlib.Path(sys.argv[1]).resolve(); W = pathlib.Path(sys.argv[2]).resolve()
BIN = sorted(glob.glob("/usr/lib/postgresql/*/bin"))[-1]
DATA, SOCK = W / "pgdata", W / "sock"
KEY = "K" * 43                     # dummy moderation key (43 chars like the real format)
shutil.rmtree(W, ignore_errors=True); SOCK.mkdir(parents=True)
env = {"PATH": f"{BIN}:/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": str(W)}
subprocess.run([f"{BIN}/initdb", "-D", str(DATA), "-U", "postgres", "-E", "UTF8", "--locale=C.UTF-8", "-A", "trust"], check=True, capture_output=True, env=env)
subprocess.run([f"{BIN}/pg_ctl", "-D", str(DATA), "-w", "-l", str(W / "pg.log"), "-o", f"-k {SOCK} -c listen_addresses=''", "start"], check=True, capture_output=True, env=env)

def psql(sql, role=None):
    pre = f"set role {role};\n" if role else ""
    r = subprocess.run(["psql", "-h", str(SOCK), "-U", "postgres", "-d", "postgres", "-X", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1"],
                       input=pre + sql, capture_output=True, text=True, env=env)  # stdin: no argv size limit
    return r.returncode, (r.stdout + r.stderr).strip()

res = []
def check(title, ok, detail=""):
    print(("BLOCKED " if ok else "!!! VULNERABLE ") + title + ("" if ok else f"\n   {detail}")); res.append(ok)

try:
    # Supabase-like roles and schemas, then the real migration file(s)
    # Supabase grants anon/authenticated everything on NEW objects in public by default: emulate that,
    # so the migration must close things itself.
    rc, out = psql("create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema extensions; "
                   "grant usage on schema public to anon, authenticated; "
                   "alter default privileges in schema public grant all on tables to anon, authenticated, service_role; "
                   "alter default privileges in schema public grant all on functions to anon, authenticated, service_role; "
                   "alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;")
    assert rc == 0, out
    for f in sorted((REPO / "supabase" / "migrations").glob("*.sql")):
        rc, out = psql(f.read_text())
        assert rc == 0, f"{f.name}: {out}"
    rc, out = psql(f"insert into private.moderation_key (key_sha256) values (encode(extensions.digest('{KEY}', 'sha256'), 'hex'));")
    assert rc == 0, out
    sub = lambda body, mod="nabd-pack", kind="pro", nick="null", dev="null", ip=None: psql(
        (f"select set_config('request.headers', '{{\"cf-connecting-ip\": \"{ip}\"}}', false);\n" if ip else "")
        + f"select public.submit_comment('{mod}', '{kind}', $b${body}$b$, {nick}, {dev});", "anon")
    last = lambda o: o.splitlines()[-1] if o else o
    count = lambda where="true": psql(f"select count(*) from public.comments where {where}")[1]

    # --- direct access to the table and private functions
    for stmt in ["select * from public.comments", "insert into public.comments (mod_id, kind, body, status) values ('a','pro','xx','approved')",
                 "update public.comments set status='approved'", "delete from public.comments", "select * from private.moderation_key",
                 f"select private.key_ok('{KEY}')", "select private.clean_text('x', 5)"]:
        rc, out = psql(stmt, "anon")
        check(f"anon cannot run: {stmt[:60]}", rc != 0 and "permission denied" in out, out)
    rc, out = psql("create table public.evil (x int)", "anon")
    check("anon cannot create objects in public", rc != 0, out)
    for stmt in ["select nextval('public.comments_id_seq')", "select setval('public.comments_id_seq', 9223372036854775807)",
                 "select * from private.known_mods", "select * from private.submit_log", "select * from private.daily_salt",
                 "select private.has_link('x')"]:
        rc, out = psql(stmt, "authenticated")
        check(f"authenticated cannot run: {stmt[:60]}", rc != 0 and "permission denied" in out, out)
    rc, out = psql("select string_agg(p.proname, ',' order by p.proname) from pg_proc p join pg_namespace n on n.oid = p.pronamespace "
                   "where n.nspname in ('public','private') and not coalesce(p.proconfig @> array['search_path=\"\"'], false)")
    check("every function pins an empty search_path", rc == 0 and out == "", out)
    rc, out = psql("select string_agg(p.proname, ',' order by p.proname) from pg_proc p join pg_namespace n on n.oid = p.pronamespace "
                   "where n.nspname = 'public' and has_function_privilege('anon', p.oid, 'execute')")
    check("anon can call exactly the seven intended functions", out == "list_comments,mod_list,mod_page,mod_purge_pending,mod_set,mod_sync_mods,submit_comment", out)
    rc, out = psql("select string_agg(provolatile::text, '') from pg_proc where proname in ('mod_list', 'mod_page', 'mod_set', 'mod_purge_pending', 'mod_sync_mods')")
    check("owner functions are volatile (PostgREST refuses GET, key never in a URL)", out == "vvvvv", out)
    rc, out = psql("select count(*) from pg_proc where proname in ('list_comments', 'mod_list')")
    check("no leftover overloads of public functions", out == "2", out)

    # --- submit validation
    cases = {
        "link https": ("شوف https://evil.example", "no_links"), "link www": ("www.evil.example حلو", "no_links"),
        "bare domain": ("زوروا evil.com", "no_links"), "email": ("راسلني a@b.co", "no_links"), "html": ("<img src=x onerror=alert(1)>", "no_links"),
        "too short": ("x", "too_short"), "only invisible": ("\u200b\u200f\u202e", "too_short"), "too long": ("أ" * 2500, "too_long"),
        "fullwidth link": ("ｈｔｔｐｓ：／／evil", "no_links"), "fullwidth dot": ("evil．com", "no_links"), "ideographic dot": ("evil。com", "no_links"),
        "bracket dot": ("evil[.]com", "no_links"), ".co / .shop": ("evil.co و evil.shop", "no_links"), "discord invite": ("discord.gg/abc", "no_links"),
        "Hangul filler only": ("\u3164\u3164\u3164\u3164", "too_short"), "braille blank only": ("\u2800\u2800\u2800", "too_short"),
        "tag characters only": ("\U000e0061\U000e0062\U000e0063", "too_short"), "emoji/punctuation only": ("!!! ...", "too_short"),
        "huge body (5 MB) refused before work": ("أ" * 2_500_000, "too_long"),
    }
    for name, (body, want) in cases.items():
        rc, out = sub(body)
        check(f"submit rejects {name}", out == want, out)
    for mod, want in [("../x", "bad_mod"), ("NABD; drop table x", "bad_mod"), ("a" * 60, "bad_mod")]:
        rc, out = sub("حلو", mod=mod); check(f"submit rejects mod id {mod[:20]!r}", out == want, out)
    rc, out = sub("حلو", kind="approved"); check("submit rejects fake kind", out == "bad_kind", out)
    rc, out = sub("حلو", dev="'laptop'"); check("submit rejects fake device", out == "bad_device", out)
    rc, out = sub("حلو", nick="'<b>x</b>'"); check("submit rejects markup nickname", out in ("bad_nickname", "no_links"), out)
    rc, out = sub("حلو", nick="'evil.com'"); check("submit rejects link nickname", out == "no_links", out)
    rc, out = sub("حلو", nick="'\u3164'"); check("invisible-only nickname becomes anonymous", out == "ok" and psql("select nickname is null from public.comments order by id desc limit 1")[1] == "t", out)
    rc, out = sub("حلو", nick="'" + "x" * 500 + "'"); check("huge nickname refused", out == "too_long", out)
    rc, out = sub("حلو", mod="no-such-mod"); check("comments only on real (known) mods", out == "bad_mod", out)
    rc, out = sub("مود حلو z" + "\u0301" * 50 + "x"); check("Zalgo marks stripped", out == "ok" and "\u0301" not in psql("select body from public.comments order by id desc limit 1")[1], out)
    rc, out = sub("مود رهيب ومرتب"); check("normal Arabic comment accepted", out == "ok", out)
    psql("delete from public.comments")
    rc, out = sub("حلو $$; drop table public.comments; --"); check("SQL in text is just text", out == "ok" and count() == "1", out)
    rc, out = sub("سطر‮مقلوب\u0001\nثاني"); check("control/bidi characters removed", out == "ok" and "‮" not in psql("select body from public.comments order by id desc limit 1")[1])
    rc, out = psql("select count(*) from public.list_comments('nabd-pack')", "anon")
    check("pending comments are NOT visible", out == "0", out)
    # per visitor (address from Cloudflare's header, stored only as a salted hash)
    outs = [last(sub("حلو كلش", ip="203.0.113.7")[1]) for _ in range(5)]
    check("per-visitor limit: 3 per 10 minutes", outs == ["ok", "ok", "ok", "limit", "limit"], outs)
    rc, out = sub("حلو كلش", ip="203.0.113.8"); check("another visitor is not blocked by the first", last(out) == "ok", out)
    rc, out = psql("select count(*) from private.submit_log where who ~ '^[0-9a-f]{64}$' and who !~ '203'")
    check("visitor address is stored only as a hash", out == "4", out)
    oks = 3
    for _ in range(4):
        psql("update private.submit_log set at = at - interval '11 minutes'; update public.comments set created_at = created_at - interval '11 minutes'")
        oks += [last(sub("حلو كلش", ip="203.0.113.7")[1]) for _ in range(3)].count("ok")
    check("per-visitor daily cap: 10 per day", oks == 10, oks)
    psql("update private.submit_log set at = at - interval '2 days'")
    sub("حلو كلش", ip="203.0.113.9")
    check("visitor log older than 24h is deleted", psql("select count(*) from private.submit_log where at < now() - interval '1 day'")[1] == "0")
    psql("delete from public.comments; delete from private.submit_log")
    rc, out = psql("select public.submit_comment('nabd-pack','pro','حلو كلش', null, null) from generate_series(1,40)", "anon")
    check("site-wide flood limit: at most 30 per 10 minutes", count() == "30" and "busy" in out, count())

    # --- moderation key
    for bad in ["", "K" * 42, "k" * 43, KEY + " ", "x' or '1'='1", KEY[:-1] + "L", "K" * 300]:
        rc, out = psql(f"select count(*) from public.mod_list($k${bad}$k$)", "anon")
        check(f"wrong moderation key refused ({bad[:12]!r}…)", rc != 0 and "not allowed" in out, out)
        rc, out = psql(f"select public.mod_set($k${bad}$k$, 1, 'approve')", "anon")
        check(f"wrong key cannot approve ({bad[:12]!r}…)", rc != 0, out)
    rc, out = psql("select public.mod_set(null, 1, 'approve')", "anon"); check("null key cannot approve", rc != 0, out)
    rc, out = psql(f"select public.mod_purge_pending($k$x' or '1'='1$k$)", "anon"); check("wrong key cannot purge", rc != 0, out)
    rc, out = psql(f"select count(*) from public.mod_page($k${'K'*42}L$k$, 'pending', null)", "anon"); check("wrong key cannot page the owner list", rc != 0 and "not allowed" in out, out)
    rc, out = psql(f"select public.mod_sync_mods($k$bad$k$, array['evil'])", "anon"); check("wrong key cannot change the mod list", rc != 0, out)
    rc, out = psql(f"select public.mod_sync_mods('{KEY}', array['../x'])", "anon"); check("mod list rejects bad ids", out == "-1", out)
    rc, out = psql(f"select count(*) from public.mod_list('{KEY}')", "anon"); check("right key lists pending (100 per page)", rc == 0 and out == "30", out)
    rc, out = psql(f"select count(*) from public.mod_page('{KEY}', 'pending', {int(psql("select max(id) from public.comments")[1]) - 9})", "anon")
    check("owner list pages with p_before", out == "20", out)
    rc, out = psql(f"select public.mod_set('{KEY}', 1, 'drop')", "anon"); check("unknown action refused", out == "bad_action", out)
    first = psql("select min(id) from public.comments")[1]
    rc, out = psql(f"select public.mod_set('{KEY}', {first}, 'approve')", "anon")
    rc2, out2 = psql("select count(*) from public.list_comments('nabd-pack')", "anon")
    check("approved comment becomes visible", out == "ok" and out2 == "1", f"{out} {out2}")
    rc, out = psql("select count(*) from public.list_comments('other-mod')", "anon"); check("other mods see nothing", out == "0", out)
    rc, out = psql("select * from public.list_comments('nabd-pack')", "anon")
    check("public list exposes no id/status/created/mod internals", out.count("|") == 5 and out.startswith("|"), out)
    rc, out = psql(f"select public.mod_set('{KEY}', {first}, 'delete')", "anon")
    check("owner can delete", out == "ok" and psql("select count(*) from public.list_comments('nabd-pack')", "anon")[1] == "0", out)
    rc, out = psql(f"select public.mod_purge_pending('{KEY}')", "anon")
    check("owner can delete all pending spam at once", out == "29" and count("status='pending'") == "0", out)
    # caps: 60 pending per mod, 300 pending overall (time moved back to skip the 10-minute limits)
    ids = [f"m{i}" for i in range(7)]
    psql(f"select public.mod_sync_mods('{KEY}', array{ids!r})", "anon")
    for mod in ids:
        for _ in range(3):
            psql(f"select public.submit_comment('{mod}','pro','حلو كلش', null, null) from generate_series(1,25)", "anon")
            psql("update public.comments set created_at = created_at - interval '11 minutes'")
    check("pending caps: 60 per mod and 300 overall", count("status='pending'") == "300" and count("mod_id='m0' and status='pending'") == "60", count("status='pending'"))
    rc, out = sub("حلو", mod="nabd-pack"); check("sync removed mods that no longer exist", out == "bad_mod", out)
finally:
    subprocess.run([f"{BIN}/pg_ctl", "-D", str(DATA), "-m", "immediate", "stop"], capture_output=True, env=env)

print(f"\n{sum(res)}/{len(res)} attacks blocked")
sys.exit(0 if all(res) else 1)
