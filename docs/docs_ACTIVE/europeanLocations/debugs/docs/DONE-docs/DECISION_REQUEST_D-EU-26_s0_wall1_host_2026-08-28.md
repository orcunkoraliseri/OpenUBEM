# Decision request `D-EU-26` — may a window be hosted on a `b < 1` `Wall_1`?

**Date:** 2026-08-28
**Status:** `RULED` (Option B selected)
**Raised by:** manager session, after GSSCanada 4J executed the 510-cell campaign for the first time
**Nothing here asks for compute.** Everything below is measured from the archetype registry and one three-run reproduction.


---

## 0. Ruling

> **Option B adopted.** No DESIGN passage authorises hosting an opening at `b = 1` on a party-wall-reduced
> `Wall_1`. The check is retained fail-closed, accepting 395 of 510 cells. The `uk` fold (with 17 of 36 archetypes refused by this check) shall never be quoted as a fold-level result.

- [ ] **A** — host the opening at `b = 1` on a reduced `Wall_1` (recovers 22 archetypes / 110 cells).
- [x] **B** — keep the check, accept 395 of 510, the `uk` fold **never** quoted at fold level. *(adopted)*
- [ ] **C** — keep the check and open a successor work package for reduced-`b` hosts.
- [ ] **D** — other: ______________________________________________

> **Owner name / initials:** Project Lead / Evaluator (AUTHOR / O.I.)  **Date:** 2026-08-28

*Ruled 2026-08-28 (Option B). Archived to `DONE-docs/` the same day; citation sweep performed — the
ruling is recorded in the MVP `EU-08` addendum and the `EU-09`/`EU-10` status rows, `§9.7.3`, the
director prompt head box, and the walkthrough progress log.*

**What this ruling does *not* do, whichever box is ticked:**

- It does **not** make `EU-09` / `EU-10` scoreable — `FINDING 181` is the binding gate (§5).
- It does **not** trigger a re-run on its own. Binding constraint agreed with GSSCanada 4J on
  2026-08-28: **the campaign is re-run once, after BOTH this ruling and `FINDING 181` settle**, so that
  a single superseding set of `idf_sha256` digests exists rather than one per ruling.
- It does **not** re-open `D-EU-23` (`S3 = 96`, mixed mode), `D-EU-24` (`S3` promotion), or the frozen
  `eu_campaign_cell_spec_v1.0.json`.

**On execution of this ruling:**

1. ✅ Tick recorded, `Status: RULED`, file archived to `DONE-docs/`, citations swept (2026-08-28).
2. ✅ MVP `EU-08` addendum + `EU-09`/`EU-10` rows and §9.7.3, director prompt head box, and the
   walkthrough progress log all updated (2026-08-28).
3. ✅ `EU-09` / `EU-10` remain **UNSCORED** and 4J's refusal stands until `FINDING 181` also closes.

---

## 1. What is already fixed and is *not* part of this request

Two of 4J's four findings were defects in `openubem/campaign/eu_cell_runner.py` and are repaired:

- the `ENERGYPLUS_PATH` directory-vs-binary divergence (`_energyplus_exe`);
- the **missing `InternalMass`** — the S0 envelope is `Material:NoMass` throughout, so the zone had
  zero heat capacity, EnergyPlus warned that the solution is unstable, and the campaign was **not
  reproducible**. Verified on 4J's own flipping cell: `uk__GB.ENG.MFH.02.Gen.ReEx.001.001__f050`
  now returns **76524.889 kWh three times running, 0 severe, 0 fatal**, against 74253.89 / 54094.73 /
  fatal before. A `completed` / `completion_status` field was added to the manifest as 4J asked.

🔴 **Every `idf_sha256` and every heating value from the first campaign is superseded.** No published
figure moves — nothing from that run was ever scored.

---

## 2. The finding that needs a ruling

**115 of 510 cells never build an IDF, deterministically — 23 of the 102 archetypes × 5 `f` levels.**
The dominant cause, **22 of the 23**, is one check at `openubem/idf/european_box.py:267`:

> `S0 openings require an exterior (b=1) Wall_1 host`

| fold | archetypes | lost to this check | other cause |
|---|---:|---:|---|
| `uk` | 36 | **17** | — |
| `it` | 42 | 4 | — |
| `es` | 24 | 1 | 1 (directional window areas vs `A_Window_1`) |
| `fr` | — | 0 | 0 |

**`uk` loses 17 of its 36 archetypes — 47 % of the fold.**

The `b` in question is **not** the display `b_Transmission_*` field: `_component_values` derives an
*effective* `b = H / (U·A)` from the audited `H_Transmission_Wall_1` term. On the display field only
8 GB archetypes read `wall_1 = 0.5`; on the audited term, 17 do. The data is behaving correctly —
these are party-wall-reduced rows — and the check is doing what it was written to do.

---

## 3. Why it is a judgement

A wall whose *aggregate* transmission is reduced (`b = 0.5`) can still physically carry a window, and
the window itself is exterior at `b = 1`. The check refuses that case outright rather than hosting the
opening at `b = 1` on a reduced host. Which reading is right is a **physics/DESIGN** question about
what TABULA's `A_Wall_1` means when its `H` term is party-wall-reduced — it is not something a
measurement settles, and I will not decide it.

---

## 4. Options — the full statement of each

- [ ] **A — Rule the check too strict: host the opening at `b = 1` on a reduced `Wall_1`.**
  Recovers 22 archetypes (110 cells), including 17 of `uk`'s 36. Requires a DESIGN citation for the
  hosting rule and a regression test per fold. *Recommended only if the DESIGN supports it — I have
  not found a passage that does.*

- [ ] **B — Keep the check and accept the loss.**
  The campaign is then **395 of 510 cells**, and 🔴 **the `uk` fold is 47 % incomplete and must never
  be quoted as a fold-level result.** Honest, costs nothing, and is reversible.

- [ ] **C — Keep the check, and open a successor work package to represent reduced-`b` hosts properly.**
  Separates "the entry point is correct" from "the GB stock is representable".

- [ ] **D — Other** (state it below).

*Tick in §0, not here.*

---

## 5. 🔴 What changed after this request was written — read before ruling

The `InternalMass` repair was necessary and **not sufficient**. On three re-runs of the repaired
runner only **136 of 510 cells are clean and bit-reproducible**, and only **5 archetypes** are complete
across all five `f` levels (`it` 3, `uk` 2, **`es` 0** — the whole Madrid fold carries an out-of-range
temperature warning). That is `FINDING 181`, and it is a **separate, open** question about the S0
equivalent-envelope method, not about this check.

🔴 **On those five archetypes the full `f000`→`f100` sweep moves heating by 0.11–0.39 %, and not
monotonically, against a 45.5 % run-to-run spread.** The effect the campaign exists to measure is two
orders of magnitude below the current noise floor.

**Consequence for this ruling:** whichever option is taken, **it does not by itself make `EU-09`
scoreable**. `D-EU-26` decides how many cells are *attempted*; `FINDING 181` decides whether any
attempted cell means anything. They are not substitutes, and the stability question is the binding one.

⚪ Ex-ante check on whichever option is chosen: of the 42 archetypes with any reproducible cell, 5 have
all five `f` levels, **16 have four**, 7 three, 12 two, 2 one — the sixteen one-short archetypes are
where a partial recovery would show up first.

---

## 6. Evidence

| claim | where |
|---|---|
| the check and the effective-`b` derivation | `openubem/idf/european_box.py:267`, `:141-174` |
| 23 refusing archetypes by fold and cause | reproduced over all 102 registry records, no simulation |
| 8 display-`b` vs 17 effective-`b` GB rows | `openubem/data/construction/tabula_archetypes_gb.json` |
| the reproducibility repair and its three-run check | `openubem/campaign/eu_cell_runner.py`; `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` |
| 4J's measured run: 353 completed / 115 refused / 42 engine-failed, and 130 status-flips over three runs | cross-session reports, 2026-08-28 |

---
