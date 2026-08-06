# MEASUREMENT — OPEN-22: what the labelled-accuracy metric actually measures

> **Task:** N02, `PLAN_no-compute-queue.md` §6. **Measurement only — no remediation, no relabelling,
> no edits to fixture/tests/classifier.** Executed 2026-08-06.
> **Artifacts:** this doc + `openubem/outputs/comparisons/open22_fixture_rule_breakdown.csv` (50 rows).
> **Method:** `tests/test_building_classifier.py:1004` `_run_labelled_fixture()`, called **unmodified**,
> plus a scratchpad script (`.../scratchpad/open22_fixture_rule_breakdown.py`, not under `docs/` or
> `openubem/`) that calls the same public entry point, `BuildingClassifier().classify(...)`, with the
> same fixture-loading/reordering code copied verbatim from the helper, to retain the
> `archetype_source` / `archetype_confidence` columns that the helper drops before merging. The
> classifier and helper were not edited. Cross-checked below.

## 1. Reproduction of the three current numbers — **PASS**

Run via the unmodified `_run_labelled_fixture()`, exactly as M04 did (`PLAN_published-numbers.md` §8):

| Metric | Reproduced | Expected (§5.5) | Result |
|---|---|---|---|
| Coarse top-1 | 100.0% (50/50) | 100.0% | PASS |
| Fine top-1 | 88.0% (44/50) | 88.0% | PASS |
| Distinct `expected_archetype` values | 13 | 13 | PASS |

All three reproduce exactly. Per §5.5/plan rule, this authorises the split below.

**Cross-check (harness self-validation):** a second call through the same public `classify()` entry
point, retaining `archetype_source`/`archetype_confidence`, was merged against the same 50 osm_ids and
compared row-for-row against the unmodified helper's `archetype_id`. **0/50 mismatches** — the extended
read is not a diverging harness, it is the same deterministic classifier output with two more columns
kept.

⚠️ Not used: the stale Boston 41.0% / Chicago 65.4% figures from `INVESTIGATION_steps-1-3-audit.md:93`
(register §6: predate `E-R3-2`). Named here only as excluded.

## 2. Fine top-1 accuracy, all 50 rows

**44/50 = 88.0%** (matches §1, same computation, same denominator).

## 3. Fine top-1 accuracy, excluding `FALLBACK_SIZE_DEFAULT` rows

- Rows decided by `FALLBACK_SIZE_DEFAULT`: **n = 17** (excluded)
- Remaining rows: **n = 33**
- Fine top-1 over the 33: **29/33 = 87.9%**

So excluding the fallback-decided rows moves the fine accuracy from 88.0% (n=50) to 87.9% (n=33) — the
17 fallback rows contributed 15/17 correct (88.2%), close to the overall rate, not the accuracy driver
by itself. (Stated as counts per rule 9; not an interpretation of what it means for OPEN-22 — that is
the user's call per §5.4/task instructions.)

## 4. Per-rule-token row counts — all ten §5.3 vocabulary tokens

| Rule token | n rows |
|---|---|
| `RULE_HIGHRISE` | 5 |
| `RULE_RESIDENTIAL_TIER` | 2 |
| `RULE_LODGING_TIER` | 2 |
| `RULE_FUNCTION_TAG` | 4 |
| `RULE_FUNCTION_TAG_SIZE` | 0 |
| `RULE_USE_CLASS` | 1 |
| `RULE_USE_CLASS_SIZE` | 14 |
| `MIXED_USE_DOMINANT_TAG` | 0 |
| `FALLBACK_UNKNOWN` | 5 |
| `FALLBACK_SIZE_DEFAULT` | 17 |
| **Sum** | **50** |

Sum over the 10-vocab tokens = 50 = row count; no row fell outside this vocabulary at the head-token
position (checked against the classifier's full 16-token `_EMIT_TOKENS` set — every fired head token in
this fixture is one of the 10 named in plan §5.3; no composite/other heads appeared).

## 5. Confidence tier × match/mismatch

| Tier | Match | Mismatch | Tier total |
|---|---|---|---|
| HIGH | 7 | 1 | 8 |
| MEDIUM | 16 | 3 | 19 |
| LOW | 21 | 2 | 23 |
| **Total** | **44** | **6** | **50** |

## 6. Connected hypothesis (register §6, "a lead, not a finding") — reported, not interpreted

Of the 17 rows decided by `FALLBACK_SIZE_DEFAULT` (rule 17a is the same token — §5.4 confirms 17a's
emitted token *is* `FALLBACK_SIZE_DEFAULT`, `building_classifier.py:327-329`), the human answer key also
labelled **16 of 17** as one of the three office archetypes (`SmallOffice`/`MediumOffice`/`LargeOffice`).

**Two-guesses-agreeing count: 16 / 17 FALLBACK_SIZE_DEFAULT rows.** Reported only — no ruling made here.

## 7. Six fine-top-1 mismatches (for audit context, all rows outside the office-fallback-agreement set
except one)

| osm_id | expected | got | confidence | rule_token |
|---|---|---|---|---|
| 240540694 | MediumOffice | LargeOffice | LOW | FALLBACK_SIZE_DEFAULT |
| 405668717 | MidriseApartment | HighriseApartment | MEDIUM | RULE_RESIDENTIAL_TIER |
| 816270033 | RetailStandalone | SmallOffice | LOW | FALLBACK_SIZE_DEFAULT |
| 124865497 | SmallOffice | LargeOffice | MEDIUM | RULE_USE_CLASS_SIZE |
| 145080938 | OpenUBEMUnknown | Courthouse | HIGH | RULE_USE_CLASS |
| 210671718 | MediumOffice | LargeOffice | MEDIUM | RULE_USE_CLASS_SIZE |

## 8. Spot-check — 5 rows against the raw fixture CSV, verbatim

Raw fixture: `tests/fixtures/labelled_archetypes_50.csv`.

1. **osm_id 1280678588** — raw: `1280678588,boston_downtown_500m,yes,,2.0,,70.66438015793675,SmallOffice,commercial,tiny 70m2 x 2fl ~141m2 generic downtown -> small commercial default`. `building_tag=yes`, no function tag → `use_class=unknown` → rule 17a → `FALLBACK_SIZE_DEFAULT`, LOW. Classifier emitted `SmallOffice` / LOW / `FALLBACK_SIZE_DEFAULT` — matches expected `SmallOffice`. ✅.
2. **osm_id 241978446** — raw: `241978446,boston_downtown_500m,commercial,,13.0,44.196,1743.2221287307161,LargeOffice,commercial,commercial 13fl x 1743m2 = 22660m2 -> LargeOffice`. `building_tag=commercial` → `use_class=commercial` → `RULE_USE_CLASS_SIZE`, MEDIUM. Classifier emitted `LargeOffice` / MEDIUM / `RULE_USE_CLASS_SIZE` — matches. ✅.
3. **osm_id 405668798** — raw: `405668798,boston_downtown_500m,yes,,5.0,18.7,376.5953798782133,SmallOffice,commercial,5fl x 377m2 = 1883m2 < 2322 -> SmallOffice (E-R3-3 CBES bins)`. `building_tag=yes` → `FALLBACK_SIZE_DEFAULT`, LOW. Classifier emitted `SmallOffice` / LOW / `FALLBACK_SIZE_DEFAULT` — matches. ✅.
4. **osm_id 108240968** — raw: `108240968,chicago_loop_500m,public,government,12.0,,4362.2621189252795,Courthouse,commercial,public + government function tag direct match`. `function_tag=government` → `RULE_FUNCTION_TAG` (rule 7), HIGH. Classifier emitted `Courthouse` / HIGH / `RULE_FUNCTION_TAG` — matches. ✅.
5. **osm_id 73751952** — raw: `73751952,chicago_loop_500m,office,,27.0,,1682.4093698510314,TallBuilding,commercial,office 27fl >= 20 -> TallBuilding`. `levels=27 >= 20`, `use_class=commercial` (from `office` tag) → `RULE_HIGHRISE` (rule 1b), HIGH. Classifier emitted `TallBuilding` / HIGH / `RULE_HIGHRISE` — matches. ✅.

## 9. Fixture/test/classifier integrity check

```
git status --short tests/fixtures/labelled_archetypes_50.csv tests/test_building_classifier.py openubem/semantic/building_classifier.py
```
returned **empty, before and after the run** — no edits made to any of the three.

## 10. What this does and does not settle

This measurement produces the split the register asked for: **44/50 (88.0%) overall fine accuracy**
decomposes into **17 rows (34%) decided by the untagged-building-guesses-office fallback**, of which
**16 (94%) happen to agree with the human label**, alongside **29/33 (87.9%)** accuracy on the
non-fallback-decided rows. Whether that 16/17 agreement means the metric is inflated by the fallback
and answer key being tuned toward each other (§5.4's hypothesis), or whether it means the fallback is a
reasonable prior given this fixture's building mix, **is not decided here** — per task instructions,
that ruling belongs to the user.
