from fastapi import APIRouter, Depends, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime,UTC

from src.configs.db import get_db
from src.configs.redis_client import cache 
from src.models.schema import UrlCreate, UrlResponse
from src.utils.url import create_short_url, get_url_by_code, update_url_stats
from src.configs.limiter import limiter

router = APIRouter()


@router.post(
    "/shorten",
    response_model=UrlResponse,
    status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
def shorten_url(
    payload: UrlCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    base_url = str(request.base_url)

    result = create_short_url(
        db=db,
        long_url=str(payload.longUrl),
        base_url=base_url,
        custom_alias=payload.custom_alias 
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return {
        "success": True,
        "shortURL": result["short_url"],
        "createdAt": result["created_at"],
        "message": result.get("message", "Success")
    }

@router.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def redirect_url(short_code: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    cached_long_url = cache.get(short_code)
    
    if cached_long_url:
        background_tasks.add_task(update_url_stats, db, short_code)
        return RedirectResponse(url=cached_long_url)

    url_data = get_url_by_code(db, short_code)

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
        
    if url_data.expires_at and url_data.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This Short URL has expired"
        )

    cache.setex(short_code, 86400, url_data.long_url)

    background_tasks.add_task(update_url_stats, db, short_code)

    return RedirectResponse(url=url_data.long_url)


@router.get("/stats/{short_code}")
def get_url_stats(short_code: str, db: Session = Depends(get_db)):
    url_data = get_url_by_code(db, short_code)

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short Url not found"
        )

    return {
        "success": True,
        "urlStats": {
            "lastVisit": url_data.last_visit,
            "visitCount": url_data.visit_count,
            "createdAt": url_data.created_at
        }
    }
