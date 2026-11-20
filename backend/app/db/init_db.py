from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.db import base  # noqa: F401  (imports every model so Base knows its tables)
from app.db.session import Base
from app.models.user import User

DEFAULT_USER_EMAIL = "demo@alphatrigger.ai"


def init_db(engine: Engine) -> None:
    """Create all tables (no-op when they exist) and make sure the demo user (id 1) exists."""
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        if session.query(User).filter(User.id == 1).first() is None:
            session.add(User(email=DEFAULT_USER_EMAIL))
            session.commit()
    finally:
        session.close()
