"""S03 (OPEN board row, plan PLAN_four-board-items-2026-08-20.md T02):
Build tests/fixtures/labelled_archetypes_tagrich_v3.csv covering ALL 592 tag-rich buildings
(no sampling) plus a separate, ungraded tests/fixtures/labelled_archetypes_tagpoor_v3.csv for
the remaining 290 rows.

Never imports openubem.semantic.building_classifier. Labels are derived from tag evidence
(building_tag, function_tag, and other descriptive OSM attributes in surplus_tags) only.
Floor area / height / levels are used ONLY to pick a size band inside an already
tag-determined class (e.g. Small/Medium/Large office, Midrise/Highrise apartment,
Small/Large hotel) -- never to invent the class itself. Rows where the class would have to
be inferred from size, or where tag evidence genuinely conflicts, are evidence_strength=thin,
flagged_for_ruling=yes.

Usage: python scripts/analysis/open_s03_label_tagrich_v3_2026-08-20.py
"""

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

SMALL_MAX_M2 = 2322.0
MEDIUM_MAX_M2 = 9290.0
HIGHRISE_APT_LEVELS = 9
LARGE_HOTEL_LEVELS = 5  # matches building_classifier.py _HOTEL_LARGE_MIN_LEVELS (line 194)

_COARSE = {"MidriseApartment": "residential", "HighriseApartment": "residential"}


def _coarse(archetype: str) -> str:
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


def _office_tier(levels, footprint_area_m2) -> tuple[str, str]:
    total_area = footprint_area_m2 * (levels if pd.notna(levels) else 1.0)
    lvl_txt = f"{int(levels)}fl" if pd.notna(levels) else "no floor data, footprint as proxy"
    if total_area < SMALL_MAX_M2:
        return "SmallOffice", f"{lvl_txt} x {footprint_area_m2:.0f}m2 = {total_area:.0f}m2 < {SMALL_MAX_M2:.0f} -> SmallOffice"
    if total_area < MEDIUM_MAX_M2:
        return "MediumOffice", f"{lvl_txt} x {footprint_area_m2:.0f}m2 = {total_area:.0f}m2 in [{SMALL_MAX_M2:.0f},{MEDIUM_MAX_M2:.0f}) -> MediumOffice"
    return "LargeOffice", f"{lvl_txt} x {footprint_area_m2:.0f}m2 = {total_area:.0f}m2 >= {MEDIUM_MAX_M2:.0f} -> LargeOffice"


def _apt_tier(levels) -> tuple[str, str]:
    if pd.notna(levels):
        if levels >= HIGHRISE_APT_LEVELS:
            return "HighriseApartment", f"{int(levels)}fl >= {HIGHRISE_APT_LEVELS} -> HighriseApartment"
        return "MidriseApartment", f"{int(levels)}fl < {HIGHRISE_APT_LEVELS} -> MidriseApartment"
    return "MidriseApartment", "no floor data -> MidriseApartment default (established convention, tagrich_v2)"


def _hotel_tier(levels, height_m) -> tuple[str, str]:
    if pd.notna(levels):
        if levels >= LARGE_HOTEL_LEVELS:
            return "LargeHotel", f"{int(levels)}fl >= {LARGE_HOTEL_LEVELS} -> LargeHotel (building_classifier.py:194 threshold)"
        return "SmallHotel", f"{int(levels)}fl < {LARGE_HOTEL_LEVELS} -> SmallHotel"
    if pd.notna(height_m) and height_m > 0:
        est_lvl = max(1, int(height_m // 3.5))
        tier = "LargeHotel" if est_lvl >= LARGE_HOTEL_LEVELS else "SmallHotel"
        return tier, f"no levels; height {height_m:.1f}m / 3.5 ~= {est_lvl}fl -> {tier}"
    return None, None  # caller handles the 3 no-data rows individually


# ── decision table keyed by (building_tag, function_tag_or_None) ──────────────
# rule tokens: office, apartment, hotel (need row-level tiering);
#              a bare final archetype id (direct assignment);
#              "THIN:<archetype>" (thin + flagged, best-guess archetype given)
_NA = None

_TABLE: dict[tuple[str, "str | None"], tuple[str, str, str]] = {
    # (rule, evidence_basis, note)
    ("office", _NA): ("office", "building_tag", "office tag -> Office family (tag-determined), size-tiered"),
    ("commercial", _NA): ("office", "building_tag", "commercial tag -> Office family (tag-determined), size-tiered"),
    ("office", "company"): ("office", "building_tag", "office tag -> Office family; 'company' function tag non-specific, confirms commercial use"),
    ("office", "studio"): ("office", "building_tag", "office tag -> Office family; 'studio' function tag non-specific, confirms commercial use"),
    ("commercial", "financial_advisor"): ("office", "both", "commercial + financial_advisor (professional-services shop) -> Office family, size-tiered"),
    ("roof", _NA): ("OpenUBEMUnknown", "building_tag", "'roof' building tag = canopy/non-conditioned structure, not in 30-vocab"),
    ("roof", "shelter"): ("OpenUBEMUnknown", "both", "'roof'+'shelter' = canopy/open-air structure, not in 30-vocab"),
    ("parking", "parking"): ("OpenUBEMUnknown", "both", "parking structure, not in 30-vocab"),
    ("garage", "parking"): ("OpenUBEMUnknown", "both", "parking garage, not in 30-vocab"),
    ("yes", "parking"): ("OpenUBEMUnknown", "function_tag", "function_tag=parking, non-conditioned structure, not in 30-vocab"),
    ("yes", "shelter"): ("OpenUBEMUnknown", "function_tag", "function_tag=shelter, open-air/unconditioned structure, not in 30-vocab"),
    ("train_station", _NA): ("OpenUBEMUnknown", "building_tag", "transit infrastructure, not in 30-vocab"),
    ("transportation", _NA): ("OpenUBEMUnknown", "building_tag", "transit/infrastructure, not in 30-vocab"),
    ("service", _NA): ("OpenUBEMUnknown", "building_tag", "MEP/service structure, not in 30-vocab"),
    ("power_substation", _NA): ("OpenUBEMUnknown", "building_tag", "utility infrastructure, not in 30-vocab"),
    ("bridge", _NA): ("OpenUBEMUnknown", "building_tag", "bridge structure, not a conditioned building, not in 30-vocab"),
    ("construction", _NA): ("OpenUBEMUnknown", "building_tag", "under-construction site, not a completed conditioned building"),
    ("no", "street_vendor"): ("OpenUBEMUnknown", "both", "'no' building tag (explicitly not a building) + informal street_vendor structure"),
    ("theatre", "theatre"): ("OpenUBEMUnknown", "both", "theatre/performing-arts venue, no matching archetype in 30-vocab"),
    ("commercial", "theatre"): ("OpenUBEMUnknown", "function_tag", "specific 'theatre' function overrides generic commercial building tag; no matching archetype in 30-vocab"),
    ("yes", "theatre"): ("OpenUBEMUnknown", "function_tag", "theatre venue, no matching archetype in 30-vocab"),
    ("yes", "cinema"): ("OpenUBEMUnknown", "function_tag", "cinema venue, no matching archetype in 30-vocab"),
    ("apartments", _NA): ("apartment", "building_tag", "apartments tag -> Apartment family (tag-determined), size-tiered"),
    ("dormitory", _NA): ("apartment", "building_tag", "dormitory tag -> residential use class -> Apartment family, size-tiered"),
    ("residential", _NA): ("apartment", "building_tag", "residential tag -> Apartment family, size-tiered"),
    ("hotel", _NA): ("hotel", "building_tag", "hotel tag -> Hotel family (tag-determined), size-tiered"),
    ("retail", _NA): ("RetailStandalone", "building_tag", "retail tag -> RetailStandalone (direct match)"),
    ("retail", "department_store"): ("RetailStandalone", "both", "retail + department_store -> RetailStandalone"),
    ("retail", "mall"): ("RetailStandalone", "both", "retail + mall -> RetailStandalone"),
    ("retail", "clothes"): ("RetailStandalone", "both", "retail + clothes (goods retail) -> RetailStandalone"),
    ("retail", "cafe"): ("QuickServiceRestaurant", "function_tag", "function_tag=cafe overrides retail tag -> QuickServiceRestaurant"),
    ("retail", "restaurant"): ("FullServiceRestaurant", "function_tag", "function_tag=restaurant overrides retail tag -> FullServiceRestaurant"),
    ("kiosk", _NA): ("RetailStandalone", "building_tag", "kiosk -> RetailStandalone"),
    ("kiosk", "gift"): ("RetailStandalone", "both", "kiosk + gift shop -> RetailStandalone"),
    ("train_station", "mall"): ("RetailStandalone", "function_tag", "function_tag=mall (retail concourse) overrides station infrastructure tag -> RetailStandalone"),
    ("office", "jewelry"): ("RetailStandalone", "function_tag", "jewelry shop (goods retail) overrides generic office building tag -> RetailStandalone"),
    ("yes", "cosmetics"): ("RetailStandalone", "function_tag", "cosmetics shop (goods retail) -> RetailStandalone"),
    ("yes", "marketplace"): ("RetailStandalone", "function_tag", "marketplace (retail context) -> RetailStandalone"),
    ("yes", "restaurant"): ("FullServiceRestaurant", "function_tag", "restaurant function tag -> FullServiceRestaurant"),
    ("historic", "restaurant"): ("FullServiceRestaurant", "function_tag", "restaurant function tag -> FullServiceRestaurant"),
    ("yes", "bar"): ("QuickServiceRestaurant", "function_tag", "bar function tag -> QuickServiceRestaurant"),
    ("yes", "cafe"): ("QuickServiceRestaurant", "function_tag", "cafe function tag -> QuickServiceRestaurant"),
    ("yes", "pub"): ("QuickServiceRestaurant", "function_tag", "pub function tag -> QuickServiceRestaurant"),
    ("yes", "food_court"): ("QuickServiceRestaurant", "function_tag", "food_court -> QuickServiceRestaurant (closest DOE match)"),
    ("yes", "doctors"): ("Outpatient", "function_tag", "doctors function tag -> Outpatient"),
    ("university", _NA): ("College", "building_tag", "university tag -> College (only post-secondary archetype)"),
    ("college", _NA): ("College", "building_tag", "college tag -> College"),
    ("yes", "university"): ("College", "function_tag", "university function tag -> College"),
    ("government", "government"): ("Courthouse", "both", "government use -> Courthouse (only civic archetype)"),
    ("public", "government"): ("Courthouse", "both", "public/government use -> Courthouse"),
    ("office", "government"): ("Courthouse", "function_tag", "government function tag overrides generic office building tag -> Courthouse"),
    ("public", _NA): ("Courthouse", "building_tag", "public tag -> Courthouse (civic catch-all)"),
    ("public", "townhall"): ("Courthouse", "both", "public/townhall civic use -> Courthouse"),
    ("public", "post_office"): ("Courthouse", "both", "public/post_office civic use -> Courthouse"),
    ("public", "arts_centre"): ("Courthouse", "building_tag", "public building tag (civic) -> Courthouse; arts_centre is a civic/cultural function"),
    ("commercial", "arts_centre"): ("Courthouse", "function_tag", "arts_centre = civic/cultural institution (akin to museum/library) -> Courthouse catch-all"),
    ("government", "courthouse"): ("Courthouse", "both", "government/courthouse -> Courthouse"),
    ("government", "townhall"): ("Courthouse", "both", "government/townhall civic use -> Courthouse"),
    ("yes", "courthouse"): ("Courthouse", "function_tag", "courthouse function tag -> Courthouse"),
    ("yes", "library"): ("Courthouse", "function_tag", "library (institutional use class) -> Courthouse catch-all, no dedicated library archetype"),
    ("church", "place_of_worship"): ("Courthouse", "both", "church tag (institutional use class) -> Courthouse catch-all, no dedicated worship archetype"),
    ("synagogue", "place_of_worship"): ("Courthouse", "both", "synagogue tag (institutional use class) -> Courthouse catch-all"),
    ("temple", "place_of_worship"): ("Courthouse", "both", "temple tag (institutional use class) -> Courthouse catch-all"),
    ("yes", "place_of_worship"): ("Courthouse", "function_tag", "place_of_worship function tag decisively indicates a religious/institutional building -> Courthouse catch-all (osm_to_use_class.json has no place_of_worship entry; this is a documented labeller deviation, see header)"),
}

# rows the table cannot resolve without individual research; handled by osm_id below
_ROW_OVERRIDES: dict[str, tuple[str, str, str, str, str]] = {
    # osm_id: (archetype, coarse_basis, strength, basis, note)
    "29615909": ("SmallHotel", "commercial", "thin",
                 "building_tag", "'Rowes Wharf' hotel; no levels, no height_m, no rooms count in "
                 "surplus_tags; footprint (5,334 m2) alone is not a reliable hotel-tier proxy "
                 "(compare osm_id 74451017: 1,622 m2 footprint but 403 rooms = LargeHotel) -- "
                 "defaulting SmallHotel as the more conservative guess, evidence insufficient"),
    "74451017": ("LargeHotel", "commercial", "strong",
                 "both", "'THE MIDLAND HOTEL, Chicago, a Tribute Portfolio Hotel'; no levels/height, "
                 "but surplus_tags carries rooms=403 (decisive OSM descriptive attribute) -> LargeHotel"),
    "147489619": ("LargeHotel", "commercial", "thin",
                  "building_tag", "'The Palmer House Hilton'; no levels, no height_m, no rooms count; "
                  "brand=Hilton + largest footprint of the three no-data hotels (7,614 m2) suggests "
                  "full-service scale but is not measured evidence -- defaulting LargeHotel, flagged "
                  "for ruling since no rooms/levels/height data exists"),
    "137060374": ("LargeOffice", "commercial", "thin",
                  "both", "'First United Methodist Church of Chicago' / 'Chicago Temple Building': "
                  "building_tag=office + building:levels=23 + amenity=place_of_worship + "
                  "denomination=methodist -- a genuine real-world mixed-use skyscraper (church at "
                  "street level, offices above). Tag evidence conflicts (office vs. place_of_worship) "
                  "and neither tag subordinates the other. Defaulting LargeOffice (23fl x 1416m2 = "
                  "32,568 m2 >> 9290, majority of floor area is plausibly office) but flagged for "
                  "ruling given the decisive place_of_worship tag"),
    "148043641": ("Courthouse", "commercial", "strong",
                  "function_tag", "'Downtown Islamic Center', amenity=place_of_worship, "
                  "religion=muslim -- name and religion tag decisively indicate the building is "
                  "entirely a religious institution despite generic building_tag=commercial "
                  "(surplus_tags name attribute used as decisive descriptive evidence) -> Courthouse "
                  "catch-all"),
}


def label_row(row: pd.Series) -> tuple[str, str, str, str, str]:
    """Return (archetype, evidence_basis, evidence_strength, flagged, notes)."""
    osm_id = str(row["osm_id"])
    if osm_id in _ROW_OVERRIDES:
        aid, _, strength, basis, note = _ROW_OVERRIDES[osm_id]
        flagged = "yes" if strength == "thin" else "no"
        return aid, basis, strength, flagged, note

    bt = str(row["building_tag"]).strip().lower() if pd.notna(row["building_tag"]) else ""
    ft_raw = str(row["function_tag"]).strip().lower() if pd.notna(row["function_tag"]) else ""
    ft = ft_raw if ft_raw else None
    levels = row["levels"]
    height_m = row["height_m"]
    footprint = row["footprint_area_m2"]

    key = (bt, ft)
    if key not in _TABLE:
        # should not happen for the 66 combos present in the 592-row pool
        return "OpenUBEMUnknown", "building_tag", "thin", "yes", (
            f"no labelling rule covers building_tag={bt!r} function_tag={ft!r} -- flagged for ruling"
        )

    rule, basis, note = _TABLE[key]

    if rule == "office":
        aid, tier_note = _office_tier(levels, footprint)
        return aid, basis, "strong", "no", f"{note}; {tier_note}"
    if rule == "apartment":
        aid, tier_note = _apt_tier(levels)
        return aid, basis, "strong", "no", f"{note}; {tier_note}"
    if rule == "hotel":
        aid, tier_note = _hotel_tier(levels, height_m)
        if aid is None:
            # should be covered by _ROW_OVERRIDES (the 3 no-data hotels); guard anyway
            return "SmallHotel", basis, "thin", "yes", f"{note}; no levels/height data -> defaulting SmallHotel, flagged"
        return aid, basis, "strong", "no", f"{note}; {tier_note}"

    # direct archetype assignment, no size involved
    return rule, basis, "strong", "no", note


def main() -> None:
    pool = load_pool()
    mask = tagrich_mask(pool)
    tagrich = pool[mask].copy()
    tagpoor = pool[~mask].copy()

    n_bos = int((tagrich["source_fixture"] == "boston_downtown_500m").sum())
    n_chi = int((tagrich["source_fixture"] == "chicago_loop_500m").sum())
    print(f"pool verification: tagrich={len(tagrich)} (boston={n_bos}, chicago={n_chi}) tagpoor={len(tagpoor)}")
    assert len(tagrich) == 592 and n_bos == 233 and n_chi == 359 and len(tagpoor) == 290, "STOP: pool counts do not match §5"

    labels = tagrich.apply(label_row, axis=1, result_type="expand")
    tagrich["expected_archetype"] = labels[0]
    tagrich["evidence_basis"] = labels[1]
    tagrich["evidence_strength"] = labels[2]
    tagrich["flagged_for_ruling"] = labels[3]
    tagrich["notes"] = labels[4]
    tagrich["expected_coarse_class"] = tagrich["expected_archetype"].map(_coarse)

    valid30 = json.loads(
        (REPO_ROOT / "openubem/data/openstudio_archetypes.json").read_text(encoding="utf-8")
    )
    valid_ids = {a["archetype_id"] for a in valid30["archetypes"]}
    bad = set(tagrich["expected_archetype"].unique()) - valid_ids
    assert not bad, f"STOP: labels outside 30-vocab: {bad}"

    dupes = tagrich["osm_id"].duplicated().sum()
    assert dupes == 0, f"STOP: {dupes} duplicate osm_id in tagrich pool"

    thin_bad = tagrich[(tagrich["evidence_strength"] == "thin") & (tagrich["flagged_for_ruling"] != "yes")]
    assert len(thin_bad) == 0, f"STOP: {len(thin_bad)} thin rows not flagged"

    n_flagged = int((tagrich["flagged_for_ruling"] == "yes").sum())
    print(f"n_flagged={n_flagged}")
    print(tagrich["expected_archetype"].value_counts().to_string())
    print("strength counts:")
    print(tagrich["evidence_strength"].value_counts().to_string())

    out_cols = [
        "osm_id", "source_fixture", "building_tag", "function_tag", "levels",
        "height_m", "footprint_area_m2", "expected_archetype", "expected_coarse_class",
        "notes", "evidence_basis", "evidence_strength", "flagged_for_ruling",
    ]
    out = tagrich[out_cols].copy()

    header_comment = (
        "# labeller=claude-sonnet-5, plan=PLAN_four-board-items-2026-08-20.md T02, "
        "pool=592 tag-rich of 882 (union: building_tag present and != 'yes' OR function_tag "
        "present, boston_downtown_500m.gpkg [233] + chicago_loop_500m.gpkg [359]), NO SAMPLING "
        "(user ruling 2026-08-20: widened to all the data), tagpoor=290 (separate ungraded sheet), "
        f"snapshot_date=2026-08-20, source_gpkgs=tests/fixtures/boston_downtown_500m.gpkg;"
        "tests/fixtures/chicago_loop_500m.gpkg, "
        f"n_flagged_for_ruling={n_flagged}, "
        "labelling_basis=tag evidence only (building_tag/function_tag/surplus_tags); floor "
        "area/height/levels used only to pick a size band inside an already tag-determined "
        "class (Small/Medium/Large office, Midrise/Highrise apartment, Small/Large hotel), never "
        "to invent the class itself; hotel tier threshold matches building_classifier.py:194 "
        "(_HOTEL_LARGE_MIN_LEVELS=5, not v2's 4); TallBuilding/SuperTallBuilding height overrides "
        "are deliberately NOT applied in this exam (T02 forbids using height/levels for anything "
        "but sub-tiering, so a tall hotel/office stays in its tag-determined family) -- this is a "
        "documented, intentional divergence from the classifier's own rule 1a/1b and will surface "
        "as a confusion pair, not a labelling error; 5 rows hand-resolved from surplus_tags "
        "name/rooms/religion attributes (osm_id 29615909,74451017,147489619,137060374,148043641)"
    )

    out_path = REPO_ROOT / "tests/fixtures/labelled_archetypes_tagrich_v3.csv"
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(header_comment + "\n")
    out.to_csv(out_path, mode="a", index=False, encoding="utf-8-sig")
    print(f"\nwrote {out_path} ({len(out)} rows)")

    tagpoor_out = tagpoor[[
        "osm_id", "source_fixture", "building_tag", "function_tag", "levels",
        "height_m", "footprint_area_m2",
    ]].copy()
    tagpoor_out["expected_archetype"] = ""
    tagpoor_out["expected_coarse_class"] = ""
    tagpoor_out["notes"] = "tag-poor: excluded from labelling (v2 objection was size-only class inference)"
    tagpoor_out["evidence_basis"] = "size_only"
    tagpoor_out["evidence_strength"] = ""
    tagpoor_out["flagged_for_ruling"] = "no"
    tagpoor_out = tagpoor_out[out_cols]

    poor_header = (
        "# ungraded tag-poor sheet (T02 deliverable #2): 290 rows with building_tag missing/'yes' "
        "AND function_tag missing, from the same 882-row pool as labelled_archetypes_tagrich_v3.csv. "
        "expected_archetype intentionally left empty -- these rows exist only to keep the size-only "
        "objection visible, they are NOT labelled or graded. snapshot_date=2026-08-20"
    )
    poor_path = REPO_ROOT / "tests/fixtures/labelled_archetypes_tagpoor_v3.csv"
    with open(poor_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(poor_header + "\n")
    tagpoor_out.to_csv(poor_path, mode="a", index=False, encoding="utf-8-sig")
    print(f"wrote {poor_path} ({len(tagpoor_out)} rows)")


if __name__ == "__main__":
    main()
