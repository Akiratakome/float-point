#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/eos.hpp"
#include "euler/euler_flux.hpp"

#include <algorithm>
#include <cmath>

namespace hrsc {

// Rusanov (Local Lax-Friedrichs) approximate Riemann solver.
// F = 0.5 * (F_L + F_R) - 0.5 * S_max * (U_R - U_L)
// where S_max = max(|u_L| + a_L, |u_R| + a_R).
//
// Unlike HLLC, this flux has zero branching — a single arithmetic
// expression. More diffusive, but useful as a baseline for
// floating-point sensitivity analysis (no branch-dependent code paths).
template <typename Real>
HD_FUNC Vec<Real, EulerNVars> rusanov_flux(
    const Vec<Real, EulerNVars>& qL, const Vec<Real, EulerNVars>& qR, Real gamma)
{
    // Primitive variables
    Real rhoL = qL[RHO];
    Real uL   = qL[RHOU] / rhoL;
    Real pL   = pressure(qL, gamma);
    Real aL   = sound_speed(rhoL, pL, gamma);

    Real rhoR = qR[RHO];
    Real uR   = qR[RHOU] / rhoR;
    Real pR   = pressure(qR, gamma);
    Real aR   = sound_speed(rhoR, pR, gamma);

    // Maximum wave speed
    Real S_max = std::max(std::abs(uL) + aL, std::abs(uR) + aR);

    // Physical fluxes
    Vec<Real, EulerNVars> FL = euler_flux_x(qL, gamma);
    Vec<Real, EulerNVars> FR = euler_flux_x(qR, gamma);

    // Rusanov flux: centred average minus diffusion
    return (FL + FR) * Real(0.5) - (qR - qL) * (Real(0.5) * S_max);
}

} // namespace hrsc
