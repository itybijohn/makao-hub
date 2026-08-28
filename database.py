import os
from sqlmodel import SQLModel, create_engine, Session

# Check if we are in the cloud (Render provides a DATABASE_URL)
# If not, fallback to local SQLite for testing
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL connection for the cloud
    # We must replace 'postgresql://' with 'postgresql+psycopg://' for SQLAlchemy
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
else:
    # Local SQLite connection
    DATABASE_URL = "sqlite:///makao_hub.db"

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session