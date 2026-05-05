// src/gpu/euler_kernels.cu

#include "gpu/euler_kernels.cuh"

#include "euler/euler_flux.hpp"
#include "euler/muscl.hpp"
#include "euler/rusanov.hpp"
#include "gpu/cuda_utils.cuh"

#include <cstring>
#include <limits>
#include <stdexcept>

namespace hrsc {

namespace {

// Block dim shared by both MUSCL reconstruction launchers (X and Y).
// Using plain int constants because CUDA's `dim3` ctor is not constexpr.
static constexpr int kReconstructBlockX = 16;
static constexpr int kReconstructBlockY = 16;

template <typename Real>
__device__ int grid_index(int i, int j, int var, int nx) {
    constexpr int ng = GridView<Real, EulerNVars>::ng;
    const int nx_total = nx + 2 * ng;
    return ((j + ng) * nx_total + (i + ng)) * EulerNVars + var;
}

__device__ unsigned long long double_to_ordered_bits(double x) {
    return static_cast<unsigned long long>(__double_as_longlong(x));
}

__host__ unsigned long long double_to_ordered_bits_host(double x) {
    unsigned long long bits = 0;
    std::memcpy(&bits, &x, sizeof(bits));
    return bits;
}

__host__ double ordered_bits_to_double_host(unsigned long long bits) {
    double x = 0.0;
    std::memcpy(&x, &bits, sizeof(x));
    return x;
}

__device__ void atomic_min_positive_double(unsigned long long* addr,
                                           double value) {
    const unsigned long long value_bits = double_to_ordered_bits(value);
    unsigned long long old = *addr;
    while (value_bits < old) {
        const unsigned long long assumed = old;
        old = atomicCAS(addr, assumed, value_bits);
        if (old == assumed) return;
    }
}

__device__ float device_abs(float x) {
    return fabsf(x);
}

__device__ double device_abs(double x) {
    return fabs(x);
}

__device__ float device_sqrt(float x) {
    return sqrtf(x);
}

__device__ double device_sqrt(double x) {
    return sqrt(x);
}

__device__ double reduce_min(double a, double b) {
    return (b < a) ? b : a;
}

template <typename Real>
__global__ void cfl_dt_kernel(const Real* data, int nx, int ny, Real dx,
                              Real dy, Real gamma, Real cfl,
                              unsigned long long* global_min_bits) {
    extern __shared__ double block_dt[];

    const int tid = threadIdx.x;
    const int global_tid = blockIdx.x * blockDim.x + tid;
    const int stride = blockDim.x * gridDim.x;
    const int ncells = nx * ny;
    double local_min = INFINITY;

    for (int cell = global_tid; cell < ncells; cell += stride) {
        const int i = cell % nx;
        const int j = cell / nx;

        const Real rho = data[grid_index<Real>(i, j, RHO, nx)];
        const Real rho_u = data[grid_index<Real>(i, j, RHOU, nx)];
        const Real rho_v = data[grid_index<Real>(i, j, RHOV, nx)];
        const Real energy = data[grid_index<Real>(i, j, EN, nx)];

        const Real u = rho_u / rho;
        const Real vel_v = rho_v / rho;
        const Real ke = Real(0.5) * (rho_u * rho_u + rho_v * rho_v) / rho;
        const Real p = (gamma - Real(1)) * (energy - ke);
        const Real a = device_sqrt(gamma * p / rho);
        const Real sx = device_abs(u) + a;
        const Real sy = device_abs(vel_v) + a;

        const double dtx = static_cast<double>(dx) / static_cast<double>(sx);
        const double dty = static_cast<double>(dy) / static_cast<double>(sy);
        const double cell_dt =
            static_cast<double>(cfl) * ((dty < dtx) ? dty : dtx);
        local_min = reduce_min(local_min, cell_dt);
    }

    block_dt[tid] = local_min;
    __syncthreads();

    for (int offset = blockDim.x / 2; offset > 0; offset >>= 1) {
        if (tid < offset) {
            block_dt[tid] =
                reduce_min(block_dt[tid], block_dt[tid + offset]);
        }
        __syncthreads();
    }

    if (tid == 0) {
        atomic_min_positive_double(global_min_bits, block_dt[0]);
    }
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
__global__ void muscl_reconstruct_x_kernel(const Real* data, int nx, int ny,
                                            Vec<Real, EulerNVars>* qL,
                                            Vec<Real, EulerNVars>* qR) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i >= nx || j >= ny) return;

    Vec<Real, EulerNVars> q_left{}, q_right{};
    for (int v = 0; v < EulerNVars; ++v) {
        const Real u_im1 = data[grid_index<Real>(i - 1, j, v, nx)];
        const Real u_i   = data[grid_index<Real>(i,     j, v, nx)];
        const Real u_ip1 = data[grid_index<Real>(i + 1, j, v, nx)];

        const Real backward = u_i - u_im1;
        const Real forward  = u_ip1 - u_i;
        const Real slope    = minbee<Real>(backward, forward);

        q_left[v]  = u_i - Real(0.5) * slope;
        q_right[v] = u_i + Real(0.5) * slope;
    }

    const int idx = j * nx + i;
    qL[idx] = q_left;
    qR[idx] = q_right;
}

template <typename Real>
__global__ void muscl_reconstruct_y_kernel(const Real* data, int nx, int ny,
                                            Vec<Real, EulerNVars>* q_bottom,
                                            Vec<Real, EulerNVars>* q_top) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i >= nx || j >= ny) return;

    Vec<Real, EulerNVars> qB{}, qT{};
    for (int v = 0; v < EulerNVars; ++v) {
        const Real u_jm1 = data[grid_index<Real>(i, j - 1, v, nx)];
        const Real u_j   = data[grid_index<Real>(i, j,     v, nx)];
        const Real u_jp1 = data[grid_index<Real>(i, j + 1, v, nx)];

        const Real backward = u_j - u_jm1;
        const Real forward  = u_jp1 - u_j;
        const Real slope    = minbee<Real>(backward, forward);

        qB[v] = u_j - Real(0.5) * slope;
        qT[v] = u_j + Real(0.5) * slope;
    }

    const int idx = j * nx + i;
    q_bottom[idx] = qB;
    q_top[idx] = qT;
}

template <typename Real>
__global__ void hancock_predict_x_kernel(const Real* data, int nx, int ny,
                                          Real dt, Real dx, Real gamma,
                                          Vec<Real, EulerNVars>* qL,
                                          Vec<Real, EulerNVars>* qR) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i >= nx || j >= ny) return;

    // Step 1: MUSCL reconstruction (same expression tree as CPU oracle).
    Vec<Real, EulerNVars> q_left{}, q_right{};
    for (int v = 0; v < EulerNVars; ++v) {
        const Real u_im1 = data[grid_index<Real>(i - 1, j, v, nx)];
        const Real u_i   = data[grid_index<Real>(i,     j, v, nx)];
        const Real u_ip1 = data[grid_index<Real>(i + 1, j, v, nx)];

        const Real backward = u_i - u_im1;
        const Real forward  = u_ip1 - u_i;
        const Real slope    = minbee<Real>(backward, forward);

        q_left[v]  = u_i - Real(0.5) * slope;
        q_right[v] = u_i + Real(0.5) * slope;
    }

    // Step 2: physical fluxes at both faces.
    Vec<Real, EulerNVars> fL = euler_flux_x<Real>(q_left,  gamma);
    Vec<Real, EulerNVars> fR = euler_flux_x<Real>(q_right, gamma);

    // Step 3: half-step evolution. Match the CPU oracle's expression tree:
    //   half_dtdx = 0.5 * dt / dx;
    //   df = fL - fR;
    //   q += df * half_dtdx;
    const Real half_dtdx = Real(0.5) * dt / dx;
    const Vec<Real, EulerNVars> df = fL - fR;

    q_left  += df * half_dtdx;
    q_right += df * half_dtdx;

    const int idx = j * nx + i;
    qL[idx] = q_left;
    qR[idx] = q_right;
}

template <typename Real>
__global__ void hancock_predict_y_kernel(const Real* data, int nx, int ny,
                                          Real dt, Real dy, Real gamma,
                                          Vec<Real, EulerNVars>* q_bottom,
                                          Vec<Real, EulerNVars>* q_top) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i >= nx || j >= ny) return;

    // Step 1: MUSCL reconstruction (Y-axis).
    Vec<Real, EulerNVars> qB{}, qT{};
    for (int v = 0; v < EulerNVars; ++v) {
        const Real u_jm1 = data[grid_index<Real>(i, j - 1, v, nx)];
        const Real u_j   = data[grid_index<Real>(i, j,     v, nx)];
        const Real u_jp1 = data[grid_index<Real>(i, j + 1, v, nx)];

        const Real backward = u_j - u_jm1;
        const Real forward  = u_jp1 - u_j;
        const Real slope    = minbee<Real>(backward, forward);

        qB[v] = u_j - Real(0.5) * slope;
        qT[v] = u_j + Real(0.5) * slope;
    }

    // Step 2: physical y-fluxes at both faces.
    Vec<Real, EulerNVars> gB = euler_flux_y<Real>(qB, gamma);
    Vec<Real, EulerNVars> gT = euler_flux_y<Real>(qT, gamma);

    // Step 3: half-step evolution using dy.
    const Real half_dtdy = Real(0.5) * dt / dy;
    const Vec<Real, EulerNVars> dg = gB - gT;

    qB += dg * half_dtdy;
    qT += dg * half_dtdy;

    const int idx = j * nx + i;
    q_bottom[idx] = qB;
    q_top[idx]    = qT;
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

// Rusanov (Local Lax-Friedrichs) flux on every X-face. Input buffers qL_face
// and qR_face are sized (nx+1) * ny (linear index j*(nx+1) + k). Output
// flux_x has the same shape. Calls rusanov_flux from src/euler/rusanov.hpp
// (HD_FUNC) per face — no swap_momentum since we're on X-interfaces.
// Inlined Rusanov body: nvcc miscompiles `std::max<Real>` from <algorithm>
// in __global__ context (returns 0 silently), so we expand the algebra here
// using a ternary that matches std::max's behavior on equality (returns
// second arg). All other steps reuse the HD_FUNC primitives directly so the
// expression tree matches the CPU oracle in src/euler/rusanov.hpp.
template <typename Real>
__global__ void rusanov_flux_x_kernel(
    const Vec<Real, EulerNVars>* qL_face,
    const Vec<Real, EulerNVars>* qR_face,
    int nx, int ny, Real gamma,
    Vec<Real, EulerNVars>* flux_x) {
    const int k = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (k > nx || j >= ny) return;
    const int idx = j * (nx + 1) + k;

    const Vec<Real, EulerNVars> qL = qL_face[idx];
    const Vec<Real, EulerNVars> qR = qR_face[idx];
    const Real rhoL = qL[RHO];
    const Real uL   = qL[RHOU] / rhoL;
    const Real pL_  = pressure<Real>(qL, gamma);
    const Real aL   = sound_speed<Real>(rhoL, pL_, gamma);
    const Real rhoR = qR[RHO];
    const Real uR   = qR[RHOU] / rhoR;
    const Real pR_  = pressure<Real>(qR, gamma);
    const Real aR   = sound_speed<Real>(rhoR, pR_, gamma);
    const Real absL = std::abs(uL) + aL;
    const Real absR = std::abs(uR) + aR;
    // std::max(absL, absR): returns absR when absL == absR (second arg).
    const Real S_max = (absL < absR) ? absR : absL;

    const Vec<Real, EulerNVars> FL = euler_flux_x<Real>(qL, gamma);
    const Vec<Real, EulerNVars> FR = euler_flux_x<Real>(qR, gamma);
    Vec<Real, EulerNVars> result{};
    for (int v = 0; v < EulerNVars; ++v) {
        result[v] = (FL[v] + FR[v]) * Real(0.5)
                  - (qR[v] - qL[v]) * (Real(0.5) * S_max);
    }
    flux_x[idx] = result;
}

// Rusanov flux on every Y-face. Buffers qB_face and qT_face are nx * (ny+1)
// (linear index i*(ny+1) + k). Output flux_y has the same shape. Mirrors
// the CPU rotation strategy: swap_momentum on inputs, swap_momentum on
// output — matching src/euler/euler_solver.cpp::y_sweep flux construction.
template <typename Real>
__global__ void rusanov_flux_y_kernel(
    const Vec<Real, EulerNVars>* qB_face,
    const Vec<Real, EulerNVars>* qT_face,
    int nx, int ny, Real gamma,
    Vec<Real, EulerNVars>* flux_y) {
    const int k = blockIdx.x * blockDim.x + threadIdx.x;
    const int i = blockIdx.y * blockDim.y + threadIdx.y;
    if (k > ny || i >= nx) return;
    const int idx = i * (ny + 1) + k;

    // Rotate momentum: y-interface treats RHOV as normal velocity. Mirror
    // src/euler/euler_solver.cpp::y_sweep flux construction.
    const Vec<Real, EulerNVars> qL = swap_momentum<Real>(qB_face[idx]);
    const Vec<Real, EulerNVars> qR = swap_momentum<Real>(qT_face[idx]);
    const Real rhoL = qL[RHO];
    const Real uL   = qL[RHOU] / rhoL;
    const Real pL_  = pressure<Real>(qL, gamma);
    const Real aL   = sound_speed<Real>(rhoL, pL_, gamma);
    const Real rhoR = qR[RHO];
    const Real uR   = qR[RHOU] / rhoR;
    const Real pR_  = pressure<Real>(qR, gamma);
    const Real aR   = sound_speed<Real>(rhoR, pR_, gamma);
    const Real absL = std::abs(uL) + aL;
    const Real absR = std::abs(uR) + aR;
    const Real S_max = (absL < absR) ? absR : absL;

    const Vec<Real, EulerNVars> FL = euler_flux_x<Real>(qL, gamma);
    const Vec<Real, EulerNVars> FR = euler_flux_x<Real>(qR, gamma);
    Vec<Real, EulerNVars> rotated{};
    for (int v = 0; v < EulerNVars; ++v) {
        rotated[v] = (FL[v] + FR[v]) * Real(0.5)
                   - (qR[v] - qL[v]) * (Real(0.5) * S_max);
    }
    flux_y[idx] = swap_momentum<Real>(rotated);
}

// Per-cell Hancock helper for X-axis: minmod reconstruct + half-step flux
// evolution at cell (i, j). Inlined into the per-face kernel below; matches
// the algebra in src/euler/hancock.hpp::muscl_hancock_x line-for-line.
template <typename Real>
__device__ __forceinline__ void hancock_cell_x(
    const Real* data, int i, int j, int nx,
    Real dt, Real dx, Real gamma,
    Vec<Real, EulerNVars>& qL,
    Vec<Real, EulerNVars>& qR) {
    for (int v = 0; v < EulerNVars; ++v) {
        const Real u_im1 = data[grid_index<Real>(i - 1, j, v, nx)];
        const Real u_i   = data[grid_index<Real>(i,     j, v, nx)];
        const Real u_ip1 = data[grid_index<Real>(i + 1, j, v, nx)];
        const Real backward = u_i - u_im1;
        const Real forward  = u_ip1 - u_i;
        const Real slope    = minbee<Real>(backward, forward);
        qL[v] = u_i - Real(0.5) * slope;
        qR[v] = u_i + Real(0.5) * slope;
    }
    const Vec<Real, EulerNVars> fL = euler_flux_x<Real>(qL, gamma);
    const Vec<Real, EulerNVars> fR = euler_flux_x<Real>(qR, gamma);
    const Real half_dtdx = Real(0.5) * dt / dx;
    for (int v = 0; v < EulerNVars; ++v) {
        const Real df = fL[v] - fR[v];
        qL[v] += df * half_dtdx;
        qR[v] += df * half_dtdx;
    }
}

// Per-cell Hancock helper for Y-axis (no momentum rotation here — rotation
// is applied later by rusanov_flux_y_kernel). Mirrors hancock.hpp.
template <typename Real>
__device__ __forceinline__ void hancock_cell_y(
    const Real* data, int i, int j, int nx,
    Real dt, Real dy, Real gamma,
    Vec<Real, EulerNVars>& qB,
    Vec<Real, EulerNVars>& qT) {
    for (int v = 0; v < EulerNVars; ++v) {
        const Real u_jm1 = data[grid_index<Real>(i, j - 1, v, nx)];
        const Real u_j   = data[grid_index<Real>(i, j,     v, nx)];
        const Real u_jp1 = data[grid_index<Real>(i, j + 1, v, nx)];
        const Real backward = u_j - u_jm1;
        const Real forward  = u_jp1 - u_j;
        const Real slope    = minbee<Real>(backward, forward);
        qB[v] = u_j - Real(0.5) * slope;
        qT[v] = u_j + Real(0.5) * slope;
    }
    const Vec<Real, EulerNVars> gB = euler_flux_y<Real>(qB, gamma);
    const Vec<Real, EulerNVars> gT = euler_flux_y<Real>(qT, gamma);
    const Real half_dtdy = Real(0.5) * dt / dy;
    for (int v = 0; v < EulerNVars; ++v) {
        const Real dg = gB[v] - gT[v];
        qB[v] += dg * half_dtdy;
        qT[v] += dg * half_dtdy;
    }
}

// Per-face Hancock kernel for X-axis: for each face k in row j, run Hancock
// on cells k-1 and k and write face-state buffers. Mirrors the inner loop
// in src/euler/euler_solver.cpp::x_sweep flux block (duplicates Hancock per
// cell across faces but keeps a single kernel launch).
template <typename Real>
__global__ void hancock_face_x_kernel(
    const Real* data, int nx, int ny,
    Real dt, Real dx, Real gamma,
    Vec<Real, EulerNVars>* qL_face,
    Vec<Real, EulerNVars>* qR_face) {
    const int k = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (k > nx || j >= ny) return;

    Vec<Real, EulerNVars> qL_left{}, qL_right{};
    Vec<Real, EulerNVars> qR_left{}, qR_right{};
    hancock_cell_x<Real>(data, k - 1, j, nx, dt, dx, gamma, qL_left, qL_right);
    hancock_cell_x<Real>(data, k,     j, nx, dt, dx, gamma, qR_left, qR_right);

    const int idx = j * (nx + 1) + k;
    qL_face[idx] = qL_right;
    qR_face[idx] = qR_left;
}

// Per-face Hancock kernel for Y-axis. No momentum rotation here; rotation
// is applied later by rusanov_flux_y_kernel.
template <typename Real>
__global__ void hancock_face_y_kernel(
    const Real* data, int nx, int ny,
    Real dt, Real dy, Real gamma,
    Vec<Real, EulerNVars>* qB_face,
    Vec<Real, EulerNVars>* qT_face) {
    const int k = blockIdx.x * blockDim.x + threadIdx.x;
    const int i = blockIdx.y * blockDim.y + threadIdx.y;
    if (k > ny || i >= nx) return;

    Vec<Real, EulerNVars> qB_below{}, qT_below{};
    Vec<Real, EulerNVars> qB_above{}, qT_above{};
    hancock_cell_y<Real>(data, i, k - 1, nx, dt, dy, gamma, qB_below, qT_below);
    hancock_cell_y<Real>(data, i, k,     nx, dt, dy, gamma, qB_above, qT_above);

    const int idx = i * (ny + 1) + k;
    qB_face[idx] = qT_below;  // top state of cell k-1 (below the face)
    qT_face[idx] = qB_above;  // bottom state of cell k (above the face)
}

// Conservative update along X: U[i,j] -= dtdx * (flux_x[i+1,j] - flux_x[i,j]).
// flux_x is a per-row contiguous buffer of size (nx+1) * ny; linear index for
// interface k of row j is j*(nx+1) + k. Expression order matches the CPU
// oracle in src/euler/euler_solver.cpp::x_sweep update block.
template <typename Real>
__global__ void apply_update_x_kernel(Real* data, int nx, int ny,
                                      const Vec<Real, EulerNVars>* flux_x,
                                      Real dtdx) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i >= nx || j >= ny) return;

    const int row_base = j * (nx + 1);
    const Vec<Real, EulerNVars> f_prev = flux_x[row_base + i];
    const Vec<Real, EulerNVars> f_next = flux_x[row_base + i + 1];
    for (int v = 0; v < EulerNVars; ++v) {
        data[grid_index<Real>(i, j, v, nx)] -= dtdx * (f_next[v] - f_prev[v]);
    }
}

// Conservative update along Y: U[i,j] -= dtdy * (flux_y[i,j+1] - flux_y[i,j]).
// flux_y is a per-column contiguous buffer of size nx * (ny+1); linear index
// for interface k of column i is i*(ny+1) + k. Matches the CPU oracle in
// src/euler/euler_solver.cpp::y_sweep update block.
template <typename Real>
__global__ void apply_update_y_kernel(Real* data, int nx, int ny,
                                      const Vec<Real, EulerNVars>* flux_y,
                                      Real dtdy) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    const int j = blockIdx.y * blockDim.y + threadIdx.y;
    if (i >= nx || j >= ny) return;

    const int col_base = i * (ny + 1);
    const Vec<Real, EulerNVars> f_prev = flux_y[col_base + j];
    const Vec<Real, EulerNVars> f_next = flux_y[col_base + j + 1];
    for (int v = 0; v < EulerNVars; ++v) {
        data[grid_index<Real>(i, j, v, nx)] -= dtdy * (f_next[v] - f_prev[v]);
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

template <typename Real>
TimeReal compute_dt_gpu(GpuGrid<Real, EulerNVars>& g, Real gamma, Real cfl) {
    constexpr int threads = 256;
    const int cells = g.nx() * g.ny();
    const int blocks = (cells + threads - 1) / threads;
    const double inf = std::numeric_limits<double>::infinity();
    const unsigned long long init_bits = double_to_ordered_bits_host(inf);

    DeviceArray<unsigned long long> global_min_bits(1);
    global_min_bits.copy_from_host(&init_bits, 1);

    cfl_dt_kernel<Real><<<blocks, threads, threads * sizeof(double)>>>(
        g.data(), g.nx(), g.ny(), g.dx(), g.dy(), gamma, cfl,
        global_min_bits.data());
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());

    unsigned long long result_bits = 0;
    global_min_bits.copy_to_host(&result_bits, 1);
    return ordered_bits_to_double_host(result_bits);
}

template <typename Real>
void muscl_reconstruct_x_gpu(GpuGrid<Real, EulerNVars>& g,
                             Vec<Real, EulerNVars>* qL,
                             Vec<Real, EulerNVars>* qR) {
    const dim3 threads(kReconstructBlockX, kReconstructBlockY);
    const dim3 blocks((g.nx() + threads.x - 1) / threads.x,
                      (g.ny() + threads.y - 1) / threads.y);
    muscl_reconstruct_x_kernel<Real><<<blocks, threads>>>(
        g.data(), g.nx(), g.ny(), qL, qR);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void muscl_reconstruct_y_gpu(GpuGrid<Real, EulerNVars>& g,
                             Vec<Real, EulerNVars>* q_bottom,
                             Vec<Real, EulerNVars>* q_top) {
    const dim3 threads(kReconstructBlockX, kReconstructBlockY);
    const dim3 blocks((g.nx() + threads.x - 1) / threads.x,
                      (g.ny() + threads.y - 1) / threads.y);
    muscl_reconstruct_y_kernel<Real><<<blocks, threads>>>(
        g.data(), g.nx(), g.ny(), q_bottom, q_top);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void hancock_predict_x_gpu(GpuGrid<Real, EulerNVars>& g,
                           Real dt, Real gamma,
                           Vec<Real, EulerNVars>* qL,
                           Vec<Real, EulerNVars>* qR) {
    const dim3 threads(kReconstructBlockX, kReconstructBlockY);
    const dim3 blocks((g.nx() + threads.x - 1) / threads.x,
                      (g.ny() + threads.y - 1) / threads.y);
    hancock_predict_x_kernel<Real><<<blocks, threads>>>(
        g.data(), g.nx(), g.ny(), dt, g.dx(), gamma, qL, qR);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void hancock_predict_y_gpu(GpuGrid<Real, EulerNVars>& g,
                           Real dt, Real gamma,
                           Vec<Real, EulerNVars>* q_bottom,
                           Vec<Real, EulerNVars>* q_top) {
    const dim3 threads(kReconstructBlockX, kReconstructBlockY);
    const dim3 blocks((g.nx() + threads.x - 1) / threads.x,
                      (g.ny() + threads.y - 1) / threads.y);
    hancock_predict_y_kernel<Real><<<blocks, threads>>>(
        g.data(), g.nx(), g.ny(), dt, g.dy(), gamma, q_bottom, q_top);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void rusanov_flux_x_gpu(int nx, int ny, Real gamma,
                        const Vec<Real, EulerNVars>* qL_face,
                        const Vec<Real, EulerNVars>* qR_face,
                        Vec<Real, EulerNVars>* flux_x) {
    const dim3 threads(kReconstructBlockX, kReconstructBlockY);
    const dim3 blocks(((nx + 1) + threads.x - 1) / threads.x,
                      (ny + threads.y - 1) / threads.y);
    rusanov_flux_x_kernel<Real><<<blocks, threads>>>(
        qL_face, qR_face, nx, ny, gamma, flux_x);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void rusanov_flux_y_gpu(int nx, int ny, Real gamma,
                        const Vec<Real, EulerNVars>* qB_face,
                        const Vec<Real, EulerNVars>* qT_face,
                        Vec<Real, EulerNVars>* flux_y) {
    const dim3 threads(kReconstructBlockX, kReconstructBlockY);
    const dim3 blocks(((ny + 1) + threads.x - 1) / threads.x,
                      (nx + threads.y - 1) / threads.y);
    rusanov_flux_y_kernel<Real><<<blocks, threads>>>(
        qB_face, qT_face, nx, ny, gamma, flux_y);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void apply_update_x_gpu(GpuGrid<Real, EulerNVars>& g,
                        const Vec<Real, EulerNVars>* flux_x,
                        Real dt) {
    const Real dtdx = dt / g.dx();
    const dim3 threads(kReconstructBlockX, kReconstructBlockY);
    const dim3 blocks((g.nx() + threads.x - 1) / threads.x,
                      (g.ny() + threads.y - 1) / threads.y);
    apply_update_x_kernel<Real><<<blocks, threads>>>(
        g.data(), g.nx(), g.ny(), flux_x, dtdx);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

template <typename Real>
void apply_update_y_gpu(GpuGrid<Real, EulerNVars>& g,
                        const Vec<Real, EulerNVars>* flux_y,
                        Real dt) {
    const Real dtdy = dt / g.dy();
    const dim3 threads(kReconstructBlockX, kReconstructBlockY);
    const dim3 blocks((g.nx() + threads.x - 1) / threads.x,
                      (g.ny() + threads.y - 1) / threads.y);
    apply_update_y_kernel<Real><<<blocks, threads>>>(
        g.data(), g.nx(), g.ny(), flux_y, dtdy);
    HRSC_CUDA_CHECK(cudaGetLastError());
    HRSC_CUDA_CHECK(cudaDeviceSynchronize());
}

// Bundle: per-face Hancock + Rusanov flux + conservative update along X.
// Allocates transient face/flux buffers internally. Mirrors the CPU x_sweep
// in src/euler/euler_solver.cpp (BC is the caller's responsibility).
template <typename Real>
void sweep_x_gpu(GpuGrid<Real, EulerNVars>& g, Real dt, Real gamma,
                 FluxScheme flux_scheme) {
    const int nx = g.nx();
    const int ny = g.ny();
    const std::size_t nface =
        static_cast<std::size_t>(nx + 1) * static_cast<std::size_t>(ny);

    DeviceArray<Vec<Real, EulerNVars>> qL_face(nface);
    DeviceArray<Vec<Real, EulerNVars>> qR_face(nface);
    DeviceArray<Vec<Real, EulerNVars>> flux_face(nface);

    // Hancock per face.
    {
        const dim3 threads(kReconstructBlockX, kReconstructBlockY);
        const dim3 blocks(((nx + 1) + threads.x - 1) / threads.x,
                          (ny + threads.y - 1) / threads.y);
        hancock_face_x_kernel<Real><<<blocks, threads>>>(
            g.data(), nx, ny, dt, g.dx(), gamma,
            qL_face.data(), qR_face.data());
        HRSC_CUDA_CHECK(cudaGetLastError());
        HRSC_CUDA_CHECK(cudaDeviceSynchronize());
    }

    // Flux per face. T20 will swap in HLLC behind FluxScheme.
    if (flux_scheme == FluxScheme::Rusanov) {
        rusanov_flux_x_gpu<Real>(nx, ny, gamma,
                                 qL_face.data(), qR_face.data(),
                                 flux_face.data());
    } else {
        // HLLC GPU is T20; for now sweep_x_gpu only supports Rusanov.
        throw std::runtime_error(
            "sweep_x_gpu: HLLC FluxScheme not yet wired (Week 6 T20)");
    }

    // Conservative update: U -= (dt/dx) * (flux[k+1] - flux[k]).
    apply_update_x_gpu<Real>(g, flux_face.data(), dt);
}

template <typename Real>
void sweep_y_gpu(GpuGrid<Real, EulerNVars>& g, Real dt, Real gamma,
                 FluxScheme flux_scheme) {
    const int nx = g.nx();
    const int ny = g.ny();
    const std::size_t nface =
        static_cast<std::size_t>(nx) * static_cast<std::size_t>(ny + 1);

    DeviceArray<Vec<Real, EulerNVars>> qB_face(nface);
    DeviceArray<Vec<Real, EulerNVars>> qT_face(nface);
    DeviceArray<Vec<Real, EulerNVars>> flux_face(nface);

    {
        const dim3 threads(kReconstructBlockX, kReconstructBlockY);
        const dim3 blocks(((ny + 1) + threads.x - 1) / threads.x,
                          (nx + threads.y - 1) / threads.y);
        hancock_face_y_kernel<Real><<<blocks, threads>>>(
            g.data(), nx, ny, dt, g.dy(), gamma,
            qB_face.data(), qT_face.data());
        HRSC_CUDA_CHECK(cudaGetLastError());
        HRSC_CUDA_CHECK(cudaDeviceSynchronize());
    }

    if (flux_scheme == FluxScheme::Rusanov) {
        rusanov_flux_y_gpu<Real>(nx, ny, gamma,
                                 qB_face.data(), qT_face.data(),
                                 flux_face.data());
    } else {
        throw std::runtime_error(
            "sweep_y_gpu: HLLC FluxScheme not yet wired (Week 6 T20)");
    }

    apply_update_y_gpu<Real>(g, flux_face.data(), dt);
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

template TimeReal compute_dt_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float gamma, float cfl);
template TimeReal compute_dt_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double gamma, double cfl);

template void muscl_reconstruct_x_gpu<float>(
    GpuGrid<float, EulerNVars>& g,
    Vec<float, EulerNVars>* qL, Vec<float, EulerNVars>* qR);
template void muscl_reconstruct_x_gpu<double>(
    GpuGrid<double, EulerNVars>& g,
    Vec<double, EulerNVars>* qL, Vec<double, EulerNVars>* qR);

template void muscl_reconstruct_y_gpu<float>(
    GpuGrid<float, EulerNVars>& g,
    Vec<float, EulerNVars>* q_bottom, Vec<float, EulerNVars>* q_top);
template void muscl_reconstruct_y_gpu<double>(
    GpuGrid<double, EulerNVars>& g,
    Vec<double, EulerNVars>* q_bottom, Vec<double, EulerNVars>* q_top);

template void hancock_predict_x_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float dt, float gamma,
    Vec<float, EulerNVars>* qL, Vec<float, EulerNVars>* qR);
template void hancock_predict_x_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double dt, double gamma,
    Vec<double, EulerNVars>* qL, Vec<double, EulerNVars>* qR);

template void hancock_predict_y_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float dt, float gamma,
    Vec<float, EulerNVars>* q_bottom, Vec<float, EulerNVars>* q_top);
template void hancock_predict_y_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double dt, double gamma,
    Vec<double, EulerNVars>* q_bottom, Vec<double, EulerNVars>* q_top);

template void rusanov_flux_x_gpu<float>(
    int nx, int ny, float gamma,
    const Vec<float, EulerNVars>* qL_face,
    const Vec<float, EulerNVars>* qR_face,
    Vec<float, EulerNVars>* flux_x);
template void rusanov_flux_x_gpu<double>(
    int nx, int ny, double gamma,
    const Vec<double, EulerNVars>* qL_face,
    const Vec<double, EulerNVars>* qR_face,
    Vec<double, EulerNVars>* flux_x);

template void rusanov_flux_y_gpu<float>(
    int nx, int ny, float gamma,
    const Vec<float, EulerNVars>* qB_face,
    const Vec<float, EulerNVars>* qT_face,
    Vec<float, EulerNVars>* flux_y);
template void rusanov_flux_y_gpu<double>(
    int nx, int ny, double gamma,
    const Vec<double, EulerNVars>* qB_face,
    const Vec<double, EulerNVars>* qT_face,
    Vec<double, EulerNVars>* flux_y);

template void apply_update_x_gpu<float>(
    GpuGrid<float, EulerNVars>& g,
    const Vec<float, EulerNVars>* flux_x, float dt);
template void apply_update_x_gpu<double>(
    GpuGrid<double, EulerNVars>& g,
    const Vec<double, EulerNVars>* flux_x, double dt);

template void apply_update_y_gpu<float>(
    GpuGrid<float, EulerNVars>& g,
    const Vec<float, EulerNVars>* flux_y, float dt);
template void apply_update_y_gpu<double>(
    GpuGrid<double, EulerNVars>& g,
    const Vec<double, EulerNVars>* flux_y, double dt);

template void sweep_x_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float dt, float gamma, FluxScheme flux);
template void sweep_x_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double dt, double gamma, FluxScheme flux);

template void sweep_y_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float dt, float gamma, FluxScheme flux);
template void sweep_y_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double dt, double gamma, FluxScheme flux);

} // namespace hrsc
