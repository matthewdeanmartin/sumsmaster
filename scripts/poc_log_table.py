#!/usr/bin/env python3
"""Standalone PoC: how good is mental multiplication via a memorized log table?

Question
--------
Suppose your brain can hold a budget of D digits. You can spend them on a
memorized base-10 log table (more entries, or more decimals per entry) and
then multiply by adding logs and taking an antilog. How much precision do you
get per memorized digit, is there an optimal table shape, and how does the
whole scheme stack up against just rounding both operands to n significant
figures and multiplying directly?

Lookup modes
------------
interp   slide-rule style: linearly interpolate between the two bracketing
         entries (both forward and for the antilog). More accurate, but the
         interpolation is itself a mental division you must perform.
nearest  no interpolation at all: snap the mantissa to the nearest table
         point and read its value; antilog by snapping to the nearest stored
         value. This is what "I memorized a log table but can't interpolate
         in my head" looks like.

For the nearest mode, grids that are uniform in *log* space matter: the
Renard "preferred number" series R10 (1, 1.25, 1.6, 2, 2.5, 3.15, 4, 5, 6.3,
8, 10) has logs of exactly 0.0, 0.1, ..., 1.0 — so the *values* are a free
pattern and only the grid points cost memory. R20 is the same at 0.05 steps.
This is decibel arithmetic.

Memory cost model
-----------------
+ value digits:  `decimals` per interior entry, but FREE if the stored
                 values form a constant-step sequence (a pattern, not facts).
+ grid digits:   fractional digits of each non-integer grid point, but FREE
                 if the grid itself is constant-step (e.g. "integers 1..10",
                 "quarter steps").
log 1 = 0 and log 10 = 1 are always free.

Direct baseline: round each operand to n significant figures, multiply
exactly. No long-term memory cost, but you must hold ~2n operand digits and
run an n x n-digit mental multiplication (working-memory load grows ~ n^2).

Errors are relative, |estimate/truth - 1|, over Monte Carlo problems with
log-uniform mantissas (Benford-realistic).

Run:  python scripts/poc_log_table.py   (stdlib only)
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# The memorized table
# ---------------------------------------------------------------------------


def _is_uniform(seq: list[float], tol: float = 1e-9) -> bool:
    diffs = [b - a for a, b in zip(seq, seq[1:])]
    return all(abs(d - diffs[0]) <= tol for d in diffs)


def _frac_digits(x: float) -> int:
    s = f"{x:g}"
    return len(s.split(".")[1]) if "." in s else 0


@dataclass
class LogTable:
    name: str
    points: list[float]  # mantissas in [1, 10], must include 1 and 10
    decimals: int
    # Renard-style tables memorize the VALUES as an exact pattern (0.05*k,
    # "decibels") and accept that the grid points only approximately hit
    # those logs. Default is the reverse: true logs rounded to `decimals`.
    pattern_values: bool = False
    values: list[float] = field(init=False)

    def __post_init__(self) -> None:
        self.points = sorted(self.points)
        assert self.points[0] == 1.0 and self.points[-1] == 10.0
        if self.pattern_values:
            n = len(self.points) - 1
            self.values = [round(k / n, self.decimals) for k in range(n + 1)]
        else:
            self.values = [round(math.log10(p), self.decimals)
                           for p in self.points]
        # rounding a monotonic function stays (weakly) monotonic
        assert all(v1 >= v0 for v0, v1 in zip(self.values, self.values[1:]))

    @property
    def memorized_digits(self) -> int:
        value_cost = (0 if _is_uniform(self.values)
                      else self.decimals * (len(self.points) - 2))
        grid_cost = (0 if _is_uniform(self.points)
                     else sum(_frac_digits(p) for p in self.points))
        return value_cost + grid_cost

    # -- interpolating lookups ------------------------------------------------

    def log_interp(self, m: float) -> float:
        i = self._bracket(self.points, m)
        x0, x1 = self.points[i], self.points[i + 1]
        v0, v1 = self.values[i], self.values[i + 1]
        est = v0 + (m - x0) / (x1 - x0) * (v1 - v0)
        return round(est, self.decimals)  # head holds table precision, no more

    def antilog_interp(self, f: float) -> float:
        for i in range(len(self.points) - 1):
            v0, v1 = self.values[i], self.values[i + 1]
            if v0 <= f <= v1 and v1 > v0:
                x0, x1 = self.points[i], self.points[i + 1]
                return x0 + (f - v0) / (v1 - v0) * (x1 - x0)
        return 10.0  # f above every interior value (only via fp dust)

    # -- nearest-entry lookups (no interpolation) -----------------------------

    def log_nearest(self, m: float) -> float:
        return min(zip(self.points, self.values), key=lambda pv: abs(pv[0] - m))[1]

    def antilog_nearest(self, f: float) -> float:
        return min(zip(self.points, self.values), key=lambda pv: abs(pv[1] - f))[0]

    @staticmethod
    def _bracket(xs: list[float], x: float) -> int:
        lo, hi = 0, len(xs) - 2
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if xs[mid] <= x:
                lo = mid
            else:
                hi = mid - 1
        return lo


def split(x: float) -> tuple[float, int]:
    e = math.floor(math.log10(x))
    m = x / 10**e
    if m >= 10.0:
        m, e = m / 10.0, e + 1
    if m < 1.0:
        m, e = m * 10.0, e - 1
    return m, e


def log_multiply(a: float, b: float, table: LogTable, mode: str) -> float:
    ma, ea = split(a)
    mb, eb = split(b)
    if mode == "interp":
        total = table.log_interp(ma) + table.log_interp(mb)
    else:
        total = table.log_nearest(ma) + table.log_nearest(mb)
    k = math.floor(total + 1e-12)
    frac = total - k
    mant = (table.antilog_interp(frac) if mode == "interp"
            else table.antilog_nearest(frac))
    return mant * 10.0 ** (ea + eb + k)


# ---------------------------------------------------------------------------
# Baseline: round to n significant figures and multiply exactly
# ---------------------------------------------------------------------------


def round_sig(x: float, n: int) -> float:
    if x == 0:
        return 0.0
    e = math.floor(math.log10(abs(x)))
    return round(x, -(e - (n - 1)))


def direct_multiply(a: float, b: float, sig: int) -> float:
    return round_sig(a, sig) * round_sig(b, sig)


# ---------------------------------------------------------------------------
# Monte Carlo study
# ---------------------------------------------------------------------------


@dataclass
class Stats:
    label: str
    cost: str
    cost_digits: int
    median: float
    p90: float
    worst: float
    within_1: float
    within_5: float
    within_10: float

    @classmethod
    def from_errors(cls, label: str, cost: str, cost_digits: int,
                    errs: list[float]) -> "Stats":
        errs = sorted(errs)
        n = len(errs)
        return cls(
            label=label,
            cost=cost,
            cost_digits=cost_digits,
            median=statistics.median(errs),
            p90=errs[int(0.9 * n)],
            worst=errs[-1],
            within_1=sum(e <= 0.01 for e in errs) / n,
            within_5=sum(e <= 0.05 for e in errs) / n,
            within_10=sum(e <= 0.10 for e in errs) / n,
        )

    def row(self) -> str:
        return (f"{self.label:42} {self.cost:28} {self.median:7.2%} "
                f"{self.p90:7.2%} {self.worst:7.2%} {self.within_1:5.0%} "
                f"{self.within_5:5.0%} {self.within_10:5.0%}")


def sample_problems(n: int, rng: random.Random) -> list[tuple[float, float]]:
    """Operands with log-uniform mantissas (leading digits follow Benford)."""
    out = []
    for _ in range(n):
        a = 10.0 ** rng.uniform(0.0, 1.0) * 10 ** rng.randint(0, 4)
        b = 10.0 ** rng.uniform(0.0, 1.0) * 10 ** rng.randint(0, 4)
        out.append((a, b))
    return out


def frange(start: float, stop: float, step: float) -> list[float]:
    n = round((stop - start) / step)
    return [round(start + i * step, 10) for i in range(n + 1)]


R10 = [1.0, 1.25, 1.6, 2.0, 2.5, 3.15, 4.0, 5.0, 6.3, 8.0, 10.0]
R20 = [1.0, 1.12, 1.25, 1.4, 1.6, 1.8, 2.0, 2.24, 2.5, 2.8, 3.15, 3.55,
       4.0, 4.5, 5.0, 5.6, 6.3, 7.1, 8.0, 9.0, 10.0]


def build_tables() -> list[LogTable]:
    integers = [float(i) for i in range(1, 11)]
    configs = [
        ("integers 1-10", integers, 1),
        ("integers 1-10", integers, 2),
        ("integers 1-10", integers, 3),
        ("ints + 1.5/2.5/3.5", integers + [1.5, 2.5, 3.5], 2),
        ("half steps", frange(1.0, 10.0, 0.5), 2),
        ("quarter steps", frange(1.0, 10.0, 0.25), 2),
        ("quarter steps", frange(1.0, 10.0, 0.25), 3),
    ]
    tables = [LogTable(f"{name}, {k} dec", pts, k) for name, pts, k in configs]
    tables.append(LogTable("R10 preferred numbers, 1 dec", R10, 1,
                           pattern_values=True))
    tables.append(LogTable("R20 preferred numbers, 2 dec", R20, 2,
                           pattern_values=True))
    return tables


def run() -> None:
    rng = random.Random(42)
    problems = sample_problems(20_000, rng)
    truths = [a * b for a, b in problems]

    log_stats: list[Stats] = []
    for mode in ("interp", "nearest"):
        for table in build_tables():
            errs = [abs(log_multiply(a, b, table, mode) / t - 1.0)
                    for (a, b), t in zip(problems, truths)]
            log_stats.append(Stats.from_errors(
                f"log/{mode}: {table.name}",
                f"{table.memorized_digits} memorized",
                table.memorized_digits,
                errs,
            ))

    direct_stats: list[Stats] = []
    for sig in (1, 2, 3):
        errs = [abs(direct_multiply(a, b, sig) / t - 1.0)
                for (a, b), t in zip(problems, truths)]
        direct_stats.append(Stats.from_errors(
            f"direct: round to {sig} sig fig{'s' if sig > 1 else ''}",
            f"0 memorized, {sig}x{sig} multiply",
            0,
            errs,
        ))

    header = (f"{'method':42} {'memory cost':28} {'median':>8} {'p90':>8} "
              f"{'worst':>8} {'<=1%':>6} {'<=5%':>6} {'<=10%':>6}")
    sep = "-" * len(header)

    print("Mental multiplication accuracy, 20,000 random problems")
    print("(relative error; mantissas log-uniform in [1,10))\n")
    print(header)
    print(sep)
    for s in sorted(log_stats, key=lambda s: (s.label.split(":")[0], s.cost_digits)):
        print(s.row())
    print(sep)
    for s in direct_stats:
        print(s.row())

    print("\nPareto-optimal log configs, either mode "
          "(no cheaper config has lower p90 error):")
    frontier = [
        s for s in log_stats
        if not any(o.cost_digits <= s.cost_digits and o.p90 < s.p90
                   and o is not s for o in log_stats)
    ]
    for s in sorted(frontier, key=lambda s: s.cost_digits):
        print(f"  {s.cost_digits:3d} digits -> p90 {s.p90:6.2%}  ({s.label})")

    print("""
Error sources by mode:
  interp    quantization ~ 0.5*10^-decimals per lookup, plus linear-
            interpolation error ~ h^2/(8 m^2 ln10), worst near m = 1.
  nearest   snapping error: up to half the *log-domain* gap between
            neighboring entries, per lookup (3 lookups per multiply).
            On a linear grid the gaps near m = 1 are huge (log 2 - log 1
            = 0.30), so nearest-mode hurts most exactly where Benford
            puts most mantissas. A log-uniform grid (R10/R20 preferred
            numbers) equalizes every gap AND makes the stored values a
            free arithmetic pattern - you memorize the grid, not the logs.""")


if __name__ == "__main__":
    run()
