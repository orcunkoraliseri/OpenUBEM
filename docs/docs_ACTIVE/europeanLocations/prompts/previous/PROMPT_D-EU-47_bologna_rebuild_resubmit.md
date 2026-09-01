# `D-EU-47` — Executor prompt: rebuild and resubmit Bologna's 177 `FINDING 210`-class failures

- **Arc**: European locations × Step 8, `EU-16`. **Plan**: `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
- ✅ **AUTHORISED 2026-08-31.** Owner's authorising sentence, verbatim: *"oui j'autorise, vas-y"* (owner,
  2026-08-31, replying directly to the manager's line "Waiting on you: autoriser une vague de
  reconstruction/resoumission (Bologna 177 via le fix existant + Lyon 9 via time bump) — recommend yes.").
  Paste this sentence into the `D-EU-47` progress-log entry. It authorises **exactly** the 177 Bologna stems
  named below, via the existing unmodified `FINDING 210`/`D-EU-43` gate — nothing else, no new fix, no other
  district.
- 🔴 Still bound: `sbatch --array` fire-and-forget only, never the login node, tcsh remote shell via the
  `_ssh()` helper, EnergyPlus 23.1.0 Ubuntu20 on Speed ≠ Windows local (`FINDING 187`/`190`), never touch
  another project's/district's cluster runs, ship to a dedicated fleet dir — never overwrite the shared base
  tree in place.
- **Executor**: fresh Sonnet session. **Do NOT edit** `content/walkthrough_progress_log.csv`,
  `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`, `results/RESULTS_EU-11.md`, or
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Report results back to the manager; the manager folds
  them into the shared docs.

## What is already known — use it, do not re-derive

- Classification (`D-EU-45` investigation, 2026-08-31), 177 `FAILED` Bologna stems (job `1299947`):
  85 exact `FINDING 210` vertex-size-mismatch, 52 exact `D-EU-43` non-planar/zero-area, 40 zero-area-only
  (same family, convexity check just didn't fire first). All 177 are hypothesised covered by the existing
  gate — **Bologna's IDFs simply predate the fix and were never rebuilt**, unlike Madrid/Lyon/London.
- The fix (unmodified, do not touch): `scripts/run_eu_s2_campaign.py::build_idf_for_building` calls
  `find_mismatched_interzone_pairs` after `extrude_geometry`, reroutes via
  `_force_reroute_room_layout_to_one_zone_per_floor` when needed; `_has_near_duplicate_vertex_surfaces`
  additionally gates on near-duplicate vertices and machine-precision collinearity. Same code path used
  unmodified for `D-EU-42`/`D-EU-43`/`D-EU-44`.
- Results tree pattern: `/speed-scratch/o_iseri/fleets/EU11_IT-BOL-GALVANI2_deu47/out/<stem>/` (dedicated dir,
  same pattern as `D-EU-44`'s `EU11_ES-MAD-BERRUGUETE_deu44`) — never write into the shared
  `EU11_IT-BOL-GALVANI2/` base tree.
- Local manifest: `openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/it_bol_galvani2_manifest.csv`.

## Task

1. From the manifest, enumerate the exact 177 stems (`FAILED`, blank `heating_kwh`) — confirm the count
   matches 177 before proceeding; stop and report if it does not.
2. Rebuild their IDFs through `run_eu_s2_district_campaign.py`/`run_eu_s2_campaign.py::build_idf_for_building`,
   unmodified, exactly as `D-EU-44` did.
3. **Prove on real local EnergyPlus 23.1.0** (Windows, `ExpandObjects.exe`+`energyplus.exe`) before shipping —
   at minimum one stem from each of the three signature buckets (85/52/40), ideally all 177 if runtime allows;
   report RC and severe/fatal counts. Synthetic (Python-only vertex-count) proof is not sufficient — this arc
   already had one false-green incident (`T09-FINDING210-ROOTCAUSE-FIX-V2` progress-log entry) on exactly this
   mistake.
4. Ship to a dedicated fleet dir (`EU11_IT-BOL-GALVANI2_deu47`), submit **one** `sbatch --array` over exactly
   these 177 stems.
5. Once drained: harvest (`sacct -j <jobid> --format=JobID,State,ExitCode -X`, remote tar fetch, sqlite
   `heating_kwh` parse), fold results into a fresh copy of the Bologna manifest, regenerate the Bologna viewer,
   mirror to `docs/docs_ACTIVE/europeanLocations/outputs_3D/`, `diff -rq` check.
*Standing constraint.* Never tune an input to move an EUI into a band. Every Speed failure still classified
and carried, never dropped. Bologna's `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` provenance note still
applies to every Bologna EUI figure reported.

## Report back (to the manager, not into shared docs)

Job ID, array size, `sacct` completed/failed counts; local pre-ship proof results (RC, severe/fatal, per
bucket); recovered heating figures and new Bologna pooled EUI (before/after); `diff -rq` mirror output
(pasted, not summarised); any residual failures (with signature) if not all 177 recover. Under 350 words.
