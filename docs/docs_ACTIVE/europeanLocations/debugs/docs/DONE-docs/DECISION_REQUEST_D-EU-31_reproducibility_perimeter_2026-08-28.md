# DECISION REQUEST `D-EU-31` — what the certified 149 may still be used for

**Raised:** 2026-08-28. **Work package:** `EU-09` / `EU-10`. **Status:** RULED (Option A selected).
**Supersedes nothing. Changes no number until ruled.**
**Source:** GSSCanada 4J, `4J_docs_occ/messages_OpenUBEM/2026-08-28_4J_to_OpenUBEM_FINDING181_arms_1_2_3_results.md`.

This request **groups the three questions 4J put to us in one ruling**, because they share one cause and
answering them separately would ask the owner to re-load the same evidence three times.

---

## 0. Why this is being raised

`D-EU-28` selected the quotable perimeter of **149 cells** by a conjunction that includes *three
bitwise-identical `heating_kwh` across three replicates*. 4J has now run the **same 149 cells ten times**
(arm 3, a control we did not ask for) and the criterion does not mean what it appeared to mean:

- **53 of 149 (35.6 %)** produce more than one distinct `heating_kwh` over ten replicates — `it` 30/74
  (40.5 %), `uk` 23/75 (30.7 %).
- The per-cell probability that three independent draws land on one value has **mean 0.859, median 1.000,
  and 13 cells below 0.5**. Those 13 would fail the certification test more often than they pass it.
- **78 of the 149 failed to `complete` in at least one of the ten re-runs.**

So the 149 were not selected purely for being reproducible; they were selected partly by **which cells got
lucky in three draws**. The certified set is still decisively better than the known-bad 90 (whose same
statistic is mean 0.390 / median 0.173, 53 of 90 below 0.5) — it is *better*, not *clean*.

**Nothing has been changed by 4J and nothing is being changed here.** `eu_certified_rerun_2026-08-28/` is
untouched, no gate was re-scored, no published figure has moved.

---

## 1. The measured facts behind it

| Finding | Statement |
|---|---|
| **190** | **Divergence is NOT worker contention.** Power-matched (arm 1's first three replicates vs arm 2's three): pooled 52/85 (61.2 %) at `--workers 14` vs 47/83 (56.6 %) at `--workers 1`. **`uk` is identical serially — 1/11 vs 1/10.** Set overlap 37 both / 15 parallel-only / **10 serial-only**, so it is not even nested. Worker count moves the *rate*, not the *phenomenon*. |
| **188** | **`completed` is a random variable, not a cell attribute.** Same cell, same IDF, same weather, same binary: completes in some replicates, `ENGINE_FAILED` in others. Arm 1: 64 of 90 inconsistent. Arm 3: **78 of 149 inconsistent**, per-replicate `engine_failed` 8–18 with no trend. |
| **189** | **Not bistability — a continuum.** Distinct `heating_kwh` per cell over ten replicates: arm 1 up to **8 states** (52 of 90 show ≥ 3); arm 3 up to 4. Worst: `es …MFH.06…f015` **79.11 %** over 8 states; `it …MidClim.TH.07…f015` 35.16 % over 4. A three-replicate comparison samples this distribution at low resolution **and with bias**. |
| **191** | The arm-3 control above — the certification criterion is luck-driven. Worst inside the certified set: `uk …AB.04…f050` **79.14 %**, `uk …AB.03…f015` 73.67 %, `uk …AB.03…f000` 73.64 %. |
| **192** | **The fold aggregate survives.** Basis = cells complete in all ten replicates (**71 of 149**; `it` 35, `uk` 36), like-for-like sums: **`it` spread 0.157 %** across ten independent re-runs of the whole set (per-`f`: 0.435 / 0.216 / 0.594 / 0.052 / 0.558 %). `uk` spread **11.498 %**, driven by `uk\|f000` at 58.54 %. Every one of the ten sums was distinct → the aggregate is **numerically stable, NOT bitwise reproducible**. |
| **186 AMENDED** | 4J's own correction. The `it` odds ratio **4.12 must no longer be quoted** — it was measured on 3-replicate labels, where a cell is only labelled divergent if divergence is *frequent*, so part of it was a detection-power artefact. At ten replicates: arm 1 `it` fvf=True 92.1 % vs False 84.6 %; arm 3 48.6 % vs 33.3 %. **The conclusion stands — associated, neither necessary nor sufficient — the effect size does not.** `uk` still diverges 23/75 with the kind never appearing. |

⚠ **One caveat the owner must see before ruling:** `FINDING 192`'s `it` tolerance of ±0.157 % is measured
over **35 `it` cells**, not the **74** that carry the published **108.25 kWh/m²**. It is the best available
estimate of re-run tolerance, not a re-measurement of the published figure.

⚪ `FINDING 181` stays **OPEN** — contention is now excluded, but the mechanism is still unidentified, and
the phenomenon is now known to reach **inside** the certified perimeter.

---

## 2. What is being asked — three questions, one ruling

### Q1 — May the 149 still be used at **cell level**?
`FINDING 191` says a cell-level number from the 149 carries an unstated re-run risk of up to 79 %.

### Q2 — Do we adopt `FINDING 192` as the mitigation?
4J recommends: restrict the 149 to **fold-level aggregate** use, quote the `it` figure with a stated
re-run tolerance of about **±0.16 %**, and drop cell-level claims. This preserves everything `EU-10`
currently reports at fold level.

### Q3 — What happens to `G8.1`–`G8.4`, the bitwise-reproducibility tripwires?
`FINDINGS 188`–`191` say a single-replicate bitwise comparison **cannot pass reliably on any cell** of this
engine. The gates are ours; 4J has touched nothing.

---

## 3. Options

**Option A — RECOMMENDED. Adopt the mitigation, in full, without re-ruling the perimeter.**
- The 149 stays the **level** perimeter and 92 the **difference** perimeter — `D-EU-28` and `D-EU-30` are
  **not reopened**.
- **Cell-level use of the 149 is BARRED.** No individual cell's `heating_kwh` may be quoted, ranked,
  tabulated or used as an example. The published `it` **cell range 45.08–156.70** falls under this bar and
  must be withdrawn from the quotable set.
- The `it` fold figure **108.25 kWh/m²** is retained and must from now on be written **with a stated
  re-run tolerance of ±0.16 %**, itself stated as measured on 35 of the 74 cells.
- `G8.1`–`G8.4` are recorded **NOT SCOREABLE on this engine** — carried with that reason, exactly as
  `G8.0` is carried as FAIL. **They must never be reported as PASS.**
- `FINDING 186`'s odds ratio 4.12 is **struck**; the qualitative conclusion is kept.
- Cost: **zero compute.** `EU-10`'s fold-level reporting is unaffected.

**Option B — Adopt Q2 but re-rule the perimeter.** As A, plus re-derive certification from ten replicates,
which would shrink 149 to the 96 single-valued cells. Cost: a full re-scoring, and it discards the `uk`
side of `EU-09` entirely. **Not recommended** — it spends the arc's remaining capacity to sharpen a
perimeter that Option A already forbids using at cell level.

**Option C — Change nothing, record the findings only.** Leaves the cell range quotable at a measured
risk of up to 79 %. **Not recommended.**

---

## 4. What must be written if Option A is ruled

1. `STATE v2` §1 gains a bar: *cell-level use of the 149 is barred*; the `it` cell range is struck from
   the row that carries it.
2. `STATE v2` §1 `it` row becomes **108.25 kWh/m² ± 0.16 % re-run tolerance (measured on 35 of 74)**.
3. `STATE v2` §3 records `FINDINGS 188, 189, 190, 191, 192` and the `186` amendment; `FINDING 181` stays
   OPEN with contention excluded.
4. `G8.1`–`G8.4` recorded NOT SCOREABLE with reason; `EU-09` gate tally restated.
5. Progress log row; director prompt SEC block.
6. **No file under `openubem/` is touched and no gate is re-run.**

---

## 5. Evidence

- 4J letter: `4J_docs_occ/messages_OpenUBEM/2026-08-28_4J_to_OpenUBEM_FINDING181_arms_1_2_3_results.md`
- 4J scratchpad: `f181_arms12.json`, `f181_matched.json`, `f181_arm3.json`, `f181_aggregate.json`; the
  thirty `campaign_summary.json` under `_local_runs/4J_f181_arm{1,2,3}_rep*`
- Host `tabletop1`, EnergyPlus `23.1.0-87ed9199d4` Windows. **Single-host diagnostic — these arms predate
  the `platform` manifest field, so none of their manifests carries one, and this is not a certifiable
  two-host result.**
- This side: `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v2.md` §1, §3.

---

## 6. Ruling

**Option selected:** **Option A — Adopt the mitigation, in full, without re-ruling the perimeter.**

**Ruled by:** Project Lead / Evaluator (AUTHOR / O.I.)  **Date:** 2026-08-28

**Notes:** Option A approved. The 149 level perimeter and 92 difference perimeter are retained without compute re-run. Cell-level publication and ranking of individual cell heating values are strictly barred (the previous cell range 45.08–156.70 is withdrawn). The Italian fold aggregate (108.25 kWh/m²) is retained with an explicit stated re-run tolerance of ±0.16% (measured on 35 of 74 cells). Gates G8.1–G8.4 are formally recorded as NOT SCOREABLE on this engine. FINDING 186's odds ratio 4.12 is struck while retaining the qualitative association.
