"""Tests for practice plan definitions."""

from __future__ import annotations

from sumsmaster.gui.plans import ALL_PLANS, DEFAULT_PLAN_ID, get_plan
from sumsmaster.tricks import ALL_TRICKS, Operation


def test_every_plan_resolves_to_real_tricks() -> None:
    names = {t.name for t in ALL_TRICKS}
    for plan in ALL_PLANS:
        assert plan.trick_names, plan.id
        assert set(plan.trick_names) <= names
        assert len(plan.tricks) == len(plan.trick_names)


def test_everything_plan_covers_registry() -> None:
    assert set(get_plan("everything").trick_names) == {t.name for t in ALL_TRICKS}


def test_operation_plans_are_scoped() -> None:
    for plan_id, op in [
        ("addition-foundations", Operation.ADD),
        ("subtraction-strategies", Operation.SUB),
        ("times-tables", Operation.MUL),
        ("division-basics", Operation.DIV),
    ]:
        for trick in get_plan(plan_id).tricks:
            assert op in trick.applies_to, (plan_id, trick.name)


def test_unknown_plan_falls_back_to_default() -> None:
    assert get_plan("no-such-plan").id == DEFAULT_PLAN_ID


def test_plan_ids_unique() -> None:
    ids = [p.id for p in ALL_PLANS]
    assert len(ids) == len(set(ids))
