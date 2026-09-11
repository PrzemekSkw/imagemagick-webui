"""
Security regression tests for the normal (non-raw) operations path.

These pin the fix for an authenticated OS command injection in build_command():
the `transparent` operation interpolated a user-supplied colour into a shell
string that was then run with shell=True, so a colour like `'; id; echo '`
escaped the quoting and started a second command.

The operations path now builds an argv list executed with shell=False, and
colour values are narrowed to a name / hex / rgb() form before use. These tests
cover both halves of that fix.

Run:  pytest backend/tests/test_operation_argv_security.py -v
"""
import asyncio

import pytest

from app.services.imagemagick import ImageMagickService


@pytest.fixture()
def svc():
    s = ImageMagickService()
    s._magick_cmd = "convert"  # skip the `which` probe in tests
    return s


def _build(svc, operations, inp="/app/uploads/in.png", out="/app/processed/out.png"):
    return asyncio.run(svc.build_argv(inp, out, operations))


# --- the injection itself -------------------------------------------------

INJECTION_PAYLOADS = [
    "'; id; echo '",       # the original PoC: break out of the single quotes
    '"; id; echo "',
    "$(id)",
    "`id`",
    "white; rm -rf /",
    "|touch /tmp/pwned",
    "white\nid",           # newline, the trick that defeated the raw denylist
]


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_transparent_colour_cannot_inject(svc, payload):
    """A hostile colour must never survive into the argument list."""
    argv = _build(svc, [{"operation": "transparent", "params": {"color": payload}}])

    value = argv[argv.index("-transparent") + 1]
    assert value in svc.NAMED_COLORS, f"unsafe colour reached argv: {value!r}"

    # And nothing anywhere in argv carries the payload.
    assert not any(payload in token for token in argv)


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_watermark_text_stays_a_single_token(svc, payload):
    """
    Watermark text is attacker-controlled but legitimately free-form. It is not
    sanitised, it is *contained*: whatever it holds must land in exactly one
    argv entry, where ImageMagick reads it as text rather than as syntax.
    """
    argv = _build(svc, [{"operation": "watermark", "params": {"text": payload}}])

    positions = [i for i, t in enumerate(argv) if t == "-annotate"]
    assert positions, "watermark produced no -annotate"
    for i in positions:
        assert argv[i + 2] == payload  # one token, verbatim, never split


def test_no_argv_token_is_a_shell_fragment(svc):
    """Broad sweep: no operation may emit a token holding two arguments."""
    argv = _build(svc, [
        {"operation": "resize", "params": {"width": 800, "height": 600}},
        {"operation": "crop", "params": {"width": 10, "height": 10, "x": 1, "y": 2}},
        {"operation": "trim", "params": {}},
        {"operation": "enhance", "params": {}},
        {"operation": "watermark", "params": {"text": "hello"}},
    ])
    # "-trim +repage" as one string would mean we regressed to shell-joining.
    for token in argv:
        assert not (token.startswith("-") and " " in token), f"fused token: {token!r}"


# --- the colour validator -------------------------------------------------

@pytest.mark.parametrize("colour", [
    "white", "black", "none", "transparent",
    "#fff", "#ffff", "#ff00aa", "#ff00aa80",
    "rgb(1,2,3)", "rgba(0, 0, 0, 0.5)", "rgba(255,255,255,1)",
])
def test_legitimate_colours_pass_through(svc, colour):
    """The guard must not break normal use."""
    assert ImageMagickService._safe_color(colour) == colour.strip().lower()


@pytest.mark.parametrize("colour", [
    "xc:/etc/passwd", "gradient:red-blue", "../../etc/passwd",
    "rgb(1,2,3);id", "#gggggg", "label:@/etc/passwd", "",
])
def test_hostile_colours_fall_back(colour):
    """Anything outside the three accepted shapes degrades to the default."""
    assert ImageMagickService._safe_color(colour) == "white"


# --- resource limits ------------------------------------------------------

def test_resource_limits_are_always_prepended(svc):
    """Operations cannot displace the memory/time caps."""
    argv = _build(svc, [{"operation": "resize", "params": {"percent": 50}}])
    assert argv[1:4] == ["-limit", "memory", str(svc.memory_limit)]
    assert argv[4:7] == ["-limit", "time", str(svc.timeout)]


def test_unknown_operations_are_dropped(svc):
    """An operation outside the allowlist contributes nothing to argv."""
    argv = _build(svc, [{"operation": "evil", "params": {"anything": "; id"}}])
    assert "; id" not in argv
    assert argv == [
        "convert",
        "-limit", "memory", str(svc.memory_limit),
        "-limit", "time", str(svc.timeout),
        "/app/uploads/in.png",
        "-auto-orient",
        "/app/processed/out.png",
    ]
