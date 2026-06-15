#pragma once

#include "mhd/mhd_state.hpp"

#include <cmath>

namespace hrsc {

template <typename Real>
HD_FUNC Real mhd_minmod(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return (std::abs(a) < std::abs(b)) ? a : b;
}

template <typename Real>
HD_FUNC Vec<Real, MhdNVars> mhd_slope(const Vec<Real, MhdNVars>& Um,
                                      const Vec<Real, MhdNVars>& U0,
                                      const Vec<Real, MhdNVars>& Up) {
    Vec<Real, MhdNVars> s;
    for (int k = 0; k < MhdNVars; ++k) {
        s[k] = mhd_minmod(U0[k] - Um[k], Up[k] - U0[k]);
    }
    return s;
}

} // namespace hrsc
