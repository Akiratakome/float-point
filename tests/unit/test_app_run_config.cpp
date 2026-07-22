#include "catch.hpp"
#include "app/run_config.hpp"
#include "utils/config.hpp"

using namespace hrsc;
using namespace hrsc::app;

TEST_CASE("parse_mode accepts only supported run modes", "[app][config]") {
    Config cfg;
    REQUIRE(parse_mode(cfg) == RunMode::Normal);

    cfg.set("mode", "convergence");
    REQUIRE(parse_mode(cfg) == RunMode::Convergence);

    cfg.set("mode", "typo");
    REQUIRE_THROWS_WITH(parse_mode(cfg),
                        "Unknown mode: typo (expected 'normal' or 'convergence')");
}

TEST_CASE("parse_device defaults to CPU and validates values", "[app][config]") {
    Config cfg;
    REQUIRE(parse_device(cfg) == Device::Cpu);

    cfg.set("device", "gpu");
    REQUIRE(parse_device(cfg) == Device::Gpu);

    cfg.set("device", "typo");
    REQUIRE_THROWS_WITH(parse_device(cfg),
                        "Invalid device='typo'; expected 'cpu' or 'gpu'");
}

TEST_CASE("validate_output_options rejects unreachable checkpoint times", "[app][config]") {
    const std::vector<double> output_times{0.01, 0.04};

    REQUIRE_THROWS_WITH(
        validate_output_options("binary", "grid.bin", output_times, 0.03,
                                false),
        "output_times value 0.04 exceeds t_end 0.03");
}

TEST_CASE("validate_output_options rejects binary output without a path before running", "[app][config]") {
    REQUIRE_THROWS_WITH(
        validate_output_options("binary", "", {}, 0.03, false),
        "output_file must be set when output_format=binary");
}
