from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from configs.db import Base

class Url(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    long_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True, nullable=True)
    visit_count = Column(Integer, default=0)
    last_visit = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now())