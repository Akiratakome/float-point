#include "catch.hpp"
#include "mhd/hlld.hpp"
#include "mhd/hll.hpp"
#include "mhd/mhd_solver.hpp"
#include <cmath>

using namespace hrsc;

TEST_CASE("HLLD with identical states returns the physical flux", "[mhd][hlld]") {
    const double gamma = 2.0, ch = 2.0;
    MhdPrim<double> w{};
    w.rho = 1.0; w.vx = 0.3; w.vy = 0.1; w.Bx = 0.75; w.By = 1.0; w.p = 1.0;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);
    Vec<double, MhdNVars> F = mhd_hlld_flux(U, U, gamma, ch);
    Vec<double, MhdNVars> Fphys = mhd_flux_x(U, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k) REQUIRE(F[k] == Approx(Fphys[k]).margin(1e-12));
}

TEST_CASE("HLLD GLM (Bx,psi) split is exact in the supersonic branch", "[mhd][hlld]") {
    const double gamma = 2.0, ch = 3.0;
    // Supersonic to the right so SL>=0 -> the FL branch is taken; only the
    // GLM-split BX/PSI components are overwritten and are checkable by hand.
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0; wl.vx = 10.0; wl.Bx = 0.8; wl.By = 0.5; wl.p = 1.0; wl.psi = 0.2;
    wr.rho = 1.0; wr.vx = 10.0; wr.Bx = 0.6; wr.By = 0.5; wr.p = 1.0; wr.psi = -0.1;
    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma), UR = prim_to_cons(wr, gamma);
    Vec<double, MhdNVars> F = mhd_hlld_flux(UL, UR, gamma, ch);
    const double Bxs = 0.5 * (wl.Bx + wr.Bx) - 0.5 * (wr.psi - wl.psi) / ch;
    const double psis = 0.5 * (wl.psi + wr.psi) - 0.5 * ch * (wr.Bx - wl.Bx);
    REQUIRE(F[MhdIdx::BX]  == Approx(psis));
    REQUIRE(F[MhdIdx::PSI] == Approx(ch * ch * Bxs));
    REQUIRE(F[MhdIdx::RHO] == Approx(wl.rho * wl.vx));  // upwind physical mass flux
}

TEST_CASE("HLLD produces finite, conservative flux on Brio-Wu states", "[mhd][hlld]") {
    const double gamma = 2.0, ch = 3.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0;   wl.Bx = 0.75; wl.By = 1.0;  wl.p = 1.0;
    wr.rho = 0.125; wr.Bx = 0.75; wr.By = -1.0; wr.p = 0.1;
    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma), UR = prim_to_cons(wr, gamma);
    Vec<double, MhdNVars> F = mhd_hlld_flux(UL, UR, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k) REQUIRE(std::isfinite(F[k]));
}

TEST_CASE("HLLD falls back to HLL for a degenerate (ch<=0) input", "[mhd][hlld]") {
    // The GLM split divides by ch; ch=0 must route to the HLL flux rather than
    // produce inf/nan. With identical Bx and psi=0 the two solvers also agree.
    const double gamma = 2.0, ch = 0.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0;   wl.Bx = 0.75; wl.By = 1.0;  wl.p = 1.0;
    wr.rho = 0.125; wr.Bx = 0.75; wr.By = -1.0; wr.p = 0.1;
    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma), UR = prim_to_cons(wr, gamma);
    Vec<double, MhdNVars> Fd = mhd_hlld_flux(UL, UR, gamma, ch);
    Vec<double, MhdNVars> Fh = mhd_hll_flux(UL, UR, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k) {
        REQUIRE(std::isfinite(Fd[k]));
        REQUIRE(Fd[k] == Approx(Fh[k]).margin(1e-12));
    }
}

TEST_CASE("HLLD solver advances Brio-Wu with no nonphysical state", "[mhd][hlld][solver]") {
    MhdSolver<double, HlldFlux> s(128, 1.0 / 128, 0.0, 2.0, 0.4, 0.05);
    setup_brio_wu(s.grid_view(), 128, 1.0 / 128, 0.0, 2.0, 0.5);
    s.run();  // throws if any nonphysical state is produced
    auto gv = s.grid_view();
    for (int i = 0; i < 128; ++i) {
        REQUIRE(std::isfinite(gv(i, 0, MhdIdx::RHO)));
        REQUIRE(gv(i, 0, MhdIdx::BX) == Approx(0.75).margin(1e-6));  // psi~0 in 1D
    }
}
