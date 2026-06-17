#pragma once

#include "mhd/mhd_flux.hpp"

#include <algorithm>

namespace hrsc {

template <typename Real>
HD_FUNC Vec<Real, MhdNVars> mhd_hll_flux(const Vec<Real, MhdNVars>& UL,
                                         const Vec<Real, MhdNVars>& UR,
                                         Real gamma, Real ch) {
    const MhdPrim<Real> wl = cons_to_prim(UL, gamma);
    const MhdPrim<Real> wr = cons_to_prim(UR, gamma);
    const Real cfL = fast_speed_x(wl, gamma);
    const Real cfR = fast_speed_x(wr, gamma);

    const Real SL = std::min(std::min(wl.vx - cfL, wr.vx - cfR), -ch);
    const Real SR = std::max(std::max(wr.vx + cfR, wl.vx + cfL), ch);

    const Vec<Real, MhdNVars> FL = mhd_flux_x(UL, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(UR, gamma, ch);

#ifdef RIEMANN_STRICT_INEQUALITY
    if (SL > Real(0)) return FL;
    if (SR < Real(0)) return FR;
#else
    if (SL >= Real(0)) return FL;
    if (SR <= Real(0)) return FR;
#endif

    Vec<Real, MhdNVars> F;
    const Real inv = Real(1) / (SR - SL);
    for (int k = 0; k < MhdNVars; ++k)
        F[k] = (SR*FL[k] - SL*FR[k] + SL*SR*(UR[k] - UL[k])) * inv;
    return F;
}

} // namespace hrsc
