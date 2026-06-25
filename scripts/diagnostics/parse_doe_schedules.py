"""
Parse Schedule:Compact objects from DOE Commercial Prototype STD2013 IDFs.

For each schedule group, extracts the dominant-zone Occupancy/Lighting/Equipment
profiles into Weekday / Saturday / AllOtherDays day-types.

Outputs:
  - Console: parsed profiles + EFLH cross-check vs RESULT_*.md values
  - docs/implementation/scheduleDigitization/PROVENANCE.md
  - docs/implementation/scheduleDigitization/parsed_profiles.json

Usage:
  python scripts/diagnostics/parse_doe_schedules.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_DIR = REPO_ROOT / "docs" / "implementation" / "scheduleDigitization" / "sources"
OUT_DIR = REPO_ROOT / "docs" / "implementation" / "scheduleDigitization"


# ---------------------------------------------------------------------------
# IDF parser — line-by-line tokenizer to avoid multi-line comment stripping
# ---------------------------------------------------------------------------

def _idf_tokens(idf_text: str) -> list[str]:
    """
    Tokenize an IDF text into a flat list of field values.

    Strategy:
      1. Split into lines.
      2. Per line: strip the trailing !- comment.
      3. Split each cleaned line on commas and semicolons.
      4. Flatten; skip blank tokens.
    Returns list of non-empty string tokens (field values, keywords).
    Terminators (commas/semicolons) are NOT preserved.
    """
    tokens: list[str] = []
    for raw_line in idf_text.splitlines():
        # Strip inline comment (everything from first ! onward)
        comment_idx = raw_line.find("!")
        if comment_idx >= 0:
            line = raw_line[:comment_idx]
        else:
            line = raw_line
        # Split on , and ; (field separators in IDF)
        for part in re.split(r"[,;]", line):
            tok = part.strip()
            if tok:
                tokens.append(tok)
    return tokens


def parse_schedule_compact(
    idf_text: str, schedule_name: str
) -> dict[str, list[tuple[str, float]]]:
    """
    Extract a named Schedule:Compact from the IDF token stream.

    Returns dict with keys 'Weekdays', 'Saturday', 'AllOtherDays'.
    Design-day blocks (SummerDesignDay, WinterDesignDay) are dropped.
    AllDays -> populates all three day-types.
    """
    tokens = _idf_tokens(idf_text)
    n = len(tokens)

    # Find the token index where this schedule object begins
    start_idx: int | None = None
    for i, tok in enumerate(tokens):
        # Find SCHEDULE:COMPACT keyword (case-insensitive)
        if not re.match(r"(?i)^SCHEDULE\s*:\s*COMPACT$", tok):
            continue
        # Next token is the name
        if i + 1 < n and tokens[i + 1].lower() == schedule_name.lower():
            start_idx = i
            break

    if start_idx is None:
        return {}

    # Extract the block: from start_idx up to (but not including) the next
    # SCHEDULE:COMPACT keyword (or end of tokens)
    end_idx = n
    for i in range(start_idx + 1, n):
        if re.match(r"(?i)^SCHEDULE\s*:\s*COMPACT$", tokens[i]):
            end_idx = i
            break

    block_tokens = tokens[start_idx : end_idx]
    # block_tokens[0] = "SCHEDULE:COMPACT" / "Schedule:Compact"
    # block_tokens[1] = name
    # block_tokens[2] = type-limits  (e.g. "Fraction")
    # block_tokens[3+] = Through:/For:/Until:/value fields
    body = block_tokens[3:]

    # Day-type parsing helpers
    def parse_for_token(for_str: str) -> list[str]:
        """
        Map a For: <daytype(s)> string to canonical day-type keys.

        Design-day tokens (SummerDesignDay, WinterDesignDay) are stripped out
        but the remaining real-day tokens are still honored.
        e.g. 'Weekdays Saturday WinterDesignDay' -> ['Weekdays', 'Saturday']
        """
        s = for_str.strip().lower()
        # Remove design-day tokens (they're sizing-only; strip them but keep the rest)
        s = re.sub(r"\b(summer|winter)\s*design\s*day\b", "", s).strip()
        # If after stripping design days nothing meaningful remains, skip
        if not s or s in ("", " "):
            return []
        # Skip holiday-only (no other day type present)
        s_nospace = re.sub(r"\s+", "", s)
        if "holiday" in s_nospace and "allotherdays" not in s_nospace and "weekday" not in s_nospace and "saturday" not in s_nospace:
            return []
        result: list[str] = []
        # AllDays (overrides everything)
        if s_nospace == "alldays":
            return ["Weekdays", "Saturday", "AllOtherDays"]
        # Weekdays / Weekday
        if "weekdays" in s:
            result.append("Weekdays")
        elif "weekday" in s:
            result.append("Weekdays")
        # Saturday
        if "saturday" in s:
            result.append("Saturday")
        # Sunday / AllOtherDays / Weekend
        if "sunday" in s or "allotherdays" in s_nospace or "weekend" in s:
            if "AllOtherDays" not in result:
                result.append("AllOtherDays")
        return result

    day_profiles: dict[str, list[tuple[str, float]]] = {
        "Weekdays": [],
        "Saturday": [],
        "AllOtherDays": [],
    }
    active_day_types: list[str] = []
    # Track Through: periods; we use the LAST Through: 12/31 period as the primary.
    # Collect all periods first, then pick.
    periods: list[tuple[str, dict]] = []  # (date_str, day_profiles dict)
    current_period_date = "12/31"
    current_period_profiles: dict[str, list[tuple[str, float]]] = {
        "Weekdays": [], "Saturday": [], "AllOtherDays": [],
    }

    i = 0
    while i < len(body):
        tok = body[i]
        tl = tok.lower().replace(" ", "")

        # Through: MM/DD — start a new period
        if tok.lower().startswith("through:") or tok.lower().startswith("through :"):
            # Save any completed period
            if any(current_period_profiles.values()):
                periods.append((current_period_date, current_period_profiles))
            date_raw = re.sub(r"(?i)^through\s*:?\s*", "", tok).strip()
            if not date_raw and i + 1 < len(body):
                i += 1
                date_raw = body[i]
            current_period_date = date_raw
            current_period_profiles = {"Weekdays": [], "Saturday": [], "AllOtherDays": []}
            active_day_types = []
            i += 1
            continue

        # For: <day-type(s)>
        if tok.lower().startswith("for:") or tok.lower().startswith("for "):
            for_val = re.sub(r"(?i)^for\s*:?\s*", "", tok).strip()
            if not for_val and i + 1 < len(body):
                i += 1
                for_val = body[i]
            active_day_types = parse_for_token(for_val)
            i += 1
            continue

        # Until: HH:MM
        if tok.lower().startswith("until:") or tok.lower().startswith("until :"):
            time_raw = re.sub(r"(?i)^until\s*:?\s*", "", tok).strip()
            if ":" in time_raw:
                try:
                    h_str, m_str = time_raw.split(":", 1)
                    hh = int(h_str)
                    mm = int(m_str)
                    time_key = f"{hh:02d}:{mm:02d}"
                except ValueError:
                    i += 1
                    continue
            else:
                i += 1
                continue

            # Next token is the fraction value
            i += 1
            if i < len(body):
                val_tok = body[i]
                # Make sure it's a number, not a keyword
                if not (val_tok.lower().startswith("for") or
                        val_tok.lower().startswith("until") or
                        val_tok.lower().startswith("through")):
                    try:
                        frac = float(val_tok)
                        for dt in active_day_types:
                            current_period_profiles[dt].append((time_key, frac))
                        i += 1
                    except ValueError:
                        pass
            continue

        i += 1

    # Save the last period
    if any(current_period_profiles.values()):
        periods.append((current_period_date, current_period_profiles))

    if not periods:
        return {}

    # Multi-period schedules (e.g. school summer/winter split):
    # Use the Through: 12/31 period if present (school year Oct-Dec = dominant season).
    # If only one period exists, use it directly.
    # For schedules where the FIRST period is the primary school-year block (through 6/30),
    # we prefer the LONGEST period. Since all have Through: 12/31 as last, use that.
    for_1231 = [p for p in periods if p[0].strip() == "12/31"]
    if for_1231:
        day_profiles = for_1231[-1][1]  # last Through: 12/31 period
    else:
        # Fall back to last period
        day_profiles = periods[-1][1]

    return day_profiles


# ---------------------------------------------------------------------------
# Group → IDF file + object names (per PLAN §4 + AUDIT rulings)
# ---------------------------------------------------------------------------

# Note: RESULT_1's object name map uses STD2022 names in some places.
# We verified against the actual STD2013 IDFs — object names match for
# MediumOffice (BLDG_OCC_SCH / ltg_sch_office / BLDG_EQUIP_SCH).
# BLDG_LIGHT_SCH is the STD2013 lighting object name for retail/warehouse/school/hospital/outpatient.
# For Restaurant STD2013, BLDG_LIGHT_SCH may differ from STD2022 ltg_sch_dining.

GROUP_CONFIG: dict[str, dict] = {
    "Office": {
        "idf": SOURCES_DIR / "MediumOffice_90.1-2013.idf",
        "url": "https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_OfficeMedium_STD2013.zip",
        "idf_filename_in_zip": "ASHRAE901_OfficeMedium_STD2013_Buffalo.idf",
        "Occupancy": "BLDG_OCC_SCH",
        "Lighting":  "ltg_sch_office",
        "Equipment": "BLDG_EQUIP_SCH",
        "note": "MediumOffice dominant-zone whole-building schedules",
    },
    "Retail": {
        "idf": SOURCES_DIR / "RetailStandalone_90.1-2013.idf",
        "url": "https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RetailStandalone_STD2013.zip",
        "idf_filename_in_zip": "ASHRAE901_RetailStandalone_STD2013_Buffalo.idf",
        "Occupancy": "BLDG_OCC_SCH",
        "Lighting":  "ltg_sch_sale",
        "Equipment": "BLDG_EQUIP_SCH",
        "note": "RetailStandalone dominant-zone; ltg_sch_sale = main sales floor (dominant area per PLAN §4); also used for SuperMarket",
    },
    "School": {
        "idf": SOURCES_DIR / "SchoolPrimary_90.1-2013.idf",
        "url": "https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_SchoolPrimary_STD2013.zip",
        "idf_filename_in_zip": "ASHRAE901_SchoolPrimary_STD2013_Buffalo.idf",
        "Occupancy": "BLDG_OCC_SCH",
        "Lighting":  "ltg_sch_classroom",
        "Equipment": "BLDG_EQUIP_SCH",
        "note": "PrimarySchool classroom-dominant; ltg_sch_classroom per PLAN §4; BLDG_OCC_SCH has seasonal structure (Through periods) — parser uses Through:12/31 period",
    },
    "Hotel": {
        "idf": SOURCES_DIR / "SmallHotel_90.1-2013.idf",
        "url": "energycodes.gov STD2013 (already saved in sources/)",
        "idf_filename_in_zip": "SmallHotel_90.1-2013.idf",
        "Occupancy": "GuestRoom_Occ_Sch",
        "Lighting":  "ltg_sch_guestroom",
        "Equipment": "Guestroom_Eqp_Sch_Adva",
        "note": "SmallHotel guest-room dominant zone",
    },
    "Apartment": {
        "idf": SOURCES_DIR / "MidriseApartment_90.1-2013.idf",
        "url": "energycodes.gov STD2013 (already saved in sources/)",
        "idf_filename_in_zip": "MidriseApartment_90.1-2013.idf",
        "Occupancy": "OCC_APT_SCH_WORKING_FAMILY",
        "Lighting":  "ltg_sch_apartment_hardwired",
        "Equipment": "EQP_APT_SCH",
        "note": "MidriseApartment dwelling-unit dominant zone; lighting diversity-baked (peak=0.181 verbatim)",
    },
    "Warehouse": {
        "idf": SOURCES_DIR / "Warehouse_90.1-2013.idf",
        "url": "https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_Warehouse_STD2013.zip",
        "idf_filename_in_zip": "ASHRAE901_Warehouse_STD2013_Buffalo.idf",
        "Occupancy": "BLDG_OCC_SCH",
        "Lighting":  "ltg_sch_bulk_storage",
        "Equipment": "Bulk Storage Plug Schedule",
        "note": "Warehouse bulk-storage dominant zone; ltg_sch_bulk_storage + Bulk Storage Plug Schedule per PLAN §4 / RESULT_1 map",
    },
    "Restaurant": {
        "idf": SOURCES_DIR / "Restaurant_FullServiceRestaurant.idf",
        "url": "energycodes.gov STD2013 (already saved in sources/)",
        "idf_filename_in_zip": "Restaurant_FullServiceRestaurant.idf",
        "Occupancy": "BLDG_OCC_SCH",
        "Lighting":  "ltg_sch_dining",
        "Equipment": "BLDG_EQUIP_SCH",
        "note": "FullServiceRestaurant dining-zone dominant; ltg_sch_dining per PLAN §4; BLDG_EQUIP_SCH = electric plug (kitchen gas out of scope)",
    },
    "Hospital": {
        "idf": SOURCES_DIR / "Hospital_90.1-2013.idf",
        "url": "https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_Hospital_STD2013.zip",
        "idf_filename_in_zip": "ASHRAE901_Hospital_STD2013_Buffalo.idf",
        "Occupancy": "BLDG_OCC_SCH",
        "Lighting":  "ltg_sch10_patient_room",
        "Equipment": "BLDG_EQUIP_SCH",
        "note": "Hospital patient-room dominant; ltg_sch10_patient_room per PLAN §4 / RESULT_1 map",
    },
    "Outpatient": {
        "idf": SOURCES_DIR / "OutPatientHealthCare_90.1-2013.idf",
        "url": "https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_OutPatientHealthCare_STD2013.zip",
        "idf_filename_in_zip": "ASHRAE901_OutPatientHealthCare_STD2013_Buffalo.idf",
        "Occupancy": "BLDG_OCC_SCH",
        "Lighting":  "ltg_sch_exam",
        "Equipment": "BLDG_EQUIP_SCH",
        "note": "OutPatientHealthCare exam-room dominant; ltg_sch_exam per PLAN §4 / RESULT_1 map",
    },
}


# ---------------------------------------------------------------------------
# EFLH calculation
# ---------------------------------------------------------------------------

def compute_eflh(profile: dict[str, list[tuple[str, float]]]) -> float:
    """Annual EFLH = weekday*261 + saturday*52 + allotherdays*52."""
    def daily_eflh(day_pts: list[tuple[str, float]]) -> float:
        if not day_pts:
            return 0.0
        total = 0.0
        prev_h = 0.0
        for time_str, frac in day_pts:
            h_str, m_str = time_str.split(":")
            h = int(h_str) + int(m_str) / 60.0
            total += (h - prev_h) * frac
            prev_h = h
        return total

    wd = daily_eflh(profile.get("Weekdays", []))
    sa = daily_eflh(profile.get("Saturday", []))
    od = daily_eflh(profile.get("AllOtherDays", []))
    return wd * 261 + sa * 52 + od * 52


# ---------------------------------------------------------------------------
# RESULT cross-check reference EFLH values (from RESULT_2/4/5 verified tables)
# ---------------------------------------------------------------------------

RESULT_EFLH_REF: dict[str, dict[str, float | None]] = {
    "Apartment": {
        "Lighting":   527.0,   # RESULT_2 + audit byte-verified
        "Equipment":  None,
        "Occupancy":  None,
    },
    "Office": {
        "Occupancy":  2844.20,  # RESULT_4 (tesp lineage; deviation expected if STD2013 differs)
        "Lighting":   3235.30,
        "Equipment":  4744.40,
    },
    "Retail":     {"Occupancy": None, "Lighting": None, "Equipment": None},
    "Warehouse":  {"Occupancy": None, "Lighting": None, "Equipment": None},
    "School": {
        "Occupancy":  1761.75,  # RESULT_5 (openstudio lineage)
        "Lighting":   4193.89,
        "Equipment":  4475.40,
    },
    "Hospital":   {"Occupancy": None, "Lighting": None, "Equipment": None},
    "Outpatient": {"Occupancy": None, "Lighting": None, "Equipment": None},
    "Restaurant": {"Occupancy": None, "Lighting": None, "Equipment": None},
    "Hotel":      {"Occupancy": None, "Lighting": None, "Equipment": None},
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    results: dict[str, dict] = {}
    parse_errors: list[str] = []

    # First pass: probe actual schedule names in each IDF
    for group, cfg in GROUP_CONFIG.items():
        idf_path: Path = cfg["idf"]
        if not idf_path.exists():
            parse_errors.append(f"MISSING IDF: {idf_path}")
            print(f"[ERROR] Missing IDF for {group}: {idf_path}", file=sys.stderr)
            continue

        idf_text = idf_path.read_text(encoding="utf-8", errors="replace")
        group_result: dict[str, dict] = {}

        for family in ("Occupancy", "Lighting", "Equipment"):
            sched_name: str = cfg[family]
            profile = parse_schedule_compact(idf_text, sched_name)
            has_data = any(v for v in profile.values())

            if not has_data:
                # Attempt to list available schedule names for diagnostics
                available = _list_schedule_names(idf_text)
                parse_errors.append(
                    f"{group}/{family}: '{sched_name}' not found. "
                    f"Available (first 10): {available[:10]}"
                )
                print(
                    f"[WARN] {group}/{family}: '{sched_name}' not found in {idf_path.name}",
                    file=sys.stderr,
                )
                group_result[family] = {"object_name": sched_name, "profile": {}, "eflh": 0.0}
            else:
                eflh = compute_eflh(profile)
                group_result[family] = {
                    "object_name": sched_name,
                    "profile": profile,
                    "eflh": round(eflh, 2),
                }

        results[group] = group_result

    # Save parsed profiles JSON
    out_json = OUT_DIR / "parsed_profiles.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nParsed profiles saved to {out_json}")

    # Print cross-check table
    print("\n" + "=" * 90)
    print("PARSED vs RESULT CROSS-CHECK (EFLH = weekday*261 + sat*52 + other*52)")
    print("=" * 90)
    print(f"{'Group':<12} {'Family':<12} {'Parsed EFLH':>14} {'RESULT ref':>12} {'Dev%':>8} {'Flag':>10}")
    print("-" * 90)

    deviations: list[str] = []
    for group in GROUP_CONFIG:
        if group not in results:
            print(f"{group:<12} {'--':<12} {'IDF MISSING':>14}")
            continue
        for family in ("Occupancy", "Lighting", "Equipment"):
            fdata = results[group][family]
            parsed_eflh = fdata["eflh"]
            ref = RESULT_EFLH_REF.get(group, {}).get(family)
            if ref is not None and ref > 0:
                dev_pct = abs(parsed_eflh - ref) / ref * 100
                flag = "***FLAG***" if dev_pct > 2.0 else "ok"
                if dev_pct > 2.0:
                    deviations.append(
                        f"{group}/{family}: parsed={parsed_eflh:.1f} ref={ref:.1f} dev={dev_pct:.1f}%"
                    )
            else:
                dev_pct = float("nan")
                flag = "no-ref"
            ref_str = f"{ref:.2f}" if ref is not None else "N/A"
            dev_str = f"{dev_pct:.1f}" if dev_pct == dev_pct else "N/A"
            print(
                f"{group:<12} {family:<12} {parsed_eflh:>14.2f} {ref_str:>12} {dev_str:>8} {flag:>10}"
            )

    print("=" * 90)

    if deviations:
        print("\nFLAGGED deviations > 2% vs RESULT reference values:")
        for d in deviations:
            print(f"  {d}")
    else:
        print("\nNo deviations > 2% vs RESULT reference values.")

    if parse_errors:
        print("\nPARSE ERRORS / WARNINGS:")
        for e in parse_errors:
            print(f"  {e}")

    # Print Apartment group in full (manager spot-check)
    print("\n" + "=" * 90)
    print("APARTMENT GROUP -- full parsed profiles (manager spot-check)")
    print("=" * 90)
    apt = results.get("Apartment", {})
    for family in ("Occupancy", "Lighting", "Equipment"):
        fdata = apt.get(family, {})
        print(f"\n  {family} (object: {fdata.get('object_name', '?')})  EFLH={fdata.get('eflh', 0):.2f}")
        profile = fdata.get("profile", {})
        for dt in ("Weekdays", "Saturday", "AllOtherDays"):
            pts = profile.get(dt, [])
            if pts:
                print(f"    {dt}:")
                for t, v in pts:
                    print(f"      Until {t}: {v}")
            else:
                print(f"    {dt}: (empty)")

    # Build PROVENANCE.md
    _write_provenance(results)
    print(f"\nPROVENANCE.md written to {OUT_DIR / 'PROVENANCE.md'}")


def _list_schedule_names(idf_text: str) -> list[str]:
    """Return all Schedule:Compact names found in the IDF token stream."""
    tokens = _idf_tokens(idf_text)
    names: list[str] = []
    for i, tok in enumerate(tokens):
        if re.match(r"(?i)^SCHEDULE\s*:\s*COMPACT$", tok) and i + 1 < len(tokens):
            names.append(tokens[i + 1])
    return names


def _write_provenance(results: dict) -> None:
    lines = [
        "# PROVENANCE -- DOE Commercial Prototype Schedules (OQ-2)",
        "",
        "**Edition:** ASHRAE 90.1-2013  ",
        "**Source:** U.S. DOE Building Energy Codes Program, PNNL.  ",
        "**License:** Public Domain (U.S. Federal Government work, 17 U.S.C. SS 105).  ",
        "**Energycodes.gov base URL:** https://www.energycodes.gov/prototype-building-models  ",
        "",
        "## Refresh procedure",
        "",
        "1. Visit https://www.energycodes.gov/prototype-building-models and download the",
        "   `ASHRAE901_<Type>_STD2013.zip` for each prototype listed below.",
        "2. Extract any climate-variant IDF (schedules are climate-invariant per PNNL-23269 SS 3).",
        "3. Save to `docs/implementation/scheduleDigitization/sources/<Group>_90.1-2013.idf`.",
        "4. Re-run `python scripts/diagnostics/parse_doe_schedules.py` to regenerate",
        "   `parsed_profiles.json` and verify EFLH cross-check.",
        "",
        "## Per-group source map",
        "",
        "| Group | Source IDF file | Energycodes ZIP URL | Edition | Occ object | Ltg object | Equip object | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for group, cfg in GROUP_CONFIG.items():
        if group not in results:
            row_note = "IDF MISSING at parse time"
            occ_obj = cfg.get("Occupancy", "?")
            ltg_obj = cfg.get("Lighting", "?")
            eqp_obj = cfg.get("Equipment", "?")
        else:
            occ_obj = results[group]["Occupancy"]["object_name"]
            ltg_obj = results[group]["Lighting"]["object_name"]
            eqp_obj = results[group]["Equipment"]["object_name"]
            row_note = cfg.get("note", "")

        idf_name = Path(cfg["idf"]).name
        url = cfg.get("url", "see sources/")
        lines.append(
            f"| {group} | `{idf_name}` | {url} | 90.1-2013 "
            f"| `{occ_obj}` | `{ltg_obj}` | `{eqp_obj}` | {row_note} |"
        )

    lines += [
        "",
        "## DataCenter exception",
        "",
        "| Group | Source IDF file | Notes |",
        "|---|---|---|",
        "| DataCenter | N/A | No DOE Commercial Prototype for data centers in STD2013. "
        "Kept as 24/7 constant=1.0 for all three families. Documented exception per PLAN SS 4. |",
        "",
        "## SuperMarket note",
        "",
        "No ASHRAE 90.1-2013 SuperMarket prototype IDF is published on energycodes.gov.",
        "Per PLAN SS 4 and AUDIT ruling 6: SuperMarket uses the Retail group schedules",
        "(`_SCHED_GROUP` maps SuperMarket -> Retail).",
        "Plug EFLH difference vs Retail is only ~2.5% (RESULT_4 finding).",
        "Refrigeration modeled by separate `Refrigeration:*` objects in OpenUBEM reconstruction layer.",
        "",
    ]

    (OUT_DIR / "PROVENANCE.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
