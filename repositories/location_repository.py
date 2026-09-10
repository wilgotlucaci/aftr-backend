from database.client import supabase


class LocationRepository:
    def create(
        self,
        night_id: str,
        user_id: str,
        recorded_at: str,
        latitude: float,
        longitude: float,
        speed: float | None = None,
        horizontal_accuracy: float | None = None,
    ):
        response = (
            supabase
            .table("location_points")
            .insert({
                "night_id": night_id,
                "user_id": user_id,
                "recorded_at": recorded_at,
                "latitude": latitude,
                "longitude": longitude,
                "speed": speed,
                "horizontal_accuracy": horizontal_accuracy,
            })
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]