#include "catch.hpp"

#ifdef HRSC_ENABLE_PROFILING

#include "euler/euler_solver.hpp"
#include "toro_tests.hpp"

#include <sstream>

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

TEST_CASE("ProfilingRegistry writes phase timing lines", "[profiling]") {
    ProfilingRegistry reg;
    reg.add("bc", 0.1);
    reg.add("flux", 0.2);

    std::ostringstream out;
    write_profiling_timings(out, reg);

    const std::string text = out.str();
    REQUIRE(text.find("[timing] phase=bc seconds=") != std::string::npos);
    REQUIRE(text.find("[timing] phase=flux seconds=") != std::string::npos);
}

#endif // HRSC_ENABLE_PROFILING
