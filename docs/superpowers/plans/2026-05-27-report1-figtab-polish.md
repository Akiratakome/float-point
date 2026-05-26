# Report 1 Figure & Table Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish all 17 figures, 10 tables, and 27 captions in `report1/phd-thesis-template-2.4/` to top-tier journal style. No data changes, no new figures, no solver/cfg/harness edits.

**Architecture:** Staged five-phase rollout — P0 builds shared LaTeX/Python style infrastructure (4-color palette, siunitx, three-segment caption macros, matplotlib rc-style module). P1 restyles all tables. P2 regenerates all PNGs under unified matplotlib style, outputting `.pdf + .png` pairs. P3 recolors three Ch3 TikZ figures. P4 rewrites all figure captions in three-segment form. Each phase commits separately for clean revert. v1 cut = P0+P1+P2 (3 days); v2 cut = +P3+P4+Final (1.5 days).

**Tech Stack:** LaTeX (booktabs, siunitx, caption, subcaption, tikz, xcolor — all already in preamble), Python 3 matplotlib, git on branch `report`, PowerShell on Windows + WSL bash.

**Spec:** `docs/superpowers/specs/2026-05-27-report1-figtab-polish-design.md`

**Pre-flight verified facts:**
- Preamble file: `report1/phd-thesis-template-2.4/Preamble/preamble.tex`
- `siunitx`, `booktabs`, `subcaption`, `tikz` already `\usepackage`'d (lines 76, 79, 87, 91)
- `caption`, `xcolor` NOT yet loaded — must be added
- 14 `\includegraphics{...png}` occurrences in Ch5 (9) and Ch6 (5) to be stripped of extension
- Existing figure scripts under `scripts/figures/`: `plot_2d.py`, `plot_drift_timeseries.py`, `plot_hllc_rusanov_points.py`, `plot_stationary_contact_vfc.py`, `plot_vfc_hllc_vs_rusanov.py`, `report1_d2_replots.py`

---

## Phase P0 — Style Infrastructure

### Task P0.1: Add palette + sisetup + captionsetup + graphics-extensions to preamble

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Preamble/preamble.tex` (append after existing `\usepackage{siunitx}` on line 91 and after `\usepackage{tikz}` on line 87)

- [ ] **Step 1: Snapshot baseline texcount and pdf hash**

```powershell
cd report1/phd-thesis-template-2.4
texcount -inc -sum -1 thesis.tex | Out-File ../../docs/superpowers/plans/.figtab-baseline-texcount.txt
Get-FileHash thesis.pdf -Algorithm SHA256 | Out-File ../../docs/superpowers/plans/.figtab-baseline-pdfhash.txt
cd ../..
```

Save these two paths — used by Final phase to confirm word-count delta and document baseline pdf.

- [ ] **Step 2: Append style block to preamble.tex after line 91**

Insert the following block immediately after the existing `\usepackage{siunitx}` line in `report1/phd-thesis-template-2.4/Preamble/preamble.tex`:

```latex
% ============== Report 1 figure/table polish style ==============
% 4-color palette (review.md §6 + spec §2.1)
\usepackage{xcolor}
\definecolor{fpDarkBlue}{HTML}{1F4E79}   % fp64, CPU, HLLC
\definecolor{fpCyanGreen}{HTML}{2A9D8F}  % GPU, secondary
\definecolor{fpOrange}{HTML}{E76F51}     % fp32, highlight
\definecolor{fpGray}{HTML}{6C757D}       % reference, neutral

% siunitx alignment for tables
\sisetup{
  table-format            = 1.3e-2,
  table-number-alignment  = center,
  exponent-product        = \times,
  output-exponent-marker  = \ensuremath{\mathrm{e}},
  detect-weight           = true,
  detect-family           = true,
}

% Caption style (three-segment lead-in)
\usepackage[font=small,labelfont=bf,labelsep=period,%
            justification=justified,singlelinecheck=false]{caption}
\captionsetup[table]{position=top,skip=4pt}
\captionsetup[figure]{position=bottom,skip=6pt}
\captionsetup[subfigure]{labelformat=parens,labelsep=space,font=footnotesize}

% Prefer PDF over PNG for figure inclusion
\DeclareGraphicsExtensions{.pdf,.png,.jpg}
% =================================================================
```

- [ ] **Step 3: Build pdflatex round-trip to confirm preamble compiles**

```powershell
cd report1/phd-thesis-template-2.4
.\compile-thesis-windows.bat
# or on WSL: bash compile-thesis.sh
cd ../..
```

Expected: thesis.pdf rebuilds with no new errors. Warnings about already-loaded packages may appear if `caption` was implicitly pulled by another package — if so, drop the explicit `\usepackage[...]{caption}` and rely on `\captionsetup[...]` directly. Confirm by reading `thesis.log` for `LaTeX Error`.

- [ ] **Step 4: Commit P0.1**

```bash
git add report1/phd-thesis-template-2.4/Preamble/preamble.tex
git commit -m "report1 figtab P0: add palette + sisetup + captionsetup to preamble"
```

### Task P0.2: Create scripts/figures/_style.py

**Files:**
- Create: `scripts/figures/_style.py`

- [ ] **Step 1: Write the file**

```python
"""Unified plot style for report1 figures.

Usage in any plot_*.py:
    from _style import apply, PALETTE, DIVERGING_CMAP, save_pair
    apply()
    ...
    save_pair(fig, "stem", outdir)

Palette references review.md §6 / spec §2.2.
"""
import matplotlib as mpl
from cycler import cycler

PALETTE = {
    "fp64":    "#1F4E79",
    "fp32":    "#E76F51",
    "cpu":     "#1F4E79",
    "gpu":     "#2A9D8F",
    "hllc":    "#1F4E79",
    "rusanov": "#6C757D",
    "ref":     "#000000",
    "gray":    "#6C757D",
    "accent":  "#9B2226",
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
    """Save both PDF (preferred) and PNG (backup) so LaTeX graphicx picks PDF."""
    import os
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(f"{outdir}/{stem}.pdf")
    fig.savefig(f"{outdir}/{stem}.png", dpi=200)
```

- [ ] **Step 2: Smoke test — import and apply without error**

```powershell
cd scripts/figures
python -c "from _style import apply, PALETTE, save_pair; apply(); print('ok:', PALETTE['fp64'])"
cd ../..
```

Expected output:
```
ok: #1F4E79
```

If `FontWarning` about Latin Modern Roman appears, ignore — DejaVu Serif fallback is acceptable per spec §6 R1.

- [ ] **Step 3: Commit P0.2**

```bash
git add scripts/figures/_style.py
git commit -m "report1 figtab P0: add scripts/figures/_style.py shared style module"
```

---

## Phase P1 — Tables (10)

Each table follows the spec §3.1 rules: `\small`, no `\setlength{\tabcolsep}`, `S[table-format=...]` columns, double-row header (top = quantity, bottom italic = condition), three-segment caption with short caption.

**Caption template** (use for every table caption):

```latex
\caption[<short caption ≤ 12 words>]{\textbf{<Lead-in title>.}
  <Explanation: column definitions, references, conditions.>
  \emph{<One-sentence take-away.>}}
```

### Task P1.1: Restyle Tables 4.1, 4.2, 4.3, and Algorithm 1 caption (Chapter 4)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex` (table blocks at lines ≈ 146, 233, 267; Algorithm 1 caption around line 50–100 — verify at task start)

- [ ] **Step 1: Read the current chapter to confirm line ranges and table content**

```powershell
# locate all \begin{table}, \begin{algorithm}, and Algorithm 1 caption in Ch4
grep -n -E "\\\\begin\\{table\\}|\\\\begin\\{algorithm\\}|\\\\caption" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Save the line numbers for the three tables and the Algorithm 1 caption.

- [ ] **Step 2: Restyle Table 4.1**

Rules:
1. Replace `\footnotesize`/`\scriptsize` (if any) with `\small`.
2. Remove any `\setlength{\tabcolsep}{...}`.
3. Convert `c`/`l` numeric columns to `S[table-format=…]` where data is numeric.
4. Restructure header to two rows: top = symbol, bottom = `\itshape` condition.
5. Rewrite `\caption{...}` → `\caption[short]{\textbf{Lead-in.} explanation. \emph{take-away.}}`.
6. **Data rows untouched** — diff after restyle should show only column-type / header / caption changes.

- [ ] **Step 3: Restyle Table 4.2 — same rules**

- [ ] **Step 4: Restyle Table 4.3 — same rules**

Special case: Table 4.3's surrounding paragraph contains review3-added GPU-timing prose (8.53 s / 0.57 s on RTX 5090). Leave prose unchanged; only restyle the table itself.

- [ ] **Step 5: Rewrite Algorithm 1 caption**

Algorithm captions use `\caption` inside `\begin{algorithm}`. Apply the same three-segment form. **Preserve verbatim** the review3-added CFL line: "The CFL coefficient is fixed per case: `C_CFL = 0.8` for 1D tests, `C_CFL = 0.5` for LW3, `C_CFL = 0.4` for LW12."

- [ ] **Step 6: Verify forbidden tokens absent inside Ch4 table blocks**

```powershell
# inside Chapter4/chapter4.tex, between each \begin{table} and \end{table},
# expect 0 hits for \footnotesize, \scriptsize, \setlength{\tabcolsep}
grep -n -E "\\\\footnotesize|\\\\scriptsize|\\\\setlength\\{\\\\tabcolsep" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Each remaining hit must be **outside** a `\begin{table}` block (e.g. in a tikz figure or text). If any hit is inside a table, return and remove.

- [ ] **Step 7: pdflatex check**

```powershell
cd report1/phd-thesis-template-2.4
.\compile-thesis-windows.bat
cd ../..
```

Expected: clean build, no new "Undefined column type S" (means siunitx loaded), no new `Overfull \hbox` > 5pt. If a single column overflows, narrow its `table-format` (e.g. `1.2e-2` → `1.1e-2`).

- [ ] **Step 8: Commit P1.1**

```bash
git add report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
git commit -m "report1 figtab P1: restyle Ch4 Tables 4.1-4.3 + Algorithm 1 caption"
```

### Task P1.2: Restyle Tables 5.1, 5.2, 5.3 (Chapter 5, 1D)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` (line ≈ 54, 81, 107 — verify)

- [ ] **Step 1: Restyle Table 5.1 (1D exact-reference density convergence)**

Apply the template from the mockup we approved during brainstorming. Existing data rows (Sod / Toro3 / Toro5) must remain numerically identical. Recommended `S[table-format=1.6e-2]` for the four error columns and `S[table-format=1.2]` for the `p_{400→800}` column.

- [ ] **Step 2: Restyle Table 5.2 (1D feature-location and density-error split)**

`S[table-format=1.6e-2]` for the four error columns; `S[table-format=1.3]` for band fraction.

- [ ] **Step 3: Restyle Table 5.3 (1D precision and device summary)**

This is the table whose target form was approved as mockup B. Concrete LaTeX:

```latex
\begin{table}[t]
\centering
\small
\begin{tabular}{@{}lSSc@{}}
\toprule
\multirow{2}{*}{Case}
  & {$\|U_{\mathrm{fp64}}-U_{\mathrm{fp32}}\|_1$}
  & {$R_\rho^{\mathrm{exact}}$}
  & {CPU/GPU drift} \\
  & \itshape $N=200$ & \itshape $N=800$ & \itshape $L_1/L_\infty/\mathrm{ULP}_{\max}$ \\
\midrule \addlinespace[2pt]
Sod   & 8.74e-8 & 1.06e-4 & {0 / 0 / 0} \\
Toro3 & 6.39e-5 & 1.36e-5 & {0 / 0 / 0} \\
Toro5 & 1.30e-4 & 3.91e-5 & {0 / 0 / 0} \\
\bottomrule
\end{tabular}
\caption[One-dimensional precision and device summary]{\textbf{One-dimensional precision and device summary.}
  Column 2 is the conservative-state fp64–fp32 final-state $L_1$ at $N=200$;
  column 3 is the density reference-scaled ratio
  $R_\rho^{\mathrm{exact}} = \|\rho_{\mathrm{fp32}}-\rho_{\mathrm{fp64}}\|_1
  / \|\rho_{\mathrm{fp64}}-\rho_{\mathrm{exact}}\|_1$ at $N=800$;
  column 4 reports saved-state drift $L_1 / L_\infty / \mathrm{ULP}_{\max}$
  between matched strict-IEEE CPU and GPU HLLC outputs.
  \emph{fp32–fp64 perturbation stays below the discretisation-error scale,
  and matched-binary CPU/GPU differences are zero for every tested case.}}
\label{tab:ch5-1d-summary}
\end{table}
```

Notes: braces `{...}` around `0 / 0 / 0` keep siunitx from trying to parse it; if `multirow` is loaded (it is, line 80 of preamble), `\multirow{2}{*}{Case}` works.

- [ ] **Step 4: pdflatex check**

```powershell
cd report1/phd-thesis-template-2.4
.\compile-thesis-windows.bat
cd ../..
```

Expected: clean. If `Undefined control sequence \multirow` — confirm preamble's `\usepackage{multirow}` (line 80) survived.

- [ ] **Step 5: Commit P1.2**

```bash
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "report1 figtab P1: restyle Ch5 Tables 5.1-5.3 (1D)"
```

### Task P1.3: Restyle Table 5.4 (Chapter 5, 2D summary — review3 LW12 rows MUST be preserved)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` (line ≈ 184)

- [ ] **Step 1: Snapshot the existing data rows**

Before editing, save the six existing data rows (LW3 / LW12 against fp64 ref + LW12 self-conv rows) so they can be diffed byte-for-byte against the result.

- [ ] **Step 2: Restyle header + columns + caption only**

Column types become `lll S[table-format=1.2e-2] S[table-format=1.4] S[table-format=1.2e-2] S[table-format=1.2e-2]`. Header re-organised as `Case / reference / grid` on top row, and the four numeric column headers each get italic units (`L_1` units, `dimensionless`, etc.) on the second row.

- [ ] **Step 3: Confirm no data row was changed**

```powershell
git diff report1/phd-thesis-template-2.4/Chapter5/chapter5.tex | Select-String -Pattern "^[-+]\s+(LW3|LW12)" 
```

For each `+` line there must be a matching `-` line with identical numeric content (only column-separator changes acceptable). If any number differs, revert.

- [ ] **Step 4: pdflatex check + commit P1.3**

```powershell
cd report1/phd-thesis-template-2.4 ; .\compile-thesis-windows.bat ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "report1 figtab P1: restyle Ch5 Table 5.4 (2D, review3 data preserved)"
```

### Task P1.4: Restyle Table 5.5 (Matched CPU/GPU coverage — review3 footnote preserved)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` (line ≈ 286)

- [ ] **Step 1: Identify the review3-added footnote text**

The footnote (per review3 §3.10) starts "Toro3 and Toro5 are reported here from the CSC strict-IEEE rerun…". Copy this paragraph verbatim into the new caption's "explanation" segment — do not paraphrase.

- [ ] **Step 2: Restyle and write three-segment caption**

Caption pattern:
```latex
\caption[Matched CPU/GPU saved-state coverage]{\textbf{Matched CPU/GPU saved-state coverage.}
  <verbatim review3 footnote text, slightly reflowed if needed>.
  \emph{All five cases show $L_1 = L_\infty = \mathrm{ULP}_{\max} = 0$ between matched
  strict-IEEE CPU and GPU saved outputs, with no exception in fp64 or fp32.}}
```

- [ ] **Step 3: pdflatex check + commit P1.4**

```powershell
cd report1/phd-thesis-template-2.4 ; .\compile-thesis-windows.bat ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "report1 figtab P1: restyle Ch5 Table 5.5 (CPU/GPU, review3 footnote preserved)"
```

### Task P1.5: Restyle Table 5.6 (Variation matrix — review3 branch-rule row preserved)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex` (line ≈ 346)

- [ ] **Step 1: Restyle header + column types only**

Replace the existing header with two-row form. Numeric columns become `S[table-format=...]`. Data rows including review3's expanded branch-rule row stay identical text-for-text.

- [ ] **Step 2: Rewrite caption to three-segment form**

- [ ] **Step 3: pdflatex check + commit P1.5**

```powershell
cd report1/phd-thesis-template-2.4 ; .\compile-thesis-windows.bat ; cd ../..
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "report1 figtab P1: restyle Ch5 Table 5.6 (variation matrix, review3 row preserved)"
```

### Task P1.6: P1 acceptance audit

- [ ] **Step 1: Forbidden-token grep (must be 0 inside table blocks)**

```powershell
grep -n -E "\\\\footnotesize|\\\\scriptsize|\\\\setlength\\{\\\\tabcolsep" report1/phd-thesis-template-2.4/Chapter[34]/chapter*.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex | Select-String -NotMatch "Chapter5\.tex:4[0-9][0-9]"
```

Inspect each remaining hit — must be **outside** any `\begin{table}...\end{table}` block. If inside, return.

- [ ] **Step 2: Caption-form grep (every table must have short + three-segment caption)**

```powershell
# every \begin{table} should be followed within ~30 lines by \caption[..]{\textbf{..} ..\emph{..}}
grep -n -B1 -A30 "begin{table}" report1/phd-thesis-template-2.4/Chapter[345]/chapter*.tex | grep -E "caption\[.*\]\{\\\\textbf"
```

Count must be 10 (3 Ch4 tables + 6 Ch5 tables + 1 Algorithm 1 caption may not match the `\begin{table}` filter — count it separately).

- [ ] **Step 3: texcount delta**

```powershell
cd report1/phd-thesis-template-2.4
texcount -inc -sum -1 thesis.tex
cd ../..
# manual compare against .figtab-baseline-texcount.txt; expect delta in [-10, +50]
```

- [ ] **Step 4: Read 1 random new table block end-to-end to confirm form**

Pick e.g. Table 5.4 by `Read` and visually confirm: `\small`, S columns, two-row header, three-segment caption, no `\setlength`, no `\footnotesize`.

---

## Phase P2 — PNG Figure Regeneration (14)

### Task P2.1: Inventory generating scripts vs figure stems

**Files:**
- Read-only: `scripts/figures/*.py`, `report1/phd-thesis-template-2.4/Figs/report1/*.png`

- [ ] **Step 1: List PNGs currently in Figs/report1**

```powershell
ls report1/phd-thesis-template-2.4/Figs/report1/*.png | ForEach-Object { $_.Name }
```

- [ ] **Step 2: For each PNG, locate its generating script**

```powershell
# Search for the stem name in scripts/figures
foreach ($png in ls report1/phd-thesis-template-2.4/Figs/report1/*.png) {
    $stem = $png.BaseName
    Write-Host "==> $stem"
    grep -l $stem scripts/figures/*.py
}
```

Save the (stem → script) map. Any stem with no matching script: log it for the §4.3 fallback path (still gets a wrapper PDF via imagemagick at Task P2.5).

- [ ] **Step 3: Commit the inventory note**

```powershell
# write the map as a comment block at the top of scripts/figures/_style.py
# or as a separate scripts/figures/_inventory.md
```

Either form is acceptable; the goal is a written record so the P2 sub-agent doesn't re-discover it on a retry. Commit:

```bash
git add scripts/figures/_inventory.md
git commit -m "report1 figtab P2: inventory PNG figure -> script mapping"
```

### Task P2.2: Modify each plot script to use _style

Apply to every script identified in P2.1. Pattern for each script:

- [ ] **Step 1: Add imports at top of script (after stdlib imports, before matplotlib calls)**

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _style import apply, PALETTE, DIVERGING_CMAP, save_pair
apply()
```

(The `sys.path.insert` line lets the script be invoked from a different cwd.)

- [ ] **Step 2: Remove or comment out any existing `plt.rc(...)` / `mpl.rcParams[...] = ...` overrides**

Exception: keep `plt.subplots(figsize=...)` and any explicit `set_xlim` / `set_ylim` — those are figure-specific.

- [ ] **Step 3: Replace inline hex colors with PALETTE keys**

Examples of common substitutions:
- `color='blue'` → `color=PALETTE["fp64"]` (if the line represents fp64 or CPU or HLLC)
- `color='red'`, `color='orange'` → `PALETTE["fp32"]`
- `color='gray'`, `color='k'` for reference → `PALETTE["ref"]` or `PALETTE["gray"]`
- `cmap='jet'`, `cmap='rainbow'` → `cmap=SEQUENTIAL_CMAP` (sequential field) or `cmap=DIVERGING_CMAP, vmin=-vmax, vmax=vmax` (signed difference)

- [ ] **Step 4: Replace final `plt.savefig(stem.png)` with `save_pair(fig, stem, outdir)`**

Where `outdir` should resolve to the absolute path of `report1/phd-thesis-template-2.4/Figs/report1` (use `os.path.join(repo_root, …)` if the script lives elsewhere).

- [ ] **Step 5: Run the script and confirm PDF + PNG are produced**

```powershell
python scripts/figures/<script_name>.py
ls report1/phd-thesis-template-2.4/Figs/report1/<stem>.pdf
ls report1/phd-thesis-template-2.4/Figs/report1/<stem>.png
```

- [ ] **Step 6: Commit per script** (granular commits — easier to revert one bad regeneration):

```bash
git add scripts/figures/<script_name>.py report1/phd-thesis-template-2.4/Figs/report1/<stem>.pdf report1/phd-thesis-template-2.4/Figs/report1/<stem>.png
git commit -m "report1 figtab P2: regenerate <stem>.{pdf,png} under unified style"
```

**Repeat steps 1–6 for every script** in the P2.1 inventory. Specific notes per script:

- `plot_2d.py` — for `lw12_n400_fp32_minus_fp64_rho` use `DIVERGING_CMAP` with `vmin=-vmax`; for `lw3_n400_double_rho_schlieren` and `lw12_n400_double_rho_schlieren` use `SEQUENTIAL_CMAP` (viridis).
- `plot_drift_timeseries.py` — semilog-y; first four cases drawn from `CYCLE`; `_selected` variant: 3 emphasised + grey context.
- `plot_hllc_rusanov_points.py` — HLLC = `PALETTE["hllc"]` solid; Rusanov = `PALETTE["rusanov"]` solid; density and pressure panels share x-range.
- `report1_d2_replots.py` — re-run with n=30 inputs from `experiments/review3_mca_n30/` (do **not** rerun the experiment); preserves all numerics from review3.
- `plot_stationary_contact_vfc.py` / `plot_vfc_hllc_vs_rusanov.py` — 4-color cycle from `CYCLE`.

### Task P2.3: Fallback wrapper PDF for stems without a known script

- [ ] **Step 1: For each stem from P2.1 with no script, generate a PDF wrapper from the existing PNG**

```powershell
foreach ($stem in $orphan_stems) {
    magick "report1/phd-thesis-template-2.4/Figs/report1/$stem.png" "report1/phd-thesis-template-2.4/Figs/report1/$stem.pdf"
}
```

(If `magick` is not installed, document in `scripts/figures/_inventory.md` that these stems remain PNG-only.)

- [ ] **Step 2: Commit fallback PDFs**

```bash
git add report1/phd-thesis-template-2.4/Figs/report1/*.pdf
git commit -m "report1 figtab P2: PDF wrappers for stems without regenerating script"
```

### Task P2.4: Strip `.png` extensions from `\includegraphics` calls

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

- [ ] **Step 1: Run a single sed/PowerShell replace**

```powershell
# For each chapter:
$content = Get-Content report1/phd-thesis-template-2.4/Chapter5/chapter5.tex -Raw
$content = $content -replace '(includegraphics\[[^\]]*\]\{[^}]+)\.png\}', '$1}'
Set-Content -Path report1/phd-thesis-template-2.4/Chapter5/chapter5.tex -Value $content -NoNewline
```

Repeat for Chapter6.

- [ ] **Step 2: Grep to confirm zero `.png}` remaining inside `\includegraphics`**

```powershell
grep -n -E "includegraphics.*\\.png\\}" report1/phd-thesis-template-2.4/Chapter*/chapter*.tex
```

Expected: no output.

- [ ] **Step 3: pdflatex check**

```powershell
cd report1/phd-thesis-template-2.4 ; .\compile-thesis-windows.bat ; cd ../..
```

Expected: clean build; graphicx silently picks `.pdf` over `.png` for each figure (per `\DeclareGraphicsExtensions`).

- [ ] **Step 4: Visual spot-check 3 figures in thesis.pdf**

Open `thesis.pdf` and check that 3 randomly sampled figures (e.g. `sigma_fp_vs_precision`, `sod_comparison`, `lw3_n400_double_rho_schlieren`) render with the new palette and serif font.

- [ ] **Step 5: Commit P2.4**

```bash
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git commit -m "report1 figtab P2: drop .png extension from includegraphics (prefer .pdf)"
```

---

## Phase P3 — TikZ Ch3 (3)

### Task P3.1: Recolor Fig 3.1 finite-volume conservative update

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` (`\begin{figure}` at line ≈ 72)

- [ ] **Step 1: Locate the TikZ block**

```powershell
grep -n -A 200 "begin{figure}\[htbp\]" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex | Select-String -Pattern "tikzpicture|end{figure}" | Select-Object -First 4
```

- [ ] **Step 2: Substitute colors**

Inside this TikZ block only, replace literal colors with palette macros:

| Match | Replacement |
|---|---|
| `draw=blue`, `draw=red`, `color=blue`, `color=red` (main shapes) | `draw=fpDarkBlue` |
| `fill=blue!20`, `fill=red!20` (cell-background) | `fill=fpDarkBlue!20` |
| `draw=gray`, `draw=black!50` (reference axes) | `draw=fpGray` |
| `draw=orange`, `color=orange` (highlight arrows) | `draw=fpOrange` |

Add or normalise line widths inside the same block:
- Main flux arrows / cell boundary: `line width=1.2pt`
- Reference grid / construction lines: `line width=0.6pt` (or `thin`)

- [ ] **Step 3: pdflatex check**

```powershell
cd report1/phd-thesis-template-2.4 ; .\compile-thesis-windows.bat ; cd ../..
```

- [ ] **Step 4: Visual check in thesis.pdf**

Confirm Fig 3.1 renders with deep-blue cell outline and dark-gray reference axes.

### Task P3.2: Recolor Fig 3.2 HLLC wave fan

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` (`\begin{figure}` at line ≈ 235)

- [ ] **Step 1: Locate the TikZ block**

- [ ] **Step 2: Substitute**

| Item | Color |
|---|---|
| Shock waves $S_L$, $S_R$ | `fpDarkBlue`, line width 1.2pt |
| Contact wave | `fpGray`, line width 1.2pt, optionally dashed |
| Star-state highlight box / arrow | `fpOrange`, line width 1.2pt |
| Reference/construction lines | `fpGray`, line width 0.6pt |

- [ ] **Step 3: pdflatex check + visual check**

### Task P3.3: Recolor Fig 3.3 MHD seven-wave fan

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` (`\begin{figure}` at line ≈ 528)

- [ ] **Step 1: Locate the TikZ block**

- [ ] **Step 2: Substitute**

| Wave family | Color |
|---|---|
| Fast magnetosonic | `fpDarkBlue` |
| Alfvén | `fpCyanGreen` |
| Slow magnetosonic | `fpOrange` |
| Entropy / contact | `fpGray` |

All main lines `line width=1.2pt`; construction lines `line width=0.6pt`.

- [ ] **Step 3: pdflatex check + visual check**

### Task P3.4: P3 acceptance audit and commit

- [ ] **Step 1: Forbidden-color grep inside Ch3 TikZ blocks**

```powershell
# Inside each of the three figures only, expect 0 hits for literal colors
grep -n -E "(draw|fill|color)=(red|blue|green|orange|black!|red!|blue!)" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Each remaining hit must be **outside** the three TikZ figures (e.g. in a `\textcolor` in prose). If inside, return.

- [ ] **Step 2: Line-width grep inside Ch3 TikZ blocks**

```powershell
grep -n -E "line width=[0-9]" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Expected: only `1.2pt` or `0.6pt` (or `thick`/`thin`) inside the three TikZ figures.

- [ ] **Step 3: pdflatex full build, no new warnings**

- [ ] **Step 4: Commit P3**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
git commit -m "report1 figtab P3: recolor Ch3 TikZ figures to 4-color palette"
```

---

## Phase P4 — Figure Captions (17)

Template (same as P1 tables):

```latex
\caption[<short caption>]{\textbf{<Lead-in title>.}
  <Explanation: what's shown, definitions, conditions, color meaning, source.>
  \emph{<Single-sentence take-away.>}}
```

### Task P4.1: Rewrite Ch3 figure captions (3)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter3/chapter3.tex` (captions of Fig 3.1, 3.2, 3.3)

- [ ] **Step 1: For each of the three figures**

Convert existing `\caption{...}` to the three-segment form. Allowed to add information from prose (per spec §5.2 "information migration rule"):
- Equation cross-references (e.g. "see Eq.~\eqref{eq:ch3-fv-update}")
- Color legend description ("dark blue lines mark the shock waves $S_L$, $S_R$; orange highlights the star state where rounding may flip the branch")
- Condition labels

Forbidden:
- Deleting any `\cite`, `\ref`, `\autoref` from main text
- Removing any argumentative sentence from prose

- [ ] **Step 2: pdflatex + visual spot-check**

- [ ] **Step 3: Commit P4.1**

```bash
git add report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
git commit -m "report1 figtab P4: rewrite Ch3 figure captions in 3-segment form"
```

### Task P4.2: Rewrite Ch5 figure captions (9 figures, one subfigure pair)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`

Targets identified earlier (`\begin{figure}` lines 130, 137, 144, 209, 216, 257, 264, 372, 432).

- [ ] **Step 1: For each of the 9 figure blocks**

Rewrite caption. Each must end up with:
- `\caption[short]{\textbf{lead-in.} explanation. \emph{take-away.}}`
- Bold lead-in matches the figure's role (e.g. `Sod shock-tube density / pressure comparison` for Fig 5.x).
- Explanation states: $N$, $t$, fp precision, reference source, color semantics.
- Take-away: one sentence (e.g. "fp64 and fp32 final-state profiles overlap visually; the conservative-state $L_1$ difference is $\mathcal{O}(10^{-5})$, well below the reference-error scale").

- [ ] **Step 2: pdflatex + visual spot-check**

- [ ] **Step 3: Commit P4.2**

```bash
git add report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
git commit -m "report1 figtab P4: rewrite Ch5 figure captions in 3-segment form"
```

### Task P4.3: Rewrite Ch6 figure captions (4 figure blocks; 1 has subfigures)

**Files:**
- Modify: `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`

Targets: `\begin{figure}` lines ≈ 11, 22 (subfigure pair), 40, 54.

- [ ] **Step 1: Fig `sigma_fp_vs_precision` (line 11)**

Apply three-segment caption. Keep review3's content note (`Values near $10^{-11}$ at \texttt{p53} approach the fp64 noise floor and bound rather than measure the rounding scale at that precision.`) inside the explanation segment.

- [ ] **Step 2: LoSoS subfigure-combined block (line 22)**

Outer `\caption` is three-segment; each subfigure keeps a short `\subcaption{...}`. Pattern:

```latex
\begin{figure}[t]
  \centering
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{Figs/report1/losos_quantiles_rho}
    \subcaption{Quantile view of raw LoSoS.}
    \label{fig:ch6-losos-quantiles}
  \end{subfigure}\hfill
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{Figs/report1/region_losos_margin_rho_p32}
    \subcaption{Region-aware margin at \texttt{p32}.}
    \label{fig:ch6-region-losos}
  \end{subfigure}
  \caption[LoSoS quantile and region-aware margin for LW3 density]%
    {\textbf{LoSoS quantile and region-aware margin for LW3 density under MCA.}
    Left: sample quantiles ($q_{05}/q_{25}$/median) of raw LoSoS at $n=30$ seeds
    per (precision, solver), with HLLC in deep blue and Rusanov in grey. Right:
    region-aware margin (available digits minus $s_{\mathrm{req}}$) at virtual
    precision \texttt{p32}, split by smooth, transition, and shock-front regions.
    \emph{Median LoSoS rises with virtual precision while lower quantiles remain
    front-sensitive; the \texttt{p32} margin is positive in the smooth interior
    and negative in the shock-front band.}}
  \label{fig:ch6-losos-combined}
\end{figure}
```

- [ ] **Step 3: Fig `noise_to_error_ratio_heatmap_grid_rho` (line 40)**

Apply three-segment caption. Add color-semantics note ("brighter values = larger noise-to-error ratio").

- [ ] **Step 4: Fig `region_noise_to_error_ratio_precision_grid_rho` (line 54)**

Keep the existing short caption text, expand into three segments. Include the review3-added "$0\,\%$ at \texttt{p32}" headline.

- [ ] **Step 5: pdflatex + visual spot-check + commit P4.3**

```bash
git add report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
git commit -m "report1 figtab P4: rewrite Ch6 figure captions in 3-segment form"
```

### Task P4.4: P4 acceptance audit

- [ ] **Step 1: Three-segment caption grep across Ch3/Ch5/Ch6 figures**

```powershell
# every \begin{figure} should be followed within 60 lines by a \caption with \textbf and \emph
grep -n -A 60 "begin{figure}" report1/phd-thesis-template-2.4/Chapter[356]/chapter*.tex | Select-String -Pattern "caption\[.*\]\{\\\\textbf"
```

Count = total figure blocks in those chapters (3 + 9 + 4 = 16). The 17th figure is the subfigure-combined LW3 LoSoS pair where `\caption{...}` covers both — count it once.

- [ ] **Step 2: Citation-preservation check**

Compare the count of `\cite{...}` in main text Ch3/Ch5/Ch6 before-and-after P4:

```powershell
# baseline taken at start of P4
git show HEAD~5:report1/phd-thesis-template-2.4/Chapter3/chapter3.tex | grep -c "\\\\cite{"
grep -c "\\\\cite{" report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
# expect new count >= baseline
```

If new count is lower for any chapter, restore the missing citation by re-introducing it in prose (caption-only is not enough — citations must stay in main text).

---

## Phase Final — Build, Audit, and Cleanup

### Task F.1: Full clean pdflatex round-trip

- [ ] **Step 1: Remove aux files and rebuild from scratch**

```powershell
cd report1/phd-thesis-template-2.4
Remove-Item *.aux,*.bbl,*.blg,*.lof,*.log,*.lot,*.out,*.toc -ErrorAction SilentlyContinue
.\compile-thesis-windows.bat
cd ../..
```

Expected: thesis.pdf rebuilds cleanly. No undefined refs in `thesis.log`.

- [ ] **Step 2: Grep thesis.log for new warnings**

```powershell
grep -E "^(Overfull|Underfull|! |LaTeX Warning)" report1/phd-thesis-template-2.4/thesis.log | Select-Object -First 30
```

`Overfull \hbox` > 5pt that did not exist in baseline → fix (e.g. narrow a `S[table-format=...]` column).

### Task F.2: texcount delta

- [ ] **Step 1: Compute final texcount and compare to baseline**

```powershell
cd report1/phd-thesis-template-2.4
texcount -inc -sum -1 thesis.tex
cd ../..
Get-Content docs/superpowers/plans/.figtab-baseline-texcount.txt
```

Expected delta: ∈ `[-10, +50]` words.

If outside the band, identify which phase contributed and consider trimming caption text. If under by more than 10, that's acceptable (likely from improved column alignment removing wrap words).

### Task F.3: Visual spot-check (5 figures + 3 tables)

- [ ] **Step 1: Pick 5 random figures and 3 random tables; visually confirm**

Open `report1/phd-thesis-template-2.4/thesis.pdf`. For each:
- Figure: fonts are serif; colors match palette (deep blue / orange / cyan-green / gray); no rainbow colormap; legend / colorbar present.
- Table: `\small` font; numbers aligned at decimal/exponent; double-row header readable; caption shows bold lead-in, plain explanation, italic take-away.

### Task F.4: Final commit and tag (optional)

- [ ] **Step 1: Verify clean working tree**

```bash
git status
```

If any uncommitted file remains, decide: roll into a "Final" commit or revert.

- [ ] **Step 2: Final summary commit (if any)**

```bash
git add -A report1/phd-thesis-template-2.4/ scripts/figures/ docs/superpowers/plans/.figtab-baseline-*.txt
git commit -m "report1 figtab Final: pdflatex audit + texcount delta + spot-check"
```

- [ ] **Step 3: Optional tag**

```bash
git tag -a report1-figtab-v1 -m "Report 1 figure/table polish — P0+P1+P2+P3+P4 done"
```

---

## Self-Review

**Spec coverage**

| Spec section | Covered by | Notes |
|---|---|---|
| §1.1 in-scope (1) preamble | P0.1 | ✓ |
| §1.1 in-scope (2) `_style.py` | P0.2 | ✓ |
| §1.1 in-scope (3) 14 PNG | P2.1–P2.4 | ✓ |
| §1.1 in-scope (4) 3 TikZ | P3.1–P3.3 | ✓ |
| §1.1 in-scope (5) 10 tables | P1.1–P1.5 | ✓ |
| §1.1 in-scope (6) 27 captions | P1 captions + P4 | ✓ (captions for tables handled in P1; figure captions in P4) |
| §1.1 in-scope (7) drop `.png` ext | P2.4 | ✓ |
| §1.2 out-of-scope | implicit by exclusion | ✓ — no task touches data, prose, new figures, cfg, harness |
| §1.4 Definition of Done | F.1–F.3 | ✓ |
| §2.1 LaTeX preamble block | P0.1 step 2 | ✓ (verbatim) |
| §2.2 `_style.py` skeleton | P0.2 step 1 | ✓ (verbatim) |
| §3 table rules | P1 tasks | ✓ |
| §4 figure rules | P2 tasks | ✓ |
| §5.1 TikZ rules | P3 tasks | ✓ |
| §5.2 caption migration rule | P4 step 1 of each subtask | ✓ |
| §6 risks (R1–R10) | acknowledged inline; mitigations active | ✓ |
| §7.2 acceptance gates | P1.6, P2.4 step 2, P3.4, P4.4, F.1, F.2 | ✓ |
| §9 open questions | P0.1 (preamble file location), P0.2 step 2 (font), P2.3 (magick) | ✓ |

**Placeholder scan:** No "TBD", "TODO", or "implement later". Every code-bearing step has its code block. Every grep / shell step has the command.

**Type / name consistency:** Palette macro names (`fpDarkBlue`, `fpCyanGreen`, `fpOrange`, `fpGray`) consistent across P0.1 (defined), P1 (used in caption / not applicable), P3 (used in TikZ). `PALETTE` keys (`fp64`, `fp32`, `cpu`, `gpu`, `hllc`, `rusanov`, `ref`, `gray`, `accent`) consistent between P0.2 (defined) and P2.2 (used). `save_pair(fig, stem, outdir)` signature consistent. Function `apply()` consistent. `DIVERGING_CMAP` / `SEQUENTIAL_CMAP` names consistent.

**One gap to flag:** P2.1 inventory may discover that `pressure_hllc_vs_rusanov_200` (mentioned in spec §4.3) does not have a current PNG in `Figs/report1/`. If so, treat as inventory record only — no new figure created.
