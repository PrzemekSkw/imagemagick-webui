"""
Application configuration using Pydantic Settings
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "ImageMagick WebGUI"
    debug: bool = False
    secret_key: str = Field(default="supersecretkey_change_in_production_2024")
    jwt_secret: str = Field(default="jwt_secret_key_change_this_in_production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Database
    database_url: str = Field(default="postgresql+asyncpg://imagemagick:imagemagick@localhost:5432/imagemagick")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # File handling
    max_upload_size_mb: int = 100
    allowed_extensions: List[str] = [
        ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", 
        ".tiff", ".tif", ".pdf", ".bmp", ".ico", ".heic", ".heif", ".avif"
    ]
    upload_dir: str = "/app/uploads"
    processed_dir: str = "/app/processed"
    temp_dir: str = "/tmp/imagemagick"
    
    # ImageMagick
    imagemagick_timeout: int = 180
    imagemagick_memory_limit: str = "2GB"
    max_concurrent_jobs: int = 10
    
    # AI / Background removal (rembg)
    # Default model. isnet-general-use gives noticeably cleaner edges than u2net
    # at comparable speed. Other options: u2net, u2net_human_seg, silueta.
    rembg_model: str = "isnet-general-use"
    # Images larger than this (longest side, px) are downscaled before inference
    # for speed, then scaled back. Lower = faster on weak CPUs, higher = sharper.
    rembg_max_size: int = 2048
    # ONNX Runtime intra-op threads. 0 = use all available cores.
    # Set to a low number (e.g. 2) on shared/weak VPS to limit CPU usage.
    onnx_threads: int = 0
    
    # AI / GPU acceleration (v1.1.0)
    # Set to true automatically by Dockerfile.gpu (ENV GPU_ENABLED=true).
    # On the CPU image this stays false and CUDA is never attempted.
    gpu_enabled: bool = False
    # Force CPU even on the GPU image (debugging / fallback). Overrides gpu_enabled.
    force_cpu: bool = False
    # GPU memory arena cap (bytes) for the CUDA execution provider.
    # 0 (default) = no fixed cap; onnxruntime grows the arena dynamically up to
    # whatever the card has. Required for large models like BiRefNet — a low cap
    # causes "Available memory of 0 is smaller than requested bytes". Set a
    # positive value only to hard-cap the arena when sharing the card.
    cuda_gpu_mem_limit: int = 0
    
    # Security
    rate_limit: str = "100/minute"
    require_login: bool = True  # If True, users must login to use the app
    allow_registration: bool = True  # If False, only admins can create users
    
    # Default processing settings
    default_output_format: str = "webp"
    default_quality: int = 85
    
    # OAuth (optional)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # History retention
    history_retention_hours: int = 24
    
    @field_validator('require_login', 'allow_registration', 'gpu_enabled', 'force_cpu', mode='before')
    @classmethod
    def parse_bool(cls, v):
        """Parse boolean from various string formats"""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    @field_validator('google_client_id', 'google_client_secret', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty strings to None for optional fields"""
        if v is None or (isinstance(v, str) and v.strip() == ''):
            return None
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
