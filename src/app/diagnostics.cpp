#include "app/diagnostics.hpp"

#include <cmath>
#include <cstdlib>
#include <limits>
#include <stdexcept>
#include <string>

namespace hrsc::app {

static const char* env_nonempty(const char* name) {
    const char* value = std::getenv(name);
    return (value && value[0]) ? value : nullptr;
}

static long long env_long_long(const char* name, long long fallback) {
    const char* value = env_nonempty(name);
    if (!value) return fallback;
    try {
        return std::stoll(value);
    } catch (const std::exception&) {
        throw std::runtime_error(std::string(name) + " must be an integer");
    }
}

static int env_int(const char* name, int fallback) {
    long long value = env_long_long(name, fallback);
    if (value < std::numeric_limits<int>::min() ||
        value > std::numeric_limits<int>::max()) {
        throw std::runtime_error(std::string(name) + " is outside int range");
    }
    return static_cast<int>(value);
}

static double env_double(const char* name, double fallback) {
    const char* value = env_nonempty(name);
    if (!value) return fallback;
    try {
        double parsed = std::stod(value);
        if (!std::isfinite(parsed)) {
            throw std::runtime_error("non-finite");
        }
        return parsed;
    } catch (const std::exception&) {
        throw std::runtime_error(std::string(name) + " must be a finite double");
    }
}

DiagnosticSettings configure_diagnostics_from_env() {
    hllc_trace::TraceConfig trace_cfg;
    if (const char* trace_file = env_nonempty("HRSC_HLLC_TRACE_FILE")) {
        trace_cfg.enabled = true;
        trace_cfg.path = trace_file;
        trace_cfg.max_records = env_long_long("HRSC_HLLC_TRACE_MAX_RECORDS", 100000);
        trace_cfg.face_min = env_int("HRSC_HLLC_TRACE_FACE_MIN",
                                     std::numeric_limits<int>::min());
        trace_cfg.face_max = env_int("HRSC_HLLC_TRACE_FACE_MAX",
                                     std::numeric_limits<int>::max());
        trace_cfg.line_min = env_int("HRSC_HLLC_TRACE_LINE_MIN",
                                     std::numeric_limits<int>::min());
        trace_cfg.line_max = env_int("HRSC_HLLC_TRACE_LINE_MAX",
                                     std::numeric_limits<int>::max());
    }
    hllc_trace::configure(trace_cfg);

    DiagnosticSettings diag;
    diag.max_steps = env_long_long("HRSC_DIAG_MAX_STEPS", 0);
    diag.dt_floor = env_double("HRSC_DIAG_DT_FLOOR", 0.0);
    if (const char* dump_file = env_nonempty("HRSC_DIAG_DUMP_FILE")) {
        diag.dump_file = dump_file;
    }
    diag.enabled = hllc_trace::enabled()
                || diag.max_steps > 0
                || diag.dt_floor > 0.0
                || !diag.dump_file.empty();
    return diag;
}

} // namespace hrsc::app
