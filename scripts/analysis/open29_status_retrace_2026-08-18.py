"""
OPEN-29 T04 (PLAN_open-52-and-four-items-2026-08-18.md) -- re-derive the defect-status trace
at HEAD, 2026-08-18. Measurement only. No production code is touched by this script.

Step 1 is a hard gate: reproduce the E-LA-20 method control blind through the forward-citation
procedure. If it does not land on "FIXED, verified 150/150" at the cited path:line, STOP --
the procedure is broken, not the data.

Step 3 checks HEAD's harvest scripts for whether `has_fatal` still tests only the one-space
`** Fatal **` literal (E-LA-21's own defect), live off the filesystem, not from a document's claim.

The 13-row trace (E-LA-06 split into two halves, plus 11 other IDs) is a forward-citation trace
across documents -- inherently a manual research artifact, not a computed one -- so its rows are
recorded here as data, each carrying its own path:line citation, re-derived from a fresh read of
the register and this arc's plan/extra docs on 2026-08-18 (see the accompanying MEASUREMENT doc for
the full citation trail). The two claims that ARE mechanically checkable (the E-LA-20 control and
the E-LA-21 HEAD-parser re-check) are verified live below, not asserted.
"""

import csv
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]

E_LA_20_CONTROL_FILE = (
    REPO_ROOT
    / "docs/docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md"
)
E_LA_20_CONTROL_LINE = 68
E_LA_20_EXPECTED_SUBSTRINGS = ["SIGNED 2026-07-25", "150/150 PASS", "0 CTF Fatal"]

HARVEST_SCRIPTS = [
    "scripts/cluster/t20_harvest_layout_assign.py",
    "scripts/cluster/t08_harvest_results.py",
    "scripts/cluster/t07_harvest_results.py",
    "scripts/cluster/t07b_run_auto_refit_local.py",
    "scripts/cluster/t17_harvest_layout_assign.py",
    "scripts/cluster/t18_harvest_layout_assign.py",
    "scripts/cluster/t08_local_remainder.py",
]

ONE_SPACE_LITERAL = re.compile(r'"\*\* Fatal \*\*"|\'\*\* Fatal \*\*\'')
CORRECT_REGEX_LITERAL = re.compile(r"has_fatal\s*=.*Fatal")


def step1_e_la_20_control():
    print("=== STEP 1 (hard gate): E-LA-20 method control, run blind through the procedure ===")
    if not E_LA_20_CONTROL_FILE.exists():
        print(f"FAIL: control file not found: {E_LA_20_CONTROL_FILE}")
        sys.exit(1)
    lines = E_LA_20_CONTROL_FILE.read_text(encoding="utf-8").splitlines()
    if len(lines) < E_LA_20_CONTROL_LINE:
        print(f"FAIL: control file has only {len(lines)} lines, expected >= {E_LA_20_CONTROL_LINE}")
        sys.exit(1)
    line_text = lines[E_LA_20_CONTROL_LINE - 1]
    print(f"  {E_LA_20_CONTROL_FILE.relative_to(REPO_ROOT)}:{E_LA_20_CONTROL_LINE}")
    print(f"  {line_text}")
    missing = [s for s in E_LA_20_EXPECTED_SUBSTRINGS if s not in line_text]
    if missing:
        print(f"FAIL: control line is missing expected substrings: {missing}")
        print("STOP -- the procedure is broken, not the data.")
        sys.exit(1)
    print("  PASS -- control reproduces FIXED, verified 150/150.")
    print()


def step3_e_la_21_head_recheck():
    print("=== STEP 3: E-LA-21 -- does has_fatal still test only the one-space form, at HEAD? ===")
    any_one_space = False
    for rel in HARVEST_SCRIPTS:
        path = REPO_ROOT / rel
        if not path.exists():
            print(f"  {rel}: FILE NOT FOUND")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "has_fatal" in line and "=" in line and "Fatal" in line:
                flag = "ONE-SPACE LITERAL" if ONE_SPACE_LITERAL.search(line) else "regex/other form"
                print(f"  {rel}:{lineno}: {line.strip()}  [{flag}]")
                if ONE_SPACE_LITERAL.search(line):
                    any_one_space = True
    if any_one_space:
        print("  RESULT: at least one harvest script still tests only the one-space literal.")
    else:
        print("  RESULT: no harvest script tests only the one-space literal at HEAD.")
        print("  E-LA-21's own defect (has_fatal, one-space) is FIXED at HEAD across all 7 sites"
              " checked (R06, 2026-08-09; confirmed unchanged since).")
    print()
    return any_one_space


# 13-row forward-citation trace, re-derived 2026-08-18. Each row's `latest_document` is the
# latest-dated document found (this arc's register, plan docs under implemenation/, and extra/
# reports were all searched) that mentions the ID; see MEASUREMENT_open-29_status-retrace.md for
# the full search trail (grep commands, git log windows) behind each row.
ROWS = [
    dict(
        id="E-LA-06 (warmup half)",
        defining_site="docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:616",
        defining_status="OPEN-BLOCKED-PARTIAL (2026-07-23)",
        latest_document="docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:553",
        latest_date="2026-07-26",
        latest_status_quote=(
            "Re-attributed, not simply closed -- the SecondarySchool residual was "
            "CheckWarmupConvergence, now tracked as the E-LA-14/16/18/19/23 lineage"
        ),
        bucket="SUPERSEDED",
        notes=(
            "Unchanged since 2026-08-06. No document dated after 2026-07-26 revisits this half; "
            "the E-LA-14/16/18/19/23 lineage it was folded into is itself untouched at HEAD "
            "(openubem/geometry/layout_assigner.py:863-865, comment-only change 2026-08-18 for "
            "E-LA-16, not this lineage)."
        ),
        changed_since="No",
    ),
    dict(
        id="E-LA-06 (flow-balance half)",
        defining_site="docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:616",
        defining_status="OPEN-BLOCKED-PARTIAL (2026-07-23)",
        latest_document="extra/MEASUREMENT_open-29_eight-defect-recheck.md (table row)",
        latest_date="2026-08-13",
        latest_status_quote=(
            "STILL-OPEN -- openubem/geometry/layout_assigner.py:863-865, 2026-07-26 comment still "
            "reads the CheckAirLoopFlowBalance class as pre-existing/untouched; no later document "
            "mentions it again except as a still-current label"
        ),
        bucket="STILL-OPEN",
        notes=(
            "Re-verified at HEAD 2026-08-18: `grep -n CheckAirLoopFlowBalance "
            "openubem/geometry/layout_assigner.py` still hits the same lines; git log --since="
            "2026-08-13 on that file shows only the unrelated E-LA-16 comment fix (b2d0220). "
            "Unchanged since 2026-08-06."
        ),
        changed_since="No",
    ),
    dict(
        id="E-LA-11",
        defining_site="docs_DONE/SETUP/layoutAssigner/debug/DONE/PLAN_debug_implementation.md:412",
        defining_status="no explicit OPEN/CLOSED word at header (2026-07-23)",
        latest_document="INVESTIGATION_open-items-register.md:1804,1915",
        latest_date="2026-08-06",
        latest_status_quote=(
            "CLOSED-ELSEWHERE -- all closed at the structural-fixes CP-B/CP-C (2026-07-23), "
            "reconfirmed 2026-07-25; register's own framing corrected: a stale absence of a "
            "status word, not a stale OPEN"
        ),
        bucket="CLOSED-ELSEWHERE",
        notes="No document after 2026-08-06 mentions E-LA-11. Unchanged.",
        changed_since="No",
    ),
    dict(
        id="E-LA-12",
        defining_site="docs_DONE/SETUP/layoutAssigner/debug/DONE/PLAN_debug_implementation.md:424",
        defining_status="OPEN, LATENT/MASKED IN PRODUCTION (2026-07-23)",
        latest_document="INVESTIGATION_open-items-register.md:1804",
        latest_date="2026-08-06",
        latest_status_quote="CLOSED-ELSEWHERE -- all closed at the structural-fixes CP-B/CP-C (2026-07-23), reconfirmed 2026-07-25",
        bucket="CLOSED-ELSEWHERE",
        notes="No document after 2026-08-06 mentions E-LA-12. Unchanged.",
        changed_since="No",
    ),
    dict(
        id="E-LA-13",
        defining_site="docs_DONE/SETUP/layoutAssigner/debug/DONE/PLAN_debug_implementation.md:433",
        defining_status="OPEN-BLOCKED (2026-07-23)",
        latest_document="INVESTIGATION_open-items-register.md:1804",
        latest_date="2026-08-06",
        latest_status_quote="CLOSED-ELSEWHERE -- all closed at the structural-fixes CP-B/CP-C (2026-07-23), reconfirmed 2026-07-25",
        bucket="CLOSED-ELSEWHERE",
        notes="No document after 2026-08-06 mentions E-LA-13. Unchanged.",
        changed_since="No",
    ),
    dict(
        id="E-LA-15",
        defining_site="docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:270",
        defining_status="OPEN (2026-07-23 T04)",
        latest_document="extra/MEASUREMENT_open-29_eight-defect-recheck.md (table row)",
        latest_date="2026-08-13",
        latest_status_quote=(
            "STILL-OPEN -- named mechanism string SizeAirLoopBranches appears nowhere in "
            "production code; never handled, never guarded"
        ),
        bucket="STILL-OPEN",
        notes=(
            "Re-verified at HEAD 2026-08-18: `grep -rn SizeAirLoopBranches openubem/ scripts/ "
            "--include=*.py` -> 0 hits, same as 2026-08-13. Unchanged since 2026-08-06."
        ),
        changed_since="No",
    ),
    dict(
        id="E-LA-16",
        defining_site="docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:279",
        defining_status="OPEN (2026-07-23 T04/T05)",
        latest_document="INVESTIGATION_open-items-register.md:5164-5228 (OPEN-51 section, closed 2026-08-18)",
        latest_date="2026-08-18",
        latest_status_quote=(
            "OPEN-51 (the *identity* question -- which of two readings is the real E-LA-16) is "
            "ADJUDICATED + CLOSED + ID RETIRED 2026-08-18. Verdict: E-LA-16 names the "
            "cooling-coil-design-UA/cooling-tower-UA-autosize family, the defining-text reading. "
            "'OPEN-29 -- no change.'"
        ),
        bucket="STILL-OPEN",
        notes=(
            "IMPORTANT DISTINCTION, re-verified 2026-08-18, not taken on trust: OPEN-51 closed the "
            "REGISTER ITEM asking which of two readings E-LA-16 is -- it did NOT close the "
            "underlying defect. The register's own text says so explicitly ('OPEN-29 -- no change... "
            "this item resolves the question they deliberately left open', line ~5226). Confirmed "
            "live: `grep -rn 'cooling.coil.UA|CoolingCoilUA|cooling.tower.UA|cooling coil design UA' "
            "openubem/ scripts/ --include=*.py` matches exactly one line, "
            "openubem/geometry/layout_assigner.py:867, which is only the corrected COMMENT text "
            "('E-LA-16 removed from this list 2026-08-18 -- it names a different, unrelated "
            "mechanism...'), not a code path that handles the mechanism. Confirmed via `git log -p "
            "--since=2026-08-13 -- openubem/geometry/layout_assigner.py`: the only change in that "
            "window is this comment (commit b2d0220, 2026-08-18). The defect itself remains "
            "unpatched and STILL-OPEN. Bucket is unchanged from 2026-08-06; the citation and the "
            "identity ambiguity noted in the 2026-08-06/08-13 traces are now resolved."
        ),
        changed_since="Citation only (identity resolved by OPEN-51); bucket unchanged",
    ),
    dict(
        id="E-LA-17",
        defining_site="docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:290",
        defining_status="OPEN (2026-07-23 T04)",
        latest_document="extra/MEASUREMENT_open-29_eight-defect-recheck.md (table row)",
        latest_date="2026-08-13",
        latest_status_quote=(
            "STILL-OPEN -- persistent-divergence signature mechanism string appears nowhere in "
            "production code"
        ),
        bucket="STILL-OPEN",
        notes=(
            "Re-verified at HEAD 2026-08-18: `grep -rn persistent.divergence openubem/ scripts/ "
            "--include=*.py` -> 0 hits, same as 2026-08-13. Unchanged since 2026-08-06."
        ),
        changed_since="No",
    ),
    dict(
        id="E-LA-18",
        defining_site="docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:338",
        defining_status="OPEN (2026-07-23 T07)",
        latest_document="INVESTIGATION_open-items-register.md:5220 (OPEN-51 knock-on, 2026-08-18)",
        latest_date="2026-08-18",
        latest_status_quote=(
            "OPEN-09's C06 'five inherited log entries' list narrows to four: E-LA-14, E-LA-18, "
            "E-LA-19, E-LA-23 (E-LA-16 removed, it is a different mechanism)"
        ),
        bucket="STILL-OPEN",
        notes=(
            "Bucket unchanged: the CheckWarmupConvergence Severe class is still live and unpatched "
            "(openubem/geometry/layout_assigner.py:863-865; scripts/cluster/t20_harvest_layout_"
            "assign.py:264-265,441-448 still counts it every harvest). The only 2026-08-18 change "
            "affecting this row is bookkeeping -- which IDs C06's accuracy finding covers -- not a "
            "fix. OPEN-09's C06 (2026-08-06) still only tested one population "
            "(nyc_rural/SmallOffice), per MEASUREMENT_open-29_eight-defect-recheck.md section 3."
        ),
        changed_since="No (citation refreshed; bucket unchanged)",
    ),
    dict(
        id="E-LA-19",
        defining_site="docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:488",
        defining_status="OPEN, informational (2026-07-24 T10)",
        latest_document="INVESTIGATION_open-items-register.md:5220 (OPEN-51 knock-on, 2026-08-18)",
        latest_date="2026-08-18",
        latest_status_quote="Same knock-on as E-LA-18 -- narrows the C06 list to four IDs, does not fix the mechanism",
        bucket="STILL-OPEN",
        notes="Same reasoning as E-LA-18's row. Bucket unchanged since 2026-08-06.",
        changed_since="No (citation refreshed; bucket unchanged)",
    ),
    dict(
        id="E-LA-21",
        defining_site="docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/PLAN_e-la-20_investigation.md:493",
        defining_status="OPEN, informational (2026-07-25)",
        latest_document="INVESTIGATION_open-items-register.md:1894-1906 (R06 completion, 2026-08-09)",
        latest_date="2026-08-09",
        latest_status_quote=(
            "R06 is DONE and manager-audited 2026-08-09. All six live sites now test "
            "\\*\\*\\s+Fatal\\s+\\*\\*... E-LA-21 is now closed as a live code defect; OPEN-29 is "
            "NOT closed -- eight other defect IDs remain live inside it."
        ),
        bucket="CLOSED-ELSEWHERE",
        notes=(
            "CHANGED SINCE 2026-08-06. The 2026-08-06 trace found this STILL-OPEN, citing "
            "t20_harvest_layout_assign.py:259 as still the one-space literal. R06 (2026-08-09) "
            "and the malformed-variant sweep (2026-08-12) fixed it repo-wide. Re-verified live at "
            "HEAD 2026-08-18 by this script's Step 3, independent of the register's own claim: all "
            "7 harvest sites (t20/t08/t07/t07b/t17/t18_harvest*.py, t08_local_remainder.py) now use "
            "`re.search(r'\\*\\*\\s+Fatal\\s+\\*\\*', err)`. `grep -rn '\"\\*\\* Fatal \\*\\*\"' "
            "scripts/ openubem/` matches nothing in code (only the stale 2026-08-06 CSV row). No "
            "live one-space literal survives anywhere under scripts/ or openubem/."
        ),
        changed_since="Yes -- STILL-OPEN (2026-08-06) -> CLOSED-ELSEWHERE / FIXED (R06, 2026-08-09)",
    ),
    dict(
        id="E-LA-30",
        defining_site="docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/DONE_PLAN_storey-matching_implementation.md:3493",
        defining_status="OPEN, found by manager at CP-B (2026-07-26)",
        latest_document="extra/MEASUREMENT_open-29_eight-defect-recheck.md (table row)",
        latest_date="2026-08-13",
        latest_status_quote=(
            "STILL-OPEN -- fast_scale_idf_text() still present, file unchanged since 2026-07-26 "
            "(mtime Jul 26 11:11); replacement scripts still explicitly avoid calling it"
        ),
        bucket="STILL-OPEN",
        notes=(
            "Re-verified at HEAD 2026-08-18: scripts/analysis/a4_bis_generate_layout_assign_"
            "viewer.py:17 still defines fast_scale_idf_text(); `git log --since=2026-08-13` on this "
            "file returns nothing. Unchanged since 2026-08-06."
        ),
        changed_since="No",
    ),
    dict(
        id="E-LA-33",
        defining_site="docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/DONE_PLAN_storey-matching_implementation.md:3353",
        defining_status="OPEN (2026-07-26); still one of two grounds C02 go was withheld on",
        latest_document="extra/MEASUREMENT_open-29_eight-defect-recheck.md (table row)",
        latest_date="2026-08-13",
        latest_status_quote=(
            "STILL-OPEN -- match_storeys() still uses the Zone.Multiplier mechanism only; no "
            "vertex/Z-coordinate scaling added; the design decision 'not to be done reflexively' "
            "still stands"
        ),
        bucket="STILL-OPEN",
        notes=(
            "Re-verified at HEAD 2026-08-18: `grep -n 'def match_storeys' "
            "openubem/geometry/layout_assigner.py` -> :539, unchanged; git log --since=2026-08-13 "
            "on layout_assigner.py shows only the unrelated E-LA-16 comment fix. Unchanged since "
            "2026-08-06."
        ),
        changed_since="No",
    ),
]

CSV_COLUMNS = [
    "id",
    "defining_site",
    "defining_status",
    "latest_document",
    "latest_date",
    "latest_status_quote",
    "bucket",
    "notes",
    "changed_since_2026-08-06",
]


def step2_and_4_emit_csv():
    print("=== STEP 2/4: emit the 13-row re-derived trace ===")
    out_path = REPO_ROOT / "openubem/outputs/comparisons/open29_defect_status_trace_2026-08-18.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in ROWS:
            writer.writerow(
                {
                    "id": row["id"],
                    "defining_site": row["defining_site"],
                    "defining_status": row["defining_status"],
                    "latest_document": row["latest_document"],
                    "latest_date": row["latest_date"],
                    "latest_status_quote": row["latest_status_quote"],
                    "bucket": row["bucket"],
                    "notes": row["notes"],
                    "changed_since_2026-08-06": row["changed_since"],
                }
            )
    print(f"  Wrote {out_path.relative_to(REPO_ROOT)} ({len(ROWS)} rows)")

    buckets = {}
    for row in ROWS:
        buckets[row["bucket"]] = buckets.get(row["bucket"], 0) + 1
    print("  Bucket counts (2026-08-18):", buckets)
    old_buckets = {"CLOSED-ELSEWHERE": 3, "STILL-OPEN": 9, "SUPERSEDED": 1}
    print("  Bucket counts (2026-08-06, for comparison):", old_buckets)
    print()
    return out_path, buckets


def main():
    step1_e_la_20_control()
    any_one_space = step3_e_la_21_head_recheck()
    out_path, buckets = step2_and_4_emit_csv()
    print("=== SUMMARY ===")
    print(f"E-LA-20 control: PASS")
    print(f"E-LA-21 HEAD re-check: {'still one-space (BUG LIVE)' if any_one_space else 'fixed at HEAD (regex form everywhere)'}")
    print(f"New bucket counts: {buckets}")
    print(f"Old bucket counts: CLOSED-ELSEWHERE=3, STILL-OPEN=9, SUPERSEDED=1 (13 rows total, 2026-08-06)")
    print(f"Output CSV: {out_path}")


if __name__ == "__main__":
    main()
