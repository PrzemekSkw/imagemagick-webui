"""
ImageMagick WebGUI - FastAPI Backend
Production-ready API for image processing with ImageMagick
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, images, operations, queue, settings as settings_api, health, projects

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting ImageMagick WebGUI Backend...")
    # Database tables are created by init_db.py before uvicorn starts
    print("✅ Ready to handle requests")
    
    yield
    
    # Shutdown
    print("👋 Shutting down ImageMagick WebGUI Backend...")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="ImageMagick WebGUI API",
    description="Production-ready API for image processing with ImageMagick",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(images.router, prefix="/api/images", tags=["Images"])
app.include_router(operations.router, prefix="/api/operations", tags=["Operations"])
app.include_router(queue.router, prefix="/api/queue", tags=["Queue"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["Settings"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "ImageMagick WebGUI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }
