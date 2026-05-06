// tests/unit/test_gpu_reconstruct.cpp
//
// CUDA-only bit-exact oracle tests for the GPU MUSCL reconstruction kernel.
// Compares the per-cell qL/qR (X-axis) and q_bottom/q_top (Y-axis) buffers
// produced by the GPU kernel against the CPU oracle in src/euler/muscl.hpp
// using std::memcmp under strict-IEEE.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/grid.hpp"
#include "core/vec.hpp"
#include "euler/muscl.hpp"
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
void fill_random(Grid2D<Real, EulerNVars>& grid, std::uint32_t seed) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> dist(-1.0e3, 1.0e3);
    for (auto& x : grid.data) {
        x = static_cast<Real>(dist(rng));
    }
}

// Fill with constants (per-variable) so the slope-limiter returns 0 and
// qL == qR == cell value for every cell.
template <typename Real>
void fill_constant(Grid2D<Real, EulerNVars>& grid) {
    const Real values[EulerNVars] = {
        Real(1.25), Real(-0.5), Real(0.75), Real(2.5)
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

// Fill with a 2D tent (peak in the middle) PLUS an isolated diagonal jump.
// Designed to exercise ALL three branches of the minbee limiter on BOTH
// axes (X and Y see non-trivial slopes):
//   - On either side of the peak, backward and forward differences have the
//     same sign with different magnitudes -> exercises the |a|<|b| branch.
//   - At the peak (apex of the tent), adjacent differences have opposite
//     signs -> exercises the sign-flip branch (a*b <= 0 -> returns 0).
//   - At the diagonal jump, one of the differences is large while the other
//     remains small but same-sign -> further exercises |a|<|b| with a
//     dominant forward/backward step.
// Per-variable additive offset prevents trivial structure across variables.
template <typename Real>
void fill_tent_jump_2d(Grid2D<Real, EulerNVars>& grid) {
    const int ng = Grid2D<Real, EulerNVars>::ng;
    const int nx_total = grid.nx + 2 * ng;
    const int ny_total = grid.ny + 2 * ng;
    const int hx = grid.nx / 2;
    const int hy = grid.ny / 2;
    const int half = (grid.nx + grid.ny) / 2;
    for (int j = 0; j < ny_total; ++j) {
        for (int i = 0; i < nx_total; ++i) {
            const int ic = i - ng;
            const int jc = j - ng;
            for (int v = 0; v < EulerNVars; ++v) {
                // Tent in x: rises to peak at i=hx, falls after. Same in y.
                const Real tent_x = static_cast<Real>(
                    (ic <= hx) ? ic : (2 * hx - ic));
                const Real tent_y = static_cast<Real>(
                    (jc <= hy) ? jc : (2 * hy - jc));
                const Real ramp = tent_x * Real(1.5) + tent_y * Real(0.7);
                const Real jump =
                    (ic + jc >= half) ? Real(1000) : Real(0);
                const Real var_offset = static_cast<Real>(v) * Real(0.25);
                grid.data[(j * nx_total + i) * EulerNVars + v] =
                    ramp + jump + var_offset;
            }
        }
    }
}

// CPU oracle: produce per-cell qL/qR for X-axis MUSCL reconstruction
// over all interior cells (i in [0, nx), j in [0, ny)). Buffer layout:
// linear index = j * nx + i, each entry holds a Vec<Real, EulerNVars>.
template <typename Real>
void cpu_reconstruct_x_oracle(
    const Grid2D<Real, EulerNVars>& host,
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
            muscl_reconstruct_x<Real>(gv, i, j, qL, qR);
            qL_out[j * nx + i] = qL;
            qR_out[j * nx + i] = qR;
        }
    }
}

template <typename Real>
void cpu_reconstruct_y_oracle(
    const Grid2D<Real, EulerNVars>& host,
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
            muscl_reconstruct_y<Real>(gv, i, j, qB, qT);
            qB_out[j * nx + i] = qB;
            qT_out[j * nx + i] = qT;
        }
    }
}

// Run GPU X reconstruction and compare bit-for-bit against the CPU oracle.
template <typename Real>
void require_gpu_reconstruct_x_matches_cpu(
    const Grid2D<Real, EulerNVars>& host) {
    std::vector<Vec<Real, EulerNVars>> qL_oracle, qR_oracle;
    cpu_reconstruct_x_oracle(host, qL_oracle, qR_oracle);

    GpuGrid<Real, EulerNVars> dev(host);
    const std::size_t cells =
        static_cast<std::size_t>(host.nx) * static_cast<std::size_t>(host.ny);
    DeviceArray<Vec<Real, EulerNVars>> qL_dev(cells);
    DeviceArray<Vec<Real, EulerNVars>> qR_dev(cells);

    muscl_reconstruct_x_gpu<Real>(dev, qL_dev.data(), qR_dev.data());

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
void require_gpu_reconstruct_y_matches_cpu(
    const Grid2D<Real, EulerNVars>& host) {
    std::vector<Vec<Real, EulerNVars>> qB_oracle, qT_oracle;
    cpu_reconstruct_y_oracle(host, qB_oracle, qT_oracle);

    GpuGrid<Real, EulerNVars> dev(host);
    const std::size_t cells =
        static_cast<std::size_t>(host.nx) * static_cast<std::size_t>(host.ny);
    DeviceArray<Vec<Real, EulerNVars>> qB_dev(cells);
    DeviceArray<Vec<Real, EulerNVars>> qT_dev(cells);

    muscl_reconstruct_y_gpu<Real>(dev, qB_dev.data(), qT_dev.data());

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

// Case 1: trivial constant data over a 1x1 interior — slopes are 0,
// so qL == qR == cell value byte-for-byte.
TEST_CASE("GPU MUSCL reconstruction is bit-exact for constant data",
          "[gpu][reconstruct]") {
    {
        auto host = make_grid<double>(1, 1);
        fill_constant(host);
        require_gpu_reconstruct_x_matches_cpu<double>(host);
        require_gpu_reconstruct_y_matches_cpu<double>(host);
    }
    {
        auto host = make_grid<float>(1, 1);
        fill_constant(host);
        require_gpu_reconstruct_x_matches_cpu<float>(host);
        require_gpu_reconstruct_y_matches_cpu<float>(host);
    }
}

// Case 2: 16x16 smooth 2D ramp plus an isolated diagonal jump. Exercises
// both the |a|<|b| selection and the sign-flip (→0) branches of minbee on
// BOTH axes (slopes are non-trivial in x and y).
TEST_CASE("GPU MUSCL reconstruction is bit-exact across a strong jump",
          "[gpu][reconstruct]") {
    {
        auto host = make_grid<double>(16, 16);
        fill_tent_jump_2d(host);
        require_gpu_reconstruct_x_matches_cpu<double>(host);
        require_gpu_reconstruct_y_matches_cpu<double>(host);
    }
    {
        auto host = make_grid<float>(16, 16);
        fill_tent_jump_2d(host);
        require_gpu_reconstruct_x_matches_cpu<float>(host);
        require_gpu_reconstruct_y_matches_cpu<float>(host);
    }
}

// Case 3: 33x17 (non-power-of-two) full-grid random reconstruction.
TEST_CASE("GPU MUSCL reconstruction is bit-exact on non-power-of-two grid",
          "[gpu][reconstruct]") {
    {
        auto host = make_grid<double>(33, 17);
        fill_random(host, 0xC51u);
        require_gpu_reconstruct_x_matches_cpu<double>(host);
        require_gpu_reconstruct_y_matches_cpu<double>(host);
    }
    {
        auto host = make_grid<float>(33, 17);
        fill_random(host, 0xC52u);
        require_gpu_reconstruct_x_matches_cpu<float>(host);
        require_gpu_reconstruct_y_matches_cpu<float>(host);
    }
}

#endif // HRSC_HAS_CUDA
