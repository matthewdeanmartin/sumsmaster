"""Practice session engine.

Generates trick-tagged problems from the phase-0 fact domains, checks
answers, updates per-trick progress on the profile, and serializes to/from
:class:`~sumsmaster.gui.store.SessionState` so a half-finished session can
be resumed later.

Scheduling is deliberately simple (roadmap: "start simple"): each session
slot picks a trick from the plan, weighted toward tricks with the fewest
correct answers; mastered tricks drop to a light review weight instead of
disappearing entirely.
"""

from __future__ import annotations

import random
import secrets
from dataclasses import dataclass
from functools import cache, lru_cache
from typing import Any

from sumsmaster.coverage import addition_domain, division_domain, multiplication_domain, subtraction_domain
from sumsmaster.gui.plans import Plan
from sumsmaster.gui.store import Profile, SessionState
from sumsmaster.tricks import Operation, Problem, Trick

DEFAULT_SESSION_LENGTH = 10
REVIEW_WEIGHT = 1.0  # relative pick weight of a mastered trick
LEARNING_WEIGHT = 8.0  # base weight of an unmastered trick


@lru_cache(maxsize=1)
def _fact_space() -> tuple[Problem, ...]:
    """Every fact in the phase-0 domains — same space `coverage` analyzes."""
    return tuple(
        [
            *addition_domain(0, 12),
            *subtraction_domain(0, 20),
            *multiplication_domain(0, 12),
            *division_domain(1, 12),
        ]
    )


@cache
def problems_for_trick(trick_name: str) -> tuple[Problem, ...]:
    """All phase-0 facts on which the named trick fires."""
    from sumsmaster.tricks.registry import ALL_TRICKS

    by_name = {t.name: t for t in ALL_TRICKS}
    trick = by_name[trick_name]
    return tuple(p for p in _fact_space() if trick.matches(p))


@dataclass(frozen=True)
class TaggedProblem:
    """A problem plus the trick it was generated to exercise."""

    problem: Problem
    trick: Trick

    def to_row(self) -> list[Any]:
        return [self.problem.a, self.problem.b, self.problem.op.value, self.trick.name]

    @classmethod
    def from_row(cls, row: list[Any]) -> TaggedProblem:
        from sumsmaster.tricks.registry import ALL_TRICKS

        a, b, op_symbol, trick_name = row
        by_name = {t.name: t for t in ALL_TRICKS}
        return cls(
            problem=Problem(int(a), int(b), Operation(op_symbol)),
            trick=by_name[trick_name],
        )


def _pick_tricks(plan: Plan, profile: Profile, count: int, rng: random.Random) -> list[Trick]:
    """Mastery-weighted trick selection for one session."""
    candidates = [t for t in plan.tricks if problems_for_trick(t.name)]
    if not candidates:
        raise ValueError(f"plan {plan.id!r} has no generatable problems")
    weights = []
    for trick in candidates:
        prog = profile.progress.get(trick.name)
        if prog is not None and prog.mastered:
            weights.append(REVIEW_WEIGHT)
        else:
            correct = prog.correct if prog else 0
            # Fewer correct answers → higher weight; floor keeps it positive.
            weights.append(LEARNING_WEIGHT / (1 + correct))
    return rng.choices(candidates, weights=weights, k=count)


def build_queue(
    plan: Plan,
    profile: Profile,
    length: int = DEFAULT_SESSION_LENGTH,
    rng: secrets.SystemRandom | None = None,
) -> list[TaggedProblem]:
    """Generate a fresh session queue for a profile's plan."""
    rng = rng or secrets.SystemRandom()
    queue: list[TaggedProblem] = []
    seen: set[tuple[int, int, Operation]] = set()
    for trick in _pick_tricks(plan, profile, length, rng):
        pool = problems_for_trick(trick.name)
        problem = rng.choice(pool)
        # Avoid immediate duplicates when the pool allows it.
        for _ in range(5):
            key = (problem.a, problem.b, problem.op)
            if key not in seen or len(pool) <= len(seen):
                break
            problem = rng.choice(pool)
        seen.add((problem.a, problem.b, problem.op))
        queue.append(TaggedProblem(problem=problem, trick=trick))
    return queue


class PracticeSession:
    """A run of N problems against one profile.

    The session mutates ``profile.progress`` on each answer and keeps
    ``profile.session`` in sync so callers can persist after every step —
    that persisted state is what "resume" restores.
    """

    def __init__(
        self, profile: Profile, queue: list[TaggedProblem], total: int, answered: int = 0, correct: int = 0
    ) -> None:
        self.profile = profile
        self.queue = queue
        self.total = total
        self.answered = answered
        self.correct = correct

    # -- construction --------------------------------------------------------

    @classmethod
    def start(
        cls,
        profile: Profile,
        plan: Plan,
        length: int = DEFAULT_SESSION_LENGTH,
        rng: secrets.SystemRandom | None = None,
    ) -> PracticeSession:
        queue = build_queue(plan, profile, length, rng)
        session = cls(profile, queue, total=len(queue))
        session._sync_state()
        return session

    @classmethod
    def resume(cls, profile: Profile) -> PracticeSession | None:
        state = profile.session
        if state is None or not state.queue:
            return None
        try:
            queue = [TaggedProblem.from_row(row) for row in state.queue]
        except (KeyError, ValueError, TypeError):
            # A trick was renamed/removed since the session was saved.
            profile.session = None
            return None
        return cls(
            profile,
            queue,
            total=state.total,
            answered=state.answered,
            correct=state.correct,
        )

    # -- flow -----------------------------------------------------------------

    @property
    def finished(self) -> bool:
        return not self.queue

    @property
    def current(self) -> TaggedProblem | None:
        return self.queue[0] if self.queue else None

    def submit(self, answer: int) -> bool:
        """Grade the current problem, update progress, advance the queue."""
        item = self.current
        if item is None:
            raise ValueError("session is finished")
        is_correct = answer == item.problem.answer
        self.profile.progress_for(item.trick.name).record(is_correct)
        self.queue.pop(0)
        self.answered += 1
        if is_correct:
            self.correct += 1
        self._sync_state()
        return is_correct

    def abandon(self) -> None:
        """Discard the remaining queue (progress already recorded stays)."""
        self.queue.clear()
        self.profile.session = None

    def _sync_state(self) -> None:
        if self.finished:
            self.profile.session = None
        else:
            self.profile.session = SessionState(
                queue=[item.to_row() for item in self.queue],
                total=self.total,
                answered=self.answered,
                correct=self.correct,
            )
