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

    # US Compliance & CRM fields
    sms_opt_in = Column(Boolean, default=False)
    appointment_booked = Column(Boolean, default=False)
    crm_synced = Column(Boolean, default=False)
    estimated_commission = Column(Float, default=0.0)

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

class AgencyLead(Base):
    __tablename__ = "agency_leads"

    id = Column(Integer, primary_key=True, index=True)
    agency_name = Column(String, index=True)
    owner_name = Column(String, nullable=True)
    website = Column(String)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    google_rating = Column(Float, nullable=True)
    num_listings = Column(Integer, nullable=True)

    # Analysis fields
    classification = Column(String, nullable=True) # Solo Agent, Small Team, Large Brokerage, Luxury Brokerage
    score = Column(Integer, default=0) # 1-10
    strength_summary = Column(Text, nullable=True)
    growth_opportunity_summary = Column(Text, nullable=True)

    # Module 2 & 3 fields
    tier = Column(String, nullable=True) # Tier 1, Tier 2, Tier 3
    market_analysis = Column(Text, nullable=True) # JSON or structured text
    weaknesses = Column(Text, nullable=True)

    # Module 4 fields
    outreach_email = Column(Text, nullable=True)
    outreach_status = Column(String, default="PENDING") # PENDING, GENERATED, SENT

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AgencyLead(name='{self.agency_name}', tier='{self.tier}', score={self.score})>"
