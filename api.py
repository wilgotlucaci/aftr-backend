from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from auth.current_user import get_current_user
from recap import build_serialized_recap
from utils.join_code import (
    JOIN_CODE_LENGTH,
    night_join_code,
    normalise_join_code,
)
from repositories.location_repository import LocationRepository
from repositories.night_repository import NightRepository
from repositories.participant_repository import ParticipantRepository
from repositories.recap_repository import RecapRepository


app = FastAPI(
    title="AFTR API",
    version="0.1.0",
)

night_repository = NightRepository()
participant_repository = ParticipantRepository()
location_repository = LocationRepository()
recap_repository = RecapRepository()


class CreateNightRequest(BaseModel):
    title: str


class JoinNightRequest(BaseModel):
    code: str


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


@app.post("/nights/{night_id}/end")
def end_night(
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
        finished_night
    )

    recap_repository.save(
        night_id,
        recap,
    )

    return {
        "night": ended_night,
        "recap_generated": True,
        "recap": recap,
    }


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
        night
    )

    recap_repository.save(
        night_id,
        recap,
    )

    return recap