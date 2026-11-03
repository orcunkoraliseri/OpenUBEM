"""Per-building, per-cell campaign wiring (plan block-6 SCEN-WIRE, item 4).

Not wired into the build path. The only importers of this module are
`tests/test_scenario_campaign_wiring.py` and this module's own docstring
example — same isolation rule as `openubem.scenarios.campaign` and
`openubem.scenarios.measures` (carried from PLAN_techtransfer-block5-2026-09-17.md
rule 3 / SCEN-01's own "How", now extended to this task).

Given a small manifest of already-built baseline IDFs, applies each of the 8 cells
from `openubem.scenarios.campaign.build_full_factorial_campaign()` to a *fresh copy*
of each building's IDF via the existing `openubem.scenarios.campaign.apply_cell()`,
and writes each resulting IDF to disk under a per-cell output subdirectory. Returns
(and optionally writes to disk) a manifest recording which building, which cell, and
the output path.

No EnergyPlus run happens anywhere in this module. No `05_results` write. Fleet-scale
execution (8,139 buildings x 8 cells) is item 6 of
`PLAN_techtransfer-block6-2026-09-18.md` §2a, separately gated on the unresolved
`05_results` write-slot question (§2b) — this module only produces the per-building,
per-cell IDFs on disk that a future fleet run would consume.
"""

import csv
from pathlib import Path
from typing import NamedTuple

from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.scenarios.campaign import apply_cell, build_full_factorial_campaign


class ManifestRow(NamedTuple):
    building_id: str
    cell_name: str
    output_path: str


def _ensure_idd_set() -> None:
    try:
        GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass


def run_campaign(
    buildings: "list[tuple[str, str]]",
    output_dir: "str",
    *,
    enabled: bool = True,
    archetype: "str | None" = None,
    write_manifest_csv: bool = True,
) -> "list[ManifestRow]":
    """Apply every cell of the full-factorial campaign to every listed building.

    `buildings` is a list of (building_id, baseline_idf_path) pairs. For each of the
    8 cells, each building's baseline IDF is loaded fresh (never mutated across
    cells) and `apply_cell()` applies that cell's measures to the in-memory copy,
    which is then saved to `output_dir/<cell_name>/<building_id>.idf`.
    """
    _ensure_idd_set()
    output_root = Path(output_dir)
    cells = build_full_factorial_campaign()
    manifest: "list[ManifestRow]" = []
    for cell in cells:
        cell_dir = output_root / cell.name
        cell_dir.mkdir(parents=True, exist_ok=True)
        for building_id, baseline_idf_path in buildings:
            idf = GeomIDF(str(baseline_idf_path))
            apply_cell(idf, cell, enabled=enabled, archetype=archetype)
            out_path = cell_dir / f"{building_id}.idf"
            idf.saveas(str(out_path))
            manifest.append(
                ManifestRow(building_id=building_id, cell_name=cell.name, output_path=str(out_path))
            )
    if write_manifest_csv:
        _write_manifest_csv(manifest, output_root / "manifest.csv")
    return manifest


def _write_manifest_csv(manifest: "list[ManifestRow]", path: "Path") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["building_id", "cell_name", "output_path"])
        for row in manifest:
            writer.writerow([row.building_id, row.cell_name, row.output_path])
