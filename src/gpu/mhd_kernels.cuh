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

extern template void sweep_x_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float dt, float gamma, float ch);
extern template void sweep_x_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double dt, double gamma, double ch);

} // namespace hrsc

#endif // HRSC_HAS_CUDA
