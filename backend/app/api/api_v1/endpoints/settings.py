from fastapi import APIRouter, Depends
from app.services.settings_service import settings_service, SystemSettings

router = APIRouter()

@router.get("/")
def get_settings():
    return settings_service.get_settings()

@router.post("/update")
def update_settings(settings: dict):
    return settings_service.update_settings(settings)
