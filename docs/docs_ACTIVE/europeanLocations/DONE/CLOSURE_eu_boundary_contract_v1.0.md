# CLOSURE — §9.4 boundary contract, `eu_campaign_cell_spec_v1.0.json`

- **Date signed:** 2026-08-27
- **Checkpoint:** `EU-07 / CP-C` (plan `docs/docs_ACTIVE/europeanLocations/previous/PLAN_eu-boundary-closure-2026-08-26.md` §6 T08)
- **Contract:** `openubem/data/campaign/eu_campaign_cell_spec_v1.0.json`
- **Spec status:** `FROZEN_PINNED` — 510 cells, 510 unique `cell_id`, 22 caveats
- **Contract SHA-256:** `2af95d940045b7cb1d57657e123a31baa871f170ab65d902da3b9bbaada4a7e1`
- **Frozen at git commit:** `4bd4cad` (`git_dirty: true` — recorded honestly; the working tree carried
  the `it` ERA5 archives and this closure's own edits at freeze time)
- **Source of truth for the caveat register:** `MVP_european_locations.md` §12.10, Table 26

---

## 1. The one sentence

The §9.4 coupling boundary is **signed and immutable**: all four weather folds are pinned to a gated,
hashed EPW, all 510 campaign cells carry a resolved `epw_path` and a verified `weather_sha256`, and the
22-entry caveat register travels inside the artefact stating what the contract does **not** license
anyone to conclude.

## 2. What was verified, against which artefact, and how

Every line below was re-derived by the director **independently of the tool that wrote the file** —
`freeze_eu_campaign_cell_spec.py` is not permitted to be its own witness.

| Claim | Verified against | Result |
|---|---|---|
| 510 cells, 510 unique ids, 22 caveats, `FROZEN` | `eu_campaign_cell_spec_v1.0.json`, re-read and re-counted | **`510 510 22 FROZEN`** |
| Per-fold cell counts | the frozen `cells` block | es **120** / uk **180** / it **210** = 510 |
| Archetype count | distinct `(survey_fold, archetype_id)` | **102** |
| `f` ladder | `f_levels` | `[0.0, 0.15, 0.3, 0.5, 1.0]` |
| Every cell is executable | scan of all 510 cells | **0** cells unpinned; no `PENDING_EU07_WEATHER`, no null `weather_sha256` |
| Weather identity is real, not merely recorded | SHA-256 recomputed from each EPW **on disk** | 3 of 3 **match** the value frozen into the contract |
| Cell schema | `validate_campaign_cells` re-run on the frozen `cells` | accepted |

## 3. The four weather folds at signature

| Fold | City | Diary year | EPW | SHA-256 (head) | Registry status | Gate 5 |
|---|---|---|---|---|---|---|
| `fr` | Lyon-Bron | 2023 | `fr_lyon_bron_2023_era5.epw` | `2cf15311b9c6d112` | `RULED_PINNED_EXCEPTION` | `PASS_WITH_DOCUMENTED_NOVEMBER_EXCEPTION` (D-EU-07) |
| `es` | Madrid | 2010 | `es_madrid_2009_2010_y2010.epw` | `d2563b7dfdd8a787` | `RULED_PINNED_EXCEPTION` | `PASS_WITH_DOCUMENTED_EXCEPTION` (D-EU-15) |
| `uk` | London | 2015 | `uk_london_2014_2015_y2015.epw` | `379d10100e944b10` | `RULED_PINNED_EXCEPTION` | `PASS_WITH_DOCUMENTED_EXCEPTION` (D-EU-18 auto-grant) |
| `it` | Bologna | 2014 | `it_bologna_2013_2014_y2014.epw` | `ab631c6026e3f7cf` | `RULED_PINNED_EXCEPTION` | `PASS_WITH_DOCUMENTED_EXCEPTION` (**D-EU-19**, individually ruled) |

`fr` is the evidence fold and **is not a campaign fold** — it contributes no cell to the 510 (C-19).

Gates 1, 2, 3, 4 and 6 are `PASS` for all four folds. **No fold passed gate 5 cleanly.** Every one of
the four carries a named, quantified monthly exception, and that is the single most important fact in
this document: the contract is signed on four EPWs that disagree with the PVGIS/JRC benchmark on at
least one month each.

The registry's **top-level** `status` moved `PARTIALLY_PINNED` → **`FULLY_PINNED`** at this signature.
That value is not invented for the occasion: it is the vocabulary the repository's own fully-pinned
fixture already used (`tests/test_eu_campaign_cell_spec_freeze.py`, `_synthetic_pinned_registry`). No
production code reads that field — `freeze_eu_campaign_cell_spec.py` gates on the **per-fold** `status`
— but leaving it saying `PARTIALLY_PINNED` would have shipped a boundary artefact contradicting itself.

## 4. D-EU-19 — the one exception that was not pre-authorised

`it` 2014 is the only fold-year in the arc that D-EU-18's pre-authorisation **refused**.

- Offending months: **February** (52.1987 vs 59.6200 kWh/m², −7.4213, 12.4477 %) and
  **October** (82.9330 vs 100.2900 kWh/m², **−17.3570**, **17.3068 %**).
- Bounds cleared: 5 of 7 — gates 1–4+6 all PASS · 2 offending months (≤ 2) · relative Δ 17.31 % (≤ 20 %) ·
  annual Δ **2.5527 %** (≤ 5 %) · provenance written.
- Bounds breached: **2 of 7** — October's benchmark **100.29 kWh/m² is not below the 80 kWh/m²
  low-irradiance ceiling**, and its **17.357 kWh/m² gap exceeds the 15 kWh/m² ceiling**.
- Escalated as its own decision request, **not absorbed as judgement**, exactly as D-EU-18 requires.
  Ruled **2026-08-27, option (a)** by *Project Lead / Evaluator*:
  `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_EU-19_it_gate5_october_2026-08-27.md`.

**Two facts travel with that grant, permanently:**

1. October 2014's **17.357 kWh/m² is the largest single-month gap accepted anywhere in this arc**
   (previous maximum 8.93 kWh/m², `es` 2010).
2. It is the **first accepted month that is not a winter month**, and the same October deficit appears
   in `it` 2013 (−7.89 kWh/m², 11.05 %) — so it is **systematic, not an isolated year**.

> **Carried caveat (C-22 amendment, and the wording ruled at D-EU-19):** `it` (Bologna) carries a
> documented gate-5 exception on February and **October** 2014. October GHI is 17.36 kWh/m² (17.31 %)
> below the PVGIS benchmark, the largest single-month exception granted in this arc, and the same
> deficit appears in 2013. **No Bologna result may be quoted at monthly or seasonal resolution for
> August–November without restating this.** Annual GHI is within 2.55 %.

Direction of the error: the EPW is **darker** than the benchmark, so modelled October solar gains are
low and shoulder-season heating demand is biased **slightly high**.

A physical cause is plausible — a persistent negative ERA5 GHI bias over the Po Valley in the autumn
stratus/fog season — but **this arc did not measure that**, and it is recorded here as hypothesis, never
as finding. What is measured is the pattern: same month, same sign, both years.

The `it` 2013 EPW was converted and gated (`DEU18_REFUSED it 2013`, offending months 1, 9, 10) and is
**consumed by no campaign cell**: D-EU-16 pinned the `it` diary year to 2014, and the promotion path
promotes the ruled year alone. Its refusal line is diagnostic output, never a stop condition.

## 5. D-EU-14 is satisfied, not overridden

§12.14 ruled option **(b)**: stay at `DRAFT_WEATHER_NOT_PINNED` until GSSCanada answers the diary-year
question, so that a **single executable `v1.0`** could be signed the moment the years were ruled, with
no further weather computation. That condition is now met — D-EU-16 ruled all three diary years, and the
freeze consumed gate verdicts that already existed. The DRAFT never became a partial freeze:
`FROZEN_PARTIAL_WEATHER`, `--carry-unpinned` and the `carried_folds` header block were **not built**,
as that ruling directed, and `--allow-unpinned` is exactly as narrow as it was. **The freeze was run
without it.**

## 6. What OpenUBEM delivers

| Capability | Evidence |
|---|---|
| 102-record TABULA registry, three stocks | `openubem/data/construction/tabula_archetypes_{es,gb,it}.json` |
| 510-cell campaign specification | `openubem/data/campaign/eu_campaign_cell_spec_v1.0.json` |
| Caveat register, 22 entries, embedded verbatim | `openubem/data/campaign/eu_boundary_caveats_v1.0.json`; MVP Table 26 |
| ERA5 → EPW conversion, nine variables, 25 month-archives per fold | `scripts/convert_era5_eu_folds_to_epw.py`; `openubem/data/weather/raw/` |
| DR08 six-gate weather validation | `openubem/acquisition/european_weather.py`; `openubem/outputs/eu_evidence/EU-07/t06_*_six_gates.json` |
| Weather promotion decision, registry-writing | `scripts/run_eu_t06_weather_promotion.py`; `openubem/data/weather/weather_registry.json` |
| End-to-end physics proof on real buildings | `openubem/outputs/eu_evidence/EU-04/s2_campaign_v3/` |
| Gate scoring, three-way and honest | `openubem/outputs/eu_evidence/EU-09/` |

## 7. The one real end-to-end proof

**FR-LYO-HAUTCOEURPENTES, Lyon 2023, `f = 0`, n = 31 buildings.** 31/31 EnergyPlus returns 0;
**0 severe, 0 fatal**. Area-pooled heating EUI **60.7087 kWh/m²** over 19,823.6173 m², after two
repairs — the 10.0 m³ zone-volume substitution (C-20) and the reversed floor winding (C-21).
**31.2144 and 68.8114 kWh/m² are both WITHDRAWN** and preserved as superseded.

S2 gate conformance: **3 PASS / 0 FAIL / 14 VACUOUS**. G8.15 is green and was **earned** — the
untriaged warning kind disappeared because the geometry defect behind it was fixed, not because a
warning was approved into a list.

**This proof shares no fold, no building and no weather file with the 510 cells** (C-19). It shows the
pipeline runs end to end; the specification fixes the boundary Step 8 consumes. They answer different
questions, and neither substitutes for the other.

## 8. What is explicitly NOT delivered

Per `MVP_european_locations.md` §9.4, these are **GSSCanada-owned**, and nothing in this contract
supplies them:

- the **execution** of the 510 campaign cells — **0 of 510 have been simulated**;
- held-out LOCO fold selection and Step 7 schedule provenance;
- diary chaining and household sampling rules;
- run ordering across the five-level `f` matrix;
- Step 8 `manifest.json`, gate scoring, mutation probes and scientific reporting.

The contract says what Step 8 **may** run. It does not say that anything was run.

## 9. Carried caveats — the honest half of the deliverable

All 22 travel inside the artefact. The ones a receiving reader must not miss:

| Caveat | What it denies |
|---|---|
| C-03 | 26 of 31 evidence results are geometry-limited; only 5 emitted a real dwelling layout |
| C-08 | G8.15's original FAIL was genuine; no `approved_warning_kinds` list was ever ruled |
| C-09 | 14 of 17 gates are **VACUOUS** — vacuous is not a soft pass |
| C-16 | **Resolved at this freeze: 0 folds left unpinned.** Retained because the rule it states is what held |
| C-17 | The diary year is an owner ruling (D-EU-16), never a code default — **amended; its "None / RULED_NOT_PINNED" claim is superseded** |
| C-19 | The evidence bundle and this specification share no fold — **amended: 510 of 510 now carry a pinned weather file, 0 of 510 are simulated** |
| C-20 | Every simulated zone once ran at 10.0 m³; a warning kind may be counted but must be read |
| C-21 | Vertex order alone is worth **11.8 %** of heating; no area- or volume-based check can detect it |
| C-22 | Gate-5 exceptions are named and excepted, **not clean passes**; the 10 % tolerance was never widened — **amended with the D-EU-19 refusal-and-individual-ruling record** |

Four caveats were amended at this signature — **C-16, C-17, C-19, C-22** — under the register's own
rule: *a caveat may be added at CP-C; none may be removed*, and a caveat whose figures are superseded is
**restated in place, never rewritten silently**. The register still holds exactly **22** entries.

## 10. Findings carried into closure

| Finding | Substance |
|---|---|
| **EU-S2-06** | DR08 gate 5 is a **relative** test at a fixed 10 %, so ERA5's cloud bias against PVGIS bites hardest where absolute irradiance is smallest. Four of four folds failed it on at least one month |
| **EU-S2-08** | Vertex order alone is worth 11.8 % of heating demand |
| **EU-S2-09** | Tests coupled to a mutable ruled data file break every time a fold is promoted |
| **EU-S2-10** | An excepted status must be visible in the artefact the consumer actually reads, not only in the evidence behind it |
| **EU-S2-11** | A `licence_status: CAPTURED_AT_DOWNLOAD` that names its own source is not evidence the licence was granted — open the file it points at |

## 11. Licence provenance

All four folds carry the CDS `cc-by revision 1 (CC-BY-4.0)` licence text captured **verbatim at
download** in `openubem/outputs/eu_evidence/EU-07/cds_licence_text_at_download_2026-08-26.txt`,
LF-normalised SHA-256 `57ab1c144fa26cf6480d18a7d847d380dfdda7783a9e4a6b8bac14e48d822191` —
**re-verified at this signature**, not copied forward. `it`'s licence fields were filled from that file
at promotion; before that they were `null` / `CAPTURE_AT_DOWNLOAD`. The earlier
`cds_era5_licence_gate_2026-08-25.txt` pointer is **not** the licence: it records an HTTP 403 licence
refusal (EU-S2-11).

## 12. Test suite at signature, and the two changes the signature forced

`pytest -q tests/` → **2,245 passed / 55 skipped / 0 failed**, exit 0, 25 min 20 s (2026-08-27).
This matches the pre-closure baseline exactly — **the arc closed without moving the suite.**

The first full run at closure was **2 failed / 2,243 passed / 55 skipped**. Both failures were caused by
the closure itself, and both were fixed rather than tolerated:

1. **A defect introduced by this closure, caught by the repo's own guard.** The C-19 and C-22 amendments
   were written with embedded newlines, which `json.dumps(..., ensure_ascii=True)` renders as `\n` —
   and `test_serialised_spec_carries_no_absolute_or_windows_path` forbids **any** backslash in the
   serialised spec, because a backslash is how a Windows path would leak in. The guard fired on prose,
   not on a path, and it was right to: the caveat text is whitespace-normalised and the spec re-frozen.
   **The signature was not taken over a red suite.**
2. **FINDING EU-S2-09, fourth recurrence.** Two tests asserted literal values against the **live mutable**
   registry, and both became false the moment the last fold pinned:
   `test_allow_unpinned_writes_draft_with_510_cells` assumed some fold was still unpinned, and
   `test_committed_registry_preserves_template_targets_and_records_lyon_promotion` pinned the literal
   string `PARTIALLY_PINNED`. Both were **decoupled, never softened**: the first now drives `main`
   against a synthetic registry with one `RULED_NOT_PINNED` fold, and the second asserts the **invariant**
   that the top-level label must agree with the per-fold statuses it summarises — which is *stricter*
   than the literal it replaced, since it also fails on a stale label.

Files changed: `tests/test_eu_campaign_cell_spec_freeze.py`, `tests/test_eu_weather_registry.py`. No
production code was changed at the signature.

## 13. Signature

The contract was frozen, independently re-verified against the artefacts named in §2, and is
**immutable**. Any change produces a `v1.1`; it does not amend this file.

- **Verified by:** OpenUBEM director session, 2026-08-27
- **Ruling authority for D-EU-19:** Project Lead / Evaluator, 2026-08-27
- **§9.4 status: CLOSED — SIGNED**
