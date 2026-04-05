#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"

#include <algorithm>
#include <cmath>

namespace hrsc {

// Minmod slope limiter: returns the value with smaller magnitude
// if both have the same sign, otherwise zero.
template <typename Real>
HD_FUNC Real minmod(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return (std::abs(a) < std::abs(b)) ? a : b;
}

// MUSCL piecewise-linear reconstruction for cell i in x-direction.
// Returns boundary-extrapolated values at left face (i-1/2) and right face (i+1/2).
// Uses minmod limiter, component-wise on conserved variables.
// Stencil: cells i-1, i, i+1 (within NgHost=2 ghost layers).
template <typename Real, typename Ptr>
HD_FUNC void muscl_reconstruct_x(
    GridViewBase<Real, 4, Ptr> grid, int i, int j,
    Vec<Real, 4>& q_left, Vec<Real, 4>& q_right)
{
    for (int v = 0; v < 4; ++v) {
        Real u_im1 = grid(i - 1, j, v);
        Real u_i   = grid(i,     j, v);
        Real u_ip1 = grid(i + 1, j, v);

        Real backward = u_i - u_im1;
        Real forward  = u_ip1 - u_i;
        Real slope    = minmod(backward, forward);

        q_left[v]  = u_i - Real(0.5) * slope;
        q_right[v] = u_i + Real(0.5) * slope;
    }
}

} // namespace hrsc
