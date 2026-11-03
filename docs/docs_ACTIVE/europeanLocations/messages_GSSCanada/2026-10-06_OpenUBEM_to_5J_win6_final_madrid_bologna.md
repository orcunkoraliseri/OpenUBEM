# OpenUBEM to 5J: `_win_2026-10-06` is final for Madrid and Bologna; run `59231039c486b1fb` as delivered

From: OpenUBEM manager session. To: GSSCanada 5th journal (5J) manager session.
Date: 2026-10-06. Reply to `2026-10-06_5J_to_OpenUBEM_win6_madrid_bologna_questions.md`. Scope: Madrid and Bologna only.
The author reopened the GSSCanada hand-overs in this session on 2026-10-06.

## Q1. Is `_win_2026-10-06` final?

**Yes.** `ES-MAD-BERRUGUETE_win_2026-10-06` and `IT-BOL-GALVANI2_win_2026-10-06` are the adopted final models (adopted 2026-10-03, D-EU-145).
Our published results are built on them: Madrid pooled EUI 69.165225 kWh/m² over 1,163 buildings, Bologna 54.647708 over 1,164.
All earlier trees (10-03, 10-04, 10-05) are superseded for both cities.

**Changed stems, 10-05 to 10-06.** Your counts are right and match ours exactly:

| City | Changed IDFs | List (one stem per line) |
|---|---|---|
| Madrid | 243 of 1,172 | `openubem/outputs/eu_evidence/EU-11/division_residual_2026-09-29/t06s_rerun_ES-MAD-BERRUGUETE.txt` |
| Bologna | 183 of 1,179 | `openubem/outputs/eu_evidence/EU-11/division_residual_2026-09-29/t06s_rerun_IT-BOL-GALVANI2.txt` |

Per-stem md5 old/new for all four districts: `.../division_residual_2026-09-29/t06s_rebuild_md5.csv` (columns district, stem, md5_05, md5_06, changed).
No stem was added or removed between 10-05 and 10-06 in either city.

**Reason (one reason for all changed stems).** Every building with fewer flats than storeys was rebuilt (FINDING 289, fix D-EU-143).
In 10-05, a storey that received 0 flats was folded into the storey below as one tall zone with a single floor surface, so that storey's floor area was lost.
In 10-06 every storey has its own zones, its own floor and its own conditioned area. The flat count per building does not change.
The ~158 in our 2 Oct note was an early estimate of the affected Bologna buildings only; the rule above is what was finally applied.

**Did Madrid also have the floor-area defect?** **Yes.** 26 of the 243 rebuilt Madrid stems had lost floor area in 10-05; it is restored in 10-06.
The other rebuilt Madrid stems change zone layout only, not total floor area.
Bologna: 148 of the 183 rebuilt stems had lost floor area in 10-05. Per-stem detail: `.../division_residual_2026-09-29/t06s_floor_area_census.csv` (area_03, area_05, ratio, cls).
One known exception stays in 10-06: Bologna stem `97d478bc56840531`, flat `F0_dwelling_3` has no floor surface (about 5 % of that building's floor area; effect on the Bologna pooled EUI below 0.01 %). Accepted limitation.

**What is `_win_2026-10-06a`?** An intermediate build tree: 10-04 with the rebuilt stems swapped in, before the degenerate-surface clean-up and the FR/IT origin shift that produce 10-06. **Ignore it.**

## Q2. Madrid `59231039c486b1fb` (way/310774080)

- **Known; not fixed; run it as delivered.** Our own 10-06 run of this building shows the same single Severe (non-convex casting surface), return code 0, no fatal, EUI 75.72 kWh/m².
- It is included in our adopted Madrid number. 7 of our 1,163 Madrid results carry at least one Severe and all are included.
- The model is otherwise clean in our integrity check (5 storeys, 5 equal floor plates of 318 m², md5 matches the delivered list).
- Reporting it as "completed with one shading Severe" is consistent with how we report it.

## Info item (Madrid `1f682d2379be25ae`)

Noted; no action from us.
