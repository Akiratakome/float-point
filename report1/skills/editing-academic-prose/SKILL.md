---
name: editing-academic-prose
description: Use when revising a draft chapter or paragraph of an academic dissertation, when prose feels wordy or unclear, when a topic sentence seems off, when reviewers flag weak flow or over-hedging, when a non-native English writer is polishing prose, when sentences drift into nominalisations, register slips, or filler like "it is important to note that".
---

# Editing Academic Prose

## Overview

Edit macro to micro. Polishing sentences in a paragraph that does not earn its place is wasted work. Edit for the reader. Core principle: **characters as subjects, actions as verbs**; calibrated hedging; clarity > concision > elegance.

## When to use

- Revising a chapter, section, or paragraph
- Prose feels wordy, vague, or dense
- Topic sentence does not match the paragraph
- Reviewer flags unclear flow, over-hedging, register
- Non-native writer polishing articles, prepositions, register
- Final pre-submission pass

## Editing pass order (do NOT skip ahead)

1. **Structural** — Does this paragraph belong? What is its job? Move or cut whole paragraphs before fixing sentences.
2. **Paragraph** — One idea. Topic sentence states it; later sentences develop or complicate; last sentence resolves or pivots. Check given→new flow.
3. **Sentence** — Characters as subjects, actions as verbs. Cut empty subjects (*There is*, *It is*) and empty verbs (*conduct an investigation* → *investigate*). Check agreement.
4. **Word** — Filler, register, hedging, articles, prepositions, consistent terminology.

Diagnostics: **paragraph split** (blank line after every full stop; read sentences in isolation, check linkage); **read aloud** or TTS (catches run-ons and missing connectives).

## Quick reference: cuts and rewrites

| Before | After | Move |
|---|---|---|
| It is important to note that X | X | Cut meta-filler |
| There is a tendency for the solver to diverge | The solver tends to diverge | Kill *there is* + nominalisation |
| Due to the fact that / In order to | Because / To | Padding |
| The implementation of the algorithm was carried out | We implemented the algorithm | Nominalisation + empty verb |
| This evidence proves the method is insufficient | This evidence suggests the method is insufficient in this regime | Hedge + bound scope |
| It may possibly perhaps be the case that errors could arise | Errors may arise | Cut hedge-stacking |
| The method has the ability to capture the target feature | The method captures the target feature | Cut *has the ability to* |
| As is well-known, the method is more accurate | The method is more accurate in this setting (cite source) | Cite, do not appeal |

**Hedging dial.** Three stacked hedges signal lack of confidence — strengthen or cut. For the strength-to-verb mapping, use the hedging ladder in [`academic-english-style`](../academic-english-style/SKILL.md).

**Nominalisation check.** *-tion / -ment / -ance / -ity* attached to empty verbs (*be, have, make, conduct, perform, carry out*) is usually rewritable as a verb. Keep nominalisations only when the concept itself is the subject.

## Common slips for non-native / Chinese-academic writers

- **Over-long sentences** with commas + *and* — split at the logical hinge.
- **Appeal phrases** (*as is well-known*) — cite or cut.
- **Article drift**: *the* proposed method (specific); *model uncertainty* (general property, no article).
- **Prepositions**: research *on*, consistent *with*, evidence *for*, effect *on*, depend *on*.
- **Register**: *a lot of* → *many*; *get* → *obtain*; vary *show / demonstrate / indicate*.
- **Hedge-stacking**: one hedge per clause.
- **Topic-comment carryover**: *For the proposed method, it is more accurate* → *The proposed method is more accurate*.

## Worked example

**Before:**

> It is important to note that in the present work an investigation of the impact of a modelling choice on two numerical methods has been carried out by us. As is well-known, the first method, which is a second-order method, has the ability to capture sharp gradients, however it may possibly perhaps suffer from a loss of accuracy under the altered setting. The implementation of the second method was also made and a comparison between the two was conducted. The results show that the second method is better.

**After:**

> We investigate how a modelling choice affects two numerical methods. The first method captures sharp gradients accurately in the baseline setting, but loses accuracy near strong discontinuities under the altered setting. The second method, by contrast, retains accuracy across the same test suite. These results suggest that the second method is less sensitive to this modelling choice for the regimes studied here.

**What changed:**

1. Cut filler/passive/nominalisation (*It is important to note that... has been carried out by us*) -> active *We investigate*. Topic sentence now introduces both methods.
2. Cut appeal (*as is well-known*) and padding (*has the ability to*). Replaced stacked hedges (*may possibly perhaps*) with a concrete, located claim.
3. Cut nominalisations (*implementation... was made*, *comparison... was conducted*). Parallel structure carries the contrast between the two methods.
4. Vague *is better* → calibrated, scope-bounded claim.

Now: topic sentence, two parallel evidence sentences, hedged conclusion.

## Red flags

- Rewording sentences but cannot state the paragraph's job → return to structural pass.
- Three hedges in one clause → cut to one or strengthen the claim.
- Subject of five+ words made of nominalisations → rewrite with a character as subject.
- Paragraph ends without resolving its topic sentence → add a closing sentence or move the paragraph.

## Companion Skill

Default to this skill alone after a draft exists. If the only remaining problem is generic or machine-polished tone, use `avoiding-ai-flavor` as the one companion skill.
