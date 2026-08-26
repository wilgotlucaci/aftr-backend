from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database.client import supabase
from repositories.user_repository import UserRepository


security = HTTPBearer()
user_repository = UserRepository()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)
        auth_user = response.user
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    if auth_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )

    user = user_repository.get_by_auth_user_id(
        str(auth_user.id)
    )

    if user is None:
        raise HTTPException(
            status_code=403,
            detail="AFTR user not found",
        )

    return user