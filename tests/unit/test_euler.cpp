#include "catch.hpp"
#include "euler/euler_flux.hpp"

using namespace hrsc;

// --- euler_flux_x tests ---

TEST_CASE("euler_flux_x: stationary gas returns {0, p, 0, 0}", "[flux]") {
    // rho=1, u=0, v=0, p=1 → cons = {1, 0, 0, 2.5}
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5};
    Vec<double, 4> f = euler_flux_x(cons, 1.4);

    REQUIRE(f[0] == Approx(0.0).margin(1e-15));  // rho*u = 0
    REQUIRE(f[1] == Approx(1.0).epsilon(1e-12));  // rho*u^2 + p = p = 1
    REQUIRE(f[2] == Approx(0.0).margin(1e-15));  // rho*u*v = 0
    REQUIRE(f[3] == Approx(0.0).margin(1e-15));  // u*(E+p) = 0
}

TEST_CASE("euler_flux_x: uniform rightward flow", "[flux]") {
    // rho=2, u=3, v=1, p=4, gamma=1.4
    // cons: rho=2, rho*u=6, rho*v=2, E = p/(gamma-1) + 0.5*rho*(u^2+v^2)
    //     = 4/0.4 + 0.5*2*(9+1) = 10 + 10 = 20
    Vec<double, 4> cons = {2.0, 6.0, 2.0, 20.0};
    Vec<double, 4> f = euler_flux_x(cons, 1.4);

    // F = {rho*u, rho*u^2+p, rho*u*v, u*(E+p)}
    //   = {6, 2*9+4, 6*1, 3*(20+4)} = {6, 22, 6, 72}
    REQUIRE(f[0] == Approx(6.0).epsilon(1e-12));
    REQUIRE(f[1] == Approx(22.0).epsilon(1e-12));
    REQUIRE(f[2] == Approx(6.0).epsilon(1e-12));
    REQUIRE(f[3] == Approx(72.0).epsilon(1e-12));
}
