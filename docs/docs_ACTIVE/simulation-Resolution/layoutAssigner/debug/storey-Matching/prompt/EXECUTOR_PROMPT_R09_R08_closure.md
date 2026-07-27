# Executor prompt — R09 (figures) then R08 (documentation closure)

> Pre-drafted by the director 2026-07-26. Dispatch a **fresh Sonnet** only after the `R06` progress-log
> entry exists in §5 and the director has accepted it. R09 consumes R06's `t20_*` harvest; there is no
> shortcut that reuses T19.

---

Working directory `C:\Users\o_iseri\Desktop\OpenUBEM`. Read §1 (hard rules) and §3 tasks **R08** and
**R09** of
`docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\PLAN_storey-matching_REMAINder.md`,
plus the **AUDIT — CP-D** entry and the `R06` entry in §5. Do not read
`PLAN_storey-matching_implementation.md` (CLOSED, ~3,500 lines) — grep it by `F-nn` / `E-LA-nn` ID.

Execute **R09 first, then R08**, in that order, in one pass.

## 🔴 Absolute rules

- **🔒 The four existing viewers and everything else already under**
  `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\figures\` **are FROZEN.** Do not re-run
  `scripts\analysis\enrich_layout_assign_viewers.py`. Do not touch `before_viewer_enrich\`,
  `before_B05\`, `before_B08b\`.
  **Exception, and only this one:** R09's five `layout_assign_vs_modes_*` figures, their summary CSV
  and `README.md` are its named deliverables and ARE regenerated — but **only after archiving the
  current versions** to `openubem/outputs/comparisons/previous/*_t19.*`, exactly as the T17 set was
  preserved when T19 landed. **Archive first, overwrite second.** Never overwrite a prior generation
  without archiving it.
- **Never `git commit`.** Never edit root `main.py`, any OVERVIEW or DESIGN doc, or `MEMORY.md`.
- Never rewrite a frozen progress-log or AUDIT entry — append only.
- No compute on the Speed login node. Interpreter `./.venv/Scripts/python.exe`.
- All `.png` outputs also go flat to `openubem/outputs/`; keep the `docs_ACTIVE` copies in sync.

## R09 — the five cross-mode figures, on the T20 harvest

Target: `docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\figures\` — five PNGs,
`layout_assign_vs_modes_la_summary.csv`, `README.md`, and §3/§3a of
`OpenUBEM_results_LayoutAssigner.md`.

Compare `layout_assign` against `building` / `floor` / `fast_zone` / `auto`: zone-count fidelity
(Fig 1), LA-cell EUI (Fig 2), full-fleet EUI (Fig 5), full-fleet success/fail (Fig 6).

Non-negotiable labelling:
- **Label the harvest provenance on each side of every figure.** Mixing a T20 side against a T17/T19
  side unlabelled is the failure mode to avoid.
- **State the EUI denominator convention per mode**, explicitly. This arc exists partly because a
  nominal denominator was silently wrong; do not ship a figure whose denominator is implicit.
- **Figure 3 (severity) stays frozen** unless you rebuild it from real `eplusout.err` data.
- The **never-validated-against-metered-data** caveat survives verbatim. Do not soften it.
- **E-LA-22 still stands**, so T20-vs-T19 deltas are not cleanly attributable to this arc. Say so on
  the figures or in the README — not only in the prose.

## R08 — documentation closure

Update the results doc, `PROJECT_CHECKLIST.md` §L, and **Q3's own entry in
`DONE/DONE-implementation_plan.md` §7** — Q3 is closed by this arc or it is not closed at all.

**The disclosure list is headline text, not a footnote.** Every item below is disclosed plainly:

1. `match_storeys()` expresses only `n_proto ∈ {1, 3}` and only the taller case. `n_proto == 2`
   (`SmallOffice`, 2,848 fleet buildings) and `n_proto >= 4` fall back permanently, as does every
   `n_real < n_proto`.
2. **R10's exactness rule further shrinks the expressible set on the two ZoneGroup archetypes:**
   `HighriseApartment` matches only at `n_real ∈ {10, 18, 26, …}`, `MidriseApartment` only at even
   `n_real ≥ 4`. Use **R06 item 6's measured count** — the old 81.6% / 98.4% inert shares are stale
   and must not be reprinted.
3. Storey matching is invisible in geometry by construction (D3(a)). Height does **not** track
   `num_floors` (E-LA-33) — state it, so no reader infers that 12.19 m towers over 1-storey houses
   were intended.
4. 718 buildings (8.8%) have no `ARCHETYPE_IDF_MAP` entry.
5. The shape-mismatch overlap residual is a **design property** of the mode, not a bug.
6. **R03's PV/generator invariance is synthetic-fixture only** — neither apartment archetype carries
   PV or generator objects, so it has no real-run evidence. Disclose it as such; do not imply it was
   validated on a real run.
7. **E-LA-36** (the `Zone.Multiplier` × `ZoneList` compounding, a silent 50% storey over-count on the
   dominant archetype) was found and fixed **inside this arc**. Say what it was and what it would have
   cost — a defect caught by audit is part of the result, not an embarrassment to bury.
8. **Forwarded out, not fixed here:** E-LA-21/22/23/24 and **E-LA-37** (editing the `ZoneGroup`'s own
   Zone List Multiplier would restore exact expressibility at every `n_real`; it is a different
   mechanism from D3(a) and R04 is closed at option (a)).

**R07 is REDUCED to a written statement inside R08** — no new figure panel. Write up its three
already-measured quantities (placement: hull centroid vs `footprint_centroid_utm`; plate area and
aspect ratio vs the real footprint; the overlap residual labelled as the design property it is), from
B08a/B08b's measurements, plus the explicit out-of-scope statement about height. Nothing is dropped
from the record — only the redundant rendering pass.
**Reinstate R07 in full only if** R06 turned out to change geometry.

## Deliverable

Append one `R09` and one `R08` progress-log entry to §5, then write a short **completion report** for
the director covering: what changed in the figures, the final disclosure list as shipped, and anything
you could not close. Then report back — **CP-E is the director's to sign, not yours.**
