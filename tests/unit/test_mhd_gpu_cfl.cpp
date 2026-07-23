// tests/unit/test_mhd_gpu_cfl.cpp
//
// CUDA-only deterministic CFL reduction tests for MHD.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "gpu/gpu_grid.cuh"
#include "mhd/mhd_flux.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <random>

namespace hrsc {
template <typename Real>
TimeReal compute_dt_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real gamma, Real cfl);
}

using namespace hrsc;

namespace {

bool bit_equal(TimeReal a, TimeReal b) {
    return std::memcmp(&a, &b, sizeof(TimeReal)) == 0;
}

template <typename Real>
void fill_valid_mhd_state(Grid2D<Real, MhdNVars>& grid, std::uint32_t seed) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> rho_dist(0.3, 4.0);
    std::uniform_real_distribution<double> vel_dist(-2.0, 2.0);
    std::uniform_real_distribution<double> b_dist(-0.8, 0.8);
    std::uniform_real_distribution<double> p_dist(0.2, 5.0);
    std::uniform_real_distribution<double> psi_dist(-0.4, 0.4);

    constexpr Real gamma = Real(5) / Real(3);
    auto gv = grid.view();
    for (int j = 0; j < grid.ny; ++j) {
        for (int i = 0; i < grid.nx; ++i) {
            MhdPrim<Real> w{};
            w.rho = static_cast<Real>(rho_dist(rng));
            w.vx = static_cast<Real>(vel_dist(rng));
            w.vy = static_cast<Real>(vel_dist(rng));
            w.vz = static_cast<Real>(vel_dist(rng));
            w.Bx = static_cast<Real>(b_dist(rng));
            w.By = static_cast<Real>(b_dist(rng));
            w.Bz = static_cast<Real>(b_dist(rng));
            w.p = static_cast<Real>(p_dist(rng));
            w.psi = static_cast<Real>(psi_dist(rng));
            const auto U = prim_to_cons(w, gamma);
            for (int v = 0; v < MhdNVars; ++v) {
                gv(i, j, v) = U[v];
            }
        }
    }
}

template <typename Real>
TimeReal compute_dt_cpu_oracle(const Grid2D<Real, MhdNVars>& grid,
                               Real gamma, Real cfl) {
    const auto gv = static_cast<const Grid2D<Real, MhdNVars>&>(grid).view();
    Real ch = Real(0);
    for (int j = 0; j < gv.ny; ++j) {
        for (int i = 0; i < gv.nx; ++i) {
            Vec<Real, MhdNVars> U{};
            for (int v = 0; v < MhdNVars; ++v) {
                U[v] = gv(i, j, v);
            }

            const MhdPrim<Real> w = cons_to_prim(U, gamma);
            ch = std::max(ch, std::abs(w.vx) + fast_speed_x(w, gamma));
            if (gv.ny > 1) {
                ch = std::max(ch, std::abs(w.vy) +
                                      fast_speed_x(mhd_swap_xy_prim(w), gamma));
            }
        }
    }

    const Real denom = std::max(ch, Real(1e-30));
    const Real h = (gv.ny > 1) ? std::min(gv.dx, gv.dy) : gv.dx;
    return static_cast<TimeReal>(cfl) * static_cast<TimeReal>(h) /
           static_cast<TimeReal>(denom);
}

template <typename Real>
void require_gpu_dt_matches_cpu(int nx, int ny, std::uint32_t seed) {
    Grid2D<Real, MhdNVars> host(nx, ny);
    host.dx = static_cast<Real>(0.85) / static_cast<Real>(nx);
    host.dy = static_cast<Real>(1.15) / static_cast<Real>(ny);
    fill_valid_mhd_state(host, seed);

    constexpr Real gamma = Real(5) / Real(3);
    constexpr Real cfl = Real(0.38);
    const TimeReal oracle = compute_dt_cpu_oracle(host, gamma, cfl);

    GpuGrid<Real, MhdNVars> dev(host);
    const TimeReal got = compute_dt_mhd_gpu(dev, gamma, cfl);

    REQUIRE(bit_equal(got, oracle));
}

} // namespace

TEST_CASE("MHD GPU CFL matches CPU oracle bit-exact", "[gpu][mhd][cfl]") {
    require_gpu_dt_matches_cpu<double>(7, 3, 0x4D4801u);
    require_gpu_dt_matches_cpu<double>(257, 129, 0x4D4802u);
    require_gpu_dt_matches_cpu<float>(31, 1, 0x4D4803u);
    require_gpu_dt_matches_cpu<float>(257, 129, 0x4D4804u);
}

TEST_CASE("MHD GPU CFL is run-to-run bit-identical", "[gpu][mhd][cfl]") {
    Grid2D<double, MhdNVars> host(257, 129);
    host.dx = 0.85 / static_cast<double>(host.nx);
    host.dy = 1.15 / static_cast<double>(host.ny);
    fill_valid_mhd_state(host, 0x4D4810u);

    constexpr double gamma = 5.0 / 3.0;
    constexpr double cfl = 0.38;
    GpuGrid<double, MhdNVars> dev(host);

    const TimeReal first = compute_dt_mhd_gpu(dev, gamma, cfl);
    for (int iter = 0; iter < 100; ++iter) {
        const TimeReal got = compute_dt_mhd_gpu(dev, gamma, cfl);
        REQUIRE(bit_equal(got, first));
    }
}

#endif // HRSC_HAS_CUDA
