#include "utils/config.hpp"
#include "core/eos.hpp"
#include "euler/euler_solver.hpp"
#include "toro_tests.hpp"

#include <iostream>
#include <iomanip>
#include <string>
#include <stdexcept>

using namespace hrsc;

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: hrsc <config_file>\n";
        return 1;
    }

    Config cfg(argv[1]);

    std::string test = cfg.get_string("test");
    int    nx    = cfg.get_int("nx", 200);
    double xmin  = cfg.get_double("xmin", 0.0);
    double xmax  = cfg.get_double("xmax", 1.0);
    double gamma = cfg.get_double("gamma", 1.4);
    double cfl   = cfg.get_double("cfl", 0.8);
    double t_end = cfg.get_double("t_end", 0.25);

    double dx = (xmax - xmin) / nx;

    EulerSolver<double> solver(nx, dx, gamma, cfl, t_end);

    // Set initial conditions
    if (test == "sod") {
        setup_sod(solver.grid_view(), gamma);
    } else if (test == "toro2") {
        setup_toro2(solver.grid_view(), gamma);
    } else if (test == "toro3") {
        setup_toro3(solver.grid_view(), gamma);
    } else if (test == "toro4") {
        setup_toro4(solver.grid_view(), gamma);
    } else if (test == "toro5") {
        setup_toro5(solver.grid_view(), gamma);
    } else {
        throw std::runtime_error("Unknown test: " + test);
    }

    // Run solver
    solver.run();

    std::cerr << "Finished: " << solver.step_count() << " steps, t = "
              << solver.time() << "\n";

    // Output: x  rho  u  v  p  (one cell per line)
    auto gv = solver.grid_view();
    std::cout << std::setprecision(17);
    for (int i = 0; i < nx; ++i) {
        double x = xmin + (i + 0.5) * dx;
        Vec<double, 4> cons;
        for (int v = 0; v < 4; ++v) cons[v] = gv(i, 0, v);
        Vec<double, 4> prim = cons_to_prim(cons, gamma);

        std::cout << x          << "\t"
                  << prim[PRHO] << "\t"
                  << prim[VX]   << "\t"
                  << prim[VY]   << "\t"
                  << prim[PRES] << "\n";
    }

    return 0;
}
