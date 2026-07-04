"""Tests for local profile storage (no tkinter required)."""

from __future__ import annotations

from pathlib import Path

from sumsmaster.gui.store import MASTERY_STREAK, Profile, ProfileStore, SessionState, TrickProgress, slugify


def make_store(tmp_path: Path) -> ProfileStore:
    return ProfileStore(root=tmp_path / "sumsmaster-home")


def test_slugify() -> None:
    assert slugify("Maya M.") == "maya-m"
    assert slugify("  ") == "profile"
    assert slugify("Ünïcode!") == "n-code"


def test_ensure_default_creates_once(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    first = store.ensure_default()
    first.progress_for("doubles").record(True)
    store.save(first)
    again = store.ensure_default()
    assert again.name == "default"
    assert again.progress["doubles"].attempts == 1  # not recreated blank


def test_profile_round_trip(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    profile = Profile(name="Maya", plan="times-tables")
    profile.progress_for("square").record(True)
    profile.progress_for("square").record(False)
    profile.session = SessionState(queue=[[3, 4, "*", "distributive split"]], total=10, answered=9, correct=7)
    store.save(profile)

    loaded = store.load("maya")
    assert loaded is not None
    assert loaded.name == "Maya"
    assert loaded.plan == "times-tables"
    prog = loaded.progress["square"]
    assert (prog.attempts, prog.correct, prog.streak) == (2, 1, 0)
    assert loaded.session is not None
    assert loaded.session.queue == [[3, 4, "*", "distributive split"]]
    assert loaded.session.answered == 9


def test_list_delete_and_exists(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.save(Profile(name="Alpha", plan="everything"))
    store.save(Profile(name="Beta", plan="everything"))
    assert [p.name for p in store.list_profiles()] == ["Alpha", "Beta"]
    assert store.exists("alpha") and store.exists("Alpha")
    store.delete("alpha")
    assert [p.name for p in store.list_profiles()] == ["Beta"]
    store.delete("alpha")  # deleting a missing profile is a no-op


def test_corrupt_profile_file_is_skipped(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.save(Profile(name="Good", plan="everything"))
    store.profiles_dir.joinpath("bad.json").write_text("{not json", encoding="utf-8")
    assert [p.name for p in store.list_profiles()] == ["Good"]
    assert store.load("bad") is None


def test_last_profile_settings(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    assert store.last_profile_slug() is None
    store.remember_profile("maya")
    assert store.last_profile_slug() == "maya"


def test_mastery_streak_semantics() -> None:
    prog = TrickProgress()
    for _ in range(MASTERY_STREAK - 1):
        prog.record(True)
    assert not prog.mastered
    prog.record(True)
    assert prog.mastered
    prog.record(False)  # a miss resets the streak and mastery
    assert prog.streak == 0
    assert not prog.mastered
    assert prog.accuracy == MASTERY_STREAK / (MASTERY_STREAK + 1)
