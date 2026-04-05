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

# --- Main executable ---
add_executable(hrsc src/main.cpp)
target_link_libraries(hrsc PRIVATE hrsc_core)

# --- Unit tests ---
file(GLOB TEST_SOURCES tests/unit/test_*.cpp)
add_executable(unit_tests ${TEST_SOURCES})
target_link_libraries(unit_tests PRIVATE hrsc_core)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/external/catch2)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/toro_1d)
