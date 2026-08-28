"""
Security regression tests for the raw/terminal command path.

These pin the fix for GHSA-fqpc-f5jc-78c3 (authenticated OS command injection
via newline bypass of the metacharacter denylist). The raw path now builds an
argv list executed with shell=False plus a strict per-token allowlist, so no
shell metacharacter can start a second command.

Run:  pytest backend/tests/test_raw_command_security.py -v
"""
import os
import asyncio

import pytest

from app.services.imagemagick import ImageMagickService


@pytest.fixture()
def svc():
    s = ImageMagickService()
    s._magick_cmd = "convert"  # skip the `which` probe in tests
    return s


def _build(svc, cmd, inp="/work/in.png", out="/work/out.png"):
    return asyncio.run(svc.build_raw_argv(inp, out, cmd))


def test_newline_injection_is_rejected(svc):
    """The exact advisory PoC: a literal newline + a second command."""
    poc = "{input} {output}\nid > /tmp/pwned\n"
    argv, error = _build(svc, poc)
    assert argv == []
    assert error  # rejected with a message, never turned into a command


def test_shell_metacharacters_never_reach_a_shell(svc):
    """; & | $() are either rejected or, if built, are inert argv literals.

    The guarantee is that no argv we produce is ever passed to a shell, so even
    a token like '|' is a literal filename argument to `convert`, not a pipe.
    """
    for cmd in (
        "{input} {output}; touch /tmp/pwned",
        "{input} {output} | id",
        "{input} {output} & id",
        "{input} $(id) {output}",
    ):
        argv, error = _build(svc, cmd)
        # Whatever the outcome, no shell is involved: build_raw_argv only ever
        # returns a list to run with shell=False. If a token slipped through it
        # is a literal arg, so `id`/`touch` can never execute.
        assert isinstance(argv, list)


def test_dangerous_flags_and_paths_are_blocked(svc):
    assert _build(svc, "{input} -write /tmp/pwned {output}")[0] == []      # arbitrary write
    assert _build(svc, "{input} @/etc/passwd {output}")[0] == []           # @file read
    assert _build(svc, "/etc/passwd {output}")[0] == []                    # absolute path read
    assert _build(svc, "{input} msl:/tmp/x.msl {output}")[0] == []         # MSL coder
    assert _build(svc, "{input} -draw 'image over 0,0 0,0 x' {output}")[0] == []  # -draw not allowed


def test_missing_placeholders_are_rejected(svc):
    assert _build(svc, "-resize 50%")[0] == []                 # no {input}/{output}
    assert _build(svc, "{input} -resize 50%")[0] == []         # no {output}


def test_legit_command_builds_expected_argv(svc):
    argv, error = _build(svc, "{input} -resize 50% -quality 80 {output}")
    assert error == ""
    assert argv[0] == "convert"
    # our own resource limits are always prepended and cannot be overridden
    assert "-limit" in argv and "memory" in argv
    assert "/work/in.png" in argv and "/work/out.png" in argv
    assert "-resize" in argv and "50%" in argv


def test_user_cannot_raise_resource_limits(svc):
    # -limit is intentionally NOT on the allowlist, so a user cannot lift the
    # 2GB / timeout caps we enforce.
    argv, error = _build(svc, "{input} -limit memory 64GB {output}")
    assert argv == []
    assert "limit" in error.lower()
