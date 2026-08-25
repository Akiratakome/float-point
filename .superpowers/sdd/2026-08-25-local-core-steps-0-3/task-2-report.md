# Task 2 report: `config_filename`

## RED evidence

Added the six `config_filename` contract tests to
`tests/py/test_aiinfra_harness_contract.py`, then ran:

```text
python -m pytest tests/py/test_aiinfra_harness_contract.py -q -k config_filename
```

Observed before implementation:

```text
1 passed, 5 failed, 7 deselected in 0.04s
```

The default-name behavior passed through the existing legacy path. The five
bare-name validation cases failed because `normalise_run` ignored the new
field, confirming the tests exercised the missing behavior.

## GREEN evidence

After the minimal implementation:

```text
python -m pytest tests/py/test_aiinfra_harness_contract.py -q -k config_filename
6 passed, 7 deselected in 0.06s

python -m pytest tests/py/test_aiinfra_harness_contract.py tests/py/test_harness_scripts.py -q
45 passed in 1.24s
```

## Changes

- `scripts/run_matrix.py`
  - Added `MatrixRun.config_filename`, defaulting to `config.cfg`.
  - Validated it as a bare filename during normalization.
  - Materialized into the selected filename.
  - Applied cfg overrides only to `.cfg` files and rejected overrides for
    non-`.cfg` filenames.
  - Used the selected filename in canonical and legacy metadata paths.
- `tests/py/test_aiinfra_harness_contract.py`
  - Added default, JSON verbatim-copy, fail-closed override, and invalid-name
    coverage.

## Self-review

- Existing HRSC defaults retain `config.cfg`, the same cfg override behavior,
  command shape, and metadata field sets.
- Non-`.cfg` source files are copied without text rewriting when no cfg
  overrides are requested.
- Filename traversal and path-separator inputs fail before materialization.
- `git diff --check` produced no whitespace errors.

## Concerns

None identified within Task 2 scope. `output_file` is intentionally only
translated into cfg overrides for `.cfg` configurations, matching the brief.
