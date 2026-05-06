// tests/unit/test_gpu_update.cpp
//
// CUDA-only bit-exact oracle tests for the GPU conservative-update kernel.
// Compares the post-update interior data of GpuGrid against the CPU oracle
// in src/euler/euler_solver.cpp (x_sweep / y_sweep update blocks) using
// std::memcmp under strict-IEEE (--fmad=false is set on euler_kernels.cu).

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/boundary.hpp"
#include "core/grid.hpp"
#include "core/vec.hpp"
#include "gpu/cuda_utils.cuh"
#include "gpu/euler_kernels.cuh"
#include "gpu/gpu_grid.cuh"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <random>
#include <vector>

using namespace hrsc;

namespace {

template <typename Real>
void fill_random_state(Grid2D<Real, EulerNVars>& grid, std::uint32_t seed) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> dist(-1.0, 1.0);
    for (auto& x : grid.data) {
        x = static_cast<Real>(dist(rng));
    }
}

template <typename Real>
std::vector<Vec<Real, EulerNVars>> make_synthetic_flux(
    int n_interfaces, int n_lines, std::uint32_t seed) {
    std::vector<Vec<Real, EulerNVars>> flux(
        static_cast<std::size_t>(n_interfaces) * n_lines);
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> dist(-2.0, 2.0);
    for (auto& f : flux) {
        for (int v = 0; v < EulerNVars; ++v) {
            f[v] = static_cast<Real>(dist(rng));
        }
    }
    return flux;
}

// CPU oracle for X-update; mirrors the expression in src/euler/euler_solver.cpp
// x_sweep update block (line ~123). Per-row flux layout: flux_x[j*(nx+1) + k].
template <typename Real>
void cpu_apply_update_x(Grid2D<Real, EulerNVars>& host,
                        const std::vector<Vec<Real, EulerNVars>>& flux_x,
                        Real dt) {
    auto gv = host.view();
    const Real dtdx = dt / gv.dx;
    for (int j = 0; j < gv.ny; ++j) {
        for (int i = 0; i < gv.nx; ++i) {
            const auto f_prev = flux_x[j * (gv.nx + 1) + i];
            const auto f_next = flux_x[j * (gv.nx + 1) + (i + 1)];
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) -= dtdx * (f_next[v] - f_prev[v]);
            }
        }
    }
}

// CPU oracle for Y-update; mirrors src/euler/euler_solver.cpp y_sweep update
// block (line ~211). Per-column flux layout: flux_y[i*(ny+1) + k].
template <typename Real>
void cpu_apply_update_y(Grid2D<Real, EulerNVars>& host,
                        const std::vector<Vec<Real, EulerNVars>>& flux_y,
                        Real dt) {
    auto gv = host.view();
    const Real dtdy = dt / gv.dy;
    for (int i = 0; i < gv.nx; ++i) {
        for (int j = 0; j < gv.ny; ++j) {
            const auto f_prev = flux_y[i * (gv.ny + 1) + j];
            const auto f_next = flux_y[i * (gv.ny + 1) + (j + 1)];
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) -= dtdy * (f_next[v] - f_prev[v]);
            }
        }
    }
}

template <typename Real>
bool byte_equal(const Grid2D<Real, EulerNVars>& a,
                const Grid2D<Real, EulerNVars>& b) {
    return a.data.size() == b.data.size() &&
           std::memcmp(a.data.data(), b.data.data(),
                       a.data.size() * sizeof(Real)) == 0;
}

template <typename Real>
Grid2D<Real, EulerNVars> make_grid(int nx, int ny) {
    Grid2D<Real, EulerNVars> g(nx, ny);
    g.dx = Real(1) / static_cast<Real>(nx);
    g.dy = Real(1) / static_cast<Real>(ny);
    return g;
}

template <typename Real>
void require_gpu_update_x_matches_cpu(int nx, int ny, std::uint32_t seed) {
    auto host = make_grid<Real>(nx, ny);
    fill_random_state(host, seed);
    auto flux_x = make_synthetic_flux<Real>(nx + 1, ny, seed ^ 0xF1u);
    const Real dt = Real(0.001);

    auto oracle = host;
    cpu_apply_update_x<Real>(oracle, flux_x, dt);

    GpuGrid<Real, EulerNVars> dev(host);
    DeviceArray<Vec<Real, EulerNVars>> dev_flux(flux_x.size());
    dev_flux.copy_from_host(flux_x.data(), flux_x.size());
    apply_update_x_gpu<Real>(dev, dev_flux.data(), dt);

    auto got = make_grid<Real>(nx, ny);
    dev.download_to(got);

    REQUIRE(byte_equal(got, oracle));
}

template <typename Real>
void require_gpu_update_y_matches_cpu(int nx, int ny, std::uint32_t seed) {
    auto host = make_grid<Real>(nx, ny);
    fill_random_state(host, seed);
    auto flux_y = make_synthetic_flux<Real>(ny + 1, nx, seed ^ 0xF2u);
    const Real dt = Real(0.001);

    auto oracle = host;
    cpu_apply_update_y<Real>(oracle, flux_y, dt);

    GpuGrid<Real, EulerNVars> dev(host);
    DeviceArray<Vec<Real, EulerNVars>> dev_flux(flux_y.size());
    dev_flux.copy_from_host(flux_y.data(), flux_y.size());
    apply_update_y_gpu<Real>(dev, dev_flux.data(), dt);

    auto got = make_grid<Real>(nx, ny);
    dev.download_to(got);

    REQUIRE(byte_equal(got, oracle));
}

} // namespace

// Case 1: small synthetic grid (4x4) with deterministic flux input. Validates
// the basic single-axis update expression on a non-trivial grid in both X and
// Y. Exercises the per-cell stride and the (nx+1)*ny / nx*(ny+1) flux layout.
TEST_CASE("GPU conservative update is bit-exact for synthetic flux input",
          "[gpu][update]") {
    require_gpu_update_x_matches_cpu<double>(4, 4, 0x14000001u);
    require_gpu_update_x_matches_cpu<float>(4, 4, 0x14000002u);
    require_gpu_update_y_matches_cpu<double>(4, 4, 0x14000003u);
    require_gpu_update_y_matches_cpu<float>(4, 4, 0x14000004u);
}

// Case 2: BC-then-update on a 16x16 grid. Apply outflow BCs to both grids
// (reuses T6 kernels), then perform the update. Confirms ghost cells set by
// the BC stage are not disturbed by the update kernel and that the interior
// matches the CPU result bit-exactly.
TEST_CASE("GPU update matches CPU after outflow BC application",
          "[gpu][update]") {
    auto run = [](auto real_tag, std::uint32_t seed) {
        using Real = decltype(real_tag);
        const int nx = 16, ny = 16;
        auto host = make_grid<Real>(nx, ny);
        fill_random_state(host, seed);

        auto flux_x = make_synthetic_flux<Real>(nx + 1, ny, seed ^ 0xBC1u);
        const Real dt = Real(0.001);

        // Apply BC on CPU, then update.
        auto oracle = host;
        apply_outflow_bc(oracle.view(), Axis::X);
        apply_outflow_bc(oracle.view(), Axis::Y);
        cpu_apply_update_x<Real>(oracle, flux_x, dt);

        // Apply BC on GPU, then update.
        GpuGrid<Real, EulerNVars> dev(host);
        apply_outflow_bc_gpu<Real>(dev, Axis::X);
        apply_outflow_bc_gpu<Real>(dev, Axis::Y);
        DeviceArray<Vec<Real, EulerNVars>> dev_flux(flux_x.size());
        dev_flux.copy_from_host(flux_x.data(), flux_x.size());
        apply_update_x_gpu<Real>(dev, dev_flux.data(), dt);

        auto got = make_grid<Real>(nx, ny);
        dev.download_to(got);
        REQUIRE(byte_equal(got, oracle));
    };
    run(double{}, 0x14000010u);
    run(float{},  0x14000011u);
}

// Case 3: Lie-splitting half-step on a 33x17 (non-power-of-two) grid. Apply
// X-update then Y-update sequentially with independent flux buffers; confirms
// compositional bit-exactness across both axes and the non-pow2 boundary.
TEST_CASE("GPU update is bit-exact across composed X-then-Y Lie split",
          "[gpu][update]") {
    auto run = [](auto real_tag, std::uint32_t seed) {
        using Real = decltype(real_tag);
        const int nx = 33, ny = 17;
        auto host = make_grid<Real>(nx, ny);
        fill_random_state(host, seed);

        auto flux_x = make_synthetic_flux<Real>(nx + 1, ny, seed ^ 0xC1u);
        auto flux_y = make_synthetic_flux<Real>(ny + 1, nx, seed ^ 0xC2u);
        const Real dt = Real(0.001);

        auto oracle = host;
        cpu_apply_update_x<Real>(oracle, flux_x, dt);
        cpu_apply_update_y<Real>(oracle, flux_y, dt);

        GpuGrid<Real, EulerNVars> dev(host);
        DeviceArray<Vec<Real, EulerNVars>> dev_fx(flux_x.size());
        dev_fx.copy_from_host(flux_x.data(), flux_x.size());
        apply_update_x_gpu<Real>(dev, dev_fx.data(), dt);

        DeviceArray<Vec<Real, EulerNVars>> dev_fy(flux_y.size());
        dev_fy.copy_from_host(flux_y.data(), flux_y.size());
        apply_update_y_gpu<Real>(dev, dev_fy.data(), dt);

        auto got = make_grid<Real>(nx, ny);
        dev.download_to(got);
        REQUIRE(byte_equal(got, oracle));
    };
    run(double{}, 0x14000020u);
    run(float{},  0x14000021u);
}

#endif // HRSC_HAS_CUDA
