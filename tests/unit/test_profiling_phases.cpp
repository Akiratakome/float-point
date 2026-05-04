#include "catch.hpp"

#ifdef HRSC_ENABLE_PROFILING

#include "euler/euler_solver.hpp"
#include "toro_tests.hpp"

using namespace hrsc;

TEST_CASE("EulerSolver profiling records CPU step phases", "[profiling]") {
    constexpr int nx = 8;
    constexpr double gamma = 1.4;
    constexpr double dx = 1.0 / nx;

    EulerSolver<double> solver(nx, dx, 0.0, gamma, 0.8, 0.01);
    setup_sod(solver.grid_view(), gamma);

    solver.step();

    const auto phases = solver.profiling().snapshot();
    REQUIRE(phases.count("bc") == 1);
    REQUIRE(phases.count("cfl") == 1);
    REQUIRE(phases.count("flux") == 1);
    REQUIRE(phases.count("update") == 1);
}

#endif // HRSC_ENABLE_PROFILING
