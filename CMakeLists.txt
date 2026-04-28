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

# Riemann solver inequality variant: <= (default) vs < (strict)
option(RIEMANN_STRICT_INEQUALITY "Use strict < instead of <= in HLLC/HLLD" OFF)
if(RIEMANN_STRICT_INEQUALITY)
    target_compile_definitions(hrsc_core INTERFACE RIEMANN_STRICT_INEQUALITY)
endif()

# OpenMP parallelisation of the per-row / per-column sweep loops.
# Disable with -DENABLE_OPENMP=OFF when running under Verificarlo MCA
# (the libinterflop PRNG is not thread-safe; MCA runs must stay serial
# via OMP_NUM_THREADS=1 in any case, but turning the pragmas off at
# build time makes the intent explicit).
option(ENABLE_OPENMP "Enable OpenMP parallelisation in sweeps" ON)
if(ENABLE_OPENMP)
    find_package(OpenMP)
    if(OpenMP_CXX_FOUND)
        target_link_libraries(hrsc_core INTERFACE OpenMP::OpenMP_CXX)
        message(STATUS "OpenMP enabled (${OpenMP_CXX_VERSION})")
    else()
        message(WARNING "ENABLE_OPENMP=ON but OpenMP not found; building serial")
    endif()
endif()

# --- Separated Euler solver library ---
# EulerSolver was split header-only -> .hpp/.cpp with explicit instantiation
# for float and double in src/euler/euler_solver.cpp. Keeping the solver as
# a static library ensures it's compiled once per binary (rather than once
# per TU) and gives a clean linker error if a caller asks for a precision
# the .cpp didn't instantiate (e.g. long double).
add_library(hrsc_euler STATIC src/euler/euler_solver.cpp)
target_link_libraries(hrsc_euler PUBLIC hrsc_core)

# --- Main executable ---
add_executable(hrsc src/main.cpp)
target_link_libraries(hrsc PRIVATE hrsc_core hrsc_euler)
target_include_directories(hrsc PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/toro_1d)
target_include_directories(hrsc PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/liska_wendroff_2d)

# --- Unit tests ---
file(GLOB TEST_SOURCES tests/unit/test_*.cpp)
add_executable(unit_tests ${TEST_SOURCES})
target_link_libraries(unit_tests PRIVATE hrsc_core hrsc_euler)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/external/catch2)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/toro_1d)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/liska_wendroff_2d)
