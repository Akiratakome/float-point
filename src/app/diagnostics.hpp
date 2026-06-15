#pragma once

#include "app/output.hpp"
#include "app/run_config.hpp"
#include "core/eos.hpp"
#include "core/types.hpp"
#include "euler/euler_solver.hpp"
#include "euler/hllc_trace.hpp"
#include "utils/io.hpp"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace hrsc::app {

struct DiagnosticSettings {
    bool enabled = false;
    long long max_steps = 0;
    double dt_floor = 0.0;
    std::string dump_file;
};

DiagnosticSettings configure_diagnostics_from_env();

struct StateStats {
    bool finite = true;
    double min_rho = std::numeric_limits<double>::infinity();
    double min_p = std::numeric_limits<double>::infinity();
    int bad_i = -1;
    int bad_j = -1;
};

template <typename Real>
StateStats collect_state_stats(EulerSolver<Real>& solver, Real gamma) {
    StateStats stats;
    auto gv = solver.grid_view();
    for (int j = 0; j < gv.ny; ++j) {
        for (int i = 0; i < gv.nx; ++i) {
            Vec<Real, EulerNVars> cons;
            for (int v = 0; v < EulerNVars; ++v) {
                cons[v] = gv(i, j, v);
                if (!std::isfinite(static_cast<double>(cons[v])) && stats.finite) {
                    stats.finite = false;
                    stats.bad_i = i;
                    stats.bad_j = j;
                }
            }
            double rho = static_cast<double>(cons[RHO]);
            double p = static_cast<double>(pressure(cons, gamma));
            stats.min_rho = std::min(stats.min_rho, rho);
            stats.min_p = std::min(stats.min_p, p);
            if ((!std::isfinite(rho) || !std::isfinite(p) || rho <= 0.0 || p <= 0.0)
                && stats.bad_i < 0) {
                stats.finite = false;
                stats.bad_i = i;
                stats.bad_j = j;
            }
        }
    }
    return stats;
}

template <typename Real>
void write_diagnostic_dump(const DiagnosticSettings& diag,
                           const std::string& reason,
                           EulerSolver<Real>& solver,
                           int nx, int ny,
                           Real dx, Real dy,
                           const StateStats& stats) {
    std::cerr << "[diagnostic] stop_reason=" << reason
              << " step=" << solver.step_count()
              << " time=" << static_cast<double>(solver.time())
              << " min_rho=" << stats.min_rho
              << " min_p=" << stats.min_p
              << " bad_i=" << stats.bad_i
              << " bad_j=" << stats.bad_j << "\n";
    if (!diag.dump_file.empty()) {
        write_binary<Real, EulerNVars>(
            diag.dump_file, solver.grid_view(),
            nx, ny, dx, dy,
            static_cast<Real>(solver.time()));
        std::cerr << "[diagnostic] dump_file=" << diag.dump_file << "\n";
    }
}

template <typename Real>
void run_with_diagnostics(EulerSolver<Real>& solver,
                          int nx, int ny,
                          Real dx, Real dy,
                          double t_end,
                          const std::string& output_file,
                          const std::vector<double>& output_times,
                          const DiagnosticSettings& diag,
                          Real gamma) {
    std::size_t next_output = 0;
    auto write_due_checkpoint = [&]() {
        const double t = static_cast<double>(solver.time());
        while (next_output < output_times.size() &&
               t + 1e-14 >= output_times[next_output]) {
            const std::string checkpoint =
                checkpoint_output_file(output_file, next_output);
            write_binary<Real, EulerNVars>(
                checkpoint, solver.grid_view(),
                nx, ny, dx, dy,
                static_cast<Real>(solver.time()));
            ++next_output;
        }
    };

    std::cerr << "[diagnostic] enabled max_steps=" << diag.max_steps
              << " dt_floor=" << diag.dt_floor
              << " trace=" << (hllc_trace::enabled() ? "on" : "off") << "\n";
    write_due_checkpoint();
    while (static_cast<double>(solver.time()) < t_end) {
        StateStats stats = collect_state_stats(solver, gamma);
        TimeReal dt = solver.compute_dt();
        if (!stats.finite) {
            write_diagnostic_dump(diag, "invalid_state_before_step",
                                  solver, nx, ny, dx, dy, stats);
            return;
        }
        if (!std::isfinite(static_cast<double>(dt)) || dt <= TimeReal(0)) {
            write_diagnostic_dump(diag, "non_positive_dt",
                                  solver, nx, ny, dx, dy, stats);
            return;
        }
        if (diag.dt_floor > 0.0 && static_cast<double>(dt) < diag.dt_floor) {
            write_diagnostic_dump(diag, "dt_floor",
                                  solver, nx, ny, dx, dy, stats);
            return;
        }

        const int step_before = solver.step_count();
        const TimeReal time_before = solver.time();
        solver.step();
        write_due_checkpoint();

        stats = collect_state_stats(solver, gamma);
        if (!stats.finite) {
            write_diagnostic_dump(diag, "invalid_state_after_step",
                                  solver, nx, ny, dx, dy, stats);
            return;
        }
        if (solver.step_count() == step_before || solver.time() == time_before) {
            write_diagnostic_dump(diag, "no_time_or_step_progress",
                                  solver, nx, ny, dx, dy, stats);
            return;
        }
        if (diag.max_steps > 0 && solver.step_count() >= diag.max_steps) {
            write_diagnostic_dump(diag, "max_steps",
                                  solver, nx, ny, dx, dy, stats);
            return;
        }
    }
}

} // namespace hrsc::app
