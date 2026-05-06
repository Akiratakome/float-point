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

// State arrays follow the template precision (float / double).
// Time accumulator is ALWAYS double, independent of Real, because:
//   (1) t_end, dt, m_time only accumulate; their round-off dominates
//       over state round-off for long evolutions.
//   (2) float32 eps ~ 1.2e-7 causes "large-number-eats-small" in
//       m_time += dt once t > ~0.25 and dt ~ 1e-7. Classical bug.
//   (3) double precision for time costs 8 bytes of solver state per
//       time-step -- negligible vs O(N^2) state array.
// This does NOT violate overall.md "template solver for float/double":
// the STATE is templated; the TIME ACCUMULATOR is a separate concern.
using TimeReal = double;

// Physical constants templated on precision type
template <typename Real>
struct Constants {
    static constexpr Real Gamma   = static_cast<Real>(1.4);
    static constexpr Real GammaM1 = static_cast<Real>(0.4);
};

} // namespace hrsc
