#include "catch.hpp"
#include "core/eos.hpp"
#include "lw_tests.hpp"

using namespace hrsc;

TEST_CASE("LW Config3 sets expected quadrant primitive states", "[liska_wendroff]") {
    using Real = double;
    constexpr int nx = 100;
    constexpr int ny = 100;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(nx, ny);
    grid.dx = Real(1.0) / nx;
    grid.dy = Real(1.0) / ny;
    auto gv = grid.view();

    setup_liska_wendroff_config3(gv, gamma);

    auto read_prim = [&](int i, int j) {
        Vec<Real, EulerNVars> cons{};
        for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
        return cons_to_prim(cons, gamma);
    };

    auto q1 = read_prim(75, 75);  // x>0.5, y>0.5
    REQUIRE(q1[PRHO] == Approx(1.5));
    REQUIRE(q1[VX]   == Approx(0.0));
    REQUIRE(q1[VY]   == Approx(0.0));
    REQUIRE(q1[PRES] == Approx(1.5));

    auto q2 = read_prim(25, 75);  // x<0.5, y>0.5
    REQUIRE(q2[PRHO] == Approx(0.5323));
    REQUIRE(q2[VX]   == Approx(1.206));
    REQUIRE(q2[VY]   == Approx(0.0));
    REQUIRE(q2[PRES] == Approx(0.3));

    auto q3 = read_prim(25, 25);  // x<0.5, y<0.5
    REQUIRE(q3[PRHO] == Approx(0.138));
    REQUIRE(q3[VX]   == Approx(1.206));
    REQUIRE(q3[VY]   == Approx(1.206));
    REQUIRE(q3[PRES] == Approx(0.029));

    auto q4 = read_prim(75, 25);  // x>0.5, y<0.5
    REQUIRE(q4[PRHO] == Approx(0.5323));
    REQUIRE(q4[VX]   == Approx(0.0));
    REQUIRE(q4[VY]   == Approx(1.206));
    REQUIRE(q4[PRES] == Approx(0.3));
}

TEST_CASE("LW Config6 stub throws clear error", "[liska_wendroff]") {
    using Real = double;
    Grid2D<Real, EulerNVars> grid(8, 8);
    grid.dx = 1.0 / 8.0;
    grid.dy = 1.0 / 8.0;
    auto gv = grid.view();

    REQUIRE_THROWS_WITH(
        setup_liska_wendroff_config6(gv, Real(1.4)),
        "Config 6 not implemented yet (Week 5)");
}
