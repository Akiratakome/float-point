// src/gpu/gpu_grid.cuh
//
// Device-side mirror of Grid2D<Real, NVars>. The memory layout is identical:
// row-major cells, variable-last storage, and host ghost cells included.

#pragma once

#include "core/grid.hpp"
#include "core/types.hpp"
#include "gpu/cuda_utils.cuh"

#include <cstddef>
#include <stdexcept>

namespace hrsc {

template <typename Real, int NVars>
class GpuGrid {
public:
    explicit GpuGrid(const Grid2D<Real, NVars>& host)
        : nx_(host.nx),
          ny_(host.ny),
          dx_(host.dx),
          dy_(host.dy),
          dev_(static_cast<std::size_t>(host.data.size())) {
        dev_.copy_from_host(host.data.data(), host.data.size());
    }

    void download_to(Grid2D<Real, NVars>& host) const {
        if (host.nx != nx_ || host.ny != ny_) {
            throw std::runtime_error("GpuGrid::download_to size mismatch");
        }
        dev_.copy_to_host(host.data.data(), host.data.size());
    }

    Real* data() noexcept { return dev_.data(); }
    const Real* data() const noexcept { return dev_.data(); }

    int nx() const noexcept { return nx_; }
    int ny() const noexcept { return ny_; }
    Real dx() const noexcept { return dx_; }
    Real dy() const noexcept { return dy_; }
    static constexpr int ng() noexcept { return NgHost; }

    std::size_t total_cells_with_ghosts() const noexcept {
        return static_cast<std::size_t>(nx_total()) *
               static_cast<std::size_t>(ny_total());
    }

    std::size_t element_count() const noexcept {
        return total_cells_with_ghosts() * static_cast<std::size_t>(NVars);
    }

private:
    int nx_total() const noexcept { return nx_ + 2 * NgHost; }
    int ny_total() const noexcept { return ny_ + 2 * NgHost; }

    int nx_;
    int ny_;
    Real dx_;
    Real dy_;
    DeviceArray<Real> dev_;
};

} // namespace hrsc
