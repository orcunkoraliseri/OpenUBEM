"""
T05 of PLAN_four-items-2026-08-18.md, step 1.

Programmatic recount of the register's Section 1 summary table body
(INVESTIGATION_open-items-register.md). Never counts by hand, never trusts
the prose header -- reads the table rows themselves.

Table body located between the "| ID | Item | Theme | Blast radius | Evidence |"
header/separator and the first blank line that follows the last OPEN-NN row,
confirmed by inspection to run from the header separator at line 634 through
the last data row at line 688 (one stray blank line at 675 tolerated).
"""
import re
from pathlib import Path

REGISTER = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\openings\INVESTIGATION_open-items-register.md")

HEADER_LINE = "| ID | Item | Theme | Blast radius | Evidence |"
SEP_LINE_PREFIX = "|---|---|---|---|---|"

lines = REGISTER.read_text(encoding="utf-8").splitlines()

start = None
for i, line in enumerate(lines):
    if line.strip() == HEADER_LINE:
        start = i
        break
if start is None:
    raise SystemExit("Table header not found")

assert lines[start + 1].strip() == SEP_LINE_PREFIX, lines[start + 1]

row_start = start + 2
rows = []
i = row_start
while i < len(lines):
    line = lines[i]
    if line.strip() == "":
        # tolerate a single stray blank line inside the table (known: line ~675);
        # stop only if the *next* non-blank line is not a table row.
        j = i + 1
        if j < len(lines) and lines[j].startswith("|"):
            i += 1
            continue
        else:
            break
    if not line.startswith("|"):
        break
    rows.append(line)
    i += 1

end = i - 1

id_pattern = re.compile(r"OPEN-(\d+)")

live_ids = []
struck_ids = []
all_ids_seen = []

for row in rows:
    cells = row.split("|")
    # cells[0] is '' (before first pipe), cells[1] is the ID cell
    id_cell = cells[1].strip()
    m = id_pattern.search(id_cell)
    if not m:
        continue
    open_id = f"OPEN-{m.group(1)}"
    all_ids_seen.append(open_id)
    is_struck = id_cell.startswith("~~") or "~~OPEN-" in id_cell
    if is_struck:
        struck_ids.append(open_id)
    else:
        live_ids.append(open_id)

total = len(all_ids_seen)
live_n = len(live_ids)
struck_n = len(struck_ids)

# next free ID = max numeric ID + 1
nums = sorted(int(re.match(r"OPEN-(\d+)", x).group(1)) for x in all_ids_seen)
max_id = nums[-1] if nums else 0
expected_seq = list(range(1, max_id + 1))
missing = sorted(set(expected_seq) - set(nums))
dupes = sorted({x for x in nums if nums.count(x) > 1})

print(f"Table body: lines {start+1}-{end+1} (1-indexed), {len(rows)} row-lines")
print(f"Total OPEN-NN rows found: {total}")
print(f"Live (non-struck) rows: {live_n}")
print(f"Struck rows: {struck_n}")
print(f"ID range: OPEN-01 .. OPEN-{max_id:02d}")
print(f"Missing IDs in sequence: {missing if missing else 'none'}")
print(f"Duplicate IDs: {dupes if dupes else 'none'}")
print(f"Next free item ID: OPEN-{max_id+1}")
print()
print("Struck IDs:", ", ".join(struck_ids))
