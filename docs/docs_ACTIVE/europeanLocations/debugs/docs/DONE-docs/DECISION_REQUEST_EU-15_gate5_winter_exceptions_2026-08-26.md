# DECISION REQUEST D-EU-15 — gate 5 fails one winter month per fold-year

- **Date:** 2026-08-26
- **Arc:** European locations × Step 8 boundary closure
- **Record:** `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12.15
- **Finding:** **EU-S2-06** (new)
- **Blocks:** promotion of any fold to `RULED_PINNED` — and therefore the executable `v1.0`
- **Follows:** D-EU-14, ruled (b) — this is the preparation D-EU-14 ordered, reporting its first result
- **Precedent:** D-EU-07 (Lyon, November 13.8 %, approved as a documented exception G5-A)

---

## 1. The one-sentence version

Madrid's weather passes five of six DR08 gates on **both** candidate years and fails gate 5 on **one
winter month each** — while agreeing with the independent benchmark to **0.22 %** over the whole of
2009. The same thing already happened to France and you approved it. The question is whether that
approval was a one-off or a rule.

## 2. What was run, and why now

D-EU-14 was ruled (b) with the instruction to gate both candidate years of every fold immediately.
Madrid was the only fold with all 25 ERA5 archives on disk, so it went first:

```
$ python scripts/run_eu_t06_weather_promotion.py --fold es --dry-run

EPW_SHA256 es 2009 88c6c26e1e8151f8be81df648e19ad32940ecdcbc1e1f4a910bde08028b4a631
EPW_SHA256 es 2010 d2563b7dfdd8a78716ce3611c4180bea4e4d217b3779d0f693c607390a17346d
STOP es YEAR_NOT_RULED_TWO_CANDIDATES
```

The `STOP` is correct and expected — it is FINDING EU-S2-03 refusing to choose a diary year. The
conversion is deterministic: both SHA-256s reproduced byte-identically on a second run.

| Gate | es 2009 | es 2010 |
|---|---|---|
| 1 header | PASS | PASS |
| 2 8760 continuity | PASS | PASS |
| 3 no missing mandatory fields | PASS | PASS |
| 4 physical and solar bounds | PASS | PASS |
| **5 monthly benchmark** | **FAIL** — month 12 | **FAIL** — month 1 |
| 6 EnergyPlus smoke | PASS | PASS |

## 3. The pattern — three fold-years, three winter months

| Fold-year | Offending month | Δ that month | Absolute gap | **Annual Δ** |
|---|---|---|---|---|
| `fr` 2023 | November | 13.82 % | 5.90 kWh/m² | 3.23 % |
| `es` 2009 | December | 12.04 % | 6.46 kWh/m² | **0.22 %** |
| `es` 2010 | January | 14.13 % | 8.93 kWh/m² | 2.55 % |

Three independent fold-years. Three winter months. Three absolute gaps of 6–9 kWh/m². Three annual
agreements inside 3.3 %. Madrid 2009 matches PVGIS to **0.22 % over the year** and still fails the gate.

### Madrid 2009, all twelve months

```
m01  epw  56.99   bench  53.01    7.50 %
m02  epw  90.11   bench  92.49    2.57 %
m03  epw 158.63   bench 150.03    5.73 %
m04  epw 180.40   bench 168.43    7.10 %
m05  epw 228.89   bench 226.90    0.88 %
m06  epw 226.35   bench 227.39    0.46 %
m07  epw 251.52   bench 250.18    0.53 %
m08  epw 214.14   bench 210.14    1.90 %
m09  epw 151.65   bench 160.68    5.62 %
m10  epw 123.67   bench 126.99    2.62 %
m11  epw  71.83   bench  77.55    7.37 %
m12  epw  47.23   bench  53.69   12.04 %   <-- FAIL
                        ANNUAL    0.22 %
```

## 4. Why the rule bites where it does

Gate 5 is a **relative** test at a fixed 10 %. December in Madrid carries 53.69 kWh/m²; July carries
250.18. The same 6.46 kWh/m² discrepancy is **12 %** in December and **2.6 %** in July.

The tolerance is therefore harshest exactly where the absolute stakes are lowest, and a
reanalysis-versus-satellite disagreement of a few kWh/m² — ERA5's known winter cloud bias against PVGIS
SARAH — is close to guaranteed to trip it. **This is not evidence that the Madrid EPW is bad.** The
annual totals say the opposite, and gates 1–4 and 6 all pass.

It is also not a reason for this project to change the rule on its own authority. The 10 % tolerance is
ruled, and no `approved_exception_months` list may be written without an owner ruling — that is what the
France precedent established.

## 5. Options

### (a) Approve per fold-year, as with France — **RECOMMENDED**

Grant `PASS_WITH_DOCUMENTED_EXCEPTION` for `es` 2009 month 12 and `es` 2010 month 1, exactly as G5-A was
granted for `fr` 2023 month 11: the approved month list must match the offending months **exactly**, and
each approval is recorded in the registry with its measured deviation.

- Consistent with the only precedent that exists.
- Each fold-year is judged on its own evidence; nothing is granted in advance.
- Cost: three separate rulings so far, and one more per fold-year still to be gated (uk 2014/2015,
  it 2013/2014) — up to four more.

### (b) Rule the winter-month behaviour once, as a standing exception

Define a standing rule — for example, *a month whose benchmark total is below 80 kWh/m² is tested at a
wider tolerance, or on absolute difference* — and re-derive every verdict under it.

- Removes four future rulings and states the physics honestly rather than case by case.
- Cost: it changes a **pre-registered gate** after seeing its results, which is exactly the move the
  arc's own discipline exists to prevent. The France verdict would also have to be restated under the
  new rule.

### (c) Reject the affected fold-years

Treat gate 5 as failed, leave `es` `RULED_NOT_PINNED`, and stop.

- Cost: Madrid has no third candidate year. This ends the ES fold, and by the same logic probably UK and
  IT, leaving the campaign with no pinned weather at all. The evidence does not support it — an annual
  agreement of 0.22 % is not a bad weather file.

## 6. Recommendation — (a)

(a) is the only option that neither changes a pre-registered gate after seeing its results nor discards
a weather file the evidence says is sound. It is also already the established practice: the France
exception was granted on a **worse** month (13.82 %) and a **worse** annual figure (3.23 %) than Madrid
2009 shows.

The cost of (a) is rulings, and that cost is bounded and known — at most four more, one per remaining
fold-year, each carrying its own measured numbers.

**One thing (a) changes regardless of the answer.** The France exception can no longer be described as a
one-off. It is the first observed instance of a systematic pattern, and any future statement that "the
weather passed six gates" must name which months were excepted, for which fold-year, under which ruling.
That is FINDING EU-S2-06 and it stands whichever option you choose.

## 7. Where to check this

| Path | What it shows |
|---|---|
| `openubem/outputs/eu_evidence/EU-07/t06_es_2009_six_gates.json` | The 2009 verdicts and the EPW SHA-256 |
| `openubem/outputs/eu_evidence/EU-07/t06_es_2010_six_gates.json` | The 2010 verdicts |
| `openubem/data/weather/benchmarks/es_2009_monthly_ghi_benchmark.json` | The reference values, with their PVGIS endpoint |
| `openubem/acquisition/european_weather.py` — `evaluate_monthly_benchmark_gate` | The 10 % relative rule and the exception mechanism |
| `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_EU-07_Lyon_gate5_GHI_2026-08-26.md` | The France precedent |
| `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12.15 | FINDING EU-S2-06 |

**Answer:** **(a) Approve per fold-year** ☒   **(b) Standing winter rule** ☐   **(c) Reject** ☐

**RULING:** Option (a) approved. Grant `PASS_WITH_DOCUMENTED_EXCEPTION` for `es` 2009 (month 12: 12.04 % deviation; annual agreement 0.22 %) and `es` 2010 (month 1: 14.13 % deviation; annual agreement 2.55 %). Record the exact approved exception months and measured deviations in the weather registry and promotion evidence per the established precedent.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-26

