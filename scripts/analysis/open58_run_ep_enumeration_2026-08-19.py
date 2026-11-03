"""OPEN-58 T03: independent re-derivation of the run_ep()/read_run() blast radius.

Enumerates every scripts/*.py file that mentions run_ep (grep), classifies each as a
real importer of scripts/analysis/open56_zone_volume_experiment.py's run_ep/read_run
vs. a local name-collision (its own def), and writes the classification table.

This does not trust or copy `extra/MEASUREMENT_open-58_blast-radius.md`'s table --
it is derived independently from source, per plan rule 11 (re-derive, don't quote).
"""
import re
import subprocess
from pathlib import Path

REPO = Path(r"C:/Users/o_iseri/Desktop/OpenUBEM")
SCRIPTS = REPO / "scripts"


def find_mentioning_files():
    # NOT git grep: the register records that the origin file and its importers are
    # UNTRACKED, so a tracked-files-only search would silently miss them. Walk disk.
    files = [
        p for p in SCRIPTS.rglob("*.py")
        if "__pycache__" not in p.parts and p.name != Path(__file__).name
    ]
    hits = [p for p in files if "run_ep" in p.read_text(encoding="utf-8", errors="replace")]
    return sorted(set(hits))


def classify(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    defines_own_run_ep = bool(re.search(r"^def _?run_ep\b", text, re.M))
    imports_from_source = "open56_zone_volume_experiment import" in text
    imported_names = []
    m = re.search(
        r"from open56_zone_volume_experiment import\s*\(([^)]*)\)"
        r"|from open56_zone_volume_experiment import\s*([^\n(]+)",
        text,
    )
    if m:
        raw = m.group(1) if m.group(1) else m.group(2)
        raw = re.sub(r"#.*", "", raw)
        imported_names = [n.strip() for n in raw.split(",") if n.strip()]
    return {
        "file": str(path.relative_to(REPO)).replace("\\", "/"),
        "defines_own_run_ep": defines_own_run_ep,
        "imports_from_open56_zone_volume_experiment": imports_from_source,
        "imported_names": ";".join(imported_names),
        "classification": (
            "real_importer" if imports_from_source else
            "name_collision_local_def" if defines_own_run_ep else
            "mentions_only"
        ),
    }


def main():
    files = find_mentioning_files()
    rows = [classify(f) for f in files if f.name != "open56_zone_volume_experiment.py"]
    # source file itself
    src = SCRIPTS / "analysis" / "open56_zone_volume_experiment.py"
    rows.insert(0, {
        "file": "scripts/analysis/open56_zone_volume_experiment.py",
        "defines_own_run_ep": True,
        "imports_from_open56_zone_volume_experiment": False,
        "imported_names": "",
        "classification": "origin_defines_run_ep_and_read_run",
    })

    import csv
    out_path = REPO / "openubem/outputs/comparisons/open58_run_ep_consumers.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"{len(rows)} files written to {out_path}")
    for r in rows:
        print(r["file"], "->", r["classification"], "imports:", r["imported_names"])


if __name__ == "__main__":
    main()
