#include "catch.hpp"
#include "core/grid.hpp"
#include "mhd/mhd_solver.hpp"
#include "mhd/mhd_state.hpp"
#include "utils/error_norms.hpp"
#include <cmath>

using namespace hrsc;

namespace {

Vec<double, MhdNVars> load_cell_test(GridView<double, MhdNVars> gv, int i, int j) {
    Vec<double, MhdNVars> U{};
    for (int k = 0; k < MhdNVars; ++k) U[k] = gv(i, j, k);
    return U;
}

} // namespace

TEST_CASE("Kelvin-Helmholtz IC sets double shear layer and uniform magnetic field", "[mhd][kh]") {
    const int nx = 40, ny = 32;
    const double xmin = -0.35, ymin = -0.125;
    const double dx = 1.0 / nx, dy = 1.0 / ny, gamma = 5.0 / 3.0;
    Grid2D<double, MhdNVars> grid(nx, ny);
    grid.dx = dx;
    grid.dy = dy;

    setup_kelvin_helmholtz<double>(grid.view(), nx, ny, dx, dy, xmin, ymin, gamma);

    auto gv = grid.view();
    const int i_mid = 18;
    const int j_inside = 20;  // y = 0.515625, well inside the positive-velocity band.
    const int j_below = 4;    // y = 0.015625, safely below y1=0.25.
    const int j_above = 30;   // y = 0.828125, safely above y2=0.75.
    const int i_seed = 12;
    const int j_seed = 12;    // y = 0.265625, near the lower seeded interface.

    const MhdPrim<double> inside = cons_to_prim(load_cell_test(gv, i_mid, j_inside), gamma);
    const MhdPrim<double> below = cons_to_prim(load_cell_test(gv, i_mid, j_below), gamma);
    const MhdPrim<double> above = cons_to_prim(load_cell_test(gv, i_mid, j_above), gamma);
    auto expected_vx = [ymin, dy](int j) {
        const double y = ymin + (j + 0.5) * dy;
        return 0.5 * (std::tanh((y - 0.25) / 0.025)
                    - std::tanh((y - 0.75) / 0.025) - 1.0);
    };

    REQUIRE(inside.rho == Approx(1.0));
    REQUIRE(inside.p == Approx(1.0));
    REQUIRE(inside.Bx == Approx(0.1));
    REQUIRE(inside.By == Approx(0.0));
    REQUIRE(inside.Bz == Approx(0.0));
    REQUIRE(inside.psi == Approx(0.0));
    REQUIRE(inside.vx == Approx(expected_vx(j_inside)));
    REQUIRE(below.vx == Approx(expected_vx(j_below)));
    REQUIRE(above.vx == Approx(expected_vx(j_above)));

    const MhdPrim<double> seed = cons_to_prim(load_cell_test(gv, i_seed, j_seed), gamma);
    const double pi = 3.14159265358979323846;
    const double x_seed = xmin + (i_seed + 0.5) * dx;
    const double y_seed = ymin + (j_seed + 0.5) * dy;
    const double dy1 = y_seed - 0.25;
    const double dy2 = y_seed - 0.75;
    const double expected_vy = 0.01 * std::sin(2.0 * pi * x_seed)
        * (std::exp(-(dy1 * dy1) / (0.05 * 0.05))
         + std::exp(-(dy2 * dy2) / (0.05 * 0.05)));
    REQUIRE(seed.vy == Approx(expected_vy));

    for (int j : {j_below, j_inside, j_above}) {
        for (int i : {0, i_mid, nx - 1}) {
            const MhdPrim<double> w = cons_to_prim(load_cell_test(gv, i, j), gamma);
            REQUIRE(w.rho == Approx(1.0));
            REQUIRE(w.p == Approx(1.0));
            REQUIRE(w.Bx == Approx(0.1));
            REQUIRE(w.By == Approx(0.0));
            REQUIRE(w.Bz == Approx(0.0));
            REQUIRE(w.psi == Approx(0.0));
        }
    }

    const DivBNorms<double> d = compute_divB_norms<double>(gv, nx, ny, dx, dy);
    REQUIRE(d.mean == Approx(0.0).margin(1e-12));
    REQUIRE(d.max == Approx(0.0).margin(1e-12));
}
