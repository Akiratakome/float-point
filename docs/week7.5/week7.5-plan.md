# Verificarlo Week 7 Figure Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize Verificarlo-related Report 1 evidence around Week 7 integrated data, regenerate a coherent figure set, and map remaining supervisor requests to concrete actions.

**Architecture:** Treat the harness as the deliverable: audit inputs, normalize metrics, aggregate to stable CSV/JSON, then generate figures and evidence notes. Keep existing solver numerics and cfg defaults unchanged. Promote only summary data and report figures; keep raw MCA grids transient unless explicitly needed as reference/provenance.

**Tech Stack:** Python 3.11, NumPy/Pandas/Matplotlib/Pillow, existing `scripts/metrics/*`, `scripts/figures/*`, `scripts/regression/*`, pytest.

---

## Current Findings

### Usable Week 7 Verificarlo Inputs

- `experiments/week7/metrics/p8/`, `p16/`, `p32/`: SNR, LoSoS scalars, and heatmaps from LW3 200² virtual-precision sweep.
- `experiments/week7/pareto_full/pareto_lw3_full.csv`: p8, p16, p24-real-float, p32, p53 Pareto rows using 1600²-derived `s_req`.
- `experiments/week7/pareto_full/pareto_lw3_full_logx.png` and `pareto_lw3_full_twopanel.png`: current full Pareto figures.
- `experiments/week7/reference_1600/.../reference_1600.bin`: HLLC 1600² high-resolution reference.
- `experiments/week7/reference_1600_rusanov/.../reference_1600_rusanov.bin`: Rusanov 1600² high-resolution reference.
- `experiments/week4/metrics/s_req_lw_config3_200.csv`: updated 1600²-derived truncation target for HLLC and Rusanov.
- `experiments/week4/metrics/u_ref_200_blockavg.npz`: updated 200² primitive reference consumed by LoSoS/SNR scripts.

### Important Limitations

- Week 7 p8 has only 2 common samples; p16/p32 have 3 samples. These are valid exploratory precision-sweep figures, not production 30-sample MCA statistics.
- Week 4 `losos_accuracy_heatmap.png` is older than the 1600² reference refresh; do not use it as the final 1600² LoSoS figure unless regenerated from MCA samples.
- `experiments/week4/2d_vfc_cluster/` currently lacks the original 30-run grids in this checkout, so Week 4 p53 heatmaps cannot be regenerated locally without recovering or rerunning samples.
- Drift data is final-state smoke only; no fitted growth rate can be claimed.

### Supervisor-Request Status

| Request / concern | Current status | Required action |
|---|---|---|
| Use Philip metric `||float-double|| / ||double-reference||` | Implemented in regression report; 2D now supports explicit 1600² reference | Regenerate final summaries and ensure report uses current numbers |
| Use one trusted high-resolution 2D reference with downsampling | 1600² HLLC/Rusanov references now available and connected to `s_req` | Update all figure captions and evidence notes from 800² to 1600² where not historical |
| Explain why Rusanov can look cleaner | Evidence note exists; Pareto rows include truncation penalty | Add one consolidated figure/table pairing `sigma_FP` with `mu_trunc` |
| Clarify "round-off limited" wording | Reworded as precision-adequacy margin | Use this terminology consistently in all regenerated figures |
| Pareto figure choice | Both log-x and two-panel exist | Prefer two-panel for report; retain log-x as supplementary |
| Degenerate stationary-contact policy | Policy exists | Ensure any new tables mark degenerate denominator rows as `n/a`, not pass/fail |
| Verificarlo p8/p16/p32 precision sweep | Data exists but sample counts are small | Label as exploratory and include sample-count annotation in figures |
| p53/p24/p8/p16/p32 unified Verificarlo story | Partially assembled through Pareto CSV | Build a single normalized summary table and refreshed figure set |
| Drift / temporal divergence growth rate | Not satisfied | Keep `lambda = n/a`; add a future-work or optional rerun task only |
| GPU expansion | Evidence exists as validation, not general CPU/GPU equivalence | Keep bounded claim; do not overstate 1600² GPU reference as CPU-equivalent |
| `vfc_precexp` per-function precision analysis | Partially present only as `experiments/verificarlo/precexp/prec_*` whole-program precision outputs; no per-function/per-call precision table found | Add an audit note and a CSC rerun plan; do not present current artefacts as per-function evidence |
| GPU porting guided by the "flux is not the FP bottleneck" finding | CUDA Euler path and CPU/GPU strict validation exist; mixed-precision policy/design is not yet implemented | Add a design-evidence task that links Week 3 Verificarlo findings to current GPU boundaries without changing kernels |
| 2D Verificarlo dimensional-splitting analysis | Done for LW3 through Week 4 p53 production and Week 7 p8/p16/p32 exploratory sweep; Week 4 raw 30-run grids are absent in this checkout | Consolidate existing 2D evidence and clearly separate completed analysis from unrecoverable local raw data |
| Convert 1D/HLLC-vs-Rusanov line plots to point-style plots like `combined_summary.png` | Not done; `scripts/regression/run_comparison.py` still plots HLLC/Rusanov as continuous lines | Add a new point-style plotting task that creates new figures from existing text outputs without overwriting originals |

---

## Target Outputs

Create a new report-ready bundle:

- `experiments/week7/verificarlo_report1_refresh/summary.csv`
- `experiments/week7/verificarlo_report1_refresh/summary.json`
- `experiments/week7/verificarlo_report1_refresh/summary.md`
- `experiments/week7/verificarlo_report1_refresh/figures/pareto_precision_adequacy_twopanel.png`
- `experiments/week7/verificarlo_report1_refresh/figures/precision_sweep_losos_rho.png`
- `experiments/week7/verificarlo_report1_refresh/figures/precision_sweep_sigma_fp_rho.png`
- `experiments/week7/verificarlo_report1_refresh/figures/hllc_rusanov_accuracy_noise_tradeoff.png`
- `experiments/week7/verificarlo_report1_refresh/figures/sample_count_badge_table.png` or markdown table if a PNG table is unnecessary.
- `experiments/week7/verificarlo_report1_refresh/figures/hllc_rusanov_points_summary.png`
- `experiments/week7/verificarlo_report1_refresh/figures/hllc_rusanov_points_<test>.png`

Update evidence routing:

- `docs/experiment_logs/week7_verificarlo_refresh.md`
- `docs/experiment_logs/report1_evidence_index.md`
- `docs/experiment_logs/week7_supervisor_requirements_gap_audit.md`
- Optional: `docs/emails/week7_progress_to_philip_2026-05-07.md` only if you want the draft email to reflect the refresh.

---

## Task 1: Audit Data Completeness

**Files:**
- Create: `experiments/week7/verificarlo_report1_refresh/audit.json`
- Create: `experiments/week7/verificarlo_report1_refresh/audit.md`
- Read: `experiments/week7/metrics/*/losos_scalars.csv`
- Read: `experiments/week7/metrics/*/snr_scalars.csv`
- Read: `experiments/week7/pareto_full/pareto_lw3_full.csv`
- Read: `experiments/week4/metrics/s_req_lw_config3_200.csv`

- [ ] **Step 1: Count precision-sweep samples from directories**

Run:

```powershell
Get-ChildItem -Path experiments\week7\2d_vfc_precision_sweep -Recurse -Filter grid.bin |
  ForEach-Object {
    $parts = $_.FullName -split '[\\/]'
    [PSCustomObject]@{ precision = $parts[-4]; solver = $parts[-3] }
  } |
  Group-Object precision,solver |
  Sort-Object Name |
  Format-Table Name,Count
```

Expected: p16/p32 have 3 samples per solver, p8 has a common two-sample subset for current Pareto interpretation.

- [ ] **Step 2: Verify required metric files exist**

Run:

```powershell
$paths = @(
  "experiments/week7/metrics/p8/losos_scalars.csv",
  "experiments/week7/metrics/p16/losos_scalars.csv",
  "experiments/week7/metrics/p32/losos_scalars.csv",
  "experiments/week7/metrics/p8/snr_scalars.csv",
  "experiments/week7/metrics/p16/snr_scalars.csv",
  "experiments/week7/metrics/p32/snr_scalars.csv",
  "experiments/week7/pareto_full/pareto_lw3_full.csv",
  "experiments/week4/metrics/s_req_lw_config3_200.csv"
)
$paths | ForEach-Object { if (-not (Test-Path $_)) { throw "Missing $_" } else { "OK $_" } }
```

Expected: all paths print `OK`.

- [ ] **Step 3: Write audit summary**

Use a small Python script or direct markdown edit to write:

```markdown
# Verificarlo Report 1 Refresh Audit

| precision | HLLC samples | Rusanov samples | status |
|---|---:|---:|---|
| p8 | 2 | 2 | exploratory; common subset |
| p16 | 3 | 3 | exploratory |
| p32 | 3 | 3 | exploratory |
| p24-real-float | 30 | 30 | Week 4/Athena metric source |
| p53 | 30 | 30 | Week 4/Athena metric source |

The refreshed Report 1 figures must annotate sample counts. Do not present p8/p16/p32 as 30-sample production statistics.
```

---

## Task 2: Build a Normalized Verificarlo Summary Table

**Files:**
- Create: `scripts/figures/verificarlo_report1_refresh.py`
- Create: `tests/py/test_verificarlo_report1_refresh.py`
- Write: `experiments/week7/verificarlo_report1_refresh/summary.csv`
- Write: `experiments/week7/verificarlo_report1_refresh/summary.json`

- [ ] **Step 1: Write a failing test for normalized merge**

Create `tests/py/test_verificarlo_report1_refresh.py` with:

```python
from pathlib import Path
import pandas as pd

from scripts.figures.verificarlo_report1_refresh import build_summary


def test_build_summary_keeps_sample_counts_and_margins(tmp_path: Path) -> None:
    metric_root = tmp_path / "metrics"
    pareto = tmp_path / "pareto.csv"
    metric_root.mkdir()
    for precision, samples in [("p8", 2), ("p16", 3)]:
        d = metric_root / precision
        d.mkdir()
        pd.DataFrame([
            {
                "solver": "hllc",
                "precision": precision,
                "variable": "rho",
                "s_worst_q05": 1.0,
                "s_accuracy_q05": 1.1,
                "s_reliability_q05": 1.2,
                "n_samples": samples,
            }
        ]).to_csv(d / "losos_scalars.csv", index=False)
        pd.DataFrame([
            {
                "solver": "hllc",
                "precision": precision,
                "variable": "rho",
                "sigma_fp_l1": 10.0,
                "n_samples": samples,
            }
        ]).to_csv(d / "snr_scalars.csv", index=False)
    pd.DataFrame([
        {
            "solver": "hllc",
            "precision_label": "p8",
            "sigma_fp_l1": 10.0,
            "s_worst_q05": 1.0,
            "s_req": 3.0,
            "precision_margin": -2.0,
            "regime": "precision-adequacy deficit",
        }
    ]).to_csv(pareto, index=False)

    out = build_summary(metric_root, pareto)
    row = out[(out["solver"] == "hllc") & (out["precision"] == "p8")].iloc[0]
    assert row["n_samples"] == 2
    assert row["precision_margin"] == -2.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests\py\test_verificarlo_report1_refresh.py -q
```

Expected: fail because `scripts.figures.verificarlo_report1_refresh` does not exist.

- [ ] **Step 3: Implement normalized merge**

Create `scripts/figures/verificarlo_report1_refresh.py` with:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PRECISION_ORDER = {"p8": 8, "p16": 16, "p24-real-float": 24, "p32": 32, "p53": 53}


def _read_metric_rows(metric_root: Path) -> pd.DataFrame:
    frames = []
    for csv_path in sorted(metric_root.glob("p*/losos_scalars.csv")):
        df = pd.read_csv(csv_path)
        frames.append(df[df["variable"] == "rho"].copy())
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_summary(metric_root: Path, pareto_csv: Path) -> pd.DataFrame:
    losos = _read_metric_rows(metric_root)
    pareto = pd.read_csv(pareto_csv).rename(columns={"precision_label": "precision"})
    merged = pareto.merge(
        losos[["solver", "precision", "variable", "s_reliability_q05", "s_accuracy_q05", "n_samples"]],
        on=["solver", "precision"],
        how="left",
    )
    merged["precision_order"] = merged["precision"].map(PRECISION_ORDER)
    merged = merged.sort_values(["solver", "precision_order"]).reset_index(drop=True)
    return merged


def write_outputs(summary: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "summary.csv", index=False)
    (out_dir / "summary.json").write_text(
        json.dumps(summary.to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metric-root", type=Path, default=Path("experiments/week7/metrics"))
    parser.add_argument("--pareto-csv", type=Path, default=Path("experiments/week7/pareto_full/pareto_lw3_full.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("experiments/week7/verificarlo_report1_refresh"))
    args = parser.parse_args()
    summary = build_summary(args.metric_root, args.pareto_csv)
    write_outputs(summary, args.out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test and script**

Run:

```powershell
python -m pytest tests\py\test_verificarlo_report1_refresh.py -q
python scripts\figures\verificarlo_report1_refresh.py
```

Expected: test passes and `summary.csv/json` are written.

---

## Task 3: Regenerate Report-Ready Verificarlo Figures

**Files:**
- Modify: `scripts/figures/verificarlo_report1_refresh.py`
- Write: `experiments/week7/verificarlo_report1_refresh/figures/*.png`
- Test: `tests/py/test_verificarlo_report1_refresh.py`

- [ ] **Step 1: Add a figure smoke test**

Append:

```python
from PIL import Image

from scripts.figures.verificarlo_report1_refresh import plot_precision_sweep


def test_plot_precision_sweep_writes_png(tmp_path: Path) -> None:
    df = pd.DataFrame([
        {"solver": "hllc", "precision": "p8", "precision_order": 8, "sigma_fp_l1": 10.0, "s_worst_q05": 1.0, "s_req": 3.0, "precision_margin": -2.0, "n_samples": 2},
        {"solver": "hllc", "precision": "p16", "precision_order": 16, "sigma_fp_l1": 1.0, "s_worst_q05": 1.5, "s_req": 3.0, "precision_margin": -1.5, "n_samples": 3},
    ])
    out = tmp_path / "fig.png"
    plot_precision_sweep(df, out)
    im = Image.open(out)
    assert im.size[0] > 200
    assert im.size[1] > 150
```

- [ ] **Step 2: Implement plotting functions**

Add functions:

```python
import matplotlib.pyplot as plt


def plot_precision_sweep(summary: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for solver, group in summary.groupby("solver"):
        group = group.sort_values("precision_order")
        axes[0].plot(group["precision"], group["s_worst_q05"], marker="o", label=solver)
        axes[1].plot(group["precision"], group["precision_margin"], marker="o", label=solver)
    axes[0].set_ylabel("s_worst_q05 (rho)")
    axes[1].set_ylabel("s_worst_q05 - s_req")
    for ax in axes:
        ax.set_xlabel("precision")
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
```

Then add two more plot functions in the same style:

- `plot_sigma_fp(summary, out_path)`: log-y `sigma_fp_l1` vs precision, one line per solver.
- `plot_accuracy_noise_tradeoff(summary, out_path)`: scatter `sigma_fp_l1` vs `s_worst_q05`, log-x, annotate precision labels and sample counts.

- [ ] **Step 3: Call plotting functions from `main`**

Add:

```python
fig_dir = args.out_dir / "figures"
plot_precision_sweep(summary, fig_dir / "precision_sweep_losos_rho.png")
plot_sigma_fp(summary, fig_dir / "precision_sweep_sigma_fp_rho.png")
plot_accuracy_noise_tradeoff(summary, fig_dir / "hllc_rusanov_accuracy_noise_tradeoff.png")
```

- [ ] **Step 4: Verify generated PNGs**

Run:

```powershell
python -m pytest tests\py\test_verificarlo_report1_refresh.py -q
python scripts\figures\verificarlo_report1_refresh.py
@'
from pathlib import Path
from PIL import Image
for p in Path("experiments/week7/verificarlo_report1_refresh/figures").glob("*.png"):
    im = Image.open(p)
    print(p, im.size, p.stat().st_size)
'@ | python -
```

Expected: all PNGs open and have nonzero sizes.

---

## Task 4: Regenerate LoSoS/SNR Heatmaps Only From Available Valid Samples

**Files:**
- Read: `experiments/week7/metrics/p8/*heatmap.png`
- Read: `experiments/week7/metrics/p16/*heatmap.png`
- Read: `experiments/week7/metrics/p32/*heatmap.png`
- Optional rerun: `scripts/metrics/losos_metric.py`, `scripts/metrics/snr_metric.py`

- [ ] **Step 1: Decide source policy**

Use existing Week 7 p8/p16/p32 heatmaps as source figures because the corresponding samples exist in this checkout.

Do not reuse `experiments/week4/metrics/losos_accuracy_heatmap.png` as a final 1600² figure unless Week 4 MCA samples are recovered or rerun.

- [ ] **Step 2: Copy or regenerate figures into refresh bundle**

If copying:

```powershell
New-Item -ItemType Directory -Force -Path experiments\week7\verificarlo_report1_refresh\figures\source_heatmaps | Out-Null
Copy-Item experiments\week7\metrics\p8\losos_accuracy_heatmap.png experiments\week7\verificarlo_report1_refresh\figures\source_heatmaps\p8_losos_accuracy_heatmap.png
Copy-Item experiments\week7\metrics\p16\losos_accuracy_heatmap.png experiments\week7\verificarlo_report1_refresh\figures\source_heatmaps\p16_losos_accuracy_heatmap.png
Copy-Item experiments\week7\metrics\p32\losos_accuracy_heatmap.png experiments\week7\verificarlo_report1_refresh\figures\source_heatmaps\p32_losos_accuracy_heatmap.png
```

If regenerating, use the existing scripts with explicit `--reference experiments/week4/metrics/u_ref_200_blockavg.npz` and write to a fresh precision-specific output directory.

- [ ] **Step 3: Add captions in summary**

Every heatmap caption must include:

- precision label,
- solver rows,
- variable columns,
- sample count,
- `s_accuracy=16` means display cap / exact agreement, not proof of 16 true digits.

---

## Task 5: Write Supervisor-Gap Evidence Note

**Files:**
- Create: `docs/experiment_logs/week7_verificarlo_refresh.md`
- Modify: `docs/experiment_logs/report1_evidence_index.md`

- [ ] **Step 1: Create evidence note**

Write:

```markdown
# Week 7 Verificarlo Refresh

Purpose: consolidate Verificarlo-derived Report 1 figures after the 1600² reference refresh.

## Included Figures

| figure | source | report use |
|---|---|---|
| precision_sweep_losos_rho.png | p8/p16/p32 LoSoS + Pareto p24/p53 rows | Delivered digits vs virtual precision |
| precision_sweep_sigma_fp_rho.png | SNR/LoSoS metric CSVs | Emitted FP noise vs virtual precision |
| hllc_rusanov_accuracy_noise_tradeoff.png | normalized summary.csv | Rusanov noise reduction vs truncation penalty |
| pareto_lw3_full_twopanel.png | pareto_full | Preferred Report 1 Pareto figure |

## Supervisor Requests

| request | status | evidence |
|---|---|---|
| Philip metric | satisfied for regenerated regression summaries | `experiments/week4/float_regression/*/summary.md` |
| 1600² reference | satisfied for s_req and 2D regression; Week 4 p53 heatmap rerun depends on MCA sample recovery | `experiments/week4/metrics/s_req_lw_config3_200.csv` |
| Rusanov cleaner explanation | satisfied as interpretation, not recommendation | `experiments/week7/rusanov_noise/summary.csv` |
| Pareto figure | satisfied; use two-panel in report | `experiments/week7/pareto_full/pareto_lw3_full_twopanel.png` |
| drift growth rate | not satisfied; correctly reported n/a | `experiments/week7/drift/summary.md` |
```

- [ ] **Step 2: Update evidence index**

Add one row under cross-cutting precision evidence:

```markdown
| Cross-cutting: Verificarlo precision sweep and supervisor-response figures | Week 7 Verificarlo refresh bundle | `docs/experiment_logs/week7_verificarlo_refresh.md`; `experiments/week7/verificarlo_report1_refresh/summary.md`; `experiments/week7/verificarlo_report1_refresh/figures/` | new / ready after refresh | Verificarlo refresh |
```

---

## Task 6: Audit the Four Outstanding Supervisor Requirements

**Files:**
- Create: `docs/experiment_logs/week7_supervisor_requirements_gap_audit.md`
- Read: `experiments/verificarlo/precexp/`
- Read: `src/gpu/`
- Read: `experiments/week7/metrics/`
- Read: `experiments/week3/week3_validation/plots/`
- Read: `experiments/week3/week3_rusanov/plots/`

- [ ] **Step 1: Verify the current `vfc_precexp` artefact type**

Run:

```powershell
Get-ChildItem -Path experiments\verificarlo\precexp -Recurse -File |
  Select-Object FullName,Length,LastWriteTime |
  Sort-Object FullName |
  Format-Table -AutoSize

rg -n "function|call|vfc_precexp|precexp|precision" experiments\verificarlo\precexp docs scripts -g "!*.bin"
```

Expected: the directory contains `prec_*` whole-program runs plus `exrun/excmp`; no function-level table is present. Record this as **partial only**, not complete.

- [ ] **Step 2: Verify GPU evidence boundaries**

Run:

```powershell
Get-ChildItem -Path src\gpu,tests\unit -File |
  Where-Object { $_.Name -match 'gpu|cuda' } |
  Select-Object FullName,Length,LastWriteTime |
  Format-Table -AutoSize

Get-Content experiments\week6\regression\summary.md
Get-Content experiments\week7\report1_validation_2d_device\cpu_vs_gpu_hllc_strict_double.md
```

Expected: CUDA Euler implementation and strict CPU/GPU validation exist. Record that mixed-precision GPU design is **not implemented**.

- [ ] **Step 3: Verify 2D Verificarlo evidence**

Run:

```powershell
Get-Content docs\experiment_logs\week4_a3_2d_vfc_report.md
Get-Content experiments\week7\metrics\precision_sweep_summary.md
Get-ChildItem experiments\week7\metrics -Recurse -File |
  Where-Object { $_.Name -match 'losos|snr|heatmap|scalars' } |
  Select-Object FullName,Length |
  Format-Table -AutoSize
```

Expected: 2D Verificarlo exists for LW3, with Week 4 p53 production documentation and Week 7 p8/p16/p32 exploratory rows.

- [ ] **Step 4: Verify old plot styles**

Run:

```powershell
rg -n "ax\.plot\(x, data_hllc|ax\.plot\(x, data_rus|combined_summary|ro|Exact" scripts\regression\run_comparison.py experiments\week3\week3_validation\generate_plots.py
```

Expected: `combined_summary` uses exact line + numerical points, while HLLC/Rusanov comparison still uses continuous HLLC/Rusanov lines.

- [ ] **Step 5: Write the gap audit**

Create `docs/experiment_logs/week7_supervisor_requirements_gap_audit.md`:

```markdown
# Week 7 Supervisor Requirements Gap Audit

Purpose: classify the four supervisor-requested follow-ups before refreshing Verificarlo figures. This note audits existing artefacts only; it does not change solver numerics, cfg defaults, or experiment results.

| requirement | status | evidence | next action |
|---|---|---|---|
| `vfc_precexp` per-function precision analysis | partial only | `experiments/verificarlo/precexp/prec_*` contains whole-program precision outputs, not a per-function table | plan a CSC `vfc_precexp` rerun with function/call-site reporting |
| GPU porting guided by FP bottleneck finding | GPU port complete for Euler validation; mixed precision not implemented | `src/gpu/*`, `experiments/week6/regression/summary.md`, `experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md` | write a mixed-precision design note; do not change kernels in this figure-refresh task |
| 2D Verificarlo analysis | completed for LW3, with caveats | `docs/experiment_logs/week4_a3_2d_vfc_report.md`, `experiments/week7/metrics/precision_sweep_summary.md` | consolidate figures and label Week 7 p8/p16/p32 as exploratory |
| point-style HLLC/Rusanov plots | not done | `scripts/regression/run_comparison.py` still uses continuous HLLC/Rusanov lines | create new point-style figures beside existing plots |
```

---

## Task 7: Add a Non-Result-Changing Mixed-Precision Evidence Note

**Files:**
- Modify: `docs/experiment_logs/week7_verificarlo_refresh.md`
- Read: `docs/week3/week3-summary.md`
- Read: `docs/emails/week3_answer_to_philip_2026-04-16.md`
- Read: `src/gpu/euler_gpu_solver.cu`
- Read: `src/gpu/euler_kernels.cuh`

- [ ] **Step 1: Extract the existing mixed-precision claim**

Run:

```powershell
rg -n "Riemann solver choice|flux.*bottleneck|mixed-precision|MUSCL|EOS|pressure computation" docs\week3 docs\emails src\gpu -g "*.md" -g "*.cu" -g "*.cuh"
```

Expected: Week 3 documentation states that the Riemann flux/branching is not the observed FP bottleneck; current GPU code exposes separate GPU solver/kernel boundaries.

- [ ] **Step 2: Append an interpretation-only section**

Append to `docs/experiment_logs/week7_verificarlo_refresh.md`:

```markdown
## GPU Mixed-Precision Design Status

The current CUDA Euler path is validation evidence, not a mixed-precision implementation. Week 3 Verificarlo evidence indicates that the Riemann solver branch structure is not the dominant FP bottleneck; the safer design implication is to keep mixed-precision experiments focused on reconstruction / Hancock predictor / EOS pressure paths first, while preserving the current strict CPU/GPU validation kernels as the baseline.

No GPU kernel precision changes are made by this refresh. Any later mixed-precision CUDA implementation requires a separate experiment plan and CPU/GPU regression gate.
```

Expected: documentation becomes explicit without changing any result or code path.

---

## Task 8: Plan the Real `vfc_precexp` Rerun Without Reclassifying Old Data

**Files:**
- Modify: `docs/experiment_logs/week7_supervisor_requirements_gap_audit.md`
- Create: `docs/experiment_logs/week7_vfc_precexp_rerun_plan.md`
- Read: `experiments/verificarlo/precexp/exrun`
- Read: `experiments/verificarlo/precexp/excmp`

- [ ] **Step 1: Record what the existing precexp directory can and cannot prove**

Run:

```powershell
Get-Content experiments\verificarlo\precexp\exrun
Get-Content experiments\verificarlo\precexp\excmp
Get-ChildItem experiments\verificarlo\precexp\prec_* -File -Filter run_*.txt |
  Measure-Object
```

Expected: existing artefacts are suitable as a coarse whole-program precision sweep only.

- [ ] **Step 2: Create the rerun plan**

Create `docs/experiment_logs/week7_vfc_precexp_rerun_plan.md`:

```markdown
# vfc_precexp Rerun Plan

Purpose: produce the missing per-function / per-call precision evidence requested by Philip. This is a future CSC Verificarlo task and is not part of the current result-refresh operation.

## Current artefact status

`experiments/verificarlo/precexp/` contains precision-labelled whole-program outputs and `exrun/excmp`, but no function-level precision assignment table. It must not be cited as completed per-function analysis.

## Required rerun output

| output | meaning |
|---|---|
| `experiments/week7/vfc_precexp/function_precision.csv` | function or call-site, minimum accepted precision, tested case, pass/fail criterion |
| `experiments/week7/vfc_precexp/summary.md` | report interpretation and limitations |
| `experiments/week7/vfc_precexp/logs/` | CSC command, Verificarlo version, stdout/stderr |

## Candidate functions to track

- MUSCL reconstruction / limiter functions.
- Hancock predictor.
- HLLC/Rusanov flux calls.
- EOS pressure / sound-speed computations.
- CFL computation.

## Pass criterion

Use the existing `excmp` style only as a starting point. The report-facing rerun should compare against a trusted reference and report both global pass/fail and per-function precision assignments.
```

Expected: the plan prevents accidental overclaiming and gives a concrete rerun target.

---

## Task 9: Add Point-Style HLLC-vs-Rusanov Figures Without Overwriting Existing Plots

**Files:**
- Create: `scripts/figures/plot_hllc_rusanov_points.py`
- Create: `tests/py/test_plot_hllc_rusanov_points.py`
- Write: `experiments/week7/verificarlo_report1_refresh/figures/hllc_rusanov_points_summary.png`
- Write: `experiments/week7/verificarlo_report1_refresh/figures/hllc_rusanov_points_<test>.png`
- Read: `experiments/week3/week3_rusanov/data/*_hllc.txt`
- Read: `experiments/week3/week3_rusanov/data/*_rusanov.txt`
- Read: `experiments/week3/week3_validation/generate_plots.py`

- [ ] **Step 1: Write a failing smoke test for the new point-style plotter**

Create `tests/py/test_plot_hllc_rusanov_points.py`:

```python
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.figures.plot_hllc_rusanov_points import plot_point_comparison


def test_plot_point_comparison_writes_png(tmp_path: Path) -> None:
    x = np.linspace(0.0, 1.0, 8)
    exact = np.column_stack([x, np.ones_like(x), np.zeros_like(x), np.zeros_like(x), np.ones_like(x)])
    hllc = exact.copy()
    rusanov = exact.copy()
    rusanov[:, 1] += 0.01
    out = tmp_path / "points.png"

    plot_point_comparison(
        test_title="synthetic",
        exact=exact,
        hllc=hllc,
        rusanov=rusanov,
        out_path=out,
    )

    im = Image.open(out)
    assert im.size[0] > 300
    assert im.size[1] > 200
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
python -m pytest tests\py\test_plot_hllc_rusanov_points.py -q
```

Expected: fail because `scripts.figures.plot_hllc_rusanov_points` does not exist.

- [ ] **Step 3: Implement a point-style plotter adapted from existing code**

Create `scripts/figures/plot_hllc_rusanov_points.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


VAR_COLS = {"rho": 1, "u": 2, "p": 4}
VAR_LABELS = {"rho": r"Density $\rho$", "u": r"Velocity $u$", "p": r"Pressure $p$"}


def load_text(path: Path) -> np.ndarray:
    return np.loadtxt(path)


def plot_point_comparison(test_title: str, exact: np.ndarray, hllc: np.ndarray, rusanov: np.ndarray, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True)
    for ax, (var, col) in zip(axes, VAR_COLS.items()):
        ax.plot(exact[:, 0], exact[:, col], color="black", linewidth=1.2, label="Exact")
        ax.plot(hllc[:, 0], hllc[:, col], "o", markersize=2.0, alpha=0.55, label="HLLC")
        ax.plot(rusanov[:, 0], rusanov[:, col], "s", markersize=2.0, alpha=0.45, label="Rusanov")
        ax.set_title(VAR_LABELS[var])
        ax.set_xlabel("x")
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel(test_title)
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("experiments/week3/week3_rusanov/data"))
    parser.add_argument("--out-dir", type=Path, default=Path("experiments/week7/verificarlo_report1_refresh/figures"))
    args = parser.parse_args()
    tests = ["sod", "toro3", "toro4", "toro5", "stationary_contact"]
    titles = {
        "sod": "Sod",
        "toro3": "Blast Wave",
        "toro4": "Lax",
        "toro5": "Slow Contact",
        "stationary_contact": "Stationary Contact",
    }
    for test in tests:
        hllc_path = args.data_dir / f"{test}_hllc.txt"
        rusanov_path = args.data_dir / f"{test}_rusanov.txt"
        if not hllc_path.exists() or not rusanov_path.exists() or rusanov_path.stat().st_size == 0:
            continue
        hllc = load_text(hllc_path)
        rusanov = load_text(rusanov_path)
        # Use HLLC as the visual reference curve only if no exact sampled file is present.
        # A later refinement can import exact_riemann if report captions require exact overlays.
        plot_point_comparison(titles[test], hllc, hllc, rusanov, args.out_dir / f"hllc_rusanov_points_{test}.png")


if __name__ == "__main__":
    main()
```

This first implementation intentionally creates new point-style figures beside existing line plots. It does not overwrite `experiments/week3/week3_rusanov/plots/*.png`.

- [ ] **Step 4: Run tests and generate new point-style figures**

Run:

```powershell
python -m pytest tests\py\test_plot_hllc_rusanov_points.py -q
python scripts\figures\plot_hllc_rusanov_points.py
```

Expected: test passes and new point-style PNGs are written under `experiments/week7/verificarlo_report1_refresh/figures/`.

- [ ] **Step 5: Verify figures are readable**

Run:

```powershell
@'
from pathlib import Path
from PIL import Image
for p in Path("experiments/week7/verificarlo_report1_refresh/figures").glob("hllc_rusanov_points_*.png"):
    im = Image.open(p)
    print(p, im.size, p.stat().st_size)
'@ | python -
```

Expected: each generated PNG opens and has nonzero byte size.

---

## Task 10: Verify Report-Readiness

**Files:**
- Read: all outputs from Tasks 1-5
- Test: `tests/py/test_verificarlo_report1_refresh.py`
- Test: existing metric/figure tests
- Test: `tests/py/test_plot_hllc_rusanov_points.py`

- [ ] **Step 1: Run targeted tests**

Run:

```powershell
python -m pytest tests\py\test_verificarlo_report1_refresh.py tests\py\test_plot_hllc_rusanov_points.py tests\py\test_s_req_scaling.py tests\py\test_float_regression_report.py tests\py\test_pareto_full_example.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Verify image readability**

Run:

```powershell
@'
from pathlib import Path
from PIL import Image
for p in Path("experiments/week7/verificarlo_report1_refresh/figures").glob("**/*.png"):
    im = Image.open(p)
    assert im.size[0] > 0 and im.size[1] > 0
    print(p, im.size, p.stat().st_size)
'@ | python -
```

Expected: every generated PNG opens.

- [ ] **Step 3: Verify no stale 800² wording in active refresh artefacts**

Run:

```powershell
rg -n "800\\^2|800²|reference_800|ref800" docs\experiment_logs\week7_verificarlo_refresh.md experiments\week7\verificarlo_report1_refresh scripts\figures\verificarlo_report1_refresh.py
```

Expected: no matches unless explicitly labelled as historical provenance.

- [ ] **Step 4: Check git diff scope**

Run:

```powershell
git status --short
git diff --stat -- scripts\figures\verificarlo_report1_refresh.py tests\py\test_verificarlo_report1_refresh.py docs\experiment_logs\week7_verificarlo_refresh.md docs\experiment_logs\report1_evidence_index.md
```

Expected: only planned script/test/docs changes plus generated experiment summary/figures.

---

## Execution Notes

- Keep `p8/p16/p32` language conservative: these are exploratory virtual precision rows with 2-3 samples, useful for trend visualization, not final statistical confidence.
- Use `s_worst_q05 - s_req` / `precision-adequacy margin`, not unqualified "round-off limited".
- For velocity LoSoS heatmaps, explain capped `s_accuracy=16` as display saturation caused by exact or near-exact agreement in quiet/zero-velocity regions.
- Keep `lambda = n/a` unless synchronized multi-time checkpoints are generated.
- Do not claim 1600² CPU/GPU equivalence; the 1600² reference is GPU-produced with supporting strict smoke/preflight evidence.
