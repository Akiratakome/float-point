import json
import shutil
import subprocess
from pathlib import Path

import pytest


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


@pytest.mark.parametrize(
    ("opt_level", "fast_math", "strict_ieee", "expected_mode"),
    [
        ("Ofast", False, False, "fast"),
        ("O2", True, False, "fast"),
        ("Ofast", True, True, "strict"),
    ],
)
def test_cmake_configure_generates_valid_build_semantics(
    tmp_path: Path,
    opt_level: str,
    fast_math: bool,
    strict_ieee: bool,
    expected_mode: str,
) -> None:
    cmake = shutil.which("cmake")
    if cmake is None:
        pytest.skip("CMake is unavailable")

    build_dir = tmp_path / f"build-{opt_level}-{fast_math}-{strict_ieee}"
    command = [
        cmake,
        "-S",
        str(ROOT),
        "-B",
        str(build_dir),
        "-DFLOAT_PRECISION=double",
        "-DENABLE_OPENMP=OFF",
        f"-DOPT_LEVEL={opt_level}",
        f"-DFAST_MATH={'ON' if fast_math else 'OFF'}",
        f"-DSTRICT_IEEE={'ON' if strict_ieee else 'OFF'}",
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)

    semantics = json.loads((build_dir / "build_semantics.json").read_text(encoding="utf-8"))
    assert semantics["schema"] == {"name": "hrsc.build-semantics", "version": 1}
    assert semantics["requested"] == {
        "opt_level": opt_level,
        "fast_math": fast_math,
        "strict_ieee": strict_ieee,
    }
    assert semantics["effective_math_mode"] == expected_mode
    assert isinstance(semantics["compiler"]["id"], str) and semantics["compiler"]["id"]
    assert isinstance(semantics["compiler"]["version"], str) and semantics["compiler"]["version"]
    assert isinstance(semantics["compiler"]["path"], str) and semantics["compiler"]["path"]
    assert "\\" not in semantics["compiler"]["path"]
