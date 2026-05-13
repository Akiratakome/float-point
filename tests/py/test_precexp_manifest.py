from scripts.verificarlo.precexp_manifest import build_manifest


def test_build_manifest_contains_required_function_groups() -> None:
    manifest = build_manifest(cases=["sod"], solvers=["hllc"])
    groups = {entry["component"] for entry in manifest["candidate_symbols"]}
    assert {"muscl", "hancock", "flux", "eos", "cfl"}.issubset(groups)
    assert manifest["cases"] == ["sod"]
    assert manifest["solvers"] == ["hllc"]
    assert manifest["output_root"] == "experiments/week7/vfc_precexp"
