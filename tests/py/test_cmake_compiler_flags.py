from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FLAGS = ROOT / "cmake" / "CompilerFlags.cmake"


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
