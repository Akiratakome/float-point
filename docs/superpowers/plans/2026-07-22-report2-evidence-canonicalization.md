# Report 2 Evidence Canonicalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish one canonical Report 2 evidence map, restore Week 14-16 navigation, mark dated material accurately, and prepare a verified linear integration without changing numerical code or evidence values.

**Architecture:** Treat `docs/experiment_logs/report2_evidence_map.md` as the current-state authority. Week summaries become compact routing documents, while requirements, meeting reports, experiment summaries, and executed plans retain their original roles and paths. Add one Python documentation-contract test so future changes cannot silently remove required evidence status or weekly navigation.

**Tech Stack:** Markdown, Python 3.11, pytest, Git, PowerShell

## Global Constraints

- Work only on `week16-evidence-completion` until the final integration gate.
- Do not change solver numerics, CUDA code, compiler flags, cfg defaults, binary formats, or existing experiment values.
- Do not rerun or regenerate experiments in this phase.
- Do not merge or cherry-pick `codex/mhd-temporal-divergence`.
- Do not delete or move user-owned untracked files, worktrees, branches, logs, or tools.
- Preserve historical commands and experiment summaries; add current routing instead of rewriting provenance.
- Keep `config -> build -> run -> measure -> aggregate -> plot` as the harness contract.
- Use `negative-result`, not a physical Lyapunov claim, for the current temporal-divergence evidence.
- Keep Brio-Wu and Orszag-Tang combined deterministic/MCA claims `provisional` until a machine-readable unified gate exists.
- Keep GPU HLL MHD, the hardware axis, KH report-grade evidence, and 512^2 consolidation explicitly `deferred`.

---

### Task 1: Add the Report 2 documentation contract

**Files:**
- Create: `tests/py/test_report2_documentation.py`

**Interfaces:**
- Consumes: repository-relative permanent document paths.
- Produces: pytest checks for the evidence-map vocabulary, Week 14-16 navigation, historical-snapshot notices, and excluded obsolete claims.

- [ ] **Step 1: Write the failing documentation contract**

Create `tests/py/test_report2_documentation.py` with:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
EVIDENCE_MAP = DOCS / "experiment_logs" / "report2_evidence_map.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_report2_evidence_map_has_required_status_and_assets():
    text = read(EVIDENCE_MAP)
    for status in (
        "report-grade",
        "provisional",
        "validation",
        "morphology-only",
        "negative-result",
        "invalid",
        "superseded",
        "deferred",
    ):
        assert f"`{status}`" in text

    required_paths = (
        "experiments/week12/brio_wu_1d/summary.md",
        "experiments/week12/mhd_2d/divb_clean/summary.md",
        "experiments/week13/hlld_divb_followup/summary.md",
        "experiments/week13/orszag_tang/paper_summary.md",
        "experiments/week13/kelvin_helmholtz/paper_summary.md",
        "experiments/week15/brio_wu_precision_pilot_p1/summary.md",
        "experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.md",
        "experiments/week15/orszag_tang_precision_smoke/headline256_p1/summary.md",
        "experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/summary.md",
        "experiments/week15/mhd_temporal_divergence/summary.md",
    )
    for relative in required_paths:
        assert relative in text
        assert (ROOT / relative).is_file()


def test_week14_to_week16_have_canonical_navigation():
    index = read(DOCS / "INDEX.md")
    for week in (14, 15, 16):
        plan = DOCS / f"week{week}" / f"week{week}-plan.md"
        summary = DOCS / f"week{week}" / f"week{week}-summary.md"
        assert plan.is_file()
        assert summary.is_file()
        assert f"week{week}/week{week}-plan.md" in index
        assert f"week{week}/week{week}-summary.md" in index

    assert "report2_evidence_map.md" in index
    assert "**Active branch**" not in index


def test_dated_meeting_material_is_not_current_status():
    snapshots = (
        DOCS / "week13" / "week13-supervisor-meeting.md",
        DOCS / "week13" / "week13-supervisor-meeting-EN.md",
        DOCS / "week14" / "week14-supervisor-meeting.md",
        DOCS / "week14" / "week14-supervisor-meeting-EN.md",
        DOCS / "week15" / "week15-supervisor-meeting.md",
        DOCS / "week15" / "week15-supervisor-meeting-EN.md",
        DOCS / "week15" / "week15-supervisor-report.md",
    )
    for path in snapshots:
        text = read(path).lower()
        assert "historical snapshot" in text
        assert "report2_evidence_map.md" in text


def test_temporal_claim_is_bounded():
    text = read(EVIDENCE_MAP)
    assert "planned OT > Brio-Wu contrast was not observed" in text
    assert "formal maximal Lyapunov exponent" in text
    assert "not claimed" in text
```

- [ ] **Step 2: Run the new test and confirm the documentation is missing**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_report2_documentation.py -q
```

Expected: failure because `docs/experiment_logs/report2_evidence_map.md` and the Week 14-16 canonical files do not yet exist.

- [ ] **Step 3: Commit the failing contract**

```powershell
git add tests/py/test_report2_documentation.py
git commit -m "test(docs): define Report 2 evidence contract"
```

---

### Task 2: Create the canonical Report 2 evidence map

**Files:**
- Create: `docs/experiment_logs/report2_evidence_map.md`
- Test: `tests/py/test_report2_documentation.py`

**Interfaces:**
- Consumes: committed Week 12-15 summaries and the status vocabulary from the design.
- Produces: the authoritative Report 2 evidence routing table used by weekly summaries and `docs/INDEX.md`.

- [ ] **Step 1: Create the evidence-map header and interpretation rules**

The file must start with:

```markdown
# Report 2 Evidence Map

> Current status authority for Report 2. Requirements and dated meeting reports
> are historical inputs; experiment summaries remain the numerical authority.
> Last audited: 2026-07-22 on `week16-evidence-completion`.

## Status vocabulary
```

Define all eight statuses exactly as specified in the design and state that a
status applies only to the bounded claim in the same row.

- [ ] **Step 2: Add the evidence inventory**

Add a table with these required rows and classifications:

| Evidence | Status | Required authority and boundary |
|---|---|---|
| Week 12 Brio-Wu 1D | `validation` | `experiments/week12/brio_wu_1d/summary.md`; validation only |
| Week 12 2D invariance/GLM | `validation` | `experiments/week12/mhd_2d/brio_wu_2d/summary.md` and `divb_clean/summary.md` |
| Week 13 HLLD divB follow-up | `validation` | `experiments/week13/hlld_divb_followup/summary.md`; supersedes the stale-binary interpretation |
| Week 13 OT morphology | `morphology-only` | `experiments/week13/orszag_tang/paper_summary.md` |
| Week 13 KH morphology | `morphology-only` | `experiments/week13/kelvin_helmholtz/paper_summary.md`; no precision claim |
| Week 14 HLL MCA | `invalid` | p24 instrumentation did not take effect; superseded by Week 15 N=30 |
| Week 14 pilots/smokes | `superseded` | retained as development provenance |
| Week 15 Brio-Wu HLL | `provisional` | 24 deterministic variants plus p53/p24 N=30 exist, but summary claim still says provisional |
| Week 15 Brio-Wu HLLD | `provisional` | same boundary as HLL |
| Week 15 OT HLL | `provisional` | `headline256_p1` and `mca_n30` are separate packages, not one unified gate |
| Week 15 OT HLLD | `provisional` | same boundary as HLL |
| Temporal divergence | `negative-result` | 80 successful runs; 15/25 paired samples; planned OT > Brio-Wu contrast was not observed |
| GPU HLL MHD | `deferred` | design and plan exist, implementation absent |
| CPU/GPU hardware axis | `deferred` | depends on validated GPU HLL MHD |
| KH report-grade precision | `deferred` | current KH evidence remains morphology-only |
| OT/KH 512^2 consolidation | `deferred` | two-resolution sensitivity only when complete |

For every row include authoritative paths, sample/resolution facts, supported
claim, excluded claim, superseded assets, and tracked/local retention state.

- [ ] **Step 3: Add current Report 2 claim boundaries**

State explicitly:

- precision effects are measured against project baselines, not exact MHD solutions;
- HLLD is an analysed CPU solver but is not silently promoted to the production default;
- temporal rates are bounded Lyapunov-like engineering fits;
- a formal maximal Lyapunov exponent is not claimed;
- the planned OT > Brio-Wu contrast was not observed;
- GPU and hardware conclusions are unavailable;
- KH supports morphology only;
- two resolutions do not establish asymptotic convergence.

- [ ] **Step 4: Add plan and retention routing**

List the active completion design and the GPU plan as `partially executed` and
`planned`, respectively. List the 2026-07-02 OT plan as `superseded`. Record
that temporal configs/logs/metadata remain local ignored assets, while the
committed summary embeds generated config and metadata text and no transient
grids are retained.

- [ ] **Step 5: Run the evidence-map portion of the test**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_report2_documentation.py::test_report2_evidence_map_has_required_status_and_assets tests\py\test_report2_documentation.py::test_temporal_claim_is_bounded -q
```

Expected: `2 passed`.

- [ ] **Step 6: Commit the canonical map**

```powershell
git add docs/experiment_logs/report2_evidence_map.md
git commit -m "docs(report2): add canonical evidence map"
```

---

### Task 3: Restore Week 14-16 canonical navigation

**Files:**
- Create: `docs/week14/week14-plan.md`
- Create: `docs/week14/week14-summary.md`
- Create: `docs/week15/week15-plan.md`
- Create: `docs/week15/week15-summary.md`
- Create: `docs/week16/week16-plan.md`
- Create: `docs/week16/week16-summary.md`
- Test: `tests/py/test_report2_documentation.py`

**Interfaces:**
- Consumes: `docs/experiment_logs/report2_evidence_map.md` and existing specs/plans.
- Produces: the Week 14-16 plan/summary pairs required by `docs/INDEX.md`.

- [ ] **Step 1: Create Week 14 plan and summary**

`week14-plan.md` must route to:

- `docs/superpowers/specs/2026-07-01-week14-mhd-plan-design.md`;
- `docs/superpowers/plans/2026-07-01-week14-mhd-precision-pilot.md`;
- the HLL-first CPU Brio-Wu pilot scope;
- the later HLLD diagnostic extension;
- a completion-status section identifying executed, superseded, and deferred items.

`week14-summary.md` must distinguish valid deterministic/G0 pilot evidence
from the invalid HLL MCA setup, link the Week 15 replacement, and avoid using
the invalid p24 result in any Report 2 claim.

- [ ] **Step 2: Create Week 15 plan and summary**

`week15-plan.md` must route to the 2026-07-08 solver-aware OT plan and the
2026-07-09 breadth/MCA-depth plan, identify the 2026-07-02 plan as superseded,
and preserve CPU-only scope.

`week15-summary.md` must list the four 24-variant plus N=30 CPU evidence sets as
`provisional`, link all deterministic and MCA authorities separately, link the
six report figures as dated presentation material, and defer GPU/KH/512^2 and
temporal work to Week 16.

- [ ] **Step 3: Create Week 16 plan and summary**

`week16-plan.md` must point to:

- `docs/superpowers/specs/2026-07-21-week15-16-completion-design.md`;
- `docs/superpowers/plans/2026-07-21-mhd-temporal-divergence.md`;
- `docs/superpowers/specs/2026-07-22-report2-evidence-canonicalization-design.md`;
- this implementation plan.

`week16-summary.md` must state that only phase 1, temporal divergence, is
complete; report the 80 runs and 15/25 samples; record the unexpected bounded
negative result; and list GPU HLL MHD, hardware-axis evidence, KH report-grade
evidence, and 512^2 consolidation as incomplete.

- [ ] **Step 4: Run the weekly-file existence checks directly**

```powershell
14..16 | ForEach-Object {
  Test-Path "docs/week$_/week$_-plan.md"
  Test-Path "docs/week$_/week$_-summary.md"
}
```

Expected: six `True` lines.

- [ ] **Step 5: Commit the weekly navigation documents**

```powershell
git add docs/week14/week14-plan.md docs/week14/week14-summary.md docs/week15/week15-plan.md docs/week15/week15-summary.md docs/week16/week16-plan.md docs/week16/week16-summary.md
git commit -m "docs(report2): restore week14 to week16 navigation"
```

---

### Task 4: Mark historical material and import the English Week 15 snapshot

**Files:**
- Modify: `docs/week13/week13-supervisor-meeting.md`
- Modify: `docs/week13/week13-supervisor-meeting-EN.md`
- Modify: `docs/week14/week14-supervisor-meeting.md`
- Modify: `docs/week14/week14-supervisor-meeting-EN.md`
- Modify: `docs/week15/week15-supervisor-meeting.md`
- Modify: `docs/week15/week15-supervisor-report.md`
- Create from root-worktree draft: `docs/week15/week15-supervisor-meeting-EN.md`
- Create from root-worktree draft: `docs/superpowers/plans/2026-07-09-week15-supervisor-meeting-english.md`
- Test: `tests/py/test_report2_documentation.py`

**Interfaces:**
- Consumes: dated existing meeting material and the root worktree's two untracked English files.
- Produces: clearly historical snapshots with a route to the current evidence map.

- [ ] **Step 1: Add the exact snapshot notice to every dated meeting/report file**

Immediately after each H1 heading add:

```markdown
> **Historical snapshot:** This dated meeting document preserves what was known
> at the time. It is not the current Report 2 status. See
> [report2_evidence_map.md](../experiment_logs/report2_evidence_map.md) for
> current evidence, supersession, and claim boundaries.
```

Do not alter the historical numerical statements below the notice.

- [ ] **Step 2: Import and normalize the English Week 15 meeting document**

Read the root-worktree source at:

`C:/Users/tangy/Desktop/floatpoint/docs/week15/week15-supervisor-meeting-en.md`

Create the branch file as:

`docs/week15/week15-supervisor-meeting-EN.md`

Preserve its body and numerical values exactly, change only the filename and
insert the snapshot notice. Do not copy the obsolete old temporal branch's
seventh figure or post-hoc fit claims.

- [ ] **Step 3: Import and label the executed translation plan**

Read the root-worktree source at:

`C:/Users/tangy/Desktop/floatpoint/docs/superpowers/plans/2026-07-09-week15-supervisor-meeting-english.md`

Create the same relative path on this branch and insert below its H1:

```markdown
> **Status (2026-07-22): EXECUTED.** The resulting document is the dated
> historical snapshot at `docs/week15/week15-supervisor-meeting-EN.md`.
```

- [ ] **Step 4: Run the historical-snapshot test**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_report2_documentation.py::test_dated_meeting_material_is_not_current_status -q
```

Expected: `1 passed`.

- [ ] **Step 5: Verify excluded root-worktree assets were not staged**

```powershell
git status --short
git ls-files --error-unmatch tmp7reev1u0 2>$null
git ls-files --error-unmatch tools/icm2026_export_schedule.py 2>$null
```

Expected: only the listed documentation changes appear; both `git ls-files`
commands fail because excluded assets are not tracked.

- [ ] **Step 6: Commit the historical-document classification**

```powershell
git add docs/week13/week13-supervisor-meeting.md docs/week13/week13-supervisor-meeting-EN.md docs/week14/week14-supervisor-meeting.md docs/week14/week14-supervisor-meeting-EN.md docs/week15/week15-supervisor-meeting.md docs/week15/week15-supervisor-meeting-EN.md docs/week15/week15-supervisor-report.md docs/superpowers/plans/2026-07-09-week15-supervisor-meeting-english.md
git commit -m "docs(report2): classify dated supervisor material"
```

---

### Task 5: Update permanent indexes and baseline-status wording

**Files:**
- Modify: `docs/INDEX.md`
- Modify: `docs/requirement/overall.md`
- Modify: `docs/HARNESS.md`
- Modify: `scripts/README.md`
- Test: `tests/py/test_report2_documentation.py`

**Interfaces:**
- Consumes: the canonical evidence map and Week 14-16 files.
- Produces: permanent navigation that distinguishes requirements, current status, historical evidence, and deferred work.

- [ ] **Step 1: Update `docs/INDEX.md`**

Make these exact structural changes:

- replace the mutable `Default branch / Active branch` line with `Integration: see Git topology and the Report 2 evidence map; do not infer status from a worktree branch name`;
- add `report2_evidence_map.md` to the concern table as the Report 2 current source of truth;
- add Week 14, Week 15, and Week 16 rows linking each canonical plan and summary;
- add a Report 2 section linking the evidence map, the current completion design, the GPU plan, and the temporal negative result;
- identify meeting reports as dated historical snapshots;
- change the footer date to `2026-07-22`.

- [ ] **Step 2: Mark `overall.md` as baseline requirements**

Immediately below its title add:

```markdown
> **Status note (2026-07-22):** This file preserves the baseline requirements
> and original 20-week schedule. It is not the current implementation-status
> authority. Use [report2_evidence_map.md](../experiment_logs/report2_evidence_map.md)
> for delivered, superseded, negative, and deferred Report 2 evidence.
```

Do not rewrite the original schedule or planned architecture.

- [ ] **Step 3: Correct the stale GPU status in `docs/HARNESS.md`**

Replace the statement that GPU is simply not included because it is a Week 5/6
bring-up item with a bounded status paragraph:

```markdown
The canonical CPU matrix remains the default harness path. The Euler CUDA
correctness path exists, but a report-grade generic GPU matrix and MHD GPU path
are not yet complete. Hardware-axis conclusions therefore remain deferred; see
`docs/experiment_logs/report2_evidence_map.md`.
```

- [ ] **Step 4: Register temporal divergence in `scripts/README.md`**

Add `scripts/regression/mhd_temporal_divergence.py` under the Report 2
regression entries and describe it as the canonical fixed-window,
provenance-gated fp32/fp64 HLL temporal driver. Do not copy the old branch's
implementation or numerical claims.

- [ ] **Step 5: Run the complete documentation contract**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_report2_documentation.py -q
```

Expected: `4 passed`.

- [ ] **Step 6: Commit permanent navigation updates**

```powershell
git add docs/INDEX.md docs/requirement/overall.md docs/HARNESS.md scripts/README.md tests/py/test_report2_documentation.py
git commit -m "docs(report2): route canonical status and evidence"
```

---

### Task 6: Verify canonicalization and prepare integration

**Files:**
- Verify only; no planned source changes.

**Interfaces:**
- Consumes: all previous task commits.
- Produces: fresh evidence that the branch is complete for this documentation phase and linearly integrable.

- [ ] **Step 1: Run the full Python test suite**

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py -q
```

Expected: all tests pass; the exact count is reported from the fresh run.

- [ ] **Step 2: Audit changed Markdown links**

Run a Python one-liner or short read-only script that extracts relative Markdown
links from every changed `.md` file, ignores external URLs and anchors, resolves
each link relative to its document, and exits nonzero for missing targets.

Expected: exit 0 and no missing local links.

- [ ] **Step 3: Audit tracked evidence and excluded assets**

```powershell
git diff --check
git status --short
git ls-files | Select-String -Pattern '\.bin$|(^|/)build[^/]*/|tmp7reev1u0|tools/icm2026_export_schedule.py'
git check-ignore -v experiments/week15/mhd_temporal_divergence/runs 2>$null
```

Expected: clean whitespace, no unintended tracked binary/build/temp/tool path,
and temporal run directories remain ignored.

- [ ] **Step 4: Verify branch topology**

```powershell
git merge-base --is-ancestor main week16-evidence-completion
git merge-base --is-ancestor week12-mhd-implementation week16-evidence-completion
git merge-base --is-ancestor codex/mhd-temporal-divergence week16-evidence-completion
git log --oneline --decorate main..week16-evidence-completion
```

Expected: the first two ancestry checks return 0; the obsolete temporal branch
check returns nonzero; the log is linear and contains the canonicalization
commits.

- [ ] **Step 5: Create a durable local backup reference**

```powershell
git branch report2-pre-integration-backup week16-evidence-completion
```

Expected: the backup branch points at the same commit as
`week16-evidence-completion`. Keep both branches.

- [ ] **Step 6: Report integration readiness before changing another branch**

Record:

- final branch commit;
- fresh pytest count;
- link-audit result;
- tracked-asset audit result;
- exact root-worktree conflict (`tests/py/test_mhd_temporal_divergence.py`);
- proposed target branch and `git merge --ff-only` command.

Do not perform the fast-forward until the root-worktree conflict is safely
preserved and the intended target branch is explicit.
