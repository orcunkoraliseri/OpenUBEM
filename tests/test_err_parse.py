"""Unit tests for openubem.results.err_parse (OPEN-45, T01).

Real EnergyPlus .err output uses TWO spaces inside the ** ... ** delimiters
(e.g. "**  Severe  **"), not one. The fixtures below use the real two-space
form so a regression back to a one-space-only matcher is caught.
"""
from __future__ import annotations

from openubem.results.err_parse import (
    FATAL_RE,
    SEVERE_RE,
    WARNING_RE,
    count_severe,
    first_severe,
    has_fatal,
    iter_severe,
)

TWO_SPACE_ERR = """\
Program Version,EnergyPlus, Version 23.1.0-87ed9199d4, YMD=2026.08.12 00:00
   ************* Beginning Zone Sizing Calculations
**  Severe  ** GetSurfaceData: Very small surface area entered, less than 1E-05 m2, for Surface=WALL-01
**   ~~~   ** Check surface geometry.
**  Fatal  ** Program terminated for reason listed above
**  Warning  ** Weather file location differs from IDF site location
   ===== EnergyPlus Errors File =====
    1 Warning;    1 Severe Errors.
"""

ONE_SPACE_ERR = """\
** Severe ** GetSurfaceData: Very small surface area entered, less than 1E-05 m2, for Surface=WALL-01
** Fatal ** Program terminated for reason listed above
** Warning ** Weather file location differs from IDF site location
"""

NO_ERROR_ERR = """\
Program Version,EnergyPlus, Version 23.1.0-87ed9199d4, YMD=2026.08.12 00:00
   ************* Beginning Zone Sizing Calculations
   ===== EnergyPlus Errors File =====
    0 Warning;    0 Severe Errors.
"""


class TestTwoSpaceForm:
    """The real EnergyPlus form must match — this is the whole point of OPEN-45."""

    def test_severe_re_matches(self):
        assert SEVERE_RE.search(TWO_SPACE_ERR) is not None

    def test_fatal_re_matches(self):
        assert FATAL_RE.search(TWO_SPACE_ERR) is not None

    def test_warning_re_matches(self):
        assert WARNING_RE.search(TWO_SPACE_ERR) is not None

    def test_iter_severe_nonempty(self):
        assert iter_severe(TWO_SPACE_ERR) == [
            "**  Severe  ** GetSurfaceData: Very small surface area entered, less than 1E-05 m2, for Surface=WALL-01"
        ]

    def test_first_severe_nonempty(self):
        result = first_severe(TWO_SPACE_ERR)
        assert result != ""
        assert "GetSurfaceData" in result

    def test_count_severe(self):
        assert count_severe(TWO_SPACE_ERR) == 1

    def test_has_fatal_true(self):
        assert has_fatal(TWO_SPACE_ERR) is True


class TestOneSpaceForm:
    """The matcher must also tolerate the (incorrect, but historically written) one-space form."""

    def test_severe_re_matches(self):
        assert SEVERE_RE.search(ONE_SPACE_ERR) is not None

    def test_fatal_re_matches(self):
        assert FATAL_RE.search(ONE_SPACE_ERR) is not None

    def test_first_severe_nonempty(self):
        assert first_severe(ONE_SPACE_ERR) != ""

    def test_has_fatal_true(self):
        assert has_fatal(ONE_SPACE_ERR) is True


class TestNoError:
    def test_first_severe_empty(self):
        assert first_severe(NO_ERROR_ERR) == ""

    def test_count_severe_zero(self):
        assert count_severe(NO_ERROR_ERR) == 0

    def test_has_fatal_false(self):
        assert has_fatal(NO_ERROR_ERR) is False


class TestNonVacuityControl:
    """Plan hard rule 7: a scan that finds nothing must prove the scanner works.

    This test is the executable proof for T01's non-vacuity control: it shows the
    OLD one-space substring check (as it existed at
    scripts/validation/v12_cell_pipeline.py:625 before this task) FAILS to find the
    severe line in the real two-space fixture, while the NEW matcher in this module
    PASSES against the same fixture.
    """

    def test_old_one_space_substring_check_fails_on_real_fixture(self):
        old_style_severes = [
            l.strip() for l in TWO_SPACE_ERR.splitlines() if "** Severe **" in l
        ]
        old_style_error_summary = old_style_severes[0] if old_style_severes else ""
        assert old_style_error_summary == "", (
            "the old one-space literal unexpectedly matched the two-space fixture; "
            "the non-vacuity control requires it to fail here"
        )

    def test_new_matcher_passes_on_same_fixture(self):
        new_error_summary = first_severe(TWO_SPACE_ERR)
        assert new_error_summary != ""
        assert "GetSurfaceData" in new_error_summary
