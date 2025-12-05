"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "imagemagick-webgui-api"
    }


@router.get("/health/config")
async def config_check():
    """Check configuration values (for debugging)"""
    from app.core.config import settings
    
    return {
        "require_login": settings.require_login,
        "default_output_format": settings.default_output_format,
        "default_quality": settings.default_quality,
        "max_upload_size_mb": settings.max_upload_size_mb,
        # Also show raw env var for debugging
        "env_require_login": os.environ.get("REQUIRE_LOGIN", "NOT_SET"),
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check including dependencies"""
    from app.core.config import settings
    import redis
    
    checks = {
        "api": True,
        "redis": False,
        "imagemagick": False
    }
    
    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        checks["redis"] = True
    except Exception:
        pass
    
    # Check ImageMagick
    try:
        import subprocess
        result = subprocess.run(["magick", "-version"], capture_output=True)
        checks["imagemagick"] = result.returncode == 0
    except Exception:
        pass
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
