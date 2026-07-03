"""Practice plans — named, ordered subsets of the trick registry.

A plan is the free tier's "course": pick one when creating a profile and
practice draws only from its tricks. Plans are defined in code and validated
against the registry at import time so a trick rename fails loudly.
"""

from __future__ import annotations

from dataclasses import dataclass

from sumsmaster.tricks import ALL_TRICKS, Operation, Trick

_BY_NAME: dict[str, Trick] = {t.name: t for t in ALL_TRICKS}


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    description: str
    trick_names: tuple[str, ...]

    @property
    def tricks(self) -> tuple[Trick, ...]:
        return tuple(_BY_NAME[n] for n in self.trick_names)


def _names_for(*ops: Operation) -> tuple[str, ...]:
    wanted = set(ops)
    return tuple(t.name for t in ALL_TRICKS if t.applies_to & wanted)


ALL_PLANS: tuple[Plan, ...] = (
    Plan(
        id="everything",
        name="Everything",
        description="All tricks across addition, subtraction, multiplication and division.",
        trick_names=tuple(t.name for t in ALL_TRICKS),
    ),
    Plan(
        id="addition-foundations",
        name="Addition Foundations",
        description="Counting on, doubles, make-ten and compensation strategies.",
        trick_names=_names_for(Operation.ADD),
    ),
    Plan(
        id="subtraction-strategies",
        name="Subtraction Strategies",
        description="Counting up, teen splits and near-ten compensation.",
        trick_names=_names_for(Operation.SUB),
    ),
    Plan(
        id="times-tables",
        name="Times-Table Tricks",
        description="The 12×12 grid through doubling, ×5, ×9, ×10, ×11 and splits.",
        trick_names=_names_for(Operation.MUL),
    ),
    Plan(
        id="division-basics",
        name="Division Basics",
        description="Halving, ÷5, ÷10 and inverse multiplication facts.",
        trick_names=_names_for(Operation.DIV),
    ),
)

PLANS_BY_ID: dict[str, Plan] = {p.id: p for p in ALL_PLANS}
DEFAULT_PLAN_ID = "everything"


def get_plan(plan_id: str) -> Plan:
    """Look up a plan, falling back to the default for unknown/stale ids."""
    return PLANS_BY_ID.get(plan_id, PLANS_BY_ID[DEFAULT_PLAN_ID])


def _validate() -> None:
    for plan in ALL_PLANS:
        if not plan.trick_names:
            raise ValueError(f"plan {plan.id!r} has no tricks")
        missing = [n for n in plan.trick_names if n not in _BY_NAME]
        if missing:
            raise ValueError(f"plan {plan.id!r} references unknown tricks: {missing}")


_validate()
