"""
Queue API for job management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from pathlib import Path
import zipfile
import io
import mimetypes

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.image import Image
from app.services.queue_service import queue_service
from app.services.imagemagick import imagemagick_service

router = APIRouter()


# Response models
class JobDetailResponse(BaseModel):
    id: int
    job_id: str
    operation: str
    status: str
    progress: int
    error_message: Optional[str]
    input_files: List[int]
    output_files: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    parameters: dict
    
    class Config:
        from_attributes = True


class QueueStatsResponse(BaseModel):
    queued: int
    processing: int
    completed: int
    failed: int


@router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_stats():
    """Get queue statistics"""
    stats = queue_service.get_queue_stats()
    
    return QueueStatsResponse(
        queued=stats.get("queued", 0),
        processing=stats.get("started", 0),
        completed=stats.get("finished", 0),
        failed=stats.get("failed", 0)
    )


@router.get("/jobs", response_model=List[JobDetailResponse])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List user's jobs"""
    query = select(Job).order_by(Job.created_at.desc()).limit(limit)
    
    if current_user:
        query = query.where(Job.user_id == current_user.id)
    else:
        query = query.where(Job.user_id.is_(None))
    
    if status:
        query = query.where(Job.status == status)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    # Sync status from RQ for pending/processing jobs
    updated = False
    for job in jobs:
        if job.status in [JobStatus.PENDING, JobStatus.PROCESSING]:
            rq_status = queue_service.get_job_status(job.job_id)
            if rq_status:
                if rq_status["status"] == "finished":
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.utcnow()
                    if rq_status.get("result"):
                        job.output_files = rq_status["result"].get("output_files", [])
                    updated = True
                elif rq_status["status"] == "failed":
                    job.status = JobStatus.FAILED
                    job.error_message = rq_status.get("exc_info", "Unknown error")[:500]
                    job.completed_at = datetime.utcnow()
                    updated = True
                elif rq_status["status"] == "started":
                    job.status = JobStatus.PROCESSING
                    job.started_at = job.started_at or datetime.utcnow()
                    updated = True
                
                if rq_status.get("meta"):
                    job.progress = rq_status["meta"].get("progress", 0)
            else:
                # Job not found in RQ - might have expired
                # Check if it's been pending for more than 5 minutes
                if job.created_at:
                    age_seconds = (datetime.utcnow() - job.created_at).total_seconds()
                    if age_seconds > 300:  # 5 minutes
                        # Mark as failed (expired)
                        job.status = JobStatus.FAILED
                        job.error_message = "Job expired or was lost. Please try again."
                        job.completed_at = datetime.utcnow()
                        updated = True
    
    if updated:
        await db.commit()
    
    return [
        JobDetailResponse(
            id=job.id,
            job_id=job.job_id,
            operation=job.operation,
            status=job.status,
            progress=job.progress,
            error_message=job.error_message,
            input_files=job.input_files or [],
            output_files=job.output_files or [],
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            parameters=job.parameters or {}
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get job details"""
    query = select(Job).where(Job.job_id == job_id)
    
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update status from RQ
    rq_status = queue_service.get_job_status(job_id)
    if rq_status:
        if rq_status["status"] == "finished":
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            if rq_status.get("result"):
                output_files = rq_status["result"].get("output_files", [])
                job.output_files = output_files
                
                # Create Image records for processed files if not already created
                user_id = current_user.id if current_user else None
                for output_path in output_files:
                    # Check if Image record already exists for this path
                    existing = await db.execute(
                        select(Image).where(Image.file_path == output_path)
                    )
                    if existing.scalar_one_or_none():
                        continue  # Already exists
                    
                    # Create thumbnail
                    thumb_dir = Path(output_path).parent / "thumbnails"
                    thumb_dir.mkdir(parents=True, exist_ok=True)
                    thumb_path = thumb_dir / f"{Path(output_path).stem}_thumb.webp"
                    
                    try:
                        await imagemagick_service.create_thumbnail(output_path, str(thumb_path), 300)
                        thumbnail_path = str(thumb_path) if thumb_path.exists() else None
                    except Exception:
                        thumbnail_path = None
                    
                    # Get file info
                    file_path = Path(output_path)
                    stored_filename = file_path.name
                    original_name = stored_filename.split('_')[0] if '_' in stored_filename else stored_filename
                    mime_type, _ = mimetypes.guess_type(output_path)
                    file_size = file_path.stat().st_size if file_path.exists() else 0
                    
                    # Create Image record
                    new_image = Image(
                        user_id=user_id,
                        original_filename=f"processed_{original_name}",
                        stored_filename=stored_filename,
                        file_path=output_path,
                        thumbnail_path=thumbnail_path,
                        mime_type=mime_type or "application/octet-stream",
                        file_size=file_size,
                    )
                    db.add(new_image)
                
        elif rq_status["status"] == "failed":
            job.status = JobStatus.FAILED
            job.error_message = rq_status.get("exc_info", "Unknown error")
            job.completed_at = datetime.utcnow()
        elif rq_status["status"] == "started":
            job.status = JobStatus.PROCESSING
            job.started_at = job.started_at or datetime.utcnow()
        
        if rq_status.get("meta"):
            job.progress = rq_status["meta"].get("progress", 0)
        
        await db.commit()
    
    return JobDetailResponse(
        id=job.id,
        job_id=job.job_id,
        operation=job.operation,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        input_files=job.input_files or [],
        output_files=job.output_files or [],
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        parameters=job.parameters or {}
    )


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Cancel a pending job"""
    query = select(Job).where(Job.job_id == job_id)
    
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(
            status_code=400, 
            detail="Can only cancel pending or processing jobs"
        )
    
    # Cancel in RQ
    queue_service.cancel_job(job_id)
    
    # Update database
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Job cancelled successfully"}


@router.get("/jobs/{job_id}/download")
async def download_job_results(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Download job results - single file or ZIP for multiple files"""
    query = select(Job).where(Job.job_id == job_id)
    
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not job.output_files:
        raise HTTPException(status_code=404, detail="No output files")
    
    # Filter existing files
    existing_files = [f for f in job.output_files if Path(f).exists()]
    
    if not existing_files:
        raise HTTPException(status_code=404, detail="Output files not found on disk")
    
    # If only one file, return it directly (not as ZIP)
    if len(existing_files) == 1:
        file_path = existing_files[0]
        path = Path(file_path)
        
        # Determine mime type from extension
        ext_to_mime = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.gif': 'image/gif',
            '.avif': 'image/avif',
            '.pdf': 'application/pdf',
        }
        mime_type = ext_to_mime.get(path.suffix.lower(), 'application/octet-stream')
        
        return FileResponse(
            file_path,
            media_type=mime_type,
            filename=path.name
        )
    
    # Multiple files - create ZIP
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in existing_files:
            path = Path(file_path)
            zf.write(file_path, path.name)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=processed_{job_id[:8]}.zip"}
    )


@router.get("/jobs/{job_id}/files/{index}")
async def download_single_file(
    job_id: str,
    index: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Download a single output file from job"""
    query = select(Job).where(Job.job_id == job_id)
    
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.output_files or index >= len(job.output_files):
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = job.output_files[index]
    path = Path(file_path)
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        file_path,
        filename=path.name
    )


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Delete job and its output files"""
    query = select(Job).where(Job.job_id == job_id)
    
    if current_user:
        query = query.where(Job.user_id == current_user.id)
    
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete output files
    if job.output_files:
        for file_path in job.output_files:
            path = Path(file_path)
            if path.exists():
                path.unlink()
    
    # Delete job record
    await db.delete(job)
    await db.commit()
    
    return {"message": "Job deleted successfully"}
