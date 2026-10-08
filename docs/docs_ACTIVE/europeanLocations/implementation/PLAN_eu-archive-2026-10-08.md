# PLAN — Archive the European-locations arc into docs_DONE/SETUP and repair every link to it (2026-10-08)

- **Slug:** `eu-archive-2026-10-08`
- **Author:** director (manager session), 2026-10-08 17:30. Executor: fresh Sonnet sessions (T01–T02, then T03–T05).
- **Owner request (2026-10-08, verbatim):** "can you check if anything left under this one ...\europeanLocations otherwise i will relocate under ...\docs\docs_DONE\SETUP as a completed project" → director: "may I move it myself and repair all the links in the same pass?" → owner: "yes yo udo it".
- **Rule source:** `docs/PROJECT_CHECKLIST.md:182-190` (archiving rule: not finished until every live citation is repaired; standing exclusions; sweep `.py` too, `:156`).
- **Old path:** `docs/docs_ACTIVE/europeanLocations/` · **New path:** `docs/docs_DONE/SETUP/europeanLocations/` (nothing renamed).
- **This plan file moves with the folder at T02.** After T02 read and append to it at `docs/docs_DONE/SETUP/europeanLocations/implementation/PLAN_eu-archive-2026-10-08.md`.

## 1. Hard rules for the executor

1. Never touch `openubem/outputs/eu_evidence/**` — it holds the FROZEN Bologna folder `IT-BOL-GALVANI2_win_2026-10-06/` and `rulebook_2026-09-30/partner_fixed_homes_2026-10-08/` that another project still reads. Read-only, no edits, no moves.
2. Never touch anything on Speed. No simulations, no `sbatch`.
3. Never delete anything. The move is one directory rename; if it fails, STOP and report the exact error — no copy-then-delete, no partial move, no retry with force.
4. Never `taskkill /IM`; stop a process only by its own PID, and only one you started.
5. Never edit root `main.py`, `CLAUDE.md`, any `docs/docs_main/**`, any `docs/docs_DONE/**` file other than inside the moved folder for T01's closure lines (which you write BEFORE the move), or `docs/docs_TODO/layoutgenerator/**`.
6. `docs/PROJECT_CHECKLIST.md` journal blocks are append-only: do NOT rewrite old paths there; add one migration-table row (T05) instead.
7. Cap every command's output (`| head -40`, `grep -c`, `--stat`). Report counts and file:line, not file contents.
8. Do not propose alternatives — execute. If something here is ambiguous, STOP and quote it.

## 2. Tasks

### T01 — Close the open bookkeeping (before the move)

**What.** Add a one-line closure marker; change no other text.
- Top of each of these four plans, directly under the `# PLAN —` title line, insert:
  `> **CLOSED 2026-10-08 — arc archived.** Tasks without a completed entry were not run; superseded by the owner's stop rulings D-EU-148 / D-EU-149 (2026-10-08).`
  Files: `implementation/PLAN_eu-bent-walls-2026-09-30.md`, `implementation/PLAN_eu-floor-division-residual-2026-09-29.md`, `implementation/PLAN_eu-rulebook-change-2026-09-30.md`, `implementation/PLAN_eu-model-integrity-2026-10-02.md`.
- `CHECKLIST_european_locations_v5.md`: on each line that starts with `- [ ]` (8 lines today, e.g. `:58`, `:63`, `:78`, `:176`, `:178`, `:188`, `:193`, `:194`), append ` — **closed at archive 2026-10-08, not pursued (D-EU-148/149).**` Do not tick the box.
- `STATE_european_locations_v5.md` and `CHECKLIST_european_locations_v5.md`: insert directly under the first `#` title line: `> **ARCHIVED 2026-10-08** to `docs/docs_DONE/SETUP/europeanLocations/`. Final results: `results/EU11_results_2026-10-08_*` (Madrid 68.774 / 1,119 · Lyon 57.810 / 501 · London 68.307 / 1,215 · Bologna 58.164 / 1,035 · fleet 62.626 / 3,870). Bologna files under `openubem/outputs/eu_evidence/EU-11/` stay frozen until the GSS Canada 4J session reports done.`

**Why.** Four plans and eight checklist boxes look open but were overtaken by the owner's stop rulings; a reader of the archive must see that.
**How to test.** `grep -c "CLOSED 2026-10-08" implementation/PLAN_eu-{bent-walls,floor-division-residual,rulebook-change,model-integrity}*.md` → 1 each; `grep -c "^- \[ \].*closed at archive" CHECKLIST_european_locations_v5.md` equals `grep -c "^- \[ \]" CHECKLIST_european_locations_v5.md`.

### T02 — Baseline the tests, then move the folder

**What / How.**
1. Find the tests that name the folder: `grep -rlI "europeanLocations" tests | head -40`. Run them: `python -m pytest <those files> -q -p no:cacheprovider 2>&1 | tail -15`. Record pass / fail / error counts and the names of any failing tests (this is the "before").
2. Record before-move: file count (`find docs/docs_ACTIVE/europeanLocations -type f | wc -l`, expect ~452) and size (`du -sb`).
3. Confirm the target does not exist: `ls docs/docs_DONE/SETUP/europeanLocations` must fail.
4. Move with one PowerShell call from the repo root: `Move-Item -LiteralPath "docs\docs_ACTIVE\europeanLocations" -Destination "docs\docs_DONE\SETUP\europeanLocations"`. If it errors (e.g. a file is open), STOP and report the message verbatim — rule 3.
5. After: the same file count and byte size at the new path; old path absent.

**Why.** The owner asked for the move; the before-test run lets T04 separate breakage we cause from failures that already existed.
**How to test.** Counts before = after; `ls docs/docs_ACTIVE/europeanLocations` fails.

**STOP after T02** — append T01 and T02 progress entries to this plan at its NEW path, then report.

### T03 — Repair every live link to the old path

**What.** Every live file outside the moved folder that names the old path must name the new one.
Search pattern (both slash styles, doubled backslashes in JSON/Python strings, `/` or `\` after `docs`): `docs[/\\]+docs_ACTIVE[/\\]+europeanLocations`. Also look for relative joins such as `"docs_ACTIVE", "europeanLocations"` or `docs_ACTIVE" / "europeanLocations"` (pathlib): `grep -rnI "docs_ACTIVE.\{0,6\}europeanLocations"`.
Scope (live, repair): `scripts/**`, `tests/**`, `openubem/**` EXCEPT `openubem/outputs/eu_evidence/**` (rule 1), `docs/docs_EXPLANATION/**`, `docs/docs_ACTIVE/**`, any other `docs/` file outside the exclusions.
Excluded (never edit): `openubem/outputs/eu_evidence/**`, `docs/docs_DONE/**` (includes the moved folder itself — its internal links are resolved by the migration-table row), `docs/docs_main/**`, `docs/docs_TODO/layoutgenerator/**`, `docs/PROJECT_CHECKLIST.md` journal text (rule 6), root `scratchpad/**`, `.git/**`.
**How.** Replace `docs_ACTIVE` + separator + `europeanLocations` with `docs_DONE` + same separator + `SETUP` + same separator + `europeanLocations`, keeping each file's own separator style (and doubled backslashes where the file uses them). For pathlib/`os.path.join` part lists, insert the `"SETUP"` part and change `"docs_ACTIVE"` to `"docs_DONE"`. No other text changes. Use a small script in your scratch area, not under `docs/`.
**Why.** After the move these links point to nothing (measured before the move: about 24 scripts, 5 tests, 5 data JSON files, 4 viewer `sources.json`, 3 docs).
**How to test.** The search above over the live scope returns 0 lines; list each repaired file with its replacement count.

### T04 — Re-run the tests

**What.** Re-run exactly the T02 test files. Pass / fail / error counts must be the same or better than the T02 "before"; any test that passed before and fails now is a regression caused by this plan — fix the path it uses (only path edits allowed) and re-run.
Also `python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('openubem/data/**/*.json',recursive=True)+glob.glob('openubem/outputs/3D/*/sources.json')]; print('json ok')"` must print `json ok`.
**How to test.** Report before vs after counts on one line each.

### T05 — Register the move

**What.**
1. `docs/PROJECT_CHECKLIST.md`: in the path migration table (`:15-27`), add one row after the TechTransfer row:
   `| `docs/docs_ACTIVE/europeanLocations/` *(archived 2026-10-08, nothing renamed)* | `docs/docs_DONE/SETUP/europeanLocations/` |`
2. Append the T03–T05 progress entries to this plan.
**How to test.** `grep -c "docs_DONE/SETUP/europeanLocations" docs/PROJECT_CHECKLIST.md` ≥ 1.

## 3. Stop-and-report points

- **CP-1** after T02: counts before/after, test baseline.
- **CP-2** after T05: repaired file list with counts, the 0-line search result, test before/after, JSON check.

## 4. Progress log

(executor appends `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes)
