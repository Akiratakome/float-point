// tests/unit/test_gpu_roundtrip.cpp
//
// Catch2 driver for the GPU roundtrip wrappers in
// tests/unit/gpu_roundtrip_kernel.cu. The CUDA half is linked only when
// ENABLE_CUDA=ON; CPU-only builds compile this file with the body disabled.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <random>
#include <vector>

extern "C" bool gpu_roundtrip_double(const double* in, double* out, std::size_t n);
extern "C" bool gpu_roundtrip_float(const float* in, float* out, std::size_t n);

namespace {

template <typename T>
std::vector<T> random_vector(std::size_t n, std::uint32_t seed) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> dist(-1e3, 1e3);
    std::vector<T> v(n);
    for (auto& x : v) x = static_cast<T>(dist(rng));
    return v;
}

template <typename T>
bool bitwise_equal(const std::vector<T>& a, const std::vector<T>& b) {
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) {
        std::uint64_t ai = 0;
        std::uint64_t bi = 0;
        std::memcpy(&ai, &a[i], sizeof(T));
        std::memcpy(&bi, &b[i], sizeof(T));
        if (ai != bi) return false;
    }
    return true;
}

} // namespace

TEST_CASE("GPU roundtrip is byte-identical for double over 100 random seeds",
          "[gpu]") {
    constexpr std::size_t N = 256 * 100;
    for (std::uint32_t seed = 0; seed < 100; ++seed) {
        auto in = random_vector<double>(N, seed);
        std::vector<double> out(N, 0.0);
        REQUIRE(gpu_roundtrip_double(in.data(), out.data(), N));
        REQUIRE(bitwise_equal(in, out));
    }
}

TEST_CASE("GPU roundtrip is byte-identical for float over 100 random seeds",
          "[gpu]") {
    constexpr std::size_t N = 256 * 100;
    for (std::uint32_t seed = 1000; seed < 1100; ++seed) {
        auto in = random_vector<float>(N, seed);
        std::vector<float> out(N, 0.0f);
        REQUIRE(gpu_roundtrip_float(in.data(), out.data(), N));
        REQUIRE(bitwise_equal(in, out));
    }
}

#endif // HRSC_HAS_CUDA
