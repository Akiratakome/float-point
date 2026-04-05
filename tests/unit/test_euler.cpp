#include "catch.hpp"
#include "euler/euler_flux.hpp"
#include "euler/muscl.hpp"
#include "core/grid.hpp"

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

// --- minmod tests ---

TEST_CASE("minmod: same sign values", "[muscl]") {
    REQUIRE(minmod(2.0, 3.0) == Approx(2.0));
    REQUIRE(minmod(3.0, 2.0) == Approx(2.0));
    REQUIRE(minmod(-2.0, -3.0) == Approx(-2.0));
}

TEST_CASE("minmod: opposite signs returns zero", "[muscl]") {
    REQUIRE(minmod(2.0, -1.0) == Approx(0.0));
    REQUIRE(minmod(-2.0, 1.0) == Approx(0.0));
}

TEST_CASE("minmod: one zero returns zero", "[muscl]") {
    REQUIRE(minmod(0.0, 3.0) == Approx(0.0));
    REQUIRE(minmod(3.0, 0.0) == Approx(0.0));
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
    // minmod(0.1, 0.1) = 0.1
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

    // Cell 4: backward = 1-1=0, forward = 2-1=1 → minmod(0,1)=0
    Vec<double, 4> qL4{}, qR4{};
    muscl_reconstruct_x(grid.view(), 4, 0, qL4, qR4);
    REQUIRE(qL4[RHO] == Approx(1.0).epsilon(1e-12));
    REQUIRE(qR4[RHO] == Approx(1.0).epsilon(1e-12));

    // Cell 5: backward = 2-1=1, forward = 2-2=0 → minmod(1,0)=0
    Vec<double, 4> qL5{}, qR5{};
    muscl_reconstruct_x(grid.view(), 5, 0, qL5, qR5);
    REQUIRE(qL5[RHO] == Approx(2.0).epsilon(1e-12));
    REQUIRE(qR5[RHO] == Approx(2.0).epsilon(1e-12));
}
