#include "catch.hpp"
#include "mhd/hlld.hpp"
#include "mhd/hll.hpp"
#include "mhd/mhd_solver.hpp"
#include <cmath>

using namespace hrsc;

namespace {

Vec<double, MhdNVars> glm_fan_state(MhdPrim<double> w, double Bx, double gamma) {
    w.Bx = Bx;
    w.psi = 0.0;
    return prim_to_cons(w, gamma);
}

} // namespace

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
    Vec<double, MhdNVars> FLfan = mhd_flux_x(glm_fan_state(wl, Bxs, gamma), gamma, ch);
    REQUIRE(F[MhdIdx::BX]  == Approx(psis));
    REQUIRE(F[MhdIdx::PSI] == Approx(ch * ch * Bxs));
    REQUIRE(F[MhdIdx::RHO] == Approx(wl.rho * wl.vx));  // upwind physical mass flux
    REQUIRE(F[MhdIdx::MX]  == Approx(FLfan[MhdIdx::MX]));
    REQUIRE(F[MhdIdx::E]   == Approx(FLfan[MhdIdx::E]));
}

TEST_CASE("HLLD produces finite flux on Brio-Wu states", "[mhd][hlld]") {
    const double gamma = 2.0, ch = 3.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0;   wl.Bx = 0.75; wl.By = 1.0;  wl.p = 1.0;
    wr.rho = 0.125; wr.Bx = 0.75; wr.By = -1.0; wr.p = 0.1;
    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma), UR = prim_to_cons(wr, gamma);
    Vec<double, MhdNVars> F = mhd_hlld_flux(UL, UR, gamma, ch);
    for (int k = 0; k < MhdNVars; ++k) REQUIRE(std::isfinite(F[k]));
}

TEST_CASE("HLLD remains finite for near-zero GLM normal field stress", "[mhd][hlld]") {
    const double gamma = 2.0, ch = 3.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0; wl.vx = -0.2; wl.vy = 0.3; wl.Bx = 1.0; wl.By = 0.7; wl.p = 1.0;
    wr.rho = 0.8; wr.vx = 0.1; wr.vy = -0.4; wr.Bx = -0.8; wr.By = -0.6; wr.p = 0.9;
    wl.psi = -0.3;
    wr.psi = 0.3;  // Bx* = 0 exactly; rotational fan degenerates to the contact.
    Vec<double, MhdNVars> F = mhd_hlld_flux(prim_to_cons(wl, gamma), prim_to_cons(wr, gamma),
                                            gamma, ch);
    for (int k = 0; k < MhdNVars; ++k) REQUIRE(std::isfinite(F[k]));
}

TEST_CASE("HLLD preserves a stationary tangential discontinuity (SM=0 tie)", "[mhd][hlld]") {
    // Bn=0, vx=0, equal total pressure (ptL = 1 + 0.5*1^2 = ptR = 1.375 +
    // 0.5*0.5^2 = 1.5 exactly in FP): SM = SsL = SsR = 0 exactly, the MHD
    // analogue of the Euler stationary-contact S*=0 case. Both tie owners
    // (F*L via <=, the fall-through side via <) must produce the same exact
    // no-transport flux, so this pins the tie contract for the
    // RIEMANN_STRICT_INEQUALITY study axis: zero mass/energy/induction flux
    // and the continuous total pressure in the normal momentum component.
    const double gamma = 2.0, ch = 1.0;
    MhdPrim<double> wl{}, wr{};
    wl.rho = 1.0;   wl.By = 1.0; wl.p = 1.0;
    wr.rho = 0.125; wr.By = 0.5; wr.p = 1.375;
    Vec<double, MhdNVars> UL = prim_to_cons(wl, gamma), UR = prim_to_cons(wr, gamma);
    Vec<double, MhdNVars> F = mhd_hlld_flux(UL, UR, gamma, ch);
    const double pt = 1.5;
    REQUIRE(F[MhdIdx::RHO] == Approx(0.0).margin(1e-14));
    REQUIRE(F[MhdIdx::MX]  == Approx(pt).margin(1e-14));
    REQUIRE(F[MhdIdx::MY]  == Approx(0.0).margin(1e-14));
    REQUIRE(F[MhdIdx::MZ]  == Approx(0.0).margin(1e-14));
    REQUIRE(F[MhdIdx::BX]  == Approx(0.0).margin(1e-14));
    REQUIRE(F[MhdIdx::BY]  == Approx(0.0).margin(1e-14));
    REQUIRE(F[MhdIdx::BZ]  == Approx(0.0).margin(1e-14));
    REQUIRE(F[MhdIdx::E]   == Approx(0.0).margin(1e-14));
    REQUIRE(F[MhdIdx::PSI] == Approx(0.0).margin(1e-14));
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
