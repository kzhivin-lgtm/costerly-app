-- Stage 1, strictly additive: only three new tables, indexes, and their RLS.
-- No existing RFQ/company row or policy is changed. No function is replaced.
begin;

do $$
begin
    if to_regclass('public.companies') is null or not exists (
        select 1 from information_schema.columns
        where table_schema = 'public' and table_name = 'companies'
          and column_name = 'company_name'
    ) then
        raise exception 'Existing companies table with company_name is required';
    end if;
    if to_regclass('public.company_members') is not null
       or to_regclass('public.company_creation_invites') is not null
       or to_regclass('public.company_join_links') is not null then
        raise exception 'At least one account/invitation table already exists; stop and recheck';
    end if;
end $$;

create table public.company_members (
    user_id uuid primary key references auth.users(id),
    company_id text not null references public.companies(company_id),
    role text not null check (role in ('owner', 'member')),
    joined_at timestamptz not null default now()
);

create index company_members_company_id_idx
    on public.company_members(company_id);
create unique index company_members_one_owner_idx
    on public.company_members(company_id) where role = 'owner';

create table public.company_creation_invites (
    token_hash text primary key,
    join_token text not null unique,
    label text,
    used_at timestamptz,
    created_company_id text references public.companies(company_id),
    created_at timestamptz not null default now()
);

create table public.company_join_links (
    company_id text primary key references public.companies(company_id),
    join_token text not null unique,
    created_at timestamptz not null default now()
);

alter table public.company_members enable row level security;
alter table public.company_creation_invites enable row level security;
alter table public.company_join_links enable row level security;
grant all on public.company_members, public.company_creation_invites,
    public.company_join_links to service_role;

commit;
