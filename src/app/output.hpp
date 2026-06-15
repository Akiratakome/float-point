#pragma once

#include "core/types.hpp"
#include "euler/euler_solver.hpp"
#include "utils/io.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace hrsc::app {

std::string checkpoint_output_file(const std::string& output_file,
                                   std::size_t index);

template <typename Real>
void run_with_binary_checkpoints(EulerSolver<Real>& solver,
                                 int nx, int ny,
                                 Real dx, Real dy,
                                 double t_end,
                                 const std::string& output_file,
                                 const std::vector<double>& output_times) {
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

    write_due_checkpoint();
    while (static_cast<double>(solver.time()) < t_end) {
        solver.step();
        write_due_checkpoint();
    }
}

} // namespace hrsc::app
