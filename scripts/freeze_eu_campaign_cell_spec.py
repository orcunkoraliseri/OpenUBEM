"""Freeze the versioned, immutable ES/GB/IT campaign-cell specification.

Builds the 510 campaign cells from ``openubem.validation.european_campaign``
(never hand-authored), resolves per-fold weather identity from
``openubem/data/weather/weather_registry.json``, and writes the frozen spec
atomically. Refuses to write a PINNED spec unless every fold is
``RULED_PINNED`` or ``RULED_PINNED_EXCEPTION``.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from openubem.semantic.european_schedules import F_LEVELS
from openubem.validation.european_campaign import (
    CAMPAIGN_FOLDS,
    build_campaign_cells,
    load_campaign_archetypes,
    validate_campaign_cells,
)

SCHEMA_VERSION = "eu-campaign-cell-spec/1.0"
CAVEATS_SCHEMA_VERSION = "eu-boundary-caveats/1.0"
MIN_CAVEATS = 16
REQUIRED_CAVEAT_KEYS = ("id", "caveat", "measured_extent", "must_not_conclude")
ACCEPTED_PINNED_STATUSES = ("RULED_PINNED", "RULED_PINNED_EXCEPTION")


class CaveatRegisterError(RuntimeError):
    """Raised when the boundary caveats register is missing or malformed."""
CELL_ID_NOTE = (
    "cell_id is an index key, not a complete provenance key. Weather identity "
    "lives in each cell's epw_path, weather_id and weather_sha256 fields. A "
    "consumer that hashes cell_id alone and expects it to pin the weather "
    "input is using it wrongly."
)

ARCHETYPE_REGISTRY_PATHS = (
    REPO_ROOT / "openubem" / "data" / "construction" / "tabula_archetypes_es.json",
    REPO_ROOT / "openubem" / "data" / "construction" / "tabula_archetypes_gb.json",
    REPO_ROOT / "openubem" / "data" / "construction" / "tabula_archetypes_it.json",
)
DEFAULT_WEATHER_REGISTRY_PATH = REPO_ROOT / "openubem" / "data" / "weather" / "weather_registry.json"
DEFAULT_CAVEATS_REGISTRY_PATH = REPO_ROOT / "openubem" / "data" / "campaign" / "eu_boundary_caveats_v1.0.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "openubem" / "data" / "campaign" / "eu_campaign_cell_spec_v1.0.json"


def _repo_relative_posix(path: Path) -> str:
    """Return path as a repo-relative POSIX string; never an absolute local path."""
    candidate = Path(path)
    try:
        resolved = candidate.resolve()
        relative = resolved.relative_to(REPO_ROOT.resolve())
        return relative.as_posix()
    except ValueError:
        return candidate.as_posix()


def load_boundary_caveats(path: Path | str) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Load and hard-validate the boundary caveats register. Raise on any defect."""
    registry_path = Path(path)
    if not registry_path.is_file():
        raise CaveatRegisterError(f"boundary caveats register is missing: {registry_path}")

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version")
    if schema_version != CAVEATS_SCHEMA_VERSION:
        raise CaveatRegisterError(
            f"boundary caveats register schema_version must be {CAVEATS_SCHEMA_VERSION!r}, "
            f"found {schema_version!r} in {registry_path}"
        )

    caveats = payload.get("caveats", [])
    n_caveats = payload.get("n_caveats")
    if n_caveats != len(caveats):
        raise CaveatRegisterError(
            f"boundary caveats register n_caveats={n_caveats!r} disagrees with "
            f"len(caveats)={len(caveats)} in {registry_path}"
        )
    if len(caveats) < MIN_CAVEATS:
        raise CaveatRegisterError(
            f"boundary caveats register has only {len(caveats)} entries, fewer than the "
            f"required {MIN_CAVEATS} in {registry_path}"
        )
    for entry in caveats:
        missing = [key for key in REQUIRED_CAVEAT_KEYS if key not in entry]
        if missing:
            raise CaveatRegisterError(
                f"boundary caveats register entry {entry.get('id', '<no id>')!r} is missing "
                f"required key(s) {missing} in {registry_path}"
            )

    source = {"path": _repo_relative_posix(registry_path), "schema_version": schema_version}
    return caveats, source


def _weather_targets_by_fold(weather_registry: dict[str, object]) -> dict[str, dict[str, object]]:
    targets = weather_registry.get("targets", [])
    by_fold: dict[str, dict[str, object]] = {}
    for target in targets:
        fold = str(target.get("fold", ""))
        by_fold[fold] = target
    return by_fold


def resolve_fold_weather(fold: str, weather_registry: dict[str, object]) -> dict[str, object]:
    """Return the weather identity block for one campaign fold, or raise if absent."""
    by_fold = _weather_targets_by_fold(weather_registry)
    if fold not in by_fold:
        raise ValueError(f"weather_registry has no entry for fold {fold!r}")
    target = by_fold[fold]
    output_filename = str(target.get("output_filename", ""))
    weather_id = Path(output_filename).stem if output_filename else ""
    weather_file = target.get("weather_file")
    epw_path = str(weather_file) if weather_file else "PENDING_EU07_WEATHER"
    status = str(target.get("status", ""))
    sha256 = target.get("sha256")
    weather_sha256 = str(sha256) if sha256 else None
    return {
        "fold": fold,
        "weather_id": weather_id,
        "epw_path": epw_path,
        "weather_sha256": weather_sha256,
        "weather_status": status,
        "city": target.get("city"),
        "raw_era5_window": target.get("raw_era5_window"),
    }


def apply_weather_to_cells(
    cells: list[dict[str, object]], weather_by_fold: dict[str, dict[str, object]]
) -> list[dict[str, object]]:
    """Return new cell dicts carrying the four first-class weather fields."""
    updated: list[dict[str, object]] = []
    for cell in cells:
        fold = str(cell["survey_fold"])
        weather = weather_by_fold[fold]
        new_cell = dict(cell)
        new_cell["epw_path"] = weather["epw_path"]
        new_cell["weather_id"] = weather["weather_id"]
        new_cell["weather_sha256"] = weather["weather_sha256"]
        new_cell["weather_status"] = weather["weather_status"]
        updated.append(new_cell)
    return updated


def _git_commit_and_dirty(cwd: Path) -> tuple[str, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout
    return commit, bool(status.strip())


def build_spec(
    *,
    archetype_registry_paths: tuple[Path, ...] = ARCHETYPE_REGISTRY_PATHS,
    weather_registry_path: Path = DEFAULT_WEATHER_REGISTRY_PATH,
    caveats_registry_path: Path = DEFAULT_CAVEATS_REGISTRY_PATH,
    require_pinned: bool = True,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, object] | None, list[str]]:
    """Build the frozen spec payload. Returns (spec_or_none, refusal_lines).

    Raises ``CaveatRegisterError`` (a hard failure, unaffected by ``require_pinned``)
    if the boundary caveats register is missing, mismatched, short, or malformed.
    """
    caveats, caveats_source = load_boundary_caveats(caveats_registry_path)

    records = load_campaign_archetypes(archetype_registry_paths)
    cells = build_campaign_cells(records)

    weather_registry = json.loads(Path(weather_registry_path).read_text(encoding="utf-8"))
    weather_by_fold = {
        fold: resolve_fold_weather(fold, weather_registry) for fold in CAMPAIGN_FOLDS
    }

    refusal_lines: list[str] = []
    for fold in CAMPAIGN_FOLDS:
        status = str(weather_by_fold[fold]["weather_status"])
        if status not in ACCEPTED_PINNED_STATUSES:
            refusal_lines.append(f"NOT_PINNED {fold} {status}")

    if refusal_lines and require_pinned:
        return None, refusal_lines

    cells = apply_weather_to_cells(cells, weather_by_fold)
    validate_campaign_cells(cells)

    spec_status = "FROZEN_PINNED" if not refusal_lines else "DRAFT_WEATHER_NOT_PINNED"
    commit, dirty = _git_commit_and_dirty(repo_root)

    weather_block = {
        fold: {
            "weather_id": weather_by_fold[fold]["weather_id"],
            "epw_path": weather_by_fold[fold]["epw_path"],
            "weather_sha256": weather_by_fold[fold]["weather_sha256"],
            "weather_status": weather_by_fold[fold]["weather_status"],
        }
        for fold in CAMPAIGN_FOLDS
    }

    spec = {
        "schema_version": SCHEMA_VERSION,
        "spec_status": spec_status,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "openubem_git_commit": commit,
        "git_dirty": dirty,
        "n_cells": len(cells),
        "folds": list(CAMPAIGN_FOLDS),
        "f_levels": list(F_LEVELS),
        "weather": weather_block,
        "caveats": caveats,
        "caveats_source": caveats_source,
        "cell_id_note": CELL_ID_NOTE,
        "cells": cells,
    }
    return spec, refusal_lines


def _write_json_atomic(payload: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    os.replace(temporary, output_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-unpinned", action="store_true", help="write a DRAFT spec even if a fold is unpinned")
    parser.add_argument("--require-pinned", dest="require_pinned", action="store_true", default=True)
    parser.add_argument("--output", type=Path, default=None, help="override the output path")
    args = parser.parse_args(argv)

    require_pinned = not args.allow_unpinned

    try:
        spec, refusal_lines = build_spec(require_pinned=require_pinned)
    except CaveatRegisterError as exc:
        print(f"CAVEATS_INVALID: {exc}")
        return 1

    if spec is None:
        for line in refusal_lines:
            print(line)
        print("refusing to write pinned campaign-cell spec: not all folds are pinned")
        return 1

    if args.output is not None:
        output_path = args.output
    elif spec["spec_status"] == "DRAFT_WEATHER_NOT_PINNED":
        output_path = DEFAULT_OUTPUT_PATH.with_name(
            DEFAULT_OUTPUT_PATH.stem + "_DRAFT" + DEFAULT_OUTPUT_PATH.suffix
        )
    else:
        output_path = DEFAULT_OUTPUT_PATH

    _write_json_atomic(spec, output_path)
    print(f"wrote {output_path} status={spec['spec_status']} n_cells={spec['n_cells']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
