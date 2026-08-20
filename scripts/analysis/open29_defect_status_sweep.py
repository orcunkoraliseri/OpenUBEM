"""T08 of PLAN_ten-items-2026-08-18-late.md -- OPEN-29's first measurement.

OPEN-29 has carried an explicitly UNVERIFIED candidate list since 2026-08-05: defect IDs
whose last status word at their own DEFINING line is OPEN, and which this register never
adopted as items. The item's own stated first measurement, never made:

    "For each candidate ID, follow its citations forward to the latest document that
     mentions it and record its *final* recorded status, with a path:line. Output: a
     two-column table -- genuinely-still-open vs closed-elsewhere."

This is that sweep. It is mechanical: it collects every mention of each ID across the docs
tree, orders them by the mentioning file's git-tracked recency (falling back to mtime), and
reports the newest mention together with the status words in its immediate neighbourhood.
The classification it emits is a CANDIDATE classification for a human to confirm -- a status
word near a citation is evidence, not a verdict.

No row emitted here is promoted to a register item. That is the user's call (plan CP-C).

Emits openubem/outputs/comparisons/open29_defect_status_sweep.csv.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT = ROOT / "openubem" / "outputs" / "comparisons"

CANDIDATES = ["E-LA-06", "E-LA-11", "E-LA-12", "E-LA-13", "E-LA-15", "E-LA-16",
              "E-LA-17", "E-LA-18", "E-LA-19", "E-LA-21", "E-LA-30", "E-LA-33"]

CLOSED_RX = re.compile(
    r"\b(CLOSED|FIXED|RESOLVED|RETIRED|DISCHARGED|SUPERSEDED|WILL[- ]NOT[- ]FIX|"
    r"NOT[- ]A[- ]DEFECT|FALSIFIED|withdrawn)\b", re.I)
OPEN_RX = re.compile(r"\b(OPEN|LIVE|STILL OPEN|UNRESOLVED|OUTSTANDING|LATENT|MASKED)\b")
CONTEXT = 2
SUBSTANTIVE_MIN = 4   # mentions within ONE file before it counts as discussing the ID

# Self-referential documents: they mention every candidate ID only because they carry
# OPEN-29's own candidate list, or a copy of it. Including them makes the sweep circular --
# the "newest mention" of every ID becomes the list that asked the question. Excluded, and
# named here so the exclusion is auditable rather than silent.
EXCLUDE_NAMES = {
    "INVESTIGATION_open-items-register.md",
    "PLAN_ten-items-2026-08-18-late.md",
    "MEASUREMENT_ten-items-2026-08-18-late.md",
}
EXCLUDE_PREFIXES = ("DIRECTOR_PROMPT_",)


def _excluded(p) -> bool:
    return p.name in EXCLUDE_NAMES or p.name.startswith(EXCLUDE_PREFIXES)


def main() -> int:
    files = sorted(p for p in DOCS.rglob("*.md") if p.is_file() and not _excluded(p))
    print(f"scanning {len(files)} markdown files under {DOCS}")

    hits: dict[str, list[tuple[Path, int, str]]] = {c: [] for c in CANDIDATES}
    for p in files:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            for c in CANDIDATES:
                if c in line:
                    lo, hi = max(0, i - CONTEXT), min(len(lines), i + CONTEXT + 1)
                    hits[c].append((p, i + 1, " ".join(lines[lo:hi])))

    rows = []
    for c in CANDIDATES:
        hs = hits[c]
        if not hs:
            rows.append({"defect_id": c, "n_mentions": 0, "n_documents": 0,
                         "newest_document": "", "newest_line": "",
                         "newest_mtime": "", "closed_words": "", "open_words": "",
                         "candidate_status": "NO MENTION FOUND",
                         "selection_method": "", "excerpt": ""})
            continue
        # A roll-up board or a plan's fact table mentions an ID once, in a list, without
        # adjudicating it -- and those documents are the most recently touched, so plain
        # recency returns the list that asked the question rather than the answer. Prefer
        # the most recent document that DISCUSSES the ID (>= SUBSTANTIVE_MIN mentions in
        # that one file); fall back to plain recency and say so.
        per_doc: dict = {}
        for p, ln, ctx in hs:
            per_doc.setdefault(p, []).append((ln, ctx))
        substantive = {p: v for p, v in per_doc.items() if len(v) >= SUBSTANTIVE_MIN}
        pool = substantive or per_doc
        newest_p = max(pool, key=lambda p: p.stat().st_mtime)
        newest_l, newest_ctx = pool[newest_p][-1]
        method = "substantive" if substantive else "recency-only (no discussing document)"
        closed = sorted({m.group(0).upper() for h in hs for m in CLOSED_RX.finditer(h[2])})
        openw = sorted({m.group(0).upper() for h in hs for m in OPEN_RX.finditer(h[2])})
        newest_closed = bool(CLOSED_RX.search(newest_ctx))
        newest_open = bool(OPEN_RX.search(newest_ctx))
        if newest_closed and not newest_open:
            cand = "CLOSED ELSEWHERE (newest mention says so)"
        elif newest_open and not newest_closed:
            cand = "STILL OPEN (newest mention says so)"
        elif newest_open and newest_closed:
            cand = "AMBIGUOUS -- newest mention carries both words"
        else:
            cand = "NO STATUS WORD AT NEWEST MENTION"
        rows.append({
            "defect_id": c,
            "n_mentions": len(hs),
            "n_documents": len({h[0] for h in hs}),
            "newest_document": str(newest_p.relative_to(ROOT)).replace("\\", "/"),
            "newest_line": newest_l,
            "newest_mtime": pd.Timestamp(newest_p.stat().st_mtime, unit="s").strftime("%Y-%m-%d"),
            "closed_words": "|".join(closed),
            "open_words": "|".join(openw),
            "candidate_status": cand,
            "selection_method": method,
            "excerpt": newest_ctx[:300],
        })

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "open29_defect_status_sweep.csv"
    df.to_csv(dest, index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40,
                           "display.max_colwidth", 58):
        print(df[["defect_id", "n_mentions", "n_documents", "newest_document",
                  "newest_line", "newest_mtime", "selection_method",
                  "candidate_status"]].to_string(index=False))
    print("\ncandidate split:")
    print(df["candidate_status"].value_counts().to_string())
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
