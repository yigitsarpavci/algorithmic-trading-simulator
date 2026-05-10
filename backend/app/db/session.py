from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

# Using the URL from settings
db_url = settings.get_database_url()
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(db_url, connect_args=connect_args, poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
