#include "catch.hpp"
#include "app/run_completion.hpp"

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

    try {
        require_run_complete(std::numeric_limits<double>::quiet_NaN(), 0.1, 4);
        FAIL("expected numerical failure");
    } catch (const RunFailure& failure) {
        REQUIRE(failure.category() == FailureCategory::NumericalFailure);
    }
}

TEST_CASE("run success serialization is stable", "[app][run]") {
    std::ostringstream output;

    write_run_success(output, 0.1, 0.1, 4);

    REQUIRE(output.str() ==
            "[run-status] status=success final_time=0.1 target_time=0.1 steps=4\n");
}

TEST_CASE("run failures preserve structured and human-readable output", "[app][run]") {
    std::ostringstream output;
    const RunFailure failure(FailureCategory::IncompleteRun, "run ended early");

    write_run_failure(output, failure);

    REQUIRE(output.str() ==
            "[run-status] status=failed reason=incomplete_run\n"
            "[error] run ended early\n");
}
