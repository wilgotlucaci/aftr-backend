from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class NightStatus(str, Enum):
    ACTIVE = "active"
    PROCESSING = "processing"
    FINISHED = "finished"


class Participant(BaseModel):
    id: str
    name: str


class LocationPoint(BaseModel):
    participant_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    speed: float | None = None
    horizontal_accuracy: float | None = None


class Venue(BaseModel):
    id: str
    name: str
    category: str
    latitude: float
    longitude: float


class VenueVisit(BaseModel):
    participant_id: str
    venue_id: str
    arrived_at: datetime
    left_at: datetime


class MediaItem(BaseModel):
    id: str
    participant_id: str
    timestamp: datetime
    media_type: str
    venue_id: str | None = None


class PersonalLocation(BaseModel):
    id: str
    owner_participant_id: str
    name: str
    latitude: float
    longitude: float
    radius_meters: float = 50


class Night(BaseModel):
    id: str
    title: str
    started_at: datetime
    ended_at: datetime | None = None
    status: NightStatus
    owner_user_id: str | None = None

    participants: list[Participant] = Field(default_factory=list)
    locations: list[LocationPoint] = Field(default_factory=list)
    venues: list[Venue] = Field(default_factory=list)
    venue_visits: list[VenueVisit] = Field(default_factory=list)
    media: list[MediaItem] = Field(default_factory=list)
    personal_locations: list[PersonalLocation] = Field(default_factory=list)