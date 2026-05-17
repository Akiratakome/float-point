---
name: scientific-writing-duke
description: Use when a results or methods paragraph feels confusing despite correct grammar, when sentences have weak/abstract subjects or nominalized verbs ("performed an analysis of"), when the reader has to re-read to follow the logic, when subject and verb are separated by long clauses, when tense or voice drifts within a section, when a figure or equation sits inert beside prose that doesn't reference it, or when revising scientific prose for clarity rather than correctness.
---

# Scientific Writing (Duke / Gopen-Swan)

## Overview

**Writing serves reader expectations, not author intentions.** Readers decode sentences positionally: the grammatical subject names the character, the verb names the action, the opening names the familiar topic, the ending carries the new, emphatic point. Violate these and the reader works harder — even if every word is correct. Use this as a skill of **revision**, not first-draft composition.

*Source: Duke University Scientific Writing Resource (sites.duke.edu/scientificwriting) and the Gopen–Swan reader-expectations framework, "The Science of Scientific Writing," American Scientist 78 (1990) 550–558.*

## When to Use

- Revising Methods, Results, or Discussion in a scientific dissertation
- A reader calls a paragraph "hard to follow" but cannot name a grammar error
- Sentences read as a flat list of facts rather than a connected argument
- Figures or equations appear without prose anchoring them
- Tense or voice drifts inside a section

## Quick Reference: Gopen-Swan Rules

| Rule | Diagnosis | Fix |
|------|-----------|-----|
| **Topic position (old first)** | Opens with new/unfamiliar info | Move a familiar noun to the start |
| **Stress position (new last)** | Key claim buried mid-sentence | Move new/emphatic info to the period |
| **Character as subject** | Subject is an abstraction ("analysis", "investigation") | Make the real actor (scheme, error, we) the subject |
| **Action in the verb** | Weak verb + nominalization ("performed an analysis") | Convert nominalization back to a verb |
| **Subject-verb proximity** | Long modifier wedged between subject and verb | Move the modifier to start or end |
| **Consistent paragraph subject** | Subjects drift across unrelated nouns | Keep one recurring character in the subject slot |

## Scientific Paper Conventions

**Tense:**
- **Past** for what you did and observed: "We ran the experiment at three parameter values."
- **Present** for established facts, equations, and what a figure shows: "The model conserves mass." "Figure 3 shows the drift."
- **Present perfect** for prior literature: "Prior studies have reported..."

**Voice:** Active by default. Passive is legitimate only when the object is the true topic, not as a way to dodge "we".

**Figures and equations are anchors.** Every one must be (1) named in prose, (2) interpreted (what to see), and (3) tied to the claim. Prose surrounds the figure; the figure does not replace prose.

**Signal-to-noise:** Cut metadiscourse ("it should be noted that"), redundant hedges ("may possibly suggest"), Latinate inflation ("utilize" -> "use").

## Common Mistakes

- **Whose story?** Subjects are "the analysis" or "the investigation" instead of the real actor, method, feature, or uncertainty.
- **Buried punchline.** Key number sits mid-sentence instead of at the period.
- **Orphan figure.** "See Figure 4." with no interpretation; reader guesses what to look at.
- **Tense drift.** Past tense on universal claims, or present on your own runs.
- **Subject-verb gap.** Long clauses wedged between subject and verb force re-reading.

## Worked Example

**Before** (every rule violated):

> An investigation of the impact of a modelling choice on the two numerical methods under consideration was performed. It should be noted that the first method, when evaluated under the altered setting on the target platform, exhibited a deviation from the baseline on the order of 2.1x relative to the primary error metric. The second method behaved differently.

**After:**

> We compared the two methods under the altered setting against the baseline (Figure 4). Under this setting, the first method drifted from the baseline by 2.1x in the primary error metric at the final time. The second method, by contrast, held the drift below 0.3x under the same conditions.

**Annotations:**
- *Topic position + character:* sentences open with known actors ("We", "the first method", "the second method"), not "An investigation of".
- *Stress position:* each sentence ends on the new fact ("2.1x", "below 0.3x").
- *Action in verb:* "the first method drifted" replaces "a deviation... was exhibited".
- *Subject-verb proximity:* the long wedge between subject and verb is gone.
- *Signal-to-noise:* "It should be noted that", "under consideration", "when computations were carried out" deleted.
- *Figure as anchor:* Figure 4 is named; the prose interprets it.
- *Tense:* past for what we did and observed.

## Companion Skill

Default to this skill alone for Methods, Results, and Discussion sentence-level revision. If the problem is general wordiness rather than reader expectation, use `editing-academic-prose` instead.
