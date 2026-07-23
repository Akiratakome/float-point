#pragma once

#include <iosfwd>
#include <stdexcept>
#include <string>

namespace hrsc::app {

enum class FailureCategory {
    ConfigurationError,
    UnsupportedCapability,
    NumericalFailure,
    IncompleteRun,
    ArtifactError,
};

class RunFailure : public std::runtime_error {
public:
    RunFailure(FailureCategory category, const std::string& message);

    FailureCategory category() const noexcept { return category_; }

private:
    FailureCategory category_;
};

void require_run_complete(double final_time, double target_time, int steps);
void write_run_success(std::ostream& output,
                       double final_time, double target_time, int steps);
void write_run_failure(std::ostream& output, const RunFailure& failure);

} // namespace hrsc::app
