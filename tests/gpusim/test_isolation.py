import ast
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GPUSIM_DIR = REPO_ROOT / "openubem/gpusim"
S0_HEADER = GPUSIM_DIR / "backends/kernel/s0_common.h"

CARRY_LIST: tuple[Path, ...] = (
    REPO_ROOT / "openubem/gpusim",
    REPO_ROOT / "scripts/gpusim",
    REPO_ROOT / "tests/gpusim",
    REPO_ROOT / "tests/fixtures/gpusim",
    REPO_ROOT / "docs/docs_DONE/SETUP/GPU_based_compute",
)


def _find_forbidden_imports(py_path: Path) -> list[str]:
    """Return any imports in ``py_path`` referencing ``openubem`` outside ``gpusim``.

    Args:
        py_path: Python source file under ``openubem/gpusim``.

    Returns:
        List of human-readable violation strings; empty if isolated.
    """
    tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    rel = py_path.relative_to(GPUSIM_DIR)
    pkg_depth = len(rel.parts) - 1 if rel.name != "__init__.py" else len(rel.parts) - 1
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == "openubem" or (
                    name.startswith("openubem.")
                    and name != "openubem.gpusim"
                    and not name.startswith("openubem.gpusim.")
                ):
                    violations.append(f"{rel}:{node.lineno}: import {name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level == 0:
                if mod == "openubem":
                    for alias in node.names:
                        if alias.name != "gpusim":
                            violations.append(
                                f"{rel}:{node.lineno}: "
                                f"from openubem import {alias.name}"
                            )
                elif (
                    mod.startswith("openubem.")
                    and mod != "openubem.gpusim"
                    and not mod.startswith("openubem.gpusim.")
                ):
                    violations.append(f"{rel}:{node.lineno}: from {mod} import ...")
            else:
                max_up = pkg_depth + 1
                if node.level > max_up:
                    violations.append(
                        f"{rel}:{node.lineno}: relative import escapes gpusim "
                        f"(level={node.level}, depth={pkg_depth}, module={mod})"
                    )
    return violations


def test_gpusim_imports_isolated() -> None:
    """Assert modules under ``openubem/gpusim`` import only ``openubem.gpusim``."""
    py_files = sorted(GPUSIM_DIR.rglob("*.py"))
    assert len(py_files) > 0, "Expected Python modules under openubem/gpusim"

    all_violations: list[str] = []
    for py_path in py_files:
        all_violations.extend(_find_forbidden_imports(py_path))

    assert not all_violations, (
        "Found imports outside openubem.gpusim:\n" + "\n".join(all_violations)
    )


def test_s0_common_header_compiles_with_clang() -> None:
    """Assert ``s0_common.h`` compiles cleanly as C++17 host code with clang++."""
    assert S0_HEADER.is_file(), f"Missing header {S0_HEADER}"
    proc = subprocess.run(
        [
            "clang++",
            "-std=c++17",
            "-fsyntax-only",
            "-x",
            "c++",
            "-DGPUSIM_HOST",
            str(S0_HEADER),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"clang++ exited {proc.returncode}:\n{proc.stderr}\n{proc.stdout}"
    )


def test_carry_list_directories_exist() -> None:
    """Assert every Windows migration carry-list directory exists."""
    missing = [str(p) for p in CARRY_LIST if not p.is_dir()]
    assert not missing, f"Missing carry-list directories: {missing}"
