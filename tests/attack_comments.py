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
    r = subprocess.run(["psql", "-h", str(SOCK), "-U", "postgres", "-d", "postgres", "-X", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1", "-c", pre + sql],
                       capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()

res = []
def check(title, ok, detail=""):
    print(("BLOCKED " if ok else "!!! VULNERABLE ") + title + ("" if ok else f"\n   {detail}")); res.append(ok)

try:
    # Supabase-like roles and schemas, then the real migration file(s)
    rc, out = psql("create role anon nologin; create role authenticated nologin; create schema extensions; "
                   "grant usage on schema public to anon, authenticated;")
    assert rc == 0, out
    for f in sorted((REPO / "supabase" / "migrations").glob("*.sql")):
        rc, out = psql(f.read_text())
        assert rc == 0, f"{f.name}: {out}"
    rc, out = psql(f"insert into private.moderation_key (key_sha256) values (encode(extensions.digest('{KEY}', 'sha256'), 'hex'));")
    assert rc == 0, out
    sub = lambda body, mod="nabd-pack", kind="pro", nick="null", dev="null": psql(
        f"select public.submit_comment('{mod}', '{kind}', $b${body}$b$, {nick}, {dev});", "anon")

    # --- direct access to the table and private functions
    for stmt in ["select * from public.comments", "insert into public.comments (mod_id, kind, body, status) values ('a','pro','xx','approved')",
                 "update public.comments set status='approved'", "delete from public.comments", "select * from private.moderation_key",
                 f"select private.key_ok('{KEY}')", "select private.clean_text('x', 5)"]:
        rc, out = psql(stmt, "anon")
        check(f"anon cannot run: {stmt[:60]}", rc != 0 and "permission denied" in out, out)
    rc, out = psql("create table public.evil (x int)", "anon")
    check("anon cannot create objects in public", rc != 0, out)

    # --- submit validation
    cases = {
        "link https": ("شوف https://evil.example", "no_links"), "link www": ("www.evil.example حلو", "no_links"),
        "bare domain": ("زوروا evil.com", "no_links"), "email": ("راسلني a@b.co", "no_links"), "html": ("<img src=x onerror=alert(1)>", "no_links"),
        "too short": ("x", "too_short"), "only invisible": ("​‏‮", "too_short"), "too long": ("أ" * 2500, "too_long"),
    }
    for name, (body, want) in cases.items():
        rc, out = sub(body)
        check(f"submit rejects {name}", out == want, out)
    for mod, want in [("../x", "bad_mod"), ("NABD; drop table x", "bad_mod"), ("a" * 60, "bad_mod")]:
        rc, out = sub("حلو", mod=mod); check(f"submit rejects mod id {mod[:20]!r}", out == want, out)
    rc, out = sub("حلو", kind="approved"); check("submit rejects fake kind", out == "bad_kind", out)
    rc, out = sub("حلو", dev="'laptop'"); check("submit rejects fake device", out == "bad_device", out)
    rc, out = sub("حلو", nick="'<b>x</b>'"); check("submit rejects markup nickname", out == "bad_nickname", out)
    rc, out = sub("حلو $$; drop table public.comments; --"); check("SQL in text is just text", out == "ok" and psql("select count(*) from public.comments")[1] == "1", out)
    rc, out = sub("سطر‮مقلوب\u0001\nثاني"); check("control/bidi characters removed", out == "ok" and "‮" not in psql("select body from public.comments order by id desc limit 1")[1])
    rc, out = psql("select count(*) from public.list_comments('nabd-pack')", "anon")
    check("pending comments are NOT visible", out == "0", out)
    rc, out = psql("select public.submit_comment('nabd-pack','pro','حلو كلش', null, null) from generate_series(1,40)", "anon")
    check("flood limit: at most 20 per 10 minutes", psql("select count(*) from public.comments")[1] == "20" and "busy" in out, psql("select count(*) from public.comments")[1])

    # --- moderation key
    for bad in ["", "K" * 42, "k" * 43, KEY + " ", "x' or '1'='1", KEY[:-1] + "L", "K" * 300]:
        rc, out = psql(f"select count(*) from public.mod_list($k${bad}$k$)", "anon")
        check(f"wrong moderation key refused ({bad[:12]!r}…)", rc != 0 and "not allowed" in out, out)
        rc, out = psql(f"select public.mod_set($k${bad}$k$, 1, 'approve')", "anon")
        check(f"wrong key cannot approve ({bad[:12]!r}…)", rc != 0, out)
    rc, out = psql("select public.mod_set(null, 1, 'approve')", "anon"); check("null key cannot approve", rc != 0, out)
    rc, out = psql(f"select count(*) from public.mod_list('{KEY}')", "anon"); check("right key lists pending", rc == 0 and out == "20", out)
    rc, out = psql(f"select public.mod_set('{KEY}', 1, 'drop')", "anon"); check("unknown action refused", out == "bad_action", out)
    rc, out = psql(f"select public.mod_set('{KEY}', 1, 'approve')", "anon")
    rc2, out2 = psql("select count(*) from public.list_comments('nabd-pack')", "anon")
    check("approved comment becomes visible", out == "ok" and out2 == "1", f"{out} {out2}")
    rc, out = psql("select count(*) from public.list_comments('other-mod')", "anon"); check("other mods see nothing", out == "0", out)
    rc, out = psql("select string_agg(column_name, ',') from information_schema.columns where table_name='comments'", "anon")
    rc, out = psql("select * from public.list_comments('nabd-pack')", "anon")
    check("public list exposes no status/created/mod internals", out.count("|") == 5, out)
    rc, out = psql(f"select public.mod_set('{KEY}', 1, 'delete')", "anon")
    check("owner can delete", out == "ok" and psql("select count(*) from public.list_comments('nabd-pack')", "anon")[1] == "0", out)
finally:
    subprocess.run([f"{BIN}/pg_ctl", "-D", str(DATA), "-m", "immediate", "stop"], capture_output=True, env=env)

print(f"\n{sum(res)}/{len(res)} attacks blocked")
sys.exit(0 if all(res) else 1)
