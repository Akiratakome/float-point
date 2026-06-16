#include "utils/config.hpp"
#include "utils/error_norms.hpp"
#include "utils/io.hpp"
#include "mhd/mhd_solver.hpp"

#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <string>

#ifndef HRSC_REAL
#define HRSC_REAL double
#endif
using Real = HRSC_REAL;

namespace {

void require_finite(const char* name, double value) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument(std::string(name) + " must be finite");
    }
}

void validate_cfg(int nx, double xmin, double xmax, double gamma,
                  double cfl, double t_end, double x0) {
    if (nx <= 0) {
        throw std::invalid_argument("nx must be > 0");
    }
    require_finite("xmin", xmin);
    require_finite("xmax", xmax);
    require_finite("gamma", gamma);
    require_finite("cfl", cfl);
    require_finite("t_end", t_end);
    require_finite("x0", x0);
    if (!(xmax > xmin)) {
        throw std::invalid_argument("xmax must be > xmin");
    }
    if (!(gamma > 1.0)) {
        throw std::invalid_argument("gamma must be > 1.0");
    }
    if (!(cfl > 0.0)) {
        throw std::invalid_argument("cfl must be > 0.0");
    }
    if (!(t_end >= 0.0)) {
        throw std::invalid_argument("t_end must be >= 0.0");
    }
}

} // namespace

int main(int argc, char** argv) try {
    if (argc < 2) { std::fprintf(stderr, "usage: hrsc_mhd <cfg>\n"); return 1; }
    hrsc::Config cfg(argv[1]);

    const int    nx    = cfg.get_int("nx", 800);
    const double xmin  = cfg.get_double("xmin", 0.0);
    const double xmax  = cfg.get_double("xmax", 1.0);
    const double gamma = cfg.get_double("gamma", 2.0);
    const double cfl   = cfg.get_double("cfl", 0.4);
    const double t_end = cfg.get_double("t_end", 0.1);
    const double x0    = cfg.get_double("x0", 0.5);
    const std::string out = cfg.get_string("output_file", "");
    validate_cfg(nx, xmin, xmax, gamma, cfl, t_end, x0);

    const Real dx = static_cast<Real>((xmax - xmin) / nx);
    hrsc::MhdSolver<Real> solver(nx, dx, static_cast<Real>(xmin),
                                 static_cast<Real>(gamma), static_cast<Real>(cfl), t_end);
    hrsc::setup_brio_wu<Real>(solver.grid_view(), nx, dx, static_cast<Real>(xmin),
                              static_cast<Real>(gamma), static_cast<Real>(x0));
    solver.run();

    auto gv = solver.grid_view();
    hrsc::DivBNorms<Real> db = hrsc::compute_divB_norms<Real>(gv, nx, 1, dx, dx);
    std::fprintf(stderr, "[mhd] t=%.6f steps=%d divB_mean=%.3e divB_max=%.3e\n",
                 solver.time(), solver.step_count(), (double)db.mean, (double)db.max);

    if (!out.empty())
        hrsc::write_binary<Real, hrsc::MhdNVars>(out, gv, nx, 1, dx, dx, (Real)solver.time());
    return 0;
} catch (const std::exception& e) {
    std::fprintf(stderr, "[error] %s\n", e.what());
    return 2;
}
