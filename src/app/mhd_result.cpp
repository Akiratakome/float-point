#include "app/mhd_result.hpp"

#include <cstdio>

namespace hrsc::app {

std::string format_mhd_diagnostics(double time, int steps,
                                   const MhdDiagnostics& diagnostics) {
    char line[192];
    std::snprintf(line, sizeof(line),
                  "[mhd] t=%.6f steps=%d divB_mean=%.3e divB_max=%.3e\n",
                  time, steps, diagnostics.divb_mean, diagnostics.divb_max);
    return line;
}

} // namespace hrsc::app
