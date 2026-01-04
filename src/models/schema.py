from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class UrlCreate(BaseModel):
    longUrl: HttpUrl

class UrlResponse(BaseModel):
    success: bool
    shortURL: str
    createdAt: datetime
    message: str

class StatsResponse(BaseModel):
    lastVisit: Optional[datetime]
    visitCount: int
    createdAt: datetime