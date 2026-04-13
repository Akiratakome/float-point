#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"

namespace hrsc {

// Generic Riemann problem IC: two constant states separated at x = x0.
// grid.dx must be set before calling.
template <typename Real>
void setup_riemann(GridView<Real, 4> grid, Real gamma, Real x0,
                   Real rhoL, Real uL, Real pL,
                   Real rhoR, Real uR, Real pR) {
    for (int i = 0; i < grid.nx; ++i) {
        Real x = (Real(i) + Real(0.5)) * grid.dx;
        Vec<Real, 4> prim;
        if (x < x0) {
            prim = {rhoL, uL, Real(0), pL};
        } else {
            prim = {rhoR, uR, Real(0), pR};
        }
        Vec<Real, 4> cons = prim_to_cons(prim, gamma);
        for (int v = 0; v < 4; ++v) {
            grid(i, 0, v) = cons[v];
        }
    }
}

// Toro Test 1: Sod shock tube
// Domain [0,1], x0=0.5, t_end=0.25
template <typename Real>
void setup_sod(GridView<Real, 4> grid, Real gamma) {
    setup_riemann(grid, gamma, Real(0.5),
                  Real(1.0),   Real(0), Real(1.0),
                  Real(0.125), Real(0), Real(0.1));
}

// Toro Test 2: 123 problem (two symmetric rarefactions, near-vacuum)
// Domain [0,1], x0=0.5, t_end=0.15
template <typename Real>
void setup_toro2(GridView<Real, 4> grid, Real gamma) {
    setup_riemann(grid, gamma, Real(0.5),
                  Real(1.0), Real(-2.0), Real(0.4),
                  Real(1.0), Real( 2.0), Real(0.4));
}

// Toro Test 3: Left half of Woodward-Colella blast wave
// Domain [0,1], x0=0.5, t_end=0.012
template <typename Real>
void setup_toro3(GridView<Real, 4> grid, Real gamma) {
    setup_riemann(grid, gamma, Real(0.5),
                  Real(1.0), Real(0), Real(1000.0),
                  Real(1.0), Real(0), Real(0.01));
}

// Toro Test 4: Lax problem (contact + shocks)
// Domain [0,1], x0=0.5, t_end=0.035
template <typename Real>
void setup_toro4(GridView<Real, 4> grid, Real gamma) {
    setup_riemann(grid, gamma, Real(0.5),
                  Real(0.445), Real(0.698), Real(3.528),
                  Real(0.5),   Real(0.0),   Real(0.571));
}

// Toro Test 5: Slowly moving contact discontinuity
// Domain [0,1], x0=0.5, t_end=0.035
template <typename Real>
void setup_toro5(GridView<Real, 4> grid, Real gamma) {
    setup_riemann(grid, gamma, Real(0.5),
                  Real(5.99924), Real(19.5975),  Real(460.894),
                  Real(5.99242), Real(-6.19633), Real(46.0950));
}

// Stationary contact discontinuity: S_M = 0 exactly
// Domain [0,1], x0=0.5, t_end=0.5
template <typename Real>
void setup_stationary_contact(GridView<Real, 4> grid, Real gamma) {
    setup_riemann(grid, gamma, Real(0.5),
                  Real(1.0), Real(0), Real(1.0),    // left: rho=1, u=0, p=1
                  Real(0.5), Real(0), Real(1.0));   // right: rho=0.5, u=0, p=1
}

} // namespace hrsc
