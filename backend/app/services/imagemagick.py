"""
ImageMagick service for secure command execution
"""

import os
import re
import shlex
import asyncio
import logging
import subprocess
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


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
    
    # Flags permitted in raw/terminal mode. This is defense-in-depth ON TOP OF
    # shell=False: even without it the argv execution below makes OS command
    # injection impossible, but the allowlist also blocks ImageMagick-native
    # abuse (arbitrary file read/write via -write, -draw 'image', @file, etc.).
    # Note: -limit is intentionally NOT here so a user cannot raise the memory /
    # time caps we prepend ourselves.
    ALLOWED_RAW_FLAGS = {
        "-resize", "-crop", "-repage", "+repage", "-rotate", "-flip", "-flop",
        "-transpose", "-transverse", "-quality", "-format", "-strip", "-thumbnail",
        "-sample", "-scale", "-adaptive-resize", "-extent", "-trim", "-shave",
        "-border", "-frame", "-blur", "-gaussian-blur", "-sharpen", "-unsharp",
        "-emboss", "-edge", "-charcoal", "-sketch", "-colorspace", "-sepia-tone",
        "-negate", "-modulate", "-brightness-contrast", "-colorize", "-tint",
        "-gamma", "-level", "-auto-level", "-auto-gamma", "-normalize", "-enhance",
        "-auto-orient", "-deskew", "-despeckle", "-median", "-depth", "-alpha",
        "-background", "-flatten", "-density", "-gravity", "-pointsize", "-fill",
        "-annotate", "-bordercolor", "-fuzz", "-transparent", "-monochrome",
        "-contrast", "-equalize", "-type", "-compress", "-quantize", "-colors",
        "-dither", "+dither", "-antialias", "+antialias", "-rotate",
    }

    # A token is a flag only if it starts with - or + FOLLOWED BY a letter.
    # This keeps geometry like "+10+10" and negative numbers like "-5" as values.
    _RAW_FLAG_RE = re.compile(r"^[-+][a-zA-Z]")

    # Protocol / coder prefixes and path patterns ImageMagick treats specially;
    # they can read or write arbitrary files or fetch URLs. Always rejected.
    _RAW_TOKEN_BLOCKLIST = re.compile(
        r"(?:^@|@/|ephemeral:|msl:|mvg:|url:|https?:|ftp:|file:|label:|caption:|"
        r"pango:|text:|inline:|xc:@|/dev/|/proc/|/sys/|/etc/|\.\./)",
        re.IGNORECASE,
    )

    # Allowed input formats
    ALLOWED_INPUT_FORMATS = {
        "jpg", "jpeg", "png", "webp", "gif", "svg", "tiff", "tif",
        "pdf", "bmp", "ico", "heic", "heif", "avif", "psd"
    }
    
    # Allowed output formats
    ALLOWED_OUTPUT_FORMATS = {
        "jpg", "jpeg", "png", "webp", "gif", "avif", "tiff", "pdf", "bmp", "ico"
    }

    # Colour values accepted from request params. ImageMagick's own colour
    # parser is far more permissive than we need, so user input is narrowed to
    # three well-understood shapes: a known name, a hex literal, or rgb()/rgba().
    NAMED_COLORS = {
        "white", "black", "red", "green", "blue", "yellow", "cyan", "magenta",
        "gray", "grey", "orange", "purple", "brown", "pink", "silver", "gold",
        "navy", "teal", "olive", "maroon", "lime", "aqua", "fuchsia",
        "none", "transparent",
    }

    _COLOR_HEX_RE = re.compile(r"^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$")
    _COLOR_FUNC_RE = re.compile(
        r"^rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*"
        r"(?:,\s*(?:0|1|0?\.\d+)\s*)?\)$"
    )

    @classmethod
    def _safe_color(cls, value, default: str = "white") -> str:
        """
        Reduce a user-supplied colour to a form ImageMagick parses predictably.

        Anything unrecognised falls back to `default` rather than raising: these
        values arrive as free-form request params, and a bad colour should not
        turn an otherwise valid edit into a 500.
        """
        import logging

        color = str(value).strip().lower()
        if color in cls.NAMED_COLORS:
            return color
        if cls._COLOR_HEX_RE.match(color) or cls._COLOR_FUNC_RE.match(color):
            return color

        logging.getLogger(__name__).warning(
            f"Rejected colour value {value!r}, falling back to {default!r}"
        )
        return default


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
                process = await asyncio.create_subprocess_exec(
                    "which", cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()
                if process.returncode == 0:
                    self._magick_cmd = cmd
                    return cmd
            except OSError:
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
    
    async def build_argv(
        self,
        input_path: str,
        output_path: str,
        operations: List[Dict]
    ) -> List[str]:
        """
        Build an ARGV LIST for the requested operations.

        Returns a list executed with shell=False, so no parameter value can ever
        be interpreted as a shell metacharacter. Every value below is either
        cast to int/float, mapped through a lookup table, or passed through
        _safe_color() — user strings never reach the argument list verbatim.
        """
        magick_cmd = await self._get_magick_cmd()

        argv: List[str] = [
            magick_cmd,
            "-limit", "memory", str(self.memory_limit),
            "-limit", "time", str(self.timeout),
        ]

        # Check if input is PDF
        is_pdf = input_path.lower().endswith('.pdf')

        if is_pdf:
            # For PDF: add density before input for better quality
            argv += ["-density", "150"]
            # Add input file with page selector [0] for first page
            argv.append(f"{input_path}[0]")
            # Flatten to handle transparency
            argv.append("-flatten")
        else:
            argv.append(input_path)

        # Always auto-orient to fix EXIF rotation issues
        argv.append("-auto-orient")

        # Process operations
        # Get image dimensions for scaling
        img_width = None
        try:
            from PIL import Image as PILImage
            with PILImage.open(input_path) as pil_img:
                img_width = pil_img.width
        except Exception:
            pass

        for op in operations:
            op_name = op.get("operation", "").lower().replace("_", "-")
            params = op.get("params", {})

            if op_name not in self.ALLOWED_OPERATIONS:
                continue

            # Build operation arguments based on type
            if op_name == "resize":
                width = int(params.get("width", 0))
                height = int(params.get("height", 0))
                mode = params.get("mode", "")

                if width > 0 and height > 0:
                    geometry = f"{width}x{height}"
                    if mode == "force":
                        geometry += "!"
                    elif mode == "fill":
                        geometry += "^"
                    argv += ["-resize", geometry]
                elif params.get("percent"):
                    pct = int(params["percent"])
                    argv += ["-resize", f"{pct}%"]

            elif op_name == "crop":
                width = int(params.get("width", 0))
                height = int(params.get("height", 0))
                x = int(params.get("x", 0))
                y = int(params.get("y", 0))
                if width > 0 and height > 0:
                    argv += ["-crop", f"{width}x{height}+{x}+{y}", "+repage"]

            elif op_name == "crop-aspect":
                aspect_w = int(params.get("aspect_w", 1))
                aspect_h = int(params.get("aspect_h", 1))
                argv += ["-gravity", "center"]
                argv += ["-crop", f"{aspect_w}:{aspect_h}"]
                argv.append("+repage")

            elif op_name == "rotate":
                angle = float(params.get("angle", 0))
                argv += ["-rotate", str(angle)]

            elif op_name == "flip":
                argv.append("-flip")

            elif op_name == "flop":
                argv.append("-flop")

            elif op_name == "quality":
                quality = max(1, min(100, int(params.get("value", 85))))
                argv += ["-quality", str(quality)]

            elif op_name == "blur":
                css_blur = float(params.get("sigma", params.get("radius", 0)))
                if css_blur > 0:
                    if img_width and img_width > 800:
                        scale_factor = img_width / 800
                        sigma = css_blur * scale_factor
                    else:
                        sigma = css_blur * 1.0
                    argv += ["-blur", f"0x{sigma:.1f}"]
                    logger.info(
                        f"BLUR: css_blur={css_blur}, img_width={img_width}, sigma={sigma:.1f}"
                    )

            elif op_name == "sharpen":
                radius = float(params.get("radius", 0))
                sigma = float(params.get("sigma", 1))
                argv += ["-sharpen", f"{radius}x{sigma}"]

            elif op_name == "grayscale":
                argv += ["-colorspace", "Gray"]

            elif op_name == "sepia-tone":
                threshold = float(params.get("threshold", 80))
                argv += ["-sepia-tone", f"{threshold}%"]

            elif op_name == "brightness-contrast":
                brightness = int(params.get("brightness", 0))
                contrast = int(params.get("contrast", 0))
                argv += ["-brightness-contrast", f"{brightness}x{contrast}"]

            elif op_name == "modulate":
                brightness = int(params.get("brightness", 100))
                saturation = int(params.get("saturation", 100))
                hue = int(params.get("hue", 100))
                argv += ["-modulate", f"{brightness},{saturation},{hue}"]

            elif op_name == "auto-orient":
                argv.append("-auto-orient")

            elif op_name == "enhance":
                argv.append("-normalize")
                argv += ["-modulate", "100,110,100"]
                argv += ["-unsharp", "0x0.5+0.5+0.008"]

            elif op_name == "auto-level":
                argv.append("-auto-level")

            elif op_name == "normalize":
                argv.append("-normalize")

            elif op_name == "strip":
                argv.append("-strip")

            elif op_name == "trim":
                argv += ["-trim", "+repage"]

            elif op_name == "negate":
                argv.append("-negate")

            elif op_name == "annotate" or op_name == "watermark":
                text = params.get("text", "")
                if text:
                    # Text is a single argv token, so it needs no escaping; it is
                    # still length-capped so a huge string cannot blow up argv.
                    text = str(text)[:500]
                    position = params.get("position", "southeast").lower()
                    font_size_base = int(params.get("font_size", 24))
                    font_size = max(font_size_base, int(font_size_base * (img_width / 800))) if img_width else font_size_base
                    opacity = max(0.0, min(1.0, float(params.get("opacity", 0.5))))

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

                    shadow_offset = max(2, int(font_size * 0.05))
                    text_offset = max(10, int(font_size * 0.4))

                    argv += ["-gravity", gravity]
                    argv += ["-pointsize", str(font_size)]
                    argv += ["-fill", f"rgba(0,0,0,{opacity})"]
                    argv += [
                        "-annotate",
                        f"+{text_offset + shadow_offset}+{text_offset + shadow_offset}",
                        text,
                    ]
                    argv += ["-fill", f"rgba(255,255,255,{opacity})"]
                    argv += ["-annotate", f"+{text_offset}+{text_offset}", text]

            elif op_name == "transparent":
                raw_color = str(params.get("color", "white")).strip().lower()
                fuzz = max(0, min(100, int(params.get("fuzz", 10))))

                argv.append("-alpha")
                argv.append("set")
                argv += ["-fuzz", f"{fuzz}%"]

                if raw_color == "auto":
                    argv += ["-fill", "none", "-draw", "color 0,0 floodfill"]
                else:
                    argv += ["-transparent", self._safe_color(raw_color)]

        # Add output file
        argv.append(output_path)

        return argv

    def _validate_raw_token(self, token: str) -> Tuple[bool, str]:
        """Validate a single token from a raw/terminal command."""
        # Absolute paths and special coder/protocol prefixes are never allowed
        # for user-supplied tokens (the real input/output paths are appended
        # separately and never go through this check).
        if token.startswith("/") or self._RAW_TOKEN_BLOCKLIST.search(token):
            return False, f"Disallowed token in raw command: {token!r}"
        # Anything that looks like a flag must be on the allowlist.
        if self._RAW_FLAG_RE.match(token) and token not in self.ALLOWED_RAW_FLAGS:
            return False, f"Flag not allowed in raw command: {token!r}"
        return True, ""

    async def build_raw_argv(
        self,
        input_path: str,
        output_path: str,
        raw_command: str,
    ) -> Tuple[List[str], str]:
        """
        Build an ARGV LIST (not a shell string) from raw/terminal input.

        The list is executed with shell=False, so no shell metacharacter -
        newline, ;, &, |, $, >, backtick - can ever start a second command.
        Every token is additionally checked against a strict allowlist.
        Returns (argv, error_message); argv is empty when error_message is set.
        """
        magick_cmd = await self._get_magick_cmd()

        try:
            tokens = shlex.split(raw_command)
        except ValueError as exc:
            return [], f"Could not parse command: {exc}"

        # Drop a leading 'magick'/'convert' the user may have typed; we add our own.
        if tokens and tokens[0] in ("magick", "convert"):
            tokens = tokens[1:]

        argv: List[str] = [
            magick_cmd,
            "-limit", "memory", str(self.memory_limit),
            "-limit", "time", str(self.timeout),
        ]

        saw_input = saw_output = False
        for token in tokens:
            if token == "{input}":
                argv.append(input_path)
                saw_input = True
                continue
            if token == "{output}":
                argv.append(output_path)
                saw_output = True
                continue

            ok, error = self._validate_raw_token(token)
            if not ok:
                return [], error
            argv.append(token)

        if not saw_input:
            return [], "Command must contain the {input} placeholder"
        if not saw_output:
            return [], "Command must contain the {output} placeholder"

        return argv, ""

    def _run_argv_sync(self, argv: List[str]) -> Tuple[bool, str, str]:
        """Execute an argv list with shell=False in a clean environment."""
        import logging
        import os
        import signal
        logger = logging.getLogger(__name__)

        clean_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'HOME': '/tmp',
            'TMPDIR': '/tmp',
            'MAGICK_TEMPORARY_PATH': '/tmp',
            'LC_ALL': 'C',
        }

        def preexec():
            os.setsid()
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

        try:
            logger.debug(f"Executing argv: {argv}")
            result = subprocess.run(
                argv,
                shell=False,
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
            logger.error(f"Command timed out after {self.timeout}s")
            return False, "", f"Command timed out after {self.timeout} seconds"
        except Exception as exc:
            logger.exception(f"Command execution error: {exc}")
            return False, "", str(exc)

    async def execute_argv(self, argv: List[str]) -> Tuple[bool, str, str]:
        """Execute an argv list (shell=False) in a worker thread."""
        import concurrent.futures

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(executor, self._run_argv_sync, argv)

    async def get_image_info(self, file_path: str) -> Optional[Dict]:
        """Get image metadata using ImageMagick identify"""
        success, stdout, stderr = await self.execute_argv(
            ["identify", "-verbose", file_path]
        )

        if not success:
            return None
        
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
            
            pdftoppm_argv = [
                "pdftoppm", "-png", "-f", "1", "-l", "1", "-r", "150",
                "-singlefile", input_path, temp_base,
            ]
            logger.info(f"PDF thumbnail argv: {pdftoppm_argv}")

            try:
                process = await asyncio.create_subprocess_exec(
                    *pdftoppm_argv,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)

                logger.info(f"pdftoppm returncode: {process.returncode}, checking for: {temp_file}")

                if process.returncode == 0 and Path(temp_file).exists():
                    success, resize_err = False, ""
                    for resize_cmd_name in ["magick", "convert"]:
                        success, _, resize_err = await self.execute_argv([
                            resize_cmd_name, temp_file,
                            "-thumbnail", f"{size}x{size}>",
                            "-quality", "85", output_path,
                        ])
                        if success:
                            break
                        if "not found" not in resize_err.lower():
                            break

                    try:
                        Path(temp_file).unlink()
                    except OSError:
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
                    success, stdout, stderr = await self.execute_argv([
                        cmd, "-density", "150", f"{input_path}[0]",
                        "-thumbnail", f"{size}x{size}>",
                        "-quality", "85", output_path,
                    ])

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
                gs_argv = [
                    "gs", "-dNOPAUSE", "-dBATCH", "-sDEVICE=png16m", "-r150",
                    "-dFirstPage=1", "-dLastPage=1",
                    f"-sOutputFile={gs_output}", input_path,
                ]
                logger.info(f"GS argv: {gs_argv}")

                process = await asyncio.create_subprocess_exec(
                    *gs_argv,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(process.communicate(), timeout=120)

                if Path(gs_output).exists():
                    success = False
                    for resize_cmd_name in ["magick", "convert"]:
                        success, _, _ = await self.execute_argv([
                            resize_cmd_name, gs_output,
                            "-thumbnail", f"{size}x{size}>",
                            "-quality", "85", output_path,
                        ])
                        if success:
                            break
                    try:
                        Path(gs_output).unlink()
                    except OSError:
                        pass
                    if success and Path(output_path).exists():
                        logger.info(f"PDF thumbnail created (gs): {output_path}")
                        return True
            except Exception as e:
                logger.exception(f"GS exception: {e}")
        else:
            # ===== FIX: Use Pillow for ALL thumbnails (fast, no subprocess overhead) =====
            try:
                from PIL import Image as PILImage
                
                with PILImage.open(input_path) as img:
                    # Convert RGBA/P to RGB for WebP/JPEG output compatibility
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # Keep alpha for WebP
                        if output_path.lower().endswith('.webp'):
                            img = img.convert('RGBA')
                        else:
                            background = PILImage.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize to thumbnail dimensions
                    img.thumbnail((size, size), PILImage.LANCZOS)
                    
                    # Save in appropriate format
                    if output_path.lower().endswith('.webp'):
                        img.save(output_path, 'WEBP', quality=85)
                    elif output_path.lower().endswith('.png'):
                        img.save(output_path, 'PNG', optimize=True)
                    else:
                        img.save(output_path, 'JPEG', quality=85)
                
                if Path(output_path).exists():
                    logger.info(f"Thumbnail created with Pillow: {output_path} ({Path(output_path).stat().st_size} bytes)")
                    return True
            except Exception as e:
                logger.warning(f"Pillow thumbnail failed: {e}, falling back to ImageMagick")
            
            # Fallback: use ImageMagick (for formats Pillow can't handle)
            for cmd in ["magick", "convert"]:
                try:
                    success, stdout, stderr = await self.execute_argv([
                        cmd, input_path,
                        "-thumbnail", f"{size}x{size}>",
                        "-quality", "85", output_path,
                    ])

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

        if not Path(input_path).exists():
            logger.error(f"Input file not found: {input_path}")
            return None

        output_path = self.generate_temp_path("webp")

        try:
            preview_ops = operations.copy()
            preview_ops.insert(0, {
                "operation": "resize",
                "params": {"width": max_size, "height": max_size, "mode": "fit"}
            })

            argv = await self.build_argv(input_path, output_path, preview_ops)
            logger.info(f"Preview argv: {argv}")

            success, stdout, stderr = await self.execute_argv(argv)

            if success and Path(output_path).exists():
                with open(output_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                
                Path(output_path).unlink(missing_ok=True)
                
                return f"data:image/webp;base64,{data}"
            else:
                logger.error(f"Preview generation failed: {stderr}")
                return None
                
        except Exception as e:
            logger.exception(f"Error generating preview: {e}")
            Path(output_path).unlink(missing_ok=True)
            return None
    
    def generate_temp_path(self, extension: str = "png") -> str:
        """Generate a unique temporary file path"""
        filename = f"{uuid.uuid4().hex}.{extension}"
        return str(self.temp_dir / filename)


# Singleton instance
imagemagick_service = ImageMagickService()
