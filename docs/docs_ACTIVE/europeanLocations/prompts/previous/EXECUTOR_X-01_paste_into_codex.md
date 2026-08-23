# EXECUTOR PROMPT — slice X-01 — single file to paste into Codex GPT / Antigravity

<!-- Director note (not part of the task): this file is self-contained. The user pastes EVERYTHING
     below the horizontal line as the first message to the external executor, with the working
     directory set to C:\Users\o_iseri\Desktop\OpenUBEM. One file per slice; the director assembles
     the next one (X-02, ...) from the same three walkthrough sections at each dispatch.
     Assembled 2026-08-23 from DIRECTOR_PROMPT §19.3 + WALKTHROUGH §12.2, §12.3 and the X-01 block
     of §12.4, verbatim. -->

---

You are the implementation executor for the OpenUBEM European-locations arc.
Repository: `C:\Users\o_iseri\Desktop\OpenUBEM` (Windows 11, PowerShell).
Interpreter: `python` is NOT on PATH. Use `.venv\Scripts\python.exe` (Python 3.14, openubem 0.1.0)
for every command: `.venv\Scripts\python.exe -m pytest -q tests\...`.
Parent read-only source tree: `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs`

Your task is exactly ONE slice: **X-01**, specified in full at the end of this message,
under the hard rules and the report format included below.

Before writing anything, read in this order and nothing else:

1. `docs/docs_ACTIVE/europeanLocations/WALKTHROUGH_european_locations.md` section 9.3.1 (parent-table reconciliation assertions)
2. `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` sections 11.2 and 11.3, Tables 13 and 14
3. MVP section 9.1 (status vocabulary) and 9.3 (frozen decisions)
4. `tests/` directory listing and one existing test file, to match conventions

Then execute X-01 top to bottom. Do not execute X-02 or X-03.
Do not modify any existing file except to add tests/fixtures; do not touch docs except your one log row.
Do not run `git add/commit/stash/checkout/reset`. Do not use ssh/scp/sbatch or any network call.
Do not invent a value: anything without a source cell is written as UNSOURCED and reported.
If two sources disagree, stop, quote both with file:line, and report — do not choose.

When done, reply with the ten-item evidence pack described below, in order, and nothing else.
Status must be one of: `DOCUMENTED`, `IMPLEMENTED_NOT_TESTED`, `LOCAL_PASS`, `BLOCKED`.
Never write VERIFIED or PASS for anything you did not observe in a command output.

## Hard rules (non-negotiable)

0. **Interpreter.** `python` is not on PATH on this workstation. Every command uses `.venv\Scripts\python.exe` (Python 3.14, `openubem 0.1.0`): `.venv\Scripts\python.exe -m pytest -q tests\test_eu_tabula_loader.py`.
1. **Read before writing.** Read the slice text, then the MVP sections it cites (always §9.1 vocabulary, §9.3 frozen decisions, §11 source alignment), then the walkthrough sections it cites. Do not read the whole arc; do not browse the web unless the slice says so.
2. **Documentation is read-only to you** except the progress-log row (evidence-pack item 8). Never edit MVP §9.2, OVERVIEW/DESIGN docs, root `main.py`, or anything under `docs/docs_main/` or `docs/docs_step*/`.
3. **No `.py` file under `docs/`, ever.** Code goes under `openubem/`, `scripts/`, `tests/`; figures go flat to `openubem/outputs/`.
4. **The GSSCanada tree is read-only.** `C:\Users\o_iseri\Desktop\GSSCanada\…` is a source; copy what you need into the OpenUBEM tree with its checksum, never modify it in place.
5. **No git state changes.** No `git add`, `commit`, `stash`, `restore`, `checkout`, `reset`, `clean`. Report `git status --short` and `git diff --stat`; the user handles git.
6. **No cluster, no network.** No `ssh`, `scp`, `sbatch`, `srun`, no call to `speed.encs.concordia.ca`, no live download in a test. EnergyPlus may run **locally** only when the slice says so and only on the fixture it names.
7. **Never invent a value.** A parameter with no source cell is written as `UNSOURCED` in the provenance record and raised in the report; it is never given a plausible literal. Never reintroduce any figure the citation audit withdrew (`277`, `1,444`, `87.3`, `32–215`, `15–25 %`, `25–40 %`, `8–15 %`, `>35 %`, `15–40 %`).
8. **Never label anything `VERIFIED` or `PASS` without a produced artefact** (a test log, a file, a return code). `IMPLEMENTED_NOT_TESTED` is the honest status for code without a run.
9. **Tests are new files** `tests/test_eu_*.py` / `tests/test_step8_*.py`. Do not modify existing tests to make them pass. Run the named test file, then the full `pytest -q tests/`, and report both counts verbatim (the last recorded baseline is 1,927 passed / 55 skipped on 2026-08-21; re-measure, do not assume).
10. **Every solved error is registered** in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in the house format (exact symptom → cause → fix with `file:line` → source doc) before the slice is reported as done. Search that file first before debugging anything.
11. **Stop on ambiguity.** If two authorities disagree and the MVP precedence (§9.1) does not settle it, stop, quote both passages with file and line, and report. Do not pick one.
12. **No scope creep.** Do not refactor, rename, reformat or "improve" files outside the slice's list, even if they look wrong. Note them in the report instead.

## The evidence pack you return

Your report contains, in this order and nothing else:

1. **Slice ID and status** — one of `DOCUMENTED`, `IMPLEMENTED_NOT_TESTED`, `LOCAL_PASS`, `BLOCKED`.
2. **Files created / modified** — full paths, one per line, with `git diff --stat` output pasted.
3. **Commands run** — verbatim, with working directory, in execution order.
4. **Observed output** — the decisive lines only (test summary line, assertion values, return codes). No full logs; store them under `openubem/outputs/eu_evidence/X-01/` and give the path.
5. **Acceptance assertions** — each assertion from the slice, with the observed value and `PASS`/`FAIL`.
6. **Deviations** — anything done differently from the slice text, with the reason.
7. **Decisions needed** — anything that required a choice the MVP does not make, phrased as a question with the options seen. Empty is a valid answer.
8. **Progress-log row** — the one row appended to Walkthrough Table 4 (§11) **and** to `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv` (same nine fields, same order, UTC timestamp, commit + `dirty` caveat).
9. **Errors registered** — the bullet(s) added to `OpenUBEM_debug_References.md`, or "none".
10. **Single recommended next action.**

A report missing any item is returned for completion, not accepted.

## The slice — X-01: CP0 baseline capture and EU-01 reconciliation loader (no JSON written yet)

- **What.** (a) Capture the repository baseline: `git rev-parse HEAD`, `git status --short`, `.venv\Scripts\python.exe -c "from importlib.metadata import version; print(version('openubem'))"`, `.venv\Scripts\python.exe -m pytest -q tests/` — record all four outputs verbatim under `openubem/outputs/eu_evidence/X-01/`. (b) Write `openubem/data/construction/tabula_reconcile.py` exposing `load_parent_tables(step8_outputs_dir: Path) -> dict[str, pandas.DataFrame]` that reads the three parent CSVs with `#` comment lines skipped, and `assert_parent_invariants(tables) -> dict` that evaluates every assertion of walkthrough §9.3.1 and returns the observed values. (c) Write `tests/test_eu_tabula_loader.py` with one test per §9.3.1 assertion, parametrised over the three folds, reading the parent tables **from a copied fixture** under `tests/fixtures/eu/step8_outputs/` (copy the three CSVs and `archetype_parameter_provenance.md` from `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\outputs_step8\`; record their SHA-256 in `tests/fixtures/eu/step8_outputs/SHA256SUMS`). Include one negative test: a fixture row whose `Code_BoundaryCond` is `ES.SUH` must make `assert_parent_invariants` raise.
- **Why.** EU-01 consumes the parent tables (MVP §11.3). Before any OpenUBEM JSON exists, the loader must prove it reads exactly 24/36/42 rows and refuses every contaminant the parent already refuses.
- **How.** Pandas `read_csv(path, comment="#")`. No network. No EnergyPlus. No changes to any existing module. Paths to the parent tree only in the fixture-copy step and in a docstring; the code takes a directory argument.
- **How to test.** `.venv\Scripts\python.exe -m pytest -q tests/test_eu_tabula_loader.py` then `.venv\Scripts\python.exe -m pytest -q tests/`. Acceptance: every §9.3.1 assertion observed `PASS` on the fixture; the negative test observed to raise; full-suite count reported and compared with the recorded baseline; `git diff --stat` touches only the files named here plus the evidence directory.
- **Stop point.** Report. Do not write `tabula_archetypes_*.json`; the JSON schema and the `c_m`/`n_air_use`/`F_red_htr` join (MVP Tables 13–14) are slice `X-02`.
