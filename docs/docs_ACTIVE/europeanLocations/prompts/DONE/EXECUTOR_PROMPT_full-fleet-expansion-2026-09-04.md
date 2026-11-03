# Executor prompt — EU full-fleet expansion prep (2026-09-04)

Copy this whole file into the external agent session (Gemini / Antigravity). It is self-contained: you have
no access to this project's other conversations, memory, or `CLAUDE.md`. Everything you need is below.

## Repository facts you cannot guess

- Working directory: `C:\Users\o_iseri\Desktop\OpenUBEM` (Windows).
- `python` is **not** on `PATH`. Always invoke `.venv\Scripts\python.exe` (or, if you are running under a
  POSIX shell inside this checkout, `.venv/Scripts/python.exe`) — never a bare `python` / `python3`.
- This is a git repository. **Do not commit, do not push, do not run any destructive git command**
  (`reset --hard`, `checkout --`, `clean -f`). Leave your edits and new output folders as-is; a human
  reviews and commits.
- **No cluster access from you.** Do not `ssh`, `scp`, or run anything cluster-related. This task is 100%
  local — two small code edits plus four local script runs that write files under `openubem/outputs/`.

## What this task is

Four European districts (Madrid, Lyon, London, Bologna) are simulated the published way — every residential
building, real footprint, real storeys — but today's fleet only covers buildings whose type was
classifiable by the existing pipeline (2,544 of 4,186 real residential buildings across the four districts).
The owner ruled that **every** residential building must eventually be simulated regardless of type
(house/apartment/terrace/generic), not just this narrower set. The gap is +1,659 buildings (London +1,160,
Lyon +237, Madrid +242, Bologna +20).

One district (London) already had its classification code fixed and verified: the pipeline never mapped
OpenStreetMap's `house` tag to a building type at all — not a data gap, a code gap. The fix recovered 82→389
London buildings by splitting `house` into semi-detached vs. terraced using footprint adjacency (does the
building's footprint touch its neighbour's footprint?). Madrid has the **same** kind of gap, not yet fixed.
Your job is to extend that fix to Madrid, then re-run the pipeline for all four districts so their IDFs
(EnergyPlus input files) are ready to hand to the Speed cluster the moment the currently-running campaign
finishes — you are **not** submitting anything to Speed yourself, just preparing the files.

## Hard rules

1. Edit **only** the two files named in Task 1. Do not touch
   `openubem/geometry/european_residential.py`, `openubem/geometry/european_nocore.py`, or
   `openubem/geometry/zoning.py` — that engine is closed and already verified against 2,544 test cases;
   changing it would invalidate that verification.
2. Write every new output under a path containing `_full_fleet_2026-09-04` (exact folders given in Task 2).
   **Never** write into, overwrite, or delete anything under
   `openubem/outputs/eu_evidence/EU-11/*_finding249_remedy_2026-09-04/` — that is the source fleet for a
   Speed cluster campaign that is running right now; touching it corrupts a live run.
3. Quote real numbers. When you report a count (buildings prepared, exclusions), copy it verbatim from the
   script's own `summary.json` output — never estimate, round, or paraphrase it.
4. If any district's `prepare()` run exits non-zero, or produces `population_prepared: 0`, or produces
   fewer prepared buildings than the "before" counts listed in Task 3 — **stop immediately and report**.
   Do not debug past that point, do not try alternative fixes, do not touch the closed engine files to make
   it pass. Report the exact error/count and stop.
5. When finished (or when you hit rule 4's stop condition), write your report as plain text at the end of
   your session — do not create any new `.md` file, do not edit any file other than the two named in Task 1
   and the output folders in Task 2.

## Task 1 — fix Madrid's classification gap (two small edits)

**File A**: `openubem/semantic/european_archetype_mapping.py`, line 225. It currently reads:
```python
    if building_type is None and country == "FR":
```
Change it to:
```python
    if building_type is None and country in ("FR", "ES"):
```
This is a function called `map_observed_building_to_tabula`. Line 213 already accepts `ES` as a valid
country code — only this one derivation branch was gated to France.

**File B**: `scripts/run_eu_s2_district_campaign.py`, function `_mapped_rows` (around lines 334-340). It
currently reads (approximately):
```python
def _mapped_rows(district: str, gdf: gpd.GeoDataFrame, records: list[dict]) -> tuple[list[dict], Counter]:
    country = DISTRICTS[district]["country"]
    if district == "ES-MAD-BERRUGUETE":
        gdf = apply_attribute_sidecar(gdf, pd.read_csv(ES_SIDECAR))
    if district == "FR-LYO-HAUTCOEURPENTES":
        gdf = gdf.assign(is_attached=compute_footprint_adjacency(gdf))
```
Add the same `is_attached` assignment to the ES branch, so it reads:
```python
    if district == "ES-MAD-BERRUGUETE":
        gdf = apply_attribute_sidecar(gdf, pd.read_csv(ES_SIDECAR))
        gdf = gdf.assign(is_attached=compute_footprint_adjacency(gdf))
    if district == "FR-LYO-HAUTCOEURPENTES":
        gdf = gdf.assign(is_attached=compute_footprint_adjacency(gdf))
```
**Both edits must land together.** File A alone is unsafe: without File B, every Madrid building lacking an
explicit type tag would silently get `is_attached = None` → treated as detached (`SFH`) even when it is
actually a mid-terrace row house (`TH`) — those behave very differently thermally, so this would quietly
mislabel real buildings rather than leaving them correctly excluded. `compute_footprint_adjacency` is already
imported in `scripts/run_eu_s2_district_campaign.py` — do not add a new import, just call it.

Do not touch Bologna's or London's classification functions (`_it_rows`, `_gb_rows`) — they do not have this
bug; London's was already fixed in a previous session.

## Task 2 — re-run all four districts

Run these four commands from the repository root, one at a time (they are independent — order does not
matter, but run all four):

```
.venv\Scripts\python.exe scripts\run_eu_s2_district_campaign.py --district GB-LDN-STDUNSTANS --out openubem\outputs\eu_evidence\EU-11\GB-LDN-STDUNSTANS_full_fleet_2026-09-04
.venv\Scripts\python.exe scripts\run_eu_s2_district_campaign.py --district FR-LYO-HAUTCOEURPENTES --out openubem\outputs\eu_evidence\EU-11\FR-LYO-HAUTCOEURPENTES_full_fleet_2026-09-04
.venv\Scripts\python.exe scripts\run_eu_s2_district_campaign.py --district ES-MAD-BERRUGUETE --out openubem\outputs\eu_evidence\EU-11\ES-MAD-BERRUGUETE_full_fleet_2026-09-04
.venv\Scripts\python.exe scripts\run_eu_s2_district_campaign.py --district IT-BOL-GALVANI2 --out openubem\outputs\eu_evidence\EU-11\IT-BOL-GALVANI2_full_fleet_2026-09-04
```

Yes — run London again even though its code fix already landed: that fix was only verified at the
classification stage in a prior session, never carried through a full run that actually writes IDFs for the
newly-recovered 307 buildings. This command does that.

Each command prints a JSON summary to stdout and also writes it to `<out>/summary.json`. Each run takes a
few minutes (it builds one IDF per building locally — no simulation, no EnergyPlus execution, just file
generation). Expect: several hundred to ~1,200 IDFs written per district, no cluster/network calls except
reading local files already on disk (the Bologna run — `_it_rows` — does call two Bologna open-data HTTP
endpoints for building heights and census sections; this is pre-existing behaviour, not new, and is not a
"live-network integration test" — it is how this script has always worked. Leave it as-is).

## Task 3 — report

For each of the four districts, report exactly:
- `population_attempted` and `population_prepared` from that district's `summary.json`.
- The full `blocker_exclusions` dict, verbatim (key: count, for every key).
- The delta in `population_prepared` versus these "before" counts (the narrow-census run that is still live
  on the Speed cluster): **London 82** (pre-fix; 389 is the classification-only number, not yet a real
  `prepare()` output — compare against 82), **Lyon 293**, **Madrid 952**, **Bologna 1,200**.

Expected shape (not a target to force — report what actually comes out): London should rise substantially
(the `house`-tag fix). Madrid should rise by some amount (the fix in Task 1) but not close the whole +242 gap
— many of Madrid's gap buildings are excluded for unrelated reasons (missing cadastral match, ambiguous
build period) that this task does not fix. Lyon and Bologna are **not expected to move** — their gaps are
real missing source data, not a code defect this task addresses; if either does move noticeably, say so, it
would be worth a second look by the project owner.

Write this report as your final plain-text output. Do not create a file for it.
