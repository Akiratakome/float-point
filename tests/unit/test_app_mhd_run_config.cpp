#include "catch.hpp"
#include "app/mhd_run_config.hpp"
#include "app/run_completion.hpp"
#include "utils/config.hpp"

#include <array>
#include <string>

using namespace hrsc;
using namespace hrsc::app;

TEST_CASE("MHD run options preserve legacy CPU binary behavior", "[app][mhd]") {
    Config cfg;
    cfg.set("output_file", "grid.bin");

    const auto options = parse_mhd_run_options(cfg);

    REQUIRE(options.device == Device::Cpu);
    REQUIRE(options.output_format == "binary");
    REQUIRE(options.output_file == "grid.bin");
}

TEST_CASE("MHD run options preserve no-output default", "[app][mhd]") {
    Config cfg;

    const auto options = parse_mhd_run_options(cfg);

    REQUIRE(options.device == Device::Cpu);
    REQUIRE(options.output_format.empty());
    REQUIRE(options.output_file.empty());
}

TEST_CASE("MHD binary output format requires an output file", "[app][mhd]") {
    Config cfg;
    cfg.set("output_format", "binary");

    try {
        (void)parse_mhd_run_options(cfg);
        FAIL("expected configuration failure");
    } catch (const RunFailure& failure) {
        REQUIRE(failure.category() == FailureCategory::ConfigurationError);
        REQUIRE(std::string(failure.what()) ==
                "output_file must be set when output_format=binary");
    }
}

TEST_CASE("MHD explicit binary output format preserves a configured path", "[app][mhd]") {
    Config cfg;
    cfg.set("output_format", "binary");
    cfg.set("output_file", "grid.bin");

    const auto options = parse_mhd_run_options(cfg);

    REQUIRE(options.output_format == "binary");
    REQUIRE(options.output_file == "grid.bin");
}

TEST_CASE("MHD table output is rejected as a configuration error", "[app][mhd]") {
    Config cfg;
    cfg.set("output_format", "table");

    try {
        (void)parse_mhd_run_options(cfg);
        FAIL("expected configuration failure");
    } catch (const RunFailure& failure) {
        REQUIRE(failure.category() == FailureCategory::ConfigurationError);
    }
}

TEST_CASE("MHD any configured output times are an unsupported capability", "[app][mhd]") {
    const std::array<const char*, 3> raw_values{{"0.01", "not-a-time", ", \t "}};
    for (const char* raw_value : raw_values) {
        CAPTURE(raw_value);
        Config cfg;
        cfg.set("output_times", raw_value);

        try {
            (void)parse_mhd_run_options(cfg);
            FAIL("expected unsupported capability failure");
        } catch (const RunFailure& failure) {
            REQUIRE(failure.category() == FailureCategory::UnsupportedCapability);
        }
    }
}

TEST_CASE("MHD empty configured output times are an unsupported capability", "[app][mhd]") {
    std::istringstream input("output_times =   \n");
    Config cfg(input);

    REQUIRE(cfg.get_string("output_times").empty());
    try {
        (void)parse_mhd_run_options(cfg);
        FAIL("expected unsupported capability failure");
    } catch (const RunFailure& failure) {
        REQUIRE(failure.category() == FailureCategory::UnsupportedCapability);
    }
}

TEST_CASE("MHD GPU option is accepted for the opt-in HLL CUDA path", "[app][mhd]") {
    Config cfg;
    cfg.set("device", "gpu");

    const auto options = parse_mhd_run_options(cfg);
    REQUIRE(options.device == Device::Gpu);
    REQUIRE_NOTHROW(require_mhd_device_supported(options.device));
}
