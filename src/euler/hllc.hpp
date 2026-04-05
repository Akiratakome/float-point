#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/eos.hpp"
#include "euler/euler_flux.hpp"

#include <algorithm>
#include <cmath>

namespace hrsc {

// HLLC approximate Riemann solver (Toro 2009, Chapter 10).
// Takes left/right conserved states, returns intercell flux.
// Wave speed estimates: Davis (simplest, robust).
// Compile flag RIEMANN_STRICT_INEQUALITY controls <= vs < in flux selection.
template <typename Real>
HD_FUNC Vec<Real, 4> hllc_flux(
    const Vec<Real, 4>& qL, const Vec<Real, 4>& qR, Real gamma)
{
    // --- Primitive variables ---
    Real rhoL = qL[RHO];
    Real uL   = qL[RHOU] / rhoL;
    Real vL   = qL[RHOV] / rhoL;
    Real pL   = pressure(qL, gamma);
    Real aL   = sound_speed(rhoL, pL, gamma);

    Real rhoR = qR[RHO];
    Real uR   = qR[RHOU] / rhoR;
    Real vR   = qR[RHOV] / rhoR;
    Real pR   = pressure(qR, gamma);
    Real aR   = sound_speed(rhoR, pR, gamma);

    // --- Wave speed estimates (Davis) ---
    Real SL = std::min(uL - aL, uR - aR);
    Real SR = std::max(uL + aL, uR + aR);

    // --- Contact wave speed S* ---
    Real S_star = (pR - pL
                   + rhoL * uL * (SL - uL)
                   - rhoR * uR * (SR - uR))
                / (rhoL * (SL - uL) - rhoR * (SR - uR));

    // --- Physical fluxes ---
    Vec<Real, 4> FL = euler_flux_x(qL, gamma);
    Vec<Real, 4> FR = euler_flux_x(qR, gamma);

    // --- Flux selection ---
    if (SL >= Real(0)) {
        return FL;
    }

#ifdef RIEMANN_STRICT_INEQUALITY
    if (SL < Real(0) && Real(0) < S_star) {
#else
    if (SL <= Real(0) && Real(0) <= S_star) {
#endif
        // Left star state
        Real coeff = rhoL * (SL - uL) / (SL - S_star);
        Vec<Real, 4> U_starL = {
            coeff,
            coeff * S_star,
            coeff * vL,
            coeff * (qL[EN] / rhoL
                     + (S_star - uL) * (S_star + pL / (rhoL * (SL - uL))))
        };
        return FL + (U_starL - qL) * SL;
    }

#ifdef RIEMANN_STRICT_INEQUALITY
    if (S_star < Real(0) && Real(0) < SR) {
#else
    if (S_star <= Real(0) && Real(0) <= SR) {
#endif
        // Right star state
        Real coeff = rhoR * (SR - uR) / (SR - S_star);
        Vec<Real, 4> U_starR = {
            coeff,
            coeff * S_star,
            coeff * vR,
            coeff * (qR[EN] / rhoR
                     + (S_star - uR) * (S_star + pR / (rhoR * (SR - uR))))
        };
        return FR + (U_starR - qR) * SR;
    }

    // SR <= 0
    return FR;
}

} // namespace hrsc
