from fastapi import APIRouter, Depends, HTTPException
from db import connect_db
from utils import generate_stats_plot
from auth import is_admin, get_current_user
import logging

router = APIRouter()

@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    if current_user['profile'] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    async with connect_db() as conn:
        stats = await conn.fetch("SELECT * FROM some_table")
        
    generate_stats_plot(stats)
    logging.info("Generated statistics")
    
    return {"message": "Statistics generated", "stats_url": "/static/stats.png"}
