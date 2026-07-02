"""Pure aggregation helpers for the Week 14 MHD precision pilot."""

import csv
import json
import math
from pathlib import Path

REFERENCE = "cpu-double-O2-ieee-leq"
ANCHOR_STEPS = 759
ANCHOR_DIVB_MAX = 4.441e-14
ANCHOR_DIVB_ATOL = 1.0e-13

MCA_FIELD_KEYS = (
    "spread_rho",
    "spread_By",
    "spread_p",
    "spread_vx",
    "snr_rho",
    "snr_By",
    "snr_p",
    "rho_mean_spread",
)

_ROW_REQUIRED_KEYS = (
    "variant",
    "precision",
    "opt",
    "fastmath",
    "riemann",
    "finite",
    "rc",
    "steps",
    "divB_max",
    "walltime_s",
    "is_reference",
    "L1_rho",
    "L2_rho",
    "Linf_rho",
    "L1_By",
    "L2_By",
    "Linf_By",
    "L1_p",
    "L2_p",
    "Linf_p",
    "L1_vx",
    "L2_vx",
    "Linf_vx",
)
_ROW_FINITE_NUMBER_KEYS = (
    "divB_max",
    "walltime_s",
    "L1_rho",
    "L2_rho",
    "Linf_rho",
    "L1_By",
    "L2_By",
    "Linf_By",
    "L1_p",
    "L2_p",
    "Linf_p",
    "L1_vx",
    "L2_vx",
    "Linf_vx",
)
SUMMARY_CSV_COLUMNS = _ROW_REQUIRED_KEYS
_MCA_BLOCK_REQUIRED_KEYS = ("status", "n", *MCA_FIELD_KEYS)
_MCA_REQUIRED_BLOCKS = ("p53", "p24")
_MCA_STATUSES = {
    "completed",
    "blocked_environment",
    "blocked_run",
    "runnable_environment",
    "failed",
    "missing",
    "pending",
}


def blocked_mca_block(status, reason):
    """Return a schema-complete MCA block for an unavailable evidence run."""
    block = {key: None for key in MCA_FIELD_KEYS}
    block.update(
        {
            "status": status,
            "reason": reason,
            "n": 0,
            "mca_evidence_generated": False,
        }
    )
    return block


def schema_valid(rows, mca):
    """Return True when deterministic rows and MCA blocks expose required keys."""
    if not isinstance(rows, list) or not isinstance(mca, dict):
        return False
    if any(not _row_schema_valid(row) for row in rows):
        return False
    if not _mca_has_required_blocks(mca):
        return False
    return all(_mca_block_schema_valid(block) for block in _mca_blocks(mca))


def gate_g0(rows, mca):
    """Gate G0: finite deterministic runs, reproduced anchor, schema, MCA shape."""
    schema_ok = schema_valid(rows, mca)
    all_finite = bool(rows) and all(row.get("finite") is True for row in rows)
    anchor_reproduced = _anchor_reproduced(rows)
    mca_representable = schema_ok and _mca_representable(mca)
    passed = all((all_finite, anchor_reproduced, schema_ok, mca_representable))
    return {
        "pass": passed,
        "all_finite": all_finite,
        "anchor_reproduced": anchor_reproduced,
        "schema_valid": schema_ok,
        "mca_representable": mca_representable,
    }


def ordering_flags(rows):
    """Emit soft flags where fastmath is unexpectedly closer than IEEE."""
    by_axis = {}
    for row in rows:
        if not _row_schema_valid(row):
            continue
        key = (row.get("precision"), row.get("opt"), row.get("riemann"))
        if None in key:
            continue
        slot = by_axis.setdefault(key, {})
        slot[row.get("fastmath")] = row

    flags = []
    for (precision, opt, riemann), pair in sorted(by_axis.items()):
        ieee = pair.get(False)
        fastmath = pair.get(True)
        if not ieee or not fastmath:
            continue
        ieee_linf = ieee.get("Linf_rho")
        fastmath_linf = fastmath.get("Linf_rho")
        if _is_number(ieee_linf) and _is_number(fastmath_linf) and fastmath_linf < ieee_linf:
            flags.append(
                {
                    "axis": "fastmath",
                    "precision": precision,
                    "opt": opt,
                    "riemann": riemann,
                    "ieee_variant": ieee.get("variant"),
                    "fastmath_variant": fastmath.get("variant"),
                    "ieee_Linf_rho": ieee_linf,
                    "fastmath_Linf_rho": fastmath_linf,
                }
            )
    return flags


def gate_g1(rows):
    """Gate G1 reports deterministic ordering soft flags."""
    flags = ordering_flags(rows)
    row_schema_ok = isinstance(rows, list) and all(_row_schema_valid(row) for row in rows)
    all_finite = bool(rows) and all(row.get("finite") is True for row in rows)
    anchor_ok = _anchor_reproduced(rows)
    return {
        "pass": row_schema_ok and all_finite and anchor_ok,
        "row_schema_valid": row_schema_ok,
        "all_finite": all_finite,
        "anchor_ok": anchor_ok,
        "ordering_flags": flags,
    }


def gate_g2(mca):
    """Gate G2 reports whether MCA depth has enough completed evidence to assess."""
    completed = {
        name: block
        for name, block in _named_mca_blocks(mca).items()
        if _has_meaningful_completed_spreads(block)
    }
    status = "evaluated" if any(name in completed for name in ("p53", "p24")) else "pending_depth"
    return {
        "status": status,
        "completed_blocks": sorted(completed),
        "p53_near_eps": _mca_near_eps(completed.get("p53")),
        "p24_float_scale": _mca_float_scale(completed.get("p24")),
    }


def assemble_summary(rows, mca, git_commit):
    """Assemble the stable experiment summary payload."""
    return {
        "experiment": "week14-mhd-precision-pilot",
        "case": "brio_wu_1d",
        "solver": "hll",
        "reference": REFERENCE,
        "git_commit": git_commit,
        "deterministic": list(rows),
        "mca": mca,
        "gates": {
            "G0": gate_g0(rows, mca),
            "G1": gate_g1(rows),
            "G2": gate_g2(mca),
        },
        "claims": {
            "morphology": "Report only morphology after G0 passes and deterministic rows are finite.",
            "self_reference": "Reference claims are anchored to the cpu double O2 IEEE leq run.",
            "precision_noise": "Precision-noise claims remain provisional until MCA depth is evaluated.",
        },
    }


def write_summaries(summary, out_dir):
    """Write authoritative JSON plus stable CSV and Markdown summary views."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    with (out_path / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")

    with (out_path / "summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in summary.get("deterministic", []):
            writer.writerow(row)

    (out_path / "summary.md").write_text(_summary_markdown(summary), encoding="utf-8")


def _summary_markdown(summary):
    lines = [
        "# MHD Precision Pilot Summary",
        "",
        f"- Experiment: {_markdown_text(summary.get('experiment'))}",
        f"- Case: {_markdown_text(summary.get('case'))}",
        f"- Solver: {_markdown_text(summary.get('solver'))}",
        f"- Reference: {_markdown_text(summary.get('reference'))}",
        f"- Git commit: {_markdown_text(summary.get('git_commit'))}",
        "",
        "## G0",
        "",
        f"- Pass: {_markdown_text(summary.get('gates', {}).get('G0', {}).get('pass'))}",
        "",
        "## Deterministic variants",
        "",
        _markdown_table(SUMMARY_CSV_COLUMNS, summary.get("deterministic", [])),
        "",
        "## MCA",
        "",
        _mca_markdown_table(summary.get("mca", {})),
        "",
        "## Ordering flags",
        "",
        _markdown_table(
            (
                "axis", "precision", "opt", "riemann", "ieee_variant",
                "fastmath_variant", "ieee_Linf_rho", "fastmath_Linf_rho",
            ),
            summary.get("gates", {}).get("G1", {}).get("ordering_flags", []),
        ),
        "",
        "## Claim buckets",
        "",
    ]
    claims = summary.get("claims", {})
    if claims:
        for name in sorted(claims):
            lines.append(f"- {_markdown_text(name)}: {_markdown_text(claims.get(name))}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _mca_markdown_table(mca):
    columns = ("name", "status", "reason", "n", "runner", "mca_evidence_generated", *MCA_FIELD_KEYS)
    rows = []
    for name, block in sorted(_named_mca_blocks(mca).items()):
        row = {"name": name}
        row.update(block)
        rows.append(row)
    return _markdown_table(columns, rows)


def _markdown_table(columns, rows):
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_markdown_cell(row.get(column)) for column in columns) + " |"
        for row in rows
    ]
    if not body:
        body = ["| " + " | ".join("" for _ in columns) + " |"]
    return "\n".join([header, divider, *body])


def _display(value):
    if value is None:
        return ""
    return str(value)


def _markdown_cell(value):
    return _display(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def _markdown_text(value):
    return _display(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def _has_keys(mapping, keys):
    return all(key in mapping for key in keys)


def _row_schema_valid(row):
    if not isinstance(row, dict) or not _has_keys(row, _ROW_REQUIRED_KEYS):
        return False
    if not all(isinstance(row.get(key), bool) for key in ("finite", "fastmath", "is_reference")):
        return False
    if not all(_is_int(row.get(key)) for key in ("steps", "rc")):
        return False
    if row.get("rc") != 0:
        return False
    return all(_is_number(row.get(key)) for key in _ROW_FINITE_NUMBER_KEYS)


def _mca_has_required_blocks(mca):
    return all(isinstance(mca.get(name), dict) for name in _MCA_REQUIRED_BLOCKS)


def _mca_blocks(mca):
    if _looks_like_mca_block(mca):
        return [mca]
    if not _mca_has_required_blocks(mca):
        return []
    return [mca[name] for name in _MCA_REQUIRED_BLOCKS]


def _named_mca_blocks(mca):
    if not isinstance(mca, dict):
        return {}
    if _looks_like_mca_block(mca):
        return {"mca": mca}
    return {name: block for name, block in mca.items() if isinstance(block, dict)}


def _looks_like_mca_block(value):
    return isinstance(value, dict) and "status" in value and any(key in value for key in MCA_FIELD_KEYS)


def _mca_block_schema_valid(block):
    if not isinstance(block, dict) or not _has_keys(block, _MCA_BLOCK_REQUIRED_KEYS):
        return False
    if block.get("status") not in _MCA_STATUSES:
        return False
    if not isinstance(block.get("n"), int) or block.get("n") < 0:
        return False
    if block.get("status") == "completed":
        return all(_is_number(block.get(key)) for key in MCA_FIELD_KEYS)
    return all(block.get(key) is None or _is_number(block.get(key)) for key in MCA_FIELD_KEYS)


def _mca_representable(mca):
    if not isinstance(mca, dict) or not _mca_has_required_blocks(mca):
        return False
    for block in _mca_blocks(mca):
        status = block.get("status")
        if status not in _MCA_STATUSES:
            return False
        if status == "completed" and not all(_is_number(block.get(key)) for key in MCA_FIELD_KEYS):
            return False
    return True


def _anchor_reproduced(rows):
    for row in rows:
        if not _is_reference_row(row):
            continue
        if row.get("steps") != ANCHOR_STEPS:
            continue
        divb = row.get("divB_max")
        if _is_number(divb) and abs(divb - ANCHOR_DIVB_MAX) <= ANCHOR_DIVB_ATOL:
            return True
    return False


def _is_reference_row(row):
    return (
        row.get("variant") == REFERENCE
        and row.get("precision") == "double"
        and row.get("opt") == "O2"
        and row.get("fastmath") is False
        and row.get("riemann") == "leq"
    )


def _has_meaningful_completed_spreads(block):
    return _completed_spread_metrics(block) is not None


def _completed_spread_metrics(block):
    if not _mca_block_schema_valid(block) or block.get("n") < 2:
        return None
    spreads = [block.get(key) for key in ("spread_rho", "spread_By", "spread_p")]
    if not all(_is_number(value) for value in spreads):
        return None
    return spreads


def _mca_float_scale(block):
    spreads = _completed_spread_metrics(block)
    return spreads is not None and max(spreads) >= 1.0e-12


def _mca_near_eps(block):
    spreads = _completed_spread_metrics(block)
    return spreads is not None and max(spreads) < 1.0e-12


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)
