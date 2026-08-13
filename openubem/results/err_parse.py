"""Whitespace-tolerant matcher for EnergyPlus ``.err`` file markers.

Real EnergyPlus ``.err`` output uses **two spaces** inside the ``**`` delimiters,
e.g. ``**  Severe  **`` and ``**  Fatal  **`` (not ``** Severe **`` / ``** Fatal **``,
one space). A one-space literal match against real output never matches, so any
downstream code that greps for ``"** Severe **"`` silently produces an always-empty
result. This is documented as OPEN-45 in
`docs/docs_ACTIVE/openings/implemenation/PLAN_three-new-items-2026-08-12.md` (T01):
this is the third instance of the same one-space bug across this codebase, hence a
single shared, tested helper instead of another point-patch.

These patterns tolerate any run of whitespace (one or more spaces/tabs) inside the
``** ... **`` delimiters, and tolerate leading indentation on the line, so they match
both the one-space and two-space forms.
"""

from __future__ import annotations

import re

SEVERE_RE = re.compile(r"^\s*\*\*\s+Severe\s+\*\*", re.MULTILINE)
FATAL_RE = re.compile(r"^\s*\*\*\s+Fatal\s+\*\*", re.MULTILINE)
WARNING_RE = re.compile(r"^\s*\*\*\s+Warning\s+\*\*", re.MULTILINE)


def iter_severe(text: str) -> list[str]:
    """Return every stripped line in ``text`` that carries a ``** Severe **`` marker."""
    return [line.strip() for line in text.splitlines() if SEVERE_RE.match(line)]


def first_severe(text: str) -> str:
    """Return the first ``** Severe **`` line in ``text``, stripped, or ``""`` if none."""
    lines = iter_severe(text)
    return lines[0] if lines else ""


def count_severe(text: str) -> int:
    """Return the number of ``** Severe **`` marker lines in ``text``."""
    return len(iter_severe(text))


def has_fatal(text: str) -> bool:
    """Return True if ``text`` contains a ``** Fatal **`` marker line.

    Note: per the plan's hard rule 9, a column named ``has_fatal`` elsewhere in this
    project is measured wrong (OPEN-29) and must not be used. This function is the
    correct, whitespace-tolerant replacement for that concept.
    """
    return bool(FATAL_RE.search(text))
