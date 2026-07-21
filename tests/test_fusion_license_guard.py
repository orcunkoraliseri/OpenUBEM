"""T12.5 -- license/bundle guard for `openubem/data/fixtures/fusion/`.

Pure filesystem/manifest test (no network) -- the test IS the guard (plan
§6 T12.5). Asserts the repo vendors no restricted external building/raster
dataset: every bundled fixture is (a) listed in `LICENSES.md`, (b) under the
per-file size cap, and (c) under an allowlisted license. A negative case
proves the checker actually bites on a barred license / oversized entry.
"""
import re
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "openubem" / "data" / "fixtures" / "fusion"
MANIFEST_PATH = FIXTURES_DIR / "LICENSES.md"

SIZE_CAP_BYTES = 5 * 1024 * 1024  # a slice, never a city-wide raster (M07 §2)

ALLOWED_LICENSES = {
    "ODbL-1.0", "CC-BY-4.0", "CDLA-Permissive-2.0", "public-domain",
}
BARRED_LICENSES = {
    "CC-BY-NC-4.0", "proprietary", "restrictive-ShareAlike", "TKGM-restricted",
}

# Files under this dir that are NOT external-dataset fixtures (scope = new
# external-building/raster datasets only, §5F) -- excluded from the guard.
_NON_DATASET_FILES = {"LICENSES.md", "__init__.py"}

_ROW_RE = re.compile(
    r"^\|\s*(?P<file>[^|]+?)\s*\|\s*(?P<source>[^|]+?)\s*\|\s*(?P<license>[^|]+?)\s*\|\s*(?P<size>\d+)\s*\|\s*$"
)


def parse_manifest(text: str) -> "list[dict]":
    rows = []
    for line in text.splitlines():
        m = _ROW_RE.match(line.strip())
        if m is None:
            continue
        if m.group("file") == "file":  # header row
            continue
        rows.append({
            "file": m.group("file"),
            "source": m.group("source"),
            "license": m.group("license"),
            "size": int(m.group("size")),
        })
    return rows


def check_manifest(rows: "list[dict]", *, size_cap: int = SIZE_CAP_BYTES,
                    allowed: "set[str]" = ALLOWED_LICENSES) -> "list[str]":
    """Returns a list of violation messages (empty = guard passes)."""
    violations = []
    for row in rows:
        if row["license"] not in allowed:
            violations.append(f"{row['file']}: license {row['license']!r} not allowlisted")
        if row["size"] > size_cap:
            violations.append(f"{row['file']}: size {row['size']} exceeds cap {size_cap}")
    return violations


class TestManifestExistsAndParses:
    def test_manifest_file_exists(self):
        assert MANIFEST_PATH.exists(), f"missing fixture manifest: {MANIFEST_PATH}"

    def test_manifest_has_at_least_one_row(self):
        rows = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert len(rows) > 0


class TestFilesystemMatchesManifest:
    def test_every_bundled_dataset_file_is_in_the_manifest(self):
        rows = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest_files = {r["file"] for r in rows}
        on_disk = {
            p.name for p in FIXTURES_DIR.iterdir()
            if p.is_file() and p.name not in _NON_DATASET_FILES
        }
        missing_from_manifest = on_disk - manifest_files
        assert not missing_from_manifest, (
            f"fixture file(s) not declared in LICENSES.md: {missing_from_manifest}"
        )

    def test_every_manifest_entry_exists_on_disk(self):
        rows = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
        for row in rows:
            assert (FIXTURES_DIR / row["file"]).exists(), f"manifest lists missing file {row['file']}"

    def test_manifest_declared_sizes_match_actual_file_sizes(self):
        rows = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
        for row in rows:
            actual = (FIXTURES_DIR / row["file"]).stat().st_size
            assert actual == row["size"], (
                f"{row['file']}: manifest size {row['size']} != actual {actual}"
            )


class TestLicenseAndSizeGuardPasses:
    def test_real_manifest_passes_the_guard(self):
        rows = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
        violations = check_manifest(rows)
        assert violations == [], f"license/bundle guard violations: {violations}"

    def test_existing_legit_data_reference_tables_are_out_of_scope(self):
        # §5F: openubem/data/{construction,schedules,loads,...} are OpenUBEM's
        # own reference tables, not external building datasets -- the guard
        # never scans that directory tree, only openubem/data/fixtures/fusion/.
        legit_dir = FIXTURES_DIR.parent.parent / "construction"
        assert legit_dir.exists()
        rows = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert not any("construction" in r["file"] for r in rows)


class TestGuardBites:
    def test_barred_license_fails(self):
        rows = [{"file": "restricted_dataset.gpkg", "source": "fake", "license": "CC-BY-NC-4.0", "size": 100}]
        violations = check_manifest(rows)
        assert len(violations) == 1
        assert "not allowlisted" in violations[0]

    def test_oversized_file_fails(self):
        rows = [{"file": "huge_raster.tif", "source": "fake", "license": "public-domain", "size": SIZE_CAP_BYTES + 1}]
        violations = check_manifest(rows)
        assert len(violations) == 1
        assert "exceeds cap" in violations[0]

    def test_proprietary_and_restricted_classes_are_barred(self):
        for barred in BARRED_LICENSES:
            rows = [{"file": "x", "source": "fake", "license": barred, "size": 1}]
            assert check_manifest(rows), f"{barred!r} should be barred but guard passed"
