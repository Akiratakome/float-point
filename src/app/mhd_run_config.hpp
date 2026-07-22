#pragma once

#include "app/validation.hpp"

#include <string>

namespace hrsc {
class Config;
}

namespace hrsc::app {

struct MhdRunOptions {
    Device device = Device::Cpu;
    std::string output_format;
    std::string output_file;
};

MhdRunOptions parse_mhd_run_options(const Config& cfg);
void require_mhd_device_supported(Device device);

} // namespace hrsc::app
