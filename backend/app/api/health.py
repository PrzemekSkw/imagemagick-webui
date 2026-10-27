"""
Health check endpoints
"""

import logging
import os
import subprocess
from datetime import datetime

from fastapi import APIRouter

logger = logging.getLogger(__name__)
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
    from app.services.imagemagick import imagemagick_service
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
    except Exception as e:
        logger.warning("Readiness: Redis check failed: %s", e)

    # Check ImageMagick. IM6 images ship 'convert', IM7 ships 'magick';
    # the service knows which one is installed.
    try:
        cmd = imagemagick_service.resolve_magick_cmd()
        result = subprocess.run([cmd, "-version"], capture_output=True, timeout=5)
        checks["imagemagick"] = result.returncode == 0
        if result.returncode != 0:
            logger.warning(
                "Readiness: '%s -version' exited %s: %s",
                cmd, result.returncode, result.stderr.decode(errors="replace")[:200],
            )
    except Exception as e:
        logger.warning("Readiness: ImageMagick check failed: %s", e)

    all_healthy = all(checks.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
