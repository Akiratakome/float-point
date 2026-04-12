#include "catch.hpp"
#include "euler/euler_flux.hpp"
#include "euler/muscl.hpp"
#include "euler/hancock.hpp"
#include "euler/hllc.hpp"
#include "euler/euler_solver.hpp"
#include "euler/exact_riemann.hpp"
#include "core/grid.hpp"
#include "core/boundary.hpp"
#include "toro_tests.hpp"

using namespace hrsc;

// --- euler_flux_x tests ---

TEST_CASE("euler_flux_x: stationary gas returns {0, p, 0, 0}", "[flux]") {
    // rho=1, u=0, v=0, p=1 → cons = {1, 0, 0, 2.5}
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5};
    Vec<double, 4> f = euler_flux_x(cons, 1.4);

    REQUIRE(f[0] == Approx(0.0).margin(1e-15));  // rho*u = 0
    REQUIRE(f[1] == Approx(1.0).epsilon(1e-12));  // rho*u^2 + p = p = 1
    REQUIRE(f[2] == Approx(0.0).margin(1e-15));  // rho*u*v = 0
    REQUIRE(f[3] == Approx(0.0).margin(1e-15));  // u*(E+p) = 0
}

TEST_CASE("euler_flux_x: uniform rightward flow", "[flux]") {
    // rho=2, u=3, v=1, p=4, gamma=1.4
    // cons: rho=2, rho*u=6, rho*v=2, E = p/(gamma-1) + 0.5*rho*(u^2+v^2)
    //     = 4/0.4 + 0.5*2*(9+1) = 10 + 10 = 20
    Vec<double, 4> cons = {2.0, 6.0, 2.0, 20.0};
    Vec<double, 4> f = euler_flux_x(cons, 1.4);

    // F = {rho*u, rho*u^2+p, rho*u*v, u*(E+p)}
    //   = {6, 2*9+4, 6*1, 3*(20+4)} = {6, 22, 6, 72}
    REQUIRE(f[0] == Approx(6.0).epsilon(1e-12));
    REQUIRE(f[1] == Approx(22.0).epsilon(1e-12));
    REQUIRE(f[2] == Approx(6.0).epsilon(1e-12));
    REQUIRE(f[3] == Approx(72.0).epsilon(1e-12));
}

// --- minbee tests ---

TEST_CASE("minbee: same sign values", "[limiter]") {
    REQUIRE(minbee(2.0, 3.0) == Approx(2.0));
    REQUIRE(minbee(3.0, 2.0) == Approx(2.0));
    REQUIRE(minbee(-2.0, -3.0) == Approx(-2.0));
}

TEST_CASE("minbee: opposite signs returns zero", "[limiter]") {
    REQUIRE(minbee(2.0, -1.0) == Approx(0.0));
    REQUIRE(minbee(-2.0, 1.0) == Approx(0.0));
}

TEST_CASE("minbee: one zero returns zero", "[limiter]") {
    REQUIRE(minbee(0.0, 3.0) == Approx(0.0));
    REQUIRE(minbee(3.0, 0.0) == Approx(0.0));
}

// --- vanleer tests ---

TEST_CASE("vanleer: same sign values", "[limiter]") {
    REQUIRE(vanleer(2.0, 3.0) == Approx(2.4));       // 2*2*3/(2+3) = 2.4
    REQUIRE(vanleer(-2.0, -3.0) == Approx(-2.4));
}

TEST_CASE("vanleer: opposite signs returns zero", "[limiter]") {
    REQUIRE(vanleer(2.0, -1.0) == Approx(0.0));
}

TEST_CASE("vanleer: equal values recover gradient", "[limiter]") {
    REQUIRE(vanleer(1.5, 1.5) == Approx(1.5));       // 2*1.5*1.5/(1.5+1.5) = 1.5
    REQUIRE(vanleer(-0.7, -0.7) == Approx(-0.7));
}

// --- superbee tests ---

TEST_CASE("superbee: same sign values", "[limiter]") {
    // superbee(2,3) = max(min(2, 6), min(4, 3)) = max(2, 3) = 3
    REQUIRE(superbee(2.0, 3.0) == Approx(3.0));
    REQUIRE(superbee(-2.0, -3.0) == Approx(-3.0));
}

TEST_CASE("superbee: opposite signs returns zero", "[limiter]") {
    REQUIRE(superbee(2.0, -1.0) == Approx(0.0));
}

TEST_CASE("superbee: returns larger slope than minbee", "[limiter]") {
    double a = 1.0, b = 2.0;
    REQUIRE(std::abs(superbee(a, b)) >= std::abs(minbee(a, b)));
}

// --- vanalbada tests ---

TEST_CASE("vanalbada: same sign values", "[limiter]") {
    // vanalbada(2,3) = 2*3*(2+3)/(4+9) = 30/13 ≈ 2.3077
    REQUIRE(vanalbada(2.0, 3.0) == Approx(30.0 / 13.0).epsilon(1e-12));
}

TEST_CASE("vanalbada: opposite signs returns zero", "[limiter]") {
    REQUIRE(vanalbada(2.0, -1.0) == Approx(0.0));
}

TEST_CASE("vanalbada: equal values recover gradient", "[limiter]") {
    // vanalbada(a,a) = a*a*(2a)/(2a^2) = a
    REQUIRE(vanalbada(1.5, 1.5) == Approx(1.5));
}

// --- muscl_reconstruct_x tests ---

TEST_CASE("muscl_reconstruct_x: uniform field gives no reconstruction", "[muscl]") {
    // 10-cell 1D grid, uniform rho=1, u=0, v=0, p=1 → cons={1,0,0,2.5}
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int i = -2; i < 12; ++i) {
        gv(i, 0, RHO)  = 1.0;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = 2.5;
    }

    Vec<double, 4> qL{}, qR{};
    muscl_reconstruct_x(grid.view(), 5, 0, qL, qR);

    // Uniform field: left face == right face == cell value
    for (int v = 0; v < 4; ++v) {
        Vec<double, 4> cell = {1.0, 0.0, 0.0, 2.5};
        REQUIRE(qL[v] == Approx(cell[v]).margin(1e-15));
        REQUIRE(qR[v] == Approx(cell[v]).margin(1e-15));
    }
}

TEST_CASE("muscl_reconstruct_x: linear field recovers exact gradient", "[muscl]") {
    // 10-cell 1D grid, rho varies linearly: rho_i = 1 + 0.1*i
    // All other variables uniform
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int i = -2; i < 12; ++i) {
        gv(i, 0, RHO)  = 1.0 + 0.1 * i;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = 2.5;
    }

    Vec<double, 4> qL{}, qR{};
    muscl_reconstruct_x(grid.view(), 5, 0, qL, qR);

    // Cell 5 center value: rho = 1.5
    // backward diff: rho_5 - rho_4 = 0.1, forward diff: rho_6 - rho_5 = 0.1
    // minbee(0.1, 0.1) = 0.1
    // qL (left face) = 1.5 - 0.5 * 0.1 = 1.45
    // qR (right face) = 1.5 + 0.5 * 0.1 = 1.55
    REQUIRE(qL[RHO] == Approx(1.45).epsilon(1e-12));
    REQUIRE(qR[RHO] == Approx(1.55).epsilon(1e-12));
}

TEST_CASE("muscl_reconstruct_x: discontinuity triggers limiter", "[muscl]") {
    // 10-cell grid: cells 0-4 have rho=1, cells 5-9 have rho=2
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int i = -2; i < 12; ++i) {
        double rho = (i < 5) ? 1.0 : 2.0;
        gv(i, 0, RHO)  = rho;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = 2.5;
    }

    // Cell 4: backward = 1-1=0, forward = 2-1=1 → minbee(0,1)=0
    Vec<double, 4> qL4{}, qR4{};
    muscl_reconstruct_x(grid.view(), 4, 0, qL4, qR4);
    REQUIRE(qL4[RHO] == Approx(1.0).epsilon(1e-12));
    REQUIRE(qR4[RHO] == Approx(1.0).epsilon(1e-12));

    // Cell 5: backward = 2-1=1, forward = 2-2=0 → minbee(1,0)=0
    Vec<double, 4> qL5{}, qR5{};
    muscl_reconstruct_x(grid.view(), 5, 0, qL5, qR5);
    REQUIRE(qL5[RHO] == Approx(2.0).epsilon(1e-12));
    REQUIRE(qR5[RHO] == Approx(2.0).epsilon(1e-12));
}

TEST_CASE("muscl_reconstruct_x: van Leer on linear field", "[muscl]") {
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int i = -2; i < 12; ++i) {
        gv(i, 0, RHO)  = 1.0 + 0.1 * i;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = 2.5;
    }

    Vec<double, 4> qL{}, qR{};
    muscl_reconstruct_x(grid.view(), 5, 0, qL, qR, VanLeerLimiter{});

    // Cell 5: rho=1.5, backward=forward=0.1
    // vanleer(0.1, 0.1) = 0.1 (exact gradient recovery)
    REQUIRE(qL[RHO] == Approx(1.45).epsilon(1e-12));
    REQUIRE(qR[RHO] == Approx(1.55).epsilon(1e-12));
}

// --- muscl_hancock_x tests ---

TEST_CASE("muscl_hancock_x: uniform field unchanged after half-step", "[hancock]") {
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    // Uniform state: rho=1, u=0, v=0, p=1 → cons={1, 0, 0, 2.5}
    for (int i = -2; i < 12; ++i) {
        gv(i, 0, RHO)  = 1.0;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = 2.5;
    }

    Vec<double, 4> qL{}, qR{};
    muscl_hancock_x(grid.view(), 5, 0, 0.001, 1.4, qL, qR);

    // Uniform → slope=0 → q_left=q_right=cell value → F(qL)=F(qR) → no evolution
    REQUIRE(qL[RHO]  == Approx(1.0).epsilon(1e-12));
    REQUIRE(qL[RHOU] == Approx(0.0).margin(1e-15));
    REQUIRE(qL[RHOV] == Approx(0.0).margin(1e-15));
    REQUIRE(qL[EN]   == Approx(2.5).epsilon(1e-12));

    REQUIRE(qR[RHO]  == Approx(1.0).epsilon(1e-12));
    REQUIRE(qR[RHOU] == Approx(0.0).margin(1e-15));
    REQUIRE(qR[RHOV] == Approx(0.0).margin(1e-15));
    REQUIRE(qR[EN]   == Approx(2.5).epsilon(1e-12));
}

TEST_CASE("muscl_hancock_x: linear density field evolves symmetrically", "[hancock]") {
    Grid2D<double, 4> grid(10, 1);
    grid.dx = 0.1;
    grid.dy = 0.1;
    auto gv = grid.view();

    for (int i = -2; i < 12; ++i) {
        double rho = 1.0 + 0.1 * i;
        double p   = 1.0;
        double E   = p / 0.4;  // gamma-1 = 0.4, u=v=0
        gv(i, 0, RHO)  = rho;
        gv(i, 0, RHOU) = 0.0;
        gv(i, 0, RHOV) = 0.0;
        gv(i, 0, EN)   = E;
    }

    Vec<double, 4> qL{}, qR{};
    muscl_hancock_x(grid.view(), 5, 0, 0.001, 1.4, qL, qR);

    // With u=0, E is constant (p/(gamma-1)), pressure is constant.
    // F(qL) = {0, p, 0, 0} = F(qR) → no Hancock correction.
    // So the result is just the MUSCL reconstruction.
    // Cell 5: rho=1.5, slope=0.1
    REQUIRE(qL[RHO] == Approx(1.45).epsilon(1e-10));
    REQUIRE(qR[RHO] == Approx(1.55).epsilon(1e-10));
}

// --- hllc_flux tests ---

TEST_CASE("hllc_flux: identical states returns physical flux", "[hllc]") {
    // If qL == qR, any Riemann solver must return F(q)
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5}; // rho=1, u=0, v=0, p=1
    Vec<double, 4> f_hllc = hllc_flux(cons, cons, 1.4);
    Vec<double, 4> f_phys = euler_flux_x(cons, 1.4);

    for (int v = 0; v < 4; ++v) {
        REQUIRE(f_hllc[v] == Approx(f_phys[v]).margin(1e-14));
    }
}

TEST_CASE("hllc_flux: identical states with nonzero velocity", "[hllc]") {
    // rho=2, u=3, v=1, p=4 → cons = {2, 6, 2, 20}
    Vec<double, 4> cons = {2.0, 6.0, 2.0, 20.0};
    Vec<double, 4> f_hllc = hllc_flux(cons, cons, 1.4);
    Vec<double, 4> f_phys = euler_flux_x(cons, 1.4);

    for (int v = 0; v < 4; ++v) {
        REQUIRE(f_hllc[v] == Approx(f_phys[v]).margin(1e-12));
    }
}

TEST_CASE("hllc_flux: Sod interface gives reasonable flux", "[hllc]") {
    // Left: rho=1, u=0, v=0, p=1 → cons={1, 0, 0, 2.5}
    // Right: rho=0.125, u=0, v=0, p=0.1 → cons={0.125, 0, 0, 0.25}
    Vec<double, 4> qL = {1.0, 0.0, 0.0, 2.5};
    Vec<double, 4> qR = {0.125, 0.0, 0.0, 0.25};
    Vec<double, 4> f = hllc_flux(qL, qR, 1.4);

    // The Sod shock tube has a right-going shock and contact.
    // At the interface, there should be a positive mass flux (flow goes right).
    REQUIRE(f[RHO] > 0.0);
    // Momentum flux should be positive (pressure pushes right)
    REQUIRE(f[RHOU] > 0.0);
}

// Symmetry test only valid with non-strict inequality (S_star=0 is an edge case
// where strict < excludes both star regions, falling through to FR).
#ifndef RIEMANN_STRICT_INEQUALITY
TEST_CASE("hllc_flux: symmetry test", "[hllc]") {
    // Symmetric states: qL = (rho=2, u=1, v=0.5, p=3), qR = (rho=2, u=-1, v=0.5, p=3)
    // By symmetry: mass flux should be zero, momentum flux = 2*p_star region
    double gamma = 1.4;
    Vec<double, 4> primL = {2.0, 1.0, 0.5, 3.0};
    Vec<double, 4> primR = {2.0, -1.0, 0.5, 3.0};
    Vec<double, 4> qL = prim_to_cons(primL, gamma);
    Vec<double, 4> qR = prim_to_cons(primR, gamma);

    Vec<double, 4> f = hllc_flux(qL, qR, gamma);

    // Mass flux = 0 by symmetry (u=-u)
    REQUIRE(f[RHO] == Approx(0.0).margin(1e-12));
    // Energy flux = 0 by symmetry
    REQUIRE(f[EN] == Approx(0.0).margin(1e-12));
}
#endif

// --- Sod IC test ---

TEST_CASE("setup_sod: left and right states set correctly", "[sod]") {
    Grid2D<double, 4> grid(200, 1);
    grid.dx = 1.0 / 200;
    grid.dy = 1.0;
    auto gv = grid.view();

    setup_sod(gv, 1.4);

    // Cell 10 is at x = (10+0.5)*0.005 = 0.0525 → left state
    REQUIRE(gv(10, 0, RHO)  == Approx(1.0));
    REQUIRE(gv(10, 0, RHOU) == Approx(0.0));
    REQUIRE(gv(10, 0, RHOV) == Approx(0.0));
    // E = p/(gamma-1) = 1.0/0.4 = 2.5
    REQUIRE(gv(10, 0, EN)   == Approx(2.5));

    // Cell 150 is at x = (150+0.5)*0.005 = 0.7525 → right state
    REQUIRE(gv(150, 0, RHO)  == Approx(0.125));
    REQUIRE(gv(150, 0, RHOU) == Approx(0.0));
    REQUIRE(gv(150, 0, RHOV) == Approx(0.0));
    // E = p/(gamma-1) = 0.1/0.4 = 0.25
    REQUIRE(gv(150, 0, EN)   == Approx(0.25));
}

// --- EulerSolver integration tests ---

TEST_CASE("EulerSolver: Sod density stays in physical range", "[solver]") {
    int nx = 200;
    double dx = 1.0 / nx;
    EulerSolver<double> solver(nx, dx, 1.4, 0.8, 0.25);

    setup_sod(solver.grid_view(), 1.4);
    solver.run();

    auto gv = solver.grid_view();
    for (int i = 0; i < nx; ++i) {
        double rho = gv(i, 0, RHO);
        REQUIRE(rho >= 0.1);
        REQUIRE(rho <= 1.1);
    }
}

TEST_CASE("EulerSolver: Sod mass is conserved", "[solver]") {
    int nx = 200;
    double dx = 1.0 / nx;
    EulerSolver<double> solver(nx, dx, 1.4, 0.8, 0.25);

    setup_sod(solver.grid_view(), 1.4);

    // Compute initial total mass
    double mass_init = 0.0;
    {
        auto gv = solver.grid_view();
        for (int i = 0; i < nx; ++i) {
            mass_init += gv(i, 0, RHO) * dx;
        }
    }

    solver.run();

    // Compute final total mass
    double mass_final = 0.0;
    {
        auto gv = solver.grid_view();
        for (int i = 0; i < nx; ++i) {
            mass_final += gv(i, 0, RHO) * dx;
        }
    }

    // Mass should be conserved to ~machine epsilon * nsteps
    // Outflow BCs can leak mass, so allow ~1% tolerance
    REQUIRE(mass_final == Approx(mass_init).epsilon(0.01));
}

TEST_CASE("EulerSolver: Sod shock position is approximately correct", "[solver]") {
    int nx = 200;
    double dx = 1.0 / nx;
    EulerSolver<double> solver(nx, dx, 1.4, 0.8, 0.25);

    setup_sod(solver.grid_view(), 1.4);
    solver.run();

    // Find the rightmost cell where density drops below 0.2
    // (the shock front). The right-going shock at t=0.25 is ~x=0.93.
    // Density behind shock ~0.265, ahead ~0.125; threshold 0.2 straddles the jump.
    auto gv = solver.grid_view();
    int shock_cell = -1;
    for (int i = nx - 1; i >= 0; --i) {
        if (gv(i, 0, RHO) > 0.2) {
            shock_cell = i;
            break;
        }
    }

    double shock_x = (shock_cell + 0.5) * dx;
    REQUIRE(shock_x > 0.75);
    REQUIRE(shock_x < 0.95);
}

// --- exact_riemann_solve tests ---

TEST_CASE("exact_riemann_solve: Sod p_star and u_star", "[exact]") {
    double gamma = 1.4;
    double p_star = 0.0, u_star = 0.0;

    exact_riemann_solve(gamma,
        1.0, 0.0, 1.0,      // rhoL, uL, pL
        0.125, 0.0, 0.1,    // rhoR, uR, pR
        p_star, u_star);

    REQUIRE(p_star == Approx(0.30313).epsilon(1e-4));
    REQUIRE(u_star == Approx(0.92745).epsilon(1e-4));
}

TEST_CASE("exact_riemann_solve: Toro Test 2 (123 problem)", "[exact]") {
    double gamma = 1.4;
    double p_star = 0.0, u_star = 0.0;
    exact_riemann_solve(gamma,
        1.0, -2.0, 0.4,
        1.0,  2.0, 0.4,
        p_star, u_star);
    REQUIRE(p_star == Approx(0.00189).epsilon(1e-2));
    REQUIRE(u_star == Approx(0.0).margin(1e-6));
}

TEST_CASE("exact_riemann_solve: Toro Test 3 (blast wave)", "[exact]") {
    double gamma = 1.4;
    double p_star = 0.0, u_star = 0.0;
    exact_riemann_solve(gamma,
        1.0, 0.0, 1000.0,
        1.0, 0.0, 0.01,
        p_star, u_star);
    REQUIRE(p_star == Approx(460.894).epsilon(1e-3));
    REQUIRE(u_star == Approx(19.5975).epsilon(1e-3));
}

TEST_CASE("exact_riemann_solve: Toro Test 4 (Lax)", "[exact]") {
    double gamma = 1.4;
    double p_star = 0.0, u_star = 0.0;
    exact_riemann_solve(gamma,
        0.445, 0.698, 3.528,
        0.5,   0.0,   0.571,
        p_star, u_star);
    // Converged exact values for Lax IC (Toro Table 4.1)
    REQUIRE(p_star == Approx(2.46610).epsilon(1e-4));
    REQUIRE(u_star == Approx(1.52872).epsilon(1e-4));
}

TEST_CASE("exact_riemann_solve: vacuum check", "[exact]") {
    double gamma = 1.4;
    double p_star = -1.0, u_star = -1.0;
    // Two flows diverging fast enough to generate vacuum
    exact_riemann_solve(gamma,
        1.0, -100.0, 0.4,
        1.0,  100.0, 0.4,
        p_star, u_star);
    REQUIRE(p_star == Approx(0.0).margin(1e-12));
    REQUIRE(u_star == Approx(0.0).margin(1e-6));
}
