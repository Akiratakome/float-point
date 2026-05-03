// tests/unit/gpu_layout_kernel.cu
//
// Extern-C CUDA launcher used by test_gpu_grid_layout.cpp.

#include "gpu/cuda_utils.cuh"

#include <cuda_runtime.h>

namespace {

__global__ void layout_writer_kernel(double* dev, int nx_total, int ny_total,
                                     int nvars, double base) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    const int total = nx_total * ny_total * nvars;
    if (idx >= total) return;

    const int var = idx % nvars;
    const int cell = idx / nvars;
    const int i = cell % nx_total;
    const int j = cell / nx_total;
    dev[idx] = base + static_cast<double>(i * 1000 + j * 10 + var);
}

} // namespace

extern "C" void launch_layout_writer(double* dev, int nx_total, int ny_total,
                                      int nvars, double base) {
    constexpr int block_size = 256;
    const int total = nx_total * ny_total * nvars;
    const int grid_size = (total + block_size - 1) / block_size;

    layout_writer_kernel<<<grid_size, block_size>>>(dev, nx_total, ny_total,
                                                    nvars, base);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}
