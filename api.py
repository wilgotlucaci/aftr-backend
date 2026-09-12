from datetime import datetime, timezone

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from auth.current_user import get_auth_user, get_current_user
from recap import build_serialized_recap
from wrap import build_wrap
from utils import apns, safewalk
from utils.join_code import (
    JOIN_CODE_LENGTH,
    night_join_code,
    normalise_join_code,
)
from utils.storage import (
    EXTENSION_BY_TYPE,
    signed_url,
    storage_path,
    upload_media,
)
from repositories.location_repository import LocationRepository
from repositories.media_repository import MediaRepository
from repositories.night_repository import NightRepository
from repositories.participant_repository import ParticipantRepository
from repositories.personal_location_repository import (
    PersonalLocationRepository,
)
from repositories.recap_repository import RecapRepository
from repositories.user_repository import UserRepository


app = FastAPI(
    title="AFTR API",
    version="0.1.0",
)

night_repository = NightRepository()
participant_repository = ParticipantRepository()
location_repository = LocationRepository()
recap_repository = RecapRepository()
media_repository = MediaRepository()
user_repository = UserRepository()
personal_location_repository = PersonalLocationRepository()

MAX_MEDIA_BYTES = 50 * 1024 * 1024


def _require_night_access(night_id: str, user_id: str):
    """Load a Night and 403 unless the user is a participant or the host."""
    night = night_repository.get_by_id(night_id)

    if night is None:
        raise HTTPException(
            status_code=404,
            detail="Night not found",
        )

    is_participant = participant_repository.is_in_night(
        night_id=night_id,
        user_id=user_id,
    )

    is_owner = night.owner_user_id == user_id

    if not is_participant and not is_owner:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this Night",
        )

    return night


class RegisterRequest(BaseModel):
    name: str


class CreateNightRequest(BaseModel):
    title: str


class JoinNightRequest(BaseModel):
    code: str


class LiveActivityTokenRequest(BaseModel):
    push_token: str


class CreateLocationRequest(BaseModel):
    latitude: float
    longitude: float
    speed: float | None = None
    horizontal_accuracy: float | None = None


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "AFTR API",
    }


@app.get("/me")
def get_me(
    current_user=Depends(get_current_user),
):
    return current_user


@app.post("/users")
def register(
    request: RegisterRequest,
    auth_user=Depends(get_auth_user),
):
    """Create the AFTR user row for a freshly signed-up Supabase account.
    Idempotent - returns the existing row if it already exists."""
    existing = user_repository.get_by_auth_user_id(
        str(auth_user.id)
    )

    if existing is not None:
        return existing

    name = request.name.strip() or "Someone"

    user = user_repository.create(
        auth_user_id=str(auth_user.id),
        name=name,
    )

    if user is None:
        raise HTTPException(
            status_code=500,
            detail="Could not create AFTR user",
        )

    return user


@app.get("/nights")
def get_nights(
    current_user=Depends(get_current_user),
):
    nights = night_repository.get_for_user(
        current_user["id"]
    )

    return [
        {
            "id": night["id"],
            "title": night["title"],
            "started_at": night["started_at"],
            "ended_at": night["ended_at"],
            "status": night["status"],
            "owner_user_id": night["owner_user_id"],
        }
        for night in nights
    ]


@app.post("/nights")
def create_night(
    request: CreateNightRequest,
    current_user=Depends(get_current_user),
):
    night = night_repository.create(
        title=request.title,
        started_at=datetime.now()
        .astimezone()
        .isoformat(),
        owner_user_id=current_user["id"],
        status="active",
    )

    if night is None:
        raise HTTPException(
            status_code=500,
            detail="Could not create Night",
        )

    return night


@app.post("/nights/join")
def join_night_by_code(
    request: JoinNightRequest,
    current_user=Depends(get_current_user),
):
    code = normalise_join_code(request.code)

    if len(code) < JOIN_CODE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="Invalid Night code",
        )

    match = next(
        (
            night
            for night in night_repository.get_active()
            if night_join_code(night["id"]) == code
        ),
        None,
    )

    if match is None:
        raise HTTPException(
            status_code=404,
            detail="No active Night with that code",
        )

    already_in = participant_repository.is_in_night(
        night_id=match["id"],
        user_id=current_user["id"],
    )

    if not already_in:
        participant = participant_repository.add_to_night(
            night_id=match["id"],
            user_id=current_user["id"],
            joined_at=datetime.now()
            .astimezone()
            .isoformat(),
        )

        if participant is None:
            raise HTTPException(
                status_code=500,
                detail="Could not join Night",
            )

    return {
        "id": match["id"],
        "title": match["title"],
        "started_at": match["started_at"],
        "ended_at": match["ended_at"],
        "status": match["status"],
        "owner_user_id": match["owner_user_id"],
        "join_code": night_join_code(match["id"]),
    }


@app.post("/nights/{night_id}/participants")
def join_night(
    night_id: str,
    current_user=Depends(get_current_user),
):
    night = night_repository.get_by_id(
        night_id
    )

    if night is None:
        raise HTTPException(
            status_code=404,
            detail="Night not found",
        )

    participant = participant_repository.add_to_night(
        night_id=night_id,
        user_id=current_user["id"],
        joined_at=datetime.now()
        .astimezone()
        .isoformat(),
    )

    if participant is None:
        raise HTTPException(
            status_code=500,
            detail="Could not add participant",
        )

    return participant


@app.post("/nights/{night_id}/locations")
def create_location(
    night_id: str,
    request: CreateLocationRequest,
    current_user=Depends(get_current_user),
):
    night = night_repository.get_by_id(
        night_id
    )

    if night is None:
        raise HTTPException(
            status_code=404,
            detail="Night not found",
        )

    if night.status.value != "active":
        raise HTTPException(
            status_code=409,
            detail="Night is not active",
        )

    is_participant = participant_repository.is_in_night(
        night_id=night_id,
        user_id=current_user["id"],
    )

    if not is_participant:
        raise HTTPException(
            status_code=403,
            detail="You are not a participant in this Night",
        )

    location = location_repository.create(
        night_id=night_id,
        user_id=current_user["id"],
        recorded_at=datetime.now()
        .astimezone()
        .isoformat(),
        latitude=request.latitude,
        longitude=request.longitude,
        speed=request.speed,
        horizontal_accuracy=request.horizontal_accuracy,
    )

    if location is None:
        raise HTTPException(
            status_code=500,
            detail="Could not save location",
        )

    return location


@app.get("/nights/{night_id}")
def get_night(
    night_id: str,
    current_user=Depends(get_current_user),
):
    night = night_repository.get_by_id(
        night_id
    )

    if night is None:
        raise HTTPException(
            status_code=404,
            detail="Night not found",
        )

    is_participant = participant_repository.is_in_night(
        night_id=night_id,
        user_id=current_user["id"],
    )

    is_owner = (
        night.owner_user_id
        == current_user["id"]
    )

    if not is_participant and not is_owner:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this Night",
        )

    return {
        "id": night.id,
        "title": night.title,
        "join_code": night_join_code(night.id),
        "started_at": night.started_at.isoformat(),
        "ended_at": (
            night.ended_at.isoformat()
            if night.ended_at
            else None
        ),
        "status": night.status.value,
        "owner_user_id": night.owner_user_id,
        "participant_count": len(
            night.participants
        ),
        "location_point_count": len(
            night.locations
        ),
        "participants": [
            {
                "id": participant.id,
                "name": participant.name,
            }
            for participant in night.participants
        ],
    }


@app.post("/nights/{night_id}/live-activity-token")
def set_live_activity_token(
    night_id: str,
    request: LiveActivityTokenRequest,
    current_user=Depends(get_current_user),
):
    """Stores the Lock Screen Live Activity's push token so /end can push
    an immediate "ended" update to it via APNs - see utils/apns.py."""
    _require_night_access(night_id, current_user["id"])

    night_repository.set_live_activity_push_token(
        night_id=night_id,
        push_token=request.push_token,
    )

    return {"status": "ok"}


@app.post("/nights/{night_id}/end")
def end_night(
    night_id: str,
    lang: str | None = None,
    current_user=Depends(get_current_user),
):
    night = night_repository.get_by_id(
        night_id
    )

    if night is None:
        raise HTTPException(
            status_code=404,
            detail="Night not found",
        )

    if (
        night.owner_user_id
        != current_user["id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Only the Night host can end this Night",
        )

    ended_night = night_repository.end(
        night_id=night_id,
        ended_at=datetime.now()
        .astimezone()
        .isoformat(),
    )

    if ended_night is None:
        raise HTTPException(
            status_code=500,
            detail="Could not end Night",
        )

    finished_night = (
        night_repository.get_by_id(
            night_id
        )
    )

    recap = build_serialized_recap(
        finished_night,
        language=lang,
    )

    recap_repository.save(
        night_id,
        recap,
    )

    _push_live_activity_end(night_id, finished_night)

    return {
        "night": ended_night,
        "recap_generated": True,
        "recap": recap,
    }


def _push_live_activity_end(night_id: str, night):
    """Best-effort - a Live Activity is a nice-to-have, so this must never
    fail the actual "end this Night" request."""
    if not apns.is_configured():
        return

    push_token = night_repository.get_live_activity_push_token(night_id)

    if not push_token:
        return

    try:
        apns.send_live_activity_end(
            push_token=push_token,
            night_title=night.title,
            started_at_unix=night.started_at.timestamp(),
        )
    except Exception as error:  # noqa: BLE001
        print(f"[apns] Failed to push Live Activity end for {night_id}: {error}")


@app.get("/nights/{night_id}/recap")
def get_night_recap(
    night_id: str,
    current_user=Depends(get_current_user),
):
    night = night_repository.get_by_id(
        night_id
    )

    if night is None:
        raise HTTPException(
            status_code=404,
            detail="Night not found",
        )

    is_participant = (
        participant_repository.is_in_night(
            night_id=night_id,
            user_id=current_user["id"],
        )
    )

    is_owner = (
        night.owner_user_id
        == current_user["id"]
    )

    if not is_participant and not is_owner:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this Night",
        )

    saved_recap = (
        recap_repository.get_by_night_id(
            night_id
        )
    )

    if saved_recap is None:
        raise HTTPException(
            status_code=404,
            detail="Recap not generated yet",
        )

    return saved_recap["recap_data"]


@app.post("/nights/{night_id}/recap/generate")
def generate_night_recap(
    night_id: str,
    lang: str | None = None,
    current_user=Depends(get_current_user),
):
    night = night_repository.get_by_id(
        night_id
    )

    if night is None:
        raise HTTPException(
            status_code=404,
            detail="Night not found",
        )

    if (
        night.owner_user_id
        != current_user["id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Only the Night host can generate the recap",
        )

    recap = build_serialized_recap(
        night,
        language=lang,
    )

    recap_repository.save(
        night_id,
        recap,
    )

    return recap


# ---------------------------------------------------------------------------
# Home location
# ---------------------------------------------------------------------------

class HomeLocationRequest(BaseModel):
    latitude: float
    longitude: float
    radius_meters: float | None = None


def _home_payload(row) -> dict | None:
    if row is None:
        return None
    return {
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "radius_meters": row["radius_meters"],
    }


@app.get("/me/home")
def get_home(current_user=Depends(get_current_user)):
    return _home_payload(
        personal_location_repository.get_named(
            current_user["id"], "home"
        )
    )


@app.put("/me/home")
def set_home(
    request: HomeLocationRequest,
    current_user=Depends(get_current_user),
):
    row = personal_location_repository.upsert_named(
        user_id=current_user["id"],
        name="home",
        latitude=request.latitude,
        longitude=request.longitude,
        radius_meters=request.radius_meters or 120,
    )
    if row is None:
        raise HTTPException(
            status_code=500,
            detail="Could not save home location",
        )
    return _home_payload(row)


@app.delete("/me/home")
def clear_home(current_user=Depends(get_current_user)):
    personal_location_repository.delete_named(
        current_user["id"], "home"
    )
    return {"ok": True}


# ---------------------------------------------------------------------------
# Monthly wrap
# ---------------------------------------------------------------------------

@app.get("/wrap")
def get_wrap(
    month: str | None = None,
    current_user=Depends(get_current_user),
):
    now = datetime.now(timezone.utc)

    if month:
        try:
            year, mon = (int(part) for part in month.split("-")[:2])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="month must be YYYY-MM",
            )
    else:
        year, mon = now.year, now.month

    start = datetime(year, mon, 1, tzinfo=timezone.utc)
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)

    start_iso = start.isoformat()
    end_iso = end.isoformat()

    nights = [
        night
        for night in night_repository.get_for_user(current_user["id"])
        if night["status"] == "finished"
        and night.get("started_at")
        and start_iso <= night["started_at"] < end_iso
    ]

    return build_wrap(
        current_user,
        f"{year:04d}-{mon:02d}",
        nights,
        recap_repository,
    )


# ---------------------------------------------------------------------------
# Get home safe (optional share links)
# ---------------------------------------------------------------------------

class SafeWalkStartRequest(BaseModel):
    name: str | None = None


class SafeWalkPingRequest(BaseModel):
    latitude: float
    longitude: float


@app.post("/safewalks")
def start_safewalk(
    request: SafeWalkStartRequest,
    fastapi_request: Request,
    current_user=Depends(get_current_user),
):
    token = safewalk.create(
        request.name or current_user.get("name")
    )
    base = str(fastapi_request.base_url).rstrip("/")
    return {"token": token, "url": f"{base}/s/{token}"}


@app.post("/safewalks/{token}/ping")
def ping_safewalk(
    token: str,
    request: SafeWalkPingRequest,
    current_user=Depends(get_current_user),
):
    safewalk.ping(token, request.latitude, request.longitude)
    return {"ok": True}


@app.post("/safewalks/{token}/arrive")
def arrive_safewalk(
    token: str,
    current_user=Depends(get_current_user),
):
    safewalk.arrive(token)
    return {"ok": True}


@app.get("/s/{token}", response_class=HTMLResponse)
def view_safewalk(token: str):
    page = safewalk.render_page(token)
    if page is None:
        return HTMLResponse(
            "<h1>This link has expired.</h1>",
            status_code=404,
        )
    return HTMLResponse(page)


@app.post("/nights/{night_id}/media")
async def add_media(
    night_id: str,
    file: UploadFile = File(...),
    taken_at: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    venue_name: str | None = Form(None),
    source_asset_id: str | None = Form(None),
    current_user=Depends(get_current_user),
):
    _require_night_access(night_id, current_user["id"])

    content_type = file.content_type or ""

    if content_type not in EXTENSION_BY_TYPE:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {content_type}",
        )

    content = await file.read()

    if len(content) > MAX_MEDIA_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File is larger than 50 MB",
        )

    path = storage_path(
        night_id,
        current_user["id"],
        content_type,
    )

    try:
        upload_media(path, content, content_type)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Storage upload failed: {error}",
        )

    media_type = (
        "video"
        if content_type.startswith("video/")
        else "image"
    )

    row = media_repository.create(
        night_id=night_id,
        user_id=current_user["id"],
        storage_path=path,
        media_type=media_type,
        taken_at=taken_at,
        latitude=latitude,
        longitude=longitude,
        venue_name=venue_name,
        source_asset_id=source_asset_id,
    )

    if row is None:
        raise HTTPException(
            status_code=500,
            detail="Could not save media",
        )

    return {
        "id": row["id"],
        "media_type": media_type,
        "url": signed_url(path),
    }


@app.get("/nights/{night_id}/media")
def list_media(
    night_id: str,
    current_user=Depends(get_current_user),
):
    _require_night_access(night_id, current_user["id"])

    return [
        {
            "id": row["id"],
            "media_type": row["media_type"],
            "taken_at": row["taken_at"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "venue_name": row["venue_name"],
            "url": signed_url(row["storage_path"]),
            "source_asset_id": row.get("source_asset_id"),
        }
        for row in media_repository.get_for_night(night_id)
    ]