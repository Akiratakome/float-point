#include "catch.hpp"
#include "core/grid.hpp"
#include "mhd/mhd_solver.hpp"
#include "mhd/mhd_state.hpp"
#include "utils/error_norms.hpp"
#include <cmath>

using namespace hrsc;

namespace {
hrsc::Vec<double, hrsc::MhdNVars> load_cell_test(hrsc::GridView<double, hrsc::MhdNVars> gv,
                                                 int i, int j) {
    hrsc::Vec<double, hrsc::MhdNVars> U{};
    for (int k = 0; k < hrsc::MhdNVars; ++k) U[k] = gv(i, j, k);
    return U;
}
} // namespace

TEST_CASE("Orszag-Tang IC matches analytic fields and is divergence-free", "[mhd][ot]") {
    const int nx = 32, ny = 24;
    const double xmin = 0.125, ymin = -0.2;
    const double dx = 1.25 / nx, dy = 0.75 / ny, gamma = 5.0 / 3.0;
    Grid2D<double, MhdNVars> grid(nx, ny);
    grid.dx = dx; grid.dy = dy;
    setup_orszag_tang<double>(grid.view(), nx, ny, dx, dy, xmin, ymin, gamma);

    auto gv = grid.view();
    const double pi = 3.14159265358979323846;
    const double B0 = 1.0, rho0 = gamma * gamma, p0 = gamma;
    const int i = 7, j = 11;
    const double x = xmin + (i + 0.5) * dx;
    const double y = ymin + (j + 0.5) * dy;
    MhdPrim<double> w = cons_to_prim(load_cell_test(gv, i, j), gamma);
    REQUIRE(w.rho == Approx(rho0));
    REQUIRE(w.p   == Approx(p0));
    REQUIRE(w.vx  == Approx(-std::sin(2 * pi * y)));
    REQUIRE(w.vy  == Approx( std::sin(2 * pi * x)));
    REQUIRE(w.vz  == Approx(0.0));
    REQUIRE(w.Bx  == Approx(-B0 * std::sin(2 * pi * y)));
    REQUIRE(w.By  == Approx( B0 * std::sin(4 * pi * x)));
    REQUIRE(w.Bz  == Approx(0.0));
    REQUIRE(w.psi == Approx(0.0));

    DivBNorms<double> d = compute_divB_norms<double>(gv, nx, ny, dx, dy);
    REQUIRE(d.mean == Approx(0.0).margin(1e-12));
    REQUIRE(d.max == Approx(0.0).margin(1e-12));
}
