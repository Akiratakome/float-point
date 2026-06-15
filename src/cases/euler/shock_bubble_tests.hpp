// tests/cases/shock_bubble/shock_bubble_tests.hpp
//
// Single-fluid shock-density-bubble test (half-symmetric setup).
//
// Domain [0, 1] x [0, 0.25]. y=0 is the symmetry plane through the bubble
// centre; only the upper half of a circular bubble is in the computational
// domain. Reflective BC on both y boundaries (y=0 = mirror, y=0.25 = upper
// channel wall, matches Quirk-Karni 1996 half-symmetric channel layout).
//
// All gas is air, gamma=1.4. The "helium bubble" is represented purely as a
// density contrast (rho_bubble = 0.138, no species equation, no variable
// gamma). This is a deliberate single-fluid simplification.
//
// Initial state:
//   - Pre-shock air (right of x=0.05):  rho=1.0, u=0.0, p=1.0
//   - Post-shock air (left of x=0.05):  via Rankine-Hugoniot for Mach 1.22
//   - Bubble (circle centre (0.25, 0), radius 0.1, in pre-shock region):
//     rho=0.138, u=0.0, p=1.0
//
// Boundary: cfg sets bc_x = outflow, bc_y = reflective.

#pragma once

#include "core/eos.hpp"
#include "core/grid.hpp"
#include "core/types.hpp"
#include "core/vec.hpp"

#include <cmath>

namespace hrsc {

template <typename Real> inline constexpr Real SB_PRE_RHO = Real(1.0);
template <typename Real> inline constexpr Real SB_PRE_U = Real(0.0);
template <typename Real> inline constexpr Real SB_PRE_P = Real(1.0);

template <typename Real> inline constexpr Real SB_BUBBLE_RHO = Real(0.138);
template <typename Real> inline constexpr Real SB_BUBBLE_CX = Real(0.25);
template <typename Real> inline constexpr Real SB_BUBBLE_CY = Real(0.0);
template <typename Real> inline constexpr Real SB_BUBBLE_R = Real(0.1);

template <typename Real> inline constexpr Real SB_SHOCK_X = Real(0.05);
template <typename Real> inline constexpr Real SB_MACH = Real(1.22);

template <typename Real>
inline void shock_bubble_post_shock(Real gamma,
                                    Real rho1,
                                    Real p1,
                                    Real Ms,
                                    Real& rho2,
                                    Real& u2_lab,
                                    Real& p2) {
    Real Ms2 = Ms * Ms;
    Real gp1 = gamma + Real(1);
    Real gm1 = gamma - Real(1);

    Real rho_ratio = (gp1 * Ms2) / (gm1 * Ms2 + Real(2));
    rho2 = rho1 * rho_ratio;

    Real p_ratio = (Real(2) * gamma * Ms2 - gm1) / gp1;
    p2 = p1 * p_ratio;

    Real c1 = std::sqrt(gamma * p1 / rho1);
    Real Vs = Ms * c1;
    u2_lab = (Real(1) - Real(1) / rho_ratio) * Vs;
}

template <typename Real>
void setup_shock_bubble(GridView<Real, EulerNVars> gv, Real gamma) {
    Real rho2, u2, p2;
    shock_bubble_post_shock<Real>(gamma,
                                  SB_PRE_RHO<Real>,
                                  SB_PRE_P<Real>,
                                  SB_MACH<Real>,
                                  rho2,
                                  u2,
                                  p2);

    const Real shock_x = SB_SHOCK_X<Real>;
    const Real cx = SB_BUBBLE_CX<Real>;
    const Real cy = SB_BUBBLE_CY<Real>;
    const Real r2 = SB_BUBBLE_R<Real> * SB_BUBBLE_R<Real>;
    const Real rho_bub = SB_BUBBLE_RHO<Real>;

    for (int j = 0; j < gv.ny; ++j) {
        Real y = (Real(j) + Real(0.5)) * gv.dy;
        for (int i = 0; i < gv.nx; ++i) {
            Real x = (Real(i) + Real(0.5)) * gv.dx;
            Real dx_b = x - cx;
            Real dy_b = y - cy;
            bool inside_bubble = (dx_b * dx_b + dy_b * dy_b <= r2);

            Vec<Real, EulerNVars> prim;
            if (x < shock_x) {
                prim = {rho2, u2, Real(0), p2};
            } else if (inside_bubble) {
                prim = {rho_bub, SB_PRE_U<Real>, Real(0), SB_PRE_P<Real>};
            } else {
                prim = {SB_PRE_RHO<Real>, SB_PRE_U<Real>, Real(0), SB_PRE_P<Real>};
            }

            Vec<Real, EulerNVars> cons = prim_to_cons(prim, gamma);
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) = cons[v];
            }
        }
    }
}

} // namespace hrsc
