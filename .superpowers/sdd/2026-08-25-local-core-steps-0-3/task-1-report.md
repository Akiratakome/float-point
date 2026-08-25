# Task 1 report: `run_matrix` optional arguments

## Implementation

- Added `MatrixRun.arguments: tuple[str, ...]`, defaulting to `()`.
- Added validation in `normalise_run`: `arguments` must be a list of strings; malformed values raise `ValueError`.
- Added `build_command(run, config)`, placing arguments between the binary and materialised config.
- Updated `run_one` to use the shared command builder.
- Added contract tests covering legacy commands, argument insertion, and validation.

## Files

- `scripts/run_matrix.py`
- `tests/py/test_aiinfra_harness_contract.py`

## TDD evidence

RED command:

```text
python -m pytest tests/py/test_aiinfra_harness_contract.py -q
```

Result: `5 failed`. The failures were the expected missing `MatrixRun.arguments` / `build_command` behavior and missing malformed-argument validation.

GREEN command:

```text
python -m pytest tests/py/test_aiinfra_harness_contract.py tests/py/test_harness_scripts.py tests/py/test_harness_runner.py -q
```

Result: `63 passed in 1.70s`.

## Self-review

`git diff --check` passed. The implementation is additive and leaves absent `arguments` as an empty tuple, preserving the two-token HRSC command contract. The command builder uses `Path.as_posix()` for the binary so the contract remains stable on Windows, where `str(Path(...))` would otherwise convert the legacy forward slash to a backslash.

## Concerns

No known functional concerns. The focused regression suite passed in full.
