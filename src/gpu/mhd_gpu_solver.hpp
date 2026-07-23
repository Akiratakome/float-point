// src/gpu/mhd_gpu_solver.hpp
//
// CUDA-enabled MHD HLL solver surface. The implementation is hidden from
// CPU-only builds by HRSC_HAS_CUDA; CPU MHD numerics and defaults remain in
// src/mhd.

#pragma once

#ifdef HRSC_HAS_CUDA

#include "core/boundary.hpp"
#include "core/grid.hpp"
#include "core/types.hpp"
#include "gpu/gpu_grid.cuh"
#include "mhd/mhd_state.hpp"

namespace hrsc {

template <typename Real>
class MhdGpuSolver {
public:
    MhdGpuSolver(Grid2D<Real, MhdNVars> grid,
                 Real xmin, Real ymin, Real gamma, Real cfl,
                 TimeReal t_end, Real glm_cr,
                 BoundaryType bc_x, BoundaryType bc_y);

    void step(TimeReal dt);
    double run();

    Grid2D<Real, MhdNVars> download_host_grid() const;

    TimeReal current_time() const { return m_time; }
    int      step_count() const { return m_step; }

private:
    Grid2D<Real, MhdNVars> m_host_grid;
    GpuGrid<Real, MhdNVars> m_dev_grid;
    Real m_xmin;
    Real m_ymin;
    Real m_gamma;
    Real m_cfl;
    Real m_glm_cr;
    TimeReal m_t_end;
    TimeReal m_time;
    int m_step;
    BoundaryType m_bc_x;
    BoundaryType m_bc_y;
};

extern template class MhdGpuSolver<float>;
extern template class MhdGpuSolver<double>;

} // namespace hrsc

#endif // HRSC_HAS_CUDA
