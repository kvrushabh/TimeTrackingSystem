from sqlalchemy import Column, DateTime
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
