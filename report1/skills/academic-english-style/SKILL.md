---
name: academic-english-style
description: Use when drafting, revising, or reviewing academic prose, choosing between "I"/"we"/passive, calibrating hedging on evidence-based claims, hunting field-specific collocations, or removing journalistic, pompous, or vague filler from a science dissertation.
---

# Academic English Style (Cambridge ELO)

## Overview

- **Clarity** — sequence ideas logically; prefer plain over journalistic or ornate phrasing.
- **Objectivity** — focus on evidence, not the writer; use passive or "we" purposefully.
- **Precision** — match strength of language to strength of evidence; hedge numerical claims.
- **Honesty** — quote and paraphrase with attribution and your own framing voice.

Overconfident wording, vague intensifiers, and dropped-in quotes erode credibility even when results are sound.

## When to use

- Drafting or revising dissertation prose.
- Reporting results where uncertainty or scope is not fully characterised.
- A paragraph feels breezy, pompous, journalistic, or overconfident.
- Choosing "I" / "We" / passive for a sentence.
- Hunting a verb or collocation that fits an academic paper.

## I / We / Passive

| Context | Use | Example |
|---|---|---|
| Reproducible method/result | Passive | "The algorithm **was implemented** in two configurations." |
| Aim, choice, contribution | "We" (or "I" in single-author thesis) | "We focus on the effect of the modelling assumption on convergence." |
| Interpretation, judgement | "We" or impersonal | "These results suggest..." / "It can be argued that..." |
| Routine step, actor irrelevant | Passive | "Each run was repeated five times." |

Mix the two. Pure passive becomes leaden; pure first person becomes informal.

## Hedging ladder (strongest to weakest claim)

| Strength | Verbs / modals | Use when |
|---|---|---|
| Definite | is, shows, proves | Analytic identities, definitions |
| Strong | indicates, demonstrates, establishes | Replicated result, tight error bars |
| Moderate | suggests, implies, supports the view that | Consistent trend, not exhaustive |
| Tentative | appears to, tends to, may, is likely to | Single experiment, plausible mechanism |
| Speculative | might, could, it is possible that | Hypothesis without direct evidence |

Stack hedges ("may suggest") only when uncertainty is genuinely double — not as filler.

## Numerical-methods collocations bank

Mine more via Google Scholar (subject + phrase). Starter set:

- Results: "results indicate", "is in close agreement with", "the discrepancy is on the order of", "convergence is observed at rate p".
- Methods: "the method exhibits", "the model preserves", "the constraint is satisfied", "the diagnostic activates near the transition".
- Error: "error accumulates", "is bounded above by", "is monotonically decreasing in N", "introduces a relative error of order eps", "the variance across runs is".
- Framing: "we focus on", "we restrict attention to", "throughout, we assume", "for definiteness, we take", "without loss of generality".
- Citing: "Smith (2020) reports that...", "as shown by...", "consistent with the findings of...".

**focus on / examine / investigate / characterise** are not synonyms:

| Verb | Use when |
|---|---|
| *focus on* | narrowing scope; declares what is in/out of frame |
| *examine* | inspect closely; descriptive, no commitment to an outcome |
| *investigate* | systematic study driven by a question being answered |
| *characterise* | quantify properties or behaviour; output is a description |

## Common slips

- **Pompous filler**: "It can be argued to some degree that..." — delete.
- **Journalistic intensifiers**: incredibly, amazing, huge, really, lots of, top-class, and so on, etc. — cut or quantify.
- **Vague quantifiers**: quite a few, some basic observations, missing bits — replace with numbers or named items.
- **Spoken narration**: Basically..., Actually..., Anyway... — remove.
- **Overclaim**: "proves" where you mean "is consistent with"; "for all methods" where you tested two.
- **Detached quotation**: quote dropped in with no framing voice on either side.

## Worked examples (bad to good)

| Bad (overclaim / journalistic / pompous) | Good (precise / hedged / impersonal) |
|---|---|
| "Our runs prove that method A is way more accurate than method B, which is a huge result." | "Across the configurations tested, method A gives lower error than method B, indicating that its additional cost is justified in this regime." |
| "Basically, the correction pretty much fixes the issue and the results are amazing." | "The correction reduces the variance across repeated runs by roughly an order of magnitude, suggesting that it suppresses a significant source of noise." |
| "It can be argued to some degree that the alternative implementation is consistent with efficient hardware utilisation." | "The alternative implementation trades accuracy for throughput; the question is at what point this trade-off degrades solution quality." |

## Red flags — stop and rewrite

- Rhetorical adverbs: *clearly, obviously, undoubtedly, extremely, incredibly*.
- Adjective with no number behind it: *significant, large, small, accurate, fast*.
- A quote whose subject is not connected to the surrounding text.
- Three or more passive clauses in a row.
- A claim about "all methods / every case / any parameter value" from a finite set of experiments.

## Companion Skill

Default to this skill alone for style, stance, voice, and hedging. If structure is the main problem, switch to the relevant section-writing skill instead of stacking more skills.
