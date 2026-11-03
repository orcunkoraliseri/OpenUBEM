# `D-EU-48` — Executor prompt: resubmit Lyon's 9 timed-out stems with a walltime bump

- **Arc**: European locations × Step 8, `EU-16`. **Plan**: `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
- ✅ **AUTHORISED 2026-08-31.** Owner's authorising sentence, verbatim: *"oui j'autorise, vas-y"* (owner,
  2026-08-31, replying directly to the manager's line "Waiting on you: autoriser une vague de
  reconstruction/resoumission (Bologna 177 via le fix existant + Lyon 9 via time bump) — recommend yes.").
  Paste this sentence into the `D-EU-48` progress-log entry. It authorises **exactly** the 9 Lyon stems named
  below, resubmitted with a longer walltime — no rebuild, no code change, no other district.
- 🔴 Still bound: `sbatch --array` fire-and-forget only, never the login node, tcsh remote shell via the
  `_ssh()` helper, EnergyPlus 23.1.0 Ubuntu20 on Speed ≠ Windows local.
- **Executor**: fresh Sonnet session. **Do NOT edit** `content/walkthrough_progress_log.csv`,
  `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`, `results/RESULTS_EU-11.md`, or
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Report results back to the manager; the manager folds
  them into the shared docs.

## What is already known — use it, do not re-derive

- `D-EU-46` investigation (2026-08-31) confirmed all 9 are genuine wall-clock exhaustion, not a defect: all 9
  exceeded the 2-hour limit by 0–28 s, `eplusout.err` empty, no `task.rc`, working files present. No geometry
  issue — **no rebuild needed**, these IDFs are already correct.
- The 9 stems (building / cluster stem / original array idx):
  `240880193_part0` `d05053aee5953e2b` idx132; `240880367_part0` `5e0376cc50cbea69` idx171;
  `240880384_part0` `eb1dd6ffa1a5f622` idx179; `240881149_part0` `92de3427ce129748` idx231;
  `240881166_part0` `ed3e2d36d0c44b80` idx237; `240881271_part0` `2a197dac889ada83` idx261;
  `240881280_part0` `aec18ccb210f0bca` idx264; `240881308_part0` `4a1d49fc78fa56c6` idx267;
  `240881534_part0` `1836a0cc5d117063` idx284.
- Current limit: `scripts/cluster/submit_fleet_t08.sbatch:5` (`--time=02:00:00`). **Do not edit that shared
  script** — it is used by every district's submission. Override on the command line instead:
  `sbatch --time=03:00:00 --array=...`.
- 8/9 are large buildings (≥72nd percentile floor area vs the 288 completed Lyon buildings); one outlier
  (`240880367_part0`, 798 m², 48th percentile) does not fit the size explanation as cleanly — watch it
  specifically; if it times out again at 3h, do not resubmit it a third time without reporting back first.

## Task

1. Build (or reuse, if still present, byte-identical) the IDFs for exactly these 9 stems — no code change, no
   rebuild through a modified path.
2. Ship to a dedicated fleet dir if needed (or reuse the existing Lyon base tree location if the IDFs are
   already there and untouched — confirm before reusing).
3. Submit **one** `sbatch --array` over exactly these 9 stems, `--time=03:00:00` overriding the script default,
   fire-and-forget.
4. Once drained: harvest, fold results into the Lyon manifest, regenerate the Lyon viewer, mirror, `diff -rq`
   check.
*Standing constraint.* Never tune an input to move an EUI into a band. Every Speed failure still classified
and carried, never dropped.

## Report back (to the manager, not into shared docs)

Job ID, array size (9), `sacct` completed/failed/timeout counts per stem; recovered heating figures and new
Lyon pooled EUI (before/after); whether the 798 m² outlier recovered or timed out again; `diff -rq` mirror
output (pasted, not summarised). Under 250 words.
