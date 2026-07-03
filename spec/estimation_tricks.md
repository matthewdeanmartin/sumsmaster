# Estimation Tricks — Phase Plan

Status: **planning document**. Nothing here is implemented. This extends the
trick taxonomy beyond exact elementary arithmetic into **estimation**: large
numbers, approximate answers, and operations/functions beyond `+ − × ÷`.

The audience for this file is the implementing bot. It assumes the Phase 0
codebase: `sumsmaster/tricks/model.py` (`Problem`, `Trick`, detectors),
`sumsmaster/tricks/registry.py` (exact tricks), `sumsmaster/coverage.py`
(domain enumeration + coverage report).

---

## 1. Why estimation is a different product surface

Exact tricks answer: *"what is 7 × 8?"* — graded right/wrong.

Estimation tricks answer: *"roughly what is 487 × 2,310?"* or *"about what is
√70?"* — graded by **how close** you got and **how fast**. This is the skill
adults actually use (tips, unit conversion, sanity-checking a spreadsheet,
Fermi questions in interviews), and it is the skill the classic mental-math
books teach (slide-rule-era texts literally tell you to memorize a low
precision log table and interpolate — see §4).

Two consequences for the architecture:

1. **Answers are tolerance-graded, not exact-matched.** The learner model
   must record *precision achieved*, not just correct/incorrect.
2. **Some tricks have memorized tables as prerequisites.** "Multiply via
   logs" is unusable until the learner has drilled ~10 log values. Tables
   become first-class learnable objects with their own spaced repetition.

---

## 2. New domain model (Phase E1)

Do **not** overload the existing `Problem` (it is `int a, int b, binary op`
and many exact detectors depend on that). Add a parallel model.

```text
sumsmaster/estimation/
  model.py       # EstimationProblem, grading
  registry.py    # estimation tricks
  tables.py      # memorization assets (log table, reciprocals, anchors)
  coverage.py    # estimation-domain coverage analysis
```

### EstimationProblem

```text
EstimationProblem:
  expression: str            # human-readable, e.g. "487 × 2310", "√70", "ln 3"
  true_value: float
  kind: enum                 # MUL_LARGE, DIV_LARGE, SQRT, CBRT, POWER, LOG,
                             # EXP, TRIG, PERCENT, COMPOUND_GROWTH, FERMI, ...
  operands: tuple[float,...] # raw inputs, for detectors
```

Unary operations are first-class (`√70` has one operand). `kind` plays the
role the `Operation` enum plays for exact tricks: a fast pre-filter before
detectors run.

### Grading: log-distance bands

Grade an answer `x` against truth `t` by relative log error:

```text
err = |log10(x / t)|        (undefined/max if signs differ or x == 0)
```

Bands (tunable constants, store the band on each review):

```text
exact        err == 0
within 1%    err ≤ log10(1.01)  ≈ 0.0043
within 5%    err ≤ log10(1.05)  ≈ 0.021
within 10%   err ≤ log10(1.10)  ≈ 0.041
within 2×    err ≤ log10(2)     ≈ 0.301
right OOM    err ≤ 0.5          (order of magnitude)
wrong        otherwise
```

Each estimation trick declares a **target band** (the precision the trick can
deliver when executed correctly). Mastery of an estimation trick means:
consistently landing in the trick's target band, fast. Landing in a *worse*
band is the estimation analog of a wrong answer; the gap between achieved
band and target band is diagnostic signal (e.g. log-method answers off by
exactly 10× usually mean a dropped characteristic — see §4).

### What "mastered" means here

Per trick: last N attempts, fraction landing in target band, median seconds.
Reuse the exact-trick `SkillState` shape; add `achieved_band` to the review
record.

---

## 3. Memorization assets / tables (Phase E2)

A `Table` is a named set of fact→value pairs drilled by ordinary flashcard
spaced repetition, but tracked as a *prerequisite* for tricks.

```text
Table:
  name: str
  entries: dict[str, float]   # prompt -> value
  precision: int              # sig figs expected on recall
```

### Table 1: log₁₀ of 1–10 (two decimal places)

The cornerstone. This is the trick from the slide-rule-era books.

```text
log 1 = 0.00      log 6 = 0.78
log 2 = 0.30      log 7 = 0.85
log 3 = 0.48      log 8 = 0.90
log 4 = 0.60      log 9 = 0.95
log 5 = 0.70      log 10 = 1.00
```

Teach the *structure*, not ten arbitrary facts — that is the Sumsmaster way:

```text
log 2 ≈ 0.30   because 2^10 = 1024 ≈ 10^3
log 4 = 2·log 2 = 0.60
log 8 = 3·log 2 = 0.90
log 5 = 1 − log 2 = 0.70
log 3 ≈ 0.48   (memorize; or 3^4 = 81 ≈ 80 ⇒ 4·log3 ≈ 1.9)
log 6 = log 2 + log 3 = 0.78
log 9 = 2·log 3 = 0.95 (really 0.954)
log 7 ≈ 0.845  (memorize; or log 49 ≈ log 50 = 1.70 ⇒ log 7 ≈ 0.85)
```

Only **two** entries are irreducible memorization (log 2, log 3, arguably
log 7); the rest derive. The prerequisite graph should encode this.

### Table 2: reciprocals of 2–12 (three decimals)

```text
1/2 = .500   1/3 = .333   1/4 = .250   1/6 = .167   1/7 = .143
1/8 = .125   1/9 = .111   1/11 = .0909  1/12 = .0833
```

Turns division into multiplication: `a ÷ 7 ≈ a × 0.143`.

### Table 3: anchor constants

```text
√2 ≈ 1.414      √3 ≈ 1.732     √10 ≈ 3.16
π ≈ 3.14        π² ≈ 9.87 (≈10)   1/π ≈ 0.318
e ≈ 2.718       ln 10 ≈ 2.30      log e ≈ 0.434
1 rad ≈ 57.3°   2^10 ≈ 10^3
mile ≈ 1.61 km (≈ φ; adjacent Fibonacci numbers convert mi↔km)
```

### Table 4: squares 13–31 (enables √ and difference-of-squares tricks)

Already implied by exact-trick deferred work (`squaring teens`); estimation
gives it a second consumer.

---

## 4. The estimation trick catalog (Phase E3)

Each item below should become a `Trick`-like object with: name, explanation,
worked example, `kind` pre-filter, detector, **generator**, target band, and
prerequisite tables/tricks. Grouped by category.

### 4.1 Foundations: scientific notation and rounding

| Trick | Method | Target band |
|---|---|---|
| split off powers of 10 | `487 × 2310 → 4.87×10² × 2.31×10³`; multiply mantissas, add exponents | n/a (enabler) |
| round to 1–2 sig figs | `4.87 × 2.31 → 5 × 2.3` | 10% |
| compensated rounding | round one operand up, the other down: `4.87×2.31 ≈ 5×2.25` | 5% |
| error-direction tracking | note "I rounded up twice ⇒ true answer is lower" | improves any band |
| digit-count rule | #digits of `a×b` is `d_a + d_b` or `d_a + d_b − 1`; decide by leading digits | OOM check |

### 4.2 The log method (the book trick)

Prerequisite: Table 1. This is the flagship — a learner who masters it can
multiply, divide, take powers and roots of arbitrary numbers to ~2 sig figs.

```text
Multiply:  487 × 2310
  log ≈ 2 + log 4.87 + 3 + log 2.31
  log 4.87 ≈ 0.69   (interpolate between log 4 = .60 and log 5 = .70)
  log 2.31 ≈ 0.36   (interpolate between log 2 = .30 and log 3 = .48)
  sum ≈ 5 + 0.69 + 0.36 = 6.05
  antilog 0.05 ≈ 1.12  ⇒  ≈ 1.12 × 10^6      (true: 1,124,970 — 0.3% off)

Divide:    subtract logs instead of adding.
Powers:    a^n → n · log a.       e.g. 1.07^10 ≈ 10^(10×0.0294) ≈ 2.0
Roots:     ⁿ√a → log a ÷ n.       e.g. ∛5000 ≈ 10^(3.70/3) = 10^1.233 ≈ 17.1
```

Sub-tricks to model **separately** (they fail independently):

* **interpolation forward** (number → log): linear interpolation between
  table entries. Yes, really — logs are smooth enough that linear
  interpolation on a 10-entry table gives ~1% accuracy.
* **interpolation backward** (antilog: fractional log → mantissa).
* **characteristic bookkeeping** (the integer part / powers of ten).
  Classic failure mode: answer off by exactly 10× — make the wrong-answer
  diagnoser check for this.

Target band: 5% for multiply/divide, 10% for powers/roots.

> **Measured update:** see `spec/better_logs.md`. Simulation confirms these
> bands *with* interpolation, but shows the integer table collapses without
> it (median 14%). The no-interpolation on-ramp is a Renard/preferred-number
> table (R10 → R20), which should be offered as Table 1's alternative form.

### 4.3 Division without logs

| Trick | Method | Band |
|---|---|---|
| multiply by reciprocal | `a ÷ 7 = a × 0.143` (Table 2) | 1% |
| scale to a clean divisor | `÷ 4.8 ≈ ÷ 5 then × 25/24 ≈ +4%` | 5% |
| ÷9, ÷11, ÷99 patterns | repeating decimals: `a/9` repeats digit, `a/11` repeats pair | exact-ish |
| fraction simplification | cancel common factors before estimating | enabler |

### 4.4 Roots

| Trick | Method | Band |
|---|---|---|
| √ via nearest square | `√(a² + b) ≈ a + b/(2a)`; e.g. `√70 ≈ 8 + 6/16 = 8.375` (true 8.367) | 1% |
| √ digit-pairing for OOM | pair digits from right; #pairs gives #digits of root | OOM |
| Newton step | guess g, then average `(g + n/g)/2` | 1% |
| √10 ≈ 3.16 shift | `√(a × 10^2k) = √a × 10^k`; odd exponent ⇒ multiply by 3.16 | enabler |
| ∛ via log | `log ÷ 3` | 10% |
| perfect-cube last digit | cube roots of perfect cubes ≤ 10⁶ from last digit + magnitude (party trick, teaches structure) | exact |

### 4.5 Small-x approximations (the calculus-free Taylor toolkit)

| Trick | Method | Band |
|---|---|---|
| binomial | `(1+x)ⁿ ≈ 1 + nx` for |nx| ≲ 0.2; second-order `+ n(n−1)x²/2` to upgrade | 5%/1% |
| reciprocal of near-1 | `1/(1+x) ≈ 1 − x`; e.g. `1/1.04 ≈ 0.96` | 1% |
| √ of near-1 | `√(1+x) ≈ 1 + x/2` | 1% |
| ln of near-1 | `ln(1+x) ≈ x`, so `log10(1+x) ≈ 0.434·x` — feeds the log method's interpolation | 1% |
| eˣ small x | `eˣ ≈ 1 + x` | 5% |

### 4.6 Percentages, growth, money

| Trick | Method | Band |
|---|---|---|
| a% of b = b% of a | `16% of 25 = 25% of 16 = 4` | exact |
| percent via 10%/1% blocks | `35% = 3×10% + 5×1%·... ` decompose | exact |
| successive percentages | `+x% then +y% ≈ +(x+y+xy/100)%` | 1% |
| rule of 72 | doubling time ≈ 72 / rate%; (rule of 70 / 69.3 variants — 72 wins on divisibility) | 5% |
| rule of 72 inverted | rate needed to double in t years ≈ 72/t | 5% |
| compound growth via log | `1.07^10`: see §4.2 powers | 5% |
| tip/tax scaling | 15% = 10% + half of that; 18% ≈ 20% − 10% of that | exact |

### 4.7 Functions beyond the four (trig, log, exp)

| Trick | Method | Band |
|---|---|---|
| small-angle sin/tan | `sin x ≈ x` in radians; degrees: `sin d° ≈ d/57.3` for d ≲ 30 | 5% |
| trig anchors + interpolation | memorize sin of 0/30/45/60/90 (`√0,√1,√2,√3,√4 over 2`); interpolate between | 10% |
| cos from sin | `cos x = sin(90°−x)` | enabler |
| ln from log | `ln a = 2.30 × log a` | 5% |
| natural log anchors | `ln 2 ≈ 0.69`, `ln 10 ≈ 2.30`, `ln 3 ≈ 1.10` | 1% |
| e^x via 10^x | `eˣ = 10^(0.434x)` then antilog | 10% |

### 4.8 Fermi / sanity layer

These are tricks about *unknown* quantities; grading is OOM-band only.

* **geometric-mean bracketing**: sure it's between 10³ and 10⁵? Estimate
  10⁴ (average the exponents, not the values).
* **factor-tree decomposition**: piano tuners in Chicago — decompose into
  factors you can bound.
* **relative-error propagation**: under × and ÷, *relative* errors add;
  under + they don't. Know which operand's sloppiness dominates.
* **plausibility checks** (these double as checks on exact arithmetic):
  last-digit check, parity check, casting out nines, magnitude check.

### 4.9 Exact-trick spillover (large exact arithmetic)

Estimation sessions will surface these; they belong in the *exact* registry's
larger-domain expansion (already catalogued in `spec/deferred.md`), listed
here so the implementer wires the cross-reference:

`25×n = n×100÷4`, `×50 = ×100÷2`, `×15 = ×10 + half`, squaring numbers
ending in 5 (`n5² = n(n+1)‖25`), difference of squares
(`a×b = m² − d²` where `m` is the midpoint), near-100 multiplication
(`97×96 = (97−4)×100 + 4×3`), constant-difference subtraction
(`62−38 = 64−40`).

---

## 5. Problem generation (Phase E3, with the registry)

Each estimation trick needs a generator, not just a detector (this is also
true of exact tricks — same deferred interface, build once):

```text
generate(rng, difficulty) -> EstimationProblem
```

Difficulty knobs per category:

* mantissa "niceness" (4.87 is harder than 5.0),
* number of sig figs the operands carry,
* exponent size (10² vs 10⁷ — pure bookkeeping load),
* for log method: whether interpolation is needed or operands sit on
  table entries,
* for small-x: size of x (approximation degrades as x grows — learner
  should *feel* the band break down around |nx| ~ 0.3).

Detectors still matter (given a problem, which tricks apply?), but for
estimation the generator is primary: sessions are "drill the log method,"
not "classify this found problem."

---

## 6. Coverage analog (Phase E4)

The Phase-0 question was "what fraction of facts does some trick cover?"
The estimation analog:

> Sample N random problems per `kind` across difficulty bands. For each,
> what is the **best band achievable** by some applicable trick, and how
> many tricks apply?

Deliverable: `python -m sumsmaster est-coverage` printing, per kind:
applicable-trick distribution and best-achievable-band distribution. Success
criterion mirrors Phase 0: e.g. ≥95% of MUL_LARGE/DIV_LARGE problems
reachable at the 10% band with ≤2 table prerequisites.

Also add `python -m sumsmaster est-tricks` (taxonomy dump, mirroring
`tricks`).

---

## 7. Suggested implementation order

```text
E1. estimation/model.py — EstimationProblem, kinds, log-distance grading,
    band constants. Pure, tested (property: band montonic in |err|).
E2. estimation/tables.py — Table model + the four tables above, with
    derivation structure (log 4 = 2·log 2) encoded as prerequisites.
E3. estimation/registry.py — tricks from §4 with detector + generator +
    target band + prerequisites. Start with: §4.1 foundations, §4.2 log
    method, §4.4 √ via nearest square, §4.6 rule of 72. That's the MVP
    "wow" set. Then breadth.
E4. estimation/coverage.py + CLI subcommands (est-coverage, est-tricks).
E5. Wire into the (future, deferred.md) SR loop: tolerance-graded reviews,
    achieved_band on Review, table drilling as flashcards gated before
    dependent tricks.
```

Keep E1–E4 free of storage/SR dependencies, matching how Phase 0 kept the
exact-trick taxonomy pure.

## 8. Open questions for the implementer

1. **Float-equality and display.** `true_value` is float; expression
   rendering needs care (√, superscripts) for CLI. Unicode vs ASCII (`sqrt`,
   `^`)? Pick one, make it a formatting concern only.
2. **Timing as a grading input.** Estimation without a clock rewards
   long-division-in-your-head. Bands probably need a time budget per
   difficulty. Defer actual enforcement to the SR loop, but record
   elapsed time from day one.
3. **Does Fermi belong in v1?** It needs curated question content (no clean
   generator). Recommend: define the `FERMI` kind, ship zero generators,
   revisit.
4. **Shared trick base class?** Exact `Trick` and estimation tricks share
   name/explanation/detect but differ in grading and generation. Consider a
   common protocol once the estimation shape stabilizes — do not force it
   prematurely.
5. **Interpolation as its own drillable skill.** Linear interpolation
   appears in the log method, antilog, and trig tables. It may deserve to be
   a standalone trick with its own generated drills (`"log 4.3 ≈ ?"`) and a
   prerequisite edge from each consumer.
