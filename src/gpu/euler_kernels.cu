// src/gpu/euler_kernels.cu

#include "gpu/euler_kernels.cuh"

#include "gpu/cuda_utils.cuh"

namespace hrsc {

namespace {

template <typename Real>
__device__ int grid_index(int i, int j, int var, int nx) {
    constexpr int ng = GridView<Real, EulerNVars>::ng;
    const int nx_total = nx + 2 * ng;
    return ((j + ng) * nx_total + (i + ng)) * EulerNVars + var;
}

template <typename Real>
__global__ void outflow_x_kernel(Real* data, int nx, int ny) {
    constexpr int ng = GridView<Real, EulerNVars>::ng;
    const int row = blockIdx.x * blockDim.x + threadIdx.x;
    const int rows = ny + 2 * ng;
    if (row >= rows) return;

    const int j = row - ng;
    const int js = (j < 0) ? 0 : (j >= ny ? ny - 1 : j);
    for (int var = 0; var < EulerNVars; ++var) {
        for (int g = 1; g <= ng; ++g) {
            data[grid_index<Real>(-g, j, var, nx)] =
                data[grid_index<Real>(0, js, var, nx)];
            data[grid_index<Real>(nx - 1 + g, j, var, nx)] =
                data[grid_index<Real>(nx - 1, js, var, nx)];
        }
    }
}

template <typename Real>
__global__ void outflow_y_kernel(Real* data, int nx, int ny) {
    constexpr int ng = GridView<Real, EulerNVars>::ng;
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int cols = nx + 2 * ng;
    if (col >= cols) return;

    const int i = col - ng;
    for (int var = 0; var < EulerNVars; ++var) {
        for (int g = 1; g <= ng; ++g) {
            data[grid_index<Real>(i, -g, var, nx)] =
                data[grid_index<Real>(i, 0, var, nx)];
            data[grid_index<Real>(i, ny - 1 + g, var, nx)] =
                data[grid_index<Real>(i, ny - 1, var, nx)];
        }
    }
}

template <typename Real>
__global__ void periodic_x_kernel(Real* data, int nx, int ny) {
    constexpr int ng = GridView<Real, EulerNVars>::ng;
    const int row = blockIdx.x * blockDim.x + threadIdx.x;
    const int rows = ny + 2 * ng;
    if (row >= rows) return;

    const int j = row - ng;
    const int js = ((j % ny) + ny) % ny;
    for (int var = 0; var < EulerNVars; ++var) {
        for (int g = 1; g <= ng; ++g) {
            const int src_left = ((nx - g) % nx + nx) % nx;
            const int src_right = ((g - 1) % nx + nx) % nx;
            data[grid_index<Real>(-g, j, var, nx)] =
                data[grid_index<Real>(src_left, js, var, nx)];
            data[grid_index<Real>(nx - 1 + g, j, var, nx)] =
                data[grid_index<Real>(src_right, js, var, nx)];
        }
    }
}

template <typename Real>
__global__ void periodic_y_kernel(Real* data, int nx, int ny) {
    constexpr int ng = GridView<Real, EulerNVars>::ng;
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int cols = nx + 2 * ng;
    if (col >= cols) return;

    const int i = col - ng;
    for (int var = 0; var < EulerNVars; ++var) {
        for (int g = 1; g <= ng; ++g) {
            const int src_bottom = ((ny - g) % ny + ny) % ny;
            const int src_top = ((g - 1) % ny + ny) % ny;
            data[grid_index<Real>(i, -g, var, nx)] =
                data[grid_index<Real>(i, src_bottom, var, nx)];
            data[grid_index<Real>(i, ny - 1 + g, var, nx)] =
                data[grid_index<Real>(i, src_top, var, nx)];
        }
    }
}

template <typename Real>
__global__ void reflective_x_kernel(Real* data, int nx, int ny) {
    constexpr int ng = GridView<Real, EulerNVars>::ng;
    const int row = blockIdx.x * blockDim.x + threadIdx.x;
    const int rows = ny + 2 * ng;
    if (row >= rows) return;

    const int j = row - ng;
    const int js = (j < 0) ? 0 : (j >= ny ? ny - 1 : j);
    for (int var = 0; var < EulerNVars; ++var) {
        for (int g = 1; g <= ng; ++g) {
            data[grid_index<Real>(-g, j, var, nx)] =
                data[grid_index<Real>(g - 1, js, var, nx)];
            data[grid_index<Real>(nx - 1 + g, j, var, nx)] =
                data[grid_index<Real>(nx - g, js, var, nx)];
        }
    }

    for (int g = 1; g <= ng; ++g) {
        data[grid_index<Real>(-g, j, RHOU, nx)] =
            -data[grid_index<Real>(-g, j, RHOU, nx)];
        data[grid_index<Real>(nx - 1 + g, j, RHOU, nx)] =
            -data[grid_index<Real>(nx - 1 + g, j, RHOU, nx)];
    }
}

template <typename Real>
__global__ void reflective_y_kernel(Real* data, int nx, int ny) {
    constexpr int ng = GridView<Real, EulerNVars>::ng;
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int cols = nx + 2 * ng;
    if (col >= cols) return;

    const int i = col - ng;
    for (int var = 0; var < EulerNVars; ++var) {
        for (int g = 1; g <= ng; ++g) {
            data[grid_index<Real>(i, -g, var, nx)] =
                data[grid_index<Real>(i, g - 1, var, nx)];
            data[grid_index<Real>(i, ny - 1 + g, var, nx)] =
                data[grid_index<Real>(i, ny - g, var, nx)];
        }
    }

    for (int g = 1; g <= ng; ++g) {
        data[grid_index<Real>(i, -g, RHOV, nx)] =
            -data[grid_index<Real>(i, -g, RHOV, nx)];
        data[grid_index<Real>(i, ny - 1 + g, RHOV, nx)] =
            -data[grid_index<Real>(i, ny - 1 + g, RHOV, nx)];
    }
}

} // namespace

template <typename Real>
void apply_outflow_bc_gpu(GpuGrid<Real, EulerNVars>& g, Axis axis) {
    constexpr int threads = 128;
    if (axis == Axis::X) {
        constexpr int ng = GridView<Real, EulerNVars>::ng;
        const int rows = g.ny() + 2 * ng;
        const int blocks = (rows + threads - 1) / threads;
        outflow_x_kernel<Real><<<blocks, threads>>>(g.data(), g.nx(), g.ny());
    } else {
        constexpr int ng = GridView<Real, EulerNVars>::ng;
        const int cols = g.nx() + 2 * ng;
        const int blocks = (cols + threads - 1) / threads;
        outflow_y_kernel<Real><<<blocks, threads>>>(g.data(), g.nx(), g.ny());
    }
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void apply_periodic_bc_gpu(GpuGrid<Real, EulerNVars>& g, Axis axis) {
    constexpr int threads = 128;
    if (axis == Axis::X) {
        constexpr int ng = GridView<Real, EulerNVars>::ng;
        const int rows = g.ny() + 2 * ng;
        const int blocks = (rows + threads - 1) / threads;
        periodic_x_kernel<Real><<<blocks, threads>>>(g.data(), g.nx(),
                                                     g.ny());
    } else {
        constexpr int ng = GridView<Real, EulerNVars>::ng;
        const int cols = g.nx() + 2 * ng;
        const int blocks = (cols + threads - 1) / threads;
        periodic_y_kernel<Real><<<blocks, threads>>>(g.data(), g.nx(),
                                                     g.ny());
    }
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void apply_reflective_bc_gpu(GpuGrid<Real, EulerNVars>& g, Axis axis) {
    constexpr int threads = 128;
    if (axis == Axis::X) {
        constexpr int ng = GridView<Real, EulerNVars>::ng;
        const int rows = g.ny() + 2 * ng;
        const int blocks = (rows + threads - 1) / threads;
        reflective_x_kernel<Real><<<blocks, threads>>>(g.data(), g.nx(),
                                                       g.ny());
    } else {
        constexpr int ng = GridView<Real, EulerNVars>::ng;
        const int cols = g.nx() + 2 * ng;
        const int blocks = (cols + threads - 1) / threads;
        reflective_y_kernel<Real><<<blocks, threads>>>(g.data(), g.nx(),
                                                       g.ny());
    }
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template void apply_outflow_bc_gpu<float>(
    GpuGrid<float, EulerNVars>& g, Axis axis);
template void apply_outflow_bc_gpu<double>(
    GpuGrid<double, EulerNVars>& g, Axis axis);

template void apply_periodic_bc_gpu<float>(
    GpuGrid<float, EulerNVars>& g, Axis axis);
template void apply_periodic_bc_gpu<double>(
    GpuGrid<double, EulerNVars>& g, Axis axis);

template void apply_reflective_bc_gpu<float>(
    GpuGrid<float, EulerNVars>& g, Axis axis);
template void apply_reflective_bc_gpu<double>(
    GpuGrid<double, EulerNVars>& g, Axis axis);

} // namespace hrsc
