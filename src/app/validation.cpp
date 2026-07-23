#include "app/validation.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <stdexcept>

namespace hrsc::app {

Device parse_device(const Config& cfg) {
    const std::string value = cfg.get_string("device", "cpu");
    if (value == "cpu") return Device::Cpu;
    if (value == "gpu") return Device::Gpu;
    throw std::runtime_error(
        "Invalid device='" + value + "'; expected 'cpu' or 'gpu'");
}

std::vector<double> parse_output_times(const Config& cfg) {
    std::string raw = cfg.get_string("output_times", "");
    if (raw.empty()) return {};

    std::vector<double> result;
    std::istringstream iss(raw);
    std::string token;
    while (std::getline(iss, token, ',')) {
        auto start = token.find_first_not_of(" \t\r\n");
        auto end = token.find_last_not_of(" \t\r\n");
        if (start == std::string::npos) continue;
        std::string trimmed = token.substr(start, end - start + 1);
        try {
            double value = std::stod(trimmed);
            if (!std::isfinite(value) || value < 0.0) {
                throw std::runtime_error(
                    "output_times values must be finite and non-negative: " + trimmed);
            }
            result.push_back(value);
        } catch (const std::invalid_argument&) {
            throw std::runtime_error(
                "Failed to parse output_times value as double: " + trimmed);
        } catch (const std::out_of_range&) {
            throw std::runtime_error(
                "Failed to parse output_times value as double (out of range): " + trimmed);
        }
    }

    std::sort(result.begin(), result.end());
    result.erase(std::unique(result.begin(), result.end()), result.end());
    return result;
}

void validate_domain(int nx, int ny,
                     double xmin, double xmax,
                     double ymin, double ymax) {
    if (nx <= 0) {
        throw std::runtime_error("nx must be positive (got " + std::to_string(nx) + ")");
    }
    if (ny <= 0) {
        throw std::runtime_error("ny must be positive (got " + std::to_string(ny) + ")");
    }
    if (!(xmax > xmin)) {
        throw std::runtime_error(
            "xmax must be > xmin (got xmin=" + std::to_string(xmin) +
            ", xmax=" + std::to_string(xmax) + ")");
    }
    if (ny > 1 && !(ymax > ymin)) {
        throw std::runtime_error(
            "ymax must be > ymin when ny > 1 (got ymin=" + std::to_string(ymin) +
            ", ymax=" + std::to_string(ymax) + ")");
    }
}

void validate_physics(double gamma, double cfl, double t_end) {
    if (!std::isfinite(gamma) || gamma <= 1.0) {
        throw std::runtime_error("gamma must be finite and > 1");
    }
    if (!std::isfinite(cfl) || cfl <= 0.0) {
        throw std::runtime_error("cfl must be finite and positive");
    }
    if (!std::isfinite(t_end) || t_end < 0.0) {
        throw std::runtime_error("t_end must be finite and non-negative");
    }
}

void validate_output_precision(int out_prec) {
    if (out_prec < 1 || out_prec > 17) {
        throw std::runtime_error(
            "output_precision must be in [1, 17] (got " +
            std::to_string(out_prec) + ")");
    }
}

void validate_output_options(const std::string& output_format,
                             const std::string& output_file,
                             const std::vector<double>& output_times,
                             double t_end,
                             bool gpu_device) {
    if (output_format != "table" && output_format != "binary") {
        throw std::runtime_error(
            "Unknown output_format: " + output_format + " (expected table|binary)");
    }
    if (output_format == "binary" && output_file.empty()) {
        throw std::runtime_error("output_file must be set when output_format=binary");
    }
    if (!output_times.empty() && output_format != "binary") {
        throw std::runtime_error("output_times requires output_format=binary");
    }
    if (!output_times.empty() && output_file.empty()) {
        throw std::runtime_error(
            "output_file must be set when output_times is present");
    }
    if (gpu_device && !output_times.empty()) {
        throw std::runtime_error(
            "output_times is not supported for device=gpu; use multiple final-time runs");
    }
    for (double output_time : output_times) {
        if (output_time > t_end) {
            std::ostringstream msg;
            msg << "output_times value " << output_time
                << " exceeds t_end " << t_end;
            throw std::runtime_error(msg.str());
        }
    }
}

} // namespace hrsc::app
