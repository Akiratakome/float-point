// tests/unit/test_gpu_rusanov.cpp
//
// CUDA-only bit-exact oracle tests for the GPU Rusanov (LLF) flux kernel.
// Compares per-face flux output against the CPU oracle in
// src/euler/rusanov.hpp using std::memcmp under strict-IEEE
// (--fmad=false on euler_kernels.cu).

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/grid.hpp"
#include "core/vec.hpp"
#include "euler/euler_flux.hpp"   // swap_momentum
#include "euler/rusanov.hpp"
#include "gpu/cuda_utils.cuh"
#include "gpu/euler_kernels.cuh"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <random>
#include <vector>

using namespace hrsc;

namespace {

// Build a physically valid Euler conserved state from primitive variables.
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
bool buf_byte_equal(const std::vector<Vec<Real, EulerNVars>>& a,
                    const std::vector<Vec<Real, EulerNVars>>& b) {
    return a.size() == b.size() &&
           std::memcmp(a.data(), b.data(),
                       a.size() * sizeof(Vec<Real, EulerNVars>)) == 0;
}

// CPU oracle for the X-face flux buffer.
template <typename Real>
std::vector<Vec<Real, EulerNVars>> cpu_rusanov_flux_x(
    const std::vector<Vec<Real, EulerNVars>>& qL,
    const std::vector<Vec<Real, EulerNVars>>& qR,
    Real gamma) {
    std::vector<Vec<Real, EulerNVars>> flux(qL.size());
    for (std::size_t k = 0; k < qL.size(); ++k) {
        flux[k] = rusanov_flux<Real>(qL[k], qR[k], gamma);
    }
    return flux;
}

// CPU oracle for the Y-face flux buffer (rotation handled).
template <typename Real>
std::vector<Vec<Real, EulerNVars>> cpu_rusanov_flux_y(
    const std::vector<Vec<Real, EulerNVars>>& qB,
    const std::vector<Vec<Real, EulerNVars>>& qT,
    Real gamma) {
    std::vector<Vec<Real, EulerNVars>> flux(qB.size());
    for (std::size_t k = 0; k < qB.size(); ++k) {
        const auto rotL = swap_momentum<Real>(qB[k]);
        const auto rotR = swap_momentum<Real>(qT[k]);
        flux[k] = swap_momentum<Real>(rusanov_flux<Real>(rotL, rotR, gamma));
    }
    return flux;
}

template <typename Real>
void require_x_face_flux_matches(
    const std::vector<Vec<Real, EulerNVars>>& qL,
    const std::vector<Vec<Real, EulerNVars>>& qR,
    int nx, int ny, Real gamma) {
    REQUIRE(qL.size() == static_cast<std::size_t>((nx + 1)) * ny);
    REQUIRE(qR.size() == qL.size());

    auto oracle = cpu_rusanov_flux_x<Real>(qL, qR, gamma);

    DeviceArray<Vec<Real, EulerNVars>> dev_qL(qL.size());
    DeviceArray<Vec<Real, EulerNVars>> dev_qR(qR.size());
    DeviceArray<Vec<Real, EulerNVars>> dev_flux(qL.size());
    dev_qL.copy_from_host(qL.data(), qL.size());
    dev_qR.copy_from_host(qR.data(), qR.size());

    rusanov_flux_x_gpu<Real>(nx, ny, gamma, dev_qL.data(), dev_qR.data(),
                             dev_flux.data());

    std::vector<Vec<Real, EulerNVars>> got(qL.size());
    dev_flux.copy_to_host(got.data(), got.size());

    REQUIRE(buf_byte_equal(got, oracle));
}

template <typename Real>
void require_y_face_flux_matches(
    const std::vector<Vec<Real, EulerNVars>>& qB,
    const std::vector<Vec<Real, EulerNVars>>& qT,
    int nx, int ny, Real gamma) {
    REQUIRE(qB.size() == static_cast<std::size_t>(nx) * (ny + 1));
    REQUIRE(qT.size() == qB.size());

    auto oracle = cpu_rusanov_flux_y<Real>(qB, qT, gamma);

    DeviceArray<Vec<Real, EulerNVars>> dev_qB(qB.size());
    DeviceArray<Vec<Real, EulerNVars>> dev_qT(qT.size());
    DeviceArray<Vec<Real, EulerNVars>> dev_flux(qB.size());
    dev_qB.copy_from_host(qB.data(), qB.size());
    dev_qT.copy_from_host(qT.data(), qT.size());

    rusanov_flux_y_gpu<Real>(nx, ny, gamma, dev_qB.data(), dev_qT.data(),
                             dev_flux.data());

    std::vector<Vec<Real, EulerNVars>> got(qB.size());
    dev_flux.copy_to_host(got.data(), got.size());

    REQUIRE(buf_byte_equal(got, oracle));
}

} // namespace

// Case 1: single X-face. One thread launched (nx=0 yields nx+1=1 face).
TEST_CASE("GPU Rusanov flux is bit-exact on a single X-face",
          "[gpu][rusanov]") {
    auto run = [](auto real_tag) {
        using Real = decltype(real_tag);
        const Real gamma = Real(1.4);
        std::vector<Vec<Real, EulerNVars>> qL = {
            make_state<Real>(Real(1.0), Real(0.5), Real(0.0),
                             Real(1.0), gamma)};
        std::vector<Vec<Real, EulerNVars>> qR = {
            make_state<Real>(Real(0.125), Real(0.0), Real(0.0),
                             Real(0.1), gamma)};
        // nx = 0 -> nx+1 = 1 face; ny = 1.
        require_x_face_flux_matches<Real>(qL, qR, 0, 1, gamma);
    };
    run(double{});
    run(float{});
}

// Case 2: sonic-point face. State chosen so |u| ≈ a (near sonic) on either
// side, exercising the std::abs / std::max selection in S_max.
TEST_CASE("GPU Rusanov flux is bit-exact at a near-sonic X-face",
          "[gpu][rusanov]") {
    auto run = [](auto real_tag) {
        using Real = decltype(real_tag);
        const Real gamma = Real(1.4);
        // a = sqrt(gamma * p / rho); pick rho = 1.0, p = 1.0 -> a ≈ 1.183.
        // Choose u_L = -1.183 (left-going sonic), u_R = +1.183.
        std::vector<Vec<Real, EulerNVars>> qL = {
            make_state<Real>(Real(1.0), Real(-1.183216), Real(0.0),
                             Real(1.0), gamma)};
        std::vector<Vec<Real, EulerNVars>> qR = {
            make_state<Real>(Real(1.0), Real(+1.183216), Real(0.0),
                             Real(1.0), gamma)};
        require_x_face_flux_matches<Real>(qL, qR, 0, 1, gamma);
    };
    run(double{});
    run(float{});
}

// Case 3: stationary contact face. p_L = p_R, u = 0 on both sides, only
// density differs. S_max is dominated by sound speed; the (qR - qL)
// diffusive term is purely on the rho component.
TEST_CASE("GPU Rusanov flux is bit-exact at a stationary contact face",
          "[gpu][rusanov]") {
    auto run = [](auto real_tag) {
        using Real = decltype(real_tag);
        const Real gamma = Real(1.4);
        std::vector<Vec<Real, EulerNVars>> qL = {
            make_state<Real>(Real(1.0), Real(0.0), Real(0.0),
                             Real(1.0), gamma)};
        std::vector<Vec<Real, EulerNVars>> qR = {
            make_state<Real>(Real(0.125), Real(0.0), Real(0.0),
                             Real(1.0), gamma)};
        require_x_face_flux_matches<Real>(qL, qR, 0, 1, gamma);
    };
    run(double{});
    run(float{});
}

// Case 4: 16x16 full sweep with random physical states covering both X and Y
// face buffers. Verifies the kernel index arithmetic for the
// (nx+1) x ny and nx x (ny+1) layouts and exercises swap_momentum on Y.
TEST_CASE("GPU Rusanov flux is bit-exact on a 16x16 full-grid face sweep",
          "[gpu][rusanov]") {
    auto run = [](auto real_tag, std::uint32_t seed) {
        using Real = decltype(real_tag);
        const Real gamma = Real(1.4);
        const int nx = 16, ny = 16;
        std::mt19937 rng(seed);
        std::uniform_real_distribution<double> rho_dist(0.5, 2.0);
        std::uniform_real_distribution<double> vel_dist(-0.8, 0.8);
        std::uniform_real_distribution<double> p_dist(0.5, 2.0);

        std::vector<Vec<Real, EulerNVars>> qL_x(
            static_cast<std::size_t>(nx + 1) * ny);
        std::vector<Vec<Real, EulerNVars>> qR_x(qL_x.size());
        for (std::size_t k = 0; k < qL_x.size(); ++k) {
            qL_x[k] = make_state<Real>(
                static_cast<Real>(rho_dist(rng)),
                static_cast<Real>(vel_dist(rng)),
                static_cast<Real>(vel_dist(rng)),
                static_cast<Real>(p_dist(rng)), gamma);
            qR_x[k] = make_state<Real>(
                static_cast<Real>(rho_dist(rng)),
                static_cast<Real>(vel_dist(rng)),
                static_cast<Real>(vel_dist(rng)),
                static_cast<Real>(p_dist(rng)), gamma);
        }
        require_x_face_flux_matches<Real>(qL_x, qR_x, nx, ny, gamma);

        std::vector<Vec<Real, EulerNVars>> qB_y(
            static_cast<std::size_t>(nx) * (ny + 1));
        std::vector<Vec<Real, EulerNVars>> qT_y(qB_y.size());
        for (std::size_t k = 0; k < qB_y.size(); ++k) {
            qB_y[k] = make_state<Real>(
                static_cast<Real>(rho_dist(rng)),
                static_cast<Real>(vel_dist(rng)),
                static_cast<Real>(vel_dist(rng)),
                static_cast<Real>(p_dist(rng)), gamma);
            qT_y[k] = make_state<Real>(
                static_cast<Real>(rho_dist(rng)),
                static_cast<Real>(vel_dist(rng)),
                static_cast<Real>(vel_dist(rng)),
                static_cast<Real>(p_dist(rng)), gamma);
        }
        require_y_face_flux_matches<Real>(qB_y, qT_y, nx, ny, gamma);
    };
    run(double{}, 0x14000040u);
    run(float{},  0x14000041u);
}

#endif // HRSC_HAS_CUDA
