// tests/unit/test_mhd_gpu_orszag_tang.cpp
//
// CUDA-only end-to-end Orszag-Tang agreement test for the GPU MHD solver.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "gpu/mhd_gpu_solver.hpp"
#include "mhd/mhd_solver.hpp"

#include <cstring>

using namespace hrsc;

namespace {

template <typename Real>
bool byte_equal(const Grid2D<Real, MhdNVars>& a,
                const Grid2D<Real, MhdNVars>& b) {
    return a.data.size() == b.data.size() &&
           std::memcmp(a.data.data(), b.data.data(),
                       a.data.size() * sizeof(Real)) == 0;
}

template <typename Real>
Grid2D<Real, MhdNVars> make_orszag_tang_host(int nx, int ny, Real dx, Real dy,
                                             Real xmin, Real ymin,
                                             Real gamma) {
    Grid2D<Real, MhdNVars> g(nx, ny);
    g.dx = dx;
    g.dy = dy;
    setup_orszag_tang(g.view(), nx, ny, dx, dy, xmin, ymin, gamma);
    return g;
}

template <typename Real>
Grid2D<Real, MhdNVars> snapshot_cpu_grid(MhdSolver<Real, HllFlux>& solver) {
    auto gv = solver.grid_view();
    Grid2D<Real, MhdNVars> out(gv.nx, gv.ny);
    out.dx = gv.dx;
    out.dy = gv.dy;
    auto ov = out.view();
    constexpr int ng = GridView<Real, MhdNVars>::ng;
    for (int j = -ng; j < gv.ny + ng; ++j) {
        for (int i = -ng; i < gv.nx + ng; ++i) {
            for (int v = 0; v < MhdNVars; ++v) {
                ov(i, j, v) = gv(i, j, v);
            }
        }
    }
    return out;
}

template <typename Real>
void require_orszag_tang_gpu_matches_cpu() {
    constexpr int nx = 16;
    constexpr int ny = 16;
    const Real xmin = Real(0);
    const Real ymin = Real(0);
    const Real dx = Real(1) / static_cast<Real>(nx);
    const Real dy = Real(1) / static_cast<Real>(ny);
    const Real gamma = Real(5) / Real(3);
    const Real cfl = Real(0.4);
    const Real glm_cr = Real(0.18);
    const TimeReal t_end = TimeReal(0.002);

    MhdSolver<Real, HllFlux> cpu(nx, ny, dx, dy, xmin, ymin, gamma, cfl,
                                 t_end, BoundaryType::Periodic,
                                 BoundaryType::Periodic, glm_cr);
    setup_orszag_tang(cpu.grid_view(), nx, ny, dx, dy, xmin, ymin, gamma);
    cpu.run();

    auto host = make_orszag_tang_host(nx, ny, dx, dy, xmin, ymin, gamma);
    MhdGpuSolver<Real> gpu(host, xmin, ymin, gamma, cfl, t_end, glm_cr,
                           BoundaryType::Periodic, BoundaryType::Periodic);
    gpu.run();

    REQUIRE(gpu.step_count() == cpu.step_count());
    REQUIRE(gpu.current_time() == cpu.time());
    REQUIRE(byte_equal(gpu.download_host_grid(), snapshot_cpu_grid(cpu)));
}

} // namespace

TEST_CASE("MHD GPU Orszag-Tang 2D matches CPU HLL end-to-end",
          "[gpu][mhd][orszag-tang]") {
    require_orszag_tang_gpu_matches_cpu<double>();
    require_orszag_tang_gpu_matches_cpu<float>();
}

#endif // HRSC_HAS_CUDA
