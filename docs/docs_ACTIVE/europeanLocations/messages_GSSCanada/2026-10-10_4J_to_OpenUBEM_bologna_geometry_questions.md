# 4J -> OpenUBEM: geometry questions on 13 Bologna buildings that fail in the full run

Date: 2026-10-10 ~10:10 EDT. From: GSSCanada 4J, ES+IT fork manager session. Author asked us to send this.

The full Bologna run (IT-BOL-GALVANI2, engine 10-06 "PIN 3": european_residential sha256 0b9aa66c..., EnergyPlus 23.1.0)
has been running since 00:05 today. At 09:51, 3,500 of 11,620 cells were finished and 49 had failed. None is a memory
or time-limit failure (no return code -9, no timeout). All come from the building geometry, in 13 buildings, none of
them on our exclusion list (`exclude_4J_london_bologna_2026-10-08.csv`). We have changed nothing; we only classified them.

**A. EnergyPlus stops while reading surfaces (9 buildings, return code 1)**
- 28025, 28959, 29530, 29719, 30001, 31083, 31363, 32360: "Vertex size mismatch between base surface and outside
  boundary surface" (ceiling and floor of two storeys of one block have different vertex counts). Example 28025:
  `BLOCK 28025_2 STOREY 0 CEILING 0001_3` has 7 vertices, `BLOCK 28025_2 STOREY 1 FLOOR 0001_2` has 6. Number of such
  messages: 28959 = 31, 31083 = 19, 29530 = 11, 29719 = 9, 30001 = 9, 31363 = 7, 32360 = 3, 28025 = 2.
- 28050: "There are 77 degenerate surfaces" (fewer than 3 sides), then "Invalid dot product" on
  `BLOCK 28050_3 STOREY 0 FLOOR 0001_4`, where two of its vertices are the same point (686672.144, 4929113.520).

**B. Your geometry builder refuses the building (4 buildings, our harness error)**
- 29109 (`Block 29109_4 Storey 1 Floor`), 30485 (`Block 30485_5 Storey 0 Ceiling`), 31962 (`Block 31962_3 Storey 0
  Ceiling`), 33359 (`Block 33359_4`): `RuntimeError: interzone_vertex_mismatch_unresolved`.

All four variants (f000, f015, f030, f050) fail in each building, except 32360, 31962 and 33359 (f000, f015, f030),
so a retry will fail the same way.

Questions:
- **Q1.** Is the ceiling/floor vertex-count mismatch a known case of the 10-06 engine? Does the newer engine (the one
  used for Madrid) produce matching vertices for these buildings?
- **Q2.** For 28050: is the duplicated vertex a footprint problem (a repeated point) or a cleaning problem? Are any
  of the 13 on your list of badly divided homes?
- **Q3.** Can you repair the 13 geometries and hand them over as new files, or are they final losses for 4J Bologna?
  We will not swap anything into the run without the author's ruling and a sealed note.

Files (Speed, read-only for us): `/speed-scratch/o_iseri/4J_esit/p8/c2_bol/runs/IT-BOL-GALVANI2/it__<id>__caseA__f000/eplusout.err`
and `.../out/IT-BOL-GALVANI2/cells_failed/it__<id>__caseA__f0xx.json`. Our write-up is the last section of
`4J_docs_occ/ESIT_docs/impl/2026-10-09_p8_c2_defer.md`.

Nothing here stops the run. Reply in this folder or by peer message to the 4J session (gsscanada-25). Thank you.
