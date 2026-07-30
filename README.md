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
  -> list[Listing]` (see `adapters/base.py`). `adapters/nellis.py` hits Nellis's
  search endpoint directly; see "Nellis adapter" below.
- `core/` — site-agnostic logic: dedup against seen items, watchlist matching,
  reminder scheduling.
- `notifications/` — pluggable channels implementing `send(message, target)`:
  email (SMTP) and push (ntfy.sh).
- `db/` — Supabase client + data access layer (`repository.py`). Schema lives
  in `db/schema.sql`.
- `main.py` — entrypoint the GitHub Actions workflow calls.

## Status

- **Nellis adapter** (`adapters/nellis.py`) is implemented and hits the real
  site — see "Nellis adapter" below for what it needs to actually return results.
- **Supabase** (`db/`) has a schema and client set up, but no project is
  wired in yet. Until `SUPABASE_URL` / `SUPABASE_KEY` are set, `db/repository.py`
  transparently runs against a couple of fake in-memory watchlist items instead,
  so the whole pipeline is runnable today.

## Nellis adapter

Hits `GET nellisauction.com/search?query=<keyword>&_data=routes/search`
directly — no login required, confirmed via DevTools. Results are scoped by
a `__shopping-location` cookie; without it Nellis defaults to Las Vegas and
returns zero Mesa/Phoenix results, so the adapter treats a missing
`NELLIS_SHOPPING_LOCATION_COOKIE` env var as a hard stop (logs a warning,
returns `[]`) rather than silently querying the wrong region. That cookie is
a location preference, not a login credential — see `.env.example` for how
to grab its value from your browser, and note it's currently only good
until 2027-09-02.

The API has no product-URL field, so `adapters/nellis.py` builds one from
the numeric id (`/p/<slug>/<id>`) — Nellis's own router only actually looks
up the trailing id, ignoring the slug, which was confirmed by loading a
product page with a deliberately wrong slug.

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in what you have; unset vars just disable that piece
python main.py
```

With a blank `.env`, the Nellis adapter has no shopping-location cookie to
work with, so it logs a warning and returns no listings — the fake watchlist
still runs through the rest of the pipeline end-to-end, so you can see it
execute before any real credentials exist. Set `NELLIS_SHOPPING_LOCATION_COOKIE`
to get real results back.

Run the tests (mocked — no real network calls) with:

```bash
python -m unittest discover -s tests
```

## Data model

See `db/schema.sql`. Three tables: `watchlist_items` (what to look for),
`seen_items` (dedup log, one row per listing ever matched to a watchlist item),
and `bid_reminders` (one-off reminders to check back on a bid).

## Frontend

`web/` is a Next.js (App Router + TypeScript + Tailwind) app, kept in this
repo rather than a separate one. Right now it's just auth: `/login` sends a
Supabase magic link, and a protected `/dashboard` placeholder proves the
session works end-to-end (shows the logged-in user's email). Watchlist CRUD
and match history are next.

```bash
cd web
cp .env.local.example .env.local   # fill in your Supabase project URL + publishable key
npm install
npm run dev
```

## Next steps

1. Create the Supabase project and run `db/schema.sql`.
2. Add real watchlist items and point `.env` at real SMTP / ntfy.sh / Nellis
   cookie config.
3. Build out `web/dashboard`: watchlist CRUD and match history.
