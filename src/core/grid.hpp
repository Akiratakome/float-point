#pragma once

#include "core/types.hpp"

#include <vector>

namespace hrsc {

// Const-generic view: Ptr is Real* or const Real*
template <typename Real, int NVars, typename Ptr>
struct GridViewBase {
    Ptr data;
    int nx, ny;
    Real dx, dy;
    static constexpr int ng = 2;

    HD_FUNC int nx_total() const { return nx + 2 * ng; }
    HD_FUNC int ny_total() const { return ny + 2 * ng; }

    HD_FUNC int index(int i, int j, int var) const {
        return ((j + ng) * nx_total() + (i + ng)) * NVars + var;
    }

    HD_FUNC auto operator()(int i, int j, int var) -> decltype(data[0]) {
        return data[index(i, j, var)];
    }

    HD_FUNC auto operator()(int i, int j, int var) const -> decltype(data[0]) {
        return data[index(i, j, var)];
    }
};

template <typename Real, int NVars>
using GridView = GridViewBase<Real, NVars, Real*>;

template <typename Real, int NVars>
using ConstGridView = GridViewBase<Real, NVars, const Real*>;

// Owning container — host only, no HD_FUNC
template <typename Real, int NVars>
struct Grid2D {
    int nx, ny;
    static constexpr int ng = 2;
    std::vector<Real> data;
    Real dx, dy;

    Grid2D(int nx_, int ny_)
        : nx(nx_), ny(ny_),
          data(static_cast<size_t>((nx_ + 2 * ng) * (ny_ + 2 * ng) * NVars), Real(0)),
          dx(Real(0)), dy(Real(0)) {}

    // Set dx/dy before calling view() — the view captures them by value.
    GridView<Real, NVars> view() {
        return {data.data(), nx, ny, dx, dy};
    }

    ConstGridView<Real, NVars> view() const {
        return {data.data(), nx, ny, dx, dy};
    }
};

} // namespace hrsc
