// tests/unit/test_gpu_hancock.cpp
//
// CUDA-only bit-exact oracle tests for the GPU MUSCL-Hancock predictor.
// Compares per-cell qL/qR (X-axis) and q_bottom/q_top (Y-axis) buffers
// produced by the GPU kernel against the CPU oracle in src/euler/hancock.hpp
// using std::memcmp under strict-IEEE.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/eos.hpp"
#include "core/grid.hpp"
#include "core/vec.hpp"
#include "euler/hancock.hpp"
#include "gpu/cuda_utils.cuh"
#include "gpu/euler_kernels.cuh"
#include "gpu/gpu_grid.cuh"

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <random>
#include <vector>

using namespace hrsc;

namespace {

// Fill with constants (per-variable) so the slope-limiter returns 0 and
// the Hancock half-step contributes zero (qL == qR == cell value).
template <typename Real>
void fill_constant(Grid2D<Real, EulerNVars>& grid) {
    // Use physically valid Euler conserved state so the EOS pressure is
    // positive (Case 1's trivial test must still represent a valid state).
    // {rho, rho*u, rho*v, E} with u=0.1, v=-0.05, p=1.0, gamma=1.4.
    const Real values[EulerNVars] = {
        Real(1.25), Real(0.125), Real(-0.0625), Real(2.5078125)
    };
    const int nx_total = grid.nx + 2 * Grid2D<Real, EulerNVars>::ng;
    const int ny_total = grid.ny + 2 * Grid2D<Real, EulerNVars>::ng;
    for (int j = 0; j < ny_total; ++j) {
        for (int i = 0; i < nx_total; ++i) {
            for (int v = 0; v < EulerNVars; ++v) {
                grid.data[(j * nx_total + i) * EulerNVars + v] = values[v];
            }
        }
    }
}

// Build a 2D state spanning subsonic, supersonic and (near-)sonic regimes.
// Density and pressure vary smoothly; momentum varies so |u| sweeps from
// near zero up past the local sound speed. This produces non-trivial slopes
// in BOTH x and y, and ensures the test crosses |M|=1 somewhere.
template <typename Real>
void fill_sub_super_sonic_2d(Grid2D<Real, EulerNVars>& grid) {
    const int ng = Grid2D<Real, EulerNVars>::ng;
    const int nx_total = grid.nx + 2 * ng;
    const int ny_total = grid.ny + 2 * ng;
    const Real gamma = Real(1.4);
    for (int j = 0; j < ny_total; ++j) {
        for (int i = 0; i < nx_total; ++i) {
            const int ic = i - ng;
            const int jc = j - ng;
            // Smoothly varying density 0.6..1.6, pressure 0.5..1.5.
            const Real fx = static_cast<Real>(ic) /
                            static_cast<Real>(grid.nx);
            const Real fy = static_cast<Real>(jc) /
                            static_cast<Real>(grid.ny);
            const Real rho = Real(0.6) + Real(1.0) * (fx + Real(1)) *
                                              Real(0.5);
            const Real p   = Real(0.5) + Real(1.0) * (fy + Real(1)) *
                                              Real(0.5);
            // Velocity sweeps from 0 to ~3 across the grid: at gamma=1.4,
            // local sound speed ~ sqrt(1.4 * p / rho) is O(1), so |u|
            // straddles the sonic point.
            const Real u = Real(3) * fx;
            const Real v = Real(2) * fy - Real(1);
            const Real ke = Real(0.5) * rho * (u * u + v * v);
            const Real E  = p / (gamma - Real(1)) + ke;
            grid.data[(j * nx_total + i) * EulerNVars + RHO]  = rho;
            grid.data[(j * nx_total + i) * EulerNVars + RHOU] = rho * u;
            grid.data[(j * nx_total + i) * EulerNVars + RHOV] = rho * v;
            grid.data[(j * nx_total + i) * EulerNVars + EN]   = E;
        }
    }
}

// Random fill that is still EOS-valid: positive rho/p, finite velocities.
// Used for non-power-of-two coverage (Case 3).
template <typename Real>
void fill_random_valid(Grid2D<Real, EulerNVars>& grid, std::uint32_t seed) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> drho(0.5, 2.0);
    std::uniform_real_distribution<double> dvel(-1.5, 1.5);
    std::uniform_real_distribution<double> dp(0.5, 2.0);
    const Real gamma = Real(1.4);
    const int ng = Grid2D<Real, EulerNVars>::ng;
    const int nx_total = grid.nx + 2 * ng;
    const int ny_total = grid.ny + 2 * ng;
    for (int j = 0; j < ny_total; ++j) {
        for (int i = 0; i < nx_total; ++i) {
            const Real rho = static_cast<Real>(drho(rng));
            const Real u   = static_cast<Real>(dvel(rng));
            const Real v   = static_cast<Real>(dvel(rng));
            const Real p   = static_cast<Real>(dp(rng));
            const Real ke  = Real(0.5) * rho * (u * u + v * v);
            const Real E   = p / (gamma - Real(1)) + ke;
            grid.data[(j * nx_total + i) * EulerNVars + RHO]  = rho;
            grid.data[(j * nx_total + i) * EulerNVars + RHOU] = rho * u;
            grid.data[(j * nx_total + i) * EulerNVars + RHOV] = rho * v;
            grid.data[(j * nx_total + i) * EulerNVars + EN]   = E;
        }
    }
}

// Helper: classify whether the grid contains AT LEAST ONE subsonic cell
// AND AT LEAST ONE supersonic cell (in either axis). Returns true if so.
template <typename Real>
bool spans_sub_and_supersonic(const Grid2D<Real, EulerNVars>& host,
                              Real gamma) {
    bool has_sub = false;
    bool has_super = false;
    auto gv = host.view();
    for (int j = 0; j < host.ny; ++j) {
        for (int i = 0; i < host.nx; ++i) {
            Vec<Real, EulerNVars> q{};
            for (int v = 0; v < EulerNVars; ++v) q[v] = gv(i, j, v);
            const Real rho = q[RHO];
            const Real u = q[RHOU] / rho;
            const Real v = q[RHOV] / rho;
            const Real p = pressure<Real>(q, gamma);
            const Real a = sound_speed<Real>(rho, p, gamma);
            const Real speed =
                std::sqrt(static_cast<double>(u * u + v * v));
            if (speed < a) has_sub = true;
            if (speed > a) has_super = true;
        }
    }
    return has_sub && has_super;
}

// CPU oracle for X-axis Hancock: per-cell qL/qR over interior cells.
template <typename Real>
void cpu_hancock_x_oracle(
    const Grid2D<Real, EulerNVars>& host,
    Real dt, Real gamma,
    std::vector<Vec<Real, EulerNVars>>& qL_out,
    std::vector<Vec<Real, EulerNVars>>& qR_out) {
    const int nx = host.nx;
    const int ny = host.ny;
    qL_out.assign(static_cast<std::size_t>(nx) * static_cast<std::size_t>(ny),
                  Vec<Real, EulerNVars>{});
    qR_out.assign(static_cast<std::size_t>(nx) * static_cast<std::size_t>(ny),
                  Vec<Real, EulerNVars>{});
    auto gv = host.view();
    for (int j = 0; j < ny; ++j) {
        for (int i = 0; i < nx; ++i) {
            Vec<Real, EulerNVars> qL{}, qR{};
            muscl_hancock_x<Real>(gv, i, j, dt, gamma, qL, qR);
            qL_out[j * nx + i] = qL;
            qR_out[j * nx + i] = qR;
        }
    }
}

template <typename Real>
void cpu_hancock_y_oracle(
    const Grid2D<Real, EulerNVars>& host,
    Real dt, Real gamma,
    std::vector<Vec<Real, EulerNVars>>& qB_out,
    std::vector<Vec<Real, EulerNVars>>& qT_out) {
    const int nx = host.nx;
    const int ny = host.ny;
    qB_out.assign(static_cast<std::size_t>(nx) * static_cast<std::size_t>(ny),
                  Vec<Real, EulerNVars>{});
    qT_out.assign(static_cast<std::size_t>(nx) * static_cast<std::size_t>(ny),
                  Vec<Real, EulerNVars>{});
    auto gv = host.view();
    for (int j = 0; j < ny; ++j) {
        for (int i = 0; i < nx; ++i) {
            Vec<Real, EulerNVars> qB{}, qT{};
            muscl_hancock_y<Real>(gv, i, j, dt, gamma, qB, qT);
            qB_out[j * nx + i] = qB;
            qT_out[j * nx + i] = qT;
        }
    }
}

template <typename Real>
void require_gpu_hancock_x_matches_cpu(
    const Grid2D<Real, EulerNVars>& host, Real dt, Real gamma) {
    std::vector<Vec<Real, EulerNVars>> qL_oracle, qR_oracle;
    cpu_hancock_x_oracle(host, dt, gamma, qL_oracle, qR_oracle);

    GpuGrid<Real, EulerNVars> dev(host);
    const std::size_t cells =
        static_cast<std::size_t>(host.nx) * static_cast<std::size_t>(host.ny);
    DeviceArray<Vec<Real, EulerNVars>> qL_dev(cells);
    DeviceArray<Vec<Real, EulerNVars>> qR_dev(cells);

    hancock_predict_x_gpu<Real>(dev, dt, gamma, qL_dev.data(), qR_dev.data());

    std::vector<Vec<Real, EulerNVars>> qL_got(cells, Vec<Real, EulerNVars>{});
    std::vector<Vec<Real, EulerNVars>> qR_got(cells, Vec<Real, EulerNVars>{});
    qL_dev.copy_to_host(qL_got.data(), cells);
    qR_dev.copy_to_host(qR_got.data(), cells);

    REQUIRE(std::memcmp(qL_got.data(), qL_oracle.data(),
                        cells * sizeof(Vec<Real, EulerNVars>)) == 0);
    REQUIRE(std::memcmp(qR_got.data(), qR_oracle.data(),
                        cells * sizeof(Vec<Real, EulerNVars>)) == 0);
}

template <typename Real>
void require_gpu_hancock_y_matches_cpu(
    const Grid2D<Real, EulerNVars>& host, Real dt, Real gamma) {
    std::vector<Vec<Real, EulerNVars>> qB_oracle, qT_oracle;
    cpu_hancock_y_oracle(host, dt, gamma, qB_oracle, qT_oracle);

    GpuGrid<Real, EulerNVars> dev(host);
    const std::size_t cells =
        static_cast<std::size_t>(host.nx) * static_cast<std::size_t>(host.ny);
    DeviceArray<Vec<Real, EulerNVars>> qB_dev(cells);
    DeviceArray<Vec<Real, EulerNVars>> qT_dev(cells);

    hancock_predict_y_gpu<Real>(dev, dt, gamma, qB_dev.data(), qT_dev.data());

    std::vector<Vec<Real, EulerNVars>> qB_got(cells, Vec<Real, EulerNVars>{});
    std::vector<Vec<Real, EulerNVars>> qT_got(cells, Vec<Real, EulerNVars>{});
    qB_dev.copy_to_host(qB_got.data(), cells);
    qT_dev.copy_to_host(qT_got.data(), cells);

    REQUIRE(std::memcmp(qB_got.data(), qB_oracle.data(),
                        cells * sizeof(Vec<Real, EulerNVars>)) == 0);
    REQUIRE(std::memcmp(qT_got.data(), qT_oracle.data(),
                        cells * sizeof(Vec<Real, EulerNVars>)) == 0);
}

template <typename Real>
Grid2D<Real, EulerNVars> make_grid(int nx, int ny) {
    Grid2D<Real, EulerNVars> g(nx, ny);
    g.dx = Real(1) / static_cast<Real>(nx);
    g.dy = Real(1) / static_cast<Real>(ny);
    return g;
}

} // namespace

// Case 1: trivial constant data over a 1x1 interior — slopes are 0 so the
// Hancock half-step's flux difference is zero; qL == qR == cell value.
TEST_CASE("GPU Hancock predictor is bit-exact for constant data",
          "[gpu][hancock]") {
    const double dt_d = 0.001;
    const double gamma_d = 1.4;
    {
        auto host = make_grid<double>(1, 1);
        fill_constant(host);
        require_gpu_hancock_x_matches_cpu<double>(host, dt_d, gamma_d);
        require_gpu_hancock_y_matches_cpu<double>(host, dt_d, gamma_d);
    }
    {
        auto host = make_grid<float>(1, 1);
        fill_constant(host);
        require_gpu_hancock_x_matches_cpu<float>(host,
                                                  static_cast<float>(dt_d),
                                                  static_cast<float>(gamma_d));
        require_gpu_hancock_y_matches_cpu<float>(host,
                                                  static_cast<float>(dt_d),
                                                  static_cast<float>(gamma_d));
    }
}

// Case 2: 16x16 grid with a state field that spans subsonic, supersonic,
// and (near-)sonic-point regimes. Asserts the spec invariant explicitly
// before the bit-exact check, so a regression in the construction would
// surface immediately.
TEST_CASE("GPU Hancock predictor is bit-exact across sub/super/sonic states",
          "[gpu][hancock]") {
    const double dt_d = 0.001;
    const double gamma_d = 1.4;
    {
        auto host = make_grid<double>(16, 16);
        fill_sub_super_sonic_2d(host);
        REQUIRE(spans_sub_and_supersonic<double>(host, gamma_d));
        require_gpu_hancock_x_matches_cpu<double>(host, dt_d, gamma_d);
        require_gpu_hancock_y_matches_cpu<double>(host, dt_d, gamma_d);
    }
    {
        auto host = make_grid<float>(16, 16);
        fill_sub_super_sonic_2d(host);
        REQUIRE(spans_sub_and_supersonic<float>(host,
                                                 static_cast<float>(gamma_d)));
        require_gpu_hancock_x_matches_cpu<float>(host,
                                                  static_cast<float>(dt_d),
                                                  static_cast<float>(gamma_d));
        require_gpu_hancock_y_matches_cpu<float>(host,
                                                  static_cast<float>(dt_d),
                                                  static_cast<float>(gamma_d));
    }
}

// Case 3: 33x17 (non-power-of-two) full-grid Hancock prediction with a
// fixed-seed random EOS-valid fill. Covers boundary conditions of the
// 2D launch grid where blocks straddle the interior boundary.
TEST_CASE("GPU Hancock predictor is bit-exact on non-power-of-two grid",
          "[gpu][hancock]") {
    const double dt_d = 0.001;
    const double gamma_d = 1.4;
    {
        auto host = make_grid<double>(33, 17);
        fill_random_valid(host, 0xD12u);  // fixed seed
        require_gpu_hancock_x_matches_cpu<double>(host, dt_d, gamma_d);
        require_gpu_hancock_y_matches_cpu<double>(host, dt_d, gamma_d);
    }
    {
        auto host = make_grid<float>(33, 17);
        fill_random_valid(host, 0xF12u);
        require_gpu_hancock_x_matches_cpu<float>(host,
                                                  static_cast<float>(dt_d),
                                                  static_cast<float>(gamma_d));
        require_gpu_hancock_y_matches_cpu<float>(host,
                                                  static_cast<float>(dt_d),
                                                  static_cast<float>(gamma_d));
    }
}

#endif // HRSC_HAS_CUDA
