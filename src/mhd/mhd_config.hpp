#pragma once

#include "core/boundary.hpp"

#include <stdexcept>
#include <string>

namespace hrsc {

enum class MhdTestCase { BrioWu };

inline MhdTestCase parse_mhd_test(const std::string& value) {
    if (value == "brio_wu") {
        return MhdTestCase::BrioWu;
    }
    throw std::invalid_argument("unsupported MHD test case: " + value);
}

inline BoundaryType parse_mhd_boundary(const std::string& value) {
    if (value == "outflow") {
        return BoundaryType::Outflow;
    }
    throw std::invalid_argument("unsupported MHD boundary condition: " + value);
}

} // namespace hrsc
