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

TEST_CASE("Periodic BC wraps opposite edges in both directions", "[boundary]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    for (int j = 0; j < 3; ++j) {
        for (int i = 0; i < 4; ++i) {
            v(i, j, 0) = 100.0 * j + i;
        }
    }

    apply_periodic_bc(v);

    // X wrap
    REQUIRE(v(-1, 1, 0) == Approx(v(3, 1, 0)));
    REQUIRE(v(-2, 1, 0) == Approx(v(2, 1, 0)));
    REQUIRE(v(4, 1, 0) == Approx(v(0, 1, 0)));
    REQUIRE(v(5, 1, 0) == Approx(v(1, 1, 0)));

    // Y wrap
    REQUIRE(v(2, -1, 0) == Approx(v(2, 2, 0)));
    REQUIRE(v(2, -2, 0) == Approx(v(2, 1, 0)));
    REQUIRE(v(2, 3, 0) == Approx(v(2, 0, 0)));
    REQUIRE(v(2, 4, 0) == Approx(v(2, 1, 0)));
}

TEST_CASE("Periodic BC handles 1D (ny=1) without ghost-source leakage", "[boundary]") {
    Grid2D<double, NVARS> grid(5, 1);
    auto v = grid.view();

    for (int i = 0; i < 5; ++i) {
        v(i, 0, 0) = 10.0 + i;
    }

    apply_periodic_bc(v);

    for (int i = 0; i < 5; ++i) {
        REQUIRE(v(i, -1, 0) == Approx(v(i, 0, 0)));
        REQUIRE(v(i, -2, 0) == Approx(v(i, 0, 0)));
        REQUIRE(v(i, 1, 0) == Approx(v(i, 0, 0)));
        REQUIRE(v(i, 2, 0) == Approx(v(i, 0, 0)));
    }
}

TEST_CASE("Reflective BC flips normal momentum components", "[boundary]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    for (int j = 0; j < 3; ++j) {
        for (int i = 0; i < 4; ++i) {
            v(i, j, RHO) = 1.0 + i + j;
            v(i, j, RHOU) = 10.0 + i;
            v(i, j, RHOV) = 20.0 + j;
            v(i, j, EN) = 50.0;
        }
    }

    apply_reflective_bc(v);

    // Left/right: RHOU flips sign, RHOV keeps sign.
    REQUIRE(v(-1, 1, RHOU) == Approx(-v(0, 1, RHOU)));
    REQUIRE(v(4, 1, RHOU) == Approx(-v(3, 1, RHOU)));
    REQUIRE(v(-1, 1, RHOV) == Approx(v(0, 1, RHOV)));
    REQUIRE(v(4, 1, RHOV) == Approx(v(3, 1, RHOV)));

    // Bottom/top: RHOV flips sign, RHOU keeps sign.
    REQUIRE(v(2, -1, RHOV) == Approx(-v(2, 0, RHOV)));
    REQUIRE(v(2, 3, RHOV) == Approx(-v(2, 2, RHOV)));
    REQUIRE(v(2, -1, RHOU) == Approx(v(2, 0, RHOU)));
    REQUIRE(v(2, 3, RHOU) == Approx(v(2, 2, RHOU)));
}
