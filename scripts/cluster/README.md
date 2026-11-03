# Cluster Offload Runbook — OpenUBEM on Speed (SLURM)

## Polite ceiling policy (hard limits — never raise without manager approval)

| Resource | Pilot (8 bldg) | Full fleet (≤483 bldg) |
|---|---|---|
| Partition | `ps` | `ps` |
| Array throttle | `%8` | `%32` |
| CPUs per task | 1 | 1 |
| Memory per task | 6G | 6G |
| Wall time | 1:30:00 | 1:30:00 |
| Job name prefix | `openubem_` | `openubem_` |

EnergyPlus is single-threaded per building — never raise cpus-per-task above 1.
Never use GPU or fat-node partitions.

---

## Prerequisites

- SSH key auth from local machine to `speed.encs.concordia.ca` (BatchMode).
- EnergyPlus 23.1.0 Ubuntu20.04 extracted at:
  `/speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-87ed9199d4-Linux-Ubuntu20.04-x86_64/`
- Submitted from local machine using `ssh` + `scp`. Never run compute on the login node.

---

## Step 1 — Pack fleet

```bash
# Locally stage IDFs + EPW into a tarball
mkdir -p /tmp/my_fleet/idfs /tmp/my_fleet/weather
cp /path/to/idfs/*.idf /tmp/my_fleet/idfs/
cp /path/to/epw/*.epw /tmp/my_fleet/weather/
# fleet.lst: one osm_id per line, matching IDF filenames (without .idf)
printf '29716487\n240391795\n...\n' > /tmp/my_fleet/fleet.lst
cd /tmp/my_fleet && tar -czf fleet.tar.gz idfs weather fleet.lst
```

## Step 2 — Ship to cluster

```bash
FLEET_REMOTE=/speed-scratch/o_iseri/openubem/fleets/my_fleet
ssh o_iseri@speed.encs.concordia.ca "bash -lc 'mkdir -p ${FLEET_REMOTE}'"
scp /tmp/my_fleet/fleet.tar.gz o_iseri@speed.encs.concordia.ca:${FLEET_REMOTE}/fleet.tar.gz
ssh o_iseri@speed.encs.concordia.ca "bash -lc 'cd ${FLEET_REMOTE} && tar -xzf fleet.tar.gz && mkdir -p out'"
# Verify
ssh o_iseri@speed.encs.concordia.ca "bash -lc 'ls ${FLEET_REMOTE}/idfs | wc -l'"
```

## Step 3 — Submit SLURM array

```bash
N=8        # number of buildings
THROTTLE=8 # pilot: 8; full fleet: 32
FLEET_REMOTE=/speed-scratch/o_iseri/openubem/fleets/my_fleet

ssh o_iseri@speed.encs.concordia.ca \
  "bash -lc 'sbatch --array=1-${N}%${THROTTLE} \
    --export=FLEET_DIR=${FLEET_REMOTE} \
    /speed-scratch/o_iseri/openubem/scripts/submit_fleet.sbatch'"
# → "Submitted batch job NNNNNN"
```

## Step 4 — Poll from local machine (never leave a watch loop on the login node)

```bash
JOB_ID=NNNNNN
# Poll every ~60s from local machine:
ssh o_iseri@speed.encs.concordia.ca \
  "bash -lc 'sacct -j ${JOB_ID} --format=JobID,State,Elapsed,ExitCode --noheader'"
# Repeat until all array tasks show COMPLETED or FAILED.
```

## Step 5 — Fetch results

```bash
LOCAL_OUT=/tmp/ubem_cluster_pilot8
mkdir -p ${LOCAL_OUT}
for OSM_ID in 29716487 240391795 ...; do
  mkdir -p ${LOCAL_OUT}/${OSM_ID}
  for F in eplusout.sql eplusout.err eplusout.end; do
    scp o_iseri@speed.encs.concordia.ca:${FLEET_REMOTE}/out/${OSM_ID}/${F} \
        ${LOCAL_OUT}/${OSM_ID}/${F} || true
  done
done
# Write fleet.lst into LOCAL_OUT (required by manifest adapter)
printf '29716487\n240391795\n...\n' > ${LOCAL_OUT}/fleet.lst
```

## Step 6 — Build Step-4 manifest

```bash
cd C:\Users\o_iseri\Desktop\OpenUBEM
python scripts/cluster/make_manifest_from_cluster.py \
    ${LOCAL_OUT} \
    ${LOCAL_OUT}/04_simulation_manifest.parquet \
    --idf-dir /tmp/ubem_boston_r1/step3/idfs \
    --epw "C:\Users\o_iseri\AppData\Local\openubem\epw_cache\USA_MA_Boston.994971_TMYx.2011-2025.epw" \
    --job-id ${JOB_ID}
```

## Step 7 — Run Step 5

Adapt `scripts/run_r1_t12.py` to point `MERGED_MANIFEST` at the cluster manifest.

## Step 8 — Cleanup remote

```bash
# Keep tools/ and idfs/; delete simulation outputs to free space
ssh o_iseri@speed.encs.concordia.ca \
  "bash -lc 'rm -rf ${FLEET_REMOTE}/out'"
```

---

## Notes on EnergyPlus invocation

IDFs contain `HVACTemplate:*` objects which require `ExpandObjects` preprocessing.
The `submit_fleet.sbatch` script handles this automatically:
1. Copies `Energy+.idd` and the IDF to the building's OUTDIR.
2. Runs `ExpandObjects` (produces `expanded.idf`).
3. Runs `energyplus -w <epw> -d <outdir> expanded.idf`.

Do **not** use `energyplus -x` (inline expand flag) — it attempts to create symlinks
in the source IDF directory and crashes with `filesystem_error: cannot create symlink: File exists`.

## GLIBC note

EnergyPlus 23.1.0 Ubuntu22.04 build requires GLIBC 2.35.
Speed cluster has GLIBC 2.34 → use the **Ubuntu20.04** build tarball:
`EnergyPlus-23.1.0-87ed9199d4-Linux-Ubuntu20.04-x86_64.tar.gz`
Installed at `/speed-scratch/o_iseri/openubem/tools/`.
