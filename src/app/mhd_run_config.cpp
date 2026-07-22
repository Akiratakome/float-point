#include "app/mhd_run_config.hpp"

#include "app/run_completion.hpp"
#include "utils/config.hpp"

namespace hrsc::app {

MhdRunOptions parse_mhd_run_options(const Config& cfg) {
    MhdRunOptions options;
    options.device = parse_device(cfg);
    options.output_file = cfg.get_string("output_file", "");
    options.output_format = cfg.get_string("output_format", "");

    if (!cfg.get_string("output_times", "").empty()) {
        throw RunFailure(FailureCategory::UnsupportedCapability,
                         "output_times is not supported by hrsc_mhd");
    }

    if (options.output_format.empty()) {
        if (!options.output_file.empty()) {
            options.output_format = "binary";
        }
        return options;
    }

    if (options.output_format == "binary") {
        if (options.output_file.empty()) {
            throw RunFailure(FailureCategory::ConfigurationError,
                             "output_file must be set when output_format=binary");
        }
        return options;
    }

    throw RunFailure(FailureCategory::ConfigurationError,
                     "output_format=" + options.output_format +
                     " is not supported by hrsc_mhd; expected binary");
}

void require_mhd_device_supported(Device device) {
    if (device == Device::Gpu) {
        throw RunFailure(FailureCategory::UnsupportedCapability,
                         "device=gpu is not supported by hrsc_mhd");
    }
}

} // namespace hrsc::app
