from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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
    participants: list[Participant] = []
    locations: list[LocationPoint] = []
    venues: list[Venue] = []
    venue_visits: list[VenueVisit] = []
    media: list[MediaItem] = []
    personal_locations: list[PersonalLocation] = []