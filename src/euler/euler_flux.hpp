#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/eos.hpp"

namespace hrsc {

// Physical flux F(U) in x-direction for 2D Euler equations.
// cons = {rho, rho*u, rho*v, E}
// F    = {rho*u, rho*u^2 + p, rho*u*v, u*(E + p)}
template <typename Real>
HD_FUNC Vec<Real, EulerNVars> euler_flux_x(const Vec<Real, EulerNVars>& cons, Real gamma) {
    Real rho   = cons[RHO];
    Real rho_u = cons[RHOU];
    Real rho_v = cons[RHOV];
    Real E     = cons[EN];
    Real u     = rho_u / rho;
    Real p     = pressure(cons, gamma);

    return {rho_u,
            rho_u * u + p,
            rho_v * u,
            u * (E + p)};
}

// Physical flux G(U) in y-direction for 2D Euler equations.
// cons = {rho, rho*u, rho*v, E}
// G    = {rho*v, rho*u*v, rho*v^2 + p, v*(E + p)}
template <typename Real>
HD_FUNC Vec<Real, EulerNVars> euler_flux_y(const Vec<Real, EulerNVars>& cons, Real gamma) {
    Real rho   = cons[RHO];
    Real rho_u = cons[RHOU];
    Real rho_v = cons[RHOV];
    Real E     = cons[EN];
    Real v     = rho_v / rho;
    Real p     = pressure(cons, gamma);

    return {rho_v,
            rho_u * v,
            rho_v * v + p,
            v * (E + p)};
}

// Swap momentum components for y-interface HLLC rotation.
// HLLC treats index 1 as normal velocity. For y-interfaces,
// swap RHOU <-> RHOV so v becomes the normal velocity.
template <typename Real>
HD_FUNC Vec<Real, EulerNVars> swap_momentum(const Vec<Real, EulerNVars>& q) {
    return {q[RHO], q[RHOV], q[RHOU], q[EN]};
}

} // namespace hrsc
