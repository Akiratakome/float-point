#pragma once

#include "app/mhd_run_config.hpp"
#include "mhd/mhd_state.hpp"
#include "utils/error_norms.hpp"
#include "utils/io.hpp"

#include <ostream>
#include <string>

namespace hrsc::app {

struct MhdDiagnostics {
    double divb_mean;
    double divb_max;
};

std::string format_mhd_diagnostics(double time, int steps,
                                   const MhdDiagnostics& diagnostics);

template <typename Real, typename Ptr>
MhdDiagnostics collect_mhd_diagnostics(
    GridViewBase<Real, MhdNVars, Ptr> grid, int nx, int ny, Real dx, Real dy) {
    const DivBNorms<Real> norms = compute_divB_norms<Real>(grid, nx, ny, dx, dy);
    return {static_cast<double>(norms.mean), static_cast<double>(norms.max)};
}

template <typename Real, typename Ptr>
void write_mhd_result(std::ostream& diagnostics_output,
                      const MhdRunOptions& options,
                      GridViewBase<Real, MhdNVars, Ptr> grid,
                      int nx, int ny, Real dx, Real dy, Real time, int steps) {
    const MhdDiagnostics diagnostics =
        collect_mhd_diagnostics(grid, nx, ny, dx, dy);
    diagnostics_output << format_mhd_diagnostics(
        static_cast<double>(time), steps, diagnostics);

    if (options.output_format == "binary") {
        write_binary<Real, MhdNVars>(options.output_file, grid, nx, ny, dx, dy, time);
    }
}

} // namespace hrsc::app
