#include "utils/config.hpp"
#include "core/eos.hpp"
#include "euler/euler_solver.hpp"
#include "euler/exact_riemann.hpp"
#include "utils/error_norms.hpp"
#include "utils/io.hpp"
#include "utils/timer.hpp"
#include "toro_tests.hpp"
#include "lw_tests.hpp"
#include "shock_bubble_tests.hpp"

#ifdef HRSC_HAS_CUDA
#include "gpu/euler_gpu_solver.hpp"
#endif

#include <iostream>
#include <iomanip>
#include <string>
#include <stdexcept>
#include <utility>
#include <vector>
#include <cmath>
#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <sstream>

#ifndef HRSC_REAL
#define HRSC_REAL double   // fallback if built without PrecisionConfig
#endif

// Per overall.md "Precision-Generic Design": the build system selects one
// Real type per binary. All solver objects in main use this single type.
using Real = HRSC_REAL;

using namespace hrsc;

static void setup_ic(GridView<Real, EulerNVars> gv, const std::string& test, Real gamma) {
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
        setup_liska_wendroff_config4(gv, gamma);  // Week 6 D5
    } else if (test == "lw_config12") {
        setup_liska_wendroff_config12(gv, gamma);  // Week 6 D6
    } else if (test == "lw_config6") {
        setup_liska_wendroff_config6(gv, gamma);  // implemented Week 5
    } else if (test == "shock_bubble") {
        setup_shock_bubble(gv, gamma);
    } else {
        throw std::runtime_error("Unknown test: " + test);
    }
}

// Get left/right primitive states for a given test (for exact solver)
static void get_riemann_ic(const std::string& test,
                           double& rhoL, double& uL, double& pL,
                           double& rhoR, double& uR, double& pR,
                           double& x0) {
    x0 = 0.5;
    if (test == "sod") {
        rhoL = 1.0; uL = 0.0; pL = 1.0;
        rhoR = 0.125; uR = 0.0; pR = 0.1;
    } else if (test == "toro2") {
        rhoL = 1.0; uL = -2.0; pL = 0.4;
        rhoR = 1.0; uR =  2.0; pR = 0.4;
    } else if (test == "toro3") {
        rhoL = 1.0; uL = 0.0; pL = 1000.0;
        rhoR = 1.0; uR = 0.0; pR = 0.01;
    } else if (test == "toro4") {
        rhoL = 0.445; uL = 0.698; pL = 3.528;
        rhoR = 0.5;   uR = 0.0;   pR = 0.571;
    } else if (test == "toro5") {
        rhoL = 5.99924; uL = 19.5975;  pL = 460.894;
        rhoR = 5.99242; uR = -6.19633; pR = 46.0950;
    } else if (test == "stationary_contact") {
        rhoL = 1.0; uL = 0.0; pL = 1.0;
        rhoR = 0.5; uR = 0.0; pR = 1.0;
    } else {
        throw std::runtime_error("Unknown test for convergence: " + test);
    }
}

// Default chosen to match supervisor recommendation (email 2026-04-17):
// Rusanov is the designated baseline vs HLLC for FP-sensitivity comparison.
static FluxScheme parse_flux(const Config& cfg) {
    std::string s = cfg.get_string("solver", "rusanov");
    if (s == "rusanov") return FluxScheme::Rusanov;
    if (s == "hllc") return FluxScheme::HLLC;
    throw std::runtime_error(
        "Unknown solver: " + s + " (expected 'hllc' or 'rusanov')");
}

static BoundaryType bc_from_string(const std::string& s) {
    if (s == "outflow")    return BoundaryType::Outflow;
    if (s == "periodic")   return BoundaryType::Periodic;
    if (s == "reflective") return BoundaryType::Reflective;
    throw std::runtime_error(
        "Unknown boundary type: " + s + " (expected outflow|periodic|reflective)");
}

// Resolve per-axis BCs from config. Each axis takes its bc_x/bc_y key if
// non-empty, else falls back to bc, else "outflow". Mixed per-axis modes
// are first-class (Week 5 KH uses bc_x=periodic, bc_y=reflective).
static std::pair<BoundaryType, BoundaryType> parse_boundary(const Config& cfg) {
    std::string bc  = cfg.get_string("bc",   "");
    std::string bcx = cfg.get_string("bc_x", "");
    std::string bcy = cfg.get_string("bc_y", "");
    auto pick = [](const std::string& axis, const std::string& fallback,
                   const char* default_value) {
        if (!axis.empty())     return axis;
        if (!fallback.empty()) return fallback;
        return std::string(default_value);
    };
    return { bc_from_string(pick(bcx, bc, "outflow")),
             bc_from_string(pick(bcy, bc, "outflow")) };
}

static std::vector<double> parse_output_times(const Config& cfg) {
    std::string raw = cfg.get_string("output_times", "");
    if (raw.empty()) return {};

    std::vector<double> result;
    std::istringstream iss(raw);
    std::string token;
    while (std::getline(iss, token, ',')) {
        auto start = token.find_first_not_of(" \t\r\n");
        auto end = token.find_last_not_of(" \t\r\n");
        if (start == std::string::npos) continue;
        std::string trimmed = token.substr(start, end - start + 1);
        try {
            double value = std::stod(trimmed);
            if (!std::isfinite(value) || value < 0.0) {
                throw std::runtime_error(
                    "output_times values must be finite and non-negative: " + trimmed);
            }
            result.push_back(value);
        } catch (const std::invalid_argument&) {
            throw std::runtime_error(
                "Failed to parse output_times value as double: " + trimmed);
        } catch (const std::out_of_range&) {
            throw std::runtime_error(
                "Failed to parse output_times value as double (out of range): " + trimmed);
        }
    }

    std::sort(result.begin(), result.end());
    result.erase(std::unique(result.begin(), result.end()), result.end());
    return result;
}

static std::string checkpoint_output_file(const std::string& output_file,
                                          std::size_t index) {
    std::filesystem::path path(output_file);
    std::ostringstream name;
    name << path.stem().string()
         << "_t" << std::setw(4) << std::setfill('0') << index
         << path.extension().string();
    std::filesystem::path out = path.has_parent_path()
        ? path.parent_path() / name.str()
        : std::filesystem::path(name.str());
    return out.string();
}

static void run_with_binary_checkpoints(EulerSolver<Real>& solver,
                                        int nx, int ny,
                                        Real dx, Real dy,
                                        double t_end,
                                        const std::string& output_file,
                                        const std::vector<double>& output_times) {
    std::size_t next_output = 0;
    auto write_due_checkpoint = [&]() {
        const double t = static_cast<double>(solver.time());
        while (next_output < output_times.size() &&
               t + 1e-14 >= output_times[next_output]) {
            const std::string checkpoint =
                checkpoint_output_file(output_file, next_output);
            write_binary<Real, EulerNVars>(
                checkpoint, solver.grid_view(),
                nx, ny, dx, dy,
                static_cast<Real>(solver.time()));
            ++next_output;
        }
    };

    write_due_checkpoint();
    while (static_cast<double>(solver.time()) < t_end) {
        solver.step();
        write_due_checkpoint();
    }
}

static void run_convergence(const Config& cfg) {
    std::string test = cfg.get_string("test");
    // Read in double (Config API), cast on use to Real for solver state.
    // The exact Riemann reference solution stays in double regardless of
    // the build precision -- it's the ground truth for L_p convergence.
    Real gamma   = static_cast<Real>(cfg.get_double("gamma", 1.4));
    Real cfl     = static_cast<Real>(cfg.get_double("cfl", 0.8));
    double t_end = cfg.get_double("t_end", 0.25);
    double xmin  = cfg.get_double("xmin", 0.0);
    double xmax  = cfg.get_double("xmax", 1.0);
    auto resolutions = cfg.get_int_list("resolutions");
    if (resolutions.empty()) {
        throw std::runtime_error("convergence: resolutions list is empty");
    }
    int largest_nx = *std::max_element(resolutions.begin(), resolutions.end());
    FluxScheme flux = parse_flux(cfg);

    double rhoL, uL, pL, rhoR, uR, pR, x0;
    get_riemann_ic(test, rhoL, uL, pL, rhoR, uR, pR, x0);
    // Allow config override for x0
    x0 = cfg.get_double("x0", x0);

    std::cout << std::setprecision(15) << std::scientific;
    std::cout << "# N        dx            L1_rho        L2_rho        Linf_rho"
              << "      L1_u          L2_u          Linf_u"
              << "        L1_p          L2_p          Linf_p\n";

    for (int nx : resolutions) {
        double dx = (xmax - xmin) / nx;
        EulerSolver<Real> solver(nx, static_cast<Real>(dx),
                                 static_cast<Real>(xmin),
                                 gamma, cfl, t_end, flux);
        setup_ic(solver.grid_view(), test, gamma);
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
            double xi = (x - x0) / t_end;
            double erho, eu, ep;
            exact_riemann_sample(static_cast<double>(gamma), xi,
                rhoL, uL, pL, rhoR, uR, pR,
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
    if (ny > 1 && ymax <= ymin) {
        throw std::runtime_error(
            "ymax must be > ymin when ny > 1 (got ymin=" + std::to_string(ymin) +
            ", ymax=" + std::to_string(ymax) + ")");
    }
    Real   gamma = static_cast<Real>(cfg.get_double("gamma", 1.4));
    Real   cfl   = static_cast<Real>(cfg.get_double("cfl", 0.8));
    double t_end = cfg.get_double("t_end", 0.25);
    int    out_prec = cfg.get_int("output_precision", 17);
    if (out_prec < 1 || out_prec > 17) {
        throw std::runtime_error(
            "output_precision must be in [1, 17] (got " + std::to_string(out_prec) + ")");
    }
    FluxScheme flux = parse_flux(cfg);
    auto [bc_x, bc_y] = parse_boundary(cfg);
    std::string output_format = cfg.get_string("output_format", "table");
    std::string output_file = cfg.get_string("output_file", "");
    std::vector<double> output_times = parse_output_times(cfg);
    if (!output_times.empty() && output_format != "binary") {
        throw std::runtime_error("output_times requires output_format=binary");
    }
    if (!output_times.empty() && output_file.empty()) {
        throw std::runtime_error(
            "output_file must be set when output_times is present");
    }
    // Wall-clock throttled progress on stderr (<=0 disables; default off
    // preserves legacy bit-identical behaviour for existing cfgs).
    double progress_interval_s = cfg.get_double("progress_interval_s", 0.0);

    double dx = (xmax - xmin) / nx;

    if (ny > 1) {
        // ── 2D path ───────────────────────────────────────────────────────────
        double dy = (ymax - ymin) / ny;
        EulerSolver<Real> solver(nx, ny,
                                 static_cast<Real>(dx), static_cast<Real>(dy),
                                 static_cast<Real>(xmin), static_cast<Real>(ymin),
                                 gamma, cfl, t_end,
                                 flux, bc_x, bc_y);
        setup_ic(solver.grid_view(), test, gamma);
        Timer total;
        total.start();
        if (output_times.empty()) {
            solver.run(progress_interval_s);
        } else {
            run_with_binary_checkpoints(
                solver, nx, ny,
                static_cast<Real>(dx), static_cast<Real>(dy),
                t_end, output_file, output_times);
        }
        total.stop();
        std::cerr << "[timing] total_s=" << total.elapsed_seconds() << "\n";
#ifdef HRSC_ENABLE_PROFILING
        write_profiling_timings(std::cerr, solver.profiling());
#endif

        std::cerr << "Finished: " << solver.step_count() << " steps, t = "
                  << solver.time() << "\n";

        if (output_format == "binary") {
            if (output_file.empty()) {
                throw std::runtime_error(
                    "output_file must be set when output_format=binary");
            }
            write_binary<Real, EulerNVars>(
                output_file, solver.grid_view(),
                nx, ny, static_cast<Real>(dx), static_cast<Real>(dy),
                static_cast<Real>(solver.time()));
            return;
        }
        if (output_format != "table") {
            throw std::runtime_error(
                "Unknown output_format: " + output_format + " (expected table|binary)");
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
                             flux, bc_x, bc_y);
    setup_ic(solver.grid_view(), test, gamma);
    Timer total;
    total.start();
    if (output_times.empty()) {
        solver.run(progress_interval_s);
    } else {
        run_with_binary_checkpoints(
            solver, nx, 1,
            static_cast<Real>(dx), static_cast<Real>(dx),
            t_end, output_file, output_times);
    }
    total.stop();
    std::cerr << "[timing] total_s=" << total.elapsed_seconds() << "\n";
#ifdef HRSC_ENABLE_PROFILING
    write_profiling_timings(std::cerr, solver.profiling());
#endif

    std::cerr << "Finished: " << solver.step_count() << " steps, t = "
              << static_cast<double>(solver.time()) << "\n";

    auto gv = solver.grid_view();
    if (output_format == "binary") {
        if (output_file.empty()) {
            throw std::runtime_error(
                "output_file must be set when output_format=binary");
        }
        write_binary<Real, EulerNVars>(
            output_file, gv, nx, 1,
            static_cast<Real>(dx), static_cast<Real>(dx),
            static_cast<Real>(solver.time()));
        return;
    }
    if (output_format != "table") {
        throw std::runtime_error(
            "Unknown output_format: " + output_format + " (expected table|binary)");
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
    if (ny > 1 && ymax <= ymin) {
        throw std::runtime_error(
            "ymax must be > ymin when ny > 1 (got ymin=" + std::to_string(ymin) +
            ", ymax=" + std::to_string(ymax) + ")");
    }
    Real   gamma = static_cast<Real>(cfg.get_double("gamma", 1.4));
    Real   cfl   = static_cast<Real>(cfg.get_double("cfl", 0.8));
    double t_end = cfg.get_double("t_end", 0.25);
    int    out_prec = cfg.get_int("output_precision", 17);
    if (out_prec < 1 || out_prec > 17) {
        throw std::runtime_error(
            "output_precision must be in [1, 17] (got " + std::to_string(out_prec) + ")");
    }
    FluxScheme flux = parse_flux(cfg);
    auto [bc_x, bc_y] = parse_boundary(cfg);
    std::string output_format = cfg.get_string("output_format", "table");
    std::string output_file = cfg.get_string("output_file", "");
    if (!parse_output_times(cfg).empty()) {
        throw std::runtime_error(
            "output_times is not supported for device=gpu; use multiple final-time runs");
    }

    double dx = (xmax - xmin) / nx;
    double dy = (ny > 1) ? (ymax - ymin) / ny : dx;

    // Build the IC into a host-side Grid2D, then move it into the GPU solver.
    Grid2D<Real, EulerNVars> ic(nx, ny);
    ic.dx = static_cast<Real>(dx);
    ic.dy = static_cast<Real>(dy);
    setup_ic(ic.view(), test, gamma);

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
        if (output_file.empty()) {
            throw std::runtime_error(
                "output_file must be set when output_format=binary");
        }
        write_binary<Real, EulerNVars>(
            output_file, gv, nx, ny,
            static_cast<Real>(dx), static_cast<Real>(dy),
            static_cast<Real>(solver.current_time()));
        return;
    }
    if (output_format != "table") {
        throw std::runtime_error(
            "Unknown output_format: " + output_format + " (expected table|binary)");
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
    std::string mode = cfg.get_string("mode", "normal");
    const std::string device = cfg.get_string("device", "cpu");
    if (device != "cpu" && device != "gpu") {
        throw std::runtime_error("Invalid device='" + device + "'; expected 'cpu' or 'gpu'");
    }
    if (device == "gpu") {
#ifndef HRSC_HAS_CUDA
        throw std::runtime_error("device=gpu requires building with -DENABLE_CUDA=ON");
#else
        if (mode == "convergence") {
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

    if (mode == "convergence") {
        run_convergence(cfg);
    } else {
        run_normal(cfg);
    }

    return 0;
} catch (const std::exception& e) {
    std::cerr << "[error] " << e.what() << "\n";
    return 2;
}
