# Report 1 Figure & Table Polish — Design Spec

**Date:** 2026-05-27
**Branch:** `report`
**Target manuscript:** `report1/phd-thesis-template-2.4/`
**Deadline:** 2026-05-29 (Report 1 due) — v1 (P0+P1+P2) within 3 days; v2 (+P3+P4+Final) within ≈1.5 more days
**Scope:** Style polish only for figures, tables, and captions. No data changes, no new figures, no solver/cfg/harness/experiment changes.
**Relation to prior plans:** Strictly downstream of and non-overlapping with `2026-05-26-report1-review3-revision-plan.md` (review3 — completed) and `report1/planning/review1_targeted_polish_serial_subagent_plan.md` (review1 — completed). Both prior plans' data and prose edits must be preserved verbatim.
**Reference input:** `c:/Users/tangy/Desktop/review.md` (a "desktop review" with concrete fig/table polish guidance; consulted but not blindly followed — its proposed new figures, e.g. MUSCL pipeline / propagation map / experimental matrix, are explicitly out of scope).

---

## 1. Scope, Non-Goals, Deliverables

### 1.1 In-scope (modified)

1. LaTeX preamble centralisation: `siunitx`, `booktabs`, 4-color palette macros, `\captionsetup` defaults.
2. New shared Python style module `scripts/figures/_style.py` and integration into existing `plot_*.py`.
3. 17 figures regenerated / restyled:
   - 14 PNG (matplotlib-generated, in Ch5 / Ch6) → re-run scripts under unified style → output **PDF + PNG** pair.
   - 3 TikZ (Ch3: finite-volume update, HLLC wave fan, MHD seven-wave fan) → recolor + line-width harmonisation only (no topology change).
4. 10 tables (Ch4 Tables 4.1–4.3; Ch5 Tables 5.1–5.6) restyled: uniform font, `S` column alignment via siunitx, double-row headers (quantity / condition), short caption + three-segment long caption.
5. All 17 figure captions + 10 table captions rewritten in three-segment form (bold lead-in · explanation · italic take-away).
6. LaTeX `\includegraphics` calls updated to drop file extensions so graphicx prefers the new PDF.

### 1.2 Out-of-scope (untouched)

1. Any experimental data, numeric values, or `summary.md` artefacts (review3 closed this loop).
2. New figures proposed by `review.md` (MUSCL–Hancock pipeline, precision-sensitive propagation map, matched CPU/GPU workflow, experimental matrix heatmap, regression harness diagram, CPU/CUDA layout schematic). Deferred to Report 2 or a later style v2.
3. Prose paragraphs: existing arguments, `\cite`, `\ref`, `\autoref` in main text must not be removed; only additive cross-references when caption gains information are allowed.
4. TikZ topology, node labels, equations, geometric layout (only `draw=`, `fill=`, line widths change).
5. Chapter / section ordering or titles.
6. Solver, cfg defaults, build harness, regression scripts under `scripts/regression/`, `tests/`, `src/`.
7. References / bibliography.

### 1.3 Deliverables

1. Edits to `report1/phd-thesis-template-2.4/Preamble/preamble.tex` (or whichever file the existing preamble lives in — verified at P0 start) adding the four palette `\definecolor` calls, `siunitx` setup, `caption` setup, and `\DeclareGraphicsExtensions{.pdf,.png,.jpg}`.
2. New file `scripts/figures/_style.py` (`apply()`, `PALETTE`, `CYCLE`, `DIVERGING_CMAP`, `SEQUENTIAL_CMAP`, `save_pair()`).
3. 14 figure pairs at `report1/phd-thesis-template-2.4/Figs/report1/<stem>.{pdf,png}`.
4. Restyled `\begin{table}...\end{table}` and `\begin{figure}...\end{figure}` blocks in `Chapter[3-6]/chapter*.tex`.
5. This spec at `docs/superpowers/specs/2026-05-27-report1-figtab-polish-design.md`.
6. Subsequent writing-plans output: `docs/superpowers/plans/2026-05-27-report1-figtab-polish.md`.
7. One commit per phase (P0 / P1 / P2 / P3 / P4 / Final) on `report` branch for clean per-phase revert.

### 1.4 Definition of Done

- `pdflatex` round-trip passes with no new unresolved `\ref` / `\cite`, no new `Overfull \hbox` exceeding 5pt.
- `texcount -inc -sum -1` delta vs the spec's start commit is within `[-10, +50]` words.
- All `\includegraphics` calls reference figures **without** file extensions.
- Every table uses `S` columns for numeric data; no `\setlength{\tabcolsep}{...}` survives in restyled blocks; no `\footnotesize` or `\scriptsize` survives in restyled blocks.
- All 27 captions (17 figure + 10 table) use the three-segment form (bold lead-in, explanation, italic take-away) with a short caption (`\caption[...]{...}`).
- Spot-check (5 randomly sampled figures + 3 tables) confirms palette, font size, and caption form consistency.

---

## 2. Phase 0 — Style Infrastructure

### 2.1 LaTeX preamble additions

Target file: `report1/phd-thesis-template-2.4/Preamble/preamble.tex` (verified at P0 start; if the template centralises in `Classes/PhDThesisPSnPDF.cls` instead, merge configuration there to avoid duplicate `\usepackage` calls).

```latex
% --- 4-color palette (review.md §6) ---
\definecolor{fpDarkBlue}{HTML}{1F4E79}   % fp64, CPU, HLLC
\definecolor{fpCyanGreen}{HTML}{2A9D8F}  % GPU, secondary accent
\definecolor{fpOrange}{HTML}{E76F51}     % fp32, highlight
\definecolor{fpGray}{HTML}{6C757D}       % reference, neutral

% --- siunitx for table number alignment ---
\usepackage{siunitx}
\sisetup{
  table-format            = 1.3e-2,
  table-number-alignment  = center,
  exponent-product        = \times,
  output-exponent-marker  = \ensuremath{\mathrm{e}},
  detect-weight           = true,
  detect-family           = true,
}

% --- caption style (three-segment lead-in) ---
\usepackage[font=small,labelfont=bf,labelsep=period,
            justification=justified,singlelinecheck=false]{caption}
\captionsetup[table]{position=top,skip=4pt}
\captionsetup[figure]{position=bottom,skip=6pt}
\captionsetup[subfigure]{labelformat=parens,labelsep=space,font=footnotesize}

% --- graphicx: prefer PDF over PNG when both exist ---
\DeclareGraphicsExtensions{.pdf,.png,.jpg}
```

Pre-flight: P0 sub-agent must `grep -nE '\\\\usepackage(\[.*\])?\\{(caption|siunitx|booktabs|xcolor)\\}'` across all `.tex`. If any of these is already loaded, merge the new options instead of re-`\usepackage`.

### 2.2 Python style module

New file: `scripts/figures/_style.py`

```python
"""Unified plot style for report1 figures (review.md §1, §6 palette)."""
import matplotlib as mpl
from cycler import cycler

PALETTE = {
    "fp64":  "#1F4E79",
    "fp32":  "#E76F51",
    "cpu":   "#1F4E79",
    "gpu":   "#2A9D8F",
    "hllc":  "#1F4E79",
    "rusanov": "#6C757D",
    "ref":   "#000000",
    "gray":  "#6C757D",
    "accent": "#9B2226",
}
CYCLE = ["#1F4E79", "#E76F51", "#2A9D8F", "#6C757D", "#9B2226"]
DIVERGING_CMAP = "RdBu_r"
SEQUENTIAL_CMAP = "viridis"

def apply():
    mpl.rcParams.update({
        "font.family":        "serif",
        "font.serif":         ["Latin Modern Roman", "DejaVu Serif"],
        "mathtext.fontset":   "cm",
        "axes.labelsize":     10,
        "axes.titlesize":     10,
        "xtick.labelsize":    9,
        "ytick.labelsize":    9,
        "legend.fontsize":    9,
        "legend.frameon":     False,
        "axes.linewidth":     0.8,
        "lines.linewidth":    1.3,
        "lines.markersize":   4,
        "grid.linewidth":     0.5,
        "grid.alpha":         0.4,
        "savefig.dpi":        200,
        "savefig.bbox":       "tight",
        "savefig.pad_inches": 0.02,
        "axes.prop_cycle":    cycler(color=CYCLE),
        "image.cmap":         SEQUENTIAL_CMAP,
    })

def save_pair(fig, stem, outdir):
    fig.savefig(f"{outdir}/{stem}.pdf")
    fig.savefig(f"{outdir}/{stem}.png", dpi=200)
```

Integration contract: every `plot_*.py` referenced in Section 4 (P2) adds at top:

```python
from _style import apply, PALETTE, DIVERGING_CMAP, save_pair
apply()
```

Any pre-existing `mpl.rcParams[...] = ...` or `plt.rc(...)` calls in those scripts are removed unless they set figure-specific size (`figure.figsize`).

### 2.3 P0 acceptance

- `pdflatex thesis.tex` builds without new errors after preamble edits.
- `python -c "import _style; _style.apply()"` runs without ImportError or FontWarning (FontWarning to DejaVu Serif fallback is accepted; documented in §6 R1).
- One demo figure (`drift_timeseries_l1_selected`) regenerated under the new style for visual sanity; no commit yet — kept locally.

---

## 3. Phase 1 — Tables (10)

### 3.1 Per-table changes

Each restyled `\begin{table}` block obeys all rules below; data rows preserved bit-for-bit from the post-review3 state.

- Drop `\footnotesize` / `\scriptsize` / `\setlength{\tabcolsep}{...}`; set `\small`.
- All numeric columns become `S[table-format=...]`; pick `table-format` per column to match the largest magnitude actually present.
- Two-row header: top row = symbol / quantity, bottom row in italic = grid / unit / condition. Separate with `\midrule` (not `\cmidrule`).
- Add `\addlinespace[2pt]` between header and first data row.
- Caption rewritten in three segments via `\caption[...]{...}`:

```latex
\caption[<short caption ≤ 12 words>]{\textbf{<Lead-in title>.}
  <Explanation sentence(s): what each column means, how metrics are
  defined, the reference, the grid, the time, the precision.>
  \emph{<Single-sentence take-away for this report.>}}
```

### 3.2 Table inventory

| Table | Chapter / section | Restyle items | Data preserved from |
|---|---|---|---|
| Table 4.1 | Ch4 §"Test-Case Matrix and Metrics" | header + S cols + caption + Algo 1 caption left untouched aside from review3's CFL line | review3 |
| Table 4.2 | Ch4 §"Reference-Solution Strategy" | S cols + caption | review3 |
| Table 4.3 | Ch4 §"Precision and Hardware Variants" | S cols + caption (review3 GPU-timing prose around it stays) | review3 |
| Table 5.1 | Ch5 §"One-Dimensional Euler Validation" | drop `\footnotesize \tabcolsep=3pt` → `\small`; S cols; caption | review3 |
| Table 5.2 | Ch5 §"One-Dimensional Euler Validation" | same | review3 |
| Table 5.3 | Ch5 §"One-Dimensional Euler Validation" | double-row header (as in mockup B); S cols; caption | review3 |
| Table 5.4 | Ch5 §"Two-Dimensional Euler Validation" | S cols; caption; **review3 LW12 self-conv rows unchanged** | review3 |
| Table 5.5 | Ch5 §"Matched CPU/GPU Comparison" | S cols; caption; **review3 footnote unchanged in content; reformatted to 3-segment** | review3 |
| Table 5.6 | Ch5 §"Compiler, Branch, Solver, and Drift-Growth Sensitivity" | S cols; caption; **review3 branch-rule row unchanged** | review3 |
| Algorithm 1 caption | Ch4 §"Algorithmic Structure of the Implementation" | three-segment caption only; **review3 CFL line preserved** | review3 |

### 3.3 P1 acceptance

- `grep -n '\\\\footnotesize\|\\\\scriptsize\|\\\\setlength{\\\\tabcolsep}' Chapter*/chapter*.tex` returns 0 hits inside `\begin{table}...\end{table}` blocks.
- Every `\begin{table}` has `\caption[...]{...}` (short caption present) and `\textbf{` within 80 characters of `\caption{`.
- `pdflatex` builds with at most existing overfull warnings (no new ones > 5pt).
- Numeric row values: random spot-check of 3 cells against the source `summary.md` / `reference_scaled_ratios.csv`. Zero discrepancies.

---

## 4. Phase 2 — PNG Figures (14)

### 4.1 Per-figure regeneration contract

Every script in §4.3 below:

1. Imports `_style` at top, calls `apply()`.
2. Removes any `plt.rc(...)` / `mpl.rcParams[...] = ` that overrides global style (figure-size overrides allowed).
3. Maps colors via `PALETTE` semantic keys — not literal hex inline.
4. For diverging fields (fp32–fp64 differences, signed deltas): uses `DIVERGING_CMAP` with `vmin = -vmax`.
5. For sequential fields (noise, error, ratio): uses `SEQUENTIAL_CMAP` (viridis).
6. Calls `save_pair(fig, stem, outdir)` with `outdir = report1/phd-thesis-template-2.4/Figs/report1`.

### 4.2 Width tiers (LaTeX side)

| Figure role | `width=` |
|---|---|
| 1D physical-variable comparison (Sod/Toro3/Toro5) | `0.85\textwidth` |
| 2D schlieren / colormap | `\textwidth` |
| Bar / single-variable comparison | `0.7\textwidth` |
| subfigure inside `\begin{figure}` | `\textwidth` of subfigure |

All `\includegraphics` calls drop file extensions: `\includegraphics[width=0.85\textwidth]{Figs/report1/sigma_fp_vs_precision}`.

### 4.3 Figure inventory

| Stem | Generating script | Key style change |
|---|---|---|
| `sod_comparison`, `toro3_comparison`, `toro5_comparison` | `scripts/figures/<existing-1d-comparison>.py` (located at P2 start by grep) | fp64 = `#1F4E79`, fp32 = `#E76F51`, exact reference = black dashed; unified legend (top-right, frame off) |
| `lw3_n400_double_rho_schlieren`, `lw12_n400_double_rho_schlieren` | `scripts/figures/<2d-schlieren>.py` | viridis cmap; colorbar label `density (-)`; square axes |
| `lw12_n400_fp32_minus_fp64_rho` | same family as 2D schlieren, signed-difference branch | **RdBu_r diverging, `vmin = -vmax`**; centered colorbar at 0 |
| `float_double_over_reference_bar` | `scripts/figures/<bar>.py` | 4-color bars; semilog-y; reference baseline `fpGray` dashed |
| `density_hllc_vs_rusanov_200`, `pressure_hllc_vs_rusanov_200` | `scripts/figures/<hllc-rusanov>.py` | HLLC = `fpDarkBlue` solid, Rusanov = `fpGray` solid; identical axis ranges between density and pressure variants |
| `drift_timeseries_l1`, `drift_timeseries_l1_normalized`, `drift_timeseries_l1_selected` | `scripts/figures/report1_d2_replots.py` (or sibling — verified at P2 start) | semilog-y; first four cases from `CYCLE`; selected variant uses 3 emphasised lines + grey context |
| `vfc_sod_overlay` | `scripts/figures/<vfc>.py` | 4-color cycle |
| `sigma_fp_vs_precision` | `scripts/figures/report1_d2_replots.py` | HLLC = `fpDarkBlue`, Rusanov = `fpGray`; x = virtual precision label; y = semilog `σ_FP,L1`; **n=30 data from review3 preserved bit-for-bit** |
| `losos_quantiles_rho` | same | q05 / q25 / median rendered at three alpha levels on same color per solver |
| `region_losos_margin_rho_p32` | same | three-region semantic colors (smooth = `fpDarkBlue`, transition = `fpCyanGreen`, shock = `fpOrange`) |
| `noise_to_error_ratio_heatmap_grid_rho` | same | viridis; shared colorbar across panels (max over the grid) |
| `region_noise_to_error_ratio_precision_grid_rho` | same | viridis; shared colorbar |

Any script the P2 sub-agent cannot locate is reported up — the figure stays as the existing PNG (and a `.pdf` is generated via `magick convert <png> <pdf>` only as a last-resort PDF wrapper). This fallback path does not change colors and is recorded as a known limitation in §6.

### 4.4 LaTeX-side change

After P2 produces the new PDFs, update every `\includegraphics{Figs/report1/<stem>.png}` to `\includegraphics{Figs/report1/<stem>}` (drop extension). The `\DeclareGraphicsExtensions{.pdf,.png}` setting then prefers the new PDF; if it doesn't exist (fallback case), graphicx falls back to PNG cleanly.

### 4.5 P2 acceptance

- For every stem in §4.3, both `<stem>.pdf` and `<stem>.png` exist with mtime ≥ the P2 sub-agent's start time.
- `grep -nE 'includegraphics.*\\.png\}' Chapter*/chapter*.tex` returns 0 hits.
- `pdflatex` builds with no new "File not found" warnings.
- Visual spot-check on 3 randomly drawn `<stem>.pdf` files: serif font, palette colors present, no rainbow/jet colormap.
- Old PNGs that are replaced by new PNG + PDF are kept (git-tracked), so the diff documents the change; no `git rm` in P2.

---

## 5. Phase 3 — TikZ Recolor (Ch3, 3 figures) · Phase 4 — Captions (27)

### 5.1 P3 — TikZ

Targets in `Chapter3/chapter3.tex`:

| TikZ figure | Line range hint (verify at P3 start) | Restyle |
|---|---|---|
| Finite-volume conservative update (Fig 3.1) | line ≈ 72 | main cell / flux arrows: `fpDarkBlue, line width=1.2pt`; reference axes: `fpGray, line width=0.6pt` |
| HLLC wave fan (Fig 3.2) | line ≈ 235 | shock waves: `fpDarkBlue`; contact: `fpGray`; star-state highlight: `fpOrange`; main lines 1.2 pt, light dashes 0.6 pt |
| MHD seven-wave fan (Fig 3.3) | line ≈ 528 | fast magnetosonic: `fpDarkBlue`; Alfvén: `fpCyanGreen`; slow magnetosonic: `fpOrange`; entropy/contact: `fpGray`; line widths same scheme |

Constraints:

- No node moves, no label-text changes, no equation edits, no new annotations.
- All literal `red`, `blue`, `black!50`, `red!50` inside the three TikZ blocks are replaced by the four palette macros.
- Add `every node/.style={font=\small}` only if existing nodes mix sizes.

### 5.2 P4 — Captions (17 figure + 10 table)

Apply the three-segment template uniformly:

```latex
\caption[<short caption>]{\textbf{<Lead-in title>.}
  <Explanation: what is shown, definitions, conditions, color/marker
  meaning, reference / data source.>
  \emph{<Single-sentence take-away or interpretive hook.>}}
```

Information migration rule (review.md "把信息从原文解放"):

- **Allowed to add to caption**: variable definitions, condition (N, t, precision), reference source, color / marker semantics, ROI markers, definitions of error metrics.
- **Forbidden to remove from prose**: any `\cite`, `\ref`, `\autoref`, or argumentative sentence in main text. Only additive cross-references when caption gains information are allowed.
- **Forbidden to duplicate**: do not copy-paste main-text sentences verbatim into the caption — extend or define, do not echo.

Subfigure-aware form (used for `fig:ch6-losos-combined`):

```latex
\begin{figure}[t]
  \centering
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{Figs/report1/losos_quantiles_rho}
    \subcaption{<short subcaption>}
    \label{fig:ch6-losos-quantiles}
  \end{subfigure}\hfill
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{Figs/report1/region_losos_margin_rho_p32}
    \subcaption{<short subcaption>}
    \label{fig:ch6-region-losos}
  \end{subfigure}
  \caption[<short outer caption>]{\textbf{<Lead-in>.}
    <Explanation covering both panels and how they relate.>
    \emph{<Take-away.>}}
  \label{fig:ch6-losos-combined}
\end{figure}
```

### 5.3 P3 + P4 acceptance

- TikZ blocks: `grep -nE '(draw|fill)=(red|blue|green|black!|red!|blue!)' Chapter3/chapter3.tex` returns 0 hits inside the three target figures.
- `grep -nE 'line width=[0-9]' Chapter3/chapter3.tex` returns only `1.2pt` or `0.6pt` (or `thick`/`thin` aliases) inside the three target figures.
- For every `\begin{figure}` and `\begin{table}` in `Chapter[3-6]/chapter*.tex`:
  - `\caption[...]{...}` form is present (short caption non-empty);
  - within 80 characters of `\caption{`, both `\textbf{` and `\emph{` appear (regex-checkable).
- `pdflatex` builds clean.
- `texcount` delta from baseline is within `[-10, +50]` words.

---

## 6. Risks and Mitigations

| ID | Risk | Mitigation |
|---|---|---|
| R1 | matplotlib has no Latin Modern Roman → fallback to DejaVu Serif visible | Accepted; final thesis PDF still embeds the same backend font for all figures, so internal consistency holds. v2 can switch to `pgf` backend if external review flags it. |
| R2 | siunitx column widths cause `Overfull \hbox` in restyled tables | Monitor each P1 commit's pdflatex log; per-column `S[table-format=...]` cap to match actual data. |
| R3 | graphicx picks new PDF over old PNG silently — but old PNG could be picked if PDF generation fails | P2 sub-agent verifies both files exist before stripping extensions; if PDF missing for any stem, the LaTeX call retains `.png` until fallback resolves. |
| R4 | Per-script `plt.rc(...)` overrides global `_style.apply()` | P2 sub-agent removes such overrides; figure-specific size overrides via `plt.subplots(figsize=...)` are allowed. |
| R5 | Figure regeneration accidentally re-reads or re-writes `summary.md` / `experiments/` artefacts | P2 sub-agent contract: scripts only read inputs; any write outside `Figs/report1/` aborts the phase. |
| R6 | review3 data in Tables 5.4 / 5.5 / 5.6 overwritten during restyling | P1 sub-agent `git diff` after each table; only header rows / column types / caption changes accepted. Data rows must `git diff` clean. |
| R7 | TikZ `\definecolor` macros not loaded by preamble at P3 time → compile error | P3 sub-agent pre-checks that `fpDarkBlue` etc. resolve in preamble before editing TikZ blocks. |
| R8 | Caption information migration drops a `\cite` or `\autoref` in main text | P4 sub-agent contract: never delete `\cite`, `\ref`, `\autoref` in prose; only add. After P4, grep for previously-present citation keys; counts must not decrease. |
| R9 | The script source for some `.png` cannot be located (older / lost) | Fallback PDF wrapper via `magick convert`; figure keeps current colors. Logged as a known limitation in the spec's open-questions section if it actually happens. |
| R10 | Three-day v1 timeline slips due to siunitx setup churn | P0 has a 0.5-day budget; if it overruns past 1 day, defer P3+P4 and ship v1 with only P0+P1+P2. |

---

## 7. Workflow

Same shape as the review3 plan: serial sub-agents, main-process audit between phases.

### 7.1 Sub-agent envelope (per phase)

1. Phase goal (one paragraph) and exact file paths to edit.
2. Pointer to this spec (`docs/superpowers/specs/2026-05-27-report1-figtab-polish-design.md`) and `scripts/figures/_style.py` (for P2+).
3. Hard constraints: palette hex values, font sizes, caption template, forbidden tokens.
4. Things explicitly out-of-scope for this phase (e.g. P1 must not touch any figure file).
5. Acceptance commands the sub-agent runs and reports back.
6. Stop condition on any mismatch — never silently "best-effort".

### 7.2 Main-process audit (after each phase)

- `pdflatex thesis.tex` clean build, no new errors / unresolved refs.
- `texcount -inc -sum -1` delta against the spec's start baseline within `[-10, +50]`.
- Phase-specific grep checks listed in §3.3 / §4.5 / §5.3.
- Visual spot-check (3–5 samples).
- `git diff --stat` reviewed for unintended files / line ranges.
- Commit (squash sub-agent commits if any) with message `report1 figtab polish: <phase>`.

### 7.3 Phase order, time budget, word-delta budget

| # | Phase | Depends on | Time | texcount delta |
|---|---|---|---|---|
| P0 | LaTeX preamble + `_style.py` | — | 0.5 d | 0 |
| P1 | 10 tables restyled + table captions | P0 | 1 d | +20 / −0 |
| P2 | 14 PNG regenerated + LaTeX `\includegraphics` extension drop | P0 | 1 d | 0 |
| P3 | 3 TikZ recolor + line-width unify | P0 | 0.5 d | 0 |
| P4 | 17 figure captions in three-segment form (with allowed info migration) | P2, P3 | 0.5 d | +20 / −0 |
| Final | Compile, audit, commit cleanup | all | 0.5 d | net within `[-10, +50]` |

v1 cut: P0 + P1 + P2 — three days, delivers the dominant visual uplift.
v2 cut: + P3 + P4 + Final — additional 1.5 days, completes the spec.

---

## 8. Interaction with Prior and Concurrent Plans

| Prior plan | What it changed | This plan's interaction |
|---|---|---|
| `2026-05-26-report1-review3-revision-plan.md` (complete) | Data and prose in Ch3 / Ch4 / Ch5 / Ch6 / Ch7 + 5 Ch6 figures refreshed to n=30 + Table 5.4 / 5.5 / 5.6 data updates | Style only; preserves all review3 prose, data rows, and the n=30 figure data. We restyle the n=30 figures' visual settings while reading the same underlying outputs. |
| `report1/planning/review1_targeted_polish_serial_subagent_plan.md` (complete) | Structural and argumentative additions | No overlap; this plan does not touch prose. |
| Supervisor feedback | Content-level (FMA, branch rule, mixed precision, etc.) | Already addressed by review1 / review3 / earlier; this plan does not address content gaps. |

The "do-not" list from review3 §7 applies in full (no fp32 = fp64 identity claim, no CPU/GPU bit-identity beyond saved state, no LW12 asymptotic-convergence claim, etc.). This plan does not introduce or remove any such claim — it only restyles the surfaces that present them.

---

## 9. Open Questions (to confirm at execution start)

1. The single file (`Preamble/preamble.tex` vs `Classes/PhDThesisPSnPDF.cls`) that should host the new `\definecolor` / siunitx / caption setup — verified by P0 sub-agent before editing.
2. Whether system has Latin Modern Roman installed for matplotlib (no: accepted DejaVu Serif fallback; documented in R1).
3. Whether `magick`/`convert` is available for the §4.3 fallback path (only relevant if any figure script cannot be located).

---

**This spec is read-only. No edits to `report1/phd-thesis-template-2.4/` or `scripts/figures/` are performed by this document. Execution is sequenced by the writing-plans output that follows.**
