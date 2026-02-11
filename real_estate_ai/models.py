from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    email = Column(String)
    budget = Column(Float)
    area = Column(String)
    property_type = Column(String)
    timeframe = Column(String)
    source = Column(String, default="Website")
    mortgage_status = Column(String) # "approved", "not_approved", etc.
    cash_buyer = Column(Boolean, default=False)
    message = Column(Text)

    # Intelligence fields
    score = Column(Integer, default=0)
    close_probability = Column(Float, default=0.0)
    lead_status = Column(String, default="COLD") # HOT, WARM, COLD
    recommended_action = Column(String)

    # Tracking fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_contacted = Column(DateTime, nullable=True)
    response_time_minutes = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Lead(name='{self.name}', status='{self.lead_status}', score={self.score})>"
