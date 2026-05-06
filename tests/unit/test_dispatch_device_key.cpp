#include "catch.hpp"
#include "utils/config.hpp"
#include <stdexcept>

using namespace hrsc;

TEST_CASE("device cfg key defaults to cpu when absent", "[dispatch]") {
    Config cfg;
    REQUIRE(cfg.get_string("device", "cpu") == "cpu");
}

TEST_CASE("device cfg key accepts cpu and gpu", "[dispatch]") {
    Config cfg;
    cfg.set("device", "gpu");
    REQUIRE(cfg.get_string("device", "cpu") == "gpu");
    cfg.set("device", "cpu");
    REQUIRE(cfg.get_string("device", "cpu") == "cpu");
}
