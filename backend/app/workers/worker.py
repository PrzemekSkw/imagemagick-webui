"""
RQ Worker for processing ImageMagick jobs
"""

import redis
from rq import Worker, Queue, Connection
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.config import settings


def run_worker():
    """Start the RQ worker"""
    redis_conn = redis.from_url(settings.redis_url)
    
    with Connection(redis_conn):
        worker = Worker(
            queues=[Queue("imagemagick", connection=redis_conn)],
            connection=redis_conn,
        )
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    run_worker()
