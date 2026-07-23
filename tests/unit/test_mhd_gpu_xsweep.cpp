// tests/unit/test_mhd_gpu_xsweep.cpp
//
// CUDA-only oracle test for the MHD HLL x-sweep.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/boundary.hpp"
#include "gpu/gpu_grid.cuh"
#include "mhd/hll.hpp"
#include "mhd/mhd_reconstruct.hpp"
#include "mhd/mhd_solver.hpp"

#include <cmath>
#include <cstring>
#include <vector>

namespace hrsc {
template <typename Real>
void sweep_x_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real dt, Real gamma, Real ch);
}

using namespace hrsc;

namespace {

template <typename Real, typename Ptr>
Vec<Real, MhdNVars> load_cell_test(GridViewBase<Real, MhdNVars, Ptr> gv,
                                   int i, int j) {
    Vec<Real, MhdNVars> U{};
    for (int k = 0; k < MhdNVars; ++k) U[k] = gv(i, j, k);
    return U;
}

template <typename Real>
void store_cell_test(GridView<Real, MhdNVars> gv, int i, int j,
                     const Vec<Real, MhdNVars>& U) {
    for (int k = 0; k < MhdNVars; ++k) gv(i, j, k) = U[k];
}

template <typename Real>
bool physical_test(const Vec<Real, MhdNVars>& U, Real gamma) {
    for (int k = 0; k < MhdNVars; ++k) {
        if (!std::isfinite(U[k])) return false;
    }
    if (!(U[MhdIdx::RHO] > Real(0))) return false;
    const Real p = pressure(U, gamma);
    return std::isfinite(p) && p > Real(0);
}

template <typename Real>
void predict_faces_test(const Vec<Real, MhdNVars>& Um,
                        const Vec<Real, MhdNVars>& U0,
                        const Vec<Real, MhdNVars>& Up,
                        Real dt, Real gamma, Real ch, Real h,
                        Vec<Real, MhdNVars>& left,
                        Vec<Real, MhdNVars>& right) {
    const Vec<Real, MhdNVars> slope = mhd_slope(Um, U0, Up);

    left = U0 - Real(0.5) * slope;
    right = U0 + Real(0.5) * slope;

    if (!physical_test(left, gamma) || !physical_test(right, gamma)) {
        left = U0;
        right = U0;
        return;
    }

    const Vec<Real, MhdNVars> FL = mhd_flux_x(left, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(right, gamma, ch);
    const Real half_dtdx = Real(0.5) * dt / h;
    for (int k = 0; k < MhdNVars; ++k) {
        const Real predictor = half_dtdx * (FR[k] - FL[k]);
        left[k] -= predictor;
        right[k] -= predictor;
    }

    if (!physical_test(left, gamma) || !physical_test(right, gamma)) {
        left = U0;
        right = U0;
    }
}

template <typename Real>
void cpu_mhd_x_sweep(Grid2D<Real, MhdNVars>& host, Real dt,
                     Real gamma, Real ch) {
    auto gv = host.view();
    for (int j = 0; j < gv.ny; ++j) {
        std::vector<Vec<Real, MhdNVars>> flux(
            static_cast<std::size_t>(gv.nx + 1));
        for (int iface = 0; iface <= gv.nx; ++iface) {
            const int iL = iface - 1;
            const int iR = iface;
            Vec<Real, MhdNVars> left_cell_left{}, left_cell_right{};
            Vec<Real, MhdNVars> right_cell_left{}, right_cell_right{};
            predict_faces_test(load_cell_test(gv, iL - 1, j),
                               load_cell_test(gv, iL, j),
                               load_cell_test(gv, iL + 1, j),
                               dt, gamma, ch, gv.dx,
                               left_cell_left, left_cell_right);
            predict_faces_test(load_cell_test(gv, iR - 1, j),
                               load_cell_test(gv, iR, j),
                               load_cell_test(gv, iR + 1, j),
                               dt, gamma, ch, gv.dx,
                               right_cell_left, right_cell_right);
            flux[static_cast<std::size_t>(iface)] =
                HllFlux{}(left_cell_right, right_cell_left, gamma, ch);
        }

        const Real dtdx = dt / gv.dx;
        for (int i = 0; i < gv.nx; ++i) {
            Vec<Real, MhdNVars> U = load_cell_test(gv, i, j);
            const auto& fL = flux[static_cast<std::size_t>(i)];
            const auto& fR = flux[static_cast<std::size_t>(i + 1)];
            for (int k = 0; k < MhdNVars; ++k) {
                U[k] -= dtdx * (fR[k] - fL[k]);
            }
            store_cell_test(gv, i, j, U);
        }
    }
}

template <typename Real>
Grid2D<Real, MhdNVars> make_brio_wu_grid(int nx) {
    Grid2D<Real, MhdNVars> g(nx, 1);
    g.dx = Real(1) / static_cast<Real>(nx);
    g.dy = g.dx;
    setup_brio_wu(g.view(), nx, g.dx, Real(0), Real(2), Real(0.5));
    apply_outflow_bc(g.view(), Axis::X);
    return g;
}

template <typename Real>
bool byte_equal(const Grid2D<Real, MhdNVars>& a,
                const Grid2D<Real, MhdNVars>& b) {
    return a.data.size() == b.data.size() &&
           std::memcmp(a.data.data(), b.data.data(),
                       a.data.size() * sizeof(Real)) == 0;
}

template <typename Real>
void require_x_sweep_matches_cpu() {
    constexpr int nx = 64;
    const Real gamma = Real(2);
    const Real ch = Real(2);
    const Real dt = Real(0.0005);

    auto host = make_brio_wu_grid<Real>(nx);
    auto oracle = host;
    cpu_mhd_x_sweep(oracle, dt, gamma, ch);

    GpuGrid<Real, MhdNVars> dev(host);
    sweep_x_mhd_gpu(dev, dt, gamma, ch);

    auto got = make_brio_wu_grid<Real>(nx);
    dev.download_to(got);
    REQUIRE(byte_equal(got, oracle));
}

} // namespace

TEST_CASE("MHD GPU x-sweep matches CPU HLL x-sweep", "[gpu][mhd][sweep]") {
    require_x_sweep_matches_cpu<double>();
    require_x_sweep_matches_cpu<float>();
}

#endif // HRSC_HAS_CUDA
