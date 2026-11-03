import re
import csv
from pathlib import Path
from collections import Counter

ROOT = Path("evidence/open48_refleet4")
CELLS = ["austin", "la", "nyc"]
SUBS = ["centre", "rural", "suburban", "urban"]

FATAL_RE = re.compile(r"\*\*  Fatal  \*\*")
SEVERE_RE = re.compile(r"\*\* Severe  \*\*\s*(.*)")
WARNING_RE = re.compile(r"\*\* Warning \*\*")
OPEN09_SIGNATURE = "Inside surface heat balance did not converge"

zone_re = re.compile(r'zone="[^"]*"|zone=\S+', re.IGNORECASE)
surface_re = re.compile(r'surface="[^"]*"|Surface="[^"]*"', re.IGNORECASE)
bound_re = re.compile(r"[\[\(]-?\d[\d.eE+-]*[\]\)]")
num_re = re.compile(r"-?\d+\.\d+|-?\d+")


def normalize(msg: str) -> str:
    msg = surface_re.sub("surface=<SURFACE>", msg)
    msg = zone_re.sub("zone=<ZONE>", msg)
    msg = bound_re.sub("<BOUND>", msg)
    msg = num_re.sub("<NUM>", msg)
    return msg.strip()


bldg_out = Path("openubem/outputs/comparisons/open38-09-45_err-census-buildings_2026-08-21b.csv")

n_files = 0
n_fatal_files = 0
n_open09_files = 0
total_severe = 0
total_warning = 0
class_counter = Counter()
no_preceding_severe = 0
bldg_rows = []

sim_dirs = []
for city in CELLS:
    for sub in SUBS:
        cell = f"{city}_{sub}"
        sim_out = ROOT / cell / "sim_out"
        if not sim_out.is_dir():
            continue
        for d in sorted(sim_out.iterdir()):
            if d.is_dir():
                sim_dirs.append((cell, d))

for cell, d in sim_dirs:
    err = d / "eplusout.err"
    if not err.is_file():
        continue
    n_files += 1
    stem = d.name
    try:
        text = err.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    lines = text.splitlines()

    n_severe = 0
    n_warning = 0
    fatal_idx = None
    severe_indices = []
    has_open09 = False

    for i, line in enumerate(lines):
        if SEVERE_RE.search(line):
            n_severe += 1
            severe_indices.append(i)
        if WARNING_RE.search(line):
            n_warning += 1
        if OPEN09_SIGNATURE in line:
            has_open09 = True
        if fatal_idx is None and FATAL_RE.search(line):
            fatal_idx = i

    total_severe += n_severe
    total_warning += n_warning
    is_fatal = fatal_idx is not None
    if is_fatal:
        n_fatal_files += 1
    if has_open09:
        n_open09_files += 1

    assigned_class = ""
    if severe_indices:
        if is_fatal:
            window = [j for j in severe_indices if fatal_idx - 5 <= j < fatal_idx]
            chosen_idx = window[-1] if window else severe_indices[0]
        else:
            chosen_idx = severe_indices[0]
        m = SEVERE_RE.search(lines[chosen_idx])
        raw_msg = m.group(1) if m else lines[chosen_idx]
        assigned_class = normalize(raw_msg)
        class_counter[assigned_class] += 1
    else:
        if is_fatal:
            no_preceding_severe += 1

    bldg_rows.append([
        cell, stem, is_fatal, n_severe, n_warning, has_open09, assigned_class,
    ])

bldg_out.parent.mkdir(parents=True, exist_ok=True)
with bldg_out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["cell", "stem", "is_fatal", "n_severe", "n_warning", "is_open09_signature", "severe_class"])
    w.writerows(bldg_rows)

print("=== T06 summary ===")
print(f"err files found: {n_files}")
print(f"files with two-space Fatal marker: {n_fatal_files} / {n_files}")
print(f"total ** Severe  ** count (fleet-wide): {total_severe}")
print(f"total ** Warning ** count (fleet-wide): {total_warning}")
print(f"fatal files with no preceding/available severe: {no_preceding_severe} / {n_fatal_files}")
print(f"files matching OPEN-09 signature ('{OPEN09_SIGNATURE}'): {n_open09_files} / {n_files}")
print("--- top severe classes (last-before-fatal or first-in-file), count / denominator = files with >=1 severe ---")
n_with_class = sum(class_counter.values())
for cls, cnt in class_counter.most_common(10):
    print(f"{cnt} / {n_with_class} : {cls}")
print(f"wrote per-building csv: {bldg_out} ({len(bldg_rows)} rows)")
