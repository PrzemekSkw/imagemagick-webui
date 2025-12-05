"""
Settings API for user preferences
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.core.config import settings as app_settings
from app.models.user import User

router = APIRouter()

# Default settings - use values from config
DEFAULT_SETTINGS = {
    "theme": "system",
    "max_upload_size_mb": app_settings.max_upload_size_mb,
    "default_quality": app_settings.default_quality,
    "default_format": app_settings.default_output_format,
    "max_parallel_jobs": 5,
    "delete_originals": False,
    "auto_download": True,
}


class UserSettingsRequest(BaseModel):
    theme: Optional[str] = None  # light, dark, system
    max_upload_size_mb: Optional[int] = Field(None, ge=1, le=500)
    default_quality: Optional[int] = Field(None, ge=1, le=100)
    default_format: Optional[str] = None
    max_parallel_jobs: Optional[int] = Field(None, ge=1, le=20)
    delete_originals: Optional[bool] = None
    auto_download: Optional[bool] = None


class UserSettingsResponse(BaseModel):
    theme: str
    max_upload_size_mb: int
    default_quality: int
    default_format: str
    max_parallel_jobs: int
    delete_originals: bool
    auto_download: bool
    require_login: bool  # Read-only, from .env


@router.get("/", response_model=UserSettingsResponse)
async def get_settings(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get current user settings (or defaults if not logged in)"""
    if current_user:
        settings = current_user.settings or {}
    else:
        settings = {}
    
    return UserSettingsResponse(
        theme=settings.get("theme", DEFAULT_SETTINGS["theme"]),
        max_upload_size_mb=settings.get("max_upload_size_mb", DEFAULT_SETTINGS["max_upload_size_mb"]),
        default_quality=settings.get("default_quality", DEFAULT_SETTINGS["default_quality"]),
        default_format=settings.get("default_format", DEFAULT_SETTINGS["default_format"]),
        max_parallel_jobs=settings.get("max_parallel_jobs", DEFAULT_SETTINGS["max_parallel_jobs"]),
        delete_originals=settings.get("delete_originals", DEFAULT_SETTINGS["delete_originals"]),
        auto_download=settings.get("auto_download", DEFAULT_SETTINGS["auto_download"]),
        require_login=app_settings.require_login,  # Always from config
    )


@router.put("/", response_model=UserSettingsResponse)
async def update_settings(
    request: UserSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Update user settings (requires authentication to persist)"""
    if not current_user:
        # Return the requested settings without persisting
        return UserSettingsResponse(
            theme=request.theme or DEFAULT_SETTINGS["theme"],
            max_upload_size_mb=request.max_upload_size_mb or DEFAULT_SETTINGS["max_upload_size_mb"],
            default_quality=request.default_quality or DEFAULT_SETTINGS["default_quality"],
            default_format=request.default_format or DEFAULT_SETTINGS["default_format"],
            max_parallel_jobs=request.max_parallel_jobs or DEFAULT_SETTINGS["max_parallel_jobs"],
            delete_originals=request.delete_originals if request.delete_originals is not None else DEFAULT_SETTINGS["delete_originals"],
            auto_download=request.auto_download if request.auto_download is not None else DEFAULT_SETTINGS["auto_download"],
            require_login=app_settings.require_login,
        )
    
    # Get current settings
    settings = current_user.settings or {}
    
    # Update only provided fields
    if request.theme is not None:
        if request.theme not in ["light", "dark", "system"]:
            raise HTTPException(status_code=400, detail="Invalid theme")
        settings["theme"] = request.theme
    
    if request.max_upload_size_mb is not None:
        settings["max_upload_size_mb"] = request.max_upload_size_mb
    
    if request.default_quality is not None:
        settings["default_quality"] = request.default_quality
    
    if request.default_format is not None:
        allowed_formats = ["webp", "avif", "jpeg", "jpg", "png", "gif"]
        if request.default_format not in allowed_formats:
            raise HTTPException(status_code=400, detail="Invalid format")
        settings["default_format"] = request.default_format
    
    if request.max_parallel_jobs is not None:
        settings["max_parallel_jobs"] = request.max_parallel_jobs
    
    if request.delete_originals is not None:
        settings["delete_originals"] = request.delete_originals
    
    if request.auto_download is not None:
        settings["auto_download"] = request.auto_download
    
    # Save to database
    current_user.settings = settings
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    
    return UserSettingsResponse(
        theme=settings.get("theme", DEFAULT_SETTINGS["theme"]),
        max_upload_size_mb=settings.get("max_upload_size_mb", DEFAULT_SETTINGS["max_upload_size_mb"]),
        default_quality=settings.get("default_quality", DEFAULT_SETTINGS["default_quality"]),
        default_format=settings.get("default_format", DEFAULT_SETTINGS["default_format"]),
        max_parallel_jobs=settings.get("max_parallel_jobs", DEFAULT_SETTINGS["max_parallel_jobs"]),
        delete_originals=settings.get("delete_originals", DEFAULT_SETTINGS["delete_originals"]),
        auto_download=settings.get("auto_download", DEFAULT_SETTINGS["auto_download"]),
        require_login=app_settings.require_login,
    )


@router.post("/reset")
async def reset_settings(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Reset settings to defaults"""
    if current_user:
        current_user.settings = {}
        current_user.updated_at = datetime.utcnow()
        await db.commit()
    
    return {"message": "Settings reset to defaults"}
