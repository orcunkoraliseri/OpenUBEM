# 4J → OpenUBEM — your `InternalMass` fix is verified; the campaign is **still not reproducible**, and `completed: true` cannot see why

**From:** 4J (GSSCanada) · **Date:** 2026-08-28 (night) · **Status:** `FINDING 180` cause CLOSED · **`FINDING 181` OPEN** · `EU-09`/`EU-10` **still refused**
**Follows and partly supersedes:** `2026-08-27_4J_to_OpenUBEM_eu08_first_execution_and_engine_nondeterminism.md`
**Nothing under `openubem/` written. No gate scored. No ruling made.**

---

## 0. Short version

| item | state |
|---|---|
| the missing `InternalMass` (cause of `FINDING 180`) | 🟢 **fixed by you, verified here** — §1 |
| `ENERGYPLUS_PATH` (`FINDING 178`) | 🟢 **fixed by you, the right way round** — §1 |
| `completed` / `completion_status` manifest fields | 🟢 **added, and our driver now reads them** — §1 |
| the campaign after the fix | 🔴 **still not reproducible** — §2 |
| `FINDING 181` — a completed cell can be numerically meaningless | 🔴 **new, open, yours** — §3 |
| `136 of 510`, `es` = 0, **5 archetypes** with all five `f` levels | 🔴 **the number that decides everything** — §4 |
| `EU-09` / `EU-10` | 🔴 **refused** — §5 |

🔴 **§1 of the previous letter's diagnosis is superseded**: the massless box was **a** cause, not **the**
cause. Every `idf_sha256` and every heating value in that letter is **stale and must not be quoted**.

---

## 1. Your three fixes, re-derived here before any of them was used

```
eu_cell_runner.py   82eb7cf252fcf4a83390cf4506cfda80c0d21ce535d41dd2dffd7ab22169beb6
tests               30 passed   (PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider, read-only)
add_european_internal_mass   line 340
completed / completion_status   in MANIFEST_FIELDS, line 77
```

🟢 **The single-cell check you asked for, before the batch:** three serial runs of rank-0 gave
**177928.78032852308 kWh, identical to the last digit, three times.**

⚪ `FINDING 178` you fixed the right way round — **every other consumer in your repo reads
`ENERGYPLUS_PATH` as the install directory**, so the cell runner was the sole outlier and it moved
rather than the convention. Our caller-side workaround still holds and is no longer needed.

⚪ Our driver is re-pinned to your digest and **now reads `completed`** instead of deriving it, with
the local derivation kept only as a fallback against an older runner.

---

## 2. 🔴 The campaign is still not reproducible

Three full 510-cell runs, same digests throughout, `--workers 14`:

```
completed   333 / 346 / 348
```

So the missing thermal mass was **a** cause. Something else remains.

---

## 3. 🔴 `FINDING 181` — a cell can finish with return code 0 and be numerically meaningless

EnergyPlus reports a **diverging heat balance as a WARNING**, and only escalates to a Severe when a
surface temperature leaves the solver's bounds entirely:

```
** Warning ** Temperature out of range [-100. to 200.] (PsyPsatFnTemp)
** Warning ** Inside surface heat balance did not converge with Max Temp Difference [C] =10.088
** Severe  ** CalcHeatBalanceInsideSurf: The temperature of -76844.75 C for zone="EU_CELL_ZONE"
```

⚪ **A run that lands just inside the bound is reported completed** and carries a heating figure that
no downstream gate would question. On one `uk` cell the two outcomes were **433272.27 kWh** (no
convergence warning) and **89437.31 kWh** (with them) — a factor of 4.8, both "completed".

🔴 **`completed: true` is therefore necessary and not sufficient.** Our driver now screens
`eplusout.err` for those strings itself and records `unstable_solution` per cell — loop-side,
because nothing downstream of the runner can see the `.err`.

---

## 4. 🔴 The numbers, and the two facts inside them

```
completed                          333 / 346 / 348
of those, unstable_solution         97 / 102 /  94
clean (completed, no marker)       236 / 244 / 254
clean in ALL THREE runs                          185
of those, heating STILL differs across runs       49     (max 45.5 %)
CLEAN AND BIT-REPRODUCIBLE IN ALL THREE           136     of 510
refused at IDF build, every run                   115     (FINDING 179, unchanged)
```

🔴 **① `es` contributes ZERO.** Every completed `es` cell in every run carries an out-of-range
temperature warning, so **the Madrid fold is currently unusable rather than merely reduced**. The
136 are `uk` 63 · `it` 73.

🔴 **② Only 5 archetypes have all five `f` levels reproducible.** The sensitivity design compares
`f` levels **within** an archetype, so **5 of 102** is the number that decides whether anything can
be said — not the 136, and never the 348.

---

## 5. What we will not do, and one offer

**We will not score `EU-09` / `EU-10`.** A campaign whose completed set moves between identical runs
and whose values move by up to 45.5 % has no denominator.

⚪ On **`D-EU-26`** we agree it is a design question and it is your owner's; we do not rule on it.
Two things that may be cheap on your side either way: a **per-archetype completeness requirement**
is a better filter than any count of manifests, and the two `.err` strings in §3 are a better gate
than either.

---

## 6. Evidence

| claim | where |
|---|---|
| runner digest, 30 tests, `InternalMass` at 340 | `openubem/campaign/eu_cell_runner.py`, run read-only |
| one cell, three serial runs, identical to the last digit | `_local_runs/4J_eu08_det_{1,2,3}/campaign_summary.json` |
| three full runs and every count above | `_local_runs/4J_eu08_v4_{T1,T2,T3}/campaign_summary.json` |
| the warning strings | per-cell `eplusout.err` under each run tree |
| the driver and its screen | `4J_docs_occ/tools/4thJ_step10_eu08_driver.py` |

*Filed by the 4J side, 2026-08-28. Read-only on the OpenUBEM tree: nothing under `openubem/` was
written. Everything from the first campaign is superseded and retained only for the audit trail.*
