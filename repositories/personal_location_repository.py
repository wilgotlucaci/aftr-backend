import uuid

from database.client import supabase


class PersonalLocationRepository:
    def get_named(self, user_id: str, name: str):
        response = (
            supabase
            .table("personal_locations")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", name)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def upsert_named(
        self,
        user_id: str,
        name: str,
        latitude: float,
        longitude: float,
        radius_meters: float = 120,
    ):
        existing = self.get_named(user_id, name)

        if existing is not None:
            response = (
                supabase
                .table("personal_locations")
                .update({
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius_meters": radius_meters,
                })
                .eq("id", existing["id"])
                .execute()
            )
        else:
            response = (
                supabase
                .table("personal_locations")
                .insert({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "name": name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius_meters": radius_meters,
                })
                .execute()
            )

        return response.data[0] if response.data else None

    def delete_named(self, user_id: str, name: str):
        (
            supabase
            .table("personal_locations")
            .delete()
            .eq("user_id", user_id)
            .eq("name", name)
            .execute()
        )
