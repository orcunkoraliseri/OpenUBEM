"""Full-factorial scenario campaign definition (plan block-6 SCEN-01).

Not wired into the build path. The only importer of this module is
`tests/test_scenario_campaign.py` (same isolation rule as `openubem.scenarios.measures`,
carried from PLAN_techtransfer-block5-2026-09-17.md rule 3 / this task's own "How").

Pure data/pure-function campaign generator over the measure table already shipped at
`openubem/data/scenarios/measures.json`. Produces the 8 cells of the full factorial over
the 3 currently active measures (baseline + every non-empty subset of
`lighting_power_density`, `thermostat_setback`, `infiltration_tightening`, i.e. all 2**3
combinations). The withdrawn measure `envelope_u_upgrade` never enters a cell.

Packaging decision: PLAN_techtransfer-block6-2026-09-18.md §2b, Option C (full factorial),
routed to Gemini and relayed by the user 2026-09-18.

`build_full_factorial_campaign()` fails closed (raises) if the table's set of active
measure ids ever stops matching exactly the 3 this module is defined over, rather than
silently building a campaign over a subset.

Applying a cell's measures to an IDF goes through the existing
`openubem.scenarios.measures.apply_measure` via `apply_cell()` below — this module adds no
second way to call a measure.
"""

from itertools import combinations
from typing import NamedTuple

from openubem.scenarios import measures

_SHORT_NAMES = {
    "lighting_power_density": "lighting",
    "thermostat_setback": "setback",
    "infiltration_tightening": "infiltration",
}


class Cell(NamedTuple):
    name: str
    measure_ids: tuple


def active_measure_ids(table: "dict | None" = None) -> list:
    table = table if table is not None else measures.load_measures()
    return [mid for mid in table if table[mid].get("status") == "active"]


def build_full_factorial_campaign(table: "dict | None" = None) -> "list[Cell]":
    table = table if table is not None else measures.load_measures()
    ids = active_measure_ids(table)
    expected = list(_SHORT_NAMES)
    if set(ids) != set(expected):
        raise ValueError(
            f"build_full_factorial_campaign: active measure ids {ids!r} do not match the "
            f"3 measures this campaign is defined over {expected!r}"
        )
    cells = []
    for r in range(len(ids) + 1):
        for combo in combinations(ids, r):
            name = "baseline" if r == 0 else "+".join(_SHORT_NAMES[m] for m in combo)
            cells.append(Cell(name=name, measure_ids=combo))
    return cells


def apply_cell(
    idf, cell: Cell, *, enabled: bool = True, archetype: "str | None" = None
) -> "list[dict]":
    return [
        measures.apply_measure(idf, measure_id, enabled=enabled, archetype=archetype)
        for measure_id in cell.measure_ids
    ]
