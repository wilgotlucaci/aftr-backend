from database.client import supabase


class RecapRepository:
    def get_by_night_id(self, night_id: str):
        response = (
            supabase
            .table("recaps")
            .select("*")
            .eq("night_id", night_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def save(self, night_id: str, recap_data: dict):
        response = (
            supabase
            .table("recaps")
            .upsert(
                {
                    "night_id": night_id,
                    "recap_data": recap_data,
                },
                on_conflict="night_id",
            )
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]