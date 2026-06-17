#include "catch.hpp"
#include "mhd/mhd_solver.hpp"

#include <cmath>
#include <stdexcept>

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

TEST_CASE("MHD solver keeps Brio-Wu physical at N800 through t=0.1", "[mhd][solver]") {
    constexpr int nx = 800;
    constexpr double dx = 1.0 / nx;

    MhdSolver<double> solver(nx, dx, 0.0, /*gamma=*/2.0, /*cfl=*/0.4, /*t_end=*/0.1);
    setup_brio_wu(solver.grid_view(), nx, dx, 0.0, 2.0, 0.5);
    solver.run();

    require_physical_brio_wu_state(solver.grid_view(), nx, 2.0, solver.step_count(), solver.time());
    REQUIRE(solver.time() == Approx(0.1));
}

TEST_CASE("MHD solver rejects unsupported Periodic boundary conditions", "[mhd][solver]") {
    MhdSolver<double> solver(16, 1.0/16, 0.0, 2.0, 0.4, 0.01, BoundaryType::Periodic);
    setup_brio_wu(solver.grid_view(), 16, 1.0/16, 0.0, 2.0, 0.5);

    REQUIRE_THROWS_AS(solver.step(), std::logic_error);
}

TEST_CASE("MHD solver rejects unsupported Reflective boundary conditions", "[mhd][solver]") {
    MhdSolver<double> solver(16, 1.0/16, 0.0, 2.0, 0.4, 0.01, BoundaryType::Reflective);
    setup_brio_wu(solver.grid_view(), 16, 1.0/16, 0.0, 2.0, 0.5);

    REQUIRE_THROWS_AS(solver.run(), std::logic_error);
}

TEST_CASE("MHD solver evolves Bx/psi instead of clamping GLM variables", "[mhd][solver]") {
    constexpr int nx = 32;
    constexpr double dx = 1.0 / nx;
    MhdSolver<double> solver(nx, dx, 0.0, /*gamma=*/2.0, /*cfl=*/0.1, /*t_end=*/0.001);
    auto gv = solver.grid_view();

    for (int i = 0; i < nx; ++i) {
        const double x = (i + 0.5) * dx;
        MhdPrim<double> w{};
        w.rho = 1.0;
        w.vx = 0.0;
        w.vy = 0.0;
        w.vz = 0.0;
        w.Bx = 0.6 + 0.05 * std::sin(2.0 * 3.14159265358979323846 * x);
        w.By = 0.0;
        w.Bz = 0.0;
        w.p = 1.0;
        w.psi = 0.0;
        const Vec<double, MhdNVars> U = prim_to_cons(w, 2.0);
        for (int k = 0; k < MhdNVars; ++k) {
            gv(i, 0, k) = U[k];
        }
    }

    solver.step();

    double max_abs_psi = 0.0;
    double max_bx_delta = 0.0;
    for (int i = 0; i < nx; ++i) {
        const double x = (i + 0.5) * dx;
        const double initial_bx = 0.6 + 0.05 * std::sin(2.0 * 3.14159265358979323846 * x);
        max_abs_psi = std::max(max_abs_psi, std::abs(gv(i, 0, MhdIdx::PSI)));
        max_bx_delta = std::max(max_bx_delta, std::abs(gv(i, 0, MhdIdx::BX) - initial_bx));
    }

    REQUIRE(max_abs_psi > 1e-8);
    REQUIRE(max_bx_delta > 1e-8);
}
