"""Installed `lesson-kit` entry point with small extension dispatch."""

import sys


EXTENSION_COMMANDS = {"experience", "mirror"}


def command_names():
    """Every top-level command exposed by the installed `lesson-kit` entry point."""
    from workbench.cli import main
    return sorted(set(main.command_names()) | EXTENSION_COMMANDS)


def lesson_kit_main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "experience":
        from workbench.cli import experience
        return experience.main(args[1:], prog="lesson-kit experience")
    if args and args[0] == "mirror":
        from workbench.cli import mirror
        return mirror.main(args[1:], prog="lesson-kit mirror")
    from workbench.cli import main
    return main.lesson_kit_main(args)


if __name__ == "__main__":
    raise SystemExit(lesson_kit_main())
