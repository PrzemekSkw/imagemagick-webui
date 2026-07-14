"""
Tests for the centralised path validation in app.core.paths.

Two things this guards that the previous per-module copies did not:
  - the prefix comparison now requires a separator, so a sibling directory
    whose name merely starts with an allowed one ("/data/uploads_evil" against
    "/data/uploads") is rejected;
  - /tmp at large is no longer whitelisted, only settings.temp_dir.
"""

import os

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.paths import validate_path


def test_rejects_empty_path():
    with pytest.raises(HTTPException) as exc:
        validate_path("")
    assert exc.value.status_code == 400


def test_accepts_path_inside_upload_dir():
    target = os.path.join(settings.upload_dir, "1", "photo.jpg")
    assert validate_path(target) == os.path.realpath(target)


def test_accepts_path_inside_processed_dir():
    target = os.path.join(settings.processed_dir, "1", "photo.webp")
    assert validate_path(target) == os.path.realpath(target)


def test_accepts_path_inside_temp_dir():
    target = os.path.join(settings.temp_dir, "download_abc.png")
    assert validate_path(target) == os.path.realpath(target)


@pytest.mark.parametrize(
    "hostile",
    [
        "/etc/passwd",
        "/root/.ssh/id_rsa",
        "../../etc/shadow",
    ],
)
def test_rejects_paths_outside_allowed_dirs(hostile):
    with pytest.raises(HTTPException) as exc:
        validate_path(hostile)
    assert exc.value.status_code == 403


def test_rejects_traversal_out_of_upload_dir():
    escape = os.path.join(settings.upload_dir, "..", "..", "etc", "passwd")
    with pytest.raises(HTTPException) as exc:
        validate_path(escape)
    assert exc.value.status_code == 403


def test_rejects_sibling_directory_sharing_a_prefix():
    """"/data/uploads_evil" must not pass a check against "/data/uploads"."""
    sibling = os.path.realpath(settings.upload_dir) + "_evil/file.jpg"
    with pytest.raises(HTTPException) as exc:
        validate_path(sibling)
    assert exc.value.status_code == 403


def test_bare_tmp_is_no_longer_allowed():
    """Only settings.temp_dir is whitelisted, not the whole of /tmp."""
    if os.path.realpath(settings.temp_dir) == "/tmp":
        pytest.skip("temp_dir is /tmp in this configuration")
    with pytest.raises(HTTPException) as exc:
        validate_path("/tmp/somebody_elses_file.png")
    assert exc.value.status_code == 403
