from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FLAGS = ROOT / "cmake" / "CompilerFlags.cmake"
CMAKE_LISTS = ROOT / "CMakeLists.txt"
SEMANTICS_TEMPLATE = ROOT / "cmake" / "build_semantics.json.in"


def test_optimisation_axis_maps_flags_per_compiler():
    text = FLAGS.read_text(encoding="utf-8")

    assert 'add_compile_options("-${OPT_LEVEL}")' not in text
    assert 'CMAKE_CXX_COMPILER_ID STREQUAL "MSVC"' in text
    assert 'CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|AppleClang"' in text
    assert 'OPT_LEVEL STREQUAL "Ofast"' in text
    assert "/Ox" in text
    assert "/fp:fast" in text
    assert 'set(_hrsc_opt_flags "-${OPT_LEVEL}")' in text


def test_fast_math_axis_maps_flags_per_compiler():
    text = FLAGS.read_text(encoding="utf-8")

    assert "add_compile_options(-ffast-math)" not in text
    assert "FAST_MATH" in text
    assert "/fp:fast" in text
    assert "-ffast-math" in text


def test_compiler_flags_record_effective_math_semantics():
    text = FLAGS.read_text(encoding="utf-8")

    assert "HRSC_EFFECTIVE_MATH_MODE" in text
    assert 'OPT_LEVEL STREQUAL "Ofast"' in text
    assert "elseif(FAST_MATH OR OPT_LEVEL STREQUAL \"Ofast\")" in text
    assert "if(STRICT_IEEE)" in text
    assert "HRSC_STRICT_IEEE_FLAG_EVIDENCE" in text


def test_cmake_configures_valid_json_build_semantics_template():
    cmake_text = CMAKE_LISTS.read_text(encoding="utf-8")
    template = SEMANTICS_TEMPLATE.read_text(encoding="utf-8")

    assert "file(TO_CMAKE_PATH \"${CMAKE_CXX_COMPILER}\" HRSC_CXX_COMPILER_JSON_PATH)" in cmake_text
    assert "configure_file(" in cmake_text
    assert "cmake/build_semantics.json.in" in cmake_text
    assert '"fast_math": @HRSC_FAST_MATH_JSON@' in template
    assert '"strict_ieee": @HRSC_STRICT_IEEE_JSON@' in template
    assert '"effective_math_mode": "@HRSC_EFFECTIVE_MATH_MODE@"' in template
