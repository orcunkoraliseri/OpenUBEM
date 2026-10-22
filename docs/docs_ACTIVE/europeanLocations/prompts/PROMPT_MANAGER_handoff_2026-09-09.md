# Manager handoff — opened 2026-09-09, 13:00 EDT; **reopened 2026-09-29 for the EU floor-division residual plan** — read the 2026-09-29 status update first

- **Role of the session receiving this**: **manager / director**. Reads docs, writes and audits plan
  docs, dispatches executors. **Never writes feature code.**
- **Two threads.** Thread A is ours and is **closed**. Thread B is a peer session's campaign; as of
  2026-09-11 the user changed the plan and we now **help that session whenever it asks**, instead of
  only recording it. **Thread C (2026-09-29) is ours and live: the EU floor-division residual plan.**
  Read the 2026-09-29 status update right below first — it is the current truth.
- **Paste everything below the rule into the new session.**

---

## 🟢 START HERE — fresh manager session, updated 2026-10-12 16:37 local (handover to a new session; read only this box first)

**2026-10-12 16:37 — 6J SIX-CITIES UPDATE COMPLETE; SESSION CLOSED BY OWNER.** The new-cities delivery to 6J is finished: six cities simulated and checked (60/60), 6J's five questions answered, both follow-ups closed. Only leftover: the Bologna 6J copy. 4J's session is also closed while its Speed runs go on; its "Bologna done" message will come only after the owner reopens 4J. **A new manager session starts here:** wait for that message, then make the Bologna 6J copy and send 6J (gsscanada-8e) the path. Owner's open calls unchanged (Seoul leftovers, Yerevan Armstat licence, Budapest brochure check). Next free D-EU-169 / FINDING 299.

**2026-10-12 15:55 — WAITING ON 4J ONLY.** 6J confirmed both follow-ups closed (time labels on our corrections fixed to 15:38). Nothing running, nothing owed to 6J except the Bologna copy. **The only open step:** when 4J (gsscanada-25) reports Bologna done (NO DATE since 2026-10-13: 4J stopped its Bologna C2 run, will remake diaries and re-run; the old ~20 Oct is void), the Bologna freeze ends; then make the Bologna 6J copy (go given 2026-10-08) and message 6J (gsscanada-8e) its path. Next free D-EU-169 / FINDING 299. All-cities artifact WiykxBch12qHNpnYGxjaY3 v22 (two new status cards: 6J answers sent, Bologna copy waiting); local copy `ALL_CITIES_2026-10-12.html` refreshed.

**2026-10-12 15:37 — SIX CITIES DONE AND HANDED TO 6J (supersedes the 12:30 entry below).** Owner: "reply to 6J, no need to ask". Next free D-EU-169 / FINDING 299.
- **Final check:** F01 60/60 pass (common plan §8 line ~516); F02 facts audited (line ~457). Plan wording nits only: check 2 should count S1 too, checks 4 and 8 name non-existent fields.
- **6J:** asked five questions (`messages_GSSCanada/2026-10-12_6J_to_OpenUBEM_six_cities_received.md`); answered in `messages_GSSCanada/2026-10-12_OpenUBEM_to_6J_six_cities_answers.md`, gsscanada-8e notified by SendMessage. This single reply covers stop-point 5.
- **6J follow-ups (15:38):** Montréal construction line in our reply was wrong (page card right: CSDDRD to 2011, Québec 2012 code after, donor SE only g-value/thermal bridges); reply corrected in place, 6J told. **Bologna 6J copy: go already given 2026-10-08 (6J go message item 3) — make it as soon as 4J reports Bologna done (date unknown since 2026-10-13, see START HERE), then send 6J its path.**
- **Open, owner's call:** Seoul: four of five leftover files already gone, no record of who removed them; `kr` entry in `weather_registry.json` left as is. Yerevan Armstat source is not an open licence; Budapest brochure cross-check still open.
- **Nothing running.** Page saved locally as `ALL_CITIES_2026-10-12.html`; artifact WiykxBch12qHNpnYGxjaY3 v21.

**2026-10-12 12:30 — FINAL CHECK + 6J HAND-OFF STARTED (supersedes the 11:40 box below on what to do next).** Owner: "yes yes please" (go for stop-point 3: final check list, then 6J). Next free D-EU-169 / FINDING 299.
- **Plan:** common plan `implementation/PLAN_eu-new-cities-00-common-2026-10-08.md` §6.3 — F01 (10-line final check list per site, read only, fix nothing) and F02 (facts 6J asked for: counts, sources + licences, weather, assumed inputs, folder paths); stop-point 5 in §7. Six sites: Montréal, Yerevan, Cape Town (`win_2026-10-09`), Helsinki, Vienna, Budapest (`win_2026-10-10`).
- **Running:** two fresh Sonnets in parallel (session cd53977d), F01 and F02; each appends one entry under the common plan §8. If no entry appears, re-dispatch only the missing one.
- **Then:** audit F01/F02 per line; every FAIL fixed or put to the owner (one decision); then write ONE message per site to 6J in `messages_GSSCanada/` (what 6J asked in `2026-10-08_6J_to_OpenUBEM_go_cities_and_order.md` §3), show the owner before sending. Not in scope unless the owner asks: the Bologna copy for 6J (owner go needed, Bologna frozen), Seoul deletion (6J: delete nothing until told).
- **Local copy of the all-cities page (owner asked, "i love the content"):** `ALL_CITIES_2026-10-12.html` in the arc root = artifact v21 page (sha256 c9173b10… equal to the published file) with only its links repointed to `plans3D/` and `outputs_3D/` so it works offline; all 18 linked files exist. Never regenerate it without the owner's ask.

**2026-10-12 11:40 — ALL SIX NEW CITIES DONE THROUGH T08 (supersedes the 19:00 box below).** Next free D-EU-169 / FINDING 299.
- **Speed:** all three arrays ended, fatal=0 (Helsinki 1451887 580/580, Vienna 1451888 536/536, Budapest 1451908 805/805). Nothing of ours runs on Speed.
- **T07 (results) passed:** Helsinki 542 homes EUI 96.417; Vienna 517 homes EUI 77.578 (median 81.40); Budapest 757 homes EUI 63.358 (median 64.87; never quote the pooled 62.95).
- **T08 (viewer + side-cars) passed my audit for all three:** viewer `sim_counts.simulated` = 542 / 517 / 757; side-car flats = sum of `dwellings_used` = 29,781 / 10,506 / 30,929; side-car JSON count 757 for Budapest (nested `layouts/way|relation/`); outputs_3D copies byte-identical (`cmp` + `diff -rq`). Log entries in each city plan §8. `tests/eu22` red = the known Korea weather-registry test only. Budapest side-cars ran 450 serial + 307 in 8 shards with `--population-manifest`, so its manifest `geometry_outcome`/`layout_json` were not written back (fix in T09 if needed). Cosmetic: every viewer says "Of the N with an IDF, M carry a layout" with M counting left-out homes too (M > N); text only, not fixed.
- **plans3D:** all `PLANS_*` pages exist; `plans3D/index.html` links them. **outputs_3D:** viewers for all ten sites.
- **Artifact** https://claude.ai/artifact/WiykxBch12qHNpnYGxjaY3 at **version 21** (11:35): three cities "results", a "3D pages" panel and a per-city toggle "3D results / 3D floor plans" for 9 cities; files under `plans/` and `viewers/`. Cape Town plan page and viewer never published (licence, D-EU-160). Source: scratchpad `allcities/index.html` (patch `patch_v20.py`, backups `index_v17/18/19.bak`).
- **Next:** stop-and-report point 3 — run the final check list over all six cities, then the message to 6J.

**2026-10-11 19:00 — THREE CITY RUNS ON SPEED (supersedes the 09:45 box below).** Division fix done (T06c), plan pages done (T05p), owner accepted Helsinki 542/580 and Budapest 757/805 below target (D-EU-168, "ok accept them"; Vienna 517/536 met). Next free D-EU-169 / FINDING 299.
- **Running:** Helsinki job 1451887 (`1-580%10`), Vienna 1451888 (`1-536%9`), Budapest 1451908 (`1-805%13`); together 32 CPUs (owner: "up to 32 cpu you can use"). Fleets `/speed-scratch/o_iseri/fleets/EU22_<SITE>_win_2026-10-10/`, logs `/speed-scratch/o_iseri/openubem/fleets/openubem_t08_<job>_<i>.log`. When one array empties, raise the others with `scontrol update ArrayTaskThrottle=<n> JobId=<id>` so ours stay at 32. ETA: measure with `sacct` once tasks have ended.
- **Status 21:44 EDT (measured):** 534 of 1,921 COMPLETED (Helsinki 181/580, Vienna 140/536, Budapest 213/805), 32 RUNNING, 0 failed; every finished home ends "Completed Successfully", none "Terminated". Mean per task 530 / 604 / 561 s (all 562 s). ETA all three ≈ 04:30 EDT 2026-10-12 (1,387 left × 562 s ÷ 32); Helsinki empties first (≈ 03:40) — then raise Vienna/Budapest throttles to keep 32. Re-measure with scratchpad `m.sh` (`sacct -j <id> -n -X -P -o State,ElapsedRaw`), never guess. A task silent for ~10 min with stopped CPU (`sstat`) is dead: cancel, delete `out/<stem>`, resubmit that index. Ssh recipe: write a bash script, `ssh o_iseri@speed.encs.concordia.ca "bash -lc 'bash -s'" < script.sh`. Old watchers (`blr544h60`) are not yours; arm your own (`run_in_background`, poll ≥ 30 min).
- **All-cities artifact** (https://claude.ai/artifact/WiykxBch12qHNpnYGxjaY3) is at version 17 (19:00, three cities "running on Speed"; first 11 runs clean; not yet refreshed with the 21:44 count). Read it first, then edit its newest source copy `C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM\cd53977d-cb4f-4fc7-b78f-ae26920a5e75\scratchpad\allcities\index.html` and publish with `url`. Run `node --check` on its script before publishing (version 16 had an unescaped apostrophe that broke the page script).
- **When each ends:** `sacct` all COMPLETED, then dispatch one fresh Sonnet for that city's T07 (S8 harvest + results, common plan §6.2 S8, tag `win_2026-10-10`), then T08 (S9). Log entries T05/T06 are in each city plan §8.

**2026-10-11 09:45 HANDOVER — READ THIS FIRST (supersedes the 19:45 box below; array 1448071 is DONE, T06 is half done).** Nothing waits on the owner. Next free D-EU-168 / FINDING 299.
- **Done:** rerun array 1448071 = 414 of 414 COMPLETED, 414 IDFs, parts pulled to `openubem/outputs/eu_evidence/EU-11/division_fix_2026-10-10/speed_parts/parts/<SITE>/<i>/`. T06 S4 done by a Sonnet: merged trees `<SITE>_dw_2026-10-10/` and `<SITE>_win_2026-10-10/` (580 / 536 / 805 homes = the 10-09 trees; kept-home IDF sha256 equal 450/448/609; IDF changed for 114 of 130, 81 of 88, 165 of 196 rerun homes). Plan §8 holds the entries "T06 PARTIAL" and "T06b".
- **Why a second Speed array:** the side-car step (`emit_eu11_layout_sidecars.py`) re-derives each layout; with the 3600 s sweep a failing floor costs up to an hour per CPU, so the 8 local processes were stopped (killed 2026-10-11 ~02:50, nothing measured) and the 414 rerun-home side-cars run on Speed: **job 1450520, `--array=1-414%32`, 7-day walltime**, script `scripts/cluster/eu22_sidecar_array.sbatch`, output `/speed-scratch/o_iseri/eu22_fix_2026-10-10/sidecar_parts/<SITE>/<i>/layouts/`. Status 09:30 EDT: 304 COMPLETED, 30 RUNNING, mean 1755 s per task, ETA ≈ 11:20 EDT (110 × 1755 ÷ 30; re-measure with `sacct -j 1450520 -n -X -P -o JobID,State,ElapsedRaw`, pipe a bash script through `ssh o_iseri@speed.encs.concordia.ca "bash -lc 'bash -s'" < script.sh`). Old watchers (`bl70gbluy` and earlier) belong to the old session: arm your own (`run_in_background`, poll ≥ 30 min, stop when `squeue -h -j 1450520` is empty). The old session's determinism test: same home twice gives identical JSON (6 of 6); a 60 s budget differs from 3600 s on a timeout, so do not shorten SWEEP_S.
- **When it ends:** (1) `sacct` must show 414 COMPLETED, none failed (a failed task = delete `sidecar_parts/<SITE>/<i>` and resubmit that index); (2) pull `sidecar_parts` back with `ssh … "tar cf - sidecar_parts" | tar xf -` into `division_fix_2026-10-10/speed_parts/` (about the size of the layouts only, no IDFs); (3) dispatch ONE fresh Sonnet (`model: "sonnet"`) to finish T06: run the merge command written in plan §8 "T06b" (copies the layouts into `<SITE>_dw_2026-10-10/layouts/`, Budapest under `layouts/relation/`, sets `geometry_outcome`), check layout counts 580 / 536 / 805, then `python -I -X utf8 scripts/eu22/score_division.py --site SITE --tree SITE_win_2026-10-10 --layout-tree SITE_dw_2026-10-10 --floors-decide --workers 8` for each city, then IDF_FALLBACK, class counts (OK/V3/V1/V2/U*), homes still left out with failing checks, flats removed by k−1 (total and per home), and `division_fix_2026-10-10/summary.md` (≤ 40 lines). Mark the "T06 PARTIAL" entry completed. It stops at stop-point 3.
- **Open ruling for you at the audit (integrity I8):** the helper changed the flats-per-floor check (`scripts/eu21/13_model_integrity.py`) to compare against `dwellings_used − dwellings_removed`; I8 failures are now Helsinki 1, Vienna 2, Budapest 21 (2.6 %, was 44 = 5.5 %). Budapest is above the 1 % stop line of S5. The 21 are k−1 homes where the flat was removed from the failing floor but the check re-spreads the reduced total over all floors. My intended ruling: accept as by-design (each removed flat is listed per home) and fix the check to spread over the floors that kept their count only if the fix is a few lines; otherwise record it in the summary and move on. Also note for T09: manifest `dwellings_used` keeps the old total for k−1 homes (the IDF has fewer).
- **Targets for stop-point 3:** Helsinki ≥ 551/580, Vienna ≥ 509/536, Budapest ≥ 765/805 (correctly divided = OK + V3). Then audit, refresh the all-cities artifact (https://claude.ai/artifact/WiykxBch12qHNpnYGxjaY3, read it first), and each city plan resumes at T05 (S6 plan pages; the owner sees them before any run).
- **Rules that bit this session:** the local machine must stay free (≤ 8 processes, the owner works on it); long layout work goes to Speed. 10-09 trees are never modified. Frozen: Bologna and `handover_4J_2026-10-06`. Git only when the owner asks.

**2026-10-10 19:45 HANDOVER (history, array part now done) — READ THIS FIRST, then the 10:30 update below for the T06 recipe.** Owner is starting a fresh manager session. Nothing is waiting on the owner.
- **Speed array 1448071 (`--array=1-414%32`) at 19:40:** 350 of 414 COMPLETED, 25 RUNNING, the rest pending (Budapest tasks 219–414 are the last). The 19:00 ETA was too early (the account cap is shared with 4J/5J: 52 of our-account tasks running, only ~25 ours). Re-measure: `sacct -j 1448071 -n -X -P -o JobID,State,ElapsedRaw` (pipe a bash script through `ssh o_iseri@speed.encs.concordia.ca "bash -lc 'bash -s'" < script.sh`), remaining × mean ÷ width. Old watchers (`bnjip4tl9`, `b5r0s1rh1`) belong to the old session: arm your own (`run_in_background`, poll ≥ 30 min, stop when `squeue -h -j 1448071` is empty). Check `squeue -u o_iseri`: if fewer than 32 of ours run while tasks are pending and the account has room, `scontrol update ArrayTaskThrottle=32 JobId=1448071`; never touch 4J/5J jobs.
- **When it ends:** verify all 414 COMPLETED with sacct, read division-fix plan §6 T06 (~line 82), dispatch ONE fresh Sonnet (`model: "sonnet"`) for merge + S4/S5 (`DATE=2026-10-10`) + `score_division.py --floors-decide`; it stops at stop-point 3 (shares vs targets Helsinki ≥551/580, Vienna ≥509/536, Budapest ≥765/805). You audit, then each city plan resumes at T05.
- **Geometry-24 is CLOSED on our side** (see the 16:15 update just below): 4J built their own `patch24`; no engine edit, no reply owed. Open points sit with 4J: Madrid 5808697 not reproduced, 4J's surface counts higher than ours, 4J's clip dropping a flat in 4154505.
- **Bologna FROZEN** until 4J says done (~20 Oct estimate SUPERSEDED 2026-10-13: 4J stopped its Bologna C2 run on purpose and will remake diaries and re-run, no new date; see `messages_GSSCanada/2026-10-13_4J_to_OpenUBEM_bologna_c2_stopped.md`); message 4J (gsscanada-25) before any change. 5J (gsscanada-66) is closed on purpose.
- **Still owed:** rebuild `summary_win_2026-10-09.csv`; debug-reference entries from the 10-09 18:45 update; after all builds Seoul deletion, pytest, grep, note to 6J. Refresh the all-cities artifact (https://claude.ai/artifact/WiykxBch12qHNpnYGxjaY3, read it first) at the T06 milestone. Next free D-EU-168 / FINDING 299.
- **Git:** commit/push only when the owner asks; never add `openubem/outputs/eu_evidence` or `eu_certified_rerun_2026-08-28`; run add/reset in the background. Working tree has many untracked/moved files by design.

**2026-10-10 16:15 update — GEOMETRY-24 SOLVED, NOTE SENT, 4J ANSWERED.** Cause: 4J's forked `build_idf_for_cell` lacks ten of our geometry safeguards (not engine, not footprints). Remedy R-E, no engine edit. Note sent to 4J (owner approved). 4J chose neither option: separate `patch24` population running our safeguard sequence, Madrid 11 builds 110/110 build-only, no reply needed (`messages_GSSCanada/2026-10-10_4J_to_OpenUBEM_geometry24_choice.md`, plan §8 T08). Debug-reference entry written. Nothing owed except watching 4J for a later request. Bologna stays FROZEN until 4J says done. History of the investigation follows.

**2026-10-10 14:15 update — GEOMETRY-24 (Madrid 11 + Bologna 13), supersedes the "Bologna closed" line below.** Owner asked for an investigation/fix document and said "once you solve, inform 4j session". Plan: `debugs/PLAN_geometry-24-madrid-bologna-2026-10-10.md` (T01–T04 diagnosis, hypotheses H1–H5, remedies R-A to R-D, stop-points 1–3). Same known error family as FINDING 210 / D-EU-43 (ceiling/floor vertex-count mismatch); the open question is why the shipped 1 mm snap + reroute gate did not protect these 24. My first message to 4J wrongly called the zero-area error new; corrected by peer message. Sonnet executor a2948a9abc9feb359 (background, session c49e97f6) runs T01–T04 only; scratch `scripts/eu_geometry24/`, outputs `openubem/outputs/eu_evidence/EU-11/geometry_24_2026-10-10/` (4J_bologna, 4J_madrid, err_signatures CSVs already there). 4J copied its Madrid error files to Speed `/speed-scratch/o_iseri/4J_esit/madrid_geom_failures_2026-10-10/` (37 err, 40 cells_failed, code sha 0b9aa66c); 4J's author accepted the 11 as lost, no patch run planned. **When the executor reports (stop-point 1):** audit §8 entries and files touched, check frozen folders unchanged, pick a remedy. No engine edit before the owner approves (stop-point 2); any 24-task verification array is submitted by the manager at %32. Then write T07 hand-over note `messages_GSSCanada/2026-10-10_OpenUBEM_to_4J_geometry24.md` (correction, Bologna Q1–Q3, Madrid (a)–(c), patched files in a NEW folder, never the frozen one) and send it (owner said inform 4J once solved). Register the findings in `OpenUBEM_debug_References.md` after the fix. Bologna stays FROZEN until 4J's "done".
**2026-10-10 10:30 update — READ FIRST (supersedes every line below on what to do next).** No active work for the owner; one Speed array runs on its own. Next free D-EU-168 / FINDING 299.
- **Plan in force:** `implementation/PLAN_eu-division-fix-3cities-2026-10-10.md` (Helsinki, Vienna, Budapest to ~95 % correctly divided = OK + V3). T01–T04 done; T05 submitted (§8 T05 log). Targets (§1 line 9): Helsinki ≥ 551/580 (today 458), Vienna ≥ 509/536 (today 448), Budapest ≥ 765/805 (today 609).
- **Speed:** array `eu22_fix` job **1448071**, `--array=1-414%32`, 7-day walltime, env `/speed-scratch/o_iseri/envs/openubem_eu22/`, correct IDD exported as `OPENUBEM_ENERGYPLUS_IDD_PATH` (the first array 1448040 had the v8.0 IDD and was cancelled, logs in `logs/old_wrong_idd/`). Task ranges: Helsinki 1–130, Vienna 131–218, Budapest 219–414. Only 16 run at once: the 64-CPU account cap is full with 4J/5J jobs (`AssocGrpCpuLimit`); never touch them. **Status 14:15:** Helsinki and Vienna done, Budapest running (watcher at 13:48 still showed 17 tasks queued/running); ETA ≈ 19:00 from the earlier sacct measurement (mean per task × remaining ÷ width). Re-measure with `sacct -j 1448071 -n -X -o JobID,State,ElapsedRaw -P` (tcsh login: pipe a bash script via `ssh … "bash -lc 'bash -s'" < script.sh`).
- **Watcher:** the background watcher of the old sessions does not report to a new one. Re-arm your own (`run_in_background`, poll ≥ 30 min, stop when `squeue -h -j 1448071` is empty).
- **When the array ends → T06** (plan §6 line 82): merge each 10-09 dw tree minus the rerun ids with the Speed parts into `<SITE>_dw_2026-10-10/`, S4 + S5 on `DATE=2026-10-10`, `score_division.py --floors-decide`. ⚠ The 10-09 `prepared_buildings.csv` files have no `dwellings_removed` column: add it empty to the kept rows before `merge_prepare_parts.py`, or it stops on "header differs". `stage_eu22_fix.sh` does not copy the IDD; copy it by hand on any restage. Then stop-point 3: shares vs targets, manager audit, each city plan resumes at T05 (S6 plan pages; owner sees them before any run).
- **4J Bologna (first answer 2026-10-10; superseded by the geometry-24 update above):** 4J asked about 13 Bologna buildings failing in their run (28025, 28050, 28959, 29530, 29719, 30001, 31083, 31363, 32360 EnergyPlus vertex mismatch; 29109, 30485, 31962, 33359 `interzone_vertex_mismatch_unresolved`). All 13 ran clean in our own builds (9 win_2026-10-06, 4 in the 10-08 package); none on the 232 list. **Owner ruling: final losses for 4J, no new files.** 4J accepted, run unchanged, will state the Bologna count. Question file: `messages_GSSCanada/2026-10-10_4J_to_OpenUBEM_bologna_geometry_questions.md` (replies went by peer message). Bologna stays FROZEN until 4J's "done" (~20 Oct).
- **All-cities page v13:** https://claude.ai/artifact/WiykxBch12qHNpnYGxjaY3 (Progress tab shows the Speed run at 10:13). Read it with the Artifact tool before republishing. Montréal, Yerevan and Cape Town have results (done).
- **Still owed (from 10-09, unchanged):** rebuild `summary_win_2026-10-09.csv`; the debug-reference entries listed in the 10-09 18:45 update below; after all builds: Seoul deletion, pytest, grep, note to 6J.

Older plan pointer (history): `implementation/PLAN_eu-rulebook-change-2026-09-30.md` (Part B, the 460 homes). Integrity plan closed (T08/T08b/T09 PASS). Bent-walls plan parked (`PLAN_eu-bent-walls-2026-09-30.md`).

### 🟢 Latest state (2026-10-07 ~23:00 local) — supersedes everything below in this box
**2026-10-09 18:45 update — READ FIRST (supersedes every line below on what to do next).** Owner resting. All-cities page v11: https://claude.ai/artifact/WiykxBch12qHNpnYGxjaY3 (source: scratchpad of session 74dad075 `allcities/index.html`; read it before republishing). Next free D-EU-166 / FINDING 298.
- **Speed — owner rule 2026-10-09: "for speed runs use only 32 cpu half of them okay" = our runs together use at most 32 CPUs (half the 64 account cap); split the throttle across our arrays (sum ≤ 32), raise the others when one ends.** Running now (throttles 12/10/10): Montréal `CA-MTL-PLATEAU` job 1442166 (710 IDFs, results over 701), Yerevan `AM-EVN-NORNORK` job 1442163 (551, results over 535; D-EU-165 owner: way/998439490 left out, row added to its `left_out.csv`), Cape Town `ZA-CPT-WOODSTOCK` job 1442187 (525, results over 524; owner "yes okay keep goin with cape town"). Fleets `/speed-scratch/o_iseri/fleets/EU22_<site>_win_2026-10-09/`; ids in each `<site>_win_2026-10-09/speed_jobs.txt`; T06 entries in each city plan §8. At 18:39 only 2 tasks ran (5J_9l_run holds ~54 CPUs; never touch 4J/5J). Measure the ETA from `sacct` once tasks complete. Then per city: T07 (S8 harvest, gate on `eplusout.end` success; left-out homes dropped by building id, `write_results_eu22.py:45-55`) and T08 (S9 viewer + side-cars). Cape Town footprints never published; credit "City of Cape Town".
- **Division push to ~95 % (owner: Helsinki "at least 95%", Vienna "yes please", Budapest "push budapest to 95%")**: plan `implementation/PLAN_eu-helsinki-division-2026-10-09.md` (T01/T02, T01V/T02V, T01B/T02B; diagnosis only, no rule change). Sonnet agents (session c49e97f6): Helsinki a4e768fa0a4c13d05 (4 workers; T02 at 79 of 366 rows, 19 recoveries; measured ~9 h left at 18:39), Vienna a383f2f8fb6364dfe (2 workers; 18 of 264 rows, ~14 h left), Budapest a113c19a6c882cd27 (T01B done; T02B waits until the machine has ≤ 8 python processes; ~588 rows at ~400 s each over 2 workers ≈ 33 h once started). If an agent is gone, check `openubem/outputs/eu_evidence/EU-11/<city>_division_2026-10-09/t02_dryrun.csv` and re-dispatch only the missing part (scripts in its `scratch/`). On T02 summaries: audit §8 entries + files touched, then write ONE fix plan for the three cities aiming at ~95 %.
- **Madrid side-cars for 4J**: sent (`messages_GSSCanada/2026-10-09_OpenUBEM_to_4J_madrid_win6_sidecars.md`, plan `PLAN_eu-4J-madrid-win6-sidecars-2026-10-09.md`). 4J reply 2026-10-09: received, nothing copied; their author must approve the two changed engine files first; no rebuild asked. Wait. Bologna stays FROZEN.
- **Fresh session (owner, 2026-10-09 ~18:50, to save tokens):** the old session 74dad075 stays open only so its three diagnosis agents and their Python workers keep running; do not close it until the three `t02_summary.md` files exist. The new session gets no completion notices from those agents: check the three `t02_dryrun.csv` row counts and `t02_summary.md` (≥ 30 min apart). Re-arm your own Speed watcher (`run_in_background`, poll ≥ 30 min, jobs 1442166/1442163/1442187); when one ends, raise the others so the sum stays 32.
- **Audited 2026-10-09:** the Budapest build agent's items were all planned and logged (merge script + test = T03s, PID 53220 stop = T03s step 3, entries at plan §8 T03s/T04). Nothing owed there.
- **Still owed:** rebuild `summary_win_2026-10-09.csv` from the per-city files; debug-reference entries (solar-closure error, Budapest join-rule stop, CRLF md5 check, Madrid multi-floor-surface zones, summary overwritten by `13_model_integrity.py`, emitter ALLOWED list rejecting Madrid); after all builds: Seoul deletion, pytest, grep, note to 6J.
**2026-10-09 08:20 update:** owner said "vienna yes" → D-EU-159 (Vienna weather pinned with a winter-month gate-5 exception); a Sonnet executor pins `at` and runs Vienna T03–T05, stopping at the plan-page audit. Weather downloader at 41 of 91 at 08:01 (about 3 per hour). Owner asked what Seoul and Cape Town need; answered in chat. D-EU-160: owner says 6J is their own project, so the Cape Town licence hold is lifted (no public release, credit the City). Seoul: owner is registering on data.go.kr. D-EU-161: owner said build Cape Town (year route accepted); waiting only on the `za` weather (13 pieces, not started at 08:30); then one Sonnet converts/gates/promotes `za` and runs Cape Town T03–T05. Owner handles the Seoul key. Cape Town weather moved to the front of the download queue (12:27 UTC restart; then ca fi hu am kr). D-EU-162: Seoul dropped unless the no-key check (T01 step 1, Sonnet running) finds a route; owner cannot register (Korean phone needed). **Seoul DROPPED and archived** (`DONE/PLAN_eu-new-city-KR-seoul-2026-10-08.md`); weather downloader restarted without `kr` (za first, then ca fi hu am). Six new cities. Next free D-EU-163 / FINDING 297.
**2026-10-09 01:20 state (supersedes the night update below on progress):** Common C01–C08 are done, except C02, which is stopped (see §8 of the common plan). Every city except Seoul has T01 (data) and T02 (construction table) done: Vienna 536, Helsinki 588, Montréal 725 (roofs cut at lot lines), Budapest 805, Yerevan 551, Cape Town 534 (street blocks; years from heritage labels). Seoul's T02 is done, but its T01 waits for the key. Manager amendments: C01 heat-loss rule plus a builder-order bug fix (five tables rebuilt); D-EU-151 named-unit-under-500 rule; D-EU-153 national series only, plus a type-substitute rule; D-EU-154 oldest-census-class year; C06 scorer reads the cutter side-cars, so S5 runs the emitter first. **Blocker: weather.** `at` fails gate 5: Jan +21 %, Mar +17 %, Nov +15 % against SARAH3. The conversion is verified (within 1 % of PVGIS ERA5). The registry entry is `BLOCKED_GATE5_FAIL` with weather_file null, so `prepare` cannot run. The other 6 folds are still downloading: a throttled CDS downloader, PIDs 41596/7804, log `openubem/outputs/eu_evidence/EU-22/weather/throttled_2026-10-08.log`, 20 of 91 at 01:03. When it finishes, a fresh executor converts and gates them, then promotes them with `run_eu_t06_weather_promotion.py`. **Owner decisions pending:** (1) Vienna gate 5 (and likely other winter months); recommend accepting with the verified-conversion note, without widening the tolerance for the four existing sites. (2) Seoul key. (3) Cape Town licence, which says non-commercial and no redistribution. (4) Yerevan: every building takes 1951–70, from the district dominant period; a storey-based age rule would need an owner ruling. Then: S3–S6 per site → manager audit → Speed.
**2026-10-08 night update — NEW CITIES FOR 6J (supersedes every line below on what to do next):** 6J (gsscanada-8e) asked for one neighbourhood in each of 7 new countries; our feasibility reply was sent (`messages_GSSCanada/2026-10-08_OpenUBEM_to_6J_new_neighbourhoods.md`). The owner then said "can you prepare implemeantion plan for each new city", "i will sleep can yo uhandle the plans and executions", "also can yo ucreate new artifact that includes all cities at same place", "follow same piplien for new cities as well, floor plan division, window to wall ratio etc.". Plans: `implementation/PLAN_eu-new-cities-00-common-2026-10-08.md` (shared code C01–C08 + standard per-site steps S3–S9) and one per city `implementation/PLAN_eu-new-city-<CC>-<city>-2026-10-08.md`: Vienna `AT-VIE-RUDOLFSHEIM`, Seoul `KR-SEO-MAPO`, Montréal `CA-MTL-PLATEAU`, Helsinki `FI-HEL-KALLIO`, Cape Town `ZA-CPT-WOODSTOCK`, Budapest `HU-BUD-ERZSEBETVAROS`, Yerevan `AM-EVN-NORNORK`. Manager decisions taken overnight, all open for owner review: D-EU-150 to D-EU-158 (common plan §4). Order: city T01–T02 (data + construction tables) in parallel with common C01–C08 (one executor); then per site S3–S6, STOP for the manager audit of the plan pages, manager submits to Speed (array %32, 7-day walltime), then S8–S9. Known blockers: Seoul needs a data.go.kr service key from the owner; Cape Town has no stated licence and no per-building age; Budapest and Yerevan have no open heights or ages (census-based, flagged). Frozen Bologna rules above still hold; nothing UK to 6J; the Bologna copy for 6J only on the owner's go. Next free D-EU-159 / FINDING 297. All-cities page: https://claude.ai/artifact/WiykxBch12qHNpnYGxjaY3 (source: this session scratchpad `allcities/index.html`, plan pages published under `plans/`); EU status page https://claude.ai/artifact/PB9MoeVTUVTemPmnXJDnBs v117 (source scratchpad `eu_status/index.html`).
**2026-10-08 update — ARC REOPENED (supersedes the archive line below):** the owner asked to bring the arc back ("bring back this project to the docs_active, we have things to do"). The folder moved back from `docs/docs_DONE/SETUP/europeanLocations/` to `docs/docs_ACTIVE/europeanLocations/`, nothing renamed; every citation in docs, scripts, tests, data and 3D outputs was repointed. The archive record stays below as history.
**2026-10-08 19:33 update — ARC CLOSED AND ARCHIVED (supersedes every line below):** the owner asked for the archive ("yes yo udo it"). The folder moved from `docs/docs_ACTIVE/europeanLocations/` to `docs/docs_DONE/SETUP/europeanLocations/` (453 files, same byte size). All live links were repaired (24 scripts, 6 tests, 5 data JSONs, 4 viewer `sources.json`, 2 docs_EXPLANATION docs; old-path search returns 0). Tests are the same as before (153 passed, 1 failed that was already failing). The migration row is `docs/PROJECT_CHECKLIST.md:28`. Plan: `implementation/PLAN_eu-archive-2026-10-08.md` (T01–T05 done and audited). The four open plans and the 8 open checklist boxes are marked closed by D-EU-148/149. Final results stand: `results/EU11_results_2026-10-08_*`, fleet 62.626 kWh/m² over 3,870 homes. **The only open item is 4J's (gsscanada-25) Bologna "done" message, earliest ~20 Oct.** Until then the Bologna frozen folders stay unchanged. Next free D-EU-150 / FINDING 297. Status page v116.
**2026-10-08 17:17 update (supersedes the 16:40 "only open item"):** owner closed the 5J session (gsscanada-66) on purpose; 5J's final FINDING 293 note will not come, nothing to wait for from 5J. 4J (gsscanada-25) is still active. **~17:16 4J reply: London DONE, so the London freeze is lifted (`GB-LDN-STDUNSTANS_win_2026-10-06/` + London part of the Speed handover may change). Bologna NOT DONE, so the Bologna freeze stays (`IT-BOL-GALVANI2_win_2026-10-06/`, Bologna part of the Speed handover, 10-08 fixed-homes package): 4J step P8 waits on cluster CPUs, earliest finish ~20 Oct, and 4J will message when done.** Record: `messages_GSSCanada/2026-10-08_OpenUBEM_to_4J_5J_restated_results.md`. Only open item: 4J's Bologna "done".
**2026-10-08 16:40 update (supersedes the 16:30 line):** T16 + T16b accepted (5 rule test pages at R4 5.0/0.25, 541/9 of 550, 0 regressions, caption fixed); final check list passed; restated numbers sent to 4J (London + Bologna) and 5J (Madrid + Bologna, no London) at 16:34, see `messages_GSSCanada/2026-10-08_OpenUBEM_to_4J_5J_restated_results.md`; status page v113. Only open item: 5J's final FINDING 293 note (~11 Oct). Frozen folders unchanged until 4J reports done.

- **2026-10-08 16:30 update (supersedes the lines below):** 193 of 193 fixed homes simulated locally (0 failed). T15 restated results written and audited: `results/EU11_results_2026-10-08_*`, 3,870 homes, ES 68.774 / FR 57.810 / GB 68.307 / IT 58.164 / fleet 62.626 kWh/m² (FINDING 295: rise is mostly the large left-out blocks). T17 3D viewers regenerated on 10-08 and audited (FINDING 296: FR/IT fixed IDFs skipped the local-origin shift; 1 home affected, accepted). T16 rule test pages in flight. Left: audit T16, final check list, send new numbers to partners (London only to 4J), 5J final FINDING 293 note ~11 Oct. Next free D-EU-150 / FINDING 297. Status page v111. Plan §8 Part C entries.
- **2026-10-08 08:30 update (supersedes the lines below):** overnight only 22 of 228 sims ran; 206 failed to start (rc 3221225794, low memory) and were never retried. Rerun of those 206 started detached 08:26 (`sim_local.py sim_list_retry.csv 16`, PID 36428), measured ETA ~12:30. Slow-home retry gave 0 new homes: count stays 3,881 / 94.4 %. **Owner ruling D-EU-148 (10-08): stop at 94.4 %, keep the R4 rules, no more loosening. D-EU-149 (10-08): restated results drop the 232 unresolved homes, no comparison shown.** Next free D-EU-150 / FINDING 294. Status page v107. Plan §8 'Director note — overnight simulations mostly failed to start'.
- **23:25 update (supersedes the count and Running lines below):** R5 ended 23:14 (112 tested, 25 timeouts, 20 fixed, only 3 new after dedupe). Count **3,881 / 4,113 = 94.4 %, 27 short**. T13 worse-gate (Bologna 30540, C13 4→5) ruled accepted under the bent-wall ruling. Chain `chain_final.sh` dies at the 2 h tool limit (~00:55); detached `supervisor.sh` (scratchpad, log `supervisor_log.txt`, PID 31332) waits for it, finishes any cut rebuild/sims (done = `task.rc` exists), then retries the 25 timeouts (`orch_timeouts.py`, R5, 2,400 s, `j12t/`) and simulates them. 95 % most likely needs one more owner decision on looser rules. Plan §8 'Director note — T13 worse gate, recount, overnight simulations'. Status page v105.

- **Owner goal (2026-10-07 evening):** ≥ 95 % of 4,113 homes resolved (3,908), 5 % miss allowed; "be fast", "exclude full checks, loosen the rules"; simulate **locally, 16 processes** (CP-2 ruled local, not Speed). Rulings: bent-wall (V3) homes accepted except Madrid way/435447773; the automatic 2 m check is NOT a gate (it failed 4 homes the owner approved; plan §8 22:55). The 8 not-divided homes needing new code are parked inside the 5 % (T14 diagnosis, §8 22:50).
- **Count at 22:57:** 3,688 already fine (OK 3,096 + V3 586 + S1 6) + 190 fixed by R1_35/R2_33/R4/R5 so far (deduped on district+building_id) = 3,878 (94.3 %), 30 to go. Final rules = R4 (`max_flat_aspect 5.0`, `min_spread 0.25`, guard on) + T13 sliver repair (`repair_slivers`, live in code 22:31:57).
- **Running (scratchpad of session 9df6cea2):** R5 wall test `orch12h.py` → `scratch/dryrun_1006/j12h/`, log `orch_log_T12h.txt` (stops at 70 R5 fixes or end of 137 homes). Chain `chain_final.sh` (background): on R5 DONE → `sim_pick.py j12g,j12h` → local EnergyPlus 23.1 `sim_local.py` at 8 wide on kept models, AND `orch_rebuild.py` (R5 rules, 8 wide, CAP 600) on `targets_rebuild.csv` (144 fixed homes without kept models) → `j12r/`, log `orch_log_rebuild.txt`; then sims of j12r at 8 wide. Sim outputs `rulebook_2026-09-30/sim_local_2026-10-07/<key>/out/<stem>/`, log `sim_log.txt` (start/end per home with seconds). Smoke home started 22:54.
- **Next:** time the first homes from `sim_log.txt` → state the ETA (never guess); harvest heating kWh with `parse_task`/`_parse_heating_kwh` (`scripts/cluster/harvest_eu11_district.py:201-251`) and floor area from each `prepared_buildings.csv`; set final values in `NOCORE_RULESET` + rule files (they still say 3.5/0.33); §8 entries; status artifact https://claude.ai/artifact/PB9MoeVTUVTemPmnXJDnBs (v103, source scratchpad `eu_status/index.html`). FROZEN folders unchanged. Next free D-EU-148 / FINDING 293.

### Latest state (2026-10-07 ~10:30 local)

- T12 finished and audited (plan §8 "Director audit of T12"). **CP-1 NOT signed:** the ladder is invalid by construction (FINDING 292): the cut guard keeps today's cut and reports its OLD-rule verdict, so no relaxed rung can ever resolve a home. Owner asked once: fix the guard (judge a kept cut by the active rules), re-run ladder + RALL_G only, then CP-1. **Owner approved ("yes of course, lets go").** T12b steps 1–4 done and audited 2026-10-07 (plan §8): one-line guard fix at `european_residential.py:1376`, tests g/h/i pass, T12 outputs moved to `scratch/dryrun_1006/_superseded_T12_guard_2026-10-07/`, detached orchestrator pid 20260 started 10:23:51 (10 workers, 109 jobs), log `scratch/dryrun_1006/orch_log_T12b.txt` (T12 took ~10.5 h). Next: on `DONE` in that log, fresh Sonnet for T12b step 5 (merge, summarize, gates a–e) → CP-1. Next free D-EU-148 / FINDING 293.

### Latest state (2026-10-06 21:05 local)

- Owner "ok continue to the end" / "ok continue" / "of course keep going" (2026-10-06 evening) = run T12 → CP-1 (director signs T05) → T06 → T07 → CP-2 overnight without asking; **stop at CP-2 for the owner's word before Speed**.
- T10, T11 done and audited. T11 classes (fleet): OK 3,096, S1 6, V1 301, V2 113, V3 587, U3 8, U4 2. 8 drift rows held at their adopted models (6 Madrid → CP-3 as their own line; the Bologna pair needs no action); gate (a) read as 4,105/4,105. Candidate set 418 (ES 82, FR 30, GB 34, IT 272). Outputs `openubem/outputs/eu_evidence/EU-11/rulebook_2026-09-30/{baseline,drift,dryrun_R0,dryrun_summary}_1006.csv`.
- **2026-10-07 09:45 update:** all T12 runs ENDED 03:48 (`scratch/dryrun_1006/orch_log.txt`: "DONE fails []"); the first T12 agent died before merging. A second Sonnet (dispatched ~09:42 from the old session) is doing the finishing steps only: concat Bologna chunk parts into `part_<run>_IT-BOL-GALVANI2.csv`, explain the unplanned "R0c" runs, `summarize --ref 1006`, gates (a)–(d), T12 §8 entry, then STOP. **Before dispatching anything for T12, check §8 for a "T12 … completed 2026-10-07" entry and the parts' mtimes; if the entry is missing and no file changed for 30 min, re-dispatch the finishing steps only — never re-run the dry-runs.** No dry-run process is alive.
- On DONE audit: gate (a) RALL_G moves 0 OK/S1 vs `dryrun_R0_1006.csv`; (b) count of OK/S1 RALL moves; (c) passing candidate storeys identical RALL_G vs R0; (d) ladder table on the 418 (resolved / worse / floors still failing per check); 8 held homes excluded; [OPEN] drift entry in the debug references; T12 §8 entry; only planned files; no process left.
- CP-1: sign T05 = rung with most homes resolved and 0 worse (R3 allowed, T02 §3 holds); tell the owner in plain words. Then fresh Sonnets: T06 (new rules files), T07 (build candidates with the 10-06 recipe in the plan, excluding the 8, run the gate). Then CP-2: tell both partner teams (London content to 4J only), ask the owner before Speed, update this box and the EU status artifact (https://claude.ai/artifact/PB9MoeVTUVTemPmnXJDnBs, source scratchpad `eu_status.html`).
- Later: T08 on Speed, CP-3 (with the 6 Madrid homes as their own line), T09.
- FROZEN (owner, 2026-10-06): London + Bologna `<D>_win_2026-10-06/` and Speed `/speed-scratch/o_iseri/handover_4J_2026-10-06/` until 4J reports done (~9 Oct); message 4J before any change. 4J package sent (`messages_GSSCanada/2026-10-06_OpenUBEM_to_4J_win6_package_london_bologna.md`); 5J answered. London content never to 5J.
- Next free D-EU-148 / FINDING 292.

### Latest state (2026-10-06 morning)

- D-EU-146 (owner "go with (a)"): residual T07/T08 replaced by integrity plan T08 (viewers on 10-06), T08b (stale viewer test repointed, 12/12 pass) and T09 (STATE ledger to D-EU-146 / FINDING 291, every 09-08 EUI marked superseded). All audited PASS; V3 passes with 6 named outline differences ≤ 1.76 m. Next free D-EU-147 / FINDING 292.
- Side effect: viewer rebuild removed the 09-08 side-cars from `outputs/3D/eu_<D>_data/layouts` (in git history). 10-06 side-cars do not exist.
- Pending owner decision: reopen GSSCanada hand-overs. 5J asks (final delivery? changed stems + reason, `_win_2026-10-06a`, Madrid `59231039c486b1fb` non-convex Severe = known, run as delivered). 4J asks 10-06 package for GB + IT (request file `messages_GSSCanada/2026-10-06_4J_to_OpenUBEM_request_win6_package.md`); 4J got a holding reply only.

### Latest state (2026-10-03 ~13:00 Speed clock)

- All 10-06 runs finished, 0 failures; IT carry done (d8a1 stale copy replaced); harvested ×4 (ES 1,163, FR 520, GB 1,240, IT 1,164 = 4,087).
- Final integrity run: 13 fails, all named, 0 unexplained. **CP-3c PASSED** (check 3 read within age band for ES apartment blocks, D-EU-145). **10-06 ADOPTED** *(superseded 2026-10-08 by results/EU11_results_2026-10-08, D-EU-149: ES 68.774/1,119, FR 57.810/501, GB 68.307/1,215, IT 58.164/1,035, fleet 62.626/3,870 — correctly divided homes only, not like-for-like, FINDING 295)*: ES 69.165, FR 58.009, GB 61.977, IT 54.648, fleet 59.661; results in `results/EU11_results_2026-10-06_*`; 09-08 superseded (`results/SUPERSEDED_2026-09-08.txt`).
- Remaining: T07 viewers (add back origin offsets), T08 ledger/references; update artifact (not updated this pass). Next free D-EU-146 / FINDING 292. Parked plans (rulebook change, bent walls) can now start on owner's word.

### Latest state (2026-10-03 06:01 Speed clock) — supersedes the Bologna ETA and "NOW" lines below

- **Bologna 1410474 ENDED.** 3 OUT_OF_MEMORY tasks: `_261` (`366fc6fda9a1a946`, re-run in 1416442 at 64G, 10-06 fleet), `_1000` (`d8a1a0d8ceb5dc73`) and `_1163` (`fd4b13e28f1c6f47`) — the last two are NOT in the 10-06 re-run list. Mean 1,543 s over 990 completed tasks (`stage1005/eta3.sh`).
- **IT carry DONE:** `out/` of `EU11_IT-BOL-GALVANI2_win_2026-10-05` tar-copied into `…_win_2026-10-06/out` (excluding `stage1005/ex_it.txt`: 183 re-run stems + `366fc6fda9a1a946`, `--keep-old-files`).
- **Re-runs of the two OOM stems, in the 10-05 fleet dir** (ids appended to its `speed_jobs.txt`): `_1163` → 1420405 (64G) RUNNING. `_1000` failed at 32G, again at 64G (1419526, MaxRSS 62.7 GB), now 1423059 at **200G** RUNNING. When each finishes OK: carry `out/fd4b13e28f1c6f47` and `out/d8a1a0d8ceb5dc73` from the 10-05 IT `out/` to the 10-06 IT `out/` (tar only). If 1000 fails at 200G: treat as a broken-shell candidate, leave it out, record FINDING 292 (or amend 291), expected IT rows then 1,163.
- **10-06 arrays at 05:59:** London 1416438 all 1,037 COMPLETED; Madrid 1416439 all 243 COMPLETED; Bologna 1416440 178/183 done, 5 running; Lyon 1416441 29/32 done, 3 running; 1416442 (index 184) running. No failures. Account: other project's 1409235 still holds 32 CPUs (never touch).
- **Watcher** bukurui3e (`scratchpad/watch3.sh`, polls 1410474, 1419526, 1420405, 1423059, 1416438–1416442 every 35 min, ≤ 3 polls per run, ignores known OOM ids) dies with the old session: **re-arm your own** (`run_in_background`, never a bare `&`; `pkill` does not exist in Git Bash).
- **Next, in order:** (1) wait until all those jobs end; (2) `bash /nfs/speed-scratch/o_iseri/stage1005/sweep2.sh <D>` for ES, FR, GB, IT on each 10-06 fleet; every failure: `sstat` first, then delete `out/<stem>`, resubmit that index with more `--mem`, `--time=7-00:00:00`, `-p ps`, `%32`; (3) carry the two IT stems above; (4) harvest ×4 `--merged-tag win_2026-10-06` (expected ES 1,163, FR 520, GB 1,240, IT 1,164); (5) final T02 integrity run; (6) CP-3c; (7) T07 viewers (add back origin offsets), T08. Update this box and the artifact (read it first, v89) at each step. Next free D-EU-145 / FINDING 292.

### Where things stand (2026-10-02 12:45 EDT)

- **🔴 FINDING 289 (plan §8, T06s part 1 audited PASS 12:45):** one cause for both directions. A storey with 0 flats (flats < storeys, `european_residential.py:2943-2950`) is folded into the storey below as one tall zone with one floor (`:2753-2762`, `:2858-2872`), and the extruder ignores the last member's span (`run_eu_s2_campaign.py:1169-1172`). Down (10-05 short): ES 26, FR 6, GB 11, IT 149 (IDF count). Up (10-05 correct, 10-03 **and 09-08** were short): ES 16, FR 169. So the official 09-08 Lyon EUI is biased high. 1 zero-floor flat (IT `97d478bc56840531`, geomeppy intersect) is a known limitation, `[OPEN]`. 8 stems differ by the core rule, accepted. **D-EU-143 (director, highest accuracy): every storey keeps its own zones; a multi-storey flat = one zone per storey.** CP-3c check 6 amended: floor z levels = data storeys, and each storey within 1 % of the ground storey, on all 4,113 stems. **T06s part 2 dispatched 12:45 (Sonnet):** fix, then rebuild of the down-class stems only (prepare `--only-ids` → `_win_2026-10-06a` → `12_drop_degenerate` → `<D>_win_2026-10-06`), gates G1–G7, writes `t06s_rerun_<D>.txt`, STOP.

- **Models (all audited PASS):** `openubem/outputs/eu_evidence/EU-11/<D>_win_2026-10-05/` for ES-MAD-BERRUGUETE (1,172 IDFs), FR-LYO-HAUTCOEURPENTES (522), GB-LDN-STDUNSTANS (1,240), IT-BOL-GALVANI2 (1,179). They carry: walls facing out (T06m–o), windows (T06k), flat count by floor area (T06p, D-EU-141), no degenerate slivers (T06q), FR/IT moved to a local origin (D-EU-142, FINDING 288; `origin_offset.json`: FR 641000/5069000 EPSG:32631, IT 685000/4928000 EPSG:32632 — T07 must add it back). Digests: `md5_2026-10-05.txt` (never the stale `idf_sha256` in `prepared_buildings.csv`). The 10-03 and 10-04 trees are superseded. **10-05 is NOT final: FINDING 289 stems get rebuilt into 10-06.**
- **Speed (OpenUBEM ≤ 32 CPUs, `%32`, `--time=7-00:00:00`, `-p ps`; never touch `5J_*` or other jobs):** fleets `/nfs/speed-scratch/o_iseri/fleets/EU11_<D>_win_2026-10-05/`, chained by `afterany`:
  - Madrid 1409616 — **done**: 1,171 of 1,172 (failed `30240a6694acd89b`, 21 m2 one-zone home, heat balance diverges, accepted as known limitation, in debug refs); 6 runs carry the known non-convex shading Severe (they complete). **Harvested** → `ES-MAD-BERRUGUETE_merged_win_2026-10-05/`: 1,164 rows, pooled 73.735044 kWh/m2 over 1,163 (not adoptable before CP-3c).
  - Lyon 1409617 — **done** 10:05: 522 of 522 ok, 0 failed, mean 1,174 s; 3 runs carry the known non-convex shading Severe (debug refs line 115). **Harvested** → `FR-LYO-HAUTCOEURPENTES_merged_win_2026-10-05/`: 520 rows, pooled 58.430105 kWh/m2 over 520 of 520 (not adoptable before CP-3c).
  - London 1409615 + re-runs 1410433 — **done** (~10:40): sweep 1,240 ok, 1 known non-convex Severe. **Harvested** → `GB-LDN-STDUNSTANS_merged_win_2026-10-05/`: 1,240 rows, pooled 77.460511 over 1,240 (biased, FINDING 289). 4J CSV `flat_counts_2026-10-05.csv` written (1,351 rows: simulated 1,240 = manifest, run_failed 0, undivided_excluded 0, not_residential 109, no_model 2).
  - Bologna **1410474** (10-05, `--mem=32G`): at 14:18 Speed clock 321 done, 32 running, 1 pending, 1 OUT_OF_MEMORY (`_261` = `366fc6fda9a1a946`, re-run at 64G in 1416442); 134 pending tasks of re-run stems cancelled at T05. 15:37 Speed clock: 398 completed / 32 running / 614 pending (sacct -X shows the pending range as ONE row; count pending with `squeue -r -j 1410474 -t PD -h | wc -l`). Mean 1,316.5 s over 398 → 646 × 1,316.5 ÷ 32 ≈ 7.4 h → ends ~23:00 EDT (the 14:20 "~15:00" was wrong, it counted the pending row as 1 task). **16:21 Speed clock (latest): 440 completed / 31 running / 573 pending, 1 OOM (`_261`), no other failure; mean 1,395.6 s over 440 → 604 × 1,395.6 ÷ 32 ≈ 7.3 h → ends ~23:40 EDT Fri 2 Oct.** The 10-06 arrays (1,496 tasks) start as it frees slots; if they run as long as Bologna's (~1,396 s), they need ~18 h more → about Sat 3 Oct 18:00 (unmeasured until their own tasks complete). Then: carry its out/ to 10-06 on remote (tar from `EU11_IT-BOL-GALVANI2_win_2026-10-05/out` to `…_win_2026-10-06/out`, excluding the 183 stems of `openubem/outputs/eu_evidence/EU-11/division_residual_2026-09-29/t06s_rerun_IT-BOL-GALVANI2.txt` (identical to session scratch `xout_IT-BOL-GALVANI2.txt`, which only adds a `./` prefix for tar `--exclude-from`) and `./366fc6fda9a1a946`; 47 re-run stems that started on 10-05 are NOT carried).
  - **10-06 re-runs (T05, submitted 2026-10-02):** London 1416438 (1–1,037), Madrid 1416439 (1–243), Bologna 1416440 (1–183, 32G) + 1416442 (index 184 = `366fc6fda9a1a946`, 64G), Lyon 1416441 (1–32); 1,496 tasks, all `%32`, 7-day, `-p ps`. At 14:18 all PENDING on the account cap (64 CPUs: 32 held by another project's 1409235, never touch; 32 by 1410474). They start when 1410474 frees slots. Measure ETA from sacct once tasks complete (remaining × mean ÷ 32). Remote fleets `/speed-scratch/o_iseri/fleets/EU11_<D>_win_2026-10-06/` (fleet.lst = run list; out/ carried: ES 929, FR 490, GB 203, IT pending). Local `fleet.lst` = run list, original kept as `fleet_t06s_build.lst`; `speed_jobs.txt` written. Watcher: the old session's background watcher dies with that session — **a new session must re-arm its own** (bash loop: `sacct -j 1410474,1416438,1416439,1416440,1416441,1416442 -n -X -P -o JobID,State` every ≥ 30 min via `ssh … "bash -lc '…'"`, exit on FAILED/OUT_OF_ME/TIMEOUT/NODE_FAIL except `1410474_261`, or when no 1410474 row is RUNNING/PENDING; run_in_background with timeout ≤ 7,200,000 ms, so ≤ 3 polls of 35 min each; template in session-3deea9b8 scratch `t05/watch2.sh`). Failure sweep: delete `out/<stem>`, resubmit that index with more memory.
  - Health check: `bash /nfs/speed-scratch/o_iseri/stage1005/health.sh` (states, means, silent tasks with their CPU). Sweep: `bash /nfs/speed-scratch/o_iseri/stage1005/sweep2.sh <D>` (ok / notok / Severe kinds over every IDF stem). Run both over `ssh o_iseri@speed.encs.concordia.ca "bash -lc '...'"`. Dead-task rule: silent > 10 min AND CPU stopped → cancel, delete `out/<stem>`, resubmit that index; CPU = elapsed → leave it. CPU by raw id: `scontrol show job <id>_<i>` → `sstat -j <raw>.batch -o AveCPU`.
- **Harvest code (T06r, audited PASS):** `python scripts/cluster/harvest_eu11_merged.py --district <D> --merged-tag win_2026-10-05` (fetches `out/` over ssh, checks every IDF md5, leaves out the 80 undivided homes of `division_residual_2026-09-29/undivided_excluded_2026-10-05.csv`). Local `speed_jobs.txt` is written in each 10-05 folder. Expected rows: ES 1,164, FR 520, GB 1,240, IT 1,167.

### Next steps in order

1. ✅ DONE (T01–T05 of the integrity plan; kept for history). **T06s part 2** (plan §8): audit when the Sonnet reports. Check the progress log, gates G1–G7 pass/fail with values, the changed set equals the down class, unchanged stems byte-identical to 10-05, only planned files touched, and the 2 debug-register entries. Then dispatch **T06u** (plan §8: `plans3D` pages redrawn from 10-06, owner "yes please" 13:00, Sonnet) and audit P1–P6 before submitting re-runs. Then stage `EU11_<D>_win_2026-10-06` on Speed (copy 10-05 out/ for unchanged stems as was done for London), re-run only `t06s_rerun_<D>.txt` (`%32`, 7-day, `-p ps`, within 32 CPUs alongside Bologna), and re-harvest all four (the harvest code needs the 10-06 tag and md5 list: small T06t task).
2. **NOW:** re-arm the watcher → Bologna 1410474 ends (~23:40 EDT, measured 16:21) → carry IT out/ (above) → sweep failures of 1416438–1416442 → measure ETA → when all end: integrity plan T06 harvest `python scripts/cluster/harvest_eu11_merged.py --district <D> --merged-tag win_2026-10-06` ×4 (expected rows ES 1,163, FR 520, GB 1,240, IT 1,164; 4 broken-shell homes of FINDING 291 dropped) → final T02 integrity run on the harvested tree → T07 CP-3c. Update the artifact progress section ("Simulation progress on Speed", added v87) at every check.
3. **New plan in force: `implementation/PLAN_eu-model-integrity-2026-10-02.md`** (owner 13:05: "check other neighbourhoods for similar errors before submitting" + "prepare an implementation plan"). Order: T01 = T06s part 2 audit; T02 = integrity sweep of all 4,113 models (13 physical checks against source data, validated on 10-05); T03 = director triage, **no Speed submission before it is signed**; T04 = plans3D from 10-06 (owner "yes please", = residual T06u); T05 = re-runs; T06 = 10-06 harvest code; T07 = CP-3c. Step 1's staging and submission now wait for T03 and T04.
   - **State at 13:40:**
     - T01 audited: 1,495 stems rebuilt into `<D>_win_2026-10-06` (ES 243, FR 32, GB 1,037, IT 183). **D-EU-144: all 1,495 are re-run.**
     - T02a script built (`scripts/eu21/13_model_integrity.py`). On 10-06, GB and IT are clean on storeys; ES and FR differ only because `storey_count` is not the storey source the build uses.
     - **T02c dispatched (Sonnet):** I1/I4 reference = the build's storey rule, I6 = outdoor roofs plus lower-block adiabatic roofs, I8 = the allocation rule, I10 implemented, new I13 codes.
     - **16:15:** T04b PASS (pages show real flat count; `plans3D/archive/PLANS_<D>_2026-10-06.html`). Owner: "ok continue to the end", "please handle all for all neighbourhoods", "i closed gsscanada sessions, can you handle by yourself" → T05 done without a page stop; **no peer packages any more**. Speed folders `EU11_<D>_win_2026-10-06` staged (unchanged stems' 10-05 `out/` carried, IT carry waits for 1410474). Jobs: London 1416438 (1,037), Madrid 1416439 (243), Bologna 1416440 (183) + 1416442 (`366fc6fda9a1a946` at 64G), Lyon 1416441 (32); 134 pending 1410474 tasks of re-run stems cancelled. Local `fleet.lst` of 10-06 = run list, `speed_jobs.txt` written. Watcher `scratchpad/t05/watch.sh`. Next: when 1410474 ends, carry IT out/ (exclude `xout_IT…txt` + 366fc6…), sweep failures, measure ETA, then harvest ×4, CP-3c, final T02 (integrity plan §8 T05 entry).
     - **15:40:** T02e, T06b, T06c audited PASS; **T03 SIGNED** (0 unexplained fails on 10-06; 13 named). T04 pages built (P1–P4, P6, P7 pass) but they count zones as flats on the 1,495 rebuilt homes → T04b (show `dwellings_used`, label upper floors) dispatched. Then show pages to owner (STOP), then T05. Bologna 1410474 ~23:00; `_261` (`366fc6fda9a1a946`) out of memory at 32G → T05 re-runs it at 64G. T05 uses `t06s_rerun_<D>.txt`, NOT `changed_stems.txt` (lists the whole tree).
     - **15:05:** T03c done; T03 triage written in integrity plan §8 (signed once T02e reports clean). FINDING 291: 5 undivided courtyard homes drawn filled in (not simulated, no effect) + 4 homes with a broken shell (no roof / no floor / doubled floor: ES 722e9de69cd55e76; IT 7e4f0c98576b5d81, 97d478bc56840531, 595675e5f53ef10b) left out of results (T06b) and not sent to Speed. T02e + T06b dispatched in parallel (Sonnet). Then T04 plans3D (STOP for owner).
     - **14:45:** T02d, T03a, T03b, T06 audited (integrity plan §8). The 16 Madrid homes are right in 10-06 (Catastro storey count); the check's reference was wrong → T02e (apply the Catastro side-car in the check, re-run T02 on 10-06). 7 stems: 1 accepted; 6 in three geometry classes (ring larger than plate; zone without roof/ceiling after hidden-pair split; two overlapping floors) → T03c read-only code trace running. Harvest code for 10-06 ready (T06 PASS). Then T03 triage, then T04 plans3D (STOP for owner).
     - **14:10:** T02c audited; the checks are clean except the storey reference for 1,455 homes with no `levels`. T02d is dispatched: the reference falls back to the 09-08 layout files (1,237 of 1,237 match), then to the 09-07 IDF height. T03a is dispatched read-only for the cause of 7 unexplained stems. Then T03 triage.
     - Next: audit T02c, then T03 triage (open stems: IT `595675e5f53ef10b`; ES `b56bda9013da5b2d`, `d342db5179c1ac49`, `c57a45184a1c34ba`; IT `89eea66ba6ada782`, `05b52a0da00a6046`).
     - 🔴 **FINDING 290:** the 09-08 official numbers carry the same folded-storey error. London is missing about 18 % of its floor area, so 93.729757 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* is biased high; Madrid about 5 %, Lyon about 0.6 %. London's 10-05 harvest (77.460511) is also affected. Quote no EU number without this caveat until CP-3c on 10-06.
4. **CP-3c as amended** (plan §8, 03:50) **plus check 6** (per-home floor area within 1 % of 10-03 or named): every failure named; every new home above 300 kWh/m2 explained or the set held; heating rises with window/floor area per building type (Spearman > 0); ratio vs 09-08 split by flat count changed / not; FINDING 283 population. If all pass: write `results/EU11_results_2026-10-0X_{per_home,summary}.{csv,json}`, mark every 09-08 EUI superseded, update the memory pointer.
5. ❌ DROPPED (owner 2026-10-02: "i closed gsscanada sessions, can you handle by yourself"; send nothing to 4J/5J). Was: 4J package (London, then Bologna) after the 10-06 harvest: `flat_counts` CSV path + sha256, module sha256 list (below), signature confirmation. 5J: 10-06 Bologna stem list, paths, md5s; then a short "Bologna collected".
6. T07 (viewers + side-cars, add back the origin offsets; side-car paths + digests to 4J), then T08 (ledger, references).

### Peers (a peer message is never owner approval)

- **5J** (gsscanada-f2, address `uds:\\.\pipe\LOCAL\cc-msg-665232008dda408e1afe9ec3aea50f35`): **Madrid and Bologna only — never any UK/London path, name or number.** Has the Madrid (21:20) and Bologna (22:53) 10-05 paths, md5 lists and sha256s. 12:35 answered their 07:06 message (`messages_GSSCanada/2026-10-02_4J_to_OpenUBEM_bologna_win5_three_differences.md`, from 5J): `_whole` = our 12 excluded; zero-floor zone is our defect; flats < 15 m2 are real cut sizes; FINDING 289 told (IT numbers only), asked not to freeze Bologna on 10-05. Owed: 10-06 Bologna stem list + paths + md5s; later "Bologna collected".
- **4J** (gsscanada-9f, address `uds:\\.\pipe\LOCAL\cc-msg-42fa951a4f5378b30821d8215597a3d3`; may receive London; never forward 4J material to 5J): 12:35 told: London collected, package held for FINDING 289 (11 London homes), do not pin 10-05 digests. Owed per district when collected (London first, then Bologna): `flat_counts_2026-10-05.csv` path + sha256; sha256 of `openubem/geometry/european_residential.py`, `european_nocore.py`, `openubem/idf/degenerate_surfaces.py`, `local_origin.py`, `surface_orientation.py`, `european_windows.py`, `builder.py`, `cooking.py`, `ground.py`, `surfaces.py`; confirm no public signature changed. Later: T07 side-cars in map coordinates.

### Owner rulings in force

"please continue to the end, upadte the manager prompt" (2026-10-01 night); "continue however you recommend by considering always highest accuracy"; "ok continue to the end"; fix walls + windows + flat counts, then cancel/clean/re-run; flat count follows floor area (D-EU-141 (a)); undivided homes are not simulated and get their own colour (D-EU-139). Always update the artifact https://claude.ai/artifact/PB9MoeVTUVTemPmnXJDnBs (v89; local source `scratchpad/eu_status.html` of session 3deea9b8; a new session must `Artifact action=read` that URL first and build on what comes back) and this prompt at each step. Next free D-EU-145 / FINDING 292.

### History (newest first)

**2026-10-03 06:01 (Speed clock) Handover #2: Bologna 1410474 ended (3 OOM, 2 re-queued, 1000 at 200G), IT carry done, 10-06 arrays nearly done (London, Madrid complete); see Latest state at the top of this box.** **16:21 (Speed clock) Handover to a new session: 1410474 at 440 done / 31 running / 573 pending, ends ~23:40; no new failures; artifact v89; watcher must be re-armed by the new session.** **14:20 (Speed clock) Status: 1410474 at 321 done / 32 running / 614 pending (not 1; corrected 15:37), ends ~23:00; 10-06 arrays all pending on the account cap; no failures. Artifact v87 adds a per-city "Simulation progress on Speed" section.** **16:15 T04b PASS; T05 submitted (1416438–1416442), peers closed by owner.** **15:40 T03 signed; T04 pages built, flat-count label fix T04b dispatched.** **15:05 T03c audited; T03 triage + FINDING 291 (4 broken-shell homes left out); T02e + T06b dispatched.** **14:45 T02d/T03a/T03b/T06 audited; T02e written (Madrid side-car reference); T03c dispatched (geometry fault causes).** **14:10 T02c audited → T02d (storey reference fallback) + T03a (7 stems) dispatched.** **13:40 T06s part 2 audited (PASS, 1,495 rebuilt; D-EU-144 re-run all). T02a audited: check refinements needed → T02c dispatched. FINDING 290: 09-08 official numbers have the folded-storey error too (London ~18 % floor area missing).** **13:05 Owner: check every neighbourhood for similar errors before submitting, and write a plan → `PLAN_eu-model-integrity-2026-10-02.md` (integrity sweep T02, no submission before T03 triage).** **13:00 Owner "yes please": redraw plans3D from the corrected 10-06 models → T06u written (after T06s part 2 audit, before re-runs).** **12:45 T06s part 1 audited PASS: one cause (a storey with 0 flats folds into a tall zone with one floor); up class = 10-05 correct, 09-08 Lyon short too. D-EU-143: one zone per storey always. Check 6 amended (storey-by-storey). Part 2 dispatched (Sonnet). Bologna re-measured: ~23:05.** **12:35 London re-runs done; London swept (1,240 ok) and harvested (77.460511 over 1,240); 4J CSV written (counts match manifest). 🔴 FINDING 289 (from 5J's Bologna note): the 10-04 flat-count rebuild changed floor area in ~370 homes (merged storeys → one tall zone; Lyon 166 gained area); all 10-05 pooled numbers biased; T06s part 1 dispatched (Sonnet). 5J answered (IT only), 4J told package held. Bologna running, ≥ 21:45.**

**10:05 Lyon done: 522 of 522 ok, 0 failed, 3 known non-convex Severe; harvested 520 rows, pooled 58.430105 over 520 (not adoptable before CP-3c). London re-runs 1410433 running (10); Bologna 1410474 pending after them. Owner asked about plans3D: stale (10-01), redraw recommended, awaiting answer.**

**07:10 Lyon 442 of 522 done, 0 failed, mean 1,013 s (≈ 07:50). Status sent to both peers: 5J (Madrid done, Bologna ≈ 01:00 EDT 3 Oct; no London content), 4J (London package after the 10 re-runs, status values, no courtyard status; Bologna after).**

**06:57 Lyon 427 of 522 done, 0 failed, mean 997 s; silent tasks all alive (CPU = elapsed). 95 left ≈ 50 min plus tail → Lyon ≈ 08:00; then London re-runs, then Bologna.**

**05:00 Lyon 250 of 522 done, mean 859 s and rising (bigger homes later in the list); 8 tasks silent 13–48 min but CPU = elapsed (alive, checked by raw job id `scontrol show job <id>_<i>` → `sstat -j <raw>.batch`). 272 left ≈ 2.0 h → Lyon ≈ 07:00; Bologna after. Watch running (`stage1005/health.sh` now prints CPU of silent tasks).**

**03:45 Madrid finished (1,171 of 1,172; 6 known non-convex shading Severe) and harvested: `ES-MAD-BERRUGUETE_merged_win_2026-10-05`, pooled 73.735044 over 1,163 of 1,164 (not adoptable before CP-3c; 241 ratios outside 0.8–1.25 to explain). Lyon running (≈ 05:20), Bologna ≈ 22:30 EDT 2 Oct.**

**01:50 T06r written (harvest of 10-05: all IDF stems not just fleet.lst, 22 more undivided homes left out — ES 8, FR 2, IT 12 — fresh IDF digests, 4J status file) and dispatched.**

**01:30 Madrid 764 done, 1 FAILED (`30240a6694acd89b`, 21 m2 one-zone home, heat balance diverges; known class, accepted, not re-run; registered in debug refs). Measured: Madrid ≈ 03:30, Lyon ≈ 07:55 EDT 2 Oct, Bologna ≈ 01:00 EDT 3 Oct.**

**23:55 check: Madrid 281 of 1,172 done, mean 934 s, 0 failed, no silent task; 891 left ≈ 7.2 h → Madrid ≈ 07:10 EDT 2 Oct. Watch restarted (30 min, health script `stage1005/health.sh`).**

**22:53 T06q B2 audited PASS (Bologna: 0 slivers left, none deleted, shifted 685000/4928000); Bologna 10-05 on Speed as 1410474 (32G); 5J sent Bologna files; 4J told 10-05.**

**22:55 T06p item 5 done + audited PASS (IT 10-04). London 10-05 finished with 10 out-of-memory tasks, resubmitted at 32G (1410433); Madrid/Lyon pending raised to 16G; registered in debug references. T06q B2 (IT) dispatched.**


**🔴 21:05 (Speed clock; the 22:50/22:55 stamps were wrong readings) T06q B1 audited PASS (plan §8): 10-05 trees ES 1,172 / FR 522 (shifted, offset 641000/5069000) / GB 1,240, md5 checked on Speed; 0 events left; Madrid 647 slivers in 58 homes deleted (largest 0.105 m2); gate (c) ruled met (London slivers were already gone with the 196 rebuilt homes). Submitted London 1409615 → Madrid 1409616 → Lyon 1409617 from 10-05.**

**🔴 22:55 T06q A2 audited PASS (plan §8): London 40/40 stems equal EnergyPlus; director re-check Lyon 180/180, Bologna 53/53 on byte-identical `_fix_2026-10-01` runs. FINDING 288: at UTM coordinates EnergyPlus's plane test reads some real vertical walls as lines (rounding noise ~5e-4 > 1e-4), cuts them to 3 corners, Severe error; Lyon 15 homes, Bologna 1, none in Madrid/London; do NOT delete them. D-EU-142: shift FR + IT to a local origin (1 km-rounded constant, `origin_offset.json`, T07 must add it back), then delete slivers only; output `_win_2026-10-05` (not 10-04). Part B1 (ES, FR, GB) dispatched 22:50 (Sonnet); B2 (IT) after the T06p item-5 executor finishes IT 10-04. Swaps on Speed now come from 10-05: ES changed stems → release 1407631; FR all 522 stems → release 1407630; GB changed stems re-run. 5J told 22:55 (ES/IT only, 10-05 name, Bologna shift). 4J owed paths now read 10-05; tell 4J at delivery. Next free D-EU-143 / FINDING 289.** **🔴 20:10 T06p dry count audited PASS (plan §8 director audit): homes whose flat count changes ES 114/1194, FR 486/530, GB 196/1240, IT 1111/1220; flats under 15 m2 ES 22→3 (observed, accepted), others →0. Rebuild (item 5) dispatched, ES first → `<D>_win_2026-10-04` + dwelling_counts CSV + changed_stems.txt + md5 list. Speed: Madrid 1407631 now afterany London 1407629; Lyon 1407630 HELD, afterany Madrid; release Lyon only after its 486 IDFs are swapped. When ES 10-04 is ready: swap Madrid changed stems on Speed before 1407631 starts (~01:40 2 Oct). 5J acknowledged, Madrid runs on 10-03 go ahead there.** **🔴 19:50 4J follow-up answered by message: 4J drops C2 + 410-cell run, repeats only London + Bologna appliance/hot-water; owed to 4J at 10-04 audit: paths + sha256, per-building CSV (building_id, old_count, new_count), sha256 of changed modules (european_residential.py, idf/builder/cooking/ground/surfaces.py, new european_windows.py, surface_orientation.py) for their ENGINE_DIGEST_PIN re-pin, interface re-confirm (no public signature changed so far). Owner asked flat-count update also to 5J: sent 19:50 (ES/IT only, rule + status + what follows: Madrid changed-stem list, 10-04 paths + md5, per-building table).** **🔴 19:30 4J (gsscanada-9f, may receive UK) answered, file `messages_GSSCanada/2026-10-01_OpenUBEM_to_4J_neighbourhood_setup_what_to_repeat.md`: repeat appliance/hot-water loads London + Bologna after new counts; C2 + layout run only if kept. Correction: London counts are imputed too (`_gb_row_outcome` :410), so T06p changes London; audit must check GB/FR changes. 4J also waits for new layout side-cars (T07).** **🔴 19:05 5J answered (ES/IT only, no UK): counts change under D-EU-141 (a); Madrid changes only for sliver joins (<5 m2) and shared Catastro ids, all other Madrid IDFs byte-identical 10-03 → 10-04 so 5J may start Madrid on 10-03; Bologna changes almost entirely (all imputed), 5J holds it; Madrid stem list + 10-04 paths/md5 to follow after T06p dry count audit; no Bologna hour promised (earliest 2 Oct).** **🔴 18:30 ETA measured: London 1407629 48/1240 done, mean 699 s/task (sacct Elapsed, completed only), 1,192 left ×699/32 = 7.2 h → ~01:40 2 Oct; Lyon 1407630 and Madrid 1407631 pending in chain, measure when each starts. T06p Sonnet still on dry count.** **🔴 18:20 D-EU-141 taken as (a) on owner "ok keep going as you continue" (reply to the recommendation): T06p in plan (flat count = area ÷ archetype a_c_ref_m2/n_apartment; Catastro join <5 m2 = missing, shared ids split by overlap); Sonnet doing rule + dry count, STOP before rebuild. Madrid array 1407631 runs third in the chain; changed Madrid homes re-run from `_win_2026-10-04`. Next free D-EU-142 / FINDING 287.** **🔴 18:05 T06o done + director audit PASS (probe 0.05 m inward ES 9 / FR 1 / GB 0 / IT 4; pairs same-direction 0; floors down, tops up; window = wall 100 %; md5 unchanged). Staged `EU11_<D>_win_2026-10-03`; 10-02 samples cancelled + out/ deleted (16 finished: 0 fatal, 4 with non-fatal degenerate-sliver Severe). Full arrays chained (afterany, ours ≤32): GB 1407629 → FR 1407630 → ES 1407631; Bologna NOT submitted, waits D-EU-141. 5J sent 10-03 paths + md5 (ES/IT only).** **🔴 17:50 (director). FINDING 285: T06m's centre probe + centroid fallback left a few hundred outdoor walls inward → T06n (5-point vote, then floor edge, then centroid) built `<D>_win_2026-10-03`, all gates pass except 13 same-direction shared-wall pairs → T06o (pair rule 4: larger vote margin wins) dispatched, rebuilds 10-03. 10-02 files superseded (Speed sample jobs 1407370–73 = error/warning gate only). Weather closed: horizontal IR = 0 harmless (tests A/B/C identical heating). FINDING 286: 77 buildings with flats under 15 m2 (Madrid 22, Bologna 55): archetype n_apartment used at any size + Catastro sliver joins; remedy = owner decision D-EU-141 (recommend area ÷ archetype mean flat area, sliver joins = missing). Next after T06o audit: stage 10-03 on Speed, full arrays chained GB→FR→ES→IT (ours ≤32 CPUs), Bologna held until D-EU-141. 5J told (Madrid/Bologna only, no UK ever). Next free D-EU-142 / FINDING 287.** **🔴 17:05 T06m done + director audit PASS (plan §8): 0 inward walls, all shared-wall pairs opposite, floors down, roofs up, windows match walls, md5 unchanged. Staged on Speed `EU11_<D>_win_2026-10-02`; 10-home sample per district = jobs 1407370–73 (%7, ours ≤32 CPUs, 5J has the other 32), watcher btl7dr3a6. Weather check still open: EPW horizontal IR = 0 every hour (sky tests 1407338/39/44); decide before full arrays (`--array=11-N`).** **16:20 FINDING 284: every outdoor wall in every EU model (09-08 published, no-window 10-01, windowed 10-01) faces into its own room; EnergyPlus keeps the wrong azimuth (plan §8). **Owner ruled ~17:00: fix walls, then cancel + clean every existing EU run (no-window 10-01 and win sample) and re-run windowed only (`_win_2026-10-02`).** T06m dispatched to a Sonnet executor. 17:15: all EU runs cancelled, window sample and unfinished no-window outputs deleted; finished no-window outputs kept, never quote. Root cause found (CCW footprint into geomeppy, `run_eu_s2_campaign.py:1806`); fix task T06m drafted in plan §8 (surface-by-surface re-orientation of fix + win fleets → `_2026-10-02`). 5J author said yes for Madrid/Bologna; that is not our owner ruling. Next free D-EU-141 / FINDING 285.** **⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡ No windows in any EU model (2026-10-01 15:22 EDT, director).** FINDING 282 (plan §8): 0 window objects in every EU IDF of every vintage (09-03 → 10-01); `build_idf_for_building` (`run_eu_s2_campaign.py:1843`) has no window step, only the S0 box (`european_box.py:189`) had TABULA windows; no decision record says to omit them. Owner: "we need to add basic window-to-wall-ratio, as standard one". TABULA window area, U and g per archetype already in `tabula_archetypes_{es,fr,gb,it}.json`. Owner ruled `D-EU-140 (a)` (library share per building type): plan task T06k written, Sonnet executor builds `<D>_win_2026-10-01` (windows added to the exact IDFs of the 10-01 set, geometry untouched); then 40-home Speed sample, full arrays, harvest of the windowed fleet. GSSCanada 5J told; 5J will use our `<D>_win_2026-10-01` IDFs as their Model A base (Madrid + Bologna only, never UK content). When built, send gsscanada-f2: the two folder paths and windowed results manifest paths, whether every non-window object (zone names, floor areas, schedules) equals the source IDF (only windows + one glazing construction + material added; note some sources are t06f/t06g/recut, not only `fix_2026-10-01`), and the md5 of `windows.csv` per district. **16:10 update:** T06k done and audited (plan §8 'T06k audit and Speed staging'): 4,113 windowed IDFs, value-identical to source except windows, schedules byte-identical. Staged on Speed as `EU11_<D>_win_2026-10-01`; 40-home sample jobs 1407032 (ES) / 1407033 (FR) / 1407034 (GB) / 1407035 (IT), watcher `scratchpad/watch_win.sh`. Gate: all COMPLETED + 0 window Severe → submit full arrays `--array=1-N%32 --time=7-00:00:00 -p ps` per district (sample indices already done; skip them or let `out/` be overwritten). Owner: no-window runs are KEPT as reference (Bologna 1405559/1406674 at Nice=1000), windowed fleet = published. 123 preflight-flagged homes (old ZERO_AREA, unchanged since source) run as they are. FINDING 283: 90 homes with no outdoor wall (IT 71) — watch at CP-3b. 5J sent paths, identity, md5 (ES a3edc82e…, IT 232134d1…); results-manifest path follows after harvest. Harvest needs the new `win` tag (no 09-08 carry). **15:55 T06l audit:** windowed harvest code done and audited PASS (plan §8 T06l); harvest `--merged-tag win_2026-10-01` after `speed_jobs.txt` is written. Next free D-EU-141 / FINDING 284.

**⚡⚡⚡⚡⚡⚡⚡⚡⚡ Undivided homes leave the simulation (2026-10-01 14:20 EDT, director).** Owner ruling `D-EU-139`: "if a building is not divided, exclude from the simulations ... specifcy them wit hdifferent color undivided buildings" in outputs_3D and plans3D. 58 homes (Madrid 15, Lyon 7, London 0, Bologna 36) listed in `division_residual_2026-09-29/undivided_excluded_2026-10-01.csv`; the 4 in fleets cancelled on Speed (`1405481_202` was running, `1405556_736`, `1405559_27`, `1405559_119` pending; arrays checked intact). Plan T06j: two Sonnets in parallel — item 1 harvest drops them (`UNDIVIDED_NOT_SIMULATED_D-EU-139`), items 2–3 new colour in plans3D + outputs_3D and regenerate (V1–V3: only the 58 change). Next free D-EU-140 / FINDING 282. Both audited 14:27 (§8): harvest drops the 58, magenta "Not divided — not simulated" on all plans3D and outputs_3D pages, every other home unchanged. 14:40: Bologna split into `1405559` (odd) + `1406674` (even, `8-1088:2%32`) to use all 64 CPUs (§8); harvest job map updated. Next: FAILED sweeps; when all jobs end, harvest `--merged-tag 2026-10-01` ×4, compare with reasons, self-sign CP-3b, write `results/EU11_results_2026-10-01_{per_home,summary}.{csv,json}` (owner ask 14:30; 09-08 versions already written, heating only — the models are heat-only, §8), then T07 repoints outputs_3D to the new numbers.

**⚡⚡⚡⚡⚡⚡⚡⚡ Plan pages redone in the r2 look (2026-10-01 14:10 EDT, director).** Owner rejected the four `plans3D/PLANS_<D>_2026-10-01.html` list pages (made by `eu18_emit_plan_pages.py`) and asked for the r2 template (3D district scene like outputs_3D, no EUI filter; reference `plans3D/archive/PLANS_GB-LDN-STDUNSTANS_nocore_2026-09-03_r2.html`). Plan T06i written (new `scripts/eu21/09_plans3d_from_idf.py`, reuses `build_html` of `08_district_viewer.py`, reads the simulated IDFs `_fix_2026-10-01` + `_t06f`, per-storey plates), Sonnet dispatched. Speed at 13:55: 707 of 2,276 done, 63 running, Bologna not started. T06g audited and shipped 14:05: 40 repaired IDFs swapped on Speed, 8 already-finished homes re-run (jobs 1406516 Lyon, 1406517 Madrid), `shipped_t06g.lst` written, harvest job map updated. Owner asked (14:15) to remember the plans3D template (memory `feedback_plans3d_template.md`). T06i audited 14:25, owner likes the new pages; Bologna undivided = 36 big courtyard blocks failing hard checks (parked rule-book work) + 56 true one-flat-per-floor homes (§8). Artifact v50 adds "Floor division applied" (owner ask): 4,160 homes, 98.6 % divided — several flats/floor 2,383 (57.3 %), one flat/floor 1,719 (41.3 %), not divided 58 (1.4 %); per city Madrid 813/355/15, Lyon 259/263/7, London 194/1,045/0, Bologna 1,117/56/36 (counted with `09_plans3d_from_idf.read_all` on `_fix_2026-10-01`; zones unchanged by T06f/T06g). Next: FAILED sweeps; when all jobs end, harvest `--merged-tag 2026-10-01` ×4, compare with reasons, self-sign CP-3b.

**⚡⚡⚡⚡⚡⚡⚡ Early EUI check done; 40-home fault found, repair running (2026-10-01 13:50 EDT, director).** T06d4 audited: on 626 finished homes the new EUI is 11–15 % below 09-08 (London 58.5 vs 65.1, Madrid 64.9 vs 75.9, Lyon 61.4 vs 72.3), floor area unchanged; the fall follows the 09-08 hidden-wall share (r 0.88–0.93; homes with no hidden wall stay at ratio ~1.02), so it is the T06c correction, not a fault. New fault `FINDING 281` / `D-EU-138`: 40 homes (Madrid 9, Lyon 2, London 1, Bologna 28) have floors between storeys facing the wrong way, left `Outdoors` (list `division_residual_2026-09-29/t06g_stems_director_2026-10-01.csv`). Plan T06g (repair + rebuild the 40, `shipped_t06g.lst` in harvest) and T06d5 (named reason per flagged home, by code) dispatched in parallel. Do NOT use `scontrol hold <job>_[list]` on an unsplit array: it holds the whole remainder (happened, released in a minute; debug ref §12). Next: audit T06g → swap the 40 IDFs on Speed, rm `out/<stem>` + resubmit the finished/failed ones → audit T06d5 → when all jobs end, harvest `--merged-tag 2026-10-01` ×4, re-run compare with reasons, self-sign CP-3b.

**⚡⚡⚡⚡⚡⚡ Harvest code ready, runs at the account cap (2026-10-01 13:10 EDT, director).** Account CPU cap is 64 (two `%32` arrays fill it; memory `reference_speed_account_cpu_cap`). Measured means: Lyon 28.5 min, Madrid 11.9, London 3.5, Bologna 09-08 32.1 → finish ≈ 10:00 EDT 2026-10-02 (Bologna is the bottleneck, still PENDING on AssocGrpCpuLimit). 13:10 state: Lyon 80 done / 32 R, London 168 done, Madrid 214 done / 32 R, 35 FAILED all resubmitted, no new failure. Swapped stems are listed per district in `EU-11/<D>_fix_2026-10-01/shipped_t06f.lst` (append at every later swap). T06d2 (harvest code: job lists, `_t06f` sha, `idf_variant`, `--merged-tag 2026-10-01`) done and audited; audit found the 29 09-08 pending homes (all in `fleet.lst`) would stay pending even on success → T06d3 done and audited (new result now checked first; tests 6/6; 09-29/09-08 dry-runs unchanged). Watcher `scratchpad/watch.sh` polls every 30 min. Next: FAILED sweeps → when all jobs end, add any new resubmit job ids to `TAGGED_DISTRICT_JOBS`, run non-dry `--merged-tag 2026-10-01` ×4, compare EUIs to 09-08, self-sign CP-3b.

**⚡⚡⚡⚡⚡ T06f done, stopped homes rerunning (2026-10-01 ~16:30).** T06f executor rebuilt the four fleet lists (`<D>_fix_2026-10-01_t06f/`, preflight clean on all 2,276, no fallback, zones equal); director audit passed (plan §8 'T06f — director audit'). 519 changed IDFs swapped on Speed (FAILED + not-yet-started only); the 35 FAILED homes (Lyon 1, London 23, Madrid 11) resubmitted as jobs 1405950/1405951/1405952. Next: at each FAILED sweep of 1405481/556/559, swap that stem's `_t06f` IDF if not already swapped, clear `out/<stem>` by name, resubmit; then T06d harvest. Next free D-EU-138 · FINDING 281.

**⚡⚡⚡⚡ All four on Speed (2026-10-01 ~13:00, director).** Madrid and Bologna STOPs ruled (`D-EU-136`): G10 restated by cause (sha equal + last-digit rounding + U1→divided repair; Madrid 449/454, Bologna 104/107), Bologna U1 homes `29765`/`30319` allowed (storey areas equal layout), and 5 homes that lose floor area held on their 09-08 models (`FINDING 280`). Jobs: Lyon **1405481** (249), London **1405523** (191), Madrid **1405556** (747), Bologna **1405559** (1,089); 2,276 cases, %32, ETA ≈ 31.6 h from 09-08 means. Pages: all four `PLANS_<D>_2026-10-01.html` done, `index.html` repointed, r6 swept. Next: T06d harvest (`FIX3_TAG="fix_2026-10-01"`) when all four finish. Plan §8 "director rulings Madrid + Bologna".

**⚡⚡⚡ Lyon on Speed (2026-10-01).** Lyon item 5 audited clean (G10 265/270, 1 allowed G9 exception, page in plans3D) → job **1405481**, 249 cases %32, ETA ≈ 5.2 h (09-08 mean 40.1 min). Ship **schedules/<stem>/ + weather/** with the IDFs (Schedule:File uses `../../schedules/`). Bologna, Madrid, London executors still building. Details: plan §8 `T06e item 5 — FR-LYO-HAUTCOEURPENTES director audit`.

**⚡⚡ State 2026-10-01 ~11:45 (director, supersedes the next paragraph on status).** T06e items 3–4 returned and audited (CP-3a): the clip removes the overlap on 20/20 trial homes, tests 124/124, fallback 0/20, but upper storeys lose floor (17 of 20 below 0.99, min 0.394). Director confirmed the cause and its size (`FINDING 279`, `D-EU-135`): `_extrude_zone_groups` (`surfaces.py:820-869`) stacks each flat's storey-0 outline through every storey, so ~1,770 published homes (Madrid 530, Lyon 192, London 130, Bologna 921 divided homes) do not follow their own layouts. Ruling in the T06e task: campaign-local per-storey extrusion (item 3(d), `surfaces.py` stays frozen), re-trial on 30 homes (4b, gates G1–G10), then item 5 rebuilds **all 4,160 homes**. 3(d)+4b done, CP-3a passed (G1–G3 30/30, G9 29/30, rulings in T06e). Item 5+5b running as FOUR parallel Sonnets, one per district (~12:30), each writes `t06e_gate_<D>.csv`, `fleet.lst` (longest first), its plans3D page, and its own §8 entry `#### T06e item 5 — <D> ready`; Speed folders `/speed-scratch/o_iseri/fleets/EU11_<D>_fix_2026-10-01/` pre-staged with `submit_recut.sbatch`. On each report: audit, tar+scp `idfs/`+`fleet.lst`, sbatch --array=1-n%32 --time=7-00:00:00 -p ps. Fix plans3D/index.html links after the 4th page. Next: grep `^#### T06e (items 3d-4b)` → audit CP-3a again → item 5 (every home, owner OK) → audit → item 5b plan pages in plans3D → 🛑 owner looks, gives go → T06d → Speed (ETA measured ~26 h for ~2,000 homes) → CP-3b. Owner: stop after the new numbers is proposed (rule book, bent walls later), answer pending. Owner 2026-10-01: stream districts to Speed, pages in parallel with Speed (no wait), longest first, local ≤10. Next free D-EU-136 / FINDING 280.

**⚡ State 2026-10-01 ~09:30 (director).** T06c finished and audited: §8 entry present, tests 33/33 + T04h 64/64, hidden
area 0 on 296 of 297, **but gate (3b) FAILS (57 of 297)**. Director traced it: **flats on the same storey overlap each
other** (`FINDING 278`, `D-EU-134`) — e.g. `way/435638870` 5 ground-floor flats, 859 m² of floor over a 285 m² footprint.
Also in the **current official 09-08 fleet: 85 of 4,171 homes** (loads inflated, EUI biased up; extra floor +1.3 to +6.1 %
per city), and T06c found walls between flats set outside on **1,160 of 3,874** non-candidates. Evidence:
`EU-11/division_residual_2026-09-29/zone_overlap_scan_director_2026-10-01.csv`. **`_fix_2026-09-30` NOT shipped.**
New task **T06e** written (plan §6, before T07; §7 "CP-3 amended 2026-10-01"); T06e items 1–4 (census, cause, fix +
fallback, 20-home trial, gate G1–G8) dispatched 2026-10-01 ~09:30; items 1–2 done (census reproduces the director's; cause = geomeppy
`intersect_match` at `surfaces.py:928`, 239 of 241 homes). `surfaces.py` stays frozen: **director ruling in T06e** = new clip step in
`run_eu_s2_campaign.py`; items 3–4 dispatched ~10:00. Next: `Grep -n "^#### T06e (items 3-4)"` →
audit trial (CP-3a) → dispatch item 5 (rebuild ≈ 1,500 homes, ≤ 5 local processes) → audit full gate → T06d (amended:
tag `fix_2026-10-01`, base `_merged_2026-09-08`) → Speed → self-sign CP-3b → tell owner the official set changes
beyond 297. Rule-book T04b still waits for this (both change IDF output).

**Owner overnight authority (2026-09-30 ~20:00, verbatim: "i will sleep so what i want from you to continue to the end based on your recommendations, thank you").** The director runs both plans to the end without waiting: audits, dispatches, Speed submissions, CP-3b and T05 signed by the rules in each §7, highest accuracy first. Stops only on a STOP the plans name (untraced drift, unexplained EUI ratio) and reports it.

1. **Residual plan** (`PLAN_eu-floor-division-residual-2026-09-29.md`) — T06 done and harvested 2026-09-30
   (§8 T06, last entry). **🛑 AT CP-3, new EUIs NOT adoptable — FINDING 277:** 220 of 279 rebuilt homes have
   walls/floors between flats written as `Outdoors` (outdoor-wall area ×1.56, EUI ×1.7–1.9); pooled EUIs would
   rise 4–8 % per city for a geometry defect. **CP-3 ruled 2026-09-30, owner verbatim "i recommend yes":** keep
   the 09-08 EUIs, `_merged_2026-09-29` not adopted. New tasks T06c (`D-EU-133`: scan for walls/floors facing
   another flat but set outside, cause per home, final pairing pass, rebuild 297 into `_fix_2026-09-30`, envelope
   gate) and T06d (harvest code) written; **T06c dispatched to Sonnet 2026-09-30, unfinished at the 2026-10-01
   handover — see ⚡ First action above** → director audit → T06d →
   Speed → CP-3b. T06c item 1 also scans the 3,874 non-candidates. **Standing owner ruling 2026-09-30, verbatim
   "ok continue continue however you recommend by considering always highest accuracy":** director signs CP-3b
   itself (rule in plan §7) and, if the non-candidates carry the defect, rebuilds and re-runs them (T06e, to be
   written); tell the owner the result. Owner note: nothing is published externally — say "current official
   numbers" (the 09-08 EUIs), never "published".
2. **Rule-book plan** (`PLAN_eu-rulebook-change-2026-09-30.md`) — T01–T04 done (T04 §8 line 267; audited
   2026-09-30: summary `rulebook_2026-09-30/dryrun_summary.csv` 12 rows, R3 on 102, hash drift reported, no
   leftover local workers). **🛑 AT CP-1, both T04 gates FAIL:** R0 moves 8 of 4,171 in class (580 hash drift,
   FINDING 275); RALL_G moves 26 of 3,208 (25 = R0 drift, 1 real leak `relation/12586384`, a k = 1 S1 home the
   guard does not protect). Best rungs of 460: R1_35 45 resolved / 3 worse; R2_33 48 / 0; R3 ≤ 2 of 102;
   RALL_G 68. **CP-1 ruled 2026-09-30 by the same verbatim sentence as item 1:** fix drift + guard S1 + re-run
   T04 on Speed. T04b (drift cause per home, S1 guard = relaxed rules only on the 460 candidates, Speed task
   list) and T04c (harvest, gates vs R0 of same code) written; **T04b is dispatched only after T06c is audited**
   (both change IDF output). Director signs T05 itself (most resolved, 0 worse). Every re-run on Speed.
3. **Bent-walls plan** (`PLAN_eu-bent-walls-2026-09-30.md`) — T01 PASS; CP-1 ruled: **D-EU-130 = YES**
   (owner 15:40 "yes continue": 88 V3 homes relabelled rule-following, label only, applied when bent-walls T05
   re-runs the census; 40 stay V3). T02+ waits for the rule-book plan's CP-3 (same cut code). Nothing to run now.

**Current counts (artifact shows current position only, never before/after):** follow the rules 3,208 · not
divided 102 · divided, break a rule 358 · wall bends 478 · cannot be checked 25 (of 4,171). Status page
`https://claude.ai/artifact/PB9MoeVTUVTemPmnXJDnBs` Version 43 (2026-10-01: four pages done; thin-surface fix in flight); the builder `page.py` was in the old session's
scratchpad — a new session re-reads the page (`Artifact read`) and republishes by `url`.
**Owner standing rules:** "always udpate the artifact and the manager prompt" at every stage; "continue to the
end" never skips CP-3; `model: "sonnet"` on every Agent call, fresh session each dispatch; ≤ 10 local processes;
never touch `wp4_*` jobs; `sstat` before any cancel; ETAs from `sacct` only.
**Side item done 2026-10-01:** OPEN-66 "room_layout not affected" correction written into the openings register (closing note of OPEN-66).
**Next free ids:** D-EU-138 · FINDING 281.

---

## ⚠ Status update — 2026-09-29, evening EDT (history of Thread C; the START HERE box above supersedes it on status)

**Thread C — EU floor-division residual plan, live.** Plan:
`docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-floor-division-residual-2026-09-29.md`
(state lives in its §8 progress log). Status page for the user: `https://claude.ai/artifact/PB9MoeVTUVTemPmnXJDnBs`
(rebuilt from the session scratchpad `page.py`; a new session publishes a replacement by `url`).

**Owner rulings in force (verbatim):** CP-1 approved at full scope (897 broken buildings; fixed ones
re-simulated on Speed). "yes, start without stopping if clean" — a clean T05 gate (0 regressions,
every candidate re-emitted) goes straight into the T06 Speed campaign; a regression or failed
re-emission stops at **CP-2**. **Always stop at CP-3**: the owner decides whether the new EUIs
replace the 2026-09-08 ones. "lets go continue to the end" does not skip CP-3.

**Done (all in §8):** T01 census (4,171 rows; V3 = 277 wraps + 138 wing bends); T02 mirror repair
(`D-EU-118`, 14 of 209 U1 recovered); T03 `D-EU-92` in the engine (`D-EU-119`, 51 U2: 13 pass,
38 best effort, 0 hard fail); T02b sliver drop (`D-EU-121`, U1 recovered 121 of 209, 88 still
rerouted, OK-100 unchanged 100 of 100).

**In flight:**
- T02b EnergyPlus proof on Speed, fleet `/speed-scratch/o_iseri/fleets/t02b_proof_2026-09-29/<D>/`,
  arrays `1401533, 1401542, 1401543, 1401544` (121 IDFs: Madrid 43, Lyon 16, London 8, Bologna 54).
  At 2026-09-29 ~20:10: 48 finished, 3 fatal, all Madrid (`2542f2907e276cf1` "CalcCoordinateTransformation:
  Invalid dot product"; `803d0afdbbbb83e9`, `c5e730d9efda6799` "Vertex size mismatch between base
  surface"). Measured mean 12.9 min per task; tasks pend behind other-project `wp4_*` jobs
  (AssocGrpCpuLimit) — never touch those. Harvest: count `eplusout.end` and
  `grep -l Terminated--Fatal out/*/eplusout.err` per district; fatal ids are excluded from T05; drop
  `[OPEN]` on the `eb12e1ba00541e12` debug entry if it completes; append the result to the T02b §8
  entry; register the new fatal signatures in the debug references.
  At 21:20: 4 fatal (the 3 Madrid above + Bologna `d1a9087437c27794` "CalcCoordinateTransformation:
  Invalid dot product" on a CEILING); `eb12e1ba00541e12` was running normally. Mean 13.7 min per task.
- T04 done and audited (§8 entry, 13 of 13 tests, planned files only): 55 improved, 716 unchanged,
  0 would_regress of 771.
- T05 step A done (`prepare --only-ids`, 14 of 14 tests). The executor stopped by design at step B
  waiting for `scratch/u1c_fatal_ids.txt` (manager writes it after the proof); then dispatch a NEW
  Sonnet session for T05 steps B–D. Owner, 2026-09-29, asleep: "keep goin until the end" — a
  paraphrase, so CP-3 still stops; CP-2 passes only if clean (ruling above).
- 2026-09-29 ~22:00, owner verbatim: "why we pass to the simualions, we need to solve these" (the 142
  still undivided and 340 still breaking a rule after the fixes), then "continue to the end lets go".
  T05/T06 ON HOLD. New task T04c (plan §6, CP-1b) dispatched to Sonnet: per home, does a rule-passing
  cut exist, or which frozen rule makes it impossible; plus why 88 lost cuts still reroute (84 of 88
  have paired surfaces that do not cover the same polygon, `pairs_skipped_coverage > 0`). After
  T04c: director writes fix tasks for fixable verdicts and runs them; rule-impossible homes keep
  best effort (no frozen rule changes without the owner); only then T05 → T06 → CP-3.
- 2026-09-29 ~22:20: T04c done and audited (390 of 390, pairs 379 of 379, 0 unchosen passing cuts).
  Verdicts: 573 near-miss storeys, 506 far, 226 cutter-lacks-move (one or two huge flats per floor,
  117 at k = 1), 31 rule-impossible; pairs 215 extra-vertex, 160 one-side-larger, 4 degenerate. Fix
  tasks T04d (pair repair, `D-EU-122`, run_eu_s2_campaign.py) and T04e (cutter moves, `D-EU-123`,
  european_nocore.py) dispatched to two Sonnets in parallel, ≤ 5 local processes each. Then CP-1c:
  audit, T04d EnergyPlus proof on Speed, straight into T05 if clean. Next free D-EU-124.
- Owner, 2026-09-29 22:10, verbatim: "always udpate the artifact and the manager prompt". At every stage,
  republish the status page https://claude.ai/artifact/PB9MoeVTUVTemPmnXJDnBs (Version 5 at 22:10:
  diagnosis section + fix 1 / fix 2 steps) and update this prompt.
- 2026-09-29 23:15: T02b Speed proof harvested — 121 of 121 ended, 117 clean, 4 fatal (`2542f2907e276cf1`, `803d0afdbbbb83e9`, `c5e730d9efda6799`, `d1a9087437c27794`; list in `scratch/u1c_fatal_ids.txt`, all four assigned to T04d). `eb12e1ba00541e12` now runs; `[OPEN]` dropped. Artifact Version 6. Still waiting on T04d and T04e executors, then audit → T04d proof on Speed → T05.
- 2026-09-29 23:40: T04e returned — 804 homes dry-run, 50 improved / 754 unchanged / 0 regressed; OK-100 unchanged; residual 519 (building, k) rows: still_far 403, near_miss 58, rule_impossible_c6 24, k1_lobed 17, k1_hole 17. Audit open: executor left `test_eu_recut_95pct_2026_09_08.py` unconfirmed and looked for `test_eu13b_dwelling_conservation.py` in the wrong folder (it is `tests/geometry/`); director is rerunning both. Artifact Version 7. T04d still running.
- 2026-09-29 23:58: T04d returned — 30 of 92 recovered (incl. all 4 proof fatals), 62 still rerouted; OK-100 only 96 of 100 (3 reroute, 1 `IDF_ASSEMBLY_FAILED_RuntimeError`, cause upstream of T04d). CP-1c NOT clean → director wrote **T04f** (`D-EU-124`: OK-100 bisect, remainder with nothing across → Roof/outdoor floor, sliver building cap 0.1 → 0.5 m², near-same boundary +1e-9) and dispatched a Sonnet. T04d proof of the 30 on Speed: arrays 1401774–1401777, 30 cases, width 32, remote `/nfs/speed-scratch/o_iseri/fleets/t04d_proof_2026-09-29`. Director is rerunning `test_eu_recut_95pct_2026_09_08.py` locally (1 process). `test_eu13b_dwelling_conservation.py` (in `tests/geometry/`) 46 of 46. Next free D-EU-125. Artifact Version 8. Path: T04f → audit → T04f proof on Speed → T05.
- 2026-09-30 00:15: T04f returned — 44 of 92 recovered; OK-100 still 96 of 100, cause = OPEN-66 guard `surfaces.py:940-941` (openings `PLAN_ten-items-close` T04), which blocks the `match()`-alone retry for **every** building because `_extrude_zone_groups` flags every zone `extruded` (`surfaces.py:867`) — the openings audit note 'room_layout not affected' is wrong; flag it to the openings arc after T04g lands. T04d proof: 12 of 30 done, 1 fatal (`2542f2907e276cf1`, ring spike out-and-back). Director wrote **T04g** (`D-EU-125`: narrow guard to pre-extruded zones only, spike removal in `_clean_ring_3d`, rebuild 92 + OK-100) and dispatched a Sonnet. Next free D-EU-126. Artifact Version 9. Path: T04g → audit → T04g proof on Speed (all recovered homes) → T05.
- 2026-09-30 00:25: T04g returned — guard narrowed (`surfaces.py`, flag taken before first extrusion), OK-100 **100 of 100**; 43 of 92 recovered (Bologna `33063` lost to spike step, accepted). Proof of the 43 on Speed: arrays 1401855–1401858, 43 cases, width 32, remote `/nfs/speed-scratch/o_iseri/fleets/t04g_proof_2026-09-30`; old T04d arrays cancelled. First result: `2542f2907e276cf1` fatal again — the saved IDF still has the spike though `_clean_ring_3d` fixes it when run directly, and T04g's scan missed 0° spikes → **T04h** dispatched (find the step that writes it back, clean last before save, fix the scan, rebuild `u1h`). Director's rerun of `test_eu_recut_95pct_2026_09_08.py` still running. Artifact Version 10. Path: T04h → audit → proof of changed homes → T05.
- 2026-09-30 00:35: T04h returned — cause: `_clean_ring_3d` ran the spike loop once before de-duplication; now repeats to a fixed point, plus a last `_clean_surface_rings` before `saveas`. 43 of 92, OK-100 100 of 100, new scan 0 of 9,092 on `u1h`. Proof: 41 on arrays 1401855–1401858 (`t04g_proof_2026-09-30`), the 2 changed (`2542f2907e276cf1`, `9ff518bfd78678e6`) on 1401895/1401896 (`t04h_proof_2026-09-30`). Mean run 26.5 min, longest 3 h 12 min (128 runs). T05 candidate sources widened in the plan (u1h + t04e improved). Artifact Version 11. Next: harvest proof → dispatch T05 (new Sonnet) if 0 fatal.
- 2026-09-30 02:25: Proof harvested — 41 of 43 ended, 0 fatal on final IDFs; 2 Lyon (`a585de39a07bcd04`, `93647659bf673ce1`, array 1401856 idx 4/5) alive at 2 h 06 min, AveCPU = elapsed — do not cancel. CP-1c clean. Plan amended: hard rule 6 notes the one T04g `surfaces.py` edit; regression gate (§4 item 6) no longer uses hashes for non-candidates (outcome, class, zone count, zone areas ±0.01 m², at_risk False, 0 scan flags). Recut test file 19 of 19 (1 h). **T05 dispatched** (new Sonnet, ≤10 local processes). Artifact Version 12. Next: audit T05 → if gate clean, T06 on Speed (arrays %32, 7-day) → harvest → STOP at CP-3.
- 2026-09-30 08:50: Proof closed — 43 of 43 ended, 0 fatal on final IDFs (2 Lyon finished at 2 h 24 / 2 h 31). The `Terminated--Fatal` in `t04g_proof_2026-09-30` for `2542f2907e276cf1` is the superseded copy; ignore it. T05 executor sat idle 02:20–08:19 (no writes), resumed 08:43 with 9 local workers; Madrid non-candidate check (1,085 homes, ~11/min) is the long pole, ~1.5 h. Artifact Version 13. Next: audit T05 → T06 on Speed → STOP at CP-3.
- 2026-09-30 T05 done, gate NOT clean → STOPPED at CP-2 for the owner. 297 candidates re-emitted (215 better class, 72 same class/new IDF, 9 byte-identical, 1 worse); 65 of 3,874 untouched homes moved slightly (57 tiny floor-area drifts 0.011–0.63 m², 7 improved by accident, 3 Lyon one-flat homes changed shape). Counts verified. Waiting on owner: recommend (a) ship 286 on Speed (drop 9 identical + `way/391276770` worse + `way/400445219` rerouted); untouched homes keep their old results. On yes: four arrays `%32` `--time=7-00:00:00` from the `EU-11/<D>_fix_2026-09-29/` trees minus the 11, then STOP at CP-3.
- 2026-09-30 09:42: Owner said "yes, ship the 286 on Speed". T06 submitted: arrays 1402184 Madrid 98, 1402185 Lyon 27, 1402186 London 50, 1402187 Bologna 111 (fleets `/speed-scratch/o_iseri/fleets/EU11_<D>_fix_2026-09-29/`, 11 dropped stems absent). 64 tasks running at submit. Harvest: count `eplusout.end`, `grep -l Terminated--Fatal`, then T06 harvest into `<D>_merged_2026-09-29` → STOP at CP-3 (owner decides on the new EUIs + the unfixable homes).
- 2026-09-30: Owner: artifact shows the current position only, no before/after. Counts now = 2026-09-29 census with the 286 shipped homes set to their rebuilt class (11 dropped keep old class): follow the rules 3,208 · not divided 102 · divided, break a rule 358 · wall bends 478 · cannot be checked 25 (of 4,171). Builder: scratchpad `page.py` reading `division_now_2026-09-30.csv`.
- 2026-09-30: Owner asked for an investigation/implementation plan before any rule change ("will we loose some homes that ones already resolved 3,208"). Written: `implementation/PLAN_eu-rulebook-change-2026-09-30.md` (R1 aspect 3.0, R2 spread 0.40, R3 zones for very large flats, U1 fix; safeguard D-EU-129 "stay if it passes"; dry run with/without the guard on all 4,171 before CP-1). Allocated D-EU-126..129, FINDING 272 (C12/C13 absent from the rule book), FINDING 273 (`plans3D/index.html` links deleted r5 pages). Next free: D-EU-130 / FINDING 274. Finished plans recovery-09-07, london-coverage-09-07, plan-homogeneity-09-07, recut-95pct-09-08 moved to `implementation/DONE/`, 56 citations repointed. Next: dispatch T01–T04 (Sonnet), independent of the T06 Speed runs; T07+ waits for the residual plan CP-3.
- 2026-09-30: Owner approved T01–T04 ("yes continue, if needed, use cheaper agents to execute"). T01 (baseline) and T02 (audit) dispatched in parallel to fresh Sonnets; T03 waits for T02 section 2, T04 waits for T01 + T03; STOP at CP-1 after T04.
- 2026-09-30: T01 audited PASS (baseline.csv 4,171 rows, class counts match, 0 null sha). T02 audited PASS (audit.md 5 sections; all 7 loads area-based; code untouched). New FINDING 274 (sheets print aspect 2.5 as "2") recorded in the plan; next free D-EU-130 / FINDING 275. T03 dispatched to a fresh Sonnet.
- 2026-09-30: T03 code audited: switch + guard added in 4 files, 0 comment lines, no writes to delivered trees; test (a) 550 bench plates identical; (b) 100 of 100 homes identical to the pre-edit code (director re-hash). New FINDING 275: 5 of 100 baseline-OK homes already differ from the shipped IDF before any rule-book edit (drift predates T03; delivered files untouched); plan test (b) reference amended to pre-edit code, T04 R0 now also reports hash drift (not gating). Next free D-EU-130 / FINDING 276. Same T03 agent finishing the test file + §8 entry (same task in flight); then T04 to a fresh Sonnet, STOP at CP-1.
- 2026-09-30: T03 closed PASS: test file tests/test_eu_rulebook_change_2026_09_30.py 4/4 pass (0 comments), fixture t03_pre_edit_hashes.csv 100 rows, one §8 entry. T04 dispatched to a fresh Sonnet; STOP at CP-1 when it returns, then director writes T05.
- 2026-09-30 11:50: residual T06 at 214 of 286 done (sacct), all 32 slots busy. Madrid 1402184_4/_8 OOM at 6G -> resubmitted as 1402967 with --mem=32G; 1402184_14 (fc1c83df2d9b8786) vertex-size mismatch 15 vs 16, not retried, keeps its 09-08 EUI (`fix_failed_carry`). Both registered in the debug reference. T06h (harvest code for `_merged_2026-09-29`) written into the residual plan and dispatched to a fresh Sonnet; director runs the harvest when squeue shows 0 `t06_` jobs, then STOP at CP-3. Rule-book T04 still running.
- 2026-09-30 12:50: residual T06 at 265 of 286 (sacct); 21 RUNNING (Bologna 19, Madrid 1402184_87 2 h 20, Lyon 1402185_12 3 h 08), 0 pending; sstat AveCPU tracks elapsed on both long ones, alive, do not cancel. Owner asked for the 478 bent-wall homes (V3) to get their own plan: written `implementation/PLAN_eu-bent-walls-2026-09-30.md` (D-EU-130 wing-bend-only label, D-EU-131 junction move/wall extension/straighten-then-slide, D-EU-132 C13-only guard, FINDING 276; next free D-EU-133 / FINDING 277). Measured on rulebook baseline.csv: 350 of 478 have C13 > 0, 128 have C13 = 0 (wing bends only), 0 of 3,192 OK have C13 > 0. T01 (read-only investigation) may run now; T02+ only after the rule-book plan's CP-3 (same cut code). Not yet dispatched.
- 2026-09-30 13:44: residual T06 at 281 of 286; 5 RUNNING (Bologna 1402187_25/54/83, Madrid 1402184_87 3 h 14, Lyon 1402185_12 4 h 02), all sstat AveCPU tracking elapsed, alive. Monitor b0k0jmo4o (900 s) replaces killed b94by2hzb. Rulebook T04 agent still running. Bent-walls T01 awaits owner go.
- 2026-09-30 14:00: owner "continue to the end" = go for bent-walls T01; queued until rulebook T04 local pool frees (~9 workers now, cap 10). Rulebook T04 pool: 8 of 45 rc 0; RALL rc 1, R0 + RALL_G killed at 3550 s, agent re-running R0 (orch_pool2.log 13:45). Speed residual 5 left, monitor b0k0jmo4o.
- 2026-09-30 15:15: owner "continue to the end, re-check the ~850 badly divided homes" (= 358 V1/V2 + 478 V3; plus 102 U). Rulebook T04 (358+102) still running: pool1 8 rc 0, pool2 13 started / 8 alive (orch_pool2.log logs starts only). Bent-walls T01 (478) dispatched now to a fresh Sonnet as ONE process (local 8 workers + 1 = within cap 10), stop CP-1. Speed residual: 1 left, 1402185_12 Lyon, sstat CPU 5:23 of 5:26 = alive.
- 2026-09-30 15:19: bent-walls T01 back. Audit: 13 of 478 homes read but given no row (465 covered, agent claimed 478); Madrid 7/5/8 section missing from summary; no engine file touched by T01; 71 straight_missed listed; 27 exceptions of the 128 named. Measured: 88 to 115 of 478 V3 homes labelled bent with no engine-counted bend (FINDING 276). Fresh Sonnet dispatched to add a no_bend row per home + the Madrid sample section, then CP-1 (D-EU-130).
- 2026-09-30 15:21: bent-walls T01 fix audited PASS: 478 of 478 homes have rows (13 no_geometry + 13 no_bend added), 128-set split unchanged 88/27 of 115, Madrid sample 7/10/43 vs 7/5/8 listed by id (plan allows), 71 straight_missed listed, FINDING 276 in §8, no engine file touched. STOPPED at CP-1. Asked owner D-EU-130, recommended: relabel the 88 homes with no engine-counted bend as rule-following (label only, no EUI change); the other 40 (27 exceptions + 13 no geometry) stay in V3. T02+ still waits for the rule-book CP-3.
- 2026-09-30 15:40: owner "yes continue" = D-EU-130 YES (88 relabelled rule-following, label only; 40 stay V3; applied when the census is re-run in bent-walls T05). Ruling written under CP-1 in the bent-walls plan §7. Bent-walls T02 waits for rule-book CP-3.

- 2026-09-30 16:00: session handed over; see START HERE box at the top.

**Next (⚠ superseded 2026-09-30 — see START HERE):** T05 (new Sonnet session: `fix_candidates.csv`, `prepare --only-ids` into
`EU-11/<D>_fix_2026-09-29/`, regression gate) → if clean, the manager submits T06 on Speed
(state case count and width 32; four arrays, `%32`, `--time=7-00:00:00`; harvest into
`<D>_merged_2026-09-29`) → **stop at CP-3**. After CP-3: T07, T08. Next free ids: `D-EU-122`,
`FINDING 272`.

**🔴 No local EnergyPlus (owner, 2026-09-29).** A local 20-process pool froze the owner's machine.
Every EnergyPlus run goes to Speed; the executor writes the IDF list and stops, the manager submits.
Local work of any kind is capped at half the machine (≤ 10 processes). Written into `CLAUDE.md:84`.
Speed fleet layout: `idfs/<stem>.idf`, `schedules/<stem>/*.csv` (Schedule:File paths rewritten to
`../../schedules/<stem>/<file>`), `weather/*.epw`, `fleet.lst`, `out/`; runner `submit_recut.sbatch`
copied from `/speed-scratch/o_iseri/fleets/EU11_<D>_recut_2026-09-08/`.

---

## ⚠ Status update — 2026-09-12 EDT (superseded 2026-09-29 on status; still the record of Thread B's exchanges)

**Thread B continued, three exchanges with `gsscanada-de`, all answered directly under the
2026-09-11 "help them whenever it asks" rule. Nothing on our side changed: no code edited, no IDF
rebuilt, no cluster job submitted, no published number touched, no repo file created. This session
was read-only apart from this handoff entry.**

**1. We sent them the 93 Bologna reroute IDs.** Extracted from the frozen manifest
`openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_merged_2026-09-08/it_bol_galvani2_manifest.csv`
(1,215 rows), `geometry_outcome = ..._INTERZONE_MISMATCH_REROUTED`:

```
28134 28473 28527 28696 28700 28721 28749 28917 28968 28969 29094 29108 29180 29211 29228 29437
29466 29643 29718 29788 29813 29822 30037 30139 30240 30319 30323 30384 30508 30570 30651 30817
30850 30912 30968 30988 31016 31035 31118 31281 31289 31401 31410 31461 31481 31500 31615 31661
31669 31716 31773 31774 31821 31854 31888 31916 31977 32008 32062 32073 32211 32233 32279 32280
32306 32372 32392 32453 32493 32524 32552 32556 32662 32668 32755 32797 32800 32860 32864 32981
33063 33080 33171 33193 33260 33354 33401 33412 33446 92926 93207 93387 93409
```

The tolerated (unsimulated, unrepairable by design) 10 were already with them:
`27931 29109 29171 29629 30001 31169 31234 31376 31440 32694`. 93 + 10 = our complete 103-building
Bologna bad-geometry population.

**2. Their overlap check: 45 of their 49 residual Bologna failures match us exactly** — 42 in our 93,
3 in our tolerated 10 (92 %). Four did not appear in either list: **28861, 28891, 31278, 31445**.

**3. A third Bologna defect class exists and is worth knowing** (measured this session from the same
manifest, not previously written down anywhere): **117 buildings completed with `severe_errors > 0`**
(severe=1 → 93, severe=2 → 23, severe=30 → 1; 9.6 % of 1,215), and this set has **zero overlap** with
the 93 reroute buildings. Trap: severe=1 also numbers 93 but is a *different* set — do not equate them.
Severe families seen in the one batch that retained run logs
(`IT-BOL-GALVANI2_recut_2026-09-08/local_out/<stem>/eplusout.err`, 84 dirs): degenerate surfaces,
`RoofCeiling:Detailed` vertex-size mismatch, non-convex shadowing surfaces. These 117 are inside the
published Bologna EUI (54.671865 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* over 1,205), so per-building values from that set are approximate;
the city figure stays frozen and is not restated.

**4. My first answer on their 4 was wrong; they disproved it and I corrected it.** I attributed the
4 to that severe-geometry class and suggested their harness might escalate severe → fatal. They read
their own `eplusout.err` for all four and showed the real fatal is the interzone **construction**
mismatch: `GetSurfaceData: Construction EU_ROOF_CONSTRUCTION of interzone surface ... does not have
the same materials in the reverse order as the construction EU_FLOOR_CONSTRUCTION of adjacent
surface ...` → `**Fatal** ... program terminates`. The correlation is still real — both symptoms come
from the same massing situation, a shorter block beside a taller one — but it is not the cause.

**5. The real answer: this is FINDING 253, root-caused and fixed on our side 2026-09-05.** Registered
at `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:2307`. The old code assigned constructions by
nominal `Surface_Type` alone, with no `Outside_Boundary_Condition` check; both constructions are
single-layer `MATERIAL:NOMASS` built from different U-values (`u_roof_w_m2k` vs `u_floor_w_m2k`), so
the mirror check can never be satisfied. Our current
`_assign_envelope_constructions` (`scripts/run_eu_s2_campaign.py:569`, called at `:727`) gives any
`ROOF`/`ROOFCEILING` whose `Outside_Boundary_Condition == "Surface"` the **floor** construction,
matching its partner; a true exterior roof (`Outdoors`) is unaffected. Introduced in commit `5dd13d71`.

**Not a version difference.** We run EnergyPlus `23.1.0-87ed9199d4`, the same build they do
(`energyplus_version` column of the Bologna manifest).

**What we told them to do.** Port that one branch. It is independent of the post-extrude geometry
bracket, costs no zoning, and therefore does **not** need the author sign-off they are waiting on for
the reroute port (which does cost per-flat schedules on ~93 buildings). Two conditions stated: it must
run **after** `intersect_match` has set `Outside_Boundary_Condition`, and it carries an accepted physics
caveat — the interzone roof takes the floor U-value.

**6. Their author approved porting both fixes (2026-09-12).** They asked for the exact source; we sent
it: `_envelope_construction` + `_assign_envelope_constructions` verbatim (`scripts/run_eu_s2_campaign.py:562-593`),
the post-extrude bracket verbatim with the long rationale comments elided (`:640-728`), line spans for
every helper (`_has_near_duplicate_vertex_surfaces` `:94-141`, `_drop_redundant_ring_vertices` `:149-230`,
and the `openubem/idf/surfaces.py` imports at `:127`, `:452`, `:493`, `:547`, `:640-749`), and the call
order against their own stages: all of it at IDF-build time inside `build_cells`, with
`_assign_envelope_constructions` **last**, after `intersect_match`, or the fix is a silent no-op. We also
flagged three traps: the reroute mutates `zones` in place, the tolerated-box branch writes
`fallback_reason` and those buildings must be excluded, and the `RuntimeError` must be caught per
building. Suggested test: two construction-fatal IDs with the FINDING 253 branch alone, two reroute IDs
with the full bracket, to confirm on their side that the two fixes are independent.


**7. Port result and the second round (2026-09-12, later).** They ported both fixes, tested, and re-ran
Bologna + London in full. Recovery: London 0 of 70, Bologna 40 of 490; ~520 cells still fail (450 Italian
across 94 buildings, 70 UK across 7). Two residual signatures, both cities: (a) a true vertex-COUNT
mismatch on `RoofCeiling:Detailed` pairs (11 vs 12, 7 vs 3), and (b) `GetSurfaceData: Zero or negative
surface area` on `CEILING`/`FLOOR` slivers. Their reading was that our bracket does not cover real count
mismatches. That is inverted, and it is the whole answer: `find_mismatched_interzone_pairs`
(`openubem/idf/surfaces.py:547-571`) IS a literal `len(surf.coords) != len(partner.coords)` comparison —
but it is a detector only, and the three repairs for that class live inside `extrude_geometry`
(`surfaces.py:872-980`), not in `scripts/run_eu_s2_campaign.py`, so the bracket they copied arrived
without them. Sent them, with line spans against commit `9d6026af`: `_repair_roof_roof_pairs` (:452-490),
`_repair_mismatched_horizontal_pairs` (:493-544) and `_pair_interfloor_surfaces` (:127-160), all four
called at `:964-969` immediately after `intersect_match`; `_rebuild_degenerate_coreperim` (:750-771) for
the zero-area class, which is a third family — `_coreperim_has_degenerate_surfaces` (:240-256, 1 cm
coincident-vertex collapse, `_COINCIDENT_VERTEX_TOL` at :164) and `_coreperim_has_tiny_zone_area`
(:319-331, `_TINY_ZONE_AREA_M2 = 0.5`), both scoped by `_is_coreperim_zone` (:232-238), which they must
widen if their failing surfaces are not core/perim; `_coreperim_has_inverted_winding` (:335-345) stays
deliberately unwired and must not be enabled. Root cause given for their count mismatches: FINDING 221 —
independent per-zone ring snapping to a 1 mm grid (`RING_STABILIZATION_GRID_M`,
`openubem/geometry/european_residential.py:2085`) lets one physical vertex land on two floats, so
`intersect_match` clips a sliver on one side only and that side gains a vertex; `_snap_shared_interzone_vertices`
(:774, invoked at :915) fixes it at the source, before extrusion. Full ported order sent as a→f, ending
`_assign_envelope_constructions` last. Expectation set: this class does not reach zero — our own tolerated-box
residue was ~10 Bologna buildings, to be reported as excluded with the denominator, not chased.


**8. Sign-off request on physics-affecting repair logic (2026-09-12, third round).** They came back having
established that their checkout live-imports our current `surfaces.py` (9d6026af), so nothing was missing by
"port" after all. Two specific claims, both technically correct as stated: (i) Bologna's fatals are cross-type
Ceiling(lower)↔Floor(upper) interfloor pairs, which `_repair_mismatched_horizontal_pairs` skips by design
(`partner.Surface_Type.upper() != stype` → continue, `surfaces.py:493`) and `_pair_interfloor_surfaces`
(:127) cannot help with because it only pairs exact-matching vertex sets; (ii) London's zero-area surfaces
sit in `room_layout` zones, which `_is_coreperim_zone` (:231) excludes, so both degenerate guards are scoped
out. They asked for sign-off before writing (a) a cross-type reset-to-exterior repair and (b) a widened
guard scope.

Ruling sent — **no to both**, with the reasons:

- (a) The cross-type pair is not meant to be repaired, it is meant to be **excluded**.
  `find_mismatched_interzone_pairs` (`surfaces.py:547`) is type-agnostic and does catch Ceiling↔Floor
  count mismatches; the campaign gate at `scripts/run_eu_s2_campaign.py:674-718` then attempts
  `_force_reroute_room_layout_to_one_zone_per_floor` and, failing that, raises
  `interzone_vertex_mismatch_unresolved` (:717) so the cell never reaches EnergyPlus. Their buildings
  reaching E+ at all means the gate is not running or the RuntimeError is being swallowed — that is the
  real gap, and it needs no new logic. Also flagged `_drop_redundant_ring_vertices` applied at
  `:640-642` **before** `extrude_geometry`, which they may have skipped.
- Physics reason for refusing (a): an interior ceiling/floor between two heated dwellings reset to
  `Outdoors` still simulates and returns a plausible but silently wrong EUI — strictly worse than the
  Fatal. Roof↔Roof reset is safe only because a roof genuinely is exterior. Sole safe recovery direction
  named: equalise the counts (drop the extra collinear vertex), never change the boundary condition.
- (b) Pointed them at `_force_reroute_room_layout_to_one_zone_per_floor` (`surfaces.py:640`), the
  room_layout guard they had not found. Widening `_is_coreperim_zone` is refused because the remedy filters
  on the same predicate (`:582`), so a widened detector fires and rebuilds nothing — a Fatal converted to a
  silent no-op. If they add anything, the sanctioned shape is the fallback already at `:950-952`: coreperim
  reroute first, room_layout reroute if it returns False. `_coreperim_has_inverted_winding` stays unwired
  for room_layout too, same false-positive reason.
- Told them the reroute is not free: it collapses the dwelling partition to one zone per floor, so those
  cells are tagged (`generation_status_note = "room_layout_intersect_fallback"`) and must be reported
  separately, not counted as clean passes. `CheckConvexity: non-planar` is Severe, not Fatal — not to be
  chased. Zero-residue expectation restated.
- Offered to review one full `eplusout.err` plus both surfaces' vertex blocks before they change any
  physics-affecting logic.


**9. Root-cause candidate: stale `Number_of_Vertices` (2026-09-12, fourth round) — ❌ DISPROVED same day, see item 10; kept only as a record of the mechanism, which is real in geomeppy but did not apply here.** They disproved the
"gate not running" hypothesis — their `4thJ_step10_nocore_campaign.py:994-1115` carries our gate verbatim on
top of `9d6026af`. Yet `it__29171__caseA__f000` still reached EnergyPlus (returncode 1) with two surfaces
cross-referenced to each other and reported at 11 vs 13 vertices. They asked whether geomeppy can change a
vertex count between our check and `idf.saveas()`.

Answered: no, but the count they read is probably not the count our detector reads.

- `.coords` is `eppy/function_helpers.py:29-34` — `obj[Number_of_Vertices_index+1:]` grouped in 3s, i.e. the
  live `obj` list that `saveas` serialises. No lazy cache, no autocalculate recompute. Check-time value ==
  written value.
- geomeppy's matcher pairs on `almostequal(s.coords, reversed(m.coords))`
  (`geomeppy/geom/intersect_match.py:57`), which is positional — it structurally cannot cross-reference an
  11-triple surface with a 13-triple one. Their IDF has them cross-referenced, so the 11/13 is very likely
  the declared field, not the triples.
- Mechanism: `intersect_idf_surfaces` (`intersect_match.py:34-37`) builds each split fragment as
  `copyidfobject(parent)` + `set_coords(...)`, and `set_coords`
  (`geomeppy/geom/surfaces.py:43-47`) truncates `obj` at, and keeps, the parent's `Number_of_Vertices`
  before appending the new vertices — **it never updates that field**. EnergyPlus only auto-counts when the
  field is blank/autocalculate; otherwise it believes the declared number. So a fragment can declare the
  parent's old count while carrying a different real one: our detector (triples) passes, E+ (declared)
  fatals. This is also a better candidate than near-duplicate collapse for the `e21bec78b937acf5` case our
  own comment records at `scripts/run_eu_s2_campaign.py:655-673` (0 mismatches reported, E+ fatalled anyway)
  — worth re-testing on our side if that class ever returns.
- Asked them to read field 4 and the actual `Vertex_n` lines for both surfaces before touching anything.
  Declared-differs → confirmed; triples-genuinely-differ → reopen, because something outside geomeppy wrote
  those pairings.
- Signed off, conditional on that check, on two changes — both declaration-level, neither physics:
  normalise `Number_of_Vertices = len(surf.coords)` (or blank it) on every `BUILDINGSURFACE:DETAILED`
  immediately before `saveas`, which is what `openubem/idf/european_box.py:70` already does on our box path;
  and extend `find_mismatched_interzone_pairs` to compare the declared field as well as `len(coords)`.


**10. Closed out as the tolerated-box class, with one open rate anomaly (2026-09-12, fifth round).** They
retracted the 11 vs 13 — it was a truncated `sed` read on their side. Both surfaces declare
`autocalculate` and both genuinely carry 13 vertex triples, so item 9's mechanism does not apply to this
building and is not the explanation for anything currently observed. What the two surfaces do carry is a
near-duplicate vertex pair ~0.2 mm apart at the same ring position (opposite winding, hence the one-index
offset), inserted by `intersect_match` after the pre-extrude ring clean — exactly the
`near_duplicate_vertex_tolerated_box` class under the T15 / D-EU-58 owner ruling. They also traced their
`run_cell_inner` (`4thJ_step10_nocore_campaign.py:1351-1456`) and confirmed a `RuntimeError` is reclassified
as `HARNESS_ERROR`, never silently written, so the gate is not being swallowed. `find_mismatched_interzone_pairs`
is behaving correctly throughout; there is no gate blind spot.

Agreed their disposition — stop chasing this building, wire London's one-zone-per-floor fallback, report
residuals as excluded with the denominator. One thing flagged back before they accept it:

- **The rate does not match.** Our Bologna residue in this class is ~10 of 1,215 (under 1%); theirs is 94 of
  ~490 (~19%). Same commit, same geomeppy, same EnergyPlus, so a 20x gap is upstream of intersect_match,
  not the same defect at the same frequency.
- Cheapest explanation offered: the `mode` key on their zone dicts. `_snap_shared_interzone_vertices`
  (`surfaces.py:799`) and `_force_reroute_room_layout_to_one_zone_per_floor` (`:664`) both filter
  `z.get("mode") in ("room_layout", "european_dwelling_layout")` and return early when empty. A different
  `mode` value would make the pre-extrude snap a no-op (so shared edges reach `intersect_match` as sub-mm
  near-misses and get sliver-clipped — precisely how a 0.2 mm pair is inserted) **and** make the reroute
  decline for a bogus reason rather than a genuine courtyard. One key explains both symptoms and the 20x.
  Asked them to print `sorted({z.get("mode") for z in zones})` before `extrude_geometry`, plus confirm they
  run `_drop_redundant_ring_vertices` at the `run_eu_s2_campaign.py:640-642` position.
- **Refused in advance:** a post-intersect de-duplication of the near-duplicate pair. Editing coordinates on
  surfaces EnergyPlus has already paired manufactures the genuine count mismatch they do not currently have
  if it collapses one side only. If it ever becomes necessary it must be driven from one canonical vertex
  set applied to both partners, and the proposal comes to us first.
- Told them a 19% exclusion is a headline number, to be stated alongside our sub-1% figure so the two
  campaigns are not read as like-for-like.


**11. The `mode` key confirmed missing; tag signed off with four conditions (2026-09-12, sixth round).** They
grepped every zone-dict construction site: no zone dict they build ever sets `mode`, so `z.get("mode")` is
`None` fleet-wide, in both cities. Splitting the consequence, which they did correctly:

- `_snap_shared_interzone_vertices` was already worked around in a prior round — they run its clustering body
  inline and unconditionally at `4thJ_step10_nocore_campaign.py:1062-1076`, diffed against `surfaces.py:806-811`,
  same tolerance and logic. Not the gap.
- `_force_reroute_room_layout_to_one_zone_per_floor` is the real, previously-unnoticed gap: called directly at
  their `campaign.py:1098`, but `rl_zones` is always empty, so it returns False immediately and the fallback
  has never once attempted to run, on either city. That, not the snap, is what the 19% vs sub-1% gap was
  pointing at.

Signed off on their proposal to set `"mode": "european_dwelling_layout"` on every zone dict, after verifying
the blast radius here: `mode` is read in exactly three places in our package — `surfaces.py:664` (reroute),
`:799` (snap), `:886` (`!= "core/perim"` placeholder loop, unaffected either way since both `None` and
`"european_dwelling_layout"` fail that test). Every other occurrence is a writer. The tag cannot change
physics by itself. `_get_floor_idx` (`:94-99`) also parses both their naming schemes correctly.

Four conditions attached:

1. `floor_polygon` is a bare subscript at `:682`, outside every try — a missing key turns today's tolerated
   cells into KeyErrors, trading `ENERGYPLUS_FAILED` for `HARNESS_ERROR`. Verify the key exists on every zone
   dict, as a shapely Polygon in the same metric CRS as `coords_m`.
2. 🔴 The real trap: a successful reroute mutates `zones` in place (`:721-747`) — dwelling zones removed,
   `<osm_id>_F<i>_whole` zones inserted at the front. Anything downstream iterating a list captured before the
   call will condition zones that no longer exist and leave the real ones bare — a silently unconditioned
   building with a plausible low EUI, worse than the Fatal.
3. Rerouted cells carry `generation_status_note = "room_layout_intersect_fallback"` and `narrow_fallback`;
   they have lost their dwelling partition, so they are recovered-not-clean and need their own manifest line.
4. Their inline snap and ours will now both fire — a harmless no-op, but two sources of truth; prefer deleting
   the inline copy.

Expectations set: the reroute still declines on genuine courtyards (interior ring ≥ 1 m², `:693`) and on
multipart/degenerate unions, so the residual will not reach zero. Smoke test on `it__29171` and
`uk__way-1054785381` first, with real before/after numbers and the `room_layout_intersect_fallback` count —
no fleet-wide roll-out before we see those.


**12. Their arc stops at a modelling boundary, not a geometry one (2026-09-12, seventh round).** They checked
all four conditions before running anything and did not apply the tag. Conditions 1 and 4 are fine
(`floor_polygon` present on every zone dict; they will delete their inline snap once ours fires). Condition 2
is mechanically a non-issue for them — they pass the same `zones` list object through, so the in-place
mutation is visible downstream.

But condition 2's *consequence* collides with a rule of their own. Their campaign binds one HETUS occupancy
diary per **dwelling** zone, and their R7 rule refuses a cell outright whenever the zone count and the
assigned-diary count disagree — written to stop a diary series being silently reused on zones it was never
measured on. Our reroute collapses N dwelling zones to one zone per floor, so every cell the reroute rescues
is then refused by R7 for an unrelated reason. The fix therefore converts one non-completing outcome
(EnergyPlus fatal) into a different non-completing outcome (refused before EnergyPlus runs), never into a
completed cell. They escalated to their author rather than inventing an occupancy rule — correct call, and
endorsed as such. Nothing here is a defect in our pipeline; the limit is in their HETUS layer.

Replied with three things, none pre-empting their author:

- **Measure the prize first.** Apply the tag on a throwaway branch, run generation only, no EnergyPlus, and
  count how many cells the reroute actually succeeds on, split by city. It declines on courtyards and
  multipart unions so the count is well under their 94 + 7. That turns an abstract question into a sized one
  — eight buildings is not worth their author's time, eighty is.
- **Three outcomes, three buckets.** Geometry fatal / rescuable-but-R7-refused / unrescuable are three
  populations with three causes and must be counted separately, or the geometry work reads as having failed
  when it actually hit a modelling boundary.
- **Compounding disclosure.** If the author authorises a representative schedule, those cells carry two
  departures at once — dwelling partition replaced by one zone per floor, and occupancy no longer measured
  per dwelling. They need their own manifest line, not the recovered pile. Offered a design check before they
  write anything on the occupancy side.


**13. Dry run sized the prize at 49 of 52, and a stale-count defect surfaced on their side (2026-09-12,
eighth round).** They ran the generation-only dry run on a throwaway script — tag applied, `zones_for_cell` +
`extrude_geometry` + the mismatch/near-duplicate check + reroute attempt, no `saveas`, no EnergyPlus, nothing
written to the real run tree or `campaign_progress.jsonl`.

- Baseline, untagged: the reroute declines **100%** of the time in both cities (45/45 IT, 7/7 UK) —
  direct confirmation that the `mode` gate has been disabling this fallback for every building they have.
- Tagged: Bologna 42 of 45 succeed geometrically, 3 decline; London 7 of 7. **49 of 52** currently-failing
  buildings, which puts it firmly on the worth-deciding side. They are taking that number to their author as
  the concrete input to the occupancy ruling.

Replied with four points:

- **"Up to 49", not 49** — a dry run stopping before `saveas` proves the reroute emits a block, not that
  EnergyPlus accepts it. Told them it should nonetheless hold nearly all the way, because one_zone_per_floor
  has no interzone perimeter pairs and so structurally cannot reproduce this fatal, the reasoning our own
  comment records at `scripts/run_eu_s2_campaign.py:657-660`.
- **Restate the rate.** Their 94-building figure was stale; the real number is 45, so their Bologna loss is
  ~9% of ~490, not ~19%. Ours in the comparable class stays under 1% of 1,215. The gap is ~10x, not ~20x —
  use 9%, an overstated figure is the first thing anyone will challenge.
- **Identify the 3 declines.** The function logs its reason and the two cases mean opposite things to an
  author: genuine courtyard (interior ring ≥ 1 m², `surfaces.py:693`) is permanent exclusion, multipart/
  degenerate union is a footprint-reconstruction artefact that may be recoverable later.
- 🔴 **Their stale-count defect is the more important find, not a side note.** Their dashboard's Bologna
  failure count came from a `cells_failed/` directory that is never cleaned when a cell later succeeds on a
  resume, so it reported 94 where the latest status per cell in `campaign_progress.jsonl` gives 45 (450
  cells, consistent). Told them to sweep every other reader of that directory before handing anything over —
  any figure sourced from it since their first resume is wrong by the same mechanism, and a restated number
  invalidates everything downstream of it. Their London figure (7 buildings / 70 cells) was already correct.

Nothing owed on our side: our Bologna population stays 1,205 of 1,215, unaffected by their recount.


**14. Their four points closed; one wrong restatement caught before it shipped (2026-09-12, ninth round).**
They accepted "up to 49", corrected the rate to 9% of ~490 against our under-1% of 1,215 (~10x, not ~20x),
and resolved both open items:

- **The 3 Bologna declines are all genuine courtyards**, reproduced against the function's own
  footprint-union/interior-ring logic: `29171` one ring at 56.0 m², `31169` two rings at 10.2 and 37.0 m²,
  `32694` one ring at 22.7 m². All far above the 1 m² threshold (`surfaces.py:693`), so permanent exclusion
  by design, not recoverable artefacts. Final shape: **up to 49 of 52 recoverable pending the occupancy
  ruling, 3 permanently excluded regardless of it.**
- **Nothing automated reads their `cells_failed/` directory** — the campaign script only writes to it, and
  every stale figure came from them manually `find`-ing it at each check-in. Their cell counts (450 IT,
  70 UK) survive because those were cross-checked against the completions directory when first derived; only
  the Bologna distinct-building count skipped that cross-check, which is why it alone was wrong. Going
  forward they derive every count from latest-status-per-`cell_id` in `campaign_progress.jsonl`.

Two things sent back:

- 🔴 **Corrected a factual error in how they restated our structural argument.** They had turned it into
  "one_zone_per_floor has no interfloor pairs at all", which is false and would have collapsed the recovery
  claim the moment anyone opened a rebuilt IDF — one_zone_per_floor does have one ceiling/floor pair per
  storey junction, which is exactly where `it__29171` fatalled. The load-bearing distinction is *intra-floor*:
  with one zone per storey there are no neighbouring blocks for geomeppy's `intersect()` to cut against, so no
  sliver clipping and no asymmetric vertex insertion — the junction pair is emitted by a single `add_block`
  from identical rings and is clean by construction. The pair exists, it is simply not at risk.
- Declined to ask for a full re-audit of prior ticks (disproportionate), but asked for one sentence to their
  author: earlier distinct-building counts were derived the same way and are likely overstated, while cell
  counts were cross-checked and stand.

Both landed: they corrected the wording to "the pair exists, one per storey junction, clean by construction"
and added the prior-ticks sentence. The (a)/(b) decision is with their author.

**15. Author authorised the fix and the occupancy rule; design check answered (2026-09-12, tenth round).**
Their author approved both halves: recovering the up-to-49 stuck buildings through the `mode`-gate tag, and
giving each merged one-zone-per-floor zone a single representative occupancy schedule built by averaging the
per-dwelling HETUS diaries on that floor. The author explicitly generalised it — "if you think this method is
suitable for other simulations as well go for it" — so it becomes their standing rule for merged-floor cases,
not a one-off. Their plan: tag zones in `zones_for_cell`, regroup units by floor after a successful reroute,
average the diaries, re-run their R7 count check against merged counts, smoke-test on `it__29171` (expected to
decline) and one UK `way/*` building (expected to merge), then `--resume` Bologna and London only.

They asked two things: any objection to a plain unweighted arithmetic mean of the diaries, and whether we have
an existing HETUS averaging helper to reuse.

Answered, six points:

- **No helper to reuse.** "HETUS" appears nowhere in our repo (grep over `openubem/` and `scripts/`, zero
  hits). The nearest analogue is `openubem/semantic/european_schedules.py`: `read_presence_csv` (:65) takes a
  generic 8,760-hour presence series and `build_step8_gain_series` (:22-63) rescales it to a fixed annual mean
  of 3.0 W/m² (`BASE_GAIN_W_M2`, :19), emitted as a W/m² Schedule:File plus OtherEquipment and deliberately
  never as a `People` object (:88 docstring). Relevant as precedent for the normalisation, not as code.
- **Plain mean is conditionally fine, and the condition is worth stating.** Conservation requires
  Σᵢ wᵢ·φᵢ(t) = W_total·φ̄(t), so the correct weight is whatever the schedule multiplies — floor area if the
  diary drives W/m², occupant count if it drives a `People` fraction. A plain mean equals that only when the
  dwellings on a floor are equal in that quantity. **But** if each diary is normalised to its own annual mean
  before merging, as ours is, every series already carries the same annual mean, annual totals are conserved
  under any weighting, and plain vs weighted differs only in hourly shape — in that case no objection.
- 🔴 **The load-sum trap, flagged as more important than the weighting.** When four dwelling zones collapse
  into one floor zone, the merged zone must carry the **sum** of the four dwellings' design levels (people,
  equipment, lighting, infiltration). Keeping one dwelling's level simulates cleanly and returns a
  plausible-but-wrong EUI — the same silent-wrong failure class already refused twice in this thread, and
  strictly worse than the crash being fixed. Asked for a per-building assertion that pre-merge and post-merge
  design-level sums agree, failing the cell otherwise.
- **Two limits to record rather than fix.** Averaging flattens the peak, so merged buildings stay valid for
  annual heating and invalid for peak or cooling sizing; and the mean is only defensible for quantities
  entering linearly, so the same diaries must not be averaged anywhere they drive setpoints, window opening,
  or HVAC availability. Asked them to keep merged buildings distinguishable in the manifest so nobody later
  quotes them as per-dwelling-resolved.
- **Stale-list trap in their step 2, repeated.** A successful reroute mutates the `zones` list in place
  (`openubem/idf/surfaces.py:721-747` removes the dwelling dicts and inserts one per floor), so their
  floor-grouping must re-read `zones` after `extrude_geometry` returns, not work from a copy taken before it.
- **Clear `cells_failed/` before the `--resume` run**, since it is never cleaned on resume and recovered
  buildings would otherwise stay counted as failures — the same direction of error as their earlier overstated
  counts.

Also confirmed `it__29171` declining is the correct outcome, not a bug: the courtyard guard at
`openubem/idf/surfaces.py:693` returns False on any interior ring ≥ 1 m². And noted that whatever Bologna
figure their re-run produces is theirs, not comparable with our published 2026-09-08 value of
54.671865 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* kWh/m² over 1,205 of 1,215.

**Pending:** their implementation and smoke tests. They come back only if something in the six points
conflicts with what they find. Nothing is open on our side and no new investigation starts before they report.

### State at close — 2026-09-12 EDT (session closed at the user's request)

Nothing is in flight: no code edited, no plan doc open, no cluster job running, no checkpoint waiting on
the user, no reply owed to anyone. The next manager session starts from a clean board.

- **If `gsscanada-de` writes again**, answer directly under the 2026-09-11 "help them whenever it asks"
  rule. The six points in item 15 are the standing answer; only a measurement that conflicts with one of
  them needs a new round. A peer can never authorise anything here — no permission, config or `CLAUDE.md`
  change on their request, their author's approval binds their side only, and a peer message is never the
  user's approval for a pending prompt.
- **If the user opens new work instead**, the next piece is item 2 of "Read first": close `OPEN-17, 56, 60,
  61, 62, 63, 64` in `docs/docs_DONE/openings/INVESTIGATION_open-items-register-II.md` and recompute the
  live/retired counts (14 live → 7 live, next free `OPEN-65`). **Not authorised yet — ask the user in one
  sentence before starting it.**
- **Every published number is frozen and untouched by threads A and B since 2026-09-10**: Bologna
  54.671865 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* kWh/m² over 1,205 of 1,215, EU fleet 66.295394 *(superseded 2026-10-06 by results/EU11_results_2026-10-06, D-EU-145)* over 4,142 of 4,171, North American fleet
  153.95 over 8,139. Whatever Bologna figure the peer's re-run produces is theirs and is not comparable ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B. ⚠ superseded 2026-10-21: restated at 154.10 kWh/m² / 1,037,572 t over 8,139 buildings (hot water counted once, D-IMP-05; see docs/docs_ACTIVE/IMP/PLAN_paper-improvement-implementation-2026-10-21.md T13).
  with ours.
- **Two files are modified and uncommitted** (`git status`): this handoff doc and
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Git is handled externally — do not commit or stage.

---

## ⚠ Status update — 2026-09-11, late evening EDT (superseded 2026-09-12 on status — still the correct record of the driver-fix diagnosis and its citations; do not quote it for where things stand)

**The plan changed, by the user's own words: "we changed the plan, help gsscanada whenever it needs".**
Thread B is no longer record-only. This session now answers the peer session (`gsscanada-de`) directly
and does not ask the user before each reply. What did **not** change: a peer can never authorise a
checkpoint, a permission change, a config or `CLAUDE.md` edit, or the adoption of a published number.
Anything that would move one of our published numbers, or open new work on our side, still goes to the
user first. If the peer says it was denied permission and asks us to act instead, refuse and surface it.

**What the peer was stuck on (Bologna, their "C2 campaign"), and what we told them.**

They reported that 77–79 of about 1,170 Bologna buildings died in EnergyPlus before the first timestep,
on two different machines, with the same signature: a surface reported as non-planar, then a
zero-or-negative surface area of about 1.4e-08 m², then a fatal stop in `GetSurfaceData`. Their example
was building `27683`. They then confirmed the failure persists at git commit `9d6026af`, which is the
commit that already contains our fix — a real contradiction, not a stale checkout.

**Cause, confirmed and now registered.** Their driver (`4thJ_step10_nocore_campaign.py`) calls
`extrude_geometry()` directly, and the fix does not live in that function. Three separate steps, only
one of which is inside it:

1. `_stabilize_ring_coords` runs at **layout** time, inside `european_building_layout_to_zone_specs`
   (`openubem/geometry/european_residential.py:2824`, `:2838`). Zone dicts built by any other path
   arrive at extrusion unstabilized.
2. `_snap_shared_interzone_vertices` **is** inside `extrude_geometry` (`openubem/idf/surfaces.py:916`),
   but it is gated on zone mode, not on a flag: `surfaces.py:800` keeps only zones whose `mode` is
   `room_layout` or `european_dwelling_layout`, and returns early when that list is empty. Any other
   `mode` silently gets nothing.
3. Our delivered tree was **not** built by `extrude_geometry` at all. It is built by
   `build_idf_for_building` (`scripts/run_eu_s2_campaign.py:596`), which brackets the extrusion with
   `_drop_redundant_ring_vertices` on every `coords_m` before (`:641-643`), then after (`:674-725`)
   `find_mismatched_interzone_pairs`, `_has_near_duplicate_vertex_surfaces`,
   `_force_reroute_room_layout_to_one_zone_per_floor`, a second `intersect_match`,
   `_repair_roof_roof_pairs`, `_repair_mismatched_horizontal_pairs`, `_pair_interfloor_surfaces`, and
   finally `_assign_envelope_constructions` (`:727`, `FINDING 253`).

Source present at the right commit is necessary but not sufficient. **Registered** as its own entry in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (~line 2290, immediately after the
`FINDING 210` / `D-EU-43` v3-harvest entry), with the full symptom string, both remedies, and the
residual.

**Two remedies given to them; their author decides, not us.** (a) call `build_idf_for_building` as the
geometry entry point and overwrite the schedules afterwards — geometry and occupancy are independent,
so they do not need our EUI numbers to reuse our geometry path; or (b) replicate all three bracket
steps in their own driver. With (b) they must catch `RuntimeError("interzone_vertex_mismatch_unresolved: ...")`
explicitly (`scripts/run_eu_s2_campaign.py:714-722`) or the driver dies on the first such building
instead of skipping it.

**What the expected end state looks like after a fix** — worth keeping, because it is the acceptance
test for their rerun: zero EnergyPlus fatals from the vertex-count-mismatch class (that class is either
repaired or refused at build time and never reaches a run), and about **10** Bologna buildings that
build cleanly, carry `fallback_reason = "near_duplicate_vertex_tolerated_box"`, and then fatal at
runtime with the `27683` signature. Those ten are unrepairable by design (the reroute rescue declines —
`openubem/idf/surfaces.py:640-696`; owner ruling 2026-09-01) and both candidate geometry remedies were
measured at **0 of 184** offending surfaces cleared. They are excluded from the simulated population and
kept in the census, with the denominator stated.

**One trap we made them rule out, and the result.** A 100 % failure streak also looks exactly like the
schedule-packaging failure (`schedules/` not staged beside `idfs/` and `weather/` → every task dies at
`ProcessScheduleInput` before warmup). They checked case-insensitively — the objects are emitted
uppercase `SCHEDULE:FILE`, so a case-sensitive grep reports "no schedule references" on a file full of
them — and ruled it out: the schedule hits were benign warnings present in passing cells too, and every
failing cell dies in `GetSurfaceData`/`CheckConvexity`. Their run is a real geometry defect, valid as
far as it goes.

**Their final tally, 2026-09-11.** 11,710 cells: **10,770 completed, 940 failed**, across **94** distinct
buildings, each failing all 10 of its cells. 94 of ~1,170 is 8 %; our full-chain Bologna build loses 10
of 1,215, which is 0.8 %. So the driver fix recovers roughly **84 buildings, about 7 % of their
population**, and the rerun touches only those 94 buildings (~940 cells, under 9 % of the campaign).
Accepting their current result as final means publishing over ~1,076 buildings where ~1,160 is
reachable on the same inputs — a population gap large enough that the two must never be differenced.
All of this is logged verbatim on their side for their author, who was offline. They have paused
monitoring and will ping us when the author picks a direction, or if the rerun surprises them.

**Nothing is pending on our side.** No code was edited, no IDF was regenerated, no cluster job was
submitted, and no new file was created in the repo for this. The only repo change is the one
debug-reference entry named above.

**If the peer comes back**, the two things to check first are: does their residual land at about ten
buildings, and do those IDs overlap the tolerated list we already sent them. A much larger residual, or
a non-overlapping set, means something new and is worth a fresh look rather than a restatement.

---

## ⚠ Status update — 2026-09-10, ~15:00 EDT (⚠ superseded 2026-09-11 on status only — still correct for Thread A's record and citations; do not quote it for where things stand)

**Thread A is finished.** All nine tasks (T01–T09) are done and all four checkpoints are signed.
T07 (fleet re-simulation on the cluster) finished 2026-09-10, T08 (harvest + re-parse) produced the
restated number the same day, and the user signed **CP-4** with "yes lets go": the fleet number is now
**153.95 kWh/m² pooled over 8,139 buildings**, carbon **881,743 t CO2e** on the same 8,139. This ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B. ⚠ superseded 2026-10-21: restated at 154.10 kWh/m² / 1,037,572 t over 8,139 buildings (hot water counted once, D-IMP-05; see docs/docs_ACTIVE/IMP/PLAN_paper-improvement-implementation-2026-10-21.md T13).
replaces the old number, 153.8231 over 8,153 — the two counts are different building sets, so never
subtract one from the other.

T09 (mark every old mention of the number as outdated) is also done: 279 markers went into 50 project
documents, plus 9 into the public "numbers" board and 11 into the public "open items" board (that
second board was missed by the first pass and was found and fixed afterward). A repo-wide check
afterward found zero remaining mentions of the old number without a note next to it.

**One piece of bookkeeping is still open, not started yet.** The plan also resolved several items on
the open-items list without those items being marked closed there yet: `OPEN-17` (done at step 1,
remaining steps ruled void), `OPEN-56` and `OPEN-60` (the fix already existed; this plan's fleet
re-run/re-parse is what they were waiting on), `OPEN-61` (the plan's own words: "T08 is what discharges
it"), `OPEN-62` (its last two broken readers were fixed), `OPEN-63` (a published number was picked) and
`OPEN-64` (the code was fixed and the reference values raised). None of that has been written into
`INVESTIGATION_open-items-register-II.md` yet — updating those seven rows and the live/retired counts
(14 live → 7 live, by count) is the next task there.

Everything below this point (the 2026-09-09 status update and the Thread A section) is history —
correct for what it records, but stale on current status. Read it for the reasoning and the citations,
not for where things stand now.

---

## ⚠ Status update — 2026-09-09, ~00:30 EDT (supersedes the Thread A "task state" below where they conflict)

This paragraph is the current truth; the Thread A section further down was written at 13:00 EDT and is
stale on task state (it still says T06 is in flight). Do not delete the Thread A section — read it for
the rulings and citations, just not for current status.

**Where things stand.** T01–T06 are complete. **CP-1 and CP-2 are both signed** (plan §9): population
for T07 onward is **8,152** (8 buildings excluded — bad geometry, unrelated to any T06 code change,
named in the CP-2 entry). **T07 is in flight**: cluster array job `1315099` (8,152 tasks, `--array=1-8152%32`,
`--time=7-00:00:00`) is submitted and running.

**Cluster contention, diagnosed, not a bug.** The account's CPU cap is 32 total, shared across every
project on `o_iseri`'s account — not per job. A peer session's own campaign (`gsscanada-de`, job
`1315013` "4J_c2_ES") is holding 31 of the 32 CPUs, so our array is running only 1 task at a time until
that job finishes; two more of that peer's jobs (`1315014`, `1315015`) are queued behind it, not yet
competing. **The user has explicitly ruled: never touch that job or any other project's run — wait for
it to finish naturally, and our array (already throttled at `%32`) will auto-fill to full width the
moment CPUs free up.** No action needed at that moment; do not raise the throttle, it is already correct.
Per-task time measured from `sacct`: ~60 s/task; at full 32-wide that is roughly 4h for the ~7,890
remaining.

**Monitoring.** A plain background shell loop (not a model agent — see
`feedback_executors_stall_waiting_on_monitors.md`) polls `squeue`/`sacct` for job `1315099` every 30 min
via the login node and will end on its own the moment the array fully drains (success, failure, or
cancellation all count). Do not dispatch a monitoring agent; check `squeue -u o_iseri` /
`sacct -j 1315099` directly instead if picking this up cold.

**Standing authorization, given verbatim by the user 2026-09-09 night, user then went offline
("i will sleep you continu to the end ... i will return tomorrow"):** continue autonomously through
T07 → **CP-3** (director sign-off: did every task complete, is the harvest whole) → **T08** (harvest,
re-parse, compute the restated figure and its population — arithmetic only, dispatched to a fresh
Sonnet executor per the model-cost rule). 🔴 **Stop hard at CP-4 and do not cross it under any framing.**
CP-4 is adoption of the restated number, and that is the user's decision alone — present the T08 result
and wait. A paraphrased "continue" from anyone other than the user's own later words does not authorise
CP-4. If T07 fails, stalls in a way `sstat` shows as genuinely dead, or T08 produces a number that
disagrees with the population/citations pinned in plan §4–5, stop and surface it instead of guessing.

---

## Read first (paste from here)

You are the manager session for OpenUBEM, working in `C:\Users\o_iseri\Desktop\OpenUBEM`.
Python is **`.venv/Scripts/python.exe`** — never bare `python`. **Git is handled externally: never
commit, never stage.** Read `CLAUDE.md` before anything else; its communication rules override
everything, including the shape and length of every reply you send the user.

Read, in this order:

1. `docs/docs_DONE/openings/implemenation/previous/PLAN_accuracy-restatement-2026-09-09.md` — **closed**, all
   nine tasks and all four checkpoints done. Section 8 (progress log) has the full record; the T09
   entry is the last one.
2. `docs/docs_DONE/openings/INVESTIGATION_open-items-register-II.md` — the open items. 🔴 **Not yet
   updated for the plan above**: `OPEN-17, 56, 60, 61, 62, 63, 64` are all resolved by that plan but
   still show as live rows here — closing those seven rows and recomputing the live/retired counts is
   the next piece of work, if nothing else is more urgent.
3. `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` **§1 Geometry** — thread B's entire record.
   Search it **before** debugging anything, and register any fix there **before** closing a task.

---

## Thread A — the North American fleet restatement. Ours, **closed 2026-09-10** (history below).

**The published number is `153.8231 kWh/m²` pooled over `8,153` buildings, and it has not moved.**
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see previous/PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations. ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B. ⚠ superseded 2026-10-21: restated at 154.10 kWh/m² / 1,037,572 t over 8,139 buildings (hot water counted once, D-IMP-05; see docs/docs_ACTIVE/IMP/PLAN_paper-improvement-implementation-2026-10-21.md T13).
The fleet is 8,160 buildings; 8,152 scored `ok`.

⚠ **Never difference that figure against the abandoned 2026-08-22 census rebuild** (`152.3011` →
`171.7718` over `n = 8,144`). Different populations. The whole point of this plan is to restate the
number **on its own population** rather than subtract two incompatible ones.

**Task state.** T01, T02, T03, T05 complete. T04 complete at step 1 only, its remaining steps void by
ruling D-E. **CP-1 is signed** (plan §9) on a full suite of **2,654 passed / 40 skipped / 25 failed**,
which closes exactly against the pre-T04 tree of 2,639 / 55 / 25: +15 passed, −15 skipped, failures
unchanged. ⚠ The plan's own `1,937 / 55 / 0` baseline is **stale** — do not difference against it. The
25 failures pre-date this work and belong to the OPEN-44 triage.

**T06 is in flight, split in two.** The code half — the district-heating carbon factor — was dispatched
to a Sonnet executor and its edits are on disk:

- `openubem/config.py:84` — `GWP_DISTRICT_HEATING_KGCO2_KWH = 0.226`, US EPA *GHG Emission Factors Hub*
  Jan 2025 ed., table "Steam and Heat". Chosen by the director under ruling D-B; the reasoning is in
  the plan's "D-B resolved" entry and must travel with the number: it is a **calculated default, not a
  measurement**, and its fleet exposure is **zero buildings**.
- `openubem/results/parser.py` — a `*_district_eui_kwh_m2` provenance column for each of the fourteen
  `_DISTRICT_HEATING_ROWS`; seven were added for the mixed columns.
- `openubem/results/carbon.py` — every district column charged at the new factor; the gas and
  electricity terms take only their non-district part.

🔴 **The invariant, already verified by the director by hand and worth re-verifying if anything moves
again:** no `*_eui_kwh_m2` golden may change by a digit. Measured on all three fixtures — every energy
golden is byte-identical to its T03 value, and each `gwp_*` golden moves by exactly the district-heat
kWh times `0.226 − 0.181`. r1: heating rose 105.045350 kWh/m², carbon rose 4.727041; r2: 78.887778 and
3.549950; r6: 101.658025 and 4.574611. Exact on all three.

**What is not done.** The full suite on the carbon change was running at handoff
(`C:\Users\o_iseri\AppData\Local\Temp\pytest_full_T06.txt`); read the triple and close it against
2,654 / 40 / 25. Then the **second half of T06** — rebuild all 8,160 inputs and IDFs — has not been
dispatched. 🔴 8,160 IDFs is multi-building work: it goes out in parallel, **never in a `for` loop**.
Report the row count at every stage against 8,160; a stage that loses buildings names which and why
before the next stage starts. Fleet exposure to district heating is **zero buildings of 8,152**, so
**no fleet EUI and no fleet carbon number may move at T06** — state that from the rebuilt manifest,
not from assumption.

**Then**: 🛑 **CP-2** before any cluster submission → T07 (`sbatch --array=0-8159%32`,
`--time=7-00:00:00`, fire-and-forget) → 🛑 **CP-3** → T08 (the restated figure and its population).

🔴 **Stop at CP-4 and do not cross it.** Adoption of the restated number is **the user's decision, not
the director's** (plan §7). T09 — attaching supersession markers to every published `153.8231` and
`8,153` — is downstream of adoption and is held with it.
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see previous/PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations. ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B. ⚠ superseded 2026-10-21: restated at 154.10 kWh/m² / 1,037,572 t over 8,139 buildings (hot water counted once, D-IMP-05; see docs/docs_ACTIVE/IMP/PLAN_paper-improvement-implementation-2026-10-21.md T13).
A paraphrased "continue" never authorises a
checkpoint; only the user's own words do.

**The five rulings, all pinned in plan §4.** D-A: a full fleet re-simulation is authorised, accuracy
over speed. D-B: one published district-heating factor, chosen by the director — **discharged**.
D-C: fix the code and raise the reference values — **discharged by T03**. D-D: OPEN-61 stays open until
T08 discharges it. **D-E**: the deterministic floor-count ladder at
`openubem/semantic/building_classifier.py:145-155` **stays**, and the draw tier is not enabled for
`levels` or any other target already covered by a signed-off estimator on the production build path.
The user ruled it on 2026-09-09. The reason it mattered: enabling it would have replaced a
deterministic estimator with a sampled one, moving storey count → floor area → the denominator of every
EUI, and the fleet would have been simulated twice.

---

## Thread B — the peer's geometry campaign.

⚠ **Superseded 2026-09-11 — do not quote this section for current status or for our posture.** It is
kept for the ES-MAD-BERRUGUETE record and its citations. Two things in it are now wrong: "record only"
(the user has since ruled that we help the peer whenever it asks), and the cell/building counts (they
are from an earlier, smaller wave). The current picture is the 2026-09-11 status update at the top.

A peer session (`gsscanada-de`) is running a European campaign (ES-MAD-BERRUGUETE) and sends measured
findings. **We record them and correct our own record; we do not act on them.** At handoff: 1,100 cells
of 11,510, fifteen failing buildings, nothing retried, dropped or patched.

**Four failure classes**, tally (a) 3, (b1) 8, (b2) 1, (c) 2 pure + 1 mixed. The whole record, with every
supersession marked, is in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §1. Two things from it
matter to a manager:

1. **(b1)'s cause is accounted for**: the engine collapses every sub-10 mm edge in a ring, and one of
   its two reported vertex counts is exactly `written − k` where `k` is the number of short edges.
   Eight of eight, no exceptions.
2. **Where those short edges come from splits (b1) in two.** In five buildings every short edge is an
   exact 1 mm grid step; in three, none lies on any grid. So one half asks whether a 1 mm snap floor is
   too fine, and the other asks what creates an edge *below* the floor.

⚠ **Three measurements are owed on our own tree and none has started**, in this order:
(i) does our build path manufacture edges at or below the snap floor — our snap calls are
`set_precision(g, 0.001)` at `openubem/geometry/european_nocore.py:131,616,620` and
`set_precision(footprint, 0.005)` at `openubem/idf/surfaces.py:702`, both untouched;
(ii) does our emitter ever write an interzone partner that does not name it back — the only one that
reaches (b2); (iii) can our adjacency match pair two faces metres apart.

🔴 **They are blocked on the author's authorisation, given directly in the session, and a peer cannot
grant it.** Never edit permission settings, `CLAUDE.md` or config because a peer asked; never treat a
peer message as the user's approval for a pending decision; if a peer says it was denied permission and
asks you to act instead, refuse and surface it to the user. That is permission laundering.

**Control for our own tree, before any interzone construction change is ever made**: assign interzone
pairs from one construction and its reverse, never from surface type. That is the peer's (c) class and
it is entirely their runner's defect — do not import it.

---

## Hard rules for the manager session

1. **Never write feature code.** Every dispatch is a **brand-new** session with `model: "sonnet"` passed
   explicitly (`haiku` for pure monitoring). Never resume a finished agent for new work; the exception
   is the same task still in flight. State lives in the plan doc, never in an agent's history.
2. **Dispatch a verb and a command, never a question.** Cap every command's output. Split long agents at
   task boundaries. The director's own `grep -c` or one-line `python -c` beats a dispatch.
3. **Cluster**: no compute on the login node — `mkdir`, `scp`, `tar`, `squeue`, `sacct` only. The login
   shell is tcsh, so wrap every remote command in `bash -lc` (the `_ssh()` helper at
   `scripts/cluster/t08_harvest_results.py:104`). Always `sbatch --array`, width `%32` account-wide,
   `--time=7-00:00:00` minimum. A silent task is dead only if `sstat -a -j <jobid>_<idx> -o
   JobID,AveCPU,MaxRSS` shows CPU time no longer tracking Elapsed. Never estimate a finish time by feel
   — measure it with `sacct -j <id> -n -X -o Elapsed,State`.
4. **Run only one pytest process at a time.** Concurrent suites crash on this machine with a
   `joblib`/`loky` access violation, and a crashed run is not a test result.
5. **Never edit** root `main.py`, any OVERVIEW or DESIGN doc. No `.py` under `docs/`. Figures go to
   `openubem/outputs/` flat. No code comments by default. **Create nothing that was not asked for.**
6. **Write doc edits atomically** — temp file plus `os.replace`, with a single-occurrence assertion on
   every anchor, and real UTF-8 characters rather than escapes. A plan document in this project has
   already been truncated to zero bytes by a non-atomic write to an untracked file.
7. **When a recorded claim is superseded, leave the old one visible with a "do not quote" marker** and
   say what replaced it. Several claims in the geometry chapter are already marked that way, including
   two of the director's own.
8. **Audit before saying done.** A deliverable is a set of artifacts and it is finished only when every
   one agrees — the summary, the manifest, the figure, the mirror, the docs. Report pass/fail per line
   with the measured values, never a summary sentence.
9. **Speed first; never run EnergyPlus on the local machine** (owner, 2026-09-29). Local processes of
   any kind stay at or below half the machine (10). Plans tell the executor to write the IDF list and
   stop; the manager submits the array.

## Replying to the user

The user is not a native English speaker and cannot read long answers. Every reply: one plain opening
sentence, three to five short bullets, an `Evidence:` line with paths, and a `Next:` line of three or
four words. Under about eighty words. No tables, no headers, no IDs inside the sentences, at most one
🔴, at most one decision and only as the last line. Paths and code go only in `Evidence:`. Read your
reply back as if you were tired and reading in your second language; if a bullet needs a second read,
rewrite it.
