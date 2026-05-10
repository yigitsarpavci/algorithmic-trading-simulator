from fastapi import APIRouter
from app.api.api_v1.endpoints import watchlist, signals, trades, ws, user, settings

api_router = APIRouter()

api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(trades.router, prefix="/paper-trades", tags=["paper-trading"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
