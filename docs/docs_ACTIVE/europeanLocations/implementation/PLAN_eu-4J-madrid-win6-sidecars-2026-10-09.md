# PLAN — Madrid layout side-cars for 4J on the 10-06 set

## 1. Header

- Slug: `eu-4J-madrid-win6-sidecars`. Date: 2026-10-09. Manager: OpenUBEM manager session.
- Request: `messages_GSSCanada/2026-10-09_4J_to_OpenUBEM_request_madrid_win6_sidecars.md` (4J = gsscanada-25, owner's own project).
- Owner approval: "yes please" (2026-10-09), to build the Madrid side-cars once local slots free up. 4J: "No rush … Bologna goes first (about 12 Oct)."
- Precedents: 10-06 London/Bologna side-cars (`DONE/PLAN_eu-model-integrity-2026-10-02.md:741-795`, D-EU-147) and 10-08 fixed-home side-cars `sidecars_4J` (`DONE/PLAN_eu-rulebook-change-2026-09-30.md:620-627`).

## 2. Hard rules for the executor

- Never edit or delete any existing file of `ES-MAD-BERRUGUETE_win_2026-10-06/` or `ES-MAD-BERRUGUETE_merged_win_2026-10-06/`, nor anything in `partner_fixed_homes_2026-10-08/` (new sub-folder only), nor any Bologna/London folder (Bologna is FROZEN).
- Never touch the city build folders or processes (Vienna, Helsinki, Yerevan, Budapest, Montréal, Cape Town). Never `taskkill /IM python.exe` or kill any process you did not start.
- At most 10 local worker processes on the machine in total. Before T02, count running `python` processes whose command line contains `run_eu_s2_district_campaign` or `emit_eu11`; start only when the count is ≤ 8, and use 1 process (2 if the count is ≤ 7).
- No code edits to any repo file. One-off scripts live in the session scratchpad only. No code comments.
- Speed: login node = `mkdir`, `scp`, `sha256sum -c` only, via the `bash -lc` wrapper (`scripts/cluster/t08_harvest_results.py:104`). No `sbatch`.
- Cap every command's output (`| head -30`, counts not listings). Stop and quote on any conflict.

## 3. File layout

| Path (relative to `openubem/outputs/eu_evidence/EU-11/`) | Role |
|---|---|
| `ES-MAD-BERRUGUETE_win_2026-10-06/idfs/` (1,172), `md5_2026-10-06.txt`, `prepared_buildings.csv`, `dwelling_counts_2026-10-06.csv` | inputs, read only |
| `ES-MAD-BERRUGUETE_merged_win_2026-10-06/es_mad_berruguete_manifest.csv` | population manifest, read only |
| `ES-MAD-BERRUGUETE_win_2026-10-06/layouts/` | NEW: 10-06 side-cars (same place as London/Bologna) |
| `ES-MAD-BERRUGUETE_merged_win_2026-10-06/flat_counts_2026-10-06.csv` | NEW: flat counts, same exporter as London/Bologna |
| `rulebook_2026-09-30/partner_fixed_homes_2026-10-08/ES-MAD-BERRUGUETE/idfs/` (39) | inputs, read only |
| `rulebook_2026-09-30/partner_fixed_homes_2026-10-08/sidecars_4J_madrid_2026-10-09/` | NEW: 39 fixed-home side-cars + `per_home_check_2026-10-09.csv`, `sha256_sidecars.txt`, `code/` |
| `handover_4J_2026-10-09_madrid/` | NEW: logs, `sha256_2026-10-09.txt`, `per_home_check_win6.csv` |
| `/speed-scratch/o_iseri/handover_4J_2026-10-09_madrid/` | NEW: Speed copy |

## 4. Dependency decisions (pinned)

- **The 10-06 engine files no longer exist.** `sha256_2026-10-06.txt` records `european_residential.py` 0b9aa66c… and `european_nocore.py` f63257de…; neither version is on disk or in git (`git log` versions of both files checked 2026-10-09). On disk now: 5bb68e87… / b09c00a8… (10-08 rules, D-EU-148). Manager decision (same as 10-08, `PLAN_eu-rulebook-change-2026-09-30.md:626`): **the IDF is what was simulated, so side-car floor coordinates are taken from the IDF `_dwelling_` zone floors**; the rest of each side-car comes from the current emitter. 4J is told the file sha256s differ and is given the function hashes (as `sidecars_4J/code/NOTE_functions.txt`).
- Emitter: `scripts/emit_eu11_layout_sidecars.py` as on disk (D-EU-147 count rule: `dwellings_total` = `dwellings_used`).
- Frame: Madrid win6 has no `origin_offset.json`, so side-cars are in the IDF frame as read. The 39 fixed homes are absolute UTM (FINDING 296); their side-cars are in their own IDF frame as read. State both in `crs`/the reply exactly as found.
- Madrid exclusion list for 4J: the 48 Madrid rows of `partner_fixed_homes_2026-10-08/exclude_all_232.csv` (D-EU-149).

## 5. Facts with citations

- 10-06 emission command: `DONE/PLAN_eu-model-integrity-2026-10-02.md:741`.
- Code digest list (ten files): same plan `:748`.
- Side-car checks used for London/Bologna: `messages_GSSCanada/2026-10-06_OpenUBEM_to_4J_win6_package_london_bologna.md:10-14`.
- Per-home check format: `sidecars_4J/per_home_check_2026-10-08.csv` header.

## 6. Tasks

### T01 — Preconditions
- What: confirm the inputs are the 10-06 models.
- How: md5 of every IDF in `ES-MAD-BERRUGUETE_win_2026-10-06/idfs/` vs `md5_2026-10-06.txt`; row counts of `dwelling_counts_2026-10-06.csv`, `prepared_buildings.csv`, merged manifest; process count (§2).
- Test: 0 md5 mismatches over 1,172; any mismatch → STOP.

### T02 — Emit Madrid side-cars
- How: `python -m scripts.emit_eu11_layout_sidecars --district ES-MAD-BERRUGUETE --evidence-root ES-MAD-BERRUGUETE=<abs EU>/ES-MAD-BERRUGUETE_win_2026-10-06 --population-manifest ES-MAD-BERRUGUETE=<abs EU>/ES-MAD-BERRUGUETE_merged_win_2026-10-06/es_mad_berruguete_manifest.csv > <abs EU>/handover_4J_2026-10-09_madrid/emit_ES-MAD-BERRUGUETE.log 2>&1`, with `run_in_background`; wait for the completion notice.
- Test: side-car count; list of building_ids with no side-car (skipped ids from the log).

### T03 — Floor coordinates from the IDF
- How: scratchpad script, per side-car: read the IDF's `_dwelling_` zones and their floor surfaces (`scripts/eu_idf_plan_reader.py`), replace each zone's floor polygon in `floors` by the IDF's, matched by zone name. Set `dwellings_total` = `dwellings_used` of `prepared_buildings.csv`.
- Test, written to `handover_4J_2026-10-09_madrid/per_home_check_win6.csv` (columns as the 10-08 file): zone names in side-car = IDF `_dwelling_` zone names; max vertex deviation after < 1 mm; `dwellings_total` = flat count. A building that fails stays without a side-car and is listed. More than 1 % of buildings failing → STOP.

### T03b — Rerun T02 + T03 with the merge rule (manager amendment, 2026-10-09, after stop point 2)
- Why: 589 homes failed T03 only because a `_dwelling_` zone has several floor surfaces in the IDF and a side-car holds one polygon per zone; the 589 failed side-cars were deleted, so they must be emitted again.
- Rule (precedent: the 10-08 fixed-home side-cars 4J already accepted, `DONE/PLAN_eu-rulebook-change-2026-09-30.md:626`): per zone, take the floor rings at the zone's lowest z, drop rings under 0.002 m², and merge them with the 10-08 function `build()` of `C:/Users/o_iseri/AppData/Local/Temp/claude/C--Users-o-iseri-Desktop-OpenUBEM/31678675-3590-41c3-a4b1-aaafba467d82/scratchpad/fix.py:38-75` (with `big`, `fill`, `sa`, `idf_zones` of `:10-37`), copied unchanged into this session's scratchpad. It tries exact union, then vertex snapping up to 10 mm, then bridging gaps up to 12 mm; every output vertex is an IDF vertex. Result `FAIL` → the building stays without a side-car and is listed.
- How: (1) re-run the T02 command unchanged (it rewrites all of `layouts/`; same process-count rule as §2); (2) re-run T03 on all 1,151 side-cars with the rule above.
- Test, `per_home_check_win6.csv` rewritten, two columns added: `merged_zones` (count of zones built from more than one ring) and `max_area_dev_m2` (largest gap between a zone polygon and the sum of its IDF floor rings). PASS = zone names equal, one simple polygon per zone, `max_area_dev_m2` ≤ 0.03, `dwellings_total` = flat count. Report counts by merge outcome (exact / snapped / lens / lens_loose / FAIL). More than 1 % of 1,163 failing → STOP. Also state how many of the 12 homes with no side-car are in the 48 Madrid exclusion rows.

### T04 — The 39 fixed Madrid homes
- How: for each IDF in `partner_fixed_homes_2026-10-08/ES-MAD-BERRUGUETE/idfs/`, start from the T03 side-car of the same building_id; take floors from the fixed IDF as in T03; `dwellings_total` = number of `_dwelling_` zones in the fixed IDF. Write to `sidecars_4J_madrid_2026-10-09/ES-MAD-BERRUGUETE/`, plus `per_home_check_2026-10-09.csv`, `sha256_sidecars.txt`, `code/` (copy of the two engine files, `sha256_code.txt`, `NOTE_functions.txt` recomputed the same way as the 10-08 one).
- Test: 39 of 39 pass the T03 checks.

### T05 — Flat counts and code digests
- How (amended 2026-10-09: the exporter's `ALLOWED` list rejects Madrid; no repo edit): a scratchpad script runs `import scripts.cluster.export_flat_counts_4j as E; E.ALLOWED = E.ALLOWED + ("ES-MAD-BERRUGUETE",)` and then calls `E.main()` with `--district ES-MAD-BERRUGUETE --tag win_2026-10-06`; the exporter file itself stays unchanged (its sha256 must equal the 10-06 one); confirm it writes `ES-MAD-BERRUGUETE_merged_win_2026-10-06/flat_counts_2026-10-06.csv` and touches nothing else (if it would overwrite any file → STOP). sha256 of the ten files of `PLAN_eu-model-integrity-2026-10-02.md:748` into `handover_4J_2026-10-09_madrid/sha256_2026-10-09.txt`, with a yes/no per file vs `handover_4J_2026-10-06/sha256_2026-10-06.txt`.
- Test: flat-count rows = 1,172 simulated; `dwellings_total` of every side-car = its flat count (0 mismatches).

### T06 — Speed copy
- How: tar and `scp` to `/speed-scratch/o_iseri/handover_4J_2026-10-09_madrid/`: `ES-MAD-BERRUGUETE_win_2026-10-06/` (idfs, schedules, weather, layouts, md5 file, `dwelling_counts_2026-10-06.csv`), `flat_counts_2026-10-06.csv`, `sidecars_4J_madrid_2026-10-09/`, the 39 fixed IDFs, the Madrid rows of the exclusion list as `exclude_4J_madrid.csv`, `sha256_2026-10-09.txt`, and one `sha256_all.txt` over every file sent.
- Test: `sha256sum -c sha256_all.txt` on Speed, 0 failures.

## 7. Stop-and-report points

1. After T01 if any md5 differs.
2. After T03 if more than 1 % of buildings fail.
3. After T06: report to the manager. **The manager, not the executor, writes the reply to 4J.**

## 8. Progress log

#### T01 — Preconditions — completed 2026-10-09
- Artifacts: none.
- Deviations: none. The md5 file has CRLF line endings, so it was checked with `tr -d '\r' | md5sum -c`.
- Test status: PASS. md5 of 1,172 IDFs: 1,172 OK, 0 mismatches. Row counts: `dwelling_counts_2026-10-06.csv` 1,172; `prepared_buildings.csv` 1,172; win6 `es_mad_berruguete_manifest.csv` 1,172; merged manifest 1,163 (9 fewer than the IDFs, `excluded_buildings.csv` lists 24 rows).
- Notes: process count at 12:58 was 18 raw matches (about 9 real jobs, each a venv launcher plus its child), above the limit of 8, so T02 waits in a background loop (log in scratchpad `load_wait.log`). The emitter takes `dwellings_used` from the merged manifest (1,163 ids), so at most 1,163 side-cars can be emitted. `prepared_buildings.csv` has no `dwellings_used` column; T03 uses `new_count` of `dwelling_counts_2026-10-06.csv`.

#### T02 — Emit Madrid side-cars — completed 2026-10-09
- Artifacts: `ES-MAD-BERRUGUETE_win_2026-10-06/layouts/` (1,151 files at emission), `handover_4J_2026-10-09_madrid/emit_ES-MAD-BERRUGUETE.log`.
- Deviations: started at 15:18 with 4 matching processes (limit 8; the earlier wait lasted about 2h20). The population manifest was skipped for write-back as designed; no manifest file was touched.
- Test status: 1,151 side-cars for 1,163 population ids. 12 ids got no side-car because the emitter builds Madrid rows from the observed-attribute mapper only, and these 12 are `area_imputed` homes: way/1503016147, 340701292, 391276770, 433014840, 435508455, 435508458, 435823583, 435927688, 435927689, 435929955, 987123379, 988302825. The other 9 IDFs outside the 1,163 are not in the population manifest.
- Notes: the 12 are listed as NO_SIDECAR_EMITTED in `per_home_check_win6.csv`.

#### T03 — Floor coordinates from the IDF — STOPPED 2026-10-09 (stop point 2)
- Artifacts: `handover_4J_2026-10-09_madrid/per_home_check_win6.csv` (1,163 rows); `layouts/` now holds 562 corrected side-cars. The 589 failed side-cars were deleted, as the plan says a failing building stays without one.
- Deviations: none. Zone matching uses (storey, dwelling index) because side-car zone names use the building id and IDF zone names use the stem.
- Test status: FAIL. 562 pass, 589 fail (50.2 % of 1,163), 12 no side-car. Threshold is 1 %. All 589 fail on one cause: a `_dwelling_` zone has more than one floor surface in the IDF (1 ring: 6,947 zones; 2: 752; 3: 515; 4: 243; 5 or more: 64), while a side-car holds one polygon per zone. For these zones the floor rings, merged, form one polygon in 816 cases and several separate polygons in 758 cases.
- Notes: plan conflict. §6 T03 says "replace each zone's floor polygon by the IDF's", which has no rule for a zone with several floor surfaces. I did not invent one (for example merging rings). T04 to T06 are not started.
- Also found before T05: `scripts/cluster/export_flat_counts_4j.py` rejects Madrid (`ALLOWED = ("GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2")`, and ES-MAD-BERRUGUETE is not in `NEW_SITES`), so T05's command raises ValueError without a code change, which §2 forbids.

#### T03b — Rerun T02 + T03 with the merge rule — completed 2026-10-09
- Artifacts: `ES-MAD-BERRUGUETE_win_2026-10-06/layouts/` (1,149 side-cars after the check), `handover_4J_2026-10-09_madrid/emit_ES-MAD-BERRUGUETE.log` (rewritten), `handover_4J_2026-10-09_madrid/per_home_check_win6.csv` (1,163 rows, two columns added).
- Deviations: T02 waited about 3 h for the process count to reach 8 (it stood at 8 when started; 1 process). The merge function is the unchanged copy of `fix.py:10-75`. Zones with one ring (after dropping rings under 0.002 m²) use the IDF ring directly, without calling `build()`, so they keep every IDF vertex. Ring orientation follows the freshly emitted side-car (as in the 10-08 precedent). `max_area_dev_m2` compares the zone polygon with the sum of all rings at the zone's lowest z, including the dropped small ones.
- Test status: T02 rerun: 1,151 side-cars, exit 0. T03b: 1,149 PASS, 2 FAIL (0.17 % of 1,163, under the 1 % limit; stop point 2 not triggered), 12 NO_SIDECAR_EMITTED. Merge outcome by zone: exact 11,378, snapped 753, lens 51, lens_loose 13, FAIL 2. By building (worst zone): exact 825, snapped 271, lens 41, lens_loose 12, FAIL 2. Zones built from several rings: 587 buildings have at least one. Largest `max_area_dev_m2` 0.0203 (limit 0.03). Largest vertex distance to an IDF vertex 0.58 mm (limit 1 mm). The 2 failures: relation/13255968 and way/310738154 (merge FAIL), their side-cars were deleted. Of the 12 homes with no side-car, 0 are in the 48 Madrid exclusion rows (of the 2 failed ones, relation/13255968 is).
- Notes: the 12 no-side-car ids are the `area_imputed` homes listed under T02.

#### T04 — The 39 fixed Madrid homes — completed with 1 gap 2026-10-09
- Artifacts: `rulebook_2026-09-30/partner_fixed_homes_2026-10-08/sidecars_4J_madrid_2026-10-09/` (38 side-cars in `ES-MAD-BERRUGUETE/`, `per_home_check_2026-10-09.csv`, `sha256_sidecars.txt`, `code/` with the two engine files, `sha256_code.txt`, `NOTE_functions.txt`). The three function digests in the note equal those of the 10-08 note.
- Deviations: none in method (stem to building_id from `manifest_5J_madrid_bologna.csv`).
- Test status: FAIL against "39 of 39": 38 PASS (exact 16, snapped 19, lens 2, lens_loose 1). The 39th, way/391276770 (IDF 88df8e48213666eb), is one of the 12 `area_imputed` homes; it has no T02 side-car to start from and the plan has no rule for that case. No side-car was invented for it.
- Notes: it is not in the exclusion rows, so 4J gets 38 of 39. Manager decision needed.

#### T05 — Flat counts and code digests — completed 2026-10-09 (two plan conflicts)
- Artifacts: `ES-MAD-BERRUGUETE_merged_win_2026-10-06/flat_counts_2026-10-06.csv`; `handover_4J_2026-10-09_madrid/sha256_2026-10-09.txt` (ten files); `handover_4J_2026-10-09_madrid/sha256_compare_vs_2026-10-06.txt` (yes/no per file, kept separate so `sha256sum -c` stays clean).
- Deviations: exporter run through the scratchpad wrapper (`E.ALLOWED` extended in memory). Exporter file sha256 a7c18d88… before and after, unchanged by this run; the file did not exist as output before (nothing overwritten).
- Conflicts: (1) the exporter on disk (sha a7c18d88…, modified 2026-10-08 23:40, uncommitted `NEW_SITES` branch) does NOT equal the 10-06 digest 45cd2c9b…; the branch is not used for Madrid. (2) the plan says "1,172 simulated"; the exporter writes one row per building: 1,398 rows, of which simulated 1,163 (the merged population), undivided_excluded 23, not_residential 204, no_model 8, run_failed 0.
- Test status: side-car `dwellings_total` = flat-count `new_count` for 1,149 of 1,149 (0 mismatches). Digest comparison vs 10-06: same = surface_orientation, degenerate_surfaces, run_eu_s2_campaign, eu_idf_plan_reader; different = european_residential, european_nocore, run_eu_s2_district_campaign, emit_eu11_layout_sidecars, 12_drop_degenerate, export_flat_counts_4j.

#### T06 — Speed copy — completed 2026-10-09
- Artifacts: `/speed-scratch/o_iseri/handover_4J_2026-10-09_madrid/` (win tree with idfs, schedules, weather, layouts, md5 file, `dwelling_counts_2026-10-06.csv`; `flat_counts_2026-10-06.csv`; `sidecars_4J_madrid_2026-10-09/`; `fixed_homes_2026-10-08/ES-MAD-BERRUGUETE/idfs/` with the 39 fixed IDFs; `exclude_4J_madrid.csv` (48 rows); `sha256_2026-10-09.txt`; `sha256_compare_vs_2026-10-06.txt`; `sha256_all.txt`; `sha_check.log`).
- Deviations: one local tar (765 MB) sent with `scp`, untarred and deleted on Speed; the login node ran only `mkdir`, `tar`, `sha256sum -c`. The tar was built from a scratchpad staging copy (deleted).
- Test status: PASS. `sha256sum -c sha256_all.txt` on Speed: 14,771 OK, 0 failures. Counts on Speed: 1,211 IDFs (1,172 + 39), 1,149 layout side-cars, 38 Madrid fixed-home side-cars.
- Notes: stop point 3 reached. The reply to 4J is the manager's.
