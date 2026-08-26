from database.client import supabase


class ParticipantRepository:
    def add_to_night(
        self,
        night_id: str,
        user_id: str,
        joined_at: str,
    ):
        response = (
            supabase
            .table("night_participants")
            .upsert(
                {
                    "night_id": night_id,
                    "user_id": user_id,
                    "joined_at": joined_at,
                },
                on_conflict="night_id,user_id",
            )
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def is_in_night(
        self,
        night_id: str,
        user_id: str,
    ) -> bool:
        response = (
            supabase
            .table("night_participants")
            .select("night_id")
            .eq("night_id", night_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        return bool(response.data)