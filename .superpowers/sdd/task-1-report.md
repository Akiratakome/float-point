# Task 1 Report: Shared cfg Materialization

## Implementation Summary

Added shared cfg materialization helpers and migrated both callers to use them.
The existing `run_matrix._replace_or_append_cfg_line` and
`_mhd_harness.replace_or_append_cfg` names remain callable aliases. Matrix
binary output overrides are applied after `extra_cfg` overrides.

## Files Changed

- `scripts/harness/__init__.py`
- `scripts/harness/config.py`
- `scripts/run_matrix.py`
- `scripts/regression/_mhd_harness.py`
- `tests/py/test_harness_config.py`

## RED

Command:

```text
& 'C:\Users\tangy\miniconda3\envs\floatpoint\python.exe' -m pytest tests/py/test_harness_config.py -q
```

Output:

```text
E   ModuleNotFoundError: No module named 'scripts.harness'
1 error during collection
```

Reason: the contract test correctly failed because the shared `scripts.harness`
module did not yet exist.

## GREEN

Command:

```text
& 'C:\Users\tangy\miniconda3\envs\floatpoint\python.exe' -m pytest tests/py/test_harness_config.py tests/py/test_harness_scripts.py::test_run_matrix_writes_metadata_and_preserves_cfg tests/py/test_harness_scripts.py::test_run_matrix_applies_extra_cfg_overrides tests/py/test_mhd_harness.py::test_replace_or_append_cfg_preserves_inline_comment tests/py/test_mhd_harness.py::test_replace_or_append_cfg_appends_missing_key_with_trailing_newline -q
```

Output:

```text
......                                                                   [100%]
6 passed in 0.20s
```

## Full Python Suite

Command:

```text
& 'C:\Users\tangy\miniconda3\envs\floatpoint\python.exe' -m pytest tests/py -q
```

Result:

```text
259 passed, 10 skipped in 9.65s
```

## Self-Review

- Source cfg files remain unmodified; materialization copies before applying overrides.
- Inline comments and trailing newlines are preserved by the shared replacement helper.
- `extra_cfg` is ordered first and explicit binary output overrides are ordered last.
- Both compatibility aliases point to the shared `replace_or_append_cfg` function.
- Direct public runner paths were checked with `scripts/run_matrix.py --help` and the MHD Verificarlo runner help command.
- `git diff --check` reported no whitespace errors.
- Commit contains exactly the five Task 1 files.

## Concerns

No functional concerns. The full suite includes 10 skipped environment-gated tests.

Commit: `85a36ab refactor: share harness config materialization`

## Review Fix: Output Override Precedence Coverage

### Fix Summary

Strengthened `test_run_matrix_applies_extra_cfg_overrides` in
`tests/py/test_harness_scripts.py` so `extra_cfg` now conflicts with both
explicit binary output settings:

- `output_format = binary`
- `output_file = stale/path.bin`

The existing assertions verify that the generated run's `output_format` and
`run.raw_output` are applied last. No implementation change was required.

### TDD / Current Behavior Check

The test was modified before verification. Because the implementation already
builds `extra_cfg` first and applies `output_format` and `output_file` after it,
the intended regression assertion passed immediately. This is documented as a
coverage fix rather than an implementation RED.

Command:

```text
& 'C:\Users\tangy\miniconda3\envs\floatpoint\python.exe' -m pytest tests/py/test_harness_scripts.py::test_run_matrix_applies_extra_cfg_overrides -q
```

Output:

```text
.                                                                        [100%]
1 passed in 0.12s
```

### Focused and Covering Harness Tests

Command:

```text
& 'C:\Users\tangy\miniconda3\envs\floatpoint\python.exe' -m pytest tests/py/test_harness_config.py tests/py/test_harness_scripts.py tests/py/test_mhd_harness.py -q
```

Output:

```text
............................                                             [100%]
28 passed in 0.47s
```
