"""
Regression tests for CWE-22 path traversal in output path generation.

Before this fix, `output_format` came straight from the request body and was
interpolated into the output filename, so a value like
"png/../../../../etc/cron.d/x" could place a file anywhere the process could
write. Both the format whitelist and the resolved-path guard must stay in place.
"""

import pytest

from app.services.file_service import file_service


TRAVERSAL_FORMATS = [
    "png/../../../../etc/cron.d/x",
    "../../../../etc/passwd",
    "png/../../..",
    "/etc/passwd",
    "png\x00.sh",
    "exe",
    "",
]

VALID_FORMATS = ["webp", "jpg", "jpeg", "png", "avif"]


@pytest.mark.parametrize("bad_format", TRAVERSAL_FORMATS)
def test_get_output_path_rejects_unsafe_format(bad_format):
    with pytest.raises(ValueError):
        file_service.get_output_path("photo.jpg", bad_format, user_id=1)


@pytest.mark.parametrize("good_format", VALID_FORMATS)
def test_get_output_path_accepts_whitelisted_format(good_format):
    result = file_service.get_output_path("photo.jpg", good_format, user_id=1)
    assert result.endswith(f".{good_format}")


def test_get_output_path_stays_inside_processed_dir():
    root = str(file_service.processed_dir.resolve())
    result = file_service.get_output_path("photo.jpg", "webp", user_id=1)
    assert result.startswith(root)


@pytest.mark.parametrize(
    "filename",
    ["../../etc/passwd", "foo/../bar.png", "../../../evil.jpg"],
)
def test_get_output_path_strips_path_components_from_filename(filename):
    root = str(file_service.processed_dir.resolve())
    result = file_service.get_output_path(filename, "png", user_id=1)
    assert result.startswith(root)
    assert ".." not in result


@pytest.mark.asyncio
async def test_get_processed_path_falls_back_to_png_for_unsafe_extension():
    root = str(file_service.processed_dir.resolve())
    result = await file_service.get_processed_path("evil.sh", user_id=1)
    assert result.startswith(root)
    assert result.endswith(".png")
