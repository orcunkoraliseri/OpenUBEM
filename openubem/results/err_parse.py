"""Whitespace-tolerant matcher for EnergyPlus ``.err`` file markers.

Real EnergyPlus ``.err`` output uses **two spaces** inside the ``**`` delimiters,
e.g. ``**  Severe  **`` and ``**  Fatal  **`` (not ``** Severe **`` / ``** Fatal **``,
one space). A one-space literal match against real output never matches, so any
downstream code that greps for ``"** Severe **"`` silently produces an always-empty
result. This is documented as OPEN-45 in
`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_three-new-items-2026-08-12.md` (T01):
this is the third instance of the same one-space bug across this codebase, hence a
single shared, tested helper instead of another point-patch.

These patterns tolerate any run of whitespace (one or more spaces/tabs) inside the
``** ... **`` delimiters, and tolerate leading indentation on the line, so they match
both the one-space and two-space forms.
"""

from __future__ import annotations

import re

from openubem._rust_bridge import load_rust_module
from openubem.rust_shadow import dispatch_with_rust

SEVERE_RE = re.compile(r"^\s*\*\*\s+Severe\s+\*\*", re.MULTILINE)
FATAL_RE = re.compile(r"^\s*\*\*\s+Fatal\s+\*\*", re.MULTILINE)
WARNING_RE = re.compile(r"^\s*\*\*\s+Warning\s+\*\*", re.MULTILINE)


def iter_severe(text: str) -> list[str]:
    """Return every stripped line in ``text`` that carries a ``** Severe **`` marker."""
    rust = load_rust_module()
    rust_fn = (
        (lambda: rust.results_err_iter_severe(text))
        if rust is not None and hasattr(rust, "results_err_iter_severe")
        else None
    )
    return dispatch_with_rust(
        "openubem.results.err_parse.iter_severe",
        lambda: [line.strip() for line in text.splitlines() if SEVERE_RE.match(line)],
        rust_fn,
        bucket="B1",
    )


def first_severe(text: str) -> str:
    """Return the first ``** Severe **`` line in ``text``, stripped, or ``""`` if none."""
    rust = load_rust_module()
    rust_fn = (
        (lambda: rust.results_err_first_severe(text))
        if rust is not None and hasattr(rust, "results_err_first_severe")
        else None
    )

    def _py() -> str:
        lines = [line.strip() for line in text.splitlines() if SEVERE_RE.match(line)]
        return lines[0] if lines else ""

    return dispatch_with_rust(
        "openubem.results.err_parse.first_severe",
        _py,
        rust_fn,
        bucket="B1",
    )


def count_severe(text: str) -> int:
    """Return the number of ``** Severe **`` marker lines in ``text``."""
    rust = load_rust_module()
    rust_fn = (
        (lambda: int(rust.results_err_count_severe(text)))
        if rust is not None and hasattr(rust, "results_err_count_severe")
        else None
    )
    return dispatch_with_rust(
        "openubem.results.err_parse.count_severe",
        lambda: len([line.strip() for line in text.splitlines() if SEVERE_RE.match(line)]),
        rust_fn,
        bucket="B1",
    )


def has_fatal(text: str) -> bool:
    """Return True if ``text`` contains a ``** Fatal **`` marker line.

    Note: per the plan's hard rule 9, a column named ``has_fatal`` elsewhere in this
    project is measured wrong (OPEN-29) and must not be used. This function is the
    correct, whitespace-tolerant replacement for that concept.
    """
    rust = load_rust_module()
    rust_fn = (
        (lambda: bool(rust.results_err_has_fatal(text)))
        if rust is not None and hasattr(rust, "results_err_has_fatal")
        else None
    )
    return dispatch_with_rust(
        "openubem.results.err_parse.has_fatal",
        lambda: bool(FATAL_RE.search(text)),
        rust_fn,
        bucket="B1",
    )
