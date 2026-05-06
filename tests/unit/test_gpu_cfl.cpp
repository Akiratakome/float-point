// tests/unit/test_gpu_cfl.cpp
//
// CUDA-only deterministic CFL reduction tests.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/eos.hpp"
#include "core/grid.hpp"
#include "gpu/euler_kernels.cuh"
#include "gpu/gpu_grid.cuh"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <random>

using namespace hrsc;

namespace {

template <typename Real>
bool bit_equal(TimeReal a, TimeReal b) {
    return std::memcmp(&a, &b, sizeof(TimeReal)) == 0;
}

template <typename Real>
void fill_valid_euler_state(Grid2D<Real, EulerNVars>& grid,
                            std::uint32_t seed) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> rho_dist(0.2, 5.0);
    std::uniform_real_distribution<double> vel_dist(-3.0, 3.0);
    std::uniform_real_distribution<double> p_dist(0.05, 8.0);

    auto gv = grid.view();
    constexpr Real gamma = Real(1.4);
    for (int j = 0; j < grid.ny; ++j) {
        for (int i = 0; i < grid.nx; ++i) {
            Vec<Real, EulerNVars> prim{};
            prim[PRHO] = static_cast<Real>(rho_dist(rng));
            prim[VX] = static_cast<Real>(vel_dist(rng));
            prim[VY] = static_cast<Real>(vel_dist(rng));
            prim[PRES] = static_cast<Real>(p_dist(rng));
            Vec<Real, EulerNVars> cons = prim_to_cons(prim, gamma);
            for (int v = 0; v < EulerNVars; ++v) gv(i, j, v) = cons[v];
        }
    }

    for (auto& x : grid.data) {
        if (x == Real(0)) x = static_cast<Real>(seed % 17 + 1);
    }
}

template <typename Real>
TimeReal compute_dt_cpu_oracle(const Grid2D<Real, EulerNVars>& grid,
                               Real gamma, Real cfl) {
    auto gv = grid.view();
    Real max_Sx = std::numeric_limits<Real>::lowest();
    Real max_Sy = std::numeric_limits<Real>::lowest();

    for (int j = 0; j < gv.ny; ++j) {
        for (int i = 0; i < gv.nx; ++i) {
            Vec<Real, EulerNVars> cons{};
            for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);

            Real rho = cons[RHO];
            Real u = cons[RHOU] / rho;
            Real vel_v = cons[RHOV] / rho;
            Real p = pressure(cons, gamma);
            Real a = sound_speed(rho, p, gamma);

            max_Sx = std::max(max_Sx, std::abs(u) + a);
            max_Sy = std::max(max_Sy, std::abs(vel_v) + a);
        }
    }

    return static_cast<TimeReal>(cfl) *
           std::min(static_cast<TimeReal>(gv.dx) /
                        static_cast<TimeReal>(max_Sx),
                    static_cast<TimeReal>(gv.dy) /
                        static_cast<TimeReal>(max_Sy));
}

template <typename Real>
TimeReal require_gpu_dt_matches_oracle(int nx, int ny, std::uint32_t seed) {
    Grid2D<Real, EulerNVars> host(nx, ny);
    host.dx = static_cast<Real>(0.75) / static_cast<Real>(nx);
    host.dy = static_cast<Real>(1.25) / static_cast<Real>(ny);
    fill_valid_euler_state(host, seed);

    constexpr Real gamma = Real(1.4);
    constexpr Real cfl = Real(0.37);
    const TimeReal oracle = compute_dt_cpu_oracle(host, gamma, cfl);

    GpuGrid<Real, EulerNVars> dev(host);
    const TimeReal got = compute_dt_gpu(dev, gamma, cfl);

    REQUIRE(bit_equal<Real>(got, oracle));
    return got;
}

} // namespace

TEST_CASE("GPU CFL matches CPU oracle bit-exact for double awkward grids",
          "[gpu][cfl]") {
    require_gpu_dt_matches_oracle<double>(7, 3, 0xCF1001u);
    require_gpu_dt_matches_oracle<double>(16, 16, 0xCF1002u);
    require_gpu_dt_matches_oracle<double>(257, 129, 0xCF1003u);
    require_gpu_dt_matches_oracle<double>(1024, 1024, 0xCF1004u);
}

TEST_CASE("GPU CFL is run-to-run bit-identical",
          "[gpu][cfl]") {
    Grid2D<double, EulerNVars> host(257, 129);
    host.dx = 0.75 / static_cast<double>(host.nx);
    host.dy = 1.25 / static_cast<double>(host.ny);
    fill_valid_euler_state(host, 0xCF1100u);

    constexpr double gamma = 1.4;
    constexpr double cfl = 0.37;
    GpuGrid<double, EulerNVars> dev(host);

    const TimeReal first = compute_dt_gpu(dev, gamma, cfl);
    for (int iter = 0; iter < 100; ++iter) {
        const TimeReal got = compute_dt_gpu(dev, gamma, cfl);
        REQUIRE(bit_equal<double>(got, first));
    }
}

TEST_CASE("GPU CFL covers float awkward grids bit-exact to oracle",
          "[gpu][cfl]") {
    require_gpu_dt_matches_oracle<float>(7, 3, 0xCF1201u);
    require_gpu_dt_matches_oracle<float>(257, 129, 0xCF1202u);
}

TEST_CASE("GPU CFL covers non-power-of-two and 1D-ish grids",
          "[gpu][cfl]") {
    require_gpu_dt_matches_oracle<double>(509, 1, 0xCF1301u);
    require_gpu_dt_matches_oracle<float>(31, 1, 0xCF1302u);
}

#endif // HRSC_HAS_CUDA
