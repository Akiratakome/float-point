# Report 1 Evidence-Strengthening Revision Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen Report 1 against the original project PDF and the updated review by adding the highest-value feasible evidence, then revising only the manuscript sections that can absorb that evidence under the 7,500-word cap.

**Architecture:** Keep existing solver numerics, cfg defaults, output formats, and raw artifacts stable. New experiments must use the established `config -> build -> run -> measure -> aggregate -> plot` harness, write metadata, and be registered in `experiments/report1_evidence_map.md` before manuscript prose claims them.

**Tech Stack:** CMake/Ninja CPU/CUDA builds; existing HRSC executable; Python and shell harness scripts under `scripts/`; LaTeX report in `report1/phd-thesis-template-2.4/`; final verification with `pdflatex -draftmode -interaction=nonstopmode thesis.tex`.

---

## Revised Priority Decision

The updated review contains useful points, but they are not equally valuable for Report 1. The original PDF makes these load-bearing:

- Euler validation: at least four cases, including 1D and 2D, with supersonic waves.
- CPU/GPU comparison with quantified differences.
- Single/double precision comparison.
- Exploration of discrepancy growth over time where applicable.
- Discussion of framework/testing/reference-solution strategy.

Therefore the new priority order is:

1. Add fp32/fp64 time-evolution evidence.
2. Add 2D numerical-reference self-convergence evidence.
3. Strengthen CPU/GPU zero-drift diagnostics with auditable hashes/metrics and a strict-vs-fast counterexample already present.
4. Fix zero-word-cost figure/provenance issues.
5. Add compact literature/method fixes only by cutting repeated defensive prose.
6. Add shock-bubble and limiter-variation support only as P1/appendix evidence if explicitly authorized and clearly bounded.

## Immediate Word-Budget Reallocation Pass

This pass implements the user's requested low-risk strategy before any larger experiment insertion. It should be executed by separate workers with disjoint write scopes, then reviewed by the main process.

### Subagent A: Abstract and Chapter 6 Trimming

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Abstract/abstract.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

- [ ] Replace the abstract's full case list with "five Euler test cases spanning one and two dimensions", while retaining the `800^2` LW12 reference boundary and the Verificarlo `p32` caveat in shortened form.
- [ ] Delete or merge `Chapter6` Section 6.1 into the opening of Section 6.2.
- [ ] Compress repeated defensive language in Sections 6.2-6.4, but retain these hard boundaries: Verificarlo `p32` is virtual precision, CPU/GPU equality is saved-output only, no MHD validation is claimed, limiter variation is not measured, and MCA sample counts are small.
- [ ] Target net change: `-150` to `-220` words.

### Subagent B: Chapter 5 Validation and Claims

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

- [ ] Compress Section 5.1 from about 185 words to 2-3 sentences.
- [ ] In Section 5.2, expand the one-dimensional convergence-order explanation: global shock-tube `L1` order is discontinuity- and limiter-limited, so values below two do not contradict smooth-region second-order reconstruction.
- [ ] In Section 5.5, keep the zero CPU/GPU result but express it as byte-identical saved conservative states for covered same-precision, strict-HLLC, matched within-case outputs.
- [ ] In Section 5.6, explain that Toro4 appears only in the wider one-dimensional drift probe, not in the headline validation set; alternatively regenerate the figure without Toro4 and remove the prose reference.
- [ ] Target net change: `-55` to `-90` words.

### Subagent C: Chapter 3/4 Technical Insertions

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`

- [ ] In Chapter 3, clarify that \(\sigma_i\) is a component-wise limited cell jump, not a derivative slope.
- [ ] In Chapter 3 Section 3.5, add a concrete cancellation sentence after the \(S_\ast=N_\ast/D_\ast\) perturbation discussion, keeping "can/may" hedging.
- [ ] In Chapter 4 Section 4.1, cite Bard and Dorelli as GPU-accelerated 2D MUSCL-Hancock MHD precedent for the Report 2 route, not as Report 1 validation evidence.
- [ ] In Chapter 4 Section 4.2, explain that Kahan compensation is used only for simulation-time accumulation after \(\Delta t\) is chosen, not for flux or conservation summation.
- [ ] Do not add more CFL max-reduction text; the manuscript already says this is max/min rather than summation.
- [ ] Target net change: `+80` to `+120` words.

### Subagent D: Figure/Provenance Repairs

**Files:**
- Modify or create report-facing figure script as needed under `scripts/figures/`
- Modify generated images under `report1/phd-thesis-template-2.4/Figs/report1/`
- Modify captions only if necessary in `Chapter5/chapter5.tex`

- [ ] Replot `density_hllc_vs_rusanov_200.png` with a shared density colorbar range.
- [ ] Improve the y-axis/label of `float_double_over_reference_bar.png` through `scripts/figures/report1_d2_replots.py`.
- [ ] For `drift_timeseries_l1_selected.png`, either keep Toro4 and add one short supporting-evidence explanation in Section 5.6, or regenerate the selected figure without Toro4 and remove the prose mention.
- [ ] Target net word change: `0` unless a Toro4 explanatory sentence is chosen.

## Phase 1: Supplementary Experiments

### Task 1: fp32/fp64 Time-Evolution Evidence

**Files:**
- Create: `experiments/report1_fp32_fp64_time_drift/matrix.json`
- Create: `experiments/report1_fp32_fp64_time_drift/summary.md`
- Create: `experiments/report1_fp32_fp64_time_drift/summary.json`
- Create: `experiments/report1_fp32_fp64_time_drift/figures/fp32_fp64_drift_timeseries.png`
- Modify: `experiments/report1_evidence_map.md`
- Later consume in: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

- [x] **Step 1: Build or reuse strict CPU fp32/fp64 binaries.**

Run:
```powershell
cmake -B build-report1-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release
cmake --build build-report1-double
cmake -B build-report1-float -G Ninja -DFLOAT_PRECISION=float -DCMAKE_BUILD_TYPE=Release
cmake --build build-report1-float
```

Expected: both builds produce `hrsc.exe` or `hrsc` without changing source cfg defaults.

- [x] **Step 2: Run checkpointed fp32/fp64 pairs.**

Use existing cases first: Sod, Toro3, Toro5, LW3. Use `output_times` in generated cfg copies, not source cfg files. For 2D, keep LW3 at `200^2` unless runtime is trivial; this is a time-evolution diagnostic, not the main 2D validation table.

The generated matrix should include paired runs like:
```json
{
  "experiment": "report1-fp32-fp64-time-drift",
  "output_root": "experiments/report1_fp32_fp64_time_drift",
  "runs": [
    {
      "name": "sod-fp64-checkpoints",
      "binary": "build-report1-double/hrsc",
      "config": "tests/cases/toro_1d/sod.cfg",
      "precision": "double",
      "build": "cpu-double-strict",
      "output_file": "grid.bin",
      "extra_cfg": {"device": "cpu", "solver": "hllc", "output_times": "0.05,0.10,0.15,0.20"}
    },
    {
      "name": "sod-fp32-checkpoints",
      "binary": "build-report1-float/hrsc",
      "config": "tests/cases/toro_1d/sod.cfg",
      "precision": "float",
      "build": "cpu-float-strict",
      "output_file": "grid.bin",
      "extra_cfg": {"device": "cpu", "solver": "hllc", "output_times": "0.05,0.10,0.15,0.20"}
    }
  ]
}
```

Run:
```powershell
python scripts/run_matrix.py experiments/report1_fp32_fp64_time_drift/matrix.json
```

Expected: each run directory contains copied `config.cfg`, metadata, stdout/stderr, checkpoint files, and final `grid.bin`.

- [x] **Step 3: Aggregate same-time fp32/fp64 metrics.**

Use or adapt `scripts/metrics/drift_timeseries.py` to compare fp64 and fp32 checkpoint pairs by time. Metrics must include at least `L1`, `Linf`, and one field split if already supported.

Expected summary sentence:
```text
The fp32/fp64 discrepancy is checkpoint-dependent and case-dependent; it is reported as precision drift, not hardware drift.
```

- [x] **Step 4: Plot one compact figure.**

Use:
```powershell
python scripts/figures/plot_drift_timeseries.py --input experiments/report1_fp32_fp64_time_drift/summary.json --output experiments/report1_fp32_fp64_time_drift/figures/fp32_fp64_drift_timeseries.png
```

If the script needs a small option addition, keep it plotting-only and do not touch solver code.

Expected: one log-scale or normalised-time figure that can replace or sit beside the current compiler-drift figure.

### Task 2: 2D Reference Self-Convergence Evidence

**Files:**
- Create: `experiments/report1_reference_self_convergence/summary.md`
- Create: `experiments/report1_reference_self_convergence/summary.json`
- Optional create: `experiments/report1_reference_self_convergence/figures/reference_self_convergence.png`
- Modify: `experiments/report1_evidence_map.md`
- Later consume in: `Chapter4/chapter4.tex` and `Chapter5/chapter5.tex`

- [x] **Step 1: Use existing LW3 400/800/1600 artifacts.**

Inputs:
```text
experiments/week4/float_regression/2d/double_400.bin
experiments/week4/float_regression/2d/reference_800.bin
experiments/week7/reference_1600/runs/lw3-n1600-gpu-double-strict/reference_1600.bin
```

Compute:
```text
||rho_400 - downsample(rho_800)||_1
||rho_800 - downsample(rho_1600)||_1
observed ratio/order where meaningful
```

Use `scripts/metrics/downsample_2d.py` or the existing 2D regression metric path.

- [x] **Step 2: Add LW12 only if a 1600 reference is already feasible.**

If there is no existing LW12 `1600^2` reference, do not block the report. Either run a GPU fp64 LW12 `1600^2` reference through `scripts/run_matrix.py`, or explicitly state that LW12 has an `800^2` numerical reference and no 1600 self-convergence row.

Expected summary sentence:
```text
LW3 has an explicit 400/800/1600 self-convergence check; LW12 remains scaled against the available 800^2 reference and is not described as an exact or fully converged solution.
```

- [x] **Step 3: Update evidence map.**

Add the artifact as P0 if it is used in Chapter 4/5.

### Task 3: CPU/GPU Zero-Drift Diagnostic Packet

**Files:**
- Create: `experiments/report1_cpu_gpu_zero_drift_audit/summary.md`
- Create: `experiments/report1_cpu_gpu_zero_drift_audit/hashes.csv`
- Create: `experiments/report1_cpu_gpu_zero_drift_audit/metrics.csv`
- Modify: `experiments/report1_evidence_map.md`
- Later consume in: `Chapter4/chapter4.tex`, `Chapter5/chapter5.tex`, `Chapter6/chapter6.tex`

- [x] **Step 1: Collect final-output and checkpoint hashes.**

For the existing CPU/GPU evidence directories, compute SHA256 for paired CPU/GPU `grid.bin` and checkpoint files.

Run pattern:
```powershell
Get-FileHash -Algorithm SHA256 <path-to-grid.bin>
```

Expected: paired hashes match for all claimed zero-drift saved-output pairs.

- [x] **Step 2: Collect metric evidence.**

Use existing metric summaries where possible:
```text
experiments/week8/report1_device_hllc_fill/cpu_vs_gpu_sod_lw3fp32_hllc_strict.md
experiments/week7/report1_validation_1d_device/cpu_vs_gpu_toro3_toro5_hllc_strict.md
experiments/week7/report1_validation_2d_device/cpu_vs_gpu_hllc_strict_double.md
experiments/week8/report1_2d_config12_fill/cpu_vs_gpu_config12_hllc_strict.md
experiments/week9/cpu_gpu_midtime/summary.md
experiments/week9/cpu_gpu_midtime_n400/summary.md
```

Expected: `L1=0`, `Linf=0`, `ULPmax=0` appears in `metrics.csv` for each manuscript-covered row.

- [x] **Step 3: Add a counterexample boundary row.**

Use existing:
```text
experiments/week9/gpu_strict_vs_fast/summary.md
```

Expected interpretation:
```text
Strict CPU/GPU equality is not a claim that all CUDA builds match; strict-vs-fast CUDA outputs already differ in LW3.
```

Do not claim intermediate primitive-variable equality unless new instrumentation is added.

### Task 4: Figure and Table Repair

**Files:**
- Modify or regenerate: `report1/phd-thesis-template-2.4/Figs/report1/density_hllc_vs_rusanov_200.png`
- Modify or regenerate: `report1/phd-thesis-template-2.4/Figs/report1/drift_timeseries_l1_selected.png`
- Modify or regenerate: `report1/phd-thesis-template-2.4/Figs/report1/float_double_over_reference_bar.png`
- Modify: relevant captions in `Chapter5/chapter5.tex`

- [ ] **Step 1: Replot HLLC-vs-Rusanov with a shared colorbar.**

Use `scripts/figures/plot_hllc_rusanov_points.py` or `scripts/figures/plot_2d.py`. Set one density range for both panels, e.g. the union range used by the two arrays.

Expected: no visual comparison uses different density scales without saying so.

- [ ] **Step 2: Fix the Toro4 inconsistency.**

If the figure includes Toro4, either add one short explanatory phrase in the caption or regenerate the figure excluding Toro4. Prefer regeneration unless Toro4 carries a needed result.

- [ ] **Step 3: Improve axis labels without adding prose.**

Use plot labels such as:
```text
R_ref = ||rho_fp32 - rho_fp64||_1 / ||rho_fp64 - rho_ref||_1
L1 drift in conserved state
fraction of cells with noise/reference-error ratio > 1
```

This is a figure-editing task, not a manuscript-word task.

### Task 5: Optional Shock-Bubble Support Run

**Files:**
- Create: `experiments/report1_shock_bubble_support/matrix.json`
- Create: `experiments/report1_shock_bubble_support/summary.md`
- Create: `experiments/report1_shock_bubble_support/figures/shock_bubble_density_schlieren.png`
- Modify: `experiments/report1_evidence_map.md`
- Optional consume in: appendix or one sentence in `Chapter5/chapter5.tex`

- [x] **Step 1: Run only if Tasks 1-4 are complete.**

Use existing configs:
```text
tests/cases/shock_bubble/shock_bubble_n400x100.cfg
tests/cases/shock_bubble/shock_bubble_n400x100_rusanov.cfg
```

Completed CPU-only support matrix:
```text
HLLC, fp64, CPU
HLLC, fp32, CPU
Rusanov, fp64, CPU
Rusanov, fp32, CPU
```

- [x] **Step 2: Treat as support, not a new main validation pillar.**

No exact reference is available in the current evidence map. Use it to show a suggested test has been probed, not to displace LW3/LW12 or make a strong accuracy claim.

Expected manuscript use:
```text
A shock-bubble support run was retained as qualitative stress-test evidence only; the main quantitative validation remains the five-case matrix with exact or numerical references.
```

### Task 6: Do Not Add Limiter Variation Unless Explicitly Authorized

Limiter variation would require a documented limiter-selection interface or solver-numerics change. Under current Report 1 writing rules, keep it as a limitation unless the user explicitly asks to add a new opt-in solver variation.

User explicitly authorized a default-preserving opt-in interface. Completed evidence:

- [x] Add CPU `limiter` cfg key with `minbee` as the default; GPU rejects non-minbee because kernels hard-code minbee.
- [x] Add tests showing missing `limiter` matches explicit `minbee`, `vanleer` changes output, and invalid values fail.
- [x] Run `experiments/report1_limiter_variation_optin/summary.md` comparing minbee and van Leer on Sod, Toro3, Toro5, and LW3 N=200.
- [x] Register the support evidence in `experiments/report1_evidence_map.md`.

## Phase 2: Subagent Manuscript Revisions

Each subagent must preserve or reduce word count. Every added sentence needs a deletion elsewhere.

### Task 7: Background and Literature Subagent

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter2/chapter2.tex`
- Modify only if cited: `report1/phd-thesis-template-2.4/References/references.bib`
- Check: `report1/references/reference.md`

- [ ] Cut 80-120 words from generic background/gap prose.
- [ ] Add compact coverage of: catastrophic cancellation, rounding modes, subnormal/FTZ relevance, and Kahan summation context.
- [ ] Add only high-value citations. Minimum recommended: Demmel & Nguyen for reproducible reductions if CPU/GPU reductions are discussed; Bard & Dorelli must be cited in prose if kept in the bibliography.
- [ ] Do not expand to a 30-40 reference literature survey; that would hurt the current word budget.

### Task 8: Numerical Method Subagent

**Files:**
- Modify: `Chapter3/chapter3.tex`

- [ ] Explicitly state \(\sigma_i\) is a limited jump with units of \(U\), not a raw derivative slope.
- [ ] State the Hancock predictor is applied to conserved variables in the report implementation.
- [ ] Add one sentence distinguishing the dimensionally split update from Strang/unsplit second-order-in-time claims.
- [ ] Add primitive recovery cancellation \(p=(\gamma-1)(E-\frac12\rho |u|^2)\), sound-speed positivity, and limiter tie-breaking to the precision-sensitive decision table if space permits.
- [ ] Add one compact MHD method sentence naming HLLD/Powell/Bard-Dorelli only if equal words are cut elsewhere.

### Task 9: Implementation Subagent

**Files:**
- Modify: `Chapter4/chapter4.tex`

- [ ] Strengthen the stand-alone vs AMReX justification: custom profiling, fixed data layout, direct CPU/CUDA parity, and easier instrumentation.
- [ ] Add the CUDA details the review asks for if known from code/metadata: kernel separation, no atomics in reported reductions, shared-memory CFL block reduction, host-device transfer strategy, and no claim of throughput optimality.
- [ ] Define ULP and SSIM at first use.
- [ ] Clarify testing framework: unit tests, Python harness, binary-output comparison, metadata, and MCA seed handling.
- [ ] Explain the toolchain split as an evidence boundary and, if new unified-toolchain reruns are completed, update this section to reduce the caveat.

### Task 10: Validation Subagent

**Files:**
- Modify: `Chapter5/chapter5.tex`

- [ ] Insert the fp32/fp64 time-drift figure/table from Task 1.
- [ ] Insert the 2D reference self-convergence statement from Task 2.
- [ ] Replace the strongest CPU/GPU zero-drift wording with audit-backed saved-output wording from Task 3.
- [ ] Add the convergence-order explanation: shock-tube \(L_1\) errors are discontinuity-dominated, so observed orders below two do not contradict second-order smooth-region behaviour.
- [ ] Remove or explain Toro4 in the drift figure.
- [ ] If shock-bubble support exists, mention it only briefly or place it in appendix.

### Task 11: Discussion, Conclusion, and Abstract Subagent

**Files:**
- Modify: `Abstract/abstract.tex`
- Modify: `Chapter6/chapter6.tex`
- Modify: `Chapter7/chapter7.tex`

- [ ] Cut repeated defensive phrases such as repeated "bounded baseline" and repeated "not a general statement".
- [ ] Replace them with one compact limitations paragraph.
- [ ] Remove the abstract's detailed `p32` caveat unless it is needed to prevent confusion; move that caveat to Chapter 4/6.
- [ ] Add a clearer "what was learned" sentence: precision drift is small relative to available reference error in the tested final states, but time-drift and fast-math evidence show implementation choices can still alter saved states.
- [ ] Keep MHD as Report 2 direction; do not claim MHD validation.

## Phase 3: Review Gate

### Task 12: Evidence Map Gate

- [ ] Every new experiment has `summary.md`, metadata, and a row in `experiments/report1_evidence_map.md`.
- [ ] No manuscript claim cites a raw grid directly.
- [ ] Shock-bubble, if run, is labelled support/provenance unless it has reference metrics.

### Task 13: Forbidden Label and Claim Scan

Run:
```powershell
rg -n "week7|week8|D1|D2|HLLC-fill|config12|USE_GPU" report1/phd-thesis-template-2.4 -g "*.tex" -g "!SampleContent/**" -g "!Classes/**"
rg -n "generally adequate|hardware has no effect|MHD validation|p32.*IEEE fp32|IEEE fp32.*p32" report1/phd-thesis-template-2.4 -g "*.tex" -g "!SampleContent/**"
```

Expected: no manuscript-facing forbidden labels or overclaims.

### Task 14: Word Count Gate

Run:
```powershell
texcount -inc -sum -q thesis.tex
```

from:
```text
report1/phd-thesis-template-2.4/
```

Expected: Overleaf counted text remains below 7,500. Local `texcount` is a reference only; Overleaf count controls.

### Task 15: Compile Gate

Run:
```powershell
pdflatex -draftmode -interaction=nonstopmode thesis.tex
```

Expected: no undefined references or citations.

### Task 16: Final Writing Gate

- [ ] Every figure/table is interpreted in prose.
- [ ] Every citation supports the sentence it appears in.
- [ ] All edited prose passes `report1/skills/avoiding-ai-flavor/SKILL.md`.
- [ ] Final text still answers the original PDF, not the review in isolation.
