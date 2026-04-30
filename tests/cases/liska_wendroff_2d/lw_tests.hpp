#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"

namespace hrsc {

// ──────────────────────────────────────────────────────────────────────────────
// Liska & Wendroff 2003 (SIAM J. Sci. Comput. 25:995–1017), 2D Riemann configs.
// Domain [0,1]^2, split into four quadrants about (x_split, y_split) = (0.5, 0.5).
// The four constant initial primitive states interact through the cross at the
// center to produce a canonical pattern of shocks, contacts, and rarefactions.
// ──────────────────────────────────────────────────────────────────────────────

// Split location — shared by all LW configurations.
template <typename Real>
inline constexpr Real LW_XSPLIT = Real(0.5);

template <typename Real>
inline constexpr Real LW_YSPLIT = Real(0.5);

// ─── Config 3 (Table 4.3 of Liska & Wendroff 2003) ────────────────────────────
// Four interacting shocks. t_end = 0.3, gamma = 1.4.
// Quadrant layout (as viewed in the (x, y) plane):
//
//      ┌─────────────┬─────────────┐
//      │   Q2        │   Q1        │
//      │ x<0.5, y>0.5│ x>0.5, y>0.5│
//      ├─────────────┼─────────────┤
//      │   Q3        │   Q4        │
//      │ x<0.5, y<0.5│ x>0.5, y<0.5│
//      └─────────────┴─────────────┘
//
// Primitive state is (rho, vx, vy, p) per quadrant.

// Q1: x > 0.5, y > 0.5
template <typename Real> inline constexpr Real LW3_Q1_RHO = Real(1.5);
template <typename Real> inline constexpr Real LW3_Q1_VX  = Real(0.0);
template <typename Real> inline constexpr Real LW3_Q1_VY  = Real(0.0);
template <typename Real> inline constexpr Real LW3_Q1_P   = Real(1.5);

// Q2: x < 0.5, y > 0.5
template <typename Real> inline constexpr Real LW3_Q2_RHO = Real(0.5323);
template <typename Real> inline constexpr Real LW3_Q2_VX  = Real(1.206);
template <typename Real> inline constexpr Real LW3_Q2_VY  = Real(0.0);
template <typename Real> inline constexpr Real LW3_Q2_P   = Real(0.3);

// Q3: x < 0.5, y < 0.5
template <typename Real> inline constexpr Real LW3_Q3_RHO = Real(0.138);
template <typename Real> inline constexpr Real LW3_Q3_VX  = Real(1.206);
template <typename Real> inline constexpr Real LW3_Q3_VY  = Real(1.206);
template <typename Real> inline constexpr Real LW3_Q3_P   = Real(0.029);

// Q4: x > 0.5, y < 0.5
template <typename Real> inline constexpr Real LW3_Q4_RHO = Real(0.5323);
template <typename Real> inline constexpr Real LW3_Q4_VX  = Real(0.0);
template <typename Real> inline constexpr Real LW3_Q4_VY  = Real(1.206);
template <typename Real> inline constexpr Real LW3_Q4_P   = Real(0.3);

// ─── Config 6 (Table 4.3 of Liska & Wendroff 2003) ────────────────────────────
// Four contact discontinuities, no shocks. t_end = 0.3, gamma = 1.4.

// Q1: x > 0.5, y > 0.5
template <typename Real> inline constexpr Real LW6_Q1_RHO = Real(1.0);
template <typename Real> inline constexpr Real LW6_Q1_VX  = Real(0.75);
template <typename Real> inline constexpr Real LW6_Q1_VY  = Real(-0.5);
template <typename Real> inline constexpr Real LW6_Q1_P   = Real(1.0);

// Q2: x < 0.5, y > 0.5
template <typename Real> inline constexpr Real LW6_Q2_RHO = Real(2.0);
template <typename Real> inline constexpr Real LW6_Q2_VX  = Real(0.75);
template <typename Real> inline constexpr Real LW6_Q2_VY  = Real(0.5);
template <typename Real> inline constexpr Real LW6_Q2_P   = Real(1.0);

// Q3: x < 0.5, y < 0.5
template <typename Real> inline constexpr Real LW6_Q3_RHO = Real(1.0);
template <typename Real> inline constexpr Real LW6_Q3_VX  = Real(-0.75);
template <typename Real> inline constexpr Real LW6_Q3_VY  = Real(0.5);
template <typename Real> inline constexpr Real LW6_Q3_P   = Real(1.0);

// Q4: x > 0.5, y < 0.5
template <typename Real> inline constexpr Real LW6_Q4_RHO = Real(3.0);
template <typename Real> inline constexpr Real LW6_Q4_VX  = Real(-0.75);
template <typename Real> inline constexpr Real LW6_Q4_VY  = Real(-0.5);
template <typename Real> inline constexpr Real LW6_Q4_P   = Real(1.0);

// Config 3 setup. grid.dx, grid.dy must be set before calling; domain assumed
// to start at (xmin, ymin) = (0, 0) so that the cell-centre coordinate is
// (x, y) = ((i + 0.5) * dx, (j + 0.5) * dy) — matching the pattern in
// tests/cases/toro_1d/toro_tests.hpp::setup_riemann.
template <typename Real>
void setup_liska_wendroff_config3(GridView<Real, EulerNVars> gv, Real gamma) {
    const Real xs = LW_XSPLIT<Real>;
    const Real ys = LW_YSPLIT<Real>;

    for (int j = 0; j < gv.ny; ++j) {
        Real y = (Real(j) + Real(0.5)) * gv.dy;
        for (int i = 0; i < gv.nx; ++i) {
            Real x = (Real(i) + Real(0.5)) * gv.dx;

            Vec<Real, EulerNVars> prim;
            if (x > xs && y > ys) {
                // Q1
                prim = {LW3_Q1_RHO<Real>, LW3_Q1_VX<Real>, LW3_Q1_VY<Real>, LW3_Q1_P<Real>};
            } else if (x <= xs && y > ys) {
                // Q2
                prim = {LW3_Q2_RHO<Real>, LW3_Q2_VX<Real>, LW3_Q2_VY<Real>, LW3_Q2_P<Real>};
            } else if (x <= xs && y <= ys) {
                // Q3
                prim = {LW3_Q3_RHO<Real>, LW3_Q3_VX<Real>, LW3_Q3_VY<Real>, LW3_Q3_P<Real>};
            } else {
                // Q4: x > xs, y <= ys
                prim = {LW3_Q4_RHO<Real>, LW3_Q4_VX<Real>, LW3_Q4_VY<Real>, LW3_Q4_P<Real>};
            }

            Vec<Real, EulerNVars> cons = prim_to_cons(prim, gamma);
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) = cons[v];
            }
        }
    }
}

template <typename Real>
void setup_liska_wendroff_config6(GridView<Real, EulerNVars> gv, Real gamma) {
    const Real xs = LW_XSPLIT<Real>;
    const Real ys = LW_YSPLIT<Real>;

    for (int j = 0; j < gv.ny; ++j) {
        Real y = (Real(j) + Real(0.5)) * gv.dy;
        for (int i = 0; i < gv.nx; ++i) {
            Real x = (Real(i) + Real(0.5)) * gv.dx;

            Vec<Real, EulerNVars> prim;
            if (x > xs && y > ys) {
                // Q1
                prim = {LW6_Q1_RHO<Real>, LW6_Q1_VX<Real>, LW6_Q1_VY<Real>, LW6_Q1_P<Real>};
            } else if (x <= xs && y > ys) {
                // Q2
                prim = {LW6_Q2_RHO<Real>, LW6_Q2_VX<Real>, LW6_Q2_VY<Real>, LW6_Q2_P<Real>};
            } else if (x <= xs && y <= ys) {
                // Q3
                prim = {LW6_Q3_RHO<Real>, LW6_Q3_VX<Real>, LW6_Q3_VY<Real>, LW6_Q3_P<Real>};
            } else {
                // Q4: x > xs, y <= ys
                prim = {LW6_Q4_RHO<Real>, LW6_Q4_VX<Real>, LW6_Q4_VY<Real>, LW6_Q4_P<Real>};
            }

            Vec<Real, EulerNVars> cons = prim_to_cons(prim, gamma);
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) = cons[v];
            }
        }
    }
}

} // namespace hrsc
