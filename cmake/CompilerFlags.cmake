# Optional compiler-flag axes for experiment builds.
#
# Defaults intentionally preserve the existing CMake behavior. Flags are only
# changed when an experiment script passes OPT_LEVEL and/or FAST_MATH.

set(OPT_LEVEL "" CACHE STRING "Optional optimisation axis: O2 | O3 | Ofast")
set_property(CACHE OPT_LEVEL PROPERTY STRINGS "" O2 O3 Ofast)

option(FAST_MATH "Enable fast-math flags for experiment builds" OFF)

if(OPT_LEVEL)
    if(NOT OPT_LEVEL STREQUAL "O2" AND
       NOT OPT_LEVEL STREQUAL "O3" AND
       NOT OPT_LEVEL STREQUAL "Ofast")
        message(FATAL_ERROR "OPT_LEVEL must be O2, O3, or Ofast (got '${OPT_LEVEL}')")
    endif()
    add_compile_options("-${OPT_LEVEL}")
    message(STATUS "HRSC optimisation axis: -${OPT_LEVEL}")
endif()

if(FAST_MATH)
    add_compile_options(-ffast-math)
    message(STATUS "HRSC fast-math axis: enabled")
endif()
