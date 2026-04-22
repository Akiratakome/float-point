#include "utils/config.hpp"
#include "core/eos.hpp"
#include "euler/euler_solver.hpp"
#include "euler/exact_riemann.hpp"
#include "utils/error_norms.hpp"
#include "toro_tests.hpp"
#include "lw_tests.hpp"

#include <iostream>
#include <iomanip>
#include <string>
#include <stdexcept>
#include <vector>
#include <cmath>

using namespace hrsc;

static void setup_ic(GridView<double, EulerNVars> gv, const std::string& test, double gamma) {
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
    } else if (test == "lw_config6") {
        setup_liska_wendroff_config6(gv, gamma);  // stub throws (Week 5)
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
    return (s == "rusanov") ? FluxScheme::Rusanov : FluxScheme::HLLC;
}

static void run_convergence(const Config& cfg) {
    std::string test = cfg.get_string("test");
    double gamma = cfg.get_double("gamma", 1.4);
    double cfl   = cfg.get_double("cfl", 0.8);
    double t_end = cfg.get_double("t_end", 0.25);
    double xmin  = cfg.get_double("xmin", 0.0);
    double xmax  = cfg.get_double("xmax", 1.0);
    auto resolutions = cfg.get_int_list("resolutions");
    FluxScheme flux = parse_flux(cfg);

    double rhoL, uL, pL, rhoR, uR, pR, x0;
    get_riemann_ic(test, rhoL, uL, pL, rhoR, uR, pR, x0);
    // Allow config override for x0
    x0 = cfg.get_double("x0", x0);

    std::cout << std::setprecision(6) << std::scientific;
    std::cout << "# N        dx            L1_rho        L2_rho        Linf_rho"
              << "      L1_u          L2_u          Linf_u"
              << "        L1_p          L2_p          Linf_p\n";

    for (int nx : resolutions) {
        double dx = (xmax - xmin) / nx;
        EulerSolver<double> solver(nx, dx, xmin, gamma, cfl, t_end, flux);
        setup_ic(solver.grid_view(), test, gamma);
        solver.run();

        // Extract numerical solution and compute exact solution
        std::vector<double> num_rho(nx), num_u(nx), num_p(nx);
        std::vector<double> ext_rho(nx), ext_u(nx), ext_p(nx);

        auto gv = solver.grid_view();
        for (int i = 0; i < nx; ++i) {
            Vec<double, EulerNVars> cons;
            for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, 0, v);
            Vec<double, EulerNVars> prim = cons_to_prim(cons, gamma);
            num_rho[i] = prim[PRHO];
            num_u[i]   = prim[VX];
            num_p[i]   = prim[PRES];

            double x = xmin + (i + 0.5) * dx;
            double xi = (x - x0) / t_end;
            double erho, eu, ep;
            exact_riemann_sample(gamma, xi,
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
    double gamma = cfg.get_double("gamma", 1.4);
    double cfl   = cfg.get_double("cfl", 0.8);
    double t_end = cfg.get_double("t_end", 0.25);
    int    out_prec = cfg.get_int("output_precision", 17);
    if (out_prec < 1 || out_prec > 17) {
        throw std::runtime_error(
            "output_precision must be in [1, 17] (got " + std::to_string(out_prec) + ")");
    }
    FluxScheme flux = parse_flux(cfg);

    double dx = (xmax - xmin) / nx;

    if (ny > 1) {
        // ── 2D path ───────────────────────────────────────────────────────────
        double dy = (ymax - ymin) / ny;
        EulerSolver<double> solver(nx, ny, dx, dy, xmin, ymin,
                                   gamma, cfl, t_end, flux);
        setup_ic(solver.grid_view(), test, gamma);
        solver.run();

        std::cerr << "Finished: " << solver.step_count() << " steps, t = "
                  << solver.time() << "\n";

        auto gv = solver.grid_view();
        std::cout << std::setprecision(out_prec);
        // Gnuplot-friendly: one line per (i, j), blank line between j-blocks.
        for (int j = 0; j < ny; ++j) {
            double y = ymin + (j + 0.5) * dy;
            for (int i = 0; i < nx; ++i) {
                double x = xmin + (i + 0.5) * dx;
                Vec<double, EulerNVars> cons;
                for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);
                Vec<double, EulerNVars> prim = cons_to_prim(cons, gamma);

                std::cout << x          << "\t"
                          << y          << "\t"
                          << prim[PRHO] << "\t"
                          << prim[VX]   << "\t"
                          << prim[VY]   << "\t"
                          << prim[PRES] << "\n";
            }
            std::cout << "\n";
        }
        return;
    }

    // ── 1D path (preserve bit-identical legacy output format) ─────────────────
    EulerSolver<double> solver(nx, dx, xmin, gamma, cfl, t_end, flux);
    setup_ic(solver.grid_view(), test, gamma);
    solver.run();

    std::cerr << "Finished: " << solver.step_count() << " steps, t = "
              << solver.time() << "\n";

    auto gv = solver.grid_view();
    std::cout << std::setprecision(out_prec);
    for (int i = 0; i < nx; ++i) {
        double x = xmin + (i + 0.5) * dx;
        Vec<double, EulerNVars> cons;
        for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, 0, v);
        Vec<double, EulerNVars> prim = cons_to_prim(cons, gamma);

        std::cout << x          << "\t"
                  << prim[PRHO] << "\t"
                  << prim[VX]   << "\t"
                  << prim[VY]   << "\t"
                  << prim[PRES] << "\n";
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: hrsc <config_file>\n";
        return 1;
    }

    Config cfg(argv[1]);
    std::string mode = cfg.get_string("mode", "normal");

    if (mode == "convergence") {
        run_convergence(cfg);
    } else {
        run_normal(cfg);
    }

    return 0;
}
