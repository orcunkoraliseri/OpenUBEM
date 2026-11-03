# EXAMPLE — dwelling-layout validation sheet, no-core regime (`EU-13B` sample, superseded)

**Arc:** European locations × Step 8 · **Work package:** `EU-13B` (historical) · **Date this version:** 2026-09-02
· **Author:** director session

> **No-core regime header.** `D-EU-79`, owner's decision 2026-09-02. Supersedes
> `EXAMPLE_dwelling_layout_validation_2026-08-28.md`, which now lives in `rules/archive/`. The owner: "clearly
> [the earlier, more elaborate regime] makes things really complex. no need at this stage, our goal is to create
> flat division." Every drawing the archived version of this document showed depended on that earlier regime —
> a shared vertical-access zone on point blocks, a 1.80 m access band on slabs — and none of it survives here.

**Status: PROTOTYPE EVIDENCE, NOT A RESULT, AND SUPERSEDED.** No repository code stands behind any number in this
document. It is kept only as a historical record of the coverage-bar ruling (`D-EU-36`) and the q/(q+1)
stratification method, neither of which depended on the removed content.

---

## 1. What this document used to be, and what replaced it

The archived 2026-08-28 version drew eight real buildings twice — as EnergyPlus simulated them, and as a
prototype partitioner would — to show what a corrected floor plan looks like before `EU-13B` was dispatched. Every
one of those eight drawings depended on the earlier, more elaborate regime: a shared vertical-access zone on the
point block, an access band on the slabs, a spine on the elongated plate. Under the no-core regime none of that
is drawn, so none of those eight drawings, their shared-area-share numbers, or their per-building "scheme" labels
are valid any more.
They are **not reproduced here**, and they must not be quoted going forward.

**`D-EU-36` — coverage bar, RULED 2026-08-28 by the owner: ≥ 95 % of buildings is sufficient; 100 % is not
required.** This half of the ruling is untouched by the no-core regime: it is about how many buildings a ruled
partitioner can express, not about what sits between the flats it draws. A building the ruled scheme cannot
express is a `FAIL`, disclosed in the residual — never silently reduced in dwelling count to fit.

🔴 The other half of the original ruling — whether an unconditioned shared-access allowance is carved from the
observed plate or added outside it — is **moot under the no-core regime**: there is no such allowance to place
either way (`D-EU-79`). `EXAMPLE §1`'s open question is closed by the owner's later ruling, not answered.

---

## 2. Method — what the no-core regime draws

The live method of record is `scripts/eu21/07_nocore_tests.py` (`cut_nocore`, ported from
`06_nocore_control.py:145`), not the q/(q+1) stratification this document originally worked through. The four
laws that bind it:

1. **`D-EU-79` — the no-core regime.** A plate divides into dwellings only, with nothing else drawn on it.
2. **`D-EU-80` — no empty space per floor.** Every square metre belongs to exactly one flat; any leftover is
   absorbed into the flat it touches most. Equal flat areas are informational only, never a failure cause.
3. **`D-EU-81` — nothing narrower than 2 m.** No flat may contain any part narrower than 2.00 m, measured as the
   widest disc that fits inside it.
4. **Dwellings are equal-area column cuts of the real plate**, in the plate's own frame, clipped to the true
   footprint — not equal-width strips of a bounding box, and not the q/(q+1) storey stratification this document
   originally described.

Six checks score every plate (`scripts/eu21/04_group_tests.py:312`, `run_checks`, imported read-only by
`07_nocore_tests.py`): `C1` coverage `0.999 ≤ cov ≤ 1.001`; `C3` drawn flats equal claimed dwellings; `C4` one
room per flat, largest pairwise overlap `< 0.02 m²`; `C5` simple outline, no interior ring, no zone containing
another, `≤ 40` points per zone; `C6` outer-facade contact `≥ 2.50 m`; `C10` `widest_fit ≥ 2.00 m` over flats.
There is no seventh check and no refusal path: every plate with a usable footprint is cut, and a plate that
cannot clear a check is a `FAIL`, reported honestly.

---

## 3. Where the evidence lives now

The eight-building worked comparison this document used to carry is not reproduced under the no-core regime — it
was a hand-picked sample from a different, older population (`EU-13B`'s 2,544-building coverage census), and nothing
authorises redrawing it. The current, operative evidence is the full `EU-21` fleet:

| test | plates | verdict |
|---|---:|---|
| `TEST_01_nocore` | 33 | 33 PASS / 0 FAIL |
| `TEST_02_nocore` | 132 | 132 PASS / 0 FAIL |
| `TEST_03_nocore` | 55 | 55 PASS / 0 FAIL |
| `TEST_04_nocore` | 220 | 220 PASS / 0 FAIL |
| `TEST_05_nocore` | 110 | 110 PASS / 0 FAIL |
| **fleet** | **550** | **550 PASS / 0 FAIL** |

Sheets: `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0N_nocore_2026-09-02.html`. Census:
`openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N_nocore.json`. This is a geometric census only — no
EnergyPlus run stands behind any number here (`D-EU-55`).

---

## 4. What this document may and may not be quoted for

- ⚪ **May** be quoted for the `D-EU-36` coverage-bar ruling, which the no-core regime leaves untouched.
- 🔴 **May not** be quoted for any drawing, shared-area-share figure, or per-building scheme label from the
  archived 2026-08-28 version — every one of them described a regime the owner has since retired.
- 🔴 **May not** be quoted for any energy quantity. Nothing here, in either version, was simulated.
- 🔴 **May not** be read as the current state of the model. The operative evidence is §3 above.

---

## 5. Reproduction

| artefact | path |
|---|---|
| no-core builder | `scripts/eu21/07_nocore_tests.py` |
| fleet census | `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N_nocore.json`, N = 1..5 |
| delivered sheets | `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0N_nocore_2026-09-02.html` |
| archived original | `docs/docs_ACTIVE/europeanLocations/rules/archive/EXAMPLE_dwelling_layout_validation_2026-08-28.md` |
| plan of record | `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu21-nocore-2026-09-02.md` |
