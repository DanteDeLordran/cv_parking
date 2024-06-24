from fastapi import APIRouter, Depends, HTTPException
from models import PlateUpdateRequest
from db import connect_db
from auth import get_current_user
import logging
from datetime import datetime

router = APIRouter()

@router.post("/api/plate")
async def update_plate(request: PlateUpdateRequest, current_user: dict = Depends(get_current_user)):
    if current_user['profile'] != "admin" and current_user['username'] != request.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    timestamp = datetime.utcnow().isoformat()
    
    async with connect_db() as conn:
        await conn.execute("UPDATE users SET plate = $1, updated_at = $2 WHERE user_id = $3", request.plate, timestamp, request.user_id)
    
    logging.info(f"Updated plate for user {request.user_id} by {current_user['username']}")
    
    return {"message": "Plate updated successfully"}
