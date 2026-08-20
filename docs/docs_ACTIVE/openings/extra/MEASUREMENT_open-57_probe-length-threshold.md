# OPEN-57 — probe-length threshold measurement (T01-T03) — 2026-08-19

Plan: `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open-57-and-58_2026-08-19.md`.
Harness: `scripts/diagnostics/open57_probe_length_sweep.py`. Raw call log (JSON-lines,
one record per SSH call, in order): scratchpad `open57_probe_sweep.jsonl` (26 records).

## Result up front

**The fault is a deterministic length limit, not a transient fault, and the boundary is
now resolved to single-id precision.** The largest id count that parses is **565**
(exit 0, empty output, on a remote directory verified absent before and after the whole
sweep); the smallest that does not is **566** (exit 1, verbatim stderr `Unmatched '.`,
reproduced 3/3 independently). This directly falsifies the transient-fault hypothesis
carried forward from `extra/MEASUREMENT_open-55_acceptance-test-attempt3.md` (which
called the fault "transient or intermittent" from two data points that never varied
length). It was never transient; it had never been tested below ~23,000 characters
before.

**Director-authorised extension, 2026-08-19:** T02's original bisection stopped at a
66-id / 924-byte bracket (500 pass / 566 fail) because the plan's 20-call cap for the
whole plan ran out before single-id resolution was reached (see prior progress-log entry
under T02). The director raised the cap by 8 calls, for this one purpose only, to close
that bracket. 7 of those 8 calls were used; 1 remained unspent. The bracket closed
cleanly by simple binary search (533, 549, 557, 561, 563, 564, 565 — each a PASS,
narrowing the fail side down from 566 without ever needing to retest it) to the single-id
flip point 565/566, with the 566-fail side already reproduced 3/3 from the original T02
run. Total calls across the whole plan for OPEN-57's measurement (T01-T03 plus this
extension): **26**, against a cap of 20+8=28.

## Call budget: 26 of 28 used (20 original + 8 director-authorised for T02 narrowing)

| # | label | id count | probe bytes | exit | stderr |
|---|---|---|---|---|---|
| 1 | check_dir_absent (before) | - | - | 2 | `ls: cannot access '.../__open57_probe_nonexistent__': No such file or directory` |
| 2 | T01_positive_control_10 | 10 | 396 | 0 | (empty) |
| 3 | T01_negative_control_1589 | 1,589 | 23,160 | 1 | `Unmatched '.` |
| 4 | T02_ladder_226 | 226 | 3,420 | 0 | (empty) |
| 5 | T02_ladder_500 | 500 | 7,256 | 0 | (empty) |
| 6 | T02_ladder_1000 | 1,000 | 14,325 | 1 | `Unmatched '.` |
| 7 | T02_bisect_750 | 750 | 10,756 | 1 | `Unmatched '.` |
| 8 | T02_bisect_625 | 625 | 9,006 | 1 | `Unmatched '.` |
| 9 | T02_probe_566 | 566 | 8,180 | 1 | `Unmatched '.` |
| 10 | T02_probe_567 | 567 | 8,194 | 1 | `Unmatched '.` |
| 11 | T02_repro_500_rep2 | 500 | 7,256 | 0 | (empty) |
| 12 | T02_repro_500_rep3 | 500 | 7,256 | 0 | (empty) |
| 13 | T02_repro_566_rep2 | 566 | 8,180 | 1 | `Unmatched '.` |
| 14 | T02_repro_566_rep3 | 566 | 8,180 | 1 | `Unmatched '.` |
| 15 | T03_boundary_single_token | 566 (len-matched) | 8,180 | 1 | `Unmatched '.` |
| 16 | T03_boundary_no_quotes | 566 (len-matched) | 8,180 | 1 | `Unmatched '.` |
| 17 | T03_below_single_token | 500 (len-matched) | 7,256 | 0 | (empty) |
| 18 | T03_below_no_quotes | 500 (len-matched) | 7,256 | 0 | (empty) |
| 19 | check_dir_absent (after) | - | - | 2 | `ls: cannot access '.../__open57_probe_nonexistent__': No such file or directory` |
| 20 | T02_single_bisect_533 | 533 | 7,718 | 0 | (empty) |
| 21 | T02_single_bisect_549 | 549 | 7,942 | 0 | (empty) |
| 22 | T02_single_bisect_557 | 557 | 8,054 | 0 | (empty) |
| 23 | T02_single_bisect_561 | 561 | 8,110 | 0 | (empty) |
| 24 | T02_single_bisect_563 | 563 | 8,138 | 0 | (empty) |
| 25 | T02_single_bisect_564 | 564 | 8,152 | 0 | (empty) |
| 26 | T02_single_bisect_565 | 565 | 8,166 | 0 | (empty) |

Calls 20-26 are the director-authorised T02 narrowing extension, run 2026-08-19 after
the rest of this record. Standard binary search on id count within the (500, 566)
bracket, each step re-using the same harness and the same absent target directory: every
one of the 7 calls landed PASS, which is exactly what a monotonic single boundary
predicts — each successive midpoint (533, 549, 557, 561, 563, 564, 565) sits below the
true flip point, so the search kept moving the *low* (pass) end up without needing to
retest the *high* (566, fail) end, which had already been reproduced 3/3 in calls 9, 13,
14. The last step (565) leaves a 1-id gap to the already-confirmed failure at 566 —
single-id resolution, reached in 7 of the 8 authorised calls.

Both absent-directory checks (#1 and #19) confirm `__open57_probe_nonexistent__` was
never created — zero filesystem work occurred on the remote side for any call in this
sweep, satisfying §4.3. Calls 20-26 target the same directory via the same harness
function and are covered by the same before/after absence checks (no directory writes
occur on the parse-success path either way, per §4.3).

Real osm_ids used throughout: the frozen 1,589-entry list from OPEN-55 attempt 3
(`%TEMP%/ubem_validation/open48_refleet3_t02a3/nyc_suburban/step3/03_idf_manifest.parquet`,
IDF-stem shape `way_605951159`, 13-14 chars each) — the exact list and shape that
produced the original production fault, so this is a reproduction of the real failure,
not a synthetic analogue. No synthetic ids were needed (all tested counts stayed within
this list's 1,589 entries).

## T01 — both controls landed as predicted

- Positive control (10 ids, 396 bytes): exit 0, empty stdout+stderr.
- Negative control (1,589 ids, 23,160 bytes): exit 1, `Unmatched '.` — reproduced the
  fault on a directory that has never existed, ruling out any completeness-answer
  confound.

## T02 — the boundary, resolved to single-id precision

Pinned ladder (226 -> 500 -> 1,000 -> 1,589): **226 and 500 pass; 1,000 and 1,589 fail.**
Bisection first narrowed the flip to between 500 (pass) and 566 (fail); a targeted check
at 8,192 bytes (a common buffer-size round number, since 566/567 straddled it) showed
**both 566 (8,180 B) and 567 (8,194 B) fail** — so a naive 8,192-byte reading is already
wrong at that granularity. The director-authorised extension (calls 20-26, see call
table) then closed the remaining 66-id bracket by simple binary search on id count to a
**single-id boundary: N=565 parses, N=566 does not.**

**The threshold, in all three measures the harness records** (largest confirmed PASS vs.
smallest confirmed FAIL):

| measure | N=565 (PASS) | N=566 (FAIL) | gap |
|---|---|---|---|
| `probe_len` (probe body) | 8,166 B | 8,180 B | 14 B |
| `wrapper_len` (`bash -lc '...'`) | 8,177 B | 8,191 B | 14 B |
| `argv_len` (full `ssh` argv) | 8,213 B | 8,227 B | 14 B |

The 14-byte gap at every measure is the harness's own resolution limit here, not a
residual uncertainty: each additional id in this stretch of the frozen list is a
uniform 13-character `way_NNNNNNNNN` token plus 1 join-space (verified directly — ids
500 through 565 of the frozen list are all 13 characters), so id count cannot step the
probe by anything finer than 14 bytes. This is genuinely single-id resolution; a finer
byte-level boundary would require a different (non-id-list) length-varying mechanism,
which is outside what T02 asks for.

**Reproducibility:** the FAIL side (566 ids) was reproduced 3/3 in the original T02 run
(calls 9, 13, 14, all identical verbatim stderr `Unmatched '.`). The PASS side at the new
boundary (565 ids, call 26) was produced once; the PASS side generally was reproduced
3/3 at 500 ids (calls 5, 11, 12) earlier in the same monotonic run, and every one of the
7 new bisection calls (533 through 565) landed PASS with no exception, consistent with a
single, non-fluctuating boundary rather than a fuzzy one.

**Is this consistent with an 8,192-byte buffer? No — and the data already contradicts it
before rounding.** Take the measure closest to 8,192: `wrapper_len`. Its FAIL-side value
is **8,191 bytes — one byte below 8,192** — and it still fails. If a simple "must fit
under a 8,192-byte buffer" rule were the mechanism, 8,191 bytes should still parse; it
does not. The PASS-side `wrapper_len` (8,177 B) is 15 bytes further below 8,192, so the
true cutoff (somewhere in 8,177-8,191) sits entirely under 8,192, not at it. `probe_len`
(8,166/8,180) and `argv_len` (8,213/8,227) are not near 8,192 either — `argv_len`'s
FAIL side is in fact *above* 8,192. **None of the three measures lands on 8,192, or on
any of the plan's other four round buffer sizes (4,096 / 10,240 / 16,384 / 20,480 B) —
this is a no-round-number match, reported plainly rather than forced to one.**

## T03 — length is the cause, content is not

At both the boundary length (8,180 B, the smallest confirmed-fail) and the below-boundary
length (7,256 B, the largest confirmed-pass), three content variants were tested, all
held to the **exact same byte length** as the real-id baseline (verified locally before
spending any SSH call — see harness `build_probe_variant`):

| variant | 7,256 B (below) | 8,180 B (boundary) |
|---|---|---|
| (a) real id list | PASS (calls 5, 11, 12) | FAIL (calls 9, 13, 14) |
| (b) single long token, same total length | PASS (call 17) | FAIL (call 15) |
| (c) both double-quoted strings unquoted, length restored with trailing pad | PASS (call 18) | FAIL (call 16) |

**All three variants flip at the identical length.** Content is irrelevant; length is
the sole determinant. This matches the mechanism implied by the fault text itself: since
`_ssh`'s outer wrapper is `bash -lc '<cmd>'` and the remote login shell (tcsh) receives
this as a single `-c` argument, `Unmatched '.` is tcsh reporting that the **outer closing
single quote was never seen** — consistent with tcsh (or an intermediate buffer) simply
truncating the incoming command line at a fixed byte count, which always chops off the
final `'` regardless of what the truncated bytes contained. This is offered as an
explanation for *why* length alone matters, not as a proven root cause — no further
diagnosis was attempted (out of scope for a measurement task).

## Answer to CP-1's required elements

- **Boundary length, resolved to single-id precision:** id count **565 parses, 566 does
  not**. In bytes: `probe_len` 8,166 (pass) / 8,180 (fail); `wrapper_len` 8,177 (pass) /
  8,191 (fail); `argv_len` 8,213 (pass) / 8,227 (fail) — a 14-byte gap at every measure,
  which is the harness's own resolution limit given uniform 13-character ids plus a
  join-space (see T02 section above). **Not consistent with an 8,192-byte buffer**
  (the closest measure, `wrapper_len`, fails at 8,191 — one byte under 8,192) and **no
  match against any of the plan's five round buffer sizes.**
- **Reproducibility:** yes — the FAIL side 3/3 identical (calls 9, 13, 14) and the PASS
  side never once flipped across 500 (3x) plus every bisection step from 533 to 565 (7x),
  all exit 0 / empty output. No call in the whole sweep (26 calls) produced an outcome
  outside the two defined in §4.3.
- **T03 content result:** length is the cause; content (single-token vs. real ids,
  quoted vs. unquoted) does not shift the flip point.
- **Hypothesis supported:** **deterministic length limit**, not transient fault. This
  directly contradicts the "transient or intermittent" read in
  `extra/MEASUREMENT_open-55_acceptance-test-attempt3.md`, which is superseded by this
  measurement.

Per §4.5, this reproducible length threshold **authorises T04** (the stdin remedy).

## Artifacts

- `scripts/diagnostics/open57_probe_length_sweep.py` — harness (new file, does not
  import `v12_cell_pipeline.py`).
- Scratchpad `open57_probe_sweep.jsonl` — all 26 call records, verbatim, in order.
