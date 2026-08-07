#!/usr/bin/env python3
"""HLLD decision counts: measuring the exposure the branch-rule axis relies on.

Report 2 argues that exposure to an implementation detail follows from how many
internal decisions can be reached. For HLLD the <= / < variants can differ only
where a tie quantity is exactly zero, so counting exact zeros at S*_L, S*_R and
S_M measures that exposure directly instead of inferring it from the observed
discrepancy.

Uses the opt-in HRSC_HLLD_COUNTERS build so the default binary, and the timings
reported from it, are unchanged.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "week21" / "hlld_decision_counts"
EXPERIMENT = "week21-hlld-decision-counts"

for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)

BINARY = ROOT / "build-hlld-counters" / "hrsc_mhd"
# The 512^2 Orszag-Tang rung is the one the manuscript flags as unknown: it is
# the ladder that needed the per-line first-order HLL fallback, so its fallback
# count is the measurement that decides whether those diagnostics describe HLLD
# alone or HLLD together with its fallback policy.
CASES = [
    ("brio_wu_1d", ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg",
     {"nx": "800", "cfl": "0.4"}),
    ("orszag_tang_2d_256", ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
     {"nx": "256", "ny": "256", "cfl": "0.2"}),
    ("orszag_tang_2d_512", ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
     {"nx": "512", "ny": "512", "cfl": "0.2"}),
]
COUNTER_RE = re.compile(r'\{"hlld_counters":\s*(\{.*?\})\}')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    binary = resolve_binary(BINARY)
    binary_sha = sha256_file(binary)
    rows = []
    for case, cfg_path, overrides in CASES:
        name = f"{case}-hlld-counters"
        run_dir = OUT / "runs" / name
        run_dir.mkdir(parents=True, exist_ok=True)
        cfg_text = cfg_path.read_text(encoding="utf-8")
        cfg_text = replace_or_append_cfg(cfg_text, "riemann", "hlld")
        cfg_text = replace_or_append_cfg(cfg_text, "device", "cpu")
        for key, value in overrides.items():
            cfg_text = replace_or_append_cfg(cfg_text, key, value)
        _proc, meta, stderr_text = run_case(
            label=name, cfg_text=cfg_text, run_dir=run_dir, bin_path=binary,
            source_cfg=cfg_path, commit=commit, binary_sha256=binary_sha,
            experiment=EXPERIMENT,
        )
        match = COUNTER_RE.search(stderr_text)
        if not match:
            raise RuntimeError(f"no counter record in stderr for {name}")
        counters = json.loads(match.group(1))
        calls = counters["calls"]
        ties = counters["tie_ssl"] + counters["tie_ssr"] + counters["tie_sm"]
        lines = counters["line_total_x"] + counters["line_total_y"]
        reverts = counters["line_revert_x"] + counters["line_revert_y"]
        rows.append({
            "case": case,
            "solver": "hlld",
            "config": overrides,
            "steps": meta["stderr_diagnostics"]["steps"],
            "counters": counters,
            "tie_total": ties,
            "tie_fraction": ties / calls if calls else None,
            "hlld_fallback_fraction": counters["fallback"] / calls if calls else None,
            "line_revert_total": reverts,
            "line_revert_fraction": reverts / lines if lines else None,
        })
        print(f"{case}: calls={calls} hlld_fallback={counters['fallback']} "
              f"ties(SsL/SsR/SM)={counters['tie_ssl']}/{counters['tie_ssr']}/"
              f"{counters['tie_sm']} "
              f"line_revert={reverts}/{lines} "
              f"({rows[-1]['line_revert_fraction']:.3e})")

    payload = {
        "schema": {"name": "hrsc.week21-hlld-decision-counts", "version": 1},
        "experiment": EXPERIMENT,
        "git_commit": commit,
        "binary": str(binary),
        "binary_sha256": binary_sha,
        "rows": rows,
        "claim_boundary": [
            "Counts describe the instrumented build; the default binary is uninstrumented.",
            "tie_* counts exact zeros, the only states at which <= and < can disagree.",
            "Counts are per interface evaluation, summed over all steps and sweeps.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
