#include "catch.hpp"
#include "mhd/mhd_flux.hpp"

using namespace hrsc;

TEST_CASE("mhd_swap_xy swaps MX<->MY and BX<->BY and is self-inverse", "[mhd][swap]") {
    Vec<double, MhdNVars> U;
    for (int k = 0; k < MhdNVars; ++k) U[k] = double(k + 1);

    Vec<double, MhdNVars> S = mhd_swap_xy(U);

    REQUIRE(S[MhdIdx::RHO] == Approx(U[MhdIdx::RHO]));
    REQUIRE(S[MhdIdx::MX] == Approx(U[MhdIdx::MY]));
    REQUIRE(S[MhdIdx::MY] == Approx(U[MhdIdx::MX]));
    REQUIRE(S[MhdIdx::MZ] == Approx(U[MhdIdx::MZ]));
    REQUIRE(S[MhdIdx::BX] == Approx(U[MhdIdx::BY]));
    REQUIRE(S[MhdIdx::BY] == Approx(U[MhdIdx::BX]));
    REQUIRE(S[MhdIdx::BZ] == Approx(U[MhdIdx::BZ]));
    REQUIRE(S[MhdIdx::E] == Approx(U[MhdIdx::E]));
    REQUIRE(S[MhdIdx::PSI] == Approx(U[MhdIdx::PSI]));

    Vec<double, MhdNVars> back = mhd_swap_xy(S);
    for (int k = 0; k < MhdNVars; ++k) REQUIRE(back[k] == Approx(U[k]));
}

TEST_CASE("rotated x-flux equals the y-physical-flux", "[mhd][swap]") {
    const double gamma = 2.0;
    const double ch = 3.0;
    MhdPrim<double> w{};
    w.rho = 1.0; w.vx = 0.3; w.vy = -0.4; w.vz = 0.1;
    w.Bx = 0.75; w.By = 0.9; w.Bz = 0.2; w.p = 1.0; w.psi = -0.2;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);

    Vec<double, MhdNVars> Fy = mhd_swap_xy(mhd_flux_x(mhd_swap_xy(U), gamma, ch));

    REQUIRE(Fy[MhdIdx::RHO] == Approx(w.rho * w.vy));

    const double B2 = w.Bx*w.Bx + w.By*w.By + w.Bz*w.Bz;
    const double ptot = w.p + 0.5*B2;
    REQUIRE(Fy[MhdIdx::MY] == Approx(w.rho*w.vy*w.vy + ptot - w.By*w.By));
}
