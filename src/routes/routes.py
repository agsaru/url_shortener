from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime,UTC

from configs.db import get_db
from models.schema import UrlCreate, UrlResponse
from utils.url import create_short_url, get_url_by_code

router = APIRouter()


@router.post(
    "/shorten",
    response_model=UrlResponse,
    status_code=status.HTTP_201_CREATED
)
def shorten_url(
    payload: UrlCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    base_url = str(request.base_url)

    result = create_short_url(
        db=db,
        long_url=str(payload.longUrl),
        base_url=base_url
    )

    return {
        "success": True,
        "shortURL": result["short_url"],
        "createdAt": result["created_at"],
        "message": "New Short Url created successfully"
    }


@router.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    url_data = get_url_by_code(db, short_code)

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )

    url_data.visit_count += 1
    url_data.last_visit = datetime.now(UTC)
    db.commit()

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
