#pragma once

#include "app/validation.hpp"
#include "core/boundary.hpp"
#include "euler/euler_solver.hpp"

#include <string>
#include <utility>

namespace hrsc::app {

enum class RunMode {
    Normal,
    Convergence,
};

RunMode parse_mode(const Config& cfg);
FluxScheme parse_flux(const Config& cfg);
LimiterScheme parse_limiter(const Config& cfg);
BoundaryType bc_from_string(const std::string& s);
std::pair<BoundaryType, BoundaryType> parse_boundary(const Config& cfg);

} // namespace hrsc::app
