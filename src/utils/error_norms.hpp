#pragma once

#include <cmath>
#include <algorithm>

#include "core/grid.hpp"
#include "mhd/mhd_state.hpp"

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

namespace hrsc {

template <typename Real>
struct DivBNorms { Real mean, max; };

// Central-difference div(B). 1D uses dBx/dx; 2D adds dBy/dy.
// Interior cells only (skip first/last column/row so the stencil stays in-domain).
template <typename Real, typename Ptr>
DivBNorms<Real> compute_divB_norms(GridViewBase<Real, MhdNVars, Ptr> gv,
                                   int nx, int ny, Real dx, Real dy) {
    Real sum = Real(0), maxv = Real(0);
    long count = 0;
    const bool two_d = (ny > 1);
    const int j_begin = two_d ? 1 : 0;
    const int j_end = two_d ? ny - 1 : ny;
    for (int j = j_begin; j < j_end; ++j) {
        for (int i = 1; i < nx - 1; ++i) {
            Real div = (gv(i+1, j, MhdIdx::BX) - gv(i-1, j, MhdIdx::BX)) / (Real(2)*dx);
            if (two_d)
                div += (gv(i, j+1, MhdIdx::BY) - gv(i, j-1, MhdIdx::BY)) / (Real(2)*dy);
            Real a = std::abs(div);
            sum += a;
            maxv = std::max(maxv, a);
            ++count;
        }
    }
    return { count ? sum / Real(count) : Real(0), maxv };
}

} // namespace hrsc
