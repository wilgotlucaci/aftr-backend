"""Import-level smoke test: the app builds and every route is wired.

Skipped when there is no .env, since importing `api` constructs the
Supabase client.
"""

import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(ROOT, ".env")),
    reason="needs .env for the Supabase client",
)


def test_app_imports_and_registers_every_route():
    import api

    paths = {route.path for route in api.app.routes}

    for expected in {
        "/",
        "/me",
        "/nights",
        "/nights/join",
        "/nights/{night_id}",
        "/nights/{night_id}/participants",
        "/nights/{night_id}/locations",
        "/nights/{night_id}/live-activity-token",
        "/nights/{night_id}/end",
        "/nights/{night_id}/recap",
        "/nights/{night_id}/recap/generate",
    }:
        assert expected in paths, f"missing route: {expected}"
