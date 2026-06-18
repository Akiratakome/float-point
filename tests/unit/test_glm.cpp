#include "catch.hpp"
#include "core/grid.hpp"
#include "mhd/glm.hpp"
#include "mhd/mhd_state.hpp"

#include <cmath>

using namespace hrsc;

TEST_CASE("glm_damp decays psi by exp(-dt*ch^2/cp^2), cp^2=ch*cr", "[mhd][glm]") {
    Grid2D<double, MhdNVars> grid(4, 1);
    auto v = grid.view();

    for (int i = 0; i < 4; ++i) {
        v(i, 0, MhdIdx::PSI) = 2.0;
    }

    const double ch = 3.0;
    const double cr = 0.18;
    const double dt = 0.01;
    glm_damp<double>(v, 4, 1, ch, cr, dt);

    const double expected = 2.0 * std::exp(-dt * ch * ch / (ch * cr));
    for (int i = 0; i < 4; ++i) {
        REQUIRE(v(i, 0, MhdIdx::PSI) == Approx(expected));
    }
}

TEST_CASE("glm_damp is a no-op when cr<=0", "[mhd][glm]") {
    Grid2D<double, MhdNVars> grid(2, 1);
    auto v = grid.view();
    v(0, 0, MhdIdx::PSI) = 1.0;
    v(1, 0, MhdIdx::PSI) = -1.0;

    glm_damp<double>(v, 2, 1, /*ch=*/2.0, /*cr=*/0.0, /*dt=*/0.1);

    REQUIRE(v(0, 0, MhdIdx::PSI) == Approx(1.0));
    REQUIRE(v(1, 0, MhdIdx::PSI) == Approx(-1.0));
}

TEST_CASE("glm_damp is a no-op when ch<=0", "[mhd][glm]") {
    Grid2D<double, MhdNVars> grid(2, 1);
    auto v = grid.view();
    v(0, 0, MhdIdx::PSI) = 1.0;
    v(1, 0, MhdIdx::PSI) = -1.0;

    glm_damp<double>(v, 2, 1, /*ch=*/0.0, /*cr=*/0.18, /*dt=*/0.1);

    REQUIRE(v(0, 0, MhdIdx::PSI) == Approx(1.0));
    REQUIRE(v(1, 0, MhdIdx::PSI) == Approx(-1.0));
}
