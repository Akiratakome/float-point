#pragma once

#include "core/grid.hpp"

#include <string>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <stdexcept>

// Ensure little-endian (both x86 Windows and x86_64 Linux satisfy this)
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
    #error "Binary IO assumes little-endian architecture"
#endif

namespace hrsc {

template <typename Real, int NVars, typename Ptr>
void write_binary(const std::string& filename,
                  GridViewBase<Real, NVars, Ptr> grid,
                  int nx, int ny, Real dx, Real dy, Real time)
{
    FILE* fp = std::fopen(filename.c_str(), "wb");
    if (!fp) throw std::runtime_error("Cannot open file for writing: " + filename);

    // --- 64-byte header ---
    char header[64];
    std::memset(header, 0, 64);

    // Magic
    std::memcpy(header + 0, "HRSC", 4);
    // nx, ny, nvars, precision_tag as int32
    int32_t inx = static_cast<int32_t>(nx);
    int32_t iny = static_cast<int32_t>(ny);
    int32_t invars = static_cast<int32_t>(NVars);
    int32_t iprec = static_cast<int32_t>(sizeof(Real));
    std::memcpy(header + 4,  &inx, 4);
    std::memcpy(header + 8,  &iny, 4);
    std::memcpy(header + 12, &invars, 4);
    std::memcpy(header + 16, &iprec, 4);
    // time, dx, dy as float64
    double dtime = static_cast<double>(time);
    double ddx   = static_cast<double>(dx);
    double ddy   = static_cast<double>(dy);
    std::memcpy(header + 20, &dtime, 8);
    std::memcpy(header + 28, &ddx, 8);
    std::memcpy(header + 36, &ddy, 8);

    std::fwrite(header, 1, 64, fp);

    // --- Row-by-row data write (no buffer allocation) ---
    for (int j = 0; j < ny; ++j) {
        const Real* row_start = static_cast<const Real*>(grid.data)
            + (static_cast<size_t>(j + grid.ng) * grid.nx_total() + grid.ng) * NVars;
        std::fwrite(row_start, sizeof(Real), static_cast<size_t>(nx) * NVars, fp);
    }

    std::fclose(fp);
}

inline void read_binary_header(const std::string& filename,
                               int& nx, int& ny, int& nvars, int& precision_tag,
                               double& time, double& dx, double& dy)
{
    FILE* fp = std::fopen(filename.c_str(), "rb");
    if (!fp) throw std::runtime_error("Cannot open file for reading: " + filename);

    char header[64];
    if (std::fread(header, 1, 64, fp) != 64) {
        std::fclose(fp);
        throw std::runtime_error("Failed to read 64-byte header from: " + filename);
    }

    // Verify magic
    if (std::memcmp(header, "HRSC", 4) != 0) {
        std::fclose(fp);
        throw std::runtime_error("Invalid magic in binary file: " + filename);
    }

    int32_t inx, iny, invars, iprec;
    std::memcpy(&inx,    header + 4,  4);
    std::memcpy(&iny,    header + 8,  4);
    std::memcpy(&invars, header + 12, 4);
    std::memcpy(&iprec,  header + 16, 4);
    std::memcpy(&time,   header + 20, 8);
    std::memcpy(&dx,     header + 28, 8);
    std::memcpy(&dy,     header + 36, 8);

    nx = static_cast<int>(inx);
    ny = static_cast<int>(iny);
    nvars = static_cast<int>(invars);
    precision_tag = static_cast<int>(iprec);

    std::fclose(fp);
}

template <typename Real, int NVars>
void read_binary_data(const std::string& filename,
                      GridView<Real, NVars> grid,
                      int nx, int ny)
{
    FILE* fp = std::fopen(filename.c_str(), "rb");
    if (!fp) throw std::runtime_error("Cannot open file for reading: " + filename);

    // Skip 64-byte header
    std::fseek(fp, 64, SEEK_SET);

    // Read row-by-row into grid (filling physical cells, skipping ghosts)
    for (int j = 0; j < ny; ++j) {
        Real* row_start = grid.data
            + (static_cast<size_t>(j + grid.ng) * grid.nx_total() + grid.ng) * NVars;
        if (std::fread(row_start, sizeof(Real), static_cast<size_t>(nx) * NVars, fp)
                != static_cast<size_t>(nx) * NVars) {
            std::fclose(fp);
            throw std::runtime_error("Failed to read data row from: " + filename);
        }
    }

    std::fclose(fp);
}

} // namespace hrsc
