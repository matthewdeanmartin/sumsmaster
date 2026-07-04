"""Trick-coverage analysis over fact domains.

Phase 0 question: if we define the trick taxonomy above, what fraction of the
elementary-arithmetic fact space does *some* trick cover? A fact with zero
matching tricks is one Sumsmaster has nothing useful to say about — it would
fall back to brute memorization.

Domains in this module are deliberately small and clean (single- and
double-digit integer facts). They mirror what an early learner would face:
the 12×12 multiplication grid, addition/subtraction within 20, and the
matching division facts.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from sumsmaster.tricks import ALL_TRICKS, Operation, Problem, Trick, tricks_for

# ---------------------------------------------------------------------------
# Domains
# ---------------------------------------------------------------------------


def addition_domain(lo: int = 0, hi: int = 12) -> Iterator[Problem]:
    for a in range(lo, hi + 1):
        for b in range(lo, hi + 1):
            yield Problem(a, b, Operation.ADD)


def subtraction_domain(lo: int = 0, hi: int = 20) -> Iterator[Problem]:
    # Only non-negative results — keeps phase-0 facts clean.
    for a in range(lo, hi + 1):
        for b in range(lo, a + 1):
            yield Problem(a, b, Operation.SUB)


def multiplication_domain(lo: int = 0, hi: int = 12) -> Iterator[Problem]:
    for a in range(lo, hi + 1):
        for b in range(lo, hi + 1):
            yield Problem(a, b, Operation.MUL)


def division_domain(lo: int = 1, hi: int = 12) -> Iterator[Problem]:
    # Inverse of the multiplication grid: for every a·b = c, generate c ÷ b.
    for b in range(lo, hi + 1):
        for q in range(lo, hi + 1):
            yield Problem(b * q, b, Operation.DIV)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@dataclass
class CoverageReport:
    domain_name: str
    total_facts: int
    covered_facts: int
    uncovered: list[Problem]
    per_trick_hits: Counter[str]
    facts_by_trick_count: Counter[int]  # how many facts have N matching tricks

    @property
    def coverage_pct(self) -> float:
        return 100.0 * self.covered_facts / self.total_facts if self.total_facts else 0.0

    def format(self, show_uncovered: int = 10) -> str:
        lines = [
            f"=== {self.domain_name} ===",
            f"facts: {self.total_facts}   covered: {self.covered_facts}   " f"coverage: {self.coverage_pct:.1f}%",
            "",
            "tricks-per-fact distribution:",
        ]
        for k in sorted(self.facts_by_trick_count):
            count = self.facts_by_trick_count[k]
            pct = 100.0 * count / self.total_facts
            bar = "#" * int(pct / 2)
            lines.append(f"  {k} tricks: {count:4d} ({pct:5.1f}%) {bar}")
        lines.append("")
        lines.append("hits per trick (facts that the trick can solve):")
        for name, hits in self.per_trick_hits.most_common():
            pct = 100.0 * hits / self.total_facts
            lines.append(f"  {hits:4d} ({pct:5.1f}%)  {name}")
        if self.uncovered:
            lines.append("")
            shown = self.uncovered[:show_uncovered]
            extra = len(self.uncovered) - len(shown)
            lines.append(f"uncovered facts (no trick fires) — first {len(shown)}:")
            for p in shown:
                lines.append(f"  {p} = {p.answer}")
            if extra:
                lines.append(f"  ... and {extra} more")
        return "\n".join(lines)


def analyze(domain_name: str, problems: Iterable[Problem]) -> CoverageReport:
    per_trick: Counter[str] = Counter()
    by_count: Counter[int] = Counter()
    uncovered: list[Problem] = []
    total = 0
    covered = 0

    for p in problems:
        total += 1
        matches = tricks_for(p)
        by_count[len(matches)] += 1
        if matches:
            covered += 1
            for t in matches:
                per_trick[t.name] += 1
        else:
            uncovered.append(p)

    return CoverageReport(
        domain_name=domain_name,
        total_facts=total,
        covered_facts=covered,
        uncovered=uncovered,
        per_trick_hits=per_trick,
        facts_by_trick_count=by_count,
    )


def default_report() -> str:
    """Run the standard phase-0 coverage report and return it as text."""
    reports = [
        analyze("addition 0..12 + 0..12", addition_domain(0, 12)),
        analyze("subtraction 0..20 (non-negative)", subtraction_domain(0, 20)),
        analyze("multiplication 0..12 × 0..12", multiplication_domain(0, 12)),
        analyze("division (inverse of 1..12 × 1..12)", division_domain(1, 12)),
    ]
    body = "\n\n".join(r.format() for r in reports)

    # Aggregate one-liner across all four domains.
    total = sum(r.total_facts for r in reports)
    covered = sum(r.covered_facts for r in reports)
    pct = 100.0 * covered / total if total else 0.0
    summary = (
        f"\n\n=== overall ===\n"
        f"facts: {total}   covered: {covered}   coverage: {pct:.1f}%\n"
        f"tricks defined: {len(ALL_TRICKS)}"
    )
    return body + summary


def trick_summary() -> str:
    """List every trick with its scope — useful for taxonomy review."""
    by_op: dict[Operation, list[Trick]] = {op: [] for op in Operation}
    for t in ALL_TRICKS:
        for op in t.applies_to:
            by_op[op].append(t)
    out = []
    for op in Operation:
        out.append(f"{op.name} ({op.value}):")
        for t in by_op[op]:
            out.append(f"  - {t.name} — {t.explanation}")
    return "\n".join(out)
