# ------------------------------------------------------------------------
# PrecisionConfig.cmake -- selects the Real type for the HRSC project.
#
# Supported: float, double.
# Quad (long double / __float128) deferred to Week 17 per overall.md:
# it needs Boost.Multiprecision or libquadmath wiring and is 1D-CPU-only.
#
# Usage:  cmake -B build -DFLOAT_PRECISION=float ...
# ------------------------------------------------------------------------

set(FLOAT_PRECISION "double" CACHE STRING
    "Floating-point precision for the solver: float | double")
set_property(CACHE FLOAT_PRECISION PROPERTY STRINGS float double)

if(NOT FLOAT_PRECISION STREQUAL "float" AND
   NOT FLOAT_PRECISION STREQUAL "double")
    message(FATAL_ERROR
        "FLOAT_PRECISION must be 'float' or 'double' (got '${FLOAT_PRECISION}')")
endif()

# Expose the choice to C++ as a compile definition, used by main.cpp:
#   using Real = HRSC_REAL;
target_compile_definitions(hrsc_core INTERFACE HRSC_REAL=${FLOAT_PRECISION})
target_compile_definitions(hrsc_core INTERFACE HRSC_PRECISION_NAME="${FLOAT_PRECISION}")

message(STATUS "HRSC precision: ${FLOAT_PRECISION}")
