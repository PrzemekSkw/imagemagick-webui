"""ImageMagick binary detection: IM6 ships 'convert', IM7 ships 'magick'."""

import shutil
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.services.imagemagick import ImageMagickService, imagemagick_service


def _which_only(*available):
    return lambda name: f"/usr/bin/{name}" if name in available else None


def test_prefers_magick_on_im7():
    svc = ImageMagickService()
    with patch("app.services.imagemagick.shutil.which", _which_only("magick", "convert")):
        assert svc.resolve_magick_cmd() == "magick"


def test_falls_back_to_convert_on_im6():
    svc = ImageMagickService()
    with patch("app.services.imagemagick.shutil.which", _which_only("convert")):
        assert svc.resolve_magick_cmd() == "convert"


@pytest.mark.asyncio
async def test_readiness_uses_detected_binary():
    from app.api import health

    with patch("app.services.imagemagick.shutil.which", _which_only("convert")), \
         patch.object(imagemagick_service, "_magick_cmd", None), \
         patch("redis.from_url"), \
         patch("app.api.health.subprocess.run", return_value=MagicMock(returncode=0)) as run:
        result = await health.readiness_check()

    assert result["checks"]["imagemagick"] is True
    assert run.call_args[0][0][0] == "convert"


@pytest.mark.skipif(
    not (shutil.which("magick") or shutil.which("convert")),
    reason="ImageMagick not installed",
)
def test_detected_binary_actually_runs():
    cmd = ImageMagickService().resolve_magick_cmd()
    assert subprocess.run([cmd, "-version"], capture_output=True).returncode == 0
