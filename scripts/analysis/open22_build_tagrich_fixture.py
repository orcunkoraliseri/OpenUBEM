"""T03 (OPEN-22): build tests/fixtures/labelled_archetypes_tagrich_v2.csv.

Draws the same seeded, stratified 100-row sample as open22_sample_tagrich.py from
the 592-row tag-rich pool, then labels every row from SOURCE TAG EVIDENCE — never by
importing or calling openubem.semantic.building_classifier. The classifier is not
imported anywhere in this file.

Labelling basis (documented once here, applied uniformly, and quoted in the fixture's
own provenance comment):

  1. OSM building=* tag semantics (what the tag denotes in the real world) — from the
     OSM wiki convention and this project's own osm_to_use_class.json vocabulary
     table (openubem/data/osm_to_use_class.json), which is a static data file mapping
     OSM tags to coarse use classes, not classifier logic.
  2. The 30-archetype vocabulary (openubem/data/openstudio_archetypes.json) — which
     archetype IDs exist at all.
  3. Where a row's building/function tag denotes a structure that is not a conditioned
     building in the DOE/OpenStudio prototype sense at all (parking garage, canopy/
     roof, transit station, MEP/service structure, open shelter) -> OpenUBEMUnknown.
     This is a directly decidable negative, not a guess.
  4. Office/commercial size tiering uses the same LBNL-CBES 2322 / 9290 m^2 total-
     floor-area bins already cited (and externally sourced) in the ORIGINAL fixture's
     own provenance comment (E-R3-3) — total floor area = footprint_area_m2 *
     max(levels, 1), footprint alone when levels is missing. This is an external,
     published boundary, not something read off classifier output.
  5. A >=20-level building is labelled TallBuilding, >=40-level SuperTallBuilding,
     REGARDLESS of the specific commercial tag — this exact convention is already
     the documented, director-ratified labelling practice used to build
     labelled_archetypes_50.csv (see e.g. its own notes column: "commercial 31fl >=
     20 -> TallBuilding", "office 152m ~46fl >= 40 -> SuperTallBuilding"). Re-using an
     already-ratified labelling convention is not the same as reading classifier
     output; it is the established human labelling standard for this exam.
  6. Apartments: >=9 levels -> HighriseApartment, else MidriseApartment; missing
     levels defaults to MidriseApartment — again the existing fixture's own
     documented default ("apartments tag no floor data -> MidriseApartment default").
  7. Hotels: >=4 levels -> LargeHotel, <4 -> SmallHotel (existing fixture's own
     documented threshold). Missing levels -> UNDETERMINED (no footprint-based hotel
     tier convention is available from any source consulted; guessing is refused).
  8. Retail: single-storey retail -> RetailStandalone. Multi-storey "retail"-tagged
     buildings have no clear DOE-prototype-retail match (all three retail archetypes
     are single-storey forms) -> UNDETERMINED.
  9. University -> College (the only post-secondary archetype).
 10. public+government / government+government, when NOT overridden by a >=20-level
     TallBuilding call, -> Courthouse — the only civic/government archetype in the
     30-vocabulary, and the same mapping the ORIGINAL ratified fixture already uses
     for a "public"+"government" row (osm_id 108240968, expected_archetype
     Courthouse). public+townhall is treated the same way (nearest available civic
     archetype; no closer match exists).

Anything not covered above, or where the evidence is internally contradictory, is
marked UNDETERMINED and excluded from grading (kept in the file, visibly, not
silently dropped).

Usage: python scripts/analysis/open22_build_tagrich_fixture.py <output_csv>
"""

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

SEED = 20260812
TARGET = 100
SMALL_MAX_M2 = 2322.0
MEDIUM_MAX_M2 = 9290.0
TALL_LEVELS = 20
SUPERTALL_LEVELS = 40
HIGHRISE_APT_LEVELS = 9
LARGE_HOTEL_LEVELS = 4

REPO_ROOT = Path(__file__).resolve().parents[2]

_COARSE = {
    "MidriseApartment": "residential",
    "HighriseApartment": "residential",
}


def _coarse(archetype: str) -> str:
    if archetype == "UNDETERMINED":
        return "UNDETERMINED"
    return _COARSE.get(archetype, "commercial")


def load_pool() -> pd.DataFrame:
    bos = gpd.read_file(REPO_ROOT / "tests/fixtures/boston_downtown_500m.gpkg")
    chi = gpd.read_file(REPO_ROOT / "tests/fixtures/chicago_loop_500m.gpkg")
    bos["source_fixture"] = "boston_downtown_500m"
    chi["source_fixture"] = "chicago_loop_500m"
    bos_df = pd.DataFrame(bos.drop(columns="geometry"))
    chi_df = pd.DataFrame(chi.drop(columns="geometry"))
    return pd.concat([bos_df, chi_df], ignore_index=True)


def tagrich_mask(pool: pd.DataFrame) -> pd.Series:
    bt = pool["building_tag"].astype(str)
    ft = pool["function_tag"].astype(str)
    bt_present_not_yes = pool["building_tag"].notna() & (bt.str.strip() != "") & (bt.str.lower() != "yes")
    ft_present = pool["function_tag"].notna() & (ft.str.strip() != "")
    return bt_present_not_yes | ft_present


def stratum_of(row) -> str:
    bt = str(row["building_tag"]).strip()
    if bt and bt.lower() != "yes":
        return bt.lower()
    return "function:" + str(row["function_tag"]).strip().lower()


def allocate(counts: pd.Series, target: int) -> pd.Series:
    n = counts.sum()
    quota = counts * target / n
    alloc = np.floor(quota).astype(int)
    deficit = target - alloc.sum()
    remainder = quota - np.floor(quota)
    room = counts - alloc
    order = remainder.sort_values(ascending=False).index.tolist()
    i = 0
    guard = 0
    while deficit > 0 and guard < 100_000:
        s = order[i % len(order)]
        if room[s] > 0:
            alloc[s] += 1
            room[s] -= 1
            deficit -= 1
        i += 1
        guard += 1
    assert alloc.sum() == target
    assert (alloc <= counts).all()
    return alloc


def draw_sample() -> pd.DataFrame:
    pool = load_pool()
    sub = pool[tagrich_mask(pool)].copy()
    assert len(sub) == 592, f"tag-rich pool is {len(sub)}, expected 592"
    sub["stratum"] = sub.apply(stratum_of, axis=1)
    counts = sub["stratum"].value_counts()
    alloc = allocate(counts, TARGET)
    picked = []
    for stratum, k in alloc.items():
        if k == 0:
            continue
        grp = sub[sub["stratum"] == stratum]
        picked.append(grp if k >= len(grp) else grp.sample(n=int(k), random_state=SEED))
    sample = pd.concat(picked, ignore_index=True)
    assert len(sample) == TARGET
    return sample.sort_values(["source_fixture", "stratum", "osm_id"]).reset_index(drop=True)


def _office_tier(levels, footprint_area_m2) -> tuple[str, str]:
    """Office/commercial size-tier + tall-building override, from §4 rule 4-5 above."""
    if pd.notna(levels) and levels >= SUPERTALL_LEVELS:
        return "SuperTallBuilding", f"{int(levels)}fl >= {SUPERTALL_LEVELS} -> SuperTallBuilding (height override)"
    if pd.notna(levels) and levels >= TALL_LEVELS:
        return "TallBuilding", f"{int(levels)}fl >= {TALL_LEVELS} -> TallBuilding (height override)"
    total_area = footprint_area_m2 * (levels if pd.notna(levels) else 1.0)
    lvl_txt = f"{int(levels)}fl" if pd.notna(levels) else "no floor data, footprint as proxy"
    if total_area < SMALL_MAX_M2:
        return "SmallOffice", f"{lvl_txt} x {footprint_area_m2:.0f}m2 = {total_area:.0f}m2 < {SMALL_MAX_M2:.0f} -> SmallOffice"
    if total_area < MEDIUM_MAX_M2:
        return "MediumOffice", f"{lvl_txt} x {footprint_area_m2:.0f}m2 = {total_area:.0f}m2 in [{SMALL_MAX_M2:.0f},{MEDIUM_MAX_M2:.0f}) -> MediumOffice"
    return "LargeOffice", f"{lvl_txt} x {footprint_area_m2:.0f}m2 = {total_area:.0f}m2 >= {MEDIUM_MAX_M2:.0f} -> LargeOffice"


def label_row(row) -> tuple[str, str]:
    bt = str(row["building_tag"]).strip().lower() if pd.notna(row["building_tag"]) else ""
    ft = str(row["function_tag"]).strip().lower() if pd.notna(row["function_tag"]) else ""
    levels = row["levels"]
    footprint = row["footprint_area_m2"]

    if bt == "roof":
        return "OpenUBEMUnknown", "'roof' building tag = canopy/non-conditioned structure, not in 30-vocab -> fallback (roof-tag decision, see report)"
    if ft == "shelter":
        return "OpenUBEMUnknown", "'shelter' function tag = open-air/unconditioned structure, not in 30-vocab -> fallback"
    if ft == "parking" or bt in {"parking", "garage"}:
        return "OpenUBEMUnknown", "parking/garage structure, not in 30-vocab -> fallback"
    if ft == "restaurant":
        return "FullServiceRestaurant", "restaurant function tag direct match"
    if bt in {"train_station", "transportation", "service"}:
        return "OpenUBEMUnknown", f"'{bt}' building tag, not in 30-vocab (transit/infrastructure) -> fallback"
    if bt == "kiosk":
        return "RetailStandalone", "kiosk + retail function tag -> small standalone retail"
    if bt == "university":
        return "College", "university tag -> College (only post-secondary archetype)"
    if bt == "apartments":
        if pd.notna(levels):
            if levels >= HIGHRISE_APT_LEVELS:
                return "HighriseApartment", f"apartments tag {int(levels)}fl >= {HIGHRISE_APT_LEVELS} -> HighriseApartment"
            return "MidriseApartment", f"apartments tag {int(levels)}fl < {HIGHRISE_APT_LEVELS} -> MidriseApartment"
        return "MidriseApartment", "apartments tag, no floor data -> MidriseApartment default"
    if bt == "hotel":
        if pd.notna(levels):
            if levels >= LARGE_HOTEL_LEVELS:
                return "LargeHotel", f"hotel tag {int(levels)}fl >= {LARGE_HOTEL_LEVELS} -> LargeHotel"
            return "SmallHotel", f"hotel tag {int(levels)}fl < {LARGE_HOTEL_LEVELS} -> SmallHotel"
        return "UNDETERMINED", "hotel tag but no level data at all -> no source-evidenced tier boundary available, refusing to guess"
    if bt == "retail":
        if pd.notna(levels) and levels == 1:
            extra = f" + function_tag={ft}" if ft else ""
            return "RetailStandalone", f"retail tag{extra}, single storey -> RetailStandalone"
        return "UNDETERMINED", "retail tag, multi-storey or unknown storey count -> no DOE retail archetype is multi-storey, refusing to guess"
    if bt in {"government"} or (bt == "public" and ft in {"government", "townhall"}):
        arch, reason = _office_tier(levels, footprint)
        if arch in {"TallBuilding", "SuperTallBuilding"}:
            return arch, f"government/civic use, {reason}"
        return "Courthouse", f"government/civic use ({bt}/{ft or 'n/a'}), no height override triggered -> Courthouse (only civic archetype; matches ratified precedent osm_id 108240968)"
    if bt in {"office", "commercial"}:
        return _office_tier(levels, footprint)

    return "UNDETERMINED", f"no labelling rule covers building_tag={bt!r} function_tag={ft!r}"


def main(out_csv: str) -> None:
    sample = draw_sample()
    labels = sample.apply(label_row, axis=1, result_type="expand")
    sample["expected_archetype"] = labels[0]
    sample["expected_coarse_class"] = sample["expected_archetype"].map(_coarse)
    sample["notes"] = labels[1]

    n_undetermined = (sample["expected_archetype"] == "UNDETERMINED").sum()
    print(f"n={len(sample)}  n_undetermined={n_undetermined}  "
          f"n_graded={len(sample) - n_undetermined}")
    print(sample["expected_archetype"].value_counts().to_string())

    out_cols = [
        "osm_id", "source_fixture", "building_tag", "function_tag", "levels",
        "height_m", "footprint_area_m2", "expected_archetype", "expected_coarse_class",
        "notes",
    ]
    out = sample[out_cols].copy()

    header_comment = (
        "# labeller=claude-opus-5, director-audited, seed=20260812, "
        "pool=592 (tag-rich union: building_tag present and != 'yes' [558] OR "
        "function_tag present [100], from boston_downtown_500m.gpkg + "
        "chicago_loop_500m.gpkg), sample=100 stratified by building_tag "
        "(or function_tag when building_tag=='yes'), proportional Hare-quota "
        "allocation capped per stratum, snapshot_date=2026-08-12, "
        "source_gpkgs=tests/fixtures/boston_downtown_500m.gpkg;"
        "tests/fixtures/chicago_loop_500m.gpkg, "
        f"n_undetermined_excluded_from_grading={n_undetermined}, "
        "roof_tag_decision=included as OpenUBEMUnknown (canopy/non-building "
        "evidence, not excluded from the sample)"
    )

    out_path = Path(out_csv)
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(header_comment + "\n")
    out.to_csv(out_path, mode="a", index=False, encoding="utf-8-sig")
    print(f"\nwrote {out_path} ({len(out)} rows + provenance comment + header)")


if __name__ == "__main__":
    main(sys.argv[1])
