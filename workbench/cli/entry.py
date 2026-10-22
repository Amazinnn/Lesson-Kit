"""Installed `lesson-kit` entry point using the shared command parser."""

from workbench.cli import main


def command_names():
    """Every top-level command exposed by the installed CLI."""
    return main.command_names()


def lesson_kit_main(argv=None):
    return main.lesson_kit_main(argv)


if __name__ == "__main__":
    raise SystemExit(lesson_kit_main())
