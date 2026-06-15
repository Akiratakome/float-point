#pragma once

#include "mhd/mhd_state.hpp"

namespace hrsc {

template <typename Real>
HD_FUNC Vec<Real, MhdNVars> mhd_flux_x(const Vec<Real, MhdNVars>& U, Real gamma, Real ch) {
    const MhdPrim<Real> w = cons_to_prim(U, gamma);
    const Real B2 = w.Bx*w.Bx + w.By*w.By + w.Bz*w.Bz;
    const Real ptot = w.p + Real(0.5) * B2;
    const Real vdotB = w.vx*w.Bx + w.vy*w.By + w.vz*w.Bz;
    const Real mx = U[MhdIdx::MX];

    Vec<Real, MhdNVars> F;
    F[MhdIdx::RHO] = mx;
    F[MhdIdx::MX]  = mx*w.vx + ptot - w.Bx*w.Bx;
    F[MhdIdx::MY]  = mx*w.vy - w.Bx*w.By;
    F[MhdIdx::MZ]  = mx*w.vz - w.Bx*w.Bz;
    F[MhdIdx::BX]  = w.psi;
    F[MhdIdx::BY]  = w.By*w.vx - w.Bx*w.vy;
    F[MhdIdx::BZ]  = w.Bz*w.vx - w.Bx*w.vz;
    F[MhdIdx::E]   = (U[MhdIdx::E] + ptot)*w.vx - w.Bx*vdotB;
    F[MhdIdx::PSI] = ch*ch*w.Bx;
    return F;
}

} // namespace hrsc
