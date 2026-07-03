"""Embedded reproducibility metadata block for the CityJSON (T07).

Makes the artifact self-describing and content-addressable (V14). The build
timestamp lives in a SEPARATE, un-hashed metadata field so two builds over the
same pipeline state hash identically (CP-Reproducibility).
"""

from __future__ import annotations

import copy
import datetime
import hashlib
import subprocess

from openubem.config import RANDOM_SEED
from openubem.viz.cityjson_emitter import (
    LOD_SPEC_VERSION,
    VIEWER_SPEC_VERSION,
    dumps,
)

_REPRO_KEY = "+openubem_reproducibility"
_TIMESTAMP_KEY = "+openubem_build_timestamp"


def _git_commit(repo_dir=None) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


def _building_counts(cityjson) -> tuple[str, dict]:
    """Per-resolution_mode counts, or per-zoning_strategy when the run lacks
    resolution_mode (PLAN §5 — the pilot has no resolution_mode)."""
    key = "resolution_mode"
    counts: dict[str, int] = {}
    have_res = any("resolution_mode" in co.get("attributes", {})
                   for co in cityjson["CityObjects"].values())
    if not have_res:
        key = "zoning_strategy"
    for co in cityjson["CityObjects"].values():
        v = co.get("attributes", {}).get(key, "not_recorded")
        counts[str(v)] = counts.get(str(v), 0) + 1
    return key, counts


def add_metadata_block(
    cityjson,
    *,
    run_id: str,
    provenance_coverage: dict,
    source_refs: dict,
    repo_dir=None,
    timestamp: str | None = None,
) -> None:
    """Attach the reproducibility block + un-hashed timestamp to metadata.

    `cityjson["metadata"]` already carries `referenceSystem` + `+common_origin_utm`
    from T03; this augments it in place.
    """
    count_key, counts = _building_counts(cityjson)
    metadata = cityjson.setdefault("metadata", {})
    metadata[_REPRO_KEY] = {
        "git_commit": _git_commit(repo_dir),
        "random_seed": RANDOM_SEED,
        "run_id": run_id,
        "building_counts": {"grouped_by": count_key, "counts": counts},
        "provenance_coverage": provenance_coverage,
        "viewer_spec_version": VIEWER_SPEC_VERSION,
        "lod_spec_version": LOD_SPEC_VERSION,
        "source_refs": source_refs,
    }
    metadata[_TIMESTAMP_KEY] = (
        timestamp
        if timestamp is not None
        else datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


def content_hash(cityjson) -> str:
    """SHA-256 of the deterministic serialization, EXCLUDING the timestamp."""
    c = copy.deepcopy(cityjson)
    c.get("metadata", {}).pop(_TIMESTAMP_KEY, None)
    return hashlib.sha256(dumps(c).encode("utf-8")).hexdigest()
