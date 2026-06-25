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
    const int n = 32;
    const double L = 1.0, dx = L / n, gamma = 5.0 / 3.0;
    Grid2D<double, MhdNVars> grid(n, n);
    grid.dx = dx; grid.dy = dx;
    setup_orszag_tang<double>(grid.view(), n, n, dx, dx, 0.0, 0.0, gamma);

    auto gv = grid.view();
    const double pi = 3.14159265358979323846;
    const double B0 = 1.0, rho0 = gamma * gamma, p0 = gamma;
    const int i = 7, j = 11;
    const double x = (i + 0.5) * dx, y = (j + 0.5) * dx;
    MhdPrim<double> w = cons_to_prim(load_cell_test(gv, i, j), gamma);
    REQUIRE(w.rho == Approx(rho0));
    REQUIRE(w.p   == Approx(p0));
    REQUIRE(w.vx  == Approx(-std::sin(2 * pi * y)));
    REQUIRE(w.vy  == Approx( std::sin(2 * pi * x)));
    REQUIRE(w.Bx  == Approx(-B0 * std::sin(2 * pi * y)));
    REQUIRE(w.By  == Approx( B0 * std::sin(4 * pi * x)));

    DivBNorms<double> d = compute_divB_norms<double>(gv, n, n, dx, dx);
    REQUIRE(d.max == Approx(0.0).margin(1e-12));
}
