"""Tkinter front end for the free, self-hosted edition.

The GUI surfaces the phase-0 toolkit (trick browser, coverage report) plus
the first learner-facing loop: local unauthenticated profiles, plan
selection, trick-weighted practice sessions, progress tracking, and resume.

Everything except :mod:`sumsmaster.gui.app` is pure logic with no tkinter
import, so profiles/plans/practice are testable headless.
"""

from __future__ import annotations


def launch() -> int:
    """Start the GUI. Returns a process exit code.

    Imports tkinter lazily so `sumsmaster coverage` etc. keep working on
    systems without a Tk build (e.g. Debian minus python3-tk).
    """
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print(
            "sumsmaster gui requires tkinter, which is missing from this "
            "Python.\nOn Debian/Ubuntu: sudo apt install python3-tk"
        )
        return 1

    from sumsmaster.gui.app import App

    App().mainloop()
    return 0


__all__ = ["launch"]
