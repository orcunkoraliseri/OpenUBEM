# EXECUTOR PROMPT — EU-04 / `FR-TYPOLOGY-IMPL-01`, implement the ruled `D-EU-04-G` (Option G1)

**Paste this whole file into a fresh executor session. Execute it top to bottom. Do not propose
alternatives. If anything in it is ambiguous or contradicts the code you find, STOP and quote the
conflict rather than choosing.**

**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Date opened:** 2026-08-25
**Authority:** `docs/docs_ACTIVE/europeanLocations/debugs/docs/DECISION_REQUEST_EU-04_FR_typology_2026-08-25.md`
— status `RULED`, **Option G1 selected**, both consequences accepted by the owner.

---

## 0. What is already true, and what is not

The ruling is recorded. **The rule is not implemented.** Verified on disk before this prompt was
written:

- `DERIVED_BDTOPO_TWO_SIGNAL` appears in **no `.py` file** in the repository.
- `openubem/semantic/european_archetype_mapping.py` was last modified at 10:56 on 2026-08-25,
  before the ruling.
- `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness_summary.json` still
  reports `layout_ready_count: 0` and `UNMAPPABLE_RESIDENTIAL_TYPE: 522`.

The counts quoted in §3 below are the **manager's own measurement**, taken from the manifest while
the decision request was being written. They are the acceptance target of this task, not a record
of work already done.

---

## 1. Hard rules

1. **No network.** No WFS call, no re-acquisition, no ERA5. The manifest on disk is the input.
   `openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg` must not be rewritten.
2. **Fail-closed.** A row that does not satisfy exactly one branch of §2 is **excluded with a named
   reason**. Never assign a default type, never impute a dwelling count, never widen a threshold to
   reach a count.
3. **Derived is not observed.** Every derived type carries `DERIVED_BDTOPO_TWO_SIGNAL`, and the
   readiness summary must report derived and observed types in **separate counters** so no artefact
   can quote a derived type as a source attribute.
4. **France only.** The derivation is BD TOPO-specific. `ES`, `GB` and `IT` behaviour must not
   change by a single row — the four-site totals for those three sites are a regression check.
5. Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first.
   After solving any error, register it there before closing the task, in the house format.
6. Do not edit root `main.py`, OVERVIEW or DESIGN docs. No `.py` under `docs/`.
7. Append a progress-log entry per task (§5). Do not create files this prompt does not name.

---

## 2. The pinned rule (copied verbatim from the ruled decision)

Applied in this order to a French row; the **dwelling signal and the storey signal must agree**:

| Branch | Condition | Result |
|---|---|---|
| 1 | `dwellings == 1` and `storeys <= 4` and the footprint **shares a boundary** with a neighbour | `TH` |
| 2 | `dwellings == 1` and `storeys <= 4` and the footprint is **free-standing** | `SFH` |
| 3 | `2 <= dwellings <= 12` and `storeys <= 4` | `MFH` |
| 4 | `dwellings >= 15` and `storeys >= 5` | `AB` |
| — | anything else | **excluded**, reason recorded |

Every threshold is read off `openubem/data/construction/tabula_archetypes_fr.json` (SFH/TH carry
`n_apartment` = 1 in all ten periods at 1–3 storeys; MFH spans 4–12 dwellings at 1–4 storeys; AB
spans 15–86 dwellings at 5–10 storeys). **Do not change a threshold.**

Exclusion reason tokens — use exactly these strings:

- `TYPOLOGY_SIGNALS_DISAGREE` — dwellings and storeys select different branches or none.
- `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` — `dwellings` is 13 or 14.
- `MISSING_OBSERVED_DWELLING_COUNT` — no `nombre_de_logements`.
- `MISSING_OBSERVED_STOREY_COUNT` — no `levels`.

---

## 3. Acceptance numbers — reproduce these exactly

Measured by the manager on the 530 retained French rows:

| | `SFH` | `TH` | `MFH` | `AB` | total |
|---|---:|---:|---:|---:|---:|
| typed | | | | | **302** |
| typed **and** year observed | **7** | **21** | **123** | **146** | **297** |

Exclusions: **189** signal disagreements · **37** in the 13–14 dwelling gap · **1** missing a
dwelling count · **1** missing a storey count → **228 excluded of 530**.

**If your run does not reproduce 302 / 297 / 7 / 21 / 123 / 146, STOP and report the difference
with the row-level evidence. Do not adjust the rule to reach the numbers.**

---

## 4. Tasks

### T01 — read the two dwelling signals off the manifest

**What.** Add to `openubem/semantic/european_archetype_mapping.py` a private helper that returns the
observed dwelling count for a row: parse `surplus_tags` (JSON string) and read
`nombre_de_logements`; return `None` when absent, non-numeric, non-integer or `<= 0`.
The storey count is already `row["levels"]`; return `None` when it is null.

**Why.** The dwelling count is present in the manifest but **no code reads it today** — which is why
the one London building that has a year still ends at `MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT`.
The layout kernel refuses to infer a dwelling count from a footprint, by design.

**How.** Pure function, no I/O, no geometry. `surplus_tags` values are strings — cast before
comparing.

**How to test.** Unit test over the four shapes: present integer, absent key, non-numeric string,
zero.

### T02 — compute footprint adjacency

**What.** Add a function that, given the French `GeoDataFrame`, returns a boolean Series
`is_attached` — `True` when the footprint shares a boundary with any other footprint in the
manifest.

**Why.** `SFH` versus `TH` is the only distinction the source cannot state; adjacency is the
measurable proxy, and it is measurable from the footprints already on disk.

**How.** Reproject to **EPSG:2154** (Lambert-93) before any predicate. Use a spatial index
(`sindex`) and treat a shared boundary as `touches` **or** an intersection whose result is not a
point — a `0.0` m buffer tolerance, no positive buffer. Self-matches excluded by `osm_id`.
Expected on this manifest: **488 attached, 42 free-standing** — reproduce it exactly.

**How to test.** A synthetic fixture of three squares — two sharing an edge, one 5 m away — must
give `[True, True, False]`.

### T03 — apply the two-signal derivation, fail-closed

**What.** Add `derive_bdtopo_building_type(dwellings, storeys, is_attached)` implementing §2
exactly, returning `(building_type | None, reason | None)`. Wire it into
`map_observed_building_to_tabula` **behind** `OBSERVED_TAG_TO_TABULA_TYPE`: the observed tag wins
whenever it maps; the derivation runs only when the tag maps to nothing **and** the country is `FR`.

**Why.** The mapping contract stays fail-closed and the observed path is unchanged, so `ES`, `GB`
and `IT` cannot move.

**How.** Add a `type_provenance` field to `EuropeanArchetypeMappingDecision`, valued
`OBSERVED_TAG` or `DERIVED_BDTOPO_TWO_SIGNAL`. Where the derivation succeeds and the year is
present, resolve the archetype through the existing `select_tabula_archetype` path unchanged.
Where a dwelling count is present, the decision must reach `layout_ready = True` rather than
stopping at `MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT`.

**How to test.** Table-driven test with one case per branch **and** one per exclusion token,
including `dwellings = 13` and `dwellings = 14`; plus an assertion that a row whose
`building_tag` maps observationally is **never** stamped `DERIVED_BDTOPO_TWO_SIGNAL`.

### T04 — regenerate the readiness evidence and report

**What.** Re-run `write_eu02_archetype_mapping_readiness` over the four manifests into
`openubem/outputs/eu_evidence/EU-04/`. Extend the summary with
`type_provenance_counts` and a per-site `derived_type_counts`, keeping every existing key.

**Why.** The readiness summary is this arc's published measurement of what the corpus can support.

**How to test.** Report, from the regenerated JSON: `layout_ready_count`, the full
`reason_counts`, `type_provenance_counts`, the four French type counts, and the unchanged
`ES`/`GB`/`IT` numbers. Then run
`pytest -q tests/test_eu02_fetchers.py tests/test_eu_observed_archetype_mapping.py` and the full
European suite, and report both counts and durations.

**Expected:** `layout_ready_count` rises from **0** to **297**;
`UNMAPPABLE_RESIDENTIAL_TYPE` falls from 522 to the French exclusions that remain untyped; the
`ES` (1,194), `GB` (1,242) and `IT` (1,220) site counts and their reasons are **byte-identical** to
the current file.

---

## 5. Stop-and-report points

- **CP-1, after T03.** Report the derivation's counts against §3 before regenerating any evidence.
  If they differ, stop there.
- **CP-2, after T04.** Report the readiness deltas and both test results.

At each checkpoint append one progress-log entry to
`docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv` and the matching row to
Walkthrough Table 4, nine fields, UTC timestamp, commit + `dirty` caveat.

---

## 6. What this task does **not** do

- It does not select the S1 sample. Forming S1 is the next slice, after this one is audited.
- It does not touch `ES`, `GB` or `IT`.
- It does not fix the hardcoded `current_year = 2026` in `bdtopo_fetcher.py:82` — that deviation is
  recorded and is a separate decision.
