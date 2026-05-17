---
name: avoiding-ai-flavor
description: Use when academic prose feels too polished or generic, when adjectives feel extreme, when sentences fall into triadic "X, Y, and Z" rhythm, when em-dashes pile up, when a paragraph could have been written about any topic, or when claims sound marketing-confident.
---

# Avoiding AI Flavor

## Overview

AI-flavoured prose is fluent, evenly weighted, mildly marketing, and topic-agnostic. Credible academic prose is concrete, appropriately hedged, and grounded in the evidence, methods, and limits of the study. When in doubt, choose the more specific and more cautious phrasing.

## When to Use

Run this check whenever a paragraph reads smoothly on the first try, or after any LLM-assisted edit. Cross-check before submitting any section.

## Banned vocabulary and replacements

| BAD | BETTER |
|-----|-----|
| delve into / dive into | examine, study, test |
| unpack / unravel | analyse, decompose |
| navigate (figuratively) | handle, treat |
| leverage / harness | use, apply, exploit (sparingly) |
| unlock / empower | enable, allow |
| groundbreaking / revolutionary / paradigm-shifting | new, recent (cite the paper) |
| unprecedented / transformative | (delete; state the actual change) |
| incredible / remarkable / extraordinary | large, of order ~10^-X |
| seamless | (delete; describe what is continuous) |
| robust (overused) | stable under perturbation X, insensitive to Y |
| comprehensive (overused) | covering cases A, B, C |
| cutting-edge / state-of-the-art (loose) | (cite the specific scheme and year) |
| extremely / incredibly / absolutely | (usually delete) |
| undoubtedly / indisputably / categorically / wholly | likely, consistent with, within tested range |
| it is important to note that | (delete; state the fact) |
| it is worth noting / it should be emphasised that | (delete) |
| as we shall see / let us now turn to | (delete; use section headings) |
| in conclusion / at the end of the day | (delete) |
| tapestry / weave / journey / symphony / orchestrate | (delete; use a concrete noun) |
| landscape (non-literal) | set of methods, parameter space |
| bridge the gap | address, fill, extend |

## Sentence-rhythm tells

- **Triadic rhythm:** "X, Y, and Z" in 3+ consecutive sentences. Break by dropping to two items or expanding one.
- **"Not only X but also Y":** at most once per chapter.
- **"By doing A, we achieve B":** formulaic when repeated. Replace with "A reduces B by ~k%" or a plain causal clause.
- **Even cadence:** every sentence ~20 words. Allow one short blunt sentence per paragraph ("The scheme then fails.").
- **Em-dash pile-up:** more than one em-dash per paragraph is a tell. Use commas, parentheses, or a full stop.

## Calibrating confidence

- Avoid: "definitively superior", "unequivocally show", "absolutely clear", "the first to demonstrate".
- Prefer: "our results suggest", "the data are consistent with", "within the tested CFL range", "to our knowledge".
- Do not claim novelty without evidence. "Groundbreaking" applied to coursework is a red flag.
- Reserve strong claims for places where a figure, table, proof, or cited source directly supports them. Hedge elsewhere.

## Natural Academic Voice

- Prefer concrete technical vocabulary over generic academese.
- One specific example beats three adjectives.
- If a sentence could appear in any paper on any topic, rewrite it to mention the actual method, dataset, result, figure, or limitation.
- Do not paraphrase by inserting flowery synonyms. Plain repetition of a technical term is correct.

## Worked example

**AI-flavored (before):**
> In this groundbreaking study, we delve into the transformative impact of a technical intervention on a complex system. By leveraging a novel evaluation framework, we navigate the intricate landscape of uncertainty, unlocking remarkable insights into the seamless interplay between method design, implementation, and performance. The results unequivocally demonstrate that the intervention is incredibly effective — robust, comprehensive, and state-of-the-art.

**Academic (after):**
> We study how a reduced-precision implementation affects two numerical solvers on a standard benchmark. A stochastic-arithmetic tool is used to estimate rounding sensitivity in each solver. Within the tested parameter range, the mixed-precision variant preserves the main error metric close to the double-precision baseline. The fully reduced-precision runs fail near the sharpest feature, consistent with cancellation in the local update.

**Annotations:**
- "groundbreaking", "transformative", "remarkable", "incredible" -> deleted (extreme adjectives).
- "delve into", "leverage", "navigate", "unlock" -> "study", "use", "estimate" (banned verbs).
- "intricate landscape", "seamless interplay" -> deleted (pop metaphors).
- "unequivocally demonstrate" -> "preserves the main error metric close to the baseline" (calibrated and evidence-bound).
- "robust, comprehensive, and state-of-the-art" -> replaced by a concrete failure mode ("fail near the sharpest feature, consistent with cancellation in the local update").
- One em-dash removed; two short concrete sentences kept.
- Specific terms added: method, benchmark, measurement tool, error metric, tested range, and failure location.

## Red flags during self-review

- A sentence uses two or more banned words from the table.
- Three sentences in a row end with a three-item list.
- A paragraph contains no number, no method name, and no citation.
- The claim is stronger than the figure supporting it.
- The same paragraph could be pasted into an unrelated dissertation.

All of these mean: rewrite before submitting.
