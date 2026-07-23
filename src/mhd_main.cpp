#include "utils/config.hpp"
#include "utils/error_norms.hpp"
#include "utils/io.hpp"
#include "mhd/hll.hpp"
#include "mhd/hlld.hpp"
#include "mhd/mhd_config.hpp"
#include "mhd/mhd_solver.hpp"

#ifdef HRSC_HAS_CUDA
#include "gpu/mhd_gpu_solver.hpp"
#endif

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

void validate_cfg(int nx, int ny, double xmin, double xmax, double ymin, double ymax,
                  double gamma, double cfl, double t_end, double x0, double glm_cr) {
    if (nx <= 0) {
        throw std::invalid_argument("nx must be > 0");
    }
    if (ny <= 0) {
        throw std::invalid_argument("ny must be > 0");
    }
    if (!(glm_cr >= 0.0)) {
        throw std::invalid_argument("glm_cr must be >= 0");
    }
    require_finite("xmin", xmin);
    require_finite("xmax", xmax);
    require_finite("ymin", ymin);
    require_finite("ymax", ymax);
    require_finite("gamma", gamma);
    require_finite("cfl", cfl);
    require_finite("t_end", t_end);
    require_finite("x0", x0);
    if (!(xmax > xmin)) {
        throw std::invalid_argument("xmax must be > xmin");
    }
    if (ny > 1 && !(ymax > ymin)) {
        throw std::invalid_argument("ymax must be > ymin when ny > 1");
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

template <typename Flux>
int run_mhd(int nx, int ny, double xmin, double ymin, double gamma, double cfl,
            double t_end, double x0, double glm_cr, hrsc::MhdTestCase test,
            hrsc::BoundaryType bc, hrsc::BoundaryType bc_y, Real dx, Real dy,
            const std::string& out) {
    hrsc::MhdSolver<Real, Flux> solver(nx, ny, dx, dy, (Real)xmin, (Real)ymin,
                                       (Real)gamma, (Real)cfl, t_end, bc, bc_y, (Real)glm_cr);

    auto gv = solver.grid_view();
    if (test == hrsc::MhdTestCase::BrioWu) {
        for (int j = 0; j < ny; ++j)
            hrsc::setup_brio_wu_row<Real>(gv, nx, dx, (Real)xmin, (Real)gamma, (Real)x0, j);
    } else if (test == hrsc::MhdTestCase::OrszagTang) {
        hrsc::setup_orszag_tang<Real>(gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::KelvinHelmholtz) {
        hrsc::setup_kelvin_helmholtz<Real>(gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::DivbBlob) {
        hrsc::setup_divb_blob<Real>(gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else {
        throw std::invalid_argument("unsupported MHD test case dispatch");
    }

    solver.run();

    gv = solver.grid_view();
    hrsc::DivBNorms<Real> db = hrsc::compute_divB_norms<Real>(gv, nx, ny, dx, dy);
    std::fprintf(stderr, "[mhd] t=%.6f steps=%d divB_mean=%.3e divB_max=%.3e\n",
                 solver.time(), solver.step_count(), (double)db.mean, (double)db.max);

    if (!out.empty())
        hrsc::write_binary<Real, hrsc::MhdNVars>(out, gv, nx, ny, dx, dy, (Real)solver.time());
    return 0;
}

hrsc::Grid2D<Real, hrsc::MhdNVars> make_mhd_initial_grid(
    int nx, int ny, double xmin, double ymin, double gamma, double x0,
    Real dx, Real dy, hrsc::MhdTestCase test) {
    hrsc::Grid2D<Real, hrsc::MhdNVars> grid(nx, ny);
    grid.dx = dx;
    grid.dy = dy;

    auto gv = grid.view();
    if (test == hrsc::MhdTestCase::BrioWu) {
        for (int j = 0; j < ny; ++j) {
            hrsc::setup_brio_wu_row<Real>(
                gv, nx, dx, (Real)xmin, (Real)gamma, (Real)x0, j);
        }
    } else if (test == hrsc::MhdTestCase::OrszagTang) {
        hrsc::setup_orszag_tang<Real>(
            gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::KelvinHelmholtz) {
        hrsc::setup_kelvin_helmholtz<Real>(
            gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::DivbBlob) {
        hrsc::setup_divb_blob<Real>(
            gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else {
        throw std::invalid_argument("unsupported MHD test case dispatch");
    }

    return grid;
}

int run_mhd_gpu(int nx, int ny, double xmin, double ymin, double gamma,
                double cfl, double t_end, double x0, double glm_cr,
                hrsc::MhdTestCase test, hrsc::BoundaryType bc,
                hrsc::BoundaryType bc_y, Real dx, Real dy,
                const std::string& out) {
#ifdef HRSC_HAS_CUDA
    auto grid = make_mhd_initial_grid(
        nx, ny, xmin, ymin, gamma, x0, dx, dy, test);
    hrsc::MhdGpuSolver<Real> solver(
        grid, (Real)xmin, (Real)ymin, (Real)gamma, (Real)cfl, t_end,
        (Real)glm_cr, bc, bc_y);

    solver.run();

    hrsc::Grid2D<Real, hrsc::MhdNVars> final_grid = solver.download_host_grid();
    auto gv = final_grid.view();
    hrsc::DivBNorms<Real> db =
        hrsc::compute_divB_norms<Real>(gv, nx, ny, dx, dy);
    std::fprintf(stderr, "[mhd] t=%.6f steps=%d divB_mean=%.3e divB_max=%.3e\n",
                 solver.current_time(), solver.step_count(),
                 (double)db.mean, (double)db.max);

    if (!out.empty()) {
        hrsc::write_binary<Real, hrsc::MhdNVars>(
            out, gv, nx, ny, dx, dy, (Real)solver.current_time());
    }
    return 0;
#else
    (void)nx; (void)ny; (void)xmin; (void)ymin; (void)gamma; (void)cfl;
    (void)t_end; (void)x0; (void)glm_cr; (void)test; (void)bc; (void)bc_y;
    (void)dx; (void)dy; (void)out;
    throw std::runtime_error("device=gpu requires building with -DENABLE_CUDA=ON");
#endif
}

} // namespace

int main(int argc, char** argv) try {
    if (argc < 2) { std::fprintf(stderr, "usage: hrsc_mhd <cfg>\n"); return 1; }
    hrsc::Config cfg(argv[1]);

    const int    nx      = cfg.get_int("nx", 800);
    const int    ny      = cfg.get_int("ny", 1);
    const double xmin    = cfg.get_double("xmin", 0.0);
    const double xmax    = cfg.get_double("xmax", 1.0);
    const double ymin    = cfg.get_double("ymin", 0.0);
    const double ymax    = cfg.get_double("ymax", ny > 1 ? 1.0 : 0.0);
    const double gamma   = cfg.get_double("gamma", 2.0);
    const double cfl     = cfg.get_double("cfl", 0.4);
    const double t_end   = cfg.get_double("t_end", 0.1);
    const double x0      = cfg.get_double("x0", 0.5);
    const double glm_cr  = cfg.get_double("glm_cr", ny > 1 ? 0.18 : 0.0);
    const hrsc::MhdTestCase test = hrsc::parse_mhd_test(cfg.get_string("test", "brio_wu"));
    const hrsc::MhdRiemann riemann = hrsc::parse_mhd_riemann(cfg.get_string("riemann", "hll"));
    const hrsc::MhdDevice device = hrsc::parse_mhd_device(cfg.get_string("device", "cpu"));
    const hrsc::BoundaryType bc   = hrsc::parse_mhd_boundary(cfg.get_string("bc", "outflow"));
    const hrsc::BoundaryType bc_y = hrsc::parse_mhd_boundary(cfg.get_string("bc_y", cfg.get_string("bc", "outflow")));
    const std::string out = cfg.get_string("output_file", "");

    validate_cfg(nx, ny, xmin, xmax, ymin, ymax, gamma, cfl, t_end, x0, glm_cr);

    const Real dx = static_cast<Real>((xmax - xmin) / nx);
    const Real dy = (ny > 1) ? static_cast<Real>((ymax - ymin) / ny) : dx;

    if (device == hrsc::MhdDevice::Gpu) {
        if (riemann != hrsc::MhdRiemann::Hll) {
            throw std::invalid_argument("device=gpu supports only riemann=hll");
        }
        return run_mhd_gpu(nx, ny, xmin, ymin, gamma, cfl, t_end, x0,
                           glm_cr, test, bc, bc_y, dx, dy, out);
    }

    if (riemann == hrsc::MhdRiemann::Hlld) {
        return run_mhd<hrsc::HlldFlux>(nx, ny, xmin, ymin, gamma, cfl, t_end,
                                       x0, glm_cr, test, bc, bc_y, dx, dy, out);
    }
    return run_mhd<hrsc::HllFlux>(nx, ny, xmin, ymin, gamma, cfl, t_end,
                                  x0, glm_cr, test, bc, bc_y, dx, dy, out);
} catch (const std::exception& e) {
    std::fprintf(stderr, "[error] %s\n", e.what());
    return 2;
}
