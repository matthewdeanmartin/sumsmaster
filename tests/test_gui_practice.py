"""Tests for the practice session engine (no tkinter required)."""

from __future__ import annotations

import random

from sumsmaster.gui.plans import get_plan
from sumsmaster.gui.practice import (
    PracticeSession,
    TaggedProblem,
    build_queue,
    problems_for_trick,
)
from sumsmaster.gui.store import MASTERY_STREAK, Profile
from sumsmaster.tricks import Operation, Problem
from sumsmaster.tricks.registry import MUL_TEN


def make_profile(plan: str = "everything") -> Profile:
    return Profile(name="Test", plan=plan)


def test_problems_for_trick_all_match() -> None:
    pool = problems_for_trick(MUL_TEN.name)
    assert pool
    assert all(MUL_TEN.matches(p) for p in pool)


def test_build_queue_generates_matching_problems() -> None:
    plan = get_plan("times-tables")
    queue = build_queue(plan, make_profile("times-tables"), length=20, rng=random.Random(42))
    assert len(queue) == 20
    for item in queue:
        assert item.problem.op is Operation.MUL
        assert item.trick.matches(item.problem)
        assert item.trick.name in plan.trick_names


def test_tagged_problem_row_round_trip() -> None:
    item = TaggedProblem(problem=Problem(7, 10, Operation.MUL), trick=MUL_TEN)
    restored = TaggedProblem.from_row(item.to_row())
    assert restored.problem == item.problem
    assert restored.trick.name == MUL_TEN.name


def test_submit_updates_progress_and_advances() -> None:
    profile = make_profile()
    session = PracticeSession.start(profile, get_plan("everything"), length=3, rng=random.Random(1))
    item = session.current
    assert item is not None
    assert session.submit(item.problem.answer) is True
    prog = profile.progress[item.trick.name]
    assert (prog.attempts, prog.correct, prog.streak) == (1, 1, 1)
    assert session.answered == 1 and session.correct == 1

    item2 = session.current
    assert item2 is not None
    assert session.submit(item2.problem.answer + 1) is False
    assert profile.progress[item2.trick.name].streak == 0
    assert session.answered == 2 and session.correct == 1


def test_session_state_synced_and_resumable() -> None:
    profile = make_profile()
    session = PracticeSession.start(profile, get_plan("everything"), length=4, rng=random.Random(2))
    first = session.current
    assert first is not None
    session.submit(first.problem.answer)
    assert profile.session is not None
    assert profile.session.answered == 1
    assert len(profile.session.queue) == 3

    # Simulate quitting and reopening: resume from the profile alone.
    resumed = PracticeSession.resume(profile)
    assert resumed is not None
    assert resumed.total == 4
    assert resumed.answered == 1
    assert len(resumed.queue) == 3
    assert resumed.current is not None
    assert resumed.current.problem == session.current.problem  # type: ignore[union-attr]


def test_finishing_clears_session_state() -> None:
    profile = make_profile()
    session = PracticeSession.start(profile, get_plan("everything"), length=2, rng=random.Random(3))
    while not session.finished:
        item = session.current
        assert item is not None
        session.submit(item.problem.answer)
    assert profile.session is None
    assert PracticeSession.resume(profile) is None


def test_abandon_clears_state_but_keeps_progress() -> None:
    profile = make_profile()
    session = PracticeSession.start(profile, get_plan("everything"), length=3, rng=random.Random(4))
    item = session.current
    assert item is not None
    session.submit(item.problem.answer)
    session.abandon()
    assert profile.session is None
    assert profile.progress[item.trick.name].attempts == 1


def test_resume_with_stale_trick_name_returns_none() -> None:
    profile = make_profile()
    session = PracticeSession.start(profile, get_plan("everything"), length=2, rng=random.Random(5))
    assert profile.session is not None
    profile.session.queue[0][3] = "trick that was renamed"
    assert PracticeSession.resume(profile) is None
    assert profile.session is None  # stale state is cleared


def test_mastered_tricks_get_review_weight() -> None:
    """Mastered tricks should appear far less often than unmastered ones."""
    profile = make_profile("times-tables")
    plan = get_plan("times-tables")
    mastered_name = MUL_TEN.name
    prog = profile.progress_for(mastered_name)
    for _ in range(MASTERY_STREAK):
        prog.record(True)

    rng = random.Random(6)
    picks = [item.trick.name for item in build_queue(plan, profile, length=400, rng=rng)]
    mastered_share = picks.count(mastered_name) / len(picks)
    # Unweighted share would be ~1/14 (~7%); review weight should push the
    # mastered trick well below that.
    assert mastered_share < 0.05
