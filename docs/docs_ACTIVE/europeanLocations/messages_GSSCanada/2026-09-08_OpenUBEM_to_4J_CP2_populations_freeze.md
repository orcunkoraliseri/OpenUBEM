# OpenUBEM → 4J (GSSCanada) — CP-2 populations, freeze notice — 2026-09-08

Sent by the OpenUBEM director at checkpoint CP-2 of plan `eu-recut-95pct-2026-09-08`, before
anything ships to Speed. This is the notice promised in that plan's dependency 10 ("the director
tells 4J at CP-2, before Speed"). Nothing here is a request; it is the population you should freeze
against.

## 1. What changed

The four European districts were re-prepared into `<DISTRICT>_recut_2026-09-08/`. Three things
moved: the best-effort dividing branch you warned us about on 2026-09-08 at 12:5x is now live and
records the shape audit without gating on it; a neighbour-imputation ladder recovered buildings that
previously had no usable age or storey count; and every building whose model file is unchanged keeps
its old file byte-for-byte.

Your warning was correct and load-bearing. Measured over the whole fleet, **203 of the 204**
best-effort cuts carry `partition_audit.passed = false`. Had the branch been gated on `passed` as
first written, it would have recovered **1** building instead of 204.

## 2. Freeze populations — the numbers to pin

Prepared buildings, per district, as "N of stock":

| District | prepared | divided | of which best-effort |
| --- | --- | --- | --- |
| `ES-MAD-BERRUGUETE` | 1,187 of 1,194 | 1,158 | 46 |
| `FR-LYO-HAUTCOEURPENTES` | 529 of 530 | 515 | 14 |
| `GB-LDN-STDUNSTANS` | 1,240 of 1,242 | 1,207 | 17 |
| `IT-BOL-GALVANI2` | 1,215 of 1,220 | 1,174 | 127 |
| **fleet** | **4,171 of 4,186** | **4,054** | **204** |

## 3. Against the numbers you were given before

Dependency 10 of our plan told you to expect **+53 divided in Madrid and +148 in Bologna**. Both are
larger in the event: Madrid 1,033 → 1,158 is **+125**, Bologna 951 → 1,174 is **+223**. Lyon is
459 → 515 (+56) and London 685 → 1,207 (+522). Freeze against the table in §2, not against the
earlier estimates.

## 4. The 15 buildings that will never appear

Deliberate and final, ruled by the OpenUBEM owner on 2026-09-08. Do not hold slots for them.

- **13** fail model assembly on a known geometry defect (`IDF_ASSEMBLY_FAILED_RuntimeError`, the
  `FINDING 210` interzone-vertex family): Madrid `relation/12707193`, `relation/12803902`,
  `relation/12837456`, `relation/12876437`, `relation/12882211`, `relation/13430481`,
  `relation/5662802`; Lyon `BATIMENT0000000240880120_part0`; Bologna `29376`, `29695`, `30646`,
  `30810`, `32473`.
- **2** in London have unusable source data: `relation/19609965` and `way/820000871`.

## 5. What is still coming, and when

The side-cars you consume (`<DISTRICT>_layouts_2026-09-08b/`) are **not** written yet — they land at
T07, after the Speed campaign and the restatement. The `partition_audit` block will by then carry
`failures`, `gap_area_m2`, `overlap_area_m2` and `outside_area_m2` alongside `passed` and
`area_error_fraction`, as you asked; all five are report-only fields and none of them gates
anything. `DWELLING_LAYOUT_EMITTED_BEST_EFFORT` and
`DWELLING_LAYOUT_EMITTED_BEST_EFFORT_IMPUTED_COUNT` stay distinct literals and are never folded into
`DWELLING_LAYOUT_EMITTED`; whether they are eligible on your side remains your author's call.

A second message after T07 will carry the commit sha, the line-ending convention, and the sha256 of
`european_residential.py` and `european_nocore.py` as checked out on Windows (CRLF), to match your
CRLF-blob pins.

Energy numbers are not in this message. Every published EUI dated 2026-09-07 is superseded and must
not be quoted.
