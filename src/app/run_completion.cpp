#include "app/run_completion.hpp"

#include <cmath>
#include <ostream>

namespace hrsc::app {
namespace {

const char* failure_reason(FailureCategory category) {
    switch (category) {
    case FailureCategory::ConfigurationError:
        return "configuration_error";
    case FailureCategory::UnsupportedCapability:
        return "unsupported_capability";
    case FailureCategory::NumericalFailure:
        return "numerical_failure";
    case FailureCategory::IncompleteRun:
        return "incomplete_run";
    case FailureCategory::ArtifactError:
        return "artifact_error";
    }
    return "artifact_error";
}

} // namespace

RunFailure::RunFailure(FailureCategory category, const std::string& message)
    : std::runtime_error(message), category_(category) {}

void require_run_complete(double final_time, double target_time, int steps) {
    (void)steps;
    if (!std::isfinite(final_time) || !std::isfinite(target_time)) {
        throw RunFailure(FailureCategory::NumericalFailure,
                         "run completion time is non-finite");
    }
    if (final_time < target_time) {
        throw RunFailure(FailureCategory::IncompleteRun,
                         "run ended before reaching target time");
    }
}

void write_run_success(std::ostream& output,
                       double final_time, double target_time, int steps) {
    output << "[run-status] status=success final_time=" << final_time
           << " target_time=" << target_time << " steps=" << steps << '\n';
}

void write_run_failure(std::ostream& output, const RunFailure& failure) {
    output << "[run-status] status=failed reason="
           << failure_reason(failure.category()) << '\n';
    output << "[error] " << failure.what() << '\n';
}

} // namespace hrsc::app
