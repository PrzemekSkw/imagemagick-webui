"""
Job database model for queue management
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class JobStatus:
    """Job status constants"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    """Job model for image processing queue"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Job details
    job_id = Column(String(100), unique=True, index=True, nullable=False)  # RQ job ID
    operation = Column(String(100), nullable=False)
    command = Column(Text, nullable=True)  # Full ImageMagick command (nullable for sync ops)
    
    # Input/Output
    input_files = Column(JSON, default=list)  # List of input image IDs
    output_files = Column(JSON, default=list)  # List of output file paths
    
    # Parameters
    parameters = Column(JSON, default=dict)
    
    # Status - using String instead of ENUM to avoid duplicate type creation
    status = Column(String(20), default=JobStatus.PENDING, index=True)
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    
    def __repr__(self):
        return f"<Job {self.job_id} - {self.operation}>"
    
    @property
    def duration(self) -> float:
        """Job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
    
    @property
    def is_finished(self) -> bool:
        """Check if job is finished (completed, failed, or cancelled)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
