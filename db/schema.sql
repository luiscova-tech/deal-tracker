-- Run this in the Supabase SQL editor to create the schema.
-- Not wired up to the app yet — db/repository.py runs against in-memory
-- fake data until SUPABASE_URL / SUPABASE_KEY are set.
--
-- Multi-user: profiles and watchlist_items are owned by an auth.users row
-- and locked down with Row Level Security, so each user only ever sees
-- their own data through the client-side (anon/authenticated) key.
-- seen_items and bid_reminders are only ever touched by the scheduled job,
-- which connects with the service role key — that key bypasses RLS
-- entirely, so there's no policy to write for those two tables.

create table profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    email text not null,
    ntfy_topic text,
    created_at timestamptz not null default now()
);

alter table profiles enable row level security;

create policy "Users can manage their own profile"
    on profiles
    for all
    using (auth.uid() = id)
    with check (auth.uid() = id);

create table watchlist_items (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    name text not null,                    -- keyword to search for
    site text not null,                    -- e.g. 'nellis'
    location text,                         -- e.g. 'mesa' / 'phoenix' / 'both', null = any
    price_ceiling numeric,                 -- null = no limit
    size text,                             -- unused for now
    created_at timestamptz not null default now()
);

alter table watchlist_items enable row level security;

create policy "Users can manage their own watchlist items"
    on watchlist_items
    for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- seen_items and bid_reminders are written solely by the scheduled job via
-- the service role key, which bypasses RLS regardless. seen_items later
-- gets a read-only policy below once the dashboard needs to read it
-- directly; bid_reminders still has none as of this writing.

create table seen_items (
    id uuid primary key default gen_random_uuid(),
    watchlist_item_id uuid not null references watchlist_items (id) on delete cascade,
    site_item_id text not null,            -- the site's own id for this listing
    first_seen_at timestamptz not null default now(),
    unique (watchlist_item_id, site_item_id)
);

create table bid_reminders (
    id uuid primary key default gen_random_uuid(),
    watchlist_item_id uuid not null references watchlist_items (id) on delete cascade,
    remind_at timestamptz not null,
    sent boolean not null default false
);

create index seen_items_watchlist_item_id_idx on seen_items (watchlist_item_id);
create index bid_reminders_due_idx on bid_reminders (remind_at) where not sent;
create index watchlist_items_user_id_idx on watchlist_items (user_id);

-- Match history: persist listing details on seen_items so a future dashboard
-- can show recent matches without re-fetching from the site. seen_items
-- already exists in production, so these are separate alter statements
-- rather than edits to the create table above — run manually.
alter table seen_items add column title text;
alter table seen_items add column price numeric;
alter table seen_items add column url text;

-- Auto-create a profiles row whenever someone signs up, so the app never
-- has to handle "no profile yet" for a new user. security definer is
-- required: this runs as part of the internal auth.users insert, not as
-- the new user's own authenticated request, so it must bypass profiles'
-- RLS policy rather than satisfy it. search_path is pinned to prevent a
-- search_path-hijacking attack against a security definer function.
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, email)
    values (new.id, new.email);
    return new;
end;
$$;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- Recent-matches dashboard section reads seen_items directly via the
-- RLS-scoped (publishable key) client, so it needs its own policy — it had
-- none before since only the service-role-key backend ever touched it.
-- seen_items has no user_id column of its own, so the check goes through
-- its parent watchlist_item. Read-only: the backend still writes via the
-- service role key, which bypasses this regardless.
alter table seen_items enable row level security;

create policy "Users can view their own matches"
    on seen_items
    for select
    using (
        auth.uid() = (select user_id from watchlist_items where id = seen_items.watchlist_item_id)
    );
