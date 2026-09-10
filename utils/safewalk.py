"""Optional "get home safe" share links.

A safe walk is a small JSON document in a public storage bucket, keyed
by an unguessable token. The owner's phone pings its location while
they head home; anyone with the link sees the latest position and
whether they've made it. No database table needed.
"""

import json
import os
import secrets
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv


load_dotenv()

BUCKET = "safewalks"


def _credentials() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_KEY missing")
    return url, key


def _ensure_bucket() -> None:
    url, key = _credentials()
    requests.post(
        f"{url}/storage/v1/bucket",
        headers={
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/json",
        },
        json={"id": BUCKET, "name": BUCKET, "public": True},
        timeout=10,
    )  # 200 or 409 (already exists) - both fine


def _write(token: str, doc: dict) -> None:
    url, key = _credentials()
    _ensure_bucket()
    response = requests.post(
        f"{url}/storage/v1/object/{BUCKET}/{token}.json",
        headers={
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/json",
            "x-upsert": "true",
        },
        data=json.dumps(doc),
        timeout=15,
    )
    response.raise_for_status()


def read(token: str) -> dict | None:
    url, _ = _credentials()
    response = requests.get(
        f"{url}/storage/v1/object/public/{BUCKET}/{token}.json",
        timeout=10,
    )
    return response.json() if response.ok else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create(name: str | None) -> str:
    token = secrets.token_urlsafe(12)
    _write(
        token,
        {
            "name": (name or "Someone").strip() or "Someone",
            "status": "walking",
            "latitude": None,
            "longitude": None,
            "started_at": _now(),
            "updated_at": _now(),
        },
    )
    return token


def ping(token: str, latitude: float, longitude: float) -> None:
    doc = read(token) or {"name": "Someone", "started_at": _now()}
    doc["latitude"] = latitude
    doc["longitude"] = longitude
    doc["status"] = doc.get("status") or "walking"
    doc["updated_at"] = _now()
    _write(token, doc)


def arrive(token: str) -> None:
    doc = read(token) or {"name": "Someone", "started_at": _now()}
    doc["status"] = "home"
    doc["updated_at"] = _now()
    _write(token, doc)


def render_page(token: str) -> str | None:
    doc = read(token)
    if doc is None:
        return None

    name = doc.get("name", "Someone")
    home = doc.get("status") == "home"
    lat = doc.get("latitude")
    lon = doc.get("longitude")
    updated = doc.get("updated_at", "")

    if lat is not None and lon is not None:
        span = 0.01
        bbox = f"{lon - span},{lat - span},{lon + span},{lat + span}"
        map_html = (
            f'<iframe title="map" loading="lazy" '
            f'src="https://www.openstreetmap.org/export/embed.html?'
            f'bbox={bbox}&marker={lat},{lon}"></iframe>'
            f'<a class="maps" href="https://maps.apple.com/?ll={lat},{lon}">'
            f'Open in Maps</a>'
        )
    else:
        map_html = '<p class="muted">Waiting for the first location…</p>'

    headline = (
        f"{name} made it home safe"
        if home
        else f"{name} is heading home"
    )
    accent = "#39d98a" if home else "#ff1a94"
    refresh = "" if home else '<meta http-equiv="refresh" content="20">'

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{refresh}
<title>{headline}</title>
<style>
  :root{{color-scheme:dark}}
  body{{margin:0;background:#0a0a0c;color:#fff;
       font:16px/1.5 -apple-system,system-ui,sans-serif;
       display:flex;min-height:100vh;align-items:center;justify-content:center;padding:24px}}
  .card{{width:100%;max-width:420px}}
  h1{{font-size:1.4rem;margin:0 0 4px;color:{accent}}}
  .muted{{color:#8a8a92;font-size:.9rem}}
  iframe{{width:100%;height:300px;border:0;border-radius:16px;margin:16px 0 12px;
         background:#141418}}
  .maps{{display:inline-block;color:{accent};text-decoration:none;font-weight:600}}
  .foot{{margin-top:22px;color:#5a5a62;font-size:.8rem;letter-spacing:.12em;text-transform:uppercase}}
</style></head><body>
<div class="card">
  <h1>{headline}</h1>
  <p class="muted">Updated {updated[11:19] or "just now"} UTC · shared from AFTR</p>
  {map_html}
  <p class="foot">AFTR — get home safe</p>
</div></body></html>"""
