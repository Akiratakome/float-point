#include "catch.hpp"
#include "core/eos.hpp"
#include "euler/euler_solver.hpp"
#include "lw_tests.hpp"

#include <cmath>

using namespace hrsc;

TEST_CASE("LW Config 12 IC sample cells match published values", "[lw][lw12]") {
    using Real = double;
    constexpr int nx = 4;
    constexpr int ny = 4;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(nx, ny);
    grid.dx = Real(1.0) / nx;
    grid.dy = Real(1.0) / ny;
    auto gv = grid.view();

    setup_liska_wendroff_config12(gv, gamma);

    auto read_prim = [&](int i, int j) {
        Vec<Real, EulerNVars> cons{};
        for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
        return cons_to_prim(cons, gamma);
    };

    auto eq = [](Real expected) {
        return Approx(expected).epsilon(0).margin(1e-13);
    };

    auto q1 = read_prim(3, 3);  // x>0.5, y>0.5
    REQUIRE(q1[PRHO] == eq(0.5313));
    REQUIRE(q1[VX] == eq(0.0));
    REQUIRE(q1[VY] == eq(0.0));
    REQUIRE(q1[PRES] == eq(0.4));

    auto q2 = read_prim(0, 3);  // x<0.5, y>0.5
    REQUIRE(q2[PRHO] == eq(1.0));
    REQUIRE(q2[VX] == eq(0.7276));
    REQUIRE(q2[VY] == eq(0.0));
    REQUIRE(q2[PRES] == eq(1.0));

    auto q3 = read_prim(0, 0);  // x<0.5, y<0.5
    REQUIRE(q3[PRHO] == eq(0.8));
    REQUIRE(q3[VX] == eq(0.0));
    REQUIRE(q3[VY] == eq(0.0));
    REQUIRE(q3[PRES] == eq(1.0));

    auto q4 = read_prim(3, 0);  // x>0.5, y<0.5
    REQUIRE(q4[PRHO] == eq(1.0));
    REQUIRE(q4[VX] == eq(0.0));
    REQUIRE(q4[VY] == eq(0.7276));
    REQUIRE(q4[PRES] == eq(1.0));
}

TEST_CASE("LW Config 12 runs one step without NaN or Inf", "[lw][lw12]") {
    using Real = double;
    constexpr int nx = 16;
    constexpr int ny = 16;
    constexpr Real gamma = 1.4;
    constexpr Real cfl = 0.4;
    constexpr Real dx = Real(1.0) / nx;
    constexpr Real dy = Real(1.0) / ny;

    EulerSolver<Real> solver(nx, ny, dx, dy, Real(0.0), Real(0.0),
                             gamma, cfl, 0.25, FluxScheme::HLLC,
                             BoundaryType::Outflow, BoundaryType::Outflow);
    auto gv = solver.grid_view();
    setup_liska_wendroff_config12(gv, gamma);

    solver.step();

    REQUIRE(solver.step_count() == 1);
    REQUIRE(solver.time() > 0.0);

    for (int j = 0; j < ny; ++j) {
        for (int i = 0; i < nx; ++i) {
            Vec<Real, EulerNVars> cons{};
            for (int v = 0; v < EulerNVars; ++v) {
                cons[v] = gv(i, j, v);
                REQUIRE(std::isfinite(cons[v]));
            }
            auto prim = cons_to_prim(cons, gamma);
            for (int v = 0; v < EulerNVars; ++v) {
                REQUIRE(std::isfinite(prim[v]));
            }
        }
    }
}
