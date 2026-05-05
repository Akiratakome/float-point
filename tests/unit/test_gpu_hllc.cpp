// tests/unit/test_gpu_hllc.cpp
//
// CUDA-only HLLC flux and sweep dispatch tests. Direct flux cases compare the
// GPU face launcher against the CPU oracle in src/euler/hllc.hpp; the full-grid
// case checks EulerGpuSolver dispatches FluxScheme::HLLC through both sweeps.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/boundary.hpp"
#include "core/grid.hpp"
#include "core/vec.hpp"
#include "euler/euler_flux.hpp"
#include "euler/euler_solver.hpp"
#include "euler/hllc.hpp"
#include "gpu/cuda_utils.cuh"
#include "gpu/euler_gpu_solver.hpp"
#include "gpu/euler_kernels.cuh"
#include "../cases/liska_wendroff_2d/lw_tests.hpp"

#include <cstring>
#include <utility>
#include <vector>

using namespace hrsc;

namespace {

template <typename Real>
Vec<Real, EulerNVars> make_state(Real rho, Real u, Real v, Real p, Real gamma) {
    Vec<Real, EulerNVars> q{};
    q[RHO]  = rho;
    q[RHOU] = rho * u;
    q[RHOV] = rho * v;
    q[EN]   = p / (gamma - Real(1)) + Real(0.5) * rho * (u * u + v * v);
    return q;
}

template <typename Real>
bool buffer_byte_equal(const std::vector<Vec<Real, EulerNVars>>& a,
                       const std::vector<Vec<Real, EulerNVars>>& b) {
    return a.size() == b.size() &&
           std::memcmp(a.data(), b.data(),
                       a.size() * sizeof(Vec<Real, EulerNVars>)) == 0;
}

template <typename Real>
bool grid_byte_equal(const Grid2D<Real, EulerNVars>& a,
                     const Grid2D<Real, EulerNVars>& b) {
    return a.data.size() == b.data.size() &&
           std::memcmp(a.data.data(), b.data.data(),
                       a.data.size() * sizeof(Real)) == 0;
}

template <typename Real>
void require_hllc_x_face_matches_cpu(const Vec<Real, EulerNVars>& qL,
                                     const Vec<Real, EulerNVars>& qR) {
    const Real gamma = Real(1.4);
    std::vector<Vec<Real, EulerNVars>> left{qL};
    std::vector<Vec<Real, EulerNVars>> right{qR};
    std::vector<Vec<Real, EulerNVars>> oracle{
        hllc_flux<Real>(qL, qR, gamma)};

    DeviceArray<Vec<Real, EulerNVars>> dev_left(left.size());
    DeviceArray<Vec<Real, EulerNVars>> dev_right(right.size());
    DeviceArray<Vec<Real, EulerNVars>> dev_flux(left.size());
    dev_left.copy_from_host(left.data(), left.size());
    dev_right.copy_from_host(right.data(), right.size());

    hllc_flux_x_gpu<Real>(0, 1, gamma, dev_left.data(), dev_right.data(),
                          dev_flux.data());

    std::vector<Vec<Real, EulerNVars>> got(left.size());
    dev_flux.copy_to_host(got.data(), got.size());
    REQUIRE(buffer_byte_equal(got, oracle));
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

template <typename Real>
void require_lw_config3_hllc_one_step_matches_cpu() {
    const int nx = 16, ny = 16;
    const Real dx = Real(1) / static_cast<Real>(nx);
    const Real dy = Real(1) / static_cast<Real>(ny);
    const Real gamma = Real(1.4);
    const Real cfl = Real(0.4);
    const TimeReal t_end = TimeReal(0.3);

    EulerSolver<Real> cpu(nx, ny, dx, dy, Real(0), Real(0),
                          gamma, cfl, t_end, FluxScheme::HLLC,
                          BoundaryType::Outflow, BoundaryType::Outflow);
    setup_liska_wendroff_config3<Real>(cpu.grid_view(), gamma);

    Grid2D<Real, EulerNVars> ic_grid(nx, ny);
    ic_grid.dx = dx;
    ic_grid.dy = dy;
    setup_liska_wendroff_config3<Real>(ic_grid.view(), gamma);
    EulerGpuSolver<Real> gpu(std::move(ic_grid),
                             Real(0), Real(0), gamma, cfl, t_end,
                             FluxScheme::HLLC,
                             BoundaryType::Outflow,
                             BoundaryType::Outflow);

    const TimeReal t_before = cpu.time();
    cpu.step();
    const TimeReal dt = cpu.time() - t_before;
    REQUIRE(dt > TimeReal(0));
    gpu.step(dt);

    const auto cpu_snap = snapshot_cpu_grid<Real>(cpu, nx, ny, dx, dy);
    const auto gpu_snap = gpu.download_host_grid();
    REQUIRE(grid_byte_equal(cpu_snap, gpu_snap));
}

} // namespace

TEST_CASE("GPU HLLC flux is bit-exact on a generic subsonic face",
          "[gpu][hllc]") {
    auto run = [](auto real_tag) {
        using Real = decltype(real_tag);
        const Real gamma = Real(1.4);
        require_hllc_x_face_matches_cpu<Real>(
            make_state<Real>(Real(1.0), Real(0.35), Real(0.05), Real(1.0),
                             gamma),
            make_state<Real>(Real(0.72), Real(-0.18), Real(-0.03), Real(0.65),
                             gamma));
    };
    run(double{});
    run(float{});
}

TEST_CASE("GPU HLLC flux is bit-exact at a sonic-ish face",
          "[gpu][hllc]") {
    auto run = [](auto real_tag) {
        using Real = decltype(real_tag);
        const Real gamma = Real(1.4);
        require_hllc_x_face_matches_cpu<Real>(
            make_state<Real>(Real(1.0), Real(1.183216), Real(0.02), Real(1.0),
                             gamma),
            make_state<Real>(Real(0.85), Real(0.65), Real(-0.04), Real(0.55),
                             gamma));
    };
    run(double{});
    run(float{});
}

TEST_CASE("GPU HLLC flux is bit-exact at stationary contact Sstar zero",
          "[gpu][hllc]") {
    auto run = [](auto real_tag) {
        using Real = decltype(real_tag);
        const Real gamma = Real(1.4);
        require_hllc_x_face_matches_cpu<Real>(
            make_state<Real>(Real(1.0), Real(0.0), Real(0.0), Real(1.0),
                             gamma),
            make_state<Real>(Real(0.125), Real(0.0), Real(0.0), Real(1.0),
                             gamma));
    };
    run(double{});
    run(float{});
}

TEST_CASE("GPU HLLC flux is bit-exact when SL and SR are positive",
          "[gpu][hllc]") {
    auto run = [](auto real_tag) {
        using Real = decltype(real_tag);
        const Real gamma = Real(1.4);
        require_hllc_x_face_matches_cpu<Real>(
            make_state<Real>(Real(1.0), Real(3.0), Real(0.12), Real(0.4),
                             gamma),
            make_state<Real>(Real(0.9), Real(2.7), Real(-0.08), Real(0.35),
                             gamma));
    };
    run(double{});
    run(float{});
}

TEST_CASE("EulerGpuSolver HLLC LW Config 3 16x16 one-step matches CPU",
          "[gpu][hllc]") {
    require_lw_config3_hllc_one_step_matches_cpu<double>();
    require_lw_config3_hllc_one_step_matches_cpu<float>();
}

#endif // HRSC_HAS_CUDA
