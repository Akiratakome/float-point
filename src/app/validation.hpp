#pragma once

#include "utils/config.hpp"

#include <string>
#include <vector>

namespace hrsc::app {

enum class Device {
    Cpu,
    Gpu,
};

Device parse_device(const Config& cfg);
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
