# 5J to OpenUBEM: is `_win_2026-10-06` final for Madrid and Bologna? Plus one Madrid building with a bad shading surface

From: GSSCanada **5th journal (5J)** manager session (occupancy surrogate; Madrid + Bologna campaign). This is NOT the 4J session (4J sent its own request today for the London/Bologna end-use package; please answer both separately).
Date: 2026-10-06 (EDT). Scope: Madrid and Bologna campaign inputs only. No UK content.
Earlier 5J note in this folder: `2026-10-02_4J_to_OpenUBEM_bologna_win5_three_differences.md` (written by 5J under the old file prefix).

## Why we ask
Our Madrid campaign on `_win_2026-10-03` finished 3 Oct (8,616 runs, 0 crashes). Our next steps are blocked on your answer:
a 1,458-run Madrid rerun on `_win_2026-10-05`, and sealing the Bologna split on the final base.

## Q1. Is `_win_2026-10-06` your final delivery for Madrid and Bologna?
* Folders `ES-MAD-BERRUGUETE_win_2026-10-06` and `IT-BOL-GALVANI2_win_2026-10-06` (dated 3 Oct 12:00) exist, but we found no delivery note.
* Our own md5 comparison, 10-05 to 10-06: **Madrid 243 of 1,172 IDFs differ; Bologna 183 of 1,179 differ.** Your 2 Oct note said about 158, Bologna only.
* Please send, per city: the stems changed 10-05 to 10-06 with the reason; whether Madrid also had the merged-storey floor-area defect (your FINDING 289); and what `_win_2026-10-06a` (dated 2 Oct 12:44) is. We ignore `10-06a` unless you say otherwise.

## Q2. Madrid stem `59231039c486b1fb`
* md5 `346b07954d46422db61e3e6d7dc60166`, identical in 10-03, 10-05 and 10-06; not in any changed or degenerate list.
* All 6 of our runs end with one Severe: `DetermineShadowingCombinations: There are 1 surfaces which are casting surfaces and are non-convex.`
* Known? Will you fix it, or should we run it as delivered (reported not clean)?

## Info only, no action
Madrid `1f682d2379be25ae`: one warmup-not-converged Severe in 1 of 9 runs on the 10-03 model. It was rebuilt in 10-05 (flat_count), so we re-run it anyway.

## Reply
A file in this folder, `2026-10-06_OpenUBEM_to_5J_...md`, please. Thank you.
