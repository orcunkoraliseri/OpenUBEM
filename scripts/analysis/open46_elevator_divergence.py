"""
OPEN-46 / T04 — EVIDENCE ONLY.

Builds two inventories per docs/docs_ACTIVE/openings/implemenation/
PLAN_three-new-items-2026-08-12.md T04:

Inventory A (code): every file-pair divergence between the live tree and
docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/openubem/ that relates to
the elevator feature, plus the five archived test twins.

Inventory B (prose): every "10th end-use" / separate-elevator-reporting-line
claim found in the live tree, docs/docs_ACTIVE/, and docs/PROJECT_CHECKLIST.md.

Makes NO fix and edits NO source file. Diffs are computed with CRLF stripped
(both trees mix line endings; a raw diff makes every line look changed).
"""

import csv
import os
import re
import subprocess
import sys

REPO_ROOT = r"C:\Users\o_iseri\Desktop\OpenUBEM"
ARCH_OPENUBEM = os.path.join(
    REPO_ROOT, "docs", "docs_DONE", "LOADS & SCHEDULES", "elevators", "scripts", "openubem"
)
ARCH_TESTS = os.path.join(
    REPO_ROOT, "docs", "docs_DONE", "LOADS & SCHEDULES", "elevators", "scripts", "tests"
)

OUT_A = os.path.join(REPO_ROOT, "openubem", "outputs", "comparisons", "open46_elevator_divergence.csv")
OUT_B = os.path.join(REPO_ROOT, "openubem", "outputs", "comparisons", "open46_tenth_enduse_claims.csv")

CODE_PAIRS = [
    ("data/loads/elevators_by_archetype.json", "data/loads/elevators_by_archetype.json"),
    ("idf/elevators.py", "idf/elevators.py"),
    ("idf/builder.py", "idf/builder.py"),
    ("idf/outputs.py", "idf/outputs.py"),
    ("results/parser.py", "results/parser.py"),
    ("results/carbon.py", "results/carbon.py"),
    ("results/aggregator.py", "results/aggregator.py"),
]

TEST_PAIRS = [
    "test_elevators.py",
    "test_parser_elevators.py",
    "test_outputs.py",
    "test_results_aggregator.py",
    "test_step3_orchestrator.py",
]

MANUAL_VERDICTS = {
    "idf/builder.py": (
        "code",
        "Never imports or calls assign_elevators anywhere. hasattr(openubem.idf.builder, "
        "'assign_elevators') is False. The build() method's service-load block calls "
        "assign_hvac / assign_dhw / assign_cooking / assign_refrigeration / write_outputs "
        "in sequence with NO assign_elevators call between refrigeration and outputs.",
        "Archived build() calls assign_elevators(self.idf, row, extruded_zones) at :509, "
        "between assign_refrigeration and write_outputs.",
        "FEATURE MISSING (call site never merged) -- git log --all -S assign_elevators -- "
        "openubem/idf/builder.py returns NOTHING: the string was never added or removed in "
        "this file's tracked history. The only commit that ever touched 'assign_elevators' "
        "(ef19141, 2026-07-21) added it to the ARCHIVED builder.py copy only.",
    ),
    "idf/outputs.py": (
        "code",
        "HVAC_METERS has 13 entries, no Elevators meter.",
        "HVAC_METERS has 14 entries, including 'Elevators:InteriorEquipment:Electricity'.",
        "FEATURE MISSING (one tuple entry).",
    ),
    "results/parser.py": (
        "code",
        "METER_QUERY/_parse_meters_sql omit the elevator meter; _compute_eui sums 9 terms; "
        "no elevators_eui_kwh_m2 anywhere (0 occurrences of 'elevator', case-insensitive). "
        "ALSO has unrelated additions not in the archive: a resolution_mode parameter and "
        "layout_assign/layout_assigner zone-integrity branch in _check_zone_integrity -- "
        "this is unrelated drift (live moved on since the archive), not an elevator gap.",
        "Reads Elevators:InteriorEquipment:Electricity meter, emits elevators_eui_kwh_m2, "
        "de-folds it from equipment_eui_kwh_m2, sums 10 terms for total_eui_kwh_m2, and "
        "_failed_row includes elevators_eui_kwh_m2: nan.",
        "FEATURE MISSING (elevator lines) + UNRELATED DRIFT (resolution_mode lines, live-only, correctly not a missing feature).",
    ),
    "results/carbon.py": (
        "code",
        "9 gwp_* terms; no gwp_elevators_kgco2_m2; gwp_total sums 9 terms.",
        "gwp_elevators_kgco2_m2 = elevators_eui * f_elec, added to the nan block and to "
        "gwp_total_kgco2_m2's sum (10 terms).",
        "FEATURE MISSING.",
    ),
    "results/aggregator.py": (
        "code",
        "_STEP5_COLS omits elevators_eui_kwh_m2 and gwp_elevators_kgco2_m2. ALSO carries an "
        "unrelated docstring addition (OPEN-43 fleet-EUI pooling note) not present in the "
        "archive -- unrelated drift, not an elevator gap.",
        "_STEP5_COLS includes both elevators_eui_kwh_m2 and gwp_elevators_kgco2_m2, with "
        "comments '... + elevators (T05, 10th end-use)' and '... (9 + elevators)'.",
        "FEATURE MISSING (two column entries) + UNRELATED DRIFT (OPEN-43 docstring, live-only).",
    ),
    "idf/elevators.py": (
        "code",
        "Byte-identical to archive. Exists in the live tree and is importable.",
        "Same file.",
        "FILE ITSELF PRESENT, BUT ORPHANED: nothing in the live openubem/ package imports "
        "or calls assign_elevators (confirmed by whole-tree grep -- only this file and the "
        "JSON data file mention 'elevator'; builder.py, semantic/loads.py do not).",
    ),
    "data/loads/elevators_by_archetype.json": (
        "data",
        "Byte-identical to archive (80/80 lines, diff exit 0).",
        "Same file.",
        "IDENTICAL, NOT A DIVERGENCE.",
    ),
}

TEST_MANUAL = {
    "test_elevators.py": (
        "IDENTICAL to archive (diff exit 0).",
        "Same file.",
        "IDENTICAL -- exercises openubem.idf.elevators.assign_elevators() directly, not "
        "through the builder, so it is unaffected by builder.py's missing call site.",
        "28 passed",
    ),
    "test_parser_elevators.py": (
        "IDENTICAL to archive (diff exit 0). Still asserts elevators_eui_kwh_m2, the "
        "Elevators meter, and gwp_elevators_kgco2_m2 -- the ONE archived twin whose "
        "expectation was left in place rather than removed.",
        "Same file.",
        "EXPECTATION LEFT IN PLACE (not removed) -- this is the file that still fails live, "
        "and per the register is why OPEN-46 surfaced at all.",
        "8 failed, 0 passed",
    ),
    "test_outputs.py": (
        "test_hvac_meters_count asserts len(HVAC_METERS) == 13 (was 14); "
        "test_hvac_meters_phase_e_required's required set drops the elevator meter; "
        "test_output_meter_count asserts 13 (was 14).",
        "len(HVAC_METERS) == 14; required set includes 'Elevators:InteriorEquipment:Electricity'; "
        "test_output_meter_count asserts 14.",
        "EXPECTATION REMOVED (3 assertions weakened to match the un-merged live code).",
        "11 passed",
    ),
    "test_results_aggregator.py": (
        "Expected-row dicts (both the all-NaN failure template and the populated success "
        "rows) omit elevators_eui_kwh_m2 and gwp_elevators_kgco2_m2.",
        "Both dicts include elevators_eui_kwh_m2: nan/0.0 and gwp_elevators_kgco2_m2: nan/0.0.",
        "EXPECTATION REMOVED (2 keys removed from 2 dict templates = 4 removed assertions).",
        "29 passed",
    ),
    "test_step3_orchestrator.py": (
        "test_medium_office_idf_contains_elevator_equipment does not exist at all.",
        "Carries test_medium_office_idf_contains_elevator_equipment, which builds a "
        "MediumOffice IDF and asserts exactly one ELECTRICEQUIPMENT object with "
        "EndUse_Subcategory == 'Elevators'.",
        "WHOLE TEST DELETED (not an assertion edit -- the entire test method is absent).",
        "18 passed",
    ),
}

TENTH_ENDUSE_PATTERNS = [
    re.compile(r"10th end-?use", re.IGNORECASE),
    re.compile(r"tenth end-?use", re.IGNORECASE),
    re.compile(r"10-way", re.IGNORECASE),
    re.compile(r"ten end-?uses", re.IGNORECASE),
    re.compile(r"ten-way", re.IGNORECASE),
]

SCAN_ROOTS_B = [
    os.path.join(REPO_ROOT, "openubem"),
    os.path.join(REPO_ROOT, "scripts"),
    os.path.join(REPO_ROOT, "tests"),
    os.path.join(REPO_ROOT, "docs", "docs_ACTIVE"),
]
CHECKLIST_PATH = os.path.join(REPO_ROOT, "docs", "PROJECT_CHECKLIST.md")


def normalized_diff_lines(path_a, path_b):
    if not os.path.isfile(path_a) or not os.path.isfile(path_b):
        return None
    with open(path_a, "r", encoding="utf-8", errors="replace") as f:
        a = f.read().replace("\r\n", "\n").replace("\r", "\n").splitlines()
    with open(path_b, "r", encoding="utf-8", errors="replace") as f:
        b = f.read().replace("\r\n", "\n").replace("\r", "\n").splitlines()
    import difflib
    diff = list(difflib.unified_diff(a, b, lineterm=""))
    return diff


def build_inventory_a():
    rows = []
    print("=== INVENTORY A: code divergence, live vs archived ===\n")
    for rel_live, rel_arch in CODE_PAIRS:
        live_path = os.path.join(REPO_ROOT, "openubem", rel_live)
        arch_path = os.path.join(ARCH_OPENUBEM, rel_arch)
        diff = normalized_diff_lines(live_path, arch_path)
        n_diff_lines = len(diff) if diff else 0
        identical = (n_diff_lines == 0)
        print(f"{rel_live}: identical={identical}  diff_lines={n_diff_lines}")

        kind, live_state, arch_state, verdict = MANUAL_VERDICTS[rel_live]
        rows.append({
            "kind": kind,
            "file": f"openubem/{rel_live}",
            "live_state": live_state,
            "archived_state": arch_state,
            "verdict": verdict,
        })

    print("\n=== INVENTORY A: five archived test twins ===\n")
    for fname in TEST_PAIRS:
        live_path = os.path.join(REPO_ROOT, "tests", fname)
        arch_path = os.path.join(ARCH_TESTS, fname)
        diff = normalized_diff_lines(live_path, arch_path)
        n_diff_lines = len(diff) if diff else 0
        identical = (n_diff_lines == 0)
        print(f"tests/{fname}: identical={identical}  diff_lines={n_diff_lines}")

        live_state, arch_state, verdict, test_result = TEST_MANUAL[fname]
        rows.append({
            "kind": "test",
            "file": f"tests/{fname}",
            "live_state": live_state + f" [live pytest result: {test_result}]",
            "archived_state": arch_state,
            "verdict": verdict,
        })

    os.makedirs(os.path.dirname(OUT_A), exist_ok=True)
    with open(OUT_A, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "file", "live_state", "archived_state", "verdict"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nWrote {len(rows)} rows to {OUT_A}")
    return rows


def build_inventory_b():
    print("\n=== INVENTORY B: '10th end-use' / separate-reporting-line claims ===\n")
    rows = []

    # Non-vacuity control: plant a known positive string in a scratch file, confirm the
    # patterns catch it, then remove the file.
    scratch_path = os.path.join(REPO_ROOT, "scripts", "analysis", "_open46_control_scratch.txt")
    with open(scratch_path, "w", encoding="utf-8") as f:
        f.write("this line exists only to prove the scanner works: the 10th end-use claim\n")
    found_control = False
    with open(scratch_path, "r", encoding="utf-8") as f:
        for line in f:
            if any(p.search(line) for p in TENTH_ENDUSE_PATTERNS):
                found_control = True
    os.remove(scratch_path)
    print(f"Non-vacuity control: planted string found = {found_control}")
    assert found_control, "CONTROL FAILED: scanner did not catch its own planted positive"
    print(f"Control file removed: {scratch_path}\n")

    all_files = []
    for root in SCAN_ROOTS_B:
        for dirpath, _, filenames in os.walk(root):
            if "__pycache__" in dirpath:
                continue
            for fn in filenames:
                if fn.endswith((".py", ".md", ".html", ".csv")):
                    all_files.append(os.path.join(dirpath, fn))
    if os.path.isfile(CHECKLIST_PATH):
        all_files.append(CHECKLIST_PATH)

    self_path = os.path.abspath(__file__)
    exclude = {self_path, OUT_A, OUT_B}
    for path in all_files:
        if os.path.abspath(path) in exclude:
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, start=1):
                    if any(p.search(line) for p in TENTH_ENDUSE_PATTERNS):
                        rel = os.path.relpath(path, REPO_ROOT)
                        rows.append({
                            "file": rel.replace("\\", "/"),
                            "line": i,
                            "quote": line.strip()[:300],
                        })
        except (UnicodeDecodeError, PermissionError):
            continue

    os.makedirs(os.path.dirname(OUT_B), exist_ok=True)
    with open(OUT_B, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "line", "quote"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
            safe_quote = r["quote"].encode("ascii", errors="replace").decode("ascii")
            print(f"{r['file']}:{r['line']}: {safe_quote}")
    print(f"\nWrote {len(rows)} rows to {OUT_B}")
    return rows


def check_builder_call_graph():
    print("\n=== Supplementary check: is assign_elevators reachable from openubem.idf.builder? ===")
    code = (
        "import openubem.idf.builder as b\n"
        "print('hasattr assign_elevators:', hasattr(b, 'assign_elevators'))\n"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=REPO_ROOT,
                             capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print("STDERR:", result.stderr[-500:])


def main():
    build_inventory_a()
    build_inventory_b()
    check_builder_call_graph()


if __name__ == "__main__":
    main()
