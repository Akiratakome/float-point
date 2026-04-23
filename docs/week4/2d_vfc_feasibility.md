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

## 2. MCA local smoke (stage 1 — 40² × 3 samples, WSL + Docker)

_Pending — scheduled when WSL + Docker Verificarlo is available._

Command (run from repo root inside WSL):
```bash
bash scripts/verificarlo_run_2d.sh \
    --solver hllc --samples 3 \
    --out experiments/week4/2d_vfc/smoke/lw_config3/hllc
```

Verification:
- `experiments/.../sample_01/grid.bin` parses via `scripts/io_helper.py`.
- `experiments/.../seeds/seed_01.csv` … `seed_03.csv` present, all seeds distinct.
- Per-sample wall-clock logged below.

| Sample | Seed (dec) | Wall-clock | Notes |
|--------|------------|-----------|-------|
|   01   |  —         |    —      | to be filled |
|   02   |  —         |    —      | to be filled |
|   03   |  —         |    —      | to be filled |

## 3. MCA local feasibility (stage 2 — 100² × 5 samples)

_Pending._

Purpose: measure `t_{100²}` per-sample. Extrapolate
`t_{200²} ≈ 4 · t_{100²} · 1.3` (1.3 = analyzer / IO overhead coefficient).
Verify `t_{200²} ≤ 12 h` per-task (§A3.0 `--time` cap).

Command:
```bash
# Temporary cfg overriding nx=ny=100
sed 's/nx = 200/nx = 100/;s/ny = 200/ny = 100/' \
    tests/cases/liska_wendroff_2d/config3.cfg > /tmp/lw100_hllc.cfg
bash scripts/verificarlo_run_2d.sh \
    --config /tmp/lw100_hllc.cfg --solver hllc --samples 5 \
    --out experiments/week4/2d_vfc/feasibility/lw_config3/hllc
```

| Sample | Seed (dec) | Wall-clock | Notes |
|--------|------------|-----------|-------|
|   01   |  —         |    —      | to be filled |
|   02   |  —         |    —      | to be filled |
|   03   |  —         |    —      | to be filled |
|   04   |  —         |    —      | to be filled |
|   05   |  —         |    —      | to be filled |

Extrapolation:
- `t_{100²}_mean` = _tbd_
- `t_{200²}_est` = `4 × t_{100²}_mean × 1.3` = _tbd_
- Decision: `t_{200²}_est ≤ 12 h` → **proceed to stage 3**; else stop + replan.

## 4. CSC production (stage 3 — 200² × N=30, HLLC + Rusanov)

_To be submitted after feasibility gate._

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
