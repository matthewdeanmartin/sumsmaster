"""Concrete trick definitions.

Each detector answers: "is this problem a natural fit for this mental
shortcut?" Detectors are deliberately conservative — they fire only when the
trick is genuinely the easy path, not whenever it's *technically* applicable.
For example, `add 9 by add-10-minus-1` fires for `+9` and `+19` but not for
arbitrary `+a` where `a` happens to be 9-ish.
"""

from __future__ import annotations

from sumsmaster.tricks.model import Operation, Problem, Trick

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ADD = frozenset({Operation.ADD})
SUB = frozenset({Operation.SUB})
MUL = frozenset({Operation.MUL})
DIV = frozenset({Operation.DIV})


def _ends_in(n: int, digit: int) -> bool:
    return abs(n) % 10 == digit


def _is_power_of_10(n: int) -> bool:
    if n <= 0:
        return False
    while n % 10 == 0:
        n //= 10
    return n == 1


def _is_near(n: int, target: int, window: int = 2) -> bool:
    """True if n is within `window` of `target` (above or below)."""
    return 0 < abs(n - target) <= window


def _doubles_close(a: int, b: int, window: int = 1) -> bool:
    return a == b or abs(a - b) <= window


# ---------------------------------------------------------------------------
# Addition tricks
# ---------------------------------------------------------------------------

ADD_ZERO = Trick(
    name="add 0 (identity)",
    explanation="a + 0 = a",
    applies_to=ADD,
    detect=lambda p: p.a == 0 or p.b == 0,
)

ADD_ONE = Trick(
    name="add 1 (count up)",
    explanation="a + 1 is the next number",
    applies_to=ADD,
    detect=lambda p: p.a == 1 or p.b == 1,
)

ADD_TWO = Trick(
    name="add 2 (skip-count)",
    explanation="a + 2 = a then next-next",
    applies_to=ADD,
    detect=lambda p: p.a == 2 or p.b == 2,
)

ADD_TEN = Trick(
    name="add 10 (place value)",
    explanation="a + 10 increments the tens digit",
    applies_to=ADD,
    detect=lambda p: p.a == 10 or p.b == 10,
)

ADD_NEAR_TEN = Trick(
    name="add 9/11 as 10±1",
    explanation="a + 9 = a + 10 - 1; a + 11 = a + 10 + 1",
    applies_to=ADD,
    detect=lambda p: p.a in (9, 11) or p.b in (9, 11),
)

ADD_DOUBLES = Trick(
    name="doubles",
    explanation="a + a — memorized as a fact family",
    applies_to=ADD,
    detect=lambda p: p.a == p.b,
)

ADD_NEAR_DOUBLES = Trick(
    name="near doubles",
    explanation="a + (a+1) = 2a + 1",
    applies_to=ADD,
    detect=lambda p: abs(p.a - p.b) == 1,
)

ADD_MAKE_TEN = Trick(
    name="make ten",
    explanation="a + b where a + b = 10 (complement pairs)",
    applies_to=ADD,
    detect=lambda p: p.a + p.b == 10 and p.a > 0 and p.b > 0,
)

ADD_BRIDGE_TEN = Trick(
    name="bridge through 10",
    explanation="split b so a reaches 10 first (e.g. 8 + 5 = 8 + 2 + 3)",
    applies_to=ADD,
    # Useful when both operands are single-digit, sum > 10, and neither is
    # already a 'trivial' add (0/1/2/10 family handled above).
    detect=lambda p: (
        1 <= p.a <= 9
        and 1 <= p.b <= 9
        and p.a + p.b > 10
        and p.a not in (1, 2)
        and p.b not in (1, 2)
    ),
)

ADD_TWELVE = Trick(
    name="add 12 as 10 + 2",
    explanation="a + 12 = a + 10 + 2",
    applies_to=ADD,
    detect=lambda p: p.a == 12 or p.b == 12,
)

ADD_PARTITION_SMALL = Trick(
    name="partition small (no carry)",
    explanation="a + b where both ≤9 and sum ≤10 — split one operand if useful",
    applies_to=ADD,
    detect=lambda p: 1 <= p.a <= 9 and 1 <= p.b <= 9 and p.a + p.b <= 10,
)

ADD_NEAR_HUNDRED = Trick(
    name="add near 100",
    explanation="a + 99 = a + 100 - 1, etc.",
    applies_to=ADD,
    detect=lambda p: _is_near(p.a, 100, 2) or _is_near(p.b, 100, 2),
)


# ---------------------------------------------------------------------------
# Subtraction tricks
# ---------------------------------------------------------------------------

SUB_ZERO = Trick(
    name="subtract 0",
    explanation="a - 0 = a",
    applies_to=SUB,
    detect=lambda p: p.b == 0,
)

SUB_SELF = Trick(
    name="subtract self",
    explanation="a - a = 0",
    applies_to=SUB,
    detect=lambda p: p.a == p.b,
)

SUB_ONE = Trick(
    name="subtract 1 (count down)",
    explanation="a - 1 is the previous number",
    applies_to=SUB,
    detect=lambda p: p.b == 1,
)

SUB_TEN = Trick(
    name="subtract 10",
    explanation="a - 10 decrements the tens digit",
    applies_to=SUB,
    detect=lambda p: p.b == 10,
)

SUB_NEAR_TEN = Trick(
    name="subtract 9/11 as 10±1",
    explanation="a - 9 = a - 10 + 1; a - 11 = a - 10 - 1",
    applies_to=SUB,
    detect=lambda p: p.b in (9, 11),
)

SUB_NEAR_HUNDRED = Trick(
    name="subtract near 100",
    explanation="a - 99 = a - 100 + 1",
    applies_to=SUB,
    detect=lambda p: _is_near(p.b, 100, 2),
)

SUB_COUNT_UP_SMALL_GAP = Trick(
    name="count up (small gap)",
    explanation="when a and b are close, count up from b to a",
    applies_to=SUB,
    detect=lambda p: 0 < (p.a - p.b) <= 3,
)

SUB_INVERSE_OF_DOUBLE = Trick(
    name="inverse of a double",
    explanation="2a - a = a",
    applies_to=SUB,
    detect=lambda p: p.a == 2 * p.b and p.b > 0,
)

SUB_INVERSE_OF_ADDITION = Trick(
    name="inverse of an addition fact",
    explanation="recall the matching addition: if c - b = ?, find ? such that b + ? = c",
    applies_to=SUB,
    # Universal fallback for clean subtraction facts where both operands and
    # the answer are within the addition fact-family range. Tracks how many
    # facts only resolve via this generic recall path.
    detect=lambda p: 0 <= p.b <= 12 and 0 <= (p.a - p.b) <= 12,
)

SUB_FROM_TEEN = Trick(
    name="subtract from a teen (split)",
    explanation="13 - 5 = (10 - 5) + 3; split the teen into 10 + ones",
    applies_to=SUB,
    detect=lambda p: 11 <= p.a <= 19 and 1 <= p.b <= 9 and (p.a - p.b) >= 0,
)

SUB_FROM_TWENTY = Trick(
    name="subtract from 20",
    explanation="20 - b: complement to 10 plus 10",
    applies_to=SUB,
    detect=lambda p: p.a == 20 and 1 <= p.b <= 19,
)


# ---------------------------------------------------------------------------
# Multiplication tricks
# ---------------------------------------------------------------------------

MUL_ZERO = Trick(
    name="multiply by 0",
    explanation="a × 0 = 0",
    applies_to=MUL,
    detect=lambda p: p.a == 0 or p.b == 0,
)

MUL_ONE = Trick(
    name="multiply by 1 (identity)",
    explanation="a × 1 = a",
    applies_to=MUL,
    detect=lambda p: p.a == 1 or p.b == 1,
)

MUL_TWO = Trick(
    name="multiply by 2 (double)",
    explanation="a × 2 = a + a",
    applies_to=MUL,
    detect=lambda p: p.a == 2 or p.b == 2,
)

MUL_FIVE = Trick(
    name="multiply by 5",
    explanation="a × 5 = a × 10 ÷ 2",
    applies_to=MUL,
    detect=lambda p: p.a == 5 or p.b == 5,
)

MUL_TEN = Trick(
    name="multiply by 10 (append zero)",
    explanation="a × 10 = a with a zero appended",
    applies_to=MUL,
    detect=lambda p: p.a == 10 or p.b == 10,
)

MUL_POWER_OF_TEN = Trick(
    name="multiply by power of 10",
    explanation="a × 10^k appends k zeros",
    applies_to=MUL,
    # Excludes 1 and matches 10, 100, 1000... — useful when the domain grows
    # beyond 12×12. Will not fire on the 12×12 grid alone (besides ×10).
    detect=lambda p: (_is_power_of_10(p.a) and p.a > 1) or (_is_power_of_10(p.b) and p.b > 1),
)

MUL_ELEVEN_SMALL = Trick(
    name="multiply by 11 (small)",
    explanation="for 1 ≤ a ≤ 9: a × 11 = aa (digit repeated)",
    applies_to=MUL,
    detect=lambda p: (p.a == 11 and 1 <= p.b <= 9) or (p.b == 11 and 1 <= p.a <= 9),
)

MUL_ELEVEN_TEEN = Trick(
    name="multiply by 11 (split-and-sum)",
    explanation="a × 11 = a × 10 + a; works for any a",
    applies_to=MUL,
    detect=lambda p: p.a == 11 or p.b == 11,
)

MUL_NINE_FINGER = Trick(
    name="multiply by 9 (10×a − a)",
    explanation="a × 9 = a × 10 − a; finger-trick for 1..10",
    applies_to=MUL,
    detect=lambda p: p.a == 9 or p.b == 9,
)

MUL_SQUARE = Trick(
    name="square",
    explanation="a × a — memorized squares 1..12",
    applies_to=MUL,
    detect=lambda p: p.a == p.b,
)

MUL_DOUBLE_AND_HALF = Trick(
    name="double-and-half",
    explanation="a × b = (a×2) × (b÷2) when one factor is even",
    applies_to=MUL,
    # Only fires when one factor is even AND >=4 AND neither factor already
    # has an easier trick (×0, ×1, ×2, ×5, ×10, ×11 handled).
    detect=lambda p: (
        ((p.a % 2 == 0 and p.a >= 4) or (p.b % 2 == 0 and p.b >= 4))
        and p.a not in (0, 1, 2, 5, 10, 11)
        and p.b not in (0, 1, 2, 5, 10, 11)
    ),
)

MUL_FOUR_AS_DOUBLE_DOUBLE = Trick(
    name="multiply by 4 (double twice)",
    explanation="a × 4 = (a × 2) × 2",
    applies_to=MUL,
    detect=lambda p: p.a == 4 or p.b == 4,
)

MUL_DISTRIBUTIVE_SPLIT = Trick(
    name="distributive split",
    explanation="a × b = a × (b-1) + a, e.g. 3 × 7 = 3 × 6 + 3",
    applies_to=MUL,
    # Targets the small-factor pairs that escape every other trick (notably
    # 3×7 / 7×3 / 3×8 / 6×7 etc.). Fires when both factors are in 3..9
    # and neither is one of the easy specials.
    detect=lambda p: (
        3 <= p.a <= 9 and 3 <= p.b <= 9
        and p.a not in (5,) and p.b not in (5,)
    ),
)

MUL_NEAR_TEN = Trick(
    name="multiply near 10",
    explanation="a × 9 or a × 11 by ×10 ± a (subset of above; kept for diagnostics)",
    applies_to=MUL,
    detect=lambda p: p.a in (9, 11) or p.b in (9, 11),
)


# ---------------------------------------------------------------------------
# Division tricks (integer division on clean facts only)
# ---------------------------------------------------------------------------

DIV_BY_ONE = Trick(
    name="divide by 1",
    explanation="a ÷ 1 = a",
    applies_to=DIV,
    detect=lambda p: p.b == 1,
)

DIV_SELF = Trick(
    name="divide by self",
    explanation="a ÷ a = 1",
    applies_to=DIV,
    detect=lambda p: p.a == p.b and p.b != 0,
)

DIV_BY_TWO = Trick(
    name="divide by 2 (halve)",
    explanation="a ÷ 2 — halve",
    applies_to=DIV,
    detect=lambda p: p.b == 2,
)

DIV_BY_FIVE = Trick(
    name="divide by 5",
    explanation="a ÷ 5 = a × 2 ÷ 10",
    applies_to=DIV,
    detect=lambda p: p.b == 5,
)

DIV_BY_TEN = Trick(
    name="divide by 10",
    explanation="a ÷ 10 — strip a zero",
    applies_to=DIV,
    detect=lambda p: p.b == 10,
)

DIV_INVERSE_OF_MUL = Trick(
    name="inverse multiplication fact",
    explanation="recall the matching multiplication fact",
    applies_to=DIV,
    # Always applicable for integer division facts — this is the universal
    # fallback. Tracked so we can see how many division facts are *only*
    # reachable via this generic strategy.
    detect=lambda p: p.b != 0 and p.a % p.b == 0,
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_TRICKS: tuple[Trick, ...] = (
    # Addition
    ADD_ZERO, ADD_ONE, ADD_TWO, ADD_TEN, ADD_NEAR_TEN,
    ADD_DOUBLES, ADD_NEAR_DOUBLES, ADD_MAKE_TEN, ADD_BRIDGE_TEN,
    ADD_TWELVE, ADD_PARTITION_SMALL, ADD_NEAR_HUNDRED,
    # Subtraction
    SUB_ZERO, SUB_SELF, SUB_ONE, SUB_TEN, SUB_NEAR_TEN,
    SUB_NEAR_HUNDRED, SUB_COUNT_UP_SMALL_GAP, SUB_INVERSE_OF_DOUBLE,
    SUB_INVERSE_OF_ADDITION, SUB_FROM_TEEN, SUB_FROM_TWENTY,
    # Multiplication
    MUL_ZERO, MUL_ONE, MUL_TWO, MUL_FIVE, MUL_TEN, MUL_POWER_OF_TEN,
    MUL_ELEVEN_SMALL, MUL_ELEVEN_TEEN, MUL_NINE_FINGER, MUL_SQUARE,
    MUL_DOUBLE_AND_HALF, MUL_FOUR_AS_DOUBLE_DOUBLE, MUL_DISTRIBUTIVE_SPLIT,
    MUL_NEAR_TEN,
    # Division
    DIV_BY_ONE, DIV_SELF, DIV_BY_TWO, DIV_BY_FIVE, DIV_BY_TEN, DIV_INVERSE_OF_MUL,
)


def tricks_for(p: Problem) -> list[Trick]:
    """Return every trick whose detector fires on `p`."""
    return [t for t in ALL_TRICKS if t.matches(p)]
