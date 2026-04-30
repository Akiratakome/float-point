// src/gpu/euler_kernels.cuh
//
// Week 5 GPU data-path placeholder. Real Euler kernels land later; this copy
// kernel verifies host-device allocation, launch, and copy-back plumbing.

#pragma once

#include <cstddef>

namespace hrsc {

template <typename T>
__global__ void device_copy_kernel(const T* in, T* out, std::size_t n) {
    const std::size_t i =
        static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (i < n) out[i] = in[i];
}

} // namespace hrsc
