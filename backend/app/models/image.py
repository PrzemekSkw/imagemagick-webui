"""
Image database model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Image(Base):
    """Image model for uploaded files"""
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # File info
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False, unique=True)
    file_path = Column(String(1000), nullable=False)
    thumbnail_path = Column(String(1000), nullable=True)
    
    # Metadata
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # in bytes
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    format = Column(String(50), nullable=True)
    
    # Additional metadata from ImageMagick
    image_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # Auto-delete after this
    
    # Relationships
    user = relationship("User", back_populates="images")
    project = relationship("Project", back_populates="images")
    
    def __repr__(self):
        return f"<Image {self.original_filename}>"
    
    @property
    def size_human(self) -> str:
        """Human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
