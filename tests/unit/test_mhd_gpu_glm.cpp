// tests/unit/test_mhd_gpu_glm.cpp
//
// CUDA-only oracle tests for the MHD GLM damping step.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "gpu/gpu_grid.cuh"
#include "mhd/glm.hpp"
#include "mhd/mhd_state.hpp"

#include <cmath>
#include <cstring>

namespace hrsc {
template <typename Real>
void glm_damp_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real ch, Real cr, Real dt);
}

using namespace hrsc;

namespace {

template <typename Real>
Grid2D<Real, MhdNVars> make_glm_grid() {
    Grid2D<Real, MhdNVars> g(8, 4);
    g.dx = Real(0.125);
    g.dy = Real(0.25);
    auto gv = g.view();
    for (int j = 0; j < gv.ny; ++j) {
        for (int i = 0; i < gv.nx; ++i) {
            MhdPrim<Real> w{};
            w.rho = Real(1) + Real(0.01) * static_cast<Real>(i + j);
            w.p = Real(1);
            w.Bx = Real(0.1) * static_cast<Real>(i + 1);
            w.By = Real(0.05) * static_cast<Real>(j + 1);
            w.psi = Real(0.25) * static_cast<Real>(i - 2 * j);
            const auto U = prim_to_cons(w, Real(5) / Real(3));
            for (int v = 0; v < MhdNVars; ++v) {
                gv(i, j, v) = U[v];
            }
        }
    }
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
void require_glm_damp_matches_cpu() {
    constexpr Real gamma = Real(5) / Real(3);
    (void)gamma;
    const Real ch = Real(1.75);
    const Real cr = Real(0.18);
    const Real dt = Real(0.004);

    auto host = make_glm_grid<Real>();
    auto oracle = host;
    glm_damp<Real>(oracle.view(), oracle.nx, oracle.ny, ch, cr, dt);

    GpuGrid<Real, MhdNVars> dev(host);
    glm_damp_mhd_gpu(dev, ch, cr, dt);

    auto got = host;
    dev.download_to(got);

    const auto want = static_cast<const Grid2D<Real, MhdNVars>&>(oracle).view();
    const auto have = static_cast<const Grid2D<Real, MhdNVars>&>(got).view();
    for (int j = 0; j < got.ny; ++j) {
        for (int i = 0; i < got.nx; ++i) {
            for (int v = 0; v < MhdNVars; ++v) {
                REQUIRE(have(i, j, v) == want(i, j, v));
            }
        }
    }
}

template <typename Real>
void require_glm_noop_is_bit_exact() {
    auto host = make_glm_grid<Real>();
    GpuGrid<Real, MhdNVars> dev(host);
    glm_damp_mhd_gpu(dev, Real(0), Real(0.18), Real(0.004));

    auto got = host;
    dev.download_to(got);
    REQUIRE(byte_equal(got, host));
}

} // namespace

TEST_CASE("MHD GPU GLM damping matches CPU damping", "[gpu][mhd][glm]") {
    require_glm_damp_matches_cpu<double>();
    require_glm_damp_matches_cpu<float>();
}

TEST_CASE("MHD GPU GLM damping no-op stays bit exact", "[gpu][mhd][glm]") {
    require_glm_noop_is_bit_exact<double>();
    require_glm_noop_is_bit_exact<float>();
}

#endif // HRSC_HAS_CUDA
