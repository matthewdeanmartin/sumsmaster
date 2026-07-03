# Better Log Tables — PoC findings

Status: **experimental findings**, feeding into `estimation_tricks.md` §4.2
(the log method). Produced by `scripts/poc_log_table.py` (standalone, stdlib
only — `uv run python scripts/poc_log_table.py` reproduces every number
here, seed 42, 20,000 Monte Carlo problems).

Companion artifacts:

* `docs/renard_log_table.html` — learner-facing explainer of the Renard
  table with worked examples.
* `docs/renard_cheatsheet.txt` — printable memorization card (R10 + R20).

---

## 1. The question

The classic mental-math books say: memorize log₁₀ of 1–10 to two decimals,
interpolate linearly, and you can multiply/divide/take powers and roots to a
couple of percent. Given a budget of digits your brain can hold:

1. How much precision does that actually buy?
2. Is there an optimal number of digits to memorize?
3. How does it stack up against just rounding to n significant figures and
   multiplying directly?
4. **What if you can't (or won't) interpolate in your head?**

## 2. The model

One multiplication `a × b` via logs: split each operand into mantissa and
exponent, look up both logs, add, antilog the fractional part. Two lookup
modes:

* **interp** — linear interpolation between bracketing entries, result
  carried at table precision (you can't hold more decimals than your table
  has). The slide-rule-book method.
* **nearest** — no interpolation: snap the mantissa to the nearest table
  point and read its value; antilog by snapping to the nearest stored value.

Memory cost model (digits of long-term memorization):

* each interior entry's value costs `decimals` digits, **but is free if the
  stored values form a constant-step pattern** (counting by 0.1 is a rule,
  not ten facts);
* non-integer grid points cost their fractional digits, **but a
  constant-step grid is free** ("integers 1–10" is a rule);
* log 1 = 0 and log 10 = 1 are always free.

Baseline: round both operands to n significant figures and multiply exactly.
Costs no long-term memory, but requires an n×n-digit mental multiplication
(working-memory load grows ~n²) — a different *kind* of cost, flagged
rather than unified.

Errors are relative, over operands with log-uniform (Benford-realistic)
mantissas. Not modeled: mental-arithmetic slips, time taken, the learner's
interpolation being sloppier than exact linear interpolation.

## 3. Results

```text
method                                digits   median     p90    worst
--- with interpolation -----------------------------------------------
R10 preferred numbers, 1 dec              7    6.74%   15.53%   25.06%
integers 1-10, 1 dec                      8    7.81%   18.13%   36.22%
integers 1-10, 2 dec (the book table)    16    2.62%    6.29%   12.44%
R20 preferred numbers, 2 dec             19    0.90%    2.19%    4.97%
integers 1-10, 3 dec                     24    2.34%    5.82%   11.13%
ints + 1.5/2.5/3.5, 2 dec                25    1.02%    2.41%    4.85%
half steps, 2 dec                        34    1.00%    2.37%    5.26%
quarter steps, 2 dec                     70    0.87%    2.09%    4.39%
quarter steps, 3 dec                    105    0.18%    0.50%    1.37%
--- nearest entry, no interpolation -----------------------------------
R10 preferred numbers, 1 dec              7    6.74%   15.53%   25.06%
integers 1-10, 1 dec                      8   15.22%   34.68%   75.67%
integers 1-10, 2 dec                     16   14.28%   33.75%   75.67%
R20 preferred numbers, 2 dec             19    3.42%    7.96%   13.65%
integers 1-10, 3 dec                     24   14.30%   33.75%   75.67%
ints + 1.5/2.5/3.5, 2 dec                25    8.32%   20.31%   56.52%
half steps, 2 dec                        34    7.48%   18.83%   56.52%
quarter steps, 2 dec                     70    3.75%    9.54%   27.47%
quarter steps, 3 dec                    105    3.67%    9.48%   27.47%
--- baseline: round to n sig figs, multiply exactly -------------------
1 sig fig                                 0   11.09%   29.48%   73.22%
2 sig figs                                0    1.12%    3.21%    8.49%
3 sig figs                                0    0.11%    0.32%    0.87%
```

Pareto frontier across all log configs (no cheaper config has lower p90):

```text
  7 digits -> p90 15.5%   R10, either mode
 16 digits -> p90  6.3%   integers/2dec, interp
 19 digits -> p90  2.2%   R20/2dec, interp
 70 digits -> p90  2.1%   quarter steps/2dec, interp
105 digits -> p90  0.5%   quarter steps/3dec, interp
```

## 4. Findings

### F1. The book's claim checks out — if you interpolate

The classic 16-digit table (log 1–10, two decimals) delivers ~2.6% median,
~6% p90. Linear interpolation on a 10-entry log table really does work;
logs are smooth enough.

### F2. There is an optimal shape, set by balancing two error sources

* quantization ≈ 0.5 × 10⁻ᵈᵉᶜⁱᵐᵃˡˢ per lookup (3 lookups per multiply);
* interpolation error ≈ h²/(8 m² ln 10), worst near mantissa 1 where the
  log curve bends hardest (h = local grid gap).

A table is wasteful when these are unbalanced: a third decimal on the sparse
integer table buys almost nothing (6.3% → 5.8% p90, interpolation-limited),
and a dense grid at one decimal is *worse* than a sparse one (quantization
noise dominates). Spend digits so the two match.

### F3. Without interpolation, the classic table collapses

Median error jumps 2.6% → 14%, p90 6.3% → 34% — worse than the
zero-memorization baseline of rounding to 1 sig fig and multiplying.
Snapping error is half the *log-domain* gap between neighbors, and on a
linear grid the gaps near mantissa 1 are huge (log 2 − log 1 = 0.30) —
exactly where Benford puts most mantissas. Extra decimals do nothing in
this mode (precision you can't index into is wasted).

### F4. The no-interpolation fix: invert the table (Renard / preferred numbers)

Memorize antilogs of *round logs* instead of logs of *round numbers*:
a grid uniform in log space. That is the Renard preferred-number series —
R10 = 1, 1.25, 1.6, 2, 2.5, 3.15, 4, 5, 6.3, 8, 10, whose logs are exactly
0.0, 0.1, …, 1.0. Consequences:

* every snap costs the same small amount (no bad region near 1);
* the stored *values* are a free counting pattern — you memorize the grid
  points (~7 digits for R10, ~19 for R20), not twenty log facts;
* **interpolation becomes unnecessary**: R10 gives byte-identical results
  in both modes (when grid step = value precision, rounding to table
  precision *is* snapping);
* R20 without interpolation: median 3.4%, p90 8% at 19 digits — in the
  same league as 2-sig-fig direct multiplication, while keeping the log
  method's free extension to ÷, powers, and roots;
* R20 *with* interpolation (median 0.9%, p90 2.2% at 19 digits) is the
  overall Pareto winner, beating every linear-grid table tested.

This is decibel arithmetic (each R10 step = 1 dB of power ratio), which is
why engineers do it fluently. Memorization is further compressed by
structure: ×2 = +0.3 = exactly 3 R10 slots, so the whole R10 table is
generated by doubling the seeds {1, 1.25, 1.6}; R20 doubles the seeds
{1, 1.12, 1.25, 1.4, 1.6, 1.8} (×2 = 6 slots).

### F5. Versus round-and-multiply, the honest comparison

On raw precision the log method roughly ties 2-sig-fig direct
multiplication at realistic budgets (R20/interp slightly beats it; 3-sig-fig
direct beats everything under 100 memorized digits). The log method's real
edge is *which operations you perform* — two lookups and one short addition
instead of an n×n multiply with carries — and *generality*: the same 19
digits also buy division (subtract), roots (divide the log), and powers
(multiply the log). Direct multiplication offers no path to those.

Known weak spot: mantissas near 1 (e.g. 1.05ⁿ compound-interest problems)
— the table can't resolve them; use small-x approximations instead
(`estimation_tricks.md` §4.5: ln(1+x) ≈ x).

## 5. Curriculum implications (amendments to estimation_tricks.md)

1. **§4.2 should offer two on-ramps.** The interpolation-free path is
   R10 → R20 ("for each tick of 0.1 in log, know the number"), not the
   integer log table. The integer table only earns its keep alongside
   interpolation skill.
2. **Interpolation is confirmed as its own drillable skill** (open
   question §8.5): it is worth a ~3–4× precision multiplier on any table,
   and its absence changes which table you should memorize. Model it as a
   separate trick with prerequisite edges.
3. **Tables should support pattern-valued storage** in the Phase E2
   `Table` model: a table whose values are `k × step` must cost only its
   grid, not its values. (The cost model in `tables.py` needs this.)
4. **Add the doubling-rule derivation structure** to the Renard tables the
   same way Table 1 derives log 4 from log 2: seeds + "×2 = +3 slots".
5. **Target bands, measured:** R10/no-interp ≈ within-2× tier, reliably
   ~10–15%; R20/no-interp ≈ 10% band; R20 or augmented integer table with
   interpolation ≈ 5% band, median ~1%; 1% band needs ~100 memorized
   digits or 3-sig-fig direct multiplication.

## 6. Caveats / honest limits

* Memorized-digit cost and working-memory cost are different currencies;
  the comparison table flags but does not unify them.
* No model of slips, fatigue, or speed. Adding logs is *easier* than
  multiplying multi-digit numbers, which the error numbers don't credit.
* Human "nearest" snapping was modeled as linear distance; snapping by
  ratio would be slightly kinder to the Renard tables.
* Linear interpolation was modeled as exact; a human's eyeballed fraction
  adds noise the simulation doesn't capture (so interp rows are slightly
  optimistic, strengthening the Renard recommendation).
