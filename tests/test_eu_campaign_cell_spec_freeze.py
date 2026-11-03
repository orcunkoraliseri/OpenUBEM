import json
from pathlib import Path

import pytest

from openubem.validation.european_campaign import validate_campaign_cells
from scripts.freeze_eu_campaign_cell_spec import (
    DEFAULT_WEATHER_REGISTRY_PATH,
    CaveatRegisterError,
    build_spec,
    main,
)
import scripts.freeze_eu_campaign_cell_spec as freeze_mod


def _synthetic_caveats_registry(tmp_path: Path, *, n_entries: int = 16, schema_version: str = "eu-boundary-caveats/1.0", declared_n_caveats: int | None = None) -> Path:
    entries = [
        {
            "id": f"C-{index:02d}",
            "caveat": f"synthetic caveat {index}",
            "measured_extent": "synthetic extent",
            "must_not_conclude": "synthetic must-not-conclude",
        }
        for index in range(1, n_entries + 1)
    ]
    payload = {
        "schema_version": schema_version,
        "n_caveats": declared_n_caveats if declared_n_caveats is not None else n_entries,
        "caveats": entries,
    }
    path = tmp_path / "eu_boundary_caveats_synthetic.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _synthetic_pinned_registry(tmp_path: Path) -> Path:
    payload = {
        "schema_version": 1,
        "status": "FULLY_PINNED",
        "targets": [
            {
                "fold": "es",
                "city": "Madrid",
                "raw_era5_window": "2009-01-01/2010-12-31",
                "output_filename": "es_madrid_2009_2010.epw",
                "status": "RULED_PINNED",
                "weather_file": "openubem/data/weather/es_madrid_2009_2010.epw",
                "sha256": "a" * 64,
            },
            {
                "fold": "uk",
                "city": "London",
                "raw_era5_window": "2014-01-01/2015-12-31",
                "output_filename": "uk_london_2014_2015.epw",
                "status": "RULED_PINNED_EXCEPTION",
                "weather_file": "openubem/data/weather/uk_london_2014_2015.epw",
                "sha256": "b" * 64,
            },
            {
                "fold": "it",
                "city": "Bologna",
                "raw_era5_window": "2013-01-01/2014-12-31",
                "output_filename": "it_bologna_2013_2014.epw",
                "status": "RULED_PINNED",
                "weather_file": "openubem/data/weather/it_bologna_2013_2014.epw",
                "sha256": "c" * 64,
            },
        ],
    }
    path = tmp_path / "weather_registry_synthetic_pinned.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _synthetic_registry_with_statuses(tmp_path: Path, fold_statuses: dict[str, str]) -> Path:
    """A registry shaped like the real one (field names copied from the live file),
    with one status per fold chosen by the caller so the test does not depend on
    the live registry's mutable pinned/unpinned state."""
    city_by_fold = {"es": "Madrid", "uk": "London", "it": "Bologna"}
    window_by_fold = {
        "es": "2009-01-01/2010-12-31",
        "uk": "2014-01-01/2015-12-31",
        "it": "2013-01-01/2014-12-31",
    }
    targets = []
    for fold, status in fold_statuses.items():
        output_filename = f"{fold}_{city_by_fold[fold].lower()}.epw"
        pinned = status in ("RULED_PINNED", "RULED_PINNED_EXCEPTION")
        targets.append(
            {
                "fold": fold,
                "city": city_by_fold[fold],
                "raw_era5_window": window_by_fold[fold],
                "output_filename": output_filename,
                "status": status,
                "weather_file": f"openubem/data/weather/{output_filename}" if pinned else None,
                "sha256": ("f" * 64) if pinned else None,
            }
        )
    payload = {
        "schema_version": 1,
        "status": "PARTIALLY_PINNED",
        "targets": targets,
    }
    path = tmp_path / "weather_registry_synthetic_mixed.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_refuses_when_a_fold_is_not_pinned(tmp_path):
    registry_path = _synthetic_registry_with_statuses(
        tmp_path,
        {"es": "RULED_PINNED", "uk": "RULED_NOT_PINNED", "it": "RULED_NOT_PINNED"},
    )
    spec, refusal_lines = build_spec(
        weather_registry_path=registry_path, require_pinned=True
    )
    assert spec is None
    assert refusal_lines == [
        "NOT_PINNED uk RULED_NOT_PINNED",
        "NOT_PINNED it RULED_NOT_PINNED",
    ]


def test_allow_unpinned_writes_draft_with_510_cells(tmp_path, monkeypatch):
    draft_path = tmp_path / "eu_campaign_cell_spec_v1.0_DRAFT.json"
    monkeypatch.setattr(
        freeze_mod, "DEFAULT_OUTPUT_PATH", tmp_path / "eu_campaign_cell_spec_v1.0.json"
    )
    unpinned_registry = _synthetic_registry_with_statuses(
        tmp_path,
        {"es": "RULED_PINNED", "uk": "RULED_PINNED_EXCEPTION", "it": "RULED_NOT_PINNED"},
    )
    real_build_spec = freeze_mod.build_spec
    monkeypatch.setattr(
        freeze_mod,
        "build_spec",
        lambda **kwargs: real_build_spec(
            weather_registry_path=unpinned_registry, **kwargs
        ),
    )
    rc = main(["--allow-unpinned"])
    assert rc == 0
    assert draft_path.is_file()
    payload = json.loads(draft_path.read_text(encoding="utf-8"))
    assert payload["spec_status"] == "DRAFT_WEATHER_NOT_PINNED"
    assert payload["n_cells"] == 510
    assert len(payload["cells"]) == 510


def test_synthetic_pinned_registry_produces_510_valid_cells(tmp_path):
    synthetic_registry = _synthetic_pinned_registry(tmp_path)
    spec, refusal_lines = build_spec(
        weather_registry_path=synthetic_registry, require_pinned=True
    )
    assert refusal_lines == []
    assert spec is not None
    assert spec["spec_status"] == "FROZEN_PINNED"

    cells = spec["cells"]
    assert len(cells) == 510
    assert len({cell["cell_id"] for cell in cells}) == 510

    for cell in cells:
        assert cell["epw_path"]
        assert cell["weather_id"]
        assert cell["weather_sha256"]
        assert cell["weather_status"] in ("RULED_PINNED", "RULED_PINNED_EXCEPTION")

    validate_campaign_cells(cells)


def test_frozen_spec_top_level_fields_present():
    synthetic = None
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        registry_path = _synthetic_pinned_registry(tmp_path)
        spec, refusal_lines = build_spec(weather_registry_path=registry_path, require_pinned=True)
        assert refusal_lines == []
        assert spec["cell_id_note"].startswith("cell_id is an index key")
        register = json.loads((freeze_mod.DEFAULT_CAVEATS_REGISTRY_PATH if hasattr(freeze_mod, "DEFAULT_CAVEATS_REGISTRY_PATH")
                              else Path("openubem/data/campaign/eu_boundary_caveats_v1.0.json")).read_text(encoding="utf-8"))
        assert register["n_caveats"] == len(register["caveats"])
        assert len(spec["caveats"]) == register["n_caveats"]
        assert set(spec["folds"]) == {"es", "uk", "it"}
        assert "openubem_git_commit" in spec
        assert isinstance(spec["git_dirty"], bool)


def test_caveats_register_missing_hard_fails(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"
    with pytest.raises(CaveatRegisterError):
        build_spec(caveats_registry_path=missing_path, require_pinned=False)


def test_caveats_register_wrong_schema_version_hard_fails(tmp_path):
    bad_registry = _synthetic_caveats_registry(tmp_path, schema_version="eu-boundary-caveats/0.9")
    with pytest.raises(CaveatRegisterError):
        build_spec(caveats_registry_path=bad_registry, require_pinned=False)


def test_caveats_register_short_hard_fails(tmp_path):
    short_registry = _synthetic_caveats_registry(tmp_path, n_entries=15)
    with pytest.raises(CaveatRegisterError):
        build_spec(caveats_registry_path=short_registry, require_pinned=False)


def test_caveats_register_happy_path_embeds_every_entry_and_its_source(tmp_path):
    synthetic_weather = _synthetic_pinned_registry(tmp_path)
    good_registry = _synthetic_caveats_registry(tmp_path)
    spec, refusal_lines = build_spec(
        weather_registry_path=synthetic_weather,
        caveats_registry_path=good_registry,
        require_pinned=True,
    )
    assert refusal_lines == []
    assert spec is not None
    register = json.loads(good_registry.read_text(encoding="utf-8"))
    assert len(spec["caveats"]) == register["n_caveats"] == len(register["caveats"])
    assert spec["caveats_source"]["path"] == freeze_mod._repo_relative_posix(good_registry)
    assert spec["caveats_source"]["schema_version"] == "eu-boundary-caveats/1.0"


def test_serialised_spec_carries_no_absolute_or_windows_path(tmp_path):
    synthetic_weather = _synthetic_pinned_registry(tmp_path)
    spec, refusal_lines = build_spec(
        weather_registry_path=synthetic_weather, require_pinned=True
    )
    assert refusal_lines == []
    assert spec is not None

    serialised = json.dumps(spec, sort_keys=True, ensure_ascii=True)

    # Evaluate the membership tests in plain code and assert only on the small
    # result. Asserting `x not in serialised` directly makes pytest's assertion
    # rewriter carry this ~340 KB string through every comparison, which turns a
    # sub-millisecond check into minutes.
    # A drive letter only means an absolute path when a separator follows it.
    # Matching a bare "<letter>:" also hits legitimate prose such as the caveat
    # register's "EPSG:32631", so the separator is part of the test, not an
    # optimisation.
    drive_tokens = [
        f"{letter}:{separator}"
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for separator in ("/", "\\")
    ]
    offenders = [
        token for token in ["\\", "Users"] + drive_tokens if token in serialised
    ]
    assert offenders == []

    assert spec["caveats_source"]["path"] == "openubem/data/campaign/eu_boundary_caveats_v1.0.json"
