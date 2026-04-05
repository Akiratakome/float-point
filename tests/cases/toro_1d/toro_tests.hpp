#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"

namespace hrsc {

// Sod shock tube IC (Toro Test 1).
// Domain [0, 1], discontinuity at x = 0.5.
// Left:  rho=1.0,   u=0, v=0, p=1.0
// Right: rho=0.125, u=0, v=0, p=0.1
// grid.dx must be set before calling this function.
template <typename Real>
void setup_sod(GridView<Real, 4> grid, Real gamma) {
    Real xmin = Real(0);

    for (int i = 0; i < grid.nx; ++i) {
        Real x = xmin + (Real(i) + Real(0.5)) * grid.dx;

        Vec<Real, 4> prim;
        if (x < Real(0.5)) {
            prim = {Real(1.0), Real(0), Real(0), Real(1.0)};
        } else {
            prim = {Real(0.125), Real(0), Real(0), Real(0.1)};
        }

        Vec<Real, 4> cons = prim_to_cons(prim, gamma);
        for (int v = 0; v < 4; ++v) {
            grid(i, 0, v) = cons[v];
        }
    }
}

} // namespace hrsc
