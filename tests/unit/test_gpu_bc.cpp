// tests/unit/test_gpu_bc.cpp
//
// CUDA-only bit-exact oracle tests for GPU boundary-condition kernels.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/boundary.hpp"
#include "core/grid.hpp"
#include "gpu/euler_kernels.cuh"
#include "gpu/gpu_grid.cuh"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <random>

using namespace hrsc;

namespace {

template <typename Real>
void fill_random(Grid2D<Real, EulerNVars>& grid, std::uint32_t seed) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> dist(-1.0e6, 1.0e6);
    for (auto& x : grid.data) {
        x = static_cast<Real>(dist(rng));
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
void require_gpu_outflow_matches_cpu(Axis axis, int nx, int ny,
                                     std::uint32_t seed) {
    Grid2D<Real, EulerNVars> host(nx, ny);
    host.dx = Real(1) / static_cast<Real>(nx);
    host.dy = Real(1) / static_cast<Real>(ny);
    fill_random(host, seed);

    Grid2D<Real, EulerNVars> oracle = host;
    apply_outflow_bc(oracle.view(), axis);

    GpuGrid<Real, EulerNVars> dev(host);
    apply_outflow_bc_gpu(dev, axis);

    Grid2D<Real, EulerNVars> got(host.nx, host.ny);
    got.dx = host.dx;
    got.dy = host.dy;
    dev.download_to(got);

    REQUIRE(byte_equal(got, oracle));
}

template <typename Real>
void require_gpu_outflow_xy_matches_cpu(int nx, int ny, std::uint32_t seed) {
    Grid2D<Real, EulerNVars> host(nx, ny);
    host.dx = Real(1) / static_cast<Real>(nx);
    host.dy = Real(1) / static_cast<Real>(ny);
    fill_random(host, seed);

    Grid2D<Real, EulerNVars> oracle = host;
    apply_outflow_bc(oracle.view(), Axis::X);
    apply_outflow_bc(oracle.view(), Axis::Y);

    GpuGrid<Real, EulerNVars> dev(host);
    apply_outflow_bc_gpu(dev, Axis::X);
    apply_outflow_bc_gpu(dev, Axis::Y);

    Grid2D<Real, EulerNVars> got(host.nx, host.ny);
    got.dx = host.dx;
    got.dy = host.dy;
    dev.download_to(got);

    REQUIRE(byte_equal(got, oracle));
}

template <typename Real>
void require_gpu_periodic_matches_cpu(Axis axis, int nx, int ny,
                                      std::uint32_t seed) {
    Grid2D<Real, EulerNVars> host(nx, ny);
    host.dx = Real(1) / static_cast<Real>(nx);
    host.dy = Real(1) / static_cast<Real>(ny);
    fill_random(host, seed);

    Grid2D<Real, EulerNVars> oracle = host;
    apply_periodic_bc(oracle.view(), axis);

    GpuGrid<Real, EulerNVars> dev(host);
    apply_periodic_bc_gpu(dev, axis);

    Grid2D<Real, EulerNVars> got(host.nx, host.ny);
    got.dx = host.dx;
    got.dy = host.dy;
    dev.download_to(got);

    REQUIRE(byte_equal(got, oracle));
}

template <typename Real>
void require_gpu_reflective_matches_cpu(Axis axis, int nx, int ny,
                                        std::uint32_t seed) {
    Grid2D<Real, EulerNVars> host(nx, ny);
    host.dx = Real(1) / static_cast<Real>(nx);
    host.dy = Real(1) / static_cast<Real>(ny);
    fill_random(host, seed);

    Grid2D<Real, EulerNVars> oracle = host;
    if (axis == Axis::X) {
        apply_reflective_bc(oracle.view(), axis, std::array<int, 1>{RHOU});
    } else {
        apply_reflective_bc(oracle.view(), axis, std::array<int, 1>{RHOV});
    }

    GpuGrid<Real, EulerNVars> dev(host);
    apply_reflective_bc_gpu(dev, axis);

    Grid2D<Real, EulerNVars> got(host.nx, host.ny);
    got.dx = host.dx;
    got.dy = host.dy;
    dev.download_to(got);

    REQUIRE(byte_equal(got, oracle));
}

template <typename Real>
void require_gpu_reflective_xy_matches_cpu(int nx, int ny, std::uint32_t seed) {
    Grid2D<Real, EulerNVars> host(nx, ny);
    host.dx = Real(1) / static_cast<Real>(nx);
    host.dy = Real(1) / static_cast<Real>(ny);
    fill_random(host, seed);

    Grid2D<Real, EulerNVars> oracle = host;
    apply_reflective_bc(oracle.view(), Axis::X, std::array<int, 1>{RHOU});
    apply_reflective_bc(oracle.view(), Axis::Y, std::array<int, 1>{RHOV});

    GpuGrid<Real, EulerNVars> dev(host);
    apply_reflective_bc_gpu(dev, Axis::X);
    apply_reflective_bc_gpu(dev, Axis::Y);

    Grid2D<Real, EulerNVars> got(host.nx, host.ny);
    got.dx = host.dx;
    got.dy = host.dy;
    dev.download_to(got);

    REQUIRE(byte_equal(got, oracle));
}

} // namespace

TEST_CASE("GPU X outflow BC matches CPU oracle byte-for-byte",
          "[gpu][bc]") {
    require_gpu_outflow_matches_cpu<double>(Axis::X, 17, 9, 0xB00Cu);
    require_gpu_outflow_matches_cpu<float>(Axis::X, 17, 9, 0xB00Du);
}

TEST_CASE("GPU Y outflow BC matches CPU oracle byte-for-byte",
          "[gpu][bc]") {
    require_gpu_outflow_matches_cpu<double>(Axis::Y, 17, 9, 0xC0DEu);
    require_gpu_outflow_matches_cpu<float>(Axis::Y, 17, 9, 0xC0DFu);
}

TEST_CASE("GPU outflow BC matches CPU oracle in canonical 1D grid",
          "[gpu][bc]") {
    require_gpu_outflow_matches_cpu<double>(Axis::X, 23, 1, 0x1D00u);
    require_gpu_outflow_matches_cpu<float>(Axis::X, 23, 1, 0x1D01u);
    require_gpu_outflow_matches_cpu<double>(Axis::Y, 23, 1, 0x1D02u);
    require_gpu_outflow_matches_cpu<float>(Axis::Y, 23, 1, 0x1D03u);
}

TEST_CASE("GPU X-then-Y outflow BC composition matches CPU solver order",
          "[gpu][bc]") {
    require_gpu_outflow_xy_matches_cpu<double>(19, 7, 0xABCDu);
    require_gpu_outflow_xy_matches_cpu<float>(19, 7, 0xABCEu);
}

TEST_CASE("GPU X periodic BC matches CPU oracle byte-for-byte",
          "[gpu][bc]") {
    require_gpu_periodic_matches_cpu<double>(Axis::X, 3, 5, 0x6D0200u);
    require_gpu_periodic_matches_cpu<float>(Axis::X, 3, 5, 0x6D0201u);
    require_gpu_periodic_matches_cpu<double>(Axis::X, 17, 9, 0x6D0202u);
    require_gpu_periodic_matches_cpu<float>(Axis::X, 17, 9, 0x6D0203u);
}

TEST_CASE("GPU Y periodic BC matches CPU oracle byte-for-byte",
          "[gpu][bc]") {
    require_gpu_periodic_matches_cpu<double>(Axis::Y, 5, 3, 0x6D0204u);
    require_gpu_periodic_matches_cpu<float>(Axis::Y, 5, 3, 0x6D0205u);
    require_gpu_periodic_matches_cpu<double>(Axis::Y, 19, 7, 0x6D0206u);
    require_gpu_periodic_matches_cpu<float>(Axis::Y, 19, 7, 0x6D0207u);
}

TEST_CASE("GPU X reflective BC matches CPU oracle byte-for-byte",
          "[gpu][bc]") {
    require_gpu_reflective_matches_cpu<double>(Axis::X, 17, 9, 0x6D0300u);
    require_gpu_reflective_matches_cpu<float>(Axis::X, 17, 9, 0x6D0301u);
}

TEST_CASE("GPU Y reflective BC matches CPU oracle byte-for-byte",
          "[gpu][bc]") {
    require_gpu_reflective_matches_cpu<double>(Axis::Y, 19, 7, 0x6D0302u);
    require_gpu_reflective_matches_cpu<float>(Axis::Y, 19, 7, 0x6D0303u);
}

TEST_CASE("GPU X-then-Y reflective BC composition matches CPU solver order",
          "[gpu][bc]") {
    require_gpu_reflective_xy_matches_cpu<double>(19, 7, 0x6D0304u);
    require_gpu_reflective_xy_matches_cpu<float>(19, 7, 0x6D0305u);
    require_gpu_reflective_xy_matches_cpu<double>(3, 5, 0x6D0306u);
    require_gpu_reflective_xy_matches_cpu<float>(3, 5, 0x6D0307u);
}

#endif // HRSC_HAS_CUDA
