from __future__ import annotations

import argparse
import json
import sys

from .main import render_dashboard
from .theme import builtin_theme_path
import os
from .validator import validate_layout


def cmd_render(args: argparse.Namespace) -> int:
    # Handle theme selection before reading/validating JSON
    if args.theme:
        theme_arg = args.theme.strip()
        # Map known aliases to bundled themes
        if theme_arg.lower() in ("dark", "light", "default"):
            path = builtin_theme_path(theme_arg)
        else:
            path = builtin_theme_path(theme_arg) if not ("/" in theme_arg or "\\" in theme_arg or theme_arg.endswith('.json')) else None
            if path is None:
                path = theme_arg  # treat as explicit path
        if not os.path.exists(str(path)):
            print(f"[ERROR] Theme not found: {path}")
            return 2
        os.environ["NADA_THEME"] = str(path)
    with open(args.input, "r", encoding="utf-8") as f:
        doc = json.load(f)

    if not args.no_validate:
        errors, warnings = validate_layout(doc)
        for w in warnings:
            print(f"[WARN] {w}")
        if errors:
            for e in errors:
                print(f"[ERROR] {e}")
            return 2

    try:
        render_dashboard(doc, args.output)
        print(f"Wrote {args.output}")
        return 0
    except Exception as e:
        print(f"Render failed: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    with open(args.input, "r", encoding="utf-8") as f:
        doc = json.load(f)
    errors, warnings = validate_layout(doc)
    for w in warnings:
        print(f"[WARN] {w}")
    if errors:
        for e in errors:
            print(f"[ERROR] {e}")
        return 1
    print("OK: document is valid")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nada",
        description="NADA CLI (render | validate)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("render", help="Render JSON to PNG")
    pr.add_argument("input", help="Input JSON file")
    pr.add_argument("output", nargs="?", default="dashboard.png", help="Output PNG file")
    pr.add_argument("--no-validate", action="store_true", help="Skip JSON validation")
    pr.add_argument("--theme", help="Theme to use: 'dark' | 'light' | path/to/theme.json")
    pr.set_defaults(func=cmd_render)

    pv = sub.add_parser("validate", help="Validate JSON document")
    pv.add_argument("input", help="Input JSON file")
    pv.set_defaults(func=cmd_validate)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    code = args.func(args)
    sys.exit(code)


if __name__ == "__main__":
    main()
