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

TEST_CASE("LW Config6 sets expected quadrant primitive states", "[liska_wendroff]") {
    using Real = double;
    constexpr int nx = 100;
    constexpr int ny = 100;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(nx, ny);
    grid.dx = Real(1.0) / nx;
    grid.dy = Real(1.0) / ny;
    auto gv = grid.view();

    setup_liska_wendroff_config6(gv, gamma);

    auto read_prim = [&](int i, int j) {
        Vec<Real, EulerNVars> cons{};
        for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
        return cons_to_prim(cons, gamma);
    };

    auto eq = [](Real expected) {
        return Approx(expected).epsilon(0).margin(1e-13);
    };

    auto q1 = read_prim(75, 75);  // x>0.5, y>0.5
    REQUIRE(q1[PRHO] == eq(1.0));
    REQUIRE(q1[VX]   == eq(0.75));
    REQUIRE(q1[VY]   == eq(-0.5));
    REQUIRE(q1[PRES] == eq(1.0));

    auto q2 = read_prim(25, 75);  // x<0.5, y>0.5
    REQUIRE(q2[PRHO] == eq(2.0));
    REQUIRE(q2[VX]   == eq(0.75));
    REQUIRE(q2[VY]   == eq(0.5));
    REQUIRE(q2[PRES] == eq(1.0));

    auto q3 = read_prim(25, 25);  // x<0.5, y<0.5
    REQUIRE(q3[PRHO] == eq(1.0));
    REQUIRE(q3[VX]   == eq(-0.75));
    REQUIRE(q3[VY]   == eq(0.5));
    REQUIRE(q3[PRES] == eq(1.0));

    auto q4 = read_prim(75, 25);  // x>0.5, y<0.5
    REQUIRE(q4[PRHO] == eq(3.0));
    REQUIRE(q4[VX]   == eq(-0.75));
    REQUIRE(q4[VY]   == eq(-0.5));
    REQUIRE(q4[PRES] == eq(1.0));
}

TEST_CASE("LW Config6 has uniform pressure 1.0 across the entire domain",
          "[liska_wendroff]") {
    using Real = double;
    constexpr int N = 64;
    constexpr Real gamma = 1.4;

    Grid2D<Real, EulerNVars> grid(N, N);
    grid.dx = Real(1.0) / N;
    grid.dy = Real(1.0) / N;
    auto gv = grid.view();

    setup_liska_wendroff_config6(gv, gamma);

    for (int j = 0; j < N; ++j) {
        for (int i = 0; i < N; ++i) {
            Vec<Real, EulerNVars> cons{};
            for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
            auto prim = cons_to_prim(cons, gamma);
            REQUIRE(prim[PRES] == Approx(1.0).epsilon(0).margin(1e-13));
        }
    }
}
