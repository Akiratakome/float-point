#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"

#include <algorithm>
#include <cmath>

namespace hrsc {

// Minbee (minmod) slope limiter: returns the value with smaller magnitude
// if both have the same sign, otherwise zero. (Toro Ch. 13)
template <typename Real>
HD_FUNC Real minbee(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return (std::abs(a) < std::abs(b)) ? a : b;
}

// Van Leer limiter: smooth, moderate dissipation (Toro Ch. 13)
template <typename Real>
HD_FUNC Real vanleer(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return Real(2) * a * b / (a + b);
}

// Superbee limiter: least dissipative symmetric TVD (Toro Ch. 13)
template <typename Real>
HD_FUNC Real superbee(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    Real s = (a > Real(0)) ? Real(1) : Real(-1);
    Real abs_a = std::abs(a);
    Real abs_b = std::abs(b);
    return s * std::max(std::min(abs_a, Real(2) * abs_b),
                        std::min(Real(2) * abs_a, abs_b));
}

// Van Albada limiter: C1-smooth (Toro Ch. 13)
template <typename Real>
HD_FUNC Real vanalbada(Real a, Real b) {
    if (a * b <= Real(0)) return Real(0);
    return a * b * (a + b) / (a * a + b * b);
}

struct MinbeeLimiter {
    template <typename Real>
    HD_FUNC Real operator()(Real a, Real b) const { return minbee(a, b); }
};

struct VanLeerLimiter {
    template <typename Real>
    HD_FUNC Real operator()(Real a, Real b) const { return vanleer(a, b); }
};

struct SuperbeeLimiter {
    template <typename Real>
    HD_FUNC Real operator()(Real a, Real b) const { return superbee(a, b); }
};

struct VanAlbadaLimiter {
    template <typename Real>
    HD_FUNC Real operator()(Real a, Real b) const { return vanalbada(a, b); }
};

// MUSCL piecewise-linear reconstruction for cell i in x-direction.
// Returns boundary-extrapolated values at left face (i-1/2) and right face (i+1/2).
// Uses minbee limiter, component-wise on conserved variables.
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
        Real slope    = minbee(backward, forward);

        q_left[v]  = u_i - Real(0.5) * slope;
        q_right[v] = u_i + Real(0.5) * slope;
    }
}

} // namespace hrsc
