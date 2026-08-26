from datetime import datetime

from database.client import supabase
from models import (
    Night,
    NightStatus,
    Participant,
    LocationPoint,
    PersonalLocation,
)


class NightRepository:
    def create(
        self,
        title: str,
        started_at: str,
        owner_user_id: str,
        status: str = "active",
    ):
        response = (
            supabase
            .table("nights")
            .insert(
                {
                    "title": title,
                    "started_at": started_at,
                    "status": status,
                    "owner_user_id": owner_user_id,
                }
            )
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_by_id(self, night_id: str) -> Night | None:
        night_response = (
            supabase
            .table("nights")
            .select("*")
            .eq("id", night_id)
            .limit(1)
            .execute()
        )

        if not night_response.data:
            return None

        row = night_response.data[0]

        participants_response = (
            supabase
            .table("night_participants")
            .select("user_id, users(id, name)")
            .eq("night_id", night_id)
            .execute()
        )

        participants = []

        for item in participants_response.data:
            user = item["users"]

            participants.append(
                Participant(
                    id=user["id"],
                    name=user["name"],
                )
            )

        locations_response = (
            supabase
            .table("location_points")
            .select("*")
            .eq("night_id", night_id)
            .order("recorded_at")
            .execute()
        )

        locations = []

        for item in locations_response.data:
            locations.append(
                LocationPoint(
                    participant_id=item["user_id"],
                    timestamp=datetime.fromisoformat(
                        item["recorded_at"]
                    ),
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                )
            )

        participant_ids = [
            participant.id
            for participant in participants
        ]

        personal_locations = []

        if participant_ids:
            personal_locations_response = (
                supabase
                .table("personal_locations")
                .select("*")
                .in_("user_id", participant_ids)
                .execute()
            )

            for item in personal_locations_response.data:
                personal_locations.append(
                    PersonalLocation(
                        id=item["id"],
                        owner_participant_id=item["user_id"],
                        name=item["name"],
                        latitude=item["latitude"],
                        longitude=item["longitude"],
                        radius_meters=item["radius_meters"],
                    )
                )

        return Night(
            id=row["id"],
            title=row["title"],
            started_at=datetime.fromisoformat(
                row["started_at"]
            ),
            ended_at=(
                datetime.fromisoformat(row["ended_at"])
                if row["ended_at"]
                else None
            ),
            status=NightStatus(row["status"]),
            owner_user_id=row["owner_user_id"],
            participants=participants,
            locations=locations,
            venues=[],
            venue_visits=[],
            media=[],
            personal_locations=personal_locations,
        )

    def get_all(self):
        response = (
            supabase
            .table("nights")
            .select("*")
            .execute()
        )

        return response.data

    def end(
        self,
        night_id: str,
        ended_at: str,
    ):
        response = (
            supabase
            .table("nights")
            .update(
                {
                    "ended_at": ended_at,
                    "status": "finished",
                }
            )
            .eq("id", night_id)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]