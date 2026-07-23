#include "catch.hpp"
#include "utils/config.hpp"

#include <sstream>

using namespace hrsc;

TEST_CASE("Config parses basic key=value pairs", "[config]") {
    std::istringstream is(
        "nx = 200\n"
        "ny = 1\n"
        "gamma = 1.4\n"
        "name = sod_test\n"
    );
    Config cfg(is);

    REQUIRE(cfg.get_int("nx") == 200);
    REQUIRE(cfg.get_int("ny") == 1);
    REQUIRE(cfg.get_double("gamma") == Approx(1.4));
    REQUIRE(cfg.get_string("name") == "sod_test");
}

TEST_CASE("Config returns defaults for missing keys", "[config]") {
    std::istringstream is("nx = 100\n");
    Config cfg(is);

    REQUIRE(cfg.get_int("missing_key", 42) == 42);
    REQUIRE(cfg.get_double("missing_key", 3.14) == Approx(3.14));
    REQUIRE(cfg.get_string("missing_key", "default") == "default");
    REQUIRE(cfg.get_bool("missing_key", true) == true);
}

TEST_CASE("Config retains the presence of keys with empty values", "[config]") {
    std::istringstream is("output_times =   \n");
    Config cfg(is);

    REQUIRE_FALSE(cfg.contains("missing_key"));
    REQUIRE(cfg.contains("output_times"));
    REQUIRE(cfg.get_string("output_times").empty());
}

TEST_CASE("Config skips comments and blank lines", "[config]") {
    std::istringstream is(
        "# This is a comment\n"
        "\n"
        "   \n"
        "nx = 50\n"
        "# Another comment\n"
        "ny = 10\n"
    );
    Config cfg(is);

    REQUIRE(cfg.get_int("nx") == 50);
    REQUIRE(cfg.get_int("ny") == 10);
}

TEST_CASE("Config handles whitespace around = sign", "[config]") {
    std::istringstream is(
        "key1=value1\n"
        "key2 =value2\n"
        "key3= value3\n"
        "key4  =  value4\n"
        "  key5  =  value5  \n"
    );
    Config cfg(is);

    REQUIRE(cfg.get_string("key1") == "value1");
    REQUIRE(cfg.get_string("key2") == "value2");
    REQUIRE(cfg.get_string("key3") == "value3");
    REQUIRE(cfg.get_string("key4") == "value4");
    REQUIRE(cfg.get_string("key5") == "value5");
}

TEST_CASE("Config get_bool accepts true/false/1/0", "[config]") {
    std::istringstream is(
        "a = true\n"
        "b = false\n"
        "c = 1\n"
        "d = 0\n"
    );
    Config cfg(is);

    REQUIRE(cfg.get_bool("a") == true);
    REQUIRE(cfg.get_bool("b") == false);
    REQUIRE(cfg.get_bool("c") == true);
    REQUIRE(cfg.get_bool("d") == false);
}

TEST_CASE("Config get_bool throws on invalid value", "[config]") {
    std::istringstream is("flag = maybe\n");
    Config cfg(is);

    REQUIRE_THROWS_AS(cfg.get_bool("flag"), std::runtime_error);
    REQUIRE_THROWS_WITH(cfg.get_bool("flag"), Catch::Contains("flag"));
}

TEST_CASE("Config get_int throws on non-numeric value", "[config]") {
    std::istringstream is("count = abc\n");
    Config cfg(is);

    REQUIRE_THROWS_AS(cfg.get_int("count"), std::runtime_error);
    REQUIRE_THROWS_WITH(cfg.get_int("count"), Catch::Contains("count"));
}

TEST_CASE("Config get_double throws on non-numeric value", "[config]") {
    std::istringstream is("ratio = not_a_number\n");
    Config cfg(is);

    REQUIRE_THROWS_AS(cfg.get_double("ratio"), std::runtime_error);
    REQUIRE_THROWS_WITH(cfg.get_double("ratio"), Catch::Contains("ratio"));
}

TEST_CASE("Config splits on first = only", "[config]") {
    std::istringstream is("expr = a=b=c\n");
    Config cfg(is);

    REQUIRE(cfg.get_string("expr") == "a=b=c");
}

TEST_CASE("Config skips lines without =", "[config]") {
    std::istringstream is(
        "valid = yes\n"
        "no_equals_here\n"
        "also_valid = ok\n"
    );
    Config cfg(is);

    REQUIRE(cfg.get_string("valid") == "yes");
    REQUIRE(cfg.get_string("also_valid") == "ok");
}
