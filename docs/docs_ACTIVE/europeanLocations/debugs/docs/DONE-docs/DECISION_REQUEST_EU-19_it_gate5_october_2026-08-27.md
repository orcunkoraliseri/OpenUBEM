# DECISION REQUEST D-EU-19 — `it` 2014 fails gate 5 on October, outside D-EU-18's bounds

- **Date:** 2026-08-27
- **Arc:** European locations x Step 8 boundary closure
- **Record:** `docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md` §12.15, §12.22, §9.4
- **Finding:** **EU-S2-06** (gate-5 relative-tolerance mechanism, already open)
- **Blocks:** promotion of `it` to `RULED_PINNED_EXCEPTION` — and therefore the frozen executable `v1.0`
- **Follows:** D-EU-18, ruled (a); this is the first fold-year that D-EU-18 **refused**
- **Precedents:** D-EU-07 (`fr` 2023), D-EU-15 (`es` 2009, `es` 2010), D-EU-18 auto-grant (`uk` 2015)

---

## 1. The one-sentence version

Bologna's diary year converted cleanly and passes gates 1, 2, 3, 4 and 6, but gate 5 fails on
**October** — a month with real irradiance, not a winter month — and D-EU-18's pre-registered bounds
correctly refused to auto-approve it. The bounds did their job; the question is now yours.

## 2. What D-EU-18 refused, exactly

`it` 2014 breaches **two of the seven bounds**, both on the same single month:

| Bound | Limit | `it` 2014 | Verdict |
|---|---|---|---|
| 1. Gates 1,2,3,4,6 all PASS | — | all PASS | ✅ |
| 2. At most 2 offending months | ≤ 2 | 2 (Feb, Oct) | ✅ |
| 3. Every offending month low-irradiance | bench < 80 kWh/m² | **Oct = 100.29** | ❌ |
| 4. Every offending month relative Δ | ≤ 20 % | max 17.31 % | ✅ |
| 5. Every offending month absolute gap | ≤ 15 kWh/m² | **Oct = 17.357** | ❌ |
| 6. Annual Δ | ≤ 5 % | **2.55 %** | ✅ |
| 7. Recorded provenance | — | available | ✅ |

The two offending months:

| Month | EPW GHI | Benchmark GHI | Gap | Relative Δ | Clears D-EU-18? |
|---|---|---|---|---|---|
| February | 52.20 | 59.62 | −7.42 | 12.45 % | yes, on every bound |
| **October** | **82.93** | **100.29** | **−17.36** | **17.31 %** | no — bounds 3 and 5 |

Annual: EPW **1376.6** vs benchmark **1412.6** kWh/m² → **−2.55 %**.

## 3. What is *not* the blocker

`it` **2013** also fails gate 5 (offending months 1, 9, 10; annual −1.22 %). It is **not** load-bearing.
D-EU-16 pinned `it`'s diary year to **2014**, and `run_eu_t06_weather_promotion.py:246-256` promotes the
ruled diary year only — exactly as `es` pinned y2010 and `uk` pinned y2015. The 2013 EPW is a by-product
of the ERA5 window and is never consumed by a campaign cell. Its `DEU18_REFUSED` line is diagnostic
output, not a stop condition. **The whole decision is one month of one year.**

## 4. Why the bounds misfired here — the mechanism

D-EU-18 bound 3 (`< 80 kWh/m²`) and bound 5 (`≤ 15 kWh/m²`) are both **proxies for the same idea**: the
failure is a low-stakes winter artefact of a relative test, not a bad file. Every prior grant fitted that
shape — `fr` November, `es` December, `es` January, `uk` November + December.

Bologna's failure does not. It is **autumn**, and it is **systematic**: October is low in *both* years,
same sign, growing magnitude.

| Fold-year | Offending months | Character |
|---|---|---|
| `fr` 2023 | Nov | winter |
| `es` 2009 | Dec | winter |
| `es` 2010 | Jan | winter |
| `uk` 2015 | Nov, Dec | winter |
| **`it` 2013** | Jan, **Sep (−10.33 %)**, **Oct (−11.05 %)** | winter + **autumn** |
| **`it` 2014** | Feb, **Oct (−17.31 %)** | winter + **autumn** |

A persistent negative ERA5 GHI bias over the Po Valley in autumn is a plausible physical cause (low
stratus / fog season), but **this arc has not measured that** and it is offered as hypothesis, not
finding. What is measured is the pattern above.

## 5. What the disagreement is worth

- October carries **7.10 %** of Bologna's annual benchmark GHI (100.29 / 1412.6).
- The deficit is **1.23 %** of annual GHI (17.36 / 1412.6).
- Direction: EPW is **darker** than benchmark → modelled October solar gains low → shoulder-season
  heating demand biased **slightly high**.
- The annual figure, −2.55 %, is **mid-pack among grants already made**: `es` 2010 was 2.55 %,
  `fr` 2023 was 3.23 %, `uk` 2015 was **4.31 %** — all approved.
- The absolute gap, 17.36 kWh/m², is **larger than any granted before** (previous max: `es` 2010, 8.93).

Those last two lines are the whole tension: **by annual accuracy this file is better than one already
pinned; by single-month absolute gap it is the worst yet seen.**

## 6. Options

### (a) Grant the exception for `it` 2014, months [2, 10] — **RECOMMENDED**

Promote `it` to `RULED_PINNED_EXCEPTION` with `--approve-gate5-exception it:2014 2 10`, recording both
months, their measured Δ and gap, and the annual Δ in `weather_registry.json`.

- Gates 1, 2, 3, 4 and 6 all PASS — nothing suggests a malformed or mis-sited file.
- Bound 4 — the **relative** bound, the one that measures *severity of disagreement* rather than
  *stakes of the month* — is **not** breached (17.31 % against a 20 % ceiling).
- Annual Δ −2.55 % is better than two folds already pinned.
- Unblocks the freeze immediately: `510 510 22 FROZEN`.
- **Cost:** you are approving a larger absolute monthly gap than any precedent, on a month that is not
  low-stakes. This must be carried as a **stated caveat**, not silently absorbed — any Bologna result
  quoted at monthly or seasonal resolution in autumn inherits it.

### (b) Refuse `it`; freeze `v1.0` with `fr` + `es` + `uk` only

`it` stays `RULED_NOT_PINNED`; the spec freezes as `DRAFT_WEATHER_NOT_PINNED`, or a partial freeze is
taken under D-EU-14.

- No approval is made on a file whose autumn behaviour is not understood.
- **Cost:** `it` is **210 of 510 cells — the largest fold in the campaign**. The boundary contract ships
  covering 300 cells, and `v1.0` is not the thing that was scoped.

### (c) Re-benchmark October against a second source before ruling

Re-gate `it` 2014 against an independent monthly GHI source (CM SAF SARAH-3, or a Bologna ground
station) to establish whether PVGIS or ERA5 is the outlier.

- Would actually answer the physical question instead of ruling around it.
- **Cost:** new evidence work of unknown length, delays `v1.0` past this arc, and — stated plainly —
  it has the *shape* of shopping for a benchmark that passes. D-EU-15 option (b) was refused for
  precisely that shape. It is only defensible if the second source is chosen and pinned **before** it
  is run, and if its verdict is binding either way.

## 7. Recommendation — (a), with the caveat written into the closure

The file is annually sound, passes every structural and simulation gate, and its worst month sits inside
the severity bound D-EU-18 set for exactly this judgement. What it breaches are two bounds that encode
*"this month barely matters"* — and October at Bologna does matter somewhat, which is why the answer must
be a ruling and a recorded caveat rather than an automatic grant. That is D-EU-18 working, not failing.

If (a) is taken, the caveat to carry into `CLOSURE_eu_boundary_contract_v1.0.md` and MVP Table 26 is:

> `it` (Bologna) carries a documented gate-5 exception on February and **October** 2014. October GHI is
> 17.36 kWh/m² (17.31 %) below the PVGIS benchmark, the largest single-month exception granted in this
> arc, and the same deficit appears in 2013. **No Bologna result may be quoted at monthly or seasonal
> resolution for August–November without restating this.** Annual GHI is within 2.55 %.

## 8. What is ready the moment you rule

- 25/25 ERA5 archives on disk; both EPWs converted and hashed
  (`it` 2014 sha256 `ab631c6026e3f7cf5cfcff7c6a506eb84b6eeb62f1afa5703fc48ef0897e25fa`).
- `EU-07` licence text verified against its recorded LF-normalised sha256 `57ab1c14…`.
- Freeze runs **without** `--allow-unpinned`; independent verification expects `510 510 22 FROZEN`.
- Suite baseline to record at closure: **2,245 passed / 55 skipped**.

## 9. Ruling

**Answer:** **(a) Grant the exception for `it` 2014, months [2, 10]** ☒   **(b) Refuse `it`** ☐   **(c) Re-benchmark** ☐

**RULING:** Option (a) approved. Grant `PASS_WITH_DOCUMENTED_EXCEPTION` for `it` 2014 on months [2, 10] (February: $-12.45\,\%$, October: $-17.31\,\%$; annual concordance: $-2.55\,\%$). Promote `it` to `RULED_PINNED_EXCEPTION` with full provenance in `weather_registry.json`. Carry the documented autumn caveat into `CLOSURE_eu_boundary_contract_v1.0.md` and MVP Table 26, stating that October GHI is $17.36\text{ kWh/m}^2$ below PVGIS and that seasonal/monthly outputs for autumn must explicitly reference this deviation.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-27

