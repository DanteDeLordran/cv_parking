from fastapi import APIRouter, HTTPException, status
from models import OTPRequest
from db import connect_db
from utils import add_to_queue
from auth import get_current_user
import secrets
from datetime import datetime, timedelta
import logging

router = APIRouter()

@router.post("/api/otp")
async def generate_otp(request: OTPRequest, current_user: dict = Depends(get_current_user)):
    if current_user['profile'] != "admin" and current_user['profile'] != request.profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    otp_duration = timedelta(minutes=15) if request.profile == "engineering" else timedelta(days=1)
    otp_expiration = datetime.utcnow() + otp_duration
    otp = secrets.token_urlsafe(32)
    
    async with connect_db() as conn:
        await conn.execute("INSERT INTO otps (user_id, otp, expires_at) VALUES ($1, $2, $3)", request.user_id, otp, otp_expiration)
    
    logging.info(f"Generated OTP for user {request.user_id} with profile {request.profile}")
    
    # Agregar solicitud a la cola para procesamiento
    add_to_queue(f"OTP generated for user {request.user_id} with profile {request.profile}")
    
    return {"otp": otp, "expires_at": otp_expiration.isoformat()}
