#pragma once

#include <cmath>
#include <algorithm>

namespace hrsc {

template <typename Real>
struct ErrorNorms { Real L1, L2, Linf; };

// Dimension-agnostic error norm computation.
// dV = dx for 1D, dx*dy for 2D.
template <typename Real>
ErrorNorms<Real> compute_error(const Real* numerical, const Real* exact,
                               int total_cells, Real dV)
{
    Real sum_L1  = Real(0);
    Real sum_L2  = Real(0);
    Real max_err = Real(0);

    for (int i = 0; i < total_cells; ++i) {
        Real diff = std::abs(numerical[i] - exact[i]);
        sum_L1  += diff;
        sum_L2  += diff * diff;
        max_err  = std::max(max_err, diff);
    }

    return {sum_L1 * dV, std::sqrt(sum_L2 * dV), max_err};
}

} // namespace hrsc
