"""Module boundary and circular import validation tests.

Enforces clean architectural boundaries:
- No circular dependencies between app packages
- Shared layer (models, contracts, config, database) does not import service or router layers
- Services do not depend on routers
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

import pytest

import app


def _get_all_app_modules() -> list[str]:
    """Discover all Python modules and subpackages inside the `app` package."""
    package = app
    modules: list[str] = [package.__name__]

    if not hasattr(package, "__path__"):
        return modules

    prefix = f"{package.__name__}."
    for _, module_name, _is_pkg in pkgutil.walk_packages(package.__path__, prefix):
        modules.append(module_name)
    return modules


class ImportVisitor(ast.NodeVisitor):
    """AST visitor that collects imported module names from a Python source file."""

    def __init__(self, current_module: str) -> None:
        self.current_module = current_module
        self.imports: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level > 0:
            # Relative import: resolve base module
            parts = self.current_module.split(".")
            base_parts = parts[: -node.level]
            if node.module:
                full_name = ".".join([*base_parts, node.module])
            else:
                full_name = ".".join(base_parts)
            self.imports.add(full_name)
        elif node.module:
            self.imports.add(node.module)
        self.generic_visit(node)


def _build_app_import_graph() -> dict[str, set[str]]:
    """Build an adjacency map of app module -> set of imported app modules."""
    app_root = Path(app.__file__).parent
    graph: dict[str, set[str]] = {}

    for py_file in app_root.rglob("*.py"):
        rel_parts = py_file.relative_to(app_root.parent).with_suffix("").parts
        mod_name = ".".join(rel_parts)

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError:
            continue

        visitor = ImportVisitor(mod_name)
        visitor.visit(tree)

        # Filter only internal `app.*` dependencies
        internal_deps = {
            dep for dep in visitor.imports if dep == "app" or dep.startswith("app.")
        }
        graph[mod_name] = internal_deps

    return graph


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Detect cycles in import graph using DFS traversal."""
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> list[str] | None:
        visited.add(node)
        stack.append(node)

        for neighbor in graph.get(node, set()):
            # Direct module match or parent module match
            matched = neighbor if neighbor in graph else None
            if not matched:
                # E.g. neighbor is `app.shared.models.Event` -> check `app.shared.models`
                parts = neighbor.split(".")
                while len(parts) > 1:
                    candidate = ".".join(parts)
                    if candidate in graph:
                        matched = candidate
                        break
                    parts.pop()

            if matched:
                if matched in stack:
                    cycle_start = stack.index(matched)
                    return [*stack[cycle_start:], matched]
                if matched not in visited:
                    cycle = dfs(matched)
                    if cycle:
                        return cycle

        stack.pop()
        return None

    for node in list(graph.keys()):
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None


# ==============================================================================
# Tests
# ==============================================================================


def test_no_circular_imports_in_entire_app() -> None:
    """Every module inside `app` can be imported without circular dependency errors."""
    modules = _get_all_app_modules()
    assert len(modules) > 5

    # Test that each module imports cleanly
    for mod_name in modules:
        try:
            mod = importlib.import_module(mod_name)
            assert mod is not None
        except Exception as exc:
            pytest.fail(f"Circular import or import failure on {mod_name}: {exc}")


def test_import_graph_has_no_cycles() -> None:
    """Static AST import graph has no circular import cycles."""
    graph = _build_app_import_graph()
    cycle = _find_cycle(graph)
    assert cycle is None, f"Circular import cycle detected: {' -> '.join(cycle)}"


def test_shared_layer_does_not_depend_on_services_or_routers() -> None:
    """app.shared (contracts and models) must never import from service or router layers."""
    graph = _build_app_import_graph()

    forbidden_prefixes = (
        "app.users.service",
        "app.users.router",
        "app.events.service",
        "app.events.router",
        "app.budgets.service",
        "app.budgets.router",
        "app.timeline.service",
        "app.timeline.router",
        "app.vendors.service",
        "app.vendors.router",
        "app.guests.service",
        "app.guests.router",
        "app.ai.router",
    )

    shared_modules = [m for m in graph if m.startswith("app.shared")]
    assert len(shared_modules) > 0

    for mod in shared_modules:
        deps = graph[mod]
        for dep in deps:
            for forbidden in forbidden_prefixes:
                assert not dep.startswith(forbidden), (
                    f"Boundary violation: {mod} imports forbidden higher-level module {dep}"
                )


def test_services_do_not_depend_on_routers() -> None:
    """Business logic services must never import from presentation routers."""
    graph = _build_app_import_graph()

    service_modules = [m for m in graph if m.endswith(".service")]
    assert len(service_modules) >= 5

    for mod in service_modules:
        deps = graph[mod]
        for dep in deps:
            assert not dep.endswith(".router") and ".router." not in dep, (
                f"Boundary violation: Service {mod} imports router {dep}"
            )
