"""OPEN-36 re-sweep (T08, PLAN_rulings-and-five-items-2026-08-12.md).

Re-verifies N13's 596-entry completion-record population against the CURRENT HEAD, using the same
population (N13's own CSV, `openubem/outputs/comparisons/open36_completion_record_sweep.csv`) but an
independently re-run check for every claimed artifact -- file and symbol -- with one deliberate fix to
N13's own method: the "repo-wide unrestricted" fallback search that N13 used to correct proximity
mis-pairings is, in this script, restricted to code paths (`openubem/`, `scripts/`, `tests/`, `.py`
files only) and explicitly EXCLUDES `.md` documentation files. N13's correction step had no such
restriction and, as a result, treated a symbol's appearance in a *plan document's own prose*
(describing the intended code) as evidence the code had been committed -- this is the exact bug this
script's non-vacuity control (below) exists to catch.

Does not trust N13's `corrected_verdict` column for anything. Only uses N13's CSV to recover the
population (file, line, task_id, claimed artifacts) -- every verdict here is freshly computed.
"""
import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
N13_CSV = ROOT / "openubem/outputs/comparisons/open36_completion_record_sweep.csv"
OUT_CSV = ROOT / "openubem/outputs/comparisons/open36_governance_resweep.csv"

CODE_EXTS = (".py",)
CODE_ROOTS = ("openubem/", "scripts/", "tests/")


def run(args):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout


def file_exists_at_head(path: str) -> bool:
    out = run(["git", "cat-file", "-e", f"HEAD:{path}"])
    r = subprocess.run(["git", "cat-file", "-e", f"HEAD:{path}"], cwd=ROOT, capture_output=True)
    return r.returncode == 0


def file_ever_in_git(path: str) -> bool:
    out = run(["git", "log", "--all", "--oneline", "--follow", "--", path])
    return bool(out.strip())


def read_head_file(path: str) -> str:
    r = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return ""
    return r.stdout


def symbol_ever_in_git_this_file(symbol: str, path: str) -> bool:
    out = run(["git", "log", "--all", "-S", symbol, "--", path])
    return bool(out.strip())


_DEFINITION_PATTERNS = [
    r"def {sym}\b", r"class {sym}\b", r"^\s*{sym}\s*=", r"^\s*{sym}\s*:",
    r"{sym}\s*=\s*", r"^{sym}\b",
]


def symbol_present_elsewhere_in_code(symbol: str) -> str:
    """Restricted repo-wide fallback: .py files under openubem/, scripts/, tests/ ONLY, and only where
    the symbol is actually DEFINED (assigned/def/class), not merely referenced as a failing attribute
    access -- a bare substring hit is exactly the false-positive this script's non-vacuity control
    (T07: `imp._draw_tier` is referenced all over tests/test_draw_methods.py but defined nowhere) is
    built to catch. Never .md."""
    r = subprocess.run(["git", "grep", "-l", "-F", symbol, "HEAD", "--", "*.py"],
                        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not r.stdout.strip():
        return ""
    hits = [h.split(":", 1)[1] for h in r.stdout.strip().splitlines() if ":" in h]
    hits = [h for h in hits if h.startswith(CODE_ROOTS)]
    escaped = re.escape(symbol)
    combined = re.compile("|".join(p.format(sym=escaped) for p in _DEFINITION_PATTERNS), re.MULTILINE)
    for h in hits:
        if h not in file_cache_global:
            file_cache_global[h] = read_head_file(h)
        if combined.search(file_cache_global[h]):
            return h
    return ""


file_cache_global = {}


def parse_detail(detail: str):
    """Parse N13's 'X@Y=VERDICT(...)' || ... format into [(artifact, paired_file), ...]."""
    out = []
    if not detail:
        return out
    for clause in detail.split(" || "):
        clause = clause.strip()
        if "=" not in clause or "@" not in clause:
            continue
        head = clause.split("=", 1)[0]
        if "@" in head:
            sym, fpath = head.rsplit("@", 1)
            out.append((sym.strip(), fpath.strip()))
    return out


def parse_file_level(detail: str):
    """file_level_detail is 'path=VERDICT(...)' || ... -- no @ separator."""
    out = []
    if not detail:
        return out
    for clause in detail.split(" || "):
        clause = clause.strip()
        if "=" not in clause:
            continue
        fpath = clause.split("=", 1)[0].strip()
        out.append(fpath)
    return out


def main():
    with open(N13_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 596, f"expected 596 population rows from N13, got {len(rows)}"

    out_rows = []
    file_cache = {}
    for row in rows:
        record_file = row["file"]
        line = row["line"]
        task = row["task_id"]
        checkable_files = parse_file_level(row["file_level_detail"])
        checkable_syms = parse_detail(row["symbol_level_detail"])

        if not checkable_files and not checkable_syms:
            out_rows.append({
                "record_file": record_file, "line": line, "task": task,
                "claimed_artifact": "", "exists_at_head": "", "ever_in_git": "",
                "verdict": "UNCHECKABLE",
            })
            continue

        worst = "PRESENT"
        artifact_lines = []

        for fpath in checkable_files:
            exists = file_exists_at_head(fpath)
            ever = exists or file_ever_in_git(fpath)
            if exists:
                v = "PRESENT"
            elif ever:
                v = "MOVED"
            else:
                v = "NEVER-COMMITTED"
            artifact_lines.append((fpath, exists, ever, v))
            if v == "NEVER-COMMITTED":
                worst = "NEVER-COMMITTED"
            elif v == "MOVED" and worst != "NEVER-COMMITTED":
                worst = "MOVED"

        for sym, fpath in checkable_syms:
            if fpath not in file_cache:
                file_cache[fpath] = read_head_file(fpath)
            content = file_cache[fpath]
            if sym in content:
                artifact_lines.append((f"{sym}@{fpath}", True, True, "PRESENT"))
                continue
            ever_this_file = symbol_ever_in_git_this_file(sym, fpath)
            elsewhere = symbol_present_elsewhere_in_code(sym) if not ever_this_file else ""
            if elsewhere:
                artifact_lines.append((f"{sym}@{fpath}", True, True,
                                        f"PRESENT(elsewhere: {elsewhere})"))
                continue
            exists_head = False
            ever = ever_this_file
            if not ever:
                v = "NEVER-COMMITTED"
                worst = "NEVER-COMMITTED"
            else:
                v = "MOVED(removed after commit)"
                if worst != "NEVER-COMMITTED":
                    worst = "MOVED"
            artifact_lines.append((f"{sym}@{fpath}", exists_head, ever, v))

        out_rows.append({
            "record_file": record_file, "line": line, "task": task,
            "claimed_artifact": " || ".join(a for a, *_ in artifact_lines),
            "exists_at_head": " || ".join(str(e) for _, e, _, _ in artifact_lines),
            "ever_in_git": " || ".join(str(e) for _, _, e, _ in artifact_lines),
            "verdict": worst,
        })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["record_file", "line", "task", "claimed_artifact",
                                           "exists_at_head", "ever_in_git", "verdict"])
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    from collections import Counter
    c = Counter(r["verdict"] for r in out_rows)
    print("Total entries:", len(out_rows))
    for k, v in c.most_common():
        print(f"  {k}: {v}")

    t07 = [r for r in out_rows if r["task"] == "T07" and "imputation" in r["record_file"].lower()]
    print("\nT07 control rows:", len(t07))
    for r in t07:
        print(" ", r["record_file"], r["line"], r["task"], "->", r["verdict"])

    debias = [r for r in out_rows if r["task"] in ("T11.8", "T11.8b")]
    print("\nT11.8 / T11.8b rows:", len(debias))
    for r in debias:
        print(" ", r["record_file"], r["line"], r["task"], "->", r["verdict"])
        print("    artifacts:", r["claimed_artifact"])


if __name__ == "__main__":
    main()
