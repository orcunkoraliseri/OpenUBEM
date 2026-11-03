from pathlib import Path

import pytest

from openubem import config

_IDF_22_1 = """VERSION,22.1;

BUILDING,
    Test Building,
    0,
    City,
    0.04,
    0.2,
    FullExterior,
    25,
    6;
"""

_IDF_23_1 = _IDF_22_1.replace("VERSION,22.1;", "VERSION,23.1;")

_IDF_NO_VERSION = _IDF_22_1.replace("VERSION,22.1;\n\n", "")


def test_read_idf_version_extracts_value(tmp_path: Path) -> None:
    idf_path = tmp_path / "sample.idf"
    idf_path.write_text(_IDF_22_1, encoding="utf-8")
    assert config.read_idf_version(idf_path) == "22.1"


def test_read_idf_version_returns_none_when_absent(tmp_path: Path) -> None:
    idf_path = tmp_path / "no_version.idf"
    idf_path.write_text(_IDF_NO_VERSION, encoding="utf-8")
    assert config.read_idf_version(idf_path) is None


def test_assert_prototype_idf_version_raises_on_mismatch(tmp_path: Path) -> None:
    idf_path = tmp_path / "old_prototype.idf"
    idf_path.write_text(_IDF_22_1, encoding="utf-8")
    with pytest.raises(config.PrototypeIDFVersionError) as exc_info:
        config.assert_prototype_idf_version(idf_path, expected_version="23.1")
    message = str(exc_info.value)
    assert "old_prototype.idf" in message
    assert "22.1" in message
    assert "23.1" in message


def test_assert_prototype_idf_version_passes_on_match(tmp_path: Path) -> None:
    idf_path = tmp_path / "current_prototype.idf"
    idf_path.write_text(_IDF_23_1, encoding="utf-8")
    config.assert_prototype_idf_version(idf_path, expected_version="23.1")


def test_assert_prototype_idf_version_raises_when_version_absent(tmp_path: Path) -> None:
    idf_path = tmp_path / "unversioned.idf"
    idf_path.write_text(_IDF_NO_VERSION, encoding="utf-8")
    with pytest.raises(config.PrototypeIDFVersionError) as exc_info:
        config.assert_prototype_idf_version(idf_path, expected_version="23.1")
    assert "unversioned.idf" in str(exc_info.value)


def test_assert_prototype_idf_version_uses_configured_default(tmp_path: Path) -> None:
    idf_path = tmp_path / "default_check.idf"
    idf_path.write_text(_IDF_22_1, encoding="utf-8")
    with pytest.raises(config.PrototypeIDFVersionError) as exc_info:
        config.assert_prototype_idf_version(idf_path)
    assert config.ENERGYPLUS_VERSION in str(exc_info.value)


def test_validate_prototype_library_versions_raises_naming_the_bad_file(tmp_path: Path) -> None:
    (tmp_path / "good.idf").write_text(_IDF_23_1, encoding="utf-8")
    bad_path = tmp_path / "stale.idf"
    bad_path.write_text(_IDF_22_1, encoding="utf-8")
    with pytest.raises(config.PrototypeIDFVersionError) as exc_info:
        config.validate_prototype_library_versions(directory=tmp_path, expected_version="23.1")
    assert "stale.idf" in str(exc_info.value)


def test_validate_prototype_library_versions_passes_when_all_current(tmp_path: Path) -> None:
    (tmp_path / "a.idf").write_text(_IDF_23_1, encoding="utf-8")
    (tmp_path / "b.idf").write_text(_IDF_23_1, encoding="utf-8")
    config.validate_prototype_library_versions(directory=tmp_path, expected_version="23.1")


def test_validate_prototype_library_versions_skips_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    config.validate_prototype_library_versions(directory=missing, expected_version="23.1")


@pytest.mark.skipif(
    not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present"
)
def test_real_baseline_idf_dir_passes_the_fence() -> None:
    config.validate_prototype_library_versions()
