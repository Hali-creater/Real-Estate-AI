from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
try:
    from .models import Base
except ImportError:
    from models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./real_estate.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

    # Simple migration logic for existing databases
    inspector = inspect(engine)
    if 'leads' not in inspector.get_table_names():
        return

    existing_columns = [c['name'] for c in inspector.get_columns('leads')]

    # Define all expected columns and their types for SQLite
    # This ensures even very old databases are upgraded
    expected_columns = {
        "phone": "VARCHAR",
        "email": "VARCHAR",
        "budget": "FLOAT",
        "area": "VARCHAR",
        "property_type": "VARCHAR",
        "timeframe": "VARCHAR",
        "source": "VARCHAR",
        "mortgage_status": "VARCHAR",
        "cash_buyer": "BOOLEAN DEFAULT 0",
        "message": "TEXT",
        "sms_opt_in": "BOOLEAN DEFAULT 0",
        "appointment_booked": "BOOLEAN DEFAULT 0",
        "crm_synced": "BOOLEAN DEFAULT 0",
        "estimated_commission": "FLOAT DEFAULT 0.0",
        "score": "INTEGER DEFAULT 0",
        "close_probability": "FLOAT DEFAULT 0.0",
        "lead_status": "VARCHAR DEFAULT 'COLD'",
        "recommended_action": "VARCHAR",
        "last_contacted": "DATETIME",
        "response_time_minutes": "FLOAT"
    }

    with engine.connect() as conn:
        for col_name, col_type in expected_columns.items():
            if col_name not in existing_columns:
                try:
                    conn.execute(text(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"Added missing column: {col_name}")
                except Exception as e:
                    print(f"Error adding column {col_name}: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
