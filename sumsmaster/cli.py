"""Command-line entry point for sumsmaster."""

from __future__ import annotations

import argparse
import contextlib
import sys

from sumsmaster import coverage as coverage_mod
from sumsmaster.__about__ import __version__


def _force_utf8_stdout() -> None:
    # Windows consoles default to cp1252 and choke on the unicode characters
    # we use in trick names and explanations. Reconfigure stdout to UTF-8
    # with replacement so output never crashes the program.
    with contextlib.suppress(AttributeError, ValueError):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]


def main() -> None:
    """Run the sumsmaster CLI."""
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(
        prog="sumsmaster",
        description="Trick-aware mental arithmetic — phase 0 toolkit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser(
        "coverage",
        help="report what fraction of the elementary fact space is covered by >=1 trick",
    )
    sub.add_parser(
        "tricks",
        help="list every defined trick grouped by operation",
    )
    sub.add_parser(
        "gui",
        help="launch the graphical app (profiles, practice, progress)",
    )

    args = parser.parse_args()

    if args.command == "coverage":
        print(coverage_mod.default_report())
    elif args.command == "tricks":
        print(coverage_mod.trick_summary())
    elif args.command == "gui":
        from sumsmaster.gui import launch

        sys.exit(launch())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
