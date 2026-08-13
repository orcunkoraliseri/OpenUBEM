"""OPEN-47 / T07 — search downloaded documents for the office size-tier thresholds.

Plan: docs/docs_ACTIVE/openings/implemenation/PLAN_three-new-items-2026-08-12.md, T07.

Searches plain-text extractions (produced with `pdftotext -layout`, page breaks kept as
form-feed \\f characters) of documents downloaded to the scratchpad for the strings that would
prove an office size tiering at 25,000 ft^2 / 100,000 ft^2 (= 2,322.576 / 9,290.304 m^2).

Hard rule 10 (plan Sec.1.10) and the T07 non-vacuity requirement (plan Sec.5, T07 "How"):
for every document searched, the script also searches for a control string known to be present
in that document (drawn from its own title/abstract/a table caption already read by the
executor). If the control string is not found, the script's search on that document is treated
as unproven and is NOT reported as a "not found" result for the real target strings.

This script only reads files under the scratchpad and prints a report. It changes no source file.
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGET_TERMS = [
    "2,322",
    "2322",
    "9,290",
    "9290",
    "25,000",
    "100,000",
]

# One entry per document. `path` is the scratchpad text extraction (pdftotext -layout output).
# `control` is a string the executor has already confirmed by eye is in the document (title,
# abstract phrase, or a table caption), used as the non-vacuity check.
DOCUMENTS = [
    dict(
        key="cbecs_2018_flipbook",
        label="EIA CBECS 2018 Building Characteristics Flipbook",
        path="eia_cbecs2018_flipbook.txt",
        control="Commercial Buildings Energy Consumption Survey",
    ),
    dict(
        key="deru2011_nrel_tp5500_46861",
        label="Deru et al. (2011) NREL/TP-5500-46861",
        path="deru2011.txt",
        control="NREL/TP-5500-46861",
    ),
    dict(
        key="pnnl23269",
        label="PNNL-23269 (2014) Enhancements to ASHRAE Standard 90.1 Prototype Building Models",
        path="pnnl23269.txt",
        control="High-Rise Apartment",
    ),
    dict(
        key="hong2015_apenergy159",
        label="Hong et al. (2015) Applied Energy 159, 298-309 (real CBES paper, DOI 10.1016/j.apenergy.2015.09.002)",
        path="hong2015_apenergy159_cbes.txt",
        control="Commercial Building Energy Saver",
    ),
    dict(
        key="chen2017_apenergy205",
        label="Chen, Hong & Piette (2017) Applied Energy 205, 323-335 (DOI 10.1016/j.apenergy.2017.07.128), LBNL manuscript",
        path="chen2017_apenergy205_citybes_retrofit.txt",
        control="City Datasets for City-Scale Building",
    ),
    dict(
        key="chen2017_bs2017",
        label="Chen, Hong & Piette (2017) IBPSA BS2017_071 conference paper",
        path="chen2017_bs2017_071_nolayout.txt",
        control="CityBES",
    ),
]


def load_pages(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text.split("\f")


def find_term(pages: list[str], term: str) -> list[tuple[int, str]]:
    hits = []
    for page_no, page_text in enumerate(pages, start=1):
        for line in page_text.splitlines():
            if term.lower() in line.lower():
                hits.append((page_no, line.strip()))
    return hits


def main() -> int:
    scratch_root = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if scratch_root is None:
        print("Usage: open47_threshold_search.py <scratchpad_open47_dir>")
        return 2

    overall_rows = []
    for doc in DOCUMENTS:
        doc_path = scratch_root / doc["path"]
        print("=" * 100)
        print(f"DOCUMENT: {doc['label']}")
        print(f"  file: {doc_path}")
        if not doc_path.exists():
            print("  STATUS: FILE NOT FOUND -- skipped (document was not downloaded/extracted)")
            overall_rows.append((doc["key"], "NOT_RETRIEVED", None, None))
            continue

        pages = load_pages(doc_path)
        control_hits = find_term(pages, doc["control"])
        control_ok = len(control_hits) > 0
        print(f"  NON-VACUITY CONTROL: searching for known-present string {doc['control']!r}")
        if control_ok:
            page_no, line = control_hits[0]
            print(f"    PASS -- found on page {page_no}: {line[:160]!r}")
        else:
            print("    FAIL -- control string NOT found. This document's 'not found' results below "
                  "are UNPROVEN and must not be reported as a clean negative.")

        for term in TARGET_TERMS:
            hits = find_term(pages, term)
            status = "FOUND" if hits else "not found"
            print(f"  target {term!r}: {status} ({len(hits)} line hits)")
            for page_no, line in hits[:5]:
                print(f"      page {page_no}: {line[:160]!r}")
            overall_rows.append((doc["key"], "OK" if control_ok else "CONTROL_FAILED", term, len(hits)))

    print("=" * 100)
    print("SUMMARY (key, control_status, term, hit_count):")
    for row in overall_rows:
        print("  ", row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
