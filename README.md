# deal-tracker

Automated multi-site item watcher with price/location filters and notifications
(starting with Nellis Auction).

## How it works

```
watchlist_items (Supabase)
        │
        ▼
adapters/<site>.py   fetch_listings(filters) -> list[Listing]
        │
        ▼
core/dedup.py        drop listings already in seen_items
        │
        ▼
core/matcher.py       check keyword / location / price_ceiling
        │
        ▼
notifications/*      send(message, target) — email and/or ntfy.sh
```

`main.py` runs this loop once per invocation, then checks `bid_reminders` for
anything due and fires those too. GitHub Actions (`.github/workflows/check.yml`)
calls `main.py` every 15 minutes.

## Layout

- `adapters/` — one module per site, each implementing `fetch_listings(filters)
  -> list[Listing]` (see `adapters/base.py`). `adapters/nellis.py` is currently
  a stub that always returns `[]`.
- `core/` — site-agnostic logic: dedup against seen items, watchlist matching,
  reminder scheduling.
- `notifications/` — pluggable channels implementing `send(message, target)`:
  email (SMTP) and push (ntfy.sh).
- `db/` — Supabase client + data access layer (`repository.py`). Schema lives
  in `db/schema.sql`.
- `main.py` — entrypoint the GitHub Actions workflow calls.

## Status

Not yet connected to anything real:

- **Nellis adapter** (`adapters/nellis.py`) always returns no listings —
  the actual API/scrape call is next, once we've inspected Nellis's network
  traffic together.
- **Supabase** (`db/`) has a schema and client set up, but no project is
  wired in yet. Until `SUPABASE_URL` / `SUPABASE_KEY` are set, `db/repository.py`
  transparently runs against a couple of fake in-memory watchlist items instead,
  so the whole pipeline is runnable today.

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in what you have; unset vars just disable that piece
python main.py
```

With a blank `.env`, this runs the fake watchlist through the (empty) Nellis
adapter and logs what it would have notified, so you can see the pipeline
execute end-to-end before any real credentials exist.

## Data model

See `db/schema.sql`. Three tables: `watchlist_items` (what to look for),
`seen_items` (dedup log, one row per listing ever matched to a watchlist item),
and `bid_reminders` (one-off reminders to check back on a bid).

## Next steps

1. Inspect Nellis Auction's network traffic to find the real listings
   endpoint, then implement `adapters/nellis.py`.
2. Create the Supabase project and run `db/schema.sql`.
3. Add real watchlist items and point `.env` at real SMTP / ntfy.sh config.
