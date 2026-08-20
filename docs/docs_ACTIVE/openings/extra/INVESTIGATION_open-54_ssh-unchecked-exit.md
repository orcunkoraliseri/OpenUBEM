# INVESTIGATION — `_ssh` returns a string and never raises, so remote failures surface late and in the wrong place

**Slug:** `open-54_ssh-unchecked-exit`
**Opened:** 2026-08-18, during the OPEN-48 third fleet run
**Trigger:** `nyc_centre` died `rc=1` at 18:27 after 43 minutes of clean local work
**Status:** diagnosed; remedy specified; **remedy deliberately not applied** (§6)
**Related:** `implemenation/previous/PLAN_open-48-third-fleet-run-2026-08-18.md`, T02/T03

---

## 1. What was observed

`nyc_centre` cleared every local stage of the pipeline without a complaint:

- Step 1 loaded the seeded cache (`Step 1: loading cached GDF`) — no OSM fetch, exactly as run 3 intends
- Step 2 re-ran against current code: 738 buildings, 35 `OpenUBEMUnknown`, 7 `Courthouse`
- Step 3 generated **738/738 IDFs in 2507.3 s**, status counts `{'success': 738}`
- Both LIVE_SMOKE gates PASS — generation 100.0% against a ≥95% gate, Unknown 4.7% against a <20% gate

and then died on the first line of the cluster ship:

```
scp: dest open "/speed-scratch/o_iseri/fleets/open48_refleet3_nyc_centre/fleet.lst":
     No such file or directory
scp: failed to upload file .../fleet_staging/fleet.lst to .../fleet.lst
CalledProcessError: Command '['scp', ...]' returned non-zero exit status 1
  at v12_cell_pipeline.py:267 in ship_to_cluster
```

Forty-three minutes of correct work thrown away because a directory was missing.

---

## 2. The fault is one line above the traceback

The traceback names the `scp` at `:267`. **The `scp` is the victim.** The fault is at `:265`:

```python
_ssh(f"mkdir -p {remote_fleet_dir}/idfs {remote_fleet_dir}/weather {remote_fleet_dir}/out")

subprocess.run(["scp", str(fleet_lst), f"{REMOTE_HOST}:{remote_fleet_dir}/fleet.lst"],
               check=True, timeout=60)
```

and, underneath it, in the helper that line calls (`:111-116`):

```python
def _ssh(cmd: str, timeout: int = 120) -> str:
    result = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout + result.stderr
```

**`_ssh` never inspects `result.returncode`.** It concatenates the two streams and hands back a string.
A remote command that failed is indistinguishable from one that succeeded quietly — unless the caller
parses the returned text, and `:265` does not even bind the return value.

So the `mkdir` failed, nothing noticed, and the very next statement wrote into a directory that did not
exist. The error the operator is shown points at the wrong line, in the wrong function, about the wrong
operation.

**That is the whole defect.** Everything below is about how far it reaches.

---

## 3. Blast radius — every `_ssh` call site, classified

Eight calls, four distinct safety classes.

| Line | Call | Result used? | Class |
|---|---|---|---|
| 265 | `mkdir -p` (ship) | **discarded** | **UNGUARDED — this is what failed** |
| 457 | `mkdir -p` (repair fleet) | **discarded** | **UNGUARDED — same bug, not yet hit** |
| 536 | `mkdir -p` (reroute fleet) | **discarded** | **UNGUARDED — same bug, not yet hit** |
| 306 | `sbatch …` | parsed for `Submitted batch job` | guarded by content; `sys.exit(1)` if absent |
| 325 | `squeue -j ID --noheader 2>/dev/null \| wc -l` | `int()` if digit, else `-1` | **FALSE-SUCCESS PATH — §3.1** |
| 327 | `sacct … \| uniq -c` | printed only | cosmetic |
| 334 | `sacct … JobID,State,ExitCode` | printed only | cosmetic |
| 939 | remote completeness probe | regex; no match → `0` | fails safe (re-does work) |

Three call sites carry the identical unguarded-`mkdir` bug. Only one of them has fired.

### 3.1 The call site that is worse than the one that bit us

`:325`, inside `poll_cluster`:

```python
out = _ssh(f"squeue -j {job_id} --noheader 2>/dev/null | wc -l", timeout=60)
pending_count = int(out.strip()) if out.strip().isdigit() else -1
...
if pending_count == 0:
    print(f"[{cell_name}] Job {job_id}: no tasks in queue.")
    ...
    break
```

`pending_count == 0` is the signal that **the SLURM array has finished** and the pipeline may go fetch
results. There are two ways to reach it:

1. The job genuinely left the queue. Intended.
2. **`squeue` itself failed.** Its diagnostics are sent to `/dev/null` by the `2>/dev/null` *inside* the
   remote command, stdout is empty, and `wc -l` faithfully reports **`0`**. `_ssh` returns `"0"`,
   `isdigit()` passes, `pending_count` becomes `0`, and the poll loop **breaks and declares the job
   complete.**

A SLURM controller hiccup is therefore read as *"all tasks done"*, and the run proceeds to harvest
results that were never produced. The `nyc_centre` failure was loud and cost 43 minutes. **This one is
silent and would corrupt a fleet number.**

Note the asymmetry that makes it dangerous. A *transport* failure is safe here: ssh's own stderr gets
concatenated into `out` by `_ssh`, so `isdigit()` fails, `pending_count` becomes `-1`, and the loop
keeps polling. Only a *remote-command* failure — precisely the case `2>/dev/null` hides — yields the
bare `0`. **The stderr suppression and the sentinel interact to convert an error into a success.**

**Not observed in this run.** Recorded because the analysis found it, not because it fired.

---

### 3.2 🔴 Correction — "cosmetic" was the wrong word, and `la_urban` proved it

**Added 2026-08-18 19:28, after `la_urban` died `rc=1` at 42 minutes.**

§3's table classified `:327` and `:334` — the two `sacct` calls — as *"printed only | cosmetic"*. That
judgement was about the **return value**, and on that narrow point it holds: nothing downstream reads
the string. **It was still the wrong conclusion**, because it silently assumed the only way a call site
can hurt you is through the value it returns.

`la_urban` failed here:

```
File "v12_cell_pipeline.py", line 327, in poll_cluster
    sacct_out = _ssh(f"sacct -j {job_id} --format=State --noheader 2>/dev/null | sort | uniq -c", timeout=60)
...
subprocess.TimeoutExpired: Command '['ssh', ..., "bash -lc 'sacct -j 1271807 ...'"]' timed out after 60 seconds
```

`_ssh` passes `timeout=` straight to `subprocess.run` and never catches `TimeoutExpired`. So **every**
`_ssh` call site is fatal on a slow login node, whether or not its result is used. A status line that
exists only to be printed took down 42 minutes of completed work — and the SLURM array
(`1271807`) it was reporting on was very likely fine.

**The two failure modes are opposite in character and need opposite fixes:**

| | mechanism | symptom | fix |
|---|---|---|---|
| unchecked exit code (§2) | remote command fails, `_ssh` returns quietly | failure surfaces **later**, at the wrong line | raise on non-zero `returncode` |
| **unhandled timeout (this section)** | login node is slow, `subprocess` raises | failure surfaces **immediately**, at a line that did not matter | **catch `TimeoutExpired`** and return a sentinel at tolerant call sites |

Adding `check=True` alone — the §6 remedy as first written — would **not** have saved `la_urban`.

**Revised remedy.** In addition to §6: `_ssh` takes a `tolerant: bool = False`. When set, it catches
`TimeoutExpired` (and connection errors) and returns a sentinel instead of propagating. The two `sacct`
display calls and the completeness probe are `tolerant=True`. **A call whose output is only printed must
never be able to end a run.** Poll-loop calls stay intolerant but should retry before giving up, since a
transient slow login node is the expected condition, not an exceptional one.

**Re-scoring the table:** `:327` and `:334` are **not** cosmetic. They are *unguarded on the timeout
axis while harmless on the exit-code axis* — which is precisely why one word for "safe" was too coarse.

---

### 3.3 ✅ The blast-radius table was right — all three named sites have now fired

**Added 2026-08-18 20:27.** §3 listed three unguarded `mkdir` sites (`:265`, `:457`, `:536`) and noted
*"only one of them has fired."* Within three hours, **three different call sites from that table took
down three different cells**:

| cell | site | flavour |
|---|---|---|
| `nyc_centre` 18:27 | `:265` → `scp` at `:267` | unguarded `mkdir` (§2) |
| `la_urban` 19:28 | `:327` | **timeout** on a display-only `sacct` (§3.2) |
| `austin_suburban` 20:27 | `:536` → `scp` at `:539` | unguarded `mkdir`, **reroute** path |

`austin_suburban` is the same shape as `nyc_centre`, one function further on: the reroute `mkdir` at
`:536` failed unnoticed, and the `scp` at `:539` became the visible error — after the cell had already
completed its full simulation and entered repair. **The cost is higher here than at `:265`**, because
`:457` and `:536` are reached only *after* a cell has simulated and is being repaired: a failure there
discards a completed array, not just an upload.

**Three cells of twelve lost to this defect in one run.** §6's remedy is unchanged; what changes is its
priority. This is no longer a rare event — it is the single largest source of lost work in run 3.

---

### 3.4 🔴 The cost is not a rerun — it is a misclassified finding

`austin_centre` failed at 20:37:49 with `subprocess.TimeoutExpired` at **`:334`**, the second `sacct`
call in `poll_cluster`, seven lines below the site that killed `la_urban`. That makes four distinct
sites fired in one run (`:265`, `:327`, `:334`, `:536`) and two instances of the timeout axis that
§3.2 added. The site count is no longer the interesting part.

What matters is what the crash did to the *record*. `austin_centre` had already tripped the zero-fail
gate with **20 failed buildings against a tolerance of 5** — printed at log line 1602 — and was inside
the repair stage when the `sacct` read timed out. The cell exited `rc=1`. On the return code it is a
transport failure; on the evidence it is a model failure that happened to die twice.
`austin_suburban` (`:536`, 14 failures against a tolerance of 5) reads the same way.

So the defect did not cost two reruns. It moved two of twelve cells out of the OPEN-55 column and into
this one, and it did so **in the direction that understates the other finding**: the run appeared to
have three stopping cells when it had five. *(Corrected 20:50: the totals here were first written as six and eight; with all twelve cells landed the measured counts are three labelled `rc=2` and five in all. The re-classification argument is unaffected — two cells moved column either way.)* The only reason this was recoverable is an accident of
print ordering — the gate writes its count before the repair stage runs. Had the timeout landed one
stage earlier, the twenty failures would have left no trace.

This generalises, and it is the argument for the remedy in §6. A crash truncates evidence; it never
fabricates it. So an unchecked exit status does not produce random misclassification — it produces
**systematically optimistic** misclassification, because everything the run would have discovered
after the crash point is scored as "did not happen". A defect that silently biases the conclusions of
whatever investigation it interrupts is not a robustness nicety, and it should not be closed by
handling the two sites that were observed to fire.

## 4. What was ruled out, by measurement

The `nyc_centre` `mkdir` failure itself is **transient**. Three hypotheses were tested rather than
assumed.

**Quota — excluded.** `/speed-scratch` reports 6.3T used against a 9.8T warn and 10.0T limit, and 4M
files against no file limit at all. Home and `/groups` sit near their caps but are not written by this
path.

**Systemic block — excluded.** At the moment of failure the remote directories
`open48_refleet3_nyc_urban`, `_nyc_suburban` and `_nyc_rural` all existed and were being written
normally — `nyc_urban` had already accumulated 26G. Only `_nyc_centre` was absent. One call failed, not
the mechanism.

**Concurrency / SSH saturation — not supported.** This was the leading hypothesis, and the reason run 3
was lowered to `MAX_PARALLEL=4` after run 2 lost two cells at 6. Tested directly: **three waves of six
simultaneous `ssh` + `mkdir`, 18 of 18 succeeded** — higher concurrency than the run itself uses. Three
sequential probes immediately after the failure also returned clean.

Connection establishment at six-way concurrency is therefore **not** the bottleneck.

**Caveat, stated so this is not overread.** Those probes are cheap and short-lived. Real cells hold
long-running transfers concurrently — a gzip tar stream of 738 IDFs, then result fetches from a 26G
output tree. The probe tests whether connections can be *established*, not whether sustained transfers
degrade. It refutes the simple saturation story; it does **not** establish that concurrency is harmless.

---

## 5. What remains unexplained

**Why that particular `mkdir` failed is not known, and the evidence that would settle it no longer
exists** — `_ssh` discarded the remote stderr that would have said so.

That is the defect indicting itself: the one diagnostic capable of explaining the failure was thrown
away by the very code under investigation.

This is the honest boundary of this document. The failure is rare, not reproducible on demand, and
recovers on retry. Anything more specific would be invention.

---

## 6. Remedy — specified, and deliberately not applied

The repair is small and obvious:

- give `_ssh` a `check: bool = True` parameter that raises on a non-zero `returncode`, carrying the
  remote stderr into the exception message
- pass `check=False` at the two `sacct` display calls and the completeness probe, which legitimately
  tolerate failure
- at `:325`, stop suppressing `squeue`'s stderr — or distinguish "empty output" from "zero lines" — so
  the false-success path in §3.1 becomes unreachable

**It is not being applied now.** Two reasons, both binding:

1. **`v12_cell_pipeline.py` must not be edited** — §2 rule 2 of the run-3 plan, inherited from §2 of
   `PLAN_three-rulings-2026-08-12.md`.
2. More importantly: **editing the pipeline midway through a twelve-cell run would destroy the
   single-variable comparison the run exists to make.** Cells that ran before the edit and cells that
   ran after it would no longer be comparable, and run 3 would inherit exactly the interpretability
   defect that made run 2 useless.

The correct order is: finish run 3 on unchanged code, *then* fix this.

---

## 7. Disposition

- `nyc_centre` is re-run **alone, after the other eleven cells land** — plan §2 rule 5, task T03. Its
  partial output is discarded rather than reused.
- The retry re-does step 2 and all 738 IDFs (~42 min), because `run_cell:988` unlinks the step-3
  manifest. That is sound: generation was previously shown byte-identical on unchanged inputs, 738/738.
- This defect is registered as **OPEN-54**. It is a repository defect, independent of OPEN-48, and it
  outlives this run.
- **The `:325` false-success path is the part worth acting on** — more than the failure that prompted
  this document.
