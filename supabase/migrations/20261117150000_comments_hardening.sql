-- Hardening after the dedicated red-team review (see tests/attack_comments.py).
--  F1 spam lockout: per-visitor limit (hashed IP, daily salt, kept 24h), only real mods accepted,
--     owner can delete all pending at once.
--  F2 huge inputs are refused before any text processing.
--  F3 public list no longer shows the running id.  F4 sequence closed.
--  F5 stronger cleaning: NFKC, more invisible characters, Zalgo, links in nicknames.
--  F7 owner list can page.  mod_list is volatile so PostgREST refuses GET (key never in a URL).

revoke all on sequence public.comments_id_seq from public, anon, authenticated;

-- ---------- private tables ----------
create table if not exists private.known_mods (id text primary key check (id ~ '^[a-z0-9]+(-[a-z0-9]+)*$' and char_length(id) <= 50));
create table if not exists private.daily_salt (day date primary key, salt text not null);
create table if not exists private.submit_log (who text not null, at timestamptz not null default now());
create index if not exists submit_log_who_idx on private.submit_log (who, at);
revoke all on private.known_mods, private.daily_salt, private.submit_log from public, anon, authenticated;
-- the mods published when this was written; the admin panel keeps the list in sync afterwards
insert into private.known_mods (id) values ('nabd-pack'), ('bareview-ui'), ('zenlite') on conflict do nothing;

-- ---------- text cleaning ----------
create or replace function private.clean_text(p text, max_len int)
returns text language sql immutable set search_path = '' as $$
  select left(btrim(regexp_replace(
           regexp_replace(
             regexp_replace(normalize(coalesce(p, ''), NFKC),
               -- runs of 3+ combining marks ("Zalgo"); Arabic harakat are not in these ranges
               '[\u0300-\u036f\u0483-\u0489\u1ab0-\u1aff\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]{3,}', '', 'g'),
             -- control, invisible, filler, bidi, variation selectors, tag characters
             '[\u0000-\u001f\u007f-\u009f\u00ad\u034f\u061c\u115f\u1160\u17b4\u17b5\u180b-\u180f\u200b-\u200f\u2028-\u202e\u2060-\u206f\u2800\u3164\ufe00-\ufe0f\ufeff\uffa0\ufff0-\ufffb\U0001d173-\U0001d17a\U000e0000-\U000e007f]',
             ' ', 'g'),
           '\s+', ' ', 'g')), max_len)
$$;
revoke all on function private.clean_text(text, int) from public, anon, authenticated;

-- link / markup / contact rule, after NFKC (so fullwidth letters and dots become plain ones)
create or replace function private.has_link(p text)
returns boolean language sql immutable set search_path = '' as $$
  select coalesce(p, '') ~* '(https?:|www\.|[a-z0-9-]+(\.|\[\.\]|\(\.\)|\[dot\]|。|٫)(com|net|org|io|xyz|ru|ly|me|gg|link|site|top|co|shop|app|dev|tv|info|biz|store|online|live|tk|ml|cc|to|us|uk)\M|<|>|@[a-z0-9_.-]+\.|discord\.gg|t\.me/)'
$$;
revoke all on function private.has_link(text) from public, anon, authenticated;

-- ---------- visitors ----------
create or replace function public.submit_comment(p_mod text, p_kind text, p_body text, p_nickname text default null, p_device text default null)
returns text language plpgsql volatile security definer set search_path = '' as $$
declare
  v_body text; v_nick text; v_mod text; v_ip text; v_who text; v_salt text;
begin
  -- refuse huge inputs before doing any work on them
  if octet_length(p_body) > 8000 or octet_length(p_nickname) > 400 or octet_length(p_mod) > 200
     or octet_length(p_kind) > 20 or octet_length(p_device) > 20 then return 'too_long'; end if;
  v_body := private.clean_text(p_body, 600);
  v_nick := nullif(private.clean_text(p_nickname, 30), '');
  v_mod  := lower(btrim(coalesce(p_mod, '')));
  if v_mod !~ '^[a-z0-9]+(-[a-z0-9]+)*$' or char_length(v_mod) > 50 then return 'bad_mod'; end if;
  if not exists (select 1 from private.known_mods k where k.id = v_mod) then return 'bad_mod'; end if;
  if p_kind is null or p_kind not in ('pro', 'con', 'bug', 'idea') then return 'bad_kind'; end if;
  if p_device is not null and p_device not in ('phone', 'pc', 'console') then return 'bad_device'; end if;
  if char_length(v_body) < 2 or v_body !~ '[[:alnum:]].*[[:alnum:]]' then return 'too_short'; end if;
  if char_length(coalesce(p_body, '')) > 2000 then return 'too_long'; end if;
  if private.has_link(v_body) or private.has_link(v_nick) then return 'no_links'; end if;
  if v_nick is not null and (v_nick !~ '^[[:alnum:] _.-]+$' or v_nick !~ '[[:alnum:]]') then return 'bad_nickname'; end if;

  perform pg_advisory_xact_lock(4242);
  -- per visitor: the address Cloudflare saw (cannot be set by the visitor), stored only as a
  -- salted hash; the salt changes every day and the log is kept for 24 hours.
  v_ip := current_setting('request.headers', true)::json ->> 'cf-connecting-ip';
  delete from private.submit_log where at < now() - interval '1 day';
  if v_ip is not null and v_ip ~ '^[0-9a-fA-F:.]{3,45}$' then
    insert into private.daily_salt (day, salt) values (current_date, encode(extensions.gen_random_bytes(16), 'hex')) on conflict do nothing;
    delete from private.daily_salt where day < current_date;
    select s.salt into v_salt from private.daily_salt s where s.day = current_date;
    v_who := encode(extensions.digest(convert_to(v_salt || '|' || v_ip, 'UTF8'), 'sha256'), 'hex');
    if (select count(*) from private.submit_log l where l.who = v_who and l.at > now() - interval '10 minutes') >= 3 then return 'limit'; end if;
    if (select count(*) from private.submit_log l where l.who = v_who) >= 10 then return 'limit'; end if;
  end if;
  -- whole site: the queue only grows slowly and never without limit
  if (select count(*) from public.comments where created_at > now() - interval '10 minutes') >= 30 then return 'busy'; end if;
  if (select count(*) from public.comments where status = 'pending') >= 300 then return 'busy'; end if;
  if (select count(*) from public.comments where status = 'pending' and mod_id = v_mod) >= 60 then return 'busy'; end if;
  insert into public.comments (mod_id, kind, body, nickname, device) values (v_mod, p_kind, v_body, v_nick, p_device);
  if v_who is not null then insert into private.submit_log (who) values (v_who); end if;
  return 'ok';
end $$;

drop function if exists public.list_comments(text);
create function public.list_comments(p_mod text)
returns table (kind text, body text, nickname text, device text, approved_at timestamptz)
language sql stable security definer set search_path = '' as $$
  select c.kind, c.body, c.nickname, c.device, c.approved_at
  from public.comments c
  where c.status = 'approved' and c.mod_id = lower(btrim(left(coalesce(p_mod, ''), 60)))
  order by c.approved_at desc
  limit 50
$$;

-- ---------- owner (moderation key) ----------
drop function if exists public.mod_list(text, text);
create function public.mod_list(p_key text, p_status text default 'pending', p_before bigint default null)
returns table (id bigint, mod_id text, kind text, body text, nickname text, device text, status text, created_at timestamptz)
language plpgsql volatile security definer set search_path = '' as $$
begin
  if not private.key_ok(p_key) then raise exception 'not allowed' using errcode = '42501'; end if;
  return query select c.id, c.mod_id, c.kind, c.body, c.nickname, c.device, c.status, c.created_at
    from public.comments c
    where c.status = coalesce(p_status, 'pending') and (p_before is null or c.id < p_before)
    order by c.id desc limit 100;
end $$;

create or replace function public.mod_purge_pending(p_key text)
returns int language plpgsql volatile security definer set search_path = '' as $$
declare n int;
begin
  if not private.key_ok(p_key) then raise exception 'not allowed' using errcode = '42501'; end if;
  delete from public.comments where status = 'pending';
  get diagnostics n = row_count;
  return n;
end $$;

-- The admin panel sends the list of published mod ids so visitors can only comment on real ones.
create or replace function public.mod_sync_mods(p_key text, p_ids text[])
returns int language plpgsql volatile security definer set search_path = '' as $$
declare n int;
begin
  if not private.key_ok(p_key) then raise exception 'not allowed' using errcode = '42501'; end if;
  if p_ids is null or cardinality(p_ids) > 500
     or exists (select 1 from unnest(p_ids) i where i is null or i !~ '^[a-z0-9]+(-[a-z0-9]+)*$' or char_length(i) > 50)
  then return -1; end if;
  delete from private.known_mods k where k.id <> all (p_ids);
  insert into private.known_mods (id) select distinct i from unnest(p_ids) i on conflict do nothing;
  select count(*) into n from private.known_mods;
  return n;
end $$;

revoke all on function public.submit_comment(text, text, text, text, text) from public;
revoke all on function public.list_comments(text) from public;
revoke all on function public.mod_list(text, text, bigint) from public;
revoke all on function public.mod_purge_pending(text) from public;
revoke all on function public.mod_sync_mods(text, text[]) from public;
grant execute on function public.submit_comment(text, text, text, text, text) to anon, authenticated;
grant execute on function public.list_comments(text) to anon, authenticated;
grant execute on function public.mod_list(text, text, bigint) to anon, authenticated;
grant execute on function public.mod_purge_pending(text) to anon, authenticated;
grant execute on function public.mod_sync_mods(text, text[]) to anon, authenticated;
