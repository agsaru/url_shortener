import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from redis.exceptions import RedisError
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.configs.db import get_db
from src.configs.limiter import limiter
from src.configs.redis_client import cache
from src.configs.settings import PUBLIC_BASE_URL
from src.models.schema import UrlCreate, UrlResponse
from src.utils.url import (
    ShortUrlConflictError,
    create_short_url,
    get_url_by_code,
    update_url_stats,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def record_visit_safely(db: Session, short_code: str) -> None:
    try:
        update_url_stats(db, short_code)
    except (SQLAlchemyError, LookupError):
        logger.exception("Unable to update visit statistics for %s", short_code)


@router.post(
    "/shorten",
    response_model=UrlResponse,
    status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
def shorten_url(
    payload: UrlCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    try:
        result = create_short_url(
            db=db,
            long_url=str(payload.longUrl),
            base_url=f"{PUBLIC_BASE_URL}/",
            custom_alias=payload.custom_alias
        )
    except ShortUrlConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        db.rollback()
        logger.exception("Unable to generate a unique short code")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We couldn't create your short link right now. Please try again.",
        ) from exc
    except OperationalError as exc:
        db.rollback()
        logger.exception("Database unavailable while creating a short URL")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We couldn't save your short link right now. Please try again in a moment.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Unexpected database error while creating a short URL")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while creating your short link. Please try again.",
        ) from exc

    if result["message"] == "URL already shortened":
        response.status_code = status.HTTP_200_OK

    return {
        "success": True,
        "shortURL": result["short_url"],
        "createdAt": result["created_at"],
        "message": result.get("message", "Success")
    }


@router.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    cached_value = None
    try:
        cached_value = cache.get(short_code)
    except RedisError:
        logger.exception("Redis lookup failed for short code %s", short_code)

    if cached_value:
        try:
            cached_data = json.loads(cached_value)
        except (TypeError, json.JSONDecodeError):
            cached_data = None

        if isinstance(cached_data, dict) and isinstance(
            cached_data.get("long_url"), str
        ):
            expires_at = cached_data.get("expires_at")
            try:
                cached_expires_at = (
                    datetime.fromisoformat(expires_at)
                    if expires_at
                    else None
                )
            except (TypeError, ValueError):
                cached_expires_at = None

            if expires_at and cached_expires_at is None:
                cached_data = None

            if cached_data and cached_expires_at:
                expiry_utc = (
                    cached_expires_at.replace(tzinfo=UTC)
                    if cached_expires_at.tzinfo is None
                    else cached_expires_at
                )
                if expiry_utc < datetime.now(UTC):
                    try:
                        cache.delete(short_code)
                    except RedisError:
                        logger.exception(
                            "Redis cache delete failed for expired short code %s",
                            short_code,
                        )
                    raise HTTPException(
                        status_code=status.HTTP_410_GONE,
                        detail="This Short URL has expired",
                    )

            if cached_data:
                record_visit_safely(db, short_code)
                return RedirectResponse(url=cached_data["long_url"])

    try:
        url_data = get_url_by_code(db, short_code)
    except OperationalError as exc:
        db.rollback()
        logger.exception("Database unavailable while looking up %s", short_code)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We couldn't look up that short link right now. Please try again in a moment.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error while looking up %s", short_code)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while looking up that short link. Please try again.",
        ) from exc

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )

    expires_at = (
        url_data.expires_at.replace(tzinfo=UTC)
        if url_data.expires_at and url_data.expires_at.tzinfo is None
        else url_data.expires_at
    )
    if expires_at and expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This Short URL has expired"
        )

    cache_payload = json.dumps({
        "long_url": url_data.long_url,
        "expires_at": expires_at.isoformat() if expires_at else None,
    })
    try:
        cache.setex(short_code, 86400, cache_payload)
    except RedisError:
        logger.exception("Redis cache write failed for short code %s", short_code)

    record_visit_safely(db, short_code)

    return RedirectResponse(url=url_data.long_url)


@router.get("/stats/{short_code}")
def get_url_stats(short_code: str, db: Session = Depends(get_db)):
    try:
        url_data = get_url_by_code(db, short_code)
    except OperationalError as exc:
        db.rollback()
        logger.exception("Database unavailable while looking up stats for %s", short_code)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We couldn't load these statistics right now. Please try again in a moment.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error while looking up stats for %s", short_code)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while loading these statistics. Please try again.",
        ) from exc

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )

    return {
        "success": True,
        "urlStats": {
            "lastVisit": url_data.last_visit,
            "visitCount": url_data.visit_count,
            "createdAt": url_data.created_at
        }
    }
