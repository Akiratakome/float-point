# Review 4 — Phase 2 Cut Execution Log

**Date:** 2026-05-27
**Pre-Phase-2 body count:** 8566
**Post-P1 body count:** 8196 (−370)
**Post-P1+P2 body count:** 7968 (−228 additional, total −598)
**Cuts target:** −746 (to safety 7820)
**Gap remaining:** 148 words over the safety target (7968 vs 7820); 118 over hard cap (7850)

## Status: ESCALATE

P1 + P2 fully executed in audit order. Actual savings ran below audit estimates
(P1 saved 370 vs 518 estimated; P2 saved 228 vs 281 estimated) because the
replacement sentences ended up slightly longer than the audit's "Proposed words"
column — load-bearing forward-references, citation keys, and Table/Section
labels could not be compressed further without breaking links. Per the Phase 2
procedure §2, after P1+P2 the agent must not improvise additional cuts and
must not touch P3 (marked "low confidence"). The pdflatex build is clean and
all spec-mandated additions and numerical values remain intact.

## Cuts executed

| # | File | Old lines (audit) | Action | Est Δ | Priority | Status |
|---|---|---|---|---|---|---|
| P1.1 | Chapter3/chapter3.tex | 591–593 | removed closing paragraph | −35 | P1 | executed |
| P1.2 | Chapter3/chapter3.tex | 580–588 | collapsed HLLC-vs-MHD survey to single HLLD/Roe forward-reference sentence | −32 | P1 | executed |
| P1.3 | Chapter3/chapter3.tex | 537–542 | replaced seven-wave detail with one sentence pointing to Ch2 | −32 | P1 | executed |
| P1.4 | Chapter3/chapter3.tex | 569–580 | deleted Dedner equation block and parameterisation discussion; kept citations on remaining sentence | −65 | P1 | executed |
| P1.5 | Chapter7/chapter7.tex | 12 | dropped LW12 1.30e-4 / 1.13e-4 numbers and trimmed HLLC-Rusanov clause; replaced with table cross-refs | −57 | P1 | executed |
| P1.6 | Chapter5/chapter5.tex | tab:ch5-cpu-gpu caption | reduced to one CSC-coverage sentence | −48 | P1 | executed |
| P1.7 | Chapter6/chapter6.tex | 96–100 | trimmed item 4 parenthetical and stress-diagnostic clause | −32 | P1 | executed |
| P1.8 | Chapter4/chapter4.tex | 37 | deleted four-features meta-restatement sentence | −35 | P1 | executed |
| P1.9 | Chapter4/chapter4.tex | 215 | deleted degenerate-denominator sentence | −22 | P1 | executed |
| P1.10 | Chapter5/chapter5.tex | 230–232 | compressed two-paragraph hedge to one bridging sentence | −28 | P1 | executed |
| P1.11 | Chapter5/chapter5.tex | 193 | deleted standalone LW12 ratios sentence | −32 | P1 | executed |
| P1.12 | Chapter2/chapter2.tex | 161–162 | deleted "report measures" thesis-framing sentence | −24 | P1 | executed |
| P1.13 | Chapter4/chapter4.tex | 182–184 | replaced with one-sentence forward-reference to Ch2 | −22 | P1 | executed |
| P1.14 | Chapter6/chapter6.tex | 105–106 | deleted "validated scope is ideal-gas Euler only" sentence | −26 | P1 | executed |
| P1.15 | Chapter5/chapter5.tex | 264–265 | reduced strict-build/byte-ULP hedge to one Table reference | −16 | P1 | executed |
| P1.16 | Chapter4/chapter4.tex | 270 | dropped redundant "not a claim about all fp64 GPU hardware" sentence | −12 | P1 | executed |
| P2.1 | Chapter3/chapter3.tex | 588–590 | deleted "Report~1 does not derive" scope sentence | −38 | P2 | executed |
| P2.2 | Chapter2/chapter2.tex | 8–12 | compressed wave-feature framing | −22 | P2 | executed |
| P2.3 | Chapter5/chapter5.tex | 5–14 | replaced §Validation Overview opener with two-sentence claim-scope statement | −25 | P2 | executed |
| P2.4 | Chapter5/chapter5.tex | 50 | compressed $L_1$-orders sentence | −18 | P2 | executed |
| P2.5 | Chapter5/chapter5.tex | 162–169 | merged two LW12 hedges into single sentence | −20 | P2 | executed |
| P2.6 | Chapter1/chapter1.tex | 21 | deleted "Direct fp32 claims" forward-reference sentence | −32 | P2 | executed |
| P2.7 | Chapter4/chapter4.tex | 99 | dropped Algorithm-3 restatement + Verificarlo serial clause | −37 | P2 | executed |
| P2.8 | Chapter5/chapter5.tex | 309–315 | compressed GPU-live-arithmetic paragraph to one sentence | −28 | P2 | executed |
| P2.9 | Chapter6/chapter6.tex | 18 | compressed $n=30$ regime sentence with Ch4 cross-ref | −30 | P2 | executed |
| P2.10 | Chapter4/chapter4.tex | 159–161 | compressed compiler-axes sentence | −21 | P2 | executed |
| P2.11 | Chapter5/chapter5.tex | tab:ch5-1d-feature-validation caption | dropped emph narrow-band sentence | −10 | P2 | executed |

## Cuts skipped

All P3 items (P3.1–P3.7, audit estimated −119 words) skipped per Phase 2
procedure §2: "If STILL over after all P1+P2: ESCALATE — do NOT touch P3 (it's
marked 'low confidence' for a reason) and do NOT improvise additional cuts."

All borderline-list items (B.1–B.7) untouched — they require explicit user
sign-off.

## Build verification

- pdflatex passes (1+bibtex+2+3) all exit 0, output 68 pages.
- No `Fatal`, no `! error`, no undefined references, no undefined citations.

## Numerical / spec-mandated spot-checks (all PASS)

- LW12 reference-scaled ratio `1.30\times10^{-4}` present (Abstract line 21; Chapter5 line 205).
- Sod 1D fp64 $E_{100}$ value `6.681007e-3` present (Chapter5 line 55).
- Matched CPU/GPU `L_1 = L_\infty = \mathrm{ULP}_{\max} = 0` line preserved (Chapter4 line 283).
- `\section{Verificarlo and Monte Carlo Arithmetic}` present (Chapter2).
- `\section{Finite-Volume Derivation Overview}` present (Chapter2).
- `tab:ch2-divB-comparison` present (Chapter2).
- `lst:strict-ineq` present (Chapter3).
- `lst:hrsc-real` present (Chapter4).
- LoSoS / $s_{\mathrm{req}}$ / $\sigma_{\mathrm{FP}}$ / $\eta$ Ch6 definitional sentences present (6 LoSoS occurrences in Chapter6).
