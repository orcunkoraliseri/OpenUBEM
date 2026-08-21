# MEASUREMENT — OPEN-13 (E-UTCI-12 / E-UTCI-13) and OPEN-14 (backfill reproducibility) — N09

> **Slug:** `open-13-14_utci-forwards` · **Task:** N09, `PLAN_no-compute-queue-2.md` §6
> **Repo state read:** HEAD `bca92d0a6cdc33923bea8424f1b86ab0f94d82d9` (2026-08-06), verified live with
> `git rev-parse HEAD` at the time of this measurement. All per-file commit hashes below were re-read
> at this same HEAD.
> **Kind:** MEASUREMENT ONLY. No fix applied to anything found broken (§2 rule 2 of the governing plan).

---

## 0. Verdict up front

- **E-UTCI-12 is still true at HEAD, byte-for-byte identical to when it was found** (2026-07-25).
  `pytest -q` on the whole repo still aborts at collection with the same `AttributeError`.
- **E-UTCI-13 is still true at HEAD.** Empirically re-reproduced (not just re-read) with the committed
  offline fixture: a second normalization pass nulls `levels`/`use_class` while `height` survives.
- **OPEN-14 is still true at HEAD.** `git ls-files` confirms no Overture slice exists in the repo for
  any of the 4 E-UTCI-09-affected cells, and `config.FUSION_SOURCES_BY_TARGET` still defaults to `{}`.
  A clean checkout running Stage 6 on those 4 cells reproduces the old flat-field result. Not closed.
- **No round-1 "fixed the day after it was named" pattern found for any of the three.** All three
  defect-introducing files (`height_cache.py`, `overture_fetcher.py`, `tests/test_draw_methods.py`,
  `openubem/semantic/imputation.py`, `openubem/semantic/draw_methods.py`) have had **zero commits**
  since the commit that either introduced or last touched the defect — checked by `git log --oneline`
  per file, not assumed.

---

## 1. Search space — six files, all six opened (§5.5 / how-to-test c)

| # | File | Opened | What it contributed |
|---|---|---|---|
| 1 | `docs/PROJECT_CHECKLIST.md` | Yes, lines 800-870 read in full | CP-C closing summary for the height-backfill sub-plan; confirms E-UTCI-11/12/13 disposition at arc close |
| 2 | `docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md` | Yes, lines 130-150, 930-950, 1200-1220 read | OPEN-13/OPEN-14's register-level framing, both still marked 📄 |
| 3 | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-05_defect-id-sweep.md` | Yes, lines 95-225 read | Independent 2026-08-06 ID sweep; confirms E-UTCI-12/13 status unchanged since arc close, confirms no duplicate with E-UTCI-11 |
| 4 | `docs_DONE/OUTDOOR/UTCI/UTCI_CHECKLIST.md` | Yes, lines 1-92 read | Arc-level defect ledger; E-UTCI-12/13 both still shown OPEN, forwarded out of the arc |
| 5 | `docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md` | Yes — read in full (2038 lines): §0 checklist, §5 facts, §7 progress log excerpts, §8 error log (E-UTCI-11/12/13/14 in full), §10 (reproduction procedure), §11 (closing statement) | The defining site for all three items; §8's E-UTCI-12/13 entries and §10 are the primary evidence used below |
| 6 | `docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md` | Yes, lines 60-100 and 4385-4410 read | Parent arc's own defect ledger and closing note; confirms E-UTCI-13 forwarded to "a future Stage-1 data-acquisition arc" |

No file outside this set was needed or read for OPEN-13/OPEN-14's content. Everything below that is not
a citation to one of these six is a direct HEAD code/data read, cited by `path:line`.

---

## 2. E-UTCI-12

**One sentence:** `tests/test_draw_methods.py:645` references `openubem.semantic.imputation._draw_tier`
at class-body (import) time, but `imputation.py` has never defined that attribute, so any bare
`pytest -q` on the whole repo aborts at *collection* rather than merely failing one test.

**Defining `path:line`:** `docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md:1552-1571`
(error-log entry), evidence line quoted there: `tests/test_draw_methods.py:645`.

**Last recorded status and date:** 🔄 **OPEN, forwarded** — found 2026-07-25 at CP-A (incidentally, while
the manager ran the full suite for an unrelated check), reconfirmed unchanged in the arc checklist
(`UTCI_CHECKLIST.md:50`, `docs_DONE/.../PLAN_utci_microclimate_implementation.md:80`), and reconfirmed
again 2026-08-06 by the independent defect-ID sweep (`MEASUREMENT_open-05_defect-id-sweep.md:118`). No
document disagrees on the status — all four sightings say OPEN/forwarded, never claim it fixed.

**Is the mechanism still present in current code — HEAD citation:**

```
$ grep -n "_draw_tier" openubem/semantic/imputation.py
(no output — the attribute does not exist)

$ ./.venv/Scripts/python.exe -m pytest -q
...
_________________ ERROR collecting tests/test_draw_methods.py _________________
tests\test_draw_methods.py:645: in <module>
    class TestNoEUILeakage:
tests\test_draw_methods.py:645: in TestNoEUILeakage
    imp._draw_tier,
    ^^^^^^^^^^^^^^
E   AttributeError: module 'openubem.semantic.imputation' has no attribute '_draw_tier'
=========================== short test summary info ===========================
ERROR tests/test_draw_methods.py - AttributeError: module 'openubem.semantic....
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 47.39s
```

Re-run at HEAD `bca92d0`, byte-identical failure mode to the 2026-07-25 finding. **Still true.**

`git log --oneline -- tests/test_draw_methods.py` → single commit, `ef19141` (the same fusion/elevators
ship that also introduced E-UTCI-11's `test_fusion.py`). `git log --oneline -5 -- openubem/semantic/imputation.py`
→ most recent touch is `3a925f9` (the height-backfill/UTCI arc itself, which added `_fusion_tier`'s body
but never touched `_draw_tier`); before that `0df422e`, `03e2121`, `fe05509` — none of which is a draw-tier
commit. **Neither file has moved since the defect was named. This is not the round-1 "fixed the day
after" pattern** — it is untouched, not silently repaired.

**What is actually built, for context (not part of the defect, but explains why the gap persists):**
`openubem/semantic/draw_methods.py:1-19` (docstring, unchanged since `ef19141` per `git log --oneline`)
states plainly: *"this module is imported by nothing in the default `impute_missing` call graph until a
future task (T07) wires `_draw_tier` into `openubem/semantic/imputation.py`'s `_CANONICAL_TIER_ORDER` /
`_TIER_HANDLER_NAMES`. Until then, importing this file or setting `config.IMPUTE_DRAW_METHOD_BY_TARGET`
has zero effect on any production path."* The six draw methods this module implements are exactly
register item **OPEN-17**'s subject ("6 variance-preserving draw-tier imputers built, off"). E-UTCI-12
and OPEN-17 are the same underlying gap seen from two angles: one names the missing router function as a
collection-time test defect, the other names it as an undecided promotion question. **This is an
observation, not a merge of the items** — the register's own governing rule for OPEN-15/16/17 already
treats OPEN-17 as a promotion decision, and this measurement does not alter that framing.

**What would need to be measured before it could be planned:** whether the project wants the draw tier
enabled at all — the exact question N10 assembles for OPEN-15/16/17. If the answer is yes, the fix is to
implement `_draw_tier` in `imputation.py` (mirroring what T07 did for `_fusion_tier`, same
`_TIER_HANDLER_NAMES` pattern). If the answer is no, the fix is to correct/skip
`tests/test_draw_methods.py`'s collection-time reference rather than leave the whole suite unable to
collect. Either way, that decision — not a code trace — is the prerequisite, and it is already the
subject of a separate task in this queue (N10).

---

## 3. E-UTCI-13

**One sentence:** the height-backfill cache (`height_cache.py::pull_overture`) writes
`overture_fetcher.fetch_overture()`'s **already-normalized** output to disk, but
`fusion.OvertureSource.join` re-reads the cache through `fetch_overture(slice_path=...)` again, which
re-applies `_normalize()` a second time — and because the raw-schema columns `_normalize()` looks for
(`num_floors`, `class`) no longer exist in the once-normalized frame, `levels` and `use_class` silently
come back null on every cached re-read, while `height` survives only because its column name happens to
be identical before and after normalization.

**Defining `path:line`:** `docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md:1489-1515`
(error-log entry). Code sites: `openubem/acquisition/height_cache.py:93-118` (`pull_overture`, caches
`fetch_overture()`'s return value directly at line 116: `layer.to_parquet(_cache_path(cell))`);
`openubem/semantic/fusion.py:199-211` (`OvertureSource.join`, re-invokes
`fetch_overture(slice_path=getattr(cfg, "FUSION_OVERTURE_SLICE_PATH", None), ...)` at line 208);
`openubem/acquisition/overture_fetcher.py:32-58` (`fetch_overture` always ends by calling
`_normalize(raw)` at line 58, unconditionally, regardless of whether `raw` is already normalized);
`openubem/acquisition/overture_fetcher.py:111-127` (`_normalize`, reads `num_floors`/`class` — line 116,
118 — which are absent from an already-normalized frame, producing `NaN`/`None`).

**Last recorded status and date:** 🔄 **OPEN, deliberately unfixed** — found at T06/CP-B, 2026-07-25, by
the T04-T06 executor, promoted to a numbered defect by the manager the same day. Reconfirmed unchanged
in `UTCI_CHECKLIST.md:51`, the parent plan's closing note (`PLAN_utci_microclimate_implementation.md:4401-4403`),
`PROJECT_CHECKLIST.md:816-817`, and the 2026-08-06 defect-ID sweep
(`MEASUREMENT_open-05_defect-id-sweep.md:119`). All four sightings agree: disposition is "out of scope,
forwarded to whichever arc next touches `height_cache.py`" — never claimed fixed.

**Is the mechanism still present in current code — HEAD citation, empirically re-derived (not just
read):**

```
$ ./.venv/Scripts/python.exe scratchpad/n09_verify_eutci13.py
PASS 1 (direct fetch_overture on raw committed slice):
           id  height  levels   use_class
0  overture-A    30.0       8      office
1  overture-B    12.0       3  apartments
levels non-null: 2 / 2
use_class non-null: 2 / 2

PASS 2 (fetch_overture re-reading the cached, already-normalized frame -- simulates
fusion.OvertureSource.join re-reading pull_overture's cache):
           id  height  levels use_class
0  overture-A    30.0     NaN      None
1  overture-B    12.0     NaN      None
levels non-null: 0 / 2
use_class non-null: 0 / 2
height non-null: 2 / 2 (height column name is stable across both passes)
```

The script (kept in the session scratchpad, not under `docs/` or `openubem/`, per hard rule 14) calls
the real `fetch_overture()` twice against the real committed fixture
`openubem/data/fixtures/fusion/overture_testcell_slice.parquet` — first directly (simulating what
`pull_overture` caches), then again against the first pass's own output written to a temp parquet
(simulating `OvertureSource.join`'s re-read of that cache). `levels` and `use_class` go from fully
populated to fully null on the second pass; `height` alone survives. This is not a re-read of the arc
document's claim — it is an independent empirical reproduction of the same mechanism at HEAD, zero
network, zero EnergyPlus. **Still true.**

`git log --oneline -- openubem/acquisition/height_cache.py` → single commit, `3a925f9` (the commit that
created the file, same commit the arc closed under). `git log --oneline -- openubem/acquisition/overture_fetcher.py`
→ single commit, `ef19141` (predates the height-backfill arc; `_normalize`'s unconditional re-application
is original behaviour, not something the backfill arc introduced or was asked to fix). **Neither file has
moved since the defect was named or since the file was created — no round-1 "fixed and forgotten"
pattern here either.**

**Severity, as recorded and unchanged:** low today (this plan's dependency decision restricts fusion to
`height_m` only, and `height`'s column name happens to survive both passes — proven empirically above,
not merely asserted), medium for whoever next reuses the cache for `levels` or `use_class`.

**What would need to be measured before it could be planned:** nothing further needs measuring — the
mechanism, its cause, and its blast radius are already fully characterized (this section's own
empirical reproduction closes that gap). What remains is a **disposition decision**, not a measurement:
whether to fix `height_cache.py` to cache the pre-normalization ("raw") frame instead, or to stamp the
cached frame with a schema marker `_normalize()` can detect and skip (both options are already named in
the arc doc, `DONE-PLAN_e-utci-09_height_backfill.md:1514-1515`) — and that decision belongs to whichever
arc next touches `height_cache.py` or Stage-2 imputation, per the existing forwarding disposition. This
task does not take that decision (remediation is forbidden here).

---

## 4. OPEN-14 — backfill reproducibility from a clean checkout

**Register text (verbatim, `INVESTIGATION_open-items-register.md:936-940`):** *"The fix lives in the
mechanism rather than in committed data. Anyone rebuilding Stage 6 from a fresh clone does not get the
backfilled heights. This is a reproducibility defect in shipped inputs... it silently invalidates a
rebuild rather than degrading a known cell."*

**Concrete, mechanical answer:**

1. **Which files does Stage 6 need for the 4 affected cells** (`nyc_suburban`, `nyc_rural`,
   `austin_centre`, `austin_rural`) **to get real heights instead of a flat field:**
   - A cached Overture slice per cell at `~/.openubem/heights/overture_<cell>.parquet` (+
     `manifest.json`), produced by `height_cache.pull_overture(cell)`.
   - `config.FUSION_SOURCES_BY_TARGET` set to `{"height_m": ("overture",)}` and
     `config.FUSION_OVERTURE_SLICE_PATH` pointed at that cell's cached parquet (env-overridable:
     `OPENUBEM_FUSION_OVERTURE_SLICE_PATH`).

2. **Which are absent from a clean checkout — `git ls-files` evidence, re-run live at HEAD:**

   ```
   $ git ls-files | grep -i "nyc_suburban\|nyc_rural\|austin_centre\|austin_rural" | grep -i "overture\|height"
   (no output — none of the 4 affected cells has a tracked Overture slice or cached height file)

   $ git ls-files -- "openubem/data/fixtures/fusion/*"
   openubem/data/fixtures/fusion/LICENSES.md
   openubem/data/fixtures/fusion/__init__.py
   openubem/data/fixtures/fusion/assessor_testcell.gpkg
   openubem/data/fixtures/fusion/lidar_testcell_ndsm.tif
   openubem/data/fixtures/fusion/overture_nyc_centre_slice.parquet
   openubem/data/fixtures/fusion/overture_testcell_slice.parquet
   ```

   The only two committed Overture parquet fixtures are test fixtures for a synthetic `testcell` and for
   **`nyc_centre`** — one of the 8 already-healthy cells, unrelated to the 4 affected ones. **None of
   `nyc_suburban`, `nyc_rural`, `austin_centre`, `austin_rural` has any committed Overture artifact.**
   `~/.openubem/heights/` (the real cache location, `config.py:161-163`) is outside the repository
   working tree entirely (under the user's home directory), so it is not a `.gitignore` question — it is
   simply never inside the checkout to begin with.

3. **Which script produced the (uncommitted) artifacts, and does it still run from a clean checkout:**
   `openubem/acquisition/height_cache.py::pull_overture` (line 93) — a manual, one-off, network-calling
   entry point, explicitly not reachable from any test/CI/pipeline path by design (docstring, line 94-102,
   unchanged since `3a925f9`). It requires live network access to the pinned Overture release
   `s3://overturemaps-us-west-2/release/2026-06-17.0/...` (`height_cache.py:42`). Whether it "still runs"
   from a clean checkout is therefore gated by CLAUDE.md's own live-network restriction (§5.3, still
   closed) and by whether that specific 2026-06-17.0 release remains fetchable — **neither was tested
   here**, because doing so would itself be the one-off network exception the governing plan (§2 rule 3)
   does not authorize for a measurement task; this is reported as an unknown, not assumed either way.

4. **Config default, re-confirmed live at HEAD** (`openubem/config.py:100,141`):
   ```
   IMPUTE_ENABLED_TIERS: tuple = ("fusion", "spatial", "statistical")
   FUSION_SOURCES_BY_TARGET: dict = {}
   ```
   `fusion` sits in `IMPUTE_ENABLED_TIERS` (added at CP-B, per the arc's own ruling — not a
   contradiction, since `precedence_for()` still returns `[]` whenever `FUSION_SOURCES_BY_TARGET` is
   empty for a given target, regardless of tier-list membership). With the shipped default `{}`, `fuse()`
   is a guaranteed no-op for `height_m` on a clean checkout, exactly as `DONE-PLAN_e-utci-09_height_backfill.md:1954`
   states.

**Verdict: OPEN-14 is not closed. It is exactly as true at HEAD as when it was written.** A clean clone
running Stage 6 on the 4 affected cells reproduces the pre-backfill flat-field result
(`svf_mean = 1.0000`), because neither of the two ingredients the fix depends on (a cached Overture
slice for those 4 cells, and non-default fusion config) is present in the checked-out tree. No committed
file resolves this — the two committed Overture fixtures found above are for a different cell
(`nyc_centre`, already healthy) and a synthetic unit-test fixture (`testcell`), neither of which the
Stage-6 pipeline's real cell configs point at.

**No contradiction found between the arc's own documents on this point** — `PROJECT_CHECKLIST.md:825-837`,
the sub-plan's own §10, and the register's OPEN-14 entry all describe the identical mechanism and agree
it is open. The only place a surface tension exists is the `IMPUTE_ENABLED_TIERS`/`FUSION_SOURCES_BY_TARGET`
pair described in point 4 above, and that tension is explicitly resolved by the arc's own CP-B ruling and
E-UTCI-16 fix (comment corrected 2026-07-25) — not a live contradiction, just something worth citing
precisely rather than glossing.

---

## 5. How-to-test results (plan §6, N09)

**(a) Both E-UTCI IDs carry a HEAD citation, not only an arc-doc citation.** PASS.
- E-UTCI-12: `grep -n "_draw_tier" openubem/semantic/imputation.py` (no output) +
  `pytest -q` full-suite collection-abort transcript, both re-run live at HEAD `bca92d0`, §2 above.
- E-UTCI-13: live re-execution of `fetch_overture()` twice against the real committed fixture, §3 above
  — an empirical reproduction, stronger than a citation alone.

**(b) OPEN-14's verdict names the specific artifact and its git-tracked status (`git ls-files` output
quoted).** PASS — §4 point 2 above quotes the literal `git ls-files` output for both the 4 affected
cells (empty result) and the fusion fixtures directory (2 unrelated fixtures, no affected-cell slice).

**(c) State explicitly which of the six files you opened and which you did not, and why.** PASS — all
six opened; table in §1. None was skipped.

---

## 6. Artifacts

- This report: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13-14_utci-forwards.md`.
- Verification script (scratchpad only, not a deliverable, not under `docs/` or `openubem/`):
  `scratchpad/n09_verify_eutci13.py` equivalent, executed from the session scratchpad at
  `C:\Users\o_iseri\AppData\Local\Temp\claude\...\scratchpad\n09_verify_eutci13.py` — reproducible by
  re-running `fetch_overture(slice_path=...)` twice in sequence against
  `openubem/data/fixtures/fusion/overture_testcell_slice.parquet`, per §3's transcript.
- No CSV artifact was needed — every headline claim in this report is either a `path:line` quote, a
  literal command transcript, or a literal `git log`/`git ls-files` output, all reproduced above verbatim.
