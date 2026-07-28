-- Run this in the Supabase SQL editor to create the schema.
-- Not wired up to the app yet — db/repository.py runs against in-memory
-- fake data until SUPABASE_URL / SUPABASE_KEY are set.

create table watchlist_items (
    id uuid primary key default gen_random_uuid(),
    name text not null,                    -- keyword to search for
    site text not null,                    -- e.g. 'nellis'
    location text,                         -- e.g. 'mesa' / 'phoenix' / 'both', null = any
    price_ceiling numeric,                 -- null = no limit
    size text,                             -- unused for now
    created_at timestamptz not null default now()
);

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
