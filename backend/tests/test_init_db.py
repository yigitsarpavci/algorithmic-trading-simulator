from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.init_db import DEFAULT_USER_EMAIL, init_db
from app.models.user import User


def memory_engine():
    return create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


def test_init_db_creates_all_tables_and_the_demo_user():
    engine = memory_engine()
    init_db(engine)
    tables = set(inspect(engine).get_table_names())
    assert {"users", "signals", "paper_trades", "watchlist_items"} <= tables

    session = sessionmaker(bind=engine)()
    user = session.query(User).filter(User.id == 1).one()
    assert user.email == DEFAULT_USER_EMAIL
    assert user.portfolio_value == 100000.0


def test_init_db_is_idempotent():
    engine = memory_engine()
    init_db(engine)
    init_db(engine)
    assert sessionmaker(bind=engine)().query(User).count() == 1
