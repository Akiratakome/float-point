// src/gpu/mhd_kernels.cuh
//
// CUDA MHD kernel declarations land here as the GPU HLL MHD implementation
// grows under tests.

#pragma once

#include "core/boundary.hpp"
#include "core/grid.hpp"
#include "core/vec.hpp"
#include "mhd/mhd_state.hpp"

#ifdef HRSC_HAS_CUDA
#include "gpu/gpu_grid.cuh"

namespace hrsc {

template <typename Real>
void apply_outflow_bc_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Axis axis);

template <typename Real>
void apply_periodic_bc_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Axis axis);

template <typename Real>
void sweep_x_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real dt, Real gamma, Real ch);

template <typename Real>
void sweep_y_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real dt, Real gamma, Real ch);

template <typename Real>
void glm_damp_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real ch, Real cr, Real dt);

template <typename Real>
TimeReal compute_dt_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real gamma, Real cfl);

template <typename Real>
Real compute_ch_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real gamma);

extern template void apply_outflow_bc_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, Axis axis);
extern template void apply_outflow_bc_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, Axis axis);

extern template void apply_periodic_bc_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, Axis axis);
extern template void apply_periodic_bc_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, Axis axis);

extern template void sweep_x_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float dt, float gamma, float ch);
extern template void sweep_x_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double dt, double gamma, double ch);

extern template void sweep_y_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float dt, float gamma, float ch);
extern template void sweep_y_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double dt, double gamma, double ch);

extern template void glm_damp_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float ch, float cr, float dt);
extern template void glm_damp_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double ch, double cr, double dt);

extern template TimeReal compute_dt_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float gamma, float cfl);
extern template TimeReal compute_dt_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double gamma, double cfl);

extern template float compute_ch_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float gamma);
extern template double compute_ch_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double gamma);

} // namespace hrsc

#endif // HRSC_HAS_CUDA
