#include "catch.hpp"
#include "app/mhd_result.hpp"
#include "app/mhd_run_config.hpp"
#include "mhd/mhd_state.hpp"
#include "utils/io.hpp"

#include <cstdio>
#include <filesystem>
#include <sstream>
#include <string>

using namespace hrsc;
using namespace hrsc::app;

TEST_CASE("MHD result preserves diagnostics and binary layout", "[app][mhd]") {
    constexpr int nx = 4;
    constexpr int ny = 1;
    constexpr double dx = 0.25;
    constexpr double dy = 0.25;
    constexpr double time = 0.125;

    Grid2D<double, MhdNVars> grid(nx, ny);
    grid.dx = dx;
    grid.dy = dy;
    auto view = grid.view();
    for (int i = 0; i < nx; ++i) {
        view(i, 0, MhdIdx::BX) = 0.75;
    }

    const auto output = std::filesystem::temp_directory_path() / "hrsc-mhd-result.bin";
    std::remove(output.string().c_str());
    MhdRunOptions options;
    options.output_format = "binary";
    options.output_file = output.string();
    std::ostringstream diagnostics;

    write_mhd_result(diagnostics, options, view, nx, ny, dx, dy, time, 7);

    REQUIRE(diagnostics.str() ==
            "[mhd] t=0.125000 steps=7 divB_mean=0.000e+00 divB_max=0.000e+00\n");

    int file_nx = 0, file_ny = 0, nvars = 0, precision = 0;
    double file_time = 0.0, file_dx = 0.0, file_dy = 0.0;
    read_binary_header(output.string(), file_nx, file_ny, nvars, precision,
                       file_time, file_dx, file_dy);
    REQUIRE(file_nx == nx);
    REQUIRE(file_ny == ny);
    REQUIRE(nvars == MhdNVars);
    REQUIRE(file_time == time);

    std::remove(output.string().c_str());
}
