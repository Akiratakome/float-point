#include "catch.hpp"
#include "mhd/mhd_config.hpp"

#include <stdexcept>

using namespace hrsc;

TEST_CASE("MHD cfg parser accepts only the Week 12 Brio-Wu outflow case", "[mhd][config]") {
    REQUIRE(parse_mhd_test("brio_wu") == MhdTestCase::BrioWu);
    REQUIRE(parse_mhd_boundary("outflow") == BoundaryType::Outflow);
}

TEST_CASE("MHD cfg parser rejects unsupported tests and boundary conditions", "[mhd][config]") {
    REQUIRE_THROWS_AS(parse_mhd_test("orszag_tang"), std::invalid_argument);
    REQUIRE_THROWS_AS(parse_mhd_boundary("periodic"), std::invalid_argument);
    REQUIRE_THROWS_AS(parse_mhd_boundary("reflective"), std::invalid_argument);
}
