"""
File handling service for uploads and downloads
"""

import os
import uuid
import zipfile
import aiofiles
import magic
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from fastapi import UploadFile

from app.core.config import settings
from app.services.imagemagick import imagemagick_service


class FileService:
    """Service for handling file uploads and management"""
    
    MIME_TYPE_MAP = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
        "image/svg+xml": "svg",
        "image/tiff": "tiff",
        "image/bmp": "bmp",
        "image/x-icon": "ico",
        "image/heic": "heic",
        "image/heif": "heif",
        "image/avif": "avif",
        "application/pdf": "pdf",
    }
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.processed_dir = Path(settings.processed_dir)
        self.temp_dir = Path(settings.temp_dir)
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def validate_file(
        self, 
        file: UploadFile
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate uploaded file
        Returns (is_valid, error_message, mime_type)
        """
        # Check file extension
        if file.filename:
            ext = Path(file.filename).suffix.lower()
            if ext not in settings.allowed_extensions:
                return False, f"File extension {ext} not allowed", None
        
        # Read first chunk to detect MIME type
        chunk = await file.read(8192)
        await file.seek(0)  # Reset file pointer
        
        # Detect MIME type
        mime_type = magic.from_buffer(chunk, mime=True)
        
        # Check if MIME type is allowed
        if mime_type not in self.MIME_TYPE_MAP:
            return False, f"File type {mime_type} not allowed", None
        
        # Check file size (read all to get size)
        content = await file.read()
        await file.seek(0)
        
        file_size = len(content)
        max_size = settings.max_upload_size_mb * 1024 * 1024
        
        if file_size > max_size:
            return False, f"File size exceeds {settings.max_upload_size_mb}MB limit", None
        
        return True, "", mime_type
    
    async def save_upload(
        self,
        file: UploadFile,
        user_id: Optional[int] = None
    ) -> Tuple[str, str, int]:
        """
        Save uploaded file
        Returns (stored_filename, file_path, file_size)
        """
        # Generate unique filename
        original_ext = Path(file.filename).suffix.lower() if file.filename else ".png"
        stored_filename = f"{uuid.uuid4().hex}{original_ext}"
        
        # Create user subdirectory if user_id provided
        if user_id:
            save_dir = self.upload_dir / str(user_id)
        else:
            save_dir = self.upload_dir / "anonymous"
        
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / stored_filename
        
        # Save file
        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        return stored_filename, str(file_path), len(content)
    
    async def create_thumbnail(
        self,
        source_path: str,
        user_id: Optional[int] = None
    ) -> Optional[str]:
        """Create thumbnail for uploaded image"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Determine thumbnail directory
        if user_id:
            thumb_dir = self.upload_dir / str(user_id) / "thumbnails"
        else:
            thumb_dir = self.upload_dir / "anonymous" / "thumbnails"
        
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate thumbnail filename
        source_name = Path(source_path).stem
        thumb_path = thumb_dir / f"{source_name}_thumb.webp"
        
        logger.info(f"Creating thumbnail: {source_path} -> {thumb_path}")
        
        # Create thumbnail
        success = await imagemagick_service.create_thumbnail(
            source_path,
            str(thumb_path),
            size=300
        )
        
        if success:
            logger.info(f"Thumbnail created successfully: {thumb_path}")
            return str(thumb_path)
        
        logger.warning(f"Thumbnail creation failed for {source_path}")
        return None
    
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Read file contents"""
        path = Path(file_path)
        if not path.exists():
            return None
        
        async with aiofiles.open(path, "rb") as f:
            return await f.read()
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    
    async def create_zip(
        self,
        files: List[Tuple[str, str]],  # List of (file_path, archive_name)
        output_name: Optional[str] = None
    ) -> str:
        """
        Create a ZIP archive from multiple files
        Returns path to ZIP file
        """
        if output_name is None:
            output_name = f"processed_{uuid.uuid4().hex[:8]}.zip"
        
        zip_path = self.temp_dir / output_name
        
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path, archive_name in files:
                if Path(file_path).exists():
                    zf.write(file_path, archive_name)
        
        return str(zip_path)
    
    async def cleanup_expired(self, hours: int = 24) -> int:
        """Clean up files older than specified hours"""
        count = 0
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        for directory in [self.upload_dir, self.processed_dir, self.temp_dir]:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        file_path.unlink()
                        count += 1
        
        return count
    
    def get_output_path(
        self,
        filename: str,
        format: str,
        user_id: Optional[int] = None
    ) -> str:
        """Generate output path for processed file"""
        base_name = Path(filename).stem
        output_name = f"{base_name}_{uuid.uuid4().hex[:8]}.{format}"
        
        if user_id:
            output_dir = self.processed_dir / str(user_id)
        else:
            output_dir = self.processed_dir / "anonymous"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return str(output_dir / output_name)
    
    async def get_processed_path(
        self,
        filename: str,
        user_id: Optional[int] = None
    ) -> str:
        """Generate output path for AI processed file (async version)"""
        # Extract base name and extension
        path = Path(filename)
        base = path.stem
        ext = path.suffix if path.suffix else '.png'
        
        # ALWAYS add unique suffix to prevent duplicates
        unique_id = uuid.uuid4().hex[:8]
        output_name = f"{base}_{unique_id}{ext}"
        
        if user_id:
            output_dir = self.processed_dir / str(user_id)
        else:
            output_dir = self.processed_dir / "anonymous"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return str(output_dir / output_name)


# Singleton instance
file_service = FileService()
