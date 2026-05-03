// tests/unit/test_gpu_grid_layout.cpp
//
// CUDA-only safety net for Grid2D <-> GpuGrid storage layout.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/grid.hpp"
#include "gpu/gpu_grid.cuh"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <vector>

extern "C" void launch_layout_writer(double* dev, int nx_total, int ny_total,
                                      int nvars, double base);

using namespace hrsc;

namespace {

constexpr int NVARS = 4;

struct RawCell {
    int i;
    int j;
};

std::size_t raw_index(int i, int j, int var, int nx_total) {
    return (static_cast<std::size_t>(j) * static_cast<std::size_t>(nx_total) +
            static_cast<std::size_t>(i)) *
               static_cast<std::size_t>(NVARS) +
           static_cast<std::size_t>(var);
}

double layout_value(int i, int j, int var, double base) {
    return base + static_cast<double>(i * 1000 + j * 10 + var);
}

bool byte_equal(const std::vector<double>& a, const std::vector<double>& b) {
    return a.size() == b.size() &&
           std::memcmp(a.data(), b.data(), a.size() * sizeof(double)) == 0;
}

template <std::size_t N>
void require_raw_cells_match(const Grid2D<double, NVARS>& grid,
                             const std::array<RawCell, N>& cells,
                             int nx_total, double base) {
    for (const auto cell : cells) {
        for (int var = 0; var < NVARS; ++var) {
            const auto idx = raw_index(cell.i, cell.j, var, nx_total);
            CAPTURE(grid.nx, grid.ny, cell.i, cell.j, var, idx);
            REQUIRE(grid.data[idx] == layout_value(cell.i, cell.j, var, base));
        }
    }
}

void require_full_decoded_pattern(const Grid2D<double, NVARS>& grid,
                                  int nx_total, int ny_total, double base) {
    for (int j = 0; j < ny_total; ++j) {
        for (int i = 0; i < nx_total; ++i) {
            for (int var = 0; var < NVARS; ++var) {
                const auto idx = raw_index(i, j, var, nx_total);
                CAPTURE(grid.nx, grid.ny, i, j, var, idx);
                REQUIRE(grid.data[idx] == layout_value(i, j, var, base));
            }
        }
    }
}

} // namespace

TEST_CASE("Grid2D and GpuGrid agree on awkward element counts",
          "[gpu][layout]") {
    constexpr std::array<int, 6> awkward_nx{{7, 17, 33, 64, 257, 1024}};
    constexpr int ny = 9;
    constexpr int ng = Grid2D<double, NVARS>::ng;

    for (const int nx : awkward_nx) {
        Grid2D<double, NVARS> host(nx, ny);
        host.dx = 0.125;
        host.dy = 0.25;

        GpuGrid<double, NVARS> dev(host);

        const auto expected =
            static_cast<std::size_t>(nx + 2 * ng) *
            static_cast<std::size_t>(ny + 2 * ng) *
            static_cast<std::size_t>(NVARS);
        REQUIRE(host.data.size() == expected);
        REQUIRE(dev.element_count() == expected);
    }
}

TEST_CASE("GpuGrid roundtrip preserves host layout byte-for-byte",
          "[gpu][layout]") {
    Grid2D<double, NVARS> host(33, 11);
    host.dx = 1.0 / 33.0;
    host.dy = 1.0 / 11.0;

    for (std::size_t idx = 0; idx < host.data.size(); ++idx) {
        host.data[idx] = static_cast<double>(idx * 17 + 3);
    }
    const auto expected = host.data;

    GpuGrid<double, NVARS> dev(host);

    Grid2D<double, NVARS> out(host.nx, host.ny);
    out.dx = host.dx;
    out.dy = host.dy;
    dev.download_to(out);

    REQUIRE(byte_equal(out.data, expected));
}

TEST_CASE("GPU layout writer uses row-major variable-last indexing",
          "[gpu][layout]") {
    constexpr std::array<int, 6> awkward_nx{{7, 17, 33, 64, 257, 1024}};
    constexpr int ny = 7;
    constexpr int ng = Grid2D<double, NVARS>::ng;

    for (const int nx : awkward_nx) {
        Grid2D<double, NVARS> host(nx, ny);
        host.dx = 0.1;
        host.dy = 0.2;

        GpuGrid<double, NVARS> dev(host);
        const int nx_total = host.nx + 2 * ng;
        const int ny_total = host.ny + 2 * ng;
        const double base = 50000.0 + static_cast<double>(nx);

        launch_layout_writer(dev.data(), nx_total, ny_total, NVARS, base);

        Grid2D<double, NVARS> out(host.nx, host.ny);
        out.dx = host.dx;
        out.dy = host.dy;
        dev.download_to(out);

        const std::array<RawCell, 10> sentinels{{
            {0, 0},                         // lower-left ghost corner
            {nx_total - 1, 0},              // lower-right ghost corner
            {0, ny_total - 1},              // upper-left ghost corner
            {nx_total - 1, ny_total - 1},   // upper-right ghost corner
            {nx_total - 1, ng},             // right row boundary
            {0, ng + ny - 1},               // left row boundary
            {ng, ng},                       // first physical cell
            {ng + nx - 1, ng},              // last physical cell in first row
            {ng, ng + ny - 1},              // first physical cell in last row
            {ng + nx - 1, ng + ny - 1},     // last physical cell
        }};
        require_raw_cells_match(out, sentinels, nx_total, base);

        for (int var = 0; var < NVARS; ++var) {
            const auto first_idx = raw_index(ng, ng, var, nx_total);
            const auto last_idx =
                raw_index(ng + nx - 1, ng + ny - 1, var, nx_total);
            CAPTURE(nx, ny, var);
            REQUIRE(out.view().index(0, 0, var) == static_cast<int>(first_idx));
            REQUIRE(out.view().index(nx - 1, ny - 1, var) ==
                    static_cast<int>(last_idx));
            REQUIRE(out.view()(0, 0, var) == out.data[first_idx]);
            REQUIRE(out.view()(nx - 1, ny - 1, var) == out.data[last_idx]);
        }

        require_full_decoded_pattern(out, nx_total, ny_total, base);
    }
}

#endif // HRSC_HAS_CUDA
