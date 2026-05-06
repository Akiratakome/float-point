# 800² double reference — run workflow

**Goal:** produce own-scheme high-resolution reference solutions for LW
Config 3 (HLLC and Rusanov, IEEE double, deterministic, non-MCA) so
that `s_req(N)` can be populated at N ∈ {100, 200, 400, 800}.
**Budget:** per supervisor, ≤ 6 h wall-clock per run.

## 1. Code changes already applied

| File | Change |
|------|--------|
| `src/euler/euler_solver.hpp` | Added `run(double progress_interval_s)` overload — prints a wall-clock-throttled `[progress]` line to stderr; default (no-arg `run()`) is bit-identical to the previous behaviour. Added `#pragma omp parallel for` to `x_sweep`, `y_sweep`, and `compute_dt` outer loops. |
| `src/main.cpp` | Reads `progress_interval_s` (double, default `0.0` = off) from the cfg and forwards it to `solver.run(…)` in both 1D and 2D paths. |
| `CMakeLists.txt` | New cache option `ENABLE_OPENMP=ON` (default on). When on, `find_package(OpenMP)` and link `OpenMP::OpenMP_CXX` to `hrsc_core`. Pragmas are no-ops if OpenMP is missing or disabled. |

**No cfg file is regression-broken** — the new cfg key is optional and
the default (`0.0`) disables printing, so every existing config keeps
its prior stdout/stderr output verbatim.

Progress line format on stderr:

```
[progress:start] step=0   t=0/0.3 (0.00%) elapsed=0.0s eta=0.0s rate=0.0 steps/s
[progress:tick]  step=91  t=0.1056/0.3 (35.20%) elapsed=30.0s eta=55.2s rate=3.0 steps/s
[progress:tick]  step=183 t=0.2112/0.3 (70.40%) elapsed=60.0s eta=25.2s rate=3.1 steps/s
[progress:done]  step=259 t=0.3/0.3 (100.00%) elapsed=85.0s eta=0.0s rate=3.2 steps/s
```

Tail `-f run.err` from another shell shows you it is alive. If the
rate drops to 0 for longer than a few intervals, the job has stalled.

## 2. lovelace vs athena — recommendation

| Axis | lovelace (Cambridge LSC) | athena (Cambridge CSC, SLURM) |
|------|--------------------------|-------------------------------|
| Scheduler | none; shared node | SLURM (`sbatch --time=06:00:00` is a hard cap) |
| Cores per node | 64 shared | 76 per Icelake node (typical) |
| Verificarlo 2.4.0 | pre-installed, Clang 18 | not confirmed installed |
| Walltime hygiene | you must `ps` / `top` yourself | SLURM kills at the `--time=` cap, writes `sacct` log |
| For this 800² run | works; you babysit | **cleaner**: SLURM gives an exit-code log and enforces the 6 h cap automatically |

**For the 800² IEEE-double reference (non-MCA): athena is the better
fit.** Reasons:

1. The 800² reference is a single **deterministic** run per solver;
   it does not need Verificarlo. No dependency on the Clang 18 build
   chain that forced the earlier move to lovelace.
2. SLURM's `--time=06:00:00` hard cap makes the supervisor's 6 h
   budget an automatic, auditable constraint instead of a manual one.
3. Athena Icelake nodes typically give 1.3–1.6× higher single-core
   throughput than lovelace on memory-bandwidth-bound CFD kernels.
4. `sacct` / stderr log files are the exact artifacts we need for the
   feasibility / production log in the Week-4 report.

**Keep lovelace for anything that needs Verificarlo MCA** (the 200²
production batch already lives there and should stay).

## 3. Build on athena

```bash
# Login node
ssh <user>@athena.csc.cam.ac.uk
cd floatpoint                           # or clone/rsync from local

# Env: pick a recent gcc with OpenMP 4.5+ (any GCC ≥ 9 works).
module load gcc/11.3.0                  # or whatever athena has — `module avail gcc`

# Release build with native tuning + OpenMP.
rm -rf build-ref
cmake -B build-ref -DCMAKE_BUILD_TYPE=Release \
      -DENABLE_OPENMP=ON \
      -DCMAKE_CXX_FLAGS="-O3 -march=native -ffp-contract=off"
cmake --build build-ref -j

# Sanity: 200² should now finish in tens of seconds, not minutes.
OMP_NUM_THREADS=16 ./build-ref/hrsc tests/cases/liska_wendroff_2d/config3.cfg \
    > /tmp/sanity.out 2> /tmp/sanity.err
tail /tmp/sanity.err
```

**Why `-ffp-contract=off`**: the 800² result is a *reference*. We
want it to be the same bit-for-bit no matter which CPU reads it back,
so we disable opportunistic FMA contraction. This costs ~5% speed
and is the right call for a reference artifact.

**OpenMP and the MCA pipeline**: leave the runners that drive the
200² MCA batch alone. They already export `OMP_NUM_THREADS=1` — the
pragmas we just added are no-ops under that setting, so the MCA
statistics are unaffected.

## 4. Cfg files for the 800² runs

Two new cfgs — copy from the existing 200² versions and change
`nx`/`ny` + enable progress prints. Put them in
`tests/cases/liska_wendroff_2d/`.

`config3_ref800.cfg`:

```
mode = normal
test = lw_config3
nx = 800
ny = 800
xmin = 0.0
xmax = 1.0
ymin = 0.0
ymax = 1.0
gamma = 1.4
cfl = 0.5
t_end = 0.3
solver = hllc
bc = outflow
output_precision = 17
output_format = binary
output_file = experiments/week4/reference/hllc_800.bin
progress_interval_s = 30.0
```

`config3_ref800_rusanov.cfg`: identical except
`solver = rusanov` and `output_file = experiments/week4/reference/rusanov_800.bin`.

## 5. SLURM submission script on athena

`scripts/slurm/reference_800.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=ref800
#SBATCH --output=logs/ref800_%x_%j.out
#SBATCH --error=logs/ref800_%x_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16      # 16 OpenMP threads — see §7 scaling note
#SBATCH --mem=8G
#SBATCH --time=06:00:00         # hard cap per supervisor

set -euo pipefail

CFG=${1:?"usage: sbatch scripts/slurm/reference_800.sh <cfg>"}

module load gcc/11.3.0          # match the build env

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OPENBLAS_NUM_THREADS=1   # defensive: the solver itself does no BLAS;
                                # kept so future additions cannot silently oversubscribe

mkdir -p experiments/week4/reference logs

echo "host=$(hostname) cpus=${OMP_NUM_THREADS} cfg=${CFG} start=$(date -u +%FT%TZ)"
./build-ref/hrsc "${CFG}"
echo "finished exit=$? at $(date -u +%FT%TZ)"
```

Submit:

```bash
mkdir -p logs experiments/week4/reference
sbatch scripts/slurm/reference_800.sh tests/cases/liska_wendroff_2d/config3_ref800.cfg
sbatch scripts/slurm/reference_800.sh tests/cases/liska_wendroff_2d/config3_ref800_rusanov.cfg
```

## 6. Watching progress (answers the "is it stuck?" question)

SLURM writes stderr to `logs/ref800_<jobname>_<jobid>.err`. From any
athena login shell:

```bash
# Find the job
squeue -u $USER

# Follow the live progress stream
tail -F logs/ref800_*.err
```

You will see a `[progress:start]` line within seconds, then a
`[progress:tick]` every 30 s. If the rate (`rate=X steps/s`) holds
steady, the job is healthy; if it drops to 0 for more than two
intervals the solver has stalled and SLURM will kill it at 06:00:00
anyway.

Without SLURM (e.g., sanity runs on a login shell or lovelace):

```bash
nohup ./build-ref/hrsc tests/cases/liska_wendroff_2d/config3_ref800.cfg \
    > run.out 2> run.err &
tail -F run.err
```

## 7. Getting it under 6 h — what the speedups buy you

The per-sample wall-clock scales like `nx · ny · n_steps ≈ N³` in
2D (CFL-limited `dt ∝ dx = 1/N`). Using the feasibility log as the
anchor (200² native double ≈ 10 s on Windows MinGW single-core;
200² under Verificarlo ≈ 6 min on lovelace):

| Resolution | scale factor | single-core projection | 16-core OpenMP | 32-core OpenMP |
|------------|--------------|------------------------|----------------|----------------|
| 200²       | 1×           | 10 s native / 6 min under MCA | n/a            | n/a            |
| 400²       | 8×           | ~1.5 min native         | ~10 s           | ~6 s           |
| **800²**   | **64×**      | **~11 min native** / ~6.4 h under MCA | **~45 s**       | **~25 s**      |

So a plain IEEE-double 800² reference on athena with 16 OpenMP
threads should finish in well under 2 min, not 6 h. **If the run is
still close to the 6 h cap** the two levers are:

1. **Raise threads**: move from `--cpus-per-task=16` to `32`. The
   solver scales cleanly across row-major sweeps. 16 is a conservative
   default for a shared node; 32 is usually fine on an Icelake box.
2. **Check the build**: `cmake --build build-ref/ --target hrsc -v 2>&1 | grep -E '\-O|march'`
   should show `-O3 -march=native -fopenmp`. If `-fopenmp` is missing
   the OpenMP pragmas silently compiled as serial code — that alone
   would push 800² back to 11 min single-core, still under 6 h but
   wasteful.
3. **Avoid Verificarlo for this run.** Reference = deterministic IEEE
   double, not MCA. If you accidentally build with
   `CXX=verificarlo-c++` the 64× scale factor turns into the 6 h+
   territory.

Do **not** raise the CFL to go faster — the reference accuracy
depends on using the same CFL as the production runs.

## 8. After the runs finish

```bash
# Pull the binaries back to the local analyzer
rsync -av athena:floatpoint/experiments/week4/reference/ \
           experiments/week4/reference/

# Run s_req(N) using the freshly-minted references
python scripts/s_req_metric.py \
    --reference experiments/week4/reference/hllc_800.bin     \
    --samples   experiments/week4/2d_vfc_cluster/hllc/sample_??/grid.bin \
    --solver hllc --grid 200 \
    --out experiments/week4/s_req/hllc_200.csv

# (same with rusanov_800.bin against experiments/week4/2d_vfc_cluster/rusanov/…)
```

Success criteria for the reference runs:

- Both SLURM jobs exit 0 (`sacct -j <id> --format=JobID,State,Elapsed,ExitCode`).
- `grid.bin` size ≈ `64 + 800 * 800 * 4 * 8` bytes = 20 MB for
  4 conserved variables at double precision (check with `ls -l`).
- `[progress:done]` appears in the `.err` file with `t = 0.3`.

## 9. One-time local smoke before you submit

```bash
# On your laptop (Windows / WSL / MinGW — whatever you already use):
cmake --build build -j                                      # rebuild with new code
./build/hrsc.exe tests/cases/liska_wendroff_2d/config3.cfg  # 200², should finish in < 1 min
```

You should see the `[progress:*]` lines on stderr only if the cfg
sets `progress_interval_s > 0`; the existing 200² MCA cfgs do not set
it, so the MCA pipeline produces bit-identical output. Add
`progress_interval_s = 30.0` to any ad-hoc cfg you want to monitor.
