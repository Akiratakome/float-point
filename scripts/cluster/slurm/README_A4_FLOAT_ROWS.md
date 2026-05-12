# A4 Float Rows on CSC Athena

This guide generates the missing A4 `p24-real-float` rows for the LW Config 3
trade-off table. The rows must come from a real-float MCA ensemble; a single
deterministic `float_200.bin` is not enough because A4 needs `sigma_FP` and
LoSoS statistics over samples.

Use **Athena** for the production run because it has SLURM. `lovelace` has the
same CSC Verificarlo install but no SLURM, so it is suitable for manual
single-node work only.

## 1. Get The Current Code On Athena

From your local machine, after pushing this branch:

```bash
ssh <athena-login>
cd ~/floatpoint
git fetch origin
git checkout week4-implementation
git pull --ff-only origin week4-implementation
```

If the repo is not already cloned on Athena:

```bash
git clone <repo-url> ~/floatpoint
cd ~/floatpoint
git checkout week4-implementation
```

## 2. Verify Verificarlo And Compiler

CSC installation:

```bash
export VFC_ROOT=/lsc/opt/verificarlo-2.4.0
export PATH="$VFC_ROOT/bin:$PATH"
export LD_LIBRARY_PATH="$VFC_ROOT/lib:${LD_LIBRARY_PATH:-}"

which verificarlo-c++
test -x /usr/bin/clang++ && /usr/bin/clang++ --version | head -1
```

Expected:

- `verificarlo-c++` resolves under `/lsc/opt/verificarlo-2.4.0/bin`
- `/usr/bin/clang++` exists and reports clang++ 18

## 3. Prebuild The Real-Float Verificarlo Binary

Build once before submitting the array. The array script intentionally refuses
to build inside every task, because concurrent CMake builds in one directory can
race on shared filesystems.

```bash
CXX=/lsc/opt/verificarlo-2.4.0/bin/verificarlo-c++ cmake -S . -B build-vfc-real-float-p24 \
  -DCMAKE_BUILD_TYPE=Release \
  -DFLOAT_PRECISION=float \
  -DENABLE_OPENMP=OFF

cmake --build build-vfc-real-float-p24 -j
```

Smoke test one native binary32 MCA sample:

```bash
export OMP_NUM_THREADS=1
export VFC_BACKENDS="libinterflop_mca.so --mode=mca --precision-binary32=24 --seed=12345"
./build-vfc-real-float-p24/hrsc tests/cases/liska_wendroff_2d/config3_n200.cfg >/tmp/a4_float_smoke.txt
tail -1 /tmp/a4_float_smoke.txt
```

The final line should contain `Finished: ... t = 0.3` on stderr if you do not
redirect stderr. If the command fails, do not submit the array.

## 4. Submit Athena SLURM Arrays

Run 30 samples for each solver:

```bash
mkdir -p logs

sbatch --array=1-30 scripts/cluster/slurm/verificarlo_2d_float_array.sh \
  tests/cases/liska_wendroff_2d/config3.cfg hllc \
  experiments/week4/2d_vfc_float_p24

sbatch --array=1-30 scripts/cluster/slurm/verificarlo_2d_float_array.sh \
  tests/cases/liska_wendroff_2d/config3_rusanov.cfg rusanov \
  experiments/week4/2d_vfc_float_p24
```

Monitor:

```bash
squeue -u "$USER"
sacct -j <hllc_jobid> --format=JobID,State,ExitCode,Elapsed,MaxRSS,NodeList
sacct -j <rusanov_jobid> --format=JobID,State,ExitCode,Elapsed,MaxRSS,NodeList
```

Save accounting:

```bash
sacct -j <hllc_jobid>,<rusanov_jobid> \
  --format=JobID,State,ExitCode,Elapsed,MaxRSS,NodeList \
  > experiments/week4/2d_vfc_float_p24/sacct_report.txt
```

Expected output:

```text
experiments/week4/2d_vfc_float_p24/
  hllc/sample_01/grid.bin ... sample_30/grid.bin
  hllc/seeds/seed_01.csv ... seed_30.csv
  rusanov/sample_01/grid.bin ... sample_30/grid.bin
  rusanov/seeds/seed_01.csv ... seed_30.csv
  sacct_report.txt
```

## 5. Copy Results Back

From the local repository root:

```bash
rsync -az <athena-login>:~/floatpoint/experiments/week4/2d_vfc_float_p24/ \
  experiments/week4/2d_vfc_float_p24/
```

Do not commit `sample_*/grid.bin`; these are transient experiment grids.

## 6. Generate A4 Metrics Locally

The p53 reference file already exists at
`experiments/week4/metrics/u_ref_200_blockavg.npz`.

First make sure the p53 metrics CSVs exist. If `experiments/week4/2d_vfc_cluster`
contains the p53 HLLC/Rusanov sample grids, regenerate them:

```bash
python scripts/metrics/snr_metric.py \
  --root experiments/week4/2d_vfc_cluster \
  --expected-n 30 \
  --reference experiments/week4/metrics/u_ref_200_blockavg.npz \
  --precision-label p53 \
  --out-dir experiments/week4/metrics/a4_p53

python scripts/metrics/losos_metric.py \
  --root experiments/week4/2d_vfc_cluster \
  --expected-n 30 \
  --reference experiments/week4/metrics/u_ref_200_blockavg.npz \
  --precision-label p53 \
  --out-dir experiments/week4/metrics/a4_p53
```

If the p53 sample grids are not present locally, retrieve or rerun the Week-4
A3 p53 ensemble first. The checked-in p53 headline table is not enough to
regenerate a four-row table because the table generator joins full SNR and
LoSoS CSV inputs.

Then generate p24-real-float metrics:

```bash
python scripts/metrics/snr_metric.py \
  --root experiments/week4/2d_vfc_float_p24 \
  --expected-n 30 \
  --reference experiments/week4/metrics/u_ref_200_blockavg.npz \
  --precision-label p24-real-float \
  --out-dir experiments/week4/metrics/a4_float_p24

python scripts/metrics/losos_metric.py \
  --root experiments/week4/2d_vfc_float_p24 \
  --expected-n 30 \
  --reference experiments/week4/metrics/u_ref_200_blockavg.npz \
  --precision-label p24-real-float \
  --out-dir experiments/week4/metrics/a4_float_p24
```

Merge p53 and p24 CSV rows:

```bash
python - <<'PY'
from pathlib import Path

def merge(header_path, extra_path, out_path):
    h = Path(header_path).read_text(encoding="utf-8").splitlines()
    e = Path(extra_path).read_text(encoding="utf-8").splitlines()
    Path(out_path).write_text("\n".join(h + e[1:]) + "\n", encoding="utf-8")

merge("experiments/week4/metrics/a4_p53/snr_scalars.csv",
      "experiments/week4/metrics/a4_float_p24/snr_scalars.csv",
      "experiments/week4/metrics/a4_snr_with_float.csv")
merge("experiments/week4/metrics/a4_p53/losos_scalars.csv",
      "experiments/week4/metrics/a4_float_p24/losos_scalars.csv",
      "experiments/week4/metrics/a4_losos_with_float.csv")
PY
```

Regenerate the headline table:

```bash
python scripts/figures/tradeoff_summary_table.py \
  --snr-csv experiments/week4/metrics/a4_snr_with_float.csv \
  --losos-csv experiments/week4/metrics/a4_losos_with_float.csv \
  --s-req-csv experiments/week4/metrics/s_req_lw_config3_200.csv \
  --N 200 \
  --out docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md
```

## 7. How To Read The Outputs

`sigma_fp_heatmap.png`:

- Bright/hot regions are cells where random round-off perturbations are large.
- Compare HLLC vs Rusanov at the same color scale: lower `sigma_FP` means the
  solver is more reproducible under the same virtual precision.
- For p24-real-float, expect higher `sigma_FP` than p53. That is not a failure;
  it is the signal being measured.

`snr_local_heatmap.png`:

- Local SNR is `|mu_trunc| / sigma_FP`.
- White contour `SNR=1`: FP noise is as large as truncation bias.
- Yellow contour `SNR=10`: truncation bias is one order of magnitude larger
  than FP noise.
- Regions below `SNR=1` are round-off-sensitive at this resolution/precision.

LoSoS heatmaps:

- `s_reliability`: how tightly the MCA samples cluster.
- `s_accuracy`: how close the ensemble mean is to the current block-averaged
  high-resolution reference.
- `s_worst = min(s_reliability, s_accuracy)`: the significant digits you can
  actually trust. This is the field used in the headline table via q05.

Headline table:

- `mu_trunc_L1`: physical discretisation error against the current
  block-averaged high-resolution reference.
- `sigma_FP_L1`: accumulated FP noise across the MCA ensemble.
- `s_worst_q05`: trustworthy significant digits in the worst 5% of cells.
- `s_req(N)`: significant digits required to match truncation error at N=200².
- `s_worst - s_req`: the gate value.
- `round-off-limited`: current precision is below the truncation target.
- `marginal`: barely enough precision.
- `well-matched`: about the right precision for this grid.
- `over-provisioned`: more FP precision than the grid can use.

## 8. Expected Conclusion Pattern

If p24-real-float rows have much lower `s_worst_q05` than p53 and more negative
`s_worst - s_req`, the conclusion is:

> Native float is not sufficient for the worst cells of LW Config 3 at 200²
> under this metric; p53 already sits below the truncation-anchored target, so
> float is expected to be more round-off-limited.

If Rusanov has lower `sigma_FP_L1` but higher `mu_trunc_L1`, the conclusion is:

> Rusanov buys FP robustness through extra numerical diffusion. The Pareto
> trade-off is not “better solver” but “less FP noise at the cost of larger
> truncation error.”
