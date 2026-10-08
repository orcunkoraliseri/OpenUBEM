# PLAN — read the observed EPC `construction_year` already on disk, recover London's 30 buildings

- **Slug:** `eu-epc-construction-year-2026-09-04`
- **Date:** 2026-09-04
- **Ruling:** owner, 2026-09-04: *"yes, apply the 30 free fixes."* Scope is exactly the two **(b)** fixes —
  `b1` (+24) and `b2` (+6). **No (c) ruling in this plan.** Nothing in the straddle-intersection rule, the
  13–14 typology gap, `sap_floor_dimensions`, the ISTAT ties, the `residential` tag or the `D-EU-58`
  tolerance is implemented here.
- **DESIGN pointer:**
  `docs/docs_ACTIVE/europeanLocations/debugs/docs/INVESTIGATION_full-fleet-100pct-2026-09-04_REPORT_claude-opus-5.md`
  §1.2 (`b1`), §1.3(i) (`b2`), §10 ledger. Brief:
  `docs/docs_ACTIVE/europeanLocations/debugs/INVESTIGATION_full-fleet-100pct-2026-09-04.md`.

---

## 1. Hard rules for the executor

1. **No network. At all.** Every input this plan needs is already on disk. If any step appears to need an
   HTTP call, you have misread the plan — stop and quote the line.
2. Create exactly one new script and edit exactly one existing function. Nothing else in the repo changes:
   - new: `scripts/ingest_gb_epc_construction_year.py`
   - new: `tests/test_eu11_gb_epc_construction_year.py`
   - edit: `_gb_rows` **only**, in `scripts/run_eu_s2_district_campaign.py`
3. **`openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_certificates.csv` is read-only and must not be
   rewritten.** The new year signal goes into a *separate* sidecar file, the same way Madrid's Catastro
   attributes do (`es_catastro_attribute_sidecar.csv`). A delivered evidence artefact is never regenerated.
4. **Do not overwrite `GB-LDN-STDUNSTANS_full_fleet_2026-09-04/`.** It is the baseline this plan is measured
   against and it is cited in the report and in `STATE_european_locations_v5.md`. Write to the new folder
   named in §2. Promotion of the new folder over the old one is a director decision after T05, not part of
   this plan.
5. Run `prepare()` for **`GB-LDN-STDUNSTANS` only**. No other district's `prepare()` runs; no other
   district's folder is read, written or deleted.
6. **Nothing simulates.** This is IDF preparation only (`status: PREPARED_FOR_SPEED`). Do not run
   EnergyPlus, do not touch Speed, do not submit any job, do not open an ssh session.
7. Do not touch `git` — no `add`, `commit`, `reset`, `checkout --`, `clean`. Read-only `git status
   --porcelain` is allowed and is required by T05.
8. Fail closed everywhere. A missing cache file, an unparseable year, a year outside `1000..2026` — record
   nothing and move on. Never substitute, never interpolate, never default.
9. If the DESIGN is ambiguous, **STOP and quote the conflict**. Do not propose an alternative design.

## 2. File layout

| File | Change |
|---|---|
| `scripts/ingest_gb_epc_construction_year.py` | **new** — offline sidecar builder (reads the certificate cache, writes one CSV) |
| `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv` | **new** — the sidecar it writes |
| `scripts/run_eu_s2_district_campaign.py` | edit `_gb_rows` only (lines 170-201), plus one module-level path constant and one new helper function |
| `tests/test_eu11_gb_epc_construction_year.py` | **new** — unit tests for the helper |
| `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_full_fleet_epcyear_2026-09-04/` | **new folder** — the rebuilt London prep |

Everything else in the repo is read-only for this task.

## 3. Dependency decisions (pinned — transcribe, do not design)

### 3.1 Why a sidecar and not a wider harvest

The EPC harvester searched for `construction_age_band` only; that is visible in the CSV's own
`year_key_used` column, whose only non-null values are three variants of that key. Full-**SAP** certificates
(new build / on-construction) do not carry a band — they carry
`/body/data/sap_building_parts[i]/construction_year`, an explicit calendar year. 5,385 certificate payloads
are already cached under `openubem/outputs/eu_evidence/EU-04/D-EU-22/_cache/certificate/`. Nothing has to be
fetched; the field simply has to be read.

**Measured, and these are the numbers T01 must reproduce exactly:**

- 1,336 cached certificates carry a `construction_year` (each carries exactly one → **1,336 sidecar rows**);
- 4,045 carry a band and no year; the two sets are **disjoint** (4,045 + 1,336 + 4 empty = 5,385);
- the 1,336 map to **67 distinct `osm_id`**.

### 3.2 The sidecar file — exact contract

Path: `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv`

Columns, in this order: `osm_id, certificateNumber, registrationDate, construction_year, source_key`

One row per `(certificate, building part)` that carries a usable year. Build rule:

```
for each row of gb_epc_certificates.csv:
    path = _cache/certificate/<certificateNumber>.json
    if path does not exist: skip the row          # fail closed, no network
    data = json["body"]["data"]
    for i, part in enumerate(data.get("sap_building_parts") or []):
        v = part.get("construction_year")
        if v is None or v == "": continue
        try: y = int(v)
        except (TypeError, ValueError): continue
        if not (1000 <= y <= 2026): continue      # same guard as _parse_bdtopo_year
        emit row(osm_id, certificateNumber, registrationDate, y,
                 f"/sap_building_parts[{i}]/construction_year")
```

The script writes the CSV and prints a one-object JSON summary with `rows`, `certificates`, `osm_ids`,
`cache_files_missing`. It takes no arguments and makes no network call.

### 3.3 The two decision rules — exact semantics

Both are **fail-closed** and both are strictly additive: a footprint that maps today must map identically
after this change, with a byte-identical IDF.

**`b1` — no age band at all.** If the footprint has *no* usable EPC band, but every observed
`construction_year` for that footprint resolves to **one** TABULA GB period, use that period.
A year is a point, not an interval, so no straddle is possible. → **27 footprints qualify, 24 of them also
pass the existing type and storey gates.**

**`b2` — a straddling band plus a year that agrees with it.** If the footprint's band straddles two periods,
accept a year **only when every observed year for that footprint falls inside that band's own
`[lo, hi]` interval and all of them resolve to one period.** A year outside the band is a redevelopment or a
converted unit and must be refused — 7 such footprints exist and this rule deliberately leaves them
excluded. → **8 footprints qualify, 6 of them also pass the existing type and storey gates.**

### 3.4 The helper to add (verbatim), and where

Add immediately **above** `_gb_rows` in `scripts/run_eu_s2_district_campaign.py`:

```python
def _gb_age_decision(band: str | None, observed_years: set[int]) -> tuple[str, str, str] | tuple[None, str, str]:
    """Resolve one GB footprint's TABULA period, fail-closed.

    Returns ``(period, age_band_label, construction_period_provenance)`` on success, or
    ``(None, exclusion_key, "")`` when the evidence does not determine a single period.
    An observed ``construction_year`` is a point, so it can only ever narrow the band,
    never widen it; a year that contradicts its own band is refused, not preferred.
    """
    if band not in GB_EPC_BANDS:
        periods = {tabula_period("GB", year) for year in observed_years}
        if len(periods) == 1:
            return periods.pop(), band if band in GB_EPC_BANDS else "", "EPC_OBSERVED_CONSTRUCTION_YEAR"
        return None, "MISSING_OBSERVED_EPC_AGE_BAND", ""
    lo, hi = GB_EPC_BANDS[band]
    first, last = tabula_period("GB", lo), tabula_period("GB", hi)
    if first == last:
        return first, band, ""
    in_band = {year for year in observed_years if lo <= year <= hi}
    in_band_periods = {tabula_period("GB", year) for year in in_band}
    if observed_years and in_band == observed_years and len(in_band_periods) == 1:
        return in_band_periods.pop(), band, "EPC_CONSTRUCTION_YEAR_RESOLVED_STRADDLE"
    return None, f"PERIOD_STRADDLE_{band}_{first}_{last}", ""
```

Note the `b1` branch returns an **empty** `age_band_label`: there is no band letter to report, and the
TABULA period travels in `age_band` (set in `_gb_rows`, below) exactly as it already does for FR and ES via
`_mapped_rows`. Do not invent a synthetic band letter.

### 3.5 The `_gb_rows` edit (verbatim replacement of lines 182-187)

Add next to `GB_EPC` at module level:

```python
GB_EPC_YEARS = ROOT / "openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv"
```

Inside `_gb_rows`, after the existing `bands = ...` line, add:

```python
    year_lookup: dict[str, set[int]] = {}
    if GB_EPC_YEARS.exists():
        side = pd.read_csv(GB_EPC_YEARS)
        for key, group in side.groupby(side["osm_id"].astype(str)):
            year_lookup[key] = {int(v) for v in group["construction_year"]}
```

Then replace exactly these six lines (currently `scripts/run_eu_s2_district_campaign.py:182-187`):

```python
        if band not in GB_EPC_BANDS:
            exclusions["MISSING_OBSERVED_EPC_AGE_BAND"] += 1; continue
        lo, hi = GB_EPC_BANDS[band]
        first, last = tabula_period("GB", lo), tabula_period("GB", hi)
        if first != last:
            exclusions[f"PERIOD_STRADDLE_{band}_{first}_{last}"] += 1; continue
```

with:

```python
        first, age_label, period_provenance = _gb_age_decision(band, year_lookup.get(building_id, set()))
        if first is None:
            exclusions[age_label] += 1; continue
```

and change the `result.append({...})` at the end of the loop so that `"age_band": band` becomes
`"age_band": age_label or first`, and one key is added: `"construction_period_provenance": period_provenance`.

**Nothing else in the function changes.** `_record_for_period(records, "GB", building_type, first)` already
takes the period and is untouched. `prepare()` already writes `construction_period_provenance` from the row
(`scripts/run_eu_s2_district_campaign.py:460`), so **`prepare()` itself must not be edited** — the new
column arrives for free, blank on the 389 rows that map today and labelled on the 30 new ones.

### 3.6 Rebuild command (exact)

```
.venv/Scripts/python.exe scripts/run_eu_s2_district_campaign.py --district GB-LDN-STDUNSTANS --out openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_full_fleet_epcyear_2026-09-04
```

The `--out` folder must **not exist** before the run. `scripts/run_eu_s2_district_campaign.py:411` calls
`schedule_dir.mkdir()` with no `exist_ok=True`, so re-running into a populated folder raises
`FileExistsError` — a known, pre-existing script behaviour recorded in
`PLAN_eu-d-eu-37-lyon-mfh-widen-2026-09-04.md` §7a. If you need to re-run T04, delete only the
`epcyear` folder created by T04 and start it again. Never delete anything under
`GB-LDN-STDUNSTANS_full_fleet_2026-09-04/`.

## 4. DESIGN facts (line citations)

- `GB_EPC` path constant — `scripts/run_eu_s2_district_campaign.py:50`.
- `GB_EPC_BANDS` — `scripts/run_eu_s2_district_campaign.py:65-69`, with the comment above it stating the
  rule this plan preserves: *"A band may be used only when the complete interval belongs to one TABULA
  period; straddles remain excluded."* That rule is unchanged; `b2` does not relax it, it supplies a
  different, sharper observation for the same footprint.
- `_gb_rows` — `scripts/run_eu_s2_district_campaign.py:170-201`; the two exclusion sites at `:182-183` and
  `:186-187`.
- `prepare()` — signature `scripts/run_eu_s2_district_campaign.py:355`; the
  `"construction_period_provenance": row.get("construction_period_provenance", "")` write at `:460`;
  `main()` at `:479-487`.
- Precedent for a separate attribute sidecar joined by id without rewriting the manifest:
  `openubem/semantic/european_archetype_mapping.py:331-365` (`apply_attribute_sidecar`) and
  `openubem/outputs/eu_evidence/EU-04/es_catastro_attribute_sidecar.csv`.
- TABULA GB period boundaries, read off `tabula_period("GB", y)`:
  `GB.01 ≤ 1918 · GB.02 1919–1944 · GB.03 1945–1964 · GB.04 1965–1980 · GB.05 1981–1990 ·
  GB.06 1991–2003 · GB.07 2004–2009 · GB.08 ≥ 2010`.
- London baseline, read off
  `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_full_fleet_2026-09-04/summary.json`:
  `population_attempted 1242`, `population_prepared 389`, `blocker_exclusions`
  `MISSING_OBSERVED_EPC_AGE_BAND 445`, `MISSING_OBSERVED_STOREY_COUNT 47`,
  `PERIOD_STRADDLE_B_GB.01_GB.02 76`, `PERIOD_STRADDLE_C_GB.02_GB.03 77`,
  `PERIOD_STRADDLE_D_GB.03_GB.04 97`, `PERIOD_STRADDLE_F_GB.04_GB.05 66`,
  `PERIOD_STRADDLE_J_GB.06_GB.07 19`, `PERIOD_STRADDLE_K_GB.07_GB.08 20`,
  `UNMAPPABLE_RESIDENTIAL_TYPE 6`.

## 5. Tasks

### T01 — build the construction-year sidecar
**What:** write `scripts/ingest_gb_epc_construction_year.py` per §3.2 and run it once.
**Why:** the year exists in the cached payloads and in no column the pipeline reads; a sidecar exposes it
without rewriting a delivered evidence artefact (hard rule 3).
**How:** transcribe §3.2. No arguments, no network, no writes outside the one CSV.
**How to test:** the printed summary must read exactly `rows: 1336`, `certificates: 1336`, `osm_ids: 67`.
Confirm `gb_epc_certificates.csv` is **unmodified** (`git status --porcelain` must not list it, and its
byte size must still be 908500). Report the four summary numbers.
**If the counts differ:** STOP and report the actual numbers. Do not adjust the script to reach 1336.

### T02 — add the decision helper and wire it into `_gb_rows`
**What:** add `_gb_age_decision` (§3.4), the `GB_EPC_YEARS` constant and the `year_lookup` load, and make
the two replacements in `_gb_rows` (§3.5).
**Why:** `b1` and `b2`, the two owner-approved fixes.
**How:** transcribe §3.4 and §3.5 exactly. `prepare()` is **not** edited. No other function is edited.
**How to test:** covered by T03; do not run `prepare()` yet.

### T03 — unit-test the helper
**What:** write `tests/test_eu11_gb_epc_construction_year.py` with these six cases, calling
`_gb_age_decision` directly (no file IO, no fixtures on disk):

| Case | Input | Expected |
|---|---|---|
| non-straddling band, unchanged | `("E", set())` | `("GB.04", "E", "")` |
| straddling band, no year | `("D", set())` | `(None, "PERIOD_STRADDLE_D_GB.03_GB.04", "")` |
| no band, single-period year (`b1`) | `(None, {2019})` | `("GB.08", "", "EPC_OBSERVED_CONSTRUCTION_YEAR")` |
| no band, years spanning two periods | `(None, {2008, 2019})` | `(None, "MISSING_OBSERVED_EPC_AGE_BAND", "")` |
| straddle + in-band year (`b2`) | `("K", {2009})` | `("GB.07", "K", "EPC_CONSTRUCTION_YEAR_RESOLVED_STRADDLE")` |
| straddle + contradicting year | `("B", {2013})` | `(None, "PERIOD_STRADDLE_B_GB.01_GB.02", "")` |

**Why:** the last case is the whole safety argument — a year that disagrees with its band must never win.
**How to test:** `.venv/Scripts/python.exe -m pytest tests/test_eu11_gb_epc_construction_year.py -q`.
Then run the existing suite for regressions:
`.venv/Scripts/python.exe -m pytest tests/test_eu_observed_archetype_mapping.py tests/test_eu02_fetchers.py -q`.
Report both results verbatim.

### 🛑 STOP-AND-REPORT 1 — after T03
Report T01's four numbers and both pytest results. **Do not start T04 until the director replies.**

### T04 — rebuild London's prep into a new folder
**What:** run the exact command in §3.6.
**Why:** regenerate `summary.json` / `prepared_buildings.csv` / IDFs against the two fixes.
**How:** confirm the `--out` folder does not exist, run it, confirm exit code 0.
**How to test:** read the new `summary.json` **off disk** (not from console memory) and compare against §4's
baseline. The predicted post-fix state, computed offline before this plan was written, is:

| Key | Before | Predicted after |
|---|---|---|
| `population_attempted` | 1242 | **1242** (unchanged — this recovers exclusions, it adds no candidates) |
| `population_prepared` | 389 | **419** |
| `MISSING_OBSERVED_EPC_AGE_BAND` | 445 | **418** (−27) |
| `MISSING_OBSERVED_STOREY_COUNT` | 47 | **52** (+5) |
| `PERIOD_STRADDLE_K_GB.07_GB.08` | 20 | **12** (−8) |
| `PERIOD_STRADDLE_B / C / D / F / J` | 76 / 77 / 97 / 66 / 19 | **unchanged** |
| `UNMAPPABLE_RESIDENTIAL_TYPE` | 6 | **unchanged** |

The `+5` on storeys is expected and correct: five footprints gain an age from this fix and then fail the
*next* gate instead — `way/192335494`, `way/459203320`, `way/823489446`, `way/823489447`, `way/823489448`.
They are not a regression; they move from one exclusion bucket to another.

`prepared_buildings.csv` must show `construction_period_provenance` populated on exactly 30 rows:
**24 `EPC_OBSERVED_CONSTRUCTION_YEAR` + 6 `EPC_CONSTRUCTION_YEAR_RESOLVED_STRADDLE`**, and blank on the
other 389.

**One outcome is allowed to differ and must be reported, not fixed:** if an
`IDF_ASSEMBLY_FAILED_RuntimeError` key appears (London has none today), `population_prepared` will be below
419 by that count. That is a real new observation about the 30 new footprints. Report it; do not attempt any
geometry repair, which is out of scope for this plan.

**If any other number differs from the table:** STOP and report the actual `summary.json`.

### T05 — audit
**What:** prove the 389 baseline buildings are untouched and nothing outside §2 changed.
**Why:** the fixes are additive by construction; that has to be demonstrated, not asserted.
**How to test:** three checks, all reported verbatim:
1. Join the new `prepared_buildings.csv` to the baseline one on `building_id`. All 389 baseline rows must be
   present and their `idf_sha256` **identical**. Report the count of matched rows and the count of
   `idf_sha256` mismatches (which must be 0).
2. `git status --porcelain` must show exactly the three source files of §2 as new/modified
   (`scripts/ingest_gb_epc_construction_year.py`, `scripts/run_eu_s2_district_campaign.py`,
   `tests/test_eu11_gb_epc_construction_year.py`). Any other tracked change is a deviation — report it.
3. Confirm `GB-LDN-STDUNSTANS_full_fleet_2026-09-04/summary.json` is unchanged (still
   `population_prepared: 389`), and that no folder under `eu_evidence/EU-11/` other than the new `epcyear`
   one was created or modified.

### 🛑 STOP-AND-REPORT 2 — after T05
Report the before/after table as read off disk, the 30-row provenance split, and the three T05 checks.
**Do not promote the new folder over `GB-LDN-STDUNSTANS_full_fleet_2026-09-04/`** — that is a director
decision. Do not touch Speed. Do not start any other district.

## 6. What this plan explicitly does not do

- No `(c)` ruling is implemented: not the straddle-intersection rule (+69 more), not the 13–14 typology gap
  (+38), not `sap_floor_dimensions` storeys (+33), not the ISTAT tie policy (+12), not the `residential` tag
  (+6), not the `D-EU-58` tolerance widening (+4).
- No Catastro `BuildingPart` fetch (that is Madrid's +163 and needs a network authorisation this plan does
  not carry).
- No simulation, no Speed submission, no promotion of the new evidence folder.
- Fleet after this plan, if T04 lands as predicted: **3,066 → 3,096 / 4,186 (73.2 % → 74.0 %)**.

## 7. Progress log

(executor appends one entry per completed task below, in this format)

```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts:
- Deviations:
- Test status:
- Notes:
```

#### T01 — build the construction-year sidecar — completed 2026-09-04
- Artifacts: `scripts/ingest_gb_epc_construction_year.py` (new);
  `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv` (new, 130360 bytes).
- Deviations: none.
- Test status: printed summary `{"rows": 1336, "certificates": 1336, "osm_ids": 67,
  "cache_files_missing": 3238}` — matches the pinned `rows: 1336, certificates: 1336, osm_ids: 67` exactly.
  `gb_epc_certificates.csv` confirmed unmodified: byte size still 908500, `git status --porcelain` lists
  nothing for it.
- Notes: `cache_files_missing: 3238` is not pinned by the plan; traced it to `certificateNumber == NaN`
  rows in `gb_epc_certificates.csv` (8623 total rows, 5385 unique certificate numbers, 3238 unmatched/NaN
  rows) — the loop iterates per CSV row per §3.2's pseudocode, and every missing-cache case is a NaN
  certificate number, none is a real cache-file gap. Fail-closed as specified.

#### T02 — add the decision helper and wire it into `_gb_rows` — completed 2026-09-04
- Artifacts: `scripts/run_eu_s2_district_campaign.py` edited — `GB_EPC_YEARS` constant added next to
  `GB_EPC`; `_gb_age_decision` added verbatim immediately above `_gb_rows`; `year_lookup` load and the two
  replacements applied verbatim inside `_gb_rows`; `result.append` updated to
  `"age_band": age_label or first` plus new key `"construction_period_provenance": period_provenance`.
  `prepare()` untouched.
- Deviations: none — transcribed §3.4/§3.5 verbatim.
- Test status: covered by T03 per plan; module import sanity-checked
  (`_gb_age_decision("E", set())` → `("GB.04", "E", "")`).
- Notes: none.

#### T03 — unit-test the helper — completed 2026-09-04
- Artifacts: `tests/test_eu11_gb_epc_construction_year.py` (new, 6 test functions, one per case in §5 T03's
  table, calling `_gb_age_decision` directly, no file IO).
- Deviations: none.
- Test status: `pytest tests/test_eu11_gb_epc_construction_year.py -q` → **6 passed, 0 failed**, all six
  expected tuples matched exactly. Regression suite
  `pytest tests/test_eu_observed_archetype_mapping.py tests/test_eu02_fetchers.py -q` →
  **15 passed, 2 failed** in `test_eu_observed_archetype_mapping.py`:
  `test_all_live_manifests_are_accounted_for_with_fr_layout_readiness` (`layout_ready_count` 473 vs
  expected 297) and `test_derive_bdtopo_building_type_one_case_per_branch_and_exclusion`
  (`derive_bdtopo_building_type(6, 5, True)` returns `("MFH", None)` vs expected
  `(None, TYPOLOGY_SIGNALS_DISAGREE)`).
- Notes: both failures are on the FR/`openubem.semantic.european_archetype_mapping` pathway, which this
  plan's §2 file layout does not touch and which this test file does not import anything from
  (`scripts/run_eu_s2_district_campaign.py`, `_gb_age_decision`, the sidecar, or `GB_EPC_YEARS`). One
  failure names `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` / `TYPOLOGY_SIGNALS_DISAGREE`, matching this
  plan's own §6 exclusion list ("not the 13–14 typology gap"), i.e. a pre-existing, already-known-open FR
  condition, not a regression introduced by T01/T02. Not fixed — out of scope per hard rule 2 (only the
  three §2 files may change) and per §1 (no alternatives, no unrequested fixes).

#### T04 — rebuild London's prep into a new folder — completed 2026-09-04
- Artifacts: `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_full_fleet_epcyear_2026-09-04/`
  (new folder — `summary.json`, `prepared_buildings.csv`, `fleet.lst`, `gb_ldn_stdunstans_manifest.csv`,
  419 IDFs under `idfs/`).
- Deviations: none. Ran the exact §3.6 command against the confirmed-absent `--out` folder; exit code 0.
- Test status: `summary.json` read off disk matches §4's predicted table exactly —
  `population_attempted 1242` (unchanged), `population_prepared 419` (+30), `MISSING_OBSERVED_EPC_AGE_BAND
  418` (−27), `MISSING_OBSERVED_STOREY_COUNT 52` (+5), `PERIOD_STRADDLE_K_GB.07_GB.08 12` (−8),
  `PERIOD_STRADDLE_B/C/D/F/J` unchanged at `76/77/97/66/19`, `UNMAPPABLE_RESIDENTIAL_TYPE` unchanged at `6`.
  No `IDF_ASSEMBLY_FAILED_RuntimeError` key present, so the allowed-to-differ outcome in §5 T04 did not
  occur. `prepared_buildings.csv` (419 rows) shows `construction_period_provenance` populated on exactly
  30 rows — 24 `EPC_OBSERVED_CONSTRUCTION_YEAR` + 6 `EPC_CONSTRUCTION_YEAR_RESOLVED_STRADDLE` — blank on
  the other 389, matching §5 T04 exactly.
- Notes: none.

#### T05 — audit — completed 2026-09-04
- Artifacts: none (read-only audit).
- Deviations: none in the three §2 source files or the new folder; see check 2 note below for unrelated
  same-window repo activity that is not part of this plan.
- Test status:
  1. Baseline join on `building_id`: 389/389 baseline rows matched in the new `prepared_buildings.csv`,
     `idf_sha256` identical on all 389 (0 mismatches).
  2. `git status --porcelain` filtered to paths with mtime ≥ 2026-09-04 21:30 (this plan's execution
     window) returns 12 paths. Exactly 5 are this plan's §2 set: `scripts/ingest_gb_epc_construction_year.py`
     (new), `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv` (new),
     `scripts/run_eu_s2_district_campaign.py` (modified), `tests/test_eu11_gb_epc_construction_year.py`
     (new), `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_full_fleet_epcyear_2026-09-04/` (new
     folder). The remaining 7 are **not** part of this plan's file layout and were not touched by T04/T05:
     this plan doc itself (its own T01–T03 progress-log edits pre-date this session), plus
     `BRIEF_european_locations_v5.md`, `CHECKLIST_european_locations_v5.md`,
     `STATE_european_locations_v5.md`, `DEBUG_why-not-100-percent-2026-09-04.md` (all new/untracked) and
     `DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md`, `DEBUG_REFERENCES_european_locations.md` (both
     modified) — concurrent EU-arc activity outside this plan's scope, already on disk before T04 ran.
  3. Baseline `GB-LDN-STDUNSTANS_full_fleet_2026-09-04/summary.json` unchanged: `population_prepared` still
     389, file mtime pre-dates this plan's 21:30 cutoff by ~4 hours. No folder under `eu_evidence/EU-11/`
     other than the new `..._epcyear_2026-09-04/` has an mtime at/after the cutoff.
- Notes: check 2's raw git-status set is a superset of this plan's changes because of unrelated same-day
  work in the repo; the plan's own five artefacts are present and clean, and nothing this plan was
  forbidden from touching (the 389-row baseline, other districts, Speed, git) was touched.
