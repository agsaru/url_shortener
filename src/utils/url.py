from sqlalchemy.orm import Session
from models.model import Url
from utils.hashid import encode_id

def create_short_url(db: Session, long_url: str, base_url: str):
    db_url = Url(long_url=long_url)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    code = encode_id(db_url.id)
    db_url.short_code = code
    db.commit()
    
    return {
        "short_code": code,
        "created_at": db_url.created_at,
        "short_url": f"{base_url}{code}"
    }

def get_url_by_code(db: Session, short_code: str):
    return db.query(Url).filter(Url.short_code == short_code).first()