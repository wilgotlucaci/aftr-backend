"""Thin wrapper over Supabase Storage for the private `night-media`
bucket. Uploads go through the backend (service-role key) so the client
never needs Storage RLS policies.
"""

import os
import uuid

import requests
from dotenv import load_dotenv


load_dotenv()


BUCKET = "night-media"

EXTENSION_BY_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/heic": "heic",
    "image/heif": "heif",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
}


def _credentials() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_KEY missing from .env")

    return url, key


def storage_path(
    night_id: str,
    user_id: str,
    content_type: str,
) -> str:
    extension = EXTENSION_BY_TYPE.get(content_type, "bin")
    return f"{night_id}/{user_id}/{uuid.uuid4().hex}.{extension}"


def upload_media(
    path: str,
    content: bytes,
    content_type: str,
) -> None:
    url, key = _credentials()

    response = requests.post(
        f"{url}/storage/v1/object/{BUCKET}/{path}",
        headers={
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": content_type,
        },
        data=content,
        timeout=30,
    )

    response.raise_for_status()


def signed_url(
    path: str,
    expires_in: int = 3600,
) -> str | None:
    url, key = _credentials()

    response = requests.post(
        f"{url}/storage/v1/object/sign/{BUCKET}/{path}",
        headers={
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/json",
        },
        json={"expiresIn": expires_in},
        timeout=15,
    )

    if not response.ok:
        return None

    signed = response.json().get("signedURL")

    if not signed:
        return None

    # signedURL comes back as "/object/sign/<bucket>/<path>?token=..."
    return f"{url}/storage/v1{signed}"
