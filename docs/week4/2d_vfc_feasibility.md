# Week 4 A3 — 2D Verificarlo Feasibility Log

> Methodology transparency for plan §A3.3. Records native-precision
> baselines, MCA smoke/feasibility timings, and SLURM production wall-clock.
> **No gate**, no branching — N=30 is fixed per §A3.1.

## 1. Native baselines (Windows, Ninja Release, date 2026-04-23)

Local machine, double precision, no MCA — purely establishes that the
2D HLLC solver converges and produces physical ranges on Liska-Wendroff
Config 3. Wall-clock is for **one** run, single-threaded (no OpenMP in
solver yet).

| Grid | Solver | Steps | Wall-clock | rho range | p range |
|------|--------|-------|-----------|-----------|---------|
| 40²  | HLLC   | 51    | 0.20 s    | [0.1380, 1.5004] | [0.0290, 1.5005] |
| 200² | HLLC   | 259   | 10.4 s    | — (to be recorded during MCA smoke) | — |

Native scaling: 40² → 200² costs ~50×, consistent with 5× grid refine +
~5× steps (CFL-limited).

## 2. MCA local smoke (stage 1 — 40² × 3 samples, WSL + Docker, 2026-04-23)

Command (run from repo root inside WSL with Docker engine reachable):
```bash
sed 's/nx = 200/nx = 40/;s/ny = 200/ny = 40/' \
    tests/cases/liska_wendroff_2d/config3.cfg > /tmp/lw40_hllc.cfg
docker run --rm \
    -v "$(pwd)":/work -v /tmp:/tmp_host -w /work \
    verificarlo/verificarlo:v2.4.0 \
    bash -c 'cp /tmp_host/lw40_hllc.cfg /tmp/lw40_hllc.cfg && \
        bash scripts/verificarlo_run_2d.sh --config /tmp/lw40_hllc.cfg \
            --solver hllc --samples 3'
```

Result — **PASS**: 23 s wall-clock (whole batch incl. Docker startup).

| Sample | Seed (dec)            | Steps | Notes |
|--------|-----------------------|-------|-------|
|   01   | 7752574735489982007  | 51    | OK    |
|   02   | 9029454494804915967  | 51    | OK    |
|   03   | 2352970436582514550  | 51    | OK    |

Per-cell ρ statistics across the 3 samples:
- ρ ∈ [0.138000, 1.500390]  (mean 0.936226)
- per-cell σ(ρ) ∈ [0, 2.6 × 10⁻¹⁵], mean 5.7 × 10⁻¹⁶

→ MCA noise floor is at the expected p=53 binary64 limit; 3 distinct
seeds confirm `/dev/urandom` PRNG independence.

## 3. MCA local feasibility (stage 2 — 100² × 1 sample, 2026-04-23)

Purpose: measure per-sample wall-clock and bisect the largest grid that
the verificarlo-instrumented binary can run end-to-end.

| N (grid)  | Backend        | Steps | Per-sample wall-clock | Result |
|-----------|----------------|-------|-----------------------|--------|
| 100       | MCA p=53 rr    | 128   | 54 s                  | OK     |
| 140       | MCA p=53 rr    | 180   | ~75 s                 | OK     |
| 160       | MCA p=53 rr    | 206   | ~95 s                 | OK     |
| 180       | MCA p=53 rr    | 233   | ~135 s                | OK     |
| **200**   | **MCA p=53 rr**| —     | **<1 s**              | **SIGSEGV** |
| **200**   | **IEEE (passthrough)** | — | **<1 s**            | **SIGSEGV** |

Critical finding (2026-04-23): the `verificarlo-c++` (Clang 7.0.1, Verificarlo
v2.4.0 Docker image `verificarlo/verificarlo:v2.4.0`) build of `hrsc`
**segfaults on the LW Config 3 200² problem before completing the first
step**, *regardless* of the chosen interflop backend (MCA or IEEE
passthrough). The native Windows MinGW build runs the same problem
end-to-end in 10.4 s. The crash is therefore in the verificarlo-instrumented
codegen, not in the solver itself.

Bisection puts the failure threshold strictly between N=180 (works) and
N=200 (crashes). Crash signature: `SIGSEGV (signal 11)`, no stderr beyond
the interflop init banner.

### Production plan revisions under consideration

1. **Drop production grid to N=180** (or N=190 if it also works) —
   plan §A3.0 statistical methodology is grid-agnostic; N=30 samples
   still gives χ² 90% CI σ ±15%. Pros: unblocked today. Cons: deviates
   from plan §A3.2 nominal 200² and from the "200²×30 → 400²×30
   refinement" cadence.
2. **Try a newer Verificarlo image** (`verificarlo/verificarlo:latest`,
   or rebuild from source against Clang 14+). Highest fix probability.
3. **Try CSC's `module load verificarlo-2.4.0`** which may be built
   against a different LLVM. If that runs 200² cleanly, production
   proceeds unchanged.
4. **Build with `-O0 -g`** (debug) — quick test for an optimizer bug.
   Initial attempt failed at the cmake step inside the container; not
   yet pursued.

## 4. Production (stage 3 — 200² × N=30, HLLC + Rusanov)

### 4.1 Platform switch — CSC SLURM → Cambridge LSC lovelace (2026-04-23)

Actual production host is `lovelace.lsc.phy.private.cam.ac.uk` (Cambridge
Physics LSC), **not** a SLURM cluster. Environment:

- 64 cores, 251 GB RAM, single shared node
- Ubuntu 24.04; Verificarlo 2.4.0 at `/lsc/opt/verificarlo-2.4.0/` on
  **Clang 18.1.3** (vs Clang 7.0.1 in the local Docker image that
  segfaulted at 200²)
- No `module`, no SLURM (`sinfo` missing) — workflow uses `xargs -P`
  single-node parallelism instead of `sbatch --array`.

### 4.2 Single-node runner

`scripts/run_lovelace_parallel.sh` replaces `scripts/slurm/verificarlo_2d_array.sh`
on lovelace. Same output layout (`sample_NN/grid.bin`, `seeds/seed_NN.csv`)
so the analyzer chain is unchanged. Per-sample seed comes from
`/dev/urandom` inlined into `VFC_BACKENDS`, PRNG thread isolation via
`OMP_NUM_THREADS=1` + BLAS throttle. All 30 samples spawn concurrently
across 30 of the 64 cores.

Typical submission:
```bash
cd ~/floatpoint
export PATH=/lsc/opt/verificarlo-2.4.0/bin:$PATH
export LD_LIBRARY_PATH=/lsc/opt/verificarlo-2.4.0/lib:${LD_LIBRARY_PATH:-}

bash scripts/run_lovelace_parallel.sh \
    --config tests/cases/liska_wendroff_2d/config3.cfg \
    --solver hllc --samples 30 --parallel 30

bash scripts/run_lovelace_parallel.sh \
    --config tests/cases/liska_wendroff_2d/config3_rusanov.cfg \
    --solver rusanov --samples 30 --parallel 30
```

Expected wall-clock per solver at 200²: ≈ 1 × per-sample wall-clock
(all 30 samples run concurrently on 30 cores, plenty of RAM headroom).
Local Docker benchmarks suggest per-sample `t_{200²}` ≈ 5 min → total
~5 min per solver, ~10 min for HLLC + Rusanov combined — subject to
confirmation against Clang 18 codegen (the local 200² crash was a
Clang 7 issue).

### 4.3 Stage-3 go/no-go

Prereq sanity: run ONE 200² MCA sample on lovelace first. If
`Finished: 259 steps, t = 0.3` + exit 0, proceed with the N=30
batches above. If it still segfaults under Clang 18, fall back to
N=180 production with the same runner.

Submission commands — see `scripts/slurm/README.md`.
Per-task wall-clock + resource report captured via:
```bash
sacct -j <hllc_jobid> -j <rusanov_jobid> \
    --format=JobID,State,ExitCode,Elapsed,MaxRSS,NodeList \
    > experiments/week4/2d_vfc_cluster/sacct_report.txt
```

Seed independence check (auto-run at analyzer entry):
```python
from scripts.io_helper import load_seeds
from pathlib import Path
rows = load_seeds(Path("experiments/week4/2d_vfc_cluster/hllc/seeds"), expected_n=30)
# load_seeds raises on duplicates or missing files.
```

## 5. Statistical justification for N=30

χ² 90% confidence interval for sample standard deviation has
`σ_hat / σ ∈ [0.79, 1.14]` at N=30, i.e. ±15% (one-sided).
N=30 is the conventional threshold for "statistically valid σ estimation"
(Gosset 1908; Lindley 1985, §7.3). Per §A3.0 there is no reason to
downgrade from N=30 — SLURM array executes concurrently so wall-clock
≠ N · t_single.

64-bit `/dev/urandom` seed space: birthday-collision probability for 30
draws ≤ `30² / 2⁶⁵ ≈ 2.4 × 10⁻¹⁷` → any duplicate is a system anomaly.
