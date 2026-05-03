cmake_minimum_required(VERSION 3.18)
project(hrsc LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler warnings
add_compile_options(
    $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-Wall>
    $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-Wextra>
    $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-Wpedantic>
)
include(${CMAKE_SOURCE_DIR}/cmake/CompilerFlags.cmake)

# --- INTERFACE library for include paths ---
add_library(hrsc_core INTERFACE)
target_include_directories(hrsc_core INTERFACE ${CMAKE_SOURCE_DIR}/src)

# Precision selector: defines HRSC_REAL on hrsc_core. Must come AFTER
# add_library(hrsc_core INTERFACE) because it attaches compile defs to it.
include(${CMAKE_SOURCE_DIR}/cmake/PrecisionConfig.cmake)

# Riemann solver inequality variant: <= (default) vs < (strict)
option(RIEMANN_STRICT_INEQUALITY "Use strict < instead of <= in HLLC/HLLD" OFF)
if(RIEMANN_STRICT_INEQUALITY)
    target_compile_definitions(hrsc_core INTERFACE RIEMANN_STRICT_INEQUALITY)
endif()

# Optional CUDA path (Week 5 D.1 = toolchain smoke; Week 5 D.2 = data path;
# Week 6 = real kernels). Default OFF preserves CPU-only build behaviour.
option(ENABLE_CUDA "Enable CUDA toolchain (Week 5 GPU bring-up)" OFF)

# OpenMP parallelisation of the per-row / per-column sweep loops.
# Disable with -DENABLE_OPENMP=OFF when running under Verificarlo MCA
# (the libinterflop PRNG is not thread-safe; MCA runs must stay serial
# via OMP_NUM_THREADS=1 in any case, but turning the pragmas off at
# build time makes the intent explicit).
option(ENABLE_OPENMP "Enable OpenMP parallelisation in sweeps" ON)
option(HRSC_MSVC_OPENMP_LLVM "Use the MSVC LLVM OpenMP runtime for CPU OpenMP builds" OFF)
if(ENABLE_OPENMP)
    if(MSVC AND NOT ENABLE_CUDA AND NOT HRSC_MSVC_OPENMP_LLVM)
        message(WARNING
            "ENABLE_OPENMP=ON requested, but classic MSVC OpenMP cannot "
            "compile the existing reduction(max:...) pragmas; building "
            "serial. Configure with -DHRSC_MSVC_OPENMP_LLVM=ON to opt into "
            "/openmp:llvm for CPU OpenMP builds.")
    else()
        find_package(OpenMP)
        if(OpenMP_CXX_FOUND)
            target_link_libraries(hrsc_core INTERFACE OpenMP::OpenMP_CXX)
            if(MSVC AND NOT ENABLE_CUDA AND HRSC_MSVC_OPENMP_LLVM)
                target_compile_options(hrsc_core INTERFACE
                    $<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/openmp:llvm>)
                message(STATUS "OpenMP enabled with MSVC /openmp:llvm (${OpenMP_CXX_VERSION})")
            else()
                message(STATUS "OpenMP enabled (${OpenMP_CXX_VERSION})")
            endif()
        else()
            message(WARNING "ENABLE_OPENMP=ON but OpenMP not found; building serial")
        endif()
    endif()
endif()

# Optional per-phase wall-clock probes inside EulerSolver (Week 5 Block A).
# OFF by default: solver TU is binary-identical and cfg behaviour unchanged.
option(HRSC_ENABLE_PROFILING "Enable per-phase ScopedTimer probes in EulerSolver" OFF)
if(HRSC_ENABLE_PROFILING)
    target_compile_definitions(hrsc_core INTERFACE HRSC_ENABLE_PROFILING)
    message(STATUS "HRSC profiling probes: ON")
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
target_include_directories(hrsc PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/shock_bubble)

# --- Unit tests ---
file(GLOB TEST_SOURCES tests/unit/test_*.cpp)
add_executable(unit_tests ${TEST_SOURCES})
target_link_libraries(unit_tests PRIVATE hrsc_core hrsc_euler)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/external/catch2)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/toro_1d)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/liska_wendroff_2d)
target_include_directories(unit_tests PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/shock_bubble)

if(ENABLE_CUDA)
    include(${CMAKE_SOURCE_DIR}/cmake/CUDASetup.cmake)
    if(MSVC)
        # CUDA/MSVC host compiler compatibility workaround. Keep this opt-in
        # to CUDA builds so default CPU-only builds retain compiler defaults.
        set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} --allow-unsupported-compiler")
        target_compile_options(hrsc_core INTERFACE
            $<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/openmp:llvm>)
    endif()
    enable_language(CUDA)
    hrsc_configure_cuda_toolkit()
    target_compile_definitions(hrsc_core INTERFACE HRSC_HAS_CUDA)

    # Standalone toolchain validator. Not linked into hrsc.
    add_executable(gpu_smoke src/gpu/gpu_smoke.cu)
    target_link_libraries(gpu_smoke PRIVATE CUDA::cudart)
    set_target_properties(gpu_smoke PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
        CUDA_ARCHITECTURES "${CMAKE_CUDA_ARCHITECTURES}")

    # Day-4 GPU data path: the .cpp half is picked up by the existing
    # test_*.cpp glob; the .cu wrapper is linked only for CUDA builds.
    target_sources(unit_tests PRIVATE tests/unit/gpu_roundtrip_kernel.cu)
    set_source_files_properties(tests/unit/gpu_roundtrip_kernel.cu
        PROPERTIES LANGUAGE CUDA)
    set_target_properties(unit_tests PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
        CUDA_ARCHITECTURES "${CMAKE_CUDA_ARCHITECTURES}")
    target_link_libraries(unit_tests PRIVATE CUDA::cudart)
endif()
