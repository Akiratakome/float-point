// tests/unit/gpu_roundtrip_kernel.cu
//
// Extern-C wrappers callable from the plain C++ Catch2 driver. This keeps
// Catch2 away from nvcc while exercising DeviceArray<T> and a CUDA kernel.

#include "gpu/cuda_utils.cuh"
#include "gpu/euler_kernels.cuh"

#include <cuda_runtime.h>

#include <cstddef>

namespace {

template <typename T>
bool roundtrip_impl(const T* host_in, T* host_out, std::size_t n) {
    using namespace hrsc;

    if (n == 0) return true;

    constexpr int block_size = 256;
    const int grid_size = static_cast<int>((n + block_size - 1) / block_size);

    DeviceArray<T> in(n);
    DeviceArray<T> out(n);

    in.copy_from_host(host_in, n);

    device_copy_kernel<T><<<grid_size, block_size>>>(in.data(), out.data(), n);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());

    out.copy_to_host(host_out, n);
    return true;
}

} // namespace

extern "C" bool gpu_roundtrip_double(const double* host_in, double* host_out,
                                     std::size_t n) {
    try {
        return roundtrip_impl<double>(host_in, host_out, n);
    } catch (...) {
        return false;
    }
}

extern "C" bool gpu_roundtrip_float(const float* host_in, float* host_out,
                                    std::size_t n) {
    try {
        return roundtrip_impl<float>(host_in, host_out, n);
    } catch (...) {
        return false;
    }
}
