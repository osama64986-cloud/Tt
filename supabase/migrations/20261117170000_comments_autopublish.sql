-- Comments publish at once when they look clean; suspicious ones wait for the owner.
-- Visitors can report a comment; 3 different visitors hide an auto-published comment
-- (it goes back to the owner's queue). A comment the owner approved by hand cannot be
-- hidden by reports. Written without DROP/DELETE so it can be applied without a prompt;
-- the older functions stay in place (submit_comment does all validation and limits).

alter table public.comments add column if not exists pub_id uuid not null default gen_random_uuid();
alter table public.comments add column if not exists auto boolean not null default false;
alter table public.comments add column if not exists reports int not null default 0;
create unique index if not exists comments_pub_id_idx on public.comments (pub_id);

create table if not exists private.reports (
  comment_id bigint not null,
  who        text   not null,
  at         timestamptz not null default now(),
  primary key (comment_id, who)
);
create index if not exists reports_who_idx on private.reports (who, at);
revoke all on private.reports from public, anon, authenticated;

-- Text normalised for word checks: lower case, Arabic letter variants unified, harakat and
-- tatweel removed, Iraqi/Persian letters mapped, simple leetspeak, repeated letters collapsed.
create or replace function private.norm(p text)
returns text language sql immutable set search_path = '' as $$
  select regexp_replace(
           translate(
             regexp_replace(lower(coalesce(p, '')), '[\u064b-\u0652\u0670\u0640]', '', 'g'),
             'أإآٱىةگچڤپ013@$5', 'اااايهككفبoieass'),
           '(.)\1+', '\1', 'g')
$$;
revoke all on function private.norm(text) from public, anon, authenticated;

-- true = hold for the owner (insults, sexual words, spam patterns)
create or replace function private.needs_review(p_body text, p_nick text)
returns boolean language sql immutable set search_path = '' as $$
  with t as (select private.norm(coalesce(p_body, '') || ' ' || coalesce(p_nick, '')) as n,
                    coalesce(p_body, '') || ' ' || coalesce(p_nick, '') as raw)
  select
    -- stems (collapsed spelling) that are not part of normal words
    n ~ '(شرموط|قحب|منيوك|منيك|متناك|نياك|عرص|ديوث|كسم|كسخت|زبي|زبك|طيزك|طيزي|كواد|مخنث|لوطي|خنيث|سكسي|fuck|shit|bitch|cunt|whore|slut|niga|fagot|porn|pusy|dick|ashole|motherf|bastard|sexy)'
    -- short words only as whole words (optional Arabic prefix / suffix)
    or n ~ '(^|[^[:alnum:]])(ال|وال|و|ب|يا|ل)?(كس|زب|طيز|نيك|انيك|ينيك|نيكك|خرا|زق|عاهر|عاهره|sex|xx)(ك|ه|ي|ها|كم|ات)?($|[^[:alnum:]])'
    -- spam: one character 8+ times in a row, or the same short chunk repeated many times
    or raw ~ '(.)\1{7,}' or raw ~ '(.{2,6})\1{5,}'
  from t
$$;
revoke all on function private.needs_review(text, text) from public, anon, authenticated;

create or replace function private.visitor_hash()
returns text language plpgsql volatile security definer set search_path = '' as $$
declare v_ip text; v_salt text;
begin
  v_ip := current_setting('request.headers', true)::json ->> 'cf-connecting-ip';
  if v_ip is null or v_ip !~ '^[0-9a-fA-F:.]{3,45}$' then return null; end if;
  insert into private.daily_salt (day, salt) values (current_date, encode(extensions.gen_random_bytes(16), 'hex')) on conflict do nothing;
  select s.salt into v_salt from private.daily_salt s where s.day = current_date;
  return encode(extensions.digest(convert_to(v_salt || '|' || v_ip, 'UTF8'), 'sha256'), 'hex');
end $$;
revoke all on function private.visitor_hash() from public, anon, authenticated;

-- ---------- visitors ----------
-- Returns 'ok' (published now), 'held' (waits for the owner) or the same error codes as submit_comment.
create or replace function public.post_comment(p_mod text, p_kind text, p_body text, p_nickname text default null, p_device text default null)
returns text language plpgsql volatile security definer set search_path = '' as $$
declare r text; v_id bigint; v_body text; v_nick text;
begin
  r := public.submit_comment(p_mod, p_kind, p_body, p_nickname, p_device);  -- all checks + limits + insert (pending)
  if r <> 'ok' then return r; end if;
  -- submit_comment holds the advisory lock until this transaction ends, so the newest
  -- pending row for this mod is the one just inserted.
  select c.id, c.body, c.nickname into v_id, v_body, v_nick from public.comments c
    where c.status = 'pending' and c.mod_id = lower(btrim(p_mod)) order by c.id desc limit 1;
  if v_id is null then return 'held'; end if;
  if private.needs_review(v_body, v_nick)
     or exists (select 1 from public.comments c where c.id <> v_id and c.body = v_body and c.created_at > now() - interval '1 day')
  then return 'held'; end if;
  update public.comments set status = 'approved', approved_at = now(), auto = true where id = v_id;
  return 'ok';
end $$;

create or replace function public.comments_for(p_mod text)
returns table (pub_id uuid, kind text, body text, nickname text, device text, approved_at timestamptz)
language sql stable security definer set search_path = '' as $$
  select c.pub_id, c.kind, c.body, c.nickname, c.device, c.approved_at
  from public.comments c
  where c.status = 'approved' and c.mod_id = lower(btrim(left(coalesce(p_mod, ''), 60)))
  order by c.approved_at desc
  limit 50
$$;

-- 'ok' | 'already' | 'limit' | 'not_found'. Needs the visitor's network address (one vote each).
create or replace function public.report_comment(p_pub_id uuid)
returns text language plpgsql volatile security definer set search_path = '' as $$
declare v_who text; v_id bigint; v_auto boolean; n int;
begin
  v_who := private.visitor_hash();
  if v_who is null then return 'limit'; end if;
  select c.id, c.auto into v_id, v_auto from public.comments c where c.pub_id = p_pub_id and c.status = 'approved';
  if v_id is null then return 'not_found'; end if;
  if (select count(*) from private.reports r where r.who = v_who and r.at > now() - interval '1 day') >= 20 then return 'limit'; end if;
  insert into private.reports (comment_id, who) values (v_id, v_who) on conflict do nothing;
  if not found then return 'already'; end if;
  select count(*) into n from private.reports r where r.comment_id = v_id;
  update public.comments set reports = n,
         status = case when v_auto and n >= 3 then 'pending' else status end,
         auto   = case when v_auto and n >= 3 then false else auto end
   where id = v_id;
  return 'ok';
end $$;

-- ---------- owner ----------
create or replace function public.mod_items(p_key text, p_status text default 'pending', p_before bigint default null)
returns table (id bigint, mod_id text, kind text, body text, nickname text, device text, status text, created_at timestamptz, auto boolean, reports int)
language plpgsql volatile security definer set search_path = '' as $$
begin
  if not private.key_ok(p_key) then raise exception 'not allowed' using errcode = '42501'; end if;
  return query select c.id, c.mod_id, c.kind, c.body, c.nickname, c.device, c.status, c.created_at, c.auto, c.reports
    from public.comments c
    where c.status = coalesce(p_status, 'pending') and (p_before is null or c.id < p_before)
    order by c.id desc limit 100;
end $$;

-- Visitors now use post_comment / comments_for; the old entry points are closed to them.
revoke all on function public.submit_comment(text, text, text, text, text) from public, anon, authenticated;
revoke all on function public.list_comments(text) from public, anon, authenticated;
revoke all on function public.post_comment(text, text, text, text, text) from public;
revoke all on function public.comments_for(text) from public;
revoke all on function public.report_comment(uuid) from public;
revoke all on function public.mod_items(text, text, bigint) from public;
grant execute on function public.post_comment(text, text, text, text, text) to anon, authenticated;
grant execute on function public.comments_for(text) to anon, authenticated;
grant execute on function public.report_comment(uuid) to anon, authenticated;
grant execute on function public.mod_items(text, text, bigint) to anon, authenticated;
