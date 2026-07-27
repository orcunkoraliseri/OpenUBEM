"""LayoutAssigner: Assigns standardized baseline EnergyPlus reference models and scales floor area.

Instead of generating complex dynamic floor plans from scratch (layoutGenerator), this module
assigns pre-validated baseline IDF reference models from `00.BaselineBuildings_NUs` and scales
their floor area to match target real building dimensions.
"""

import math
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import shapely

from openubem import config

logger = logging.getLogger("openubem.geometry.layout_assigner")

# Mapping from OpenUBEM canonical archetype IDs (openubem/semantic/__init__.py
# _ARCHETYPE_VOCAB) to baseline IDF filenames. Keyed ONLY on canonical vocab
# tokens (plan §3.3) — `Courthouse`/`OpenUBEMUnknown` intentionally absent,
# no baseline exists for them (T03 handles the graceful miss).
ARCHETYPE_IDF_MAP: Dict[str, str] = {
    # Residential
    "MidriseApartment": "ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf",
    "HighriseApartment": "ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf",

    # Commercial / Institutional
    "Hospital": "ASHRAE901_Hospital_STD2022_Buffalo.idf",
    "LargeHotel": "ASHRAE901_HotelLarge_STD2022_Buffalo.idf",
    "SmallHotel": "ASHRAE901_HotelSmall_STD2022_Buffalo.idf",
    "LargeOffice": "ASHRAE901_OfficeLarge_STD2022_Buffalo.idf",
    "LargeOfficeDetailed": "ASHRAE901_OfficeLarge_STD2022_Buffalo.idf",
    "MediumOffice": "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf",
    "MediumOfficeDetailed": "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf",
    "SmallOffice": "ASHRAE901_OfficeSmall_STD2022_Buffalo.idf",
    "SmallOfficeDetailed": "ASHRAE901_OfficeSmall_STD2022_Buffalo.idf",
    "Outpatient": "ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf",

    # Education & Assembly
    "PrimarySchool": "ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf",
    "SecondarySchool": "ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled.idf",
    "College": "College_90.1-2019_6A_Buffalo_v221.idf",
    "Laboratory": "Laboratory_90.1-2019_6A_Buffalo_v221.idf",

    # Retail & Dining & Storage
    "RetailStandalone": "ASHRAE901_RetailStandalone_STD2022_Buffalo.idf",
    "RetailStripmall": "ASHRAE901_RetailStripmall_STD2022_Buffalo.idf",
    "SuperMarket": "Supermarket_V22.1.idf",
    "Warehouse": "ASHRAE901_Warehouse_STD2022_Buffalo.idf",
    "FullServiceRestaurant": "ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf",
    "QuickServiceRestaurant": "ASHRAE901_RestaurantFastFood_STD2022_Buffalo.idf",

    # Tall & Specialized
    "TallBuilding": "TallBuilding_90.1-2019_6A_Buffalo_v221.idf",
    "SuperTallBuilding": "SuperTallBuilding_90.1-2019_6A_Buffalo_v221.idf",
    "LargeDataCenterHighITE": "ASHRAE901_DataCenterLargeHighITE_STD2019.idf",
    "LargeDataCenterLowITE": "ASHRAE901_DataCenterLargeLowITE_STD2019.idf",
    "SmallDataCenterHighITE": "SmallDataCenterHighITE_90.1-2019_6A_Buffalo_v221.idf",
    "SmallDataCenterLowITE": "SmallDataCenterLowITE_90.1-2019_6A_Buffalo_v221.idf",
}

# Baseline gross floor area (m2), keyed identically to ARCHETYPE_IDF_MAP.
# *Detailed variants reuse their non-Detailed counterpart's value (same file).
# DataCenter values measured directly from the 4 baseline IDFs (sum of FLOOR-type
# BuildingSurface:Detailed areas, zone Multiplier==1 confirmed) since no prior
# per-variant figure existed (old dict had one generic "DataCenter":5000.0 for
# all 4) — reusing a single placeholder would reproduce the exact wrong-scale
# bug this task fixes (plan §3.3).
DEFAULT_BASELINE_AREAS: Dict[str, float] = {
    "MidriseApartment": 3135.0,
    "HighriseApartment": 7835.0,
    "Hospital": 22422.0,
    "LargeHotel": 11345.0,
    "SmallHotel": 4013.0,
    "LargeOffice": 46320.0,
    "LargeOfficeDetailed": 46320.0,
    "MediumOffice": 4982.0,
    "MediumOfficeDetailed": 4982.0,
    "SmallOffice": 511.0,
    "SmallOfficeDetailed": 511.0,
    "Outpatient": 3804.0,
    "PrimarySchool": 6871.0,
    "SecondarySchool": 19592.0,
    "RetailStandalone": 2294.0,
    "RetailStripmall": 2090.0,
    "SuperMarket": 4181.0,
    "Warehouse": 4835.0,
    "FullServiceRestaurant": 511.0,
    "QuickServiceRestaurant": 232.0,
    "College": 11000.0,
    "Laboratory": 8500.0,
    "TallBuilding": 25000.0,
    "SuperTallBuilding": 60000.0,
    "LargeDataCenterHighITE": 557.4,
    "LargeDataCenterLowITE": 557.4,
    "SmallDataCenterHighITE": 55.7,
    "SmallDataCenterLowITE": 55.7,
}


class BaselineIDFRegistry:
    """Registry for discovering and managing baseline IDF models."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or config.BASELINE_IDF_DIR
        self._cache: Dict[str, Path] = {}
        self._scan()

    def _scan(self):
        """Indexes available baseline IDF files in the baseline directory."""
        if not self.base_dir.exists():
            logger.warning(f"Baseline IDF directory does not exist: {self.base_dir}")
            return
        for file in self.base_dir.glob("*.idf"):
            self._cache[file.name] = file
        logger.info(f"Indexed {len(self._cache)} baseline IDF files from {self.base_dir}")

    def get_baseline_idf(self, archetype_id: str) -> Optional[Path]:
        """Finds the baseline IDF file matching an archetype ID, or None if unmapped/missing."""
        filename = ARCHETYPE_IDF_MAP.get(archetype_id)
        if filename and filename in self._cache:
            return self._cache[filename]
        return None

    def get_baseline_area(self, archetype_id: str) -> Optional[float]:
        """Returns baseline gross floor area (m2) for archetype, or None if unmapped."""
        return DEFAULT_BASELINE_AREAS.get(archetype_id)


# Lazy cached registry: no directory scan happens at module import time (plan §3.4/T01).
_registry: Optional[BaselineIDFRegistry] = None


def get_registry() -> BaselineIDFRegistry:
    """Returns the process-wide BaselineIDFRegistry, scanning config.BASELINE_IDF_DIR
    on first call only."""
    global _registry
    if _registry is None:
        _registry = BaselineIDFRegistry()
    return _registry


def calculate_scaling_factor(
    real_area_m2: float,
    baseline_area_m2: float,
    num_floors: Optional[int] = None,
    n_proto: Optional[int] = None,
    storeys_matched: bool = False,
    multiplier: Optional[int] = None,
) -> Dict[str, float]:
    """Calculates gross floor area scaling ratio and planar coordinate scale factor.

    Backward-compatible 2-arg call (num_floors/n_proto omitted or num_floors==n_proto,
    e.g. the identity case) takes the SAME code path as before this function grew a
    storey-matching mode -- byte-identical output, asserted in
    tests/test_layout_assigner.py (B02 regression guard, plan D2/B02).

    Storey-matching mode (D2, plan §5 B02 -- PLAN_storey-matching_implementation.md):
    when num_floors and n_proto are both given and differ, planar_scale_factor is
    derived from the PLATE ratio (plate_target = real_area/num_floors,
    plate_proto = baseline_area_m2/n_proto) instead of the total-area ratio, so
    matching storeys (match_storeys()) and scaling area don't double-shrink the
    plate. `baseline_area_m2` here must be A1's RECOMPUTED geometry area
    (compute_band_map()'s recomputed_area_m2 -- see
    results/a1_prototype_storey_structure.csv, recomputed_floor_area_m2), NOT the
    registry DEFAULT_BASELINE_AREAS value: the registry disagrees with the
    prototype IDFs' own geometry for 14/25 archetypes, up to +473% (E-LA-25), which
    would make plate_proto wrong before sqrt() is ever taken.

    `storeys_matched` must be True only when match_storeys() actually set a Zone
    Multiplier > 1 on this idf (status "applied"). When False (n_real == n_proto,
    or D5 fallback -- D3(b) rejected, or band structure "not expressible"),
    area_scale_ratio is pinned to the plate ratio alone rather than
    real_area/baseline_area_m2, because that raw ratio bakes in a n_real/n_proto
    storey factor that was never actually applied to the idf's Zone Multiplier
    fields. Feeding the unpinned ratio to scale_baseline_idf()'s absolute-load
    scaling in that case is exactly E-LA-27's failure mode (capacity/load fields
    scaled for a multiplier that is not in the model) -- just the fallback-population
    mirror of it, not the taller-population one A2-bis measured.

    Args:
        real_area_m2: Real building target floor area (footprint_area * num_floors)
        baseline_area_m2: Standardized prototype baseline floor area (storey-matching
            mode: A1's recomputed geometry total, not the registry -- see above).
        num_floors: Real building's storey count (n_real), or None for the old
            single-scalar call.
        n_proto: Prototype's modelled storey count (compute_band_map()'s n_proto),
            or None for the old single-scalar call.
        storeys_matched: True iff match_storeys() actually set the Zone Multiplier
            on this idf (status "applied"). Ignored unless num_floors/n_proto are
            both given and differ.
        multiplier: match_storeys()'s own "multiplier" field -- the ACTUAL integer
            Zone Multiplier value it set on the middle band, or None. Used only to
            form transformer_scale_ratio, a deliberately CONSERVATIVE UPPER BOUND
            for ElectricLoadCenter:Transformer.Rated_Capacity, not a physically
            derived whole-building load ratio -- see transformer_scale_ratio below
            and the manager's D9 ruling in PLAN_storey-matching_implementation.md
            §7 (plan §5 B06, 2026-07-26) for why a clean derivation was rejected.

    Returns:
        Dict containing area_scale_ratio, planar_scale_factor, target_area_m2,
        baseline_area_m2, transformer_scale_ratio, roof_scale_ratio.
    """
    if baseline_area_m2 <= 0:
        area_scale_ratio = 1.0
    else:
        area_scale_ratio = real_area_m2 / baseline_area_m2

    if num_floors and n_proto and num_floors != n_proto:
        plate_target = real_area_m2 / num_floors
        plate_proto = baseline_area_m2 / n_proto
        plate_ratio = plate_target / plate_proto if plate_proto > 0 else 1.0
        planar_scale_factor = math.sqrt(plate_ratio) if plate_ratio > 0 else 1.0
        if not storeys_matched:
            area_scale_ratio = plate_ratio
    else:
        # Identity case (num_floors == n_proto) and the plain 2-arg call both land
        # here -- the exact pre-storey-matching code path (B02 regression guard).
        planar_scale_factor = math.sqrt(area_scale_ratio) if area_scale_ratio > 0 else 1.0

    # D9 -- ElectricLoadCenter:Transformer.Rated_Capacity scaling (E-LA-27,
    # plan §5 B06, manager ruling 2026-07-26). THIS IS A TESTED CONSERVATIVE
    # UPPER BOUND, NOT A DERIVED WHOLE-BUILDING LOAD RATIO -- do not read
    # (planar_scale_factor**2 * multiplier) as "the" electric load growth
    # factor; it is not, and the manager's own audit of this exact number
    # found three candidate "true" ratios that all disagree for MediumOffice
    # n_real=6/n_proto=3 (multiplier=4):
    #   - whole-building conditioned-floor-area ratio, planar_area_factor x
    #     (n_real/n_proto) = 0.60214 x 2 = 1.204 -- mathematically IDENTICAL
    #     to the pre-D9/B01b area_scale_ratio mechanism already measured at
    #     134,642 Severe (E-LA-27). Confirmed disconfirmed, not merely
    #     untested: this is the exact number that failed.
    #   - measured annual electricity-energy ratio (matched/S=1 GJ,
    #     eplustbl.htm Total End Uses) = 2790.66/1720.19 = 1.622 -- untested
    #     as a transformer capacity; annual energy is also not obviously the
    #     right physical quantity for an instantaneous-overload check.
    #   - measured coincident peak electric demand ratio (Demand End Use
    #     Components Summary, Total End Uses row, matched/S=1) =
    #     295612.52/229114.06 = 1.290 W/W -- also untested, and this table's
    #     own end-use rows were verified to sum exactly to the Total row (a
    #     genuine coincident decomposition, not a sum of separate peaks), yet
    #     this facility-wide peak (295.6 kW) is itself far larger than the
    #     108.4 kVA capacity that empirically reached 0 Severe, meaning the
    #     Transformer object (PowerInFromGrid, no explicit
    #     ElectricLoadCenter:Distribution link found) does not simply see 100%
    #     of the facility's own reported peak electric demand -- the exact
    #     sub-circuit it monitors was not resolved in this task and is a real
    #     open question, not a solved one.
    # None of the three is validated as sufficient by an actual EnergyPlus
    # run; only planar_area_factor x multiplier (this formula) has been RUN
    # and reached 0 Severe (PLAN_storey-matching_implementation.md §7, B06).
    # Per rule 8 (ground truth from run artifacts, never a restatement of the
    # hypothesis) this formula ships BECAUSE it is the only one of the four
    # numbers with a passing real-EnergyPlus result behind it, not because it
    # is believed to be the physically correct load ratio. It is measurably
    # oversized relative to the annual-energy candidate (2.409 vs 1.622,
    # ~48% more nameplate than that candidate would imply) -- quantified
    # energy cost of that oversizing, from a real before/after run at fixed
    # geometry: Total Electricity end use DECREASED by 0.70 GJ (2791.36 GJ at
    # the old 1.204x/54,193 VA capacity -> 2790.66 GJ at this 2.409x/108,386
    # VA capacity), 0.025% of the annual total -- immaterial at single-
    # building scale, opposite in direction to a naive "bigger nameplate ->
    # more no-load loss" story (the transformer's NominalEfficiency
    # performance-input-method loss curve's load-dependent term apparently
    # falls faster than its no-load term rises, at least over this specific
    # capacity jump), and NOT verified at fleet scale (805 taller+transformer
    # buildings per the manager's B00-crossed census) -- forwarded as an open
    # question, not asserted closed. When storeys_matched is False (identity/
    # fallback), there is no "multiplier the model ended up with" beyond 1,
    # so transformer_scale_ratio is area_scale_ratio, unchanged from today.
    if storeys_matched and multiplier:
        transformer_scale_ratio = (planar_scale_factor ** 2) * multiplier
    else:
        transformer_scale_ratio = area_scale_ratio

    # R03 -- E-LA-32 (plan §5 REMAINder, 2026-07-26): Generator:PVWatts
    # DC_System_Capacity / ElectricLoadCenter:Generators Generator_1_Rated_
    # Electric_Power_Output track ROOF area, not whole-building floor area --
    # a Zone Multiplier repeats a middle band vertically and never touches the
    # roof (the single, never-multiplied top band). `planar_scale_factor ** 2`
    # is exactly the horizontal (X/Y) plan-area growth factor scale_baseline_idf()
    # already applies to every surface's vertices, independent of storeys_matched
    # or multiplier -- unlike transformer_scale_ratio, this one is invariant to
    # the multiplier by construction, which is the whole point (R03's own test).
    roof_scale_ratio = planar_scale_factor ** 2

    return {
        "area_scale_ratio": area_scale_ratio,
        "planar_scale_factor": planar_scale_factor,
        "target_area_m2": real_area_m2,
        "baseline_area_m2": baseline_area_m2,
        "transformer_scale_ratio": transformer_scale_ratio,
        "roof_scale_ratio": roof_scale_ratio,
    }


def assign_baseline_layout(
    osm_id: str,
    footprint_poly: shapely.Polygon,
    archetype_id: str,
    num_floors: int,
    floor_to_floor_m: float = 3.5,
) -> Dict[str, Any]:
    """Assigns standardized baseline model layout and calculates floor area scaling metadata.

    Args:
        osm_id: Real building OpenStreetMap identifier.
        footprint_poly: Real building 2D footprint polygon.
        archetype_id: Assigned archetype classification tag.
        num_floors: Number of floors of real building.
        floor_to_floor_m: Floor-to-floor height in meters.

    Returns:
        Dict representing layout assignment, zone metadata, and scaling factors.
    """
    real_area = footprint_poly.area * num_floors
    reg = get_registry()
    baseline_idf_path = reg.get_baseline_idf(archetype_id)
    baseline_area = reg.get_baseline_area(archetype_id)

    if baseline_idf_path is None or baseline_area is None:
        # No baseline exists for this archetype (e.g. Courthouse, OpenUBEMUnknown, or a
        # missing library file) — degrade gracefully, never crash (plan §3.3/T03).
        # `no_baseline=True` / `baseline_idf_filename=None` are the signal T07's builder
        # branch will consume to fall back to the standard template pipeline.
        logger.warning(
            f"No baseline available for archetype_id={archetype_id!r} (osm_id={osm_id}); "
            "returning no_baseline metadata for downstream fallback."
        )
        return {
            "name": f"{osm_id}_assigned_{archetype_id}",
            "mode": "layout_assign",
            "osm_id": osm_id,
            "archetype_id": archetype_id,
            "no_baseline": True,
            "baseline_idf_filename": None,
            "baseline_idf_path": None,
            "real_num_floors": num_floors,
            "target_floor_area_m2": real_area,
            "baseline_floor_area_m2": None,
            "area_scale_ratio": None,
            "planar_scale_factor": None,
            "height_m": num_floors * floor_to_floor_m,
        }

    scaling = calculate_scaling_factor(real_area, baseline_area)

    assigned_metadata = {
        "name": f"{osm_id}_assigned_{archetype_id}",
        "mode": "layout_assign",
        "osm_id": osm_id,
        "archetype_id": archetype_id,
        "no_baseline": False,
        "baseline_idf_filename": baseline_idf_path.name,
        "baseline_idf_path": str(baseline_idf_path),
        "real_num_floors": num_floors,
        "target_floor_area_m2": real_area,
        "baseline_floor_area_m2": baseline_area,
        "area_scale_ratio": scaling["area_scale_ratio"],
        "planar_scale_factor": scaling["planar_scale_factor"],
        "height_m": num_floors * floor_to_floor_m,
    }

    logger.info(
        f"Assigned layout for osm_id={osm_id} ({archetype_id}): "
        f"Target Area={real_area:.1f} m2, Baseline Area={baseline_area:.1f} m2, "
        f"Scale Factor={scaling['area_scale_ratio']:.3f} (Planar={scaling['planar_scale_factor']:.3f})"
    )

    return assigned_metadata


# ── B01 — storey-matching core (plan §5 B00/B01, D2/D3(a)) ─────────────────────

# Z-clustering tolerance for grouping Zone floor elevations into storey bands.
# Matches A1's method exactly (scripts/analysis/a1_map_prototypes.py) -- Z
# geometry is ground truth, not zone-name convention (F-05/F-07/A1: OfficeSmall,
# both restaurants, Laboratory already break G/M/T).
_STOREY_BAND_Z_TOLERANCE_M = 0.2


def compute_band_map(idf: Any) -> Dict[str, Any]:
    """Clusters the loaded prototype's Zone objects into storey bands by measured
    FLOOR-surface elevation (world coordinates), replicating A1's accepted method
    (scripts/analysis/a1_map_prototypes.py, 0.2 m tolerance -- see
    results/a1_prototype_storey_structure.csv) so `n_proto`/`plate_proto_m2` here
    reproduce A1's `num_modelled_storeys`/`avg_storey_plate_area_m2`. Never assumes
    a G/M/T naming convention (A1 falsified it as a generalisation -- F-07).

    R01 (plan §5, PLAN_storey-matching_REMAINder.md, AMENDED SCOPE 2026-07-26):
    also reads `ZoneList`/`ZoneGroup` so a band whose zones are repeated by a
    `ZoneGroup`'s "Zone List Multiplier" (EnergyPlus compounds this with each
    zone's own `Zone.Multiplier` field) is no longer invisible to the recomputed
    area. Exactly 2 of the pinned library's 25 files carry a real `ZoneGroup`:
    `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` (list mult 8) and
    `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` (list mult 2, object spelled
    `ZONEGROUP,` upper-case in that file -- eppy's idfobjects lookup is
    case-insensitive so this needed no special-casing). For the other 23,
    `zone_group_list_mult` is empty and every value below is IDENTICAL to the
    pre-R01 computation -- byte-identical band_map return, asserted in
    tests/test_layout_assigner.py.

    `n_proto` is deliberately left as the measured Z-BAND COUNT, never a
    represented-storey count -- match_storeys() branches on it, and redefining
    it would silently move `ApartmentMidRise` from the `n_proto == 3` "applied"
    branch to the `n_proto >= 4` "not expressible" branch, changing the thermal
    model of the dominant archetype as a side effect (R04 is closed at option
    (a); that population must not be perturbed by this task). The new
    `n_storeys_represented` field carries the ZoneGroup-aware storey count
    instead: for a band with no ZoneGroup involvement it contributes exactly 1
    (matching legacy `n_proto` band-counting precisely, regardless of any
    pre-existing literal `Zone.Multiplier` field value baked into a baseline --
    that is a pre-existing, out-of-scope behaviour this task must not disturb);
    for a band whose zones are members of a `ZoneGroup`'d `ZoneList` it
    contributes that ZoneGroup's own "Zone List Multiplier" value. This keeps
    `n_storeys_represented == n_proto` exactly for all 23 non-apartment
    prototypes (no ZoneGroup object exists in those files at all).

    `recomputed_area_m2` now sums each band's TRUE simulated area (own
    `Zone.Multiplier` compounded with any ZoneGroup list multiplier), matching
    what EnergyPlus reports in the `eio` Zone Information table. `plate_proto_m2`
    is `recomputed_area_m2 / n_storeys_represented` (not `/ n_proto`) so it keeps
    meaning "average area of one physical floor" for the 2 apartment archetypes
    exactly as it already did for the other 23 (where the two denominators are
    identical).

    Must be called on the RAW (unscaled) baseline idf, before scale_baseline_idf()
    mutates X/Y coordinates -- plate_proto_m2/recomputed_area_m2 are baseline-frame
    quantities (D2/B02).

    Args:
        idf: A loaded (pre-scaling) geomeppy/eppy IDF object.

    Returns:
        {"n_proto": int, "n_storeys_represented": int, "plate_proto_m2": float,
         "recomputed_area_m2": float,
         "bands": [{"z_level_m": float, "zone_names": [str, ...], "area_m2": float,
                    "storeys_in_band": int}, ...]}
        `bands` is ordered bottom-to-top. `n_proto` is 0 for an idf with no FLOOR
        surfaces (never expected for the 25 baselines, but never crashes).
    """
    zones_by_name = {z.Name: z for z in idf.idfobjects.get("ZONE", [])}
    rules = idf.idfobjects.get("GLOBALGEOMETRYRULES", [])
    coord_sys = rules[0].Coordinate_System.upper() if rules else "WORLD"

    # R01 -- ZoneList membership -> ZoneGroup "Zone List Multiplier", per zone.
    # `.obj[2:]` is eppy's raw field-value list past (key, Name) -- for an
    # extensible object like ZoneList this returns only the fields actually
    # written to this idf (9 for both apartment files), never the IDD's padded
    # extensible-field ceiling (500), so no manual truncation is needed.
    zonelist_members: Dict[str, List[str]] = {}
    for zl in idf.idfobjects.get("ZONELIST", []):
        zonelist_members[zl.Name] = [v for v in zl.obj[2:] if v]

    zone_group_list_mult: Dict[str, float] = {}
    for zg in idf.idfobjects.get("ZONEGROUP", []):
        zl_name = zg.Zone_List_Name
        gmult = float(zg.Zone_List_Multiplier) if zg.Zone_List_Multiplier not in (None, "") else 1.0
        for zname in zonelist_members.get(zl_name, []):
            # Compounds if a zone somehow belonged to >1 ZoneGroup'd list --
            # not the case in the pinned library, but never silently drops one.
            zone_group_list_mult[zname] = zone_group_list_mult.get(zname, 1.0) * gmult

    zone_origins: Dict[str, tuple] = {}
    zone_multipliers: Dict[str, float] = {}
    zone_group_mult_only: Dict[str, float] = {}
    for name, z in zones_by_name.items():
        x0 = float(z.X_Origin) if z.X_Origin not in (None, "") else 0.0
        y0 = float(z.Y_Origin) if z.Y_Origin not in (None, "") else 0.0
        z0 = float(z.Z_Origin) if z.Z_Origin not in (None, "") else 0.0
        own_mult = float(z.Multiplier) if z.Multiplier not in (None, "", 0) else 1.0
        gmult = zone_group_list_mult.get(name, 1.0)
        zone_origins[name] = (x0, y0, z0)
        # Effective total multiplier (own Zone.Multiplier compounded with any
        # ZoneGroup list multiplier) -- feeds recomputed_area_m2 (eio-matching).
        zone_multipliers[name] = own_mult * gmult
        # ZoneGroup-only contribution -- feeds n_storeys_represented, deliberately
        # NOT compounded with own_mult so the other 23 archetypes' band-storey
        # count is untouched by any pre-existing literal Zone.Multiplier value.
        zone_group_mult_only[name] = gmult

    zone_floor_info: Dict[str, Dict[str, Any]] = {}
    for s in idf.idfobjects.get("BUILDINGSURFACE:DETAILED", []):
        if str(s.Surface_Type).strip().upper() != "FLOOR":
            continue
        zname = s.Zone_Name
        vertices = s.coords
        if not vertices or zname not in zone_origins:
            continue
        ox, oy, oz = zone_origins[zname]
        if coord_sys == "RELATIVE":
            world_verts = [(v[0] + ox, v[1] + oy, v[2] + oz) for v in vertices]
        else:
            world_verts = list(vertices)
        z_elev = min(v[2] for v in world_verts)
        area = shapely.Polygon([(v[0], v[1]) for v in world_verts]).area
        mult = zone_multipliers.get(zname, 1.0)
        gmult = zone_group_mult_only.get(zname, 1.0)
        if zname not in zone_floor_info:
            zone_floor_info[zname] = {"floor_z": z_elev, "area_with_mult": area * mult, "group_mult": gmult}
        else:
            zone_floor_info[zname]["area_with_mult"] += area * mult
            zone_floor_info[zname]["group_mult"] = max(zone_floor_info[zname]["group_mult"], gmult)

    sorted_zones = sorted(zone_floor_info.items(), key=lambda kv: kv[1]["floor_z"])
    bands: List[Dict[str, Any]] = []
    for zname, info in sorted_zones:
        z_elev = info["floor_z"]
        matched = None
        for b in bands:
            if abs(b["z_level_m"] - z_elev) < _STOREY_BAND_Z_TOLERANCE_M:
                matched = b
                break
        if matched is None:
            bands.append({
                "z_level_m": z_elev, "zone_names": [zname], "area_m2": info["area_with_mult"],
                "storeys_in_band": info["group_mult"],
            })
        else:
            matched["zone_names"].append(zname)
            matched["area_m2"] += info["area_with_mult"]
            matched["storeys_in_band"] = max(matched["storeys_in_band"], info["group_mult"])

    n_proto = len(bands)
    n_storeys_represented = int(round(sum(b["storeys_in_band"] for b in bands)))
    recomputed_area = sum(b["area_m2"] for b in bands)
    plate_proto = recomputed_area / n_storeys_represented if n_storeys_represented > 0 else 0.0

    return {
        "n_proto": n_proto,
        "n_storeys_represented": n_storeys_represented,
        "plate_proto_m2": plate_proto,
        "recomputed_area_m2": recomputed_area,
        "bands": bands,
    }


def match_storeys(idf: Any, n_real: int, band_map: Dict[str, Any]) -> Dict[str, Any]:
    """Adjusts the prototype toward `n_real` storeys by setting `Zone.Multiplier`
    on a single repeatable band (D3(a), CP-A "PROCEED, RE-SCOPED" ruling 2026-07-26
    -- see PLAN_storey-matching_implementation.md §7). Mutates `idf` in place ONLY
    when the returned status is "applied"; every other status leaves `idf` untouched.

    - **n_real == n_proto**: "identity", no-op (B02's byte-identical regression guard).
    - **n_real < n_proto**: "fallback_shorter". D3(b) (band deletion) was measured in
      A3 and rejected -- it requires per-archetype HVAC/interzone surgery, out of
      scope for this plan. D5 fallback: caller keeps today's single-scalar-plate
      behaviour, tagged in data_quality_flag (B03), never silently.
    - **n_real > n_proto, n_proto == 1**: degenerate case -- the sole band IS the
      whole building, so it is multiplied directly by n_real (bottom=middle=top).
    - **n_real > n_proto, n_proto >= 3 with exactly one middle band**
      (`bands[1:-1]` has length 1 -- true only when n_proto == 3, the G/M/T shape):
      "applied". Multiplier on the middle band solves for the RESIDUAL value (R10,
      E-LA-36, plan §5 REMAINder 2026-07-26) rather than the absolute one -- see
      below.
    - **n_real > n_proto, otherwise** (n_proto == 2 with no middle band at all, or
      n_proto >= 4 with more than one distinct middle band -- Hospital, LargeOffice,
      TallBuilding, SuperTallBuilding, College, LargeHotel, Laboratory: A1 shows
      these already bake Multiplier > 1 or multiple non-uniform Z-bands into the raw
      baseline, so there is no single band that can be bumped unambiguously):
      "fallback_not_expressible". Also D5, tagged distinctly from the shorter case
      per the plan's B03 instruction (never folded together silently).

    R10 (E-LA-36, plan §5 REMAINder 2026-07-26): EnergyPlus COMPOUNDS a zone's own
    `Zone.Multiplier` with any pre-existing `ZoneGroup` "Zone List Multiplier"
    already baked into the target band (`band_map["bands"][i]["storeys_in_band"]`,
    set by compute_band_map()). Writing the old ABSOLUTE value
    (`n_real - (n_proto - 1)`) on a band that already carries a list multiplier > 1
    therefore over-counts storeys (measured: MidriseApartment n_real=4 produced 6
    simulated storeys, not 4). The multiplier written here is instead the RESIDUAL
    that solves `non_middle_storeys + multiplier * list_multiplier == n_real`,
    where `list_multiplier = target_band["storeys_in_band"]` and
    `non_middle_storeys` sums every OTHER band's own `storeys_in_band` (both are 1
    for the 23 non-ZoneGroup archetypes, so this reduces to the exact legacy
    formula `n_real - (n_proto - 1)` for every one of them -- byte-identical,
    asserted in tests/test_layout_assigner.py). Written only when that division is
    EXACT and >= 1; otherwise "fallback_not_expressible" (never silently rounds).
    A residual of exactly 1 means the ZoneGroup's own list multiplier already
    reproduces n_real with no Zone.Multiplier edit needed -- status is still
    "applied" (n_real IS matched) but no field write happens and
    `band_zone_names` is empty, per the plan's "do not write a redundant field
    edit" instruction.

    Args:
        idf: loaded, pre-scaling baseline idf (mutated in place iff status "applied").
        n_real: real building's num_floors.
        band_map: compute_band_map(idf) output for this SAME idf.

    Returns:
        {"status": "identity"|"applied"|"fallback_shorter"|"fallback_not_expressible",
         "n_proto": int, "n_real": int, "multiplier": int|None,
         "band_zone_names": list[str]|None}
    """
    n_proto = band_map["n_proto"]
    bands = band_map["bands"]

    if n_proto <= 0 or n_real == n_proto:
        return {"status": "identity", "n_proto": n_proto, "n_real": n_real,
                "multiplier": None, "band_zone_names": None}

    if n_real < n_proto:
        return {"status": "fallback_shorter", "n_proto": n_proto, "n_real": n_real,
                "multiplier": None, "band_zone_names": None}

    # n_real > n_proto (taller).
    if n_proto == 1:
        target_band = bands[0]
    else:
        middle_bands = bands[1:-1]
        if len(middle_bands) != 1:
            return {"status": "fallback_not_expressible", "n_proto": n_proto, "n_real": n_real,
                    "multiplier": None, "band_zone_names": None}
        target_band = middle_bands[0]

    # R10 (E-LA-36): solve for the RESIDUAL multiplier -- see docstring. For the
    # 23 non-ZoneGroup archetypes list_multiplier == 1 and non_middle_storeys ==
    # (n_proto - 1) exactly (or 0 for the n_proto==1 degenerate case), so this
    # reduces bit-for-bit to the pre-R10 formula.
    list_multiplier = target_band["storeys_in_band"]
    non_middle_storeys = sum(
        b["storeys_in_band"] for b in bands if b is not target_band
    )
    if list_multiplier <= 0:
        return {"status": "fallback_not_expressible", "n_proto": n_proto, "n_real": n_real,
                "multiplier": None, "band_zone_names": None}
    raw = n_real - non_middle_storeys
    if raw < list_multiplier or (raw % list_multiplier) != 0:
        return {"status": "fallback_not_expressible", "n_proto": n_proto, "n_real": n_real,
                "multiplier": None, "band_zone_names": None}
    residual_multiplier = int(round(raw / list_multiplier))
    if residual_multiplier < 1:
        return {"status": "fallback_not_expressible", "n_proto": n_proto, "n_real": n_real,
                "multiplier": None, "band_zone_names": None}

    if residual_multiplier == 1:
        # R10: the ZoneGroup's own list multiplier (or, for non-ZoneGroup bands,
        # the implicit 1) already reproduces n_real exactly. Do NOT write
        # Zone.Multiplier=1 -- it would be a redundant field edit per the plan's
        # explicit instruction. n_real IS matched, so status stays "applied".
        return {"status": "applied", "n_proto": n_proto, "n_real": n_real,
                "multiplier": 1, "band_zone_names": []}

    applied_names = []
    zones_by_name = {z.Name: z for z in idf.idfobjects.get("ZONE", [])}
    for zname in target_band["zone_names"]:
        z_obj = zones_by_name.get(zname)
        if z_obj is not None:
            z_obj.Multiplier = residual_multiplier
            applied_names.append(zname)

    return {"status": "applied", "n_proto": n_proto, "n_real": n_real,
            "multiplier": residual_multiplier, "band_zone_names": applied_names}


# ── T04 — scale_baseline_idf() ─────────────────────────────────────────────────

# Surface classes whose X/Y vertex coordinates scale by √S; Z is left unchanged.
_GEOMETRY_SURFACE_CLASSES = (
    "BUILDINGSURFACE:DETAILED",
    "FENESTRATIONSURFACE:DETAILED",
    "SHADING:ZONE:DETAILED",
    "SHADING:BUILDING:DETAILED",
)

# E-LA-12: Daylighting:ReferencePoint is a point object (not a surface -- no
# .coords/.setcoords()), so its X/Y fields need direct scaling by the same
# planar_scale_factor; Z is left unchanged, mirroring _GEOMETRY_SURFACE_CLASSES.
# Real IDD field names confirmed via eppy introspection (no leading underscore
# after X/Y, unlike the plan's guessed names): XCoordinate_of_Reference_Point /
# YCoordinate_of_Reference_Point / ZCoordinate_of_Reference_Point.
# Daylighting:Controls audited too -- it only carries Daylighting_Reference_Point_N_Name
# references (strings) and illuminance/fraction settings, no embedded X/Y/Z
# coordinate fields of its own, so no entry is needed for it here.
_GEOMETRY_POINT_SPECS = (
    ("DAYLIGHTING:REFERENCEPOINT", "XCoordinate_of_Reference_Point", "YCoordinate_of_Reference_Point"),
)

# (idf_class, calc_method_field, absolute_value_field, method_value_meaning_absolute).
# Only the branch matching `method_value_meaning_absolute` carries an absolute
# quantity; every other choice (Watts/Area, Flow/Area, People/Area, ...) is a
# density field and must stay byte-identical.
_ABSOLUTE_LOAD_SPECS = (
    ("LIGHTS", "Design_Level_Calculation_Method", "Lighting_Level", "LightingLevel"),
    ("ELECTRICEQUIPMENT", "Design_Level_Calculation_Method", "Design_Level", "EquipmentLevel"),
    ("GASEQUIPMENT", "Design_Level_Calculation_Method", "Design_Level", "EquipmentLevel"),
    ("PEOPLE", "Number_of_People_Calculation_Method", "Number_of_People", "People"),
    ("ZONEINFILTRATION:DESIGNFLOWRATE", "Design_Flow_Rate_Calculation_Method", "Design_Flow_Rate", "Flow/Zone"),
    ("DESIGNSPECIFICATION:OUTDOORAIR", "Outdoor_Air_Method", "Outdoor_Air_Flow_per_Zone", "Flow/Zone"),
)

# (idf_class, absolute_value_field) — no calc-method branch on these classes;
# the field is always an absolute quantity.
_UNCONDITIONAL_ABSOLUTE_SPECS = (
    ("WATERUSE:EQUIPMENT", "Peak_Flow_Rate"),
    ("EXTERIOR:LIGHTS", "Design_Level"),
    # T15/E-LA-06 — fixed-capacity auxiliary equipment, confirmed always-absolute
    # (never a per-area/per-person density field) via eppy inspection of the 6
    # T12 local-leg baselines. WaterHeater:Stratified investigated, absent in
    # all 6 — not added (see plan §9 E-LA-06 update).
    # ElectricLoadCenter:Transformer Rated_Capacity moved OUT of this list at D9
    # (plan §5 B06, 2026-07-26) -- it now scales by its own
    # transformer_scale_ratio (see the dedicated loop below), not area_scale_ratio.
    ("WATERHEATER:MIXED", "Tank_Volume"),
    ("WATERHEATER:MIXED", "Heater_Maximum_Capacity"),
    # E-LA-10 — Peak_Use_Flow_Rate was never on this list, so it stayed
    # byte-identical between baseline and scaled IDF (confirmed via direct
    # comparison on way_1014146287); fixed-capacity, always-absolute field.
    ("WATERHEATER:MIXED", "Peak_Use_Flow_Rate"),
    # T02 audit (E-LA-10 sibling fields) — literal non-blank in 64/72 and
    # 72/72 WaterHeater:Mixed objects respectively across the 20 mapped
    # baseline files that contain WaterHeater:Mixed objects; never gated on a
    # calc-method choice (unconditionally absolute, same class as
    # Heater_Maximum_Capacity). Heater_Minimum_Capacity
    # and Heater_Ignition_Minimum_Flow_Rate were also investigated: always 0.0
    # or blank, Heater_Control_Type is "Cycle" everywhere (Minimum_Capacity is
    # only used in "Modulate" mode per the E+ 23.1 IDD) -- not added.
    ("WATERHEATER:MIXED", "Off_Cycle_Parasitic_Fuel_Consumption_Rate"),
    ("WATERHEATER:MIXED", "On_Cycle_Parasitic_Fuel_Consumption_Rate"),
    ("WATERHEATER:MIXED", "Off_Cycle_Loss_Coefficient_to_Ambient_Temperature"),
    ("WATERHEATER:MIXED", "On_Cycle_Loss_Coefficient_to_Ambient_Temperature"),
    # Coil:Cooling:DX:MultiSpeed — confirmed literal (non-autosize) rated
    # capacity/flow-rate fields in SmallHotel/SecondarySchool/RetailStandalone/
    # FullServiceRestaurant (unlike the DX:SingleSpeed/DX:TwoSpeed coils used
    # elsewhere, which are autosized); Sensible_Heat_Ratio/COP/effectiveness/
    # waste-heat-fraction fields on the same object are ratios, left untouched.
    ("COIL:COOLING:DX:MULTISPEED", "Speed_1_Gross_Rated_Total_Cooling_Capacity"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_1_Rated_Air_Flow_Rate"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_2_Gross_Rated_Total_Cooling_Capacity"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_2_Rated_Air_Flow_Rate"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_3_Gross_Rated_Total_Cooling_Capacity"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_3_Rated_Air_Flow_Rate"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_4_Gross_Rated_Total_Cooling_Capacity"),
    ("COIL:COOLING:DX:MULTISPEED", "Speed_4_Rated_Air_Flow_Rate"),
    # E-LA-07 class 1 — LargeOffice's FluidCooler:TwoSpeed "Central Tower" has
    # Performance_Input_Method=NominalCapacity with literal (never-autosized)
    # High/Low_Speed_Nominal_Capacity, while Design_Water_Flow_Rate and
    # High_Fan_Speed_Air_Flow_Rate on the same object stay autosize (confirmed
    # via eppy on the raw baseline) -- same defect class as E-LA-06/E-LA-10,
    # just never scaled because no T15-tested archetype had this loop.
    ("FLUIDCOOLER:TWOSPEED", "High_Speed_Nominal_Capacity"),
    ("FLUIDCOOLER:TWOSPEED", "Low_Speed_Nominal_Capacity"),
    # B01b/E-LA-27 sibling sweep (2026-07-26) — grep of all 25 mapped baselines for
    # non-Zone-scoped (no Zone_Name field, so a Zone Multiplier never reaches them)
    # objects with a literal, non-autosize "capacity"/"rated"/"volume"/"flow"-named
    # field. ElectricLoadCenter:Transformer (E-LA-06, above) was already covered;
    # these are the same defect class on its direct siblings.
    # R03 (plan §5 REMAINder, 2026-07-26, E-LA-32) -- Generator_1_Rated_Electric_
    # Power_Output / DC_System_Capacity moved OUT of this list. D9/B06 had left
    # them on area_scale_ratio deliberately (a known-wrong mechanism, forwarded
    # rather than fixed at the time): PV/generator capacity tracks ROOF area, and
    # a Zone Multiplier never touches the roof (it lives on the single,
    # never-multiplied top band), so area_scale_ratio's n_real/n_proto growth
    # factor overstated their true driver. They now scale by their own
    # roof_scale_ratio (== planar_scale_factor ** 2, the same horizontal plan-area
    # growth factor already applied to every surface's vertices -- see the
    # dedicated loop below, same pattern as D9's transformer_scale_ratio loop).
    # Boiler:HotWater Nominal_Capacity / Chiller:Electric:{EIR,ReformulatedEIR}
    # Reference_Capacity / Humidifier:Steam:Electric Rated_Capacity moved OUT of
    # this list at B06 (2026-07-26) -- all four fields carry \autosizable in the
    # E+ 23.1 IDD (confirmed), so they now resolve to their own S=1
    # EnergyPlus-autosized value via _MEASURED_S1_ABSOLUTE_SPECS (E-LA-11 pattern)
    # instead of a literal-baseline x area_scale_ratio scale. See the dedicated
    # loop below.
    # Deliberately left unscaled (same sweep, same 25 baselines): every COP/
    # efficiency/SHR/sizing-factor/temperature field matched by the "rated"/
    # "capacity" keyword grep (dimensionless or intensive, must stay
    # byte-identical -- same rule as the density fields in _ABSOLUTE_LOAD_SPECS);
    # AirTerminal/Coil per-zone flow/capacity fields (Zone_Name-adjacent via their
    # owning zone equipment, already reached by that zone's own Multiplier);
    # CoolingTower/EvaporativeFluidCooler/Chiller auxiliary fields (Basin_Heater_
    # Capacity, Free_Convection_Capacity, Design_Water_Flow_Rate, Design_Spray_
    # Water_Flow_Rate, Reference_Chilled_Water_Flow_Rate) whose own PRIMARY
    # capacity/flow field autosizes in these baselines (confirmed no literal
    # primary field on CoolingTower:SingleSpeed) -- scaling only the auxiliary
    # while the primary correctly autosizes to the new size at runtime would be
    # the E-LA-11 autosize/S-scale interaction class, not the always-absolute one
    # this list is for; no baseline in the sweep exercising these classes was ever
    # run to Severe under storey matching (MediumOffice, the acceptance-test
    # archetype, has none of Boiler/Chiller/CoolingTower), so left as a forwarded
    # finding rather than a speculative fix.
)

# E-LA-11 -- LargeOffice's 4 DataCenter zones' WSHP coils autosize to INF/NaN
# at small S (anisotropic zone-shrink HVAC-autosize degeneracy on the shared
# plant loop -> CheckForRunawayPlantTemps Fatal; confirmed envelope-patch-
# independent, structural-fixes plan §4/debug plan T06-T07 eio evidence).
# Fix: resolve these 8 coils' rated fields to their OWN S=1 raw-baseline
# EnergyPlus-autosized values (real annual EnergyPlus 23.1 run, Buffalo
# TMYx weather -- the baseline's native design climate -- 2026-07-23,
# eplusout.eio component-sizing lines, all 4 zones sane/finite; see
# scratchpad/t19_t06_t07_work/raw_s1_largeoffice/), then scale by
# area_scale_ratio -- same "resolve-the-autosize-once, then S-scale the
# literal" pattern as E-LA-10/E-LA-07-class-1, not a novel mechanism.
#
# (idf_class, exact object Name, field, S=1 literal). Matched by exact
# **Name**, NOT a class-level (idf_class, field) tuple like
# _UNCONDITIONAL_ABSOLUTE_SPECS: a fresh eppy scan of all 25 unique mapped
# baseline files (2026-07-23) confirmed ASHRAE901_ApartmentHighRise also
# carries 24 Coil:Heating:WaterToAirHeatPump:EquationFit +
# 24 Coil:Cooling:WaterToAirHeatPump:EquationFit objects (its per-apartment
# AirLoop G/M/T *_{Heating,Cooling} Coil fleet) -- a class-level match would
# incorrectly overwrite HighriseApartment's own autosize with these
# LargeOffice-specific literals. These 8 Names
# ("AirLoop DataCenter {Basement,bot,mid,top} {Heating,Cooling} Coil") do not
# appear in any other baseline's coil-name set in the same scan, so an
# exact-Name match is sufficient scoping without threading an archetype_id
# parameter through scale_baseline_idf().
_NAMED_ABSOLUTE_SPECS = (
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Heating Coil", "Rated_Air_Flow_Rate", 21.76082),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Heating Coil", "Rated_Water_Flow_Rate", 1.10026e-2),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Heating Coil", "Gross_Rated_Heating_Capacity", 444975.22266),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Heating Coil", "Rated_Air_Flow_Rate", 0.48949),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Heating Coil", "Rated_Water_Flow_Rate", 2.44640e-4),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Heating Coil", "Gross_Rated_Heating_Capacity", 9893.94684),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Heating Coil", "Rated_Air_Flow_Rate", 4.69562),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Heating Coil", "Rated_Water_Flow_Rate", 2.34983e-3),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Heating Coil", "Gross_Rated_Heating_Capacity", 95033.94133),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Heating Coil", "Rated_Air_Flow_Rate", 0.47764),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Heating Coil", "Rated_Water_Flow_Rate", 2.38961e-4),
    ("COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Heating Coil", "Gross_Rated_Heating_Capacity", 9664.26963),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Cooling Coil", "Rated_Air_Flow_Rate", 21.76082),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Cooling Coil", "Rated_Water_Flow_Rate", 1.10026e-2),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Cooling Coil", "Gross_Rated_Total_Cooling_Capacity", 469899.78316),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter Basement Cooling Coil", "Gross_Rated_Sensible_Cooling_Capacity", 317819.49474),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Cooling Coil", "Rated_Air_Flow_Rate", 0.48949),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Cooling Coil", "Rated_Water_Flow_Rate", 2.44640e-4),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Cooling Coil", "Gross_Rated_Total_Cooling_Capacity", 10448.14012),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter bot Cooling Coil", "Gross_Rated_Sensible_Cooling_Capacity", 7110.88362),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Cooling Coil", "Rated_Air_Flow_Rate", 4.69562),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Cooling Coil", "Rated_Water_Flow_Rate", 2.34983e-3),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Cooling Coil", "Gross_Rated_Total_Cooling_Capacity", 100357.11237),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter mid Cooling Coil", "Gross_Rated_Sensible_Cooling_Capacity", 68255.93198),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Cooling Coil", "Rated_Air_Flow_Rate", 0.47764),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Cooling Coil", "Rated_Water_Flow_Rate", 2.38961e-4),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Cooling Coil", "Gross_Rated_Total_Cooling_Capacity", 10205.59792),
    ("COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT", "AirLoop DataCenter top Cooling Coil", "Gross_Rated_Sensible_Cooling_Capacity", 6942.03771),
)


# D9/B06 (2026-07-26) -- Boiler:HotWater Nominal_Capacity, Chiller:Electric:EIR/
# ReformulatedEIR Reference_Capacity, Humidifier:Steam:Electric Rated_Capacity:
# all four fields carry `\autosizable` in the E+ 23.1 IDD (confirmed by direct
# inspection of Energy+.idd), unlike ElectricLoadCenter:Transformer/Generators/
# Generator:PVWatts (none of the three carry `\autosizable` -- required hard-
# numeric fields, no EnergyPlus sizing routine exists for them at all; D9
# explicitly excludes them from this mechanism, see the Transformer-specific
# loop and E-LA-32 in scale_baseline_idf()).
#
# Measured per the E-LA-11 pattern: for each archetype below, the RAW,
# completely unscaled S=1 baseline (native footprint/storey count, no
# BuildingIDF.build() pipeline involvement) was run ONCE through real
# EnergyPlus 23.1 (sbatch --array job 1160689, Speed cluster, Buffalo TMYx
# weather -- the baseline's own native design climate, same precedent as
# E-LA-11) with ONLY the field(s) below temporarily forced to `Autosize`
# (nothing else in the file touched). The EnergyPlus-computed "Design Size"
# value read back from eplusout.eio's Component Sizing Information lines is
# recorded here as a literal constant; production always substitutes it for
# the archetype's own (frequently very different) literal baseline value,
# then scales the substituted value by area_scale_ratio like any other
# absolute-load field. All 6 runs below completed with 0 Fatal (see
# debug/storey-Matching/results/b06_s1ref/*/eplusout.err); the handful of
# pre-existing Severes present in some runs (CheckWarmupConvergence,
# CheckAirLoopFlowBalance) are the same already-tracked classes as
# E-LA-14/16/18/19/E-LA-06 and do not touch these 4 field classes' own sizing.
#
# Keyed by archetype_id (ARCHETYPE_IDF_MAP's canonical vocab token), NOT by
# (class, Name) alone: "HeatSys1 Boiler" recurs verbatim, with a DIFFERENT
# measured capacity, in Hospital/HotelLarge/OfficeLarge/OutPatientHealthCare/
# SchoolPrimary/SchoolSecondary -- a global (class, Name) match (E-LA-11's own
# pattern) would silently apply whichever entry appears last in this dict to
# every archetype whose own boiler happens to share that generic name.
# *Detailed variants (LargeOfficeDetailed) reuse their non-Detailed
# counterpart's baseline file and therefore its measured values, matching
# DEFAULT_BASELINE_AREAS's own established convention.
#
# (idf_class, exact object Name, field, S=1 EnergyPlus-autosized Design Size).
_MEASURED_S1_ABSOLUTE_SPECS: Dict[str, tuple] = {
    "HighriseApartment": (
        ("BOILER:HOTWATER", "Central Boiler", "Nominal_Capacity", 441215.66021),
    ),
    "Hospital": (
        ("BOILER:HOTWATER", "HeatSys1 Boiler", "Nominal_Capacity", 1797047.83526),
        ("CHILLER:ELECTRIC:EIR", "Heat Recovery Chiller", "Reference_Capacity", 182015.03827),
        ("CHILLER:ELECTRIC:REFORMULATEDEIR", "CoolSys1 Chiller1", "Reference_Capacity", 849070.49546),
        ("CHILLER:ELECTRIC:REFORMULATEDEIR", "CoolSys1 Chiller2", "Reference_Capacity", 849070.49546),
        ("HUMIDIFIER:STEAM:ELECTRIC", "VAV_ER Humidifier", "Rated_Capacity", 4.78029e-05),
        ("HUMIDIFIER:STEAM:ELECTRIC", "VAV_OR Humidifier", "Rated_Capacity", 9.4186e-05),
        ("HUMIDIFIER:STEAM:ELECTRIC", "VAV_ICU Humidifier", "Rated_Capacity", 5.33921e-05),
        ("HUMIDIFIER:STEAM:ELECTRIC", "VAV_PATRMS Humidifier", "Rated_Capacity", 0.000115707),
        ("HUMIDIFIER:STEAM:ELECTRIC", "VAV_LABS Humidifier", "Rated_Capacity", 1.82696e-05),
    ),
    "LargeHotel": (
        ("BOILER:HOTWATER", "HeatSys1 Boiler", "Nominal_Capacity", 479971.8465),
        ("CHILLER:ELECTRIC:EIR", "CoolSys1 Chiller1", "Reference_Capacity", 796861.11592),
    ),
    "LargeOffice": (
        ("BOILER:HOTWATER", "HeatSys1 Boiler", "Nominal_Capacity", 2658869.69789),
        ("BOILER:HOTWATER", "Central Boiler", "Nominal_Capacity", 569924.83659),
        ("CHILLER:ELECTRIC:REFORMULATEDEIR", "CoolSys1 Chiller1", "Reference_Capacity", 1195339.9923),
        ("CHILLER:ELECTRIC:REFORMULATEDEIR", "CoolSys1 Chiller2", "Reference_Capacity", 1195339.9923),
        ("HUMIDIFIER:STEAM:ELECTRIC", "DataCenter_basement_ZN_6 Humidifier", "Rated_Capacity", 0.000186408),
    ),
    "PrimarySchool": (
        ("BOILER:HOTWATER", "HeatSys1 Boiler", "Nominal_Capacity", 264869.13019),
    ),
    "SecondarySchool": (
        ("BOILER:HOTWATER", "HeatSys1 Boiler", "Nominal_Capacity", 609350.19759),
        ("CHILLER:ELECTRIC:EIR", "CoolSys1 Chiller1", "Reference_Capacity", 910251.18154),
    ),
}
_MEASURED_S1_ABSOLUTE_SPECS["LargeOfficeDetailed"] = _MEASURED_S1_ABSOLUTE_SPECS["LargeOffice"]
_MEASURED_S1_ABSOLUTE_SPECS["Outpatient"] = (
    ("BOILER:HOTWATER", "HeatSys1 Boiler", "Nominal_Capacity", 142453.93499),
    ("HUMIDIFIER:STEAM:ELECTRIC", "AHU-1 Humidifier", "Rated_Capacity", 4.36368e-05),
)


def _is_blank_or_autosize(value: Any) -> bool:
    """True for '' (unset IDF field) or 'autosize'/'autocalculate' (never multiply these)."""
    if value is None:
        return True
    if isinstance(value, str):
        v = value.strip().lower()
        return v in ("", "autosize", "autocalculate")
    return False


def scale_baseline_idf(
    idf: Any, scale_factor_dict: Dict[str, float], archetype_id: Optional[str] = None,
) -> Any:
    """Scales a baseline IDF's geometry (√S planar) and absolute loads (S) in place.

    X/Y vertex coordinates on BuildingSurface:Detailed / FenestrationSurface:Detailed /
    Shading:Zone:Detailed / Shading:Building:Detailed scale by `planar_scale_factor`
    (Z unchanged). Daylighting:ReferencePoint X/Y coordinates (E-LA-12) scale by the
    same `planar_scale_factor` (Z unchanged); Daylighting:Controls carries no embedded
    coordinate fields of its own, only reference-point name/fraction/illuminance
    settings, so nothing else needs scaling there. Absolute-quantity fields (Design/Lighting Level, Number of People,
    Design Flow Rate, Outdoor Air Flow per Zone, Peak Flow Rate, Exterior Lights Design
    Level) scale by `area_scale_ratio`, gated on each object's calculation-method field
    so per-area/per-person density fields (Watts/Area, Flow/Area, People/Area, ...) are
    left byte-identical. Blank ('') and autosize/autocalculate fields are never touched.
    Fixed-capacity auxiliary equipment (T15/E-LA-06: WaterHeater:Mixed
    Tank_Volume/Heater_Maximum_Capacity/Peak_Use_Flow_Rate (E-LA-10) plus the
    Off/On-Cycle Parasitic_Fuel_Consumption_Rate and Off/On-Cycle
    Loss_Coefficient_to_Ambient_Temperature fields (T02 audit), the literal —
    never-autosized in this baseline library — Coil:Cooling:DX:MultiSpeed
    per-speed rated capacity/flow-rate fields, and FluidCooler:TwoSpeed
    High/Low_Speed_Nominal_Capacity (E-LA-07 class 1)) also scales by
    `area_scale_ratio`. E-LA-11: LargeOffice's 4 DataCenter zones' 8
    Coil:{Heating,Cooling}:WaterToAirHeatPump:EquationFit coils (matched by
    exact object Name, not class, since ApartmentHighRise's own 48 WSHP coils
    share the same IDF class) have their rated air-flow/water-flow/capacity
    fields resolved from `autosize` to the coils' own S=1 raw-baseline
    EnergyPlus-autosized design values, then scaled by `area_scale_ratio` --
    autosize on these 8 objects degenerates to INF/NaN at small S.
    R03/E-LA-32 (plan §5 REMAINder, 2026-07-26): ElectricLoadCenter:Generators
    Generator_1_Rated_Electric_Power_Output and Generator:PVWatts
    DC_System_Capacity scale by their own `roof_scale_ratio`
    (`planar_scale_factor ** 2`), NOT `area_scale_ratio` -- PV/generator
    capacity tracks roof area, which a Zone Multiplier never touches (D9/B01b
    left this on area_scale_ratio deliberately as a known-wrong mechanism,
    forwarded rather than fixed at the time; this task closes it).
    D9/B06: ElectricLoadCenter:Transformer Rated_Capacity scales by its OWN
    `transformer_scale_ratio` (planar area factor x the ACTUAL Zone Multiplier
    match_storeys() set, not n_real/n_proto -- see calculate_scaling_factor()),
    because a naive area_scale_ratio undercounts the true built electric load
    whenever the middle band's own multiplier exceeds n_real/n_proto (true for
    every G/M/T archetype: only the middle band repeats, so its multiplier is
    always >= n_real/n_proto). B06: Boiler:HotWater Nominal_Capacity,
    Chiller:Electric:{EIR,ReformulatedEIR} Reference_Capacity and
    Humidifier:Steam:Electric Rated_Capacity all carry `\\autosizable` in the
    E+ 23.1 IDD (confirmed), so instead of scaling the archetype's own literal
    baseline value by `area_scale_ratio` (B01b's mechanism, which this
    replaces), they resolve to their own S=1 EnergyPlus-autosized design value
    (_MEASURED_S1_ABSOLUTE_SPECS, the E-LA-11 pattern) scaled by
    `area_scale_ratio` -- unlike E-LA-11's coils these fields are LITERAL, not
    `autosize`, in the raw baseline, so the substitution is unconditional
    (matched by archetype_id + exact Name), not gated on the field currently
    reading autosize. `archetype_id` disambiguates identically-named objects
    that recur verbatim across archetypes (e.g. "HeatSys1 Boiler" names both
    Hospital's and HotelLarge's own boiler, with different measured
    capacities) -- a plain (class, Name) match, as E-LA-11 used, is only safe
    when the Name is globally unique across all 25 baselines, which E-LA-11
    verified and these Boiler/Chiller/Humidifier names do not have. Other HVAC
    capacity fields are autosized in every baseline inspected and are never
    touched (not in the class lists above).

    B08b/D8 (2026-07-26): after every scale above, the whole model is
    re-centred so the XY bounding-box centre of its BuildingSurface:Detailed
    geometry lands on local (0, 0) -- unconditionally, independent of
    `planar_scale_factor` (even the S=1 identity case is re-centred, since the
    placement defect this closes is not a scaling defect). This is what makes
    builder.py's existing `+ footprint_centroid_utm` placement step land the
    prototype's own centroid, not an arbitrary local corner, on the real
    building's footprint centroid (B08a). See the dedicated comment block
    above the implementation for the Zone-Origin-vs-surface-vertex mechanics.

    Args:
        idf: A loaded geomeppy/eppy IDF object (mutated in place).
        scale_factor_dict: Output of calculate_scaling_factor() — must contain
            'planar_scale_factor', 'area_scale_ratio', 'transformer_scale_ratio'
            and 'roof_scale_ratio'.
        archetype_id: Canonical archetype id (ARCHETYPE_IDF_MAP key), used only
            to scope `_MEASURED_S1_ABSOLUTE_SPECS` lookups to the right
            archetype. If None, no measured-S1 substitution is applied (those
            fields are left at the raw baseline's own literal, unscaled --
            same as any other field absent from every spec list here).

    Returns:
        The same idf object, for chaining.
    """
    planar_k = scale_factor_dict["planar_scale_factor"]
    area_s = scale_factor_dict["area_scale_ratio"]
    transformer_s = scale_factor_dict.get("transformer_scale_ratio", area_s)
    roof_s = scale_factor_dict.get("roof_scale_ratio", planar_k ** 2)

    for cls in _GEOMETRY_SURFACE_CLASSES:
        for surf in idf.idfobjects.get(cls, []):
            scaled_coords = [(x * planar_k, y * planar_k, z) for x, y, z in surf.coords]
            surf.setcoords(scaled_coords)

    # E-LA-28/B05: Zone X/Y Origin is a second, separate coordinate field under
    # GlobalGeometryRules ... Relative (surface vertices are offsets FROM the
    # zone's Origin) -- _GEOMETRY_SURFACE_CLASSES above never touches ZONE, so
    # rooms shrank correctly while the building's own outer extent stayed frozen
    # at the raw S=1 baseline. Z Origin is explicitly NOT touched here -- it
    # belongs to B01/B03's storey matching (F-01/D2), not to this planar fix.
    for z in idf.idfobjects.get("ZONE", []):
        x0, y0 = z.X_Origin, z.Y_Origin
        if not _is_blank_or_autosize(x0):
            z.X_Origin = float(x0) * planar_k
        if not _is_blank_or_autosize(y0):
            z.Y_Origin = float(y0) * planar_k

    for cls, x_field, y_field in _GEOMETRY_POINT_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            x_val, y_val = getattr(obj, x_field), getattr(obj, y_field)
            if not _is_blank_or_autosize(x_val):
                setattr(obj, x_field, float(x_val) * planar_k)
            if not _is_blank_or_autosize(y_val):
                setattr(obj, y_field, float(y_val) * planar_k)

    for cls, method_field, value_field, absolute_method in _ABSOLUTE_LOAD_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            if str(getattr(obj, method_field, "")).strip() != absolute_method:
                continue
            val = getattr(obj, value_field)
            if _is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, float(val) * area_s)

    for cls, value_field in _UNCONDITIONAL_ABSOLUTE_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            val = getattr(obj, value_field)
            if _is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, float(val) * area_s)

    for cls, obj_name, value_field, s1_value in _NAMED_ABSOLUTE_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            if str(obj.Name).strip() != obj_name:
                continue
            val = getattr(obj, value_field)
            if not _is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, s1_value * area_s)

    # D9/B06 -- ElectricLoadCenter:Transformer Rated_Capacity, own scale factor
    # (transformer_scale_ratio, not area_scale_ratio -- see calculate_scaling_factor()).
    for obj in idf.idfobjects.get("ELECTRICLOADCENTER:TRANSFORMER", []):
        val = obj.Rated_Capacity
        if _is_blank_or_autosize(val):
            continue
        obj.Rated_Capacity = float(val) * transformer_s

    # R03/E-LA-32 -- Generator:PVWatts DC_System_Capacity / ElectricLoadCenter:
    # Generators Generator_1_Rated_Electric_Power_Output, own scale factor
    # (roof_scale_ratio == planar_scale_factor ** 2 -- see calculate_scaling_factor();
    # invariant to any Zone Multiplier by construction, unlike transformer_s).
    for obj in idf.idfobjects.get("GENERATOR:PVWATTS", []):
        val = obj.DC_System_Capacity
        if _is_blank_or_autosize(val):
            continue
        obj.DC_System_Capacity = float(val) * roof_s
    for obj in idf.idfobjects.get("ELECTRICLOADCENTER:GENERATORS", []):
        val = obj.Generator_1_Rated_Electric_Power_Output
        if _is_blank_or_autosize(val):
            continue
        obj.Generator_1_Rated_Electric_Power_Output = float(val) * roof_s

    # B06 -- Boiler/Chiller/Humidifier: archetype's own S=1 EnergyPlus-autosized
    # capacity (E-LA-11 pattern), unconditionally substituted (these fields are
    # LITERAL, not autosize, in the raw baseline -- see docstring), then scaled
    # by area_scale_ratio like every other absolute-load field.
    for cls, obj_name, value_field, s1_value in _MEASURED_S1_ABSOLUTE_SPECS.get(archetype_id, ()):
        for obj in idf.idfobjects.get(cls, []):
            if str(obj.Name).strip() != obj_name:
                continue
            setattr(obj, value_field, s1_value * area_s)

    # ── B08b/D8 -- re-centre the scaled prototype (plan §5 B08b, manager ruling
    # 2026-07-26, PLAN_storey-matching_implementation.md D8, on B08a's sub-mm
    # diagnosis) -- pure translation, applied AFTER every scaling loop above so
    # it only ever sees already-scaled coordinates. Every loop above scales the
    # prototype's Zone Origins and surface vertices about the prototype's own
    # arbitrary local (0,0) and never re-centres; builder.py's
    # `+ footprint_centroid_utm` placement step then lands that local (0,0) --
    # not the prototype's own centroid -- on the real building's footprint
    # centroid: a median 8.49 m (nyc) / 11.49 m (la) miss, B08a, n=2,630. Z is
    # not touched (same rule as the Zone-Origin loop above).
    #
    # Anchor = XY bounding-box centre of BuildingSurface:Detailed (wall/roof/
    # floor) vertices only, resolved to WORLD coordinates -- the same quantity
    # B08a validated to r=0.999999998 (max residual 0.00054 m, n=2,630) against
    # the pipeline's actual rendered placement. Fenestration/shading are
    # deliberately excluded from the anchor calculation: no baseline in the
    # mapped library carries a Shading:Building:Detailed object today (surveyed
    # 2026-07-26, all 25), but that class's own IDD memo ("these items are
    # relative to the current building origin (0,0,0)") means a future one
    # could sit far from the envelope and would corrupt the centroid if it were
    # allowed to vote on it.
    #
    # GlobalGeometryRules' "Coordinate System" field governs how
    # BuildingSurface:Detailed / FenestrationSurface:Detailed /
    # Shading:Zone:Detailed vertices are stored -- confirmed by direct
    # inspection of C:\EnergyPlusV23-1-0\Energy+.idd and by a survey of all 25
    # mapped baselines (2026-07-26): 24/25 are "Relative" (offsets from the
    # owning Zone's Origin), 1/25 (Supermarket_V22.1.idf) is "World" (already
    # absolute). Under Relative, translating the owning Zone's Origin alone
    # already translates every surface anchored to it -- touching the
    # surface's own vertex fields too would double-move them, so exactly one
    # of the two is written per idf. Shading:Building:Detailed has no
    # Zone/Base-Surface link at all (its own IDD memo: vertices are relative
    # to the BUILDING origin, not a zone) -- it cannot be zone-anchored by
    # construction, so it is always shifted directly, regardless of the
    # Coordinate System flag. Zone Origins are always absolute regardless of
    # that flag (it only governs how surface vertices *within* a zone are
    # interpreted), so they are always shifted directly too.
    # Daylighting:ReferencePoint is governed by its OWN, separate
    # "Daylighting Reference Point Coordinate System" field -- IDD default,
    # and every value found in the 25-baseline survey (2026-07-26): "Relative"
    # or blank (never "World") -- so it is left untouched here: the Zone
    # Origin shift above already carries it, exactly as it already carries
    # Daylighting:ReferencePoint under the existing planar_k scaling loop.
    rules = idf.idfobjects.get("GLOBALGEOMETRYRULES", [])
    surf_coord_sys = rules[0].Coordinate_System.upper() if rules else "WORLD"

    zone_xy: Dict[str, tuple] = {}
    for z in idf.idfobjects.get("ZONE", []):
        zx = 0.0 if _is_blank_or_autosize(z.X_Origin) else float(z.X_Origin)
        zy = 0.0 if _is_blank_or_autosize(z.Y_Origin) else float(z.Y_Origin)
        zone_xy[z.Name] = (zx, zy)

    min_x = min_y = math.inf
    max_x = max_y = -math.inf
    for surf in idf.idfobjects.get("BUILDINGSURFACE:DETAILED", []):
        if surf_coord_sys == "RELATIVE":
            ox, oy = zone_xy.get(surf.Zone_Name, (0.0, 0.0))
        else:
            ox, oy = 0.0, 0.0
        for x, y, _z in surf.coords:
            wx, wy = x + ox, y + oy
            if wx < min_x:
                min_x = wx
            if wx > max_x:
                max_x = wx
            if wy < min_y:
                min_y = wy
            if wy > max_y:
                max_y = wy

    if min_x <= max_x:  # at least one wall/roof/floor vertex found
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0

        for z in idf.idfobjects.get("ZONE", []):
            if not _is_blank_or_autosize(z.X_Origin):
                z.X_Origin = float(z.X_Origin) - cx
            if not _is_blank_or_autosize(z.Y_Origin):
                z.Y_Origin = float(z.Y_Origin) - cy

        for cls in _GEOMETRY_SURFACE_CLASSES:
            if cls != "SHADING:BUILDING:DETAILED" and surf_coord_sys == "RELATIVE":
                continue  # zone-anchored; the Zone Origin shift above already moved it
            for surf in idf.idfobjects.get(cls, []):
                surf.setcoords([(x - cx, y - cy, z) for x, y, z in surf.coords])

    return idf


# ── T05 — parse_baseline_zones() ────────────────────────────────────────────────

def _measured_zone_floor_area(idf: Any, zone_name: str) -> float:
    """Sums FLOOR-type BuildingSurface:Detailed areas referencing `zone_name`.

    Fallback for baseline IDFs that leave Zone.Floor_Area blank (common in this
    library — see plan §3.1 progress-log note).
    """
    total = 0.0
    for s in idf.idfobjects.get("BUILDINGSURFACE:DETAILED", []):
        if s.Zone_Name == zone_name and str(s.Surface_Type).strip().upper() == "FLOOR":
            total += s.area
    return total


def parse_baseline_zones(idf: Any, archetype_id: str) -> List[Dict[str, Any]]:
    """Builds the extruded_zones-shaped list from a (post-scaling) baseline IDF.

    One dict per raw `Zone` object (plenums/attics/unconditioned included, matching
    plan §3.1's counting convention) — feeds builder.py's `extruded_zones` filter
    (checks `z.get("extruded")`) and the manifest's `num_zones` (T07, not built yet).

    Args:
        idf: A loaded (post scale_baseline_idf) geomeppy/eppy IDF object.
        archetype_id: Canonical archetype ID to stamp on every zone dict.

    Returns:
        [{"name", "archetype_id", "floor_area_m2", "extruded": True}, ...]
    """
    zones = []
    for z in idf.idfobjects.get("ZONE", []):
        floor_area = z.Floor_Area
        if _is_blank_or_autosize(floor_area):
            floor_area = _measured_zone_floor_area(idf, z.Name)
        else:
            floor_area = float(floor_area)
        zones.append({
            "name": z.Name,
            "archetype_id": archetype_id,
            "floor_area_m2": floor_area,
            "extruded": True,
        })
    return zones


# ── T06 — purge_baseline_outputs() / patch_location_and_weather() ─────────────

def purge_baseline_outputs(idf: Any) -> None:
    """Deletes every baseline `Output:*`/`OutputControl:*` object in place.

    Baseline prototype IDFs ship with their own output specification (variables,
    meters, summary/monthly tables, table style). Leaving those in place while also
    calling the project's `write_outputs()` (openubem/idf/outputs.py) would duplicate
    or conflict with the harvest schema the other resolution modes rely on (plan
    §3.4/§4) — so this purges the baseline's entire output spec first, making
    `write_outputs()` the sole source of Output:*/OutputControl:* objects afterwards.

    Args:
        idf: A loaded geomeppy/eppy IDF object (mutated in place).
    """
    output_classes = [cls for cls in idf.idfobjects if cls.startswith("OUTPUT")]
    for cls in output_classes:
        for obj in list(idf.idfobjects[cls]):
            idf.removeidfobject(obj)


def patch_location_and_weather(idf: Any, epw_path: Path) -> None:
    """Overwrites `Site:Location` from the target EPW and normalizes to exactly
    one annual (1 Jan - 31 Dec) `RunPeriod`.

    Reuses builder.py's existing `_populate_site_location_from_epw()`/
    `_parse_epw_location()` — imported lazily inside this function, not at module
    level, because zoning.py imports this module at its own import time and
    builder.py imports zoning.py; a module-level import here would be a
    builder -> zoning -> layout_assigner -> builder circular import.

    `Site:WeatherFile` is not a real EnergyPlus object (plan §3.4) and is not
    created here; `SizingPeriod:DesignDay` objects are left untouched (plan §7 Q2).

    Args:
        idf: A loaded geomeppy/eppy IDF object (mutated in place).
        epw_path: Path to the target building's EPW weather file.
    """
    from openubem.idf.builder import _populate_site_location_from_epw

    _populate_site_location_from_epw(idf, epw_path)

    runperiods = list(idf.idfobjects.get("RUNPERIOD", []))
    for extra in runperiods[1:]:
        idf.removeidfobject(extra)

    rp = runperiods[0] if runperiods else idf.newidfobject("RUNPERIOD", Name="Annual")
    rp.Begin_Month = 1
    rp.Begin_Day_of_Month = 1
    rp.End_Month = 12
    rp.End_Day_of_Month = 31
