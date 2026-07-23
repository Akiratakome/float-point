#include "app/run_config.hpp"

#include <stdexcept>

namespace hrsc::app {

RunMode parse_mode(const Config& cfg) {
    std::string mode = cfg.get_string("mode", "normal");
    if (mode == "normal") return RunMode::Normal;
    if (mode == "convergence") return RunMode::Convergence;
    throw std::runtime_error(
        "Unknown mode: " + mode + " (expected 'normal' or 'convergence')");
}

// Default chosen to match supervisor recommendation (email 2026-04-17):
// Rusanov is the designated baseline vs HLLC for FP-sensitivity comparison.
FluxScheme parse_flux(const Config& cfg) {
    std::string s = cfg.get_string("solver", "rusanov");
    if (s == "rusanov") return FluxScheme::Rusanov;
    if (s == "hllc") return FluxScheme::HLLC;
    throw std::runtime_error(
        "Unknown solver: " + s + " (expected 'hllc' or 'rusanov')");
}

LimiterScheme parse_limiter(const Config& cfg) {
    std::string s = cfg.get_string("limiter", "minbee");
    if (s == "minbee" || s == "minmod") return LimiterScheme::Minbee;
    if (s == "vanleer" || s == "van_leer") return LimiterScheme::VanLeer;
    if (s == "superbee") return LimiterScheme::Superbee;
    if (s == "vanalbada" || s == "van_albada") return LimiterScheme::VanAlbada;
    throw std::runtime_error(
        "Unknown limiter: " + s +
        " (expected minbee|minmod|vanleer|van_leer|superbee|vanalbada|van_albada)");
}

BoundaryType bc_from_string(const std::string& s) {
    if (s == "outflow")    return BoundaryType::Outflow;
    if (s == "periodic")   return BoundaryType::Periodic;
    if (s == "reflective") return BoundaryType::Reflective;
    throw std::runtime_error(
        "Unknown boundary type: " + s + " (expected outflow|periodic|reflective)");
}

std::pair<BoundaryType, BoundaryType> parse_boundary(const Config& cfg) {
    std::string bc  = cfg.get_string("bc",   "");
    std::string bcx = cfg.get_string("bc_x", "");
    std::string bcy = cfg.get_string("bc_y", "");
    auto pick = [](const std::string& axis, const std::string& fallback,
                   const char* default_value) {
        if (!axis.empty())     return axis;
        if (!fallback.empty()) return fallback;
        return std::string(default_value);
    };
    return { bc_from_string(pick(bcx, bc, "outflow")),
             bc_from_string(pick(bcy, bc, "outflow")) };
}

} // namespace hrsc::app
