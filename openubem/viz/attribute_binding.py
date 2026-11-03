"""Bind simulation values + provenance onto CityObjects by osm_id (T05, T06).

Values (T05) and provenance (T06) are written into the SAME
`CityObjects[osm_id].attributes` table (never a side-channel) using the raw
OpenUBEM field names verbatim (`archetype_id`, `levels`, `iod` — never renamed).

Graceful degrade is BINDING (PLAN §5 + §9 ruling 7): a provenance field whose
source column is absent from the run's artifacts is OMITTED (never defaulted,
never inferred) and reported in `provenance_coverage` (fed to T07). The pinned
phaseE pilot genuinely lacks `resolution_mode`, `archetype_confidence`/
`archetype_source`, and both imputation-lineage fields, so the absent-field path
runs live from day one.
"""

from __future__ import annotations

import math

# T05 — value columns read verbatim from 05_results.* (success rows only).
_RESULT_VALUE_COLS = (
    "footprint_area_m2", "levels", "height_m", "archetype_id",
    "heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
    "equipment_eui_kwh_m2", "fans_eui_kwh_m2", "pumps_eui_kwh_m2",
    "dhw_gas_eui_kwh_m2", "dhw_elec_eui_kwh_m2", "dhw_eui_kwh_m2",
    "cooking_eui_kwh_m2", "refrigeration_eui_kwh_m2", "total_eui_kwh_m2",
    "gwp_heating_kgco2_m2", "gwp_cooling_kgco2_m2", "gwp_lighting_kgco2_m2",
    "gwp_equipment_kgco2_m2", "gwp_fans_kgco2_m2", "gwp_pumps_kgco2_m2",
    "gwp_dhw_kgco2_m2", "gwp_cooking_kgco2_m2", "gwp_refrigeration_kgco2_m2",
    "gwp_total_kgco2_m2", "iod",
)
# year_built lives only in 01_buildings.gpkg (PLAN §5 source map).
_BUILDINGS_VALUE_COLS = ("year_built",)

# T06 — provenance fields grouped by their pinned source (PLAN §5 source map).
_PROV_FROM_MANIFEST = (
    "resolution_mode", "zoning_strategy", "num_zones", "generation_status",
    "archetype_confidence", "archetype_source",
    "mean_imputation_confidence", "imputed_fields_count",
)
_PROV_FROM_RESULTS = ("data_quality_flag",)
_PROV_FROM_BUILDINGS = (
    "provenance_levels", "provenance_height_m", "provenance_year_built",
    "provenance_building_tag", "provenance_function_tag",
    "provenance_postcode", "provenance_geometry",
)

_ARCHETYPE_CONFIDENCE_RANK = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.1}


def _is_missing(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return False


def _clean(v):
    """Coerce a cell to a JSON-safe scalar (numpy -> python)."""
    if hasattr(v, "item"):
        v = v.item()
    return v


def _index_by_osm(df):
    return {str(r.osm_id): r for r in df.itertuples(index=False)}


def bind_values(cityjson, results_df, buildings_gdf) -> None:
    """T05: bind EUI / carbon / IOD / building attributes onto CityObjects.

    Buildings absent from `results_df` (never simulated) get NO value keys and
    are NOT dropped (T05 test c).
    """
    results = _index_by_osm(results_df)
    buildings = _index_by_osm(buildings_gdf)

    for osm_id, co in cityjson["CityObjects"].items():
        attrs = co.setdefault("attributes", {})
        r = results.get(osm_id)
        if r is not None:
            for col in _RESULT_VALUE_COLS:
                if hasattr(r, col):
                    v = _clean(getattr(r, col))
                    if not _is_missing(v):
                        attrs[col] = v
        b = buildings.get(osm_id)
        if b is not None:
            for col in _BUILDINGS_VALUE_COLS:
                if hasattr(b, col):
                    v = _clean(getattr(b, col))
                    if not _is_missing(v):
                        attrs[col] = v


def _coverage(present_cols, df_or_none, fields):
    """Split `fields` into present/absent by whether their column exists."""
    cols = set(df_or_none.columns) if df_or_none is not None else set()
    present, absent = [], []
    for f in fields:
        (present if f in cols else absent).append(f)
    present_cols.update(present)
    return present, absent


def bind_provenance(cityjson, manifest_df, results_df, buildings_gdf) -> dict:
    """T06: bind provenance fields + derived trust_confidence; return coverage.

    Returns:
        provenance_coverage = {"present": sorted[...], "absent": sorted[...]}
        over the run-level (column-exists) availability of every provenance
        field, for the T07 metadata block + T12 "not recorded" badges.
    """
    manifest = _index_by_osm(manifest_df)
    results = _index_by_osm(results_df)
    buildings = _index_by_osm(buildings_gdf)

    present: set[str] = set()
    p_man, a_man = _coverage(present, manifest_df, _PROV_FROM_MANIFEST)
    p_res, a_res = _coverage(present, results_df, _PROV_FROM_RESULTS)
    p_bld, a_bld = _coverage(present, buildings_gdf, _PROV_FROM_BUILDINGS)
    absent = a_man + a_res + a_bld

    imp_available = "mean_imputation_confidence" in set(present)
    arch_available = "archetype_confidence" in set(present)
    trust_computed_any = False

    for osm_id, co in cityjson["CityObjects"].items():
        attrs = co.setdefault("attributes", {})
        m = manifest.get(osm_id)
        r = results.get(osm_id)
        b = buildings.get(osm_id)

        for col in p_man:
            if m is not None and hasattr(m, col):
                v = _clean(getattr(m, col))
                if not _is_missing(v):
                    attrs[col] = v
        for col in p_res:
            if r is not None and hasattr(r, col):
                v = _clean(getattr(r, col))
                if not _is_missing(v):
                    attrs[col] = v
        for col in p_bld:
            if b is not None and hasattr(b, col):
                v = _clean(getattr(b, col))
                if not _is_missing(v):
                    attrs[col] = v

        # trust_confidence = min(imputation float, rank(archetype)); both sides
        # must be present AND non-missing for THIS building, else omit entirely.
        if imp_available and arch_available and m is not None:
            imp = _clean(getattr(m, "mean_imputation_confidence", None))
            arch = _clean(getattr(m, "archetype_confidence", None))
            if not _is_missing(imp) and not _is_missing(arch):
                rank = _ARCHETYPE_CONFIDENCE_RANK.get(str(arch).upper())
                if rank is not None:
                    attrs["trust_confidence"] = min(float(imp), rank)
                    trust_computed_any = True

    coverage = {"present": sorted(present), "absent": sorted(absent)}
    coverage["trust_confidence_computable"] = bool(imp_available and arch_available)
    coverage["trust_confidence_computed_any"] = trust_computed_any
    return coverage
