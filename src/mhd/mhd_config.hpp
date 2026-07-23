#pragma once

#include "core/boundary.hpp"

#include <stdexcept>
#include <string>

namespace hrsc {

enum class MhdTestCase { BrioWu, DivbBlob, OrszagTang, KelvinHelmholtz };

enum class MhdRiemann { Hll, Hlld };

enum class MhdDevice { Cpu, Gpu };

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

inline MhdRiemann parse_mhd_riemann(const std::string& value) {
    if (value == "hll")  return MhdRiemann::Hll;
    if (value == "hlld") return MhdRiemann::Hlld;
    throw std::invalid_argument("unsupported MHD Riemann solver: " + value);
}

inline MhdDevice parse_mhd_device(const std::string& value) {
    if (value == "cpu") return MhdDevice::Cpu;
    if (value == "gpu") return MhdDevice::Gpu;
    throw std::invalid_argument("unsupported MHD device: " + value);
}

} // namespace hrsc
