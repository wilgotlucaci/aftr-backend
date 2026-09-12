"""Sends Apple Push Notification service (APNs) updates to a Live Activity.

This is what makes the Lock Screen "End Night" button show an immediate
"Night Ended" confirmation: the button's own process (AFTRWidgets'
EndNightIntent) can't reliably touch the Activity object itself - see
that file's docstring - so instead the backend pushes the update directly
to Apple's servers once it has actually ended the Night, and iOS applies
it to the Live Activity regardless of which device/process triggered it.

Requires APNS_KEY_ID, APNS_TEAM_ID and APNS_AUTH_KEY (the .p8 key's PEM
contents) to be set - see the "AFTR outstanding user actions" project
notes for how to generate those in the Apple Developer portal. Silently
does nothing if they aren't configured, since Live Activity confirmation
is a nice-to-have, not something that should ever block ending a Night.
"""

import os
import time

import httpx
import jwt

APNS_KEY_ID = os.environ.get("APNS_KEY_ID")
APNS_TEAM_ID = os.environ.get("APNS_TEAM_ID")
APNS_AUTH_KEY = os.environ.get("APNS_AUTH_KEY")
APNS_BUNDLE_ID = os.environ.get("APNS_BUNDLE_ID", "com.wilgot.AFTR")

# Personal/free Apple Developer team + Xcode "Run" installs always use the
# sandbox APNs environment. Only a Release build distributed through
# TestFlight/the App Store uses production - flip this once AFTR is
# actually distributed that way.
APNS_ENVIRONMENT = os.environ.get("APNS_ENVIRONMENT", "sandbox")

_APNS_HOSTS = {
    "sandbox": "https://api.sandbox.push.apple.com",
    "production": "https://api.push.apple.com",
}

# Foundation's default `Date` Codable conformance encodes/decodes as
# `timeIntervalSinceReferenceDate` (seconds since 2001-01-01), NOT Unix
# epoch - our `ContentState.startedAt` has no custom Date strategy, so a
# push's content-state must use this reference date, even though the
# `aps.timestamp` / `aps.dismissal-date` fields below are plain Unix time.
_SWIFT_REFERENCE_DATE_OFFSET = 978_307_200

_cached_provider_token: str | None = None
_cached_provider_token_issued_at: float = 0


def _provider_token() -> str:
    """A JWT signed with the APNs Auth Key. Valid up to an hour - Apple
    asks that you reuse one rather than minting a new one per push."""
    global _cached_provider_token, _cached_provider_token_issued_at

    now = time.time()
    if (
        _cached_provider_token
        and now - _cached_provider_token_issued_at < 60 * 50
    ):
        return _cached_provider_token

    if not (APNS_KEY_ID and APNS_TEAM_ID and APNS_AUTH_KEY):
        raise RuntimeError(
            "APNS_KEY_ID / APNS_TEAM_ID / APNS_AUTH_KEY are not configured"
        )

    _cached_provider_token = jwt.encode(
        {"iss": APNS_TEAM_ID, "iat": int(now)},
        APNS_AUTH_KEY,
        algorithm="ES256",
        headers={"kid": APNS_KEY_ID},
    )
    _cached_provider_token_issued_at = now
    return _cached_provider_token


def is_configured() -> bool:
    return bool(APNS_KEY_ID and APNS_TEAM_ID and APNS_AUTH_KEY)


def send_live_activity_end(
    push_token: str,
    night_title: str,
    started_at_unix: float,
    dismiss_after_seconds: float = 8,
) -> None:
    """Pushes the "ended" content state to a running Live Activity and
    tells it to dismiss itself shortly after."""

    url = f"{_APNS_HOSTS[APNS_ENVIRONMENT]}/3/device/{push_token}"
    now = time.time()

    payload = {
        "aps": {
            "timestamp": int(now),
            "event": "end",
            "content-state": {
                "nightTitle": night_title,
                "startedAt": started_at_unix - _SWIFT_REFERENCE_DATE_OFFSET,
                "isEnded": True,
            },
            "dismissal-date": int(now + dismiss_after_seconds),
        }
    }

    headers = {
        "authorization": f"bearer {_provider_token()}",
        "apns-topic": f"{APNS_BUNDLE_ID}.push-type.liveactivity",
        "apns-push-type": "liveactivity",
        "apns-priority": "10",
    }

    with httpx.Client(http2=True, timeout=10) as client:
        response = client.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(
            f"APNs push failed: {response.status_code} {response.text}"
        )
