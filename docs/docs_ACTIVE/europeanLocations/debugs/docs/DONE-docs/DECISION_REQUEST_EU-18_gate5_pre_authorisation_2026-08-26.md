# DECISION REQUEST D-EU-18 — pre-authorise gate 5's winter exception for `uk` and `it`, or rule each one after the fact

- **Date:** 2026-08-26
- **Arc:** European locations × Step 8 boundary closure
- **Record:** `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12.15, §12.22
- **Finding:** **EU-S2-06** (already open)
- **Blocks:** promotion of `uk` and `it` to `RULED_PINNED` — and therefore the frozen executable `v1.0`
- **Follows:** D-EU-15, ruled (a) for `es` 2009 month 12 and `es` 2010 month 1
- **Precedent:** D-EU-07 (`fr` 2023, November, 13.82 %, approved as documented exception G5-A)
- **Asked now, deliberately.** The data does not exist yet — London is 23/25 archives, Bologna 0/25.
  That is precisely why this question is askable today: a bound set **before** the numbers arrive is a
  pre-registration; the same bound set afterwards is not.

---

## 1. The one-sentence version

Gate 5 has now failed on one winter month in **every** fold-year ever gated — `fr` 2023, `es` 2009,
`es` 2010 — and each failure needed its own ruling from you. `uk` and `it` will produce up to four more.
Do you want to set the acceptance conditions **now, sight-unseen**, or keep ruling each one after seeing it?

## 2. What is not in question

The 10 % relative tolerance is ruled and is **not** being changed by either option. Neither option
approves a fold-year that fails gates 1–4 or 6. Neither option lets this project widen a gate after
seeing its result — option (b) in D-EU-15, which would have done exactly that, was not taken and is not
re-offered here.

## 3. Why it recurs — the mechanism, restated

Gate 5 is a **relative** test at a fixed tolerance. December in Madrid carries 53.69 kWh/m²; July carries
250.18. The same 6.46 kWh/m² disagreement is **12 %** in December and **2.6 %** in July. The tolerance is
therefore harshest exactly where the absolute stakes are lowest, and ERA5's known winter cloud bias
against PVGIS SARAH is close to guaranteed to trip it in a low-irradiance month.

| Fold-year | Offending month | Δ that month | Absolute gap | **Annual Δ** | Ruling |
|---|---|---|---|---|---|
| `fr` 2023 | November | 13.82 % | 5.90 kWh/m² | 3.23 % | D-EU-07, approved |
| `es` 2009 | December | 12.04 % | 6.46 kWh/m² | **0.22 %** | D-EU-15 (a), approved |
| `es` 2010 | January | 14.13 % | 8.93 kWh/m² | 2.55 % | D-EU-15 (a), approved |
| `uk` 2014 | not yet gated | — | — | — | **this request** |
| `uk` 2015 | not yet gated | — | — | — | **this request** |
| `it` 2013 | not yet gated | — | — | — | **this request** |
| `it` 2014 | not yet gated | — | — | — | **this request** |

London sits further north and darker than Madrid, so its winter months carry less irradiance still and
the relative test will bite at least as hard. Bologna sits between the two.

## 4. Options

### (a) Pre-authorise under bounds fixed today — **RECOMMENDED**

`PASS_WITH_DOCUMENTED_EXCEPTION` may be granted to a `uk` or `it` fold-year **without returning to you**,
if and only if **every one** of these holds:

1. Gates **1, 2, 3, 4 and 6 all PASS** for that fold-year.
2. **At most 2** offending months in that fold-year.
3. Every offending month is a **low-irradiance month** — benchmark total **< 80 kWh/m²**.
4. Every offending month's relative Δ is **≤ 20 %**.
5. Every offending month's absolute gap is **≤ 15 kWh/m²**.
6. The **annual** Δ against the benchmark is **≤ 5 %**.
7. The written `approved_exception_months` list equals the offending list **exactly**, and each entry is
   recorded in `weather_registry.json` with its measured Δ, absolute gap and the annual Δ.

**If any single bound is breached, nothing is granted and the fold-year comes back to you as its own
decision request.** The bounds are chosen so that all three already-approved fold-years clear them
comfortably (worst observed: 1 month, 14.13 %, 8.93 kWh/m², annual 3.23 %) while leaving no room for a
genuinely bad file to slip through — a systematically wrong EPW fails on annual total, on month count,
or on a summer month, and each of those is a hard stop.

- **Removes up to four future rulings.**
- **Pre-registered:** the numbers do not exist yet, so no bound here can have been reverse-fitted.
- Cost: you are granting conditional approval to files you have not seen. Mitigated by bound 7 — every
  granted exception is recorded with its measurement and is auditable after the fact.

### (b) Keep ruling each fold-year individually, as D-EU-15 did

Every fold-year that fails gate 5 comes back as its own decision request with its twelve monthly rows.

- Every approval is made on the evidence in front of you.
- Cost: up to four more rulings, each one blocking the freeze until it is answered, and each one asking
  you the same question with different digits. On the evidence so far the answer has been "approved"
  three times out of three.

## 5. Recommendation — (a)

The pattern is now three-for-three across three independent fold-years and two countries, the mechanism
is understood and named, and the bounds can be fixed before the data lands. Option (b) is not more
rigorous than (a) — it is the same judgement, made four more times, later, and under freeze pressure.

## 6. Ruling

**Answer:** **(a) Pre-authorise under bounds fixed today** ☒   **(b) Individual rulings** ☐

**RULING:** Option (a) approved. Pre-authorisation for `PASS_WITH_DOCUMENTED_EXCEPTION` is granted for `uk` (2014, 2015) and `it` (2013, 2014) candidate fold-years under the seven strict pre-registered bounds defined in §4. Any fold-year meeting all seven criteria may be autonomously promoted to `RULED_PINNED` with complete provenance recorded in `weather_registry.json`; any fold-year that breaches any single bound must be escalated as an individual decision request.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-26


