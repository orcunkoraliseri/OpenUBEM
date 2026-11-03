# P5 — Author the external-literature-validation deep-research prompts (T09)

**Prereq:** T08 done, CP4 audited, manager greenlit authoring.
**Paste the block below to a fresh Sonnet session.** This is **markdown authoring** — no code, no compute.

---

Read `C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\PLAN_resolution_mode_switch.md`
§6 **T09**, §9 (the divergence figures to be validated), and §10 (the seed citations). Then read **all six**
template files in
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\deepResearch\layoutMapping\L01..L06_*_prompt.md`
— they are the **exact skeleton** to copy.

Execute **T09 only.** Deliverable: a new deep-research prompt set under
`docs/docs_ACTIVE/simulation-Resolution/deepResearch/literatureValidation/`.

Create:
- `00_README_literature_validation_prompt_set.md` — index + shared facts (OpenUBEM is zero-fitted, validated
  at city scale within ±9 %; the four modes; the §9 deltas to be checked; the archetype cohorts
  offices / high-rise residential / warehouse).
- **One prompt per validation axis** (you choose the exact split; suggested ~6): (1) annual-EUI zoning
  sensitivity at **building** scale; (2) annual-EUI zoning sensitivity at **district** scale; (3)
  heating/cooling resolution effect; (4) **peak / equipment-sizing** sensitivity; (5) daylighting/lighting
  over-prediction in coarse modes; (6) archetype-cohort stratification & the city-scale wash-out.

Each prompt MUST follow the L01–L06 structure **section-for-section**:
`SCOPE GUARD` (read-first, what the deliverable is and is NOT) → **What this document is** → **Role** →
**Why this matters (so you scope correctly)** → **REQUIRED OUTPUT TABLES** (fill-every-cell, asking for
published quantitative ranges with sources, in SI/%) → **Part C — Synthesis** → **Output format (follow
exactly)** → **Hard requirements**. Each table must elicit: the comparison, the measured delta, the
building/district scale, the source, and an explicit relation to OpenUBEM's **±9 % tolerance**.

Seed every prompt's Role/Why with the §10 references as starting points (Chen & Hong 2018, Faure et al.
2022, Dogan & Reinhart 2017, Cerezo Davila et al. 2017, Johari et al. 2022, Iseri et al. 2025) but require
the researcher to source beyond them and flag GAPs.

Hard rules:
- **Markdown only — no `.py` under `docs/`.** Touch only the new `literatureValidation/` folder.
- These prompts **commission** the validation research; they do **not** perform the comparison. The actual
  in/out-of-envelope check of T08 results against the returned `RESULT_*` reports is a later follow-on (same
  pattern as L01–L06 preceding the RESULT_L0x files) — say so in the README.
- Do not edit the PLAN except to append a **T09 progress-log entry under §8**.

Report: the file tree created, and a one-line purpose per prompt. If the scope is ambiguous, **STOP and
quote the conflict** — do not invent validation axes beyond the resolution-mode question.
