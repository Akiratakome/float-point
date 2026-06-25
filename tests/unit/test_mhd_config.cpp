#include "catch.hpp"
#include "mhd/mhd_config.hpp"

#include <stdexcept>

using namespace hrsc;

TEST_CASE("MHD cfg parser accepts supported test cases and outflow boundary", "[mhd][config]") {
    REQUIRE(parse_mhd_test("brio_wu") == MhdTestCase::BrioWu);
    REQUIRE(parse_mhd_test("orszag_tang") == MhdTestCase::OrszagTang);
    REQUIRE(parse_mhd_test("kelvin_helmholtz") == MhdTestCase::KelvinHelmholtz);
    REQUIRE(parse_mhd_boundary("outflow") == BoundaryType::Outflow);
}

TEST_CASE("MHD cfg parser rejects unsupported tests and boundary conditions", "[mhd][config]") {
    REQUIRE_THROWS_AS(parse_mhd_test("unsupported_case"), std::invalid_argument);
    REQUIRE_THROWS_AS(parse_mhd_boundary("reflective"), std::invalid_argument);
}

TEST_CASE("parse_mhd_boundary accepts periodic", "[mhd][config]") {
    REQUIRE(parse_mhd_boundary("periodic") == BoundaryType::Periodic);
    REQUIRE(parse_mhd_boundary("outflow")  == BoundaryType::Outflow);
}

TEST_CASE("parse_mhd_test accepts divb_blob", "[mhd][config]") {
    REQUIRE(parse_mhd_test("divb_blob") == MhdTestCase::DivbBlob);
}

TEST_CASE("parse_mhd_riemann accepts supported solvers", "[mhd][config]") {
    REQUIRE(parse_mhd_riemann("hll") == MhdRiemann::Hll);
    REQUIRE(parse_mhd_riemann("hlld") == MhdRiemann::Hlld);
}

TEST_CASE("parse_mhd_riemann rejects unsupported solvers with value", "[mhd][config]") {
    bool caught = false;
    try {
        (void)parse_mhd_riemann("roe");
    } catch (const std::invalid_argument& e) {
        caught = true;
        REQUIRE(std::string(e.what()) == "unsupported MHD Riemann solver: roe");
    }
    REQUIRE(caught);
}
