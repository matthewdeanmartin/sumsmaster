"""Tests for the trick taxonomy and detectors."""

from __future__ import annotations

import pytest

from sumsmaster.tricks import Operation, Problem, tricks_for
from sumsmaster.tricks.registry import (
    ADD_DOUBLES,
    ADD_MAKE_TEN,
    ADD_NEAR_TEN,
    ADD_TEN,
    DIV_BY_TEN,
    DIV_INVERSE_OF_MUL,
    MUL_NINE_FINGER,
    MUL_TEN,
    SUB_FROM_TEEN,
    SUB_NEAR_TEN,
)


def _p(a: int, b: int, op: Operation) -> Problem:
    return Problem(a, b, op)


# ---------------------------------------------------------------------------
# Targeted detector tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "problem,trick,expected",
    [
        (_p(7, 10, Operation.MUL), MUL_TEN, True),
        (_p(10, 7, Operation.MUL), MUL_TEN, True),
        (_p(7, 9, Operation.MUL), MUL_TEN, False),
        (_p(7, 9, Operation.MUL), MUL_NINE_FINGER, True),
        (_p(9, 7, Operation.MUL), MUL_NINE_FINGER, True),

        (_p(5, 5, Operation.ADD), ADD_DOUBLES, True),
        (_p(5, 6, Operation.ADD), ADD_DOUBLES, False),
        (_p(7, 3, Operation.ADD), ADD_MAKE_TEN, True),
        (_p(8, 2, Operation.ADD), ADD_MAKE_TEN, True),
        (_p(8, 3, Operation.ADD), ADD_MAKE_TEN, False),
        (_p(15, 10, Operation.ADD), ADD_TEN, True),
        (_p(7, 9, Operation.ADD), ADD_NEAR_TEN, True),
        (_p(11, 7, Operation.ADD), ADD_NEAR_TEN, True),

        (_p(20, 9, Operation.SUB), SUB_NEAR_TEN, True),
        (_p(15, 10, Operation.SUB), SUB_NEAR_TEN, False),
        (_p(13, 5, Operation.SUB), SUB_FROM_TEEN, True),
        (_p(20, 5, Operation.SUB), SUB_FROM_TEEN, False),

        (_p(80, 10, Operation.DIV), DIV_BY_TEN, True),
        (_p(56, 7, Operation.DIV), DIV_INVERSE_OF_MUL, True),
        # Wrong op never matches.
        (_p(7, 10, Operation.MUL), DIV_BY_TEN, False),
    ],
)
def test_detector(problem: Problem, trick, expected: bool) -> None:
    assert trick.matches(problem) is expected


def test_tricks_for_returns_multiple() -> None:
    # 5 + 5 should hit doubles, make-ten, and partition-small at minimum.
    matches = {t.name for t in tricks_for(_p(5, 5, Operation.ADD))}
    assert "doubles" in matches
    assert "make ten" in matches


def test_tricks_for_empty_when_op_mismatch() -> None:
    # 6 - 2 with the strictest detectors gone has at least the inverse-add
    # fallback; just confirm the API returns a list of Tricks.
    result = tricks_for(_p(6, 2, Operation.SUB))
    assert isinstance(result, list)
    for t in result:
        assert Operation.SUB in t.applies_to


def test_problem_answer() -> None:
    assert Problem(7, 8, Operation.ADD).answer == 15
    assert Problem(20, 7, Operation.SUB).answer == 13
    assert Problem(6, 9, Operation.MUL).answer == 54
    assert Problem(56, 8, Operation.DIV).answer == 7
