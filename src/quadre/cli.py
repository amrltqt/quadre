from __future__ import annotations



import logging

import argparse
import os
import sys
from typing import Optional


from quadre.components import component_discovery
from quadre.generator import generate_image
from quadre.theme import builtin_theme_path
from quadre.models import DocumentDef


logger = logging.getLogger(__name__)


def _apply_theme_arg(theme_arg: Optional[str]) -> Optional[int]:
    if not theme_arg:
        return None
    theme_arg = theme_arg.strip()
    # Map known aliases to bundled themes
    if theme_arg.lower() in ("dark", "light", "default"):
        path = builtin_theme_path(theme_arg)
    else:
        path = (
            builtin_theme_path(theme_arg)
            if not ("/" in theme_arg or "\\" in theme_arg or theme_arg.endswith(".json"))
            else None
        )
        if path is None:
            path = theme_arg  # treat as explicit path
    if not os.path.exists(str(path)):
        logger.error(f"Theme not found: {path}")
        return 2
    os.environ["quadre_THEME"] = str(path)
    return None


def cmd_render(args: argparse.Namespace) -> int:

    # Register components before rendering
    component_discovery()

    # Handle theme selection before reading/validating JSON
    rc = _apply_theme_arg(args.theme)
    if rc:
        return rc

    logger.info("Start rendering process", extra={
        "input_file": args.input
    })

    with open(args.input, "r", encoding="utf-8") as f:
        # Read the whole document and validate it
        doc = DocumentDef.model_validate_json(f.read())
        logger.debug("Document loaded", extra={
            "number_of_components": len(doc.components)
        })
        try:
            surface = generate_image(doc)
            surface.write_to_png(args.output)
            print(f"Wrote {args.output}")
            return 0
        except Exception:
            logger.exception("Render failed")
            return 1



def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="quadre",
        description="Quadre CLI (render | validate)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("render", help="Render JSON to PNG")
    pr.add_argument("input", help="Input JSON file")
    pr.add_argument("output", nargs="?", default="dashboard.png", help="Output PNG file")
    pr.add_argument("--no-validate", action="store_true", help="Skip JSON validation")
    pr.add_argument("--theme", help="Theme to use: 'dark' | 'light' | path/to/theme.json")
    pr.set_defaults(func=cmd_render)


    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    code = args.func(args)
    sys.exit(code)


if __name__ == "__main__":
    main()
