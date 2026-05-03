// src/gpu/euler_kernels.cuh
//
// Week 5 GPU data-path placeholder. Real Euler kernels land later; this copy
// kernel verifies host-device allocation, launch, and copy-back plumbing.

#pragma once

#include "core/boundary.hpp"
#include "core/eos.hpp"
#include "core/grid.hpp"

#ifdef HRSC_HAS_CUDA
#include "gpu/gpu_grid.cuh"
#endif

#include <cstddef>

namespace hrsc {

#ifdef __CUDACC__
template <typename T>
__global__ void device_copy_kernel(const T* in, T* out, std::size_t n) {
    const std::size_t i =
        static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (i < n) out[i] = in[i];
}
#endif

#ifdef HRSC_HAS_CUDA
template <typename Real>
void apply_outflow_bc_gpu(GpuGrid<Real, EulerNVars>& g, Axis axis);

template <typename Real>
void apply_periodic_bc_gpu(GpuGrid<Real, EulerNVars>& g, Axis axis);

template <typename Real>
void apply_reflective_bc_gpu(GpuGrid<Real, EulerNVars>& g, Axis axis);

extern template void apply_outflow_bc_gpu<float>(
    GpuGrid<float, EulerNVars>& g, Axis axis);
extern template void apply_outflow_bc_gpu<double>(
    GpuGrid<double, EulerNVars>& g, Axis axis);

extern template void apply_periodic_bc_gpu<float>(
    GpuGrid<float, EulerNVars>& g, Axis axis);
extern template void apply_periodic_bc_gpu<double>(
    GpuGrid<double, EulerNVars>& g, Axis axis);

extern template void apply_reflective_bc_gpu<float>(
    GpuGrid<float, EulerNVars>& g, Axis axis);
extern template void apply_reflective_bc_gpu<double>(
    GpuGrid<double, EulerNVars>& g, Axis axis);
#endif

} // namespace hrsc
