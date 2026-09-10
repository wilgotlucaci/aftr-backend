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
            .insert({
                "title": title,
                "started_at": started_at,
                "status": status,
                "owner_user_id": owner_user_id,
            })
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_by_id(
        self,
        night_id: str,
    ) -> Night | None:
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
                    speed=item.get("speed"),
                    horizontal_accuracy=item.get(
                        "horizontal_accuracy"
                    ),
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
                datetime.fromisoformat(
                    row["ended_at"]
                )
                if row["ended_at"]
                else None
            ),
            status=NightStatus(
                row["status"]
            ),
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

    def get_active(self):
        response = (
            supabase
            .table("nights")
            .select("*")
            .eq("status", "active")
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
            .update({
                "ended_at": ended_at,
                "status": "finished",
            })
            .eq("id", night_id)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]
    
    def get_for_user(self, user_id: str):
        owned_response = (
            supabase
            .table("nights")
            .select("*")
            .eq("owner_user_id", user_id)
            .order("started_at", desc=True)
            .execute()
        )

        participant_response = (
            supabase
            .table("night_participants")
            .select("night_id")
            .eq("user_id", user_id)
            .execute()
        )

        participant_night_ids = [
            item["night_id"]
            for item in participant_response.data
        ]

        participant_nights = []

        if participant_night_ids:
            participant_nights_response = (
                supabase
                .table("nights")
                .select("*")
                .in_("id", participant_night_ids)
                .order("started_at", desc=True)
                .execute()
            )

            participant_nights = participant_nights_response.data

        nights_by_id = {}

        for night in owned_response.data:
            nights_by_id[night["id"]] = night

        for night in participant_nights:
            nights_by_id[night["id"]] = night

        nights = list(nights_by_id.values())

        nights.sort(
            key=lambda night: night["started_at"],
            reverse=True,
        )

        return nights