#include "gpu/mhd_kernels.cuh"

#include "gpu/cuda_utils.cuh"
#include "mhd/mhd_flux.hpp"
#include "mhd/mhd_reconstruct.hpp"

#include <cstddef>
#include <cmath>
#include <utility>

#ifdef HRSC_HAS_CUDA

namespace hrsc {

namespace {

static constexpr int kMhdSweepBlockX = 16;
static constexpr int kMhdSweepBlockY = 16;

template <typename Real>
__device__ int mhd_grid_index(int i, int j, int var, int nx) {
    constexpr int ng = GridView<Real, MhdNVars>::ng;
    const int nx_total = nx + 2 * ng;
    return ((j + ng) * nx_total + (i + ng)) * MhdNVars + var;
}

template <typename Real>
__device__ Vec<Real, MhdNVars> mhd_load_cell_device(const Real* data, int nx,
                                                    int i, int j) {
    Vec<Real, MhdNVars> U{};
    for (int k = 0; k < MhdNVars; ++k) {
        U[k] = data[mhd_grid_index<Real>(i, j, k, nx)];
    }
    return U;
}

__device__ bool mhd_device_isfinite(float x) {
    return isfinite(x);
}

__device__ bool mhd_device_isfinite(double x) {
    return isfinite(x);
}

__device__ float mhd_device_abs(float x) {
    return fabsf(x);
}

__device__ double mhd_device_abs(double x) {
    return fabs(x);
}

template <typename Real>
__device__ bool mhd_is_physical_device(const Vec<Real, MhdNVars>& U,
                                       Real gamma) {
    for (int k = 0; k < MhdNVars; ++k) {
        if (!mhd_device_isfinite(U[k])) {
            return false;
        }
    }
    if (!(U[MhdIdx::RHO] > Real(0))) {
        return false;
    }
    const Real p = pressure(U, gamma);
    return mhd_device_isfinite(p) && p > Real(0);
}

template <typename Real>
__device__ Real mhd_device_min(Real a, Real b) {
    return (b < a) ? b : a;
}

template <typename Real>
__device__ Real mhd_device_max(Real a, Real b) {
    return (a < b) ? b : a;
}

template <typename Real>
__device__ Real mhd_signal_speed_device(const Real* data, int nx, int ny,
                                        int i, int j, Real gamma) {
    const Vec<Real, MhdNVars> U = mhd_load_cell_device(data, nx, i, j);
    const MhdPrim<Real> w = cons_to_prim(U, gamma);
    Real ch = mhd_device_abs(w.vx) + fast_speed_x(w, gamma);
    if (ny > 1) {
        ch = mhd_device_max(
            ch,
            mhd_device_abs(w.vy) + fast_speed_x(mhd_swap_xy_prim(w), gamma));
    }
    return ch;
}

template <typename Real>
__device__ Vec<Real, MhdNVars> mhd_hll_flux_device(
    const Vec<Real, MhdNVars>& UL, const Vec<Real, MhdNVars>& UR,
    Real gamma, Real ch) {
    const MhdPrim<Real> wl = cons_to_prim(UL, gamma);
    const MhdPrim<Real> wr = cons_to_prim(UR, gamma);
    const Real cfL = fast_speed_x(wl, gamma);
    const Real cfR = fast_speed_x(wr, gamma);

    const Real SL = mhd_device_min(
        mhd_device_min(wl.vx - cfL, wr.vx - cfR), -ch);
    const Real SR = mhd_device_max(
        mhd_device_max(wr.vx + cfR, wl.vx + cfL), ch);

    const Vec<Real, MhdNVars> FL = mhd_flux_x(UL, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(UR, gamma, ch);

#ifdef RIEMANN_STRICT_INEQUALITY
    if (SL > Real(0)) return FL;
    if (SR < Real(0)) return FR;
#else
    if (SL >= Real(0)) return FL;
    if (SR <= Real(0)) return FR;
#endif

    Vec<Real, MhdNVars> F{};
    const Real inv = Real(1) / (SR - SL);
    for (int k = 0; k < MhdNVars; ++k) {
        F[k] = (SR * FL[k] - SL * FR[k] + SL * SR * (UR[k] - UL[k])) * inv;
    }
    return F;
}

template <typename Real>
__device__ void mhd_predict_faces_device(const Vec<Real, MhdNVars>& Um,
                                         const Vec<Real, MhdNVars>& U0,
                                         const Vec<Real, MhdNVars>& Up,
                                         Real dt, Real gamma, Real ch, Real h,
                                         Vec<Real, MhdNVars>& left,
                                         Vec<Real, MhdNVars>& right) {
    const Vec<Real, MhdNVars> slope = mhd_slope(Um, U0, Up);

    left = U0 - Real(0.5) * slope;
    right = U0 + Real(0.5) * slope;

    if (!mhd_is_physical_device(left, gamma) ||
        !mhd_is_physical_device(right, gamma)) {
        left = U0;
        right = U0;
        return;
    }

    const Vec<Real, MhdNVars> FL = mhd_flux_x(left, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(right, gamma, ch);
    const Real half_dtdx = Real(0.5) * dt / h;

    for (int k = 0; k < MhdNVars; ++k) {
        const Real predictor = half_dtdx * (FR[k] - FL[k]);
        left[k] -= predictor;
        right[k] -= predictor;
    }

    if (!mhd_is_physical_device(left, gamma) ||
        !mhd_is_physical_device(right, gamma)) {
        left = U0;
        right = U0;
    }
}

template <typename Real>
__global__ void mhd_hll_face_x_kernel(
    const Real* data, int nx, int ny, Real dt, Real dx, Real gamma, Real ch,
    Vec<Real, MhdNVars>* flux_x) {
    const int iface = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (iface > nx || j >= ny) return;

    const int iL = iface - 1;
    const int iR = iface;

    Vec<Real, MhdNVars> left_cell_left{}, left_cell_right{};
    Vec<Real, MhdNVars> right_cell_left{}, right_cell_right{};
    mhd_predict_faces_device(mhd_load_cell_device(data, nx, iL - 1, j),
                             mhd_load_cell_device(data, nx, iL, j),
                             mhd_load_cell_device(data, nx, iL + 1, j),
                             dt, gamma, ch, dx,
                             left_cell_left, left_cell_right);
    mhd_predict_faces_device(mhd_load_cell_device(data, nx, iR - 1, j),
                             mhd_load_cell_device(data, nx, iR, j),
                             mhd_load_cell_device(data, nx, iR + 1, j),
                             dt, gamma, ch, dx,
                             right_cell_left, right_cell_right);

    flux_x[j * (nx + 1) + iface] =
        mhd_hll_flux_device(left_cell_right, right_cell_left, gamma, ch);
}

template <typename Real>
__global__ void mhd_update_x_kernel(Real* data, int nx, int ny,
                                    const Vec<Real, MhdNVars>* flux_x,
                                    Real dtdx) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i >= nx || j >= ny) return;

    const int row_base = j * (nx + 1);
    const Vec<Real, MhdNVars> fL = flux_x[row_base + i];
    const Vec<Real, MhdNVars> fR = flux_x[row_base + i + 1];
    for (int k = 0; k < MhdNVars; ++k) {
        data[mhd_grid_index<Real>(i, j, k, nx)] -= dtdx * (fR[k] - fL[k]);
    }
}

template <typename Real>
__global__ void mhd_glm_damp_kernel(Real* data, int nx, int ny, Real factor) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i >= nx || j >= ny) return;

    data[mhd_grid_index<Real>(i, j, MhdIdx::PSI, nx)] *= factor;
}

template <typename Real>
__global__ void mhd_signal_block_max_kernel(const Real* data, int nx, int ny,
                                            Real gamma, Real* block_max) {
    extern __shared__ unsigned char shared_raw[];
    Real* shared_max = reinterpret_cast<Real*>(shared_raw);

    const int tid = threadIdx.x;
    const int global_tid = blockIdx.x * blockDim.x + tid;
    const int stride = blockDim.x * gridDim.x;
    const int ncells = nx * ny;

    Real local_max = Real(0);
    for (int cell = global_tid; cell < ncells; cell += stride) {
        const int i = cell % nx;
        const int j = cell / nx;
        local_max = mhd_device_max(
            local_max, mhd_signal_speed_device(data, nx, ny, i, j, gamma));
    }

    shared_max[tid] = local_max;
    __syncthreads();

    for (int offset = blockDim.x / 2; offset > 0; offset >>= 1) {
        if (tid < offset) {
            shared_max[tid] =
                mhd_device_max(shared_max[tid], shared_max[tid + offset]);
        }
        __syncthreads();
    }

    if (tid == 0) {
        block_max[blockIdx.x] = shared_max[0];
    }
}

template <typename Real>
__global__ void mhd_reduce_max_kernel(const Real* in, int n, Real* out) {
    extern __shared__ unsigned char shared_raw[];
    Real* shared_max = reinterpret_cast<Real*>(shared_raw);

    const int tid = threadIdx.x;
    const int global_tid = blockIdx.x * blockDim.x + tid;
    const int stride = blockDim.x * gridDim.x;

    Real local_max = Real(0);
    for (int idx = global_tid; idx < n; idx += stride) {
        local_max = mhd_device_max(local_max, in[idx]);
    }

    shared_max[tid] = local_max;
    __syncthreads();

    for (int offset = blockDim.x / 2; offset > 0; offset >>= 1) {
        if (tid < offset) {
            shared_max[tid] =
                mhd_device_max(shared_max[tid], shared_max[tid + offset]);
        }
        __syncthreads();
    }

    if (tid == 0) {
        out[blockIdx.x] = shared_max[0];
    }
}

} // namespace

template <typename Real>
void sweep_x_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real dt, Real gamma, Real ch) {
    const int nx = g.nx();
    const int ny = g.ny();
    const std::size_t nface =
        static_cast<std::size_t>(nx + 1) * static_cast<std::size_t>(ny);

    DeviceArray<Vec<Real, MhdNVars>> flux_x(nface);

    const dim3 threads(kMhdSweepBlockX, kMhdSweepBlockY);
    const dim3 face_blocks(((nx + 1) + threads.x - 1) / threads.x,
                           (ny + threads.y - 1) / threads.y);
    mhd_hll_face_x_kernel<Real><<<face_blocks, threads>>>(
        g.data(), nx, ny, dt, g.dx(), gamma, ch, flux_x.data());
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());

    const Real dtdx = dt / g.dx();
    const dim3 update_blocks((nx + threads.x - 1) / threads.x,
                             (ny + threads.y - 1) / threads.y);
    mhd_update_x_kernel<Real><<<update_blocks, threads>>>(
        g.data(), nx, ny, flux_x.data(), dtdx);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void glm_damp_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real ch, Real cr, Real dt) {
    if (ch <= Real(0) || cr <= Real(0)) {
        return;
    }

    const Real factor = std::exp(-dt * (ch / cr));
    const dim3 threads(kMhdSweepBlockX, kMhdSweepBlockY);
    const dim3 blocks((g.nx() + threads.x - 1) / threads.x,
                      (g.ny() + threads.y - 1) / threads.y);
    mhd_glm_damp_kernel<Real><<<blocks, threads>>>(
        g.data(), g.nx(), g.ny(), factor);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
TimeReal compute_dt_mhd_gpu(GpuGrid<Real, MhdNVars>& g, Real gamma, Real cfl) {
    constexpr int threads = 256;
    const int ncells = g.nx() * g.ny();
    int count = (ncells + threads - 1) / threads;
    DeviceArray<Real> current(static_cast<std::size_t>(count));

    mhd_signal_block_max_kernel<Real>
        <<<count, threads, threads * sizeof(Real)>>>(
            g.data(), g.nx(), g.ny(), gamma, current.data());
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());

    while (count > 1) {
        const int next_count = (count + threads - 1) / threads;
        DeviceArray<Real> next(static_cast<std::size_t>(next_count));
        mhd_reduce_max_kernel<Real>
            <<<next_count, threads, threads * sizeof(Real)>>>(
                current.data(), count, next.data());
        HRSC_CUDA_CHECK(cudaGetLastError());
        HRSC_CUDA_CHECK(cudaDeviceSynchronize());
        current = std::move(next);
        count = next_count;
    }

    Real ch = Real(0);
    current.copy_to_host(&ch, 1);

    const Real denom = (ch < Real(1e-30)) ? Real(1e-30) : ch;
    const Real h = (g.ny() > 1)
                       ? ((g.dy() < g.dx()) ? g.dy() : g.dx())
                       : g.dx();
    return static_cast<TimeReal>(cfl) * static_cast<TimeReal>(h) /
           static_cast<TimeReal>(denom);
}

template void sweep_x_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float dt, float gamma, float ch);
template void sweep_x_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double dt, double gamma, double ch);

template void glm_damp_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float ch, float cr, float dt);
template void glm_damp_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double ch, double cr, double dt);

template TimeReal compute_dt_mhd_gpu<float>(
    GpuGrid<float, MhdNVars>& g, float gamma, float cfl);
template TimeReal compute_dt_mhd_gpu<double>(
    GpuGrid<double, MhdNVars>& g, double gamma, double cfl);

} // namespace hrsc

#endif // HRSC_HAS_CUDA
