"""Mental-math trick taxonomy and detectors.

A `Trick` is a named mental shortcut for a specific class of arithmetic facts.
Each trick declares which `Operation`s it applies to and exposes a detector
predicate that decides whether a given problem instance is solvable by it.

This package is intentionally pure: no I/O, no storage, no scheduling. The
goal of phase 0 is to validate that a small taxonomy of tricks covers a
useful fraction of the elementary-arithmetic fact space.
"""

from sumsmaster.tricks.model import Operation, Problem, Trick
from sumsmaster.tricks.registry import ALL_TRICKS, tricks_for

__all__ = ["ALL_TRICKS", "Operation", "Problem", "Trick", "tricks_for"]
