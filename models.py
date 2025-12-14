from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str


class ApiLog(BaseModel):
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Input payload")
    token: str
    prediction: str
    process_time: float
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Log creation time")