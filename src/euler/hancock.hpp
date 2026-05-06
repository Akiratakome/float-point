#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "euler/muscl.hpp"
#include "euler/euler_flux.hpp"

namespace hrsc {

// MUSCL-Hancock predictor for cell i in x-direction.
// 1. Calls muscl_reconstruct_x to get boundary-extrapolated (q_left, q_right)
// 2. Computes fluxes at both faces
// 3. Evolves both states by dt/2 using the flux difference
//
// q_left  = value at left face  (i - 1/2)
// q_right = value at right face (i + 1/2)
template <typename Real, typename Ptr, typename Limiter = MinbeeLimiter>
HD_FUNC void muscl_hancock_x(
    GridViewBase<Real, EulerNVars, Ptr> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, EulerNVars>& q_left, Vec<Real, EulerNVars>& q_right,
    Limiter lim = {})
{
    // Step 1: MUSCL reconstruction
    muscl_reconstruct_x(grid, i, j, q_left, q_right, lim);

    // Step 2: Compute fluxes at left and right faces
    Vec<Real, EulerNVars> fL = euler_flux_x(q_left,  gamma);
    Vec<Real, EulerNVars> fR = euler_flux_x(q_right, gamma);

    // Step 3: Half-step evolution
    // q += 0.5 * (dt/dx) * (F(q_left) - F(q_right))
    Real half_dtdx = Real(0.5) * dt / grid.dx;
    Vec<Real, EulerNVars> df = fL - fR;

    q_left  += df * half_dtdx;
    q_right += df * half_dtdx;
}

// MUSCL-Hancock predictor for cell (i,j) in y-direction.
// q_bottom = value at bottom face (j - 1/2)
// q_top    = value at top face    (j + 1/2)
template <typename Real, typename Ptr, typename Limiter = MinbeeLimiter>
HD_FUNC void muscl_hancock_y(
    GridViewBase<Real, EulerNVars, Ptr> grid, int i, int j,
    Real dt, Real gamma,
    Vec<Real, EulerNVars>& q_bottom, Vec<Real, EulerNVars>& q_top,
    Limiter lim = {})
{
    // Step 1: MUSCL reconstruction in y
    muscl_reconstruct_y(grid, i, j, q_bottom, q_top, lim);

    // Step 2: Compute y-fluxes at bottom and top faces
    Vec<Real, EulerNVars> gB = euler_flux_y(q_bottom, gamma);
    Vec<Real, EulerNVars> gT = euler_flux_y(q_top,    gamma);

    // Step 3: Half-step evolution using dy (NOT dx)
    Real half_dtdy = Real(0.5) * dt / grid.dy;
    Vec<Real, EulerNVars> dg = gB - gT;

    q_bottom += dg * half_dtdy;
    q_top    += dg * half_dtdy;
}

} // namespace hrsc
