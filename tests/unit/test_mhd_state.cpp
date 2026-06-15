#include "catch.hpp"
#include "mhd/mhd_state.hpp"

using namespace hrsc;

TEST_CASE("MHD cons<->prim round-trips", "[mhd][state]") {
    const double gamma = 2.0;
    MhdPrim<double> w;
    w.rho = 1.3; w.vx = 0.4; w.vy = -0.2; w.vz = 0.1;
    w.Bx = 0.75; w.By = 0.9; w.Bz = -0.3; w.p = 1.1; w.psi = 0.0;

    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);
    MhdPrim<double> w2 = cons_to_prim(U, gamma);

    REQUIRE(w2.rho == Approx(w.rho));
    REQUIRE(w2.vx  == Approx(w.vx));
    REQUIRE(w2.vy  == Approx(w.vy));
    REQUIRE(w2.vz  == Approx(w.vz));
    REQUIRE(w2.Bx  == Approx(w.Bx));
    REQUIRE(w2.By  == Approx(w.By));
    REQUIRE(w2.Bz  == Approx(w.Bz));
    REQUIRE(w2.p   == Approx(w.p));
    REQUIRE(w2.psi == Approx(w.psi));
}

TEST_CASE("MHD pressure subtracts kinetic and magnetic energy", "[mhd][state]") {
    const double gamma = 2.0;
    MhdPrim<double> w{};
    w.rho = 2.0; w.vx = 1.0; w.By = 2.0; w.p = 3.0;
    Vec<double, MhdNVars> U = prim_to_cons(w, gamma);
    // E = p/(g-1) + 0.5*rho*v^2 + 0.5*B^2 = 3 + 1 + 2 = 6
    REQUIRE(U[MhdIdx::E] == Approx(6.0));
    REQUIRE(pressure(U, gamma) == Approx(3.0));
}

TEST_CASE("MHD fast speed reduces to sound speed without magnetic field", "[mhd][state]") {
    const double gamma = 1.4;
    MhdPrim<double> w{};
    w.rho = 2.0;
    w.p = 8.0;

    REQUIRE(fast_speed_x(w, gamma) == Approx(std::sqrt(gamma * w.p / w.rho)));
}

TEST_CASE("MHD fast speed includes transverse magnetic pressure", "[mhd][state]") {
    const double gamma = 2.0;
    MhdPrim<double> w{};
    w.rho = 4.0;
    w.By = 3.0;
    w.p = 2.0;

    const double a2 = gamma * w.p / w.rho;
    const double ca2 = (w.By * w.By) / w.rho;

    REQUIRE(fast_speed_x(w, gamma) == Approx(std::sqrt(a2 + ca2)));
}
