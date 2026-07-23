// tests/unit/test_mhd_gpu_roundtrip.cpp
//
// CUDA-enabled MHD solver host/device residency checks.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#define private public
#include "gpu/mhd_gpu_solver.hpp"
#undef private
#include "mhd/mhd_state.hpp"

extern "C" void launch_layout_writer(double* dev, int nx_total, int ny_total,
                                      int nvars, double base);

namespace {

template <typename Real>
void fill_distinct_mhd_grid(hrsc::Grid2D<Real, hrsc::MhdNVars>& grid) {
    for (int j = -grid.ng; j < grid.ny + grid.ng; ++j) {
        for (int i = -grid.ng; i < grid.nx + grid.ng; ++i) {
            for (int v = 0; v < hrsc::MhdNVars; ++v) {
                grid.view()(i, j, v) =
                    static_cast<Real>(1000 + 100 * (j + grid.ng) +
                                      10 * (i + grid.ng) + v);
            }
        }
    }
}

} // namespace

TEST_CASE("MHD GPU host-device roundtrip preserves all nine variables",
          "[gpu][mhd]") {
    using Real = double;

    hrsc::Grid2D<Real, hrsc::MhdNVars> grid(8, 4);
    grid.dx = Real(0.125);
    grid.dy = Real(0.25);
    fill_distinct_mhd_grid(grid);

    hrsc::MhdGpuSolver<Real> solver(
        grid, Real(0), Real(0), Real(5.0 / 3.0), Real(0.4),
        hrsc::TimeReal(0), Real(0.18),
        hrsc::BoundaryType::Outflow, hrsc::BoundaryType::Outflow);

    constexpr double base = -42.25;
    launch_layout_writer(solver.m_dev_grid.data(),
                         grid.nx + 2 * grid.ng,
                         grid.ny + 2 * grid.ng,
                         hrsc::MhdNVars,
                         base);

    const auto back = solver.download_host_grid();
    for (int j = -grid.ng; j < grid.ny + grid.ng; ++j) {
        for (int i = -grid.ng; i < grid.nx + grid.ng; ++i) {
            for (int v = 0; v < hrsc::MhdNVars; ++v) {
                const auto expected =
                    static_cast<Real>(base + (i + grid.ng) * 1000 +
                                      (j + grid.ng) * 10 + v);
                REQUIRE(back.view()(i, j, v) == expected);
            }
        }
    }
}

#endif // HRSC_HAS_CUDA
