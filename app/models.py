from sqlalchemy import Column, String, DateTime, Float, Boolean

import uuid
from datetime import datetime, timezone

from .extensions import db

def generate_unique_id():
    return str(uuid.uuid4())

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = Column(String(36), primary_key=True, default=generate_unique_id)
    user_id = Column(String(36), nullable=False, index=True)
    coin_id = Column(String(100), nullable=False, index=True)
    threshold_price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))