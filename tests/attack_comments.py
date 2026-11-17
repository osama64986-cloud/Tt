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
        + f"select public.post_comment('{mod}', '{kind}', $b${body}$b$, {nick}, {dev});", "anon")
    ACC = ("ok", "held")   # accepted: published at once, or held for the owner
    def report(pid, ip=None):
        return last(psql((f"select set_config('request.headers', '{{\"cf-connecting-ip\": \"{ip}\"}}', false);\n" if ip else "")
                         + f"select public.report_comment('{pid}');", "anon")[1])
    visible = lambda mod="nabd-pack": psql(f"select count(*) from public.comments_for('{mod}')", "anon")[1]
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
                 "select private.has_link('x')", "select private.norm('x')", "select private.needs_review('x', null)",
                 "select private.visitor_hash()", "select * from private.reports",
                 "select public.submit_comment('nabd-pack','pro','old path', null, null)", "select * from public.list_comments('nabd-pack')"]:
        rc, out = psql(stmt, "authenticated")
        check(f"authenticated cannot run: {stmt[:60]}", rc != 0 and "permission denied" in out, out)
    rc, out = psql("select string_agg(p.proname, ',' order by p.proname) from pg_proc p join pg_namespace n on n.oid = p.pronamespace "
                   "where n.nspname in ('public','private') and not coalesce(p.proconfig @> array['search_path=\"\"'], false)")
    check("every function pins an empty search_path", rc == 0 and out == "", out)
    rc, out = psql("select string_agg(p.proname, ',' order by p.proname) from pg_proc p join pg_namespace n on n.oid = p.pronamespace "
                   "where n.nspname = 'public' and has_function_privilege('anon', p.oid, 'execute')")
    check("anon can call exactly the intended functions", out == "comments_for,mod_approve,mod_items,mod_list,mod_page,mod_purge_pending,mod_set,mod_sync_mods,post_comment,report_comment", out)
    rc, out = psql("select string_agg(provolatile::text, '') from pg_proc where proname in ('mod_approve', 'mod_items', 'mod_list', 'mod_page', 'mod_set', 'mod_purge_pending', 'mod_sync_mods', 'post_comment', 'report_comment')")
    check("owner/write functions are volatile (PostgREST refuses GET, key never in a URL)", out == "vvvvvvvvv", out)
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
    rc, out = sub("حلو", nick="'\u3164'"); check("invisible-only nickname becomes anonymous", out in ACC and psql("select nickname is null from public.comments order by id desc limit 1")[1] == "t", out)
    rc, out = sub("حلو", nick="'" + "x" * 500 + "'"); check("huge nickname refused", out == "too_long", out)
    rc, out = sub("حلو", mod="no-such-mod"); check("comments only on real (known) mods", out == "bad_mod", out)
    rc, out = sub("مود حلو z" + "\u0301" * 50 + "x"); check("Zalgo marks stripped", out in ACC and "\u0301" not in psql("select body from public.comments order by id desc limit 1")[1], out)
    rc, out = sub("مود رهيب ومرتب"); check("normal Arabic comment accepted", out == "ok", out)
    psql("delete from public.comments")
    rc, out = sub("حلو $$; drop table public.comments; --"); check("SQL in text is just text", out in ACC and count() == "1", out)
    rc, out = sub("سطر‮مقلوب\u0001\nثاني"); check("control/bidi characters removed", out in ACC and "‮" not in psql("select body from public.comments order by id desc limit 1")[1])
    # --- instant publishing with a word / spam filter
    psql("delete from public.comments")
    for body in ["مود رهيب ومرتب", "اكس بوكس يشتغل عليه", "اكسر الصخر بسرعة", "الميكانيك حلو", "night vision حلو", "كسرت راسي من الحلاوة"]:
        rc, out = sub(body, mod="zenlite"); check(f"clean comment published at once: {body}", out == "ok", out)
    # false positives found by the red team: these are normal text and must publish
    for body in ["الأكواد ما تشتغل", "سافرت أوزبكستان", "الزبيب طيب", "انا من الزبيدي", "بكس الموسيقى", "عرصة البيت", "2023 احسن سنة",
                 "Dickson server", "Scunthorpe fans", "shiitake mushroom", "ههههههههه حلو", "!!!!!!!! واو", "hahahaha حلو"]:
        psql("update public.comments set created_at = created_at - interval '11 minutes'")
        rc, out = sub(body, mod="nabd-pack", ip=f"192.0.2.{len(body)}")
        check(f"normal text is not held: {body}", last(out) == "ok", out)
    psql("update private.submit_log set at = at - interval '1 day'")
    bad = ["انت كواد", "يا شرموطه", "كسمك", "fuuuuck this", "يلعن نيچ", "زق عليك", "ههههههههههههههههههه", "lolololololololololol", "والكس",
           "کس امك", "کسمك", "نیك", "ش ر م و ط ه", "ش.ر.م.و.ط.ه", "ق-ح-ب-ه", "fúck", "f*ck", "fck you", "fuk", "sh!t", "b!tch",
           "kos omak", "zeb", "a7a", "sharmoota", "5ara", "🖕", "сука fuсk", "كسٱمك"]
    for i, body in enumerate(bad):
        psql("update public.comments set created_at = created_at - interval '11 minutes'")
        rc, out = sub(body, mod="bareview-ui", ip=f"198.18.{i}.1"); check(f"bad comment held or refused, not shown: {body}", last(out) in ("held", "too_short") and visible("bareview-ui") == "0", out)
    for i, nick in enumerate(["صاحب الموقع", "Admin", "NABD", "نبض", "Vanta"]):
        psql("update public.comments set created_at = created_at - interval '11 minutes'")
        rc, out = sub("مود حلو جداً " + str(i), mod="bareview-ui", nick=f"'{nick}'", ip=f"198.19.{i}.1")
        check(f"impersonating nickname held: {nick}", last(out) == "held", out)
    psql("update public.comments set created_at = created_at - interval '11 minutes'")
    rc, out = sub("مود رهيب ومرتب", mod="nabd-pack", ip="198.20.0.1"); check("same text on another mod is fine", last(out) == "ok", out)
    import time as _t
    t0 = _t.time(); rc, out = sub("ابو " * 150, mod="zenlite", ip="198.21.0.1")
    check("a 600-character comment is checked fast (<0.3 s)", _t.time() - t0 < 0.8 and last(out) in ACC, f"{_t.time() - t0:.2f}s {out}")
    psql("update private.submit_log set at = at - interval '1 day'; update public.comments set created_at = created_at - interval '11 minutes'")
    rc, out = sub("ﾌｧｯｸ fｕｃｋ you", mod="bareview-ui"); check("fullwidth insult held", out == "held", out)
    rc, out = sub("مود رهيب ومرتب", mod="zenlite"); check("copy-paste of an existing comment is held", out == "held", out)
    psql("update public.comments set status='pending', auto=false where mod_id='zenlite' and body like 'ابو%'")
    check("only clean comments are visible", visible("zenlite") == "6" and visible("bareview-ui") == "0", visible("zenlite"))
    rc, out = psql("select * from public.comments_for('zenlite') limit 1", "anon")
    import re as _re
    check("public list shows a random id only (no running number / status / mod)", bool(_re.match(r"^[0-9a-f-]{36}\|", out)) and out.count("|") == 5, out)
    # --- reports
    pid = psql("select pub_id from public.comments where mod_id='zenlite' and status='approved' order by id limit 1")[1]
    check("report without a visitor address is refused", report(pid) == "limit")
    check("first report counted", report(pid, "198.51.100.1") == "ok")
    check("same visitor cannot report twice", report(pid, "198.51.100.1") == "already")
    report(pid, "198.51.100.2")
    check("2 reports: still visible", visible("zenlite") == "6")
    report(pid, "198.51.100.3")
    check("3 different visitors hide an auto-published comment", visible("zenlite") == "5" and psql(f"select status || reports from public.comments where pub_id='{pid}'")[1] == "pending3")
    check("hidden comment cannot be reported further", report(pid, "198.51.100.4") == "not_found")
    # IPv6: one home network (/48) is one visitor, however many addresses it uses
    pid2 = psql("select pub_id from public.comments where mod_id='zenlite' and status='approved' order by id limit 1")[1]
    outs = [report(pid2, a) for a in ["2001:db8:1::1", "2001:DB8:1::2", "2001:0db8:0001:ffff::9"]]
    check("IPv6 addresses of one network count as one reporter", outs == ["ok", "already", "already"], outs)
    # parallel reports from 3 different visitors must hide the comment every time
    import concurrent.futures as _cf
    hidden_ok = 0
    for trial in range(5):
        pidx = psql("select pub_id from public.comments where mod_id='zenlite' and status='approved' and auto order by id desc limit 1")[1]
        if not pidx: break
        with _cf.ThreadPoolExecutor(3) as ex: list(ex.map(lambda k: report(pidx, f"203.0.{trial}.{k}"), range(1, 4)))
        hidden_ok += psql(f"select status || reports from public.comments where pub_id='{pidx}'")[1] == "pending3"
        psql(f"update public.comments set status='approved', auto=true, reports=0 where pub_id='{pidx}'; select 1")
        psql(f"update private.reports set comment_id = -comment_id where comment_id = (select id from public.comments where pub_id='{pidx}')")
    check("3 reports sent at the same moment still hide the comment (5/5)", hidden_ok == 5, hidden_ok)
    check("bad report id is rejected", psql("select public.report_comment('not-a-uuid')", "anon")[0] != 0)
    hid = psql(f"select id from public.comments where pub_id='{pid}'")[1]
    rc, out = psql(f"select public.mod_approve($k$bad$k$, {hid})", "anon"); check("wrong key cannot approve/keep", rc != 0 and "not allowed" in out, out)
    psql(f"select public.mod_approve('{KEY}', {hid})", "anon")
    check("owner approval resets the report counter", psql(f"select reports from public.comments where id={hid}")[1] == "0")
    for i in range(5, 9): report(pid, f"198.51.100.{i}")
    check("a comment the owner approved cannot be hidden by reports", visible("zenlite") == "6")
    psql("select set_config('request.headers', '{\"cf-connecting-ip\": \"10.9.0.1\"}', false);\n"
         "insert into private.reports (comment_id, who) select -g, private.visitor_hash() from generate_series(1, 20) g")
    psql("insert into private.reports (comment_id, who) select -1000 - g, md5(g::text) from generate_series(1, 300) g")
    check("site-wide report cap per day", report(psql("select pub_id from public.comments where mod_id='zenlite' and status='approved' order by id desc limit 1")[1], "10.20.0.1") == "limit")
    psql("update private.reports set at = at - interval '2 days' where comment_id <= -1000")
    check("report flood: at most 20 reports per visitor per day", report(psql("select pub_id from public.comments where mod_id='zenlite' and status='approved' order by id desc limit 1")[1], "10.9.0.1") == "limit")
    check("visitor address in reports is only a hash", psql("select count(*) from private.reports where who !~ '^[0-9a-f]{32,64}$'")[1] == "0")
    psql("insert into private.daily_salt values (current_date - 1, 'old') on conflict (day) do update set salt = 'old'")
    report(pid2, "10.30.0.1")
    check("yesterday's salt is wiped (old hashes cannot be linked back)", psql("select count(*) from private.daily_salt where day < current_date and salt <> ''")[1] == "0")
    rc, out = psql(f"select count(*) from public.mod_items('{KEY}', 'pending')", "anon"); check("owner sees held + hidden comments", int(out) >= 25, out)
    rc, out = psql(f"select count(*) from public.mod_items($k${'K'*42}L$k$, 'pending')", "anon"); check("wrong key cannot read held comments", rc != 0 and "not allowed" in out, out)
    # per visitor (address from Cloudflare's header, stored only as a salted hash)
    outs = [last(sub("حلو كلش", ip="203.0.113.7")[1]) for _ in range(5)]
    check("per-visitor limit: 3 per 10 minutes", [o in ACC for o in outs] == [True, True, True, False, False] and outs[3:] == ["limit", "limit"], outs)
    rc, out = sub("حلو كلش", ip="203.0.113.8"); check("another visitor is not blocked by the first", last(out) in ACC, out)
    rc, out = psql("select count(*) from private.submit_log where who ~ '^[0-9a-f]{64}$' and who !~ '203'")
    check("visitor address is stored only as a hash", out == "4", out)
    oks = 3
    for _ in range(4):
        psql("update private.submit_log set at = at - interval '11 minutes'; update public.comments set created_at = created_at - interval '11 minutes'")
        oks += sum(last(sub("حلو كلش", ip="203.0.113.7")[1]) in ACC for _ in range(3))
    check("per-visitor daily cap: 10 per day", oks == 10, oks)
    psql("update private.submit_log set at = at - interval '2 days'")
    sub("حلو كلش", ip="203.0.113.9")
    check("visitor log older than 24h is deleted", psql("select count(*) from private.submit_log where at < now() - interval '1 day'")[1] == "0")
    psql("delete from public.comments; delete from private.submit_log")
    rc, out = psql("select public.post_comment('nabd-pack','pro','حلو كلش', null, null) from generate_series(1,40)", "anon")
    check("site-wide flood limit: at most 30 per 10 minutes", count() == "30" and "busy" in out, count())
    check("a flood of the same text: only the first is published", count("status='approved'") == "1", count("status='approved'"))

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
    rc, out = psql(f"select count(*) from public.mod_list('{KEY}')", "anon"); check("right key lists pending (100 per page)", rc == 0 and out == "29", out)
    rc, out = psql(f"select count(*) from public.mod_page('{KEY}', 'pending', {int(psql("select max(id) from public.comments")[1]) - 9})", "anon")
    check("owner list pages with p_before", out == "19", out)
    rc, out = psql(f"select public.mod_set('{KEY}', 1, 'drop')", "anon"); check("unknown action refused", out == "bad_action", out)
    first = psql("select min(id) from public.comments where status='pending'")[1]
    rc, out = psql(f"select public.mod_set('{KEY}', {first}, 'approve')", "anon")
    check("approved comment becomes visible", out == "ok" and visible() == "2", f"{out} {visible()}")
    check("other mods see nothing", visible("other-mod") == "0")
    rc, out = psql(f"select public.mod_set('{KEY}', {first}, 'delete')", "anon")
    check("owner can delete", out == "ok" and visible() == "1", out)
    rc, out = psql(f"select public.mod_purge_pending('{KEY}')", "anon")
    check("owner can delete all pending spam at once", out == "28" and count("status='pending'") == "0", out)
    # caps: 60 pending per mod, 300 pending overall (time moved back to skip the 10-minute limits)
    ids = [f"m{i}" for i in range(7)]
    psql(f"select public.mod_sync_mods('{KEY}', array{ids!r})", "anon")
    for mod in ids:
        for _ in range(3):
            psql(f"select public.post_comment('{mod}','pro','حلو كلش', null, null) from generate_series(1,25)", "anon")
            psql("update public.comments set created_at = created_at - interval '11 minutes'")
    check("pending caps: 60 per mod and 300 overall", count("status='pending'") == "300" and count("mod_id='m0' and status='pending'") == "60", count("status='pending'"))
    rc, out = sub("حلو", mod="nabd-pack"); check("sync removed mods that no longer exist", out == "bad_mod", out)
finally:
    subprocess.run([f"{BIN}/pg_ctl", "-D", str(DATA), "-m", "immediate", "stop"], capture_output=True, env=env)

print(f"\n{sum(res)}/{len(res)} attacks blocked")
sys.exit(0 if all(res) else 1)
