"""
Authentication API endpoints
"""

import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_user,
    security
)
from app.models.user import User

router = APIRouter()


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements:
    - At least 8 characters
    - At least one lowercase letter
    - At least one uppercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        return False, "Password must contain at least one special character (!@#$%^&*etc.)"
    
    return True, ""


def is_registration_allowed() -> bool:
    """Check if registration is allowed via settings"""
    from app.core.config import settings
    return settings.allow_registration


# Request/Response models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    is_admin: bool = False
    created_at: datetime
    settings: dict


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # Check if registration is allowed
    if not is_registration_allowed():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently disabled. Please contact administrator."
        )
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        name=request.name,
        is_active=True,
        is_verified=False,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
    )


@router.get("/registration-status")
async def registration_status():
    """Check if registration is enabled"""
    return {"registration_enabled": is_registration_allowed()}


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password"""
    # Find user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current user info"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        is_admin=current_user.is_admin or False,
        created_at=current_user.created_at,
        settings=current_user.get_settings()
    )


@router.post("/logout")
async def logout():
    """Logout (client should discard token)"""
    return {"message": "Successfully logged out"}


@router.put("/me", response_model=UserResponse)
async def update_me(
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    if name is not None:
        current_user.name = name
    
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        is_admin=current_user.is_admin or False,
        created_at=current_user.created_at,
        settings=current_user.get_settings()
    )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v):
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool = False
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password not set for OAuth users"
        )
    
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(request.new_password)
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/create-user")
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    # Check if current user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create new users"
        )
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        is_active=True,
        is_verified=True,
        is_admin=request.is_admin,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "message": "User created successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
        }
    }


# ============== Google OAuth ==============

class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


@router.get("/google")
async def google_auth_url():
    """Get Google OAuth URL"""
    from app.core.config import settings
    
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured"
        )
    
    # Build Google OAuth URL
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": "{origin}/api/auth/google/callback",  # Will be replaced by frontend
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    
    return {
        "url_template": "https://accounts.google.com/o/oauth2/v2/auth?" + "&".join(f"{k}={v}" for k, v in params.items()),
        "client_id": settings.google_client_id,
    }


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(
    request: GoogleCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Handle Google OAuth callback"""
    import httpx
    from app.core.config import settings
    
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured"
        )
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": request.code,
                "grant_type": "authorization_code",
                "redirect_uri": request.redirect_uri,
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to exchange code: {token_response.text}"
            )
        
        tokens = token_response.json()
        
        # Get user info
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info"
            )
        
        userinfo = userinfo_response.json()
    
    google_id = userinfo.get("id")
    email = userinfo.get("email")
    name = userinfo.get("name")
    picture = userinfo.get("picture")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by Google"
        )
    
    # Find or create user
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()
    
    if not user:
        # Check if email exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            # Link Google account to existing user
            user.google_id = google_id
            user.avatar_url = picture
        else:
            # Check if registration is allowed
            if not is_registration_allowed():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Registration is disabled. Contact administrator."
                )
            
            # Create new user
            user = User(
                email=email,
                name=name,
                google_id=google_id,
                avatar_url=picture,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
    else:
        # Update user info
        if name:
            user.name = name
        if picture:
            user.avatar_url = picture
    
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    # Generate token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url,
        }
    )


@router.get("/google/status")
async def google_oauth_status():
    """Check if Google OAuth is configured"""
    from app.core.config import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    has_client_id = bool(settings.google_client_id)
    has_client_secret = bool(settings.google_client_secret)
    
    logger.info(f"Google OAuth status check: client_id={has_client_id}, client_secret={has_client_secret}")
    
    if has_client_id:
        # Log partial client ID for debugging (first 10 chars)
        partial_id = settings.google_client_id[:10] + "..." if len(settings.google_client_id) > 10 else settings.google_client_id
        logger.info(f"Google Client ID starts with: {partial_id}")
    
    return {
        "enabled": has_client_id and has_client_secret,
    }
