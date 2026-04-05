#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/eos.hpp"

namespace hrsc {

// Physical flux F(U) in x-direction for 2D Euler equations.
// cons = {rho, rho*u, rho*v, E}
// F    = {rho*u, rho*u^2 + p, rho*u*v, u*(E + p)}
template <typename Real>
HD_FUNC Vec<Real, 4> euler_flux_x(const Vec<Real, 4>& cons, Real gamma) {
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

} // namespace hrsc
