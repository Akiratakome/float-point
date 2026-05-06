// src/gpu/euler_gpu_solver.hpp
//
// EulerGpuSolver<Real>: device-resident analogue of EulerSolver<Real>.
// This is the planned GPU-facing surface for future
// std::variant<EulerSolver<Real>, EulerGpuSolver<Real>> dispatch work, not a
// byte-for-byte mirror of the current CPU solver API. See
// docs/week6/week6-design.md section 3.2 for rationale.
//
// This file declares only and is hidden from non-CUDA builds by
// HRSC_HAS_CUDA. CUDA-enabled host TUs may see CUDA runtime dependencies
// through GpuGrid until later dispatch tasks refine the interface. Method
// bodies and explicit instantiations live in euler_gpu_solver.cu.

#pragma once

#ifdef HRSC_HAS_CUDA

#include "core/grid.hpp"
#include "core/types.hpp"
#include "core/boundary.hpp"
#include "euler/euler_solver.hpp"  // FluxScheme enum reuse
#include "gpu/gpu_grid.cuh"

namespace hrsc {

template <typename Real>
class EulerGpuSolver {
public:
    EulerGpuSolver(Grid2D<Real, EulerNVars> grid,
                   Real xmin, Real ymin,
                   Real gamma, Real cfl,
                   TimeReal t_end,
                   FluxScheme flux,
                   BoundaryType bc_x, BoundaryType bc_y);

    // step(dt): advance by exactly one MUSCL-Hancock-Lie step.
    void step(TimeReal dt);

    // run(): time-loop until t_end; returns final wall-clock seconds.
    double run();

    // For IO / regression: D2H copy into and return a refreshed host grid copy.
    Grid2D<Real, EulerNVars> download_host_grid() const;

    TimeReal current_time() const { return m_time; }
    int      step_count()   const { return m_step; }

private:
    Grid2D<Real, EulerNVars> m_host_grid;   // shape mirror; data D2H-refreshed lazily
    GpuGrid<Real, EulerNVars> m_dev_grid;
    Real         m_xmin, m_ymin;
    Real         m_gamma, m_cfl;
    TimeReal     m_t_end;
    TimeReal     m_time;
    TimeReal     m_kahan_c;  // Kahan compensated summation correction (mirrors CPU)
    int          m_step;
    FluxScheme   m_flux;
    BoundaryType m_bc_x, m_bc_y;
};

extern template class EulerGpuSolver<float>;
extern template class EulerGpuSolver<double>;

} // namespace hrsc

#endif // HRSC_HAS_CUDA
