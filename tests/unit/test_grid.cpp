#include "catch.hpp"
#include "core/grid.hpp"

using namespace hrsc;

static constexpr int NVARS = 4; // Euler: rho, rho*u, rho*v, E

TEST_CASE("Grid2D allocation size is correct", "[grid]") {
    Grid2D<double, NVARS> grid(10, 20);
    int ng = Grid2D<double, NVARS>::ng; // 2
    int expected = (10 + 2 * ng) * (20 + 2 * ng) * NVARS;
    REQUIRE(grid.data.size() == static_cast<size_t>(expected));
}

TEST_CASE("Grid2D 1D mode allocation", "[grid]") {
    Grid2D<double, NVARS> grid(200, 1);
    int ng = Grid2D<double, NVARS>::ng;
    int expected = (200 + 2 * ng) * (1 + 2 * ng) * NVARS;
    REQUIRE(grid.data.size() == static_cast<size_t>(expected));
}

TEST_CASE("Grid2D zero-initialized", "[grid]") {
    Grid2D<double, NVARS> grid(5, 5);
    for (size_t i = 0; i < grid.data.size(); ++i) {
        REQUIRE(grid.data[i] == 0.0);
    }
}

TEST_CASE("GridView write and read physical cells", "[grid]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    v(2, 1, 0) = 42.0;
    REQUIRE(v(2, 1, 0) == Approx(42.0));

    v(0, 0, 3) = 99.0;
    REQUIRE(v(0, 0, 3) == Approx(99.0));
}

TEST_CASE("GridView ghost cell access", "[grid]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    v(-1, 0, 0) = 7.0;
    REQUIRE(v(-1, 0, 0) == Approx(7.0));

    v(4, 0, 0) = 8.0;
    REQUIRE(v(4, 0, 0) == Approx(8.0));

    v(0, -2, 1) = 9.0;
    REQUIRE(v(0, -2, 1) == Approx(9.0));
}

TEST_CASE("GridView index matches raw memory layout", "[grid]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();
    int ng = 2;

    int nx_total = 4 + 2 * ng; // 8
    int expected_idx = ((2 + ng) * nx_total + (1 + ng)) * NVARS + 3;
    REQUIRE(v.index(1, 2, 3) == expected_idx);

    v(1, 2, 3) = 123.456;
    REQUIRE(grid.data[static_cast<size_t>(expected_idx)] == Approx(123.456));
}

TEST_CASE("GridView 1D mode indexing", "[grid]") {
    Grid2D<double, NVARS> grid(200, 1);
    auto v = grid.view();
    int ng = 2;

    int nx_total = 200 + 2 * ng; // 204
    int expected_idx = ((0 + ng) * nx_total + (100 + ng)) * NVARS + 0;
    v(100, 0, 0) = 55.5;
    REQUIRE(grid.data[static_cast<size_t>(expected_idx)] == Approx(55.5));
}

TEST_CASE("Grid2D view() const returns ConstGridView", "[grid]") {
    Grid2D<double, NVARS> grid(4, 3);
    grid.view()(0, 0, 0) = 1.0;

    const Grid2D<double, NVARS>& cgrid = grid;
    auto cv = cgrid.view();

    REQUIRE(cv(0, 0, 0) == Approx(1.0));

    // The following should NOT compile (uncomment to verify):
    // cv(0, 0, 0) = 2.0;  // ERROR: assignment to const reference
}

TEST_CASE("Grid2D dimensions stored correctly", "[grid]") {
    Grid2D<double, NVARS> grid(10, 20);
    REQUIRE(grid.nx == 10);
    REQUIRE(grid.ny == 20);

    auto v = grid.view();
    REQUIRE(v.nx == 10);
    REQUIRE(v.ny == 20);
    REQUIRE(v.nx_total() == 14);
    REQUIRE(v.ny_total() == 24);
}

TEST_CASE("Grid2D dx/dy propagated to view", "[grid]") {
    Grid2D<double, NVARS> grid(100, 50);
    grid.dx = 0.01;
    grid.dy = 0.02;

    auto v = grid.view();
    REQUIRE(v.dx == Approx(0.01));
    REQUIRE(v.dy == Approx(0.02));
}
