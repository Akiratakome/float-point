#include "catch.hpp"
#include "mhd/hll.hpp"

#include <algorithm>

using namespace hrsc;

TEST_CASE("HLL with identical states returns the physical flux", "[mhd][hll]") {
    const double gamma = 2.0;
    MhdPrim<double> w{};
    w.rho = 1.0; w.vx = 0.5; w.Bx = 0.75; w.By = 1.0; w.p = 1.0;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);
    const double ch = 2.0;

    Vec<double, MhdNVars> Fhll = mhd_hll_flux(U, U, gamma, ch);
    Vec<double, MhdNVars> Fphys = mhd_flux_x(U, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k)
        REQUIRE(Fhll[k] == Approx(Fphys[k]));
}

TEST_CASE("HLL is conservative (consistency)", "[mhd][hll]") {
    const double gamma = 2.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0;   wl.Bx = 0.75; wl.By = 1.0;  wl.p = 1.0;
    wr.rho = 0.125; wr.Bx = 0.75; wr.By = -1.0; wr.p = 0.1;
    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma);
    Vec<double, MhdNVars> UR = prim_to_cons(wr, gamma);
    const double ch = 3.0;

    const double cfL = fast_speed_x(wl, gamma);
    const double cfR = fast_speed_x(wr, gamma);
    const double SL = std::min(wl.vx - cfL, wr.vx - cfR);
    const double SR = std::max(wr.vx + cfR, wl.vx + cfL);
    Vec<double, MhdNVars> FL = mhd_flux_x(UL, gamma, ch);
    Vec<double, MhdNVars> FR = mhd_flux_x(UR, gamma, ch);

    Vec<double, MhdNVars> F = mhd_hll_flux(UL, UR, gamma, ch);
    const double inv = 1.0 / (SR - SL);
    for (int k = 0; k < MhdNVars; ++k) {
        const double expected = (SR*FL[k] - SL*FR[k] + SL*SR*(UR[k] - UL[k])) * inv;
        REQUIRE(F[k] == Approx(expected));
    }
}

TEST_CASE("HLL returns the left flux when all waves move right", "[mhd][hll]") {
    const double gamma = 2.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0; wl.vx = 10.0; wl.vy = 0.2;  wl.vz = -0.1;
    wl.Bx = 0.75; wl.By = 0.5; wl.Bz = -0.25; wl.p = 1.0; wl.psi = 0.3;
    wr.rho = 0.8; wr.vx = 12.0; wr.vy = -0.1; wr.vz = 0.4;
    wr.Bx = 0.75; wr.By = -0.3; wr.Bz = 0.2; wr.p = 0.7; wr.psi = -0.2;

    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma);
    Vec<double, MhdNVars> UR = prim_to_cons(wr, gamma);
    const double ch = 3.0;

    REQUIRE(std::min(wl.vx - fast_speed_x(wl, gamma),
                     wr.vx - fast_speed_x(wr, gamma)) > 0.0);

    Vec<double, MhdNVars> Fhll = mhd_hll_flux(UL, UR, gamma, ch);
    Vec<double, MhdNVars> Fleft = mhd_flux_x(UL, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k)
        REQUIRE(Fhll[k] == Approx(Fleft[k]));
}

TEST_CASE("HLL returns the right flux when all waves move left", "[mhd][hll]") {
    const double gamma = 2.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0; wl.vx = -12.0; wl.vy = 0.2;  wl.vz = -0.1;
    wl.Bx = 0.75; wl.By = 0.5; wl.Bz = -0.25; wl.p = 1.0; wl.psi = 0.3;
    wr.rho = 0.8; wr.vx = -10.0; wr.vy = -0.1; wr.vz = 0.4;
    wr.Bx = 0.75; wr.By = -0.3; wr.Bz = 0.2; wr.p = 0.7; wr.psi = -0.2;

    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma);
    Vec<double, MhdNVars> UR = prim_to_cons(wr, gamma);
    const double ch = 3.0;

    REQUIRE(std::max(wr.vx + fast_speed_x(wr, gamma),
                     wl.vx + fast_speed_x(wl, gamma)) < 0.0);

    Vec<double, MhdNVars> Fhll = mhd_hll_flux(UL, UR, gamma, ch);
    Vec<double, MhdNVars> Fright = mhd_flux_x(UR, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k)
        REQUIRE(Fhll[k] == Approx(Fright[k]));
}
