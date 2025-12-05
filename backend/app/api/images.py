"""
Images API endpoints for upload and management
"""

import logging
import shlex
import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pathlib import Path
import zipfile
import io
import re
from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.core.config import settings
from app.models.user import User
from app.models.image import Image
from app.services.file_service import file_service
from app.services.imagemagick import imagemagick_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Security: Path validation
ALLOWED_DIRS = [
    os.path.realpath(settings.upload_dir),
    os.path.realpath(settings.output_dir),
    os.path.realpath(settings.temp_dir),
    '/app/uploads',
    '/app/processed',
    '/tmp'
]


def validate_path(file_path: str) -> str:
    """
    Validate that a file path is within allowed directories.
    Prevents path traversal attacks.
    Returns the validated absolute path or raises HTTPException.
    """
    if not file_path:
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    # Resolve to absolute path
    abs_path = os.path.realpath(file_path)
    
    # Check if path is within allowed directories
    is_allowed = any(
        abs_path.startswith(os.path.realpath(allowed_dir))
        for allowed_dir in ALLOWED_DIRS
        if allowed_dir and os.path.exists(os.path.dirname(allowed_dir) or '/')
    )
    
    if not is_allowed:
        logger.warning(f"Path traversal attempt blocked: {file_path} -> {abs_path}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    return abs_path


# Response models
class ImageResponse(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    thumbnail_url: Optional[str]
    mime_type: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    format: Optional[str]
    created_at: datetime
    project_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    images: List[ImageResponse]
    failed: List[dict]


@router.post("/upload", response_model=UploadResponse)
async def upload_images(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Upload multiple images"""
    user_id = current_user.id if current_user else None
    
    uploaded = []
    failed = []
    
    for file in files:
        try:
            # Validate file
            is_valid, error, mime_type = await file_service.validate_file(file)
            
            if not is_valid:
                failed.append({
                    "filename": file.filename,
                    "error": error
                })
                continue
            
            # Save file
            stored_filename, file_path, file_size = await file_service.save_upload(
                file, user_id
            )
            
            # Get image info
            image_info = await imagemagick_service.get_image_info(file_path)
            
            # Create thumbnail
            logger.info(f"Creating thumbnail for {file_path}")
            thumbnail_path = await file_service.create_thumbnail(file_path, user_id)
            logger.info(f"Thumbnail result: {thumbnail_path}")
            
            # Create database record
            image = Image(
                user_id=user_id,
                original_filename=file.filename or "unknown",
                stored_filename=stored_filename,
                file_path=file_path,
                thumbnail_path=thumbnail_path,
                mime_type=mime_type,
                file_size=file_size,
                width=image_info.get("width") if image_info else None,
                height=image_info.get("height") if image_info else None,
                format=image_info.get("format") if image_info else None,
                image_metadata=image_info or {},
                expires_at=datetime.utcnow() + timedelta(hours=settings.history_retention_hours)
            )
            
            db.add(image)
            await db.commit()
            await db.refresh(image)
            
            uploaded.append(ImageResponse(
                id=image.id,
                original_filename=image.original_filename,
                stored_filename=image.stored_filename,
                thumbnail_url=f"/api/images/{image.id}/thumbnail" if thumbnail_path else None,
                mime_type=image.mime_type,
                file_size=image.file_size,
                width=image.width,
                height=image.height,
                format=image.format,
                created_at=image.created_at
            ))
            
        except Exception as e:
            failed.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return UploadResponse(images=uploaded, failed=failed)


@router.get("/", response_model=List[ImageResponse])
async def list_images(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List user's uploaded images"""
    query = select(Image).order_by(Image.created_at.desc()).offset(skip).limit(limit)
    
    if current_user:
        query = query.where(Image.user_id == current_user.id)
    else:
        query = query.where(Image.user_id.is_(None))
    
    result = await db.execute(query)
    images = result.scalars().all()
    
    return [
        ImageResponse(
            id=img.id,
            original_filename=img.original_filename,
            stored_filename=img.stored_filename,
            thumbnail_url=f"/api/images/{img.id}/thumbnail" if img.thumbnail_path else None,
            mime_type=img.mime_type,
            file_size=img.file_size,
            width=img.width,
            height=img.height,
            format=img.format,
            created_at=img.created_at,
            project_id=img.project_id
        )
        for img in images
    ]


@router.get("/{image_id}")
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get image file"""
    query = select(Image).where(Image.id == image_id)
    
    if current_user:
        query = query.where(
            (Image.user_id == current_user.id) | (Image.user_id.is_(None))
        )
    
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if not Path(image.file_path).exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    
    # Use actual file extension for download filename
    actual_extension = Path(image.file_path).suffix
    original_stem = Path(image.original_filename).stem
    download_filename = f"{original_stem}{actual_extension}"
    
    return FileResponse(
        image.file_path,
        media_type=image.mime_type,
        filename=download_filename
    )


@router.get("/{image_id}/thumbnail")
async def get_thumbnail(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get image thumbnail"""
    query = select(Image).where(Image.id == image_id)
    
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # If thumbnail exists and file is there, return it
    if image.thumbnail_path and Path(image.thumbnail_path).exists():
        return FileResponse(
            image.thumbnail_path,
            media_type="image/webp"
        )
    
    # For PDF without thumbnail, try to generate one on-the-fly
    is_pdf = (image.mime_type and 'pdf' in image.mime_type.lower()) or \
             (image.original_filename and image.original_filename.lower().endswith('.pdf'))
    
    if is_pdf and Path(image.file_path).exists():
        # Try to create thumbnail now
        user_id = image.user_id
        thumbnail_path = await file_service.create_thumbnail(image.file_path, user_id)
        
        if thumbnail_path and Path(thumbnail_path).exists():
            # Update database
            image.thumbnail_path = thumbnail_path
            await db.commit()
            
            return FileResponse(
                thumbnail_path,
                media_type="image/webp"
            )
    
    raise HTTPException(status_code=404, detail="Thumbnail not found")


@router.get("/{image_id}/preview")
async def get_preview(
    image_id: int,
    page: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get preview of a file (especially for PDFs).
    For images, returns the original file.
    For PDFs, converts to PNG and returns.
    """
    query = select(Image).where(Image.id == image_id)
    
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Validate path is within allowed directories
    validated_path = validate_path(image.file_path)
    
    if not Path(validated_path).exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Validate page is a non-negative integer
    if page < 0 or page > 1000:
        raise HTTPException(status_code=400, detail="Invalid page number")
    
    # Check if it's a PDF
    is_pdf = image.mime_type == 'application/pdf' or image.original_filename.lower().endswith('.pdf')
    
    if not is_pdf:
        # Return original image
        return FileResponse(
            validated_path,
            media_type=image.mime_type,
            filename=image.original_filename
        )
    
    # For PDF, generate preview
    import asyncio
    
    preview_dir = Path(validated_path).parent / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize stem to remove problematic characters
    import re
    stem_safe = re.sub(r'[^A-Za-z0-9_\-]', '_', Path(validated_path).stem)
    preview_filename = f"{stem_safe}_page{page}.png"
    preview_path = preview_dir / preview_filename
    
    # Validate preview path: must be inside preview_dir
    preview_path_abs = preview_path.resolve()
    if not str(preview_path_abs).startswith(str(preview_dir.resolve())):
        logger.warning(f"Preview path traversal attempt blocked: {preview_path} -> {preview_path_abs}")
        raise HTTPException(status_code=403, detail="Access to preview denied.")
    
    # Validate again against global allowed directories for extra safety
    validated_preview = validate_path(str(preview_path_abs))
    
    # Check if preview already exists
    if Path(validated_preview).exists():
        return FileResponse(
            validated_preview,
            media_type="image/png",
            filename=preview_filename
        )
    
    # Generate preview using pdftoppm with safe path quoting
    temp_base = validated_preview.replace('.png', '')
    safe_input = shlex.quote(validated_path)
    safe_output = shlex.quote(temp_base)
    pdftoppm_cmd = ['pdftoppm', '-png', '-f', str(page + 1), '-l', str(page + 1), '-r', '150', '-singlefile', validated_path, temp_base]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *pdftoppm_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        
        if process.returncode == 0 and Path(validated_preview).exists():
            return FileResponse(
                validated_preview,
                media_type="image/png",
                filename=preview_filename
            )
    except Exception as e:
        logger.exception(f"PDF preview generation failed: {e}")
    
    # Fallback to ImageMagick with safe arguments
    try:
        magick_cmd = ['magick', '-density', '150', f'{validated_path}[{page}]', '-background', 'white', '-alpha', 'remove', '-quality', '90', validated_preview]
        process = await asyncio.create_subprocess_exec(
            *magick_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        
        if process.returncode == 0 and Path(validated_preview).exists():
            return FileResponse(
                validated_preview,
                media_type="image/png",
                filename=preview_filename
            )
    except Exception as e:
        logger.exception(f"PDF preview fallback failed: {e}")
    
    raise HTTPException(status_code=500, detail="Failed to generate PDF preview")


class RenameRequest(BaseModel):
    """Request to rename an image"""
    new_name: str


@router.patch("/{image_id}/rename")
async def rename_image(
    image_id: int,
    request: RenameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Rename an image (change original_filename)"""
    query = select(Image).where(Image.id == image_id)
    
    if current_user:
        query = query.where(
            (Image.user_id == current_user.id) | (Image.user_id.is_(None))
        )
    
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Validate new name
    new_name = request.new_name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    
    # Ensure it has an extension
    if '.' not in new_name:
        # Keep original extension
        original_ext = Path(image.original_filename).suffix
        new_name = new_name + original_ext
    
    # Update the filename
    image.original_filename = new_name
    await db.commit()
    
    return {
        "success": True,
        "id": image.id,
        "original_filename": image.original_filename
    }


@router.get("/{image_id}/info")
async def get_image_info(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get detailed image metadata"""
    query = select(Image).where(Image.id == image_id)
    
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return {
        "id": image.id,
        "original_filename": image.original_filename,
        "mime_type": image.mime_type,
        "file_size": image.file_size,
        "file_size_human": image.size_human,
        "width": image.width,
        "height": image.height,
        "format": image.format,
        "metadata": image.image_metadata,
        "created_at": image.created_at.isoformat(),
        "expires_at": image.expires_at.isoformat() if image.expires_at else None,
    }


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Delete an image"""
    query = select(Image).where(Image.id == image_id)
    
    if current_user:
        query = query.where(Image.user_id == current_user.id)
    
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete files
    await file_service.delete_file(image.file_path)
    if image.thumbnail_path:
        await file_service.delete_file(image.thumbnail_path)
    
    # Delete database record
    await db.delete(image)
    await db.commit()
    
    return {"message": "Image deleted successfully"}


@router.post("/download-zip")
async def download_images_as_zip(
    image_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Download multiple images as ZIP"""
    query = select(Image).where(Image.id.in_(image_ids))
    
    result = await db.execute(query)
    images = result.scalars().all()
    
    if not images:
        raise HTTPException(status_code=404, detail="No images found")
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for image in images:
            if Path(image.file_path).exists():
                zf.write(image.file_path, image.original_filename)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=images.zip"}
    )
