"""EU-08 per-cell entry point: signature, provenance refusals, and manifest completeness."""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest

import openubem.campaign.eu_cell_runner as runner
from openubem.campaign.eu_cell_runner import (
    MANIFEST_FIELDS,
    CampaignCellError,
    _energyplus_exe,
    load_archetype_record,
    lookup_presence,
    resolve_lift_authority,
    run_campaign_cell,
    verify_spec,
    verify_weather,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "openubem/data/campaign/eu_campaign_cell_spec_v1.1.json"
SPEC_SHA256 = "16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6"
GSS_ROOT = Path("C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ")
BINDING_PATH = GSS_ROOT / "Step10_docs/outputs_step10/eu_cell_presence_binding_v2.json"
NOTICE_PATH = GSS_ROOT / "Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md"
SCHEDULES_ROOT = GSS_ROOT / "Step7_docs/outputs_step7/schedules"

requires_spec = pytest.mark.skipif(not SPEC_PATH.exists(), reason="frozen campaign spec absent")
requires_4j = pytest.mark.skipif(
    not BINDING_PATH.exists() or not NOTICE_PATH.exists() or not SCHEDULES_ROOT.exists(),
    reason="GSSCanada 4J artefacts are not present on this machine",
)


def _spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def _cell(f: float) -> dict:
    return next(row for row in _spec()["cells"] if row["sensitivity_f"] == f)


def _uk_cell(f: float) -> dict:
    return next(
        row for row in _spec()["cells"]
        if row["sensitivity_f"] == f and row["survey_fold"] == "uk"
    )


def test_signature_is_the_agreed_contract():
    signature = inspect.signature(run_campaign_cell)
    parameters = list(signature.parameters.values())
    assert parameters[0].name == "cell"
    assert parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    keyword_only = [p.name for p in parameters[1:]]
    assert keyword_only == [
        "spec_path", "spec_sha256", "binding_path", "chaining_notice_path",
        "schedules_root", "chaining_notice_sha256", "run_root", "dry_run",
        "energyplus_timeout",
    ]
    assert all(
        p.kind is inspect.Parameter.KEYWORD_ONLY for p in parameters[1:]
    )


@requires_spec
def test_verify_spec_accepts_the_frozen_digest():
    spec = verify_spec(_cell(0.0), SPEC_PATH, SPEC_SHA256)
    assert spec["spec_status"] == "FROZEN_PINNED"
    assert spec["n_cells"] == 510


@requires_spec
def test_verify_spec_refuses_a_wrong_digest():
    with pytest.raises(CampaignCellError, match="digest mismatch"):
        verify_spec(_cell(0.0), SPEC_PATH, "0" * 64)


@requires_spec
def test_verify_spec_refuses_an_unknown_cell():
    cell = dict(_cell(0.0))
    cell["cell_id"] = "es__NOT.A.CELL__f000"
    with pytest.raises(CampaignCellError, match="not present in spec"):
        verify_spec(cell, SPEC_PATH, SPEC_SHA256)


@requires_spec
def test_verify_spec_refuses_a_mutated_cell():
    cell = dict(_cell(0.0))
    cell["epw_path"] = "openubem/data/weather/somewhere_else.epw"
    with pytest.raises(CampaignCellError, match="differs from the frozen spec"):
        verify_spec(cell, SPEC_PATH, SPEC_SHA256)


@requires_spec
def test_verify_weather_refuses_a_digest_mismatch():
    cell = dict(_cell(0.0))
    cell["weather_sha256"] = "1" * 64
    with pytest.raises(CampaignCellError, match="EPW digest mismatch"):
        verify_weather(cell)


@requires_spec
def test_uk_cells_are_repinned_to_the_2014_calendar():
    cell = _uk_cell(0.0)
    epw_path, start_day = verify_weather(cell)
    assert epw_path.name == "uk_london_2014_2015_y2014.epw"
    assert start_day == "Wednesday"


@requires_spec
@requires_4j
def test_lift_authority_is_the_notice_not_the_frozen_field():
    authority = resolve_lift_authority(NOTICE_PATH, "independent")
    assert authority["notice_sha256"] == hashlib.sha256(NOTICE_PATH.read_bytes()).hexdigest()
    assert authority["rule_named_by_notice"] == "independent"


@requires_4j
def test_lift_authority_refuses_a_missing_notice(tmp_path: Path):
    with pytest.raises(CampaignCellError, match="lift notice is missing"):
        resolve_lift_authority(tmp_path / "absent.md", "independent")


@requires_4j
def test_lift_authority_refuses_a_notice_that_does_not_name_the_rule(tmp_path: Path):
    notice = tmp_path / "notice.md"
    notice.write_text("this notice names no rule\n", encoding="utf-8")
    with pytest.raises(CampaignCellError, match="does not name the chaining rule"):
        resolve_lift_authority(notice, "independent")


@requires_spec
@requires_4j
def test_presence_lookup_reads_the_ruled_pairing():
    binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    cell = _cell(0.15)
    block = lookup_presence(cell, binding, SCHEDULES_ROOT)
    ruled = next(
        row for row in binding["folds"][cell["survey_fold"]]["binding"]
        if row["archetype_id"] == cell["archetype_id"]
    )
    assert block["presence_hid"] == ruled["hid"]
    assert block["presence_sha256"] == ruled["presence_sha256"]
    assert block["presence_n_hours"] == 8760
    assert block["chaining_rule"] == "independent"


@requires_spec
@requires_4j
def test_presence_lookup_refuses_an_unbound_archetype():
    binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    cell = dict(_cell(0.15))
    cell["archetype_id"] = "ZZ.NO.SUCH.ARCHETYPE"
    with pytest.raises(CampaignCellError, match="no ruled presence series"):
        lookup_presence(cell, binding, SCHEDULES_ROOT)


@requires_spec
@requires_4j
def test_presence_lookup_refuses_a_digest_mismatch(tmp_path: Path):
    binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    cell = _cell(0.15)
    fold = cell["survey_fold"]
    bundle = binding["folds"][fold]["bundle"]
    row = next(
        r for r in binding["folds"][fold]["binding"]
        if r["archetype_id"] == cell["archetype_id"]
    )
    fake_bundle = tmp_path / bundle
    fake_bundle.mkdir(parents=True)
    (fake_bundle / row["presence_csv"]).write_text("\n".join(["1.0"] * 8760), encoding="utf-8")
    with pytest.raises(CampaignCellError, match="presence series digest mismatch"):
        lookup_presence(cell, binding, tmp_path)


@requires_spec
@requires_4j
def test_dry_run_f0_manifest_is_complete(tmp_path: Path):
    manifest = run_campaign_cell(
        _cell(0.0),
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
        schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
    )
    assert set(MANIFEST_FIELDS) <= set(manifest)
    assert manifest["presence_source"] == "not_required_f0"
    assert manifest["schedule_status_ignored"] is True
    assert manifest["heating_source"].startswith("Zone Ideal Loads")
    assert "meter" not in manifest["heating_source"].casefold()
    assert manifest["occupant_semantics_warning"]
    assert manifest["idf_sha256"] and manifest["gain_csv_sha256"]
    assert Path(manifest["manifest_path"]).exists()


@requires_spec
@requires_4j
def test_platform_field_is_in_the_contract_and_the_manifest(tmp_path: Path):
    assert "platform" in MANIFEST_FIELDS
    manifest = run_campaign_cell(
        _cell(0.0),
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
        schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
    )
    platform_record = manifest["platform"]
    assert isinstance(platform_record, dict)
    assert set(platform_record) == {
        "hostname", "os", "machine", "processor", "python_version",
        "energyplus_exe", "energyplus_sha256",
    }


@requires_spec
@requires_4j
def test_dry_run_never_measures_the_engine_version_or_hashes_the_binary(tmp_path: Path):
    manifest = run_campaign_cell(
        _cell(0.0),
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
        schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
    )
    assert manifest["energyplus_version_measured"] == "not_run"
    assert manifest["platform"]["energyplus_sha256"] == "not_run"
    assert manifest["energyplus_version_declared"] == "23.1"


@requires_spec
@requires_4j
def test_dry_run_f_positive_manifest_carries_every_digest(tmp_path: Path):
    cell = _cell(0.15)
    manifest = run_campaign_cell(
        cell,
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
        schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
    )
    assert set(MANIFEST_FIELDS) <= set(manifest)
    assert manifest["schedule_status_frozen_value"] == "BLOCKED_CHAINING_RULE"
    assert manifest["schedule_status_ignored"] is True
    assert manifest["chaining_rule"] == "independent"
    assert manifest["lift_authority"]["notice_sha256"]
    assert manifest["presence_sha256"] and manifest["presence_hid"]
    assert manifest["presence_n_hours"] == 8760
    assert manifest["binding_spec_digest_accepted_by"] in {
        "exact_match", "binding_invariance_clause"
    }
    assert "diary_origin_hour" in manifest["local_time_basis"]
    assert "rotated_to_midnight" in manifest["local_time_basis"]


@requires_spec
@requires_4j
def test_f_positive_refuses_when_the_notice_is_absent(tmp_path: Path):
    with pytest.raises(CampaignCellError, match="lift notice is missing"):
        run_campaign_cell(
            _cell(0.15),
            spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
            binding_path=BINDING_PATH, chaining_notice_path=tmp_path / "absent.md",
            schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
        )
    assert not list(tmp_path.glob("manifests/*.json"))


@requires_spec
@requires_4j
def test_f_positive_refuses_when_the_presence_series_is_absent(tmp_path: Path):
    with pytest.raises(CampaignCellError, match="presence series not found"):
        run_campaign_cell(
            _cell(0.15),
            spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
            binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
            schedules_root=tmp_path / "empty", run_root=tmp_path, dry_run=True,
        )
    assert not list(tmp_path.glob("manifests/*.json"))


@requires_spec
@requires_4j
def test_calendar_mismatch_between_bundle_and_epw_is_refused(tmp_path: Path):
    binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    cell = _cell(0.15)
    binding["folds"][cell["survey_fold"]]["bundle_year"] += 1
    tampered = tmp_path / "binding_wrong_year.json"
    tampered.write_text(json.dumps(binding), encoding="utf-8")
    with pytest.raises(CampaignCellError, match="calendar mismatch"):
        run_campaign_cell(
            cell,
            spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
            binding_path=tampered, chaining_notice_path=NOTICE_PATH,
            schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
        )


@requires_spec
@requires_4j
def test_every_fold_agrees_between_its_bundle_year_and_its_pinned_epw():
    binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    spec = _spec()
    for fold, block in binding["folds"].items():
        epw = next(
            row["epw_path"] for row in spec["cells"] if row["survey_fold"] == fold
        )
        assert epw.endswith(f"_y{block['bundle_year']}.epw"), (fold, epw)


NOTICE_SHA256 = "058c9d132d49db5fca15f2fa3b8d0a161cc947d27559b36fde6233b4a89d74c6"


@requires_4j
def test_lift_authority_accepts_the_declared_notice_digest():
    authority = resolve_lift_authority(
        NOTICE_PATH, "independent", chaining_notice_sha256=NOTICE_SHA256
    )
    assert authority["notice_sha256"] == NOTICE_SHA256
    assert authority["notice_sha256_declared"] == NOTICE_SHA256


@requires_4j
def test_lift_authority_refuses_a_notice_digest_mismatch():
    with pytest.raises(CampaignCellError, match="notice digest mismatch"):
        resolve_lift_authority(NOTICE_PATH, "independent", chaining_notice_sha256="0" * 64)


@requires_4j
def test_a_correctly_hashed_notice_that_omits_the_rule_is_still_refused(tmp_path: Path):
    """The digest check is the first condition, not a replacement for the word check."""
    notice = tmp_path / "notice.md"
    notice.write_text("this notice names no rule", encoding="utf-8")
    digest = hashlib.sha256(notice.read_bytes()).hexdigest()
    with pytest.raises(CampaignCellError, match="does not name the chaining rule"):
        resolve_lift_authority(notice, "independent", chaining_notice_sha256=digest)


@requires_spec
@requires_4j
def test_f_positive_refuses_a_wrong_notice_digest_end_to_end(tmp_path: Path):
    with pytest.raises(CampaignCellError, match="notice digest mismatch"):
        run_campaign_cell(
            _cell(0.15),
            spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
            binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
            schedules_root=SCHEDULES_ROOT, chaining_notice_sha256="0" * 64,
            run_root=tmp_path, dry_run=True,
        )
    assert not list(tmp_path.glob("manifests/*.json"))


@requires_spec
@requires_4j
def test_binding_invariance_presence_alone_is_not_coverage(tmp_path: Path):
    """A clause that names no digest must not license a spec neither side has seen."""
    binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    binding["spec"]["sha256"] = "9" * 64
    binding["binding_invariance"] = "a clause that names nothing"
    tampered = tmp_path / "binding_uncovered.json"
    tampered.write_text(json.dumps(binding), encoding="utf-8")
    with pytest.raises(CampaignCellError, match="applies_to"):
        run_campaign_cell(
            _cell(0.0),
            spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
            binding_path=tampered, chaining_notice_path=NOTICE_PATH,
            schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
        )


@requires_spec
@requires_4j
def test_binding_invariance_with_an_applies_to_list_is_accepted(tmp_path: Path):
    binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    binding["spec"]["sha256"] = "9" * 64
    binding["binding_invariance"] = {
        "statement": "invariant under a weather-only revision",
        "applies_to": [SPEC_SHA256],
    }
    covering = tmp_path / "binding_covering.json"
    covering.write_text(json.dumps(binding), encoding="utf-8")
    manifest = run_campaign_cell(
        _cell(0.0),
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=covering, chaining_notice_path=NOTICE_PATH,
        schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
    )
    assert manifest["binding_spec_digest_accepted_by"] == (
        "binding_invariance_clause_covering_this_digest"
    )


@requires_spec
@requires_4j
def test_v2_binding_is_accepted_today_by_exact_match(tmp_path: Path):
    """v2 pins v1.1 exactly, so the coverage rule changes nothing for the run in hand."""
    manifest = run_campaign_cell(
        _cell(0.0),
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
        schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
    )
    assert manifest["binding_spec_digest_accepted_by"] == "exact_match"


def test_energyplus_path_may_be_the_install_directory(monkeypatch, tmp_path: Path):
    """Every other consumer in the repo appends the exe to ENERGYPLUS_PATH; so must this one."""
    exe_name = "energyplus.exe" if sys.platform == "win32" else "energyplus"
    install = tmp_path / "EnergyPlusV23-1-0"
    install.mkdir()
    (install / exe_name).write_bytes(b"")
    monkeypatch.setattr(runner, "ENERGYPLUS_PATH", install)
    assert _energyplus_exe() == install / exe_name


def test_energyplus_path_may_also_be_the_binary_itself(monkeypatch, tmp_path: Path):
    """A caller that already pointed the variable at the binary must not get the exe appended twice."""
    exe = tmp_path / ("energyplus.exe" if sys.platform == "win32" else "energyplus")
    exe.write_bytes(b"")
    monkeypatch.setattr(runner, "ENERGYPLUS_PATH", exe)
    assert _energyplus_exe() == exe


@requires_spec
@requires_4j
def test_a_dry_run_is_never_reported_as_completed(tmp_path: Path):
    """A manifest exists for anything that built; only `completed` says it produced a number."""
    manifest = run_campaign_cell(
        _cell(0.0),
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
        schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
    )
    assert manifest["completed"] is False
    assert manifest["completion_status"] == "DRY_RUN"
    assert manifest["heating_kwh"] is None
    assert "completed" in MANIFEST_FIELDS and "completion_status" in MANIFEST_FIELDS


@requires_spec
@requires_4j
def test_the_cell_idf_carries_its_declared_thermal_capacity(tmp_path: Path):
    """A NoMass envelope with no InternalMass has zero heat capacity, and EnergyPlus
    then warns that the solution is unstable and returns a different answer per run."""
    cell = _cell(0.0)
    manifest = run_campaign_cell(
        cell,
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
        schedules_root=SCHEDULES_ROOT, run_root=tmp_path, dry_run=True,
    )
    from eppy.modeleditor import IDDAlreadySetError
    from geomeppy import IDF

    from openubem.config import ENERGYPLUS_IDD_PATH
    from openubem.idf.european_physics import internal_mass_capacity_j_k

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    idf = IDF(str(manifest["idf_path"]))
    masses = idf.idfobjects["INTERNALMASS"]
    assert len(masses) == 1
    record = load_archetype_record(cell["country_stock_code"], cell["archetype_id"])
    expected_j_k = (
        float(record["c_m_wh_m2k"]) * 3600.0 * float(record["geometry"]["a_c_ref_m2"])
    )
    assert internal_mass_capacity_j_k(idf, masses[0].Name) == pytest.approx(
        expected_j_k, rel=1e-9
    )
