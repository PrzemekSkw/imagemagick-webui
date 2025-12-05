"""
Projects API for organizing images into collections
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.project import Project
from app.models.image import Image

router = APIRouter()


# Pydantic models
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: str = Field(default="#6366f1", pattern="^#[0-9A-Fa-f]{6}$")
    icon: str = Field(default="folder", max_length=50)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    icon: str
    image_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


class MoveImagesRequest(BaseModel):
    image_ids: List[int]
    project_id: Optional[int] = None  # None means remove from project


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List all projects for the current user"""
    if not current_user:
        return ProjectListResponse(projects=[], total=0)
    
    # Get projects with image count
    query = (
        select(Project, func.count(Image.id).label("image_count"))
        .outerjoin(Image, Image.project_id == Project.id)
        .where(Project.user_id == current_user.id)
        .group_by(Project.id)
        .order_by(Project.updated_at.desc())
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    projects = []
    for project, image_count in rows:
        projects.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            color=project.color,
            icon=project.icon,
            image_count=image_count,
            created_at=project.created_at,
            updated_at=project.updated_at
        ))
    
    return ProjectListResponse(projects=projects, total=len(projects))


@router.post("/", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    project = Project(
        name=data.name,
        description=data.description,
        color=data.color,
        icon=data.icon,
        user_id=current_user.id
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        color=project.color,
        icon=project.icon,
        image_count=0,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project"""
    query = (
        select(Project, func.count(Image.id).label("image_count"))
        .outerjoin(Image, Image.project_id == Project.id)
        .where(Project.id == project_id, Project.user_id == current_user.id)
        .group_by(Project.id)
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project, image_count = row
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        color=project.color,
        icon=project.icon,
        image_count=image_count,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project"""
    query = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.color is not None:
        project.color = data.color
    if data.icon is not None:
        project.icon = data.icon
    
    project.updated_at = datetime.utcnow()
    await db.commit()
    
    # Get image count
    count_query = select(func.count(Image.id)).where(Image.project_id == project_id)
    count_result = await db.execute(count_query)
    image_count = count_result.scalar() or 0
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        color=project.color,
        icon=project.icon,
        image_count=image_count,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project (images are not deleted, just unassigned)"""
    query = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Unassign images from project
    update_query = select(Image).where(Image.project_id == project_id)
    images_result = await db.execute(update_query)
    images = images_result.scalars().all()
    
    for image in images:
        image.project_id = None
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted", "images_unassigned": len(images)}


@router.post("/{project_id}/images")
async def add_images_to_project(
    project_id: int,
    data: MoveImagesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add images to a project"""
    # Verify project exists and belongs to user
    project_query = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id
    )
    result = await db.execute(project_query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update images
    images_query = select(Image).where(Image.id.in_(data.image_ids))
    images_result = await db.execute(images_query)
    images = images_result.scalars().all()
    
    updated = 0
    for image in images:
        # Only update if user owns the image or it's anonymous
        if image.user_id is None or image.user_id == current_user.id:
            image.project_id = project_id
            updated += 1
    
    project.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": f"Added {updated} images to project", "project_id": project_id}


@router.post("/images/remove")
async def remove_images_from_project(
    data: MoveImagesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove images from their projects"""
    images_query = select(Image).where(Image.id.in_(data.image_ids))
    images_result = await db.execute(images_query)
    images = images_result.scalars().all()
    
    updated = 0
    for image in images:
        if image.user_id is None or image.user_id == current_user.id:
            image.project_id = None
            updated += 1
    
    await db.commit()
    
    return {"message": f"Removed {updated} images from projects"}


@router.get("/{project_id}/images")
async def get_project_images(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all images in a project"""
    # Verify project exists and belongs to user
    project_query = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id
    )
    result = await db.execute(project_query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get images
    images_query = select(Image).where(
        Image.project_id == project_id
    ).order_by(Image.created_at.desc())
    
    images_result = await db.execute(images_query)
    images = images_result.scalars().all()
    
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "color": project.color,
            "icon": project.icon
        },
        "images": [
            {
                "id": img.id,
                "originalFilename": img.original_filename,
                "mimeType": img.mime_type,
                "fileSize": img.file_size,
                "width": img.width,
                "height": img.height,
                "createdAt": img.created_at.isoformat()
            }
            for img in images
        ],
        "total": len(images)
    }
