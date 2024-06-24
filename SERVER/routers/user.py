from fastapi import APIRouter, Depends, HTTPException
from models import User
from auth import create_new_user, modify_user_profile, remove_user, is_admin, get_current_user

router = APIRouter()

@router.post("/api/user", response_model=User)
async def create_user(user: User, current_user: dict = Depends(is_admin)):
    await create_new_user(user.username, user.password, user.profile)
    return user

@router.put("/api/user/{username}")
async def update_user(username: str, new_profile: str, current_user: dict = Depends(is_admin)):
    await modify_user_profile(username, new_profile)
    return {"message": f"Profile of {username} updated to {new_profile}"}

@router.delete("/api/user/{username}")
async def delete_user(username: str, current_user: dict = Depends(is_admin)):
    await remove_user(username)
    return {"message": f"User {username} deleted"}
