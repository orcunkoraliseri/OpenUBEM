# Preserved simulation corpora — inventory

**Ruling:** R6, taken 2026-08-20 (evening).
**Rule:** a preserved corpus is entered here **and re-checked**, not written once. The checker is
`scripts/analysis/corpus_inventory_check_2026-08-20.py`; run it against a corpus root, exit 0 = intact.
**Why the rule exists:** the previous corpus was discarded and cost **97.2 CPU-hours** to regenerate.

---

## 1. OPEN-61 fleet district-heating census — 2026-08-20

| field | value |
|---|---|
| path | `C:/Users/o_iseri/OpenUBEM_corpora/open61_census_2026-08-20` |
| manifest | `INVENTORY.json` at the corpus root |
| layout | `<cell>/<stem>/sim_out/eplusout.{sql,err,eio,eso,…}` |
| cells | 12 |
| building directories | **7,861** |
| `.sql` files | **7,861** |
| size | **121.9 GB** |
| moved from | the ephemeral session scratchpad (`…/Temp/claude/…/scratchpad/open61_census_fleet_work`) |
| move kind | same-volume `os.rename`, **0.77 s, no copy** |
| last checked | 2026-08-20 — **PASS** |

**Coverage — read this before quoting the corpus as complete.** 7,861 directories stand against
**8,152 `ok` census rows** = **96.4 %, not 100 %.** The 291-building gap is the census's
kill-and-resume: those buildings' `sim_out` was reclaimed before the corpus was preserved. Their
*numbers* survive in `openubem/outputs/comparisons/open61_census_fleet.csv`; their raw EnergyPlus
output does not. Anything needing a re-read of raw output for those 291 must re-simulate.

**What the 121.9 GB is made of.** `.sql` 75.7 GB across all 7,861; `.eso` 33.8 GB across only 799;
`.csv` 8.9 GB; `.htm` 1.8 GB; everything else under 1.5 GB combined. The `.eso`/`.htm`/`.csv` tail
belongs to the 799 buildings run before the driver was switched to a leaner output set — it is
**not** uniform across the corpus, so per-building size is not a usable signal for anything.

**Per cell** (building dirs / `.sql` / census rows / `ok` rows):

| cell | dirs | `.sql` | census rows | `ok` rows |
|---|---|---|---|---|
| austin_centre | 402 | 402 | 413 | 413 |
| austin_rural | 235 | 235 | 245 | 245 |
| austin_suburban | 420 | 420 | 437 | 437 |
| austin_urban | 407 | 407 | 425 | 425 |
| la_centre | 221 | 221 | 226 | 226 |
| la_rural | 141 | 141 | 149 | 144 |
| la_suburban | 1,321 | 1,321 | 1,343 | 1,343 |
| la_urban | 600 | 600 | 618 | 618 |
| nyc_centre | 717 | 717 | 738 | 736 |
| nyc_rural | 188 | 188 | 198 | 198 |
| nyc_suburban | 1,546 | 1,546 | 1,589 | 1,589 |
| nyc_urban | 1,663 | 1,663 | 1,779 | 1,778 |
| **total** | **7,861** | **7,861** | **8,160** | **8,152** |

---

## 2. Not preserved — named so the exposure is visible, not fixed here

The **run-4 fleet corpus** (`open48_refleet4`) and its five siblings still live under
`%LOCALAPPDATA%\Temp\ubem_validation\`. That is a standard Windows temp root: Storage Sense and Disk
Cleanup are entitled to delete files there by age, without warning. Those corpora have survived so
far by luck rather than by policy. **This is exactly the failure R6 was written after.** Moving them
is a separate decision with a separate cost, and is not taken here — it is recorded so that the next
person deciding does so knowingly.
