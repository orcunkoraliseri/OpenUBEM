# `S2` acceptance declaration — promotion rule met

**Work package:** `EU-04` (dwelling/core layout adapter)
**Ladder stage:** `S2` — 31 observed buildings (`D-EU-04-S2-C` C1A), MVP Table 10
**Promotion rule, verbatim:** *"Stable outputs and measured resources"*
**Authority:** ruling `D-EU-20`, Option A, step 1
(`debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-20_resume_order_2026-08-27.md`)
**Date:** 2026-08-27
**Verdict:** ✅ **MET**

> **No simulation was run to produce this document.** The ruling forbids it. Every number below is
> read off artefacts that already existed on disk before the ruling was taken.

---

## 1. Authoritative bundle

`openubem/outputs/eu_evidence/EU-04/s2_campaign_v3_manifest.csv` and
`openubem/outputs/eu_evidence/EU-04/s2_campaign_v3/` (31 per-building run directories).

`s2_campaign_manifest.csv` (31.2144 kWh/m²) and `s2_campaign_v2_manifest.csv` (68.8114 kWh/m²) are
**withdrawn and retained untouched** as the audit trail. They are not the acceptance basis and must
never be quoted.

---

## 2. Half one — "stable outputs"

| Measure | Value | Read from |
|---|---:|---|
| Buildings in the frozen sample | **31** | `s2_campaign_v3_manifest.csv` |
| EnergyPlus return code `0` | **31 of 31** | `eplus_return_code` |
| Severe errors, summed over the sample | **0** | `severe_errors` |
| Fatal errors, summed over the sample | **0** | `fatal_errors` |
| Distinct `idf_sha256` values | **31 of 31** | no building reused another's IDF |
| Distinct `weather_sha256` values | **1** (`2cf15311b9c6…`) | one pinned EPW for the whole sample |
| That EPW resolves in the pinned registry | **yes** | `openubem/data/weather/weather_registry.json` |

**Hard-gate scoring on this bundle** (`openubem/outputs/eu_evidence/EU-09/s2_gate_report_v3.json`,
`severity: hard`, `n_cells_scored: 31`): **3 PASS / 0 FAIL / 14 VACUOUS** of 17.
PASS = `G8.12`, `G8.13` (103 dwelling/zone gain schedules audited across 31 buildings) and `G8.15`
(31 of 31 scored, 0 with severe or fatal). **Zero FAIL.** Every one of the 14 `VACUOUS` results names
the empty population that caused it — chiefly that all 31 cells are `f=0`, so every by-`f` comparison
has nothing to compare.

**The strongest stability evidence is the denominator.** Across three runs that moved heating demand
by a factor of two, the modelled zone floor area did not move one digit:

| Run | Heating (kWh) | Floor area (m²) | Pooled EUI (kWh/m²) |
|---|---:|---:|---:|
| `s2_campaign` (withdrawn) | 618,782.3181 | **19,823.6173** | 31.2144 |
| `s2_campaign_v2` (withdrawn) | 1,364,091.4373 | **19,823.6173** | 68.8114 |
| **`s2_campaign_v3` (authoritative)** | **1,203,465.4667** | **19,823.6173** | **60.7087** |

That invariance is the independent proof that the floor area was always sound and only the third
dimension was not — the defect chain `EU-S2-07` (zone volume substituted with 10 m³, ventilation loss
understated 57.74×) and `EU-S2-08` (vertex order alone worth −11.8 % of heating).

**Sample composition, unchanged from the frozen selection:** `SFH` 7, `TH` 8, `MFH` 8, `AB` 8.
**Geometry outcome:** **5** `DWELLING_LAYOUT_EMITTED`, **26** `FALLBACK_PENDING_LAYOUT`.

**Restated EUI distribution on `v3`** — replaces the withdrawn run's 4.93 / 65.21 / 149.43:
**min 29.5663 · median 77.9634 · max 158.1046 kWh/m²**.

## 3. Half two — "measured resources"

| Measure | Value |
|---|---:|
| Total EnergyPlus wall-clock over the sample | **147.25 s** |
| Mean per building | **4.75 s** |
| Minimum / maximum per building | **1.41 s** / **53.08 s** |

The envelope is measured, not estimated, and the spread is a factor of **37.6** between the fastest
and slowest building — the number that must carry forward into any `S3` or `N1` resource projection,
because a mean alone would under-plan the tail by an order of magnitude.

---

## 4. Verdict

**`S2` is ACCEPTED.** Both halves of the promotion rule are satisfied on the authoritative bundle:
outputs are stable (31/31 clean returns, zero severe, zero fatal, zero failed hard gates, an
invariant denominator across three runs) and resources are measured (147.25 s total, with the tail
recorded rather than averaged away).

## 5. What this acceptance does **not** say

1. **It is not a fleet number, and 60.7087 kWh/m² is not comparable to the 153.8 kWh/m² baseline.**
   Heating only. Cooling, lighting and equipment were **never simulated** — that is not a measured
   zero — and no DHW reconstruction was layered on an incomplete base.
2. **26 of 31 buildings ran as massing boxes, not dwelling layouts** (`FALLBACK_PENDING_LAYOUT`).
   `EU-S2-01` measured the split as material: the 5 emitted layouts pool far above the 26 fallbacks.
   **`S2` therefore does not demonstrate the real-footprint dwelling path at scale** — that remains
   open work inside `EU-04`.
3. **Three PASS out of seventeen gates is not "the gates passed".** Fourteen are `VACUOUS` because
   `S2` is `f=0` only; they were scored honestly with their empty populations named, and a vacuous
   gate is an unanswered question, not a satisfied one.
4. **It does not promote `S3`.** `S3` is a different stage with a different promotion rule ("approved
   exclusions and measured resource envelope") and is **not started**.
5. **It does not close `EU-04`.** *(Superseded 2026-08-28: `D-EU-04-F` was re-ruled **F4** — `GEO-08` is no longer Grasshopper parity but an independent Python reference, and Grasshopper parity is recorded NOT TESTED. `EU-04` is still not closed; the open item is now `D-EU-25`.)* `GEO-08` Grasshopper parity stays deferred by `D-EU-04-F` until
   after `S1`–`S3`, and `EU-05`'s dwelling/core acceptance still rides on these samples.

## 6. Next, per `D-EU-20` step 2

`S3` must not be sampled or frozen until the French typology balance rule is ruled: `SFH` caps at
**7** buildings in the Lyon study area, so a typology-balanced 96-building `S3` cannot be formed as
specified. The decision request is
[`docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-21_s3_fr_balance_2026-08-27.md`](docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-21_s3_fr_balance_2026-08-27.md).

*Evidence: `openubem/outputs/eu_evidence/EU-04/s2_campaign_v3_manifest.csv`,
`openubem/outputs/eu_evidence/EU-09/s2_gate_report_v3.json`,
`openubem/data/weather/weather_registry.json`, MVP Table 10 (`MVP_european_locations.md:725-733`).*
