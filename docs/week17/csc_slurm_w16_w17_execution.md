# CSC Slurm Execution: W16/W17 KH MCA Completion

This guide stages and runs the Week 16/17 Report 2 completion work on CSC with
Slurm and Apptainer. The goal is to produce remote evidence for the Kelvin-
Helmholtz MCA gap while preserving the existing claim boundary until the full
run completes.

## Scope

Run only the W16/W17 package:

- W16 reduced KH MCA smoke: `64^2`, `t=0.05`, HLL/HLLD, p53+p24, N=30.
- W16 full 256^2/t=1.0 KH MCA: HLL/HLLD, p53+p24, N=30.
- W16 KH deterministic packet regeneration from the full MCA summary.
- W17 synthesis and paper figures after summaries are available.

The reduced smoke supports the Apptainer/Verificarlo toolchain and p24-vs-p53
noise-floor direction only. It does not promote the full KH MCA claim. The full
MCA job must complete before any full 256^2/t=1.0 KH MCA conclusion is used.

The package also contains the Week 18 robustness completion jobs:

- five-repeat CPU/GPU timing with same-precision ULP checks;
- 2D OpenMP reproducibility at 1, 2, 4, and 8 threads;
- Kelvin-Helmholtz CFL sensitivity at 0.2, 0.4, 0.6, and 0.8.

## Local Staging

From the workstation repo root:

```bash
export CSC_TARGET="user@csc:/scratch/project/floatpoint"
bash scripts/cluster/report2_w16_w17_slurm/sync_to_csc.sh
```

The sync excludes build directories and transient `grid.bin` files. It keeps
the repository metadata so remote summaries can record the source commit. The
helper is a narrow `rsync` wrapper for this W16/W17 package.

If `rsync` is unavailable on the workstation, use the tar/ssh fallback:

```bash
export CSC_TARGET="user@csc:/scratch/project/floatpoint"
bash scripts/cluster/report2_w16_w17_slurm/sync_to_csc_tar.sh
```

If the CSC host is not reachable from the workstation network, create an
offline bundle and upload it later from a machine that can reach CSC:

```bash
bash scripts/cluster/report2_w16_w17_slurm/make_bundle.sh
scp artifacts/report2_w16_w17_csc_bundle.tar.gz user@csc:/scratch/project/
ssh user@csc 'mkdir -p /scratch/project/floatpoint && tar -xzf /scratch/project/report2_w16_w17_csc_bundle.tar.gz -C /scratch/project/floatpoint'
```

## Remote Setup

Log in to CSC and enter the staged repository:

```bash
ssh user@csc
cd /scratch/project/floatpoint
```

Prepare a Verificarlo image visible to compute nodes:

```bash
module load apptainer
apptainer pull verificarlo-cmake.sif oras://registry.example.invalid/verificarlo-cmake:replace-me
```

If CSC cannot pull the image directly, create `verificarlo-cmake.sif` elsewhere
and copy it to the repo root or a shared scratch path. Then set:

```bash
export HRSC_VFC_IMAGE="$PWD/verificarlo-cmake.sif"
export HRSC_PYTHON=python3
export HRSC_MCA_JOBS=32
```

Check the image:

```bash
apptainer exec --bind "$PWD:/workdir" --pwd /workdir "$HRSC_VFC_IMAGE" \
  bash -lc 'verificarlo-c++ --version && cmake --version'
```

## Submit Jobs

Fast environment validation:

```bash
bash scripts/cluster/report2_w16_w17_slurm/submit_w16_w17.sh smoke
```

Full W16/W17 chain:

```bash
bash scripts/cluster/report2_w16_w17_slurm/submit_w16_w17.sh full
```

Week 18 robustness plus the full KH MCA gap:

```bash
export HRSC_TIMING_REPEATS=5
bash scripts/cluster/report2_w16_w17_slurm/submit_week18.sh
```

This submits independent GPU and CPU robustness jobs and the existing full KH
MCA array. The GPU job builds the float and double CUDA HLL binaries on its
assigned node. The CPU job builds OpenMP float and double binaries before
running the thread and CFL suites.

This submits:

1. `run_kh_full_mca.slurm`: array job for HLL and HLLD full KH MCA.
2. `run_kh_packets_from_mca.slurm`: runs after the full MCA array succeeds.
3. `run_w17_synthesis_and_figures.slurm`: runs after packet regeneration.

Override Slurm account/partition at submission if needed:

```bash
sbatch -A account_name -p partition_name scripts/cluster/report2_w16_w17_slurm/run_kh_full_mca.slurm
```

## Expected Outputs

Remote W16 MCA outputs:

- `experiments/week16/kelvin_helmholtz_precision/csc_mca/hll/summary.json`
- `experiments/week16/kelvin_helmholtz_precision/csc_mca/hlld/summary.json`
- `experiments/week16/kelvin_helmholtz_precision/csc_packets/hll_p1/summary.json`
- `experiments/week16/kelvin_helmholtz_precision/csc_packets/hlld_p1/summary.json`

Remote W17 outputs:

- `experiments/week17/report2_synthesis/summary.json`
- `experiments/week17/report2_synthesis/summary.md`
- `experiments/week17/paper_figures/manifest.json`
- `experiments/week17/paper_figures/*.png`

Remote Week 18 outputs:

- `experiments/week18/supplemental/hardware_repeats/summary.json`
- `experiments/week18/supplemental/thread_repro/summary.json`
- `experiments/week18/supplemental/kh_cfl/summary.json`
- `experiments/week18/supplemental/*/figures/*.png`

The `csc_*` paths intentionally avoid overwriting the local W16 authority.
After reviewing the full MCA summaries, promote selected files explicitly.

## Retrieve Results

From the workstation repo root:

```bash
export CSC_TARGET="user@csc:/scratch/project/floatpoint"
bash scripts/cluster/report2_w16_w17_slurm/sync_results_from_csc.sh
```

This retrieves summaries, environment records, Slurm logs, and figures while
excluding transient grids.

## Validation Checklist

On CSC:

```bash
python3 -m pytest tests/py/test_mhd_verificarlo_smoke.py \
  tests/py/test_mhd_precision_sampling.py \
  tests/py/test_mhd_kh_precision.py \
  tests/py/test_report2_synthesis.py -q
```

On the workstation after retrieving results:

```bash
python -m pytest tests/py/test_mhd_verificarlo_smoke.py \
  tests/py/test_report2_csc_slurm_package.py \
  tests/py/test_mhd_kh_precision.py \
  tests/py/test_report2_synthesis.py -q
```

Before a paper claim:

- Both full MCA summaries must have `mca.p53.status == completed`.
- Both full MCA summaries must have `mca.p24.status == completed`.
- The packet summaries generated from those MCA summaries must have
  `gates.mca.pass == true`.
- If any full MCA block is missing or incomplete, keep the full KH MCA
  no-claim boundary and use only the reduced smoke as toolchain support.
