#include "catch.hpp"
#include "core/grid.hpp"
#include "mhd/mhd_state.hpp"
#include "utils/error_norms.hpp"

using namespace hrsc;

TEST_CASE("divB is zero for constant Bx (1D)", "[mhd][divb]") {
    Grid2D<double, MhdNVars> grid(8, 1);
    auto v = grid.view();
    for (int i = 0; i < 8; ++i) v(i, 0, MhdIdx::BX) = 0.75;
    DivBNorms<double> d = compute_divB_norms<double>(v, 8, 1, 0.1, 0.1);
    REQUIRE(d.mean == Approx(0.0).margin(1e-14));
    REQUIRE(d.max  == Approx(0.0).margin(1e-14));
}

TEST_CASE("divB picks up a linear Bx slope (1D)", "[mhd][divb]") {
    const double dx = 0.5;
    Grid2D<double, MhdNVars> grid(8, 1);
    auto v = grid.view();
    for (int i = 0; i < 8; ++i) v(i, 0, MhdIdx::BX) = 3.0 * (i * dx); // dBx/dx = 3
    DivBNorms<double> d = compute_divB_norms<double>(v, 8, 1, dx, dx);
    REQUIRE(d.mean == Approx(3.0));
    REQUIRE(d.max == Approx(3.0));
}

TEST_CASE("divB returns zero with no 1D interior samples", "[mhd][divb]") {
    Grid2D<double, MhdNVars> grid(2, 1);
    auto v = grid.view();
    for (int i = 0; i < 2; ++i) v(i, 0, MhdIdx::BX) = 10.0 * i;
    DivBNorms<double> d = compute_divB_norms<double>(v, 2, 1, 0.25, 0.25);
    REQUIRE(d.mean == Approx(0.0).margin(1e-14));
    REQUIRE(d.max  == Approx(0.0).margin(1e-14));
}

TEST_CASE("divB returns zero with no 2D full-stencil samples", "[mhd][divb]") {
    Grid2D<double, MhdNVars> grid(4, 2);
    auto v = grid.view();
    for (int j = 0; j < 2; ++j)
        for (int i = 0; i < 4; ++i)
            v(i, j, MhdIdx::BX) = 10.0 * i;
    DivBNorms<double> d = compute_divB_norms<double>(v, 4, 2, 0.25, 0.25);
    REQUIRE(d.mean == Approx(0.0).margin(1e-14));
    REQUIRE(d.max  == Approx(0.0).margin(1e-14));
}
