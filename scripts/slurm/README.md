# CSC cluster — Week 4 A3 2D Verificarlo production

This directory hosts SLURM array jobs for the 2D Liska-Wendroff MCA
production runs (plan §A3, stage 3). The script submits 30 concurrent
tasks per solver; per-task seed comes from `/dev/urandom` and is
inlined in `VFC_BACKENDS` (the env-var `VFC_BACKENDS_SEED` is silently
ignored by `interflop_mca`).

## One-time cluster setup

1. `ssh <csc-login>` and `cd` to your project root on the cluster.
2. Clone / rsync this repository (see `scripts/rsync_from_cluster.sh` for
   the inverse direction — result retrieval). A typical push from the
   local machine:
   ```bash
   rsync -az --exclude 'build*' --exclude 'experiments/' --exclude '.git/' \
       ./ <csc-login>:/path/to/floatpoint/
   ```
3. On the cluster, resolve Verificarlo. Either:
   - `module load verificarlo-2.4.0` (Week 3 supervisor email: the site
     installation is at `/lsc/opt/verificarlo-2.4.0`), **or**
   - Copy a Singularity image `verificarlo.sif` to the repo root
     (`singularity build verificarlo.sif docker://verificarlo/verificarlo`
     on a node with internet access, then scp).

   Verify with:
   ```bash
   which verificarlo-c++   # native module path
   # or
   ls -l verificarlo.sif   # singularity fallback
   ```
4. Sanity-build once on a login node (or interactive session) so the
   array tasks reuse `build-vfc-p53/`:
   ```bash
   CXX=verificarlo-c++ cmake -S . -B build-vfc-p53 \
       -DCMAKE_BUILD_TYPE=Release -DFLOAT_PRECISION=double
   cmake --build build-vfc-p53 -j
   ```

## Submitting production (stage 3 — 200² × N=30, HLLC and Rusanov)

```bash
mkdir -p logs
sbatch --array=1-30 scripts/slurm/verificarlo_2d_array.sh \
    tests/cases/liska_wendroff_2d/config3.cfg          hllc
sbatch --array=1-30 scripts/slurm/verificarlo_2d_array.sh \
    tests/cases/liska_wendroff_2d/config3_rusanov.cfg  rusanov
```

Both submissions run independently; SLURM schedules tasks concurrently.
Wall-clock for the whole batch ≈ per-task wall-clock (not 30× per-task).

## Monitoring

```bash
squeue -u $USER                      # queued + running tasks
sacct -j <jobid> --format=JobID,State,ExitCode,Elapsed,MaxRSS
# Per-task logs:
tail -f logs/vfc2d_<jobid>_<taskid>.out
```

Write the full `sacct` report to the experiments tree for later audit:
```bash
sacct -j <jobid_hllc> -j <jobid_rusanov> \
    --format=JobID,State,ExitCode,Elapsed,MaxRSS,NodeList \
    > experiments/week4/2d_vfc_cluster/sacct_report.txt
```

## Expected output layout (per submission)

```
experiments/week4/2d_vfc_cluster/
├── hllc/
│   ├── sample_01/{run.cfg,grid.bin}
│   ├── sample_02/{run.cfg,grid.bin}
│   ├── ... (30 samples)
│   └── seeds/seed_01.csv … seed_30.csv
├── rusanov/
│   ├── sample_01/{run.cfg,grid.bin}
│   ├── ... (30 samples)
│   └── seeds/seed_01.csv … seed_30.csv
└── sacct_report.txt
```

Per-task seed files are **not** shared — flock semantics on Lustre /
GPFS / NFS are not portable, so each task owns its own seed_NN.csv.
The analyzer concatenates via glob at read time.

## Retrieving results locally

From the local machine (repo root):
```bash
bash scripts/rsync_from_cluster.sh <csc-login>:/path/to/floatpoint
```

## Notes on array concurrency

`#SBATCH --time=12:00:00` is the **per-task** cap, not the batch. N=30
tasks typically start within seconds on CSC for 1-cpu jobs; the batch
finishes in ≈ `t_single + queue_latency`. Fair-share priority and
node-hour quota are the real limits, not the 12 h wall-clock ceiling.

## Seed independence verification

After retrieval, the 2D analyzer asserts:
```python
df = load_seeds(Path("experiments/week4/2d_vfc_cluster/hllc/seeds"))
assert len(df) == 30 and df["seed_hex"].nunique() == 30
```
64-bit entropy: N²/2⁶⁵ birthday-collision bound ≤ 2.4e-17. Any duplicate
is a `/dev/urandom` failure — re-run the affected sample.
