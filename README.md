# AFTR — Backend

> Live tonight. Remember tomorrow.

FastAPI + Supabase service that turns a night out into an entertaining
recap: it ingests location pings while a **Night** is active, then on
**End Night** detects social moments, resolves venues, computes movement
stats, and has Claude write the "AFTR SAYS" highlights.

The iOS client lives in the sibling `AFTR` repo.

---

## Requirements

- Python 3.13
- A Supabase project (Postgres + Auth)
- A Google Places API key (venue resolution)
- An Anthropic API key (recap highlights) — <https://console.anthropic.com>

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env      # then fill in the four keys
```

Create the database tables from [`database/schema.sql`](database/schema.sql)
in the Supabase SQL editor. `users.auth_user_id` maps each row to a
Supabase Auth user.

## Run

```bash
.venv/bin/uvicorn api:app --reload
```

API is then at `http://127.0.0.1:8000` (`/docs` for the interactive spec).

## Test

```bash
.venv/bin/python -m pytest
```

The suite (`tests/`) covers the pure recap logic — event detectors,
route building, movement classification, fun-facts extraction, join
codes, and the "a failing section never breaks End Night" guarantee. It
needs no network or credentials.

`python main.py` builds and prints a recap for the latest finished Night
(or `python main.py <night_id>`). `mock_night.py` is a hand-built
6-person / 4-venue Night used by the tests and for local experiments.

---

## How a recap is built

```
Night (participants + location_points)
  │
  ├─ event detection        events/*.py         group splits, houdini,
  │                                              side quests, reunions,
  │                                              dynamic duo, most
  │                                              independent, early
  │                                              checkout, late arrivals,
  │                                              most distance
  ├─ venue timeline          utils/venue_*.py    GPS clusters → Google
  │                                              Places, with confidence
  ├─ movement stats          utils/movement.py   stationary / walking /
  │                                              fast / vehicle minutes
  ├─ route                   utils/route.py      per-participant polyline
  │
  ├─ fun facts               utils/fun_recap.py  flatten the above into
  │                                              candidate "facts"
  └─ fun highlights          utils/fun_copy.py   Claude picks the best
                                                 3–5 and writes the copy
```

Every section runs through `recap._safe()` — if one raises (Google down,
no AI credits, bad data) it is logged and falls back to an empty result,
so **ending a Night always succeeds** and the recap is still saved.

The recap model used for AI copy is set in one place:
[`utils/fun_copy.py`](utils/fun_copy.py) → `MODEL` (currently
`claude-haiku-4-5`).

## API

| Method | Path | Notes |
|---|---|---|
| `GET`  | `/` | health check |
| `GET`  | `/me` | current AFTR user |
| `GET`  | `/nights` | the caller's Nights |
| `POST` | `/nights` | create a Night `{title}` |
| `POST` | `/nights/join` | join an active Night `{code}` (6-char) |
| `POST` | `/nights/{id}/participants` | join by id |
| `GET`  | `/nights/{id}` | detail + `join_code` + participants |
| `POST` | `/nights/{id}/locations` | ingest a location ping |
| `POST` | `/nights/{id}/end` | end + generate + save the recap |
| `GET`  | `/nights/{id}/recap` | the saved recap |
| `POST` | `/nights/{id}/recap/generate` | regenerate (host only) |

All routes except `/` require a Supabase bearer token; the user is
resolved in [`auth/current_user.py`](auth/current_user.py).

## Layout

```
api.py                 FastAPI routes
recap.py               build_recap orchestration + _safe wrapper
models.py              pydantic domain models
main.py                local "print a recap" helper
database/              Supabase client + schema.sql
auth/                  bearer-token → AFTR user
repositories/          one module per table
events/                one detector per social moment
utils/                 venue resolution, movement, route, fun facts, AI copy
tests/                 pytest suite
```

## Notes / TODO

- `.env` is gitignored; never commit real keys. If keys were ever
  committed, rotate them.
- Deployment: any Python host that can run `uvicorn api:app`
  (Railway / Render / Fly / a VPS). Set the four env vars there.
