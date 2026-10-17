"""
Prueba de arquitectura hexagonal: verifica la dirección de las dependencias entre capas.
Falla si alguien importa un framework en el Core o conecta adaptadores al composition root.
"""

import ast
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
ROOT_MODULES = {"app.container", "app.main", "app.config"}


def imports_of(path: Path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"{path}: usa imports absolutos (from app...), no relativos"
            yield node.module


def modules_in(layer: str):
    return [(p.relative_to(APP.parent), list(imports_of(p))) for p in (APP / layer).rglob("*.py")]


def violations(layer, is_forbidden):
    return [f"{path} -> {module}" for path, modules in modules_in(layer) for module in modules if is_forbidden(module)]


def test_core_only_depends_on_stdlib_and_itself():
    def forbidden(module):
        top = module.split(".")[0]
        return not (module.startswith("app.core") or top in sys.stdlib_module_names)

    assert violations("core", forbidden) == []


def test_domain_is_the_innermost_layer():
    """El dominio no conoce puertos ni casos de uso: evita ciclos domain <-> ports."""
    assert violations("core/domain", lambda m: m.startswith(("app.core.ports", "app.core.use_cases"))) == []


def test_ports_do_not_depend_on_use_cases():
    assert violations("core/ports", lambda m: m.startswith("app.core.use_cases")) == []


@pytest.mark.parametrize("layer", ["adapters", "core"])
def test_layers_do_not_import_composition_root(layer):
    assert violations(layer, lambda m: m in ROOT_MODULES) == []


def test_outbound_adapters_do_not_depend_on_inbound():
    assert violations("adapters/outbound", lambda m: m.startswith("app.adapters.inbound")) == []


def test_inbound_adapters_do_not_depend_on_outbound():
    """Los adaptadores de entrada reciben implementaciones por inyección, nunca las importan."""
    assert violations("adapters/inbound", lambda m: m.startswith("app.adapters.outbound")) == []


def test_whole_app_uses_absolute_imports():
    for path in APP.rglob("*.py"):
        list(imports_of(path))
