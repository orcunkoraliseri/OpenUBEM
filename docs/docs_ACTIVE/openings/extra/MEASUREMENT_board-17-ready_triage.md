# MEASUREMENT — T01 of `PLAN_board-17-ready-2026-08-19.md`: triage all 17 board rows against the register

Read-only. No cluster, no fleet run, no simulation. Verdicts follow §4.2: a row whose staleness
cannot be evidenced with a file path + line number or a dated ruling is `UNRESOLVED`, not `STALE`.

## Method

The 17 rows are the ones whose status literal is `"open"` in `scratchpad/board.html`'s `WP` array,
at the line numbers given in the dispatch: 604, 618, 702, 704, 721, 727, 735, 740, 770, 809, 823,
839, 858, 864, 867, 873, 905. Each was read directly from `board.html`, matched to a register ID
using the register's §1 summary table (`docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md`,
table body starting line 686), and classified. Where a row maps to a "ruling executed" rather than a
single register ID (V7, W11, W9), the executing plan doc's own progress log was read to confirm
completion.

Full result: `openubem/outputs/comparisons/board17_row_to_register.csv`.

## Counts by verdict

| verdict | count | rows |
|---|---:|---|
| STALE-CLOSED | 7 | NEW, NEW2, N6, N10b, N10, O2, Q3 |
| STALE-RULED | 5 | T7, U6, V7, W11, W9 |
| OPEN | 4 | N05b, N3, W8, **W6** |
| IN-FLIGHT | 1 | X10 |
| UNRESOLVED | 0 | — |

**12 stale / 4 open / 1 in-flight — not the provisional 13/3/1.**

## Disagreement with the director's provisional table

**W6 ("a big number that must not be quoted") is wrongly bucketed as a closed, no-live-item
measurement. It is not — it is OPEN-35's own X04 finding, and OPEN-35 is a live register item.**

The board's W6 text: *"The 2,611 buildings with no storey information appear to use 48% more energy
than the rest of the fleet. That is an illusion created by mixing neighbourhoods. One neighbourhood
alone supplies 1,589 of them... within neighbourhoods the direction is not even consistent — four go
up, four go down."*

The register's OPEN-35 row (`INVESTIGATION_open-items-register.md:720`), its 2026-08-18 overnight
(X04) amendment, word for word: *"the +47.9% fleet EUI gap is composition (nyc_suburban is 1,589 of
2,611 with no comparison group) and WITHIN cells the direction is not even consistent — 4 lower, 4
higher. Needs an intervention, not a cross-section."*

Same numbers (47.9%/48%, 1,589, 4/4 split), same mechanism, same open question. This is not two
measurements that happen to agree — it is one finding, recorded once, inside a register item
(OPEN-35) that is **live, not struck**. The provisional table's verdict for W6 — *"measurement
complete, no live item... → done"* — is wrong on both halves: the measurement is not a standalone
closed item (it has no register ID of its own), and OPEN-35, which it belongs to, is not done.
**Corrected verdict: OPEN, folds into OPEN-35 — do not close or strike this board row on its own.**

## Every row, with evidence

### STALE-CLOSED (7) — register item struck/retired

| row | title (short) | register ID | evidence |
|---|---|---|---|
| NEW | 158 is an average of averages | OPEN-43 | register.md:729 — `~~OPEN-43~~` CLOSED 2026-08-12 on the user's ruling, formally retired 2026-08-13 (ruling `2h`); pooled 157.1 kWh/m² is the adopted headline definition |
| NEW2 | 106 hidden test failures | OPEN-44 | register.md:730 — `~~OPEN-44~~` CLOSED + ID RETIRED 2026-08-13; 0 failed / 1,859 passed / 55 skipped / 0 errors, CP-1 signed |
| N6 | completion records: six, not one | OPEN-36 | register.md:721 — `~~OPEN-36~~` CLOSED + ID RETIRED 2026-08-13; corrected at source with a dated CORRECTION banner |
| N10b | a completed task whose code was never in the project | OPEN-36 (same item as N6) | register.md:721, same citation |
| N10 | elevators are not the tenth end-use | OPEN-46 | register.md:732 — `~~OPEN-46~~` CLOSED + ID RETIRED 2026-08-18 (T01 of `PLAN_four-items-2026-08-18.md`); all four reporting-chain links verified at HEAD, 65/65 targeted tests + full suite green |
| O2 | the headline run cannot be reproduced | OPEN-48 | register.md:734 — `~~OPEN-48~~` CLOSED + ID RETIRED 2026-08-18 (late); `open48_refleet3` re-run made, OPEN-49 fix moves classified buildings under 0.08% |
| Q3 | tests quietly edit a stored dataset | OPEN-50 | register.md:742 — `~~OPEN-50~~` FIXED + ID RETIRED 2026-08-13; fixture now writes to `tmp_path_factory`, proved by hash+mtime either side of a 24-min suite run |

### STALE-RULED (5) — the user ruled and it was executed

| row | title (short) | maps to | evidence |
|---|---|---|---|
| T7 | data-centre fix, waiting on you | OPEN-55 | register.md:740 — `**OPEN-55**` (live, not struck): "RULED (user, R1, 2026-08-19): Option B+ — and IMPLEMENTED the same day (T01)." **Caveat, not smoothed over:** OPEN-55 itself is explicitly "NOT CLOSED — the proposal's own falsifiable test has never run... Blocked by OPEN-57." The specific ask ("where does the line fall") is answered; the item that ask belongs to stays open on a different blocker. |
| U6 | still waiting on you | OPEN-55 (same) | same citation as T7 |
| V7 | two closures waiting on you | ruling R2 (OPEN-42, OPEN-11) | `implemenation/previous/PLAN_ten-items-2026-08-19.md:1266`, T09 "Execute ruling R2" — progress log entry dated completed 2026-08-19; register.md:728 (`~~OPEN-42~~` CLOSED 2026-08-19, T09, ruling R2) and :696 (`~~OPEN-11~~` CLOSED 2026-08-19, T09, ruling R2) |
| W11 | four closures waiting on you | ruling R2 (OPEN-42, OPEN-11, OPEN-07, OPEN-08) | same T09 citation; register.md:728, :696, :692 (`~~OPEN-07~~`), :693 (`~~OPEN-08~~`) — all four read "CLOSED 2026-08-19 (T09, ruling R2)" |
| W9 | how exposed the evidence is, in GB | ruling R3 (OPEN-53 context) | `extra/MEASUREMENT_open-53_evidence-preservation_2026-08-19.md:94` — "323 files, 12,565,016 bytes (11.98 MB, 0.0126 GB)" copied and hash-verified twice (line 139: "323/323 verified, both passes"); `PLAN_ten-items-2026-08-19.md:1202`, T10 "Execute ruling R3" completed 2026-08-19. **Caveat:** OPEN-53 itself stays open — the MEASUREMENT doc's own line 196 says so; only the specific GB-exposure action W9 named is discharged. |

### OPEN (4) — live register item, work remains

| row | title (short) | register ID | evidence |
|---|---|---|---|
| N05b | two different guesses for the same missing storey count | OPEN-35 | register.md:720 — live; "Still open — the intended-fallback question is a DESIGN decision, not a measurement." 2,611/8,160 = 32.00%, 1,031 given a mid/high-rise archetype and built at one storey |
| N3 | literature check came back worse than empty | OPEN-47 | register.md:733 — live; source found (Chen, Hong & Piette 2017) but the classifier tests area only where the source tests area AND floor count ≤3; needs a ruling, gated behind fixture ruling `2a` |
| W8 | eight inherited defects, finally decidable | OPEN-29 | register.md:714 — live; adoption material exists (X07, T08 of `PLAN_ten-items-2026-08-19.md`), needs a director ruling per ID — see T02 below |
| **W6** | a big number that must not be quoted | **OPEN-35** (reclassified — see disagreement above) | register.md:720, X04 amendment — same finding, same numbers, live item |

### IN-FLIGHT (1)

| row | title (short) | maps to | evidence |
|---|---|---|---|
| X10 | two new problems found by accident | OPEN-57 + OPEN-58 | `implemenation/previous/PLAN_open-57-and-58_2026-08-19.md:1-8` — user authorisation quoted verbatim, 2026-08-19: *"commencer les deux en meme process, 57 et apres continnuer avec 58."* Register rows live: :743 (OPEN-57), :744 (OPEN-58). **Precision note:** the plan's own §8 progress log is empty at the time of this check — zero tasks have been reported complete. "In-flight" here means authorised and queued under a named plan, not actively mid-execution as of this reading. |

## UNRESOLVED

None. Every one of the 17 rows resolved to a register ID (or a named ruling) with a citable file
path and line number, or a quoted dated ruling.

## What this means for the board

The board currently shows 17 "ready" rows. On the evidence above: 12 are stale bookkeeping (the
underlying work is done or ruled and executed — the board just never got told), 4 are genuinely open
work with a live register item, and 1 is authorised/queued under its own plan. **This corrects the
director's provisional 13/3/1 to 12/4/1** — W6 does not get its own "done, no live item" bucket; it
folds into OPEN-35 and should be retired as a board row only when OPEN-35 closes, not on its own.
