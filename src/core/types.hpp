#pragma once

// CPU/GPU portability macro — expands to nothing on CPU builds
#ifdef __CUDACC__
  #define HD_FUNC __host__ __device__
#else
  #define HD_FUNC
#endif

namespace hrsc {

// Number of ghost cells on each boundary
static constexpr int NgHost = 2;

// Physical constants templated on precision type
template <typename Real>
struct Constants {
    static constexpr Real Gamma   = static_cast<Real>(1.4);
    static constexpr Real GammaM1 = static_cast<Real>(0.4);
};

} // namespace hrsc
