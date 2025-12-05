"""
User database model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # OAuth
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # Settings
    settings = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    images = relationship("Image", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def default_settings(self) -> dict:
        """Get default user settings"""
        return {
            "theme": "system",  # light, dark, system
            "max_upload_size_mb": 100,
            "default_quality": 85,
            "default_format": "webp",
            "max_parallel_jobs": 5,
            "delete_originals": False,
            "auto_download": False,
        }
    
    def get_settings(self) -> dict:
        """Get user settings with defaults"""
        defaults = self.default_settings
        if self.settings:
            defaults.update(self.settings)
        return defaults
