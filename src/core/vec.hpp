#pragma once

#include "core/types.hpp"

namespace hrsc {

template <typename Real, int N>
struct Vec {
    Real data[N];

    HD_FUNC Real& operator[](int i) { return data[i]; }
    HD_FUNC const Real& operator[](int i) const { return data[i]; }
};

// --- Element-wise binary operators ---

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator+(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] + b[i];
    return result;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator-(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] - b[i];
    return result;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator*(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] * b[i];
    return result;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator/(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] / b[i];
    return result;
}

// --- Scalar operators ---

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator*(const Vec<Real, N>& a, Real s) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] * s;
    return result;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator*(Real s, const Vec<Real, N>& a) {
    return a * s;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator/(const Vec<Real, N>& a, Real s) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] / s;
    return result;
}

// --- Compound assignment ---

template <typename Real, int N>
HD_FUNC Vec<Real, N>& operator+=(Vec<Real, N>& a, const Vec<Real, N>& b) {
    for (int i = 0; i < N; ++i) a[i] += b[i];
    return a;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N>& operator-=(Vec<Real, N>& a, const Vec<Real, N>& b) {
    for (int i = 0; i < N; ++i) a[i] -= b[i];
    return a;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N>& operator*=(Vec<Real, N>& a, Real s) {
    for (int i = 0; i < N; ++i) a[i] *= s;
    return a;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N>& operator/=(Vec<Real, N>& a, Real s) {
    for (int i = 0; i < N; ++i) a[i] /= s;
    return a;
}

// --- Reductions ---

template <typename Real, int N>
HD_FUNC Real dot(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Real sum = Real(0);
    for (int i = 0; i < N; ++i) sum += a[i] * b[i];
    return sum;
}

template <typename Real, int N>
HD_FUNC Real norm_sq(const Vec<Real, N>& a) {
    return dot(a, a);
}

} // namespace hrsc
