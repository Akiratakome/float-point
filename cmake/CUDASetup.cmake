# cmake/CUDASetup.cmake
#
# Configures CMAKE_CUDA_ARCHITECTURES before CUDA language enablement, then
# locates CUDAToolkit after enable_language(CUDA).
#
# Policy CMP0104 is automatically NEW because the root CMakeLists.txt requires
# CMake >= 3.18 (which sets CMP0104 to NEW by default). If anyone lowers the
# minimum below 3.18 in the future, add `cmake_policy(SET CMP0104 NEW)` here
# to prevent cryptic nvcc target-architecture errors.

# Auto-detect architectures; fall back to "native" (CMake 3.24+) or a sane
# default for older CMake. "native" lets nvcc target the GPU on this host.
if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    if(CMAKE_VERSION VERSION_GREATER_EQUAL "3.24")
        set(CMAKE_CUDA_ARCHITECTURES native CACHE STRING
            "CUDA architectures (native = detect host GPU)")
    else()
        # Conservative default: cover Pascal+Volta+Turing+Ampere; user can override.
        set(CMAKE_CUDA_ARCHITECTURES "60;70;75;80" CACHE STRING
            "CUDA architectures")
    endif()
endif()

function(hrsc_configure_cuda_toolkit)
    find_package(CUDAToolkit REQUIRED)

    message(STATUS "CUDA Toolkit: ${CUDAToolkit_VERSION} at ${CUDAToolkit_LIBRARY_DIR}")
    message(STATUS "CUDA architectures: ${CMAKE_CUDA_ARCHITECTURES}")
endfunction()
