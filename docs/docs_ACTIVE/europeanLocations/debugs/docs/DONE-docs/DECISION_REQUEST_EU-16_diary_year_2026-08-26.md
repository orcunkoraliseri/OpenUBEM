# DECISION REQUEST D-EU-16 — the diary year, with the fieldwork evidence you asked for

- **Date:** 2026-08-26
- **Arc:** European locations × Step 8 boundary closure
- **Record:** `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12.16
- **Follows:** closure question Q1, ruled option (b) — *derive the fieldwork windows first, then rule*
- **Blocks:** the signed `v1.0` — this is the last input the specification needs

---

## 1. The answer, in one table

| Fold | Survey | Fieldwork window | Months in yr 1 | Months in yr 2 | **Dominant year** |
|---|---|---|---|---|---|
| `es` | INE *Encuesta de Empleo del Tiempo* 2009-2010 | 2009-10 → 2010-09 | 3 | **9** | **2010** |
| `uk` | UKTUS 2014-2015 (UK Data Service study 8128) | 2014-04 → 2015-12 | 9 | **12** | **2015** |
| `it` | ISTAT *Indagine Uso del Tempo* 2013-2014 | 2013-11 → 2014-10 | 2 | **10** | **2014** |

**All three surveys put the majority of their fieldwork in the second calendar year.** Two of the three
put it almost entirely there: Spain collected 9 of 12 months in 2010, Italy 10 of 12 in 2014.

Sources: the INE operation *metodología* page; the UK Data Service documentation for study 8128; the
ISTAT *multiscopo — Uso del tempo* page.

## 2. Why this matters more than it looks

The obvious default — the **first** year of each window, the year the fold is named after — would have
been **wrong for every one of the three folds**.

The converter's first version defaulted to exactly that. Had the default survived, all three campaign
folds would have been simulated against weather from the wrong calendar year, and **nothing downstream
would have shown it**: the EPW would have been valid, the six gates would have passed, and the registry
would have said `RULED_PINNED`.

That is FINDING EU-S2-03, and this table is its vindication.

## 3. What is already in place

Madrid has been converted to **both** candidate years and gated on both. Conversion is deterministic —
the SHA-256s reproduce byte-identically across runs:

```
es 2009  88c6c26e1e8151f8be81df648e19ad32940ecdcbc1e1f4a910bde08028b4a631
es 2010  d2563b7dfdd8a78716ce3611c4180bea4e4d217b3779d0f693c607390a17346d
```

Both pass all six DR08 gates under the D-EU-15 winter exception. London and Bologna get the same
treatment as their archives land. **A ruling here costs no computation at all** — it selects an EPW that
already exists and already passed.

## 4. Options

**(a) Rule the dominant-fieldwork year — `es` 2010, `uk` 2015, `it` 2014.** **RECOMMENDED.**
Each fold is matched to the calendar year in which most of its occupancy diary was actually collected,
with the fieldwork window recorded in the registry beside it.

**(b) Rule the first year of each window — `es` 2009, `uk` 2014, `it` 2013.**
Simpler and matches the fold names, but the evidence above says it is the minority year in all three
cases, and the caveat register would have to say so.

**(c) Split by fold on some other basis** — for example the year containing the diary *midpoint*, which
gives the same answer as (a) for `es` and `it` and 2015 for `uk`. No practical difference here.

**Recommendation: (a).** It is the only option the fieldwork evidence supports, and it costs nothing to
apply.

## 5. What happens the moment this is ruled

1. `diary_window` and `diary_window_status` are written for the three folds.
2. `run_eu_t06_weather_promotion.py --all --commit` promotes each fold whose six gates pass.
3. `freeze_eu_campaign_cell_spec.py` stops refusing and writes `eu_campaign_cell_spec_v1.0.json`.
4. `CLOSURE_eu_boundary_contract_v1.0.md` is written and Table 26's signature row is filled.

Steps 2–4 are minutes of work. **Step 1 is the whole remaining decision.**

The only dependency left is the ERA5 acquisition for London and Bologna, which is running and cannot be
accelerated.

## 6. Where to check this

| Path | What it shows |
|---|---|
| `openubem/data/weather/weather_registry.json` | `diary_window: null`, `raw_era5_window` per fold |
| `openubem/outputs/eu_evidence/EU-07/t06_es_2009_six_gates.json` / `..._2010_...` | Both Madrid years, all six gates |
| `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12.16 | Table 29, the fieldwork derivation |

**Answer:** **(a) Dominant-fieldwork year** ☑   **(b) First year** ☐   **(c) Other** ☐

**RULING:** Option (a) approved. Rule the dominant-fieldwork calendar years for all three campaign folds: Spain (`es`) = 2010, United Kingdom (`uk`) = 2015, Italy (`it`) = 2014. Record fieldwork windows and justification in the weather registry (`weather_registry.json`), set `diary_window_status = RULED_PINNED` upon DR08 gate passage, and proceed with the promotion and contract freeze.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-26

