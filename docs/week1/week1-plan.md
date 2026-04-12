# Week 1 Foundation: Core Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the precision-generic core infrastructure (types, vec, config, grid, EOS, boundary) with Catch2 v2 unit tests, ready for the 1D Euler solver in Week 2.

**Architecture:** All computational types templated on `<Real>` inside `namespace hrsc`. Container-View separation for Grid (host `std::vector` owner + trivially-copyable `GridView` accessor for future GPU). Header-only throughout — templates live in `.hpp` files.

**Tech Stack:** C++17, CMake 3.18+, gcc/g++ on WSL/Linux, Catch2 v2 (single-header, vendored)

**Spec:** `docs/superpowers/specs/week1-foundation-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `CMakeLists.txt` | Root build config: C++17, INTERFACE lib, two targets |
| `.gitignore` | Ignore build/, output/, binaries, IDE files |
| `external/catch2/catch.hpp` | Catch2 v2 single header (vendored, ~700KB) |
| `src/main.cpp` | Stub entry point |
| `src/core/types.hpp` | `HD_FUNC` macro, `namespace hrsc`, `Constants<Real>` |
| `src/core/vec.hpp` | `Vec<Real,N>` aggregate + free-function arithmetic |
| `src/utils/config.hpp` | Header-only key=value config parser |
| `src/core/grid.hpp` | `GridViewBase`, `GridView`, `ConstGridView`, `Grid2D` |
| `src/core/eos.hpp` | Ideal gas EOS: pressure, sound speed, cons/prim conversion |
| `src/core/boundary.hpp` | Outflow (transmissive) boundary conditions |
| `tests/unit/test_main.cpp` | `#define CATCH_CONFIG_MAIN` (Catch2 entry point) |
| `tests/unit/test_vec.cpp` | Vec arithmetic, dot, aggregate init |
| `tests/unit/test_config.cpp` | Config parsing via stringstream |
| `tests/unit/test_grid.cpp` | Grid allocation, indexing, view const-correctness |
| `tests/unit/test_eos.cpp` | EOS round-trip, Sod states, sound speed |
| `tests/unit/test_boundary.cpp` | Ghost cell fill, 1D mode |

---

## Task 1: Project Skeleton + Build System

**Files:**
- Create: `.gitignore`
- Create: `CMakeLists.txt`
- Create: `src/main.cpp`
- Create: `external/catch2/catch.hpp` (download)
- Create: `tests/unit/test_main.cpp`

- [ ] **Step 1: Create `.gitignore`**

```gitignore
# Build
build/
cmake-build-*/

# Output data
output/
*.o
*.bin
*.dat
*.csv

# IDE
.vscode/
.idea/
*.swp
*~
.cache/
compile_commands.json

# Python
__pycache__/
*.pyc
.venv/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create `src/main.cpp` stub**

```cpp
#include <iostream>

int main() {
    std::cout << "HRSC Solver — not yet implemented\n";
    return 0;
}
```

- [ ] **Step 3: Download Catch2 v2 single header**

Run (in WSL):
```bash
mkdir -p external/catch2
curl -sL https://github.com/catchorg/Catch2/releases/download/v2.13.10/catch.hpp -o external/catch2/catch.hpp
```

Verify: `wc -l external/catch2/catch.hpp` should show ~17,000+ lines.

- [ ] **Step 4: Create `tests/unit/test_main.cpp`**

This file provides Catch2's `main()`. It compiles once, all other test files link against it.

```cpp
#define CATCH_CONFIG_MAIN
#include "catch.hpp"
```

- [ ] **Step 5: Create `CMakeLists.txt`**

```cmake
cmake_minimum_required(VERSION 3.18)
project(hrsc LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler warnings
add_compile_options(-Wall -Wextra -Wpedantic)

# Precision option (variable only for now, switching in Week 4)
set(FLOAT_PRECISION "double" CACHE STRING "Floating-point precision (float/double)")

# --- INTERFACE library for include paths ---
add_library(hrsc_core INTERFACE)
target_include_directories(hrsc_core INTERFACE ${CMAKE_SOURCE_DIR}/src)

# --- Main executable ---
add_executable(hrsc src/main.cpp)
target_link_libraries(hrsc PRIVATE hrsc_core)

# --- Unit tests ---
file(GLOB TEST_SOURCES tests/unit/test_*.cpp)
add_executable(unit_tests ${TEST_SOURCES})
target_link_libraries(unit_tests PRIVATE hrsc_core)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/external/catch2)
```

- [ ] **Step 6: Create placeholder directories**

Run:
```bash
mkdir -p src/core src/utils src/euler src/mhd src/gpu
mkdir -p tests/unit tests/cases/toro_1d tests/cases/liska_wendroff_2d
mkdir -p tests/cases/shock_bubble tests/cases/orszag_tang tests/cases/kelvin_helmholtz
mkdir -p output
```

- [ ] **Step 7: Build and verify**

Run:
```bash
cmake -B build -S .
cmake --build build
./build/hrsc
./build/unit_tests
```

Expected:
- `./build/hrsc` prints: `HRSC Solver — not yet implemented`
- `./build/unit_tests` prints: `No tests ran` (or similar — no test cases registered yet)

- [ ] **Step 8: Commit**

```bash
git init
git add .gitignore CMakeLists.txt src/main.cpp external/catch2/catch.hpp tests/unit/test_main.cpp
git commit -m "feat: project skeleton with CMake build system and Catch2 v2"
```

---

## Task 2: types.hpp — HD_FUNC + Constants

**Files:**
- Create: `src/core/types.hpp`

No separate test file — `types.hpp` is tested implicitly through `test_vec.cpp` in Task 3.

- [ ] **Step 1: Create `src/core/types.hpp`**

```cpp
#pragma once

// CPU/GPU portability macro — expands to nothing on CPU builds
#ifdef __CUDACC__
  #define HD_FUNC __host__ __device__
#else
  #define HD_FUNC
#endif

namespace hrsc {

// Physical constants templated on precision type
template <typename Real>
struct Constants {
    static constexpr Real gamma   = static_cast<Real>(1.4);
    static constexpr Real gamma_m1 = static_cast<Real>(0.4);
};

} // namespace hrsc
```

- [ ] **Step 2: Verify it compiles**

Run:
```bash
cmake --build build
```

Expected: clean build, no warnings.

- [ ] **Step 3: Commit**

```bash
git add src/core/types.hpp
git commit -m "feat: add types.hpp with HD_FUNC macro and Constants<Real>"
```

---

## Task 3: vec.hpp — Vec<Real, N> Aggregate + Arithmetic

**Files:**
- Create: `src/core/vec.hpp`
- Create: `tests/unit/test_vec.cpp`

- [ ] **Step 1: Write failing tests — `tests/unit/test_vec.cpp`**

```cpp
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cmake --build build 2>&1
```

Expected: compilation FAILS — `core/vec.hpp` does not exist yet.

- [ ] **Step 3: Implement `src/core/vec.hpp`**

```cpp
#pragma once

#include "core/types.hpp"

namespace hrsc {

template <typename Real, int N>
struct Vec {
    Real data[N];

    HD_FUNC Real& operator[](int i) { return data[i]; }
    HD_FUNC const Real& operator[](int i) const { return data[i]; }
};

// --- Element-wise binary operators ---

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator+(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] + b[i];
    return result;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator-(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] - b[i];
    return result;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator*(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] * b[i];
    return result;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator/(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] / b[i];
    return result;
}

// --- Scalar operators ---

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator*(const Vec<Real, N>& a, Real s) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] * s;
    return result;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator*(Real s, const Vec<Real, N>& a) {
    return a * s;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N> operator/(const Vec<Real, N>& a, Real s) {
    Vec<Real, N> result{};
    for (int i = 0; i < N; ++i) result[i] = a[i] / s;
    return result;
}

// --- Compound assignment ---

template <typename Real, int N>
HD_FUNC Vec<Real, N>& operator+=(Vec<Real, N>& a, const Vec<Real, N>& b) {
    for (int i = 0; i < N; ++i) a[i] += b[i];
    return a;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N>& operator-=(Vec<Real, N>& a, const Vec<Real, N>& b) {
    for (int i = 0; i < N; ++i) a[i] -= b[i];
    return a;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N>& operator*=(Vec<Real, N>& a, Real s) {
    for (int i = 0; i < N; ++i) a[i] *= s;
    return a;
}

template <typename Real, int N>
HD_FUNC Vec<Real, N>& operator/=(Vec<Real, N>& a, Real s) {
    for (int i = 0; i < N; ++i) a[i] /= s;
    return a;
}

// --- Reductions ---

template <typename Real, int N>
HD_FUNC Real dot(const Vec<Real, N>& a, const Vec<Real, N>& b) {
    Real sum = Real(0);
    for (int i = 0; i < N; ++i) sum += a[i] * b[i];
    return sum;
}

template <typename Real, int N>
HD_FUNC Real norm_sq(const Vec<Real, N>& a) {
    return dot(a, a);
}

} // namespace hrsc
```

- [ ] **Step 4: Build and run tests**

Run:
```bash
cmake --build build && ./build/unit_tests
```

Expected: all tests PASS. Zero warnings.

- [ ] **Step 5: Commit**

```bash
git add src/core/vec.hpp tests/unit/test_vec.cpp
git commit -m "feat: add Vec<Real,N> aggregate with arithmetic and Catch2 tests"
```

---

## Task 4: config.hpp — Key=Value Config Parser

**Files:**
- Create: `src/utils/config.hpp`
- Create: `tests/unit/test_config.cpp`

- [ ] **Step 1: Write failing tests — `tests/unit/test_config.cpp`**

```cpp
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cmake --build build 2>&1
```

Expected: compilation FAILS — `utils/config.hpp` does not exist yet.

- [ ] **Step 3: Implement `src/utils/config.hpp`**

```cpp
#pragma once

#include <fstream>
#include <sstream>
#include <string>
#include <stdexcept>
#include <unordered_map>

namespace hrsc {

class Config {
    std::unordered_map<std::string, std::string> entries_;

    static std::string trim(const std::string& s) {
        auto start = s.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) return "";
        auto end = s.find_last_not_of(" \t\r\n");
        return s.substr(start, end - start + 1);
    }

    void parse(std::istream& is) {
        std::string line;
        while (std::getline(is, line)) {
            std::string trimmed = trim(line);
            if (trimmed.empty() || trimmed[0] == '#') continue;

            auto eq_pos = trimmed.find('=');
            if (eq_pos == std::string::npos) continue;

            std::string key = trim(trimmed.substr(0, eq_pos));
            std::string val = trim(trimmed.substr(eq_pos + 1));
            if (!key.empty()) {
                entries_[key] = val;
            }
        }
    }

public:
    explicit Config(std::istream& is) { parse(is); }

    explicit Config(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open config file: " + filename);
        }
        parse(file);
    }

    std::string get_string(const std::string& key,
                           const std::string& def = "") const {
        auto it = entries_.find(key);
        return (it != entries_.end()) ? it->second : def;
    }

    int get_int(const std::string& key, int def = 0) const {
        auto it = entries_.find(key);
        if (it == entries_.end()) return def;
        try {
            return std::stoi(it->second);
        } catch (const std::invalid_argument&) {
            throw std::runtime_error(
                "Failed to parse key '" + key + "' as int: " + it->second);
        } catch (const std::out_of_range&) {
            throw std::runtime_error(
                "Failed to parse key '" + key + "' as int (out of range): " + it->second);
        }
    }

    double get_double(const std::string& key, double def = 0.0) const {
        auto it = entries_.find(key);
        if (it == entries_.end()) return def;
        try {
            return std::stod(it->second);
        } catch (const std::invalid_argument&) {
            throw std::runtime_error(
                "Failed to parse key '" + key + "' as double: " + it->second);
        } catch (const std::out_of_range&) {
            throw std::runtime_error(
                "Failed to parse key '" + key + "' as double (out of range): " + it->second);
        }
    }

    bool get_bool(const std::string& key, bool def = false) const {
        auto it = entries_.find(key);
        if (it == entries_.end()) return def;
        const std::string& val = it->second;
        if (val == "true" || val == "1") return true;
        if (val == "false" || val == "0") return false;
        throw std::runtime_error(
            "Failed to parse key '" + key + "' as bool: " + val);
    }
};

} // namespace hrsc
```

- [ ] **Step 4: Build and run tests**

Run:
```bash
cmake --build build && ./build/unit_tests "[config]"
```

Expected: all `[config]` tests PASS.

- [ ] **Step 5: Run full test suite to check no regressions**

Run:
```bash
./build/unit_tests
```

Expected: all tests PASS (vec + config).

- [ ] **Step 6: Commit**

```bash
git add src/utils/config.hpp tests/unit/test_config.cpp
git commit -m "feat: add header-only Config parser with stream-based testing"
```

---

## Task 5: grid.hpp — Container-View Separation

**Files:**
- Create: `src/core/grid.hpp`
- Create: `tests/unit/test_grid.cpp`

- [ ] **Step 1: Write failing tests — `tests/unit/test_grid.cpp`**

```cpp
#include "catch.hpp"
#include "core/grid.hpp"

using namespace hrsc;

static constexpr int NVARS = 4; // Euler: rho, rho*u, rho*v, E

TEST_CASE("Grid2D allocation size is correct", "[grid]") {
    Grid2D<double, NVARS> grid(10, 20);
    int ng = Grid2D<double, NVARS>::ng; // 2
    int expected = (10 + 2 * ng) * (20 + 2 * ng) * NVARS;
    REQUIRE(grid.data.size() == static_cast<size_t>(expected));
}

TEST_CASE("Grid2D 1D mode allocation", "[grid]") {
    Grid2D<double, NVARS> grid(200, 1);
    int ng = Grid2D<double, NVARS>::ng;
    int expected = (200 + 2 * ng) * (1 + 2 * ng) * NVARS;
    REQUIRE(grid.data.size() == static_cast<size_t>(expected));
}

TEST_CASE("Grid2D zero-initialized", "[grid]") {
    Grid2D<double, NVARS> grid(5, 5);
    for (size_t i = 0; i < grid.data.size(); ++i) {
        REQUIRE(grid.data[i] == 0.0);
    }
}

TEST_CASE("GridView write and read physical cells", "[grid]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    // Write to cell (2, 1), variable 0
    v(2, 1, 0) = 42.0;
    REQUIRE(v(2, 1, 0) == Approx(42.0));

    // Write to cell (0, 0), variable 3
    v(0, 0, 3) = 99.0;
    REQUIRE(v(0, 0, 3) == Approx(99.0));
}

TEST_CASE("GridView ghost cell access", "[grid]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    // Write to ghost cell (-1, 0, 0)
    v(-1, 0, 0) = 7.0;
    REQUIRE(v(-1, 0, 0) == Approx(7.0));

    // Write to ghost cell (4, 0, 0) — one past nx
    v(4, 0, 0) = 8.0;
    REQUIRE(v(4, 0, 0) == Approx(8.0));

    // Write to ghost cell (0, -2, 1) — two rows before
    v(0, -2, 1) = 9.0;
    REQUIRE(v(0, -2, 1) == Approx(9.0));
}

TEST_CASE("GridView index matches raw memory layout", "[grid]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();
    int ng = 2;

    // Physical cell (i=1, j=2, var=3)
    // Raw index: ((2+ng) * nx_total + (1+ng)) * NVARS + 3
    //          = (4 * 8 + 3) * 4 + 3 = 35 * 4 + 3 = 143
    int nx_total = 4 + 2 * ng; // 8
    int expected_idx = ((2 + ng) * nx_total + (1 + ng)) * NVARS + 3;
    REQUIRE(v.index(1, 2, 3) == expected_idx);

    // Write via view, read via raw pointer
    v(1, 2, 3) = 123.456;
    REQUIRE(grid.data[static_cast<size_t>(expected_idx)] == Approx(123.456));
}

TEST_CASE("GridView 1D mode indexing", "[grid]") {
    Grid2D<double, NVARS> grid(200, 1);
    auto v = grid.view();
    int ng = 2;

    // Cell (100, 0, 0)
    int nx_total = 200 + 2 * ng; // 204
    int expected_idx = ((0 + ng) * nx_total + (100 + ng)) * NVARS + 0;
    v(100, 0, 0) = 55.5;
    REQUIRE(grid.data[static_cast<size_t>(expected_idx)] == Approx(55.5));
}

TEST_CASE("Grid2D view() const returns ConstGridView", "[grid]") {
    Grid2D<double, NVARS> grid(4, 3);
    grid.view()(0, 0, 0) = 1.0;

    const Grid2D<double, NVARS>& cgrid = grid;
    auto cv = cgrid.view();  // Should return ConstGridView

    REQUIRE(cv(0, 0, 0) == Approx(1.0));

    // The following should NOT compile (uncomment to verify):
    // cv(0, 0, 0) = 2.0;  // ERROR: assignment to const reference
}

TEST_CASE("Grid2D dimensions stored correctly", "[grid]") {
    Grid2D<double, NVARS> grid(10, 20);
    REQUIRE(grid.nx == 10);
    REQUIRE(grid.ny == 20);

    auto v = grid.view();
    REQUIRE(v.nx == 10);
    REQUIRE(v.ny == 20);
    REQUIRE(v.nx_total() == 14);
    REQUIRE(v.ny_total() == 24);
}

TEST_CASE("Grid2D dx/dy propagated to view", "[grid]") {
    Grid2D<double, NVARS> grid(100, 50);
    grid.dx = 0.01;
    grid.dy = 0.02;

    auto v = grid.view();
    REQUIRE(v.dx == Approx(0.01));
    REQUIRE(v.dy == Approx(0.02));
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cmake --build build 2>&1
```

Expected: compilation FAILS — `core/grid.hpp` does not exist yet.

- [ ] **Step 3: Implement `src/core/grid.hpp`**

```cpp
#pragma once

#include "core/types.hpp"

#include <vector>

namespace hrsc {

// Const-generic view: Ptr is Real* or const Real*
template <typename Real, int NVars, typename Ptr>
struct GridViewBase {
    Ptr data;
    int nx, ny;
    Real dx, dy;
    static constexpr int ng = 2;

    HD_FUNC int nx_total() const { return nx + 2 * ng; }
    HD_FUNC int ny_total() const { return ny + 2 * ng; }

    HD_FUNC int index(int i, int j, int var) const {
        return ((j + ng) * nx_total() + (i + ng)) * NVars + var;
    }

    HD_FUNC auto operator()(int i, int j, int var) -> decltype(data[0]) {
        return data[index(i, j, var)];
    }

    HD_FUNC auto operator()(int i, int j, int var) const -> decltype(data[0]) {
        return data[index(i, j, var)];
    }
};

template <typename Real, int NVars>
using GridView = GridViewBase<Real, NVars, Real*>;

template <typename Real, int NVars>
using ConstGridView = GridViewBase<Real, NVars, const Real*>;

// Owning container — host only, no HD_FUNC
template <typename Real, int NVars>
struct Grid2D {
    int nx, ny;
    static constexpr int ng = 2;
    std::vector<Real> data;
    Real dx, dy;

    Grid2D(int nx_, int ny_)
        : nx(nx_), ny(ny_),
          data(static_cast<size_t>((nx_ + 2 * ng) * (ny_ + 2 * ng) * NVars), Real(0)),
          dx(Real(0)), dy(Real(0)) {}

    GridView<Real, NVars> view() {
        return {data.data(), nx, ny, dx, dy};
    }

    ConstGridView<Real, NVars> view() const {
        return {data.data(), nx, ny, dx, dy};
    }
};

} // namespace hrsc
```

- [ ] **Step 4: Build and run tests**

Run:
```bash
cmake --build build && ./build/unit_tests "[grid]"
```

Expected: all `[grid]` tests PASS.

- [ ] **Step 5: Run full test suite**

Run:
```bash
./build/unit_tests
```

Expected: all tests PASS (vec + config + grid).

- [ ] **Step 6: Commit**

```bash
git add src/core/grid.hpp tests/unit/test_grid.cpp
git commit -m "feat: add Grid2D with Container-View separation for GPU portability"
```

---

## Task 6: eos.hpp — Ideal Gas Equation of State

**Files:**
- Create: `src/core/eos.hpp`
- Create: `tests/unit/test_eos.cpp`

- [ ] **Step 1: Write failing tests — `tests/unit/test_eos.cpp`**

```cpp
#include "catch.hpp"
#include "core/eos.hpp"

#include <cmath>

using namespace hrsc;

template <typename Real>
constexpr Real eps() {
    return std::is_same<Real, float>::value ? Real(1e-5) : Real(1e-12);
}

TEST_CASE("EOS pressure from Sod left state", "[eos]") {
    // Sod left: rho=1, u=0, v=0, p=1, gamma=1.4
    // E = p/(gamma-1) + 0.5*rho*(u^2+v^2) = 1/0.4 + 0 = 2.5
    Vec<double, 4> cons = {1.0, 0.0, 0.0, 2.5};
    double p = pressure(cons, 1.4);
    REQUIRE(p == Approx(1.0).epsilon(1e-12));
}

TEST_CASE("EOS pressure from Sod right state", "[eos]") {
    // Sod right: rho=0.125, u=0, v=0, p=0.1
    // E = 0.1/0.4 + 0 = 0.25
    Vec<double, 4> cons = {0.125, 0.0, 0.0, 0.25};
    double p = pressure(cons, 1.4);
    REQUIRE(p == Approx(0.1).epsilon(1e-12));
}

TEST_CASE("EOS pressure with nonzero velocity", "[eos]") {
    // rho=2, u=3, v=4, p=10, gamma=1.4
    // rho_u=6, rho_v=8
    // KE = 0.5*(36+64)/2 = 25
    // E = 10/0.4 + 25 = 50
    Vec<double, 4> cons = {2.0, 6.0, 8.0, 50.0};
    double p = pressure(cons, 1.4);
    REQUIRE(p == Approx(10.0).epsilon(1e-12));
}

TEST_CASE("EOS sound speed from Sod left state", "[eos]") {
    // a = sqrt(gamma * p / rho) = sqrt(1.4 * 1.0 / 1.0) = sqrt(1.4)
    double a = sound_speed(1.0, 1.0, 1.4);
    REQUIRE(a == Approx(std::sqrt(1.4)).epsilon(1e-12));
}

TEST_CASE("EOS sound speed from Sod right state", "[eos]") {
    // a = sqrt(1.4 * 0.1 / 0.125) = sqrt(1.12)
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
    // rho=1, u=0, v=0, p=1 -> E = p/(gamma-1) = 2.5
    Vec<double, 4> prim = {1.0, 0.0, 0.0, 1.0};
    auto cons = prim_to_cons(prim, 1.4);

    REQUIRE(cons[0] == Approx(1.0));    // rho
    REQUIRE(cons[1] == Approx(0.0));    // rho*u
    REQUIRE(cons[2] == Approx(0.0));    // rho*v
    REQUIRE(cons[3] == Approx(2.5));    // E = p/(gamma-1) only
}

TEST_CASE("EOS prim_to_cons conserved variable values", "[eos]") {
    // rho=2, u=3, v=4, p=10, gamma=1.4
    Vec<double, 4> prim = {2.0, 3.0, 4.0, 10.0};
    auto cons = prim_to_cons(prim, 1.4);

    REQUIRE(cons[0] == Approx(2.0));    // rho
    REQUIRE(cons[1] == Approx(6.0));    // rho*u
    REQUIRE(cons[2] == Approx(8.0));    // rho*v
    // E = p/(gamma-1) + 0.5*rho*(u^2+v^2) = 25 + 0.5*2*25 = 50
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cmake --build build 2>&1
```

Expected: compilation FAILS — `core/eos.hpp` does not exist yet.

- [ ] **Step 3: Implement `src/core/eos.hpp`**

```cpp
#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"

#include <cassert>
#include <cmath>
#include <limits>

namespace hrsc {

// Conserved variable indexing for Euler: {rho, rho*u, rho*v, E}
enum EulerVar : int { RHO = 0, RHOU = 1, RHOV = 2, EN = 3 };

// Pressure from conserved variables
// p = (gamma - 1) * (E - 0.5 * (rho_u^2 + rho_v^2) / rho)
template <typename Real>
HD_FUNC Real pressure(const Vec<Real, 4>& cons, Real gamma) {
    Real rho   = cons[RHO];
    Real rho_u = cons[RHOU];
    Real rho_v = cons[RHOV];
    Real E     = cons[EN];

    assert(rho > std::numeric_limits<Real>::min());

    Real ke = Real(0.5) * (rho_u * rho_u + rho_v * rho_v) / rho;
    return (gamma - Real(1)) * (E - ke);
}

// Sound speed: a = sqrt(gamma * p / rho)
template <typename Real>
HD_FUNC Real sound_speed(Real rho, Real p, Real gamma) {
    assert(rho > std::numeric_limits<Real>::min());
    return std::sqrt(gamma * p / rho);
}

// Conserved {rho, rho*u, rho*v, E} -> Primitive {rho, u, v, p}
template <typename Real>
HD_FUNC Vec<Real, 4> cons_to_prim(const Vec<Real, 4>& cons, Real gamma) {
    Real rho = cons[RHO];
    assert(rho > std::numeric_limits<Real>::min());

    Real u = cons[RHOU] / rho;
    Real v = cons[RHOV] / rho;
    Real p = pressure(cons, gamma);

    return {rho, u, v, p};
}

// Primitive {rho, u, v, p} -> Conserved {rho, rho*u, rho*v, E}
template <typename Real>
HD_FUNC Vec<Real, 4> prim_to_cons(const Vec<Real, 4>& prim, Real gamma) {
    Real rho = prim[0];
    Real u   = prim[1];
    Real v   = prim[2];
    Real p   = prim[3];

    Real E = p / (gamma - Real(1)) + Real(0.5) * rho * (u * u + v * v);

    return {rho, rho * u, rho * v, E};
}

} // namespace hrsc
```

- [ ] **Step 4: Build and run tests**

Run:
```bash
cmake --build build && ./build/unit_tests "[eos]"
```

Expected: all `[eos]` tests PASS.

- [ ] **Step 5: Run full test suite**

Run:
```bash
./build/unit_tests
```

Expected: all tests PASS (vec + config + grid + eos).

- [ ] **Step 6: Commit**

```bash
git add src/core/eos.hpp tests/unit/test_eos.cpp
git commit -m "feat: add ideal gas EOS with pressure, sound speed, prim/cons conversion"
```

---

## Task 7: boundary.hpp — Outflow (Transmissive) BCs

**Files:**
- Create: `src/core/boundary.hpp`
- Create: `tests/unit/test_boundary.cpp`

- [ ] **Step 1: Write failing tests — `tests/unit/test_boundary.cpp`**

```cpp
#include "catch.hpp"
#include "core/boundary.hpp"

using namespace hrsc;

static constexpr int NVARS = 4;

TEST_CASE("Outflow BC fills x-ghost cells from outermost physical cells", "[boundary]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    // Set outermost physical columns to known values
    for (int j = 0; j < 3; ++j) {
        for (int var = 0; var < NVARS; ++var) {
            v(0, j, var) = 10.0 + j + var * 0.1;         // left edge
            v(3, j, var) = 90.0 + j + var * 0.1;         // right edge (nx-1=3)
        }
    }

    apply_outflow_bc(v);

    // Left ghosts: (-1,j) and (-2,j) should match (0,j)
    for (int j = 0; j < 3; ++j) {
        for (int var = 0; var < NVARS; ++var) {
            double expected_left = 10.0 + j + var * 0.1;
            REQUIRE(v(-1, j, var) == Approx(expected_left));
            REQUIRE(v(-2, j, var) == Approx(expected_left));
        }
    }

    // Right ghosts: (4,j) and (5,j) should match (3,j)
    for (int j = 0; j < 3; ++j) {
        for (int var = 0; var < NVARS; ++var) {
            double expected_right = 90.0 + j + var * 0.1;
            REQUIRE(v(4, j, var) == Approx(expected_right));
            REQUIRE(v(5, j, var) == Approx(expected_right));
        }
    }
}

TEST_CASE("Outflow BC fills y-ghost cells from outermost physical rows", "[boundary]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    // Set outermost physical rows to known values
    for (int i = 0; i < 4; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            v(i, 0, var) = 20.0 + i + var * 0.1;         // bottom edge
            v(i, 2, var) = 80.0 + i + var * 0.1;         // top edge (ny-1=2)
        }
    }

    apply_outflow_bc(v);

    // Bottom ghosts: (i,-1) and (i,-2) should match (i,0)
    for (int i = 0; i < 4; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            double expected_bottom = 20.0 + i + var * 0.1;
            REQUIRE(v(i, -1, var) == Approx(expected_bottom));
            REQUIRE(v(i, -2, var) == Approx(expected_bottom));
        }
    }

    // Top ghosts: (i,3) and (i,4) should match (i,2)
    for (int i = 0; i < 4; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            double expected_top = 80.0 + i + var * 0.1;
            REQUIRE(v(i, 3, var) == Approx(expected_top));
            REQUIRE(v(i, 4, var) == Approx(expected_top));
        }
    }
}

TEST_CASE("Outflow BC 1D mode fills y-ghosts without corrupting data", "[boundary]") {
    Grid2D<double, NVARS> grid(10, 1);
    auto v = grid.view();

    // Set all physical cells
    for (int i = 0; i < 10; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            v(i, 0, var) = 100.0 + i * 10.0 + var;
        }
    }

    apply_outflow_bc(v);

    // Physical cells unchanged
    for (int i = 0; i < 10; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            REQUIRE(v(i, 0, var) == Approx(100.0 + i * 10.0 + var));
        }
    }

    // X-ghosts correct
    for (int var = 0; var < NVARS; ++var) {
        REQUIRE(v(-1, 0, var) == Approx(100.0 + var));
        REQUIRE(v(-2, 0, var) == Approx(100.0 + var));
        REQUIRE(v(10, 0, var) == Approx(100.0 + 90.0 + var));
        REQUIRE(v(11, 0, var) == Approx(100.0 + 90.0 + var));
    }

    // Y-ghosts filled (not left uninitialized)
    for (int i = 0; i < 10; ++i) {
        for (int var = 0; var < NVARS; ++var) {
            double expected = 100.0 + i * 10.0 + var;
            REQUIRE(v(i, -1, var) == Approx(expected));
            REQUIRE(v(i, -2, var) == Approx(expected));
            REQUIRE(v(i, 1, var) == Approx(expected));
            REQUIRE(v(i, 2, var) == Approx(expected));
        }
    }
}

TEST_CASE("Outflow BC corner ghost cells are filled", "[boundary]") {
    Grid2D<double, NVARS> grid(4, 3);
    auto v = grid.view();

    // Set corner physical cells
    v(0, 0, 0) = 1.0;   // bottom-left
    v(3, 0, 0) = 2.0;   // bottom-right
    v(0, 2, 0) = 3.0;   // top-left
    v(3, 2, 0) = 4.0;   // top-right

    apply_outflow_bc(v);

    // Corner ghosts should be filled by either x-BC or y-BC pass
    // (-1, -1) should be some filled value (not zero/uninitialized)
    // Exact value depends on BC application order, but must not be 0.0
    REQUIRE(v(-1, -1, 0) != Approx(0.0));
    REQUIRE(v(4, -1, 0) != Approx(0.0));
    REQUIRE(v(-1, 3, 0) != Approx(0.0));
    REQUIRE(v(4, 3, 0) != Approx(0.0));
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cmake --build build 2>&1
```

Expected: compilation FAILS — `core/boundary.hpp` does not exist yet.

- [ ] **Step 3: Implement `src/core/boundary.hpp`**

```cpp
#pragma once

#include "core/grid.hpp"

namespace hrsc {

// Outflow (transmissive) boundary conditions.
// Copies outermost physical cell values into ghost layers.
// Host-only orchestrator — no HD_FUNC on this function.
template <typename Real, int NVars>
void apply_outflow_bc(GridView<Real, NVars> grid) {
    int nx = grid.nx;
    int ny = grid.ny;
    constexpr int ng = GridView<Real, NVars>::ng;

    // --- X-boundaries ---
    // Loop over all rows including ghost rows in y, so corners get filled
    for (int j = -ng; j < ny + ng; ++j) {
        for (int var = 0; var < NVars; ++var) {
            // Clamp j to physical range for source cell
            int js = (j < 0) ? 0 : (j >= ny ? ny - 1 : j);
            for (int g = 1; g <= ng; ++g) {
                grid(-g, j, var)      = grid(0, js, var);       // left
                grid(nx - 1 + g, j, var) = grid(nx - 1, js, var); // right
            }
        }
    }

    // --- Y-boundaries ---
    // Loop over all columns including ghost columns in x (already filled above)
    for (int i = -ng; i < nx + ng; ++i) {
        for (int var = 0; var < NVars; ++var) {
            for (int g = 1; g <= ng; ++g) {
                grid(i, -g, var)      = grid(i, 0, var);        // bottom
                grid(i, ny - 1 + g, var) = grid(i, ny - 1, var);  // top
            }
        }
    }
}

} // namespace hrsc
```

**Implementation note:** The x-boundary loop uses `js` (clamped j) to handle corner ghost cells where `j` is in the ghost range. When the y-boundary pass runs second, it overwrites corners with values from the y-edge, which is the correct transmissive behavior. The key invariant is: no ghost cell is left uninitialized.

- [ ] **Step 4: Build and run tests**

Run:
```bash
cmake --build build && ./build/unit_tests "[boundary]"
```

Expected: all `[boundary]` tests PASS.

- [ ] **Step 5: Run full test suite — final milestone check**

Run:
```bash
cmake --build build 2>&1 | grep -i warning
./build/unit_tests
```

Expected:
- Zero warnings from the build
- ALL tests PASS (vec + config + grid + eos + boundary)

- [ ] **Step 6: Commit**

```bash
git add src/core/boundary.hpp tests/unit/test_boundary.cpp
git commit -m "feat: add outflow boundary conditions with 1D mode support"
```

---

## Task 8: Final Verification + Milestone Commit

- [ ] **Step 1: Clean rebuild from scratch**

Run:
```bash
rm -rf build
cmake -B build -S .
cmake --build build 2>&1
```

Expected: clean build, zero warnings.

- [ ] **Step 2: Run all tests**

Run:
```bash
./build/unit_tests -v
```

Expected: all tests PASS with verbose output showing every test case.

- [ ] **Step 3: Run main executable**

Run:
```bash
./build/hrsc
```

Expected: prints `HRSC Solver — not yet implemented`

- [ ] **Step 4: Verify project structure**

Run:
```bash
find . -name '*.hpp' -o -name '*.cpp' | sort
```

Expected:
```
./src/core/boundary.hpp
./src/core/eos.hpp
./src/core/grid.hpp
./src/core/types.hpp
./src/core/vec.hpp
./src/main.cpp
./src/utils/config.hpp
./tests/unit/test_boundary.cpp
./tests/unit/test_config.cpp
./tests/unit/test_eos.cpp
./tests/unit/test_grid.cpp
./tests/unit/test_main.cpp
./tests/unit/test_vec.cpp
```

- [ ] **Step 5: Milestone commit**

```bash
git add -A
git status
git commit -m "milestone: Week 1 foundation complete — all core infrastructure with tests"
```

Week 1 milestone criteria met:
- `cmake --build build` succeeds with zero warnings
- `./build/unit_tests` passes all Catch2 tests
- Grid works in 1D mode (`ny=1`) ready for Week 2 solver
- All code inside `namespace hrsc`, all templates on `<Real>`
