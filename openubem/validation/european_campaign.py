"""Deterministic ES/GB/IT Step 8 campaign planning, without simulation submission."""
from __future__ import annotations

import csv
import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Iterable, Mapping

from openubem.semantic.european_schedules import F_LEVELS


CAMPAIGN_FOLDS = ("es", "uk", "it")
DEPENDENCY_DIGEST_SCHEMA = "step8-dependency-digest/1.0"


def load_campaign_archetypes(registry_paths: Iterable[Path | str]) -> list[dict[str, object]]:
    """Load exactly the 102 non-France occupant-campaign registry rows."""
    records: list[dict[str, object]] = []
    for path in registry_paths:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        records.extend(payload["records"])
    records.sort(key=lambda row: str(row["archetype_id"]))
    folds = {str(row["survey_fold"]) for row in records}
    if len(records) != 102 or folds != set(CAMPAIGN_FOLDS):
        raise ValueError("Step 8 occupant campaign requires exactly 102 ES/GB/IT rows")
    if len({str(row["archetype_id"]) for row in records}) != len(records):
        raise ValueError("archetype_id must be unique in the campaign registry")
    return records


def build_campaign_cells(records: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Make immutable, deterministic five-level rows with each f=0 control first."""
    ordered = sorted(records, key=lambda row: str(row["archetype_id"]))
    cells: list[dict[str, object]] = []
    for record, sensitivity_f in product(ordered, F_LEVELS):
        archetype_id = str(record["archetype_id"])
        fold = str(record["survey_fold"])
        suffix = f"f{int(round(sensitivity_f * 100)):03d}"
        cell_id = f"{fold}__{archetype_id}__{suffix}"
        cells.append({
            "cell_id": cell_id,
            "archetype_id": archetype_id,
            "survey_fold": fold,
            "country_stock_code": str(record["country_stock_code"]),
            "sensitivity_f": sensitivity_f,
            "control_cell_id": f"{fold}__{archetype_id}__f000",
            "idf_path": f"idfs/{cell_id}.idf",
            "epw_path": "PENDING_EU07_WEATHER",
            "gain_csv_path": f"schedules/{cell_id}.csv",
            "manifest_path": f"manifests/{cell_id}.json",
            "schedule_status": "READY_F0_CONTROL" if sensitivity_f == 0.0 else "BLOCKED_CHAINING_RULE",
            "weather_status": "RULED_NOT_PINNED",
        })
    validate_campaign_cells(cells)
    return cells


def validate_campaign_cells(cells: Iterable[Mapping[str, object]]) -> None:
    """Apply the pre-submission count, uniqueness, fold, and control-order assertions."""
    rows = list(cells)
    if len(rows) != 510:
        raise ValueError(f"campaign must contain 510 rows, found {len(rows)}")
    ids = [str(row["cell_id"]) for row in rows]
    if len(set(ids)) != 510:
        raise ValueError("campaign cell_id values must be unique")
    for level in F_LEVELS:
        if sum(float(row["sensitivity_f"]) == level for row in rows) != 102:
            raise ValueError(f"campaign must contain 102 rows at f={level}")
    by_archetype: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        by_archetype.setdefault(str(row["archetype_id"]), []).append(row)
    if len(by_archetype) != 102:
        raise ValueError("campaign must represent 102 distinct archetypes")
    for archetype_id, group in by_archetype.items():
        values = tuple(float(row["sensitivity_f"]) for row in group)
        if values != F_LEVELS:
            raise ValueError(f"{archetype_id} must have ordered f levels {F_LEVELS}")
        if any(str(row["control_cell_id"]) != str(group[0]["cell_id"]) for row in group):
            raise ValueError(f"{archetype_id} rows must reference their f=0 control")
    if {str(row["survey_fold"]) for row in rows} != set(CAMPAIGN_FOLDS):
        raise ValueError("campaign fold set must be es/uk/it only")


def write_campaign_lists(cells: Iterable[Mapping[str, object]], output_dir: Path | str) -> dict[str, Path]:
    """Write Q3/Q4 local planning lists; neither file authorizes a cluster submission."""
    rows = list(cells)
    validate_campaign_cells(rows)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    columns = ("cell_id", "idf_path", "epw_path", "gain_csv_path", "manifest_path")
    result: dict[str, Path] = {}
    for name, selected in (
        ("q3_control_cells.tsv", [row for row in rows if float(row["sensitivity_f"]) == 0.0]),
        ("q4_injected_cells.tsv", [row for row in rows if float(row["sensitivity_f"]) > 0.0]),
    ):
        path = output / name
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows([{key: row[key] for key in columns} for row in selected])
        result[name] = path
    return result


def _sha256_file(path: Path | str) -> str:
    """Return the measured SHA-256 of one required on-disk campaign input."""
    source = Path(path)
    if not source.is_file():
        raise ValueError(f"dependency input must be an existing file: {source}")
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dependency_fingerprints(
    *,
    idf_path: Path | str,
    schedule_path: Path | str,
    weather_path: Path | str,
    energyplus_build: str,
    adapter_config: Mapping[str, object],
    source_commit: str,
) -> dict[str, object]:
    """Measure every dependency that makes a completed Step 8 cell reusable.

    File contents, rather than filenames or timestamps, define the three physical
    inputs.  The remaining values are explicit build/configuration provenance.
    This is deliberately separate from the legacy ``is_completed`` marker check.
    """
    if not str(energyplus_build).strip():
        raise ValueError("energyplus_build must be a non-empty measured identity")
    if not str(source_commit).strip():
        raise ValueError("source_commit must be a non-empty measured identity")
    try:
        normalized_config = json.loads(json.dumps(adapter_config, sort_keys=True, separators=(",", ":")))
    except (TypeError, ValueError) as exc:
        raise ValueError("adapter_config must be JSON-serializable") from exc
    return {
        "schema_version": DEPENDENCY_DIGEST_SCHEMA,
        "idf_sha256": _sha256_file(idf_path),
        "schedule_emitted_sha256": _sha256_file(schedule_path),
        "weather_sha256": _sha256_file(weather_path),
        "energyplus_build": str(energyplus_build),
        "adapter_config": normalized_config,
        "source_commit": str(source_commit),
    }


def dependency_digest(**kwargs: object) -> str:
    """Return the canonical SHA-256 dependency digest for one campaign cell."""
    payload = dependency_fingerprints(**kwargs)  # type: ignore[arg-type]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cache_record_is_current(
    cache_record: Mapping[str, object],
    *,
    expected_dependency_digest: str,
    legacy_is_completed: bool,
) -> bool:
    """Accept a cached result only when completion *and* its exact digest agree."""
    return (
        legacy_is_completed
        and str(cache_record.get("status", "")) == "success"
        and bool(expected_dependency_digest)
        and str(cache_record.get("dependency_digest", "")) == expected_dependency_digest
    )


def resumable_cache_hit(
    work_dir: Path | str,
    cache_record: Mapping[str, object],
    *,
    expected_dependency_digest: str,
) -> bool:
    """Wrap OpenUBEM's output-marker check with the required dependency digest."""
    from openubem.simulation.parallel import is_completed

    return cache_record_is_current(
        cache_record,
        expected_dependency_digest=expected_dependency_digest,
        legacy_is_completed=is_completed(Path(work_dir)),
    )
