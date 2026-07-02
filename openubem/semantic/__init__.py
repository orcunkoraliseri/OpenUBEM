"""Step 2.2 orchestrator — enrich_semantics() (DESIGN §3A–§3G)."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from openubem import config
from openubem.semantic.construction_sets import (
    apply_nan_vintage_provenance,
    append_vintage_donor_flags,
    get_construction_set,
    resolve_vintage,
)
from openubem.semantic.loads import _LOADS_PROV_COLS, _LOADS_VALUE_COLS, get_loads
from openubem.semantic.imputation import impute_column
from openubem.semantic.schedules import build_schedule_library

logger = logging.getLogger(__name__)

# ── 30-token archetype vocabulary (DESIGN §3A) ────────────────────────────────
_ARCHETYPE_VOCAB: list[str] = [
    "College", "Courthouse", "FullServiceRestaurant", "HighriseApartment",
    "Hospital", "LargeDataCenterHighITE", "LargeDataCenterLowITE", "LargeHotel",
    "LargeOffice", "LargeOfficeDetailed", "Laboratory", "MediumOffice",
    "MediumOfficeDetailed", "MidriseApartment", "OpenUBEMUnknown", "Outpatient",
    "PrimarySchool", "QuickServiceRestaurant", "RetailStandalone", "RetailStripmall",
    "SecondarySchool", "SmallDataCenterHighITE", "SmallDataCenterLowITE",
    "SmallHotel", "SmallOffice", "SmallOfficeDetailed", "SuperMarket",
    "SuperTallBuilding", "TallBuilding", "Warehouse",
]

# 16-token climate zone vocabulary (DESIGN §3A)
_CLIMATE_ZONE_VOCAB: list[str] = [
    "1A", "2A", "2B", "3A", "3B", "3C",
    "4A", "4B", "4C", "5A", "5B", "5C",
    "6A", "6B", "7", "8",
]

# F17: the 28 appended column names in fixed order
_F17_ENVELOPE_COLS = [
    "vintage_standard",
    "u_roof_w_m2k", "assembly_roof",
    "u_wall_w_m2k", "assembly_wall",
    "u_window_w_m2k", "shgc_window",
    "u_floor_w_m2k", "infiltration_m3_s_m2",
    "provenance_u_roof", "provenance_u_wall", "provenance_u_window",
    "provenance_u_floor", "provenance_infiltration",
]
_F17_LOADS_COLS = [
    "lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person",
    "heating_setpoint_c", "cooling_setpoint_c",
    "heating_setback_c", "cooling_setup_c",
    "wwr",
    "provenance_lighting", "provenance_equipment", "provenance_occupant_density",
    "provenance_heating_setpoint", "provenance_cooling_setpoint",
    "provenance_wwr",
]
_F17_ALL = _F17_ENVELOPE_COLS + _F17_LOADS_COLS  # 28 columns

# Plausibility bounds for validate_schema() (DESIGN §3G F19, R-2.2-9)
_PLAUS = {
    # DESIGN F19 stated [0.1, 7.0] but 90.1-2019 CZ7 u_roof=0.097 W/m²K is valid → lower to 0.05
    "u_roof_w_m2k":         (0.05, 7.0),
    "u_wall_w_m2k":         (0.05, 7.0),
    "u_window_w_m2k":       (0.05, 7.0),
    "u_floor_w_m2k":        (0.05, 7.0),
    "shgc_window":          (0.0, 1.0),   # (0, 1] exclusive lower handled below
    "infiltration_m3_s_m2": (0.0, 0.01),  # (0, 0.01] exclusive lower handled below
    "lighting_w_m2":        (0.0, 50.0),  # (0, 50] exclusive lower
    "equipment_w_m2":       (0.0, 2500.0),  # (0, 2500] non-DataCenter ≤ 100 handled elsewhere
    "occupant_m2_per_person": (1.0, 500.0),  # R-2.2-9: [1, 500]
    "wwr":                  (0.05, 0.9),
}

_DONOR_ARCH = "MediumOffice"  # F13: Unknown donor archetype


def _validate_input_schema(gdf: gpd.GeoDataFrame) -> None:
    """Gate: check names + required non-null columns (DESIGN §3A F2)."""
    required = ["archetype_id", "climate_zone", "epw_path", "provenance_climate_zone"]
    missing = [c for c in required if c not in gdf.columns]
    if missing:
        raise ValueError(f"enrich_semantics input gate: missing columns {missing}")

    null_epw = gdf["epw_path"].isna().sum()
    if null_epw:
        raise ValueError(f"enrich_semantics: {null_epw} rows have null epw_path")

    null_cz = gdf["climate_zone"].isna().sum()
    if null_cz:
        raise ValueError(f"enrich_semantics: {null_cz} rows have null climate_zone")


def validate_schema(gdf: gpd.GeoDataFrame) -> None:
    """
    Post-enrichment gate: 57 cols, zero NaN in 28 appended, plausibility (DESIGN F19).
    Raises ValueError on any failure.
    """
    if len(gdf.columns) != 57:
        raise ValueError(f"validate_schema: expected 57 columns, got {len(gdf.columns)}")

    # Verify F17 columns are present in correct order at the tail
    actual_tail = list(gdf.columns[-28:])
    if actual_tail != _F17_ALL:
        raise ValueError(
            f"validate_schema: last 28 columns mismatch.\n"
            f"Expected: {_F17_ALL}\nGot: {actual_tail}"
        )

    # Zero NaN in 28 appended columns
    for col in _F17_ALL:
        n_nan = gdf[col].isna().sum()
        if n_nan:
            raise ValueError(f"validate_schema: {n_nan} NaN in appended column '{col}'")

    # Plausibility checks
    _DC_ARCHS = {
        "LargeDataCenterHighITE", "LargeDataCenterLowITE",
        "SmallDataCenterHighITE", "SmallDataCenterLowITE",
    }
    has_arch_col = "archetype_id" in gdf.columns
    for col, (lo, hi) in _PLAUS.items():
        vals = gdf[col].astype(float)
        if col in ("shgc_window", "infiltration_m3_s_m2", "lighting_w_m2", "equipment_w_m2"):
            if (vals <= 0).any():
                raise ValueError(f"validate_schema: non-positive value in '{col}'")
        # equipment_w_m2: DataCenter ITE and Unknown (PDE over full range) may exceed 100
        # non-DataCenter, non-Unknown rows must be ≤ 100 W/m² (F19)
        if col == "equipment_w_m2" and has_arch_col:
            non_dc_mask = ~gdf["archetype_id"].isin(_DC_ARCHS | {"OpenUBEMUnknown"})
            non_dc_vals = vals[non_dc_mask]
            if (non_dc_vals < lo).any() or (non_dc_vals > 100).any():
                raise ValueError(
                    f"validate_schema: non-DataCenter '{col}' out of range [{lo}, 100]: "
                    f"min={non_dc_vals.min():.4f}, max={non_dc_vals.max():.4f}"
                )
            continue
        if (vals < lo).any() or (vals > hi).any():
            raise ValueError(
                f"validate_schema: '{col}' out of range [{lo}, {hi}]: "
                f"min={vals.min():.4f}, max={vals.max():.4f}"
            )

    # Row-wise setpoint invariants (DESIGN F19)
    bad_inv = gdf["heating_setpoint_c"] >= gdf["cooling_setpoint_c"]
    if bad_inv.any():
        raise ValueError("validate_schema: heating_setpoint_c >= cooling_setpoint_c")

    bad_setback = gdf["heating_setback_c"] > gdf["heating_setpoint_c"]
    if bad_setback.any():
        raise ValueError("validate_schema: heating_setback_c > heating_setpoint_c")

    bad_htg_hi = (gdf["heating_setpoint_c"] > 25).any()
    if bad_htg_hi:
        raise ValueError("validate_schema: heating_setpoint_c > 25°C")

    bad_setup = gdf["cooling_setup_c"] < gdf["cooling_setpoint_c"]
    if bad_setup.any():
        raise ValueError("validate_schema: cooling_setup_c < cooling_setpoint_c")


def _write_schema_json(gdf: gpd.GeoDataFrame, output_dir: Path) -> None:
    """Write 02b_buildings_enriched.schema.json mirroring building_classifier pattern."""
    _NEW_ROLES = {c: "derived" for c in _F17_ALL}
    _NEW_ROLES.update({c: "provenance" for c in _F17_ALL if c.startswith("provenance_")})
    _NEW_ROLES["vintage_standard"] = "derived"

    entries = []
    for col in gdf.columns:
        if col == "geometry":
            continue
        role = _NEW_ROLES.get(col, "upstream")
        entry: dict = {"name": col, "dtype": str(gdf[col].dtype), "provenance_role": role}
        entries.append(entry)

    (output_dir / "02b_buildings_enriched.schema.json").write_text(
        json.dumps({"schema_version": "1.0.0", "columns": entries}, indent=2),
        encoding="utf-8",
    )


def _build_unknown_envelope(
    gdf: gpd.GeoDataFrame,
    unk_mask: pd.Series,
    construction_table: dict | None,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    F13: OpenUBEMUnknown rows get donor MediumOffice@DOERefPre1980 in their own zone.
    Returns envelope DataFrame for the Unknown rows only, index-aligned.
    """
    if not unk_mask.any():
        return pd.DataFrame()

    unk_gdf = gdf.loc[unk_mask].copy()
    unk_gdf["archetype_id"] = _DONOR_ARCH
    donor_vintage = pd.Series("DOERefPre1980", index=unk_gdf.index)
    env_df = get_construction_set(unk_gdf, donor_vintage, custom_table=construction_table, rng=rng)
    for col in [c for c in env_df.columns if c.startswith("provenance_")]:
        env_df[col] = "HEURISTIC"
    env_df["vintage_standard"] = "DOERefPre1980"
    return env_df


def _build_unknown_loads(
    gdf: gpd.GeoDataFrame,
    unk_mask: pd.Series,
    real_loads: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    F13: Unknown rows — densities+wwr via PDE over cross-archetype [min,max];
    setpoints via cross-archetype MEDIAN (HEURISTIC), post-guard heating < cooling.
    """
    if not unk_mask.any():
        return pd.DataFrame()

    result = pd.DataFrame(index=gdf.index[unk_mask])
    pde_cols = ["lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person", "wwr"]
    scalar_cols = ["heating_setpoint_c", "cooling_setpoint_c", "heating_setback_c", "cooling_setup_c"]

    n = unk_mask.sum()
    for col in pde_cols:
        lo, hi = real_loads[col].min(), real_loads[col].max()
        vals = rng.uniform(lo, hi, size=n)
        result[col] = vals

    for col in scalar_cols:
        result[col] = float(real_loads[col].median())

    # Post-guard: ensure heating < cooling
    if (result["heating_setpoint_c"] >= result["cooling_setpoint_c"]).any():
        result["heating_setpoint_c"] = result["heating_setpoint_c"].clip(upper=result["cooling_setpoint_c"] - 0.5)

    # Provenance
    for col in pde_cols:
        result[f"provenance_{col.replace('_w_m2', '').replace('_m2_per_person', '_density').replace('wwr', 'wwr')}"] = "PDE_GENERATED"
    result["provenance_heating_setpoint"] = "HEURISTIC"
    result["provenance_cooling_setpoint"] = "HEURISTIC"

    # Correct provenance column names to match F17 _LOADS_PROV_COLS
    rename_map = {
        "provenance_lighting": "provenance_lighting",
        "provenance_equipment": "provenance_equipment",
        "provenance_m2_per_person": "provenance_occupant_density",
        "provenance_wwr": "provenance_wwr",
    }
    # Build them explicitly
    for col in _LOADS_PROV_COLS:
        if col not in result.columns:
            if col == "provenance_lighting":
                result[col] = "PDE_GENERATED"
            elif col == "provenance_equipment":
                result[col] = "PDE_GENERATED"
            elif col == "provenance_occupant_density":
                result[col] = "PDE_GENERATED"
            elif col == "provenance_wwr":
                result[col] = "PDE_GENERATED"
            elif col == "provenance_heating_setpoint":
                result[col] = "HEURISTIC"
            elif col == "provenance_cooling_setpoint":
                result[col] = "HEURISTIC"

    return result


def enrich_semantics(
    gdf: gpd.GeoDataFrame,
    output_dir: Path | None = None,
    *,
    load_mode: str | None = None,
    random_seed: int | None = None,
    construction_table: dict | None = None,
    loads_table: dict | None = None,
    schedules_table: dict | None = None,
) -> tuple[gpd.GeoDataFrame, dict]:
    """
    Enrich a 29-column Step-2.1 GDF with 28 semantic columns → 57-column output.

    Pipeline: gate → vintage → envelope → loads → Unknown/gap imputation →
              probabilistic perturbation (if load_mode='probabilistic') →
              schedule library → validate_schema() → emit.

    Returns (enriched_gdf, schedule_library_dict).
    """
    if load_mode is None:
        load_mode = config.LOAD_MODE
    if random_seed is None:
        random_seed = config.RANDOM_SEED

    rng = np.random.default_rng(random_seed)  # F14: one RNG per run

    # ── 3A: input gate ────────────────────────────────────────────────────────
    _validate_input_schema(gdf)

    out = gdf.copy()

    # ── 3B: vintage resolution ────────────────────────────────────────────────
    vintage_series, nan_vintage_rows, vintage_prov = resolve_vintage(out)

    # ── 3C: envelope merge ────────────────────────────────────────────────────
    real_mask = out["archetype_id"] != "OpenUBEMUnknown"
    unk_mask = ~real_mask

    env_real = pd.DataFrame(index=out.index)
    if real_mask.any():
        env_real = get_construction_set(
            out.loc[real_mask],
            vintage_series.loc[real_mask],
            custom_table=construction_table,
            rng=rng,
        )
        env_real = apply_nan_vintage_provenance(env_real, nan_vintage_rows.intersection(out.index[real_mask]))

    env_unk = _build_unknown_envelope(out, unk_mask, construction_table, rng)

    # Combine envelope
    if real_mask.any() and unk_mask.any():
        env_df = pd.concat([env_real, env_unk]).reindex(out.index)
    elif real_mask.any():
        env_df = env_real
    else:
        env_df = env_unk

    # ── 3B flag append ────────────────────────────────────────────────────────
    out = append_vintage_donor_flags(out, vintage_prov)

    # ── 3D: loads merge ───────────────────────────────────────────────────────
    loads_real = pd.DataFrame(index=out.index)
    if real_mask.any():
        # Temporarily sub gdf for loads merge (needs archetype_id)
        loads_real = get_loads(out.loc[real_mask], custom_table=loads_table)

    loads_unk = _build_unknown_loads(out, unk_mask, loads_real if real_mask.any() else _get_cross_archetype_loads(), rng)

    if real_mask.any() and unk_mask.any():
        loads_df = pd.concat([loads_real, loads_unk]).reindex(out.index)
    elif real_mask.any():
        loads_df = loads_real
    else:
        loads_df = loads_unk

    # ── 3E: probabilistic perturbation (F14) ─────────────────────────────────
    # Use KDE fitted on the deterministic values to generate new samples (bounded).
    if load_mode == "probabilistic":
        for col in ["lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person"]:
            # Perturb real rows only (Unknown already PDE-generated)
            perturb_mask = real_mask
            lo, hi = _PLAUS[col]
            # Tighten upper bound for equipment to non-DataCenter ceiling on non-DC rows
            dc_archs = {
                "LargeDataCenterHighITE", "LargeDataCenterLowITE",
                "SmallDataCenterHighITE", "SmallDataCenterLowITE",
            }
            observed = loads_df.loc[perturb_mask, col].astype(float).values
            if len(observed) > 0:
                from scipy.stats import gaussian_kde
                std = float(np.std(observed))
                if std < 1e-9:
                    # Degenerate case: all values identical — perturb with 5% Gaussian noise
                    noise = rng.normal(0, max(abs(observed.mean()) * 0.05, 0.01), size=len(observed))
                    samples = observed + noise
                else:
                    kde = gaussian_kde(observed, bw_method="scott")
                    n = len(observed)
                    samples = kde.resample(n, seed=rng)[0]
                # Clip: for non-DC archetypes use [lo, 100]; DC use [lo, hi]
                for i, idx in enumerate(out.index[perturb_mask]):
                    arch_i = out.at[idx, "archetype_id"]
                    col_hi = hi if arch_i in dc_archs else (100.0 if col == "equipment_w_m2" else hi)
                    samples[i] = float(np.clip(samples[i], lo, col_hi))
                loads_df.loc[perturb_mask, col] = samples

    # ── 3F: schedule library ──────────────────────────────────────────────────
    unique_archs = out["archetype_id"].unique()
    schedule_lib: dict = {}
    for arch in unique_archs:
        schedule_lib[arch] = build_schedule_library(arch, custom_table=schedules_table)

    # ── 3G: assemble 57-column output in F17 order ────────────────────────────
    # Append 28 columns in fixed F17 order
    for col in _F17_ENVELOPE_COLS:
        out[col] = env_df[col]

    for col in _F17_LOADS_COLS:
        out[col] = loads_df[col]

    # Cast categorical columns
    out["vintage_standard"] = pd.Categorical(
        out["vintage_standard"],
        categories=[
            "DOERefPre1980", "DOERef1980to2004", "90.1-2007",
            "90.1-2010", "90.1-2013", "90.1-2016", "90.1-2019",
        ],
    )

    # ── 3G: validate_schema gate ──────────────────────────────────────────────
    validate_schema(out)

    # ── 3G: emit artifacts ────────────────────────────────────────────────────
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        out.to_file(
            str(output_dir / "02b_buildings_enriched.gpkg"),
            layer="buildings",
            driver="GPKG",
        )
        _write_schema_json(out, output_dir)

        # Persist schedule library
        (output_dir / "02b_schedule_library.json").write_text(
            json.dumps(schedule_lib, indent=2),
            encoding="utf-8",
        )

    return out, schedule_lib


def _get_cross_archetype_loads() -> pd.DataFrame:
    """Load full loads table for PDE bounds when all rows are Unknown."""
    from openubem.semantic.loads import _get_flat_loads
    return _get_flat_loads()
