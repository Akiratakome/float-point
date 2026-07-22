# Week 15 Supervisor Meeting English Version Implementation Plan
> **Status (2026-07-22): EXECUTED.** The resulting document is the dated
> historical snapshot at `docs/week15/week15-supervisor-meeting-EN.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a natural, presentation-ready academic English version of the Week 15 supervisor report.

**Architecture:** Add one English Markdown document alongside the unchanged Chinese source. Adapt the prose for spoken academic English while preserving the original structure, numerical evidence, figure references, and claim boundaries; verify the result by direct source comparison and Markdown/text scans.

**Tech Stack:** Markdown, PowerShell, ripgrep, Git

## Global Constraints

- Do not modify `docs/week15/week15-supervisor-meeting.md`.
- Do not change solver numerics, configurations, experiment outputs, or figures.
- Preserve every reported numerical value, experiment configuration, gate result, figure path, and solver/case name.
- Do not strengthen causal language or claim that HLLD is production-ready.
- Do not claim GPU results, Kelvin–Helmholtz results, 512² results, or completed temporal-divergence fitting.

---

### Task 1: Draft and verify the English supervisor report

**Files:**
- Read: `docs/week15/week15-supervisor-meeting.md`
- Read: `docs/superpowers/specs/2026-07-09-week15-supervisor-meeting-english-design.md`
- Create: `docs/week15/week15-supervisor-meeting-en.md`

**Interfaces:**
- Consumes: the approved source report and English-version design.
- Produces: a standalone English Markdown briefing with the same six figure paths and evidence boundaries as the Chinese source.

- [x] **Step 1: Create the English report**

Write `docs/week15/week15-supervisor-meeting-en.md` with these sections:

```markdown
# Week 15 Supervisor Meeting Report

> Prepared on 9 July 2026.

## Executive summary
## Work completed this week
## Six figures: how to read them and what they show
### Figure A — Which axis matters most?
### Figure B — How many significant digits remain?
### Figure C — How large is the compiler optimisation / fast-math effect?
### Figure D — How much speed-up does fp32 provide?
### Figure E — What does the 2D test case look like?
### Figure F — How strongly does 2D chaotic flow amplify fp32 drift?
## Claims supported by the current evidence
## Claims not yet supported
## Next steps
## References
```

Retain the original figure paths verbatim and use natural academic English
suitable for a supervisor meeting. Define Monte Carlo Arithmetic (MCA) and the
G0 anchor gate at first use. Preserve “Lyapunov-like” or future-tense wording
for work that has not yet been completed.

- [x] **Step 2: Verify required numerical evidence**

Run:

```powershell
rg -n "24|N=30|16|8–9|15|6–7|1\.5–1\.9e-6|1\.06–1\.34|0\.15|27|256²|t=0\.5|3e-3|759|806|3\.72|812|24\.45|3→6" docs/week15/week15-supervisor-meeting-en.md
```

Expected: every value appears in the appropriate translated section, with no
new numerical result.

- [x] **Step 3: Verify all figure references and claim boundaries**

Run:

```powershell
rg -n "fig[1-6]_.*\.png|engineering consistency|exact solution|morphology|production|GPU|Kelvin|512²|Lyapunov" docs/week15/week15-supervisor-meeting-en.md
```

Expected: six figure paths are present; engineering consistency and morphology
are distinguished from exact-solution validation; GPU, Kelvin–Helmholtz, 512²,
and Lyapunov-like fitting remain future work.

- [x] **Step 4: Check formatting and accidental untranslated text**

Run:

```powershell
git diff --check -- docs/week15/week15-supervisor-meeting-en.md
rg -n "[\p{Han}]" docs/week15/week15-supervisor-meeting-en.md
```

Expected: `git diff --check` produces no output; the Han-character scan produces
no output.

- [x] **Step 5: Review the final diff**

Run:

```powershell
git diff -- docs/week15/week15-supervisor-meeting-en.md
git status --short
```

Expected: the only new report file is
`docs/week15/week15-supervisor-meeting-en.md`; pre-existing unrelated worktree
changes remain untouched.
