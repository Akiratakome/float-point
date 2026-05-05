// src/gpu/euler_gpu_solver.cu
//
// Body lives here for two reasons:
// (1) explicit instantiation for {float, double} keeps a single TU paying
//     the kernel-launch boilerplate cost;
// (2) the header's declarations stay behind HRSC_HAS_CUDA, so non-CUDA builds
//     do not parse the CUDA runtime dependencies pulled in by the device grid.

#include "gpu/euler_gpu_solver.hpp"
#include "gpu/euler_kernels.cuh"
#include "utils/timer.hpp"

#include <stdexcept>
#include <utility>

namespace hrsc {

namespace {

// Apply boundary conditions in the order x then y, matching the CPU
// `EulerSolver::apply_boundary_conditions()` in src/euler/euler_solver.cpp.
template <typename Real>
void apply_bcs_gpu(GpuGrid<Real, EulerNVars>& g,
                   BoundaryType bc_x, BoundaryType bc_y) {
    auto apply = [&](Axis axis, BoundaryType bc) {
        switch (bc) {
            case BoundaryType::Outflow:    apply_outflow_bc_gpu<Real>(g, axis); break;
            case BoundaryType::Periodic:   apply_periodic_bc_gpu<Real>(g, axis); break;
            case BoundaryType::Reflective: apply_reflective_bc_gpu<Real>(g, axis); break;
        }
    };
    apply(Axis::X, bc_x);
    apply(Axis::Y, bc_y);
}

} // namespace

template <typename Real>
EulerGpuSolver<Real>::EulerGpuSolver(
    Grid2D<Real, EulerNVars> grid, Real xmin, Real ymin,
    Real gamma, Real cfl, TimeReal t_end,
    FluxScheme flux, BoundaryType bc_x, BoundaryType bc_y)
    : m_host_grid(std::move(grid)),
      m_dev_grid(m_host_grid),
      m_xmin(xmin), m_ymin(ymin),
      m_gamma(gamma), m_cfl(cfl),
      m_t_end(t_end), m_time(0.0), m_kahan_c(0.0), m_step(0),
      m_flux(flux), m_bc_x(bc_x), m_bc_y(bc_y) {}

// EulerGpuSolver::step — mirrors EulerSolver::step in
// src/euler/euler_solver.cpp: BC -> sweep -> [BC -> opposite sweep] ->
// Kahan-compensated time accumulation -> step_count++.
template <typename Real>
void EulerGpuSolver<Real>::step(TimeReal dt) {
    apply_bcs_gpu<Real>(m_dev_grid, m_bc_x, m_bc_y);

    if (dt <= TimeReal(0)) return;

    const Real dt_real = static_cast<Real>(dt);
    if (m_host_grid.ny == 1) {
        // 1D path: x-sweep only, exact backward compatibility with CPU.
        sweep_x_gpu<Real>(m_dev_grid, dt_real, m_gamma, m_flux);
    } else {
        // 2D path: alternating Godunov splitting; BC reapplied between sweeps.
        if ((m_step % 2) == 0) {
            sweep_x_gpu<Real>(m_dev_grid, dt_real, m_gamma, m_flux);
            apply_bcs_gpu<Real>(m_dev_grid, m_bc_x, m_bc_y);
            sweep_y_gpu<Real>(m_dev_grid, dt_real, m_gamma, m_flux);
        } else {
            sweep_y_gpu<Real>(m_dev_grid, dt_real, m_gamma, m_flux);
            apply_bcs_gpu<Real>(m_dev_grid, m_bc_x, m_bc_y);
            sweep_x_gpu<Real>(m_dev_grid, dt_real, m_gamma, m_flux);
        }
    }

    // Kahan compensated summation: matches CPU exactly so a multi-step run
    // produces a bit-identical m_time progression on CPU and GPU.
    const TimeReal y     = dt - m_kahan_c;
    const TimeReal t_new = m_time + y;
    m_kahan_c = (t_new - m_time) - y;
    m_time    = t_new;
    m_step   += 1;
}

template <typename Real>
double EulerGpuSolver<Real>::run() {
    Timer wall;
    wall.start();
    while (m_time < m_t_end) {
        TimeReal dt = compute_dt_gpu<Real>(m_dev_grid, m_gamma, m_cfl);
        if (dt <= TimeReal(0)) break;
        if (m_time + dt > m_t_end) dt = m_t_end - m_time;
        step(dt);
    }
    wall.stop();
    return wall.elapsed_seconds();
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
