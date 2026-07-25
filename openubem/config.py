import os
import tempfile
from pathlib import Path

from eppy.iddcurrent import iddcurrent as _iddcurrent


def _resolve_idd_path() -> Path:
    env_val = os.environ.get("OPENUBEM_ENERGYPLUS_IDD_PATH")
    if env_val:
        return Path(env_val)
    # Prefer the real EnergyPlus 23.1 IDD: it includes the Space Name field
    # (inserted after Zone Name in BuildingSurface:Detailed in EnergyPlus 9.6+).
    # Without it, eppy's 8.0 IDD omits that field and 23.1 parses subsequent
    # fields shifted by one position, causing fatal JSON-schema validation errors (W3.7).
    ep_idd = Path(os.environ.get("ENERGYPLUS_PATH", r"C:\EnergyPlusV23-1-0")) / "Energy+.idd"
    if ep_idd.exists():
        return ep_idd
    # Last-resort fallback: eppy's bundled IDD text (v8.0.0).
    import logging as _logging
    _logging.getLogger("openubem.config").warning(
        "EnergyPlus 23.1 IDD not found at %s; falling back to eppy bundled IDD v8.0.0 "
        "(BuildingSurface:Detailed field shift will cause fatal errors under EnergyPlus 9.6+)",
        ep_idd,
    )
    tmp = Path(tempfile.gettempdir()) / "openubem_eppy_bundled.idd"
    if not tmp.exists():
        tmp.write_text(_iddcurrent.iddtxt, encoding="utf-8")
    return tmp


ENERGYPLUS_IDD_PATH: Path = _resolve_idd_path()

SHADING_SPHERE_RADIUS: float = 30.0
DP_TOLERANCE_M: float = 0.5
DP_COARSE_TOLERANCE_M: float = 1.5
MAX_VERTICES: int = 120
FLOOR_TO_FLOOR_M: float = 3.5
PERIMETER_DEPTH_M: float = 4.57

# ── Step 2.1 climate / EPW constants (DESIGN line 28) ─────────────────────────
EPW_CACHE_DIR: Path = Path(
    os.environ.get("OPENUBEM_EPW_CACHE", str(Path.home() / ".openubem" / "epw"))
)

# ── LayoutAssigner arc T01/T08 — baseline IDF library portability ─────────────
# T08: repointed to the E+ 23.1-transitioned sibling library (plan §3.2 — the
# original 00.BaselineBuildings_NUs dir is all Version,22.1 and is left untouched).
BASELINE_IDF_DIR: Path = Path(
    os.environ.get(
        "OPENUBEM_BASELINE_IDF_DIR",
        r"C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231",
    )
)
EPW_MAX_STATION_KM: float = 300.0  # ASSUMPTION_DESIGN_DEFAULT (DESIGN line 84)
EPW_PRIMARY_MIRROR: str = "https://climate.onebuilding.org"
EPW_FALLBACK_MIRROR: str = "https://energyplus.net/weather-download"
OFFLINE: bool = False

# ── Step 2.2 semantic enrichment constants (DESIGN line 29) ───────────────────
LOAD_MODE: str = "deterministic"
RANDOM_SEED: int = 42
PDE_BOUNDS_PATH: "Path | None" = None

# ── Step 4 parallel simulation constants (DESIGN lines 26–27) ─────────────────
import sys as _sys

ENERGYPLUS_PATH: Path = Path(os.environ.get("ENERGYPLUS_PATH", r"C:\EnergyPlusV23-1-0"))
ENERGYPLUS_VERSION: str = "23.1"
SIM_TIMEOUT_S: int = 3600  # recalibrated per DESIGN line 127: 340-zone building exceeds 900s under 8-worker load
SIM_RETAIN_FILES: frozenset = frozenset({
    "eplusout.sql",
    "eplusout.csv",
    "eplusout.mtr",
    "eplusout.err",
    "eplusout.end",
    "eplustbl.htm",
    "openubem_run.log",
})
N_JOBS: int = int(os.environ.get("SLURM_CPUS_PER_TASK", 0)) or -1

# ── Step 5 results / metrics constants (DESIGN line 29) ───────────────────────
GWP_NATURAL_GAS_KGCO2_KWH: float = 0.181  # Iseri et al. (2025)
GWP_CONVENTION: str = "load_referenced_v1"
IOD_SUMMER_MONTHS: tuple[int, int] = (6, 9)  # Jun–Sep inclusive (PLAN P9)
EUI_PLAUSIBILITY_BOUNDS: tuple[float, float] = (25.0, 1000.0)  # kWh/m²/yr

# ── Phase-E reporting-layer reconstruction (T15) ──────────────────────────────
# When True, reconstruct_frame applies the Table-4 fraction-split uplift (pre-Phase-E).
# False (default in Phase-E): service loads are physically modelled; reconstruction is a no-op.
RECONSTRUCT_SERVICE_LOADS: bool = bool(int(os.environ.get("OPENUBEM_RECONSTRUCT_SERVICE_LOADS", "0")))

# ── Input-Imputation arc T07 — imputation routing config (Phase B) ────────────
# `ml` stays OUT of the default tuple until Phase C's CP-3 sign-off (below).
# `fusion` was added at E-UTCI-09 height-backfill CP-B (2026-07-25): with the
# default `FUSION_SOURCES_BY_TARGET = {}`, `_fusion_tier` is a byte-identical
# no-op (empirically re-verified on a real unaffected cell, T07(b)/plan §7) --
# safety is carried by the config, not by tier-list exclusion.
IMPUTE_STRICT_MODE: bool = False
IMPUTE_ENABLED_TIERS: tuple = ("fusion", "spatial", "statistical")

# ── Input-Imputation arc T11.3 — ML tier opt-in surface (Phase C) ─────────────
# `ml` stays OUT of IMPUTE_ENABLED_TIERS above until CP-3 passes + user
# sign-off (T11.7); reached only via ImputeConfig.per_input_tiers (opt-in).
IMPUTE_ML_METHOD_BY_TARGET: dict = {
    "year_built": "missforest",
    "levels": "missforest",
    "height": "missforest",
    "height_m": "missforest",
    "use_class": "missforest",
}
IMPUTE_ML_FLOORS: dict = {
    "missforest": 1000,
    "mice": 200,
    "knn": 200,
    "rf": 1000,
    "histgbm": 5000,
    "linear": 1000,
}

# ── Stage 6 (UTCI / outdoor microclimate) arc T01 — config block ──────────────
# PLAN docs/docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md §6/§7 T01.
UTCI_GRID_RES_M: float = float(os.environ.get("OPENUBEM_UTCI_GRID_RES_M", 2.0))
UTCI_PEDESTRIAN_HEIGHT_M: float = 1.1  # U02 Table 1 line 15 — human centre of gravity
UTCI_SVF_AZIMUTHS: int = int(os.environ.get("OPENUBEM_UTCI_SVF_AZIMUTHS", 32))  # U03 Table 2 line 27
# Shading-context radius for the microclimate domain. NOT config.SHADING_SPHERE_RADIUS (30 m,
# F-05) — that value is tuned for per-building IDF shading, far too small for a radiation domain.
UTCI_DOMAIN_BUFFER_M: float = float(os.environ.get("OPENUBEM_UTCI_DOMAIN_BUFFER_M", 200.0))
UTCI_ANALYSIS_WINDOW: str = os.environ.get("OPENUBEM_UTCI_ANALYSIS_WINDOW", "hottest_week")
UTCI_Z0_OPEN_M: float = 0.01  # COST-730 reference open-terrain roughness length (U02 §2.2 line 97)
UTCI_WIND_TIER: str = os.environ.get("OPENUBEM_UTCI_WIND_TIER", "cost730")  # | "macdonald"
UTCI_VEGETATION_TIER: str = os.environ.get("OPENUBEM_UTCI_VEGETATION_TIER", "none")  # | "osm" | "cdsm"
UTCI_WALL_TEMP_TIER: str = os.environ.get("OPENUBEM_UTCI_WALL_TEMP_TIER", "empirical")  # | "energyplus"
UTCI_RASTER_NODATA: float = -9999.0

# ── E-UTCI-09 height-backfill sub-plan T03 — fusion config surface (default-OFF) ──
# All six keys default to inert values so `fusion.precedence_for()` returns []
# and `fuse()` is a guaranteed no-op until a future task/CP explicitly wires
# real paths in -- safety is carried by these defaults, not by tier-list
# exclusion (see lines 95-98 above); adding these keys must not change any behaviour.
FUSION_SOURCES_BY_TARGET: dict = {}  # e.g. {"height_m": ("overture", "lidar", "assessor")}
FUSION_OVERTURE_SLICE_PATH: "Path | None" = (
    Path(os.environ["OPENUBEM_FUSION_OVERTURE_SLICE_PATH"])
    if os.environ.get("OPENUBEM_FUSION_OVERTURE_SLICE_PATH")
    else None
)
FUSION_OVERTURE_ENDPOINT: "str | None" = os.environ.get("OPENUBEM_FUSION_OVERTURE_ENDPOINT") or None
FUSION_LIDAR_NDSM_PATH: "Path | None" = (
    Path(os.environ["OPENUBEM_FUSION_LIDAR_NDSM_PATH"])
    if os.environ.get("OPENUBEM_FUSION_LIDAR_NDSM_PATH")
    else None
)
# Assessor keys are added for surface completeness only (F-C', plan §5 T03) --
# this plan does not configure or wire an assessor data source.
FUSION_ASSESSOR_PATH: "Path | None" = (
    Path(os.environ["OPENUBEM_FUSION_ASSESSOR_PATH"])
    if os.environ.get("OPENUBEM_FUSION_ASSESSOR_PATH")
    else None
)
FUSION_ASSESSOR_FIELDS: dict = {}
HEIGHT_CACHE_DIR: Path = Path(
    os.environ.get("OPENUBEM_HEIGHT_CACHE", str(Path.home() / ".openubem" / "heights"))
)
