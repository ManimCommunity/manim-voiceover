import importlib.util
from pathlib import Path

import pytest


def _load_collect_failures():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "check_mutmut_results.py"
    if not script_path.exists():
        pytest.skip("check_mutmut_results.py is not copied into mutmut's temporary test tree.")
    spec = importlib.util.spec_from_file_location("check_mutmut_results", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.collect_failures


def test_collect_failures_includes_partial_and_unstable_statuses():
    collect_failures = _load_collect_failures()
    output = "\n".join(
        [
            "package.module.x_mutant_1: killed",
            "package.module.x_mutant_2: survived",
            "package.module.x_mutant_3: timeout",
            "package.module.x_mutant_4: no tests",
            "package.module.x_mutant_5: suspicious",
            "package.module.x_mutant_6: not checked",
        ]
    )

    assert collect_failures(output) == [
        ("package.module.x_mutant_2", "survived"),
        ("package.module.x_mutant_3", "timeout"),
        ("package.module.x_mutant_4", "no tests"),
        ("package.module.x_mutant_5", "suspicious"),
        ("package.module.x_mutant_6", "not checked"),
    ]
