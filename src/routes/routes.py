from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from  src import database, schemas, crud, models

router = APIRouter()

@router.post("/shorten", response_model=schemas.UrlResponse)
def shorten_url(
    payload: schemas.UrlCreate, 
    request: Request, 
    db: Session = Depends(database.get_db)
):
    try:
        base_url = str(request.base_url)
        
        result = crud.create_short_url(db, str(payload.longUrl), base_url)
        
        return {
            "success": True,
            "shortURL": result["full_short_url"],
            "createdAt": result["created_at"],
            "message": "New Short Url created successfully"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "message": "Error creating shorten url", "error": str(e)}
        )

@router.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(database.get_db)):
    try:
        url_data = crud.get_url_by_code(db, short_code)
        
        if not url_data:
            return JSONResponse(
                status_code=404, 
                content={"success": False, "message": "Short URL not found"}
            )
        url_data.visit_count += 1
        url_data.last_visit = datetime.utcnow()
        db.commit()
        
        return RedirectResponse(url=url_data.long_url)
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "message": str(e)}
        )

@router.get("/stats/{short_code}")
def get_url_stats(short_code: str, db: Session = Depends(database.get_db)):
    try:
        url_data = crud.get_url_by_code(db, short_code)
        
        if not url_data:
            return JSONResponse(
                status_code=404, 
                content={"success": False, "message": "Short Url not found"}
            )
        
        stats = {
            "lastVisit": url_data.last_visit,
            "visitCount": url_data.visit_count,
            "createdAt": url_data.created_at
        }
        
        return {"success": True, "urlStats": stats}
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "message": str(e)}
        )