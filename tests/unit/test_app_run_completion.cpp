#include "catch.hpp"
#include "app/run_completion.hpp"

#include <array>
#include <limits>
#include <sstream>

using namespace hrsc::app;

TEST_CASE("run completion rejects early and non-finite final times", "[app][run]") {
    REQUIRE_NOTHROW(require_run_complete(0.1, 0.1, 4));

    try {
        require_run_complete(0.09, 0.1, 4);
        FAIL("expected incomplete run failure");
    } catch (const RunFailure& failure) {
        REQUIRE(failure.category() == FailureCategory::IncompleteRun);
    }

    const auto nan = std::numeric_limits<double>::quiet_NaN();
    const auto infinity = std::numeric_limits<double>::infinity();
    struct TimeCase {
        const char* label;
        double final_time;
        double target_time;
    };
    const std::array<TimeCase, 6> non_finite_cases{{
        {"NaN final time", nan, 0.1},
        {"positive infinite final time", infinity, 0.1},
        {"negative infinite final time", -infinity, 0.1},
        {"NaN target time", 0.1, nan},
        {"positive infinite target time", 0.1, infinity},
        {"negative infinite target time", 0.1, -infinity},
    }};
    for (const auto& test_case : non_finite_cases) {
        CAPTURE(test_case.label);
        try {
            require_run_complete(test_case.final_time, test_case.target_time, 4);
            FAIL("expected numerical failure");
        } catch (const RunFailure& failure) {
            REQUIRE(failure.category() == FailureCategory::NumericalFailure);
        }
    }
}

TEST_CASE("run success serialization is stable", "[app][run]") {
    std::ostringstream output;

    write_run_success(output, 0.1, 0.1, 4);

    REQUIRE(output.str() ==
            "[run-status] status=success final_time=0.1 target_time=0.1 steps=4\n");
}

TEST_CASE("run failures preserve structured and human-readable output", "[app][run]") {
    struct FailureCase {
        FailureCategory category;
        const char* reason;
        const char* message;
    };
    const std::array<FailureCase, 5> failure_cases{{
        {FailureCategory::ConfigurationError, "configuration_error", "invalid config"},
        {FailureCategory::UnsupportedCapability, "unsupported_capability", "unsupported device"},
        {FailureCategory::NumericalFailure, "numerical_failure", "invalid timestep"},
        {FailureCategory::IncompleteRun, "incomplete_run", "run ended early"},
        {FailureCategory::ArtifactError, "artifact_error", "missing output"},
    }};
    for (const auto& test_case : failure_cases) {
        CAPTURE(test_case.reason);
        std::ostringstream output;

        write_run_failure(output, RunFailure(test_case.category, test_case.message));

        REQUIRE(output.str() ==
                std::string("[run-status] status=failed reason=") + test_case.reason +
                "\n[error] " + test_case.message + "\n");
    }
}
