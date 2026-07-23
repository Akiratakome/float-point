// src/gpu/mhd_gpu_solver.cu
//
// Stubbed CUDA MHD solver body. Real kernels land behind tests in follow-up
// tasks; this file establishes device residency and explicit instantiation.

#include "gpu/mhd_gpu_solver.hpp"

#ifdef HRSC_HAS_CUDA

#include "gpu/mhd_kernels.cuh"
#include "utils/timer.hpp"

#include <utility>

namespace hrsc {

template <typename Real>
MhdGpuSolver<Real>::MhdGpuSolver(
    Grid2D<Real, MhdNVars> grid,
    Real xmin, Real ymin, Real gamma, Real cfl,
    TimeReal t_end, Real glm_cr,
    BoundaryType bc_x, BoundaryType bc_y)
    : m_host_grid(std::move(grid)),
      m_dev_grid(m_host_grid),
      m_xmin(xmin),
      m_ymin(ymin),
      m_gamma(gamma),
      m_cfl(cfl),
      m_glm_cr(glm_cr),
      m_t_end(t_end),
      m_time(0.0),
      m_step(0),
      m_bc_x(bc_x),
      m_bc_y(bc_y) {}

template <typename Real>
void MhdGpuSolver<Real>::step(TimeReal dt) {
    if (dt <= TimeReal(0)) return;
    m_time += dt;
    m_step += 1;
}

template <typename Real>
double MhdGpuSolver<Real>::run() {
    Timer wall;
    wall.start();
    while (m_time < m_t_end) {
        const TimeReal dt = m_t_end - m_time;
        if (dt <= TimeReal(0)) break;
        step(dt);
    }
    wall.stop();
    return wall.elapsed_seconds();
}

template <typename Real>
Grid2D<Real, MhdNVars> MhdGpuSolver<Real>::download_host_grid() const {
    Grid2D<Real, MhdNVars> out = m_host_grid;
    m_dev_grid.download_to(out);
    return out;
}

template class MhdGpuSolver<float>;
template class MhdGpuSolver<double>;

} // namespace hrsc

#endif // HRSC_HAS_CUDA
