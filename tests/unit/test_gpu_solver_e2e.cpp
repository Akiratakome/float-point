// tests/unit/test_gpu_solver_e2e.cpp
//
// End-to-end bit-exact regression tests for EulerGpuSolver: build a CPU
// solver and a GPU solver from the same IC, run identical steps on both,
// and require the post-step grids to be byte-identical (memcmp).
// Cases:
//   1. Sod 1D, 1 step
//   2. Sod 1D, 10 steps
//   3. LW Config 3, n=64, 5 steps
//   4. LW Config 3, n=200, 1 step

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/grid.hpp"
#include "euler/euler_solver.hpp"
#include "gpu/euler_gpu_solver.hpp"
#include "../cases/toro_1d/toro_tests.hpp"
#include "../cases/liska_wendroff_2d/lw_tests.hpp"

#include <cmath>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <type_traits>
#include <utility>

using namespace hrsc;

namespace {

template <typename Real>
bool grid_byte_equal(const Grid2D<Real, EulerNVars>& a,
                     const Grid2D<Real, EulerNVars>& b) {
    return a.data.size() == b.data.size() &&
           std::memcmp(a.data.data(), b.data.data(),
                       a.data.size() * sizeof(Real)) == 0;
}

// Design §4.5 gate:
//   ||cpu - gpu||_inf <= 16 * eps * ||cpu||_inf
// This is a global Linf relative-to-scale gate, not a per-value ULP-distance
// test; the latter over-weights components whose exact value is near zero.
template <typename Real>
double interior_linf_ulp_ratio(const Grid2D<Real, EulerNVars>& a,
                               const Grid2D<Real, EulerNVars>& b) {
    constexpr int ng = Grid2D<Real, EulerNVars>::ng;
    double linf_diff = 0.0;
    double linf_ref = 0.0;
    const int nx_total = a.nx + 2 * ng;
    for (int j = 0; j < a.ny; ++j) {
        for (int i = 0; i < a.nx; ++i) {
            for (int v = 0; v < EulerNVars; ++v) {
                const std::size_t idx =
                    ((j + ng) * nx_total + (i + ng)) * EulerNVars + v;
                Real av = a.data[idx];
                Real bv = b.data[idx];
                if (!std::isfinite(av) || !std::isfinite(bv)) {
                    return std::numeric_limits<double>::infinity();
                }
                const double da = std::abs(static_cast<double>(av));
                const double dd = std::abs(static_cast<double>(av - bv));
                if (da > linf_ref) linf_ref = da;
                if (dd > linf_diff) linf_diff = dd;
            }
        }
    }
    if (linf_ref == 0.0) {
        return linf_diff == 0.0 ? 0.0 : std::numeric_limits<double>::infinity();
    }
    return linf_diff / (std::numeric_limits<Real>::epsilon() * linf_ref);
}

template <typename Real>
Grid2D<Real, EulerNVars> snapshot_cpu_grid(EulerSolver<Real>& cpu,
                                           int nx, int ny, Real dx, Real dy) {
    Grid2D<Real, EulerNVars> snap(nx, ny);
    snap.dx = dx;
    snap.dy = dy;
    std::memcpy(snap.data.data(), cpu.grid_view().data,
                snap.data.size() * sizeof(Real));
    return snap;
}

// Run N steps on both solvers using the CPU's dt sequence (CPU::step
// computes dt internally; GPU::step takes explicit dt). dt is bit-exact
// between CPU and GPU at each step because compute_dt_gpu mirrors the CPU
// CFL reduction, but feeding GPU the CPU dt avoids re-running CFL on GPU
// and locks the dt sequence to a single source.
template <typename Real>
void run_n_steps_locked(EulerSolver<Real>& cpu,
                        EulerGpuSolver<Real>& gpu, int n_steps) {
    for (int s = 0; s < n_steps; ++s) {
        const TimeReal t_before = cpu.time();
        cpu.step();
        const TimeReal dt = cpu.time() - t_before;
        if (dt <= TimeReal(0)) break;
        gpu.step(dt);
    }
}

} // namespace

TEST_CASE("EulerGpuSolver Sod 1D 1-step bit-exact to CPU",
          "[gpu][e2e]") {
    auto body = [](auto real_tag) {
        using Real = decltype(real_tag);
        const int nx = 200;
        const Real dx = Real(1) / static_cast<Real>(nx);
        const Real gamma = Real(1.4);
        const Real cfl = Real(0.5);
        const TimeReal t_end = TimeReal(0.25);

        EulerSolver<Real> cpu(nx, dx, Real(0), gamma, cfl, t_end,
                              FluxScheme::Rusanov,
                              BoundaryType::Outflow, BoundaryType::Outflow);
        setup_sod<Real>(cpu.grid_view(), gamma);

        Grid2D<Real, EulerNVars> ic_grid(nx, 1);
        ic_grid.dx = dx;
        ic_grid.dy = dx;
        setup_sod<Real>(ic_grid.view(), gamma);
        EulerGpuSolver<Real> gpu(std::move(ic_grid),
                                 Real(0), Real(0), gamma, cfl, t_end,
                                 FluxScheme::Rusanov,
                                 BoundaryType::Outflow,
                                 BoundaryType::Outflow);

        run_n_steps_locked<Real>(cpu, gpu, 1);

        const auto cpu_snap = snapshot_cpu_grid<Real>(cpu, nx, 1, dx, dx);
        const auto gpu_snap = gpu.download_host_grid();
        REQUIRE(grid_byte_equal(cpu_snap, gpu_snap));
    };
    body(double{});
    body(float{});
}

TEST_CASE("EulerGpuSolver Sod 1D 10-step within 16 scaled ULP of CPU",
          "[gpu][e2e]") {
    // Task 18 / design §4.5 requires the general CPU-vs-GPU e2e tolerance
    // to stay within 16 ULP.
    auto body = [](auto real_tag) {
        using Real = decltype(real_tag);
        const int nx = 200;
        const Real dx = Real(1) / static_cast<Real>(nx);
        const Real gamma = Real(1.4);
        const Real cfl = Real(0.5);
        const TimeReal t_end = TimeReal(0.25);

        EulerSolver<Real> cpu(nx, dx, Real(0), gamma, cfl, t_end,
                              FluxScheme::Rusanov,
                              BoundaryType::Outflow, BoundaryType::Outflow);
        setup_sod<Real>(cpu.grid_view(), gamma);

        Grid2D<Real, EulerNVars> ic_grid(nx, 1);
        ic_grid.dx = dx;
        ic_grid.dy = dx;
        setup_sod<Real>(ic_grid.view(), gamma);
        EulerGpuSolver<Real> gpu(std::move(ic_grid),
                                 Real(0), Real(0), gamma, cfl, t_end,
                                 FluxScheme::Rusanov,
                                 BoundaryType::Outflow,
                                 BoundaryType::Outflow);

        run_n_steps_locked<Real>(cpu, gpu, 10);

        const auto cpu_snap = snapshot_cpu_grid<Real>(cpu, nx, 1, dx, dx);
        const auto gpu_snap = gpu.download_host_grid();
        const double ratio = interior_linf_ulp_ratio<Real>(cpu_snap, gpu_snap);
        CAPTURE(ratio);
        REQUIRE(ratio <= 16.0);
    };
    body(double{});
    body(float{});
}

TEST_CASE("EulerGpuSolver LW Config 3 n=64 5-step within 16 scaled ULP of CPU",
          "[gpu][e2e]") {
    // Task 18 / design §4.5 requires the general CPU-vs-GPU e2e tolerance
    // to stay within 16 ULP.
    auto body = [](auto real_tag) {
        using Real = decltype(real_tag);
        const int nx = 64, ny = 64;
        const Real dx = Real(1) / static_cast<Real>(nx);
        const Real dy = Real(1) / static_cast<Real>(ny);
        const Real gamma = Real(1.4);
        const Real cfl = Real(0.4);
        const TimeReal t_end = TimeReal(0.3);

        EulerSolver<Real> cpu(nx, ny, dx, dy, Real(0), Real(0),
                              gamma, cfl, t_end,
                              FluxScheme::Rusanov,
                              BoundaryType::Outflow, BoundaryType::Outflow);
        setup_liska_wendroff_config3<Real>(cpu.grid_view(), gamma);

        Grid2D<Real, EulerNVars> ic_grid(nx, ny);
        ic_grid.dx = dx;
        ic_grid.dy = dy;
        setup_liska_wendroff_config3<Real>(ic_grid.view(), gamma);
        EulerGpuSolver<Real> gpu(std::move(ic_grid),
                                 Real(0), Real(0), gamma, cfl, t_end,
                                 FluxScheme::Rusanov,
                                 BoundaryType::Outflow,
                                 BoundaryType::Outflow);

        run_n_steps_locked<Real>(cpu, gpu, 5);

        const auto cpu_snap = snapshot_cpu_grid<Real>(cpu, nx, ny, dx, dy);
        const auto gpu_snap = gpu.download_host_grid();
        const double ratio = interior_linf_ulp_ratio<Real>(cpu_snap, gpu_snap);
        CAPTURE(ratio);
        REQUIRE(ratio <= 16.0);
    };
    body(double{});
    body(float{});
}

TEST_CASE("EulerGpuSolver LW Config 3 n=200 1-step bit-exact to CPU",
          "[gpu][e2e]") {
    auto body = [](auto real_tag) {
        using Real = decltype(real_tag);
        const int nx = 200, ny = 200;
        const Real dx = Real(1) / static_cast<Real>(nx);
        const Real dy = Real(1) / static_cast<Real>(ny);
        const Real gamma = Real(1.4);
        const Real cfl = Real(0.4);
        const TimeReal t_end = TimeReal(0.3);

        EulerSolver<Real> cpu(nx, ny, dx, dy, Real(0), Real(0),
                              gamma, cfl, t_end,
                              FluxScheme::Rusanov,
                              BoundaryType::Outflow, BoundaryType::Outflow);
        setup_liska_wendroff_config3<Real>(cpu.grid_view(), gamma);

        Grid2D<Real, EulerNVars> ic_grid(nx, ny);
        ic_grid.dx = dx;
        ic_grid.dy = dy;
        setup_liska_wendroff_config3<Real>(ic_grid.view(), gamma);
        EulerGpuSolver<Real> gpu(std::move(ic_grid),
                                 Real(0), Real(0), gamma, cfl, t_end,
                                 FluxScheme::Rusanov,
                                 BoundaryType::Outflow,
                                 BoundaryType::Outflow);

        run_n_steps_locked<Real>(cpu, gpu, 1);

        const auto cpu_snap = snapshot_cpu_grid<Real>(cpu, nx, ny, dx, dy);
        const auto gpu_snap = gpu.download_host_grid();
        REQUIRE(grid_byte_equal(cpu_snap, gpu_snap));
    };
    body(double{});
    body(float{});
}

#endif // HRSC_HAS_CUDA
