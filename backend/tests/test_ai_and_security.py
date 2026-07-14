"""
Tests for AI service configuration and path-security utilities.
Covers changes around rembg model defaults and the validate_path sanitizer
(CodeQL alert #23 false positive — this proves the guard actually works).
"""

import pytest


class TestPathValidation:
    """Tests for validate_path() in operations API (path traversal guard)"""
    
    def test_rejects_path_traversal(self):
        """Paths escaping allowed dirs must be denied"""
        from fastapi import HTTPException
        from app.api.operations import validate_path
        
        dangerous = [
            "/etc/passwd",
            "../../../etc/passwd",
            "/root/.ssh/id_rsa",
            "/var/lib/postgresql/data/secret",
        ]
        
        for path in dangerous:
            with pytest.raises(HTTPException) as exc:
                validate_path(path)
            assert exc.value.status_code in (403, 400), (
                f"Expected denial for {path}, got {exc.value.status_code}"
            )
    
    def test_rejects_empty_path(self):
        """Empty path must be rejected with 400"""
        from fastapi import HTTPException
        from app.api.operations import validate_path
        
        with pytest.raises(HTTPException) as exc:
            validate_path("")
        assert exc.value.status_code == 400
    
    def test_accepts_allowed_dir(self):
        """A path inside an allowed dir must pass and return a realpath"""
        import os

        from app.core.config import settings
        from app.core.paths import validate_path

        # settings.temp_dir, not bare /tmp: the whitelist covers the directories
        # the app actually owns, so an unrelated file in /tmp is now rejected.
        target = os.path.join(settings.temp_dir, "some_generated_file.png")
        result = validate_path(target)
        assert isinstance(result, str)
        assert result == os.path.realpath(target)


class TestAIConfiguration:
    """Tests for rembg / AI settings defaults"""
    
    def test_default_model_is_isnet(self):
        """Default background-removal model should be isnet-general-use"""
        from app.core.config import settings
        assert settings.rembg_model == "isnet-general-use"
    
    def test_onnx_threads_is_int(self):
        """onnx_threads must be an int (0 = all cores)"""
        from app.core.config import settings
        assert isinstance(settings.onnx_threads, int)
        assert settings.onnx_threads >= 0
    
    def test_rembg_max_size_positive(self):
        """rembg_max_size must be a positive int"""
        from app.core.config import settings
        assert isinstance(settings.rembg_max_size, int)
        assert settings.rembg_max_size > 0
    
    def test_parse_bool_variants(self):
        """parse_bool validator handles common string forms"""
        from app.core.config import Settings
        
        assert Settings.parse_bool("true") is True
        assert Settings.parse_bool("1") is True
        assert Settings.parse_bool("yes") is True
        assert Settings.parse_bool("on") is True
        assert Settings.parse_bool("false") is False
        assert Settings.parse_bool("0") is False
        assert Settings.parse_bool("") is False


class TestAICapabilities:
    """Tests for AI service capability reporting"""
    
    @pytest.mark.asyncio
    async def test_get_capabilities_shape(self):
        """get_capabilities() must report the default model and expected keys"""
        from app.services.ai_service import ai_service
        
        caps = await ai_service.get_capabilities()
        assert caps["default_model"] == "isnet-general-use"
        assert "available_models" in caps
        assert "isnet-general-use" in caps["available_models"]
        assert isinstance(caps["loaded_models"], list)
    
    @pytest.mark.asyncio
    async def test_diagnose_shape(self):
        """diagnose() must expose rembg availability and default model"""
        from app.services.ai_service import ai_service
        
        info = await ai_service.diagnose()
        assert "rembg_available" in info
        assert info["default_model"] == "isnet-general-use"


class TestBackgroundRemovalIntegration:
    """Slow integration test: real rembg run end-to-end.
    Marked 'slow' because it loads the ONNX model. Run explicitly with:
      pytest -m slow
    This is the test that would have caught the sess_opts regression.
    """
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_remove_background_produces_rgba(self, tmp_path):
        """Removing background yields a valid RGBA PNG"""
        from PIL import Image
        from app.services.ai_service import ai_service
        
        # Build a tiny test image on the fly (no external fixtures needed)
        src = tmp_path / "src.png"
        Image.new("RGB", (64, 64), (120, 180, 90)).save(src, "PNG")
        out = tmp_path / "out.png"
        
        result_path = await ai_service.remove_background(
            str(src), str(out)
        )
        
        assert result_path
        with Image.open(result_path) as img:
            assert img.mode == "RGBA"
