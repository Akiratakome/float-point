#pragma once

#include "core/grid.hpp"
#include "core/types.hpp"
#include "euler/euler_flux.hpp"

#include <string>

namespace hrsc::app {

template <typename Real>
void setup_case_ic(GridView<Real, EulerNVars> gv,
                   const std::string& test,
                   Real gamma);

struct RiemannInitialCondition {
    double rhoL = 0.0;
    double uL = 0.0;
    double pL = 0.0;
    double rhoR = 0.0;
    double uR = 0.0;
    double pR = 0.0;
    double x0 = 0.5;
};

RiemannInitialCondition get_riemann_ic(const std::string& test);

} // namespace hrsc::app
