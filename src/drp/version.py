"""
Version numbers, and the one question we ask of them: is this newer?

Kept apart from the updater so that config.PLUGIN_VERSION and a release
tag are read by the same rule. They are written differently on
purpose - the constant never carries a "v", a tag almost always does -
and a comparison that forgot to strip it would decide that every
release is older than what is installed and never update at all.

Deliberately not a full implementation of PEP 440: only the shapes this
project actually publishes are understood, and anything else is treated
as "not an update" rather than guessed at. Silently installing something
whose version we cannot read is the worse mistake.
"""

import re

# Release tags are conventionally written with a leading "v", and this
# repository already carries both "V0.1.0" and "v1.0.0" - so the prefix
# is matched regardless of its case, and is never required.
_TAG_PREFIX = re.compile(r"^[vV]\s*")


def from_tag(tag: str) -> str:
    """The version number inside a release tag: "v1.2.3" -> "1.2.3"."""
    return _TAG_PREFIX.sub("", str(tag).strip(), count=1)


def parse(text: str):
    """Split a version into a comparable form, or None if it isn't one.

    Returns (numbers, is_prerelease), where `numbers` is a tuple of
    ints. A hyphen starts the prerelease part ("1.2.0-beta.1"), which
    sorts *below* the plain 1.2.0 rather than above it.
    """
    core, _, prerelease = from_tag(text).partition("-")

    numbers = []
    for piece in core.split("."):
        if not piece.isdigit():
            return None
        numbers.append(int(piece))

    if not numbers:
        return None

    return tuple(numbers), bool(prerelease)


def is_newer(candidate: str, current: str) -> bool:
    """True if `candidate` is a later version than `current`.

    Anything unparseable on either side answers False: an update we
    cannot compare is not an update.
    """
    left = parse(candidate)
    right = parse(current)

    if left is None or right is None:
        return False

    left_numbers, left_prerelease = left
    right_numbers, right_prerelease = right

    # 1.2 and 1.2.0 name the same version, so the shorter side is padded
    # with zeros before comparing instead of being allowed to sort lower.
    width = max(len(left_numbers), len(right_numbers))
    left_numbers += (0,) * (width - len(left_numbers))
    right_numbers += (0,) * (width - len(right_numbers))

    if left_numbers != right_numbers:
        return left_numbers > right_numbers

    # Same numbers: a prerelease is the earlier of the two.
    return not left_prerelease and right_prerelease
