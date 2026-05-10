# Import all the models, so that Base has them before being
# imported by Alembic or used by create_all()
from app.db.session import Base  # noqa
from app.models.user import User, WatchlistItem  # noqa
from app.models.signal import Signal  # noqa
from app.models.trade import PaperTrade  # noqa
from app.models.market import MarketSnapshot  # noqa
from app.models.strategy import StrategyPerformance, ModelUpdate  # noqa
from app.models.alert import Alert  # noqa
