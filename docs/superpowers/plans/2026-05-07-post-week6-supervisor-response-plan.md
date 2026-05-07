# Post-Week 6 Supervisor Response Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert Philip's latest feedback into a low-risk Week 7 / Report 1 work package: explain existing metrics, produce the missing supervisor-facing examples, and extend the experiment matrix without changing solver numerics, cfg defaults, or existing output formats.

**Architecture:** Keep all work inside the harness path `config -> build -> run -> measure -> aggregate -> plot`. New behaviour is added through new matrix files, report scripts, plotting scripts, and documentation. Existing solver code is treated as frozen unless a test exposes a harness-only bug.

**Tech Stack:** C++17/CUDA HRSC binaries already built in Week 6, Python matrix/report/plot scripts, existing Verificarlo outputs, Markdown experiment logs.

---

## Supervisor Asks Mapped To Work

| Source | Ask | Week 6 status | Plan response |
|---|---|---|---|
| `supervisor.md` | Explain why Rusanov may show less noise | Observed but not yet interpreted rigorously | Task 1: write and support a Rusanov-vs-HLLC interpretation note using existing A4/C2 data plus one targeted matrix if needed |
| `supervisor.md` | Define the criterion for "round-off limited" | Current wording is potentially confusing | Task 2: formalise the criterion and rename/report regimes if needed without rewriting old summaries in place |
| `supervisor.md` | GPU assignment code is sufficient | Week 6 CUDA solver + CSC smoke complete | Do not expand GPU numerics now; only use GPU in experiment matrices |
| `supervisor.md` | Show drift from small implementation changes; Lyapunov-like measure is sensible | Not yet done beyond CPU-vs-GPU smoke | Task 3: implement a drift time-series pipeline for CPU/GPU, `<`/`<=`, fast-math, and solver variants |
| `supervisor.md` | Precision Direction 2 should inform drift study | Existing SNR/LoSoS/s_req tools exist | Task 4: connect precision adequacy metrics to drift results in one aggregate table |
| `supervisor.md` | Pareto plot needs a full example; log axes may help | p53-only plot exists; p24 table exists | Task 5: generate a full p53+p24 Pareto example with log x-axis or two panels |
| `supervisor.md` | Degenerate cases may be excluded or density-only | Stationary contact degeneracy already noted | Task 6: define pass/fail exclusion rules and density-only fallback for degenerate denominators |
| Older Week 3/5 emails | `vfc_precexp` and unstable-branch detection remain useful | Deferred in docs | Carry forward after Report 1 unless the Week 7 drift study needs branch evidence |
| Workflow | Map every Week-7 artefact to its Report-1 destination | Implicit only | Task 8: one-page evidence index linking artefacts to Report 1 §2/§3/§4 |
| Workflow | Report progress to Philip | One round-trip per week | Task 9: end-of-week progress email bundling all Week-7 artefacts and open questions; sent *after* the work is done |

---

## File Structure

**Create:**
- `docs/emails/week7_progress_to_philip_2026-05-XX.md` - end-of-week progress email summarising Week-7 artefacts, drift/λ results, and open questions (drafted *after* Tasks 1–8 complete).
- `docs/week7/week7-plan.md` - operational Week 7 plan derived from this document.
- `docs/experiment_logs/week7_supervisor_response.md` - supervisor-facing explanation and evidence index.
- `docs/experiment_logs/report1_evidence_index.md` - one-page map of Week-7 artefacts to Report 1 §2/§3/§4.
- `experiments/week7/drift/matrix.json` - deterministic drift matrix; no large grids committed.
- `experiments/week7/pareto_full/matrix.json` - only if new runs are required; otherwise document reused inputs.
- `scripts/metrics/drift_timeseries.py` - compute per-output-time differences and exponential-growth fits (with `--fit-window` for transient vs late/chaotic regimes).
- `scripts/figures/plot_drift_timeseries.py` - plot drift curves and fitted slopes.
- `scripts/figures/pareto_full_example.py` - combine existing p53/p24 rows into a supervisor-facing figure.
- `tests/py/test_drift_timeseries.py` - hermetic tests for fit/window/degenerate behaviour.
- `tests/py/test_pareto_full_example.py` - hermetic tests for log/two-panel plotting inputs.

**Modify:**
- `scripts/regression/float_regression_report.py` only if device-mode summaries need timing or pair labels for the Week 7 matrix.
- `scripts/metrics/s_req_metric.py` only if the regime label needs to be made explicit as an additive helper, preserving existing outputs.
- `docs/INDEX.md` to add Week 7 links after `docs/week7/week7-plan.md` exists.

**Do not modify unless explicitly requested:**
- `src/euler/*`, `src/gpu/*`, numerical kernels, default cfg values, existing Week 4-6 summaries, existing binary format.

---

## Task 1: Rusanov Noise Interpretation Note

**Files:**
- Create: `docs/experiment_logs/week7_supervisor_response.md`
- Read: `docs/emails/week3_answer_to_philip_2026-04-16.md`
- Read: `docs/emails/week5_meeting_script_2026-04-30.md`
- Read: `docs/week6/week6-summary.md`

- [ ] **Step 1: Extract existing evidence**

Run:

```powershell
rg -n "Rusanov|HLLC|sigma|σ|noise|diffusive|pressure|subtractive|MCA" docs experiments scripts
```

Expected: identify existing A4/C2 figures and tables; no code changes.

- [ ] **Step 2: Write the interpretation**

Create `docs/experiment_logs/week7_supervisor_response.md` with this section:

```markdown
## Why Rusanov can look cleaner

Rusanov is more diffusive than HLLC. That extra dissipation smooths sharp
gradients and reduces the local amplification of round-off noise near shocks
and contacts. The plausible mechanism is not that Rusanov has more accurate
physics; it is that it damps high-frequency structure before the EOS pressure
calculation and reconstruction stages can amplify small perturbations.

This interpretation is consistent with the existing A4/C2 observations:

| Evidence | Interpretation |
|---|---|
| Rusanov has larger deterministic truncation error than HLLC | Cleaner noise is bought by diffusivity |
| Rusanov has lower `sigma_FP_L1` in LW3 p53/p24 rows | Round-off variance is damped |
| C2 shows pressure is sensitive near discontinuities | EOS subtraction remains a likely amplification point |
| Rusanov fails or degrades near tests where excessive diffusion is harmful | Noise reduction is not a general superiority claim |
```

- [ ] **Step 3: Add one sentence of caution**

Add:

```markdown
This is an interpretation of the measured data, not a solver recommendation:
HLLC remains the sharper and generally more accurate Euler solver in these
validation tests.
```

- [ ] **Step 4: Add one supporting analysis (not just interpretation)**

Philip asked for "both **analyse** and **interpret**", so the note must cite
*one new measurement* rather than only re-narrating existing tables. Pick the
cheapest of:

- **Total-variation decay rate** per timestep on Sod (HLLC vs Rusanov), produced
  from the existing convergence dumps — quantifies dissipation directly.
- **σ_FP histogram bucketed by local density gradient** on the LW3 200² A4
  ensemble — confirms "noise amplification concentrates near discontinuities"
  rather than asserting it.
- **Per-stage noise growth**: rerun one Sod p24-MCA with intermediate dumps
  after `reconstruct`, `riemann`, `update` and compare per-stage σ between
  HLLC and Rusanov.

Write the result as a single figure or table inside `week7_supervisor_response.md`
under a `### Supporting measurement` subsection. Pick the option whose required
data already exists; only fall back to a new run if none does.

- [ ] **Step 5: Verify no stale claim**

Run:

```powershell
rg -n "Rusanov.*better|HLLC.*worse|always cleaner|round-off-limited" docs/experiment_logs/week7_supervisor_response.md
```

Expected: no over-strong wording.

---

## Task 2: Formalise The "Round-Off Limited" Criterion

**Files:**
- Create or extend: `docs/experiment_logs/week7_supervisor_response.md`
- Optional modify: `scripts/metrics/s_req_metric.py`
- Test: existing `tests/py/test_s_req_scaling.py`

- [ ] **Step 1: State the current criterion explicitly**

Add:

```markdown
## Criterion for the regime label

The current A4 table labels a row using

`margin = s_worst_q05 - s_req(N)`.

Here `s_req(N) = -log10(||E_trunc(N)||_1) + 1`, so it is a
truncation-anchored target for how many significant digits the FP path needs
to avoid dominating the grid-resolution error. A negative margin means the
5th-percentile worst-cell significant-digit estimate is below that target.
```

- [ ] **Step 2: Clarify terminology**

Add:

```markdown
For Report 1, describe this as a "precision-adequacy margin" before calling it
"round-off limited". The phrase "round-off limited" can be misleading when
the same row also has truncation-dominated bulk error. The safer sentence is:
"at this resolution, the significant-digit margin is below the truncation
anchored target, while the bulk L1 error remains dominated by truncation."
```

- [ ] **Step 3: Decide whether to change labels in future outputs only**

If code changes are needed, add a new column such as `precision_margin` and keep
the old `regime` column unchanged for compatibility. Do not rewrite Week 4
summary files in place.

- [ ] **Step 3b: Append a terminology-update note to the old A4 table**

Edit `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md` and append
(do not rewrite) a short trailing section:

```markdown
## Terminology update (2026-05-07)

The "regime" column above is retained for traceability. Report 1 and all Week 7+
outputs use the wording "precision-adequacy margin" instead of "round-off
limited" — see `docs/experiment_logs/week7_supervisor_response.md`. The numerical
criterion (`s_worst_q05 - s_req(N) < 0`) is unchanged; only the label is
clarified.
```

This prevents Report 1 references to this table from inheriting the ambiguous
phrase while keeping the original artefact intact.

- [ ] **Step 4: Run existing metric tests if code changed**

Run:

```powershell
python -m pytest tests/py/test_s_req_scaling.py -q
```

Expected: pass.

---

## Task 3: Drift Time-Series Pipeline

**Files:**
- Create: `scripts/metrics/drift_timeseries.py`
- Create: `scripts/figures/plot_drift_timeseries.py`
- Create: `tests/py/test_drift_timeseries.py`
- Create: `experiments/week7/drift/matrix.json`

- [ ] **Step 0: Verify (or add) intermediate-time checkpoint capability**

Drift fitting needs a sequence `(t_k, ||u_A(t_k) - u_B(t_k)||)`. Today's
`run_normal` only writes the final state. Before any matrix run:

```powershell
rg -n "output_times|checkpoint|dump_every|HRSC_DUMP" src tests/cases scripts
```

If no per-time-step or per-output-time dump exists, do the smallest opt-in
extension that fits AGENTS.md ("opt-in, no default change"):

- Preferred: extend `run_normal` to honour an `output_times = t1,t2,...` cfg key
  that, when present, writes `<output_file>.t<index>.bin` at each listed time
  via the existing `write_binary` helper. Default behaviour unchanged when the
  key is absent.
- Fallback: an env-var-driven `HRSC_DUMP_EVERY=N` mirroring the Week-5
  `HRSC_DUMP_DIR/HRSC_DUMP_TAG` pattern (Task-2 of the
  `2026-04-30-supervisor-feedback-float-vs-double-regression-metric.md` plan).

Add a unit test that the default cfg path emits exactly one binary (no
regression of G5 byte identity) and that `output_times = ...` emits N+1
binaries with monotonically increasing header `time`.

This is a hidden prerequisite — without it Steps 3–5 cannot produce a time
series.

- [ ] **Step 1: Write tests for deterministic drift fitting**

Create `tests/py/test_drift_timeseries.py` with tests for:

```python
def test_fit_exponential_growth_recovers_known_lambda():
    # times=[0,1,2,3], errors=2*exp(0.3*t)
    # expected lambda ~= 0.3
    ...

def test_fit_skips_zero_and_nonfinite_errors():
    # zero initial differences should not produce -inf in the fit
    ...

def test_density_only_mode_ignores_degenerate_velocity():
    # stationary-contact-style zero velocity should not poison density drift
    ...
```

- [ ] **Step 2: Implement scalar time-series reader**

`drift_timeseries.py` should accept a list of paired HRSC binaries or summary rows and emit:

```json
{
  "case": "lw3",
  "pair": "cpu_strict_vs_gpu_strict",
  "variable": "rho",
  "times": [0.05, 0.10, 0.15],
  "l1": [1e-15, 3e-15, 1e-14],
  "linf": [2e-15, 5e-15, 2e-14],
  "lambda_l1": 0.42,
  "fit_window": [0.05, 0.15],
  "notes": []
}
```

- [ ] **Step 3: Add a matrix that produces output checkpoints**

Use new generated cfgs under `experiments/week7/drift/runs/*/config.cfg`, created
by `scripts/run_matrix.py`. Do not edit source cfgs. Each generated cfg sets
`output_times = ...` (from Step 0) so a drift time series is produced.

Drift axes covered (each row is one *pair* whose two members differ in exactly
one axis). Run the full list — any reduction can be negotiated with Philip
in the Task 9 progress email rather than blocking on it now:

| Case | Axis | Pair members |
|---|---|---|
| Sod | hardware | CPU strict vs GPU strict |
| Sod | branch rule | HLLC `<=` vs HLLC `<` |
| Sod | FMA | `--fmad=false` vs `--fmad=true` (or `-ffp-contract=off` vs `fast`) |
| Sod | optimisation | O2 IEEE vs O3 IEEE |
| Sod | fast-math | O3 IEEE vs O3 fast-math |
| LW Config 3 | hardware | CPU strict vs GPU strict |
| LW Config 3 | branch rule | HLLC `<=` vs HLLC `<` |
| LW Config 3 | optimisation+fast-math | O2 IEEE vs Ofast fast-math (combined "extreme" pair) |
| LW Config 3 (extended t) | chaos | same cfg, longer t_end (see Step 3b) |
| LW Config 4 or 12 | hardware | CPU strict vs GPU strict (2D supplementary) |

Builds for the FMA/optimisation/fast-math axes already exist via
`scripts/build_all.sh` (build matrix produced under `build-matrix/`). Reuse
those build labels rather than recreating CMake configurations here.

If runtime budget tightens, drop rows from the bottom up; keep at minimum
{hardware, branch rule, fast-math} on at least one 1D + one 2D case. Any
scope change is reported in the Task 9 progress email, not pre-cleared.

- [ ] **Step 3b: Add a chaotic / extended-time pair so λ has meaning**

`log(error) = λt + c` on Sod or LW3 at standard `t_end` only captures transient
amplification, not a Lyapunov-like exponent. Add at least one pair where the
flow has had time to enter a multi-shock-interaction (or genuinely chaotic)
regime:

- Cheap option: rerun LW Config 3 with `t_end = 1.0` (≈3.3× the standard
  `t = 0.3`); after the four-shock interaction the field has many secondary
  structures, so drift between two builds can grow before terminating.
- Better option (if MHD bring-up has slipped to the point HLL is stable): one
  Orszag-Tang run with HLL at modest resolution (128² or 256²) for a few crossing
  times, fitted with the same script.

The drift script must accept a `--fit-window` argument so that the report
distinguishes "transient amplification rate" (early window) from
"asymptotic / chaotic growth rate" (late window). Both numbers are useful;
labelling them honestly is the point.

- [ ] **Step 4: Run the smallest smoke first**

Run:

```powershell
python scripts/run_matrix.py experiments/week7/drift/matrix.json --dry-run
python -m pytest tests/py/test_drift_timeseries.py -q
```

Expected: dry-run writes configs and metadata; tests pass.

- [ ] **Step 5: Run real matrix only after dry-run inspection**

Run:

```powershell
python scripts/run_matrix.py experiments/week7/drift/matrix.json
python scripts/metrics/drift_timeseries.py --matrix experiments/week7/drift/matrix_summary.json --output experiments/week7/drift/summary
python scripts/figures/plot_drift_timeseries.py --input experiments/week7/drift/summary.json --output experiments/week7/drift/figures
```

Expected: `summary.{json,csv,md}` plus figures; large `.bin` checkpoint files deleted after aggregation unless required for reproduction.

---

## Task 4: Precision Metrics Inform Drift Results

**Files:**
- Create or extend: `docs/experiment_logs/week7_supervisor_response.md`
- Optional create: `scripts/aggregate_metrics.py` input under `experiments/week7/drift/aggregate_inputs.json`

- [ ] **Step 1: Build one combined table**

Add a table:

```markdown
| case | pair | precision/build delta | L1 drift at final time | fitted lambda | sigma_FP_L1 or Philip ratio | interpretation |
|---|---|---:|---:|---:|---:|---|
```

- [ ] **Step 2: Interpret, do not only report**

Each row must include a sentence such as:

```markdown
The CPU/GPU strict pair has zero or ULP-level drift, so the Week 6 GPU path is
not yet the source of reproducibility divergence. The larger drift appears
when compiler flags or implementation branches are changed, which supports the
project's focus on small numerical implementation choices.
```

---

## Task 5: Full Pareto Example For Philip

**Files:**
- Create: `scripts/figures/pareto_full_example.py`
- Create: `tests/py/test_pareto_full_example.py`
- Create outputs under: `experiments/week7/pareto_full/`
- Document in: `docs/experiment_logs/week7_supervisor_response.md`

- [ ] **Step 1: Write plotting input test**

Test that the script accepts rows with:

```text
solver, precision_label, sigma_fp_l1, s_worst_q05, s_req, regime
```

and produces either:

- one log-x plot, or
- two panels: p53 zoom and p24/p53 overview.

- [ ] **Step 2: Reuse existing A4 rows first**

Before deciding to rerun anything, grep the existing A4 / metrics outputs for
the required `(solver, precision, sigma_FP_L1, s_worst_q05, s_req)` rows:

```powershell
rg -n "sigma_fp|s_worst|s_req|p24|p53" experiments/week4/metrics experiments/week4/figures/a4_pareto experiments/verificarlo
ls experiments/week4/metrics
```

Only if a row is genuinely missing should Verificarlo be rerun — a single 2D
MCA batch is multi-hour cluster time and is not worth burning before the grep
confirms a gap.

- [ ] **Step 3: Generate the full example**

Run:

```powershell
python scripts/figures/pareto_full_example.py --output experiments/week7/pareto_full
```

Expected:

- `pareto_lw3_full_logx.png`
- `pareto_lw3_full_twopanel.png`
- `pareto_lw3_full.csv`
- `summary.md` explaining what the plot demonstrates

- [ ] **Step 4: Write the explanation Philip asked for**

Add:

```markdown
The Pareto plot demonstrates the trade-off between emitted FP noise
(`sigma_FP_L1`, x-axis) and delivered significant digits (`s_worst_q05`,
y-axis), with `s_req(N)` marking the target implied by truncation error at the
same grid resolution. Log scaling is required because p24 and p53 differ by
many orders of magnitude in emitted noise.
```

---

## Task 6: Degenerate-Case Policy

**Files:**
- Create or extend: `docs/experiment_logs/week7_supervisor_response.md`
- Optional modify: `scripts/regression/float_regression_report.py`
- Test: `tests/py/test_float_regression_report.py`

- [ ] **Step 1: Define policy**

Add:

```markdown
## Degenerate denominators

Pass/fail tables exclude variables whose denominator is zero or whose mean is
close enough to zero that the relative metric is dominated by cancellation.
Those cases are still reported as sensitivity tests. For stationary contact,
density is the primary pass/fail variable because it is positive and physically
meaningful; velocity relative significant-digit metrics are diagnostic only.
```

- [ ] **Step 2: If needed, add explicit `excluded_reason` fields**

Future JSON summaries may include:

```json
{"gate_status": "excluded", "excluded_reason": "zero_denominator"}
```

Keep existing Markdown columns stable; add new columns only at the end.

- [ ] **Step 3: Run report tests if code changed**

Run:

```powershell
python -m pytest tests/py/test_float_regression_report.py -q
```

Expected: pass.

---

## Task 7: Week 7 Operational Plan And Index Link

**Files:**
- Create: `docs/week7/week7-plan.md`
- Modify: `docs/INDEX.md`

- [ ] **Step 1: Create `docs/week7/week7-plan.md`**

The plan should list daily priorities:

| Day | Priority |
|---|---|
| D1 | Freeze Week 6 baseline; write supervisor-response explanation skeleton |
| D2 | Full Pareto example and regime-criterion wording |
| D3 | Drift time-series tests and smallest matrix dry-run |
| D4 | Run deterministic drift matrix locally |
| D5 | Aggregate drift + precision metrics; write interpretation |
| D6 | Optional CSC/GPU extension only if local matrix is clean |
| D7 | Cleanup large grids; final Report 1 evidence index |

- [ ] **Step 2: Add Week 7 to `docs/INDEX.md`**

Only after `docs/week7/week7-plan.md` exists, add a Week 7 row with plan link and mark summary pending.

- [ ] **Step 3: Verify links**

Run:

```powershell
Test-Path docs/week7/week7-plan.md
rg -n "week7" docs/INDEX.md
```

Expected: both present.

---

## Task 8: Report 1 Evidence Index

**Goal:** Make sure every Week-7 artefact has a clear destination in the Report-1
narrative. Not a writing task — just a one-page index that lists each figure /
table, the section it serves, and whether the file is ready or needs rerunning.

**Files:**
- Create: `docs/experiment_logs/report1_evidence_index.md`

- [ ] **Step 1: List the Report-1 sections that consume evidence**

Mirror the Report 1 marking criteria from `docs/requirement/overall.md`:

- §2 Mathematical theory — schemes, HLLC vs Rusanov, variation points (`<=`/`<`)
- §3 Code description — precision templating, harness, GPU bring-up
- §4 Validation — 1D Toro, 2D LW3, CPU vs GPU, float vs double, convergence
- (Cross-cutting) precision-adequacy / Pareto / drift evidence

- [ ] **Step 2: For each section, list the artefact and its current state**

Table columns:

| Report 1 section | Artefact | Path | State | Owner task |
|---|---|---|---|---|
| §3 / Pareto | Full Pareto example | `experiments/week7/pareto_full/pareto_lw3_full_*.png` | new (Task 5) | Task 5 |
| §4 Validation | 1D float regression (Philip metric) | `experiments/week4/float_regression/1d/summary.md` | already produced | — |
| §4 Validation | 2D LW3 float regression | `experiments/week4/float_regression/2d/summary.md` | already produced | — |
| §4 Validation | CPU vs GPU regression | `experiments/week6/regression/summary.md` | already produced | — |
| §4 Validation | CSC GPU smoke | `experiments/week6/csc_smoke/summary.md` | already produced | — |
| Cross-cut | A4 tradeoff table + terminology note | `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md` | append note (Task 2 Step 3b) | Task 2 |
| Cross-cut | Drift time-series + λ table | `experiments/week7/drift/summary.{md,csv,json}` | new (Task 3) | Task 3 |
| Cross-cut | Precision ↔ drift combined table | `docs/experiment_logs/week7_supervisor_response.md` | new (Task 4) | Task 4 |
| Cross-cut | Rusanov-noise interpretation + supporting analysis | `docs/experiment_logs/week7_supervisor_response.md` | new (Task 1) | Task 1 |

States: `already produced` / `new` / `regenerate needed` / `at risk` / `optional`.

- [ ] **Step 3: Flag gaps and rerun candidates**

End the document with a "Gaps" section listing any §-rows that have no current
artefact, plus any artefacts marked `regenerate needed` (e.g. an A4 figure that
must be re-rendered with the Task-5 log axis or the Task-2 terminology).

- [ ] **Step 4: Link from `docs/INDEX.md`**

Add one line under the existing "Where to look" table:

```markdown
| Report 1 evidence map (which artefact lives where) | [experiment_logs/report1_evidence_index.md](experiment_logs/report1_evidence_index.md) |
```

---

## Task 9: End-Of-Week Progress Email To Philip

**Goal:** After all other tasks land, send Philip a single progress-report email
that bundles the week's results, presents the new artefacts inline, and asks
the open questions in one round-trip. Do *not* gate any earlier task on his
reply — proceed with the work first, write the email last.

**Files:**
- Create: `docs/emails/week7_progress_to_philip_2026-05-XX.md` (date = actual
  send date, end of Week 7).

- [ ] **Step 1: Wait until Tasks 1–8 are complete**

The email summarises actual artefacts and numbers, so it can only be drafted
when those numbers exist. Do not write speculative results.

- [ ] **Step 2: Draft the email**

Use the same structure as `docs/emails/week3_reply_to_philip_2026-04-16.md` and
the meeting script `docs/emails/week5_meeting_script_2026-04-30.md`. Sections:

1. **One-paragraph executive summary** — Direction 1 chosen as primary; drift
   and λ extracted; Pareto full example produced; degenerate-case policy
   formalised; round-off-limited terminology clarified.
2. **Per-ask responses** — one short subsection per Philip ask in `supervisor.md`,
   each linking to the concrete artefact (Tasks 1, 2, 5, 6).
3. **Drift study results** — link `experiments/week7/drift/summary.md` and the
   λ table from Task 3 / Task 4; call out which axis (hardware, branch rule,
   FMA, fast-math) produced the largest drift.
4. **Open questions** — only the ones whose answers will steer Week 8+ work,
   e.g.:
   - Should the chaotic-extension run move to Orszag-Tang ahead of Week 12 MHD?
   - Pareto: keep both single-panel log-x and two-panel, or pick one for Report 1?
   - Any axis to drop / add for the Report 1 systematic sweep?
5. **Status note** — Report 1 deadline (2026-05-29) acknowledged; Week 8 will
   begin writing.

- [ ] **Step 3: Verify all references exist before sending**

```powershell
rg -n "experiments/week7|docs/experiment_logs/week7|docs/experiment_logs/report1_evidence_index" docs/emails/week7_progress_to_philip_*.md
```

For each path mentioned, run `Test-Path` to confirm the file is on disk.
No broken links.

---

## Verification Before Completion

- [ ] Run all new Python tests:

```powershell
python -m pytest tests/py/test_drift_timeseries.py tests/py/test_pareto_full_example.py -q
```

- [ ] Run unchanged regression-report tests if report code changed:

```powershell
python -m pytest tests/py/test_float_regression_report.py tests/py/test_float_regression_report_device_mode.py -q
```

- [ ] Confirm no tracked large transient grids:

```powershell
git status --short
git ls-files experiments/week7 | rg "\.bin$"
```

Expected: no Week 7 `.bin` files tracked unless explicitly promoted as reference artefacts.

- [ ] Confirm solver numerics untouched:

```powershell
git diff -- src/euler src/gpu tests/cases
```

Expected: empty unless the user explicitly approved numerical or cfg changes.

- [ ] Confirm Week 6 G5 byte-identity baseline still holds:

Any optional `src/main.cpp` extension (Task 3 Step 0 checkpoint dump or Task 2
Step 4 metric helper *might* touch `main.cpp`) can silently break the
default-CPU stdout MD5 baseline that Week 6 closed.
Re-run the G5 record from `docs/week6/week6-verification.md`:

```powershell
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=OFF
cmake --build build-double --target hrsc
.\build-double\hrsc.exe tests/cases/toro_1d/sod.cfg > sod_post_week7_stdout.txt
Get-FileHash -Algorithm MD5 sod_post_week7_stdout.txt
```

Expected MD5: `FD58E1A9398178E54E5B761AE9D87959` (Week 6 baseline). If this
changes, the new code path is no longer opt-in — fix before merging.

---

## Execution Order Recommendation

1. **Task 2** first — fixes the wording risk in the current narrative;
   independent of everything else and the cheapest win.
2. **Task 5** — Philip explicitly asked for a full Pareto example (grep for
   existing rows before any rerun, per Task 5 Step 2).
3. **Task 1** — turns the Rusanov observation into interpretation, with the
   added supporting analysis from Step 4.
4. **Task 6** — prevents degenerate cases from corrupting pass/fail tables.
5. **Task 3** — start with Step 0 (checkpoint capability) before any matrix
   run; then Step 3b chaotic/extended pair. Use the full axis list directly
   (no need to wait on Philip — adjustments can land in next week's email).
6. **Task 4** — combined precision↔drift table; depends on Task 3 outputs.
7. **Task 7** — Week 7 operational plan + INDEX link.
8. **Task 8** — Report 1 evidence index; needs every Week-7 artefact on disk
   so it can be linked with its real path/state.
9. **Task 9** — end-of-week progress email to Philip, drafted last so it
   reports actual numbers and links real artefacts rather than promises.

This order keeps the supervisor in the loop *with results in hand* (Task 9 is
a single round-trip after the work lands) while running the highest-runtime
experiment work (Task 3 drift matrix) on Yudong's own schedule.
