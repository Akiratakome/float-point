#pragma once

#include "core/boundary.hpp"
#include "euler/euler_solver.hpp"
#include "utils/config.hpp"

#include <string>
#include <utility>
#include <vector>

namespace hrsc::app {

enum class RunMode {
    Normal,
    Convergence,
};

RunMode parse_mode(const Config& cfg);
FluxScheme parse_flux(const Config& cfg);
LimiterScheme parse_limiter(const Config& cfg);
BoundaryType bc_from_string(const std::string& s);
std::pair<BoundaryType, BoundaryType> parse_boundary(const Config& cfg);
std::vector<double> parse_output_times(const Config& cfg);

void validate_domain(int nx, int ny,
                     double xmin, double xmax,
                     double ymin, double ymax);
void validate_physics(double gamma, double cfl, double t_end);
void validate_output_precision(int out_prec);
void validate_output_options(const std::string& output_format,
                             const std::string& output_file,
                             const std::vector<double>& output_times,
                             double t_end,
                             bool gpu_device);

} // namespace hrsc::app
