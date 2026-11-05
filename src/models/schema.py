from pydantic import BaseModel, Field, HttpUrl, field_validator
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

    @field_validator("longUrl")
    @classmethod
    def reject_embedded_credentials(cls, value: HttpUrl) -> HttpUrl:
        if value.username or value.password:
            raise ValueError("URLs containing usernames or passwords are not allowed")
        return value

class UrlResponse(BaseModel):
    success: bool
    shortURL: str
    createdAt: datetime
    message: str

class StatsResponse(BaseModel):
    lastVisit: Optional[datetime]
    visitCount: int
    createdAt: datetime