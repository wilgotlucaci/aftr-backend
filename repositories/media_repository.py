from database.client import supabase


class MediaRepository:
    def create(
        self,
        night_id: str,
        user_id: str,
        storage_path: str,
        media_type: str,
        taken_at: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        venue_name: str | None = None,
        source_asset_id: str | None = None,
    ):
        response = (
            supabase
            .table("media")
            .insert({
                "night_id": night_id,
                "user_id": user_id,
                "storage_path": storage_path,
                "media_type": media_type,
                "taken_at": taken_at,
                "latitude": latitude,
                "longitude": longitude,
                "venue_name": venue_name,
                "source_asset_id": source_asset_id,
            })
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_for_night(self, night_id: str):
        response = (
            supabase
            .table("media")
            .select("*")
            .eq("night_id", night_id)
            .order("taken_at")
            .execute()
        )

        return response.data
