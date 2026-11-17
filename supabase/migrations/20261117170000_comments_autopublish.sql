-- Comments publish at once when they look clean; suspicious ones wait for the owner.
-- Visitors can report a comment; 3 different visitors (networks) hide an auto-published
-- comment (it goes back to the owner's queue). A comment the owner approved/kept by hand
-- cannot be hidden by reports. Written so that it only adds/replaces (nothing is removed);
-- the older functions stay in place (submit_comment does all validation and limits).
-- Revised after the red-team review (M1 networks + site cap, M2 races, L1 regex cost,
-- L2/L3 filter bypasses and false positives, L4 reserved names, L5 salt, L6 owner tools).

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
create index if not exists reports_at_idx on private.reports (at);
revoke all on private.reports from public, anon, authenticated;

-- Text normalised for word checks: accents and Arabic marks removed, letter variants
-- unified (Arabic/Persian/Iraqi, common Cyrillic/Greek look-alikes), simple leetspeak,
-- repeated letters collapsed, and letters spelled out one by one ("ش ر م", "f.u.c.k") joined.
create or replace function private.norm(p text)
returns text language sql immutable set search_path = '' as $$
  select regexp_replace(
           regexp_replace(
               translate(
                 regexp_replace(normalize(lower(coalesce(p, '')), NFD),
                   '[\u0300-\u036f\u064b-\u065f\u0670\u0640\u06d6-\u06ed]', '', 'g'),
                 'أإآٱىةۀەگچڤپکیھаеорсухкмтнвіοαειкνρτυχ013@$!*',
                 'اااايهههككفبكيهaeopcyxkmthbioaeiknptuxoieasiu'),
             -- join letters written one by one with separators: ش.ر.م / f-u-c-k / ش ر م و ط
             '(?<=(^|[ ._*\-])[[:alpha:]])[ ._*\-]+(?=[[:alpha:]]([ ._*\-]|$))', '', 'g'),
           '(.)\1+', '\1', 'g')
$$;
revoke all on function private.norm(text) from public, anon, authenticated;

-- true = hold for the owner (insults, sexual words, impersonation, spam patterns)
create or replace function private.needs_review(p_body text, p_nick text)
returns boolean language sql immutable set search_path = '' as $$
  with t as (select private.norm(coalesce(p_body, '') || ' ' || coalesce(p_nick, '')) as n,
                    private.norm(coalesce(p_nick, '')) as nk,
                    lower(coalesce(p_body, '') || ' ' || coalesce(p_nick, '')) as raw)
  select
    -- Arabic stems that are not parts of normal words
    n ~ '(شرموط|قحب|منيوك|منيك|متناك|نياك|معرص|ديوث|كسم|كسام|كسخت|مخنث|لوطي|خنيث|سكسي)'
    or n ~ '(^|[^ا])كواد'
    or n ~ '(زبي|زبك|طيزك|طيزي|كسك|كسه)($|[^[:alnum:]])'
    -- short Arabic words only as whole words (optional prefix / suffix)
    or n ~ '(^|[^[:alnum:]])(ال|وال|و|يا|ل)?(كس|زب|طيز|نيك|انيك|ينيك|نيكك|خرا|زق|عاهر|عاهره)(ك|ه|ي|ها|كم|ات)?($|[^[:alnum:]])'
    -- English words as whole words (so Dickson, Scunthorpe, shiitake pass)
    or n ~ '(^|[^[:alnum:]])(fuck[a-z]*|motherf[a-z]*|fck|fuk|shit|shity|bitch[a-z]*|cunt|whore|slut|niga|fagot|porn[a-z]*|pusy|dick|dickhead|ashole|bastard|sexy|sex)($|[^[:alnum:]])'
    -- Arabizi
    or raw ~ '(^|[^a-z])(kos ?om+a?k|kosom|kos|zeb+|a7a|5ara|ayr)($|[^a-z])'
    or raw ~ '(sharm[o0u]+t|metnak|manyok|kosomak)'
    or raw ~ '\U0001f595'
    -- impersonating the site / owner in the nickname
    or nk ~ '(صاحب ?الموقع|ادمن|مشرف|نبض|فانتا|admin|moderator|owner|nabd|vanta|claude)'
    -- spam: one character 15+ times in a row, or a 2-6 character chunk repeated 8+ times
    or raw ~ '(.)\1{14,}'
    or raw ~ '(..)\1{7}|(...)\2{7}|(....)\3{7}|(.....)\4{7}|(......)\5{7}'
  from t
$$;
revoke all on function private.needs_review(text, text) from public, anon, authenticated;

-- One "visitor" = one IPv4 address or one IPv6 /48 network (a single home/VPS gets a whole
-- /64 or more, so counting full IPv6 addresses would let one person act as many).
-- Salt of past days is wiped, so stored hashes cannot be linked back after the day ends.
create or replace function private.visitor_hash()
returns text language plpgsql volatile security definer set search_path = '' as $$
declare v_ip text; v_net text; v_salt text;
begin
  v_ip := lower(btrim(coalesce(current_setting('request.headers', true)::json ->> 'cf-connecting-ip', '')));
  if v_ip !~ '^[0-9a-f:.]{3,45}$' then return null; end if;
  begin
    v_net := case when v_ip like '%:%' then network(set_masklen(v_ip::inet, 48))::text else host(v_ip::inet) end;
  exception when others then
    return null;
  end;
  insert into private.daily_salt (day, salt) values (current_date, encode(extensions.gen_random_bytes(16), 'hex')) on conflict do nothing;
  update private.daily_salt set salt = '' where day < current_date and salt <> '';
  select s.salt into v_salt from private.daily_salt s where s.day = current_date;
  return encode(extensions.digest(convert_to(v_salt || '|' || v_net, 'UTF8'), 'sha256'), 'hex');
end $$;
revoke all on function private.visitor_hash() from public, anon, authenticated;

-- ---------- visitors ----------
-- Returns 'ok' (published now), 'held' (waits for the owner) or the same error codes as submit_comment.
create or replace function public.post_comment(p_mod text, p_kind text, p_body text, p_nickname text default null, p_device text default null)
returns text language plpgsql volatile security definer set search_path = '' as $$
declare r text; v_id bigint; v_body text; v_flag boolean;
begin
  -- same size guard as submit_comment, then the (CPU-heavier) word check BEFORE the site lock
  if octet_length(p_body) > 8000 or octet_length(p_nickname) > 400 or octet_length(p_mod) > 200
     or octet_length(p_kind) > 20 or octet_length(p_device) > 20 then return 'too_long'; end if;
  v_flag := private.needs_review(private.clean_text(p_body, 600), nullif(private.clean_text(p_nickname, 30), ''));
  r := public.submit_comment(p_mod, p_kind, p_body, p_nickname, p_device);  -- all checks + limits + insert (pending)
  if r <> 'ok' then return r; end if;
  -- submit_comment holds the advisory lock until this transaction ends, so the newest
  -- pending row for this mod is the one just inserted.
  select c.id, c.body into v_id, v_body from public.comments c
    where c.status = 'pending' and c.mod_id = lower(btrim(p_mod)) order by c.id desc limit 1;
  if v_id is null then return 'held'; end if;
  if v_flag or exists (select 1 from public.comments c where c.id <> v_id and c.mod_id = lower(btrim(p_mod))
                       and c.body = v_body and c.created_at > now() - interval '1 day')
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

-- 'ok' | 'already' | 'limit' | 'not_found'. One vote per visitor network; 20 per visitor and
-- 300 site-wide per day (keeps the table small); row lock so parallel reports count correctly.
create or replace function public.report_comment(p_pub_id uuid)
returns text language plpgsql volatile security definer set search_path = '' as $$
declare v_who text; v_id bigint; v_auto boolean; n int;
begin
  v_who := private.visitor_hash();
  if v_who is null then return 'limit'; end if;
  perform pg_advisory_xact_lock(4243, hashtext(v_who));
  select c.id, c.auto into v_id, v_auto from public.comments c
    where c.pub_id = p_pub_id and c.status = 'approved' for update;
  if v_id is null then return 'not_found'; end if;
  if (select count(*) from private.reports r where r.who = v_who and r.at > now() - interval '1 day') >= 20 then return 'limit'; end if;
  if (select count(*) from private.reports r where r.at > now() - interval '1 day') >= 300 then return 'limit'; end if;
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

-- Approve (pending) or keep (already published): published by the owner's hand, reports reset,
-- and reports can no longer hide it.
create or replace function public.mod_approve(p_key text, p_id bigint)
returns text language plpgsql volatile security definer set search_path = '' as $$
begin
  if not private.key_ok(p_key) then raise exception 'not allowed' using errcode = '42501'; end if;
  update public.comments
     set status = 'approved', approved_at = case when status = 'pending' then now() else approved_at end, auto = false, reports = 0
   where id = p_id;
  return case when found then 'ok' else 'not_found' end;
end $$;

-- Visitors now use post_comment / comments_for; the old entry points are closed to them.
revoke all on function public.submit_comment(text, text, text, text, text) from public, anon, authenticated;
revoke all on function public.list_comments(text) from public, anon, authenticated;
revoke all on function public.post_comment(text, text, text, text, text) from public;
revoke all on function public.comments_for(text) from public;
revoke all on function public.report_comment(uuid) from public;
revoke all on function public.mod_items(text, text, bigint) from public;
revoke all on function public.mod_approve(text, bigint) from public;
grant execute on function public.post_comment(text, text, text, text, text) to anon, authenticated;
grant execute on function public.comments_for(text) to anon, authenticated;
grant execute on function public.report_comment(uuid) to anon, authenticated;
grant execute on function public.mod_items(text, text, bigint) to anon, authenticated;
grant execute on function public.mod_approve(text, bigint) to anon, authenticated;
