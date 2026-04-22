#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"

#include <cassert>
#include <cmath>
#include <limits>

namespace hrsc {

// Conserved variable indexing for Euler: {rho, rho*u, rho*v, E}
enum EulerVar : int { RHO = 0, RHOU = 1, RHOV = 2, EN = 3 };

// Primitive variable indexing: {rho, u, v, p}
enum PrimVar : int { PRHO = 0, VX = 1, VY = 2, PRES = 3 };

// Number of conserved variables for 2D Euler ({rho, rho*u, rho*v, E}).
// Use in place of the literal `4` across Euler code so the value cannot
// drift out of sync with the EulerVar enum and to clearly distinguish it
// from MHD (which will define its own NVars = 9).
static constexpr int EulerNVars = 4;

// Pressure from conserved variables
template <typename Real>
HD_FUNC Real pressure(const Vec<Real, EulerNVars>& cons, Real gamma) {
    Real rho   = cons[RHO];
    Real rho_u = cons[RHOU];
    Real rho_v = cons[RHOV];
    Real E     = cons[EN];

    assert(rho > std::numeric_limits<Real>::min());

    Real ke = Real(0.5) * (rho_u * rho_u + rho_v * rho_v) / rho;
    return (gamma - Real(1)) * (E - ke);
}

// Sound speed: a = sqrt(gamma * p / rho)
template <typename Real>
HD_FUNC Real sound_speed(Real rho, Real p, Real gamma) {
    assert(rho > std::numeric_limits<Real>::min());
    return std::sqrt(gamma * p / rho);
}

// Conserved -> Primitive: {rho, u, v, p}
template <typename Real>
HD_FUNC Vec<Real, EulerNVars> cons_to_prim(const Vec<Real, EulerNVars>& cons, Real gamma) {
    Real rho = cons[RHO];
    assert(rho > std::numeric_limits<Real>::min());

    Real u = cons[RHOU] / rho;
    Real v = cons[RHOV] / rho;
    Real p = pressure(cons, gamma);

    return {rho, u, v, p};
}

// Primitive -> Conserved: {rho, rho*u, rho*v, E}
// Primitive ordering: {rho, u, v, p}
template <typename Real>
HD_FUNC Vec<Real, EulerNVars> prim_to_cons(const Vec<Real, EulerNVars>& prim, Real gamma) {
    Real rho = prim[PRHO];
    Real u   = prim[VX];
    Real v   = prim[VY];
    Real p   = prim[PRES];

    Real E = p / (gamma - Real(1)) + Real(0.5) * rho * (u * u + v * v);

    return {rho, rho * u, rho * v, E};
}

} // namespace hrsc
