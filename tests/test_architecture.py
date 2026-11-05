import ast
from importlib.util import resolve_name
from pathlib import Path
from sys import stdlib_module_names

import pytest


@pytest.mark.parametrize("layer", ["domain", "application"])
def test_inner_layers_only_import_stable_dependencies(layer: str) -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "arc"
    allowed_layers = ("arc.domain",) if layer == "domain" else ("arc.domain", "arc.application")
    for path in (root / layer).rglob("*.py"):
        package = ".".join(("arc", *path.relative_to(root).parts[:-1]))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                module = resolve_name("." * node.level + (node.module or ""), package)
                imports = (
                    [module] if module != "arc" else [f"arc.{alias.name}" for alias in node.names]
                )
            else:
                continue
            for name in imports:
                assert name.split(".")[0] in stdlib_module_names or any(
                    name == allowed or name.startswith(allowed + ".") for allowed in allowed_layers
                ), f"{path.name}:{node.lineno} imports forbidden dependency {name}"
