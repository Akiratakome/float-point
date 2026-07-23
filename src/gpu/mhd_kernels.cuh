// src/gpu/mhd_kernels.cuh
//
// CUDA MHD kernel declarations land here as the GPU HLL MHD implementation
// grows under tests.

#pragma once

#include "core/grid.hpp"
#include "core/vec.hpp"
#include "mhd/mhd_state.hpp"

#ifdef HRSC_HAS_CUDA
#include "gpu/gpu_grid.cuh"

namespace hrsc {

template <typename Real>
void sweep_x_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real dt, Real gamma, Real ch);

template <typename Real>
void glm_damp_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real ch, Real cr, Real dt);

template <typename Real>
TimeReal compute_dt_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real gamma, Real cfl);

extern template void sweep_x_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float dt, float gamma, float ch);
extern template void sweep_x_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double dt, double gamma, double ch);

extern template void glm_damp_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float ch, float cr, float dt);
extern template void glm_damp_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double ch, double cr, double dt);

extern template TimeReal compute_dt_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float gamma, float cfl);
extern template TimeReal compute_dt_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double gamma, double cfl);

} // namespace hrsc

#endif // HRSC_HAS_CUDA
