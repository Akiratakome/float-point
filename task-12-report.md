# Task 12 report

Implemented the Python-test GitHub Actions workflow in `.github/workflows/tests.yml`.
The workflow runs on pushes to `main` and on every pull request with Python 3.12,
`actions/checkout@v4`, and `actions/setup-python@v5`.

## Dependency inventory

The test imports were inspected read-only before choosing the install list. The
baseline packages are used directly throughout the suite:

- `numpy`
- `matplotlib`
- `pytest`

Two additional packages are required during test collection rather than being
optional: `tests/py/test_plot_hllc_rusanov_points.py:4` and
`tests/py/test_verificarlo_report1_refresh.py:3-4` import `PIL` and `pandas` at
module scope, with no `importorskip` guard. A collection check that blocked
those two imports produced `24 errors during collection`, including direct
`ModuleNotFoundError` failures for `PIL` and `pandas`. The workflow therefore
installs the minimal additional distributions `pillow` and `pandas`.

`skimage` was not added: its only test uses `pytest.importorskip("skimage.metrics")`,
and the local environment confirms that it is absent and correctly skipped.

## Verification

- Local imports: `import numpy, matplotlib, pytest, PIL, pandas` — `ok`.
- Fresh-basetemp suite: `python -m pytest tests/py -q --basetemp=.pytest_tmp-task12`
  — `548 passed, 25 skipped in 29.72s`.
- Workflow structure: conservative local text checks passed for the trigger,
  Python 3.12, action versions, test command, and absence of fixed result counts
  and `continue-on-error`.
- `git diff --check` — clean.

This task was committed locally only. **NOT pushed**; no `gh run` or other remote
operation was performed.
