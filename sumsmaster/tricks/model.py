"""Core data model for tricks and problems."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Operation(str, Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"


@dataclass(frozen=True)
class Problem:
    """A binary arithmetic problem.

    `a op b = answer`. For division we require `b != 0` and integer answers
    in this proof-of-concept (we restrict the domain to clean facts).
    """

    a: int
    b: int
    op: Operation

    @property
    def answer(self) -> int:
        if self.op is Operation.ADD:
            return self.a + self.b
        if self.op is Operation.SUB:
            return self.a - self.b
        if self.op is Operation.MUL:
            return self.a * self.b
        if self.op is Operation.DIV:
            return self.a // self.b
        raise ValueError(self.op)

    def __str__(self) -> str:
        return f"{self.a} {self.op.value} {self.b}"


# A detector takes a problem and returns True if the trick applies.
Detector = Callable[[Problem], bool]


@dataclass(frozen=True)
class Trick:
    """A named mental-math strategy that applies to some subset of problems.

    `applies_to` is the set of operations the trick can ever match. It is a
    fast pre-filter before calling `detect`.
    """

    name: str
    explanation: str
    applies_to: frozenset[Operation]
    detect: Detector

    def matches(self, p: Problem) -> bool:
        return p.op in self.applies_to and self.detect(p)
