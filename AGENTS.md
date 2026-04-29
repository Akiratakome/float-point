# Agent Map

Read `docs/INDEX.md` first. This repository is a numerical experiment harness:
the pipeline is the deliverable, and the solver is only one component.

Hard rules:

- Do not change solver numerics or existing cfg defaults unless the user asks.
- Keep existing output formats stable.
- Fit experiment work into `config -> build -> run -> measure -> aggregate -> plot`.
- Prefer scripted, logged runs over manual one-off commands.
- Save run metadata with configs and summaries.
- Do not commit build directories or large transient grids.

Canonical harness guide: `docs/HARNESS.md`.
