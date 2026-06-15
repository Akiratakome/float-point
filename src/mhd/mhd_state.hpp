#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"

#include <cassert>
#include <cmath>
#include <limits>

namespace hrsc {

static constexpr int MhdNVars = 9;

struct MhdIdx {
    enum { RHO = 0, MX = 1, MY = 2, MZ = 3, BX = 4, BY = 5, BZ = 6, E = 7, PSI = 8 };
};

template <typename Real>
struct MhdPrim {
    Real rho, vx, vy, vz, Bx, By, Bz, p, psi;
};

template <typename Real>
HD_FUNC Vec<Real, MhdNVars> prim_to_cons(const MhdPrim<Real>& w, Real gamma) {
    Vec<Real, MhdNVars> U;
    const Real v2 = w.vx*w.vx + w.vy*w.vy + w.vz*w.vz;
    const Real B2 = w.Bx*w.Bx + w.By*w.By + w.Bz*w.Bz;
    U[MhdIdx::RHO] = w.rho;
    U[MhdIdx::MX]  = w.rho * w.vx;
    U[MhdIdx::MY]  = w.rho * w.vy;
    U[MhdIdx::MZ]  = w.rho * w.vz;
    U[MhdIdx::BX]  = w.Bx;
    U[MhdIdx::BY]  = w.By;
    U[MhdIdx::BZ]  = w.Bz;
    U[MhdIdx::E]   = w.p / (gamma - Real(1)) + Real(0.5) * w.rho * v2 + Real(0.5) * B2;
    U[MhdIdx::PSI] = w.psi;
    return U;
}

template <typename Real>
HD_FUNC Real pressure(const Vec<Real, MhdNVars>& U, Real gamma) {
    const Real rho = U[MhdIdx::RHO];
    assert(rho > std::numeric_limits<Real>::min());

    const Real v2 = (U[MhdIdx::MX]*U[MhdIdx::MX]
                   + U[MhdIdx::MY]*U[MhdIdx::MY]
                   + U[MhdIdx::MZ]*U[MhdIdx::MZ]) / (rho * rho);
    const Real B2 = U[MhdIdx::BX]*U[MhdIdx::BX]
                  + U[MhdIdx::BY]*U[MhdIdx::BY]
                  + U[MhdIdx::BZ]*U[MhdIdx::BZ];
    return (gamma - Real(1)) * (U[MhdIdx::E] - Real(0.5)*rho*v2 - Real(0.5)*B2);
}

template <typename Real>
HD_FUNC MhdPrim<Real> cons_to_prim(const Vec<Real, MhdNVars>& U, Real gamma) {
    MhdPrim<Real> w;
    w.rho = U[MhdIdx::RHO];
    assert(w.rho > std::numeric_limits<Real>::min());

    w.vx  = U[MhdIdx::MX] / w.rho;
    w.vy  = U[MhdIdx::MY] / w.rho;
    w.vz  = U[MhdIdx::MZ] / w.rho;
    w.Bx  = U[MhdIdx::BX];
    w.By  = U[MhdIdx::BY];
    w.Bz  = U[MhdIdx::BZ];
    w.psi = U[MhdIdx::PSI];
    w.p   = pressure(U, gamma);
    return w;
}

template <typename Real>
HD_FUNC Real fast_speed_x(const MhdPrim<Real>& w, Real gamma) {
    assert(w.rho > std::numeric_limits<Real>::min());

    const Real B2 = w.Bx*w.Bx + w.By*w.By + w.Bz*w.Bz;
    const Real a2 = gamma * w.p / w.rho;
    const Real ca2 = B2 / w.rho;
    const Real cax2 = w.Bx*w.Bx / w.rho;
    Real disc = (a2 + ca2)*(a2 + ca2) - Real(4)*a2*cax2;
    disc = disc > Real(0) ? disc : Real(0);
    return std::sqrt(Real(0.5) * ((a2 + ca2) + std::sqrt(disc)));
}

} // namespace hrsc
