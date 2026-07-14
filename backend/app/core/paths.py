"""
Single source of truth for filesystem path validation.

Both the images and operations APIs previously carried their own copy of
ALLOWED_DIRS and validate_path. Two copies of a security control is one copy
too many: a fix applied to one is easy to forget in the other.
"""

import logging
import os
from typing import List

from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


def _allowed_dirs() -> List[str]:
    """
    Directories the application is permitted to read from and write to.

    Resolved on every call rather than cached at import time, so tests (and
    anything else that reconfigures settings) see the current values.
    """
    return [
        os.path.realpath(settings.upload_dir),
        os.path.realpath(settings.processed_dir),
        os.path.realpath(settings.temp_dir),
    ]


def validate_path(file_path: str) -> str:
    """
    Resolve a path and confirm it lies inside an allowed directory.

    Returns the resolved absolute path, or raises HTTPException. Note the
    separator in the prefix comparison: without it, "/app/uploads_evil" would
    pass a check against "/app/uploads".
    """
    if not file_path:
        raise HTTPException(status_code=400, detail="Invalid file path")

    abs_path = os.path.realpath(file_path)

    is_allowed = any(
        abs_path == allowed or abs_path.startswith(allowed + os.sep)
        for allowed in _allowed_dirs()
    )

    if not is_allowed:
        logger.warning(f"Path traversal attempt blocked: {file_path} -> {abs_path}")
        raise HTTPException(status_code=403, detail="Access denied")

    return abs_path
