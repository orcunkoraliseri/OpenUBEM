# MEASUREMENT — OPEN-38 x OPEN-56: is volume degeneracy associated with failure, at full coverage?

Joins T02's per-zone volume table (`open56_volume-stub-zones_2026-08-21b.csv`) to T06's per-run
error census (`open38-09-45_err-census-buildings_2026-08-21b.csv`) on `(cell, stem)` — the sim-run
level, 8,160 rows, which both tables share natively. Script:
`scripts/analysis/open38-56_volume-degeneracy-vs-failure_2026-08-21b.py`. Output:
`openubem/outputs/comparisons/open38-56_volume-degeneracy-vs-failure_2026-08-21b.csv`.

## C14 — partition

- **(a) fatal: 7.** **(b) OPEN-09 signature: 16.** **(c) everything else: 8,143.**
- Overlap between (a) and (b): **6** runs are both fatal and carry the OPEN-09 signature (only 1 of
  the 7 fatals is fatal without that signature).
- `|a| + |b| + |c| − overlap(a,b) = 7 + 16 + 8,143 − 6 = 8,160` — confirmed, partitions the corpus
  exactly.

## Volume-degeneracy measures per group

| Group | n | any-zone-stubbed | all-zones-stubbed | mean frac_stub |
|---|---|---|---|---|
| (a) fatal | 7 | 7/7 (100%) | 7/7 (100%) | 1.000000 |
| (b) OPEN-09 signature | 16 | 16/16 (100%) | 7/16 (43.75%) | 0.916714 |
| (c) everything else | 8,143 | 8,143/8,143 (100%) | 7,762/8,143 (95.32%) | 0.991732 |

## C15 — headline

**"Any zone stubbed" is 100% in all three groups — fatal, OPEN-09-signature, and everything else.
A constant cannot discriminate anything: volume degeneracy cannot discriminate failure in this
corpus.** The "all zones stubbed" rate does vary (100% / 43.75% / 95.32%) but does not track failure
monotonically — the failing group (b) has the *lowest* all-stubbed rate, below the non-failing group
(c). At n=7 and n=16 this is not a usable signal either way. This supersedes the predecessor's
partial-coverage (23/44 fatals, 47/200 controls) harvest result per F2: at 100% coverage on the
adopted run, the stub is a near-universal background condition, not a fatal-run marker.
