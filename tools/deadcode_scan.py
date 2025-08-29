"""
Lightweight dead code inspection for this repo.

Heuristics only:
- Finds top-level functions/classes in `src/` and flags those whose names
  are never referenced anywhere in `src/` or `tests/` (by identifier or attribute).
- Flags per-file unused imports (simple name-based check).

Limitations:
- Name-based only; dynamic usage, reflection, string-based lookups won't be detected.
- Attribute name matches are module-agnostic and may yield false positives/negatives.
- Star imports and re-exports are ignored.

Run: `python tools/deadcode_scan.py`
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TESTS = ROOT / "tests"


def iter_py_files(base: Path) -> Iterable[Path]:
    for dirpath, _dirnames, filenames in os.walk(base):
        for fn in filenames:
            if fn.endswith(".py"):
                yield Path(dirpath) / fn


def module_name_for(path: Path) -> Optional[str]:
    try:
        rel = path.relative_to(SRC)
    except ValueError:
        return None
    parts = list(rel.with_suffix("").parts)
    if not parts:
        return None
    return ".".join(parts)


@dataclass
class Symbol:
    kind: str  # 'func' | 'class' | 'method'
    module: str
    name: str
    filepath: Path
    lineno: int


class CollectUses(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: Set[str] = set()
        self.attrs: Set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        self.names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802
        # Record attribute name usage (e.g., module.func, obj.method)
        self.attrs.add(node.attr)
        self.generic_visit(node)


class CollectDefs(ast.NodeVisitor):
    def __init__(self, module: str, filepath: Path) -> None:
        self.module = module
        self.filepath = filepath
        self.symbols: List[Symbol] = []
        self._class_stack: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.symbols.append(Symbol("class", self.module, node.name, self.filepath, node.lineno))
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        if self._class_stack:
            qual = f"{self._class_stack[-1]}.{node.name}"
            self.symbols.append(Symbol("method", self.module, qual, self.filepath, node.lineno))
        else:
            self.symbols.append(Symbol("func", self.module, node.name, self.filepath, node.lineno))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.visit_FunctionDef(node)  # treat same as sync


class CollectImports(ast.NodeVisitor):
    def __init__(self) -> None:
        self.bound_names: Set[str] = set()
        self.imported_modules: Set[str] = set()  # for module import graph

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            # Binding name is the top-level package unless aliased
            bound = alias.asname or alias.name.split(".")[0]
            self.bound_names.add(bound)
            self.imported_modules.add(alias.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module is None:
            return
        top = node.module.split(".")[0]
        self.imported_modules.add(top)
        for alias in node.names:
            if alias.name == "*":
                continue
            bound = alias.asname or alias.name
            self.bound_names.add(bound)


def parse(path: Path) -> Optional[ast.AST]:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception:
        return None


def main() -> None:
    # Index definitions in src/
    defs: List[Symbol] = []
    src_files = list(iter_py_files(SRC))
    for f in src_files:
        mod = module_name_for(f)
        if not mod:
            continue
        tree = parse(f)
        if not tree:
            continue
        cd = CollectDefs(mod, f)
        cd.visit(tree)
        defs.extend(cd.symbols)

    # Gather usages across src/ and tests/
    global_names: Set[str] = set()
    global_attrs: Set[str] = set()
    module_used_names: Dict[Path, Set[str]] = {}
    module_used_attrs: Dict[Path, Set[str]] = {}
    imported_modules_by: Dict[str, Set[str]] = {}

    all_files = src_files + list(iter_py_files(TESTS))
    for f in all_files:
        tree = parse(f)
        if not tree:
            continue
        uses = CollectUses()
        uses.visit(tree)
        global_names |= uses.names
        global_attrs |= uses.attrs
        module_used_names[f] = uses.names
        module_used_attrs[f] = uses.attrs

        # import graph
        ci = CollectImports()
        ci.visit(tree)
        for mod in ci.imported_modules:
            imported_modules_by.setdefault(mod, set()).add(str(f))

    # Per-file unused imports
    per_file_unused_imports: Dict[Path, List[str]] = {}
    for f in src_files:
        tree = parse(f)
        if not tree:
            continue
        ci = CollectImports()
        ci.visit(tree)
        # Skip package __init__.py re-export modules and __future__ imports
        if f.name == "__init__.py":
            continue
        used = module_used_names.get(f, set())
        unused: List[str] = []
        for name in ci.bound_names:
            if name == "annotations":  # from __future__ import annotations
                continue
            if name not in used:
                unused.append(name)
        unused.sort()
        if unused:
            per_file_unused_imports[f] = unused

    # Candidates: top-level funcs/classes whose names are never referenced
    dead_funcs: List[Symbol] = []
    dead_classes: List[Symbol] = []
    # For methods, too noisy; compute but keep separate
    dead_methods: List[Symbol] = []

    for sym in defs:
        name = sym.name
        # Break out class method names into the method part for attribute matching
        method_part = name.split(".")[-1]
        used = (name in global_names) or (method_part in global_attrs) or (method_part in global_names)
        # Allow dunder and private names to be ignored in dead-code reporting
        if sym.kind == "func":
            if (not used) and not name.startswith("__"):
                dead_funcs.append(sym)
        elif sym.kind == "class":
            if (not used) and not name.startswith("__"):
                dead_classes.append(sym)
        elif sym.kind == "method":
            if (not used) and not method_part.startswith("__"):
                dead_methods.append(sym)

    # Modules under our namespace that are never imported by others (excluding __main__)
    src_modules = set()
    for f in src_files:
        mod = module_name_for(f)
        if mod:
            src_modules.add(mod.split(".")[0])
    never_imported_modules = [
        m for m in sorted(src_modules)
        if m != "__main__" and not imported_modules_by.get(m)
    ]

    # Report
    print("== Dead code candidates (heuristic) ==")
    print(f"Top-level functions: {len(dead_funcs)}")
    for s in sorted(dead_funcs, key=lambda x: (x.filepath.as_posix(), x.lineno)):
        rel = s.filepath.relative_to(ROOT).as_posix()
        print(f"  - {rel}:{s.lineno}  {s.module}.{s.name}")

    print(f"\nClasses: {len(dead_classes)}")
    for s in sorted(dead_classes, key=lambda x: (x.filepath.as_posix(), x.lineno)):
        rel = s.filepath.relative_to(ROOT).as_posix()
        print(f"  - {rel}:{s.lineno}  {s.module}.{s.name}")

    if dead_methods:
        print(f"\nMethods (no references found): {len(dead_methods)}")
        # Show only first 20 to limit noise
        shown = 0
        for s in sorted(dead_methods, key=lambda x: (x.filepath.as_posix(), x.lineno)):
            rel = s.filepath.relative_to(ROOT).as_posix()
            print(f"  - {rel}:{s.lineno}  {s.module}.{s.name}")
            shown += 1
            if shown >= 20:
                print("    ... (truncated)")
                break

    print("\n== Unused imports (per file) ==")
    if not per_file_unused_imports:
        print("  None found")
    else:
        for f, names in sorted(per_file_unused_imports.items(), key=lambda x: x[0].as_posix()):
            rel = f.relative_to(ROOT).as_posix()
            print(f"  - {rel}: {', '.join(names)}")

    if never_imported_modules:
        print("\n== Modules never imported by others ==")
        for m in never_imported_modules:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
