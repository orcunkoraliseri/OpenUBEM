"""OPEN-47 T02: measure the Chen, Hong & Piette (2017) floor-count condition on office
tiering, flag ON vs flag OFF, over the 8,160 adopted-run (phaseE_elevrb) buildings.

Measurement only. Does not adopt the flag, does not change any default, does not touch
the fleet. `use_floor_count=True` is only ever passed explicitly, by this script; every
production call site defaults to False (openubem/semantic/building_classifier.py), proven
byte-identical to the pre-T02 code by scripts/analysis (see progress log for the check).

Input provenance: phaseE_elevrb's own 05_results.csv (8,160 rows, adopted run) carries
footprint_area_m2 / levels / archetype_id but not the raw Step-1 columns the classifier
needs (function_tag, building_tag, use_class inputs) or archetype_source. phaseE and
phaseE_elevrb share the same 8,160-building set (osm_id sets verified equal per cell), so
this script classifies phaseE's own 01_buildings.gpkg (Step-1 acquisition output) with
today's classifier and cross-checks the result against phaseE_elevrb's actual archetype_id
before trusting it as "archetype_off": 16/8,160 rows disagree outright (different archetype
family entirely -- e.g. LargeOffice vs MidriseApartment -- not an office-tier shift), which
cannot be reproduced from this input (no overrides CSV exists in the repo) and are excluded
from the ON/OFF comparison, reported separately, never silently dropped.

Only buildings whose recomputed archetype_source head is RULE_USE_CLASS_SIZE or
FALLBACK_SIZE_DEFAULT can possibly change under the flag: those are the only two rule paths
that call _office_size_tier. This is checked from archetype_source directly, not inferred
from archetype_id, so it is not fooled by an override or by some other rule that happens to
also land on an Office archetype.

Coordinator follow-up (2026-08-12): the floor-count condition this flag adds can be driven
by an imputed level count, not just an observed one. Each row's levels_source token
(_impute_levels's own provenance tag: OSM_OBSERVED, HEURISTIC_HEIGHT,
GROUPMEDIAN_LEVELS_MED, LEVELS_DEFAULT_LOW) is carried through to the output CSV so the
strength of the evidence behind each reclassification is visible, not just its direction.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.semantic.building_classifier import (
    BuildingClassifier,
    _INPUT_SCHEMA_COLUMNS,
    _impute_levels,
    _normalise_use_class,
)

ROOT = Path(__file__).resolve().parent.parent.parent
PHASEE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
PHASEE_ELEVRB = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE_elevrb"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
ELEVATORS_BY_ARCHETYPE_PATH = ROOT / "openubem" / "data" / "loads" / "elevators_by_archetype.json"
OUT_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open47_floorcount_reclass.csv"

_OFFICE_TIER_HEADS = {"RULE_USE_CLASS_SIZE", "FALLBACK_SIZE_DEFAULT"}


def load_cell(cell: str) -> pd.DataFrame:
    gdf = gpd.read_file(PHASEE / cell / "01_buildings.gpkg")
    gdf = gdf[_INPUT_SCHEMA_COLUMNS].copy()
    gdf["levels"] = gdf["levels"].astype("Int64")

    off = BuildingClassifier(use_floor_count=False).classify(gdf.copy())
    on = BuildingClassifier(use_floor_count=True).classify(gdf.copy())

    # The classifier's own output preserves the raw upstream "levels" column unchanged
    # (byte-equality invariant, DESIGN §4 line 302) -- it is NOT the imputed value the
    # rule table actually used. Recompute levels_imputed the same way BuildingClassifier
    # does internally (group-median lookup fit on this cell's observed-levels rows) so the
    # CSV's "levels" column is the number that actually drove the tier decision.
    clf = BuildingClassifier()
    levels_group_median, levels_global_median = clf._build_levels_median_lookup(gdf)
    use_class = gdf.apply(lambda r: _normalise_use_class(r)[0], axis=1)
    levels_imputed_pair = gdf.apply(
        lambda r: _impute_levels(
            r,
            use_class=use_class.loc[r.name],
            levels_group_median=levels_group_median,
            levels_global_median=levels_global_median,
        ),
        axis=1,
        result_type="expand",
    )
    imputed = pd.DataFrame({
        "osm_id": gdf["osm_id"],
        "levels_imputed": levels_imputed_pair[0],
        "levels_source": levels_imputed_pair[1],
    })

    adopted = pd.read_csv(PHASEE_ELEVRB / cell / "05_results.csv")[
        ["osm_id", "footprint_area_m2", "archetype_id"]
    ].rename(columns={"archetype_id": "archetype_adopted"})

    merged = off[["osm_id", "footprint_area_m2", "archetype_id", "archetype_source"]].rename(
        columns={"archetype_id": "archetype_off"}
    ).merge(
        on[["osm_id", "archetype_id"]].rename(columns={"archetype_id": "archetype_on"}),
        on="osm_id",
    ).merge(imputed, on="osm_id").merge(adopted, on="osm_id", suffixes=("", "_adopted"))
    merged["cell"] = cell
    return merged


def main() -> int:
    fleet = pd.concat([load_cell(c) for c in CELLS], ignore_index=True)
    n_total = len(fleet)
    assert n_total == 8160, f"expected 8,160 adopted-run buildings, got {n_total}"

    # Cross-check: recomputed archetype_off (from phaseE's own Step-1 input, today's
    # default flag OFF) against phaseE_elevrb's actual adopted-run archetype_id.
    reproduced = fleet[fleet["archetype_off"] == fleet["archetype_adopted"]].copy()
    unreproduced = fleet[fleet["archetype_off"] != fleet["archetype_adopted"]].copy()

    # Only rows whose rule path actually calls _office_size_tier can change under the flag.
    office_head = reproduced["archetype_source"].str.split(",").str[0].isin(_OFFICE_TIER_HEADS)
    candidates = reproduced[office_head].copy()

    changed = candidates[candidates["archetype_off"] != candidates["archetype_on"]].copy()

    elevator_archetypes = {
        k for k in json.loads(ELEVATORS_BY_ARCHETYPE_PATH.read_text(encoding="utf-8")).keys()
        if not k.startswith("_")
    }
    changed["elevator_off"] = changed["archetype_off"].isin(elevator_archetypes)
    changed["elevator_on"] = changed["archetype_on"].isin(elevator_archetypes)
    changed["elevator_eligibility_change"] = changed.apply(
        lambda r: (
            "gain" if (r["elevator_on"] and not r["elevator_off"])
            else ("lose" if (r["elevator_off"] and not r["elevator_on"]) else "none")
        ),
        axis=1,
    )
    changed["direction"] = changed["archetype_off"] + " -> " + changed["archetype_on"]
    changed["total_floor_area_m2"] = changed["footprint_area_m2"] * changed["levels_imputed"].clip(lower=1)

    out = changed[[
        "osm_id", "cell", "footprint_area_m2", "levels_imputed", "levels_source",
        "archetype_off", "archetype_on",
    ]].rename(columns={"footprint_area_m2": "area_m2", "levels_imputed": "levels"})
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    gained = changed[changed["elevator_eligibility_change"] == "gain"]

    print(f"n_total_adopted_run: {n_total}")
    print(f"n_unreproduced (excluded, archetype family disagreement vs adopted run): {len(unreproduced)}")
    print(f"n_reproduced: {len(reproduced)}")
    print(f"n_office_tier_candidates (RULE_USE_CLASS_SIZE / FALLBACK_SIZE_DEFAULT): {len(candidates)}")
    print(f"n_changed: {len(changed)} / {n_total}")
    print("by direction:")
    for direction, n in changed["direction"].value_counts().items():
        print(f"  {direction}: {n}")
    print("elevator eligibility change among changed buildings:")
    for kind, n in changed["elevator_eligibility_change"].value_counts().items():
        print(f"  {kind}: {n}")
    print(f"total floor area affected (changed rows): {changed['total_floor_area_m2'].sum():.1f} m^2")
    print(f"levels_source breakdown, {len(changed)} changed buildings:")
    for src, n in changed["levels_source"].value_counts().items():
        print(f"  {src}: {n}")
    print(f"levels_source breakdown, {len(gained)} elevator-eligibility-gaining buildings:")
    for src, n in gained["levels_source"].value_counts().items():
        print(f"  {src}: {n}")
    print(f"wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
