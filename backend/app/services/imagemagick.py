"""
ImageMagick service for secure command execution
"""

import os
import re
import shlex
import asyncio
import subprocess
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import uuid
from datetime import datetime

from app.core.config import settings


class ImageMagickError(Exception):
    """Custom exception for ImageMagick errors"""
    pass


class ImageMagickService:
    """
    Secure ImageMagick command execution service
    """
    
    # Whitelisted operations
    ALLOWED_OPERATIONS = {
        # Basic transforms
        "resize", "crop", "rotate", "flip", "flop", "transpose", "transverse",
        # Quality and format
        "quality", "format", "compress", "strip",
        # Filters and effects
        "blur", "sharpen", "unsharp", "emboss", "edge", "charcoal", "sketch",
        "grayscale", "sepia-tone", "negate", "modulate", "brightness-contrast",
        "colorize", "tint", "gamma", "level", "auto-level", "normalize",
        "enhance", "auto-orient", "auto-gamma",
        # Watermark and overlay
        "composite", "annotate", "watermark", "draw", "font", "pointsize", "fill", "gravity",
        # Geometry
        "extent", "trim", "shave", "border", "frame",
        # Color adjustments
        "colorspace", "depth", "alpha", "transparent",
        # Metadata
        "identify", "verbose",
        # Other safe operations
        "thumbnail", "sample", "scale", "adaptive-resize",
        "deskew", "despeckle", "noise", "median",
    }
    
    # Dangerous patterns to block
    BLOCKED_PATTERNS = [
        r"[;&|`$]",  # Shell injection characters
        r"\.\./",  # Path traversal
        r"ephemeral:",  # ImageMagick special protocols
        r"msl:",
        r"mvg:",
        r"url:",
        r"https?:",
        r"ftp:",
        r"label:",
        r"caption:",
        r"pango:",
        r"/dev/",  # Device files
        r"/proc/",  # Proc filesystem
        r"/etc/",  # Config files
        r"\\x",  # Hex escape sequences
    ]
    
    # Allowed input formats
    ALLOWED_INPUT_FORMATS = {
        "jpg", "jpeg", "png", "webp", "gif", "svg", "tiff", "tif",
        "pdf", "bmp", "ico", "heic", "heif", "avif", "psd"
    }
    
    # Allowed output formats
    ALLOWED_OUTPUT_FORMATS = {
        "jpg", "jpeg", "png", "webp", "gif", "avif", "tiff", "pdf", "bmp", "ico"
    }
    
    def __init__(self):
        self.timeout = settings.imagemagick_timeout
        self.memory_limit = settings.imagemagick_memory_limit
        self.temp_dir = Path(settings.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._magick_cmd = None  # Will be detected on first use
    
    async def _get_magick_cmd(self) -> str:
        """Detect which ImageMagick command is available"""
        if self._magick_cmd:
            return self._magick_cmd
        
        for cmd in ["magick", "convert"]:
            try:
                process = await asyncio.create_subprocess_shell(
                    f"which {cmd}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()
                if process.returncode == 0:
                    self._magick_cmd = cmd
                    return cmd
            except:
                pass
        
        self._magick_cmd = "magick"  # Default fallback
        return self._magick_cmd
    
    def validate_file(self, file_path: str) -> bool:
        """Validate that file exists and has allowed extension"""
        path = Path(file_path)
        if not path.exists():
            return False
        
        ext = path.suffix.lower().lstrip(".")
        return ext in self.ALLOWED_INPUT_FORMATS
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Validate ImageMagick command for security
        Returns (is_valid, error_message)
        """
        # Check for blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Blocked pattern detected: {pattern}"
        
        return True, ""
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path components
        filename = os.path.basename(filename)
        # Remove potentially dangerous characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        return filename
    
    async def build_command(
        self,
        input_path: str,
        output_path: str,
        operations: List[Dict]
    ) -> str:
        """
        Build a safe ImageMagick command from operations
        """
        magick_cmd = await self._get_magick_cmd()
        
        cmd_parts = [
            magick_cmd,
            f"-limit memory {self.memory_limit}",
            f"-limit time {self.timeout}",
        ]
        
        # Check if input is PDF
        is_pdf = input_path.lower().endswith('.pdf')
        
        if is_pdf:
            # For PDF: add density before input for better quality
            cmd_parts.append("-density 150")
            # Add input file with page selector [0] for first page
            cmd_parts.append(shlex.quote(f"{input_path}[0]"))
            # Flatten to handle transparency
            cmd_parts.append("-flatten")
        else:
            # Add input file (quoted and validated)
            cmd_parts.append(shlex.quote(input_path))
        
        # Always auto-orient to fix EXIF rotation issues
        cmd_parts.append("-auto-orient")
        
        # Process operations
        for op in operations:
            op_name = op.get("operation", "").lower().replace("_", "-")
            params = op.get("params", {})
            
            if op_name not in self.ALLOWED_OPERATIONS:
                continue
            
            # Build operation string based on type
            if op_name == "resize":
                width = int(params.get("width", 0))
                height = int(params.get("height", 0))
                mode = params.get("mode", "")
                
                if width > 0 and height > 0:
                    geometry = f"{width}x{height}"
                    if mode == "force":
                        # Force exact dimensions (ignore aspect ratio)
                        geometry += "!"
                    elif mode == "fill":
                        # Fill/cover - resize to fill the box (may need crop after)
                        geometry += "^"
                    # For "fit" mode (contain) - no suffix means fit within dimensions
                    # maintaining aspect ratio, will enlarge or shrink as needed
                    cmd_parts.append(f"-resize {geometry}")
                elif params.get("percent"):
                    pct = int(params["percent"])
                    cmd_parts.append(f"-resize {pct}%")
            
            elif op_name == "crop":
                width = int(params.get("width", 0))
                height = int(params.get("height", 0))
                x = int(params.get("x", 0))
                y = int(params.get("y", 0))
                if width > 0 and height > 0:
                    cmd_parts.append(f"-crop {width}x{height}+{x}+{y} +repage")
            
            elif op_name == "crop_aspect":
                # Crop to aspect ratio (centered, maximum size)
                aspect_w = int(params.get("aspect_w", 1))
                aspect_h = int(params.get("aspect_h", 1))
                # Use ImageMagick's gravity + extent for centered crop to aspect ratio
                cmd_parts.append("-gravity center")
                cmd_parts.append(f"-crop {aspect_w}:{aspect_h}")
                cmd_parts.append("+repage")
            
            elif op_name == "rotate":
                angle = float(params.get("angle", 0))
                cmd_parts.append(f"-rotate {angle}")
            
            elif op_name == "flip":
                cmd_parts.append("-flip")
            
            elif op_name == "flop":
                cmd_parts.append("-flop")
            
            elif op_name == "quality":
                quality = max(1, min(100, int(params.get("value", 85))))
                cmd_parts.append(f"-quality {quality}")
            
            elif op_name == "blur":
                # CSS blur(Xpx) vs ImageMagick -gaussian-blur
                # CSS blur is visually stronger, so we need higher sigma in IM
                # After testing: CSS 10px ≈ ImageMagick sigma 8-10
                css_blur = float(params.get("sigma", params.get("radius", 0)))
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"BLUR: css_blur={css_blur}, params={params}")
                if css_blur > 0:
                    # Use gaussian-blur for better quality and closer match to CSS
                    sigma = css_blur * 3.0  # 80% of CSS value
                    cmd_parts.append(f"-gaussian-blur 0x{sigma:.1f}")
                    logger.info(f"BLUR: Added -gaussian-blur 0x{sigma:.1f}")
            
            elif op_name == "sharpen":
                radius = float(params.get("radius", 0))
                sigma = float(params.get("sigma", 1))
                cmd_parts.append(f"-sharpen {radius}x{sigma}")
            
            elif op_name == "grayscale":
                cmd_parts.append("-colorspace Gray")
            
            elif op_name == "sepia-tone":
                threshold = float(params.get("threshold", 80))
                cmd_parts.append(f"-sepia-tone {threshold}%")
            
            elif op_name == "brightness-contrast":
                brightness = int(params.get("brightness", 0))
                contrast = int(params.get("contrast", 0))
                cmd_parts.append(f"-brightness-contrast {brightness}x{contrast}")
            
            elif op_name == "modulate":
                brightness = int(params.get("brightness", 100))
                saturation = int(params.get("saturation", 100))
                hue = int(params.get("hue", 100))
                cmd_parts.append(f"-modulate {brightness},{saturation},{hue}")
            
            elif op_name == "auto-orient":
                cmd_parts.append("-auto-orient")
            
            elif op_name == "enhance":
                # More visible enhancement than basic -enhance
                # Combines: normalize + slight contrast boost + subtle sharpening
                cmd_parts.append("-normalize")
                cmd_parts.append("-modulate 100,110,100")  # +10% saturation
                cmd_parts.append("-unsharp 0x0.5+0.5+0.008")  # subtle sharpening
            
            elif op_name == "auto-level":
                cmd_parts.append("-auto-level")
            
            elif op_name == "normalize":
                cmd_parts.append("-normalize")
            
            elif op_name == "strip":
                cmd_parts.append("-strip")
            
            elif op_name == "trim":
                cmd_parts.append("-trim +repage")
            
            elif op_name == "negate":
                cmd_parts.append("-negate")
            
            elif op_name == "annotate" or op_name == "watermark":
                text = params.get("text", "")
                if text:
                    # Sanitize text - remove dangerous characters
                    text = re.sub(r'[`$\\]', '', text)
                    position = params.get("position", "southeast").lower()
                    font_size = int(params.get("font_size", 24))
                    color = params.get("color", "white")
                    opacity = float(params.get("opacity", 0.5))
                    
                    # Map position to gravity
                    gravity_map = {
                        "northwest": "NorthWest",
                        "north": "North", 
                        "northeast": "NorthEast",
                        "west": "West",
                        "center": "Center",
                        "east": "East",
                        "southwest": "SouthWest",
                        "south": "South",
                        "southeast": "SouthEast",
                    }
                    gravity = gravity_map.get(position, "SouthEast")
                    
                    # Calculate offset proportional to font size (shadow offset ~5% of font size)
                    shadow_offset = max(2, int(font_size * 0.05))
                    text_offset = max(10, int(font_size * 0.4))  # margin from edge
                    
                    # Build annotate command with shadow for visibility
                    cmd_parts.append(f"-gravity {gravity}")
                    cmd_parts.append(f"-pointsize {font_size}")
                    cmd_parts.append(f"-fill 'rgba(0,0,0,{opacity})'")
                    cmd_parts.append(f"-annotate +{text_offset + shadow_offset}+{text_offset + shadow_offset} {shlex.quote(text)}")
                    cmd_parts.append(f"-fill 'rgba(255,255,255,{opacity})'")
                    cmd_parts.append(f"-annotate +{text_offset}+{text_offset} {shlex.quote(text)}")
            
            elif op_name == "transparent":
                # Make a color transparent (remove background)
                color = params.get("color", "white").lower()
                fuzz = int(params.get("fuzz", 10))
                fuzz = max(0, min(100, fuzz))  # Clamp 0-100
                
                if color == "auto":
                    # Try to detect background color from corners
                    # Use flood fill from corners with transparency
                    cmd_parts.append("-alpha set")
                    cmd_parts.append(f"-fuzz {fuzz}%")
                    # Fill from all 4 corners
                    cmd_parts.append("-fill none -draw 'color 0,0 floodfill'")
                elif color in ("white", "black", "red", "green", "blue", "transparent"):
                    cmd_parts.append("-alpha set")
                    cmd_parts.append(f"-fuzz {fuzz}%")
                    cmd_parts.append(f"-transparent {color}")
                else:
                    # Treat as hex color
                    cmd_parts.append("-alpha set")
                    cmd_parts.append(f"-fuzz {fuzz}%")
                    cmd_parts.append(f"-transparent '{color}'")
        
        # Add output file
        cmd_parts.append(shlex.quote(output_path))
        
        return " ".join(cmd_parts)
    
    async def build_raw_command(
        self,
        input_path: str,
        output_path: str,
        raw_command: str
    ) -> Tuple[str, str]:
        """
        Build command from raw user input (terminal mode)
        Returns (command, error_message)
        """
        # Validate command
        is_valid, error = self.validate_command(raw_command)
        if not is_valid:
            return "", error
        
        magick_cmd = await self._get_magick_cmd()
        
        # Replace placeholders
        command = raw_command.replace("{input}", shlex.quote(input_path))
        command = command.replace("{output}", shlex.quote(output_path))
        
        # Ensure command starts with magick/convert
        if not command.strip().startswith(("magick", "convert")):
            command = f"{magick_cmd} {command}"
        
        # Add resource limits
        limits = f"-limit memory {self.memory_limit} -limit time {self.timeout}"
        if command.strip().startswith("magick"):
            command = command.replace("magick ", f"magick {limits} ", 1)
        elif command.strip().startswith("convert"):
            command = command.replace("convert ", f"convert {limits} ", 1)
        
        return command, ""
    
    def _run_command_sync(self, command: str) -> Tuple[bool, str, str]:
        """
        Synchronous command execution in a clean environment.
        This runs in a thread pool to avoid blocking the event loop.
        """
        import logging
        import os
        import signal
        logger = logging.getLogger(__name__)
        
        # Create minimal clean environment
        clean_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'HOME': '/tmp',
            'TMPDIR': '/tmp',
            'MAGICK_TEMPORARY_PATH': '/tmp',
            'LC_ALL': 'C',
        }
        
        def preexec():
            """Pre-exec function to further isolate the child process"""
            os.setsid()  # Create new session
            # Reset signal handlers
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
        
        try:
            logger.debug(f"Executing command: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=self.timeout,
                cwd=str(self.temp_dir),
                env=clean_env,
                preexec_fn=preexec,
                close_fds=True,
            )
            
            success = result.returncode == 0
            stdout_str = result.stdout.decode('utf-8', errors='replace')
            stderr_str = result.stderr.decode('utf-8', errors='replace')
            
            if not success:
                logger.warning(f"Command failed (exit {result.returncode}): {stderr_str}")
            
            return success, stdout_str, stderr_str
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {self.timeout}s: {command}")
            return False, "", f"Command timed out after {self.timeout} seconds"
        except Exception as e:
            logger.exception(f"Command execution error: {e}")
            return False, "", str(e)
    
    async def execute(self, command: str) -> Tuple[bool, str, str]:
        """
        Execute ImageMagick command with timeout and resource limits
        Returns (success, stdout, stderr)
        
        Uses subprocess.run in a thread pool with clean environment
        to avoid ONNX Runtime library conflicts.
        """
        import concurrent.futures
        
        loop = asyncio.get_event_loop()
        
        # Run in thread pool to avoid blocking
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(
                executor,
                self._run_command_sync,
                command
            )
        
        return result
    
    async def get_image_info(self, file_path: str) -> Optional[Dict]:
        """Get image metadata using ImageMagick identify"""
        magick_cmd = await self._get_magick_cmd()
        
        # Use 'identify' command (works with both ImageMagick 6 and 7)
        command = f"identify -verbose {shlex.quote(file_path)}"
        
        success, stdout, stderr = await self.execute(command)
        
        if not success:
            return None
        
        # Parse output
        info = {
            "format": None,
            "width": None,
            "height": None,
            "colorspace": None,
            "depth": None,
            "filesize": None,
        }
        
        for line in stdout.split("\n"):
            line = line.strip()
            if line.startswith("Format:"):
                info["format"] = line.split(":")[1].strip().split()[0]
            elif line.startswith("Geometry:"):
                match = re.search(r"(\d+)x(\d+)", line)
                if match:
                    info["width"] = int(match.group(1))
                    info["height"] = int(match.group(2))
            elif line.startswith("Colorspace:"):
                info["colorspace"] = line.split(":")[1].strip()
            elif line.startswith("Depth:"):
                info["depth"] = line.split(":")[1].strip()
            elif line.startswith("Filesize:"):
                info["filesize"] = line.split(":")[1].strip()
        
        return info
    
    async def create_thumbnail(
        self,
        input_path: str,
        output_path: str,
        size: int = 300
    ) -> bool:
        """Create a thumbnail of the image"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify input file exists
        if not Path(input_path).exists():
            logger.error(f"Input file does not exist: {input_path}")
            return False
        
        # For PDFs, use pdftoppm (more reliable than ImageMagick for PDF)
        is_pdf = input_path.lower().endswith('.pdf')
        
        if is_pdf:
            logger.info(f"Creating PDF thumbnail for: {input_path}")
            
            # Method 1: Try pdftoppm
            temp_base = str(Path(output_path).with_suffix(''))
            temp_file = f"{temp_base}.png"
            
            pdftoppm_cmd = f'pdftoppm -png -f 1 -l 1 -r 150 -singlefile "{input_path}" "{temp_base}"'
            logger.info(f"PDF thumbnail command: {pdftoppm_cmd}")
            
            try:
                process = await asyncio.create_subprocess_shell(
                    pdftoppm_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
                
                logger.info(f"pdftoppm returncode: {process.returncode}, checking for: {temp_file}")
                
                if process.returncode == 0 and Path(temp_file).exists():
                    # Now resize to thumbnail size - try both commands
                    for resize_cmd_name in ["magick", "convert"]:
                        resize_cmd = f'{resize_cmd_name} "{temp_file}" -thumbnail "{size}x{size}>" -quality 85 "{output_path}"'
                        success, _, resize_err = await self.execute(resize_cmd)
                        if success:
                            break
                        if "not found" not in resize_err.lower():
                            break
                    
                    # Clean up temp file
                    try:
                        Path(temp_file).unlink()
                    except:
                        pass
                    
                    if success and Path(output_path).exists():
                        logger.info(f"PDF thumbnail created: {output_path}")
                        return True
                    else:
                        logger.warning(f"PDF thumbnail resize failed: {resize_err}")
                else:
                    logger.warning(f"pdftoppm failed: returncode={process.returncode}, stderr={stderr.decode()}")
            except asyncio.TimeoutError:
                logger.error("pdftoppm timeout")
            except Exception as e:
                logger.exception(f"PDF thumbnail exception: {e}")
            
            # Method 2: Fallback to ImageMagick with ghostscript
            logger.info("Trying ImageMagick fallback for PDF")
            for cmd in ["magick", "convert"]:
                try:
                    command = f'{cmd} -density 150 "{input_path}[0]" -thumbnail "{size}x{size}>" -quality 85 -background white -flatten "{output_path}"'
                    logger.info(f"PDF fallback command: {command}")
                    success, stdout, stderr = await self.execute(command)
                    
                    if success and Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                        logger.info(f"PDF thumbnail created (fallback): {output_path}")
                        return True
                    else:
                        logger.warning(f"Fallback failed: success={success}, exists={Path(output_path).exists()}, stderr={stderr}")
                except Exception as e:
                    logger.exception(f"PDF fallback exception ({cmd}): {e}")
                    continue
            
            # Method 3: Try gs directly
            logger.info("Trying ghostscript directly for PDF")
            try:
                gs_output = str(Path(output_path).with_suffix('.png'))
                gs_cmd = f'gs -dNOPAUSE -dBATCH -sDEVICE=png16m -r150 -dFirstPage=1 -dLastPage=1 -sOutputFile="{gs_output}" "{input_path}"'
                logger.info(f"GS command: {gs_cmd}")
                
                process = await asyncio.create_subprocess_shell(
                    gs_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(process.communicate(), timeout=30)
                
                if Path(gs_output).exists():
                    # Resize - try both commands
                    for resize_cmd_name in ["magick", "convert"]:
                        resize_cmd = f'{resize_cmd_name} "{gs_output}" -thumbnail "{size}x{size}>" -quality 85 "{output_path}"'
                        success, _, _ = await self.execute(resize_cmd)
                        if success:
                            break
                    try:
                        Path(gs_output).unlink()
                    except:
                        pass
                    if success and Path(output_path).exists():
                        logger.info(f"PDF thumbnail created (gs): {output_path}")
                        return True
            except Exception as e:
                logger.exception(f"GS exception: {e}")
        else:
            # Check if input is PNG - use Pillow instead (ImageMagick has conflicts with PNG libs)
            is_png = input_path.lower().endswith('.png')
            
            if is_png:
                logger.info(f"Using Pillow for PNG thumbnail: {input_path}")
                try:
                    from PIL import Image as PILImage
                    
                    with PILImage.open(input_path) as img:
                        # Calculate thumbnail size maintaining aspect ratio
                        img.thumbnail((size, size), PILImage.Resampling.LANCZOS)
                        
                        # If RGBA, composite on white background for webp thumbnail
                        if img.mode == 'RGBA':
                            background = PILImage.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[3])  # Use alpha as mask
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Save thumbnail
                        img.save(output_path, 'WEBP', quality=85)
                        
                        if Path(output_path).exists():
                            logger.info(f"PNG thumbnail created with Pillow: {output_path}")
                            return True
                except Exception as e:
                    logger.exception(f"Pillow thumbnail exception: {e}")
            
            # Regular image - use ImageMagick
            for cmd in ["magick", "convert"]:
                try:
                    command = f'{cmd} "{input_path}" -thumbnail "{size}x{size}>" -quality 85 -background white -flatten "{output_path}"'
                    logger.info(f"Thumbnail command: {command}")
                    success, stdout, stderr = await self.execute(command)
                    
                    if success and Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                        logger.info(f"Thumbnail created: {output_path}")
                        return True
                    elif stderr:
                        logger.warning(f"Thumbnail failed ({cmd}): {stderr[:200]}")
                        continue
                except Exception as e:
                    logger.exception(f"Thumbnail exception ({cmd}): {e}")
                    continue
        
        logger.error(f"All thumbnail attempts failed for: {input_path}")
        return False
    
    async def create_pdf_preview(
        self,
        input_path: str,
        output_path: str,
        page: int = 0,
        density: int = 150
    ) -> bool:
        """Create a preview image of a PDF page"""
        # Use ImageMagick to convert PDF page to image
        for cmd in ["magick", "convert"]:
            command = f"{cmd} -density {density} {shlex.quote(input_path)}[{page}] -background white -alpha remove -quality 90 {shlex.quote(output_path)}"
            success, _, stderr = await self.execute(command)
            if success:
                return True
            if "not found" not in stderr.lower():
                break
        return False
    
    async def apply_preview(
        self,
        input_path: str,
        operations: List[Dict],
        max_size: int = 800
    ) -> Optional[str]:
        """
        Apply operations to image and return preview (for live editing)
        Returns base64 encoded image data or None on error
        """
        import base64
        import logging
        logger = logging.getLogger(__name__)
        
        # Verify input file exists
        if not Path(input_path).exists():
            logger.error(f"Input file not found: {input_path}")
            return None
        
        # Generate temp output path
        output_path = self.generate_temp_path("webp")
        
        try:
            # Build command with resize for preview
            preview_ops = operations.copy()
            # Add resize to limit preview size
            preview_ops.insert(0, {
                "operation": "resize",
                "params": {"width": max_size, "height": max_size, "mode": "fit"}
            })
            
            command = await self.build_command(input_path, output_path, preview_ops)
            logger.info(f"Preview command: {command}")
            
            success, stdout, stderr = await self.execute(command)
            
            if success and Path(output_path).exists():
                # Read and encode as base64
                with open(output_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                
                # Clean up temp file
                Path(output_path).unlink(missing_ok=True)
                
                return f"data:image/webp;base64,{data}"
            else:
                logger.error(f"Preview generation failed: {stderr}")
                return None
                
        except Exception as e:
            logger.exception(f"Error generating preview: {e}")
            # Clean up temp file if exists
            Path(output_path).unlink(missing_ok=True)
            return None
    
    def generate_temp_path(self, extension: str = "png") -> str:
        """Generate a unique temporary file path"""
        filename = f"{uuid.uuid4().hex}.{extension}"
        return str(self.temp_dir / filename)


# Singleton instance
imagemagick_service = ImageMagickService()
