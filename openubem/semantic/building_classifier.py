"""Step 2 — OSM building → OpenStudio 30-type archetype classifier.
Implements DESIGN §3A–§3F (sub-stages) and §4 (output schema + row-level guarantees)
with Pass-2 amendments (DESIGN §11, 2026-05-06).
Public surface: BuildingClassifier class + classify_building per-row helper.
"""

import json
import logging
import re
from importlib.resources import files
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.acquisition.osm_fetcher import _SCHEMA_COLUMNS

logger = logging.getLogger("openubem.semantic")

# ── module-level data ──────────────────────────────────────────────────────────

_RAW_OSM_MAP: dict = json.loads(
    files("openubem.data").joinpath("osm_to_use_class.json").read_text(encoding="utf-8")
)
_TAG_TO_UC: dict[str, str] = _RAW_OSM_MAP["tag_to_use_class"]

_RAW_ARCHETYPES: dict = json.loads(
    files("openubem.data").joinpath("openstudio_archetypes.json").read_text(encoding="utf-8")
)
_VALID_30: frozenset[str] = frozenset(
    a["archetype_id"] for a in _RAW_ARCHETYPES["archetypes"]
)

# 16 emit-side tokens; FALLBACK_DEFAULT / HEURISTIC_DEFAULT are deprecated read-side only
# (Pass-2 §11 line 468; HEURISTIC_DEFAULT superseded by GROUPMEDIAN_LEVELS_MED /
# LEVELS_DEFAULT_LOW at T05 wave-2b — old archives may still carry it)
_EMIT_TOKENS: frozenset[str] = frozenset({
    "RULE_HIGHRISE", "RULE_RESIDENTIAL_TIER", "RULE_LODGING_TIER",
    "RULE_FUNCTION_TAG", "RULE_FUNCTION_TAG_SIZE",
    "RULE_USE_CLASS", "RULE_USE_CLASS_SIZE",
    "MIXED_USE_DOMINANT_TAG", "FALLBACK_UNKNOWN", "FALLBACK_SIZE_DEFAULT",
    "HEURISTIC_HEIGHT", "GROUPMEDIAN_LEVELS_MED", "LEVELS_DEFAULT_LOW",
    "ASSUMPTION_DOE_PROTOTYPE_DERIVED", "DETAILED_OFFICE",
    "OVERRIDE_USER",
})
_READ_SIDE_TOKENS: frozenset[str] = _EMIT_TOKENS | {"FALLBACK_DEFAULT", "HEURISTIC_DEFAULT"}
_OVERRIDE_USER_RE = re.compile(r"^OVERRIDE_USER\(.*\)$")

_DETAILED_MAP: dict[str, str] = {
    "SmallOffice": "SmallOfficeDetailed",
    "MediumOffice": "MediumOfficeDetailed",
    "LargeOffice": "LargeOfficeDetailed",
}

# Rules whose condition reads levels_imputed (determines whether HEURISTIC_* is appended)
_LEVELS_CONSUMING: frozenset[str] = frozenset({
    "RULE_HIGHRISE", "RULE_RESIDENTIAL_TIER", "RULE_LODGING_TIER",
})

_INPUT_SCHEMA_COLUMNS: list[str] = list(_SCHEMA_COLUMNS)
_OUTPUT_SCHEMA_COLUMNS: list[str] = _INPUT_SCHEMA_COLUMNS + [
    "archetype_id", "archetype_confidence", "archetype_source",
]

# provenance_role for the 23 upstream columns (used by _write_schema_json)
_UPSTREAM_ROLES: dict[str, str] = {
    "geometry": "geometry", "osm_id": "identity", "crs_utm": "identity",
    "building_tag": "raw_osm", "function_tag": "raw_osm", "levels": "raw_osm",
    "height_m": "raw_osm", "year_built": "raw_osm", "postcode": "raw_osm",
    "underground": "raw_osm", "roof_shape": "raw_osm", "roof_height_m": "raw_osm",
    "footprint_area_m2": "computed", "perimeter_m": "computed",
    "surplus_tags": "surplus",
    "provenance_levels": "provenance", "provenance_height_m": "provenance",
    "provenance_year_built": "provenance", "provenance_building_tag": "provenance",
    "provenance_function_tag": "provenance", "provenance_postcode": "provenance",
    "provenance_geometry": "provenance",
    "data_quality_flag": "quality",
}


class SchemaError(ValueError):
    pass


# ── internal helpers ───────────────────────────────────────────────────────────

def _to_str(val) -> str:
    if val is None:
        return ""
    try:
        if pd.isna(val):
            return ""
    except TypeError:
        pass
    return str(val)


# ── Stage 3A: use-class normalisation (DESIGN §3A, Pass-2 §11 line 463) ───────

def _normalise_use_class(
    row: pd.Series,
    dominant_tag_threshold: float = 0.60,
) -> tuple[str, float]:
    ft = _to_str(row.get("function_tag", ""))
    bt = _to_str(row.get("building_tag", ""))

    uc_fn = _TAG_TO_UC.get(ft) if ft else None
    uc_bt = _TAG_TO_UC.get(bt) if (bt and bt != "yes") else None

    if uc_fn is not None and uc_bt is not None:
        if uc_fn == uc_bt:
            return uc_fn, 1.0
        return "mixed", 0.5
    if uc_fn is not None:
        return uc_fn, 1.0
    if uc_bt is not None:
        return uc_bt, 1.0
    return "unknown", 0.0


# ── Stage 3D helper: levels imputation (DESIGN §3D lines 238-253) ─────────────

def _impute_levels(
    row: pd.Series,
    floor_to_floor_m: float = 3.5,
    *,
    use_class: "str | None" = None,
    levels_group_median: "dict[str, int] | None" = None,
    levels_global_median: "int | None" = None,
) -> tuple[int, str]:
    if pd.notna(row["levels"]):
        return int(row["levels"]), "OSM_OBSERVED"
    h = row["height_m"]
    if pd.notna(h) and h > 0:
        return max(1, int(h // floor_to_floor_m)), "HEURISTIC_HEIGHT"
    # T05 wave-2b: group-wise stratified median (observed-levels rows only, no leakage)
    # replaces the flat HEURISTIC_DEFAULT→1 fill (M03 Table 4 / Part C).
    if levels_group_median and use_class in levels_group_median:
        return levels_group_median[use_class], "GROUPMEDIAN_LEVELS_MED"
    if levels_global_median is not None:
        return levels_global_median, "GROUPMEDIAN_LEVELS_MED"
    return 1, "LEVELS_DEFAULT_LOW"


# E-R3-3: office size-tier bins (LBNL CBES 25,000 / 100,000 ft²; Hong et al. 2015)
_OFFICE_SMALL_MAX_M2 = 2322.0
_OFFICE_MEDIUM_MAX_M2 = 9290.0

# E-R3-3: hotel tier boundary (Deru et al. 2011: SmallHotel 4-story / LargeHotel 6-story)
_HOTEL_LARGE_MIN_LEVELS = 5

# E-R3-3: school tier boundary (Deru et al. 2011: Primary 1-story / Secondary 2-story)
_SECONDARY_SCHOOL_MIN_LEVELS = 2


def _office_size_tier(total_floor_area_m2: float) -> str:
    if total_floor_area_m2 < _OFFICE_SMALL_MAX_M2:
        return "SmallOffice"
    if total_floor_area_m2 < _OFFICE_MEDIUM_MAX_M2:
        return "MediumOffice"
    return "LargeOffice"


# ── Stage 3C: 17-rule classifier (DESIGN §3C + Pass-2 §11 line 465) ───────────

def _apply_rule_table(
    row: pd.Series,
    levels_imputed: int,
    use_class: str,
    dominant_tag_score: float,
    *,
    dominant_tag_threshold: float = 0.60,
    high_rise_levels_threshold: int = 20,
    super_tall_levels_threshold: int = 40,
) -> tuple[str, str, "str | None"]:
    """Return (archetype_id, rule_source_token, inherited_rule_token).

    inherited_rule_token is non-None only for rule 15; it carries the sub-table
    token so _assign_confidence can inherit the correct confidence tier.
    Deviation from plan's tuple[str,str]: 3rd element added for rule-15 tier
    inheritance (DESIGN §11 line 466 requires it; plan §4 fact #14).
    """
    ft = _to_str(row.get("function_tag", ""))
    bt = _to_str(row.get("building_tag", ""))
    area = float(_to_str(row.get("footprint_area_m2", 0)) or 0)
    # E-R3-1: office size metric is total floor area (footprint × levels)
    total_floor_area_m2 = area * max(levels_imputed, 1)

    # 1a — SuperTallBuilding
    if (
        levels_imputed >= super_tall_levels_threshold
        and use_class in {"commercial", "institutional", "mixed", "unknown"}
    ):
        return "SuperTallBuilding", "RULE_HIGHRISE", None

    # 1b — TallBuilding
    if (
        high_rise_levels_threshold <= levels_imputed < super_tall_levels_threshold
        and use_class in {"commercial", "institutional", "mixed", "unknown"}
    ):
        return "TallBuilding", "RULE_HIGHRISE", None

    # 2a — HighriseApartment
    if use_class == "residential" and levels_imputed >= 9:
        return "HighriseApartment", "RULE_RESIDENTIAL_TIER", None

    # 2b — MidriseApartment
    if use_class == "residential" and levels_imputed < 9:
        return "MidriseApartment", "RULE_RESIDENTIAL_TIER", None

    # 3a — LargeHotel
    if ft in {"hotel", "motel", "guest_house"} and levels_imputed >= _HOTEL_LARGE_MIN_LEVELS:
        return "LargeHotel", "RULE_LODGING_TIER", None

    # 3b — SmallHotel
    if ft in {"hotel", "motel", "guest_house"} and levels_imputed < _HOTEL_LARGE_MIN_LEVELS:
        return "SmallHotel", "RULE_LODGING_TIER", None

    # 4a — FullServiceRestaurant
    if ft == "restaurant":
        return "FullServiceRestaurant", "RULE_FUNCTION_TAG", None

    # 4b — QuickServiceRestaurant
    if ft in {"fast_food", "cafe", "bar", "pub"}:
        return "QuickServiceRestaurant", "RULE_FUNCTION_TAG", None

    # 5a — Hospital
    if ft == "hospital" or bt == "hospital":
        return "Hospital", "RULE_FUNCTION_TAG", None

    # 5b — Outpatient
    if ft in {"clinic", "doctors", "dentist"} or bt == "clinic":
        return "Outpatient", "RULE_FUNCTION_TAG", None

    # 6a — College
    if ft in {"university", "college"} or bt in {"university", "college"}:
        return "College", "RULE_FUNCTION_TAG", None

    # 6b — SecondarySchool (composite token: RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED)
    if (ft == "school" or bt == "school") and levels_imputed >= _SECONDARY_SCHOOL_MIN_LEVELS:
        return "SecondarySchool", "RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED", None

    # 6c — PrimarySchool (catch-all: any remaining school/kindergarten tag)
    if ft in {"school", "kindergarten"} or bt in {"school", "kindergarten"}:
        return "PrimarySchool", "RULE_FUNCTION_TAG", None

    # 7 — Courthouse (civic / government)
    if (
        ft in {"government", "public", "courthouse", "civic"}
        or bt in {"government", "public", "courthouse", "civic"}
    ):
        return "Courthouse", "RULE_FUNCTION_TAG", None

    # 8 — Laboratory
    if ft in {"laboratory", "research"} or bt in {"laboratory", "research"}:
        return "Laboratory", "RULE_FUNCTION_TAG", None

    # 9a — SmallDataCenterHighITE
    if (
        (ft in {"data_center", "datacenter"} or bt in {"data_center", "datacenter"})
        and area < 500
    ):
        return "SmallDataCenterHighITE", "RULE_FUNCTION_TAG_SIZE", None

    # 9b — LargeDataCenterHighITE (only reached when area >= 500)
    if (
        (ft in {"data_center", "datacenter"} or bt in {"data_center", "datacenter"})
        and area >= 500
    ):
        return "LargeDataCenterHighITE", "RULE_FUNCTION_TAG_SIZE", None

    # 10 — Warehouse (specific industrial tag)
    if (
        ft in {"warehouse", "industrial", "manufacture", "factory", "hangar"}
        or bt in {"warehouse", "industrial", "manufacture", "factory", "hangar"}
    ):
        return "Warehouse", "RULE_FUNCTION_TAG", None

    # 11a — SuperMarket
    if bt == "supermarket" or ft == "supermarket":
        return "SuperMarket", "RULE_FUNCTION_TAG", None

    # 11b — RetailStripmall
    if bt == "strip_mall" or ft == "strip_mall":
        return "RetailStripmall", "RULE_FUNCTION_TAG", None

    # 11c — RetailStandalone
    if (
        ft in {"retail", "shop", "mall", "kiosk"}
        or bt in {"retail", "shop", "mall", "kiosk"}
    ):
        return "RetailStandalone", "RULE_FUNCTION_TAG", None

    # 12a/12b/12c — Office by use_class + size (E-R3-1: total floor area; E-R3-3: bins)
    if use_class == "commercial":
        return _office_size_tier(total_floor_area_m2), "RULE_USE_CLASS_SIZE", None

    # 13 — Warehouse (industrial use_class, no specific tag matched above)
    if use_class == "industrial":
        return "Warehouse", "RULE_USE_CLASS", None

    # 14 — Courthouse (institutional use_class, no specific tag matched above)
    if use_class == "institutional":
        return "Courthouse", "RULE_USE_CLASS", None

    # 15 — MIXED_USE_DOMINANT_TAG: dominant-tag routing (Pass-2 §11 line 465)
    if use_class == "mixed" and dominant_tag_score >= dominant_tag_threshold:
        uc_fn = _TAG_TO_UC.get(ft) if ft else None
        uc_bt = _TAG_TO_UC.get(bt) if (bt and bt != "yes") else None
        dominant_class = (
            uc_fn if uc_fn is not None
            else (uc_bt if uc_bt is not None else "unknown")
        )
        # Recursive sub-evaluation with dominant class; score=0.0 prevents re-entry
        aid, inh_tok, _ = _apply_rule_table(
            row, levels_imputed, dominant_class, 0.0,
            dominant_tag_threshold=dominant_tag_threshold,
            high_rise_levels_threshold=high_rise_levels_threshold,
            super_tall_levels_threshold=super_tall_levels_threshold,
        )
        return aid, "MIXED_USE_DOMINANT_TAG", inh_tok

    # 16 — MIXED_USE_DOMINANT_TAG no-dominant fallback → MidriseApartment (Pass-2)
    if use_class == "mixed":
        return "MidriseApartment", "MIXED_USE_DOMINANT_TAG", None

    # 17a — E-R3-2: untagged building=yes → size-bucketed office default (LOW confidence)
    if use_class == "unknown" and bt == "yes":
        return _office_size_tier(total_floor_area_m2), "FALLBACK_SIZE_DEFAULT", None

    # 17 — FALLBACK_UNKNOWN (Pass-2: OpenUBEMUnknown, not MediumOffice)
    return "OpenUBEMUnknown", "FALLBACK_UNKNOWN", None


# ── Stage 3D: confidence scoring (DESIGN §3D lines 228-232, Pass-2 §11 line 466) ──

def _assign_confidence(
    row: pd.Series,
    rule_token: str,
    levels_source: str,
    use_class: str,
    *,
    inherited_rule_tier: "str | None" = None,
) -> str:
    head = rule_token.split(",")[0]

    # Rule 15 tier inheritance — no silent inflation (Pass-2 §11 line 466)
    if head == "MIXED_USE_DOMINANT_TAG" and inherited_rule_tier is not None:
        return inherited_rule_tier

    # Rule 16 no-dominant fallback → MEDIUM (Pass-2)
    if head == "MIXED_USE_DOMINANT_TAG":
        return "MEDIUM"

    # Rule 17 / 17a → LOW
    if head in {"FALLBACK_UNKNOWN", "FALLBACK_SIZE_DEFAULT"}:
        return "LOW"

    ft = _to_str(row.get("function_tag", ""))
    pbt = _to_str(row.get("provenance_building_tag", ""))
    dqf = _to_str(row.get("data_quality_flag", ""))
    ft_empty = ft == ""

    # LOW: generic building tag with no function tag
    if pbt == "OSM_GENERIC" and ft_empty:
        return "LOW"
    if "generic_tag" in dqf.split(",") and ft_empty:
        return "LOW"

    # MEDIUM: use_class + size only (no specific function tag)
    if head == "RULE_USE_CLASS_SIZE":
        return "MEDIUM"

    # MEDIUM: levels-consuming rule fired on imputed levels (explicitly includes 1a/1b)
    if levels_source != "OSM_OBSERVED" and head in _LEVELS_CONSUMING:
        return "MEDIUM"

    # HIGH(b) wins: rules 1a/1b/2a/2b with observed building_tag + observed levels (R6)
    _HIGH_B_RULES: frozenset[str] = frozenset({"RULE_HIGHRISE", "RULE_RESIDENTIAL_TIER"})
    if head in _HIGH_B_RULES and pbt == "OSM_OBSERVED" and levels_source == "OSM_OBSERVED":
        return "HIGH"

    # MEDIUM: function tag missing, building tag observed and specific
    pfn = _to_str(row.get("provenance_function_tag", ""))
    if pfn == "OSM_MISSING" and pbt == "OSM_OBSERVED" and head != "FALLBACK_UNKNOWN":
        return "MEDIUM"

    return "HIGH"


# ── Stage 3E: detailed_office post-processing (NEW Pass-2 §11 line 467) ────────

def _apply_detailed_office(
    archetype_id: str,
    archetype_source: str,
    *,
    detailed_office: bool,
) -> tuple[str, str]:
    if not detailed_office or archetype_id not in _DETAILED_MAP:
        return archetype_id, archetype_source
    return _DETAILED_MAP[archetype_id], f"{archetype_source},DETAILED_OFFICE"


# ── Stage 3F: per-row override merge (NEW Pass-2 §11 lines 468, 482) ───────────

def _apply_overrides(
    gdf: gpd.GeoDataFrame,
    overrides_path: "Path | None",
) -> gpd.GeoDataFrame:
    if overrides_path is None:
        return gdf
    p = Path(overrides_path)
    if not p.exists():
        logger.info("overrides_path %s not found; skipping override merge", p)
        return gdf

    ov = pd.read_csv(p, dtype=str).fillna({"note": ""})
    if "note" not in ov.columns:
        ov["note"] = ""

    for aid in ov["archetype_id"].unique():
        if aid not in _VALID_30:
            raise SchemaError(f"override archetype_id {aid!r} not in 30-element vocab")
    if ov["osm_id"].duplicated().any():
        raise SchemaError("duplicate osm_id in override CSV")

    aid_map = ov.set_index("osm_id")["archetype_id"].to_dict()
    note_map = ov.set_index("osm_id")["note"].to_dict()

    gdf = gdf.copy()
    for idx in gdf.index:
        osm_id = str(gdf.at[idx, "osm_id"])
        if osm_id in aid_map:
            gdf.at[idx, "archetype_id"] = aid_map[osm_id]
            gdf.at[idx, "archetype_confidence"] = "HIGH"
            gdf.at[idx, "archetype_source"] = f"OVERRIDE_USER({note_map.get(osm_id, '')})"
    return gdf


# ── Schema validators (DESIGN §3F line 278, plan T11) ──────────────────────────

_LOAD_BEARING_DTYPES: dict[str, str] = {
    "levels": "Int64",
    "footprint_area_m2": "float64",
    "height_m": "float64",
}


def _validate_input_schema(gdf: gpd.GeoDataFrame) -> None:
    cols = list(gdf.columns)
    if len(cols) != 23:
        raise SchemaError(f"expected 23 columns, got {len(cols)}: {cols}")
    if cols != _INPUT_SCHEMA_COLUMNS:
        first_bad = next((c for c, e in zip(cols, _INPUT_SCHEMA_COLUMNS) if c != e), cols[-1])
        raise SchemaError(f"input column order mismatch; first offending: {first_bad!r}")

    # E3: dtype assertions for load-bearing columns (DESIGN §3F line 278, W2.7)
    for col, expected in _LOAD_BEARING_DTYPES.items():
        actual = str(gdf[col].dtype)
        if actual != expected:
            raise ValueError(
                f"column {col!r} dtype mismatch: expected {expected!r}, got {actual!r}"
            )

    # geometry column checked separately (any geometry dtype is valid)
    if not hasattr(gdf[cols[0]], "geom_type"):
        raise SchemaError("column 'geometry' must be a geometry column")


def _validate_output_schema(gdf: gpd.GeoDataFrame) -> None:
    cols = list(gdf.columns)
    if len(cols) != 26:
        raise SchemaError(f"expected 26 columns, got {len(cols)}")
    if cols != _OUTPUT_SCHEMA_COLUMNS:
        raise SchemaError(f"output column order mismatch: {cols}")

    bad_aid = gdf.loc[~gdf["archetype_id"].isin(_VALID_30), "archetype_id"]
    if not bad_aid.empty:
        raise SchemaError(
            f"invalid archetype_id {bad_aid.iloc[0]!r} at row {bad_aid.index[0]}"
        )

    bad_conf = gdf.loc[~gdf["archetype_confidence"].isin({"HIGH", "MEDIUM", "LOW"}), "archetype_confidence"]
    if not bad_conf.empty:
        raise SchemaError(
            f"invalid archetype_confidence {bad_conf.iloc[0]!r} at row {bad_conf.index[0]}"
        )

    for idx, src in gdf["archetype_source"].items():
        src_str = str(src)
        if _OVERRIDE_USER_RE.match(src_str):
            continue
        for tok in src_str.split(","):
            tok = tok.strip()
            if tok not in _READ_SIDE_TOKENS and not _OVERRIDE_USER_RE.match(tok):
                raise SchemaError(f"invalid archetype_source token {tok!r} at row {idx}")

    # Row-level guarantee #6 (Pass-2 §11 line 469)
    for idx, row_data in gdf[gdf["archetype_id"] == "OpenUBEMUnknown"].iterrows():
        src = str(row_data["archetype_source"])
        conf = row_data["archetype_confidence"]
        ok_fallback = conf == "LOW" and "FALLBACK_UNKNOWN" in src.split(",")
        ok_override = bool(_OVERRIDE_USER_RE.match(src))
        if not ok_fallback and not ok_override:
            raise SchemaError(
                f"OpenUBEMUnknown at row {idx} must have LOW+FALLBACK_UNKNOWN or "
                f"OVERRIDE_USER(...); got conf={conf!r} source={src!r}"
            )


# ── Per-row helper (DESIGN §3 line 84, plan T10) ───────────────────────────────

def classify_building(
    row: pd.Series,
    *,
    detailed_office: bool = False,
    dominant_tag_threshold: float = 0.60,
    high_rise_levels_threshold: int = 20,
    super_tall_levels_threshold: int = 40,
    floor_to_floor_m: float = 3.5,
    levels_group_median: "dict[str, int] | None" = None,
    levels_global_median: "int | None" = None,
) -> tuple[str, str, str]:
    uc, score = _normalise_use_class(row, dominant_tag_threshold=dominant_tag_threshold)
    lev, lev_src = _impute_levels(
        row,
        floor_to_floor_m=floor_to_floor_m,
        use_class=uc,
        levels_group_median=levels_group_median,
        levels_global_median=levels_global_median,
    )

    aid, src_tok, inh_tok = _apply_rule_table(
        row, lev, uc, score,
        dominant_tag_threshold=dominant_tag_threshold,
        high_rise_levels_threshold=high_rise_levels_threshold,
        super_tall_levels_threshold=super_tall_levels_threshold,
    )

    head = src_tok.split(",")[0]

    # Compute inherited_rule_tier for rule 15 (no silent inflation, Pass-2 §11 line 466)
    inherited_rule_tier: "str | None" = None
    if head == "MIXED_USE_DOMINANT_TAG" and inh_tok is not None:
        inh_head = inh_tok.split(",")[0]
        inherited_rule_tier = _assign_confidence(row, inh_head, lev_src, uc)

    conf = _assign_confidence(
        row, head, lev_src, uc, inherited_rule_tier=inherited_rule_tier
    )

    # Token assembly (plan §4 fact #25): rule-token → HEURISTIC_* → [ASSUMPTION_* already in src_tok]
    # src_tok may already be composite for rule 6b ("RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED")
    parts = [src_tok]
    if head in _LEVELS_CONSUMING and lev_src != "OSM_OBSERVED":
        parts.append(lev_src)
    elif head == "MIXED_USE_DOMINANT_TAG" and inh_tok is not None:
        inh_head = inh_tok.split(",")[0]
        if inh_head in _LEVELS_CONSUMING and lev_src != "OSM_OBSERVED":
            parts.append(lev_src)

    archetype_source = ",".join(parts)

    # §3E: detailed_office post-processing
    aid, archetype_source = _apply_detailed_office(
        aid, archetype_source, detailed_office=detailed_office
    )

    return aid, conf, archetype_source


# ── BuildingClassifier (plan T10, Pass-2 §11 lines 467, 480) ──────────────────

class BuildingClassifier:
    def __init__(
        self,
        detailed_office: bool = False,
        overrides_path: "Path | None" = None,
        dominant_tag_threshold: float = 0.60,
        high_rise_levels_threshold: int = 20,
        super_tall_levels_threshold: int = 40,
        floor_to_floor_m: float = 3.5,
    ) -> None:
        self.detailed_office = detailed_office
        self.overrides_path = Path(overrides_path) if overrides_path is not None else None
        self.dominant_tag_threshold = dominant_tag_threshold
        self.high_rise_levels_threshold = high_rise_levels_threshold
        self.super_tall_levels_threshold = super_tall_levels_threshold
        self.floor_to_floor_m = floor_to_floor_m

    def classify(
        self,
        gdf: gpd.GeoDataFrame,
        output_dir: "Path | None" = None,
    ) -> gpd.GeoDataFrame:
        input_gdf = gdf
        _validate_input_schema(input_gdf)

        # E4: guard empty GDF before apply (0-row expand crashes with KeyError)
        if len(gdf) == 0:
            out = gdf.copy()
            out["archetype_id"] = pd.Series(dtype="object")
            out["archetype_confidence"] = pd.Series(dtype="object")
            out["archetype_source"] = pd.Series(dtype="object")
            return out

        out = gdf.copy()

        # T05 wave-2b: use_class -> median(levels) lookup, fit on OBSERVED-levels rows
        # only (no leakage) so the third _impute_levels branch stratifies instead of
        # flat-defaulting to 1 (M03 Table 4 / Part C).
        levels_group_median, levels_global_median = self._build_levels_median_lookup(out)

        results = out.apply(
            lambda row: classify_building(
                row,
                detailed_office=self.detailed_office,
                dominant_tag_threshold=self.dominant_tag_threshold,
                high_rise_levels_threshold=self.high_rise_levels_threshold,
                super_tall_levels_threshold=self.super_tall_levels_threshold,
                floor_to_floor_m=self.floor_to_floor_m,
                levels_group_median=levels_group_median,
                levels_global_median=levels_global_median,
            ),
            axis=1,
            result_type="expand",
        )
        out["archetype_id"] = results[0]
        out["archetype_confidence"] = results[1]
        out["archetype_source"] = results[2]

        # §3F: override merge — after classification + detailed_office, before validation
        out = _apply_overrides(out, self.overrides_path)

        # Byte-equality invariant: upstream 23 cols must be identical (DESIGN §4 line 302)
        pd.testing.assert_frame_equal(
            input_gdf.reset_index(drop=True),
            out[input_gdf.columns].reset_index(drop=True),
        )

        _validate_output_schema(out)

        # all_fallback_archetype warning: all rows on a FALLBACK-source path (E-R3-2)
        if len(out) > 0:
            fallback_mask = out["archetype_source"].str.startswith(
                ("FALLBACK_UNKNOWN", "FALLBACK_SIZE_DEFAULT")
            )
            if fallback_mask.all():
                logger.warning(
                    json.dumps({
                        "event": "all_fallback_archetype",
                        "n_rows": len(out),
                        "archetype_id": "OpenUBEMUnknown",
                    })
                )

        if output_dir is not None:
            # Collect summary lines for the log file (D4/W2.3): rule-fire counts, tier counts, FALLBACKs.
            log_lines = self._build_log_lines(out)
            self._serialize(out, Path(output_dir), log_lines=log_lines)

        return out

    def _build_levels_median_lookup(
        self, out: gpd.GeoDataFrame
    ) -> "tuple[dict[str, int], int | None]":
        """T05 wave-2b: use_class -> median(levels), fit on observed-levels rows only.

        No leakage: rows with missing `levels` never enter the lookup. Deterministic
        (plain median, no sampling).
        """
        observed = out[out["levels"].notna()]
        if len(observed) == 0:
            return {}, None

        obs_use_class = observed.apply(
            lambda r: _normalise_use_class(r, dominant_tag_threshold=self.dominant_tag_threshold)[0],
            axis=1,
        )
        group_medians = observed["levels"].groupby(obs_use_class).median()
        levels_group_median = {uc: max(1, round(m)) for uc, m in group_medians.items()}
        levels_global_median = max(1, round(observed["levels"].median()))
        return levels_group_median, levels_global_median

    def _build_log_lines(self, out: gpd.GeoDataFrame) -> list[str]:
        # Per-rule fire counts (first token of archetype_source).
        rule_counts: dict[str, int] = {}
        for src in out["archetype_source"]:
            tok = str(src).split(",")[0]
            rule_counts[tok] = rule_counts.get(tok, 0) + 1
        # Per-tier counts.
        tier_counts = out["archetype_confidence"].value_counts().to_dict()
        # FALLBACK osm_ids.
        fallback_ids = list(
            out.loc[out["archetype_id"] == "OpenUBEMUnknown", "osm_id"]
        )
        return [
            json.dumps({"event": "rule_fire_counts", "counts": rule_counts}),
            json.dumps({"event": "tier_counts", "counts": {str(k): int(v) for k, v in tier_counts.items()}}),
            json.dumps({"event": "FALLBACK", "osm_ids": fallback_ids, "n": len(fallback_ids)}),
        ]

    # ── serialisation (plan T12) ───────────────────────────────────────────────

    def _serialize(
        self,
        gdf: gpd.GeoDataFrame,
        output_dir: Path,
        log_lines: list[str] | None = None,
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write collected summary lines directly so the file is never 0 bytes (D4/W2.3).
        log_path = output_dir / "02_buildings_classified.log"
        lines = list(log_lines) if log_lines else []
        lines.append(json.dumps({"event": "serialize_complete", "n_rows": len(gdf)}))
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        gdf.to_file(
            output_dir / "02_buildings_classified.gpkg",
            layer="buildings",
            driver="GPKG",
        )
        self._write_schema_json(gdf, output_dir)
        self._write_distribution_csv(gdf, output_dir)

    def _write_schema_json(self, gdf: gpd.GeoDataFrame, output_dir: Path) -> None:
        entries = []
        for col in gdf.columns:
            role = _UPSTREAM_ROLES.get(col, "derived")
            if col == "archetype_source":
                role = "provenance"
            entry: dict = {"name": col, "dtype": str(gdf[col].dtype), "provenance_role": role}
            if col == "archetype_id":
                entry["vocabulary"] = sorted(_VALID_30)
            elif col == "archetype_confidence":
                entry["vocabulary"] = ["HIGH", "MEDIUM", "LOW"]
            entries.append(entry)
        (output_dir / "02_buildings_classified.schema.json").write_text(
            json.dumps({"schema_version": "1.0.0", "columns": entries}, indent=2),
            encoding="utf-8",
        )

    def _write_distribution_csv(self, gdf: gpd.GeoDataFrame, output_dir: Path) -> None:
        dist = (
            gdf.groupby("archetype_id", observed=True)
            .agg(
                n_rows=("osm_id", "count"),
                mean_floor_area_m2=("footprint_area_m2", "mean"),
                mean_levels=("levels", "mean"),
            )
            .reset_index()
        )
        dist["pct_of_total"] = dist["n_rows"] / len(gdf) * 100
        dist = dist.sort_values("n_rows", ascending=False)
        dist[
            ["archetype_id", "n_rows", "pct_of_total", "mean_floor_area_m2", "mean_levels"]
        ].to_csv(output_dir / "02_archetype_distribution.csv", index=False)
