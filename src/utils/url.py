import re
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime, UTC

from src.models.model import Url
from src.utils.hashid import encode_id

ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def normalize_url(long_url: str) -> str:
    parsed = urlsplit(long_url)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    host = f"[{hostname}]" if ":" in hostname else hostname

    if parsed.username:
        credentials = parsed.username
        if parsed.password:
            credentials += f":{parsed.password}"
        host = f"{credentials}@{host}"

    port = parsed.port
    if port and not (
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        host = f"{host}:{port}"

    return urlunsplit((scheme, host, parsed.path or "/", parsed.query, ""))


def create_short_url(
    db: Session,
    long_url: str,
    base_url: str,
    custom_alias: Optional[str] = None,
):
    long_url = normalize_url(long_url)

    if custom_alias is not None and not ALIAS_PATTERN.fullmatch(custom_alias):
        return {
            "error": (
                "Custom alias must contain only letters, numbers, underscores, "
                "or hyphens, and be at most 64 characters"
            )
        }

    existing_url = db.query(Url).filter(Url.long_url == long_url).first()
    if existing_url:
        if custom_alias and custom_alias != existing_url.short_code:
            return {
                "error": (
                    "URL already shortened with a different alias: "
                    f"{existing_url.short_code}"
                )
            }
        return {
            "short_code": existing_url.short_code,
            "created_at": existing_url.created_at,
            "short_url": f"{base_url}{existing_url.short_code}",
            "message": "URL already shortened",
        }

    if custom_alias:
        alias_exists = db.query(Url).filter(Url.short_code == custom_alias).first()
        if alias_exists:
            return {"error": "Custom alias already in use"}

    try:
        db_url = Url(long_url=long_url)
        db.add(db_url)
        db.flush()
        code = custom_alias or encode_id(db_url.id)
        db_url.short_code = code
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_url = db.query(Url).filter(Url.long_url == long_url).first()
        if existing_url:
            if custom_alias and custom_alias != existing_url.short_code:
                return {
                    "error": (
                        "URL already shortened with a different alias: "
                        f"{existing_url.short_code}"
                    )
                }
            return {
                "short_code": existing_url.short_code,
                "created_at": existing_url.created_at,
                "short_url": f"{base_url}{existing_url.short_code}",
                "message": "URL already shortened",
            }
        if custom_alias:
            return {"error": "Custom alias already in use"}
        raise
    
    return {
        "short_code": code,
        "created_at": db_url.created_at,
        "short_url": f"{base_url}{code}",
        "message": "New Short Url created successfully"
    }

def get_url_by_code(db: Session, short_code: str):
    return db.query(Url).filter(Url.short_code == short_code).first()

def update_url_stats(db: Session, short_code: str):
    try:
        updated = db.query(Url).filter(Url.short_code == short_code).update({
            Url.visit_count: Url.visit_count + 1,
            Url.last_visit: datetime.now(UTC)
        }, synchronize_session=False)
        if updated == 0:
            raise LookupError(f"Short URL not found: {short_code}")
        db.commit()
    except (SQLAlchemyError, LookupError):
        db.rollback()
        raise
