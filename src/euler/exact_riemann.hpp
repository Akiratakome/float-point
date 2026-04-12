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

// Sample the exact Riemann solution at a given x/t value
template <typename Real>
HD_FUNC void exact_riemann_sample(
    Real gamma, Real x_over_t,
    Real rhoL, Real uL, Real pL,
    Real rhoR, Real uR, Real pR,
    Real& rho, Real& u, Real& p)
{
    Real aL = sound_speed(rhoL, pL, gamma);
    Real aR = sound_speed(rhoR, pR, gamma);
    Real gm1 = gamma - Real(1);
    Real gp1 = gamma + Real(1);

    // Get star-state pressure and velocity
    Real p_star, u_star;
    exact_riemann_solve(gamma, rhoL, uL, pL, rhoR, uR, pR, p_star, u_star);

    // Vacuum state
    if (p_star < Real(1e-14)) {
        rho = Real(0);
        u   = Real(0.5) * (uL + uR);
        p   = Real(0);
        return;
    }

    if (x_over_t <= u_star) {
        // Left of contact — left wave
        if (p_star > pL) {
            // Left shock
            Real SL = uL - aL * std::sqrt((gp1 * p_star / pL + gm1) / (Real(2) * gamma));
            if (x_over_t <= SL) {
                // Undisturbed left
                rho = rhoL; u = uL; p = pL;
            } else {
                // Left star state
                Real rho_starL = rhoL * ((p_star / pL + gm1 / gp1) /
                                         (gm1 / gp1 * p_star / pL + Real(1)));
                rho = rho_starL; u = u_star; p = p_star;
            }
        } else {
            // Left rarefaction
            Real aL_star = aL * std::pow(p_star / pL, gm1 / (Real(2) * gamma));
            Real SHL = uL - aL;          // head speed
            Real STL = u_star - aL_star;  // tail speed

            if (x_over_t <= SHL) {
                // Undisturbed left
                rho = rhoL; u = uL; p = pL;
            } else if (x_over_t <= STL) {
                // Inside left rarefaction fan
                Real ratio = (Real(2) / gp1) + (gm1 / (gp1 * aL)) * (uL - x_over_t);
                rho = rhoL * std::pow(ratio, Real(2) / gm1);
                u   = (Real(2) / gp1) * (aL + gm1 * Real(0.5) * uL + x_over_t);
                p   = pL * std::pow(ratio, Real(2) * gamma / gm1);
            } else {
                // Left star state (behind rarefaction tail)
                Real rho_starL = rhoL * std::pow(p_star / pL, Real(1) / gamma);
                rho = rho_starL; u = u_star; p = p_star;
            }
        }
    } else {
        // Right of contact — right wave
        if (p_star > pR) {
            // Right shock
            Real SR = uR + aR * std::sqrt((gp1 * p_star / pR + gm1) / (Real(2) * gamma));
            if (x_over_t >= SR) {
                // Undisturbed right
                rho = rhoR; u = uR; p = pR;
            } else {
                // Right star state
                Real rho_starR = rhoR * ((p_star / pR + gm1 / gp1) /
                                         (gm1 / gp1 * p_star / pR + Real(1)));
                rho = rho_starR; u = u_star; p = p_star;
            }
        } else {
            // Right rarefaction
            Real aR_star = aR * std::pow(p_star / pR, gm1 / (Real(2) * gamma));
            Real SHR = uR + aR;          // head speed
            Real STR = u_star + aR_star;  // tail speed

            if (x_over_t >= SHR) {
                // Undisturbed right
                rho = rhoR; u = uR; p = pR;
            } else if (x_over_t >= STR) {
                // Inside right rarefaction fan
                Real ratio = (Real(2) / gp1) - (gm1 / (gp1 * aR)) * (uR - x_over_t);
                rho = rhoR * std::pow(ratio, Real(2) / gm1);
                u   = (Real(2) / gp1) * (-aR + gm1 * Real(0.5) * uR + x_over_t);
                p   = pR * std::pow(ratio, Real(2) * gamma / gm1);
            } else {
                // Right star state
                Real rho_starR = rhoR * std::pow(p_star / pR, Real(1) / gamma);
                rho = rho_starR; u = u_star; p = p_star;
            }
        }
    }
}

} // namespace hrsc
