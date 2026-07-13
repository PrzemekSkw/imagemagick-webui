"""
Operations API for image processing
"""

import os
import shlex
from typing import List, Dict, Optional, Any, Literal
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.security import get_current_user_or_enforce
from app.core.config import settings
from app.models.user import User
from app.models.image import Image
from app.models.job import Job, JobStatus
from app.services.imagemagick import imagemagick_service
from app.services.queue_service import queue_service
from app.workers.tasks import process_images, process_raw_command

router = APIRouter()


# Security: Path validation
ALLOWED_DIRS = [
    os.path.realpath(settings.upload_dir),
    os.path.realpath(settings.processed_dir),
    os.path.realpath(settings.temp_dir),
    '/app/uploads',
    '/app/processed',
    '/tmp'
]


def validate_path(file_path: str) -> str:
    """
    Validate that a file path is within allowed directories.
    Prevents path traversal attacks.
    """
    if not file_path:
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    abs_path = os.path.realpath(file_path)
    
    is_allowed = any(
        abs_path.startswith(os.path.realpath(allowed_dir))
        for allowed_dir in ALLOWED_DIRS
        if allowed_dir and os.path.exists(os.path.dirname(allowed_dir) or '/')
    )
    
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return abs_path


# Allowed output formats (whitelist prevents path traversal via format string)
OutputFormat = Literal["webp", "jpg", "jpeg", "png", "avif"]


# Request models
class ResizeParams(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    percent: Optional[int] = None
    mode: str = "fit"  # fit, fill, force


class CropParams(BaseModel):
    width: int
    height: int
    x: int = 0
    y: int = 0


class FilterParams(BaseModel):
    type: str  # blur, sharpen, grayscale, sepia, etc.
    intensity: float = 1.0
    radius: Optional[float] = None
    sigma: Optional[float] = None


class WatermarkParams(BaseModel):
    text: Optional[str] = None
    image_id: Optional[int] = None
    position: str = "southeast"  # 9 positions
    opacity: float = 0.5
    scale: float = 0.2


class Operation(BaseModel):
    operation: str
    params: Dict[str, Any] = {}


class ProcessRequest(BaseModel):
    image_ids: List[int]
    operations: List[Operation]
    output_format: OutputFormat = "webp"
    quality: int = Field(85, ge=1, le=100)


class RawCommandRequest(BaseModel):
    image_ids: List[int]
    command: str
    output_format: OutputFormat = "png"


class PreviewCommandRequest(BaseModel):
    operations: List[Operation]
    output_format: OutputFormat = "webp"
    quality: int = 85


# Response models
class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class CommandPreviewResponse(BaseModel):
    command: str
    valid: bool
    error: Optional[str] = None


# ===== Background thumbnail helper =====
async def _generate_thumbnail_background(output_path: str, thumb_path: str, size: int = 300):
    """Generate thumbnail in background - does not block the HTTP response."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        await imagemagick_service.create_thumbnail(output_path, thumb_path, size)
        logger.info(f"Background thumbnail created: {thumb_path}")
    except Exception as e:
        logger.warning(f"Background thumbnail failed: {e}")


@router.post("/process", response_model=JobResponse)
async def process_operation(
    request: ProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_enforce)
):
    """Process multiple images with specified operations"""
    user_id = current_user.id if current_user else None
    
    # Get image records
    query = select(Image).where(Image.id.in_(request.image_ids))
    result = await db.execute(query)
    images = result.scalars().all()
    
    if not images:
        raise HTTPException(status_code=404, detail="No images found")
    
    # Get file paths
    input_files = [img.file_path for img in images]
    
    # Build operations list with quality
    operations = [op.model_dump() for op in request.operations]
    operations.append({
        "operation": "quality",
        "params": {"value": request.quality}
    })
    
    # Generate job ID
    job_id = f"job_{uuid.uuid4().hex}"
    
    # Create job record
    job = Job(
        job_id=job_id,
        user_id=user_id,
        operation="batch_process",
        command=str(operations),
        input_files=[img.id for img in images],
        parameters={
            "operations": operations,
            "output_format": request.output_format,
            "quality": request.quality,
        },
        status=JobStatus.PENDING
    )
    
    db.add(job)
    await db.commit()
    
    # Enqueue job
    queue_service.enqueue(
        process_images,
        input_files,
        operations,
        request.output_format,
        user_id,
        job_id=job_id,
        timeout=len(images) * 60  # 1 minute per image max
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Processing {len(images)} images"
    )


@router.post("/raw", response_model=JobResponse)
async def process_raw(
    request: RawCommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_enforce)
):
    """Process images with raw ImageMagick command (terminal mode)"""
    user_id = current_user.id if current_user else None
    
    # Validate command
    is_valid, error = imagemagick_service.validate_command(request.command)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid command: {error}"
        )
    
    # Get image records
    query = select(Image).where(Image.id.in_(request.image_ids))
    result = await db.execute(query)
    images = result.scalars().all()
    
    if not images:
        raise HTTPException(status_code=404, detail="No images found")
    
    input_files = [img.file_path for img in images]
    
    # Generate job ID
    job_id = f"raw_{uuid.uuid4().hex}"
    
    # Create job record
    job = Job(
        job_id=job_id,
        user_id=user_id,
        operation="raw_command",
        command=request.command,
        input_files=[img.id for img in images],
        parameters={
            "raw_command": request.command,
            "output_format": request.output_format,
        },
        status=JobStatus.PENDING
    )
    
    db.add(job)
    await db.commit()
    
    # Enqueue job
    queue_service.enqueue(
        process_raw_command,
        input_files,
        request.command,
        request.output_format,
        user_id,
        job_id=job_id,
        timeout=len(images) * 60
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Processing {len(images)} images with raw command"
    )


@router.post("/preview-command", response_model=CommandPreviewResponse)
async def preview_command(request: PreviewCommandRequest):
    """Preview the ImageMagick command that will be executed"""
    operations = [op.model_dump() for op in request.operations]
    operations.append({
        "operation": "quality",
        "params": {"value": request.quality}
    })
    
    # Build command with placeholder paths
    command = await imagemagick_service.build_command(
        "{input}",
        f"{{output}}.{request.output_format}",
        operations
    )
    
    # Validate
    is_valid, error = imagemagick_service.validate_command(command)
    
    return CommandPreviewResponse(
        command=command.replace("'{input}'", "input.jpg").replace("'{output}." + request.output_format + "'", f"output.{request.output_format}"),
        valid=is_valid,
        error=error if not is_valid else None
    )


@router.get("/available")
async def list_available_operations():
    """List all available ImageMagick operations"""
    return {
        "resize": {
            "description": "Resize image",
            "params": {
                "width": "Target width in pixels",
                "height": "Target height in pixels",
                "percent": "Scale by percentage (alternative to width/height)",
                "mode": "fit (default), fill, or force"
            }
        },
        "crop": {
            "description": "Crop image",
            "params": {
                "width": "Crop width",
                "height": "Crop height",
                "x": "X offset from left",
                "y": "Y offset from top"
            }
        },
        "rotate": {
            "description": "Rotate image",
            "params": {"angle": "Rotation angle in degrees"}
        },
        "flip": {
            "description": "Flip image vertically",
            "params": {}
        },
        "flop": {
            "description": "Flip image horizontally",
            "params": {}
        },
        "blur": {
            "description": "Apply Gaussian blur",
            "params": {
                "radius": "Blur radius",
                "sigma": "Standard deviation"
            }
        },
        "sharpen": {
            "description": "Sharpen image",
            "params": {
                "radius": "Sharpen radius",
                "sigma": "Standard deviation"
            }
        },
        "grayscale": {
            "description": "Convert to grayscale",
            "params": {}
        },
        "sepia-tone": {
            "description": "Apply sepia effect",
            "params": {"threshold": "Intensity (0-100)"}
        },
        "brightness-contrast": {
            "description": "Adjust brightness and contrast",
            "params": {
                "brightness": "-100 to 100",
                "contrast": "-100 to 100"
            }
        },
        "modulate": {
            "description": "Adjust brightness, saturation, hue",
            "params": {
                "brightness": "Percentage (100 = no change)",
                "saturation": "Percentage (100 = no change)",
                "hue": "Percentage (100 = no change)"
            }
        },
        "auto-orient": {
            "description": "Auto-rotate based on EXIF",
            "params": {}
        },
        "enhance": {
            "description": "Auto-enhance image",
            "params": {}
        },
        "auto-level": {
            "description": "Auto-adjust levels",
            "params": {}
        },
        "normalize": {
            "description": "Normalize image histogram",
            "params": {}
        },
        "trim": {
            "description": "Trim borders",
            "params": {}
        },
        "strip": {
            "description": "Remove metadata",
            "params": {}
        },
        "negate": {
            "description": "Invert colors",
            "params": {}
        },
        "watermark": {
            "description": "Add text watermark",
            "params": {
                "text": "Watermark text",
                "position": "Position (northwest, north, northeast, west, center, east, southwest, south, southeast)",
                "font_size": "Font size in pixels (default: 24)",
                "opacity": "Opacity 0-1 (default: 0.5)"
            }
        },
        "remove-background": {
            "description": "AI-powered background removal",
            "params": {}
        }
    }


# New request models for live preview
class LivePreviewRequest(BaseModel):
    image_id: int
    operations: List[Operation]
    max_size: int = 800


class RemoveBackgroundRequest(BaseModel):
    image_ids: List[int]
    output_format: OutputFormat = "png"
    alpha_matting: bool = False


@router.post("/live-preview")
async def live_preview(
    request: LivePreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_enforce)
):
    """
    Generate a live preview of operations applied to an image.
    Returns base64 encoded image for instant display.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get image record
        query = select(Image).where(Image.id == request.image_id)
        result = await db.execute(query)
        image = result.scalar_one_or_none()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        from pathlib import Path
        if not Path(image.file_path).exists():
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # If no operations, just return original image as base64
        operations = [op.model_dump() for op in request.operations]
        
        if not operations or len(operations) == 0:
            import base64
            with open(image.file_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            mime_type = image.mime_type or "image/png"
            return {"preview": f"data:{mime_type};base64,{data}", "success": True}
        
        # Generate preview
        preview_data = await imagemagick_service.apply_preview(
            image.file_path,
            operations,
            max_size=request.max_size
        )
        
        if preview_data:
            return {"preview": preview_data, "success": True}
        else:
            import base64
            with open(image.file_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            mime_type = image.mime_type or "image/png"
            logger.warning(f"Preview generation failed, returning original image")
            return {"preview": f"data:{mime_type};base64,{data}", "success": True, "warning": "Using original image"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in live-preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")


@router.post("/remove-background", response_model=JobResponse)
async def remove_background(
    request: RemoveBackgroundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_enforce)
):
    """
    Remove background from images using AI (rembg).
    This creates transparent PNG images.
    """
    user_id = current_user.id if current_user else None
    
    from app.services.ai_service import ai_service
    if not await ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI background removal service is not available"
        )
    
    query = select(Image).where(Image.id.in_(request.image_ids))
    result = await db.execute(query)
    images = result.scalars().all()
    
    if not images:
        raise HTTPException(status_code=404, detail="No images found")
    
    input_files = [img.file_path for img in images]
    
    job_id = f"bg_removal_{uuid.uuid4().hex}"
    
    job = Job(
        job_id=job_id,
        user_id=user_id,
        operation="remove_background",
        command="rembg",
        input_files=[img.id for img in images],
        parameters={
            "output_format": request.output_format,
            "alpha_matting": request.alpha_matting,
        },
        status=JobStatus.PENDING
    )
    
    db.add(job)
    await db.commit()
    
    from app.workers.tasks import process_background_removal
    queue_service.enqueue(
        process_background_removal,
        input_files,
        request.output_format,
        request.alpha_matting,
        user_id,
        job_id=job_id,
        timeout=len(images) * 120
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Removing background from {len(images)} images"
    )


# Single image remove background (for editor)
class SingleRemoveBackgroundRequest(BaseModel):
    image_id: int
    alpha_matting: bool = False


@router.post("/remove-background-single", response_model=JobResponse)
async def remove_background_single(
    request: SingleRemoveBackgroundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_enforce)
):
    """Remove background from a single image (for editor)"""
    user_id = current_user.id if current_user else None
    
    from app.services.ai_service import ai_service
    if not await ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    query = select(Image).where(Image.id == request.image_id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    job_id = f"bg_removal_{uuid.uuid4().hex}"
    
    job = Job(
        job_id=job_id,
        user_id=user_id,
        operation="remove_background",
        command="rembg",
        input_files=[image.id],
        parameters={"output_format": "png", "alpha_matting": request.alpha_matting},
        status=JobStatus.PENDING
    )
    
    db.add(job)
    await db.commit()
    
    from app.workers.tasks import process_background_removal
    queue_service.enqueue(
        process_background_removal,
        [image.file_path],
        "png",
        request.alpha_matting,
        user_id,
        job_id=job_id,
        timeout=120
    )
    
    return JobResponse(job_id=job_id, status="pending", message="Removing background...")


# Synchronous remove background for editor (immediate result)
@router.post("/remove-background-sync")
async def remove_background_sync(
    request: SingleRemoveBackgroundRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_enforce)
):
    """
    Remove background synchronously and return new image URL.
    Used by editor for immediate result with loading overlay.
    """
    from pathlib import Path
    from app.services.ai_service import ai_service
    from app.services.file_service import file_service
    from app.models.job import Job
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Remove background request: image_id={request.image_id}")
    
    user_id = current_user.id if current_user else None
    
    if not await ai_service.is_available():
        logger.error("AI service not available")
        raise HTTPException(status_code=503, detail="AI service not available")
    
    query = select(Image).where(Image.id == request.image_id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    validated_input_path = validate_path(image.file_path)
    logger.info(f"Validated image path: {validated_input_path}")
    
    output_path = file_service.get_output_path(
        Path(validated_input_path).name,
        "png",
        user_id
    )
    
    try:
        logger.info("Starting background removal...")
        result_path = await ai_service.remove_background(
            validated_input_path,
            output_path,
            alpha_matting=request.alpha_matting
        )
        
        if not result_path or not Path(result_path).exists():
            logger.error("Background removal failed - no result file")
            raise HTTPException(status_code=500, detail="Background removal failed")
        
        # Generate thumbnail in background (non-blocking)
        thumb_dir = Path(output_path).parent / "thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = str(thumb_dir / f"{Path(output_path).stem}_thumb.webp")
        background_tasks.add_task(_generate_thumbnail_background, output_path, thumb_path, 300)
        
        # Create new image record (thumbnail_path set even though file not yet created)
        stored_filename = Path(output_path).name
        new_image = Image(
            user_id=user_id,
            original_filename=f"nobg_{image.original_filename}",
            stored_filename=stored_filename,
            file_path=output_path,
            thumbnail_path=thumb_path,
            mime_type="image/png",
            file_size=Path(output_path).stat().st_size,
        )
        db.add(new_image)
        
        job = Job(
            job_id=f"bg_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            operation="remove_background",
            status="completed",
            progress=100,
            input_files=[request.image_id],
            output_files=[output_path],
            parameters={"alpha_matting": request.alpha_matting},
        )
        db.add(job)
        
        await db.commit()
        await db.refresh(new_image)
        
        return {
            "success": True,
            "image_id": new_image.id,
            "image_url": f"/api/images/{new_image.id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Background removal failed: {str(e)}")


# ============== UPSCALE ==============

class UpscaleRequest(BaseModel):
    image_id: int
    scale: int = Field(default=2, ge=2, le=4, description="Scale factor (2, 3, or 4)")
    method: str = Field(default="lanczos", description="Method: lanczos (fast) or esrgan (AI, slow)")


@router.post("/upscale")
async def upscale_image(
    request: UpscaleRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_enforce)
):
    """
    Upscale image resolution.
    """
    from pathlib import Path
    from app.services.ai_service import ai_service
    from app.services.file_service import file_service
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Upscale request: image_id={request.image_id}, scale={request.scale}, method={request.method}")
    
    result = await db.execute(select(Image).where(Image.id == request.image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        logger.error(f"Image not found: {request.image_id}")
        raise HTTPException(status_code=404, detail="Image not found")
    
    logger.info(f"Found image: {image.file_path}")
    
    user_id = current_user.id if current_user else None
    if image.user_id and image.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    output_path = await file_service.get_processed_path(
        f"upscale_{request.scale}x_{image.stored_filename}",
        user_id
    )
    logger.info(f"Output path: {output_path}")
    
    try:
        logger.info("Starting upscale operation...")
        result_path = await ai_service.upscale(
            image.file_path,
            output_path,
            scale=request.scale,
            method=request.method
        )
        
        logger.info(f"Upscale result: {result_path}")
        
        if not result_path or not Path(result_path).exists():
            logger.error("Upscaling failed - no result file")
            raise HTTPException(status_code=500, detail="Upscaling failed")
        
        from PIL import Image as PILImage
        with PILImage.open(result_path) as img:
            new_width, new_height = img.size
        
        logger.info(f"New dimensions: {new_width}x{new_height}")
        
        # Generate thumbnail in background
        thumb_dir = Path(output_path).parent / "thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = str(thumb_dir / f"{Path(output_path).stem}_thumb.webp")
        background_tasks.add_task(_generate_thumbnail_background, output_path, thumb_path, 300)
        
        stored_filename = Path(output_path).name
        new_image = Image(
            user_id=user_id,
            original_filename=f"upscale_{request.scale}x_{image.original_filename}",
            stored_filename=stored_filename,
            file_path=output_path,
            thumbnail_path=thumb_path,
            mime_type="image/png",
            file_size=Path(output_path).stat().st_size,
            width=new_width,
            height=new_height,
        )
        db.add(new_image)
        
        job = Job(
            job_id=f"up_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            operation="upscale",
            status="completed",
            progress=100,
            input_files=[request.image_id],
            output_files=[output_path],
            parameters={
                "scale": request.scale,
                "method": request.method,
                "original_size": f"{image.width}x{image.height}" if image.width else "unknown",
                "new_size": f"{new_width}x{new_height}"
            },
        )
        db.add(job)
        
        await db.commit()
        await db.refresh(new_image)
        
        return {
            "success": True,
            "image_id": new_image.id,
            "image_url": f"/api/images/{new_image.id}",
            "original_size": {"width": image.width, "height": image.height},
            "new_size": {"width": new_width, "height": new_height},
            "scale": request.scale,
            "method": request.method
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upscaling failed: {str(e)}")


@router.get("/ai-capabilities")
async def get_ai_capabilities():
    """Get available AI capabilities"""
    from app.services.ai_service import ai_service
    return await ai_service.get_capabilities()


# Synchronous process endpoint (for instant crop in editor)
class ProcessSyncRequest(BaseModel):
    image_id: int
    operations: List[Operation]
    output_format: OutputFormat = "jpg"


@router.post("/process-sync")
async def process_sync(
    request: ProcessSyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_enforce)
):
    """
    Process image synchronously and return URL to result.
    Used for instant crop preview in editor.
    Thumbnail is generated in the background to avoid blocking.
    """
    from pathlib import Path
    from app.services.file_service import file_service
    from app.models.job import Job
    import logging
    
    logger = logging.getLogger(__name__)
    
    user_id = current_user.id if current_user else None
    
    # Get image
    query = select(Image).where(Image.id == request.image_id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Validate file path
    validated_input_path = validate_path(image.file_path)
    
    # Build operations
    operations = [op.model_dump() for op in request.operations]
    
    logger.info(f"PROCESS-SYNC: image_id={request.image_id}")
    
    # Determine operation name for history
    op_names = [op.get("operation", "") for op in operations]
    if "crop" in op_names:
        operation_type = "crop"
    elif "brightness-contrast" in op_names or "modulate" in op_names:
        operation_type = "adjustments"
    elif "blur" in op_names or "sharpen" in op_names:
        operation_type = "filter"
    elif "watermark" in op_names or "annotate" in op_names:
        operation_type = "watermark"
    elif "rotate" in op_names or "flip" in op_names or "flop" in op_names:
        operation_type = "rotate"
    elif "resize" in op_names:
        operation_type = "resize"
    elif "sepia-tone" in op_names or "grayscale" in op_names:
        operation_type = "filter"
    elif "enhance" in op_names or "auto-level" in op_names:
        operation_type = "auto_enhance"
    else:
        operation_type = "edit"
    
    # ===== FIX: Preserve input format instead of always converting to PNG =====
    # Detect input format and use the same for output (unless explicitly overridden)
    actual_output_format = request.output_format
    is_pdf_input = validated_input_path.lower().endswith('.pdf') or (image.mime_type and 'pdf' in image.mime_type.lower())
    
    if is_pdf_input:
        actual_output_format = 'png'
    elif actual_output_format == 'png':
        # If input is JPG/JPEG and output was defaulting to PNG, keep as JPG
        # This prevents massive file size inflation (1.6MB JPG -> 20MB PNG)
        input_ext = Path(validated_input_path).suffix.lower().lstrip('.')
        if input_ext in ('jpg', 'jpeg', 'webp'):
            actual_output_format = input_ext if input_ext != 'jpeg' else 'jpg'
            logger.info(f"PROCESS-SYNC: Preserving input format {input_ext} instead of PNG")
    
    # Generate output path
    output_path = file_service.get_output_path(
        Path(validated_input_path).name,
        actual_output_format,
        user_id
    )
    
    logger.info(f"PROCESS-SYNC: input={validated_input_path}, output={output_path}")
    logger.info(f"PROCESS-SYNC: operations={operations}")
    
    # Build and execute command
    command = await imagemagick_service.build_command(
        validated_input_path,
        output_path,
        operations
    )
    
    logger.info(f"PROCESS-SYNC: command={command}")
    
    success, stdout, stderr = await imagemagick_service.execute(command)
    
    if not success or not Path(output_path).exists():
        raise HTTPException(status_code=500, detail=f"Processing failed: {stderr}")
    
    # ===== FIX: Generate thumbnail in BACKGROUND (non-blocking) =====
    thumb_dir = Path(output_path).parent / "thumbnails"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = str(thumb_dir / f"{Path(output_path).stem}_thumb.webp")
    
    # Schedule thumbnail generation in background - response returns immediately
    background_tasks.add_task(_generate_thumbnail_background, output_path, thumb_path, 300)
    
    # Create new image record for the processed image
    stored_filename = Path(output_path).name
    new_image = Image(
        user_id=user_id,
        original_filename=f"edited_{image.original_filename}",
        stored_filename=stored_filename,
        file_path=output_path,
        thumbnail_path=thumb_path,  # Path is set, file will be created in background
        mime_type=f"image/{actual_output_format}",
        file_size=Path(output_path).stat().st_size,
    )
    db.add(new_image)
    
    # Create history entry
    job = Job(
        job_id=f"sync_{uuid.uuid4().hex[:8]}",
        user_id=user_id,
        operation=operation_type,
        status="completed",
        progress=100,
        input_files=[request.image_id],
        output_files=[output_path],
        parameters={"operations": operations, "output_format": actual_output_format},
    )
    db.add(job)
    
    await db.commit()
    await db.refresh(new_image)
    
    # Return URL to new image IMMEDIATELY (thumbnail generates in background)
    return {
        "success": True,
        "image_id": new_image.id,
        "image_url": f"/api/images/{new_image.id}"
    }


class DownloadDirectRequest(BaseModel):
    image_id: int
    operations: List[Operation]
    output_format: OutputFormat = "webp"
    quality: int = 85


@router.post("/download-direct")
async def download_direct(
    request: DownloadDirectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_enforce)
):
    """
    Process image and return file directly for download.
    Does not save to database - just processes and streams file.
    """
    allowed_formats = {'webp', 'png', 'jpg', 'jpeg', 'gif', 'avif', 'tiff', 'bmp'}
    if request.output_format.lower() not in allowed_formats:
        raise HTTPException(status_code=400, detail="Invalid output format")
    
    from pathlib import Path
    from fastapi.responses import FileResponse
    from app.services.file_service import file_service
    import tempfile
    
    user_id = current_user.id if current_user else None
    
    query = select(Image).where(Image.id == request.image_id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    validated_input_path = validate_path(image.file_path)
    
    operations = [op.model_dump() for op in request.operations]
    
    actual_output_format = request.output_format.lower().replace('/', '').replace('\\', '').replace('..', '')
    
    is_pdf_input = validated_input_path.lower().endswith('.pdf') or (image.mime_type and 'pdf' in image.mime_type.lower())
    if is_pdf_input:
        actual_output_format = 'png'
    
    original_name = Path(image.original_filename).stem
    output_filename = f"edited_{original_name}.{actual_output_format}"
    
    temp_filename = f"download_{uuid.uuid4().hex}.{actual_output_format}"
    output_path = os.path.join(tempfile.gettempdir(), temp_filename)

    validated_output_path = validate_path(output_path)
    
    command = await imagemagick_service.build_command(
        validated_input_path,
        validated_output_path,
        operations
    )
    
    success, stdout, stderr = await imagemagick_service.execute(command)
    
    if not success or not Path(validated_output_path).exists():
        raise HTTPException(status_code=500, detail=f"Processing failed: {stderr}")

    mime_types = {
        "webp": "image/webp",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
    }
    media_type = mime_types.get(actual_output_format, "application/octet-stream")
    
    return FileResponse(
        path=validated_output_path,
        filename=output_filename,
        media_type=media_type,
        headers={
        "Content-Disposition": f'attachment; filename="{output_filename}"'
       },
       background=None
)


# ============== AI DIAGNOSTICS ==============

@router.get("/ai-status")
async def ai_status():
    """Check AI service status and diagnose issues"""
    from app.services.ai_service import ai_service
    
    result = {
        "available": await ai_service.is_available(),
        "diagnostics": await ai_service.diagnose(),
    }
    
    return result
