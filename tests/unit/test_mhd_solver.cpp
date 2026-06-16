#include "catch.hpp"
#include "mhd/mhd_solver.hpp"

#include <cmath>

using namespace hrsc;

namespace {

void require_physical_brio_wu_state(GridView<double, MhdNVars> gv, int nx, double gamma,
                                    int step, double time) {
    for (int i = 0; i < nx; ++i) {
        Vec<double, MhdNVars> U{};
        for (int k = 0; k < MhdNVars; ++k) {
            U[k] = gv(i, 0, k);
            CAPTURE(step, time, i, k, U[k]);
            REQUIRE(std::isfinite(U[k]));
        }

        CAPTURE(step, time, i, U[MhdIdx::RHO]);
        REQUIRE(U[MhdIdx::RHO] > 0.0);
        const double p = pressure(U, gamma);
        CAPTURE(step, time, i, p);
        REQUIRE(p > 0.0);
        CAPTURE(step, time, i, U[MhdIdx::BX]);
        REQUIRE(U[MhdIdx::BX] == Approx(0.75).margin(1e-10));
    }
}

} // namespace

TEST_CASE("MHD solver advances Brio-Wu without NaNs and keeps Bx≈const", "[mhd][solver]") {
    MhdSolver<double> solver(64, 1.0/64, 0.0, /*gamma=*/2.0, /*cfl=*/0.4, /*t_end=*/0.02);
    setup_brio_wu(solver.grid_view(), 64, 1.0/64, 0.0, 2.0, 0.5);
    solver.run();
    require_physical_brio_wu_state(solver.grid_view(), 64, 2.0, solver.step_count(), solver.time());
    REQUIRE(solver.time() == Approx(0.02));
}

TEST_CASE("MHD solver keeps Brio-Wu physical at N800 through t=0.06", "[mhd][solver]") {
    constexpr int nx = 800;
    constexpr double dx = 1.0 / nx;

    MhdSolver<double> solver(nx, dx, 0.0, /*gamma=*/2.0, /*cfl=*/0.4, /*t_end=*/0.06);
    setup_brio_wu(solver.grid_view(), nx, dx, 0.0, 2.0, 0.5);
    solver.run();

    require_physical_brio_wu_state(solver.grid_view(), nx, 2.0, solver.step_count(), solver.time());
    REQUIRE(solver.time() == Approx(0.06));
}
