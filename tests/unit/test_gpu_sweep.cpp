// tests/unit/test_gpu_sweep.cpp
//
// Bit-exact integration test: GPU sweep_x_gpu / sweep_y_gpu vs an inline
// CPU x_sweep / y_sweep replica using the same public primitives
// (muscl_hancock_x/_y + rusanov_flux + per-cell update). Confirms the GPU
// orchestration path produces a byte-identical post-sweep grid against a
// straightforward CPU implementation, on a 64x64 LW Config 3-shaped IC.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/boundary.hpp"
#include "core/grid.hpp"
#include "core/vec.hpp"
#include "euler/euler_flux.hpp"   // swap_momentum
#include "euler/hancock.hpp"
#include "euler/rusanov.hpp"
#include "euler/euler_solver.hpp" // FluxScheme
#include "gpu/euler_kernels.cuh"
#include "gpu/gpu_grid.cuh"

#include <cstring>
#include <cstdint>
#include <random>
#include <vector>

using namespace hrsc;

namespace {

// LW Config 3-style IC (4-quadrant) projected onto a square grid. We use
// physical states known to produce non-trivial slopes in both axes.
template <typename Real>
void fill_lw_config3(Grid2D<Real, EulerNVars>& host) {
    const Real gamma = Real(1.4);
    const int ng = Grid2D<Real, EulerNVars>::ng;
    const int nx_total = host.nx + 2 * ng;
    const int ny_total = host.ny + 2 * ng;
    const int hx = host.nx / 2;
    const int hy = host.ny / 2;
    auto cons = [&](Real rho, Real u, Real v, Real p) {
        Vec<Real, EulerNVars> q{};
        q[RHO]  = rho;
        q[RHOU] = rho * u;
        q[RHOV] = rho * v;
        q[EN]   = p / (gamma - Real(1)) + Real(0.5) * rho * (u * u + v * v);
        return q;
    };
    // LW Config 3 quadrants: (rho, u, v, p)
    auto q1 = cons(Real(1.5),    Real(0.0),  Real(0.0),  Real(1.5));
    auto q2 = cons(Real(0.5323), Real(1.206), Real(0.0), Real(0.3));
    auto q3 = cons(Real(0.138),  Real(1.206), Real(1.206), Real(0.029));
    auto q4 = cons(Real(0.5323), Real(0.0),  Real(1.206), Real(0.3));
    for (int j = 0; j < ny_total; ++j) {
        for (int i = 0; i < nx_total; ++i) {
            const int ic = i - ng;
            const int jc = j - ng;
            const auto& q = (ic >= hx && jc >= hy) ? q1
                          : (ic <  hx && jc >= hy) ? q2
                          : (ic <  hx && jc <  hy) ? q3
                          :                          q4;
            for (int v = 0; v < EulerNVars; ++v) {
                host.data[(j * nx_total + i) * EulerNVars + v] = q[v];
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

// Inline CPU x_sweep, mirroring src/euler/euler_solver.cpp::x_sweep
// (non-profiling branch). Caller must apply BCs before invoking.
template <typename Real>
void cpu_x_sweep(Grid2D<Real, EulerNVars>& host, Real dt, Real gamma) {
    auto gv = host.view();
    const int nx = gv.nx;
    const int ny = gv.ny;
    const int n_interfaces = nx + 1;
    for (int j = 0; j < ny; ++j) {
        std::vector<Vec<Real, EulerNVars>> flux(n_interfaces);
        for (int k = 0; k < n_interfaces; ++k) {
            const int iL = k - 1;
            const int iR = k;
            Vec<Real, EulerNVars> qL_left{}, qL_right{};
            Vec<Real, EulerNVars> qR_left{}, qR_right{};
            muscl_hancock_x<Real>(gv, iL, j, dt, gamma, qL_left, qL_right);
            muscl_hancock_x<Real>(gv, iR, j, dt, gamma, qR_left, qR_right);
            flux[k] = rusanov_flux<Real>(qL_right, qR_left, gamma);
        }
        const Real dtdx = dt / gv.dx;
        for (int i = 0; i < nx; ++i) {
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) -= dtdx * (flux[i + 1][v] - flux[i][v]);
            }
        }
    }
}

template <typename Real>
void cpu_y_sweep(Grid2D<Real, EulerNVars>& host, Real dt, Real gamma) {
    auto gv = host.view();
    const int nx = gv.nx;
    const int ny = gv.ny;
    const int n_interfaces = ny + 1;
    for (int i = 0; i < nx; ++i) {
        std::vector<Vec<Real, EulerNVars>> flux(n_interfaces);
        for (int k = 0; k < n_interfaces; ++k) {
            const int jB = k - 1;
            const int jT = k;
            Vec<Real, EulerNVars> qB_bot{}, qB_top{};
            Vec<Real, EulerNVars> qT_bot{}, qT_top{};
            muscl_hancock_y<Real>(gv, i, jB, dt, gamma, qB_bot, qB_top);
            muscl_hancock_y<Real>(gv, i, jT, dt, gamma, qT_bot, qT_top);
            const auto rotL = swap_momentum<Real>(qB_top);
            const auto rotR = swap_momentum<Real>(qT_bot);
            const auto fr   = rusanov_flux<Real>(rotL, rotR, gamma);
            flux[k] = swap_momentum<Real>(fr);
        }
        const Real dtdy = dt / gv.dy;
        for (int j = 0; j < ny; ++j) {
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) -= dtdy * (flux[j + 1][v] - flux[j][v]);
            }
        }
    }
}

template <typename Real>
Grid2D<Real, EulerNVars> make_grid(int nx, int ny) {
    Grid2D<Real, EulerNVars> g(nx, ny);
    g.dx = Real(1) / static_cast<Real>(nx);
    g.dy = Real(1) / static_cast<Real>(ny);
    return g;
}

template <typename Real>
void require_sweep_x_matches(int nx, int ny) {
    auto host = make_grid<Real>(nx, ny);
    fill_lw_config3<Real>(host);
    apply_outflow_bc(host.view(), Axis::X);
    apply_outflow_bc(host.view(), Axis::Y);
    const Real gamma = Real(1.4);
    const Real dt = Real(0.0005);

    auto oracle = host;
    cpu_x_sweep<Real>(oracle, dt, gamma);

    GpuGrid<Real, EulerNVars> dev(host);
    sweep_x_gpu<Real>(dev, dt, gamma, FluxScheme::Rusanov);

    auto got = make_grid<Real>(nx, ny);
    dev.download_to(got);
    REQUIRE(byte_equal(got, oracle));
}

template <typename Real>
void require_sweep_y_matches(int nx, int ny) {
    auto host = make_grid<Real>(nx, ny);
    fill_lw_config3<Real>(host);
    apply_outflow_bc(host.view(), Axis::X);
    apply_outflow_bc(host.view(), Axis::Y);
    const Real gamma = Real(1.4);
    const Real dt = Real(0.0005);

    auto oracle = host;
    cpu_y_sweep<Real>(oracle, dt, gamma);

    GpuGrid<Real, EulerNVars> dev(host);
    sweep_y_gpu<Real>(dev, dt, gamma, FluxScheme::Rusanov);

    auto got = make_grid<Real>(nx, ny);
    dev.download_to(got);
    REQUIRE(byte_equal(got, oracle));
}

} // namespace

// 1 X-sweep on GPU vs CPU on a 64x64 LW Config 3-style IC, both precisions.
TEST_CASE("GPU sweep_x bit-exact to CPU x_sweep on LW Config 3 64x64",
          "[gpu][sweep]") {
    require_sweep_x_matches<double>(64, 64);
    require_sweep_x_matches<float>(64, 64);
}

// 1 Y-sweep on GPU vs CPU on the same IC.
TEST_CASE("GPU sweep_y bit-exact to CPU y_sweep on LW Config 3 64x64",
          "[gpu][sweep]") {
    require_sweep_y_matches<double>(64, 64);
    require_sweep_y_matches<float>(64, 64);
}

// X-then-Y composition on a smaller grid (Lie split half-step). BCs applied
// once before X (matching the test scope; full step() in T16 reapplies BC
// between X and Y).
TEST_CASE("GPU sweep X-then-Y matches CPU on 32x32 LW Config 3",
          "[gpu][sweep]") {
    auto run = [](auto real_tag) {
        using Real = decltype(real_tag);
        const int nx = 32, ny = 32;
        auto host = make_grid<Real>(nx, ny);
        fill_lw_config3<Real>(host);
        apply_outflow_bc(host.view(), Axis::X);
        apply_outflow_bc(host.view(), Axis::Y);
        const Real gamma = Real(1.4);
        const Real dt = Real(0.0005);

        auto oracle = host;
        cpu_x_sweep<Real>(oracle, dt, gamma);
        // Re-apply BC between X and Y to match step()'s convention exactly.
        apply_outflow_bc(oracle.view(), Axis::X);
        apply_outflow_bc(oracle.view(), Axis::Y);
        cpu_y_sweep<Real>(oracle, dt, gamma);

        GpuGrid<Real, EulerNVars> dev(host);
        sweep_x_gpu<Real>(dev, dt, gamma, FluxScheme::Rusanov);
        apply_outflow_bc_gpu<Real>(dev, Axis::X);
        apply_outflow_bc_gpu<Real>(dev, Axis::Y);
        sweep_y_gpu<Real>(dev, dt, gamma, FluxScheme::Rusanov);

        auto got = make_grid<Real>(nx, ny);
        dev.download_to(got);
        REQUIRE(byte_equal(got, oracle));
    };
    run(double{});
    run(float{});
}

#endif // HRSC_HAS_CUDA
