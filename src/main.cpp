#include "app/cases.hpp"
#include "app/diagnostics.hpp"
#include "app/output.hpp"
#include "app/run_config.hpp"
#include "utils/config.hpp"
#include "core/eos.hpp"
#include "euler/euler_solver.hpp"
#include "euler/hllc_trace.hpp"
#include "euler/exact_riemann.hpp"
#include "utils/error_norms.hpp"
#include "utils/io.hpp"
#include "utils/timer.hpp"

#ifdef HRSC_HAS_CUDA
#include "gpu/euler_gpu_solver.hpp"
#endif

#include <iostream>
#include <iomanip>
#include <string>
#include <stdexcept>
#include <vector>
#include <algorithm>
#include <cstdlib>

#ifndef HRSC_REAL
#define HRSC_REAL double   // fallback if built without PrecisionConfig
#endif

// Per overall.md "Precision-Generic Design": the build system selects one
// Real type per binary. All solver objects in main use this single type.
using Real = HRSC_REAL;

using namespace hrsc;
using namespace hrsc::app;

static void run_convergence(const Config& cfg) {
    std::string test = cfg.get_string("test");
    // Read in double (Config API), cast on use to Real for solver state.
    // The exact Riemann reference solution stays in double regardless of
    // the build precision -- it's the ground truth for L_p convergence.
    double gamma_cfg = cfg.get_double("gamma", 1.4);
    double cfl_cfg   = cfg.get_double("cfl", 0.8);
    double t_end = cfg.get_double("t_end", 0.25);
    double xmin  = cfg.get_double("xmin", 0.0);
    double xmax  = cfg.get_double("xmax", 1.0);
    validate_domain(1, 1, xmin, xmax, 0.0, 0.0);
    validate_physics(gamma_cfg, cfl_cfg, t_end);
    Real gamma = static_cast<Real>(gamma_cfg);
    Real cfl   = static_cast<Real>(cfl_cfg);
    auto resolutions = cfg.get_int_list("resolutions");
    if (resolutions.empty()) {
        throw std::runtime_error("convergence: resolutions list is empty");
    }
    for (int nx : resolutions) {
        if (nx <= 0) {
            throw std::runtime_error(
                "convergence: resolutions must be positive");
        }
    }
    int largest_nx = *std::max_element(resolutions.begin(), resolutions.end());
    FluxScheme flux = parse_flux(cfg);
    LimiterScheme limiter = parse_limiter(cfg);

    RiemannInitialCondition ic = get_riemann_ic(test);
    // Allow config override for x0
    ic.x0 = cfg.get_double("x0", ic.x0);

    std::cout << std::setprecision(15) << std::scientific;
    std::cout << "# N        dx            L1_rho        L2_rho        Linf_rho"
              << "      L1_u          L2_u          Linf_u"
              << "        L1_p          L2_p          Linf_p\n";

    for (int nx : resolutions) {
        double dx = (xmax - xmin) / nx;
        EulerSolver<Real> solver(nx, static_cast<Real>(dx),
                                 static_cast<Real>(xmin),
                                 gamma, cfl, t_end, flux,
                                 BoundaryType::Outflow, BoundaryType::Outflow,
                                 limiter);
        setup_case_ic(solver.grid_view(), test, gamma);
        Timer total;
        total.start();
        solver.run();
        total.stop();
        std::cerr << "[timing] total_s=" << total.elapsed_seconds()
                  << " nx=" << nx << "\n";
#ifdef HRSC_ENABLE_PROFILING
        write_profiling_timings(std::cerr, solver.profiling());
#endif

        // Numerical solution is cast to double for comparison with the
        // double-precision exact reference (consistent error norms across
        // float and double builds).
        std::vector<double> num_rho(nx), num_u(nx), num_p(nx);
        std::vector<double> ext_rho(nx), ext_u(nx), ext_p(nx);

        auto gv = solver.grid_view();
        for (int i = 0; i < nx; ++i) {
            Vec<Real, EulerNVars> cons;
            for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, 0, v);
            Vec<Real, EulerNVars> prim = cons_to_prim(cons, gamma);
            num_rho[i] = static_cast<double>(prim[PRHO]);
            num_u[i]   = static_cast<double>(prim[VX]);
            num_p[i]   = static_cast<double>(prim[PRES]);

            double x = xmin + (i + 0.5) * dx;
            double xi = (x - ic.x0) / t_end;
            double erho, eu, ep;
            exact_riemann_sample(static_cast<double>(gamma), xi,
                ic.rhoL, ic.uL, ic.pL, ic.rhoR, ic.uR, ic.pR,
                erho, eu, ep);
            ext_rho[i] = erho;
            ext_u[i]   = eu;
            ext_p[i]   = ep;
        }

        auto err_rho = compute_error(num_rho.data(), ext_rho.data(), nx, dx);
        auto err_u   = compute_error(num_u.data(),   ext_u.data(),   nx, dx);
        auto err_p   = compute_error(num_p.data(),   ext_p.data(),   nx, dx);

        std::cout << std::setw(6) << nx
                  << "  " << dx
                  << "  " << err_rho.L1 << "  " << err_rho.L2 << "  " << err_rho.Linf
                  << "  " << err_u.L1   << "  " << err_u.L2   << "  " << err_u.Linf
                  << "  " << err_p.L1   << "  " << err_p.L2   << "  " << err_p.Linf
                  << "\n";

        if (nx == largest_nx) {
            const char* dump_dir = std::getenv("HRSC_DUMP_DIR");
            const char* dump_tag = std::getenv("HRSC_DUMP_TAG");
            if (dump_dir && dump_tag && dump_dir[0] && dump_tag[0]) {
                std::string path = std::string(dump_dir) + "/" + test
                                 + "_" + dump_tag + "_grid.bin";
                write_binary<Real, EulerNVars>(
                    path, solver.grid_view(),
                    nx, 1,
                    static_cast<Real>(dx), static_cast<Real>(dx),
                    static_cast<Real>(solver.time()));
                std::cerr << "[dump] wrote " << path << "\n";
            }
        }
    }
}

static void run_normal(const Config& cfg) {
    std::string test = cfg.get_string("test");
    int    nx    = cfg.get_int("nx", 200);
    int    ny    = cfg.get_int("ny", 1);
    double xmin  = cfg.get_double("xmin", 0.0);
    double xmax  = cfg.get_double("xmax", 1.0);
    double ymin  = cfg.get_double("ymin", 0.0);
    double ymax  = cfg.get_double("ymax", 0.0);
    double gamma_cfg = cfg.get_double("gamma", 1.4);
    double cfl_cfg   = cfg.get_double("cfl", 0.8);
    double t_end = cfg.get_double("t_end", 0.25);
    int    out_prec = cfg.get_int("output_precision", 17);
    FluxScheme flux = parse_flux(cfg);
    LimiterScheme limiter = parse_limiter(cfg);
    auto [bc_x, bc_y] = parse_boundary(cfg);
    std::string output_format = cfg.get_string("output_format", "table");
    std::string output_file = cfg.get_string("output_file", "");
    std::vector<double> output_times = parse_output_times(cfg);
    validate_domain(nx, ny, xmin, xmax, ymin, ymax);
    validate_physics(gamma_cfg, cfl_cfg, t_end);
    validate_output_precision(out_prec);
    validate_output_options(output_format, output_file, output_times, t_end,
                            false);
    Real gamma = static_cast<Real>(gamma_cfg);
    Real cfl   = static_cast<Real>(cfl_cfg);
    // Wall-clock throttled progress on stderr (<=0 disables; default off
    // preserves legacy bit-identical behaviour for existing cfgs).
    double progress_interval_s = cfg.get_double("progress_interval_s", 0.0);

    double dx = (xmax - xmin) / nx;
    DiagnosticSettings diagnostics = configure_diagnostics_from_env();

    if (ny > 1) {
        // ── 2D path ───────────────────────────────────────────────────────────
        double dy = (ymax - ymin) / ny;
        EulerSolver<Real> solver(nx, ny,
                                 static_cast<Real>(dx), static_cast<Real>(dy),
                                 static_cast<Real>(xmin), static_cast<Real>(ymin),
                                 gamma, cfl, t_end,
                                 flux, bc_x, bc_y, limiter);
        setup_case_ic(solver.grid_view(), test, gamma);
        Timer total;
        total.start();
        if (diagnostics.enabled) {
            run_with_diagnostics(
                solver, nx, ny,
                static_cast<Real>(dx), static_cast<Real>(dy),
                t_end, output_file, output_times, diagnostics, gamma);
        } else if (output_times.empty()) {
            solver.run(progress_interval_s);
        } else {
            run_with_binary_checkpoints(
                solver, nx, ny,
                static_cast<Real>(dx), static_cast<Real>(dy),
                t_end, output_file, output_times);
        }
        hllc_trace::close();
        total.stop();
        std::cerr << "[timing] total_s=" << total.elapsed_seconds() << "\n";
#ifdef HRSC_ENABLE_PROFILING
        write_profiling_timings(std::cerr, solver.profiling());
#endif

        std::cerr << "Finished: " << solver.step_count() << " steps, t = "
                  << solver.time() << "\n";

        if (output_format == "binary") {
            write_binary<Real, EulerNVars>(
                output_file, solver.grid_view(),
                nx, ny, static_cast<Real>(dx), static_cast<Real>(dy),
                static_cast<Real>(solver.time()));
            return;
        }

        auto gv = solver.grid_view();
        std::cout << std::setprecision(out_prec);
        // Gnuplot-friendly: one line per (i, j), blank line between j-blocks.
        for (int j = 0; j < ny; ++j) {
            double y = ymin + (j + 0.5) * dy;
            for (int i = 0; i < nx; ++i) {
                double x = xmin + (i + 0.5) * dx;
                Vec<Real, EulerNVars> cons;
                for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
                Vec<Real, EulerNVars> prim = cons_to_prim(cons, gamma);

                std::cout << x                                 << "\t"
                          << y                                 << "\t"
                          << static_cast<double>(prim[PRHO])   << "\t"
                          << static_cast<double>(prim[VX])     << "\t"
                          << static_cast<double>(prim[VY])     << "\t"
                          << static_cast<double>(prim[PRES])   << "\n";
            }
            std::cout << "\n";
        }
        return;
    }

    // ── 1D path (preserve bit-identical legacy output format) ─────────────────
    EulerSolver<Real> solver(nx, static_cast<Real>(dx),
                             static_cast<Real>(xmin),
                             gamma, cfl, t_end,
                             flux, bc_x, bc_y, limiter);
    setup_case_ic(solver.grid_view(), test, gamma);
    Timer total;
    total.start();
    if (diagnostics.enabled) {
        run_with_diagnostics(
            solver, nx, 1,
            static_cast<Real>(dx), static_cast<Real>(dx),
            t_end, output_file, output_times, diagnostics, gamma);
    } else if (output_times.empty()) {
        solver.run(progress_interval_s);
    } else {
        run_with_binary_checkpoints(
            solver, nx, 1,
            static_cast<Real>(dx), static_cast<Real>(dx),
            t_end, output_file, output_times);
    }
    hllc_trace::close();
    total.stop();
    std::cerr << "[timing] total_s=" << total.elapsed_seconds() << "\n";
#ifdef HRSC_ENABLE_PROFILING
    write_profiling_timings(std::cerr, solver.profiling());
#endif

    std::cerr << "Finished: " << solver.step_count() << " steps, t = "
              << static_cast<double>(solver.time()) << "\n";

    auto gv = solver.grid_view();
    if (output_format == "binary") {
        write_binary<Real, EulerNVars>(
            output_file, gv, nx, 1,
            static_cast<Real>(dx), static_cast<Real>(dx),
            static_cast<Real>(solver.time()));
        return;
    }
    std::cout << std::setprecision(out_prec);
    for (int i = 0; i < nx; ++i) {
        double x = xmin + (i + 0.5) * dx;
        Vec<Real, EulerNVars> cons;
        for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, 0, v);
        Vec<Real, EulerNVars> prim = cons_to_prim(cons, gamma);

        std::cout << x                                 << "\t"
                  << static_cast<double>(prim[PRHO])   << "\t"
                  << static_cast<double>(prim[VX])     << "\t"
                  << static_cast<double>(prim[VY])     << "\t"
                  << static_cast<double>(prim[PRES])   << "\n";
    }
}

#ifdef HRSC_HAS_CUDA
// GPU equivalent of run_normal: builds the IC into a Grid2D, hands it to
// EulerGpuSolver, runs to completion, downloads, and shares the existing
// CPU IO path. Mirrors run_normal's cfg keys 1:1; bit-exact CPU output is
// validated by the e2e and sweep regression tests, not here.
static void run_normal_gpu(const Config& cfg) {
    std::string test = cfg.get_string("test");
    int    nx    = cfg.get_int("nx", 200);
    int    ny    = cfg.get_int("ny", 1);
    double xmin  = cfg.get_double("xmin", 0.0);
    double xmax  = cfg.get_double("xmax", 1.0);
    double ymin  = cfg.get_double("ymin", 0.0);
    double ymax  = cfg.get_double("ymax", 0.0);
    double gamma_cfg = cfg.get_double("gamma", 1.4);
    double cfl_cfg   = cfg.get_double("cfl", 0.8);
    double t_end = cfg.get_double("t_end", 0.25);
    int    out_prec = cfg.get_int("output_precision", 17);
    FluxScheme flux = parse_flux(cfg);
    LimiterScheme limiter = parse_limiter(cfg);
    if (limiter != LimiterScheme::Minbee) {
        throw std::runtime_error(
            "limiter selection is currently supported only for device=cpu; "
            "GPU kernels use the default minbee limiter");
    }
    auto [bc_x, bc_y] = parse_boundary(cfg);
    std::string output_format = cfg.get_string("output_format", "table");
    std::string output_file = cfg.get_string("output_file", "");
    std::vector<double> output_times = parse_output_times(cfg);
    validate_domain(nx, ny, xmin, xmax, ymin, ymax);
    validate_physics(gamma_cfg, cfl_cfg, t_end);
    validate_output_precision(out_prec);
    validate_output_options(output_format, output_file, output_times, t_end,
                            true);
    Real gamma = static_cast<Real>(gamma_cfg);
    Real cfl   = static_cast<Real>(cfl_cfg);

    double dx = (xmax - xmin) / nx;
    double dy = (ny > 1) ? (ymax - ymin) / ny : dx;

    // Build the IC into a host-side Grid2D, then move it into the GPU solver.
    Grid2D<Real, EulerNVars> ic(nx, ny);
    ic.dx = static_cast<Real>(dx);
    ic.dy = static_cast<Real>(dy);
    setup_case_ic(ic.view(), test, gamma);

    EulerGpuSolver<Real> solver(std::move(ic),
                                static_cast<Real>(xmin),
                                static_cast<Real>(ymin),
                                gamma, cfl, t_end,
                                flux, bc_x, bc_y);

    Timer total;
    total.start();
    double run_s = solver.run();
    total.stop();
    std::cerr << "[timing] total_s=" << total.elapsed_seconds()
              << " gpu_run_s=" << run_s << "\n";
    std::cerr << "Finished: " << solver.step_count() << " steps, t = "
              << static_cast<double>(solver.current_time()) << "\n";

    Grid2D<Real, EulerNVars> final_grid = solver.download_host_grid();
    GridView<Real, EulerNVars> gv = final_grid.view();

    if (output_format == "binary") {
        write_binary<Real, EulerNVars>(
            output_file, gv, nx, ny,
            static_cast<Real>(dx), static_cast<Real>(dy),
            static_cast<Real>(solver.current_time()));
        return;
    }

    std::cout << std::setprecision(out_prec);
    if (ny > 1) {
        for (int j = 0; j < ny; ++j) {
            double y = ymin + (j + 0.5) * dy;
            for (int i = 0; i < nx; ++i) {
                double x = xmin + (i + 0.5) * dx;
                Vec<Real, EulerNVars> cons;
                for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
                Vec<Real, EulerNVars> prim = cons_to_prim(cons, gamma);
                std::cout << x << "\t" << y << "\t"
                          << static_cast<double>(prim[PRHO]) << "\t"
                          << static_cast<double>(prim[VX])   << "\t"
                          << static_cast<double>(prim[VY])   << "\t"
                          << static_cast<double>(prim[PRES]) << "\n";
            }
            std::cout << "\n";
        }
    } else {
        for (int i = 0; i < nx; ++i) {
            double x = xmin + (i + 0.5) * dx;
            Vec<Real, EulerNVars> cons;
            for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, 0, v);
            Vec<Real, EulerNVars> prim = cons_to_prim(cons, gamma);
            std::cout << x << "\t"
                      << static_cast<double>(prim[PRHO]) << "\t"
                      << static_cast<double>(prim[VX])   << "\t"
                      << static_cast<double>(prim[VY])   << "\t"
                      << static_cast<double>(prim[PRES]) << "\n";
        }
    }
}
#endif // HRSC_HAS_CUDA

int main(int argc, char* argv[]) try {
    if (argc < 2) {
        std::cerr << "Usage: hrsc <config_file>\n";
        return 1;
    }

    Config cfg(argv[1]);
    RunMode mode = parse_mode(cfg);
    const std::string device = cfg.get_string("device", "cpu");
    if (device != "cpu" && device != "gpu") {
        throw std::runtime_error("Invalid device='" + device + "'; expected 'cpu' or 'gpu'");
    }
    if (device == "gpu") {
        LimiterScheme limiter = parse_limiter(cfg);
        if (limiter != LimiterScheme::Minbee) {
            throw std::runtime_error(
                "limiter selection is currently supported only for device=cpu; "
                "GPU kernels use the default minbee limiter");
        }
#ifndef HRSC_HAS_CUDA
        throw std::runtime_error("device=gpu requires building with -DENABLE_CUDA=ON");
#else
        if (mode == RunMode::Convergence) {
            // Convergence sweep on GPU is out of scope for Week 6; the GPU
            // path is for the time-stepping smoke matrix and regression
            // gate. Convergence stays CPU-only until a later week.
            throw std::runtime_error(
                "device=gpu does not support mode=convergence yet");
        }
        run_normal_gpu(cfg);
        return 0;
#endif
    }

    if (mode == RunMode::Convergence) {
        run_convergence(cfg);
    } else {
        run_normal(cfg);
    }

    return 0;
} catch (const std::exception& e) {
    std::cerr << "[error] " << e.what() << "\n";
    return 2;
}
