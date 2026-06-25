#pragma once

#include "core/boundary.hpp"

#include <stdexcept>
#include <string>

namespace hrsc {

enum class MhdTestCase { BrioWu, DivbBlob, OrszagTang, KelvinHelmholtz };

inline MhdTestCase parse_mhd_test(const std::string& value) {
    if (value == "brio_wu")          return MhdTestCase::BrioWu;
    if (value == "divb_blob")        return MhdTestCase::DivbBlob;
    if (value == "orszag_tang")      return MhdTestCase::OrszagTang;
    if (value == "kelvin_helmholtz") return MhdTestCase::KelvinHelmholtz;
    throw std::invalid_argument("unsupported MHD test case: " + value);
}

inline BoundaryType parse_mhd_boundary(const std::string& value) {
    if (value == "outflow")  return BoundaryType::Outflow;
    if (value == "periodic") return BoundaryType::Periodic;
    throw std::invalid_argument("unsupported MHD boundary condition: " + value);
}

} // namespace hrsc
