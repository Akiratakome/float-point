#pragma once

// CPU/GPU portability macro — expands to nothing on CPU builds
#ifdef __CUDACC__
  #define HD_FUNC __host__ __device__
#else
  #define HD_FUNC
#endif

namespace hrsc {

// Physical constants templated on precision type
template <typename Real>
struct Constants {
    static constexpr Real gamma   = static_cast<Real>(1.4);
    static constexpr Real gamma_m1 = static_cast<Real>(0.4);
};

} // namespace hrsc
