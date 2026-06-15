#include "app/cases.hpp"

#include "cases/euler/toro_tests.hpp"
#include "cases/euler/lw_tests.hpp"
#include "cases/euler/shock_bubble_tests.hpp"

#include <stdexcept>

namespace hrsc::app {

template <typename Real>
void setup_case_ic(GridView<Real, EulerNVars> gv,
                   const std::string& test,
                   Real gamma) {
    if (test == "sod") {
        setup_sod(gv, gamma);
    } else if (test == "toro2") {
        setup_toro2(gv, gamma);
    } else if (test == "toro3") {
        setup_toro3(gv, gamma);
    } else if (test == "toro4") {
        setup_toro4(gv, gamma);
    } else if (test == "toro5") {
        setup_toro5(gv, gamma);
    } else if (test == "stationary_contact") {
        setup_stationary_contact(gv, gamma);
    } else if (test == "lw_config3") {
        setup_liska_wendroff_config3(gv, gamma);
    } else if (test == "lw_config4") {
        setup_liska_wendroff_config4(gv, gamma);
    } else if (test == "lw_config12") {
        setup_liska_wendroff_config12(gv, gamma);
    } else if (test == "lw_config6") {
        setup_liska_wendroff_config6(gv, gamma);
    } else if (test == "shock_bubble") {
        setup_shock_bubble(gv, gamma);
    } else {
        throw std::runtime_error("Unknown test: " + test);
    }
}

RiemannInitialCondition get_riemann_ic(const std::string& test) {
    RiemannInitialCondition ic;
    if (test == "sod") {
        ic.rhoL = 1.0; ic.uL = 0.0; ic.pL = 1.0;
        ic.rhoR = 0.125; ic.uR = 0.0; ic.pR = 0.1;
    } else if (test == "toro2") {
        ic.rhoL = 1.0; ic.uL = -2.0; ic.pL = 0.4;
        ic.rhoR = 1.0; ic.uR =  2.0; ic.pR = 0.4;
    } else if (test == "toro3") {
        ic.rhoL = 1.0; ic.uL = 0.0; ic.pL = 1000.0;
        ic.rhoR = 1.0; ic.uR = 0.0; ic.pR = 0.01;
    } else if (test == "toro4") {
        ic.rhoL = 0.445; ic.uL = 0.698; ic.pL = 3.528;
        ic.rhoR = 0.5;   ic.uR = 0.0;   ic.pR = 0.571;
    } else if (test == "toro5") {
        ic.rhoL = 5.99924; ic.uL = 19.5975;  ic.pL = 460.894;
        ic.rhoR = 5.99242; ic.uR = -6.19633; ic.pR = 46.0950;
    } else if (test == "stationary_contact") {
        ic.rhoL = 1.0; ic.uL = 0.0; ic.pL = 1.0;
        ic.rhoR = 0.5; ic.uR = 0.0; ic.pR = 1.0;
    } else {
        throw std::runtime_error("Unknown test for convergence: " + test);
    }
    return ic;
}

template void setup_case_ic<float>(GridView<float, EulerNVars>,
                                   const std::string&,
                                   float);
template void setup_case_ic<double>(GridView<double, EulerNVars>,
                                    const std::string&,
                                    double);

} // namespace hrsc::app
