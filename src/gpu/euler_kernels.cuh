// src/gpu/euler_kernels.cuh
//
// Week 5 GPU data-path placeholder. Real Euler kernels land later; this copy
// kernel verifies host-device allocation, launch, and copy-back plumbing.

#pragma once

#include "core/boundary.hpp"
#include "core/eos.hpp"
#include "core/grid.hpp"
#include "core/vec.hpp"

#ifdef HRSC_HAS_CUDA
#include "gpu/gpu_grid.cuh"
#endif

#include <cstddef>

namespace hrsc {

enum class FluxScheme;

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

template <typename Real>
TimeReal compute_dt_gpu(GpuGrid<Real, EulerNVars>& g, Real gamma, Real cfl);

// MUSCL piecewise-linear reconstruction (minmod limiter), per-cell variant.
// For X: produces qL (i-1/2 face state from cell i) and qR (i+1/2 face state
// from cell i) for every interior cell. Output buffers are sized nx * ny
// with linear index j*nx + i. For Y: q_bottom (j-1/2) and q_top (j+1/2),
// same nx * ny layout. Bit-exact w.r.t. the CPU oracle in src/euler/muscl.hpp.
template <typename Real>
void muscl_reconstruct_x_gpu(GpuGrid<Real, EulerNVars>& g,
                             Vec<Real, EulerNVars>* qL,
                             Vec<Real, EulerNVars>* qR);

template <typename Real>
void muscl_reconstruct_y_gpu(GpuGrid<Real, EulerNVars>& g,
                             Vec<Real, EulerNVars>* q_bottom,
                             Vec<Real, EulerNVars>* q_top);

// MUSCL-Hancock predictor: per-cell qL/qR (X) and q_bottom/q_top (Y)
// after slope-reconstruction + half-step flux update. Bit-exact w.r.t. the
// CPU oracle in src/euler/hancock.hpp.
template <typename Real>
void hancock_predict_x_gpu(GpuGrid<Real, EulerNVars>& g,
                           Real dt, Real gamma,
                           Vec<Real, EulerNVars>* qL,
                           Vec<Real, EulerNVars>* qR);

template <typename Real>
void hancock_predict_y_gpu(GpuGrid<Real, EulerNVars>& g,
                           Real dt, Real gamma,
                           Vec<Real, EulerNVars>* q_bottom,
                           Vec<Real, EulerNVars>* q_top);

// Rusanov (LLF) flux on per-face left/right input buffers.
// X: qL_face / qR_face / flux_x sized (nx+1) * ny.
// Y: qB_face / qT_face / flux_y sized nx * (ny+1) (rotation handled inside).
// Bit-exact w.r.t. CPU oracle in src/euler/rusanov.hpp.
template <typename Real>
void rusanov_flux_x_gpu(int nx, int ny, Real gamma,
                        const Vec<Real, EulerNVars>* qL_face,
                        const Vec<Real, EulerNVars>* qR_face,
                        Vec<Real, EulerNVars>* flux_x);

template <typename Real>
void rusanov_flux_y_gpu(int nx, int ny, Real gamma,
                        const Vec<Real, EulerNVars>* qB_face,
                        const Vec<Real, EulerNVars>* qT_face,
                        Vec<Real, EulerNVars>* flux_y);

// HLLC flux on per-face left/right input buffers.
// X: qL_face / qR_face / flux_x sized (nx+1) * ny.
// Y: qB_face / qT_face / flux_y sized nx * (ny+1) (rotation handled inside).
// Bit-exact w.r.t. CPU oracle in src/euler/hllc.hpp.
template <typename Real>
void hllc_flux_x_gpu(int nx, int ny, Real gamma,
                     const Vec<Real, EulerNVars>* qL_face,
                     const Vec<Real, EulerNVars>* qR_face,
                     Vec<Real, EulerNVars>* flux_x);

template <typename Real>
void hllc_flux_y_gpu(int nx, int ny, Real gamma,
                     const Vec<Real, EulerNVars>* qB_face,
                     const Vec<Real, EulerNVars>* qT_face,
                     Vec<Real, EulerNVars>* flux_y);

// Per-axis sweep: per-face Hancock + flux (Rusanov in T15; HLLC in T20) +
// conservative update. Allocates transient face buffers internally.
// Caller is responsible for applying boundary conditions before each sweep.
// Bit-exact w.r.t. CPU sweep in src/euler/euler_solver.cpp under
// --fmad=false (set on this TU).
template <typename Real>
void sweep_x_gpu(GpuGrid<Real, EulerNVars>& g, Real dt, Real gamma,
                 FluxScheme flux);

template <typename Real>
void sweep_y_gpu(GpuGrid<Real, EulerNVars>& g, Real dt, Real gamma,
                 FluxScheme flux);

// Conservative update along an axis: U[i,j] -= (dt/dx) * (flux[k+1] - flux[k]).
// flux_x is shaped (nx+1) * ny (per-row, contiguous); flux_y is nx * (ny+1)
// (per-column, contiguous). Bit-exact w.r.t. the CPU oracle in
// src/euler/euler_solver.cpp (x_sweep / y_sweep update blocks).
template <typename Real>
void apply_update_x_gpu(GpuGrid<Real, EulerNVars>& g,
                        const Vec<Real, EulerNVars>* flux_x,
                        Real dt);

template <typename Real>
void apply_update_y_gpu(GpuGrid<Real, EulerNVars>& g,
                        const Vec<Real, EulerNVars>* flux_y,
                        Real dt);

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

extern template TimeReal compute_dt_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float gamma, float cfl);
extern template TimeReal compute_dt_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double gamma, double cfl);

extern template void muscl_reconstruct_x_gpu<float>(
    GpuGrid<float, EulerNVars>& g,
    Vec<float, EulerNVars>* qL, Vec<float, EulerNVars>* qR);
extern template void muscl_reconstruct_x_gpu<double>(
    GpuGrid<double, EulerNVars>& g,
    Vec<double, EulerNVars>* qL, Vec<double, EulerNVars>* qR);

extern template void muscl_reconstruct_y_gpu<float>(
    GpuGrid<float, EulerNVars>& g,
    Vec<float, EulerNVars>* q_bottom, Vec<float, EulerNVars>* q_top);
extern template void muscl_reconstruct_y_gpu<double>(
    GpuGrid<double, EulerNVars>& g,
    Vec<double, EulerNVars>* q_bottom, Vec<double, EulerNVars>* q_top);

extern template void hancock_predict_x_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float dt, float gamma,
    Vec<float, EulerNVars>* qL, Vec<float, EulerNVars>* qR);
extern template void hancock_predict_x_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double dt, double gamma,
    Vec<double, EulerNVars>* qL, Vec<double, EulerNVars>* qR);

extern template void hancock_predict_y_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float dt, float gamma,
    Vec<float, EulerNVars>* q_bottom, Vec<float, EulerNVars>* q_top);
extern template void hancock_predict_y_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double dt, double gamma,
    Vec<double, EulerNVars>* q_bottom, Vec<double, EulerNVars>* q_top);

extern template void rusanov_flux_x_gpu<float>(
    int nx, int ny, float gamma,
    const Vec<float, EulerNVars>* qL_face,
    const Vec<float, EulerNVars>* qR_face,
    Vec<float, EulerNVars>* flux_x);
extern template void rusanov_flux_x_gpu<double>(
    int nx, int ny, double gamma,
    const Vec<double, EulerNVars>* qL_face,
    const Vec<double, EulerNVars>* qR_face,
    Vec<double, EulerNVars>* flux_x);

extern template void rusanov_flux_y_gpu<float>(
    int nx, int ny, float gamma,
    const Vec<float, EulerNVars>* qB_face,
    const Vec<float, EulerNVars>* qT_face,
    Vec<float, EulerNVars>* flux_y);
extern template void rusanov_flux_y_gpu<double>(
    int nx, int ny, double gamma,
    const Vec<double, EulerNVars>* qB_face,
    const Vec<double, EulerNVars>* qT_face,
    Vec<double, EulerNVars>* flux_y);

extern template void hllc_flux_x_gpu<float>(
    int nx, int ny, float gamma,
    const Vec<float, EulerNVars>* qL_face,
    const Vec<float, EulerNVars>* qR_face,
    Vec<float, EulerNVars>* flux_x);
extern template void hllc_flux_x_gpu<double>(
    int nx, int ny, double gamma,
    const Vec<double, EulerNVars>* qL_face,
    const Vec<double, EulerNVars>* qR_face,
    Vec<double, EulerNVars>* flux_x);

extern template void hllc_flux_y_gpu<float>(
    int nx, int ny, float gamma,
    const Vec<float, EulerNVars>* qB_face,
    const Vec<float, EulerNVars>* qT_face,
    Vec<float, EulerNVars>* flux_y);
extern template void hllc_flux_y_gpu<double>(
    int nx, int ny, double gamma,
    const Vec<double, EulerNVars>* qB_face,
    const Vec<double, EulerNVars>* qT_face,
    Vec<double, EulerNVars>* flux_y);

extern template void apply_update_x_gpu<float>(
    GpuGrid<float, EulerNVars>& g,
    const Vec<float, EulerNVars>* flux_x, float dt);
extern template void apply_update_x_gpu<double>(
    GpuGrid<double, EulerNVars>& g,
    const Vec<double, EulerNVars>* flux_x, double dt);

extern template void apply_update_y_gpu<float>(
    GpuGrid<float, EulerNVars>& g,
    const Vec<float, EulerNVars>* flux_y, float dt);
extern template void apply_update_y_gpu<double>(
    GpuGrid<double, EulerNVars>& g,
    const Vec<double, EulerNVars>* flux_y, double dt);

extern template void sweep_x_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float dt, float gamma, FluxScheme flux);
extern template void sweep_x_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double dt, double gamma, FluxScheme flux);

extern template void sweep_y_gpu<float>(
    GpuGrid<float, EulerNVars>& g, float dt, float gamma, FluxScheme flux);
extern template void sweep_y_gpu<double>(
    GpuGrid<double, EulerNVars>& g, double dt, double gamma, FluxScheme flux);
#endif

} // namespace hrsc
