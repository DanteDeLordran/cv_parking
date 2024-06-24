from fastapi import APIRouter, HTTPException
from models import DecisionRequest
from utils import add_to_queue
from auth import get_current_user
import logging
import httpx

router = APIRouter()

@router.post("/api/decision")
async def make_decision(request: DecisionRequest, current_user: dict = Depends(get_current_user)):
    if current_user['profile'] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    # Simulated decision logic (replace with actual logic)
    decision_result = True
    
    # Simulate sending response to Raspberry Pi
    add_to_queue(f"Decision made: {decision_result}")
    
    return {"message": "Decision sent successfully"}
