#include "catch.hpp"
#include "core/eos.hpp"

#include <cmath>

using namespace hrsc;

template <typename Real>
constexpr Real eps() {
    return std::is_same<Real, float>::value ? Real(1e-5) : Real(1e-12);
}

TEST_CASE("EOS pressure from Sod left state", "[eos]") {
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5};
    double p = pressure(cons, 1.4);
    REQUIRE(p == Approx(1.0).epsilon(1e-12));
}

TEST_CASE("EOS pressure from Sod right state", "[eos]") {
    Vec<double, 4> cons = {0.125, 0.0, 0.0, 0.25};
    double p = pressure(cons, 1.4);
    REQUIRE(p == Approx(0.1).epsilon(1e-12));
}

TEST_CASE("EOS pressure with nonzero velocity", "[eos]") {
    Vec<double, 4> cons = {2.0, 6.0, 8.0, 50.0};
    double p = pressure(cons, 1.4);
    REQUIRE(p == Approx(10.0).epsilon(1e-12));
}

TEST_CASE("EOS sound speed from Sod left state", "[eos]") {
    double a = sound_speed(1.0, 1.0, 1.4);
    REQUIRE(a == Approx(std::sqrt(1.4)).epsilon(1e-12));
}

TEST_CASE("EOS sound speed from Sod right state", "[eos]") {
    double a = sound_speed(0.125, 0.1, 1.4);
    REQUIRE(a == Approx(std::sqrt(1.12)).epsilon(1e-12));
}

TEST_CASE("EOS prim_to_cons and cons_to_prim round-trip", "[eos]") {
    Vec<double, 4> prim = {1.0, 0.75, -0.5, 1.0};
    double gamma = 1.4;
    auto cons = prim_to_cons(prim, gamma);
    auto recovered = cons_to_prim(cons, gamma);
    REQUIRE(recovered[0] == Approx(prim[0]).epsilon(1e-12));
    REQUIRE(recovered[1] == Approx(prim[1]).epsilon(1e-12));
    REQUIRE(recovered[2] == Approx(prim[2]).epsilon(1e-12));
    REQUIRE(recovered[3] == Approx(prim[3]).epsilon(1e-12));
}

TEST_CASE("EOS round-trip with high velocity", "[eos]") {
    Vec<double, 4> prim = {0.5, 100.0, -200.0, 50.0};
    double gamma = 1.4;
    auto cons = prim_to_cons(prim, gamma);
    auto recovered = cons_to_prim(cons, gamma);
    REQUIRE(recovered[0] == Approx(prim[0]).epsilon(1e-10));
    REQUIRE(recovered[1] == Approx(prim[1]).epsilon(1e-10));
    REQUIRE(recovered[2] == Approx(prim[2]).epsilon(1e-10));
    REQUIRE(recovered[3] == Approx(prim[3]).epsilon(1e-10));
}

TEST_CASE("EOS zero velocity gives zero kinetic energy", "[eos]") {
    Vec<double, 4> prim = {1.0, 0.0, 0.0, 1.0};
    auto cons = prim_to_cons(prim, 1.4);
    REQUIRE(cons[0] == Approx(1.0));
    REQUIRE(cons[1] == Approx(0.0));
    REQUIRE(cons[2] == Approx(0.0));
    REQUIRE(cons[3] == Approx(2.5));
}

TEST_CASE("EOS prim_to_cons conserved variable values", "[eos]") {
    Vec<double, 4> prim = {2.0, 3.0, 4.0, 10.0};
    auto cons = prim_to_cons(prim, 1.4);
    REQUIRE(cons[0] == Approx(2.0));
    REQUIRE(cons[1] == Approx(6.0));
    REQUIRE(cons[2] == Approx(8.0));
    REQUIRE(cons[3] == Approx(50.0));
}

TEMPLATE_TEST_CASE("EOS round-trip is precision-aware", "[eos][template]", float, double) {
    using Real = TestType;
    Vec<Real, 4> prim = {Real(1.0), Real(0.5), Real(-0.3), Real(2.0)};
    Real gamma = Real(1.4);
    auto cons = prim_to_cons(prim, gamma);
    auto recovered = cons_to_prim(cons, gamma);
    REQUIRE(recovered[0] == Approx(prim[0]).epsilon(eps<Real>()));
    REQUIRE(recovered[1] == Approx(prim[1]).epsilon(eps<Real>()));
    REQUIRE(recovered[2] == Approx(prim[2]).epsilon(eps<Real>()));
    REQUIRE(recovered[3] == Approx(prim[3]).epsilon(eps<Real>()));
}

TEST_CASE("PrimVar enum accesses cons_to_prim output correctly", "[eos]") {
    // Sod left state: rho=1, u=0, v=0, p=1 → cons = {1, 0, 0, 2.5}
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5};
    Vec<double, 4> prim = cons_to_prim(cons, 1.4);

    REQUIRE(prim[PrimVar::PRHO] == Approx(1.0));
    REQUIRE(prim[PrimVar::VX]   == Approx(0.0));
    REQUIRE(prim[PrimVar::VY]   == Approx(0.0));
    REQUIRE(prim[PrimVar::PRES] == Approx(1.0));
}
