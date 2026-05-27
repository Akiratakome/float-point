# Report 1 Review3 Revision Plan (v1, fresh)

**Date:** 2026-05-26
**Branch:** `report`
**Target manuscript:** `report1/phd-thesis-template-2.4/`
**Wordcount baseline:** 7697 words (commit `9a48cbf`). Target window: **7750–7800**. **Hard cap: 7800.**
**Scope:** Manuscript-only edits + figure-file refresh responding to the third-round review and supervisor brief. No solver / cfg / harness changes. Edits are precise to **subsection level**; chapters or sections not listed below are untouched.

**Reader-facing naming rules (apply to every inserted manuscript word):**
- No internal codenames in manuscript text: no "week N", no "batch N", no "pack A/B/C…", no "review3", no "report-facing", no "legacy".
- "First-use spell-out" applies to **paper-concept terminology only** (HLLC, MUSCL, MCA, LoSoS, σ\_FP, SSIM, etc., already handled in earlier chapters). It does **not** apply to hardware / compute-centre names — keep the brief forms already used in the existing draft: `CSC`, `RTX 4060 Laptop GPU`, `RTX 5090`, `i9-13900H`, `AMD EPYC`.
- Cross-references use chapter / section names exactly as they appear in the manuscript (e.g. "Chapter 5 Section *Toro Test 2 Branch Stability*"), never internal numbering invented by this plan.

This plan supersedes any earlier review-3 plan in this directory.

---

## 0. Workflow Architecture — Serial Subagent + Main-Process Audit

The main process does **not** edit `.tex` files. It dispatches one sub-agent per batch in serial, then audits before launching the next.

### Sub-agent envelope (every batch receives)
1. Target file paths + `\section{...}` or `\subsection*{...}` markers (no raw line numbers — those drift).
2. Exact source evidence path(s) (`experiments/.../summary.md`).
3. Verbatim text to replace OR new text to insert (no paraphrase license).
4. Required hedge phrases (must appear).
5. Forbidden phrases (must not appear).
6. Word-delta budget for the batch.
7. Acceptance criteria (greps + texcount delta).

### Main-process audit between batches
For each completed batch:
- `texcount -inc -sum -1 …` delta vs pre-batch snapshot — must match budget ± 10 words.
- `grep` for forbidden phrases — must return 0 hits inside the touched files.
- `grep` for required hedges — must return ≥ 1 hit per required hedge.
- Read the diff and verify no new claims, no figure/table renumbering side-effects.
- If any gate fails: dispatch a fix-up sub-agent with explicit diff + failed gate. Never silently proceed.

### Batch order (serial)
| # | Batch | Dependencies | Word-Δ budget |
|---|---|---|---|
| 0 | Numeric writing fixes (Eq 3.21 wording; Ch3 §"Precision-Sensitive Decision Points" cross-link to Ch5 §"Toro Test 2 Branch Stability"; per-case CFL line in Ch4 §"Algorithmic Structure of the Implementation") | none | +50 / −0 |
| 1 | MCA $n=30$ reframe (Ch4 §"Test-Case Matrix and Metrics" + Ch6 §"Precision Adequacy and Region-Aware Diagnostics" + Ch6 §"Limitations and Report 2 Direction" item 4) **and** refresh of the five Ch6 figure files (see §12.1) from `experiments/review3_mca_n30/report1_d2_replots/` | n=30 MCA evidence | +30 / −60 |
| 2 | Toolchain consolidation (Ch4 §"Implementation Route and Comparability Principle" + Ch5 §"Matched CPU/GPU Comparison" + Ch6 §"Hardware and Implementation Sensitivity" + Ch7 §"Limitations") | Toro3/5 CSC strict rerun + CPU-only-vs-CUDA-cpu sanity | +20 / −60 |
| 3 | Reference provenance + LW12 hierarchy (Ch4 §"Reference-Solution Strategy" + Ch5 §"Two-Dimensional Euler Validation" + Ch6 §"Limitations and Report 2 Direction" item 1) | LW3 RTX 5090 preflight + LW12 1600² hierarchy | +90 / −20 |
| 4 | GPU timing + cross-hardware framing (Ch4 §"Precision and Hardware Variants" after Table 4.3) | LW3 N=400 timing split | +70 / −20 |
| 5 | Branch-rule + Toro3/5 checkpoint + $\sigma_{\mathrm{FP}}$ caption + $\texttt{p8}$ caveat + MUSCL literature (Ch5 §"Matched CPU/GPU Comparison" / Table 5.5 + Ch5 §"Compiler, Branch, Solver, and Drift-Growth Sensitivity" Table 5.6 + Ch6 §"Precision Adequacy and Region-Aware Diagnostics" Fig 6.1 caption + Ch5 §"One-Dimensional Euler Validation") | Toro3/5 checkpoints + local branch-rule fill | +60 / −30 |
| 6 | Compression pass (compensating cuts in Ch3 §"Extension to Ideal MHD", Ch6 §"Hardware and Implementation Sensitivity", Ch6 §"Limitations and Report 2 Direction") + final texcount gate + evidence-to-claim consistency check (§12.3) | none | net to land 7750–7800 |

Estimated raw additions ≈ +320, raw deletions ≈ −190. Batch 6 absorbs the residual to hit 7750–7800.

---

## 1. Current-Draft Integration Audit

### 1.1 Already integrated (leave alone unless cross-referenced)
| Item | Location |
|---|---|
| Dedner GLM `τ ≡ c_p² / c_h²` definition | Ch3 §"Extension to Ideal MHD" |
| LW3 1D self-convergence row + slow-order caveat | Ch5 §"One-Dimensional Euler Validation" |
| Toro2 `N* = 0` symmetry mechanism | Ch5 §"Toro Test 2 Branch Stability" |
| 1D shock-tube MUSCL L1 first-order band/smooth split | Ch5 §"One-Dimensional Euler Validation" |
| LW3 N=400 fp32/fp64 ratio framing | Ch5 §"Single- and Double-Precision Comparison" |
| `R_ref` definition + degenerate-denominator caveat | Ch4 §"Reference-Solution Strategy" |
| SNR framing equation in Ch6 | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" |

### 1.2 Partially integrated
| Item | Gap |
|---|---|
| LW3 1600² provenance | Ch4 §"Reference-Solution Strategy" mentions "CSC RTX 5090 strict-HLLC GPU reference candidate" but is missing the N=400 / N=800 fp64 CPU/GPU `L1=L∞=ULPmax=0` preflight numbers. |
| GPU timing reframe | Ch4 §"Precision and Hardware Variants" mentions memory/layout but lacks quantified RTX 4060 Laptop fp64 (≈0.24 TFLOPS) vs i9-13900H AVX2 fp64 (≈1 TFLOPS) and the CSC RTX 5090 8.53 s / 0.57 s counter-evidence. |
| §3.5 perturbation relative expression | Ch3 §"Precision-Sensitive Decision Points" mentions "when terms are non-zero" but has no explicit cross-link to the Toro2 `N*=0` degeneracy in Ch5. |
| Ch6 §"Hardware and Implementation Sensitivity" CPU sanity | Cites legacy WSL/GCC strict rerun; needs to point at the CSC `cpu_only_vs_cuda_cpu_sanity` evidence. |
| Ch5 §"Matched CPU/GPU Comparison" last paragraph | Same WSL/GCC framing; needs the CSC sanity replacement. |

### 1.3 Not yet integrated
| Issue | Target subsection |
|---|---|
| n=30 MCA evidence | Ch4 §"Test-Case Matrix and Metrics" (MCA paragraph); Ch6 §"Precision Adequacy and Region-Aware Diagnostics" (LoSoS-quantile paragraph + new p32 sentence + p8 caveat) |
| Toro3/Toro5 checkpoint coverage (25/50/75/100 % t_end, fp64/fp32, zero drift) | Ch5 §"Matched CPU/GPU Comparison" / Table 5.5 |
| Branch-rule expanded coverage (Sod, stationary contact, Toro3, Toro5 zero; LW3 roundoff; Toro2 degenerate) | Ch5 §"Compiler, Branch, Solver, and Drift-Growth Sensitivity" / Table 5.6 |
| LW12 1600² hierarchy + observed L1 order ≈ 0.535 + slow-convergence caveat | Ch4 §"Reference-Solution Strategy"; Ch5 §"Two-Dimensional Euler Validation"; Ch6 §"Limitations and Report 2 Direction" item 1 |
| Eq 3.21 "specific total-energy form" wording fix | Ch3 §"HLLC and Rusanov Fluxes" |
| Per-case CFL values (Sod = 0.8, LW3 = 0.5, LW12 = 0.4) | Ch4 §"Algorithmic Structure of the Implementation" / Algorithm 1 caption |
| σ\_FP,L1 = spatial mean clarification + fp64 floor caveat | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" / Fig 6.1 caption |
| Toolchain consolidation removing Windows BuildTools dependency | Ch4 §"Implementation Route and Comparability Principle"; Ch5 Table 5.5 footnote; Ch7 §"Limitations" |
| GPU timing quantitative explanation + RTX 5090 CSC counter-evidence (8.53 s CPU vs 0.57 s GPU) | Ch4 §"Precision and Hardware Variants" after Table 4.3 |
| MUSCL near-first-order L1 literature citation (ECCOMAS 2016, Berthon) | Ch5 §"One-Dimensional Euler Validation" |

### 1.4 Risky / overclaimed wording currently in draft
| Snippet | Location | Action |
|---|---|---|
| "for Toro3 and Toro5 the evidence is final-output only" | Ch5 §"Matched CPU/GPU Comparison" Table 5.5 caption | Replace with "saved-output plus four-checkpoint evidence for all five cases (Toro3/Toro5 checkpoints from CSC strict rerun)". |
| "this is CPU-only sanity evidence, not general cross-toolchain equivalence" | Ch6 §"Hardware and Implementation Sensitivity" | Reword to CSC cpu-only vs CUDA-with-`device=cpu` bit-identity statement. |
| "WSL/GCC strict rerun of Toro3 and Toro5 matched the existing strict CPU outputs" | Ch5 §"Matched CPU/GPU Comparison" final paragraph | Replace with CSC sanity statement and drop the "checkpoint coverage is uneven by design" sentence (now resolved). |
| "the two- or three-sample MCA diagnostics are spatial sensitivity maps rather than statistical distribution estimates" | Ch6 §"Limitations and Report 2 Direction" item 4 | Replace with n=30 framing. |
| Table 4.3 caption "Computational-cost context only." | Ch4 §"Precision and Hardware Variants" | Keep caption, **add** one quantification sentence + CSC RTX5090 8.53 s / 0.57 s counter-evidence after the table. |
| p8 quantile rows treated alongside p16/p32 without final-time caveat | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" | Add p8 header-drift caveat (binary header ≈ 0.3035 vs requested t = 0.3). |
| MCA sentence "raw-field quantiles use only two or three samples per virtual precision, so they are spatial diagnostics, not statistically meaningful distribution or confidence estimates" | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" | Replace with n=30 framing referencing Sohier 2021 guidance compliance. |
| MSVC BuildTools "for Toro3 and Toro5" wording | Ch6 §"Limitations and Report 2 Direction" item 2 | Add CSC/Linux strict rerun reference; keep MSVC mention as historical only. |

---

## 2. Evidence Pack → Subsection Binding (review3.md packs A–H)

| Pack | Source `summary.md` | Headline fact to insert | Target subsection(s) | Replaces |
|---|---|---|---|---|
| **A** MCA n=30 | `experiments/review3_mca_n30/summary.md` | n=30 unique seeds at p8/p16/p32/p53 × HLLC/Rusanov, no NaN/Inf; p32 noise/error > 1 cells = **0 %**; p8 has final-time header drift (binary header ≈ 0.3035 vs t = 0.3 requested). | Ch4 §"Test-Case Matrix and Metrics" MCA paragraph; Ch6 §"Precision Adequacy and Region-Aware Diagnostics" (LoSoS paragraph + new p32 adequacy sentence + new p8 caveat sentence); Ch6 §"Limitations and Report 2 Direction" item 4. | "two or three samples per virtual precision" / "spatial diagnostics, not statistically meaningful". |
| **B** Toro3/5 toolchain | `experiments/add_experiment/toolchain_toro35/summary.md` | CSC/Linux strict fp64-CPU vs fp64-GPU and fp32-CPU vs fp32-GPU final-state `L1 = L∞ = ULPmax = 0` for Toro3 and Toro5. | Ch4 §"Implementation Route and Comparability Principle" toolchain paragraph; Ch5 §"Matched CPU/GPU Comparison" Table 5.5 footnote. | Windows BuildTools dependency framing for report-facing CPU/GPU evidence. |
| **C** CPU-only vs CUDA-cpu | `experiments/add_experiment/cpu_only_vs_cuda_cpu_sanity/summary.md` | CPU-only strict binary and CUDA-enabled strict binary with `device=cpu` are bit-identical (`L1 = L∞ = ULPmax = 0`) on Toro3/Toro5 saved states, fp64 and fp32. | Ch5 §"Matched CPU/GPU Comparison" final paragraph; Ch6 §"Hardware and Implementation Sensitivity". | "WSL/GCC strict CPU sanity" attribution and the implicit "CPU evidence depends on the CUDA-enabled binary" concern. |
| **D** Toro3/5 checkpoints | `experiments/add_experiment/toolchain_toro35_checkpoints/summary.md` | Four checkpoints at 25/50/75/100 % t_end for Toro3 and Toro5, fp64/fp32, CPU vs GPU: all zero. | Ch5 §"Matched CPU/GPU Comparison" Table 5.5 (Saved-checkpoints column for Toro3/Toro5) + caption clause. | "for Toro3 and Toro5 the evidence is final-output only". |
| **E** LW3 5090 preflight | `experiments/add_experiment/lw3_5090_preflight/summary.md` | LW3 N=400 and N=800 fp64 strict CSC CPU vs RTX 5090 GPU: `L1 = L∞ = ULPmax = 0`. | Ch4 §"Reference-Solution Strategy". | Implicit-only "RTX 5090 reference candidate" framing. |
| **F** LW12 1600² hierarchy | `experiments/add_experiment/lw12_1600_reference/summary.md` and `reference_scaled_ratios.csv` | 400→800→1600 hierarchy finite; observed ρ L1 order ≈ **0.5348**; `R_ρ` ≈ 8.53e-5 at N=400 and ≈ 3.37e-4 at N=800 against the 1600² reference. | Ch4 §"Reference-Solution Strategy" (replace "no analogous 1600² row is claimed for LW12"); Ch5 §"Two-Dimensional Euler Validation" (LW12 self-convergence row); Ch6 §"Limitations and Report 2 Direction" item 1. | "LW12 800² only" limitation framing — **not** to be replaced by "clean asymptotic convergence". |
| **G** LW3 timing split | `experiments/add_experiment/lw3_timing_split/summary.md` | CSC strict path LW3 N=400 fp64 timing: CPU 8.53 s, GPU 0.57 s (end-to-end solver timing, not kernel-only). | Ch4 §"Precision and Hardware Variants" after Table 4.3. | Unquantified "memory/layout" hand-wave. |
| **H** Local fill (branch-rule + fp32 matrix) | `experiments/review3_local_fill/summary.md` | Branch-rule strict `<` vs baseline `≤`: Sod, stationary contact, Toro3, Toro5 zero; LW3 N=200 roundoff-scale (5.03e-16); Toro2 degenerate (`N*=0`, strict `<` fails to complete within 600 s, `≤` completes). fp32 compiler matrix extension: O2/O3 zero; Ofast-fastmath nonzero. | Ch5 §"Compiler, Branch, Solver, and Drift-Growth Sensitivity" branch-rule row of Table 5.6 (fp32 matrix only if Batch 6 budget allows). | "branch-rule comparison only covers LW3" implication. |

---

## 3. Subsection-Level Edit Spec

### 3.1 Ch3 §"HLLC and Rusanov Fluxes" (Eq 3.21 caption)
- **Replace:** the "the fourth entry is the specific total-energy form" wording.
- **With:** "the fourth entry has units of energy density once the prefactor is included; the bracketed factor is total energy per unit mass plus the contact-pressure correction".
- **Δ words:** 0.

### 3.2 Ch3 §"Precision-Sensitive Decision Points" (end-of-section sentence)
- **Insert at the end of the section**, one sentence:
  > When `N* = 0` exactly by symmetry (the degenerate case examined in Ch5 §"Toro Test 2 Branch Stability"), the relative perturbation in Eq~\ref{eq:ch3-sstar-perturbation} is undefined and the sign of the computed `S*` is set by accumulated rounding noise rather than first-order linearisation.
- **Δ words:** +30.

### 3.3 Ch4 §"Algorithmic Structure of the Implementation" (Algorithm 1 caption)
- **Insert** at the end of Algorithm 1's caption or in the surrounding paragraph:
  > The CFL coefficient is fixed per case: `C_CFL = 0.8` for 1D tests, `C_CFL = 0.5` for LW3, `C_CFL = 0.4` for LW12.
- **Δ words:** +20.

### 3.4 Ch4 §"Implementation Route and Comparability Principle" (toolchain paragraph)
- **Replace** the existing Toro3/Toro5 Windows BuildTools paragraph with:
  > Toro3 and Toro5 were rerun on the CSC Linux/strict-IEEE build for the matched CPU/GPU comparison; Sod, LW3, and LW12 use Linux/WSL throughout. Each within-case CPU/GPU comparison stays within one matched binary, and the two toolchains are reported here as cross-hardware evidence (i9-13900H with NVIDIA RTX 4060 Laptop GPU, against an AMD EPYC host with NVIDIA RTX 5090 on CSC), not as a toolchain confound.
- **Δ words:** +10 / −30 ≈ −20.

### 3.5 Ch4 §"Test-Case Matrix and Metrics" (MCA paragraph)
- **Replace** the existing "Verificarlo … two or three samples" framing with:
  > Each Verificarlo virtual-precision configuration is sampled with `n = 30` independent seeds at `p8`, `p16`, `p32`, and `p53` for both HLLC and Rusanov, supporting the per-cell `σ_FP` scale used in Ch6 together with q05 / q25 / median spatial quantiles. The sample count exceeds the minimum recommended by \citet{sohier_etal_2021} for the chosen significant-digits / confidence regime.
- **Δ words:** +10 / −20 ≈ −10.

### 3.6 Ch4 §"Precision and Hardware Variants" (after Table 4.3)
- **Insert** two sentences:
  > Quantitatively, the NVIDIA RTX 4060 Laptop GPU has a peak fp64 throughput of approximately 0.24 TFLOPS, against approximately 1 TFLOPS for the i9-13900H using AVX2; the GPU $\approx$ CPU fp64 result on this hardware is therefore consistent with consumer-fp64 throughput under the chosen memory layout rather than a kernel-correctness anomaly. On the CSC strict-IEEE path (AMD EPYC host with an NVIDIA RTX 5090), the same fp64 LW3 $N=400$ case runs in 8.53 s on CPU and 0.57 s on GPU (end-to-end solver timing), confirming that an fp64-capable GPU dominates the same code path when the hardware allows it.
- **Δ words:** +70.

### 3.7 Ch4 §"Reference-Solution Strategy"
- **Replace** the "no analogous $1600^2$ row is claimed for LW12" sentence with:
  > Liska--Wendroff configuration 12 (LW12) is paired with both an $800^2$ fp64 numerical reference and a complementary $400^2 \to 800^2 \to 1600^2$ self-convergence hierarchy; the observed density $L_1$ order is approximately $0.535$ and the corresponding $R_\rho$ against the $1600^2$ field is $\approx 8.53\times10^{-5}$ at $N=400$ and $\approx 3.37\times10^{-4}$ at $N=800$. The slow $L_1$ order is recorded as a caveat on $R_{\mathrm{ref}}$ magnitudes; LW12 is not claimed to be asymptotically converged.
- **Insert** one sentence on the LW3 reference provenance:
  > The LW3 $1600^2$ field is generated on the CSC strict-IEEE path with an NVIDIA RTX 5090, and is matched by a CPU vs RTX 5090 GPU preflight at $N=400$ and $N=800$ with $L_1 = L_\infty = \mathrm{ULP}_{\max} = 0$ in fp64; the RTX 5090 is used here only for high-resolution reference generation, separately from the RTX 4060 Laptop GPU used for the matched CPU/GPU comparison study.
- **Δ words:** +70 / −15 $\approx$ +55.

### 3.8 Ch5 §"One-Dimensional Euler Validation" (literature anchor)
- **Insert** one sentence in the existing convergence-order paragraph:
  > Observed L1 orders of 0.65–0.79 in 1D and ≈ 0.47 in 2D are consistent with the near-first-order L1 convergence reported in the literature for MUSCL-type schemes on shock-containing problems on uniform grids \citep{eccomas_2016_muscl,berthon_muscl_hancock,toro2009,leveque_2002}.
- **Δ words:** +25.

### 3.9 Ch5 §"Two-Dimensional Euler Validation" (Table 5.4 row + caveat)
- **Insert** a new LW12 self-convergence row in Table 5.4: `L1(400 vs 800) = 2.3177 × 10⁻³`, `L1(800 vs 1600) = 1.5998 × 10⁻³`, observed order ≈ 0.535.
- **Insert** one caveat sentence after the table:
  > LW12 self-convergence is slow (L1 order ≈ 0.535); `R_ρ` against the 1600² reference should be read with this rate in mind rather than as exact-solution agreement.
- **Δ words:** +35.

### 3.10 Ch5 §"Matched CPU/GPU Comparison" (Table 5.5 + footnote + final paragraph)
- **Update** Table 5.5 Toro3 and Toro5 "Saved checkpoints" column entries from `none` to `4 at $N=200$ (25/50/75/100 % of $t_{\mathrm{end}}$)`. Result column stays `zero`.
- **Replace** the footnote with:
  > Toro3 and Toro5 are reported here from the CSC strict-IEEE rerun, with four saved checkpoints in fp64 and fp32 and $L_1 = L_\infty = \mathrm{ULP}_{\max} = 0$ between the CPU and GPU saved states. A separate sanity check on the same CSC build showed that the CPU-only strict binary and the CUDA-enabled strict binary with $\texttt{device=cpu}$ produce bit-identical Toro3 and Toro5 saved states in both fp64 and fp32, so the CPU branch is not an artefact of running CPU code through a CUDA-enabled binary. Identity is restricted to saved conservative states under strict IEEE for the tested cases.
- **Drop** the clause "for Toro3 and Toro5 the evidence is final-output only" from the table caption.
- **Replace** the last paragraph ("A CPU-only sanity check (WSL/GCC strict rerun…) …") with:
  > A separate sanity check on the CSC strict-IEEE build showed that the CPU-only binary and the CUDA-enabled binary with $\texttt{device=cpu}$ produce bit-identical Toro3 and Toro5 saved states in both fp64 and fp32; the CPU/GPU dispatch comparison is therefore not an artefact of running CPU code through a CUDA-enabled binary. The claim remains restricted to saved-state identity under strict IEEE for the tested cases.
- **Δ words:** +15 / −40 $\approx$ −25.

### 3.11 Ch5 §"Compiler, Branch, Solver, and Drift-Growth Sensitivity" (Table 5.6 branch-rule row + prose)
- **Replace** the branch-rule row of Table 5.6 with an expanded entry:
  > HLLC branch, `≤` vs `<`: Sod, stationary contact, Toro3, Toro5 = 0 at final time; LW3 200² = 5.03 × 10⁻¹⁶ (roundoff-scale); Toro2 = degenerate (`N* = 0` symmetry; strict `<` does not complete within 600 s while baseline `≤` completes — see §"Toro Test 2 Branch Stability").
- **Δ words:** +20 / −5 ≈ +15.

### 3.12 Ch6 §"Precision Adequacy and Region-Aware Diagnostics" (LoSoS paragraph + Fig 6.1 caption + p32 sentence + p8 caveat)
- **Replace** the "raw-field quantiles use only two or three samples per virtual precision …" sentence with:
  > All MCA results in this chapter use `n = 30` independent seeds per (precision, solver); raw-field q05 / q25 / median quantiles are therefore distributional estimates within the sample-count guidance of \citet{sohier_etal_2021}, not exploratory single-realisation snapshots.
- **Insert** a new sentence after the noise-to-error paragraph:
  > At `p32`, the fraction of LW3 cells with MCA noise above the reference-error scale is `0 %` for both HLLC and Rusanov, supporting `p32` as adequate for this LW3 case at the tested resolution.
- **Insert** a `p8` caveat sentence (either inline or as a footnote):
  > `p8` MCA results are reported as a low-precision stress diagnostic only; the binary checkpoint header reaches `t ≈ 0.3035` while stderr stops at the requested `t = 0.3`, so `p8` quantiles must not be read as final-time equivalents to `p16` / `p32` / `p53`.
- **Rewrite Fig 6.1 caption** to:
  > MCA-estimated `σ_FP,L1` for LW3 density: spatial mean of the per-cell sample standard deviation across `n = 30` seeds. Values near 10⁻¹¹ at `p53` approach the fp64 noise floor and bound rather than measure the rounding scale at that precision.
- **Δ words:** +35 / −20 ≈ +15.

### 3.13 Ch6 §"Hardware and Implementation Sensitivity"
- **Replace** the "WSL/GCC strict CPU reruns for Toro3 and Toro5 matched the existing strict CPU saved outputs with zero drift, but this is CPU-only sanity evidence, not general cross-toolchain equivalence." sentence with:
  > A sanity check on the CSC strict-IEEE build showed that the CPU-only binary and the CUDA-enabled binary with $\texttt{device=cpu}$ produce bit-identical Toro3 and Toro5 saved states in fp64 and fp32, so the CPU/GPU dispatch comparison is not an artefact of running CPU code through a CUDA-enabled binary; the claim remains restricted to saved-state identity under strict IEEE for the tested cases.
- **Δ words:** +5 / −20 $\approx$ −15.

### 3.14 Ch6 §"Limitations and Report 2 Direction"
- **Item 1:** replace the LW12 wording with:
  > LW12 is paired with an $800^2$ fp64 numerical reference and a $400^2 \to 800^2 \to 1600^2$ self-convergence hierarchy with slow $L_1$ order $\approx 0.535$; $R_\rho$ magnitudes should be interpreted against this rate rather than as exact-solution agreement. LW3 retains the $400^2$/$800^2$/$1600^2$ fp64 self-convergence reference.
- **Item 2:** add a short clause noting that the Toro3 and Toro5 evidence is now the CSC Linux strict-IEEE rerun; the earlier MSVC Build Tools entry is retained only as a historical comparator.
- **Item 4:** replace with:
  > Verificarlo $\texttt{p32}$ is a virtual mantissa precision distinct from IEEE binary32; the $n = 30$ MCA diagnostics support sample-quantile reading at $\texttt{p16}$, $\texttt{p32}$, and $\texttt{p53}$, while $\texttt{p8}$ is a low-precision stress diagnostic only because final-time alignment is approximate (the binary checkpoint header reaches $t \approx 0.3035$ while stderr stops at the requested $t = 0.3$).
- **Δ words:** +25 / −20 $\approx$ +5.

### 3.15 Ch7 §"Limitations" (single sentence)
- **Replace** the "within each tested case on its Windows BuildTools or Linux/WSL toolchain" clause with:
  > within each tested case (the CSC Linux strict-IEEE rerun covers Toro3 and Toro5 final state plus four checkpoints; Sod, LW3, and LW12 are covered on the local Linux/WSL toolchain).
- **Δ words:** +10 / −5 $\approx$ +5.

### 3.16 References (`References/references.bib`)
**Add** two new entries (the literature anchor in §3.8 cites both):

```bibtex
@inproceedings{eccomas_2016_muscl,
  author    = {Wellner, Jens},
  title     = {Comparison of Finite Volume High-Order Schemes for the Two-Dimensional {E}uler Equations},
  booktitle = {{VII} European Congress on Computational Methods in Applied Sciences and Engineering ({ECCOMAS Congress 2016})},
  editor    = {Papadrakakis, M. and Papadopoulos, V. and Stefanou, G. and Plevris, V.},
  address   = {Crete Island, Greece},
  month     = jun,
  year      = {2016},
  pages     = {Paper 9251},
  note      = {DLR Institute of Propulsion Technology, Cologne, Germany}
}

@article{berthon_muscl_hancock,
  author  = {Berthon, Christophe},
  title   = {Why the {MUSCL--H}ancock scheme is {$L^1$}-stable},
  journal = {Numerische Mathematik},
  volume  = {104},
  number  = {1},
  pages   = {27--46},
  year    = {2006},
  doi     = {10.1007/s00211-006-0007-4}
}
```

**Keep** existing `sohier_etal_2021`, `toro2009`, `leveque_2002`, `dedner_2002`, `liska_wendroff_2003`, `brogi_etal_2024`, `wang_xia_chen_2025` (already present and verified).

**Optional** (only if word budget allows in Batch 6): add Croci et al. 2022 and Klöwer 2020 as defensive depth citations in Ch2 §"Background" or Ch6 §"Limitations and Report 2 Direction". **Default = skip** unless Batch 6 has $>$ 30 words of headroom.

---

## 4. Replace / Soften / Remove / Leave Unchanged

### 4.1 Replace (verbatim text → new text)
- Ch3 §"HLLC and Rusanov Fluxes": "specific total-energy form" wording (§3.1 above).
- Ch4 §"Implementation Route and Comparability Principle": toolchain paragraph (§3.4 above).
- Ch4 §"Test-Case Matrix and Metrics": MCA framing paragraph (§3.5 above).
- Ch5 §"Matched CPU/GPU Comparison": Table 5.5 footnote and final paragraph (§3.10 above).
- Ch5 §"Compiler, Branch, Solver, and Drift-Growth Sensitivity": Table 5.6 branch-rule row (§3.11 above).
- Ch6 §"Precision Adequacy and Region-Aware Diagnostics": "two or three samples" sentence and Fig 6.1 caption (§3.12 above).
- Ch6 §"Hardware and Implementation Sensitivity": WSL/GCC sanity sentence (§3.13 above).
- Ch6 §"Limitations and Report 2 Direction": items 1, 2, 4 (§3.14 above).
- Ch7 §"Limitations": toolchain clause (§3.15 above).

### 4.2 Soften
- Ch4 §"Implementation Route and Comparability Principle": Windows BuildTools framing reduced to legacy-only mention.
- Ch5 §"Matched CPU/GPU Comparison" Table 5.5 caption: drop "final-output only" clause.

### 4.3 Remove
- "for Toro3 and Toro5 the evidence is final-output only" (Ch5 Table 5.5 caption).
- "no analogous 1600² row is claimed for LW12" (Ch4 §"Reference-Solution Strategy").
- "checkpoint coverage is uneven by design (Sod, LW3, LW12 with checkpoints; Toro3, Toro5 final output only)" (Ch5 §"Matched CPU/GPU Comparison" final paragraph).

### 4.4 Leave unchanged
- All numerics in Tables 5.2, 5.3, and the non-LW12 rows of 5.4.
- Table 5.6 entries except the branch-rule row.
- Figures 6.2 / 6.3 / 6.4 themselves (verify they already point at `n = 30` outputs before final compile).
- All cfg defaults, solver formulas, HLLC algorithm.
- Ch5 §"Toro Test 2 Branch Stability" mechanism analysis.
- Ch5 §"Single- and Double-Precision Comparison" body.
- Ch1, Ch2, Ch3 §"Finite-Volume Update", Ch3 §"MUSCL-Hancock Reconstruction and Predictor Step", Ch3 §"Stability, Limiting, and Positivity", Ch3 §"Extension to Ideal MHD" — out of scope.

---

## 5. Numeric Values to Insert (single source of truth)

| Value | Insertion subsection | Source |
|---|---|---|
| `C_CFL`: 1D = 0.8, LW3 = 0.5, LW12 = 0.4 | Ch4 §"Algorithmic Structure of the Implementation" | `tests/cases/toro_1d/*.cfg`, `tests/cases/liska_wendroff_2d/config3.cfg`, `…/config12_n*.cfg` |
| `n = 30` MCA seeds; p8/p16/p32/p53 × HLLC/Rusanov; no NaN/Inf | Ch4 §"Test-Case Matrix and Metrics"; Ch6 §"Precision Adequacy and Region-Aware Diagnostics" | `experiments/review3_mca_n30/summary.md` |
| `p32` noise-to-error > 1 cells = **0 %** | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" | `experiments/review3_mca_n30/report1_d2_replots/summary.md` |
| `p8` final-time header drift: binary header ≈ 0.3035 vs requested 0.3 | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" + item 4 | `experiments/review3_mca_n30/summary.md` |
| Toro3/Toro5 checkpoints 25/50/75/100 % t_end, fp64/fp32, zero | Ch5 §"Matched CPU/GPU Comparison" Table 5.5 | `experiments/add_experiment/toolchain_toro35_checkpoints/summary.md` |
| Toro3/Toro5 CSC strict fp64/fp32 CPU/GPU final-state zero | Ch4 §"Implementation Route…"; Ch5 Table 5.5 footnote | `experiments/add_experiment/toolchain_toro35/summary.md` |
| CPU-only vs CUDA-with-`device=cpu` bit-identity Toro3/Toro5 fp64/fp32 | Ch5 §"Matched CPU/GPU Comparison" final paragraph; Ch6 §"Hardware and Implementation Sensitivity" | `experiments/add_experiment/cpu_only_vs_cuda_cpu_sanity/summary.md` |
| LW3 RTX 5090 preflight N=400 and N=800 fp64 strict CPU/GPU zero | Ch4 §"Reference-Solution Strategy" | `experiments/add_experiment/lw3_5090_preflight/summary.md` |
| LW12 hierarchy: L1(400v800) = 2.3177e-3, L1(800v1600) = 1.5998e-3, order ≈ 0.5348 | Ch5 §"Two-Dimensional Euler Validation" Table 5.4 row | `experiments/add_experiment/lw12_1600_reference/summary.md` |
| LW12 `R_ρ` against 1600² ref: ≈ 8.53e-5 at N=400, ≈ 3.37e-4 at N=800 | Ch4 §"Reference-Solution Strategy"; Ch5 §"Two-Dimensional Euler Validation" | `experiments/add_experiment/lw12_1600_reference/reference_scaled_ratios.csv` |
| LW3 N=400 fp64 CSC strict timing: CPU 8.53 s, GPU 0.57 s | Ch4 §"Precision and Hardware Variants" after Table 4.3 | `experiments/add_experiment/lw3_timing_split/summary.md` |
| Branch-rule expanded coverage (Sod, stationary contact, Toro3, Toro5 zero; LW3 N=200 roundoff; Toro2 degenerate at 600 s) | Ch5 §"Compiler, Branch, Solver, and Drift-Growth Sensitivity" Table 5.6 | `experiments/review3_local_fill/summary.md` |
| MUSCL near-first-order L1 literature anchors | Ch5 §"One-Dimensional Euler Validation" | `eccomas_2016_muscl`, `berthon_muscl_hancock` (to be added to `references.bib`) |

---

## 6. Required Hedges and Forbidden Phrases

### 6.1 Required hedges (per touched subsection, see §3 above)
| Hedge | Required in |
|---|---|
| "saved conservative state under strict IEEE, for the tested cases" | Ch5 §"Matched CPU/GPU Comparison" final paragraph; Ch6 §"Hardware and Implementation Sensitivity" |
| "same-precision CPU vs GPU" | Ch5 §"Matched CPU/GPU Comparison" Table 5.5 footnote |
| "high-resolution numerical reference with strict CSC CPU/GPU preflight at N = 400 and N = 800" | Ch4 §"Reference-Solution Strategy" |
| "slow L1 convergence (order ≈ 0.535)" | Ch5 §"Two-Dimensional Euler Validation"; Ch6 §"Limitations and Report 2 Direction" item 1 |
| "0 % of cells exceed reference-error noise floor for this LW3 case at the tested resolution" | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" |
| "low-precision stress diagnostic with approximate final-time alignment" | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" or item 4 |
| "end-to-end implementation timing under the chosen memory/layout; consistent with consumer fp64 throughput (≈ 0.24 TFLOPS on RTX 4060 Laptop)" | Ch4 §"Precision and Hardware Variants" after Table 4.3 |
| "RTX 5090 is used only for high-resolution reference generation; separate from RTX 4060 Laptop used for the matched CPU/GPU comparison" | Ch4 §"Reference-Solution Strategy" |
| "spatial mean of the per-cell sample standard deviation" | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" Fig 6.1 caption |
| "approach the fp64 noise floor and bound rather than measure" | Ch6 §"Precision Adequacy and Region-Aware Diagnostics" Fig 6.1 caption |

### 6.2 Forbidden phrases (must return 0 hits in the touched files after each batch)
1. "two or three samples"
2. "WSL/GCC strict rerun" / "WSL/GCC strict CPU"
3. "the evidence is final-output only"
4. "checkpoint coverage is uneven by design"
5. "no analogous 1600² row is claimed for LW12"
6. "specific total-energy form"
7. "C_CFL throughout" / "uniformly 0.8"
8. Any phrase asserting fp32 and fp64 are identical
9. Any phrase asserting CPU/GPU identity beyond saved state
10. Any phrase asserting LW12 is asymptotically converged

---

## 7. "Do Not Claim" List (supervisor + review3 constraints)

1. Do not claim fp32 and fp64 produce identical outputs anywhere.
2. Do not claim CPU/GPU bit-identity beyond saved conservative states for the tested strict-IEEE cases.
3. Do not claim intermediate-stage CPU/GPU identity inside a time step.
4. Do not claim clean asymptotic convergence for LW12 (only "completed 1600² hierarchy with slow L1 order ≈ 0.535").
5. Do not claim p8 final-time MCA quantiles are equivalent to p16 / p32 / p53.
6. Do not claim WSL/GCC strict CPU sanity is the primary CPU evidence; CSC strict and CPU-only-vs-CUDA-cpu sanity are.
7. Do not claim RTX 5090 timing or fp64 superiority generalises to RTX 4060 Laptop.
8. Do not claim a kernel-correctness GPU anomaly; restrict to end-to-end implementation timing on named hardware.
9. Do not claim branch-rule `<` is safe/unsafe in general; degeneracy is Toro2-`N*=0` specific.
10. Do not claim p32 noise/error = 0 % generalises beyond this LW3 case.
11. Do not claim stationary-contact fp32/fp64 ratio = ∞ is a precision-adequacy result.
12. Do not invent results from `add_experiment/` or `review3_mca_n30/`; cite the summary file.
13. Do not change solver numerics, cfg defaults, or harness.

---

## 8. Wordcount Strategy

Baseline 7697. Estimated gross additions ≈ +320, gross deletions ≈ −190 → ≈ +130 net. Target window 7750 – 7800, so Batch 6 must trim **≥ 60 words** beyond the in-flight deletions to safely sit at 7770 ± 15.

### 8.1 Batch-6 compression candidates (ranked)
| Target | Why | Savings |
|---|---|---|
| Ch6 §"Hardware and Implementation Sensitivity": "shock-bubble packet … no CPU/GPU comparison is made" sentence | Not part of Report 1 core claim; reviewer already flagged this as out-of-scope. | ~40 |
| Ch6 §"Limitations and Report 2 Direction" item 6 | Made redundant once shock-bubble sentence is trimmed. | ~20 |
| Ch3 §"Extension to Ideal MHD" final literature sentence (\citet{bard_dorelli_2014} GPU precedent) | Not load-bearing for Report 1 scope. | ~20 |
| Ch4 §"Test-Case Matrix and Metrics" RAPTOR forward-looking sentence (if present) | Forward-looking, can be deferred to Report 2. | ~15 |
| Ch6 §"Precision Adequacy and Region-Aware Diagnostics" — merge the σ\_FP definition sentence with the n=30 statement | Reduces duplication. | ~15 |

Total available compression ≈ 110 words. Batch 6 applies cuts until texcount lands in `[7750, 7800]` and stops as soon as it does.

### 8.2 Keep only in `experiments/.../summary.md` artefacts (do not expand to prose)
- Per-precision per-solver full LoSoS quantile table.
- Per-region noise/error log10 medians.
- Per-precision per-solver `σ_FP,L1` table.
- fp32 compiler matrix extension full coverage (LW3 N=200, Toro5, Sod N=400).
- Detailed p8 `s_worst_q05` / LoSoS rel mean values.

---

## 9. Verification Checklist (run after Batch 6)

1. `texcount -inc -sum -1` on `Chapter[1-7]/chapter*.tex` + `Abstract/abstract.tex` ≤ 7800 and ≥ 7750.
2. `pdflatex` round-trip with 0 unresolved refs and 0 unresolved citations.
3. All citations resolve in `references.bib`; new keys `eccomas_2016_muscl`, `berthon_muscl_hancock` present and well-formed.
4. Forbidden-phrase grep returns 0 hits across `Chapter*/chapter*.tex`.
5. Required-hedge grep returns ≥ 1 hit per hedge.
6. Spot-check 5 random numeric values from §5 against their source `summary.md` files.
7. Figure files referenced by Ch6 are the `n = 30` versions in `experiments/review3_mca_n30/report1_d2_replots/`.
8. Eq 3.21 caption no longer claims "specific total-energy form" as a definition.
9. Ch3 §"Precision-Sensitive Decision Points" ends with the §"Toro Test 2 Branch Stability" cross-link sentence.
10. Ch6 §"Limitations and Report 2 Direction" item 4 wording matches Ch4 §"Test-Case Matrix and Metrics" wording (n=30 consistency).
11. Visual inspection of Fig 6.1 caption matches the figure's axis label.
12. CFL grep in manuscript returns: "0.8 for 1D tests, 0.5 for LW3, 0.4 for LW12" exactly once.

---

## 10. Open Dependencies Before Execution

1. Confirm `references.bib` entries for `eccomas_2016_muscl` and `berthon_muscl_hancock` are obtained (full bibrecord; URL or DOI optional).
2. Confirm `experiments/review3_mca_n30/report1_d2_replots/` figure filenames match those referenced in Ch6 (`sigma_fp_vs_precision.png`, `losos_quantiles_rho.png`, `region_losos_margin_rho_p32.png`, `noise_to_error_ratio_heatmap_grid_rho.png`, `region_noise_to_error_ratio_precision_grid_rho.png`).
3. User decision: include Croci 2022 + Klöwer 2020 only if Batch 6 has > 30 words of headroom (default = skip).

---

---

## 11. Pre-Execution Audit Results (verified 2026-05-26)

A grep + read pass over the current draft confirmed which planned edits are still required (i.e. no silent prior-fix exists). All items below remain as the **current** manuscript text and are therefore still in scope for this plan.

| Edit | Current text confirmed | Location |
|---|---|---|
| Eq 3.21 caption | "specific total-energy form" verbatim | `Chapter3/chapter3.tex` line 291 |
| MCA sample-size framing | "two or three samples per virtual precision are not statistically defensible …" | `Chapter4/chapter4.tex` lines 192–195 |
| LoSoS quantile caveat | "raw-field quantiles use only two or three samples per virtual precision" | `Chapter6/chapter6.tex` line 18 |
| Toolchain split | "Toro3/Toro5 were built with Windows BuildTools; Sod/LW3/LW12 were built with Linux/WSL" | `Chapter5/chapter5.tex` lines 308–309 |
| Table 5.5 Toro3/Toro5 checkpoints | "none" | `Chapter5/chapter5.tex` lines 300–301 |
| Table 5.5 caption clause | "for Toro3 and Toro5 the evidence is final-output only" | `Chapter5/chapter5.tex` lines 314–316 |
| CPU-only sanity attribution | "A CPU-only sanity check (WSL/GCC strict rerun…) … final output only" | `Chapter5/chapter5.tex` lines 342–345 |
| Ch6 CPU sanity sentence | "WSL/GCC strict CPU reruns for Toro3 and Toro5 … CPU-only sanity evidence, not general cross-toolchain equivalence" | `Chapter6/chapter6.tex` line 80 |
| LW12 reference framing | "LW12 uses an $800^2$ fp64 numerical reference, not an exact solution" | `Chapter6/chapter6.tex` lines 90–91 + `Chapter4/chapter4.tex` lines 305, 309 + `Abstract/abstract.tex` line 9 |
| §3.5 Branch-sensitivity tail | ends at "amplifying the branch sensitivity discussed next." / linearisation paragraph closes at "first-order perturbation gives ... when the terms are non-zero." | `Chapter3/chapter3.tex` lines 444–457 |
| CFL value statement | **No `cfl`/`CFL` mention anywhere in the manuscript.** Algorithm 1 caption + §"Algorithmic Structure of the Implementation" prose do not state the coefficient. | (entire `report1/phd-thesis-template-2.4/`) |

All target edits are therefore still applicable. **No previously-applied prior fix was discovered**, so each Batch can proceed without a "skip if already done" branch.

---

## 12. Figure, Table, and Data Currency Plan

### 12.1 Figures that must be refreshed (manuscript currently shows pre-`n=30` data)

| Figure file in `report1/phd-thesis-template-2.4/Figs/report1/` | Current mtime | Source of refreshed file | Action |
|---|---|---|---|
| `sigma_fp_vs_precision.png` | 2026-05-14 | `experiments/review3_mca_n30/report1_d2_replots/sigma_fp_vs_precision.png` | Replace (cp -f) |
| `losos_quantiles_rho.png` | 2026-05-14 | `experiments/review3_mca_n30/report1_d2_replots/losos_quantiles_rho.png` | Replace |
| `region_losos_margin_rho_p32.png` | 2026-05-14 | `experiments/review3_mca_n30/report1_d2_replots/region_losos_margin_rho_p32.png` | Replace |
| `noise_to_error_ratio_heatmap_grid_rho.png` | 2026-05-14 | `experiments/review3_mca_n30/report1_d2_replots/noise_to_error_ratio_heatmap_grid_rho.png` | Replace |
| `region_noise_to_error_ratio_precision_grid_rho.png` | 2026-05-14 | `experiments/review3_mca_n30/report1_d2_replots/region_noise_to_error_ratio_precision_grid_rho.png` | Replace |

**Figure refresh is a new Batch 1a step**, executed by the same sub-agent that does the Ch6 MCA-text edits in Batch 1. Acceptance check: post-copy mtime must be $\geq$ 2026-05-25 23:36 UTC for each of the five files (matches `experiments/review3_mca_n30/summary.md` generation time).

Figures that do **not** change in this revision (verified relevant and consistent with existing tables):
`density_hllc_vs_rusanov_200.png`, `pressure_hllc_vs_rusanov_200.png`, `lw3_n400_double_rho_schlieren.png`, `lw12_n400_double_rho_schlieren.png`, `lw12_n400_fp32_minus_fp64_rho.png`, `sod_comparison.png`, `toro3_comparison.png`, `toro5_comparison.png`, `drift_timeseries_l1*.png`, `vfc_sod_overlay.png`, `float_double_over_reference_bar.png`.

### 12.2 Tables that must be updated (new evidence)

| Table | Subsection | Change | Source |
|---|---|---|---|
| Table 5.4 (2D summary) | Ch5 §"Two-Dimensional Euler Validation" | Add LW12 self-convergence row(s): `LW12 self vs $800^2$ fp64, $400^2$, …`; `LW12 self vs $1600^2$ fp64, $800^2$, …`; observed order $\approx 0.535$. | `experiments/add_experiment/lw12_1600_reference/summary.md` + `reference_scaled_ratios.csv` |
| Table 5.5 (CPU/GPU coverage) | Ch5 §"Matched CPU/GPU Comparison" | Toro3 / Toro5 "Saved checkpoints" column: `none` → `4 at $N=200$ (25/50/75/100 % of $t_{\mathrm{end}}$)`. Result column unchanged (`zero`). Caption: drop "final-output only" clause. Footnote rewritten (§3.10). | `experiments/add_experiment/toolchain_toro35_checkpoints/summary.md` + `toolchain_toro35/summary.md` + `cpu_only_vs_cuda_cpu_sanity/summary.md` |
| Table 5.6 (variation matrix) | Ch5 §"Compiler, Branch, Solver, and Drift-Growth Sensitivity" | Branch-rule row expanded (§3.11). Other rows unchanged. | `experiments/review3_local_fill/summary.md` |
| Algorithm 1 caption / surrounding text | Ch4 §"Algorithmic Structure of the Implementation" | Add the per-case CFL line (§3.3). | `tests/cases/toro_1d/*.cfg` (1D = 0.8), `tests/cases/liska_wendroff_2d/config3.cfg` (LW3 = 0.5), `tests/cases/liska_wendroff_2d/config12_n*.cfg` (LW12 = 0.4) |

### 12.3 Evidence → claim consistency check (run before Batch 6)

For each touched subsection, verify that every numeric claim is traceable to a current `summary.md` line:

1. **MCA n=30**: 30 unique seeds per (precision, solver) confirmed in `experiments/review3_mca_n30/summary.md`; p32 noise/error > 1 cells = 0 % from `report1_d2_replots/summary.md`; p8 final-time header drift from header-drift `False` flag in the same summary.
2. **Toro3/5 CSC strict CPU/GPU final-state zero**: from `experiments/add_experiment/toolchain_toro35/summary.md` (tier A1).
3. **Toro3/5 checkpoint 25/50/75/100 % zero**: from `experiments/add_experiment/toolchain_toro35_checkpoints/summary.md` (tier A2).
4. **CPU-only vs CUDA-cpu bit-identity**: from `experiments/add_experiment/cpu_only_vs_cuda_cpu_sanity/summary.md`.
5. **LW3 RTX 5090 preflight at $N=400$ and $N=800$**: from `experiments/add_experiment/lw3_5090_preflight/summary.md` (tier B).
6. **LW12 1600² hierarchy + order 0.5348**: from `experiments/add_experiment/lw12_1600_reference/summary.md` (tier C1).
7. **LW12 $R_\rho$ ratios at 1600² reference**: from `experiments/add_experiment/lw12_1600_reference/reference_scaled_ratios.csv`.
8. **LW3 N=400 fp64 CSC timing (CPU 8.53 s vs GPU 0.57 s)**: from `experiments/add_experiment/lw3_timing_split/summary.md` (tier D).
9. **Branch-rule expanded coverage (Sod / stationary contact / Toro3 / Toro5 zero; LW3 $N=200$ roundoff; Toro2 degenerate within 600 s)**: from `experiments/review3_local_fill/summary.md`.
10. **MUSCL convergence-order literature anchor**: ECCOMAS 2016 (Wellner) + Berthon 2006 from §3.16 BibTeX entries (verified by the user).

If any check fails, the corresponding insertion does not enter the manuscript. The plan does not allow paraphrase from memory.

### 12.4 Things explicitly left out (and why)

- `noise_to_error_ratio_quantiles_rho.png`, per-`p*` files in `experiments/review3_mca_n30/report1_d2_replots/`, `region_noise_to_error_ratio_precision_compare_rho.png` etc. exist in the replot directory but are **not** referenced by the manuscript; do not copy them in, as they would become orphaned figure assets.
- fp32 compiler matrix extension (LW3 N=200 / Toro5 / Sod N=400) → not promoted into Table 5.7 in v1; remains an `experiments/.../summary.md` artefact (Batch 6 may add a one-line note only if the budget allows).
- Croci 2022 + Klöwer 2020 → default skip (Batch 6 decision).

---

---

## 13. Per-Sub-Agent Pre-Edit Verification Protocol

Every batch sub-agent must run the steps below **before touching any file** and report the result back to the main process. If any verification step disagrees with §11, the sub-agent stops and asks for a re-plan rather than guessing.

### 13.1 Mandatory pre-edit checklist (each sub-agent)
1. **Read the target subsection in full** (every line of the `\section{...}` block, not just the lines listed in §3).
2. **Match the verbatim "current text"** claimed in §1.4 / §11 against what the file actually contains. If a quoted phrase has already been changed, removed, partially fixed, or wrapped in extra punctuation by some prior commit, stop and report — do not silently adapt.
3. **Re-grep the target chapter file for the forbidden phrases listed in §6.2** that apply to this batch. Each forbidden phrase must still be present before the edit, and must be absent after the edit.
4. **For every figure or table referenced in or near the target subsection** (e.g. `Fig.~\ref{fig:ch6-sigma-fp}`, `Table~\ref{tab:ch5-2d-summary}`), verify:
   - the figure file actually exists at the cited path,
   - if the file is in the §12.1 refresh list, that the replacement was already performed in this batch (or by Batch 1),
   - if the table holds numeric data being updated, that every new number is traceable to a `summary.md` line as listed in §12.3.
5. **Check the Abstract for collateral exposure** if the batch touches any of: LW12 reference, the `1600^2` / `800^2` phrasing, the saved-state $L_1 = L_\infty = \mathrm{ULP}_{\max} = 0$ headline, or the `1.30\times10^{-4}` headline. The current Abstract (`Abstract/abstract.tex`) is **not** scheduled for content edits in this revision; if a batch's change would invalidate the Abstract wording, stop and surface to main process.
6. **Word-delta probe:** before edits, snapshot `texcount -inc -sum -1` for the touched chapter files. After edits, recompute and compare against the batch budget in §0.

### 13.2 Per-batch acceptance gate (main process)
After the sub-agent reports completion, the main process runs:
- forbidden-phrase grep (per §6.2) on touched files → expect 0 hits;
- required-hedge grep (per §6.1) on touched files → expect ≥ 1 hit per applicable hedge;
- numeric-traceability spot-check on 2 random new numbers (must trace to the `summary.md` lines named in §12.3);
- figure-mtime check (if Batch 1) → all five Ch6 figures ≥ `2026-05-25 23:36 UTC`;
- Abstract-currency grep → confirm the four sentinel substrings still appear verbatim in `Abstract/abstract.tex` (`1600^2`, `800^2`, `1.30\times10^{-4}`, `\mathrm{ULP}_{\max}=0`); if any has become stale because of a downstream change, surface as an Abstract-edit follow-up rather than letting the run continue.

### 13.3 Failure handling
- If pre-edit verification fails: sub-agent stops, no file write, reports the mismatch to the main process. Main process re-reads the file, updates §11 / §3 if the manuscript state has genuinely shifted, then dispatches a corrected sub-agent.
- If post-edit acceptance gate fails: main process dispatches a fix-up sub-agent with the exact diff and failed gate. **Never silently continue to the next batch.**

---

**Plan is read-only. No edits to `report1/phd-thesis-template-2.4/` performed by this document.**
