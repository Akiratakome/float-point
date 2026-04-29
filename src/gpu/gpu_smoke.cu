// src/gpu/gpu_smoke.cu
//
// Day-1 toolchain validation. Standalone target - NOT linked into the main
// hrsc binary. Just confirms nvcc compiles, host-compiler integration works,
// and runtime sees at least one GPU.

#include <cstdio>
#include <cuda_runtime.h>

int main() {
    int count = 0;
    cudaError_t err = cudaGetDeviceCount(&count);
    if (err != cudaSuccess) {
        std::fprintf(stderr, "cudaGetDeviceCount failed: %s\n",
                     cudaGetErrorString(err));
        return 1;
    }
    std::printf("CUDA devices detected: %d\n", count);
    for (int i = 0; i < count; ++i) {
        cudaDeviceProp p{};
        if (cudaGetDeviceProperties(&p, i) == cudaSuccess) {
            std::printf("  [%d] %s  (compute capability %d.%d)\n",
                        i, p.name, p.major, p.minor);
        }
    }
    return count > 0 ? 0 : 2;
}
