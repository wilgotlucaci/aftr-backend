from database.client import supabase


class UserRepository:
    def get_by_auth_user_id(
        self,
        auth_user_id: str,
    ):
        response = (
            supabase
            .table("users")
            .select("*")
            .eq("auth_user_id", auth_user_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]