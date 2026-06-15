#include "catch.hpp"
#include "app/output.hpp"

#include <filesystem>

using namespace hrsc::app;

TEST_CASE("checkpoint_output_file preserves parent and extension", "[app][output]") {
    REQUIRE(checkpoint_output_file("grid.bin", 0) == "grid_t0000.bin");

    std::filesystem::path checkpoint =
        checkpoint_output_file("runs/lw3/grid.bin", 12);
    REQUIRE(checkpoint.filename().string() == "grid_t0012.bin");
    REQUIRE(checkpoint.parent_path().generic_string() == "runs/lw3");
}
