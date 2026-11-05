from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class UrlCreate(BaseModel):
    longUrl: HttpUrl = Field(max_length=2048)
    custom_alias: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

class UrlResponse(BaseModel):
    success: bool
    shortURL: str
    createdAt: datetime
    message: str

class StatsResponse(BaseModel):
    lastVisit: Optional[datetime]
    visitCount: int
    createdAt: datetime