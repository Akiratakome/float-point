#include "catch.hpp"
#include "core/eos.hpp"
#include "shock_bubble_tests.hpp"

#include <cmath>

using namespace hrsc;

TEST_CASE("Shock-bubble Rankine-Hugoniot: Mach 1.22 air post-shock state",
          "[shock_bubble]") {
    using Real = double;
    constexpr Real gamma = 1.4;
    constexpr Real Ms = 1.22;
    constexpr Real rho1 = 1.0;
    constexpr Real p1 = 1.0;

    Real rho2, u2, p2;
    shock_bubble_post_shock<Real>(gamma, rho1, p1, Ms, rho2, u2, p2);

    REQUIRE(rho2 == Approx(1.37636397).epsilon(1e-6));
    REQUIRE(p2 == Approx(1.5698).epsilon(1e-6));
    REQUIRE(u2 == Approx(0.39472860).epsilon(1e-5));
}

TEST_CASE("Shock-bubble IC: three regions populated correctly",
          "[shock_bubble]") {
    using Real = double;
    constexpr int nx = 400;
    constexpr int ny = 100;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(nx, ny);
    grid.dx = Real(1.0) / nx;
    grid.dy = Real(0.25) / ny;
    auto gv = grid.view();

    setup_shock_bubble(gv, gamma);

    auto read_prim = [&](int i, int j) {
        Vec<Real, EulerNVars> cons{};
        for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
        return cons_to_prim(cons, gamma);
    };

    auto post = read_prim(5, ny / 2);
    REQUIRE(post[PRHO] == Approx(1.37636397).epsilon(1e-6));
    REQUIRE(post[PRES] == Approx(1.5698).epsilon(1e-6));
    REQUIRE(post[VX] == Approx(0.39472860).epsilon(1e-5));
    REQUIRE(post[VY] == Approx(0.0).margin(1e-14));

    auto pre = read_prim(nx - 5, ny - 5);
    REQUIRE(pre[PRHO] == Approx(1.0).margin(1e-13));
    REQUIRE(pre[PRES] == Approx(1.0).margin(1e-13));
    REQUIRE(pre[VX] == Approx(0.0).margin(1e-14));
    REQUIRE(pre[VY] == Approx(0.0).margin(1e-14));

    auto bub = read_prim(100, 0);
    REQUIRE(bub[PRHO] == Approx(0.138).margin(1e-13));
    REQUIRE(bub[PRES] == Approx(1.0).margin(1e-13));
    REQUIRE(bub[VX] == Approx(0.0).margin(1e-14));
}

TEST_CASE("Shock-bubble bubble half-disc has plausible cell count",
          "[shock_bubble]") {
    using Real = double;
    constexpr int nx = 400;
    constexpr int ny = 100;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(nx, ny);
    grid.dx = Real(1.0) / nx;
    grid.dy = Real(0.25) / ny;
    auto gv = grid.view();

    setup_shock_bubble(gv, gamma);

    int bubble_cells = 0;
    for (int j = 0; j < ny; ++j) {
        for (int i = 0; i < nx; ++i) {
            Vec<Real, EulerNVars> cons{};
            for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
            auto prim = cons_to_prim(cons, gamma);
            if (prim[PRHO] == 0.138) bubble_cells++;
        }
    }

    REQUIRE(bubble_cells > 2400);
    REQUIRE(bubble_cells < 2650);
}
