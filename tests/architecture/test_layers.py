"""Layer boundaries: pipeline modules depend only downwards, HTTP stays at the edge."""

import ast
from pathlib import Path

import pytest

PACKAGE_DIR = Path(__file__).resolve().parents[2] / "src" / "test_analysis"

# package → sibling packages it must never import
FORBIDDEN_IMPORTS = {
    "lab_catalog": {"extraction", "patient_card", "api", "main", "seed"},
    "extraction": {"patient_card", "api", "main", "seed"},
    "patient_card": {"api", "main", "seed"},
}


def _imported_packages(path: Path) -> set[str]:
    packages = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        for name in names:
            parts = name.split(".")
            if parts[0] == "test_analysis" and len(parts) > 1:
                packages.add(parts[1])
    return packages


@pytest.mark.parametrize("package", sorted(FORBIDDEN_IMPORTS))
def test_package_does_not_import_upper_layers(package: str) -> None:
    violations = {
        f"{path.relative_to(PACKAGE_DIR)} → {imported}"
        for path in (PACKAGE_DIR / package).rglob("*.py")
        for imported in _imported_packages(path) & FORBIDDEN_IMPORTS[package]
    }

    assert violations == set()


def test_only_main_imports_api_routes() -> None:
    importers = {
        str(path.relative_to(PACKAGE_DIR))
        for path in PACKAGE_DIR.rglob("*.py")
        if "api" in _imported_packages(path) and path.parent.name != "api"
    }

    assert importers == {"main.py"}


def test_only_openrouter_module_imports_openai_sdk() -> None:
    for path in PACKAGE_DIR.rglob("*.py"):
        if path.parent.name == "extraction" and path.name == "openrouter.py":
            continue
        source = path.read_text(encoding="utf-8")
        assert "import openai" not in source, path
