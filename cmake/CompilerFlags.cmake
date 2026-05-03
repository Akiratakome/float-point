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

# --- Week 6: strict-IEEE pathway ---
#
# STRICT_IEEE=ON is opt-in. It pins the FP rounding model on both CPU and
# (when ENABLE_CUDA=ON) on nvcc, so CPU-vs-GPU same-precision diffs
# stay within the K.ULP bounds of docs/week6/week6-design.md Section 4.5.
#
# Explicit semantics:
#   -ffp-contract=off      : forbid the compiler from fusing a*b+c into FMA
#   -fno-fast-math         : disable the fast-math umbrella
#   -fexcess-precision=standard : prevent x87 80-bit intermediate widening
#   -fno-unsafe-math-optimizations : kills associativity tricks
#   -fno-strict-aliasing   : protects bit-pattern punning paths in regression
#   nvcc --fmad=false      : forbid implicit single-rounding FMA
#   nvcc --ftz=false       : keep denormals (no flush-to-zero)
#   nvcc --prec-div=true   : IEEE-compliant divide
#   nvcc --prec-sqrt=true  : IEEE-compliant sqrt
#
# Existing OPT_LEVEL / FAST_MATH behaviour is unchanged.

option(STRICT_IEEE "Force strict-IEEE FP flags on CPU (and CUDA if enabled)" OFF)

function(_hrsc_compile_option_scope target out_var)
    get_target_property(_hrsc_target_type ${target} TYPE)
    if(_hrsc_target_type STREQUAL "INTERFACE_LIBRARY")
        set(${out_var} INTERFACE PARENT_SCOPE)
    else()
        set(${out_var} PRIVATE PARENT_SCOPE)
    endif()
endfunction()

function(hrsc_apply_strict_ieee_cpu target)
    _hrsc_compile_option_scope(${target} _hrsc_scope)
    target_compile_options(${target} ${_hrsc_scope}
        $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-O2>
        $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-ffp-contract=off>
        $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-fno-fast-math>
        $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-fexcess-precision=standard>
        $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-fno-unsafe-math-optimizations>
        $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-fno-strict-aliasing>
        $<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/O2>
        $<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/fp:strict>
        $<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/Oi->
    )
endfunction()

function(hrsc_apply_strict_ieee_cuda target)
    _hrsc_compile_option_scope(${target} _hrsc_scope)
    target_compile_options(${target} ${_hrsc_scope}
        "$<$<COMPILE_LANGUAGE:CUDA>:--fmad=false;--ftz=false;--prec-div=true;--prec-sqrt=true>"
        "$<$<AND:$<COMPILE_LANGUAGE:CUDA>,$<CXX_COMPILER_ID:GNU,Clang,AppleClang>>:-Xcompiler=-O2;-Xcompiler=-ffp-contract=off;-Xcompiler=-fno-fast-math;-Xcompiler=-fexcess-precision=standard;-Xcompiler=-fno-unsafe-math-optimizations;-Xcompiler=-fno-strict-aliasing>"
        "$<$<AND:$<COMPILE_LANGUAGE:CUDA>,$<CXX_COMPILER_ID:MSVC>>:-Xcompiler=/O2;-Xcompiler=/fp:strict;-Xcompiler=/Oi->"
    )
endfunction()
