// src/gpu/mhd_gpu_solver.cu
//
// CUDA MHD solver body. Kernel launch details live in mhd_kernels.cu.

#include "gpu/mhd_gpu_solver.hpp"

#ifdef HRSC_HAS_CUDA

#include "gpu/mhd_kernels.cuh"
#include "utils/timer.hpp"

#include <stdexcept>
#include <utility>

namespace hrsc {

namespace {

template <typename Real>
void apply_bcs_mhd_gpu(GpuGrid<Real, MhdNVars>& g,
                       BoundaryType bc_x, BoundaryType bc_y) {
    if (bc_x == BoundaryType::Outflow) {
        apply_outflow_bc_mhd_gpu<Real>(g, Axis::X);
    } else if (bc_x == BoundaryType::Periodic) {
        apply_periodic_bc_mhd_gpu<Real>(g, Axis::X);
    } else {
        throw std::logic_error("MhdGpuSolver currently supports only outflow/periodic X BC");
    }

    if (g.ny() > 1) {
        if (bc_y == BoundaryType::Outflow) {
            apply_outflow_bc_mhd_gpu<Real>(g, Axis::Y);
        } else if (bc_y == BoundaryType::Periodic) {
            apply_periodic_bc_mhd_gpu<Real>(g, Axis::Y);
        } else {
            throw std::logic_error("MhdGpuSolver currently supports only outflow/periodic Y BC");
        }
    } else {
        (void)bc_y;
    }
}

template <typename Real>
TimeReal mhd_dt_from_ch(GpuGrid<Real, MhdNVars>& g, Real cfl, Real ch) {
    const Real denom = (ch < Real(1e-30)) ? Real(1e-30) : ch;
    const Real h = (g.ny() > 1)
                       ? ((g.dy() < g.dx()) ? g.dy() : g.dx())
                       : g.dx();
    return static_cast<TimeReal>(cfl) * static_cast<TimeReal>(h) /
           static_cast<TimeReal>(denom);
}

} // namespace

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

    apply_bcs_mhd_gpu<Real>(m_dev_grid, m_bc_x, m_bc_y);
    const Real ch = compute_ch_mhd_gpu<Real>(m_dev_grid, m_gamma);
    const Real dt_real = static_cast<Real>(dt);
    sweep_x_mhd_gpu<Real>(m_dev_grid, dt_real, m_gamma, ch);
    if (m_dev_grid.ny() > 1) {
        apply_bcs_mhd_gpu<Real>(m_dev_grid, m_bc_x, m_bc_y);
        sweep_y_mhd_gpu<Real>(m_dev_grid, dt_real, m_gamma, ch);
    }
    glm_damp_mhd_gpu<Real>(m_dev_grid, ch, m_glm_cr, dt_real);

    m_time += dt;
    m_step += 1;
}

template <typename Real>
double MhdGpuSolver<Real>::run() {
    Timer wall;
    wall.start();
    while (m_time < m_t_end) {
        apply_bcs_mhd_gpu<Real>(m_dev_grid, m_bc_x, m_bc_y);
        const Real ch = compute_ch_mhd_gpu<Real>(m_dev_grid, m_gamma);
        TimeReal dt = mhd_dt_from_ch<Real>(m_dev_grid, m_cfl, ch);
        if (dt <= TimeReal(0)) break;
        if (m_time + dt > m_t_end) {
            dt = m_t_end - m_time;
        }

        const Real dt_real = static_cast<Real>(dt);
        sweep_x_mhd_gpu<Real>(m_dev_grid, dt_real, m_gamma, ch);
        if (m_dev_grid.ny() > 1) {
            apply_bcs_mhd_gpu<Real>(m_dev_grid, m_bc_x, m_bc_y);
            sweep_y_mhd_gpu<Real>(m_dev_grid, dt_real, m_gamma, ch);
        }
        glm_damp_mhd_gpu<Real>(m_dev_grid, ch, m_glm_cr, dt_real);
        m_time += dt;
        m_step += 1;
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
