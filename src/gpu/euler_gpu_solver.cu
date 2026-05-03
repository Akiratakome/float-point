// src/gpu/euler_gpu_solver.cu
//
// Body lives here for two reasons:
// (1) explicit instantiation for {float, double} keeps a single TU paying
//     the kernel-launch boilerplate cost;
// (2) the header's declarations stay behind HRSC_HAS_CUDA, so non-CUDA builds
//     do not parse the CUDA runtime dependencies pulled in by the device grid.

#include "gpu/euler_gpu_solver.hpp"
#include "gpu/euler_kernels.cuh"

#include <utility>

namespace hrsc {

template <typename Real>
EulerGpuSolver<Real>::EulerGpuSolver(
    Grid2D<Real, EulerNVars> grid, Real xmin, Real ymin,
    Real gamma, Real cfl, TimeReal t_end,
    FluxScheme flux, BoundaryType bc_x, BoundaryType bc_y)
    : m_host_grid(std::move(grid)),
      m_dev_grid(m_host_grid),
      m_xmin(xmin), m_ymin(ymin),
      m_gamma(gamma), m_cfl(cfl),
      m_t_end(t_end), m_time(0.0), m_step(0),
      m_flux(flux), m_bc_x(bc_x), m_bc_y(bc_y) {}

template <typename Real>
void EulerGpuSolver<Real>::step(TimeReal /*dt*/) {
    // Wired in T16. Skeleton is empty so the build links.
}

template <typename Real>
double EulerGpuSolver<Real>::run() {
    return 0.0;  // wired in T16
}

template <typename Real>
Grid2D<Real, EulerNVars> EulerGpuSolver<Real>::download_host_grid() const {
    Grid2D<Real, EulerNVars> out = m_host_grid;
    m_dev_grid.download_to(out);
    return out;
}

template class EulerGpuSolver<float>;
template class EulerGpuSolver<double>;

} // namespace hrsc
