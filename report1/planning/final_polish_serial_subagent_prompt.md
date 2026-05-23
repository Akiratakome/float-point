# Final-Polish Serial Subagent Prompt (95+ → 97+)

This prompt is for a main agent that will close the remaining gaps after the
C1-C7 + Abstract + Acknowledgement round. The intent is **targeted small
edits**, dispatched serially to sub-section-scoped workers; no chapter rewrite.

The user has already accepted these scope decisions:

- WordCount declaration is intentionally absent (matches `report1/examples/Project-Report-1-example.pdf`).
- Schlieren colour scheme stays colour (no B/W conversion).
- C6 word count may grow; total Overleaf in-text must stay **≤ 7,500**.
- Citation order in `references.bib` is reorganised by **first appearance** in text (cosmetic for apalike but improves maintenance).
- Up to **3 new citation keys** may be added: `davis_1988`, `sohier_etal_2021`, `higham_mary_2022` (BibTeX metadata provided in Worker 9).
- C1-C3 may get small explanatory figures (TikZ only; captions excluded from word count).
- C4 gets two additional algorithm boxes in the example's `algpseudocode` style.

Repository:

```text
c:\Users\tangy\Desktop\floatpoint
```

Working directory and target files are listed in Worker sections.

## Word Budget Lock

Baseline (texcount): **7,246 in-text words**. Hard cap **7,500**. Total budget
delta this pass: **≤ +200 words net** (safety margin 50). Each worker has a
hard caps on word delta; the main agent reruns texcount after Workers 4, 5, 6,
8 to confirm running total.

| Worker | Δ (words) | Cumulative |
|---|---:|---:|
| W1 | +5 | 7,251 |
| W2 | +30 | 7,281 |
| W3 | +60 | 7,341 |
| W4 | +30 (net; add algo + compress) | 7,371 |
| W5 | +30 (net; add algo + compress) | 7,401 |
| W6 | -50 (compress §4.5) | 7,351 |
| W7 | -20 (rounding) | 7,331 |
| W8 | +120 (SNR para + figure) | 7,451 |
| W9 | 0 (bib metadata only) | 7,451 |
| W10 | +5 (one cite + 4 words) | 7,456 |
| W11 | 0 (TikZ + caption only) | 7,456 |

Final projected total: **7,456 ≤ 7,500** ✓ (44-word safety).

If any worker overshoots by >10 words, the main agent dispatches a
focused-compression repair before the next worker.

## Main-Agent Mandate

The main agent must:

1. Read all required context before dispatching workers.
2. Dispatch exactly one worker at a time.
3. Never allow two workers to edit the same file concurrently.
4. After each worker returns, inspect only the edited region plus one paragraph
   before and after.
5. Reject and repair any worker output that violates the original PDF
   requirements, supervisor feedback, chapter ownership, evidence boundaries,
   or word-delta caps.
6. Rerun `texcount -inc -sum thesis.tex` after Workers 4, 5, 6, 8 and the final
   pass; record the running total in the integration log.
7. Run the final verification and strict score against the original PDF.

The main agent may make mechanical integration edits only (marker preservation,
broken reference fix, whitespace, single-word forbidden-token replacement).
Any substantive prose/equation/figure change must be made by the relevant
section-scoped worker.

Tell every worker:

```text
You are not alone in the codebase. Edit only your assigned section or local
paragraph. Do not revert or overwrite changes outside your scope. Do not modify
solver numerics, cfg defaults, experiment artifacts, or anything under
experiments/. Respect the worker's word-delta cap.
```

## Required Reading

```text
docs/INDEX.md
report1/INDEX.md
report1/planning/manuscript_outline.md
report1/planning/supervisor_feedback_map.md
report1/planning/supervisorguide.md
experiments/report1_evidence_map.md
report1/references/reference.md
report1/requirements/Effect of Floating-Point precision and hardware on HRSC Schemes.pdf
report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
report1/phd-thesis-template-2.4/Chapter2/chapter2.tex
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
report1/phd-thesis-template-2.4/References/references.bib
report1/examples/Project-Report-1-example.pdf  (pages 35-38 only, for Algorithm style)
```

Read these skills before each prose-touching worker:

```text
report1/skills/scientific-writing-duke/SKILL.md
report1/skills/academic-english-style/SKILL.md
report1/skills/avoiding-ai-flavor/SKILL.md
```

## Preflight Checks

Run from repo root:

```powershell
rg -n "% <<SECTION_[0-9]+_(BEGIN|END)>>" report1/phd-thesis-template-2.4/Chapter1/chapter1.tex report1/phd-thesis-template-2.4/Chapter2/chapter2.tex report1/phd-thesis-template-2.4/Chapter3/chapter3.tex report1/phd-thesis-template-2.4/Chapter4/chapter4.tex report1/phd-thesis-template-2.4/Chapter5/chapter5.tex report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
texcount -inc -sum report1/phd-thesis-template-2.4/thesis.tex
rg -n "week[0-9]+|\bD1\b|\bD2\b|HLLC-fill|config12|LW12/config12|\bP1\b|USE_GPU|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann|well resolved in binary64|vertical interface" report1/phd-thesis-template-2.4/Chapter*/chapter*.tex report1/phd-thesis-template-2.4/Abstract/abstract.tex
```

Expected: all section markers present, baseline 7,246 in-text words, zero
forbidden-token hits in manuscript-facing files. Record results in
integration log.

---

## Worker 1: C3 §3.3 — Davis Attribution via New Bib Key

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Assigned local scope: the Davis-style wave-speed bound sentence inside
`% <<SECTION_3_BEGIN>> … % <<SECTION_3_END>>`, currently at
[Chapter3/chapter3.tex L184-L185](report1/phd-thesis-template-2.4/Chapter3/chapter3.tex#L184-L185):

```latex
In the Davis-style wave-speed bound as presented by
\citet{toro2009},
```

Depends on: Worker 9 has added `davis_1988` to `References/references.bib`.
Worker 1 runs **after** Worker 9.

Task:

- Replace the sentence with author-name prose that cites the primary source:

```latex
In the wave-speed bound of \citet{davis_1988} as presented by
\citet{toro2009},
```

Acceptance criteria:

- `\citet{davis_1988}` appears in C3 §3.3 exactly once.
- `\citet{toro2009}` remains.
- No other text changes in §3.3.

Word delta: **+5**.

Main-agent review:

- Run `rg -F "{davis_1988," report1/phd-thesis-template-2.4/References/references.bib`; confirm one hit.
- Run `bibtex thesis` after the cite is in place; confirm no undefined-citation warning.

---

## Worker 2: C3 §3.6 — Name MHD-Specific Riemann Solvers

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Assigned region: end of `% <<SECTION_6_BEGIN>> … % <<SECTION_6_END>>`,
immediately before the closing marker.

Task: append one sentence (no new citation, no equation, no figure):

```latex
In ideal MHD, Roe-type and HLLD approximate Riemann solvers extend the
HLL/HLLC family to the seven-wave fan; their selection forms part of the
Report~2 numerical-method work.
```

This closes the project brief's Mathematical Theory sub-bullet (b)
"different Riemann solvers".

Acceptance criteria:

- The sentence appears as the second-to-last sentence of §3.6.
- The existing "Report~1 evidence remains Euler-only" statement remains.
- No new citation key introduced.

Word delta: **+30**.

Main-agent review:

- Confirm §3.6 still meets its 230-word soft cap.
- Confirm no MHD validation claim was introduced.

---

## Worker 3: C4 §4.1 — Ease-of-Implementation 4-Item List

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Assigned region: end of `% <<SECTION_1_BEGIN>> … % <<SECTION_1_END>>`,
immediately before the closing marker.

Task: append the following list to satisfy brief Code Description sub-bullet 1
(ease-of-implementation and optimization features):

```latex
The four implementation features that make this comparison auditable are:
\begin{enumerate}
  \item fp32/fp64 source-level templating via \texttt{HRSC\_REAL}, so the same
        source compiles to either precision;
  \item CMake \texttt{ENABLE\_CUDA} build switch plus runtime
        \texttt{device=cpu/gpu} selection, producing matched within-binary
        CPU/GPU comparisons;
  \item a Python regression harness that re-runs the validation matrix and
        checks outputs against stored references;
  \item the matched-binary CPU--GPU switch, so bit-identity claims are not
        confused with toolchain or compiler-flag differences.
\end{enumerate}
```

Acceptance criteria:

- The `enumerate` block appears at the end of §4.1.
- All four items appear exactly once.
- No new citations.
- No source-path explanations.

Word delta: **+60**.

Main-agent review:

- Confirm §4.1 still leads with the comparability principle (no item appears before the principle is stated).
- Confirm the toolchain split sentence at the end of §4.1 remains.

---

## Worker 4: C4 §4.2 — Add Algorithm 2 (MUSCL-Hancock Predictor) and Compress Prose

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Assigned region: `% <<SECTION_2_BEGIN>> … % <<SECTION_2_END>>`.

Task: insert a new algorithm box modelled on the example
(`report1/examples/Project-Report-1-example.pdf` pp. 36-38 style: numbered
lines, `\Function`/`\State`, `\textsc{}` for routine names, `▷` for inline
comments). Place after Algorithm 1, before the "The CUDA path uses separate
kernels…" paragraph.

```latex
\begin{algorithm}
\caption{MUSCL--Hancock face-state construction for one cell, one direction}
\label{alg:muscl-hancock}
\begin{algorithmic}[1]
\Function{ReconstructFaces}{$\bar U_{i-1}^{n}, \bar U_i^{n}, \bar U_{i+1}^{n}, \Delta x, \Delta t$}
  \State $\delta^{-} \gets \bar U_i^{n} - \bar U_{i-1}^{n}$
  \State $\delta^{+} \gets \bar U_{i+1}^{n} - \bar U_i^{n}$
  \State $\sigma_i \gets \textsc{Minmod}(\delta^{-}, \delta^{+})$ \Comment{Eq.~\eqref{eq:ch3-minmod-def}}
  \State $U_{i,L}^{n} \gets \bar U_i^{n} - \tfrac{1}{2}\sigma_i$
  \State $U_{i,R}^{n} \gets \bar U_i^{n} + \tfrac{1}{2}\sigma_i$
  \State $\Delta F \gets F(U_{i,R}^{n}) - F(U_{i,L}^{n})$
  \State $\bar U_{i,L}^{n+1/2} \gets U_{i,L}^{n} - \tfrac{\Delta t}{2\Delta x}\,\Delta F$
  \State $\bar U_{i,R}^{n+1/2} \gets U_{i,R}^{n} - \tfrac{\Delta t}{2\Delta x}\,\Delta F$
  \State \Return $(\bar U_{i,L}^{n+1/2},\, \bar U_{i,R}^{n+1/2})$
\EndFunction
\end{algorithmic}
\end{algorithm}
```

To stay net +30 words, compress the existing §4.2 paragraph beginning
"The conservative state stores the variable index…" by ~60 prose words
(merge into the algorithm caption / surrounding sentences; preserve the
ghost-cell statement, the CFL formula reference, and the harness paragraph
unchanged).

Acceptance criteria:

- `alg:muscl-hancock` is referenced from at least one place in §4.2 prose
  (e.g. "Algorithm~\ref{alg:muscl-hancock} expands the per-cell predictor").
- No `\[…\]` introduced; existing equation numbering preserved.
- Worker's local word delta ≤ +35 (algorithm body counts; main-agent verifies).

Word delta: **+30** net.

Main-agent review:

- Run `texcount -inc report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`; confirm Δ ≤ +35 versus baseline.
- Confirm no source-path style explanation introduced.

---

## Worker 5: C4 §4.2 — Add Algorithm 3 (HLLC Flux Selection)

Assigned file: same as Worker 4 (run **after** Worker 4 completes).

Assigned region: end of `% <<SECTION_2_BEGIN>> … % <<SECTION_2_END>>`,
immediately before the closing marker, after the CUDA paragraph.

Task: insert the following algorithm box; the example uses one algorithm per
clearly bounded routine and the HLLC flux is the natural second routine.

```latex
\begin{algorithm}
\caption{HLLC interface flux selection (one face)}
\label{alg:hllc-flux-select}
\begin{algorithmic}[1]
\Function{HllcFlux}{$U_L, U_R$}
  \State Compute $(\rho_L,u_L,p_L,a_L)$ from $U_L$; same for $R$
  \State $S_L \gets \min(u_L-a_L,\,u_R-a_R)$ \Comment{Eq.~\eqref{eq:ch3-hllc-wavespeeds}}
  \State $S_R \gets \max(u_L+a_L,\,u_R+a_R)$
  \State $S_\ast \gets \textsc{ComputeContactSpeed}(U_L, U_R, S_L, S_R)$ \Comment{Eq.~\eqref{eq:ch3-hllc-sstar}}
  \If{$S_L \ge 0$} \State \Return $F(U_L)$
  \ElsIf{$S_\ast \ge 0$} \State \Return $F(U_L) + S_L\,(U_{\ast L} - U_L)$
  \ElsIf{$S_R \ge 0$} \State \Return $F(U_R) + S_R\,(U_{\ast R} - U_R)$
  \Else \State \Return $F(U_R)$
  \EndIf
\EndFunction
\end{algorithmic}
\end{algorithm}
```

Add one short prose sentence (≤ 25 words) to introduce the algorithm and
forward-reference §3.5 for the `<` versus `<=` test, e.g.:

```latex
Algorithm~\ref{alg:hllc-flux-select} expands the HLLC interface flux; the
strict-inequality variant tested in §3.5 toggles the comparator at the four
branch tests.
```

To stay net +30 words, compress one redundant sentence elsewhere in §4.2
(suggested target: the sentence "Metrics are collected outside the update path
from written states." — fold into the harness paragraph).

Acceptance criteria:

- Algorithm 3 appears after Algorithm 2 (Worker 4's MUSCL-Hancock).
- Forward reference to §3.5 is present.
- Worker's local word delta ≤ +35.

Word delta: **+30** net.

Main-agent review:

- Confirm running total after W4 + W5 is ≤ 7,401.
- Confirm Algorithm 3 uses the same `\textsc{}` / `▷` style as Algorithm 2.

---

## Worker 6: C4 §4.5 — Compress Reference-Strategy Paragraph

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Assigned region: `% <<SECTION_5_BEGIN>> … % <<SECTION_5_END>>`.

Task: rewrite the third paragraph of §4.5 (currently L242-L252,
"This strategy is load-bearing…") to delete ~50 words while preserving:

- the statement that ratios speak about reference scale, not general fp32 adequacy;
- the matched same-precision CPU/GPU comparison statement;
- the checkpoint-saved-output boundary.

Suggested compressed form (target ≤ 60 words):

```latex
Ratios such as
\(\|U_{\mathrm{fp32}}-U_{\mathrm{fp64}}\|_1/
\|U_{\mathrm{fp64}}-U_{\mathrm{ref}}\|_1\) bound precision drift relative
to the reference scale, not in absolute terms~\citep{higham_2002}. CPU/GPU
entries are matched same-precision final-state comparisons; checkpointed
summaries bound only saved-output behaviour, not stage-by-stage identity.
```

Acceptance criteria:

- `\citep{higham_2002}` remains.
- "matched", "checkpoint", and "saved-output" remain visible.
- §4.5 word count decreases by ≥ 40.

Word delta: **−50**.

Main-agent review:

- Confirm no Chapter 5 result number is now hidden behind §4.5 paragraph removal.

---

## Worker 7: C5 §5.2 / §5.4 / §5.6 — Numerical Precision Rounding to 3-4 sig fig

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter5/chapter5.tex
```

Assigned local scopes (apply targeted in-place replacements; do not move
sentences):

| Line ref | Old | New |
|---|---|---|
| [L54-L56](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L54-L56) | `8.743340\times10^{-8}` | `8.74\times10^{-8}` |
| [L55](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L55) | `6.386967\times10^{-5}` | `6.39\times10^{-5}` |
| [L56](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L56) | `1.296410\times10^{-4}` | `1.30\times10^{-4}` |
| [L59](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L59) | `1.364064\times10^{-5}` | `1.36\times10^{-5}` |
| [L60](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L60) | `3.913105\times10^{-5}` | `3.91\times10^{-5}` |
| [L75-L77](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L75-L77) Table 5.1 | same 6-7-digit values | 3 sig fig forms above |
| Table 5.6 / `tab:ch5-fp32-flags` [L373-L380](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L373-L380) | `9.336649e-8`, `1.192093e-6`, `4.00`, `9.900146e-8`, `1.430511e-6`, `4.80`, `6.778757e-5`, `2.807617e-3`, `9.42`, `1.708782e-4`, `1.928711e-2`, `29.94`, `3.523305e-7`, `1.204014e-5`, `23.52` | 3 sig fig forms (`9.34e-8`, `1.19e-6`, `4.00`, `9.90e-8`, `1.43e-6`, `4.80`, `6.78e-5`, `2.81e-3`, `9.42`, `1.71e-4`, `1.93e-2`, `29.9`, `3.52e-7`, `1.20e-5`, `23.5`) |
| §5.5 GPU flag probe values [L397-L401](report1/phd-thesis-template-2.4/Chapter5/chapter5.tex#L397-L401) | already mostly 3 sig fig; verify | leave |

Constraints:

- Do not change the **meaning** of any sentence.
- Do not delete any number; only round.
- Do not change captions other than column headers if needed for symmetry.

Word delta: **−20** (digit count shrinks slightly).

Main-agent review:

- Run `rg -n "[0-9]\.[0-9]{5,}\\\\times" report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`;
  confirm zero hits with 5+ post-decimal digits except where intentional.

---

## Worker 8: C6 §6.2 — Add SNR Framing Paragraph + region_noise Figure

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter6/chapter6.tex
```

Assigned region: end of `% <<SECTION_2_BEGIN>> … % <<SECTION_2_END>>`,
immediately before the closing marker.

Depends on: Worker 9 has added `sohier_etal_2021` to `References/references.bib`.
Worker 8 runs **after** Worker 9.

Task: insert the following paragraph and figure verbatim:

```latex
\paragraph{SNR framing.}
The $\sigma_{\mathrm{FP}}$, LoSoS, $s_{\mathrm{req}}$, and noise-to-error
views all reduce to a local signal-to-noise comparison. Defining a per-cell
signal-to-noise ratio as the ratio of local reference error to MCA rounding
noise,
\begin{equation}\label{eq:ch6-snr}
  \mathrm{SNR}(\mathbf{x})
  = \frac{|U_{\mathrm{fp64}}(\mathbf{x}) - U_{\mathrm{ref}}(\mathbf{x})|}{\sigma_{\mathrm{FP}}(\mathbf{x})},
\end{equation}
the noise-to-error heatmap of Fig.~\ref{fig:ch6-noise-error} is the indicator
$\mathrm{SNR}<1$ over the LW3 grid, while the required-digits threshold gives
$s_{\mathrm{req}} \approx \log_{10}(\mathrm{SNR}^{-1}_{\mathrm{target}})$ when
the target ratio is fixed across the field~\citep{sohier_etal_2021}.
Figure~\ref{fig:ch6-region-snr} shows the same SNR view split by smooth,
transition, and shock-front regions: precision-limited cells
($\mathrm{SNR}<1$) concentrate where the limited reconstruction feeds the
HLLC star-state algebra, and the precision-limited fraction shrinks
monotonically from \texttt{p8} to \texttt{p32}.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{Figs/report1/region_noise_to_error_ratio_precision_grid_rho.png}
\caption{Region-wise SNR analogue for LW3 density: noise-to-error ratio split
by smooth, transition, and shock-front regions at virtual precisions
\texttt{p8}, \texttt{p16}, and \texttt{p32}. Precision-limited regions
(ratio\,>\,1) shrink with virtual precision; the shock-front band remains the
dominant contributor at every level.}
\label{fig:ch6-region-snr}
\end{figure}
```

Acceptance criteria:

- `\citep{sohier_etal_2021}` appears in C6 exactly once.
- New figure `fig:ch6-region-snr` exists and points to the existing file
  `Figs/report1/region_noise_to_error_ratio_precision_grid_rho.png`.
- Equation label `eq:ch6-snr` exists.
- No claim that fp32 is generally adequate; SNR framing stays bounded to LW3.

Word delta: **+120**.

Main-agent review:

- Run `texcount -inc report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`; confirm new total ≤ ~1075.
- Confirm running cumulative is ≤ 7,451.
- Confirm `Figs/report1/region_noise_to_error_ratio_precision_grid_rho.png` exists.

---

## Worker 9: References — Add 3 New Keys, Drop Orphans, Reorder by First Appearance

Assigned file:

```text
report1/phd-thesis-template-2.4/References/references.bib
```

This worker is **bib-only**; runs **first** in the queue so that Workers 1, 8,
and 10 can use the new keys.

Tasks:

1. **Add three new entries** (user has already verified these are real
   publications). Use this metadata verbatim:

```bibtex
@article{davis_1988,
  author  = {Davis, S. F.},
  title   = {Simplified Second-Order {Godunov}-Type Methods},
  journal = {SIAM Journal on Scientific and Statistical Computing},
  volume  = {9},
  number  = {3},
  pages   = {445--473},
  year    = {1988},
  doi     = {10.1137/0909030},
}

@article{sohier_etal_2021,
  author  = {Sohier, Devan and de Oliveira Castro, Pablo and F{\'e}votte, Fran{\c{c}}ois and Lathuili{\`e}re, Bruno and Petit, Eric and Jamond, Olivier},
  title   = {Confidence Intervals for Stochastic Arithmetic},
  journal = {ACM Transactions on Mathematical Software},
  volume  = {47},
  number  = {2},
  pages   = {1--33},
  year    = {2021},
  doi     = {10.1145/3432184},
}

@article{higham_mary_2022,
  author  = {Higham, Nicholas J. and Mary, Theo},
  title   = {Mixed Precision Algorithms in Numerical Linear Algebra},
  journal = {Acta Numerica},
  volume  = {31},
  pages   = {347--414},
  year    = {2022},
  doi     = {10.1017/S0962492922000022},
}
```

2. **Move three orphan keys to the end of the file**, prefix with the comment
   block:

```bibtex
% ---- Orphan keys: kept for archive only. Not cited in current manuscript. ----
```

Orphans to move: `zhang_etal_2019`, `wolf_etal_1985`, `eckmann_ruelle_1985`.

3. **Reorder the cited entries** by first-appearance order (cosmetic for
   `apalike` style but improves maintenance). Order:

```text
1.  toro2009
2.  goldberg_1991
3.  ieee754_2019
4.  brogi_etal_2024
5.  wang_xia_chen_2025
6.  higham_mary_2022       (new — first use in C1 §1.2 after Worker 10)
7.  liska_wendroff_2003
8.  dedner_2002
9.  evans_hawley_1988
10. harten_lax_vanleer_1983
11. toro_spruce_speares_1994
12. davis_1988              (new — first use in C3 §3.3 after Worker 1)
13. sod_1978
14. higham_2002
15. parker_1997
16. denis_etal_2016
17. leveque_2002
18. vanleer_1979
19. bard_dorelli_2014
20. sohier_etal_2021        (new — first use in C6 §6.2 after Worker 8)
21. zhang_etal_2019         (orphan)
22. wolf_etal_1985          (orphan)
23. eckmann_ruelle_1985     (orphan)
```

Acceptance criteria:

- 3 new entries present and well-formed (no missing `}`, correct DOIs).
- 3 orphans below the orphan-comment block.
- All other cite keys retained byte-identical except for repositioning.
- File compiles via `bibtex thesis` with no new warnings.

Word delta: **0** (bib file does not enter `texcount`).

Main-agent review:

- Run `bibtex thesis`; confirm no "I didn't find a database entry" warnings.
- Run `rg -n "^@" report1/phd-thesis-template-2.4/References/references.bib`; verify 23 entries.

---

## Worker 10: C1 §1.2 — Add Higham-Mary Mixed-Precision Citation

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter1/chapter1.tex
```

Assigned local scope: the sentence in `% <<SECTION_2_BEGIN>> … % <<SECTION_2_END>>`
beginning "Recent CFD studies therefore treat reduced or mixed precision as
case-dependent: …" at [Chapter1/chapter1.tex L12](report1/phd-thesis-template-2.4/Chapter1/chapter1.tex#L12).

Depends on: Worker 9 has added `higham_mary_2022`.

Task: extend the existing CFD-precision sentence by appending one clause that
cites the broader mixed-precision survey while keeping the bounded "CFD
context" framing intact:

Old:
```latex
… Wang, Xia, and Chen study a heterogeneous hybrid-precision finite-volume
method for compressible flow \citep{brogi_etal_2024,wang_xia_chen_2025}.
```

New:
```latex
… Wang, Xia, and Chen study a heterogeneous hybrid-precision finite-volume
method for compressible flow, set against the wider linear-algebra
mixed-precision landscape surveyed by \citet{higham_mary_2022}
\citep{brogi_etal_2024,wang_xia_chen_2025}.
```

Acceptance criteria:

- `\citet{higham_mary_2022}` appears exactly once in C1.
- The qualifier "linear-algebra" is present, so the citation is **not**
  read as CFD evidence.
- Worker's local word delta ≤ +12.

Word delta: **+5** (net after small phrasing adjustments).

Main-agent review:

- Run `rg -n "higham_mary_2022" report1/phd-thesis-template-2.4/Chapter*/chapter*.tex`;
  confirm one hit, in Chapter 1.

---

## Worker 11 (Optional, run last): C3 §3.1 — TikZ Schematic of Finite-Volume Cell

This worker is **optional**. It adds an explanatory figure to C3 §3.1 without
costing word budget (TikZ figure body + caption are excluded from in-text
count). Skip if the running total after Worker 8 exceeds 7,440.

Assigned file:

```text
report1/phd-thesis-template-2.4/Chapter3/chapter3.tex
```

Assigned region: after Equation~\ref{eq:fv-update} inside
`% <<SECTION_1_BEGIN>> … % <<SECTION_1_END>>`.

Task: insert a small TikZ schematic showing a single Cartesian cell
$C_{ij}$ with the four interface fluxes $\widehat F_{i\pm1/2,j}$ and
$\widehat G_{i,j\pm1/2}$ entering/leaving, plus the cell-average symbol
$\bar U_{ij}^n$.

```latex
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[>=latex,scale=1.0]
  \draw (-1.6,-1.2) rectangle (1.6,1.2);
  \node at (0,0) {$\bar U_{ij}^n$};
  \draw[->,thick] (-2.4, 0) -- (-1.65,0) node[midway,above] {$\widehat F_{i-\tfrac{1}{2},j}$};
  \draw[->,thick] ( 1.65, 0) -- ( 2.4, 0) node[midway,above] {$\widehat F_{i+\tfrac{1}{2},j}$};
  \draw[->,thick] ( 0,-2.0) -- ( 0,-1.25) node[midway,right] {$\widehat G_{i,j-\tfrac{1}{2}}$};
  \draw[->,thick] ( 0, 1.25) -- ( 0, 2.0) node[midway,right] {$\widehat G_{i,j+\tfrac{1}{2}}$};
\end{tikzpicture}
\caption{Finite-volume conservative update: the cell average $\bar U_{ij}^n$
evolves by the difference of interface fluxes $\widehat F_{i\pm\tfrac{1}{2},j}$ in
$x$ and $\widehat G_{i,j\pm\tfrac{1}{2}}$ in $y$, following
Equation~\ref{eq:fv-update}.}
\label{fig:ch3-fv-cell}
\end{figure}
```

Add one short prose sentence (≤ 12 words) referencing it:

```latex
Fig.~\ref{fig:ch3-fv-cell} sketches the four interface fluxes in this update.
```

Acceptance criteria:

- TikZ package is already loaded (preamble check); no new package needed.
- `fig:ch3-fv-cell` is referenced exactly once.
- C3 in-text word delta ≤ +12.

Word delta: **+12** (only the prose sentence counts; TikZ body and caption do not).

Main-agent review:

- Run final `texcount` to confirm total ≤ 7,500.
- Skip this worker if running total exceeds 7,440 after Worker 10.

---

## Main-Agent Integration Review (after every worker)

1. Re-read only the edited region plus one paragraph before/after.
2. Confirm the worker's word delta cap was respected (run targeted `texcount`).
3. Confirm no forbidden-token regression (`rg` the forbidden-token list).
4. Confirm no broken `\ref`/`\cite` introduced (`pdflatex -draftmode`).
5. Append a 2-line note to integration log.

## Final Three-Round Self-Check

After all workers complete:

### Round 1: Brief, Handbook, Supervisor Coverage

Score against:

- Project brief 5 × 20% categories;
- Supervisor map remaining items (esp. C5 sig-fig, C3 §3.6 Riemann solvers, C6 SNR);
- Manuscript outline section ownership.

Pass threshold: 95/100.

### Round 2: Citation, Style, Word-Budget Audit

Run:

```powershell
texcount -inc -sum report1/phd-thesis-template-2.4/thesis.tex
rg -n "\\cite[a-z]*\{[^}]+\}" report1/phd-thesis-template-2.4/Chapter*/chapter*.tex report1/phd-thesis-template-2.4/Abstract/abstract.tex
bibtex report1/phd-thesis-template-2.4/thesis
```

Confirm:

- Total in-text ≤ 7,500.
- 3 new keys cited at least once each.
- No undefined citation, no missing-key warning.
- No bibliography metadata invented; orphans archived.

Pass threshold: 95/100.

### Round 3: Mechanical, LaTeX, Forbidden-Token, Algorithm-Style Check

```powershell
rg -n "week[0-9]+|\bD1\b|\bD2\b|HLLC-fill|config12|LW12/config12|\bP1\b|USE_GPU|Lyapunov exponent|Lyapunov-like|wolf_etal|eckmann|well resolved in binary64|vertical interface|TODO|drafting comment" report1/phd-thesis-template-2.4/Chapter*/chapter*.tex
rg -n "begin\{algorithm\}" report1/phd-thesis-template-2.4/Chapter4/chapter4.tex
```

Confirm:

- Zero forbidden-token hits.
- Chapter 4 has ≥ 3 `\begin{algorithm}` blocks (Algorithm 1 dispatch + Algorithm 2 MUSCL-Hancock + Algorithm 3 HLLC flux).
- Compile chain: `pdflatex` → `bibtex` → `pdflatex` × 2 produces zero new errors / undefined-references.

Pass threshold: no new LaTeX error, no forbidden hit.

## Strict Scoring Rubric (after Round 3)

| Area | Points | Check |
|------|---:|---|
| Literature & background | 20 | Higham-Mary added as linear-algebra contrast; brief sub-bullets all visibly covered. |
| Mathematical theory | 20 | Davis_1988 explicit cite; HLLD/Roe-MHD named; SNR formalisation present. |
| Code description | 20 | 4-item ease-of-impl list; 3 algorithm boxes example-style; reproducibility harness paragraph intact. |
| Validation | 20 | C5 numerical precision unified to 3-4 sig fig; CPU/GPU table preserved; SNR region figure adds spatial dimension. |
| Quality of write-up | 20 | C6 SNR para integrates; word total ≤ 7,500; bib reorganised; no forbidden tokens; no new compile errors. |

Target: **97/100**.

If a row scores < 18, dispatch one focused repair worker and rerun Round 3
for that row only.

## Final Response Format

Respond in Chinese with:

- which workers ran and in what order;
- baseline → final texcount delta (with cumulative after each worker);
- each new citation key and where it was cited;
- bib reorder result;
- Round 1, 2, 3 outcomes;
- final rubric scores;
- whether Worker 11 ran;
- any remaining defect that should be addressed in a separate pass.

Do not commit. Do not modify `experiments/`, `src/`, or `cfg`.
