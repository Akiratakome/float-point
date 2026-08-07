#include "app/mhd_result.hpp"
#include "app/mhd_run_config.hpp"
#include "app/run_completion.hpp"
#include "app/validation.hpp"
#include "utils/config.hpp"
#include "mhd/hll.hpp"
#include "mhd/hlld.hpp"
#include "mhd/mhd_config.hpp"
#include "mhd/mhd_solver.hpp"

#ifdef HRSC_HAS_CUDA
#include "gpu/mhd_gpu_solver.hpp"
#endif

#include <cmath>
#include <cstdio>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>

#ifndef HRSC_REAL
#define HRSC_REAL double
#endif
using Real = HRSC_REAL;

namespace {

using hrsc::app::FailureCategory;
using hrsc::app::RunFailure;

void require_finite(const char* name, double value) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument(std::string(name) + " must be finite");
    }
}

void validate_mhd_coordinates(double xmin, double xmax, double ymin, double ymax) {
    require_finite("xmin", xmin);
    require_finite("xmax", xmax);
    require_finite("ymin", ymin);
    require_finite("ymax", ymax);
}

void validate_mhd_options(double x0, double glm_cr) {
    require_finite("x0", x0);
    require_finite("glm_cr", glm_cr);
    if (!(glm_cr >= 0.0)) {
        throw std::invalid_argument("glm_cr must be >= 0");
    }
}

template <typename Callable>
decltype(auto) advance_solver(Callable&& callable) {
    try {
        return std::forward<Callable>(callable)();
    } catch (const RunFailure&) {
        throw;
    } catch (const std::exception& error) {
        throw RunFailure(FailureCategory::NumericalFailure, error.what());
    }
}

template <typename Flux>
int run_mhd(int nx, int ny, double xmin, double ymin, double gamma, double cfl,
            double t_end, double x0, double glm_cr, hrsc::MhdTestCase test,
            hrsc::BoundaryType bc, hrsc::BoundaryType bc_y, Real dx, Real dy,
            const hrsc::app::MhdRunOptions& options) {
    hrsc::MhdSolver<Real, Flux> solver(nx, ny, dx, dy, (Real)xmin, (Real)ymin,
                                       (Real)gamma, (Real)cfl, t_end, bc, bc_y,
                                       (Real)glm_cr);

    auto grid = solver.grid_view();
    if (test == hrsc::MhdTestCase::BrioWu) {
        for (int j = 0; j < ny; ++j)
            hrsc::setup_brio_wu_row<Real>(grid, nx, dx, (Real)xmin,
                                          (Real)gamma, (Real)x0, j);
    } else if (test == hrsc::MhdTestCase::OrszagTang) {
        hrsc::setup_orszag_tang<Real>(grid, nx, ny, dx, dy, (Real)xmin,
                                      (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::KelvinHelmholtz) {
        hrsc::setup_kelvin_helmholtz<Real>(grid, nx, ny, dx, dy, (Real)xmin,
                                           (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::KelvinHelmholtzLecoanet) {
        hrsc::setup_kelvin_helmholtz_lecoanet<Real>(
            grid, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::CpAlfven) {
        hrsc::setup_cp_alfven<Real>(grid, nx, ny, dx, dy, (Real)xmin,
                                    (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::DivbBlob) {
        hrsc::setup_divb_blob<Real>(grid, nx, ny, dx, dy, (Real)xmin,
                                    (Real)ymin, (Real)gamma);
    } else {
        throw std::invalid_argument("unsupported MHD test case dispatch");
    }

    advance_solver([&] { solver.run(); });

    hrsc::app::require_run_complete(
        static_cast<double>(solver.time()), t_end, solver.step_count());
    grid = solver.grid_view();
    try {
        hrsc::app::write_mhd_result(
            std::cerr, options, grid, nx, ny, dx, dy,
            static_cast<Real>(solver.time()), solver.step_count());
    } catch (const RunFailure&) {
        throw;
    } catch (const std::exception& error) {
        throw RunFailure(FailureCategory::ArtifactError, error.what());
    }
#ifdef HRSC_HLLD_COUNTERS
    {
        const auto& c = hrsc::hlld_counters();
        std::cerr << "{\"hlld_counters\":{"
                  << "\"calls\":" << c.calls
                  << ",\"fallback\":" << c.fallback
                  << ",\"star_left\":" << c.star_left
                  << ",\"star_right\":" << c.star_right
                  << ",\"dstar_left\":" << c.dstar_left
                  << ",\"dstar_right\":" << c.dstar_right
                  << ",\"tie_ssl\":" << c.tie_ssl
                  << ",\"tie_ssr\":" << c.tie_ssr
                  << ",\"tie_sm\":" << c.tie_sm
                  << ",\"line_total_x\":" << c.line_total_x
                  << ",\"line_total_y\":" << c.line_total_y
                  << ",\"line_revert_x\":" << c.line_revert_x
                  << ",\"line_revert_y\":" << c.line_revert_y
                  << "}}\n";
    }
#endif
    hrsc::app::write_run_success(
        std::cerr, static_cast<double>(solver.time()), t_end, solver.step_count());
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
    } else if (test == hrsc::MhdTestCase::KelvinHelmholtzLecoanet) {
        hrsc::setup_kelvin_helmholtz_lecoanet<Real>(
            gv, nx, ny, dx, dy, (Real)xmin, (Real)ymin, (Real)gamma);
    } else if (test == hrsc::MhdTestCase::CpAlfven) {
        hrsc::setup_cp_alfven<Real>(
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
                const hrsc::app::MhdRunOptions& options) {
#ifdef HRSC_HAS_CUDA
    auto grid = make_mhd_initial_grid(
        nx, ny, xmin, ymin, gamma, x0, dx, dy, test);
    hrsc::MhdGpuSolver<Real> solver(
        grid, (Real)xmin, (Real)ymin, (Real)gamma, (Real)cfl, t_end,
        (Real)glm_cr, bc, bc_y);

    advance_solver([&] { solver.run(); });

    hrsc::app::require_run_complete(
        solver.current_time(), t_end, solver.step_count());

    hrsc::Grid2D<Real, hrsc::MhdNVars> final_grid = solver.download_host_grid();
    auto gv = final_grid.view();
    try {
        hrsc::app::write_mhd_result(
            std::cerr, options, gv, nx, ny, dx, dy,
            static_cast<Real>(solver.current_time()), solver.step_count());
    } catch (const RunFailure&) {
        throw;
    } catch (const std::exception& error) {
        throw RunFailure(FailureCategory::ArtifactError, error.what());
    }
    hrsc::app::write_run_success(
        std::cerr, solver.current_time(), t_end, solver.step_count());
    return 0;
#else
    (void)nx; (void)ny; (void)xmin; (void)ymin; (void)gamma; (void)cfl;
    (void)t_end; (void)x0; (void)glm_cr; (void)test; (void)bc; (void)bc_y;
    (void)dx; (void)dy; (void)options;
    throw RunFailure(FailureCategory::UnsupportedCapability,
                     "device=gpu requires building with -DENABLE_CUDA=ON");
#endif
}

} // namespace

int main(int argc, char** argv) try {
    if (argc < 2) {
        std::fprintf(stderr, "usage: hrsc_mhd <cfg>\n");
        return 1;
    }
    hrsc::Config cfg(argv[1]);

    const hrsc::app::MhdRunOptions options = hrsc::app::parse_mhd_run_options(cfg);
    hrsc::app::require_mhd_device_supported(options.device);

    const int nx = cfg.get_int("nx", 800);
    const int ny = cfg.get_int("ny", 1);
    const double xmin = cfg.get_double("xmin", 0.0);
    const double xmax = cfg.get_double("xmax", 1.0);
    const double ymin = cfg.get_double("ymin", 0.0);
    const double ymax = cfg.get_double("ymax", ny > 1 ? 1.0 : 0.0);
    const double gamma = cfg.get_double("gamma", 2.0);
    const double cfl = cfg.get_double("cfl", 0.4);
    const double t_end = cfg.get_double("t_end", 0.1);
    const double x0 = cfg.get_double("x0", 0.5);
    const double glm_cr = cfg.get_double("glm_cr", ny > 1 ? 0.18 : 0.0);
    const hrsc::MhdTestCase test =
        hrsc::parse_mhd_test(cfg.get_string("test", "brio_wu"));
    const hrsc::MhdRiemann riemann =
        hrsc::parse_mhd_riemann(cfg.get_string("riemann", "hll"));
    const hrsc::BoundaryType bc =
        hrsc::parse_mhd_boundary(cfg.get_string("bc", "outflow"));
    const hrsc::BoundaryType bc_y = hrsc::parse_mhd_boundary(
        cfg.get_string("bc_y", cfg.get_string("bc", "outflow")));

    validate_mhd_coordinates(xmin, xmax, ymin, ymax);
    hrsc::app::validate_domain(nx, ny, xmin, xmax, ymin, ymax);
    hrsc::app::validate_physics(gamma, cfl, t_end);
    validate_mhd_options(x0, glm_cr);

    const Real dx = static_cast<Real>((xmax - xmin) / nx);
    const Real dy = (ny > 1) ? static_cast<Real>((ymax - ymin) / ny) : dx;

    if (options.device == hrsc::app::Device::Gpu) {
        if (riemann != hrsc::MhdRiemann::Hll) {
            throw std::invalid_argument("device=gpu supports only riemann=hll");
        }
        return run_mhd_gpu(nx, ny, xmin, ymin, gamma, cfl, t_end, x0,
                           glm_cr, test, bc, bc_y, dx, dy, options);
    }

    if (riemann == hrsc::MhdRiemann::Hlld) {
        return run_mhd<hrsc::HlldFlux>(nx, ny, xmin, ymin, gamma, cfl, t_end,
                                       x0, glm_cr, test, bc, bc_y, dx, dy, options);
    }
    return run_mhd<hrsc::HllFlux>(nx, ny, xmin, ymin, gamma, cfl, t_end,
                                  x0, glm_cr, test, bc, bc_y, dx, dy, options);
} catch (const hrsc::app::RunFailure& error) {
    hrsc::app::write_run_failure(std::cerr, error);
    return 2;
} catch (const std::exception& error) {
    hrsc::app::write_run_failure(
        std::cerr, hrsc::app::RunFailure(
            hrsc::app::FailureCategory::ConfigurationError, error.what()));
    return 2;
}
