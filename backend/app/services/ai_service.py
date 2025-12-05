"""
AI Service for intelligent image processing
Includes background removal using rembg and upscaling
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Literal
import uuid
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """AI-powered image processing service"""
    
    REMBG_MODELS = ["u2net", "isnet-general-use", "u2net_human_seg", "silueta"]
    
    def __init__(self):
        self.temp_dir = Path(settings.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._rembg_available = None
        self._session = None
    
    async def is_available(self) -> bool:
        """Check if rembg is available"""
        if self._rembg_available is None:
            try:
                import rembg
                self._rembg_available = True
                logger.info("rembg is available")
            except ImportError as e:
                logger.error(f"rembg not available: {e}")
                self._rembg_available = False
        return self._rembg_available
    
    def _get_session(self, model: str = "u2net"):
        """Get or create rembg session"""
        if self._session is None:
            try:
                from rembg import new_session
                logger.info(f"Creating rembg session with model: {model}")
                self._session = new_session(model)
                logger.info("Session created successfully")
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                raise
        return self._session
    
    async def remove_background(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        model: str = "u2net",
        alpha_matting: bool = True,
        **kwargs
    ) -> str:
        """Remove background from image using AI (rembg)"""
        
        logger.info(f"=== REMOVE BACKGROUND START ===")
        logger.info(f"Input: {input_path}")
        logger.info(f"Model: {model}, Alpha matting: {alpha_matting}")
        
        if output_path is None:
            output_name = f"nobg_{uuid.uuid4().hex}.png"
            output_path = str(self.temp_dir / output_name)
        
        logger.info(f"Output: {output_path}")
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Check input exists
        if not Path(input_path).exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        logger.info(f"Input file size: {Path(input_path).stat().st_size} bytes")
        
        # Check if pymatting is available for alpha matting
        try:
            import pymatting
            has_pymatting = True
            logger.info("pymatting available")
        except ImportError:
            has_pymatting = False
            logger.warning("pymatting not available, alpha matting disabled")
        
        use_alpha = alpha_matting and has_pymatting
        
        def _process():
            """Synchronous processing"""
            try:
                from PIL import Image
                from rembg import remove
                
                logger.info("Loading image with PIL...")
                img = Image.open(input_path)
                original_size = img.size
                logger.info(f"Image loaded: {img.size}, mode={img.mode}")
                
                # Convert to RGB if needed
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                    logger.info(f"Converted to RGB")
                
                # Resize if very large (for performance)
                max_size = 2048
                scale_factor = 1.0
                if max(img.size) > max_size:
                    scale_factor = max_size / max(img.size)
                    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    logger.info(f"Resized to: {new_size}")
                
                logger.info("Getting rembg session...")
                session = self._get_session(model)
                
                logger.info(f"Calling rembg.remove() with alpha_matting={use_alpha}...")
                
                if use_alpha:
                    result = remove(
                        img, 
                        session=session, 
                        alpha_matting=True,
                        alpha_matting_foreground_threshold=240,
                        alpha_matting_background_threshold=10,
                        alpha_matting_erode_size=10,
                    )
                else:
                    result = remove(img, session=session, alpha_matting=False)
                
                logger.info(f"Remove complete, result size: {result.size}, mode: {result.mode}")
                
                # Scale back if needed
                if scale_factor < 1.0:
                    result = result.resize(original_size, Image.Resampling.LANCZOS)
                    logger.info(f"Scaled back to: {original_size}")
                
                # Ensure RGBA mode for transparency
                if result.mode != 'RGBA':
                    result = result.convert('RGBA')
                
                logger.info(f"Saving to {output_path}...")
                result.save(output_path, 'PNG')
                logger.info("Saved successfully")
                
                return output_path
                
            except Exception as e:
                logger.exception(f"Error in _process: {e}")
                raise
        
        try:
            loop = asyncio.get_running_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _process),
                timeout=300
            )
            logger.info(f"=== REMOVE BACKGROUND SUCCESS ===")
            return result
        except asyncio.TimeoutError:
            logger.error("=== REMOVE BACKGROUND TIMEOUT ===")
            raise RuntimeError("Background removal timed out after 300s")
        except Exception as e:
            logger.exception(f"=== REMOVE BACKGROUND ERROR: {e} ===")
            raise
    
    async def upscale(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        scale: int = 2,
        method: Literal["lanczos", "esrgan"] = "lanczos",
    ) -> str:
        """Upscale image resolution"""
        
        logger.info(f"Upscale: {input_path}, scale={scale}")
        
        if output_path is None:
            ext = Path(input_path).suffix or '.png'
            output_name = f"upscale_{scale}x_{uuid.uuid4().hex}{ext}"
            output_path = str(self.temp_dir / output_name)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        def _upscale():
            from PIL import Image, ImageFilter, ImageEnhance
            
            with Image.open(input_path) as img:
                new_size = (img.width * scale, img.height * scale)
                logger.info(f"Upscaling: {img.size} -> {new_size}")
                
                result = img.resize(new_size, Image.Resampling.LANCZOS)
                result = result.filter(ImageFilter.UnsharpMask(radius=1, percent=50, threshold=3))
                
                if output_path.lower().endswith('.png'):
                    result.save(output_path, 'PNG')
                elif output_path.lower().endswith('.webp'):
                    result.save(output_path, 'WEBP', quality=95)
                else:
                    if result.mode == 'RGBA':
                        result = result.convert('RGB')
                    result.save(output_path, 'JPEG', quality=95)
                
                return output_path
        
        try:
            loop = asyncio.get_running_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, _upscale),
                timeout=120
            )
        except Exception as e:
            logger.exception(f"Upscale error: {e}")
            raise
    
    async def get_available_models(self) -> list:
        return self.REMBG_MODELS
    
    async def diagnose(self) -> dict:
        """Diagnostic info about AI service"""
        info = {
            "rembg_available": False,
            "pymatting_available": False,
            "session_loaded": self._session is not None,
            "u2net_home": os.environ.get("U2NET_HOME", "not set"),
            "home": os.environ.get("HOME", "not set"),
            "models_dir_exists": False,
            "models_found": [],
            "error": None,
        }
        
        try:
            import rembg
            info["rembg_available"] = True
            info["rembg_version"] = getattr(rembg, "__version__", "unknown")
        except ImportError as e:
            info["error"] = f"rembg import error: {e}"
        
        try:
            import pymatting
            info["pymatting_available"] = True
        except ImportError:
            pass
        
        # Check models directory
        u2net_home = os.environ.get("U2NET_HOME", os.path.expanduser("~/.u2net"))
        info["u2net_home"] = u2net_home
        
        if Path(u2net_home).exists():
            info["models_dir_exists"] = True
            info["models_found"] = [str(p) for p in Path(u2net_home).glob("*.onnx")]
        
        return info


# Singleton
ai_service = AIService()
