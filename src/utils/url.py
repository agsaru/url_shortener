from sqlalchemy.orm import Session
from .. import models, utils

def create_short_url(db: Session, long_url: str, host_url: str):
    db_url = models.Url(long_url=long_url)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    code = utils.encode_id(db_url.id)
    db_url.short_code = code
    db.commit()
    
    return {
        "short_code": code,
        "created_at": db_url.created_at,
        "full_short_url": f"{host_url}{code}"
    }

def get_url_by_code(db: Session, short_code: str):
    return db.query(models.Url).filter(models.Url.short_code == short_code).first()