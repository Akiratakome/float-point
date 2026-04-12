#pragma once

#include "core/types.hpp"
#include "core/eos.hpp"

#include <cmath>
#include <algorithm>

namespace hrsc {

// --- Internal helpers (Toro Ch. 4) ---

// Pressure function f_K for one side (K = L or R)
template <typename Real>
HD_FUNC Real riemann_fK(Real p, Real rhoK, Real pK, Real aK, Real gamma) {
    if (p > pK) {
        // Shock wave
        Real AK = Real(2) / ((gamma + Real(1)) * rhoK);
        Real BK = pK * (gamma - Real(1)) / (gamma + Real(1));
        return (p - pK) * std::sqrt(AK / (p + BK));
    } else {
        // Rarefaction wave
        Real gm1 = gamma - Real(1);
        Real exp = gm1 / (Real(2) * gamma);
        return (Real(2) * aK / gm1) * (std::pow(p / pK, exp) - Real(1));
    }
}

// Derivative df_K/dp for one side
template <typename Real>
HD_FUNC Real riemann_fK_deriv(Real p, Real rhoK, Real pK, Real aK, Real gamma) {
    if (p > pK) {
        // Shock wave
        Real AK = Real(2) / ((gamma + Real(1)) * rhoK);
        Real BK = pK * (gamma - Real(1)) / (gamma + Real(1));
        Real sqrtAB = std::sqrt(AK / (p + BK));
        return sqrtAB * (Real(1) - (p - pK) / (Real(2) * (p + BK)));
    } else {
        // Rarefaction wave
        Real exp = -(gamma + Real(1)) / (Real(2) * gamma);
        return (Real(1) / (rhoK * aK)) * std::pow(p / pK, exp);
    }
}

// Pressure iteration: Newton-Raphson for p_star, then compute u_star
template <typename Real>
HD_FUNC void exact_riemann_solve(
    Real gamma,
    Real rhoL, Real uL, Real pL,
    Real rhoR, Real uR, Real pR,
    Real& p_star, Real& u_star)
{
    Real aL = sound_speed(rhoL, pL, gamma);
    Real aR = sound_speed(rhoR, pR, gamma);
    Real gm1 = gamma - Real(1);

    // Vacuum check: if velocity difference exceeds critical value,
    // no star state exists
    if (Real(2) * aL / gm1 + Real(2) * aR / gm1 <= uR - uL) {
        p_star = Real(0);
        u_star = Real(0.5) * (uL + uR);
        return;
    }

    // Initial guess: PVRS (two-rarefaction approximation, Toro eq. 4.46)
    Real p0 = std::max(
        Real(0.5) * (pL + pR) - Real(0.125) * (uR - uL) * (rhoL + rhoR) * (aL + aR),
        Real(1e-14));

    // Newton-Raphson iteration
    Real p_scale = Real(0.5) * (pL + pR);
    Real tol = std::max(Real(1e-8) * p_scale, Real(1e-15));
    Real p_old = p0;

    for (int iter = 0; iter < 50; ++iter) {
        Real fL = riemann_fK(p_old, rhoL, pL, aL, gamma);
        Real fR = riemann_fK(p_old, rhoR, pR, aR, gamma);
        Real f  = fL + fR + (uR - uL);

        if (std::abs(f) < tol) break;

        Real dfL = riemann_fK_deriv(p_old, rhoL, pL, aL, gamma);
        Real dfR = riemann_fK_deriv(p_old, rhoR, pR, aR, gamma);
        Real df  = dfL + dfR;

        Real p_new = p_old - f / df;
        p_new = std::max(p_new, Real(1e-14));  // positivity clamp
        p_old = p_new;
    }

    p_star = p_old;

    // Contact velocity (Toro eq. 4.9)
    Real fL = riemann_fK(p_star, rhoL, pL, aL, gamma);
    Real fR = riemann_fK(p_star, rhoR, pR, aR, gamma);
    u_star = Real(0.5) * (uL + uR) + Real(0.5) * (fR - fL);
}

} // namespace hrsc
