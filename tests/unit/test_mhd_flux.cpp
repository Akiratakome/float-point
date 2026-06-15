#include "catch.hpp"
#include "mhd/mhd_flux.hpp"

using namespace hrsc;

TEST_CASE("MHD x-flux matches hand-computed values", "[mhd][flux]") {
    const double gamma = 2.0;
    MhdPrim<double> w{};
    w.rho = 1.25; w.vx = 2.0; w.vy = -0.5; w.vz = 0.25;
    w.Bx = 0.75; w.By = 1.0; w.Bz = -0.5; w.p = 1.2; w.psi = -0.4;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);

    const double ch = 3.0;
    Vec<double, MhdNVars> F = mhd_flux_x(U, gamma, ch);

    // B^2 = 0.75^2 + 1^2 + (-0.5)^2 = 1.8125, ptot = 1.2 + 0.5*B^2 = 2.10625
    REQUIRE(F[MhdIdx::RHO] == Approx(2.5));       // mx
    REQUIRE(F[MhdIdx::MX]  == Approx(6.54375));   // mx*vx + ptot - Bx^2
    REQUIRE(F[MhdIdx::MY]  == Approx(-2.0));      // mx*vy - Bx*By
    REQUIRE(F[MhdIdx::MZ]  == Approx(1.0));       // mx*vz - Bx*Bz
    REQUIRE(F[MhdIdx::BX]  == Approx(-0.4));      // psi
    REQUIRE(F[MhdIdx::BY]  == Approx(2.375));     // By*vx - Bx*vy
    REQUIRE(F[MhdIdx::BZ]  == Approx(-1.1875));   // Bz*vx - Bx*vz
    REQUIRE(F[MhdIdx::E]   == Approx(13.159375)); // (E + ptot)*vx - Bx*(v dot B)
    REQUIRE(F[MhdIdx::PSI] == Approx(6.75));      // ch^2 * Bx
}
