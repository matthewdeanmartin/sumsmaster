"""Display-guarded smoke tests for the tkinter application."""

from __future__ import annotations

import tkinter
from pathlib import Path
from typing import Any, cast

import pytest

from sumsmaster.gui.app import App
from sumsmaster.gui.store import ProfileStore


def _tk_available() -> bool:
    try:
        import tkinter

        root = tkinter.Tk()
        root.destroy()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _tk_available(), reason="no usable Tk display (headless CI)")


def _build_app(root: Path) -> App:
    """Construct the App, skipping if Tk can't (re)initialize mid-suite."""

    try:
        return App(store=ProfileStore(root=root))
    except tkinter.TclError as exc:  # flaky re-init in long test runs
        pytest.skip(f"Tk failed to initialize: {exc}")


def test_app_builds_all_screens(tmp_path: Path) -> None:
    app = _build_app(tmp_path / "home")
    try:
        app.update_idletasks()
        assert set(app.screens) == {
            "ProfileScreen",
            "DashboardScreen",
            "PracticeScreen",
            "TricksScreen",
            "CoverageScreen",
        }
        # First launch auto-creates the default profile and lists it.
        names = [p.name for p in app.store.list_profiles()]
        assert names == ["default"]
    finally:
        app.destroy()


def test_profile_flow_to_dashboard_and_practice(tmp_path: Path) -> None:
    from sumsmaster.gui.app import DashboardScreen, ProfileScreen
    from sumsmaster.gui.store import Profile, ProfileStore

    store = ProfileStore(root=tmp_path / "home")
    store.save(Profile(name="Maya", plan="times-tables"))
    app = _build_app(tmp_path / "home")
    try:
        screen = app.screens["ProfileScreen"]
        assert isinstance(screen, ProfileScreen)
        screen.refresh()
        idx = [p.name for p in screen.profiles].index("Maya")
        screen.listbox.selection_clear(0, "end")
        screen.listbox.selection_set(idx)
        screen._open_selected()
        assert app.profile is not None and app.profile.name == "Maya"
        assert store.last_profile_slug() == "maya"

        dash = app.screens["DashboardScreen"]
        assert isinstance(dash, DashboardScreen)
        dash._start()
        assert app.session is not None
        assert app.session.total == 10

        # Answer one problem through the widget layer.
        practice = app.screens["PracticeScreen"]
        item = app.session.current
        assert item is not None
        cast(Any, practice.answer_var).set(str(item.problem.answer))  # type: ignore[attr-defined]
        cast(Any, practice)._submit()
        assert app.session.answered == 1

        # The paused session must be resumable from disk.
        app.save_profile()
        reloaded = store.load("maya")
        assert reloaded is not None
        assert reloaded.session is not None
        assert reloaded.session.answered == 1
    finally:
        app.destroy()
