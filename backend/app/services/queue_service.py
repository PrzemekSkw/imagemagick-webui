"""
Queue service using Redis and RQ
"""

import redis
from rq import Queue, Worker
from rq.job import Job as RQJob
from typing import Optional, List, Dict, Any
import uuid

from app.core.config import settings


class QueueService:
    """Service for managing job queues with Redis and RQ"""
    
    def __init__(self):
        self.redis_conn = redis.from_url(settings.redis_url)
        self.queue = Queue("imagemagick", connection=self.redis_conn)
    
    def enqueue(
        self,
        func: callable,
        *args,
        job_id: Optional[str] = None,
        timeout: int = 60,
        **kwargs
    ) -> str:
        """
        Add a job to the queue
        Returns job ID
        """
        if job_id is None:
            job_id = f"job_{uuid.uuid4().hex}"
        
        job = self.queue.enqueue(
            func,
            *args,
            job_id=job_id,
            job_timeout=timeout,
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=86400,  # Keep failed jobs for 24 hours
            **kwargs
        )
        
        return job.id
    
    def get_job(self, job_id: str) -> Optional[RQJob]:
        """Get job by ID"""
        try:
            return RQJob.fetch(job_id, connection=self.redis_conn)
        except Exception:
            return None
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details"""
        job = self.get_job(job_id)
        
        if job is None:
            return None
        
        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "meta": job.meta,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "exc_info": job.exc_info,
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.get_job(job_id)
        if job:
            job.cancel()
            return True
        return False
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        return {
            "queued": len(self.queue),
            "failed": len(self.queue.failed_job_registry),
            "finished": len(self.queue.finished_job_registry),
            "started": len(self.queue.started_job_registry),
            "deferred": len(self.queue.deferred_job_registry),
        }
    
    def get_pending_jobs(self, limit: int = 50) -> List[Dict]:
        """Get list of pending jobs"""
        jobs = []
        for job in self.queue.jobs[:limit]:
            jobs.append({
                "id": job.id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "meta": job.meta,
            })
        return jobs
    
    def clear_failed(self) -> int:
        """Clear all failed jobs"""
        registry = self.queue.failed_job_registry
        count = len(registry)
        for job_id in registry.get_job_ids():
            registry.remove(self.get_job(job_id))
        return count
    
    def set_job_progress(self, job_id: str, progress: int, message: str = ""):
        """Update job progress (0-100)"""
        job = self.get_job(job_id)
        if job:
            job.meta["progress"] = progress
            job.meta["message"] = message
            job.save_meta()


# Singleton instance
queue_service = QueueService()
