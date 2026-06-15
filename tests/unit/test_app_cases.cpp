#include "catch.hpp"
#include "app/cases.hpp"
#include "core/eos.hpp"
#include "core/grid.hpp"

using namespace hrsc;
using namespace hrsc::app;

TEST_CASE("setup_case_ic initializes Sod left and right states", "[app][cases]") {
    Grid2D<double, EulerNVars> grid(4, 1);
    grid.dx = 0.25;
    grid.dy = 0.25;
    setup_case_ic(grid.view(), "sod", 1.4);

    Vec<double, EulerNVars> left;
    Vec<double, EulerNVars> right;
    auto view = grid.view();
    for (int v = 0; v < EulerNVars; ++v) {
        left[v] = view(0, 0, v);
        right[v] = view(3, 0, v);
    }

    REQUIRE(left[RHO] == Approx(1.0));
    REQUIRE(pressure(left, 1.4) == Approx(1.0));
    REQUIRE(right[RHO] == Approx(0.125));
    REQUIRE(pressure(right, 1.4) == Approx(0.1));
}

TEST_CASE("get_riemann_ic returns Toro 3 exact-reference states", "[app][cases]") {
    RiemannInitialCondition ic = get_riemann_ic("toro3");

    REQUIRE(ic.x0 == Approx(0.5));
    REQUIRE(ic.rhoL == Approx(1.0));
    REQUIRE(ic.uL == Approx(0.0));
    REQUIRE(ic.pL == Approx(1000.0));
    REQUIRE(ic.rhoR == Approx(1.0));
    REQUIRE(ic.uR == Approx(0.0));
    REQUIRE(ic.pR == Approx(0.01));
}
