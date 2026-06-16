#include "catch.hpp"
#include "mhd/mhd_solver.hpp"

#include <cmath>

using namespace hrsc;

TEST_CASE("MHD solver advances Brio-Wu without NaNs and keeps Bx≈const", "[mhd][solver]") {
    MhdSolver<double> solver(64, 1.0/64, 0.0, /*gamma=*/2.0, /*cfl=*/0.4, /*t_end=*/0.02);
    setup_brio_wu(solver.grid_view(), 64, 1.0/64, 0.0, 2.0, 0.5);
    solver.run();
    auto gv = solver.grid_view();
    for (int i = 0; i < 64; ++i) {
        REQUIRE(std::isfinite(gv(i, 0, MhdIdx::RHO)));
        REQUIRE(gv(i, 0, MhdIdx::BX) == Approx(0.75).margin(1e-10));
    }
    REQUIRE(solver.time() == Approx(0.02));
}
