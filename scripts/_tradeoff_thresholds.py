"""Centralized constants for tradeoff regime classification.

The dynamic axis of the s_req(N) framework — "is this (solver, precision)
combination over-provisioned, well-matched, or limited at this grid?" — is
classified by the SIGN AND MAGNITUDE of (s_worst_q05 − s_req(N)). The
margins below define those bins; they are deliberately NOT folded into a
single composite scalar because doing so would hide the asymmetry between
"too much FP precision" and "not enough" — see plan §A4.2.2.

The bitwise reproducibility axis (a separate concern: do two runs on
different machines agree bit-for-bit?) is governed by s_reliability_q05
against a per-precision integer floor. These two axes never share
constants: bitwise is engineering-aligned, regime is data-aligned.

No magic numbers. Every value below has a written rationale; do not edit
without updating the comment.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Regime-margin thresholds: applied to (s_worst_q05 − s_req(N))
# ---------------------------------------------------------------------------

# > 2.0 → "over-provisioned": >2 spare significant digits beyond what the
# grid's truncation error can absorb; further FP precision is wasted.
REGIME_MARGIN_OVER_PROVISIONED = 2.0

# (1.0, 2.0] → "well-matched": round-off sits ~10× below truncation, exactly
# the safety margin needed for clean log-log convergence-rate fits.
REGIME_MARGIN_WELL_MATCHED = 1.0

# Below 1.0: solver is FP-limited (round-off and truncation comparable
# or round-off dominates); upgrade precision or use compensated summation.

# ---------------------------------------------------------------------------
# Bitwise-reproducibility thresholds: applied to s_reliability_q05
# ---------------------------------------------------------------------------

# Engineering convention: ~15 sig digits is the practical floor at which
# two double-precision runs on different IEEE-754 platforms agree to
# within last-bit noise (see Higham 2002 §1.3 on backward-stable double).
BITWISE_DOUBLE_S_RELIABILITY = 15

# Same convention for binary32 (~7 sig digits).
BITWISE_FLOAT_S_RELIABILITY = 7
