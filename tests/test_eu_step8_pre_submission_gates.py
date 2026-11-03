"""Mutation coverage for the non-engine subset of EU-09 Step 8 gates."""
from __future__ import annotations

from pathlib import Path

from openubem.validation.european_campaign import build_campaign_cells, load_campaign_archetypes
from openubem.validation.step8_gates import HARD_SEVERITY, evaluate_pre_submission_gates, findings_by_gate


ROOT = Path(__file__).parents[1]
REGISTRIES = [ROOT / "openubem" / "data" / "construction" / f"tabula_archetypes_{fold}.json" for fold in ("es", "gb", "it")]
TABLE = "campaigns/step8_cells.tsv"


def _clean_inputs():
    cells = build_campaign_cells(load_campaign_archetypes(REGISTRIES))
    manifests = []
    cache = []
    for cell in cells:
        cell_id = cell["cell_id"]
        digest = f"dependency-{cell_id}"
        manifests.append({
            "cell_id": cell_id,
            "status": "success",
            "schedule_emitted_sha256": f"schedule-{cell_id}",
            "dependency_digest": digest,
            "platform": "test-platform",
            "created_utc": "2026-08-23T00:00:00Z",
            "fold": f"{cell['survey_fold']}_held_out",
            "held_out_country": cell["survey_fold"],
        })
        cache.append({"cell_id": cell_id, "dependency_digest": digest})
    return cells, manifests, cache


def _report(cells, manifests, cache, **kwargs):
    return findings_by_gate(evaluate_pre_submission_gates(
        cells, manifests, cache, declared_cell_count=510,
        campaign_table_path=TABLE, scoring_table_path=TABLE, **kwargs,
    ))


def test_null_perturbation_passes_all_supported_hard_gates():
    report = _report(*_clean_inputs())
    assert all(finding.passed for finding in report.values())
    assert all(finding.severity == HARD_SEVERITY for finding in report.values())


def test_mutations_fire_their_designated_pre_submission_gate_only():
    cells, manifests, cache = _clean_inputs()
    same_schedule = [dict(item) for item in manifests]
    same_schedule[1]["schedule_emitted_sha256"] = same_schedule[0]["schedule_emitted_sha256"]
    assert not _report(cells, same_schedule, cache)["G8.8"].passed

    stale_cache = [dict(item) for item in cache]
    stale_cache[1]["dependency_digest"] = "obsolete"
    stale = _report(cells, manifests, stale_cache)
    assert not stale["G8.9"].passed and stale["G8.8"].passed

    copied = [dict(item) for item in manifests]
    copied[1] = {**copied[0], "cell_id": cells[0]["cell_id"]}
    assert not _report(cells, copied, cache)["G8.14"].passed

    wrong_fold = [dict(item) for item in manifests]
    non_es_index = next(index for index, cell in enumerate(cells) if cell["survey_fold"] != "es")
    wrong_fold[non_es_index]["fold"] = "es_held_out"
    report = _report(cells, wrong_fold, cache)
    assert not report["G8.16"].passed and report["G8.14"].passed


def test_controls_and_vacuity_guards_fail_closed():
    cells, manifests, cache = _clean_inputs()
    controls = [dict(item) for item in manifests]
    controls[0]["status"] = "failed"
    assert not _report(cells, controls, cache)["G8.0"].passed

    report = findings_by_gate(evaluate_pre_submission_gates(
        cells, manifests, cache, declared_cell_count=509,
        campaign_table_path=TABLE, scoring_table_path="campaigns/other.tsv",
    ))
    assert not any(finding.passed for finding in report.values())

    missing_fold = [dict(item) for item in manifests]
    del missing_fold[0]["fold"]
    assert not _report(cells, missing_fold, cache)["G8.16"].passed
