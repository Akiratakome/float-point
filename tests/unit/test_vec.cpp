#include "catch.hpp"
#include "core/vec.hpp"

using namespace hrsc;

// Helper: precision-aware epsilon
template <typename Real>
constexpr Real eps() {
    return std::is_same<Real, float>::value ? Real(1e-6) : Real(1e-12);
}

TEST_CASE("Vec aggregate initialization", "[vec]") {
    Vec<double, 3> v = {1.0, 2.0, 3.0};
    REQUIRE(v[0] == Approx(1.0));
    REQUIRE(v[1] == Approx(2.0));
    REQUIRE(v[2] == Approx(3.0));
}

TEST_CASE("Vec zero initialization", "[vec]") {
    Vec<double, 4> v = {0.0, 0.0, 0.0, 0.0};
    for (int i = 0; i < 4; ++i) {
        REQUIRE(v[i] == Approx(0.0));
    }
}

TEST_CASE("Vec addition", "[vec]") {
    Vec<double, 3> a = {1.0, 2.0, 3.0};
    Vec<double, 3> b = {4.0, 5.0, 6.0};
    auto c = a + b;
    REQUIRE(c[0] == Approx(5.0));
    REQUIRE(c[1] == Approx(7.0));
    REQUIRE(c[2] == Approx(9.0));
}

TEST_CASE("Vec subtraction", "[vec]") {
    Vec<double, 3> a = {4.0, 5.0, 6.0};
    Vec<double, 3> b = {1.0, 2.0, 3.0};
    auto c = a - b;
    REQUIRE(c[0] == Approx(3.0));
    REQUIRE(c[1] == Approx(3.0));
    REQUIRE(c[2] == Approx(3.0));
}

TEST_CASE("Vec element-wise multiplication", "[vec]") {
    Vec<double, 3> a = {2.0, 3.0, 4.0};
    Vec<double, 3> b = {5.0, 6.0, 7.0};
    auto c = a * b;
    REQUIRE(c[0] == Approx(10.0));
    REQUIRE(c[1] == Approx(18.0));
    REQUIRE(c[2] == Approx(28.0));
}

TEST_CASE("Vec element-wise division", "[vec]") {
    Vec<double, 3> a = {10.0, 18.0, 28.0};
    Vec<double, 3> b = {5.0, 6.0, 7.0};
    auto c = a / b;
    REQUIRE(c[0] == Approx(2.0));
    REQUIRE(c[1] == Approx(3.0));
    REQUIRE(c[2] == Approx(4.0));
}

TEST_CASE("Vec scalar multiplication", "[vec]") {
    Vec<double, 3> a = {1.0, 2.0, 3.0};
    auto b = a * 2.0;
    auto c = 2.0 * a;
    REQUIRE(b[0] == Approx(2.0));
    REQUIRE(b[1] == Approx(4.0));
    REQUIRE(b[2] == Approx(6.0));
    REQUIRE(c[0] == Approx(2.0));
    REQUIRE(c[1] == Approx(4.0));
    REQUIRE(c[2] == Approx(6.0));
}

TEST_CASE("Vec scalar division", "[vec]") {
    Vec<double, 3> a = {2.0, 4.0, 6.0};
    auto b = a / 2.0;
    REQUIRE(b[0] == Approx(1.0));
    REQUIRE(b[1] == Approx(2.0));
    REQUIRE(b[2] == Approx(3.0));
}

TEST_CASE("Vec compound assignment operators", "[vec]") {
    Vec<double, 3> a = {1.0, 2.0, 3.0};
    Vec<double, 3> b = {4.0, 5.0, 6.0};

    a += b;
    REQUIRE(a[0] == Approx(5.0));
    REQUIRE(a[1] == Approx(7.0));
    REQUIRE(a[2] == Approx(9.0));

    a -= b;
    REQUIRE(a[0] == Approx(1.0));
    REQUIRE(a[1] == Approx(2.0));
    REQUIRE(a[2] == Approx(3.0));

    a *= 3.0;
    REQUIRE(a[0] == Approx(3.0));
    REQUIRE(a[1] == Approx(6.0));
    REQUIRE(a[2] == Approx(9.0));

    a /= 3.0;
    REQUIRE(a[0] == Approx(1.0));
    REQUIRE(a[1] == Approx(2.0));
    REQUIRE(a[2] == Approx(3.0));
}

TEST_CASE("Vec dot product", "[vec]") {
    Vec<double, 3> a = {1.0, 2.0, 3.0};
    Vec<double, 3> b = {4.0, 5.0, 6.0};
    // 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
    REQUIRE(dot(a, b) == Approx(32.0));
}

TEST_CASE("Vec norm_sq", "[vec]") {
    Vec<double, 3> a = {3.0, 4.0, 0.0};
    // 9 + 16 + 0 = 25
    REQUIRE(norm_sq(a) == Approx(25.0));
}

TEST_CASE("Vec negative values", "[vec]") {
    Vec<double, 3> a = {-1.0, -2.0, -3.0};
    Vec<double, 3> b = {1.0, 2.0, 3.0};
    auto c = a + b;
    REQUIRE(c[0] == Approx(0.0));
    REQUIRE(c[1] == Approx(0.0));
    REQUIRE(c[2] == Approx(0.0));
    REQUIRE(dot(a, b) == Approx(-14.0));
}

TEMPLATE_TEST_CASE("Vec arithmetic is precision-aware", "[vec][template]", float, double) {
    using Real = TestType;
    Vec<Real, 3> a = {Real(1.0), Real(2.0), Real(3.0)};
    Vec<Real, 3> b = {Real(0.1), Real(0.2), Real(0.3)};
    auto c = a + b;
    REQUIRE(c[0] == Approx(Real(1.1)).epsilon(eps<Real>()));
    REQUIRE(c[1] == Approx(Real(2.2)).epsilon(eps<Real>()));
    REQUIRE(c[2] == Approx(Real(3.3)).epsilon(eps<Real>()));
}

TEMPLATE_TEST_CASE("Constants are precision-correct", "[types][template]", float, double) {
    using Real = TestType;
    REQUIRE(Constants<Real>::gamma == Approx(Real(1.4)).epsilon(eps<Real>()));
    REQUIRE(Constants<Real>::gamma_m1 == Approx(Real(0.4)).epsilon(eps<Real>()));
}
