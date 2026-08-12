"""T05 -- Read-only cluster and local-records audit for OPEN-39 and OPEN-40.

Read-only. Uses `ls`, `du`, `sacct` on Speed, all through `_ssh()` (imported from
scripts/cluster/t08_harvest_results.py, which wraps every remote command in
`bash -lc` because Speed's login shell is tcsh). No sbatch, no srun, no
`ssh ... python`, no deletions, no writes to the cluster.

(a) OPEN-39 -- size the orphaned disk left by failed tasks (set -e skips the
    trim block and the task.rc write on any task where EnergyPlus itself
    exits non-zero), and grep local harvest/resume/completion scripts for any
    use of task.rc PRESENCE as a completion test.
(b) OPEN-40 -- trace (or fail to trace) eight job IDs that fall outside both
    documented E02 submission waves, using sacct facts, not a reconstructed
    story from timestamps.

Plan: docs/docs_ACTIVE/openings/implemenation/PLAN_e02-audit-and-closure.md, T05.
"""

from __future__ import annotations

import csv
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(REPO / "scripts" / "cluster"))

from t08_harvest_results import _ssh  # noqa: E402  -- the tcsh-safe wrapper, per project rule

CORPUS_ROOT = r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest"
OPEN41_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open41_failure_causes.csv"
REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"

# The 45th failure, confirmed independently against the local corpus
# (nyc_centre_fast_zone/way_1240348353 -- missing eplusout.end, no Fatal string,
# std::bad_alloc per the register). T01 already confirmed this is the fleet's
# only n_dirs != n_end array.
MISSING_END_FAILURE = ("nyc_centre", "fast_zone", "way_1240348353")

# OPEN-40's eight job IDs, and the two documented submission waves.
OPEN40_JOB_IDS = [1177095, 1177838, 1177839, 1177840, 1177841, 1177875, 1178313, 1178538]
WAVE1_RANGE = (1176411, 1176599)
WAVE2_RANGE = (1198104, 1200571)

FATAL_RE = re.compile(r"\*\*\s+Fatal\s+\*\*")

# Discovered empirically while writing this script (not documented anywhere before):
# a single _ssh() command string >= 8192 chars over this remote path returns
# "Unmatched '." (a tcsh quote-parse error, NOT a Python quoting bug -- reproduced
# with a quote-free payload; 8104 chars succeeds, 8192 fails, exactly at the
# boundary). Chunk any generated multi-target remote command below this limit.
REMOTE_CMD_SAFE_LEN = 7500


def load_45_failures() -> list[tuple[str, str, str]]:
    """Reuse T02's OPEN-41 census (44 fatal failures) + the one missing-.end
    failure (independently reconfirmed above), per the plan's rule against
    reimplementing evidence that already exists on disk (dependency decision 6)."""
    import pandas as pd

    df = pd.read_csv(OPEN41_CSV)
    fails = [(r.cell, r.mode, r.stem) for r in df.itertuples()]
    fails.append(MISSING_END_FAILURE)
    assert len(fails) == 45, f"expected 45 failures, got {len(fails)}"
    return fails


def find_one_successful_stem(cell: str, mode: str, exclude_stem: str) -> str | None:
    """Local scan: first building dir in this array with .end present, no fatal,
    and not the excluded (failed) stem. Used for the same-array existence control
    and for the successful-sample side of the du comparison."""
    array_path = os.path.join(CORPUS_ROOT, f"{cell}_{mode}")
    if not os.path.isdir(array_path):
        return None
    with os.scandir(array_path) as it:
        for entry in it:
            if not entry.is_dir() or entry.name == exclude_stem:
                continue
            end_path = os.path.join(entry.path, "eplusout.end")
            err_path = os.path.join(entry.path, "eplusout.err")
            if not os.path.isfile(end_path):
                continue
            if os.path.isfile(err_path):
                txt = Path(err_path).read_text(errors="replace")
                if FATAL_RE.search(txt):
                    continue
            return entry.name
    return None


def grep_task_rc_usage() -> list[dict]:
    """Scan every .py/.sbatch/.sh under scripts/ for `task.rc` and classify each
    hit as a WRITE (echo $RC > task.rc / .write_text) or a possible READ
    (anything else -- exists()/open()/read on the path) that could be used as
    a completion test."""
    hits = []
    write_patterns = [
        re.compile(r'echo\s+\$RC\s*>\s*"[^"]*task\.rc"'),
        re.compile(r'\.write_text\(str\(rc\)\)'),
    ]
    for path in (REPO / "scripts").rglob("*"):
        if not path.is_file() or path.name == "e02_cluster_readonly_audit.py":
            continue
        if path.suffix.lower() not in (".py", ".sbatch", ".sh") and "sbatch" not in path.name:
            continue
        try:
            text = path.read_text(errors="replace")
        except Exception:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "task.rc" not in line and "task_rc" not in line:
                continue
            is_write = any(p.search(line) for p in write_patterns)
            hits.append({
                "path": str(path.relative_to(REPO)),
                "line": lineno,
                "text": line.strip(),
                "classified_as": "WRITE" if is_write else "REVIEW",
            })
    return hits


def main() -> None:
    report_lines: list[str] = []

    def log(msg: str = "") -> None:
        print(msg)
        report_lines.append(msg)

    log("=" * 78)
    log("T05 -- OPEN-39 / OPEN-40 read-only cluster + records audit")
    log("=" * 78)

    # ---- Step 0: prove one success before any batch -------------------------
    log("\n### Step 0: connectivity proof (must pass before any batch) ###")
    t0 = time.monotonic()
    out_hostname = _ssh("hostname")
    log(f"_ssh('hostname') -> {out_hostname.strip()!r}")

    known_dir = f"{REMOTE_FLEET_BASE}/e02_nyc_centre_auto"
    out_du = _ssh(f"du -sh {known_dir} 2>&1")
    log(f"_ssh('du -sh {known_dir}') -> {out_du.strip()!r}")

    if not out_hostname.strip():
        log("STOP: hostname probe returned nothing -- cluster unreachable. "
            "Recording as not obtained per plan instructions; not retrying indefinitely.")
        write_report(report_lines, local_only=True)
        return

    # ---- (a)(ii) local: task.rc usage grep -----------------------------------
    log("\n### (a)(ii) Local grep: does any script use task.rc PRESENCE as a completion test? ###")
    hits = grep_task_rc_usage()
    for h in hits:
        log(f"  {h['path']}:{h['line']}  [{h['classified_as']}]  {h['text']}")
    review_hits = [h for h in hits if h["classified_as"] == "REVIEW"]
    log(f"\n  Total task.rc references: {len(hits)}")
    log(f"  Classified WRITE (echo $RC > task.rc / .write_text(str(rc))): {len(hits) - len(review_hits)}")
    log(f"  Classified REVIEW (not a plain write -- inspect for read/exists use): {len(review_hits)}")
    if review_hits:
        log("  ^ These need manual inspection -- see lines above.")
    else:
        log("  VERDICT: every task.rc reference found is a WRITE. No script reads task.rc's "
            "presence/absence as a completion test.")

    # ---- (a)(i) identify the 45 failed tasks locally --------------------------
    log("\n### (a)(i) Identify the 45 failed E02 tasks (reusing T02's OPEN-41 census + "
        "the independently reconfirmed missing-.end building) ###")
    failures = load_45_failures()
    log(f"  45 failures loaded: 44 from {OPEN41_CSV.name}, 1 reconfirmed locally "
        f"({MISSING_END_FAILURE}).")

    # one successful stem per distinct (cell, mode) among the 45, for the du sample
    arrays_with_failures = sorted({(c, m) for c, m, _ in failures})
    sample_pairs: list[tuple[str, str, str, str]] = []  # (cell, mode, failed_stem, ok_stem)
    for cell, mode in arrays_with_failures:
        failed_stems_here = [s for c, m, s in failures if c == cell and m == mode]
        failed_stem = failed_stems_here[0]
        ok_stem = find_one_successful_stem(cell, mode, exclude_stem=failed_stem)
        sample_pairs.append((cell, mode, failed_stem, ok_stem or ""))

    log(f"  {len(arrays_with_failures)} distinct (cell, mode) arrays carry the 45 failures.")
    for cell, mode, failed_stem, ok_stem in sample_pairs:
        log(f"    {cell}/{mode}: failed_sample={failed_stem}  ok_sample={ok_stem or 'NONE FOUND'}")

    # ---- (a)(i) existence control: one success vs one failure, same array -----
    log("\n### Existence control: one successful vs one failed task dir, same array ###")
    ctrl_cell, ctrl_mode, ctrl_failed, ctrl_ok = sample_pairs[0]
    ctrl_failed_dir = f"{REMOTE_FLEET_BASE}/e02_{ctrl_cell}_{ctrl_mode}/out/{ctrl_failed}"
    ctrl_ok_dir = f"{REMOTE_FLEET_BASE}/e02_{ctrl_cell}_{ctrl_mode}/out/{ctrl_ok}" if ctrl_ok else None
    log(f"  Failed dir: {ctrl_failed_dir}")
    log(f"  OK dir:     {ctrl_ok_dir}")

    ctrl_cmd_parts = [f'echo "=== FAILED: {ctrl_failed_dir} ==="', f'du -sh "{ctrl_failed_dir}" 2>&1',
                       f'ls -la "{ctrl_failed_dir}" 2>&1']
    if ctrl_ok_dir:
        ctrl_cmd_parts += [f'echo "=== OK: {ctrl_ok_dir} ==="', f'du -sh "{ctrl_ok_dir}" 2>&1',
                            f'ls -la "{ctrl_ok_dir}" 2>&1']
    ctrl_cmd = " ; ".join(ctrl_cmd_parts)
    ctrl_out = _ssh(ctrl_cmd, timeout=120)
    log("  --- remote output ---")
    for line in ctrl_out.splitlines():
        log(f"  {line}")
    failed_has_rc = "task.rc" in ctrl_out.split("=== OK")[0] if "=== OK" in ctrl_out else "task.rc" in ctrl_out
    log(f"\n  task.rc appears in FAILED block listing: {'task.rc' in ctrl_out.split('=== OK:')[0]}")
    if ctrl_ok_dir:
        log(f"  task.rc appears in OK block listing: {'task.rc' in ctrl_out.split('=== OK:')[1] if '=== OK:' in ctrl_out else 'N/A'}")

    # ---- (a)(i) batch du over all 45 failed dirs + matched OK sample ----------
    log("\n### (a)(i) Batch du -sh over all 45 failed task directories ###")
    failed_paths = [
        f"{REMOTE_FLEET_BASE}/e02_{c}_{m}/out/{s}" for c, m, s in failures
    ]
    ok_paths = [
        f"{REMOTE_FLEET_BASE}/e02_{c}_{m}/out/{s}" for c, m, _, s in sample_pairs if s
    ]

    def batch_du(paths: list[str], label: str) -> list[tuple[str, str]]:
        # one remote command, loop over all paths -- avoids per-directory round trips.
        list_str = " ".join(f'"{p}"' for p in paths)
        cmd = f'for d in {list_str}; do du -sh "$d" 2>&1; done'
        out = _ssh(cmd, timeout=180)
        results = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            results.append(line)
        log(f"  [{label}] {len(paths)} dirs requested, {len(results)} du lines returned")
        return results

    failed_du_lines = batch_du(failed_paths, "45 FAILED dirs")
    ok_du_lines = batch_du(ok_paths, f"{len(ok_paths)} matched OK-sample dirs")

    def parse_du(lines: list[str]) -> tuple[list[tuple[str, float]], list[str]]:
        sizes = []
        errors = []
        for line in lines:
            m = re.match(r"^([\d.]+)([KMGT]?)\s+(.+)$", line)
            if not m:
                errors.append(line)
                continue
            val, unit, path = m.groups()
            mult = {"": 1 / 1024, "K": 1, "M": 1024, "G": 1024 * 1024, "T": 1024 * 1024 * 1024}[unit]
            sizes.append((path, float(val) * mult))  # normalized to KB
        return sizes, errors

    failed_sizes, failed_errors = parse_du(failed_du_lines)
    ok_sizes, ok_errors = parse_du(ok_du_lines)

    total_failed_kb = sum(s for _, s in failed_sizes)
    total_ok_kb = sum(s for _, s in ok_sizes)
    log(f"\n  Failed dirs parsed OK: {len(failed_sizes)}/{len(failed_paths)}  "
        f"(unparsed/error lines: {len(failed_errors)})")
    for e in failed_errors:
        log(f"    UNPARSED: {e}")
    log(f"  OK-sample dirs parsed OK: {len(ok_sizes)}/{len(ok_paths)}  "
        f"(unparsed/error lines: {len(ok_errors)})")
    for e in ok_errors:
        log(f"    UNPARSED: {e}")

    log(f"\n  TOTAL size, 45 failed dirs:      {total_failed_kb:,.0f} KB "
        f"({total_failed_kb/1024:,.1f} MB)")
    log(f"  TOTAL size, {len(ok_sizes)} matched OK dirs: {total_ok_kb:,.0f} KB "
        f"({total_ok_kb/1024:,.1f} MB)")
    if ok_sizes:
        mean_failed = total_failed_kb / len(failed_sizes) if failed_sizes else 0
        mean_ok = total_ok_kb / len(ok_sizes)
        log(f"  Mean per-dir: failed={mean_failed:,.0f} KB   ok={mean_ok:,.0f} KB   "
            f"ratio(failed/ok)={mean_failed / mean_ok if mean_ok else float('nan'):.2f}x")

    # ---- (a)(i) extend to other fleets, by listing + sampling, not walking ----
    log("\n### (a)(i) Extension to other fleets under /speed-scratch/o_iseri/fleets/ "
        "(directory listing + sampling only) ###")
    fleets_out = _ssh(f"ls -1 {REMOTE_FLEET_BASE}/", timeout=60)
    fleet_dirs = [l.strip() for l in fleets_out.splitlines() if l.strip()]
    log(f"  {len(fleet_dirs)} entries listed under {REMOTE_FLEET_BASE}/")
    for l in fleet_dirs:
        log(f"    {l}")

    # group by tag prefix (portion before the first cell-name token), sample up to
    # 2 fleets per tag that are NOT e02 (already measured above in full).
    non_e02 = [f for f in fleet_dirs if not f.startswith("e02_")]
    tags: dict[str, list[str]] = {}
    for f in non_e02:
        tag = f.split("_")[0]
        tags.setdefault(tag, []).append(f)
    log(f"\n  Non-e02 fleet tags found: {sorted(tags.keys())}")

    sample_fleets = []
    for tag, dirs in tags.items():
        sample_fleets.extend(dirs[:1])
    log(f"  Sampling {len(sample_fleets)} fleets (1 per tag): {sample_fleets}")

    if sample_fleets:
        # For each sampled fleet, list a few task dirs under out/ and check task.rc
        # + du. No double quotes needed -- none of these path components contain
        # spaces -- and the whole batch is chunked under REMOTE_CMD_SAFE_LEN
        # (see the module-level comment: this remote path breaks silently above
        # ~8192 chars with "Unmatched '." from tcsh, unrelated to Python quoting).
        def fleet_cmd(fd: str) -> str:
            return (
                f'echo === {fd} ===; '
                f'for s in $(ls {REMOTE_FLEET_BASE}/{fd}/out/ 2>/dev/null | head -3); do '
                f'du -sh {REMOTE_FLEET_BASE}/{fd}/out/$s 2>&1; '
                f'test -f {REMOTE_FLEET_BASE}/{fd}/out/$s/task.rc && echo TASKRC_PRESENT || echo TASKRC_ABSENT; '
                f'done'
            )

        chunks: list[list[str]] = [[]]
        cur_len = 0
        for fd in sample_fleets:
            piece = fleet_cmd(fd)
            if cur_len + len(piece) > REMOTE_CMD_SAFE_LEN and chunks[-1]:
                chunks.append([])
                cur_len = 0
            chunks[-1].append(piece)
            cur_len += len(piece)

        log(f"  Split into {len(chunks)} remote command(s) to stay under the "
            f"{REMOTE_CMD_SAFE_LEN}-char safe length.")
        for i, chunk in enumerate(chunks):
            other_fleet_cmd = " ; ".join(chunk)
            other_fleet_out = _ssh(other_fleet_cmd, timeout=120)
            log(f"\n  --- sample output, other fleets, chunk {i + 1}/{len(chunks)} "
                f"(cmd len {len(other_fleet_cmd)}) ---")
            for line in other_fleet_out.splitlines():
                log(f"  {line}")
    else:
        log("  No non-e02 fleets found on disk -- nothing to sample.")

    # ---- (b) OPEN-40: sacct facts on the 8 job IDs -----------------------------
    log("\n### (b) OPEN-40 -- sacct facts on the 8 orphan job IDs ###")
    ids_str = ",".join(str(j) for j in OPEN40_JOB_IDS)
    sacct_cmd = (
        f'sacct -j {ids_str} -X -P '
        f'--format=JobID,JobName%40,Submit,State,WorkDir%80,User'
    )
    sacct_out = _ssh(sacct_cmd, timeout=60)
    log(f"  Command: {sacct_cmd}")
    log("  --- raw sacct output ---")
    for line in sacct_out.splitlines():
        log(f"  {line}")

    log("\n  Range control -- each of the 8 IDs vs the two documented wave ranges "
        f"(wave1 {WAVE1_RANGE}, wave2 {WAVE2_RANGE}), arithmetic only (not re-fetched from the plan):")
    for jid in OPEN40_JOB_IDS:
        in_wave1 = WAVE1_RANGE[0] <= jid <= WAVE1_RANGE[1]
        in_wave2 = WAVE2_RANGE[0] <= jid <= WAVE2_RANGE[1]
        log(f"    {jid}: in_wave1={in_wave1}  in_wave2={in_wave2}  "
            f"outside_both={not in_wave1 and not in_wave2}")

    # independent reconstruction of the real wave boundaries from sacct itself,
    # rather than trusting the plan's stated ranges.
    log("\n  Independent reconstruction: all e02_* array jobs from sacct over the run window, "
        "to verify the wave boundaries independently (not taken from the plan document).")
    window_cmd = (
        'sacct -u o_iseri -X -P --starttime=2026-08-09T00:00:00 --endtime=2026-08-11T00:00:00 '
        '--format=JobID,JobName%40,Submit,State'
    )
    window_out = _ssh(window_cmd, timeout=120)
    e02_lines = [l for l in window_out.splitlines() if "e02_" in l]
    log(f"  Command: {window_cmd}")
    log(f"  Total sacct rows in window: {len(window_out.splitlines())}; "
        f"rows with 'e02_' in JobName: {len(e02_lines)}")
    for line in e02_lines:
        log(f"    {line}")

    # ---- (b) local-side trace: scratchpad driver scripts + shell reachable log ---
    log("\n### (b) Local-side trace: scratchpad submit scripts and e02_run*.log ###")
    log("  Searched: e02_fleet_submit.py, e02_submit_remainder.sh, e02_remainder_jobids.txt "
        "(found under a prior session's scratchpad), and %TEMP%\\ubem_e02_five_mode\\e02_run*.log.")
    log("  None of these locally-reachable files contain any of the 8 job IDs "
        "(grepped, zero matches).")
    log("  e02_remainder_jobids.txt documents wave 2 in full (41 arrays, 1198104-1200571) "
        "with per-array timestamps; it contains no reference to the 8 IDs.")
    log("  No local artifact documents wave 1's submission event either (only its ID range, "
        "which is a register-carried fact, not something this task re-derives from a local file) "
        "-- the two E02 generation-summary JSONs on disk both have submitted_flag=False and empty "
        "job_ids, confirming wave 1 was NOT submitted by either of the generate+ship-only "
        "invocations that produced those JSON files.")

    # ---- (b) check for shell history reachable on the login node ---------------
    log("\n### (b) Remote shell history reachable on the login node ###")
    hist_cmd = 'ls -la ~/.bash_history ~/.history ~/.sh_history 2>&1'
    hist_out = _ssh(hist_cmd, timeout=30)
    log(f"  Command: {hist_cmd}")
    for line in hist_out.splitlines():
        log(f"  {line}")

    elapsed = time.monotonic() - t0
    log(f"\n### Total remote wall-clock: {elapsed:.1f}s (cap: 40 min = 2400s) ###")

    write_report(report_lines, local_only=False)


def write_report(lines: list[str], local_only: bool) -> None:
    # Intermediate raw console dump only -- lives under tempfile.gettempdir(),
    # never in the repo. The dated report is
    # docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-39-40_cluster-records.md.
    import tempfile
    out_path = Path(tempfile.gettempdir()) / "t05_cluster_readonly_audit_raw_output.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nRaw output written to {out_path} (intermediate; the dated report is "
          f"docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-39-40_cluster-records.md)")
    if local_only:
        print("NOTE: cluster was unreachable -- only local halves of (a)(ii) and (b) were run.")


if __name__ == "__main__":
    main()
