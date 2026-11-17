-- Visitor comments for the NABD site (applied to Supabase project eqcexrzutbqaubzyelce).
-- Visitors can ONLY call submit_comment (goes to a private pending queue) and
-- list_comments (approved ones). The table itself is closed to everyone.
-- The owner moderates with a long random key; only its SHA-256 is stored.

create extension if not exists pgcrypto with schema extensions;

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create table public.comments (
  id          bigint generated always as identity primary key,
  mod_id      text not null check (mod_id ~ '^[a-z0-9]+(-[a-z0-9]+)*$' and char_length(mod_id) <= 50),
  kind        text not null check (kind in ('pro', 'con', 'bug', 'idea')),
  body        text not null check (char_length(body) between 2 and 600),
  nickname    text check (nickname is null or char_length(nickname) between 1 and 30),
  device      text check (device is null or device in ('phone', 'pc', 'console')),
  status      text not null default 'pending' check (status in ('pending', 'approved')),
  created_at  timestamptz not null default now(),
  approved_at timestamptz
);
create index comments_mod_status_idx on public.comments (mod_id, status, approved_at desc);
create index comments_created_idx on public.comments (created_at desc);

alter table public.comments enable row level security;
revoke all on public.comments from public, anon, authenticated;
-- (no RLS policies on purpose: nobody can read or write the table directly)

create table private.moderation_key (
  id         int primary key default 1 check (id = 1),
  key_sha256 text not null check (key_sha256 ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default now()
);
revoke all on private.moderation_key from public, anon, authenticated;

-- Plain text: drop control / invisible / bidi characters, collapse spaces.
create or replace function private.clean_text(p text, max_len int)
returns text language sql immutable set search_path = '' as $$
  select left(btrim(regexp_replace(
           regexp_replace(coalesce(p, ''), '[\u0000-\u001f\u007f-\u009f­؜᠎​-‏‪-‮  ⁠-⁯﻿￹-￻]', ' ', 'g'),
           '\s+', ' ', 'g')), max_len)
$$;

create or replace function private.key_ok(p_key text)
returns boolean language sql stable security definer set search_path = '' as $$
  select coalesce(char_length(p_key) between 40 and 200, false)
     and exists (select 1 from private.moderation_key k
                 where k.key_sha256 = encode(extensions.digest(convert_to(p_key, 'UTF8'), 'sha256'), 'hex'))
$$;
revoke all on function private.key_ok(text) from public, anon, authenticated;
revoke all on function private.clean_text(text, int) from public, anon, authenticated;

-- ---------- visitors ----------
create or replace function public.submit_comment(p_mod text, p_kind text, p_body text, p_nickname text default null, p_device text default null)
returns text language plpgsql volatile security definer set search_path = '' as $$
declare
  v_body text := private.clean_text(p_body, 600);
  v_nick text := nullif(private.clean_text(p_nickname, 30), '');
  v_mod  text := lower(btrim(coalesce(p_mod, '')));
begin
  if v_mod !~ '^[a-z0-9]+(-[a-z0-9]+)*$' or char_length(v_mod) > 50 then return 'bad_mod'; end if;
  if p_kind is null or p_kind not in ('pro', 'con', 'bug', 'idea') then return 'bad_kind'; end if;
  if p_device is not null and p_device not in ('phone', 'pc', 'console') then return 'bad_device'; end if;
  if char_length(v_body) < 2 then return 'too_short'; end if;
  if char_length(coalesce(p_body, '')) > 2000 then return 'too_long'; end if;
  -- no links or markup (spam), no contact details
  if v_body ~* '(https?://|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|ly|me|gg|link|site|top)\M|<|>|@[a-z0-9_.-]+\.)' then return 'no_links'; end if;
  if v_nick is not null and v_nick !~ '^[[:alnum:] _.-]+$' then return 'bad_nickname'; end if;
  -- flood protection (whole site): the queue only grows slowly and never without limit
  perform pg_advisory_xact_lock(4242);
  if (select count(*) from public.comments where created_at > now() - interval '10 minutes') >= 20 then return 'busy'; end if;
  if (select count(*) from public.comments where status = 'pending') >= 300 then return 'busy'; end if;
  if (select count(*) from public.comments where status = 'pending' and mod_id = v_mod) >= 60 then return 'busy'; end if;
  insert into public.comments (mod_id, kind, body, nickname, device) values (v_mod, p_kind, v_body, v_nick, p_device);
  return 'ok';
end $$;

create or replace function public.list_comments(p_mod text)
returns table (id bigint, kind text, body text, nickname text, device text, approved_at timestamptz)
language sql stable security definer set search_path = '' as $$
  select c.id, c.kind, c.body, c.nickname, c.device, c.approved_at
  from public.comments c
  where c.status = 'approved' and c.mod_id = lower(btrim(coalesce(p_mod, '')))
  order by c.approved_at desc
  limit 50
$$;

-- ---------- owner (moderation key) ----------
create or replace function public.mod_list(p_key text, p_status text default 'pending')
returns table (id bigint, mod_id text, kind text, body text, nickname text, device text, status text, created_at timestamptz)
language plpgsql stable security definer set search_path = '' as $$
begin
  if not private.key_ok(p_key) then raise exception 'not allowed' using errcode = '42501'; end if;
  return query select c.id, c.mod_id, c.kind, c.body, c.nickname, c.device, c.status, c.created_at
    from public.comments c where c.status = coalesce(p_status, 'pending')
    order by c.created_at desc limit 300;
end $$;

create or replace function public.mod_set(p_key text, p_id bigint, p_action text)
returns text language plpgsql volatile security definer set search_path = '' as $$
begin
  if not private.key_ok(p_key) then raise exception 'not allowed' using errcode = '42501'; end if;
  if p_action = 'approve' then
    update public.comments set status = 'approved', approved_at = now() where id = p_id and status = 'pending';
  elsif p_action = 'delete' then
    delete from public.comments where id = p_id;
  else
    return 'bad_action';
  end if;
  return case when found then 'ok' else 'not_found' end;
end $$;

-- Only these four functions are callable from the internet.
revoke all on function public.submit_comment(text, text, text, text, text) from public;
revoke all on function public.list_comments(text) from public;
revoke all on function public.mod_list(text, text) from public;
revoke all on function public.mod_set(text, bigint, text) from public;
grant execute on function public.submit_comment(text, text, text, text, text) to anon, authenticated;
grant execute on function public.list_comments(text) to anon, authenticated;
grant execute on function public.mod_list(text, text) to anon, authenticated;
grant execute on function public.mod_set(text, bigint, text) to anon, authenticated;
