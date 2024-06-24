from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    username: str
    profile: str

class OTPRequest(BaseModel):
    user_id: str
    profile: str

class PlateUpdateRequest(BaseModel):
    plate: str
    user_id: str

class DecisionRequest(BaseModel):
    data: str

class ErrorNotification(BaseModel):
    error: str
    timestamp: datetime
