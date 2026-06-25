from sqlalchemy.orm import Session
from src.models.model import Url
from src.utils.hashid import encode_id

def create_short_url(db: Session, long_url: str, base_url: str, custom_alias: str = None):
    if not custom_alias:
        existing_url = db.query(Url).filter(Url.long_url == long_url).first()
        if existing_url:
            return {
                "short_code": existing_url.short_code,
                "created_at": existing_url.created_at,
                "short_url": f"{base_url}{existing_url.short_code}",
                "message": "URL already shortened"
            }
        
    if custom_alias:
        alias_exists = db.query(Url).filter(Url.short_code == custom_alias).first()
        if alias_exists:
            return {"error": "Custom alias already in use"}

    db_url = Url(long_url=long_url)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    if custom_alias:
        code = custom_alias
    else:
        code = encode_id(db_url.id)

    db_url.short_code = code
    db.commit()
    
    return {
        "short_code": code,
        "created_at": db_url.created_at,
        "short_url": f"{base_url}{code}",
        "message": "New Short Url created successfully"
    }

def get_url_by_code(db: Session, short_code: str):
    return db.query(Url).filter(Url.short_code == short_code).first()