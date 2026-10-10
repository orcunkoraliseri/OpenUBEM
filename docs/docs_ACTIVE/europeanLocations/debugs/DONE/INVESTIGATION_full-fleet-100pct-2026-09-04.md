# INVESTIGATION — how far can the EU-11 full-fleet population be pushed toward 100 %?

Copy this whole file into the external agent session (Gemini). It is self-contained: you have no access to
this project's other conversations, memory, or `CLAUDE.md`. Everything you need is below.

- **Arc**: European locations, full-fleet expansion (`D-EU-101`).
- **Related docs, read for prior art, do not re-derive what they already settled**:
  `docs/docs_ACTIVE/europeanLocations/prompts/EXECUTOR_PROMPT_full-fleet-expansion-2026-09-04.md` (the two
  code fixes already applied: London/Madrid `house`-tag → SFH/TH split, `FINDING 251`/`253`) and
  `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-37_typology_table_extension_2026-09-04.md`
  (Lyon's mid-rise widen, ruled and implemented 2026-09-04, `FINDING 255`).
- **This is an investigation, not an implementation task.** Report options with evidence. Do not edit any
  file, do not re-run anything, do not touch git, do not touch the Speed cluster.

## Repository facts you cannot guess

- Working directory: `C:\Users\o_iseri\Desktop\OpenUBEM` (Windows). `python` is not on `PATH`; the venv is
  `.venv\Scripts\python.exe`.
- This is a git repository with a large amount of pre-existing uncommitted work from other arcs — do not run
  `git add`, `git commit`, `git reset`, `git checkout --`, or `git clean`. Read-only `git status`/`git diff`
  are fine.
- No cluster access from you. No `ssh`/`scp`. This task is local, read-only: grep the code, read manifests
  and `summary.json` files already on disk, read scraped source data if referenced, and write your findings
  as plain text (or, if you want a durable record, a new file — see "Where to write findings" below).

## The goal and where it stands today

Every real residential building in four districts (Madrid Berruguete, Lyon Hauts de Croix-Rousse, London St
Dunstan's, Bologna Galvani 2) should eventually be simulated — 4,186 buildings total. As of 2026-09-04, after
two rounds of code fixes (`FINDING 251`/`253`/`255`), the fleet stands at **3,066 / 4,186 prepared (73.2 %)**.
The remaining gap is **1,120 buildings**, read directly off each district's own
`openubem/outputs/eu_evidence/EU-11/<DISTRICT>_full_fleet_2026-09-04/summary.json` (`population_attempted`
minus `population_prepared`, and the `blocker_exclusions` dict, quoted verbatim below — do not recompute
these from any other source, they are ground truth):

| District | Attempted | Prepared | Gap |
|---|---|---|---|
| `FR-LYO-HAUTCOEURPENTES` | 530 | 469 | 61 |
| `ES-MAD-BERRUGUETE` | 1,194 | 1,008 | 186 |
| `IT-BOL-GALVANI2` | 1,220 | 1,200 | 20 |
| `GB-LDN-STDUNSTANS` | 1,242 | 389 | 853 |
| **Total** | **4,186** | **3,066** | **1,120** |

Every excluded building carries a `blocker_exclusions` reason key in its district's `summary.json`. Your job
is to go category by category, verify the code citation given, and report — for each category — whether
there is a **legitimate, evidence-based** way to recover some or all of it (a real alternate data source, a
real code bug, a defensible extension of an already-established pattern), or whether it is a genuine dead end
(the source data does not exist anywhere reachable). **Never propose fabricating, guessing, or interpolating
a building attribute to force it through** — every existing rule in this codebase is fail-closed specifically
to avoid that, and any recovery must be traceable to a real, cited source.

## The nine categories, in priority order (biggest lever first)

### 1. London `MISSING_OBSERVED_EPC_AGE_BAND` (445) + `PERIOD_STRADDLE_*` (355) — 800 buildings, the single largest lever in the whole fleet

Code: `scripts/run_eu_s2_district_campaign.py`, `GB_EPC_BANDS` dict at line 65, consumed around lines
182-187. A UK Energy Performance Certificate gives a construction-period band (e.g. `GB.03`); the join to
each building is an **exact `osm_id` match, no fuzzy matching**. `MISSING_OBSERVED_EPC_AGE_BAND` = no EPC
record joins at all. `PERIOD_STRADDLE_<band>_<lo>_<hi>` = an EPC record joined, but its declared period
straddles two of this project's construction-year bands, and the code deliberately refuses to guess which
side it falls on.
**Investigate:** (a) is there a second, independent UK building-age source that could substitute for a
missing EPC match — e.g. Ordnance Survey building age layers, VOA council tax band year-built data, other UK
open-data building-age registries — that could be joined the same way (exact ID, no fuzzy match) to recover
some of the 445? (b) For the 355 straddling records, is there a real secondary signal already sitting unused
in the EPC record itself (e.g. a more granular sub-field, or the property's `TRANSACTION_TYPE`/`CURRENT-ENERGY-RATING`
history) that could break the tie without guessing? Report exact counts recoverable per source, and cite the
source's actual coverage/reliability — do not assume it would help without checking real numbers.

### 2. `MISSING_OBSERVED_STOREY_COUNT` — Madrid 163 + London 47 = 210 buildings

Already checked once (`FINDING 254`, 2026-09-04): in both districts' manifests, `levels`, `height_m`, and
`roof_height_m` are all null on every affected row, and `provenance_levels == "OSM_MISSING"` throughout — no
fallback signal existed *in the manifest as built*. **Investigate further, do not just repeat that check:**
does the *original* source data (before it was joined into the manifest) carry a storey/height signal that
never made it into the manifest — e.g. a cadastral height raster, a LIDAR-derived building height dataset, a
municipal register? Check what `openubem/outputs/eu02/<district>/02_residential_manifest.gpkg` was built
from (trace the acquisition script) and whether any unused column or unjoined external source could supply
storeys. If truly nothing exists anywhere, say so explicitly and cite what you checked.

### 3. `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` — Lyon 37 + Madrid 1 = 38 buildings — never investigated

Code: `openubem/semantic/european_archetype_mapping.py:193-194` (`derive_bdtopo_building_type`):
```python
if dwellings in (13, 14):
    return None, TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14
```
This sits between the `MFH` bucket (`2 <= dwellings <= 12`) and the `AB` bucket (`dwellings >= 15`) — a
building with exactly 13 or 14 dwellings is excluded regardless of its storey count. The module's docstring
(lines 37-41) says every threshold in this function is read off `tabula_archetypes_fr.json`, never invented.
**Investigate:** open `tabula_archetypes_fr.json` (find it via `openubem/semantic/construction_sets.py`,
imported at the top of the mapping file) and check whether it actually defines a boundary at 13-14 dwellings
that this code is honouring, or whether this gap is an arbitrary omission with no source backing at all. If
the latter, this is the same shape of question `D-EU-37` just was — report it as a candidate for an owner
ruling (a new bucket, e.g. treating 13-14 dwellings as `MFH` or `AB` by whichever neighbour bucket's storey
range it falls into), but **do not rule it yourself** — that decision belongs to the project owner, exactly
like `D-EU-37` did.

### 4. `IDF_ASSEMBLY_FAILED_RuntimeError` — Lyon 4 + Madrid 9 + Bologna 4 = 17 buildings

Code: catch site at `scripts/run_eu_s2_district_campaign.py:443-449`, with an in-code comment explaining that
geomeppy's `intersect_match` can fail numerically on a live noisy footprint even after two reroute safety
nets in `openubem/idf/surfaces.py` give up, so the one building fails closed rather than aborting the whole
district. This has never been root-caused at the `intersect_match` level itself.
**Investigate:** for a handful of the 17 failing stems (per-district manifests list them), what specifically
is geometrically unusual about their footprints (self-intersection, near-duplicate vertices, a degenerate
edge)? Is there a defensible, already-used-elsewhere repair (e.g. the same near-duplicate-vertex carve-out
used for `FINDING 249`'s remedy) that would apply here too, or is each one a genuinely different pathological
shape? Report per-building diagnosis, not a guess at a blanket fix.

### 5. `MISSING_OBSERVED_YEAR_BUILT` — Lyon 8 + Madrid 11 (7 alone + 4 combined with dwelling-count-missing) = 19 buildings — never root-caused with citations

**Investigate:** trace exactly which source field this comes from for FR/ES buildings, confirm whether it is
truly absent from every reachable source (BD-TOPO / Spanish cadastre) for these specific buildings, or
whether an alternate registry has a year-built value that was never joined in.

### 6. Bologna `CENSUS_SECTION_PERIOD_TIE_*` (12) + `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS` (4) — 16 buildings — never investigated

Code: `scripts/run_eu_s2_district_campaign.py` lines ~291 (`CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS`) and
~298 (`CENSUS_SECTION_PERIOD_TIE_...`), inside `_it_rows`. A building's construction period is assigned by
which Italian census section it falls in; a "tie" means two adjacent census-period codes are equally
plausible and the code refuses to pick. **Investigate:** is there a real secondary signal (building footprint
centroid distance to each candidate section's centroid, or an independent Bologna open-data building-age
field) that could break the tie without guessing? Same question for the 4 "no residential buildings in this
census section" rows — is that a data artifact (wrong section boundary) or genuinely correct?

### 7. London `UNMAPPABLE_RESIDENTIAL_TYPE` (6) — never investigated

Code: `scripts/run_eu_s2_district_campaign.py:197`, inside `_gb_rows`. Small residual — check what OSM
building tag(s) these 6 rows carry that neither the house/apartment/terrace mapping nor `FINDING 251`'s fix
covers. Likely a quick, low-effort category; report what the actual tag values are.

### 8. `MISSING_OBSERVED_DWELLING_COUNT` — Lyon 1 + Madrid 1 = 2 buildings — trivial, low priority, report only if a one-line explanation falls out of category 5's tracing.

### 9. Lyon `TYPOLOGY_SIGNALS_DISAGREE` residual outliers — 10 buildings — **already adjudicated, do not re-open**

8 buildings at `dwellings >= 15 & storeys <= 4`, 2 at `dwellings == 1 & storeys >= 5`. The `D-EU-37` decision
request (§4, option 1) explicitly scoped these out as "too few to generalize a rule from" and the owner's
ruling only widened the 176-building coherent shape, not these. List them for completeness in your report but
do not spend investigation effort here unless you find a genuinely new, previously-unconsidered signal — and
even then, flag it as a new candidate for an owner ruling, not something to implement.

## Report format

For each of the 9 categories: the exact count, the exact code citation you verified, your investigation
method, and one of three verdicts — **(a) genuine dead end**, with what you checked to be sure; **(b) a real
code/data fix exists**, with the exact source and expected recovery count; or **(c) a policy question for the
owner**, framed the same way `DECISION_REQUEST_D-EU-37...md` was (what the options are, what each recovers,
why it isn't a transcription but a new threshold). Do not implement anything — this is a report back to the
project owner, who rules each open item the same way `D-EU-37` was ruled.

## Where to write findings

Do not edit any existing file. If you want a durable record rather than just a chat reply, write a **new**
file named `docs/docs_ACTIVE/europeanLocations/debugs/docs/INVESTIGATION_full-fleet-100pct-2026-09-04_REPORT.md`
— nothing else.
