#include "catch.hpp"
#include "core/boundary.hpp"

using namespace hrsc;

static constexpr int NVARS = 4;

TEST_CASE("Outflow BC fills x-ghost cells from outermost physical cells", "[boundary]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    for (int j = 0; j < 3; ++j) {
        for (int var = 0; var < NVARS; ++var) {
            v(0, j, var) = 10.0 + j + var * 0.1;
            v(3, j, var) = 90.0 + j + var * 0.1;
        }
    }

    apply_outflow_bc(v);

    for (int j = 0; j < 3; ++j) {
        for (int var = 0; var < NVARS; ++var) {
            double expected_left = 10.0 + j + var * 0.1;
            REQUIRE(v(-1, j, var) == Approx(expected_left));
            REQUIRE(v(-2, j, var) == Approx(expected_left));
        }
    }

    for (int j = 0; j < 3; ++j) {
        for (int var = 0; var < NVARS; ++var) {
            double expected_right = 90.0 + j + var * 0.1;
            REQUIRE(v(4, j, var) == Approx(expected_right));
            REQUIRE(v(5, j, var) == Approx(expected_right));
        }
    }
}

TEST_CASE("Outflow BC fills y-ghost cells from outermost physical rows", "[boundary]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    for (int i = 0; i < 4; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            v(i, 0, var) = 20.0 + i + var * 0.1;
            v(i, 2, var) = 80.0 + i + var * 0.1;
        }
    }

    apply_outflow_bc(v);

    for (int i = 0; i < 4; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            double expected_bottom = 20.0 + i + var * 0.1;
            REQUIRE(v(i, -1, var) == Approx(expected_bottom));
            REQUIRE(v(i, -2, var) == Approx(expected_bottom));
        }
    }

    for (int i = 0; i < 4; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            double expected_top = 80.0 + i + var * 0.1;
            REQUIRE(v(i, 3, var) == Approx(expected_top));
            REQUIRE(v(i, 4, var) == Approx(expected_top));
        }
    }
}

TEST_CASE("Outflow BC 1D mode fills y-ghosts without corrupting data", "[boundary]") {
    Grid2D<double, NVARS> grid(10, 1);
    auto v = grid.view();

    for (int i = 0; i < 10; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            v(i, 0, var) = 100.0 + i * 10.0 + var;
        }
    }

    apply_outflow_bc(v);

    // Physical cells unchanged
    for (int i = 0; i < 10; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            REQUIRE(v(i, 0, var) == Approx(100.0 + i * 10.0 + var));
        }
    }

    // X-ghosts correct
    for (int var = 0; var < NVARS; ++var) {
        REQUIRE(v(-1, 0, var) == Approx(100.0 + var));
        REQUIRE(v(-2, 0, var) == Approx(100.0 + var));
        REQUIRE(v(10, 0, var) == Approx(100.0 + 90.0 + var));
        REQUIRE(v(11, 0, var) == Approx(100.0 + 90.0 + var));
    }

    // Y-ghosts filled (not left uninitialized)
    for (int i = 0; i < 10; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            double expected = 100.0 + i * 10.0 + var;
            REQUIRE(v(i, -1, var) == Approx(expected));
            REQUIRE(v(i, -2, var) == Approx(expected));
            REQUIRE(v(i, 1, var) == Approx(expected));
            REQUIRE(v(i, 2, var) == Approx(expected));
        }
    }
}

TEST_CASE("Outflow BC corner ghost cells are filled", "[boundary]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    v(0, 0, 0) = 1.0;
    v(3, 0, 0) = 2.0;
    v(0, 2, 0) = 3.0;
    v(3, 2, 0) = 4.0;

    apply_outflow_bc(v);

    // Corner ghosts: y-pass runs last, copies from y-edge which x-pass already filled
    REQUIRE(v(-1, -1, 0) == Approx(1.0));  // from v(0,0,0)
    REQUIRE(v(4, -1, 0) == Approx(2.0));   // from v(3,0,0)
    REQUIRE(v(-1, 3, 0) == Approx(3.0));   // from v(0,2,0)
    REQUIRE(v(4, 3, 0) == Approx(4.0));    // from v(3,2,0)
}
